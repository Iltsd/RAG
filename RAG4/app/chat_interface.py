import streamlit as st
from api_utils import get_api_response, get_chat_history
import time

def load_chat_history(session_id):
    """Вспомогательная функция для загрузки истории чата."""
    chat_history = get_chat_history(session_id)
    if chat_history:
        return [
            {"role": "U" if msg["role"] == "human" else "assistant", "content": msg["content"]}
            for msg in chat_history
        ]
    return []

def display_chat_interface():
    # Custom CSS with high-contrast loading spinner
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
    </style>
    """, unsafe_allow_html=True)

    # Загрузка истории чата только при первом выборе сессии
    if "show_chat_history" in st.session_state and st.session_state.show_chat_history:
        session_id = st.session_state.session_id
        if session_id and "chat_history_loaded" not in st.session_state:
            with st.spinner("Загрузка истории чата..."):
                st.session_state.messages = load_chat_history(session_id)
                st.session_state.chat_history_loaded = True

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your question..."):
        st.session_state.messages.append({"role": "U", "content": prompt})
        with st.chat_message("U"):
            st.markdown(prompt)

        # High-contrast loading animation
        with st.empty():
            st.markdown("""
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <div class="loading-text">Processing request<span class="pulse-dots"></span></div>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(0.3)
            response = get_api_response(prompt, st.session_state.session_id, st.session_state.model)
            st.empty()

            if response:
                st.session_state.session_id = response.get('session_id')
                st.session_state.messages.append({"role": "assistant", "content": response['answer']})
                with st.chat_message("assistant"):
                    st.markdown(response['answer'])
                    with st.expander("Response Details"):
                        st.markdown("Generated Answer")
                        st.markdown(response['answer'])
                        st.markdown("Model Used")
                        st.markdown(response['model'])
                        st.markdown("Session ID")
                        st.markdown(response['session_id'])
            else:
                st.error("Failed to get a response from the API. Please try again.")

    # Сброс флага загрузки истории при смене чата
    if "chat_history_loaded" in st.session_state and st.session_state.show_chat_history:
        del st.session_state.chat_history_loaded