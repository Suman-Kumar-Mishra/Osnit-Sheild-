import requests
import os
from dotenv import load_dotenv

load_dotenv()


NEWS_API_KEY = os.getenv("NEWS_API_KEY")

INDIA_KEYWORDS = (
    "India OR Kashmir OR LOC OR border OR military "
    "OR infiltration OR BSF OR army OR China border OR Pakistan border"
)


def collect_news():
    records = []

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": INDIA_KEYWORDS,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 30,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code != 200:
            print("NewsAPI error:", response.text)
            return []

        data = response.json()

    except Exception as e:
        print("NewsAPI failed:", e)
        return []

    for article in data.get("articles", []):
        records.append({
            "source": "newsapi",
            "content": article.get("title"),
            "url": article.get("url"),
            "country": "India",
            "metadata": {
                "author": article.get("author"),
                "published_at": article.get("publishedAt"),
                "source_name": article.get("source", {}).get("name")
            }
        })

    return records
