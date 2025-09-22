# Handoff Protocol (Minimal Token, Max Collaboration)

MESSAGE_SCHEMA (JSON only):
{
  "task": "<what to do>",
  "inputs": {"...": "..."},
  "constraints": {"style":"terse","json_only":true,"max_tokens":512},
  "provenance": [{"source":"<url|doc|runbook>","why":"<use>"}],
  "expected": "<name of schema e.g., output.default>",
  "return": "json"
}

AGENT-TO-AGENT RULES:
- Always include 'provenance' with at least one entry.
- Return only the JSON that matches the expected schema.
- Keep 'notes' minimal: decisions or flags only.
- If blocked, return ERROR_FORMAT from system prompt.

DELEGATION EXAMPLE:
{
  "task":"summarize runbook changes",
  "inputs":{"diff":"<patch>"},
  "constraints":{"json_only":true,"max_tokens":256},
  "provenance":[{"source":"docs/runbooks/ai-orchestrator.md","why":"original"}],
  "expected":"output.default",
  "return":"json"
}
