from fastapi import FastAPI
from pymongo import MongoClient
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🌐 CORS (for React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 MongoDB
MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 🤖 OPTIONAL (we are NOT using it now, but keeping safe)
summarizer = None

@app.get("/topic/{topic}")
def get_topic_details(topic: str):
    docs = list(
        collection.find({"topic": topic})
        .sort("created_at", 1)
    )

    if not docs:
        return {"error": "No data"}

    return {
        "topic": topic,
        "topic_name": docs[0].get("topic_name"),
        "summary": docs[0].get("summary"),
        "messages": docs
    }



@app.on_event("startup")
def load_model():
    global summarizer
    print("API started (no heavy model needed)")


# 🔥 Get all topics (FAST — no ML here)
def get_all_topics():
    topics = collection.distinct("topic")
    result = []

    for topic in topics:
        docs = list(
            collection.find({"topic": topic})
            .sort("created_at", -1)
        )

        if not docs:
            continue

        latest = docs[0]
        count = len(docs)

        result.append({
            "topic": topic,
            "headline": latest.get("headline"),
            "topic_name": latest.get("topic_name"),
            "summary": latest.get("summary"),
            "updates": count,
            "last_updated": latest.get("created_at")  # ✅ FIX added
        })

    # 🔥 sort by importance
    result.sort(
        key=lambda x: (x["updates"], x["last_updated"]),
        reverse=True
    )

    return result


# 🚀 API endpoint
@app.get("/topics")
def get_topics():
    return get_all_topics()