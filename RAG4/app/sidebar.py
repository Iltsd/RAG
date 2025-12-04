import streamlit as st
from api_utils import upload_document, list_documents, delete_document, get_chat_sessions

def display_sidebar():
    with st.sidebar:
        st.markdown("""
                    <div style='color: #3a7bd5; text-align: center; font-size: 30px; font-weight: bold;'>
                    Панель управления
                    </div>
        """, unsafe_allow_html=True)


        st.markdown("---")

        st.markdown("<h1 style='color: #3a7bd5;'>Выбор модели</h1>", unsafe_allow_html=True)
        model_options = ["llama3.2", "llama3.1"]
        selected_model = st.selectbox(
            "Выберите модель ИИ",
            options=model_options,
            index=0,
            help="Выберите модель для обработки запросов",
            key="model"
        )

        agent_options = ["rag", "summarizer"]
        selected_agent = st.selectbox(
        "Выберите тип агента",
        options=agent_options,
        index=0,
        key="agent_type"
)

        st.markdown("<h1 style='color: #3a7bd5;'>Источники данных</h1>", unsafe_allow_html=True)
        forums_options = ["Stackoverflow", "Reddit", "Habr"]
        selected_sites = st.multiselect(
            "Выберите платформы",
            options=forums_options,
            default=None,
            help="Выбор платформ для поиска",
            max_selections=2,
            key="selected_sites"  
        )

        st.markdown("---")
        st.markdown("<h1 style='color: #3a7bd5;'>Текущие настройки:</h1>", unsafe_allow_html=True)
        st.write(f"Модель: `{selected_model}`")
        st.write(f"Платформы: {', '.join(selected_sites) if selected_sites else 'Не выбраны'}")

        st.markdown("---")
        st.markdown("<h1 style='color: #3a7bd5;'>История чатов</h1>", unsafe_allow_html=True)
        
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

        st.markdown("---")
        st.markdown("<h1 style='color: #3a7bd5;'>Загрузка документов</h1>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Выберите файл для загрузки", type=["pdf", "docx", "html"])

        if uploaded_file is not None:
            if st.button("Загрузить файл"):
                with st.spinner("Загрузка..."):
                    upload_response = upload_document(uploaded_file)
                    if upload_response:
                        st.success(f"Файл **{uploaded_file.name}** загружен. ID: `{upload_response['file_id']}`")
                        st.session_state.documents = list_documents()
                    else:
                        st.error("Ошибка при загрузке файла.")

        st.markdown("<h1 style='color: #3a7bd5;'>Загруженные документы</h1>", unsafe_allow_html=True)

        if st.button("Обновить список документов"):
            with st.spinner("Обновление..."):
                st.session_state.documents = list_documents()

        if "documents" not in st.session_state:
            st.session_state.documents = list_documents()

        documents = st.session_state.documents
        if documents:
            st.markdown("<ul style='font-size: 0.9em;'>", unsafe_allow_html=True)
            for doc in documents:
                st.markdown(
                    f"<li><b>{doc['filename']}</b> — <i>{doc['upload_timestamp']}</i><br>"
                    f"ID: <code>{doc['id']}</code></li>",
                    unsafe_allow_html=True
                )
            st.markdown("</ul>", unsafe_allow_html=True)

            selected_file_id = st.selectbox(
                "Выберите документ для удаления",
                options=[doc['id'] for doc in documents],
                format_func=lambda x: next(doc['filename'] for doc in documents if doc['id'] == x)
            )

            if st.button("Удалить выбранный документ"):
                with st.spinner("Удаление..."):
                    delete_response = delete_document(selected_file_id)
                    if delete_response:
                        st.success(f"Документ с ID `{selected_file_id}` удалён.")
                        st.session_state.documents = list_documents()
                    else:
                        st.error(f"Не удалось удалить документ с ID `{selected_file_id}`.")
