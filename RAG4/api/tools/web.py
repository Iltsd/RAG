import requests
from langchain_core.tools import tool


@tool
def fetch_url(url: str) -> str:
    """Fetch the text content of a URL. Use this to browse the web or API documentation."""
    try:
        resp = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (compatible; HertaBot/1.0)"
        })
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                return resp.text
            return resp.text
        return f"Error: HTTP {resp.status_code}"
    except requests.Timeout:
        return "Error: Request timed out after 10 seconds"
    except Exception as e:
        return f"Error: {e}"
