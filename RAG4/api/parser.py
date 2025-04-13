from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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
                    combined_text.append(f"Title: {item['title']}\nLink: {item['link']}\nQuestion: {question.get_text()}\nAnswer: {text.get_text(strip=True)}")
                    print(f"Добавлен текст для {url}")  # Отладка
                else:
                    print(f"Не найден текст ответа для {url}")
            else:
                print(f"Не найден блок ответа для {url}")
        except Exception as e:
            print(f"Ошибка при обработке {url}: {e}")
    
    print(f"Итоговый список текстов: {combined_text}")  # Отладка
    return combined_text


def search_habr(query: str):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)

    search_url = f"https://habr.com/ru/search/?q={query}&target_type=posts"
    driver.get(search_url)
    time.sleep(3)  # Подождите, пока страница полностью загрузится

    soup = BeautifulSoup(driver.page_source, 'lxml')
    posts = soup.find_all("li", class_="tm-articles-list__item")

    articles = []
    print(f"Найдено постов: {len(posts)}")

    for post in posts:
        try:
            link_tag = post.find("a", class_="tm-title__link")
            if not link_tag:
                continue

            title = link_tag.text.strip()
            href = "https://habr.com" + link_tag["href"]

            # Парсим количество лайков
            rating_tag = post.find("span", class_="tm-votes-meter__value")
            rating = int(rating_tag.text.strip()) if rating_tag else 0

            # Переходим на страницу статьи
            driver.get(href)
            time.sleep(2)
            article_soup = BeautifulSoup(driver.page_source, "lxml")
            article_body = article_soup.find("div", id="post-content-body")
            if not article_body:
                continue

            content = article_body.get_text(separator="\n", strip=True)
            articles.append({
                "title": title,
                "link": href,
                "content": content,
                "likes": rating
            })

            print(f"Добавлен пост: {title} | 👍 {rating}")
        except Exception as e:
            print(f"Ошибка при обработке поста: {e}")

    driver.quit()

    # Сортировка по лайкам и ограничение до 5
    top_articles = sorted(articles, key=lambda x: x["likes"], reverse=True)[:5]

    combined_text = [
        f"Title: {a['title']}\nLink: {a['link']}\nLikes: {a['likes']}\nContent: {a['content']}"
        for a in top_articles
    ]

    print(f"Выбрано топ-{len(combined_text)} постов по лайкам")
    return combined_text


def search_reddit(query: str):
    url = "https://www.reddit.com/r/all/search.json"
    params = {
        "q": query,
        "sort": "relevance", 
        "limit": 5, 
    }
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Ошибка запроса: {response.status_code}")
    
    data = response.json()
    combined_text = []
    
    print(f"Найдено элементов в API: {len(data['data']['children'])}")  # Отладка
    for item in data["data"]["children"]:
        try:
            post_data = item["data"]
            post_url = f"https://www.reddit.com{post_data['permalink']}"
            post_title = post_data["title"]
            post_text = post_data["selftext"]
            post_comments = post_data["num_comments"]
            
            combined_text.append(f"Title: {post_title}\nLink: {post_url}\nText: {post_text}\nComments: {post_comments}")
            print(f"Добавлен текст для {post_url}")  
        except Exception as e:
            print(f"Ошибка при обработке поста: {e}")
    
    print(f"Итоговый список текстов: {combined_text}") 
    return combined_text

def search_mailru(query: str):
    url = f"https://www.habr.com/search/?q={query}"
    
    soup = BeautifulSoup(url, 'lxml')

    # Ищем посты по data-testid (как в вашем первом примере)
    posts = soup.find_all('div', class_="")
    combined_text = []

    print(f"Найдено элементов в API: {len(posts)}")  # Отладка
    
    print(f"Итоговый список текстов: {combined_text}")  # Отладка
    return combined_text

def search_geekforgeeks(query: str):
    # URL для поиска на GeekForGeeks
    base_url = "https://www.geeksforgeeks.org"
    search_url = f"{base_url}/search/?q={query}"

    # Отправка GET-запроса
    response = requests.get(search_url)

    if response.status_code != 200:
        raise Exception(f"Ошибка запроса: {response.status_code}")

    soup = BeautifulSoup(response.text, 'lxml')

    # Найдем все результаты поиска (передбразуем их в ссылки на статьи)
    search_results = soup.find_all('div', class_='gsc-webResult')

    combined_text = []

    for item in search_results:
        try:
            title = item.find('a', class_='gs-title')
            link = title['href']
            title_text = title.get_text(strip=True)
            
            # Получим описание или вводный текст (если есть)
            description = item.find('div', class_='gs-snippet')
            description_text = description.get_text(strip=True) if description else 'Описание не найдено'

            combined_text.append(f"Title: {title_text}\nLink: {link}\nDescription: {description_text}")
            print(f"Добавлен текст для {link}")  # Отладка
        except Exception as e:
            print(f"Ошибка при обработке элемента: {e}")

    print(f"Итоговый список текстов: {combined_text}")  # Отладка
    return combined_text
