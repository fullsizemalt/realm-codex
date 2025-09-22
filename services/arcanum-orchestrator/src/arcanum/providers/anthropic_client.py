import os, httpx, json, pathlib

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def call_claude(message: dict) -> str:
    if not ANTHROPIC_KEY:
        return json.dumps({"answer":"(mock) claude response","provenance":[{"source":"arcanum","why":"no api key"}]})
    system_path = os.environ.get("CLAUDE_SYSTEM_PATH","prompts/claude_system_compact.md")
    if pathlib.Path(system_path).exists():
        system_prompt = pathlib.Path(system_path).read_text(encoding="utf-8")
    else:
        system_prompt = ""
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": int(os.environ.get("CLAUDE_MAX_TOKENS","512")),
        "system": system_prompt,
        "messages": [{"role":"user","content": json.dumps(message)}]
    }
    headers = {"x-api-key": ANTHROPIC_KEY, "content-type":"application/json"}
    r = httpx.post(ANTHROPIC_URL, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    content = "".join([c.get("text","") for c in data.get("content",[]) if c.get("type")=="text"])
    return content or json.dumps({"answer":"", "notes":[{"type":"empty","msg":"no content"}]})
