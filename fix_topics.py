from pymongo import MongoClient
from transformers import pipeline

# 🔌 MongoDB
MONGO_URI = "your_mongodb_uri_here"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 🤖 Load model once
print("Loading model...")
headline_generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)
print("Model loaded!")

# 🧠 Headline generator
def generate_headline(text):
    prompt = f"""
    Generate a short breaking news headline (max 8 words).

    Rules:
    - Do NOT use "X vs Y"
    - Capture the main event clearly
    - Use proper country/entity names
    - Avoid vague words

    Text:
    {text}
    """

    try:
        result = headline_generator(
            prompt,
            max_length=30,
            do_sample=False
        )[0]['generated_text']

        return result.strip()

    except Exception as e:
        print("Error:", e)
        return "Breaking news"


# 🔄 Process all documents
print("Fixing old topics...\n")

for doc in collection.find():
    try:
        text = doc.get("text", "")

        if not text.strip():
            continue

        new_headline = generate_headline(text[:300])

        collection.update_one(
            {"_id": doc["_id"]},
            {
                "$set": {
                    "topic_name": new_headline   # or "headline"
                }
            }
        )

        print("UPDATED:", new_headline)

    except Exception as e:
        print("Error processing doc:", e)

print("\nDone fixing topics!")