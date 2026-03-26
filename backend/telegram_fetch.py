from telethon import TelegramClient, events
from pymongo import MongoClient
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import time
import spacy
import os
import threading

# 🔥 FASTAPI (for Render port requirement)
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"status": "telegram fetch running"}


# 🔤 NLP
nlp = spacy.load("en_core_web_sm")

# 🤖 embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# 🔌 MongoDB
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

# 🤖 headline generator
headline_generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

# 🔍 Find topic using similarity
def find_topic(message):
    new_emb = model.encode(message)

    recent = list(collection.find().sort("created_at", -1).limit(100))

    best_score = 0
    best_topic = None

    for doc in recent:
        if "embedding" not in doc:
            continue

        old_emb = doc["embedding"]
        score = cosine_similarity([new_emb], [old_emb])[0][0]

        if score > best_score:
            best_score = score
            best_topic = doc.get("topic")

    if best_score > 0.4 and best_topic:
        return best_topic, new_emb
    else:
        return f"Topic_{int(time.time())}", new_emb


# 🧠 Smart topic naming
def generate_topic_name(text):
    prompt = f"""
    Generate a short news headline (max 8 words).

    Rules:
    - Do NOT use "X vs Y"
    - Capture the main event
    - Use proper country/entity names

    Text:
    {text}
    """

    try:
        result = headline_generator(
            prompt,
            max_length=30,
            do_sample=False
        )[0]['generated_text']

        return result.strip()

    except:
        return "Breaking news"


# 📡 TELEGRAM CONFIG
api_id = int(os.getenv("TELEGRAM_API_ID"))
api_hash = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient('session', api_id, api_hash, auto_reconnect=True)

channels = ["osinttv", "defencesphere", "MappingConflicts", "goreunit", "dashNewsmy"]


# 🔄 MESSAGE HANDLER
@client.on(events.NewMessage(chats=channels))
async def handler(event):
    message = event.message.text

    if not message:
        return

    topic, embedding = find_topic(message)
    topic_name = generate_topic_name(message)

    data = {
        "text": message,
        "date": event.message.date,
        "channel": str(event.chat_id),
        "created_at": datetime.utcnow(),
        "topic": topic,
        "topic_name": topic_name,
        "embedding": embedding.tolist()
    }

    # 🔥 avoid duplicates
    collection.update_one(
        {"text": message},
        {"$setOnInsert": data},
        upsert=True
    )

    print(f"✅ Saved: {topic_name}")


# 🚀 TELEGRAM LISTENER FUNCTION
def start_telegram():
    while True:
        try:
            print("🚀 Starting Telegram listener...")
            client.start()
            client.run_until_disconnected()
        except Exception as e:
            print("❌ Telegram error:", e)
            time.sleep(5)


# 🚀 MAIN ENTRY
if __name__ == "__main__":
    # Run telegram in background
    threading.Thread(target=start_telegram, daemon=True).start()

    # Start FastAPI server (required by Render)
    uvicorn.run(app, host="0.0.0.0", port=10000)