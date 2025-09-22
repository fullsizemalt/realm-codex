# Realm Refactor: Phase 4 AI Agent Management
# Unified commands for agent lifecycle management

.PHONY: help agents-list agents-validate agents-deploy agents-canary agents-quality observability-start weave docs serve

help:
	@echo "🤖 AI Agent Management Commands:"
	@echo ""
	@echo "Agent Registry:"
	@echo "  make agents-list                 - List all agents"
	@echo "  make agents-validate             - Validate all agent specs"
	@echo "  make agents-update-registry      - Update central registry"
	@echo ""
	@echo "Quality Gates:"
	@echo "  make agents-quality              - Run quality gates for all agents"
	@echo "  make agents-quality-single AGENT=<name> - Run quality gates for specific agent"
	@echo "  make agents-standards            - Show quality standards"
	@echo ""
	@echo "Canary Deployments:"
	@echo "  make agents-canary-list          - List active canary deployments"
	@echo "  make agents-canary-deploy AGENT=<name> CONFIG=<file> - Deploy canary"
	@echo "  make agents-canary-promote ID=<deployment_id> - Promote canary"
	@echo "  make agents-canary-rollback ID=<deployment_id> - Rollback canary"
	@echo "  make agents-canary-check         - Check for expired deployments"
	@echo ""
	@echo "Media & Storage:"
	@echo "  make media-scan                  - Scan media directories with checksums"
	@echo "  make media-report                - Generate media inventory report"
	@echo "  make quota-check                 - Check storage quotas"
	@echo "  make quota-prune                 - Auto-prune old files"
	@echo "  make find-duplicates             - Find duplicate files"
	@echo "  make security-report             - Generate security/privacy report"
	@echo ""
	@echo "Cleanup & Decommission:"
	@echo "  make service-audit               - Audit running services and containers"
	@echo "  make quick-cleanup               - Quick cleanup of temp files and old downloads"
	@echo "  make legacy-scan                 - Scan for legacy files and security risks"
	@echo "  make cleanup-dead                - Remove dead files (dry-run by default)"
	@echo "  make docker-cleanup              - Clean all Docker resources"
	@echo ""
	@echo "Codex Automation:"
	@echo "  make codex-update                - Full automated codex update"
	@echo "  make codex-update-dry            - Dry run codex update"
	@echo "  make codex-status                - Show current codex status"
	@echo "  make setup-automation            - Install local cron automation"
	@echo "  make automation-status           - Check automation status"
	@echo ""
	@echo "Observability:"
	@echo "  make observability-start         - Start monitoring stack"
	@echo "  make observability-stop          - Stop monitoring stack"
	@echo "  make observability-status        - Check stack status"

# Agent Registry Commands
agents-list:
	@python3 scripts/agent_registry.py list

agents-validate:
	@python3 scripts/agent_registry.py validate-all

agents-update-registry:
	@python3 scripts/agent_registry.py update-registry

# Quality Gates Commands
agents-quality:
	@python3 scripts/agent_quality_gates.py batch-check

agents-quality-single:
	@if [ -z "$(AGENT)" ]; then echo "❌ AGENT parameter required"; exit 1; fi
	@python3 scripts/agent_quality_gates.py check $(AGENT)

agents-standards:
	@python3 scripts/agent_quality_gates.py standards

# Canary Deployment Commands
agents-canary-list:
	@python3 scripts/agent_canary.py list

agents-canary-deploy:
	@if [ -z "$(AGENT)" ] || [ -z "$(CONFIG)" ]; then echo "❌ AGENT and CONFIG parameters required"; exit 1; fi
	@python3 scripts/agent_canary.py deploy $(AGENT) $(CONFIG)

agents-canary-promote:
	@if [ -z "$(ID)" ]; then echo "❌ ID parameter required"; exit 1; fi
	@python3 scripts/agent_canary.py promote $(ID)

agents-canary-rollback:
	@if [ -z "$(ID)" ]; then echo "❌ ID parameter required"; exit 1; fi
	@python3 scripts/agent_canary.py rollback $(ID)

agents-canary-check:
	@python3 scripts/agent_canary.py check-expired

# Media & Storage Commands
media-scan:
	@python3 scripts/media_manager.py scan

media-report:
	@python3 scripts/media_manager.py report

quota-check:
	@python3 scripts/quota_gates.py check

quota-prune:
	@python3 scripts/quota_gates.py prune

provenance-scan:
	@if [ -z "$(PATH)" ]; then echo "❌ PATH parameter required"; exit 1; fi
	@python3 scripts/provenance_scanner.py scan-provenance $(PATH)

find-duplicates:
	@python3 scripts/provenance_scanner.py find-duplicates "$(HOME)/Downloads,$(HOME)/Documents"

security-report:
	@python3 scripts/provenance_scanner.py security-report

# Observability Commands
observability-start:
	@echo "🚀 Starting observability stack..."
	@docker-compose up -d prometheus grafana loki promtail alertmanager
	@echo "✅ Stack started. Access:"
	@echo "  • Grafana: http://localhost:3000 (admin/admin)"
	@echo "  • Prometheus: http://localhost:9090"
	@echo "  • AlertManager: http://localhost:9093"

observability-stop:
	@echo "🛑 Stopping observability stack..."
	@docker-compose down

observability-status:
	@echo "📊 Observability Stack Status:"
	@docker-compose ps prometheus grafana loki promtail alertmanager

# Phase 6: Cleanup & Decommission Commands
service-audit:
	@python3 scripts/service_audit.py

quick-cleanup:
	@python3 scripts/quick_cleanup.py

legacy-scan:
	@python3 scripts/legacy_scanner.py scan

cleanup-dead:
	@python3 scripts/legacy_scanner.py cleanup-dead

docker-cleanup:
	@echo "🐳 Cleaning Docker resources..."
	@docker container prune -f
	@docker image prune -f
	@docker volume prune -f
	@docker network prune -f

# Codex Automation Commands
codex-update:
	@echo "🤖 Running full codex update..."
	@python3 scripts/codex_updater.py

codex-update-dry:
	@echo "🔍 Running codex update (dry run)..."
	@python3 scripts/codex_updater.py --dry-run

codex-status:
	@echo "📊 Current Codex Status:"
	@echo "  Live Documentation: https://fullsizemalt.github.io/realm-codex/"
	@echo "  Last Update: $$(git log -1 --pretty=format:'%ci' -- docs/)"
	@echo "  Observability: $$(docker-compose ps --services | wc -l | xargs echo) services"
	@echo "  Reports: $$(ls reports/ 2>/dev/null | wc -l | xargs echo) generated"
	@if [ -f config/system_metrics.json ]; then \
		echo "  Metrics: Available"; \
	else \
		echo "  Metrics: Not generated"; \
	fi

setup-automation:
	@echo "🤖 Setting up codex automation..."
	@python3 scripts/setup_cron.py install

automation-status:
	@python3 scripts/setup_cron.py status

# Legacy Commands
weave:
	python3 scripts/apply_realm_config.py

docs:
	pip install mkdocs-material pyyaml
	mkdocs build

serve:
	pip install mkdocs-material pyyaml
	mkdocs serve -a 0.0.0.0:8000
