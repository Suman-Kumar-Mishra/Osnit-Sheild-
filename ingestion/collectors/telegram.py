# ingestion/collectors/telegram.py

import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

CHANNELS = [
    "DawnNews",        # Pakistan
    "ARYNEWSOFFICIAL",   # Pakistan
    "IndiaToday",        # India
    "timesofindia",      # India
    "WIONews",           # India international focus
]

KEYWORDS = [
    "India",
    "Kashmir",
    "border",
    "Delhi",
    "Punjab",
    "military"
]

async def collect_telegram_async():
    if not API_ID or not API_HASH:
        print("Telegram credentials missing")
        return []

    records = []

    async with TelegramClient("osnit_session", int(API_ID), API_HASH) as client:
        for channel in CHANNELS:
            try:
                async for message in client.iter_messages(channel, limit=50):
                    if message.text:
                        text = message.text.lower()
                        if any(k.lower() in text for k in KEYWORDS):
                            records.append({
                                "source": f"telegram_{channel}",
                                "content": message.text,
                                "url": None,
                                "country": "external",
                                "metadata": {
                                    "channel": channel,
                                    "date": str(message.date)
                                }
                            })
            except Exception as e:
                print("Telegram error:", e)

    return records

def collect_telegram():
    return asyncio.run(collect_telegram_async())
