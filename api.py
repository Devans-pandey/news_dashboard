from fastapi import FastAPI
from pymongo import MongoClient
import os
from fastapi.middleware.cors import CORSMiddleware

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

        # 🔥 combine ALL messages
        all_text = " ".join([d.get("text", "") for d in docs])

        # 🔥 basic summary (later replace with AI)
        summary = all_text[:300] + "..." if len(all_text) > 300 else all_text

        result.append({
            "topic": topic,
            "topic_name": latest.get("topic_name", "Unknown"),
            "headline": latest.get("headline", "No headline"),
            "summary": summary,
            "updates": len(docs),
            "last_updated": latest.get("created_at")
        })

    # 🔥 sort by most updates
    result.sort(key=lambda x: x["updates"], reverse=True)

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
                "created_at": d.get("created_at")
            }
            for d in docs
        ]
    }