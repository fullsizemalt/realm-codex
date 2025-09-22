import os, json, time, hashlib, uuid
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import JSONResponse, PlainTextResponse
from jsonschema import validate, ValidationError
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from .schema import load_schema, ensure_json, try_auto_repair
from .providers.anthropic_client import call_claude
from .providers.google_client import call_gemini
from .retrieval_adapter import batch_retrieve
from .attribution import _attribution_logger
from .agent_metrics import record_agent_metrics

app = FastAPI(title="Arcanum Orchestrator", version="0.1.0")

# Agent SLO status endpoint
@app.get("/agents/{agent_name}/slo")
def get_agent_slo_status(agent_name: str, hours_back: int = 1):
    """Get SLO status for a specific agent"""
    from .agent_metrics import _metrics_collector
    return _metrics_collector.get_agent_slo_status(agent_name, hours_back)

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
    start_time = time.time()
    provider = payload.get("provider")
    message = payload.get("message")
    provenance = payload.get("provenance", [])
    agent_name = payload.get("agent_name", f"arcanum-{provider}")

    if provider not in {"claude","gemini"}:
        raise HTTPException(400, "provider must be one of: claude, gemini")
    if not isinstance(message, dict):
        raise HTTPException(400, "message must be an object")

    if "retrieval_ids" in message:
        docs = batch_retrieve(message.get("retrieval_ids", []), include_snippets=message.get("include_snippets", False))
        message["retrieval_results"] = docs

    status = "success"
    error = None
    raw = None

    try:
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
                status = "bad_json"
                error = f"provider returned non-JSON: {e}"
                record_agent_metrics(agent_name, provider, _get_model_for_provider(provider), start_time, status, error=error)
                raise HTTPException(502, error)

        try:
            validate(instance=data, schema=OUTPUT_SCHEMA)
        except ValidationError as e:
            REQS.labels(provider, "bad_schema").inc()
            status = "bad_schema"
            error = f"provider JSON failed schema: {e.message}"
            record_agent_metrics(agent_name, provider, _get_model_for_provider(provider), start_time, status, error=error)
            raise HTTPException(502, error)

        prov = data.get("provenance", [])
        if isinstance(prov, list):
            prov.extend(provenance)
        else:
            prov = provenance
        data["provenance"] = prov

        # Record successful interaction
        input_tokens = _estimate_tokens(json.dumps(message))
        output_tokens = _estimate_tokens(json.dumps(data))
        record_agent_metrics(
            agent_name=agent_name,
            provider=provider,
            model=_get_model_for_provider(provider),
            start_time=start_time,
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        # Enhanced attribution logging
        try:
            _attribution_logger.log_agent_interaction(
                agent_name=agent_name,
                provider=provider,
                message=message,
                output=data,
                start_time=start_time,
                status=status
            )
        except Exception:
            pass

        REQS.labels(provider, "ok").inc()
        return JSONResponse(data)

    except HTTPException:
        raise
    except Exception as e:
        status = "error"
        error = str(e)
        record_agent_metrics(agent_name, provider, _get_model_for_provider(provider), start_time, status, error=error)
        REQS.labels(provider, "error").inc()
        raise HTTPException(500, f"Internal error: {e}")

def _get_model_for_provider(provider: str) -> str:
    """Get model name for provider"""
    if provider == "claude":
        return os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet")
    elif provider == "gemini":
        return os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    return provider

def _estimate_tokens(text: str) -> int:
    """Rough token estimation"""
    return len(text.split())
