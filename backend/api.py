from fastapi import FastAPI, Request
from pymongo import MongoClient
import os
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fetcher import fetch_news

import threading
import time

app = FastAPI()

# 🌐 CORS (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ change in production
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

# ⚡ CREATE INDEXES (IMPORTANT for performance)
collection.create_index([("topic", 1)])
collection.create_index([("created_at", -1)])
collection.create_index([("processed", 1)])

# 🏠 Health check
@app.api_route("/", methods=["GET", "HEAD"])
def home(request: Request):
    return {"status": "API is running 🚀"}


# 🔥 AUTO FETCH FUNCTION (SAFE VERSION)
def background_fetch():
    while True:
        try:
            print("🚀 Auto fetching news...")
            fetch_news()
            print("✅ Fetch done. Sleeping 60 sec...\n")
        except Exception as e:
            print("❌ Fetch error:", e)

        time.sleep(60)


# 🚀 START BACKGROUND TASK
@app.on_event("startup")
def start_background_task():
    thread = threading.Thread(target=background_fetch, daemon=True)
    thread.start()


# 🔥 MANUAL FETCH
@app.get("/fetch-news")
def run_fetch():
    try:
        fetch_news()
        return {"status": "News fetched successfully ✅"}
    except Exception as e:
        return {"error": str(e)}


# 🔥 GET ALL TOPICS (OPTIMIZED)
@app.get("/topics")
def get_topics():
    pipeline = [
        {"$sort": {"created_at": -1}},
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
        {"$sort": {"last_updated": -1}},
        {"$limit": 50}  # ⚠️ prevent huge responses
    ]

    result = list(collection.aggregate(pipeline))

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


# 🔥 GET FULL TIMELINE (PAGINATED)
@app.get("/topic/{topic_id}")
def get_topic_details(topic_id: str, limit: int = 50):
    docs = list(
        collection.find({"topic": topic_id})
        .sort("created_at", -1)
        .limit(limit)
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


# 🔥 OPTIONAL: DELETE OLD DATA (to control DB size)
@app.delete("/cleanup")
def cleanup(days: int = 7):
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = collection.delete_many({
        "created_at": {"$lt": cutoff}
    })

    return {"deleted": result.deleted_count}