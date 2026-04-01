import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def generate_summary_and_title(messages):
    combined_text = " ".join(messages)

    prompt = f"""
You are a professional news assistant.

1. Generate a short factual headline (max 10 words)
2. Generate a clear summary (3-4 lines)
3. Do NOT add false or misleading information

News:
{combined_text}
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            }
        )

        text = response.json()['candidates'][0]['content']['parts'][0]['text']

        lines = text.split("\n")
        title = lines[0]
        summary = "\n".join(lines[1:])

        return title.strip(), summary.strip()

    except Exception as e:
        print("Gemini error:", e)
        return "No headline", "No summary"