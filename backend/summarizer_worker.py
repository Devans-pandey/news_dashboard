from pymongo import MongoClient
from transformers import pipeline
from datetime import datetime
import time

# 🔌 MongoDB
MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 🤖 LOAD MODELS
print("Loading models...")

# 🧾 Summary model (BEST for news)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# 📰 Headline model (light + fast)
headline_generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-small"
)

print("Models loaded ✅")


# 🧾 Generate summary (FOR FULL TOPIC)
def generate_summary(text):
    try:
        # BART has token limit → chunking
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]

        summaries = []

        for chunk in chunks:
            result = summarizer(
                chunk,
                max_length=120,
                min_length=40,
                do_sample=False
            )[0]["summary_text"]

            summaries.append(result)

        return " ".join(summaries)

    except Exception as e:
        print("Summary error:", e)
        return "Summary unavailable"


# 📰 Generate headline (FROM SUMMARY)
def generate_headline(summary):
    prompt = f"""
    Generate a short breaking news headline (max 8 words).

    News:
    {summary}
    """

    try:
        result = headline_generator(
            prompt,
            max_length=20,
            do_sample=False
        )[0]["generated_text"]

        return result.strip()

    except Exception as e:
        print("Headline error:", e)
        return "Breaking News"


# 🔄 PROCESS TOPICS
def process_topics():
    print("Checking topics...")

    topics = collection.distinct("topic")

    for topic in topics:
        docs = list(collection.find({
            "topic": topic,
            "processed": False
        }))

        if not docs:
            continue

        print(f"\nProcessing topic: {topic}")

        # 🔥 Combine ALL messages
        combined_text = "\n".join([d["text"] for d in docs if d.get("text")])

        if len(combined_text) < 50:
            continue

        # 🧠 Generate summary
        summary = generate_summary(combined_text)

        # 🧠 Generate headline from summary
        headline = generate_headline(summary)

        # 💾 Update DB
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