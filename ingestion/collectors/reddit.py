import praw
import os
from dotenv import load_dotenv
from ingestion.utils import insert_record
import logging

load_dotenv()

def collect_reddit():
    logging.info("Starting Reddit ingestion...")

    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT")
    )

    inserted = 0

    for post in reddit.subreddit("worldnews").new(limit=20):
        success = insert_record(
            source="reddit",
            content=post.title,
            url=post.url,
            metadata={
                "subreddit": post.subreddit.display_name,
                "score": post.score
            }
        )

        if success:
            inserted += 1

    logging.info(f"Reddit inserted: {inserted}")
