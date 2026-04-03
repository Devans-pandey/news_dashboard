from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
import os
import threading
import time
import requests as http_requests
from collections import defaultdict
from datetime import datetime
from telegram_fetcher import run_fetch
from gemini_summariser import generate_summary_and_title
from topic_classifier import classify_topic

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


# ============================================
# 🔄 BACKGROUND KEEP-ALIVE + AUTO-FETCH
# ============================================
RENDER_URL = os.getenv("RENDER_URL", "")  # e.g. https://news-dashboard-xsto.onrender.com
FETCH_INTERVAL = 300    # fetch new messages every 5 minutes
PING_INTERVAL = 600     # ping self every 10 minutes to prevent sleep
SUMMARY_INTERVAL = 1800 # regenerate summaries every 30 minutes


def background_worker():
    """Background thread: keeps Render awake + auto-fetches + generates summaries."""
    time.sleep(30)  # wait for server to fully start
    print("🔄 Background worker started")

    last_fetch = 0
    last_ping = 0
    last_summary = 0

    while True:
        now = time.time()

        # Auto-fetch from Telegram
        if now - last_fetch >= FETCH_INTERVAL:
            try:
                print("🚀 Auto-fetching messages...")
                run_fetch()
                last_fetch = now
                print("✅ Auto-fetch complete")
            except Exception as e:
                print(f"❌ Auto-fetch error: {e}")

        # Auto-generate summaries (calls Gemini sparingly)
        if now - last_summary >= SUMMARY_INTERVAL:
            try:
                print("📝 Auto-generating summaries...")
                if RENDER_URL:
                    http_requests.get(f"{RENDER_URL}/generate-summaries", timeout=60)
                last_summary = now
                print("✅ Summaries generated")
            except Exception as e:
                print(f"⚠️ Summary generation error: {e}")

        # Self-ping to prevent Render sleep
        if RENDER_URL and now - last_ping >= PING_INTERVAL:
            try:
                http_requests.get(f"{RENDER_URL}/", timeout=10)
                last_ping = now
                print("🏓 Self-ping OK")
            except Exception as e:
                print(f"⚠️ Self-ping failed: {e}")

        time.sleep(60)  # check every minute


# Start background worker on server boot
worker_thread = threading.Thread(target=background_worker, daemon=True)
worker_thread.start()


@app.get("/")
def home():
    return {"message": "News API running"}


# 🚀 DEBUG ENDPOINT — check what env vars are set (safe: only shows key names)
@app.get("/debug")
def debug():
    return {
        "MONGO_URI": "SET" if os.getenv("MONGO_URI") else "MISSING",
        "TELEGRAM_API_ID": "SET" if os.getenv("TELEGRAM_API_ID") else "MISSING",
        "TELEGRAM_API_HASH": "SET" if os.getenv("TELEGRAM_API_HASH") else "MISSING",
        "TELEGRAM_SESSION": "SET" if os.getenv("TELEGRAM_SESSION") else "MISSING",
        "HF_API_KEY": "SET" if os.getenv("HF_API_KEY") else "MISSING",
        "GEMINI_API_KEY": "SET" if os.getenv("GEMINI_API_KEY") else "MISSING",
        "mongo_db": db.name,
        "mongo_collection": collection.name,
        "document_count": collection.count_documents({}),
    }


# 🚀 FETCH ENDPOINT — trigger Telegram fetch
@app.get("/fetch")
def fetch():
    try:
        result = run_fetch()
        count = collection.count_documents({})
        return {
            "status": "fetched",
            "total_messages": count,
            "details": result,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# 🚀 RECLASSIFY ENDPOINT — re-classify all existing messages
@app.get("/reclassify")
def reclassify():
    try:
        docs = list(collection.find())
        updated = 0

        for doc in docs:
            text = doc.get("text", "")
            if not text.strip():
                continue

            new_topic = classify_topic(text)
            old_topic = doc.get("topic", "General News")

            if new_topic != old_topic:
                collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"topic": new_topic}}
                )
                updated += 1

        return {
            "status": "reclassified",
            "total": len(docs),
            "updated": updated,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

# 🚀 STATS ENDPOINT — dashboard statistics
@app.get("/stats")
def get_stats():
    total_messages = collection.count_documents({})
    topics = collection.distinct("topic")
    total_topics = len(topics)

    last_doc = collection.find_one(sort=[("created_at", -1)])
    last_updated = last_doc.get("created_at") if last_doc else None

    return {
        "total_messages": total_messages,
        "total_topics": total_topics,
        "last_updated": last_updated,
    }


# 🔥 Summaries cache collection
summaries_collection = db["summaries"]


def _get_cached_summary(topic):
    """Get cached headline + summary from MongoDB."""
    cached = summaries_collection.find_one({"topic": topic})
    if cached:
        return cached.get("headline", ""), cached.get("summary", "")
    return None, None


def _fallback_summary(texts):
    """Quick text-based summary without any API call."""
    combined = " ".join(t.strip() for t in texts if t.strip())
    if not combined:
        return "Breaking News", "Details coming soon..."

    sentences = combined.replace("\n", ". ").split(".")
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    headline = sentences[0][:80] if sentences else combined[:80]
    summary = ". ".join(sentences[:3])[:300] if sentences else combined[:300]
    return headline, summary


# 🚀 GENERATE SUMMARIES — call Gemini ONCE per topic, cache in MongoDB
@app.get("/generate-summaries")
def generate_summaries():
    """Generate and cache summaries for all topics. Call this once, not on every page load."""
    try:
        topics = collection.distinct("topic")
        generated = 0

        for topic in topics:
            docs = list(
                collection.find({"topic": topic}).sort("created_at", -1).limit(5)
            )
            if not docs:
                continue

            texts = [d.get("text", "") for d in docs]

            try:
                headline, summary = generate_summary_and_title(texts)
                if headline and headline != "No headline":
                    summaries_collection.update_one(
                        {"topic": topic},
                        {"$set": {
                            "topic": topic,
                            "headline": headline,
                            "summary": summary,
                            "generated_at": datetime.utcnow(),
                        }},
                        upsert=True,
                    )
                    generated += 1
                    print(f"✅ Summary cached: {topic} → {headline}")
            except Exception as e:
                print(f"⚠️ Summary failed for {topic}: {e}")

        return {"status": "done", "generated": generated, "total_topics": len(topics)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# 🚀 TOPICS ENDPOINT — list all topics (uses cached summaries, NO Gemini calls)
@app.get("/topics")
def get_topics():
    data = list(collection.find())

    if not data:
        return []

    # group messages by topic
    grouped = defaultdict(list)
    for item in data:
        topic = item.get("topic", "General News")
        grouped[topic].append(item)

    response = []

    for topic, docs in grouped.items():
        docs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)

        latest = docs[0]
        count = len(docs)
        texts = [d.get("text", "") for d in docs[:5]]

        # Use CACHED summary (no API call)
        headline, summary = _get_cached_summary(topic)
        if not headline:
            headline, summary = _fallback_summary(texts)

        response.append({
            "topic": topic,
            "headline": headline,
            "summary": summary,
            "message_count": count,
            "last_updated": latest.get("created_at"),
            "channel": latest.get("channel", "unknown"),
        })

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

    texts = [d.get("text", "") for d in docs[:5]]

    # Use CACHED summary (no API call)
    headline, summary = _get_cached_summary(topic_name)
    if not headline:
        headline, summary = _fallback_summary(texts)

    return {
        "topic": topic_name,
        "headline": headline,
        "summary": summary,
        "messages": messages,
        "count": len(messages),
        "last_updated": docs[0].get("created_at") if docs else None,
    }