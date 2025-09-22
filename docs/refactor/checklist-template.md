---
attribution:
- Attribution Details
author:
- Your Name/Alias
date: 2025-09-22
env: all
realm:
- Realm Name
title: Refactor Checklist (Template)
---

# Refactor Checklist (Template)

**Service/Subsystem:**  
**Owner:**  
**Env(s):** dev/stg/prod  
**Date:**  

## DoD
- [ ] Containerized with health check and limits
- [ ] Logs → Loki, metrics → Prometheus, alerts defined
- [ ] Config & secrets externalized (Vault/Vaultwarden)
- [ ] GitOps pipeline (+ staging + canary + rollback)
- [ ] Runbook updated in MkDocs
- [ ] Ops Journal entry added

## Risks & Mitigation
- [ ] Rollback plan
- [ ] Backup verified before change
- [ ] Approvals for irreversible actions

## Notes
- ...
