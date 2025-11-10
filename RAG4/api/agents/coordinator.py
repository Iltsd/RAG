# api/agents/coordinator.py
from .chat_agent import ChatAgent
from .forum_agent import ForumAgent
from .document_agent import DocumentAgent
from .session_agent import SessionAgent
from pydantic_models import QueryInput, QueryResponse

class AgentCoordinator:
    def __init__(self):
        self.chat_agent = ChatAgent()
        self.forum_agent = ForumAgent()
        self.document_agent = DocumentAgent()
        self.session_agent = SessionAgent()
    
    def process_chat(self, query_input: QueryInput) -> QueryResponse:
        """Обрабатывает чат-запрос"""
        result = self.chat_agent.process(query_input)
        return QueryResponse(**result)
    
    def upload_document(self, file):
        """Загружает документ"""
        return self.document_agent.process({"action": "upload", "file": file})
    
    def delete_document(self, file_id):
        """Удаляет документ"""
        return self.document_agent.process({"action": "delete", "file_id": file_id})
    
    def list_documents(self):
        """Список документов"""
        return self.document_agent.process({"action": "list"})
    
    def get_chat_sessions(self):
        """Список сессий"""
        return self.session_agent.get_chat_sessions()
    
    def get_chat_history(self, session_id):
        """История чата"""
        return self.session_agent.get_chat_history(session_id)

# Глобальный экземпляр координатора
coordinator = AgentCoordinator()