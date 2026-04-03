import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def generate_summary_and_title(messages):
    """Generate a headline and summary from a list of message texts.
    Uses Gemini API, with a text-extraction fallback if API fails.
    """
    if not messages or all(not m.strip() for m in messages):
        return "Breaking News", "No details available yet."

    combined_text = " ".join(m.strip() for m in messages if m.strip())

    # Try Gemini API
    if GEMINI_API_KEY:
        try:
            result = _call_gemini(combined_text)
            if result:
                return result
        except Exception as e:
            print(f"⚠️ Gemini API failed: {e}")

    # Fallback: extract headline + summary from the text itself
    return _fallback_extract(combined_text)


def _call_gemini(text):
    """Call Gemini API to generate headline + summary."""

    prompt = f"""You are a professional news editor.

Given the following news messages, generate:
1. A short factual headline (max 10 words) on the FIRST line
2. A clear summary (2-3 sentences) on the SECOND line

Rules:
- Do NOT add false or misleading information
- Be concise and factual
- Output ONLY two lines: headline then summary

News:
{text[:2000]}"""

    # Try multiple model names (API versions change)
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
                    "contents": [{"parts": [{"text": prompt}]}]
                },
                timeout=15,
            )

            data = response.json()

            # Check for errors
            if "error" in data:
                print(f"⚠️ Gemini model {model} error: {data['error'].get('message', '')}")
                continue

            text_out = data["candidates"][0]["content"]["parts"][0]["text"]
            lines = [l.strip() for l in text_out.strip().split("\n") if l.strip()]

            if len(lines) >= 2:
                title = lines[0].lstrip("#").lstrip("*").strip()
                summary = " ".join(lines[1:]).lstrip("*").strip()
                return title, summary
            elif len(lines) == 1:
                return lines[0], lines[0]

        except Exception as e:
            print(f"⚠️ Gemini model {model} exception: {e}")
            continue

    return None


def _fallback_extract(text):
    """Extract headline + summary from raw text when API is unavailable."""
    # Use first sentence as headline
    sentences = text.replace("\n", ". ").split(".")
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return "Breaking News Update", text[:200].strip()

    headline = sentences[0][:80].strip()
    if not headline.endswith((".", "!", "?")):
        headline += "..."

    # Summary = first 2-3 sentences
    summary_parts = sentences[:3]
    summary = ". ".join(summary_parts)
    if len(summary) > 300:
        summary = summary[:300].rsplit(" ", 1)[0] + "..."

    return headline, summary