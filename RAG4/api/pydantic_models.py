from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class ModelName(str, Enum):
    GPT4_O = "gpt-4o"
    GPT4_O_MINI = "gpt-4o-mini"
    LLAMA3_2 = "llama3.2"
    LLAMA3_1 = "llama3.1"

class QueryInput(BaseModel):
    question: str
    session_id: Optional[str] = None
    model: ModelName = ModelName.LLAMA3_2
    selected_sites: Optional[List[str]] = None
    agent_type: Optional[str] = "rag"

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    model: ModelName
    audio_file: Optional[str] = None  # Fixed: Make optional

class DocumentInfo(BaseModel):
    id: int
    filename: str
    upload_timestamp: datetime

class DeleteFileRequest(BaseModel):
    file_id: int