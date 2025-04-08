from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver




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

def search_reddit(query: str):
    driver = webdriver.Chrome()  # Установите ChromeDriver
    url = f"https://www.reddit.com/search/?q={query}"
    driver.get(url)
    time.sleep(3)  # Ждем загрузки контента
    
    soup = BeautifulSoup(driver.page_source, 'lxml')
    driver.quit()
    
    # Ищем посты по data-testid (как в вашем первом примере)
    posts = soup.find_all('a', attrs={"data-testid": "post-title-text"})
    combined_text = []
    
    # Находим все посты на странице поиска
    posts = soup.find_all('div', class_="text-16 xs:text-18 text-neutral-content-strong no-underline hover:no-underline visited:text-neutral-content-weak hover:no line-clamp-3 text-ellipsis font-semibold mb-xs")  # Класс может отличаться, нужно проверить актуальность
    print(posts)
    print(f"Найдено элементов в API: {len(posts)}")  # Отладка
    '''
    for post in posts[:5]:  # Ограничиваем до 5 постов, как в StackOverflow
        try:
            # Извлекаем заголовок
            title_elem = post.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            
            # Извлекаем текст поста (если есть)
            content_elem = post.find('div', class_="s-prose")  # Класс может отличаться
            content = content_elem.get_text(strip=True) if content_elem else "No content"
            
            # Извлекаем ссылку на пост
            link_elem = post.find('a', href=True)
            post_url = "https://www.reddit.com" + link_elem['href'] if link_elem else None
            
            if post_url:
                # Запрос к полной странице поста для получения комментариев
                post_response = requests.get(post_url, headers=headers)
                if post_response.status_code != 200:
                    print(f"Не удалось загрузить страницу {post_url}")
                    continue
                
                post_soup = BeautifulSoup(post_response.text, 'lxml')
                # Находим лучший комментарий (например, первый с высоким рейтингом)
                top_comment_elem = post_soup.find('div', class_="Comment")  # Класс может отличаться
                top_comment = top_comment_elem.get_text(strip=True) if top_comment_elem else "No comments"
                
                if content or top_comment:
                    combined_text.append(f"Title: {title}\nPost: {content}\nTop Comment: {top_comment}")
                    print(f"Добавлен текст для {post_url}")  # Отладка
                else:
                    print(f"Не найден текст поста или комментариев для {post_url}")
            else:
                print(f"Не найдена ссылка для поста с заголовком: {title}")
        except Exception as e:
            print(f"Ошибка при обработке поста: {e}")
    '''
    print(f"Итоговый список текстов: {combined_text}")  # Отладка
    return combined_text