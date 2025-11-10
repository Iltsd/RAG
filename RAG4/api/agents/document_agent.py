# api/agents/document_agent.py
from .base_agent import BaseAgent
from db_utils import insert_document_record, delete_document_record, get_all_documents
from chroma_utils import index_document_to_chroma, delete_doc_from_chroma
import os
import shutil
from fastapi import UploadFile

class DocumentAgent(BaseAgent):
    def __init__(self):
        super().__init__("DocumentAgent")
    
    def process(self, data):
        """Основной метод обработки - диспетчеризация по типу действия"""
        action = data.get("action")
        
        if action == "upload":
            return self.process_upload(data["file"])
        elif action == "delete":
            return self.process_deletion(data["file_id"])
        elif action == "list":
            return self.get_documents_list()
        else:
            return {"error": f"Unknown action: {action}"}
    
    def process_upload(self, file: UploadFile):
        self.log(f"Uploading: {file.filename}")
        
        allowed_extensions = ['.pdf', '.docx', '.html']
        file_extension = os.path.splitext(file.filename)[1].lower()

        if file_extension not in allowed_extensions:
            return {"error": f"Unsupported file type: {file_extension}"}

        temp_file_path = f"temp_{file.filename}"

        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_id = insert_document_record(file.filename)
            success = index_document_to_chroma(temp_file_path, file_id)

            if success:
                self.log(f"Successfully uploaded: {file.filename}")
                return {"message": f"File uploaded and indexed", "file_id": file_id}
            else:
                delete_document_record(file_id)
                return {"error": f"Failed to index {file.filename}"}
                
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def process_deletion(self, file_id: int):
        self.log(f"Deleting document: {file_id}")
        
        chroma_success = delete_doc_from_chroma(file_id)
        db_success = delete_document_record(file_id)
        
        if chroma_success and db_success:
            self.log(f"Successfully deleted: {file_id}")
            return {"message": f"Document {file_id} deleted"}
        else:
            self.log(f"Delete failed: {file_id}")
            return {"error": f"Delete failed for {file_id}"}
    
    def get_documents_list(self):
        self.log("Fetching documents list")
        return get_all_documents()