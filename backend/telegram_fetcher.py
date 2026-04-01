from telethon import TelegramClient
from pymongo import MongoClient
from datetime import datetime
import os
import asyncio

# ENV variables (SAFE)
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
MONGO_URI = os.getenv("MONGO_URI", "")

# MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

# Channels
channels = ["your_dummy_channel"]  # change later


def get_client():
    return TelegramClient('session', API_ID, API_HASH)


async def fetch_messages():
    print("Fetching messages...")

    client = get_client()
    await client.start()

    for channel in channels:
        async for message in client.iter_messages(channel, limit=30):
            if message.text:

                data = {
                    "text": message.text,
                    "date": message.date,
                    "channel": channel,
                    "created_at": datetime.utcnow(),
                    "topic": "general"
                }

                # Avoid duplicates
                collection.update_one(
                    {"text": message.text},
                    {"$set": data},
                    upsert=True
                )

    print("Fetch completed.")


def run_fetch():
    asyncio.run(fetch_messages())