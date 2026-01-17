# api/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from agents.coordinator import coordinator
import logging

logging.basicConfig(filename='app.log', level=logging.INFO)
app = FastAPI()

@app.post("/chat", response_model=QueryResponse)
async def chat(query_input: QueryInput):
    return coordinator.process_chat(query_input)

@app.post("/forums-search")
async def upload_parsed_document(query_input: QueryInput):
    success = coordinator.forum_agent.process({
        "question": query_input.question,
        "selected_sites": query_input.selected_sites
    })
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to search forums.")
    
    return {"message": "Forum search completed successfully"}

@app.post("/upload-doc")
async def upload_and_index_document(file: UploadFile = File(...)):
    return coordinator.upload_document(file)

@app.get("/list-docs", response_model=list[DocumentInfo])
async def list_documents():
    return coordinator.list_documents()

@app.post("/delete-doc")
async def delete_document(request: DeleteFileRequest):
    return coordinator.delete_document(request.file_id)

@app.get("/chat-sessions")
async def get_chat_sessions():
    return coordinator.get_chat_sessions()

@app.get("/chat-history")
async def get_selected_chat_history(session_id: str):
    return coordinator.get_chat_history(session_id)

@app.get("/")
async def root():
    return {"message": "RAG API Server is running"}
""" sudo fuser -k 8000/tcp """