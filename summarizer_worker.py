from pymongo import MongoClient
from transformers import pipeline
import time

# 🔌 MongoDB connection
MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 🤖 Load summarizer (only once)
print("Loading summarizer model...")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-6-6")

print("Worker started successfully!")

# 🧠 Generate headline from summary
def generate_headline(summary):
    try:
        short = summarizer(
            summary,
            max_length=25,
            min_length=8,
            do_sample=False
        )[0]["summary_text"]

        return short.strip()

    except:
        return summary[:60]


# 🔁 MAIN LOOP (TOPIC-LEVEL PROCESSING)
while True:
    print("\n🔄 Updating topic summaries...")

    try:
        # 🔥 get all topics
        topics = collection.distinct("topic")

        for topic in topics:
            # 🔥 get latest 5 messages for that topic
            docs = list(
                collection.find({"topic": topic})
                .sort("created_at", -1)
                .limit(5)
            )

            if not docs:
                continue

            # 🔥 combine text
            combined_text = " ".join([d.get("text", "") for d in docs])

            if not combined_text.strip():
                continue

            try:
                # ✂️ Generate summary
                summary = summarizer(
                    combined_text,
                    max_length=100,
                    min_length=30,
                    do_sample=False
                )[0]["summary_text"]

                # 🧠 Generate headline
                headline = generate_headline(summary)

                # 💾 Update ALL documents of that topic
                collection.update_many(
                    {"topic": topic},
                    {
                        "$set": {
                            "summary": summary,
                            "headline": headline
                        }
                    }
                )

                print(f"✅ Updated topic: {topic}")
                print(f"📰 Headline: {headline}\n")

            except Exception as e:
                print(f"❌ Error processing topic {topic}: {e}")

    except Exception as e:
        print("❌ Worker error:", e)

    # ⏱️ wait before next cycle
    time.sleep(10)