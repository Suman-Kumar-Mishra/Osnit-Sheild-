
import feedparser
import requests

REGIONAL_SOURCES = {
    "Pakistan": [
        "https://www.dawn.com/feeds/home",
        "https://tribune.com.pk/feed"
    ],
    "Bangladesh": [
        "https://bdnews24.com/?widgetName=rssfeed&widgetId=1151&getXmlFeed=true"
    ],
    "Nepal": [
        "https://kathmandupost.com/rss"
    ],
    "Sri Lanka": [
        "http://www.dailymirror.lk/RSS"
    ]
}

KEYWORDS = [
    "India",
    "border",
    "military",
    "Kashmir",
    "LOC",
    "security",
    "army"
]


def collect_regional_rss():

    records = []

    for country, feeds in REGIONAL_SOURCES.items():

        for feed_url in feeds:

            try:
                response = requests.get(feed_url, timeout=8)
                feed = feedparser.parse(response.content)

            except Exception:
                continue

            for entry in feed.entries[:15]:

                title = entry.get("title", "")

                if any(keyword.lower() in title.lower() for keyword in KEYWORDS):

                    records.append({
                        "source": "regional_rss",
                        "content": title,
                        "url": entry.get("link"),
                        "country": country,
                        "metadata": {
                            "feed_url": feed_url,
                            "published": entry.get("published")
                        }
                    })

    return records
