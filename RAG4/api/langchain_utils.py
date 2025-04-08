from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from chroma_utils import vectorstore
from langchain.callbacks import StdOutCallbackHandler  # Для отладки

# Инициализация ретривера с настройками
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 2,  # Количество возвращаемых документов
    }
)

# Промпт для контекстуализации вопроса с учетом истории
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
    "if u have links u should add them after the answer"
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# Промпт для генерации ответа с явным указанием использования контекста
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Use the following context to answer the user's question. "
               "If the context is insufficient, say so and provide a general answer based on your knowledge."),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

def get_rag_chain(model="gpt-4o-mini", verbose=False):

    # Инициализация LLM с опциональными callbacks для отладки
    llm = ChatOllama(
        model=model,
        callbacks=[StdOutCallbackHandler()] if verbose else None
    )
    
    # Создание ретривера с учетом истории
    history_aware_retriever = create_history_aware_retriever(
        llm, 
        retriever, 
        contextualize_q_prompt
    )
    
    # Создание цепочки для ответа на вопрос
    question_answer_chain = create_stuff_documents_chain(
        llm, 
        qa_prompt
    )
    
    # Объединение в RAG-цепочку
    rag_chain = create_retrieval_chain(
        history_aware_retriever, 
        question_answer_chain
    )
    
    return rag_chain
'''
# Пример использования с отладкой
def test_rag_chain(query, chat_history=None):
    """
    Тестирует RAG-цепочку с заданным запросом и историей чата.
    
    Args:
        query (str): Вопрос пользователя.
        chat_history (list): Список сообщений истории чата (опционально).
    """
    if chat_history is None:
        chat_history = []
    
    rag_chain = get_rag_chain(model="llama3.2", verbose=True)  # Включаем отладку
    result = rag_chain.invoke({
        "input": query,
        "chat_history": chat_history
    })
    
    print("Ответ:", result["answer"])
    print("Использованный контекст:")
    for i, doc in enumerate(result.get("context", [])):
        print(f"Документ {i+1}: {doc.page_content[:200]}...")

if __name__ == "__main__":
    # Тестовый запрос
    query = "HTTPS issues"
    chat_history = [
        {"role": "human", "content": "I’m learning Python."},
        {"role": "assistant", "content": "Great! Python is versatile."}
    ]
    test_rag_chain(query, chat_history)'
    '''