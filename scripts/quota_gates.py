#!/usr/bin/env python3
"""
Phase 5: Quota and Pruning Gates
Automated cleanup and storage management
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class QuotaGates:
    def __init__(self):
        self.config = {
            'storage_limits': {
                'downloads': {'quota_gb': 50, 'auto_prune_days': 30},
                'temp': {'quota_gb': 10, 'auto_prune_days': 7},
                'logs': {'quota_gb': 5, 'auto_prune_days': 90},
                'docker_volumes': {'quota_gb': 20, 'auto_prune_days': 30}
            },
            'file_patterns': {
                'temporary': ['.tmp', '.temp', '.cache', '.DS_Store'],
                'large_archives': ['.tar.gz', '.zip', '.7z'],
                'duplicates': ['copy', 'duplicate', '(1)', '(2)']
            }
        }

    def check_quotas(self) -> Dict[str, Any]:
        """Check storage quotas and recommend actions"""
        results = {'checks': {}, 'actions_needed': []}

        for path_name, limits in self.config['storage_limits'].items():
            path = Path.home() / path_name.replace('_', '-')  # downloads, temp, etc.
            if path.exists():
                usage = self._calculate_directory_size(path)
                usage_gb = usage / (1024**3)

                results['checks'][path_name] = {
                    'path': str(path),
                    'usage_gb': usage_gb,
                    'quota_gb': limits['quota_gb'],
                    'usage_percent': (usage_gb / limits['quota_gb']) * 100,
                    'over_quota': usage_gb > limits['quota_gb']
                }

                if usage_gb > limits['quota_gb']:
                    results['actions_needed'].append({
                        'action': 'prune',
                        'path': str(path),
                        'excess_gb': usage_gb - limits['quota_gb']
                    })

        return results

    def _calculate_directory_size(self, path: Path) -> int:
        """Calculate total size of directory"""
        total = 0
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total += file_path.stat().st_size
        except PermissionError:
            pass
        return total

    def auto_prune(self, dry_run: bool = True) -> Dict[str, Any]:
        """Auto-prune old files based on rules"""
        actions = {'files_removed': 0, 'space_freed_gb': 0, 'actions': []}

        downloads_path = Path.home() / "Downloads"
        if downloads_path.exists():
            cutoff = datetime.now() - timedelta(days=30)

            for file_path in downloads_path.rglob("*"):
                if file_path.is_file():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff:
                        size_gb = file_path.stat().st_size / (1024**3)
                        actions['actions'].append({
                            'action': 'remove',
                            'file': str(file_path),
                            'age_days': (datetime.now() - mtime).days,
                            'size_gb': size_gb
                        })

                        if not dry_run:
                            file_path.unlink()
                            actions['files_removed'] += 1
                            actions['space_freed_gb'] += size_gb

        return actions

def main():
    gates = QuotaGates()
    command = sys.argv[1] if len(sys.argv) > 1 else 'check'

    if command == 'check':
        results = gates.check_quotas()
        print("📊 Quota Status:")
        for name, check in results['checks'].items():
            status = "❌ OVER" if check['over_quota'] else "✅ OK"
            print(f"  {name}: {check['usage_gb']:.1f}GB / {check['quota_gb']}GB {status}")

    elif command == 'prune':
        dry_run = '--live' not in sys.argv
        results = gates.auto_prune(dry_run)
        print(f"🧹 Prune Results ({'DRY RUN' if dry_run else 'LIVE'}):")
        print(f"  Files to remove: {len(results['actions'])}")
        print(f"  Space to free: {results['space_freed_gb']:.2f}GB")

if __name__ == "__main__":
    main()