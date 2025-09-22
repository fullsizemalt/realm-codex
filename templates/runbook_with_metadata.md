---
title: "Runbook — <svc>/<mod>"
author: "your-handle"
date: "2025-09-22"
realm: "<realm-slug>"
env: "prod"
attribution:
  - source: "docs/refactor/phases.md"
    description: "followed program standards"
---

# Purpose
What this module does (single responsibility).

# Interfaces & Contracts
- Endpoints: `/healthz`, `/readyz`, `/metrics`, `/contract.json`
- Inputs/Outputs (schemas, limits)

# Operations
- Start/Stop/Restart
- Backups & Restore
- Logs & Metrics (links to dashboards)

# Failure Modes & Self-healing
- Known failure → remediation
- Circuit breaker / backoff / retries

# Security
- Secrets (Vault paths), least privilege

# Change History
- PRs / approvals / dates
