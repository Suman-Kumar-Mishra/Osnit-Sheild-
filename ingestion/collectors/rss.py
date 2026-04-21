import feedparser
import logging
from ingestion.utils import insert_record

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
]

def collect_rss():
    logging.info("Starting RSS ingestion...")

    inserted = 0

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            content = entry.get("summary") or entry.get("title")

            if not content:
                continue

            success = insert_record(
                source="rss",
                content=content,
                url=entry.get("link"),
                metadata={
                    "feed_source": feed.feed.get("title"),
                    "published": entry.get("published")
                }
            )

            if success:
                inserted += 1

    logging.info(f"RSS inserted: {inserted}")
