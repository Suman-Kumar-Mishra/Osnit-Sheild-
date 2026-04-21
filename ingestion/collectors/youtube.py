# ingestion/collectors/youtube.py

from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def collect_youtube():
    if not YOUTUBE_API_KEY:
        print("YOUTUBE_API_KEY missing")
        return []

    records = []

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        request = youtube.search().list(
            q="India border OR Kashmir OR military",
            part="snippet",
            maxResults=20,
            type="video"
        )

        response = request.execute()

    except Exception as e:
        print("YouTube error:", e)
        return []

    for item in response.get("items", []):
        records.append({
            "source": "youtube",
            "content": item["snippet"]["title"],
            "url": f"https://youtube.com/watch?v={item['id']['videoId']}",
            "country": "unknown",
            "metadata": {
                "channel": item["snippet"]["channelTitle"],
                "published_at": item["snippet"]["publishedAt"]
            }
        })

    return records
