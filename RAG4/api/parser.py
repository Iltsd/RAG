from bs4 import BeautifulSoup
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.documents import Document

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
model = SentenceTransformer("all-MiniLM-L6-v2")

vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)

from bs4 import BeautifulSoup
import requests

def search_stackoverflow(query: str):
    url = "https://api.stackexchange.com/2.3/search/advanced"
    params = {
        "order": "desc",
        "sort": "relevance",
        "q": query,
        "site": "stackoverflow",
        "pagesize": 5,
    }
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Ошибка запроса: {response.status_code}")
    
    data = response.json()
    combined_text = []
    
    print(f"Найдено элементов в API: {len(data['items'])}")  # Отладка
    for item in data["items"][:len(data['items'])]:
        try:
            url = item["link"]
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Не удалось загрузить страницу {url}")
                continue
            
            soup = BeautifulSoup(response.text, 'lxml')
            question = soup.find('div', class_="s-prose js-post-body")
            right_answer = soup.find('div', class_="answercell post-layout--right")
            
            if right_answer:
                text = right_answer.find('div', class_="s-prose js-post-body")
                if text and text.get_text(strip=True):
                    combined_text.append(f"Title: {item['title']}\nQuestion: {question.get_text()}\nAnswer: {text.get_text(strip=True)}")
                    print(f"Добавлен текст для {url}")  # Отладка
                else:
                    print(f"Не найден текст ответа для {url}")
            else:
                print(f"Не найден блок ответа для {url}")
        except Exception as e:
            print(f"Ошибка при обработке {url}: {e}")
    
    print(f"Итоговый список текстов: {combined_text}")  # Отладка
    return combined_text