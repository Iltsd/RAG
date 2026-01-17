from .base_agent import BaseAgent
from db_utils import get_all_chat_sessions, get_chat_history

class SessionAgent(BaseAgent):
    def __init__(self):
        super().__init__("SessionAgent")
    
    def process(self, data):
        """Основной метод обработки"""
        action = data.get("action")
        
        if action == "get_sessions":
            return self.get_chat_sessions()
        elif action == "get_history":
            return self.get_chat_history(data["session_id"])
        else:
            return {"error": f"Unknown action: {action}"}
    
    def get_chat_sessions(self):
        self.log("Fetching chat sessions")
        return get_all_chat_sessions()
    
    def get_chat_history(self, session_id):
        self.log(f"Fetching history for: {session_id}")
        return get_chat_history(session_id)