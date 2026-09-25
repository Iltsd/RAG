import streamlit as st
import requests
import io
import wave
import time
from api_utils import get_api_response_stream, get_chat_history

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
from utils import strip_markdown

def load_chat_history(session_id):
    chat_history = get_chat_history(session_id)
    if chat_history:
        return [
            {"role": "U" if msg["role"] == "human" else "assistant", "content": msg["content"]}
            for msg in chat_history
        ]
    return []

def display_chat_interface():
    st.markdown("""
    <style>
        /* High-contrast gradient spinner */
        @keyframes spin {
            0% { 
                transform: rotate(0deg);
                border-top-color: #00d2ff;
                border-right-color: #3a7bd5;
                border-bottom-color: #00d2ff;
                border-left-color: #3a7bd5;
            }
            25% {
                border-top-color: #3a7bd5;
                border-right-color: #00d2ff;
                border-bottom-color: #3a7bd5;
                border-left-color: #00d2ff;
            }
            50% {
                border-top-color: #00d2ff;
                border-right-color: #3a7bd5;
                border-bottom-color: #00d2ff;
                border-left-color: #3a7bd5;
            }
            75% {
                border-top-color: #3a7bd5;
                border-right-color: #00d2ff;
                border-bottom-color: #3a7bd5;
                border-left-color: #00d2ff;
            }
            100% { 
                transform: rotate(360deg);
                border-top-color: #00d2ff;
                border-right-color: #3a7bd5;
                border-bottom-color: #00d2ff;
                border-left-color: #3a7bd5;
            }
        }
        
        .loading-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .loading-spinner {
            width: 65px;
            height: 65px;
            border: 7px solid;
            border-radius: 50%;
            animation: spin 1.2s linear infinite;
            margin-bottom: 15px;
            box-shadow: 0 0 20px rgba(58, 123, 213, 0.4);
            position: relative;
            filter: brightness(1.1);
        }
        
        .loading-spinner::before {
            content: '';
            position: absolute;
            top: -7px;
            left: -7px;
            right: -7px;
            bottom: -7px;
            border: 7px solid transparent;
            border-radius: 50%;
            border-top-color: rgba(0, 210, 255, 0.3);
            border-right-color: rgba(58, 123, 213, 0.3);
            animation: spin 2.5s linear infinite reverse;
        }
        
        .loading-spinner::after {
            content: '';
            position: absolute;
            top: -14px;
            left: -14px;
            right: -14px;
            bottom: -14px;
            border: 7px solid transparent;
            border-radius: 50%;
            border-bottom-color: rgba(0, 210, 255, 0.2);
            border-left-color: rgba(58, 123, 213, 0.2);
            animation: spin 4s linear infinite;
        }
        
        .loading-text {
            color: #3a7bd5;
            font-size: 1.1em;
            font-weight: 600;
            text-align: center;
            margin-top: 15px;
            text-shadow: 0 0 8px rgba(0, 210, 255, 0.3);
            animation: textPulse 1.8s ease-in-out infinite;
        }
        
        @keyframes textPulse {
            0% { 
                opacity: 0.9;
                text-shadow: 0 0 8px rgba(0, 210, 255, 0.3);
            }
            50% { 
                opacity: 1;
                text-shadow: 0 0 12px rgba(0, 210, 255, 0.5);
                color: #00d2ff;
            }
            100% { 
                opacity: 0.9;
                text-shadow: 0 0 8px rgba(0, 210, 255, 0.3);
            }
        }
        
        .pulse-dots::after {
            content: '...';
            animation: dotPulse 1.8s steps(5, end) infinite;
        }
        
        @keyframes dotPulse {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
                
        .chat-bubble {
            padding: 12px 16px;
            margin: 10px 0;
            border-radius: 18px;
            max-width: 90%;
            word-wrap: break-word;
            line-height: 1.5;
        }
        .user-message {
            background: linear-gradient(to right, #3165b3, #3165b3);
            align-self: flex-end;
            border: 1px solid #3a7bd5;
            box-shadow: 0 0 16px rgba(0, 204, 255, 0.3);
        }
        .assistant-message {
            background: linear-gradient(to right, #3165b3, #3165b3);
            border: 1px solid #3a7bd5;
            box-shadow: 0 0 16px rgba(100, 116, 139, 0.2);
        }
        .chat-container {
            display: flex;
            flex-direction: column;
        }
        .chat-header {
            text-align: center;
            font-size: 4em;
            font-weight: bold;
            color: #3a7bd5;
            text-shadow: 0 0 12px rgba(0, 210, 255, 0.4);
            margin-bottom: 42px;
        }
        .stTextInput > div > input {
            background-color: #3a7bd5;
            border: 1px solid #38bdf8;
            border-radius: 16px;
            padding: 14px;
            box-shadow: 0 0 4px rgba(56, 189, 248, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='chat-header'>For&Com Chatbot</div>", unsafe_allow_html=True)

    if "show_chat_history" in st.session_state and st.session_state.show_chat_history:
        session_id = st.session_state.session_id
        if session_id and "chat_history_loaded" not in st.session_state:
            with st.spinner("Загрузка истории чата..."):
                st.session_state.messages = load_chat_history(session_id)
                st.session_state.chat_history_loaded = True

    audio_placeholder = st.empty()

    def _fetch_tts(delta):
        try:
            resp = requests.get("http://localhost:8000/tts", params={"text": delta, "raw": True}, timeout=10)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            pass
        return None

    def _play_pcm(pcm):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(pcm)
        audio_placeholder.audio(buf.getvalue(), format="audio/wav", autoplay=True)

    def _play_tts(text):
        if not st.session_state.get("tts_enabled", True):
            return
        spoken = st.session_state.get("tts_spoken_until", 0)
        delta = text[spoken:]
        if not delta.strip():
            return
        st.session_state.tts_spoken_until = len(text)
        cleaned = strip_markdown(delta)
        pcm = _fetch_tts(cleaned)
        if pcm is None:
            return
        now = time.time()
        playing_until = st.session_state.get("tts_playing_until", 0)
        if now < playing_until:
            st.session_state.setdefault("tts_queue", []).append((pcm, len(pcm) / 44100))
            return
        st.session_state.tts_playing_until = now + len(pcm) / 44100
        _play_pcm(pcm)

    def _flush_tts():
        queue = st.session_state.get("tts_queue", [])
        st.session_state.tts_queue = []
        for pcm, duration in queue:
            st.session_state.tts_playing_until = time.time() + duration
            _play_pcm(pcm)
            time.sleep(duration)

    for i, message in enumerate(st.session_state.messages):
        role_class = "user-message" if message["role"] == "U" else "assistant-message"
        if message["role"] == "U":
            st.markdown(
                f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>",
                unsafe_allow_html=True
            )
        else:
            col1, col2 = st.columns([0.95, 0.05])
            with col1:
                st.markdown(
                    f"<div class='chat-container'><div class='chat-bubble {role_class}'>{message['content']}</div></div>",
                    unsafe_allow_html=True
                )
            if st.session_state.get("tts_enabled", True):
                with col2:
                    if st.button("🔊", key=f"tts_{i}", help="Озвучить ответ"):
                        cleaned = strip_markdown(message["content"])
                        try:
                            resp = requests.get("http://localhost:8000/tts", params={"text": cleaned, "raw": True})
                            if resp.status_code == 200:
                                buf = io.BytesIO()
                                with wave.open(buf, "wb") as wf:
                                    wf.setnchannels(1)
                                    wf.setsampwidth(2)
                                    wf.setframerate(22050)
                                    wf.writeframes(resp.content)
                                audio_placeholder.audio(buf.getvalue(), format="audio/wav", autoplay=True)
                        except Exception:
                            pass

    if prompt := st.chat_input("Введите ваш вопрос..."):
        st.session_state.messages.append({"role": "U", "content": prompt})
        st.session_state.tts_spoken_until = 0
        st.session_state.tts_queue = []

        response_text = ""
        message_placeholder = st.empty()
        first_token = True
        tts_char_counter = 0
        TTS_CHAR_THRESHOLD = 50

        tool_messages = []

        for event in get_api_response_stream(prompt, st.session_state.session_id, st.session_state.model):
            if "token" in event:
                response_text += event["token"]
                message_placeholder.markdown(
                    f"<div class='chat-container'><div class='chat-bubble assistant-message'>{response_text}</div></div>",
                    unsafe_allow_html=True
                )
                if st.session_state.get("tts_enabled", True):
                    tts_char_counter += len(event["token"])
                    if first_token or tts_char_counter >= TTS_CHAR_THRESHOLD:
                        _play_tts(response_text)
                        first_token = False
                        tts_char_counter = 0
            elif "session_id" in event:
                st.session_state.session_id = event["session_id"]
            elif "tool_call" in event:
                tc = event["tool_call"]
                tool_messages.append(f"🔧 **{tc['tool']}**({tc['args']})...")
                message_placeholder.markdown(
                    "<br>".join(tool_messages) + "<br>" +
                    f"<div class='chat-container'><div class='chat-bubble assistant-message'>{response_text}</div></div>",
                    unsafe_allow_html=True
                )
            elif "tool_result" in event:
                tr = event["tool_result"]
                tool_messages.append(f"✅ **{tr['tool']}** → {tr['result'][:100]}")
                message_placeholder.markdown(
                    "<br>".join(tool_messages) + "<br>" +
                    f"<div class='chat-container'><div class='chat-bubble assistant-message'>{response_text}</div></div>",
                    unsafe_allow_html=True
                )
            elif "tool_error" in event:
                te = event["tool_error"]
                tool_messages.append(f"❌ **{te['tool']}** — {te['error'][:100]}")
                message_placeholder.markdown(
                    "<br>".join(tool_messages) + "<br>" +
                    f"<div class='chat-container'><div class='chat-bubble assistant-message'>{response_text}</div></div>",
                    unsafe_allow_html=True
                )

        if response_text:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            if st.session_state.get("tts_enabled", True):
                _flush_tts()

    if "chat_history_loaded" in st.session_state and st.session_state.show_chat_history:
        del st.session_state.chat_history_loaded
