import streamlit as st
from sidebar import display_sidebar
from chat_interface import display_chat_interface

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "preprocessing_enabled" not in st.session_state:
    st.session_state.preprocessing_enabled = True

if "tts_enabled" not in st.session_state:
    st.session_state.tts_enabled = True

if "pending_tts" not in st.session_state:
    st.session_state.pending_tts = None

if "retrieval_enabled" not in st.session_state:
    st.session_state.retrieval_enabled = True

if "tools_enabled" not in st.session_state:
    st.session_state.tools_enabled = False

if "tts_spoken_until" not in st.session_state:
    st.session_state.tts_spoken_until = 0

if "tts_playing_until" not in st.session_state:
    st.session_state.tts_playing_until = 0

if "tts_queue" not in st.session_state:
    st.session_state.tts_queue = []

display_sidebar()

display_chat_interface()
