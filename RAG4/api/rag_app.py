from langchain_utils import get_rag_chain
from textTS import synthesize_speech
from typing import Dict, Optional
import uuid
from langchain_community.llms import Ollama  # Для простых агентов без RAG

class SimpleRAGAgent:
    """
    Простой агент для RAG-системы: получает запрос, генерирует ответ и озвучивает его.
    """
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.rag_chain = get_rag_chain(model_name)
   
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Обрабатывает запрос: генерирует ответ и озвучивает его.
       
        Args:
            query (str): Запрос пользователя.
            session_id (str): ID сессии (опционально).
       
        Returns:
            Dict: {'answer': str, 'audio_file': str or None}
        """
        if not session_id:
            session_id = str(uuid.uuid4())
       
        # Получаем историю чата (если есть)
        from db_utils import get_chat_history
        chat_history = get_chat_history(session_id)
       
        # Генерируем ответ через RAG
        result = self.rag_chain.invoke({
            "input": query,
            "chat_history": chat_history
        })
        answer = result["answer"]
       
        # Озвучиваем ответ
        audio_file = synthesize_speech(answer)
       
        # Сохраняем в историю (опционально)
        from db_utils import insert_application_logs
        insert_application_logs(session_id, query, answer, self.model_name)
       
        return {
            "answer": answer,
            "audio_file": audio_file,
            "session_id": session_id
        }

class SummarizerAgent:
    """
    Агент для суммаризации: генерирует ответ, затем создаёт краткую версию (summary) и озвучивает её.
    """
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.llm = Ollama(model=model_name)
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Генерирует полный ответ, суммирует его и возвращает краткую версию с озвучкой.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        from db_utils import get_chat_history
        chat_history = get_chat_history(session_id)
        
        # Генерируем полный ответ через RAG
        from langchain_utils import get_rag_chain
        rag_chain = get_rag_chain(self.model_name)
        result = rag_chain.invoke({
            "input": query,
            "chat_history": chat_history
        })
        full_answer = result["answer"]
        
        # Суммируем ответ
        summary_prompt = f"Summarize text in 3 sentences(don't add this sentence 'Summarize text in 3 sentences'): {full_answer}"
        summary = self.llm.invoke(summary_prompt)
        answer = summary  # Исправление: summary - строка
        
        # Озвучиваем суммари
        audio_file = synthesize_speech(answer)
        
        from db_utils import insert_application_logs
        insert_application_logs(session_id, query, full_answer, self.model_name)  # Сохраняем полный ответ
        
        return {
            "answer": answer,  # Краткая версия
            "full_answer": full_answer,  # Полный ответ (опционально)
            "audio_file": audio_file,
            "session_id": session_id
        }

class PreprocessorAgent:
    """
    Агент для предобработки: очищает и форматирует запрос перед передачей дальше.
    """
    def __init__(self):
        self.llm = Ollama(model="llama3.2")
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Очищает и форматирует запрос для передачи следующему агенту.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Простая предобработка: очистка, форматирование
        cleaned_query = query.strip().replace("\n", " ").replace("\t", " ")
        prompt = f"Format and refine the following search query: {cleaned_query}"
        formatted_query = self.llm.invoke(prompt)
        answer = formatted_query  # Возвращаем уточнённый запрос как "ответ"
        
        return {
            "answer": answer,  # Уточнённый запрос для следующего агента
            "session_id": session_id
        }

class TTSAgent:
    """
    Агент для озвучивания: принимает текст и генерирует аудиофайл.
    """
    def process_query(self, text: str, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Озвучивает переданный текст и возвращает путь к файлу.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        audio_file = synthesize_speech(text)
        
        return {
            "answer": text,  # Текст (для цепочки)
            "audio_file": audio_file,
            "session_id": session_id
        }

class MultiAgentChain:
    """
    Цепочка агентов: последовательно вызывает Preprocessor → SimpleRAGAgent → SummarizerAgent → TTSAgent.
    """
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.preprocessor = PreprocessorAgent()
        self.rag_agent = SimpleRAGAgent(model_name)
        self.summarizer = SummarizerAgent(model_name)
        self.tts_agent = TTSAgent()
    
    def process_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, str]:
        """
        Вызывает агентов последовательно, передавая данные.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 1. Предобработка
        print("Step 1: Preprocessing...")
        prep_result = self.preprocessor.process_query(query, session_id)
        cleaned_query = prep_result["answer"]
        
        # 2. RAG-генерация
        print("Step 2: RAG generation...")
        rag_result = self.rag_agent.process_query(cleaned_query, session_id)
        full_answer = rag_result["answer"]
        
        # 3. Суммаризация
        print("Step 3: Summarization...")
        summary_result = self.summarizer.process_query(full_answer, session_id)
        summary_answer = summary_result["answer"]
        
        # 4. Озвучивание
        print("Step 4: TTS...")
        tts_result = self.tts_agent.process_query(summary_answer, session_id)
        final_audio = tts_result["audio_file"]
        
        return {
            "answer": summary_answer,  # Финальный ответ (суммари)
            "full_answer": full_answer,  # Полный для деталей
            "audio_file": final_audio,
            "session_id": session_id
        }

# Пример использования
if __name__ == "__main__":
    chain = MultiAgentChain("llama3.2")
    result = chain.process_query("What is HTTPS?")
    print(f"Summary: {result['answer']}")
    print(f"Full: {result['full_answer'][:100]}...")
    print(f"Audio: {result['audio_file']}")