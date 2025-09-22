import json, os, re
from pathlib import Path

def load_schema():
    path = os.environ.get("ARCANUM_SCHEMA_PATH", "schemas/output.default.json")
    if not Path(path).exists():
        return {"type":"object","required":["answer"],"properties":{"answer":{"type":"string"}}}
    return json.loads(Path(path).read_text(encoding="utf-8"))

def ensure_json(raw: str):
    if isinstance(raw, dict):
        return raw
    s = raw.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9]*\n", "", s)
        if s.endswith("```"):
            s = s[:-3]
    return json.loads(s)

def try_auto_repair(raw: str) -> str:
    s = raw.strip()
    s = re.sub(r"^```[a-zA-Z0-9]*\n", "", s)
    s = re.sub(r"```\s*$", "", s)
    s = re.sub(r",\s*([}\]])", r"\1", s)
    if not s.startswith("{") and "{" in s:
        s = s[s.find("{"):]
    if not s.endswith("}") and "}" in s:
        s = s[:s.rfind("}")+1]
    return s
