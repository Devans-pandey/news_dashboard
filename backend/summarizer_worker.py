from pymongo import MongoClient
from transformers import pipeline
from datetime import datetime
import time

# 🔌 MongoDB
MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 🤖 Load model
print("Loading summarizer model...")
generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

# 🧠 Generate summary for topic
def generate_summary(text):
    prompt = f"""
    Summarize the following news updates into a clear concise paragraph:

    {text}
    """

    try:
        result = generator(prompt, max_length=200, do_sample=False)[0]['generated_text']
        return result.strip()
    except Exception as e:
        print("Summary error:", e)
        return "Summary unavailable"


# 🧠 Generate headline for topic
def generate_headline(text):
    prompt = f"""
    Generate a short news headline (max 8 words).

    Rules:
    - Capture the main event
    - Use real entity names
    - No vague words

    Text:
    {text}
    """

    try:
        result = generator(prompt, max_length=20, do_sample=False)[0]['generated_text']
        return result.strip()
    except Exception as e:
        print("Headline error:", e)
        return "Breaking News"


# 🔄 Process topics
def process_topics():
    print("Checking for unprocessed topics...")

    # get unique topics
    topics = collection.distinct("topic")

    for topic in topics:
        if not topic:
            continue

        docs = list(collection.find({
            "topic": topic,
            "processed": False
        }))

        if not docs:
            continue

        print(f"\nProcessing topic: {topic}")

        # 🧠 Combine all messages
        combined_text = "\n".join([doc["text"] for doc in docs if doc.get("text")])

        if len(combined_text) < 20:
            continue

        # 🤖 AI generation
        summary = generate_summary(combined_text)
        headline = generate_headline(combined_text)

        # 💾 Update all docs in this topic
        collection.update_many(
            {"topic": topic},
            {
                "$set": {
                    "summary": summary,
                    "headline": headline,
                    "processed": True,
                    "last_updated": datetime.utcnow()
                }
            }
        )

        print("✅ Done:", headline)


# 🚀 LOOP
def main():
    while True:
        try:
            process_topics()
            print("\nSleeping 30 sec...\n")
            time.sleep(30)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)


if __name__ == "__main__":
    main()