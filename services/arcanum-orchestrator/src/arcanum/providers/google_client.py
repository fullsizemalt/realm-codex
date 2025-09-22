import os, httpx, json, pathlib

GEMINI_MODEL = os.environ.get("GEMINI_MODEL","gemini-1.5-flash")
GEMINI_KEY = os.environ.get("GOOGLE_API_KEY","")

def call_gemini(message: dict) -> str:
    if not GEMINI_KEY:
        return json.dumps({"answer":"(mock) gemini response","provenance":[{"source":"arcanum","why":"no api key"}]})
    system_path = os.environ.get("GEMINI_SYSTEM_PATH","prompts/gemini_system_compact.md")
    system_prompt = pathlib.Path(system_path).read_text(encoding="utf-8") if pathlib.Path(system_path).exists() else ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    body = {
        "contents": [{
            "parts": [
                {"text": "SYSTEM:\n" + system_prompt},
                {"text": "USER:\n" + json.dumps(message)}
            ]
        }],
        "generationConfig": {
            "maxOutputTokens": int(os.environ.get("GEMINI_MAX_TOKENS","384")),
            "temperature": float(os.environ.get("GEMINI_TEMPERATURE","0.2"))
        }
    }
    r = httpx.post(url, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        text = json.dumps({"answer":"", "notes":[{"type":"empty","msg":"no content"}]})
    return text
