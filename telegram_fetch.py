from telethon import TelegramClient, events
from pymongo import MongoClient
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import time
import spacy

# 🔤 NLP
nlp = spacy.load("en_core_web_sm")

# 🤖 embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# 🔌 MongoDB
MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

headline_generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)


# 🔍 Find topic using similarity
def find_topic(message):
    new_emb = model.encode(message)

    recent = list(collection.find().sort("created_at", -1).limit(100))

    best_score = 0
    best_topic = None

    for doc in recent:
        if "embedding" not in doc:
            continue

        old_emb = doc["embedding"]
        score = cosine_similarity([new_emb], [old_emb])[0][0]

        if score > best_score:
            best_score = score
            best_topic = doc.get("topic")

    if best_score > 0.4 and best_topic:
        print("Best similarity:", best_score)
        return best_topic, new_emb
    else:
        print("Best similarity:", best_score)
        return f"Topic_{int(time.time())}", new_emb


# 🧠 Smart topic naming
def generate_topic_name(text):
    prompt = f"""
    Generate a short news headline (max 8 words).

    Rules:
    - Do NOT use "X vs Y"
    - Capture the main event
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
        print("Headline error:", e)
        return "Breaking news"


# 📡 Telegram API
api_id = 32424333
api_hash = "3fae8215547deff7b0930dbff9870226"

client = TelegramClient('session', api_id, api_hash, auto_reconnect=True)

channels = ["osinttv", "defencesphere", "MappingConflicts", "goreunit", "dashNewsmy"]


# 🔄 Message handler
@client.on(events.NewMessage(chats=channels))
async def handler(event):
    message = event.message.text

    if message:
        topic, embedding = find_topic(message)

        topic_name = generate_topic_name(message)

        data = {
            "text": message,
            "date": event.message.date,
            "channel": str(event.chat_id),
            "created_at": datetime.utcnow(),
            "topic": topic,
            "topic_name": topic_name,
            "embedding": embedding.tolist()
        }

        collection.insert_one(data)

        print("\nSAVED MESSAGE:")
        print("TOPIC:", topic_name)
        print(message)
        print("-" * 50)


# 🚀 Run loop
def main():
    while True:
        try: 
            print("Listening and saving messages...\n")
            client.start()
            client.run_until_disconnected()
        except Exception as e:
            print("Error:", e)
            print("Reconnecting in 5 sec...\n")
            time.sleep(5)


if __name__ == "__main__":
    main()