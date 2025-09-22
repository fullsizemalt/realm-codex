import os, json, time, hashlib, uuid
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse, PlainTextResponse
from jsonschema import validate, ValidationError
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from .schema import load_schema, ensure_json, try_auto_repair
from .providers.anthropic_client import call_claude
from .providers.google_client import call_gemini
from .retrieval_adapter import batch_retrieve
from .attribution import append_chronicle_entry

app = FastAPI(title="Arcanum Orchestrator", version="0.1.0")

REQS = Counter("arcanum_requests_total", "Total requests", ["provider","status"])

OUTPUT_SCHEMA = load_schema()

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/readyz")
def readyz():
    return {"ready": True}

@app.get("/contract.json")
def contract():
    return {
        "name": "arcanum-orchestrator",
        "version": "0.1.0",
        "endpoints": ["/invoke", "/metrics", "/healthz", "/readyz", "/contract.json"],
    }

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

@app.post("/invoke")
def invoke(payload: dict = Body(...)):
    provider = payload.get("provider")
    message = payload.get("message")
    provenance = payload.get("provenance", [])
    if provider not in {"claude","gemini"}:
        raise HTTPException(400, "provider must be one of: claude, gemini")
    if not isinstance(message, dict):
        raise HTTPException(400, "message must be an object")

    if "retrieval_ids" in message:
        docs = batch_retrieve(message.get("retrieval_ids", []), include_snippets=message.get("include_snippets", False))
        message["retrieval_results"] = docs

    if provider == "claude":
        raw = call_claude(message)
    else:
        raw = call_gemini(message)

    try:
        data = ensure_json(raw)
    except Exception as e:
        repaired = try_auto_repair(raw)
        try:
            data = ensure_json(repaired)
        except Exception:
            REQS.labels(provider, "bad_json").inc()
            raise HTTPException(502, f"provider returned non-JSON: {e}")

    try:
        validate(instance=data, schema=OUTPUT_SCHEMA)
    except ValidationError as e:
        REQS.labels(provider, "bad_schema").inc()
        raise HTTPException(502, f"provider JSON failed schema: {e.message}")

    prov = data.get("provenance", [])
    if isinstance(prov, list):
        prov.extend(provenance)
    else:
        prov = provenance
    data["provenance"] = prov

    if os.environ.get("ARCANUM_APPEND_JOURNAL", "false").lower() == "true":
        try:
            append_chronicle_entry(action="invoke", provider=provider, message=message, output=data)
        except Exception:
            pass

    REQS.labels(provider, "ok").inc()
    return JSONResponse(data)
