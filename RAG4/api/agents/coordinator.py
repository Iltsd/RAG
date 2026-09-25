from .chat_agent import ChatAgent
from .forum_agent import ForumAgent
from .document_agent import DocumentAgent
from .session_agent import SessionAgent
from pydantic_models import QueryInput, QueryResponse
from typing import AsyncIterator
from llm_provider import create_provider, load_config
from tts_engine import create_tts_engine

class AgentCoordinator:
    def __init__(self):
        config = load_config()
        provider = create_provider(config)
        preprocessing_enabled = config.get("preprocessing", {}).get("enabled", True)
        retrieval_enabled = config.get("retrieval", {}).get("enabled", True)
        tools_enabled = config.get("tools", {}).get("enabled", False)
        self.chat_agent = ChatAgent(provider=provider, preprocessing_enabled=preprocessing_enabled, retrieval_enabled=retrieval_enabled)
        self.forum_agent = ForumAgent()
        self.document_agent = DocumentAgent()
        self.session_agent = SessionAgent()
        self.tts_engine = create_tts_engine(config)
    
    def process_chat(self, query_input: QueryInput) -> QueryResponse:
        result = self.chat_agent.process(query_input)
        return QueryResponse(**result)

    async def stream_chat(self, query_input: QueryInput) -> AsyncIterator[str]:
        async for token in self.chat_agent.stream_process(query_input):
            yield token
    
    def upload_document(self, file):
        return self.document_agent.process({"action": "upload", "file": file})
    
    def delete_document(self, file_id):
        return self.document_agent.process({"action": "delete", "file_id": file_id})
    
    def list_documents(self):
        return self.document_agent.process({"action": "list"})
    
    def get_chat_sessions(self):
        return self.session_agent.get_chat_sessions()
    
    def get_chat_history(self, session_id):
        return self.session_agent.get_chat_history(session_id)

coordinator = AgentCoordinator()
