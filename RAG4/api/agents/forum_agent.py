from .base_agent import BaseAgent
from chroma_utils import search_forum

class ForumAgent(BaseAgent):
    def __init__(self):
        super().__init__("ForumAgent")
    
    def process(self, data):
        question = data.get("question", "")
        selected_sites = data.get("selected_sites", [])
        
        self.log(f"Searching for: '{question}' on {selected_sites}")
        
        if not selected_sites:
            self.log("No sites selected")
            return True
        
        success = search_forum(question, selected_sites)
        
        if success:
            self.log(f"Successfully searched {len(selected_sites)} sites")
        else:
            self.log("Forum search failed")
            
        return success