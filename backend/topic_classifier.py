import os
import requests
import time

HF_API_KEY = os.getenv("HF_API_KEY", "")

API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

LABELS = [
    "India Politics",
    "International Relations",
    "War and Conflict",
    "Technology",
    "Economy",
    "Defense",
    "General News"
]


def classify_topic_hf(text):
    """Classify using HuggingFace zero-shot API with retry for cold starts."""

    payload = {
        "inputs": text[:500],  # limit text length to avoid API issues
        "parameters": {
            "candidate_labels": LABELS
        }
    }

    # Retry up to 3 times (HF free tier often has cold start delays)
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            result = response.json()

            # HF returns {"error": "Model is currently loading"} on cold start
            if "error" in result:
                print(f"⚠️ HF API attempt {attempt+1}: {result['error']}")
                wait_time = result.get("estimated_time", 10)
                time.sleep(min(wait_time, 15))
                continue

            if "labels" in result and len(result["labels"]) > 0:
                topic = result["labels"][0]
                score = result["scores"][0]
                print(f"✅ HF classified: '{text[:50]}...' → {topic} ({score:.2f})")
                return topic

        except Exception as e:
            print(f"⚠️ HF API attempt {attempt+1} error: {e}")
            time.sleep(2)

    return None  # signal that HF failed


def classify_topic_keywords(text):
    """Fast keyword-based fallback classifier."""
    text_lower = text.lower()

    keyword_map = {
        "War and Conflict": [
            "war", "attack", "bomb", "strike", "missile", "drone", "kill",
            "troops", "military", "combat", "battle", "invasion", "ceasefire",
            "airstrike", "casualties", "artillery", "frontline", "offensive",
            "soldier", "weapon", "warfare", "explosion", "shelling", "hamas",
            "hezbollah", "isis", "taliban", "insurgent"
        ],
        "Defense": [
            "defense", "defence", "navy", "army", "air force", "fighter jet",
            "submarine", "warship", "radar", "ammunition", "arsenal",
            "pentagon", "nato", "military exercise", "deployment", "base"
        ],
        "India Politics": [
            "modi", "india", "bjp", "congress", "parliament", "delhi",
            "lok sabha", "rajya sabha", "election", "indian government",
            "nda", "opposition", "kashmir"
        ],
        "International Relations": [
            "diplomat", "treaty", "sanctions", "summit", "united nations",
            "bilateral", "embassy", "foreign minister", "geopolitics",
            "alliance", "iran", "israel", "china", "russia", "ukraine",
            "trump", "usa", "biden", "eu", "nato", "g7", "g20",
            "north korea", "taiwan", "middle east", "syria"
        ],
        "Technology": [
            "ai", "artificial intelligence", "tech", "software", "cyber",
            "satellite", "space", "robot", "drone tech", "startup",
            "digital", "5g", "quantum", "chip", "semiconductor"
        ],
        "Economy": [
            "economy", "gdp", "inflation", "stock", "market", "trade",
            "tariff", "export", "import", "bank", "currency", "rupee",
            "dollar", "oil price", "recession", "fiscal", "budget"
        ],
    }

    # Score each topic by counting keyword matches
    scores = {}
    for topic, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[topic] = score

    if scores:
        best_topic = max(scores, key=scores.get)
        print(f"🔑 Keyword classified: '{text[:50]}...' → {best_topic} (score: {scores[best_topic]})")
        return best_topic

    return "General News"


def classify_topic(text):
    """Main classifier — tries HF API first, falls back to keywords."""
    if not text or len(text.strip()) < 20:
        return "General News"

    # Try HuggingFace zero-shot first
    if HF_API_KEY:
        result = classify_topic_hf(text)
        if result:
            return result

    # Fallback to keyword-based classification
    return classify_topic_keywords(text)