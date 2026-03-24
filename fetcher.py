import requests
import time
from pymongo import MongoClient
from datetime import datetime
import os

# 🔌 MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI not found")

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 📰 NEWS API KEY (SAFE)
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

if not NEWS_API_KEY:
    raise Exception("NEWS_API_KEY not found")

NEWS_URL = f"https://newsapi.org/v2/top-headlines?language=en&pageSize=10&apiKey={NEWS_API_KEY}"


# 🔥 SIMPLE TOPIC GROUPING
def get_topic(text):
    text = text.lower()

    if "iran" in text or "israel" in text:
        return "middle_east"
    elif "trump" in text or "usa" in text:
        return "usa"
    elif "china" in text:
        return "china"
    elif "india" in text:
        return "india"
    else:
        return "general"


# 🔥 FETCH FUNCTION
def fetch_news():
    try:
        response = requests.get(NEWS_URL)
        data = response.json()

        if data.get("status") != "ok":
            print("❌ API Error:", data)
            return

        articles = data.get("articles", [])

        for article in articles:
            title = article.get("title", "")
            description = article.get("description") or ""

            text = f"{title}. {description}"

            if not text.strip():
                continue

            # 🔥 UNIQUE TOPIC
            topic = f"{get_topic(text)}_{hash(text) % 100000}"

            doc = {
                "topic": topic,
                "topic_name": get_topic(text).capitalize(),
                "text": text,
                "headline": title,
                "summary": description,
                "processed": False,  # 🔥 IMPORTANT
                "created_at": datetime.utcnow()
            }

            collection.update_one(
                {"text": text},
                {"$setOnInsert": doc},
                upsert=True
            )

        print("✅ News fetched successfully")

    except Exception as e:
        print("❌ Error fetching news:", e)


# 🔁 CONTINUOUS RUN
def run():
    while True:
        print("🚀 Fetching news...")
        fetch_news()
        print("😴 Sleeping 60 sec...\n")
        time.sleep(60)


if __name__ == "__main__":
    run()