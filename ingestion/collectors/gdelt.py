# ingestion/collectors/gdelt.py

import requests
import urllib.parse

def collect_gdelt():
    records = []

    query = "India"
    encoded_query = urllib.parse.quote(query)

    url = (
        "https://api.gdeltproject.org/api/v2/doc/doc?"
        f"query={encoded_query}"
        "&mode=ArtList"
        "&maxrecords=20"
        "&format=json"
    )

    try:
        response = requests.get(url, timeout=30)

        if response.status_code != 200:
            print("GDELT HTTP error:", response.status_code)
            return []

        data = response.json()

    except Exception as e:
        print("GDELT failed:", str(e))
        return []

    for article in data.get("articles", []):
        records.append({
            "source": "gdelt",
            "content": article.get("title"),
            "url": article.get("url"),
            "country": article.get("sourceCountry"),
            "metadata": {
                "domain": article.get("domain"),
                "language": article.get("language"),
                "tone": article.get("tone")
            }
        })

    return records
