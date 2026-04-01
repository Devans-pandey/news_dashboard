from telethon import TelegramClient
from pymongo import MongoClient
from datetime import datetime
import os
import asyncio

# ENV variables
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
MONGO_URI = os.getenv("MONGO_URI")

# Telegram client
client = TelegramClient('session', API_ID, API_HASH)

# MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

# Channels (add more later)
channels = ["your_dummy_channel"]


async def fetch_messages():
    print("Fetching messages from Telegram...")

    await client.start()

    for channel in channels:
        async for message in client.iter_messages(channel, limit=30):
            if message.text:

                data = {
                    "text": message.text,
                    "date": message.date,
                    "channel": channel,
                    "created_at": datetime.utcnow(),
                    "topic": "general"   # we improve later
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