import requests
import json
import streamlit as st

def get_api_response(question, session_id, model):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "question": question,
        "model": model
    }
    if session_id:
        data["session_id"] = session_id
    selected_sites = st.session_state.get("selected_sites", [])
    if selected_sites:
        data["selected_sites"] = selected_sites
    
    try:
        print(selected_sites)
        if selected_sites:
            forums_search(headers=headers, data=data)
        else:
            print(f"Not searching forums")

        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

def get_api_response_stream(question, session_id, model):
    headers = {
        'accept': 'text/event-stream',
        'Content-Type': 'application/json'
    }
    data = {
        "question": question,
        "model": model,
        "preprocessing_enabled": st.session_state.get("preprocessing_enabled", True),
        "retrieval_enabled": st.session_state.get("retrieval_enabled", True),
        "tools_enabled": st.session_state.get("tools_enabled", False),
    }
    if session_id:
        data["session_id"] = session_id
    selected_sites = st.session_state.get("selected_sites", [])
    if selected_sites:
        data["selected_sites"] = selected_sites

    try:
        if selected_sites:
            forums_search(headers, data)

        resp = requests.post(
            "http://localhost:8000/chat/stream",
            headers=headers,
            json=data,
            stream=True
        )

        if resp.status_code != 200:
            st.error(f"Stream request failed: {resp.status_code} {resp.text}")
            resp.close()
            return

        current_event = None
        while True:
            try:
                raw_line = resp.raw.readline()
            except Exception:
                break
            if not raw_line:
                break
            try:
                line = raw_line.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            if not line:
                continue
            if line.startswith("event: "):
                current_event = line[7:]
            elif line.startswith("data: "):
                payload = json.loads(line[6:])
                if current_event == "done":
                    yield {"session_id": payload["session_id"]}
                elif current_event == "token":
                    yield {"token": payload["token"]}
                elif current_event == "tool_call":
                    yield {"tool_call": payload}
                elif current_event == "tool_result":
                    yield {"tool_result": payload}
                elif current_event == "tool_error":
                    yield {"tool_error": payload}
                current_event = None
    except Exception as e:
        st.error(f"Stream error: {str(e)}")

def forums_search(headers, data):
    print("Parsing forums..." + data["question"])
    try:
        response = requests.post("http://localhost:8000/forums-search", headers=headers, json=data)
        if response.status_code == 200:
            return True
        else:
            st.error(f"Failed to search forums: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None    

def upload_document(file):
    print("Uploading file...")
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post("http://localhost:8000/upload-doc", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload file. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
        return None

def list_documents():
    try:
        response = requests.get("http://localhost:8000/list-docs")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
        return []

def delete_document(file_id):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {"file_id": file_id}
    try:
        response = requests.post("http://localhost:8000/delete-doc", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None

def get_chat_sessions():
    try:
        response = requests.get("http://localhost:8000/chat-sessions")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch chat sessions. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching chat sessions: {str(e)}")
        return []

def get_chat_history(session_id):
    try:
        head = {
            'session_id': session_id
        }
        response = requests.get(f"http://localhost:8000/chat-history", head)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch chat history. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching chat history: {str(e)}")
        return []
