# Command Reference

**Updated**: 2025-09-22

Complete reference for all available commands in the Realm system.

## Agent Registry

### `make agents`
list                 - List all agents

### `make agents`
validate             - Validate all agent specs

### `make agents`
update-registry      - Update central registry

## Quality Gates

### `make agents`
quality              - Run quality gates for all agents

### `make agents`
quality-single AGENT=<name> - Run quality gates for specific agent

### `make agents`
standards            - Show quality standards

## Canary Deployments

### `make agents`
canary-list          - List active canary deployments

### `make agents`
canary-deploy AGENT=<name> CONFIG=<file> - Deploy canary

### `make agents`
canary-promote ID=<deployment_id> - Promote canary

### `make agents`
canary-rollback ID=<deployment_id> - Rollback canary

### `make agents`
canary-check         - Check for expired deployments

## Media & Storage

### `make media`
scan                  - Scan media directories with checksums

### `make media`
report                - Generate media inventory report

### `make quota`
check                 - Check storage quotas

### `make quota`
prune                 - Auto-prune old files

### `make find`
duplicates             - Find duplicate files

### `make security`
report             - Generate security/privacy report

## Cleanup & Decommission

### `make service`
audit               - Audit running services and containers

### `make quick`
cleanup               - Quick cleanup of temp files and old downloads

### `make legacy`
scan                 - Scan for legacy files and security risks

### `make cleanup`
dead                - Remove dead files (dry-run by default)

### `make docker`
cleanup              - Clean all Docker resources

## Codex Automation

### `make codex`
update                - Full automated codex update

### `make codex`
update-dry            - Dry run codex update

### `make codex`
status                - Show current codex status

### `make setup`
automation            - Install local cron automation

### `make automation`
status           - Check automation status

## Observability

### `make observability`
start         - Start monitoring stack

### `make observability`
stop          - Stop monitoring stack

### `make observability`
status        - Check stack status

## Usage Examples

```bash
# Check system status
make observability-status

# Run complete health check
make service-audit
make agents-quality
make security-report

# Perform maintenance
make quick-cleanup
make docker-cleanup

# Update documentation
make codex-update
```

---
*Auto-generated from Makefile*
