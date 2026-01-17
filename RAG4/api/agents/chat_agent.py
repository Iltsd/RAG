from .base_agent import BaseAgent
from langchain_utils import get_rag_chain
from db_utils import get_chat_history, insert_application_logs
import uuid

class ChatAgent(BaseAgent):
    def __init__(self):
        super().__init__("ChatAgent")
    
    def process(self, query_input):
        self.log(f"Processing: {query_input.question[:50]}...")
        
        session_id = query_input.session_id or str(uuid.uuid4())
        chat_history = get_chat_history(session_id)
        
        rag_chain = get_rag_chain(query_input.model.value)
        result = rag_chain.invoke({
            "input": query_input.question,
            "chat_history": chat_history
        })
        
        answer = result["answer"]
        
        # Логируем источники
        for i, doc in enumerate(result.get("context", [])):
            self.log(f"Source {i+1}: {doc.page_content[:100]}...")
        
        insert_application_logs(session_id, query_input.question, answer, query_input.model.value)
        self.log(f"Response generated for session {session_id}")
        
        return {
            "answer": answer,
            "session_id": session_id,
            "model": query_input.model
        }