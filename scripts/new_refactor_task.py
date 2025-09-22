#!/usr/bin/env python3
import sys, os, datetime, textwrap
if len(sys.argv) < 3:
    print("Usage: scripts/new_refactor_task.py <svc/mod> <short-title>")
    sys.exit(1)

slug = sys.argv[1].replace("/", "-")
title = " ".join(sys.argv[2:])
date = datetime.date.today().isoformat()

path = f"docs/refactor/tasks/{date}-{slug}.md"
os.makedirs(os.path.dirname(path), exist_ok=True)
content = f"""# {title}

**Service/Subsystem:** {sys.argv[1]}
**Date:** {date}

## DoD
- [ ] Containerized with health check and limits
- [ ] Logs→Loki, metrics→Prometheus, alerts
- [ ] Config & secrets externalized (Vault/Vaultwarden)
- [ ] GitOps pipeline (+ staging + canary + rollback)
- [ ] Runbook updated in MkDocs
- [ ] Ops Journal entry added

## Plan
- Steps...

## Risk & Rollback
- ...

## Links
- Issue: 
- PR: 
- Dashboard: 
"""
open(path, "w", encoding="utf-8").write(content)
print(f"Created {path}")
