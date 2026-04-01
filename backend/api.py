from fastapi import FastAPI
from pymongo import MongoClient
import os

from gemini_summariser import generate_summary_and_title

app = FastAPI()

# DEBUG (remove later)
print("FILES:", os.listdir())
print("API STARTING...")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]


# 🔹 Root
@app.get("/")
def home():
    return {"status": "API running"}


# 🔹 Fetch (IMPORTANT: lazy import)
@app.get("/fetch")
def fetch():
    from telegram_fetcher import run_fetch
    run_fetch()
    return {"status": "fetched successfully"}


# 🔹 Topics
@app.get("/topics")
def get_topics():
    topics = []
    grouped = {}

    for msg in collection.find().sort("date", -1).limit(100):
        topic = msg.get("topic", "general")

        if topic not in grouped:
            grouped[topic] = []

        grouped[topic].append(msg["text"])

    for topic, messages in grouped.items():
        title, summary = generate_summary_and_title(messages)

        topics.append({
            "topic": topic,
            "headline": title,
            "summary": summary
        })

    return topics