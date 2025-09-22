# CONTRIBUTING — Modularity, Independence, Attribution

**Effective:** 2025-09-22

## Principles
- **Modular & Independent:** one responsibility per module; replaceable with minimal blast radius.
- **Bounded Interfaces:** stable contracts; internals may change.
- **Observability Required:** `/healthz`, `/readyz`, `/metrics`, `/contract.json` for every service.
- **Docs-First:** every change updates docs; add an Ops Journal entry.
- **Attribution & Metadata:** all docs and generated artifacts must include YAML front matter with author & provenance.

## Required Front Matter (YAML)
```yaml
---
title: "<doc title>"
author: "<your name or handle>"
date: "2025-09-22"
realm: "<realm-slug>"
env: "<dev|stg|prod>"
attribution:
  - source: "<url or path>"
    description: "<what was used>"
---
```

## PR Rules (Definition of Done)
- Health endpoints exposed; limits set.
- Logs → Loki; metrics → Prometheus; alerts defined.
- Config & secrets externalized (Vault/Vaultwarden).
- Runbook updated under `docs/runbooks/`.
- Ops Journal entry appended in `docs/chronicle.md` (include PR link).
- All touched docs include front matter with `author` and `attribution`.
