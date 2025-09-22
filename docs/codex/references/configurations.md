# Configuration Reference

**Updated**: 2025-09-22

Reference for all configuration files in the Realm system.

## Configuration Files

### .JSON Files

- **`config/system_metrics.json`** (2.4KB)
- **`grafana/dashboards/arcanum.json`** (2.1KB)
- **`grafana/dashboards/realm-observability.json`** (4.4KB)
- **`reports/media_inventory_20250922_132909.json`** (0.2KB)
- **`reports/security_report_20250922_132909.json`** (0.2KB)
- **`reports/service_audit_20250922_131741.json`** (26.3KB)
- **`reports/service_audit_20250922_132908.json`** (24.6KB)
- **`schemas/agent.spec.v1.json`** (6.4KB)
- **`schemas/output.default.json`** (0.8KB)
- **`schemas/tool.code_diff.json`** (0.3KB)
- **`schemas/tool.retrieval_batch.json`** (0.4KB)
- **`schemas/tool.search.json`** (0.4KB)
- **`services/arcanum-orchestrator/contract.json`** (0.2KB)
- **`services/arcanum-orchestrator/schemas/output.default.json`** (0.8KB)
### .YAML Files

- **`agents/claude_sonnet.yaml`** (0.8KB)
- **`agents/gemini_flash.yaml`** (0.7KB)
- **`config/agent_registry.yaml`** (0.7KB)
- **`config/alerts.yaml`** (1.0KB)
- **`config/environments/dev/arcanum.yaml`** (0.8KB)
- **`config/environments/prod/arcanum.yaml`** (0.8KB)
- **`loki/loki-config.yaml`** (0.8KB)
- **`loki/promtail-config.yaml`** (1.1KB)
- **`services/arcanum-orchestrator/docker-compose.yaml`** (1.1KB)
- **`services/vaultwarden/docker-compose.yaml`** (0.7KB)
### .YML Files

- **`alertmanager/config.yml`** (1.4KB)
- **`docker-compose.yml`** (4.5KB)
- **`grafana/provisioning/dashboards/dashboards.yml`** (0.2KB)
- **`grafana/provisioning/datasources/datasource.yml`** (0.8KB)
- **`mkdocs.yml`** (1.9KB)
- **`prometheus/alert_rules.yml`** (4.2KB)
- **`prometheus/prometheus.yml`** (0.9KB)
- **`realm.yml`** (0.9KB)

## Key Configuration Files

### Docker & Services
- `docker-compose.yml` - Main service orchestration
- `prometheus/prometheus.yml` - Metrics collection config
- `grafana/provisioning/` - Dashboard and datasource configs

### Documentation
- `mkdocs.yml` - Documentation site configuration
- `.github/workflows/` - Automation workflows

### Scripts & Tools
- `config/` - Tool-specific configurations
- `schemas/` - Validation schemas

---
*Auto-generated from file system scan*
