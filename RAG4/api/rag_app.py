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
        from db_utils import get_chat_history  # Импорт из вашего файла
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
        summary_prompt = f"Summarize this text in 2-3 sentences: {full_answer}"
        summary = self.llm.invoke(summary_prompt)
        answer = summary  # <-- Исправление: summary - строка, используем напрямую
        
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

# Пример использования
if __name__ == "__main__":
    agents = {
        "rag": SimpleRAGAgent(),
        "summarizer": SummarizerAgent()
    }
    query = "What is HTTPS?"
    agent_type = "rag"  # Или "summarizer"
    result = agents[agent_type].process_query(query)
    print(f"Ответ: {result['answer']}")
    print(f"Аудио: {result['audio_file']}")