# Arcanum Orchestrator

Routes minimal-token tasks to **Claude Sonnet** and **Gemini Flash**, validates JSON schema, attempts auto-repair, batches retrieval, and appends attribution to the Chronicle.

## Quickstart
```bash
# from services/arcanum-orchestrator
cp .env.example .env   # add API keys
docker compose up -d --build

# Smoke test (mock if no keys)
curl -X POST localhost:8080/invoke -H 'content-type: application/json' -d '{"provider":"claude","message":{"task":"plan","inputs":{},"expected":"output.default","return":"json"}}'
```
## Env vars
- ANTHROPIC_API_KEY, GOOGLE_API_KEY
- CLAUDE_MODEL, GEMINI_MODEL, token/temperature vars
- ARCANUM_SCHEMA_PATH (default schemas/output.default.json)
- ARCANUM_APPEND_JOURNAL (true/false)
- ARCANUM_CHRONICLE_PATH (default docs/chronicle.md)
