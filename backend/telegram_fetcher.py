from telethon import TelegramClient, events
from pymongo import MongoClient
from datetime import datetime
import time
import os

# 🔌 MongoDB connection (use env variable in Render)
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("❌ MONGO_URI not found in environment variables")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

# 📡 Telegram API credentials (YOURS)
api_id = 32424333
api_hash = "3fae8215547deff7b0930dbff9870226"

# 📡 Telegram client
client = TelegramClient('session', api_id, api_hash, auto_reconnect=True)

# 📢 Channels to monitor
channels = [
    "osinttv",
    "defencesphere",
    "MappingConflicts",
    "dashNewsmy"
]

print("🚀 Starting Telegram Fetcher...")

# 🔄 Message handler (NO AI — only raw storage)
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

        # 🔥 IMPORTANT FLAGS
        "processed": False,   # worker will process later
        "topic": None,
        "topic_name": None,
        "headline": None,
        "summary": None
    }

    try:
        collection.insert_one(data)

        print("\n✅ NEW MESSAGE SAVED:")
        print(message[:100])
        print("-" * 50)

    except Exception as e:
        print("❌ DB Error:", e)


# 🚀 MAIN LOOP (auto reconnect)
def main():
    while True:
        try:
            print("📡 Listening to Telegram channels...\n")
            client.start()
            client.run_until_disconnected()

        except Exception as e:
            print("❌ Error:", e)
            print("🔄 Reconnecting in 5 seconds...\n")
            time.sleep(5)


# ▶️ Run
if __name__ == "__main__":
    main()