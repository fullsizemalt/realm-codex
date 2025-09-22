# Tools Documentation

**Updated**: 2025-09-22

Documentation for all scripts and tools in the Realm system.

## Available Tools

- [quota_gates.py](quota_gates.md): Phase 5: Quota and Pruning Gates
Automated cleanup and storage management
- [agent_canary.py](agent_canary.md): Phase 4 AI Agents: Canary deployment system for agent configurations
Safely deploy agent changes with automatic rollback on SLO violations
- [secrets_manager.py](secrets_manager.md): Phase 2 GitOps: Simple secrets management for Vaultwarden
Provides a CLI interface to store/retrieve secrets from Vaultwarden API
- [agent_registry.py](agent_registry.md): Phase 4 AI Agents: Agent Registry and Management System
Handles agent specifications, validation, and deployment
- [content_ingester.py](content_ingester.md): Codex Content Population System
Ingests, processes, and organizes knowledge for the realm codex
- [media_manager.py](media_manager.md): Phase 5: Media & Seedbox Hardening
Comprehensive media file management with rclone, checksums, and provenance tracking
- [alert_manager.py](alert_manager.md): Phase 1 Guardrail: Simple alert manager for realm services
Reads config/alerts.yaml and sends notifications based on monitoring results
- [agent_quality_gates.py](agent_quality_gates.md): Phase 4 AI Agents: Quality Gates for Agent Deployments
Automated checks to ensure agents meet standards before deployment
- [provenance_scanner.py](provenance_scanner.md): Phase 5: Provenance Scanner
Track file origins, detect duplicates, extract metadata for audit trails
- [legacy_scanner.py](legacy_scanner.md): Phase 6: Legacy System Scanner
Identify dead scripts, unused services, and security risks for decommissioning
- [codex_updater.py](codex_updater.md): Automated Codex Update System
Synchronizes system state, generates reports, and updates documentation
- [issue_to_chronicle.py](issue_to_chronicle.md): ---
title: "Handoff — {issue_title}"
author: "{issue_user}"
date: "{closed_at}"
realm: "<realm-slug>"
env: "all"
attribution:
  - source: "https://github.com/{repo_full}/issues/{issue_number}"
    description: "handoff issue"
---

## State
{state or "(none provided)"}

## Next Focus
{next_focus or "(none provided)"}

## Ask
{ask or "(none provided)"}

---
- [service_audit.py](service_audit.md): Phase 6: Service Audit
Identify running services and containers for decommissioning assessment
- [validate_config.py](validate_config.md): Phase 1 Guardrail: Configuration validation gates
Validates YAML configuration files before deployment
- [gitops_deploy.py](gitops_deploy.md): Phase 2 GitOps: Pull-based deployment system
Deploys services based on environment-specific configurations
- [quick_cleanup.py](quick_cleanup.md): Phase 6: Quick Cleanup Script
Fast cleanup of obvious waste and legacy items
- [self_healing.py](self_healing.md): Phase 3 Self-Healing: Automated remediation system
Listens for alerts and triggers appropriate remediation actions
- [new_refactor_task.py](new_refactor_task.md): # {title}

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
- [migrate_to_secrets.py](migrate_to_secrets.md): Phase 2 GitOps: Migrate arcanum service from env vars to secrets management
- [setup_cron.py](setup_cron.md): Setup local cron job for automated codex updates
