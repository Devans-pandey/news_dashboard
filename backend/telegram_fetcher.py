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

    new_count = 0

    for channel in channels:
        print(f"Fetching from {channel}")

        async for message in tg_client.iter_messages(channel, limit=20):
            if not message.text:
                continue

            text = message.text.strip()

            if not text:
                continue

            # 🔥 AI Topic Classification
            topic = classify_topic(text)

            doc = {
                "text": text,
                "channel": channel,
                "message_id": message.id,
                "created_at": datetime.utcnow(),
                "topic": topic,
            }

            # 🔥 Upsert to prevent duplicates — keyed on (channel, message_id)
            result = collection.update_one(
                {"channel": channel, "message_id": message.id},
                {"$setOnInsert": doc},
                upsert=True,
            )

            if result.upserted_id:
                new_count += 1

    print(f"Fetching complete — {new_count} new messages inserted")
    return new_count


def run_fetch():
    return asyncio.run(fetch_messages())