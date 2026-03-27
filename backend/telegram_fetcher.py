from fastapi import FastAPI
from telethon import TelegramClient, events
from pymongo import MongoClient
from datetime import datetime
import asyncio
import os

app = FastAPI()

# 🔌 MongoDB
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI not found")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

# 📡 Telegram API
api_id = 32424333
api_hash = "3fae8215547deff7b0930dbff9870226"

client = TelegramClient('session', api_id, api_hash)

channels = [
    "osinttv",
    "defencesphere",
    "MappingConflicts",
    "dashNewsmy"
]

# 📡 Message handler
@client.on(events.NewMessage(chats=channels))
async def handler(event):
    message = event.message.text

    if not message:
        return

    data = {
        "text": message,
        "date": event.message.date,
        "channel": str(event.chat_id),
        "created_at": datetime.utcnow(),
        "processed": False
    }

    try:
        collection.insert_one(data)

        print("\n✅ SAVED MESSAGE:")
        print(message[:100])
        print("-" * 50)

    except Exception as e:
        print("❌ DB Error:", e)


# 🔁 Background task
async def start_telegram():
    print("🚀 Starting Telegram client...")
    await client.start()
    print("📡 Listening to channels...")
    await client.run_until_disconnected()


# 🚀 Run background on startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_telegram())


# 🏠 Health route (REQUIRED for Render)
@app.get("/")
def home():
    return {"status": "Fetcher running 🚀"}