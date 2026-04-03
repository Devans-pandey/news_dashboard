from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
from collections import defaultdict
from datetime import datetime
from telegram_fetcher import run_fetch
from gemini_summariser import generate_summary_and_title

app = FastAPI(title="News Dashboard API")

# 🔥 CORS — allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]


@app.get("/")
def home():
    return {"message": "News API running"}


# 🚀 FETCH ENDPOINT — trigger Telegram fetch
@app.get("/fetch")
def fetch():
    run_fetch()
    count = collection.count_documents({})
    return {"status": "fetched", "total_messages": count}


# 🚀 STATS ENDPOINT — dashboard statistics
@app.get("/stats")
def get_stats():
    total_messages = collection.count_documents({})
    topics = collection.distinct("topic")
    total_topics = len(topics)

    # get last message timestamp
    last_doc = collection.find_one(sort=[("created_at", -1)])
    last_updated = last_doc.get("created_at") if last_doc else None

    return {
        "total_messages": total_messages,
        "total_topics": total_topics,
        "last_updated": last_updated,
    }


# 🚀 TOPICS ENDPOINT — list all topics with headline + summary
@app.get("/topics")
def get_topics():
    data = list(collection.find())

    # group messages by topic
    grouped = defaultdict(list)
    for item in data:
        topic = item.get("topic", "General News")
        grouped[topic].append(item)

    response = []

    for topic, docs in grouped.items():
        # sort by created_at descending
        docs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

        latest = docs[0]
        count = len(docs)
        texts = [d.get("text", "") for d in docs[:5]]

        # try Gemini for headline + summary
        try:
            headline, summary = generate_summary_and_title(texts)
        except Exception:
            combined = " ".join(texts)
            headline = combined[:100]
            summary = combined[:300]

        response.append({
            "topic": topic,
            "headline": headline,
            "summary": summary,
            "message_count": count,
            "last_updated": latest.get("created_at"),
            "channel": latest.get("channel", "unknown"),
        })

    # sort by message count + recency
    response.sort(
        key=lambda x: (x["message_count"], x.get("last_updated") or datetime.min),
        reverse=True,
    )

    return response


# 🚀 TOPIC DETAIL ENDPOINT — all messages for a specific topic
@app.get("/topics/{topic_name}")
def get_topic_messages(topic_name: str):
    docs = list(
        collection.find({"topic": topic_name}).sort("created_at", -1)
    )

    if not docs:
        return {"topic": topic_name, "messages": [], "count": 0}

    messages = []
    for doc in docs:
        messages.append({
            "text": doc.get("text", ""),
            "channel": doc.get("channel", "unknown"),
            "created_at": doc.get("created_at"),
            "topic": doc.get("topic", "General News"),
        })

    # generate headline + summary for the topic
    texts = [d.get("text", "") for d in docs[:5]]
    try:
        headline, summary = generate_summary_and_title(texts)
    except Exception:
        combined = " ".join(texts)
        headline = combined[:100]
        summary = combined[:300]

    return {
        "topic": topic_name,
        "headline": headline,
        "summary": summary,
        "messages": messages,
        "count": len(messages),
        "last_updated": docs[0].get("created_at") if docs else None,
    }