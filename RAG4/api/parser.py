from bs4 import BeautifulSoup
import requests
import time
import os


STACKOVERFLOW_KEY = os.getenv("STACKOVERFLOW_KEY", "")


def search_stackoverflow(query: str):
    search_url = "https://api.stackexchange.com/2.3/search/advanced"
    search_params = {
        "order": "desc",
        "sort": "relevance",
        "q": query,
        "site": "stackoverflow",
        "pagesize": 5,
        "filter": "withbody",
    }
    if STACKOVERFLOW_KEY:
        search_params["key"] = STACKOVERFLOW_KEY

    resp = requests.get(search_url, params=search_params)
    if resp.status_code != 200:
        raise Exception(f"Stackoverflow API error: {resp.status_code}")

    data = resp.json()
    combined = []

    for item in data.get("items", []):
        try:
            question_id = item["question_id"]
            title = item.get("title", "")
            link = item.get("link", "")
            question_body = BeautifulSoup(item.get("body", ""), "html.parser").get_text(strip=True)

            answers_url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
            answers_params = {
                "order": "desc",
                "sort": "votes",
                "site": "stackoverflow",
                "filter": "withbody",
                "pagesize": 1,
            }
            if STACKOVERFLOW_KEY:
                answers_params["key"] = STACKOVERFLOW_KEY

            ans_resp = requests.get(answers_url, params=answers_params)
            answer_text = ""
            if ans_resp.status_code == 200:
                ans_data = ans_resp.json()
                if ans_data.get("items"):
                    answer_text = BeautifulSoup(
                        ans_data["items"][0].get("body", ""), "html.parser"
                    ).get_text(strip=True)

            combined.append(
                f"Title: {title}\nLink: {link}\nQuestion: {question_body}\nAnswer: {answer_text}"
            )
        except Exception as e:
            print(f"Stackoverflow error processing item: {e}")

    return combined


def search_habr(query: str):
    search_url = f"https://habr.com/ru/search/?q={query}&target_type=posts&sort=relevance"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    resp = requests.get(search_url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Habr search error: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "lxml")
    articles = []

    for post_tag in soup.find_all("div", class_="tm-article-snippet")[:5]:
        try:
            link_tag = post_tag.find("a", class_="tm-title__link")
            if not link_tag:
                continue
            title = link_tag.text.strip()
            href = "https://habr.com" + link_tag["href"]

            rating_tag = post_tag.find("span", class_="tm-votes-meter__value")
            rating = int(rating_tag.text.strip()) if rating_tag else 0

            art_resp = requests.get(href, headers=headers)
            if art_resp.status_code != 200:
                continue
            art_soup = BeautifulSoup(art_resp.text, "lxml")
            body = art_soup.find("div", id="post-content-body")
            if not body:
                continue
            content = body.get_text(separator="\n", strip=True)
            articles.append({"title": title, "link": href, "content": content, "likes": rating})
        except Exception as e:
            print(f"Habr error processing post: {e}")

    top = sorted(articles, key=lambda x: x["likes"], reverse=True)[:5]
    return [
        f"Title: {a['title']}\nLink: {a['link']}\nLikes: {a['likes']}\nContent: {a['content']}"
        for a in top
    ]


def search_reddit(query: str):
    try:
        import praw
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        if client_id and client_secret:
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent="RAG scraper by showee",
            )
            combined = []
            for submission in reddit.subreddit("all").search(query, sort="relevance", limit=5):
                combined.append(
                    f"Title: {submission.title}\nLink: https://reddit.com{submission.permalink}\n"
                    f"Text: {submission.selftext}\nComments: {submission.num_comments}"
                )
            return combined
    except Exception as e:
        print(f"PRAW failed, falling back to public API: {e}")

    try:
        url = "https://www.reddit.com/r/all/search.json"
        params = {"q": query, "sort": "relevance", "limit": 5}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"Reddit API error: {resp.status_code}, trying old.reddit.com")
            url = f"https://old.reddit.com/r/all/search.json"
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"Reddit API still failing: {resp.status_code}")
                return []

        data = resp.json()
        combined = []
        for item in data.get("data", {}).get("children", []):
            try:
                p = item["data"]
                combined.append(
                    f"Title: {p['title']}\nLink: https://www.reddit.com{p['permalink']}\n"
                    f"Text: {p['selftext']}\nComments: {p['num_comments']}"
                )
            except Exception as e:
                print(f"Reddit error: {e}")
        return combined
    except Exception as e:
        print(f"Reddit search failed: {e}")
        return []


def search_mailru(query: str):
    url = f"https://otvet.mail.ru/search/{query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Mail.ru search error: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "lxml")
    combined = []

    for post in soup.find_all("div", class_="mMhMm")[:5]:
        try:
            link_tag = post.find("a", class_="KFtEM aR6dQ Ub4yk")
            if not link_tag:
                continue
            post_url = "https://otvet.mail.ru" + link_tag["href"]
            post_title = link_tag.get_text(strip=True)

            detail_resp = requests.get(post_url, headers=headers)
            if detail_resp.status_code != 200:
                continue
            detail_soup = BeautifulSoup(detail_resp.text, "lxml")

            question_tag = detail_soup.find("div", class_="aitWd PcSgH")
            answer_tag = detail_soup.find("div", class_="aitWd _Jzbh")
            q_text = question_tag.get_text(strip=True) if question_tag else ""
            a_text = answer_tag.get_text(strip=True) if answer_tag else ""

            combined.append(
                f"Title: {post_title}\nLink: {post_url}\nQuestion: {q_text}\nAnswer: {a_text}"
            )
        except Exception as e:
            print(f"Mail.ru error: {e}")

    return combined


def search_geekforgeeks(query: str):
    search_url = f"https://www.geeksforgeeks.org/search/?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    resp = requests.get(search_url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"GeeksForGeeks search error: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "lxml")
    combined = []

    for item in soup.find_all("div", class_="gcse-title")[:5]:
        try:
            title_tag = item.find("div", class_="article-title")
            if not title_tag:
                continue
            link = title_tag.get("href", "")
            title_text = title_tag.get_text(strip=True)

            art_resp = requests.get(link, headers=headers)
            if art_resp.status_code != 200:
                continue
            art_soup = BeautifulSoup(art_resp.text, "lxml")
            desc = art_soup.find("div", class_="article--viewer_content")
            desc_text = desc.get_text(strip=True) if desc else ""

            combined.append(
                f"Title: {title_text}\nLink: {link}\nDiscription: {desc_text}"
            )
        except Exception as e:
            print(f"GeeksForGeeks error: {e}")

    return combined
