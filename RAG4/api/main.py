# api/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
from pydantic_models import QueryInput, QueryResponse, DocumentInfo, DeleteFileRequest
from agents.coordinator import coordinator
import logging
import json
import io
import wave

logging.basicConfig(filename='app.log', level=logging.INFO)
app = FastAPI()

@app.post("/chat", response_model=QueryResponse)
async def chat(query_input: QueryInput):
    return coordinator.process_chat(query_input)

@app.post("/chat/stream")
async def chat_stream(query_input: QueryInput):
    async def event_generator():
        async for token in coordinator.stream_chat(query_input):
            if token.startswith("[SESSION_ID:"):
                session_id = token.strip("[]").split(":")[1]
                yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"
            elif token.startswith("[TOOL_CALL:"):
                inner = token[len("[TOOL_CALL:"):-1]
                tool, args = inner.split("|", 1)
                yield f"event: tool_call\ndata: {json.dumps({'tool': tool, 'args': args})}\n\n"
            elif token.startswith("[TOOL_RESULT:"):
                inner = token[len("[TOOL_RESULT:"):-1]
                tool, result = inner.split("|", 1)
                yield f"event: tool_result\ndata: {json.dumps({'tool': tool, 'result': result})}\n\n"
            elif token.startswith("[TOOL_ERROR:"):
                inner = token[len("[TOOL_ERROR:"):-1]
                tool, error = inner.split("|", 1)
                yield f"event: tool_error\ndata: {json.dumps({'tool': tool, 'error': error})}\n\n"
            else:
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        yield "event: complete\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

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

@app.get("/tts")
async def text_to_speech(text: str = Query(...), raw: bool = Query(default=False)):
    if coordinator.tts_engine is None:
        raise HTTPException(status_code=503, detail="TTS not available")
    if len(text) < 3:
        text = text.ljust(3)
    audio_chunks = []
    async for chunk in coordinator.tts_engine.speak(text):
        audio_chunks.append(chunk)
    pcm_data = b"".join(audio_chunks)
    if raw:
        return Response(content=pcm_data, media_type="application/octet-stream")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(pcm_data)
    return Response(content=buf.getvalue(), media_type="audio/wav")

@app.get("/config")
async def get_config():
    from llm_provider import load_config
    config = load_config()
    return {
        "tts_enabled": config.get("tts", {}).get("enabled", False),
        "preprocessing_enabled": config.get("preprocessing", {}).get("enabled", True),
    }

@app.get("/")
async def root():
    return {"message": "RAG API Server is running"}
""" sudo fuser -k 8000/tcp """