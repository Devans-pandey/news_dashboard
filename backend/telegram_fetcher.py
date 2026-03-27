from telethon import TelegramClient, events
from pymongo import MongoClient
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import time

# 🔌 MongoDB
MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["messages"]

# 🤖 Embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# 🔍 Topic clustering
def find_topic(message):
    new_emb = model.encode(message)

    recent = list(collection.find().sort("created_at", -1).limit(50))

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

    # 🔥 Adjust threshold for better grouping
    if best_score > 0.6 and best_topic:
        return best_topic, new_emb
    else:
        return f"Topic_{int(time.time()*1000)}", new_emb


# 📡 Telegram API
api_id = 32424333
api_hash = "3fae8215547deff7b0930dbff9870226"

client = TelegramClient('session', api_id, api_hash)

# 👉 USE YOUR DUMMY CHANNEL USERNAME
channels = ["dashNewsmy", "osinttv", "WNGNEW","DefenceSphere"]


@client.on(events.NewMessage(chats=channels))
async def handler(event):
    message = event.message.text

    if not message:
        return

    topic, embedding = find_topic(message)

    data = {
        "text": message,
        "topic": topic,
        "embedding": embedding.tolist(),
        "created_at": datetime.utcnow(),
        "processed": False
    }

    collection.insert_one(data)

    print(f"Saved → {topic}")


def main():
    while True:
        try:
            print("Listening...\n")
            client.start()
            client.run_until_disconnected()
        except Exception as e:
            print("Error:", e)
            time.sleep(5)


if __name__ == "__main__":
    main()