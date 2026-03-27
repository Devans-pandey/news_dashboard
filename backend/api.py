from fastapi import FastAPI
from pymongo import MongoClient
import os

app = FastAPI()

# 🔌 MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI not found")

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]


# 🏠 Health check (VERY IMPORTANT for Render)
@app.get("/")
def home():
    return {"status": "API running 🚀"}


# 📊 Get topics
@app.get("/topics")
def get_topics():
    topics = collection.distinct("topic")

    result = []

    for topic in topics:
        docs = list(
            collection.find({"topic": topic})
            .sort("created_at", -1)
            .limit(5)
        )

        if not docs:
            continue

        latest = docs[0]

        # 🧠 Simple headline & summary (no heavy AI)
        headline = latest.get("text", "")[:80]
        summary = " ".join([d.get("text", "") for d in docs])[:250]

        result.append({
            "topic": topic,
            "topic_name": topic,
            "headline": headline,
            "summary": summary,
            "updates": len(docs),
            "last_updated": latest.get("created_at")
        })

    # 🔥 Sort by latest update (newest first)
    result.sort(key=lambda x: x["last_updated"], reverse=True)

    return result