import streamlit as st
from api_utils import upload_document, list_documents, delete_document, get_chat_sessions

def display_sidebar():
    with st.sidebar:
        st.markdown("""
            <h2 style='color: #AFDBF5; text-align: center;'>
                Панель управления
            </h2>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("<h3 style='color: #AFDBF5;'>Выбор модели</h3>", unsafe_allow_html=True)
        model_options = ["llama3.2", "llama3.1", "gpt-4o", "gpt-4o-mini"]
        selected_model = st.selectbox(
            "Выберите модель ИИ",
            options=model_options,
            index=0,
            help="Выберите модель для обработки запросов",
            key="model"
        )

        st.markdown("<h3 style='color: #AFDBF5;'>Источники данных</h3>", unsafe_allow_html=True)
        forums_options = ["Stackoverflow", "Reddit", "Habr", "Mail.ru", "GeekForGeeks",]
        selected_sites = st.multiselect(
            "Выберите платформы",
            options=forums_options,
            default=[],
            help="Выбор платформ для поиска",
            max_selections=2,
            key="selected_sites"  # Уникальный ключ для сохранения в session_state
        )

        st.markdown("---")
        st.markdown("<h3 style='color: #AFDBF5;'>Текущие настройки:</h3>", unsafe_allow_html=True)
        st.write(f"Модель: `{selected_model}`")
        st.write(f"Платформы: {', '.join(selected_sites) if selected_sites else 'Не выбраны'}")

# История чатов
        st.markdown("---")
        st.markdown("<h3 style='color: #AFDBF5;'>История чатов</h3>", unsafe_allow_html=True)
        
        if "show_chat_selector" not in st.session_state:
            st.session_state.show_chat_selector = False

        if st.button("Создать новый чат"):
            print("Новый разговор")
            st.session_state.session_id = None
            st.session_state.show_chat_history = False
            st.session_state.show_chat_selector = False  
            st.session_state.messages = []

        if st.button("Выбрать чат"):
            chat_sessions = get_chat_sessions()
            if chat_sessions:
                st.session_state.show_chat_selector = True
                st.session_state.chat_sessions = chat_sessions  
            else:
                st.write("История чатов пуста или не удалось загрузить.")

        if st.session_state.show_chat_selector:
            chat_sessions = st.session_state.chat_sessions
            session_titles = [session["title"] for session in chat_sessions]
            selected_session_title = st.selectbox(
                "Выберите чат",
                options=session_titles,
                help="Выберите прошлый чат для просмотра",
                key="chat_selector"
            )
            if selected_session_title:
                print(f"Выбранный заголовок: {selected_session_title}")
                selected_session = next(
                    (session for session in chat_sessions if session["title"] == selected_session_title),
                    None
                )
                if selected_session:
                    st.session_state.session_id = selected_session["session_id"]
                    st.session_state.show_chat_history = True 
                    print(f"Установлен session_id: {st.session_state.session_id}")



        # Upload Document и остальной код остаются без изменений
        st.header("Upload Document")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "html"])
        if uploaded_file is not None:
            if st.button("Upload"):
                with st.spinner("Uploading..."):
                    upload_response = upload_document(uploaded_file)
                    if upload_response:
                        st.success(f"File '{uploaded_file.name}' uploaded successfully with ID {upload_response['file_id']}.")
                        st.session_state.documents = list_documents()

        st.header("Uploaded Documents")
        if st.button("Refresh Document List"):
            with st.spinner("Refreshing..."):
                st.session_state.documents = list_documents()

        if "documents" not in st.session_state:
            st.session_state.documents = list_documents()

        documents = st.session_state.documents
        if documents:
            for doc in documents:
                st.text(f"{doc['filename']} (ID: {doc['id']}, Uploaded: {doc['upload_timestamp']})")
            selected_file_id = st.selectbox(
                "Select a document to delete",
                options=[doc['id'] for doc in documents],
                format_func=lambda x: next(doc['filename'] for doc in documents if doc['id'] == x)
            )
            if st.button("Delete Selected Document"):
                with st.spinner("Deleting..."):
                    delete_response = delete_document(selected_file_id)
                    if delete_response:
                        st.success(f"Document with ID {selected_file_id} deleted successfully.")
                        st.session_state.documents = list_documents()
                    else:
                        st.error(f"Failed to delete document with ID {selected_file_id}.")