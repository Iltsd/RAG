import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from chroma_utils import vectorstore

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 2,
    }
)

DEFAULT_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "herta.txt")


def load_system_prompt(path=None):
    if path is None:
        path = DEFAULT_PROMPT_PATH
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return (
            "You are a helpful AI assistant. Use the following context to answer "
            "the user's question. If the context is insufficient, use your own "
            "knowledge to help."
        )


contextualize_q_system_prompt = (
    "You are a strict text pre-processor. Your ONLY job is to resolve "
    "ambiguities in the user's question based on chat history.\n\n"
    "Rules (apply in order):\n"
    "1. If the question contains pronouns (it, they, that, this, these, those) "
    "that clearly refer to something in the chat history, replace the pronoun "
    "with the exact noun phrase from history.\n"
    "2. If the question contains obvious typos (edit distance <= 2 from a real word), "
    "fix the typos.\n"
    "3. If NEITHER rule applies, return the question EXACTLY AS GIVEN.\n"
    "4. NEVER change the topic, intent, or add information not present in the original question.\n"
    "5. NEVER answer the question. Only reformulate if rules 1 or 2 apply.\n\n"
    "Examples:\n"
    "History: 'Python is a programming language'\n"
    "Question: 'What about it?' → 'What about Python?'\n"
    "Question: 'Hw do I sort a lst?' → 'How do I sort a list?'\n"
    "Question: 'How do I sort a list?' → 'How do I sort a list?' (unchanged)\n"
    "Question: 'Tell me more about Python' → 'Tell me more about Python' (unchanged)"
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

persona_prompt = load_system_prompt()

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", persona_prompt),
    ("system", "Context: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])


def get_rag_chain(llm, with_preprocessing=True, retrieval_enabled=True):

    question_answer_chain = create_stuff_documents_chain(
        llm,
        qa_prompt
    )

    if not retrieval_enabled:
        return question_answer_chain

    if with_preprocessing:
        history_aware_retriever = create_history_aware_retriever(
            llm,
            retriever,
            contextualize_q_prompt
        )
        rag_chain = create_retrieval_chain(
            history_aware_retriever,
            question_answer_chain
        )
    else:
        rag_chain = create_retrieval_chain(
            retriever,
            question_answer_chain
        )

    return rag_chain
