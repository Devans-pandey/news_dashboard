from pymongo import MongoClient
from transformers import pipeline

# 🔌 MongoDB connection
MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 🤖 Load summarization model (first run will download ~1GB)
print("Loading summarizer model...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# 🔥 Generate summary for a topic
def generate_topic_summary(topic):
    docs = list(
        collection.find({"topic": topic})
        .sort("created_at", -1)
        .limit(3)
    )

    if not docs:
        return "No data available"

    combined_text = " ".join([d["text"] for d in docs])

    # 🔥 dynamic length (fix warnings)
    input_length = len(combined_text.split())

    max_len = min(60, input_length)   # never exceed input
    min_len = max(10, max_len // 2)   # reasonable minimum

    try:
        result = summarizer(
            combined_text,
            max_length=max_len,
            min_length=min_len,
            do_sample=False,
            num_beams=4,          # 🔥 improves quality
            length_penalty=1.2    # 🔥 avoids cut sentences
        )

        summary = result[0]["summary_text"]
       # clean trailing commas / incomplete endings
        summary = summary.rstrip(",.; ")
       
        return summary

    except Exception as e:
        print("Summarization error:", e)
        return combined_text[:200]



# 🔥 Get all topics (dashboard feed)
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
            "topic_name": latest.get("topic_name"),
            "summary": generate_topic_summary(topic),
            "updates": count,
            "last_updated": latest.get("created_at")
        })

    # 🔥 sort by importance (updates + recency)
    result.sort(
        key=lambda x: (x["updates"], x["last_updated"]),
        reverse=True
    )

    return result


# 🚀 Run dashboard in terminal
if __name__ == "__main__":
    print("\n🔥 LIVE NEWS DASHBOARD\n")

    topics = get_all_topics()

    for t in topics:
        print("🔥", t["topic_name"])
        print("Updates:", t["updates"])
        print("Summary:", t["summary"])
        print("-" * 60)