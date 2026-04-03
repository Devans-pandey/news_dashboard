from fastapi import FastAPI
from pymongo import MongoClient
import os
from collections import defaultdict
from telegram_fetcher import run_fetch

app = FastAPI()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]


@app.get("/")
def home():
    return {"message": "News API running"}


# 🚀 FETCH ENDPOINT
@app.get("/fetch")
def fetch():
    run_fetch()
    return {"status": "fetched"}


# 🚀 TOPICS ENDPOINT
@app.get("/topics")
def get_topics():
    data = list(collection.find())

    grouped = defaultdict(list)

    for item in data:
        topic = item.get("topic", "General News")
        grouped[topic].append(item["text"])

    response = []

    for topic, texts in grouped.items():
        combined_text = " ".join(texts[:5])  # take few messages

        response.append({
            "topic": topic,
            "headline": combined_text[:100],
            "summary": combined_text[:300]
        })

    return response