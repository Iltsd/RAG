import requests
import streamlit as st

def get_api_response(question, session_id, model):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    data = {
        "question": question,
        "model": model,
        "agent_type": st.session_state.get("agent_type", "rag") 
    }
    if session_id:
        data["session_id"] = session_id
    selected_sites = st.session_state.get("selected_sites", [])
    if selected_sites:
        data["selected_sites"] = selected_sites
    data["agent_type"] = st.session_state.get("agent_type", "rag")
    
    try:
        print(selected_sites)
        if selected_sites:
            forums_search(headers=headers, data=data)
        else:
            print(f"Not searching forums")

        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('audio_file'):
                print(f"Audio file received: {result['audio_file']}")
            return result
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

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