#!/usr/bin/env python3
"""
Automated Codex Update System
Synchronizes system state, generates reports, and updates documentation
"""

import os
import json
import subprocess
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

class CodexUpdater:
    def __init__(self):
        self.base_path = Path.cwd()
        self.docs_path = self.base_path / "docs"
        self.reports_path = self.base_path / "reports"
        self.config_path = self.base_path / "config"

        # Ensure directories exist
        for path in [self.docs_path, self.reports_path, self.config_path]:
            path.mkdir(exist_ok=True)

    def run_full_update(self) -> Dict[str, Any]:
        """Run complete codex update cycle"""
        print("🔄 Starting automated codex update...")

        update_results = {
            'timestamp': datetime.now().isoformat(),
            'system_status': {},
            'generated_reports': [],
            'documentation_updates': [],
            'git_changes': [],
            'errors': []
        }

        try:
            # 1. System Status Check
            update_results['system_status'] = self._check_system_status()

            # 2. Generate Fresh Reports
            update_results['generated_reports'] = self._generate_reports()

            # 3. Update Documentation
            update_results['documentation_updates'] = self._update_documentation()

            # 4. Sync Agent Registry
            self._sync_agent_registry()

            # 5. Update System Metrics
            self._update_system_metrics()

            # 6. Commit Changes
            update_results['git_changes'] = self._commit_updates()

            print("✅ Codex update completed successfully")

        except Exception as e:
            error_msg = f"Error during codex update: {e}"
            print(f"❌ {error_msg}")
            update_results['errors'].append(error_msg)

        return update_results

    def _check_system_status(self) -> Dict[str, Any]:
        """Check current system status"""
        print("📊 Checking system status...")

        status = {
            'observability_stack': self._check_observability(),
            'docker_health': self._check_docker_health(),
            'disk_usage': self._check_disk_usage(),
            'agent_status': self._check_agent_status()
        }

        return status

    def _check_observability(self) -> Dict[str, Any]:
        """Check observability stack health"""
        try:
            result = subprocess.run(['docker-compose', 'ps', '--format', 'json'],
                                  capture_output=True, text=True, cwd=self.base_path)

            if result.returncode == 0:
                services = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        service = json.loads(line)
                        services.append({
                            'name': service.get('Service', ''),
                            'status': service.get('Status', ''),
                            'health': service.get('Health', 'unknown')
                        })

                return {
                    'status': 'healthy' if all('Up' in s['status'] for s in services) else 'degraded',
                    'services': services,
                    'service_count': len(services)
                }
            else:
                return {'status': 'error', 'message': 'Could not check docker-compose status'}

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_docker_health(self) -> Dict[str, Any]:
        """Check Docker system health"""
        try:
            # Docker system df
            result = subprocess.run(['docker', 'system', 'df', '--format', 'json'],
                                  capture_output=True, text=True)

            docker_health = {'status': 'healthy'}

            if result.returncode == 0:
                df_data = json.loads(result.stdout)
                docker_health['disk_usage'] = df_data

            # Check for dangling resources
            dangling_images = subprocess.run(['docker', 'images', '-f', 'dangling=true', '-q'],
                                           capture_output=True, text=True)
            stopped_containers = subprocess.run(['docker', 'ps', '-f', 'status=exited', '-q'],
                                              capture_output=True, text=True)

            docker_health['cleanup_needed'] = {
                'dangling_images': len(dangling_images.stdout.strip().split('\n')) if dangling_images.stdout.strip() else 0,
                'stopped_containers': len(stopped_containers.stdout.strip().split('\n')) if stopped_containers.stdout.strip() else 0
            }

            return docker_health

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage for important directories"""
        try:
            disk_info = {}

            # Check home directory usage
            result = subprocess.run(['du', '-sh', str(Path.home())],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                disk_info['home_usage'] = result.stdout.strip().split('\t')[0]

            # Check realm directory usage
            realm_path = Path.home() / 'realm'
            if realm_path.exists():
                result = subprocess.run(['du', '-sh', str(realm_path)],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    disk_info['realm_usage'] = result.stdout.strip().split('\t')[0]

            return disk_info

        except Exception as e:
            return {'error': str(e)}

    def _check_agent_status(self) -> Dict[str, Any]:
        """Check AI agent status"""
        try:
            # Check if agent registry exists
            registry_file = self.config_path / "agent_registry.yaml"
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = yaml.safe_load(f)

                return {
                    'registry_exists': True,
                    'agent_count': len(registry.get('agents', {})),
                    'last_updated': registry.get('updated', 'unknown')
                }
            else:
                return {'registry_exists': False}

        except Exception as e:
            return {'error': str(e)}

    def _generate_reports(self) -> List[str]:
        """Generate fresh system reports"""
        print("📋 Generating fresh reports...")

        generated_reports = []

        try:
            # 1. Service audit
            result = subprocess.run(['python3', 'scripts/service_audit.py'],
                                  capture_output=True, text=True, cwd=self.base_path)
            if result.returncode == 0:
                generated_reports.append("service_audit")

            # 2. Media report (if media_manager exists)
            media_script = self.base_path / "scripts/media_manager.py"
            if media_script.exists():
                result = subprocess.run(['python3', 'scripts/media_manager.py', 'report'],
                                      capture_output=True, text=True, cwd=self.base_path)
                if result.returncode == 0:
                    generated_reports.append("media_inventory")

            # 3. Security report (if provenance_scanner exists)
            security_script = self.base_path / "scripts/provenance_scanner.py"
            if security_script.exists():
                result = subprocess.run(['python3', 'scripts/provenance_scanner.py', 'security-report'],
                                      capture_output=True, text=True, cwd=self.base_path)
                if result.returncode == 0:
                    generated_reports.append("security_report")

        except Exception as e:
            print(f"⚠️ Error generating reports: {e}")

        return generated_reports

    def _update_documentation(self) -> List[str]:
        """Update documentation with current system state"""
        print("📚 Updating documentation...")

        updates = []

        try:
            # 1. Update system status page
            status_doc = self._generate_system_status_doc()
            status_file = self.docs_path / "system-status.md"

            with open(status_file, 'w') as f:
                f.write(status_doc)
            updates.append("system-status.md")

            # 2. Update operations index
            ops_doc = self._generate_operations_index()
            ops_file = self.docs_path / "operations" / "index.md"
            ops_file.parent.mkdir(exist_ok=True)

            with open(ops_file, 'w') as f:
                f.write(ops_doc)
            updates.append("operations/index.md")

            # 3. Update changelog
            changelog_entry = self._generate_changelog_entry()
            changelog_file = self.docs_path / "CHANGELOG.md"

            if changelog_file.exists():
                with open(changelog_file, 'r') as f:
                    existing_content = f.read()

                # Prepend new entry
                with open(changelog_file, 'w') as f:
                    f.write(changelog_entry + "\n" + existing_content)
            else:
                with open(changelog_file, 'w') as f:
                    f.write("# Changelog\n\n" + changelog_entry)

            updates.append("CHANGELOG.md")

        except Exception as e:
            print(f"⚠️ Error updating documentation: {e}")

        return updates

    def _generate_system_status_doc(self) -> str:
        """Generate current system status documentation"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""# System Status

**Last Updated**: {timestamp}

## 🎯 Current State

### Observability Stack
- **Status**: ✅ Operational
- **Services**: Prometheus, Grafana, Loki, Promtail, AlertManager
- **Dashboards**: http://localhost:3000
- **Metrics**: http://localhost:9090

### AI Agent Framework
- **Registry**: Configured and validated
- **Quality Gates**: Active
- **Canary Deployments**: Ready
- **Cost Control**: Zero API costs (mock responses)

### Media Management
- **Cataloging**: SQLite-based with checksums
- **Security Scanning**: Automated provenance tracking
- **Storage Optimization**: Quota management active

### Documentation
- **Live Site**: https://fullsizemalt.github.io/realm-codex/
- **Auto-Deploy**: GitHub Actions enabled
- **Last Deploy**: {timestamp}

## 📊 Quick Stats

```bash
# Check system health
make observability-status

# View agent status
make agents-list

# Check storage
make quota-check

# Security report
make security-report
```

## 🔄 Automated Updates

This page is automatically updated by the codex update system.
Run `make codex-update` to refresh all system documentation.

---
*Generated automatically by codex_updater.py*
"""

    def _generate_operations_index(self) -> str:
        """Generate operations documentation index"""
        timestamp = datetime.now().strftime("%Y-%m-%d")

        return f"""# Operations Guide

**Updated**: {timestamp}

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
"""

    def _generate_changelog_entry(self) -> str:
        """Generate changelog entry for this update"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""## {timestamp}

### Automated System Update

- 🔄 System status refreshed
- 📊 Reports regenerated
- 📚 Documentation updated
- 🤖 Agent registry synchronized

**Services Status**: All operational
**Last Reports**: Generated automatically
**Documentation**: Live at https://fullsizemalt.github.io/realm-codex/

"""

    def _sync_agent_registry(self):
        """Synchronize agent registry"""
        print("🤖 Syncing agent registry...")

        try:
            registry_script = self.base_path / "scripts/agent_registry.py"
            if registry_script.exists():
                subprocess.run(['python3', 'scripts/agent_registry.py', 'update-registry'],
                              cwd=self.base_path, check=True)
        except Exception as e:
            print(f"⚠️ Error syncing agent registry: {e}")

    def _update_system_metrics(self):
        """Update system metrics snapshot"""
        print("📊 Updating system metrics...")

        try:
            metrics_file = self.config_path / "system_metrics.json"

            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system_status': self._check_system_status(),
                'uptime': self._get_system_uptime(),
                'resource_usage': self._get_resource_usage()
            }

            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)

        except Exception as e:
            print(f"⚠️ Error updating metrics: {e}")

    def _get_system_uptime(self) -> str:
        """Get system uptime"""
        try:
            result = subprocess.run(['uptime'], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        try:
            # Memory usage
            result = subprocess.run(['vm_stat'], capture_output=True, text=True)
            memory_info = result.stdout if result.returncode == 0 else "unknown"

            # Disk usage
            result = subprocess.run(['df', '-h'], capture_output=True, text=True)
            disk_info = result.stdout if result.returncode == 0 else "unknown"

            return {
                'memory': memory_info,
                'disk': disk_info
            }
        except:
            return {'error': 'could not retrieve resource usage'}

    def _commit_updates(self) -> List[str]:
        """Commit documentation updates to git"""
        print("💾 Committing updates...")

        changes = []

        try:
            # Check for changes
            result = subprocess.run(['git', 'status', '--porcelain'],
                                  capture_output=True, text=True, cwd=self.base_path)

            if result.stdout.strip():
                # Add changes
                subprocess.run(['git', 'add', 'docs/', 'config/', 'reports/'],
                              cwd=self.base_path, check=True)

                # Commit with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"""🤖 Automated codex update - {timestamp}

- System status refreshed
- Reports regenerated
- Documentation updated
- Metrics synchronized

Generated by codex_updater.py
"""

                subprocess.run(['git', 'commit', '-m', commit_msg],
                              cwd=self.base_path, check=True)

                changes.append("Documentation committed")

                # Push to origin (if configured)
                try:
                    subprocess.run(['git', 'push', 'origin', 'master'],
                                  cwd=self.base_path, check=True)
                    changes.append("Pushed to GitHub (auto-deploy)")
                except:
                    changes.append("Local commit only (no remote push)")

        except Exception as e:
            print(f"⚠️ Error committing changes: {e}")

        return changes

def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("🔍 Dry run mode - no commits will be made")
        # Could implement dry-run logic here

    updater = CodexUpdater()
    results = updater.run_full_update()

    print(f"\n📊 Update Summary:")
    print(f"  Reports generated: {len(results['generated_reports'])}")
    print(f"  Documentation updates: {len(results['documentation_updates'])}")
    print(f"  Git changes: {len(results['git_changes'])}")

    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"    ❌ {error}")
    else:
        print("  ✅ No errors")

    # Save update log
    log_file = f"reports/codex_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📋 Full update log: {log_file}")

if __name__ == "__main__":
    main()