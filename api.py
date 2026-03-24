from fastapi import FastAPI
from pymongo import MongoClient
import os
import requests
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

app = FastAPI()

# 🌐 CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI not found in environment variables")

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]


# 🔥 AI SUMMARY FUNCTION
def generate_ai_summary(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

    headers = {
        "Authorization": f"Bearer {os.getenv('HF_API_KEY')}"
    }

    # 🔥 limit text size
    text = text[:2000]

    payload = {
        "inputs": f"Summarize the following news updates into a clear, concise 2-3 sentence summary:\n\n{text}",
        "parameters": {
            "max_length": 120,
            "min_length": 40
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            return response.json()[0]["summary_text"]

        return text[:200]

    except Exception as e:
        print("AI Error:", e)
        return text[:200]


# 🏠 Health check
@app.get("/")
def home():
    return {"status": "API is running 🚀"}


# 🔥 MAIN: Get all topics
@app.get("/topics")
def get_topics():
    topics = collection.distinct("topic")

    result = []

    for topic in topics:
        docs = list(
            collection.find({"topic": topic})
            .sort("created_at", 1)  # chronological
        )

        if not docs:
            continue

        latest = docs[-1]

        # 🔥 FILTER OLD NEWS (last 24 hours only)
        if "created_at" in latest:
            if latest["created_at"] < datetime.utcnow() - timedelta(hours=24):
                continue

        # 🔥 combine ALL messages
        all_text = " ".join([d.get("text", "") for d in docs])

        # 🤖 AI summary
        summary = generate_ai_summary(all_text)

        result.append({
            "topic": topic,
            "topic_name": latest.get("topic_name", "Unknown"),
            "headline": latest.get("headline", "No headline"),
            "summary": summary,
            "updates": len(docs),
            "last_updated": latest.get("created_at").strftime("%d %b %I:%M %p") if latest.get("created_at") else ""
        })

    # 🔥 SORT BY LATEST UPDATE TIME
    result.sort(key=lambda x: x["last_updated"], reverse=True)

    return result


# 🔥 TIMELINE: Get full topic details
@app.get("/topic/{topic_id}")
def get_topic_details(topic_id: str):
    docs = list(
        collection.find({"topic": topic_id})
        .sort("created_at", 1)
    )

    if not docs:
        return {"error": "Topic not found"}

    return {
        "topic": topic_id,
        "topic_name": docs[0].get("topic_name", "Unknown"),
        "messages": [
            {
                "text": d.get("text"),
                "summary": d.get("summary"),
                "headline": d.get("headline"),
                "created_at": d.get("created_at").strftime("%d %b %I:%M %p") if d.get("created_at") else ""
            }
            for d in docs
        ]
    }