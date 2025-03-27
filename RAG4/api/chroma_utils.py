from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
from typing import List
from langchain_core.documents import Document
from parser import search_stackoverflow

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)

def load_and_split_document(file_path: str) -> List[Document]:
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith('.html'):
        loader = UnstructuredHTMLLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    documents = loader.load()
    return text_splitter.split_documents(documents)

def index_document_to_chroma(file_path: str, file_id: int) -> bool:
    try:
        splits = load_and_split_document(file_path)

        for split in splits:
            split.metadata['file_id'] = file_id

        vectorstore.add_documents(splits)
        return True
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False

def delete_doc_from_chroma(file_id: int):
    try:
        docs = vectorstore.get(where={"file_id": file_id})
        print(f"Found {len(docs['ids'])} document chunks for file_id {file_id}")

        vectorstore._collection.delete(where={"file_id": file_id})
        print(f"Deleted all documents with file_id {file_id}")

        return True
    except Exception as e:
        print(f"Error deleting document with file_id {file_id} from Chroma: {str(e)}")
        return False
    

def process_and_store_texts(question):
    try:
        texts = search_stackoverflow(question)
        print(f"Получено текстов: {len(texts)}")  # Отладка
        
        if not texts:
            print("Нет данных для обработки")
            return False
        
        documents = []
        for text in texts:
            if not isinstance(text, str):
                print(f"Пропущен некорректный элемент: {text}, тип: {type(text)}")
                continue
            chunks = text_splitter.split_text(text)
            print(f"Чанки для текста '{text[:50]}...': {len(chunks)}")  # Отладка
            for i, chunk in enumerate(chunks):
                documents.append(Document(page_content=chunk, metadata={"source": "StackOverflow"}))
        
        if documents:
            vectorstore.add_documents(documents)
            print(f"Добавлено {len(documents)} чанков в ChromaDB")
            return True
        else:
            print("Нет чанков для добавления")
            return False
    except Exception as e:
        print(f"Error indexing document: {e}")
        return False
