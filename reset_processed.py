from pymongo import MongoClient

MONGO_URI = "mongodb+srv://newsdash:newsdash@cluster0.tialnu4.mongodb.net/news_db?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["messages"]

# 🔥 remove processed + summary + headline
result = collection.update_many(
    {},
    {
        "$unset": {
            "processed": "",
            "summary": "",
            "headline": ""
        }
    }
)

print("Updated docs:", result.modified_count)