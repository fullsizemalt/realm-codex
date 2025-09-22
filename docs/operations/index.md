# Operations Guide

**Updated**: 2025-09-22

## 🚀 Daily Operations

### System Health
```bash
make observability-status    # Check all services
make service-audit          # Audit running containers
make quota-check           # Storage usage
```

### Maintenance
```bash
make quick-cleanup         # Remove temp files
make docker-cleanup        # Clean Docker resources
make agents-quality        # Validate AI agents
```

### Monitoring
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## 📋 Weekly Tasks

1. **System Cleanup**: `make quick-cleanup`
2. **Security Scan**: `make security-report`
3. **Storage Review**: `make find-duplicates`
4. **Service Audit**: `make service-audit`

## 🔄 Automation

### Auto-Updates
- **Documentation**: Commits auto-deploy to GitHub Pages
- **Reports**: Generated daily via codex updater
- **Monitoring**: Continuous via Prometheus alerts

### Manual Updates
```bash
make codex-update          # Full system update
```

## 📚 Reference

- [Phase Summaries](../refactor/)
- [System Status](../system-status.md)
- [Changelog](../CHANGELOG.md)

---
*This guide is automatically maintained by the codex update system.*
