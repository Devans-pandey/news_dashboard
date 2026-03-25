from fastapi import FastAPI, Request
from pymongo import MongoClient
import os
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fetcher import fetch_news

import threading
import time

app = FastAPI()

# 🌐 CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict to your frontend URL
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


# 🏠 Health check (FIXED for UptimeRobot)
@app.api_route("/", methods=["GET", "HEAD"])
def home(request: Request):
    return {"status": "API is running 🚀"}


# 🔥 AUTO FETCH FUNCTION
def background_fetch():
    while True:
        try:
            print("🚀 Auto fetching news...")
            fetch_news()
            print("✅ Fetch done. Sleeping 60 sec...\n")
        except Exception as e:
            print("❌ Fetch error:", e)

        time.sleep(60)  # every 60 seconds


# 🚀 START BACKGROUND TASK
@app.on_event("startup")
def start_background_task():
    thread = threading.Thread(target=background_fetch)
    thread.daemon = True
    thread.start()


# 🔥 MANUAL FETCH (optional)
@app.get("/fetch-news")
def run_fetch():
    try:
        fetch_news()
        return {"status": "News fetched successfully ✅"}
    except Exception as e:
        return {"error": str(e)}


# 🔥 GET ALL TOPICS
@app.get("/topics")
def get_topics():
    pipeline = [
        {
            "$sort": {"created_at": -1}
        },
        {
            "$group": {
                "_id": "$topic",
                "topic_name": {"$first": "$topic_name"},
                "headline": {"$first": "$headline"},
                "summary": {"$first": "$summary"},
                "last_updated": {"$first": "$created_at"},
                "updates": {"$sum": 1}
            }
        },
        {
            "$sort": {"last_updated": -1}
        }
    ]

    result = list(collection.aggregate(pipeline))

    # clean format
    return [
        {
            "topic": r["_id"],
            "topic_name": r.get("topic_name"),
            "headline": r.get("headline"),
            "summary": r.get("summary"),
            "updates": r.get("updates"),
            "last_updated": r.get("last_updated")
        }
        for r in result
    ]


# 🔥 GET FULL TIMELINE
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
                "created_at": d.get("created_at")
            }
            for d in docs
        ]
    }