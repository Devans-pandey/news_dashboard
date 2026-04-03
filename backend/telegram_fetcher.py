import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from pymongo import MongoClient
from datetime import datetime
from topic_classifier import classify_topic

# ENV VARIABLES
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
MONGO_URI = os.getenv("MONGO_URI", "")

# 🔥 String session — survives Render redeploys (no file needed)
# Generate once locally, then store as env var on Render
SESSION_STRING = os.getenv("TELEGRAM_SESSION", "")

# MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

# Channels (IMPORTANT: only usernames, no https)
channels = [
    "osinttv",
    "defencesphere",
    "MappingConflicts",
    "dashNewsmy"
]


async def fetch_messages():
    """Fetch messages from Telegram channels and store in MongoDB."""

    # Use StringSession if available, else fall back to file session
    if SESSION_STRING:
        tg_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        tg_client = TelegramClient("session", API_ID, API_HASH)

    await tg_client.start()

    new_count = 0
    errors = []

    for channel in channels:
        try:
            print(f"📡 Fetching from {channel}...")

            async for message in tg_client.iter_messages(channel, limit=20):
                if not message.text:
                    continue

                text = message.text.strip()
                if not text:
                    continue

                # 🔥 Check if message already exists BEFORE classifying to save API calls
                existing = collection.find_one({"channel": channel, "message_id": message.id})
                if existing:
                    continue  # Skip immediately!

                # 🔥 AI Topic Classification
                try:
                    topic = classify_topic(text)
                except Exception as e:
                    print(f"⚠️ Classifier failed: {e}")
                    topic = "General News"

                doc = {
                    "text": text,
                    "channel": channel,
                    "message_id": message.id,
                    "created_at": datetime.utcnow(),
                    "topic": topic,
                }

                # Insert the completely new message
                collection.insert_one(doc)
                new_count += 1
                print(f"✅ Stored NEW message from {channel}: {text[:30]}...")

        except Exception as e:
            error_msg = f"❌ Error fetching from {channel}: {e}"
            print(error_msg)
            errors.append(error_msg)

    await tg_client.disconnect()

    print(f"✅ Fetching complete — {new_count} new messages inserted")
    return {"new_count": new_count, "errors": errors}


def run_fetch():
    """Run the async fetch — handles both standalone and inside-event-loop cases."""
    try:
        # Check if there's already a running event loop (e.g. inside FastAPI/uvicorn)
        loop = asyncio.get_running_loop()
        # We're inside an existing loop — create a new thread to run it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, fetch_messages()).result()
        return result
    except RuntimeError:
        # No running loop — safe to use asyncio.run directly
        return asyncio.run(fetch_messages())