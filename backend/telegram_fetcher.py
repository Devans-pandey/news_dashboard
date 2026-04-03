import os
import asyncio
from telethon import TelegramClient
from pymongo import MongoClient
from datetime import datetime
from topic_classifier import classify_topic

# ENV VARIABLES
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# Telegram client (session file must exist)
tg_client = TelegramClient("session", API_ID, API_HASH)

# Channels (IMPORTANT: only usernames, no https)
channels = [
    "osinttv",
    "defencesphere",
    "MappingConflicts",
    "dashNewsmy"
]

async def fetch_messages():
    await tg_client.start()

    for channel in channels:
        print(f"Fetching from {channel}")

        async for message in tg_client.iter_messages(channel, limit=20):
            if not message.text:
                continue

            text = message.text.strip()

            # 🔥 AI Topic Classification
            topic = classify_topic(text)

            doc = {
                "text": text,
                "channel": channel,
                "created_at": datetime.utcnow(),
                "topic": topic
            }

            collection.insert_one(doc)

    print("Fetching complete")


def run_fetch():
    asyncio.run(fetch_messages())