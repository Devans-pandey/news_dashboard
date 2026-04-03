import os
import requests

HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

def classify_topic(text):
    if not text or len(text.strip()) < 20:
        return "General News"

    labels = [
        "India Politics",
        "International Relations",
        "War and Conflict",
        "Technology",
        "Economy",
        "Defense",
        "General News"
    ]

    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": labels
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()

        return result["labels"][0]

    except Exception as e:
        print("Classifier error:", e)
        return "General News"