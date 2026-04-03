"""
🔄 Re-classify all messages in MongoDB that are stuck as "General News".
Run this once after deploying the improved classifier.

Usage (locally):
    set MONGO_URI=your_mongo_uri
    set HF_API_KEY=your_hf_key
    python reclassify.py
"""

import os
from pymongo import MongoClient
from topic_classifier import classify_topic

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ Set MONGO_URI env var first!")
    exit(1)

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

docs = list(collection.find())
print(f"📦 Found {len(docs)} messages in MongoDB\n")

updated = 0
for doc in docs:
    text = doc.get("text", "")
    old_topic = doc.get("topic", "General News")

    if not text.strip():
        continue

    new_topic = classify_topic(text)

    if new_topic != old_topic:
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"topic": new_topic}}
        )
        print(f"  ✅ '{text[:60]}...' → {old_topic} ➜ {new_topic}")
        updated += 1
    else:
        print(f"  ⏭️  '{text[:60]}...' → {old_topic} (unchanged)")

print(f"\n🎯 Done! Updated {updated}/{len(docs)} messages.")
