from langchain_utils import get_rag_chain
from textTS import synthesize_speech
from typing import Dict, Optional, Annotated, TypedDict
import uuid
from langchain_community.llms import Ollama  # Для простых агентов без RAG
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Состояние для передачи данных между агентами
class AgentState(TypedDict):
    query: str
    answer: str
    full_answer: str
    audio_file: str
    session_id: str

class SimpleRAGAgent:
    """
    Простой агент для RAG-системы: получает запрос, генерирует ответ и озвучивает его.
    """
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.rag_chain = get_rag_chain(model_name)
   
    def process_query(self, state: AgentState) -> AgentState:
        """
        Обрабатывает запрос: генерирует ответ.
        """
        from db_utils import get_chat_history
        chat_history = get_chat_history(state["session_id"])
       
        # Генерируем ответ через RAG
        result = self.rag_chain.invoke({
            "input": state["query"],
            "chat_history": chat_history
        })
        full_answer = result["answer"]
       
        # Сохраняем в историю
        from db_utils import insert_application_logs
        insert_application_logs(state["session_id"], state["query"], full_answer, self.model_name)
       
        return {
            "full_answer": full_answer,
            "answer": full_answer,  # Пока что полный как базовый
            "session_id": state["session_id"]
        }

class SummarizerAgent:
    """
    Агент для суммаризации: суммирует полный ответ.
    """
    def __init__(self, model_name: str = "llama3.2"):
        self.model_name = model_name
        self.llm = Ollama(model=model_name)
    
    def process_query(self, state: AgentState) -> AgentState:
        """
        Суммирует полный ответ.
        """
        summary_prompt = f"Summarize next text in few sentences: {state['query']}"
        summary = self.llm.invoke(summary_prompt)
        answer = summary
        
        return {
            "answer": answer,
            "full_answer": answer,
            "session_id": state["session_id"]
        }

class PreprocessorAgent:
    """
    Агент для предобработки: очищает и форматирует запрос перед передачей дальше.
    """
    def __init__(self):
        self.llm = Ollama(model="llama3.2")
    
    def process_query(self, state: AgentState) -> AgentState:
        """
        Очищает и форматирует запрос для передачи следующему агенту.
        """
        # Простая предобработка: очистка, форматирование
        cleaned_query = state["query"].strip().replace("\n", " ").replace("\t", " ")
        prompt = f"Format and refine your next search query: {cleaned_query}"
        formatted_query = self.llm.invoke(prompt)
        
        return {
            "query": formatted_query,
            "session_id": state["session_id"]
        }

class TTSAgent:
    """
    Агент для озвучивания: принимает текст и генерирует аудиофайл.
    """
    def process_query(self, state: AgentState) -> AgentState:
        """
        Озвучивает финальный ответ и возвращает путь к файлу.
        """
        audio_file = synthesize_speech(state["answer"])
        
        return {
            "answer": state["answer"],
            "audio_file": audio_file,
            "session_id": state["session_id"]
        }

def create_rag_graph(model_name: str = "llama3.2"):
    graph = StateGraph(AgentState)
    
    graph.add_node("preprocessor", PreprocessorAgent().process_query)
    graph.add_node("rag", SimpleRAGAgent(model_name).process_query)
    graph.add_node("summarizer", SummarizerAgent(model_name).process_query)
    graph.add_node("tts", TTSAgent().process_query)
    
    graph.add_edge("preprocessor", "rag")
    graph.add_edge("rag", "tts")
    graph.add_edge("tts", END)
    
    graph.set_entry_point("preprocessor")
    
    return graph.compile()

def create_summary_graph(model_name: str = "llama3.2"):
    graph = StateGraph(AgentState)
    
    graph.add_node("preprocessor", PreprocessorAgent().process_query)
    graph.add_node("summarizer", SummarizerAgent(model_name).process_query)
    graph.add_node("tts", TTSAgent().process_query)
    
    graph.add_edge("preprocessor", "summarizer")
    graph.add_edge("summarizer", "tts")
    graph.add_edge("tts", END)
    
    graph.set_entry_point("preprocessor")
    
    return graph.compile()

# Функция для вызова графа (выбор по типу)
def run_agent_chain(query: str, chain_type: str = "rag", model_name: str = "llama3.2", session_id: Optional[str] = None) -> Dict[str, str]:
    """
    Вызывает выбранную цепочку агентов.
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Создаём состояние
    initial_state = {
        "query": query,
        "session_id": session_id
    }
    
    if chain_type == "rag":
        graph = create_rag_graph(model_name)
    elif chain_type == "summarizer":
        graph = create_summary_graph(model_name)
    else:
        raise ValueError(f"Unknown chain_type: {chain_type}")
    
    # Запускаем граф
    final_state = graph.invoke(initial_state)
    
    return {
        "answer": final_state["answer"],
        "audio_file": final_state["audio_file"],
        "session_id": final_state["session_id"]
    }

# Пример использования
if __name__ == "__main__":
    query = "What is HTTPS?"
    chain_type = "rag"  # Или "summary"
    result = run_agent_chain(query, chain_type)
    print(f"Ответ: {result['answer']}")
    print(f"Аудио: {result['audio_file']}")