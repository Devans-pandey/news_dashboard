import os
import requests
import time

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")

HF_API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"

LABELS = [
    "India Politics",
    "International Relations",
    "War and Conflict",
    "Technology",
    "Economy",
    "Defense",
    "General News"
]


# ============================================
# GEMINI CLASSIFIER (Primary — best quality)
# ============================================

def classify_topic_gemini(text):
    """Classify using Gemini API — fast, accurate, and reliable."""

    valid_labels = ", ".join(LABELS)

    prompt = f"""You are a news topic classifier. Classify the following news message into EXACTLY ONE of these categories:

{valid_labels}

Rules:
- Output ONLY the category name, nothing else
- No explanations, no quotes, no extra text
- Pick the MOST relevant category
- If unsure, use "General News"

News message:
{text[:1500]}

Category:"""

    models = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-pro",
    ]

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 20,
                    }
                },
                timeout=10,
            )

            data = response.json()

            if "error" in data:
                print(f"⚠️ Gemini classifier ({model}) error: {data['error'].get('message', '')}")
                continue

            raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean up the response — Gemini sometimes adds quotes or extra whitespace
            result = raw.strip('"').strip("'").strip("*").strip()

            # Validate it's one of our labels
            for label in LABELS:
                if label.lower() == result.lower():
                    print(f"🤖 Gemini classified: '{text[:50]}...' → {label}")
                    return label

            # Fuzzy match — check if the response contains a label
            for label in LABELS:
                if label.lower() in result.lower():
                    print(f"🤖 Gemini classified (fuzzy): '{text[:50]}...' → {label}")
                    return label

            print(f"⚠️ Gemini returned unexpected label: '{result}'")

        except Exception as e:
            print(f"⚠️ Gemini classifier ({model}) exception: {e}")
            continue

    return None  # Signal that Gemini failed


# ============================================
# HUGGINGFACE CLASSIFIER (Secondary fallback)
# ============================================

def classify_topic_hf(text):
    """Classify using HuggingFace zero-shot API with retry for cold starts."""

    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    payload = {
        "inputs": text[:500],
        "parameters": {
            "candidate_labels": LABELS
        }
    }

    for attempt in range(2):
        try:
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=20)
            result = response.json()

            if "error" in result:
                print(f"⚠️ HF API attempt {attempt+1}: {result['error']}")
                wait_time = result.get("estimated_time", 8)
                time.sleep(min(wait_time, 10))
                continue

            if "labels" in result and len(result["labels"]) > 0:
                topic = result["labels"][0]
                score = result["scores"][0]
                print(f"✅ HF classified: '{text[:50]}...' → {topic} ({score:.2f})")
                return topic

        except Exception as e:
            print(f"⚠️ HF API attempt {attempt+1} error: {e}")
            time.sleep(2)

    return None


# ============================================
# KEYWORD CLASSIFIER (Fast fallback)
# ============================================

def classify_topic_keywords(text):
    """Fast keyword-based fallback classifier."""
    text_lower = text.lower()

    keyword_map = {
        "War and Conflict": [
            "war", "attack", "bomb", "strike", "missile", "drone", "kill",
            "troops", "military", "combat", "battle", "invasion", "ceasefire",
            "airstrike", "casualties", "artillery", "frontline", "offensive",
            "soldier", "weapon", "warfare", "explosion", "shelling", "hamas",
            "hezbollah", "isis", "taliban", "insurgent", "shot down",
            "destroyed", "intercept", "raid"
        ],
        "Defense": [
            "defense", "defence", "navy", "army", "air force", "fighter jet",
            "submarine", "warship", "radar", "ammunition", "arsenal",
            "pentagon", "nato", "military exercise", "deployment", "base",
            "commissioning", "fleet", "aircraft carrier", "ssbn", "frigate"
        ],
        "India Politics": [
            "modi", "india", "bjp", "congress", "parliament", "delhi",
            "lok sabha", "rajya sabha", "election", "indian government",
            "nda", "opposition", "kashmir", "rajnath", "amit shah"
        ],
        "International Relations": [
            "diplomat", "treaty", "sanctions", "summit", "united nations",
            "bilateral", "embassy", "foreign minister", "geopolitics",
            "alliance", "iran", "israel", "china", "russia", "ukraine",
            "trump", "usa", "biden", "eu", "g7", "g20",
            "north korea", "taiwan", "middle east", "syria", "negotiations"
        ],
        "Technology": [
            "ai", "artificial intelligence", "tech", "software", "cyber",
            "satellite", "space", "robot", "startup", "digital", "5g",
            "quantum", "chip", "semiconductor", "spacex", "isro", "nasa"
        ],
        "Economy": [
            "economy", "gdp", "inflation", "stock", "market", "trade",
            "tariff", "export", "import", "bank", "currency", "rupee",
            "dollar", "oil price", "recession", "fiscal", "budget"
        ],
    }

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


# ============================================
# MAIN CLASSIFIER — cascading priority
# ============================================

def classify_topic(text):
    """Main classifier — Gemini first → HF fallback → keyword fallback."""
    if not text or len(text.strip()) < 20:
        return "General News"

    # 1. Try Gemini (best quality)
    if GEMINI_API_KEY:
        result = classify_topic_gemini(text)
        if result:
            return result

    # 2. Try HuggingFace zero-shot
    if HF_API_KEY:
        result = classify_topic_hf(text)
        if result:
            return result

    # 3. Keyword fallback
    return classify_topic_keywords(text)