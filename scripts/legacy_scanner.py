#!/usr/bin/env python3
"""
Phase 6: Legacy System Scanner
Identify dead scripts, unused services, and security risks for decommissioning
"""

import os
import re
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

class LegacyScanner:
    def __init__(self):
        self.scan_results = {
            'dead_scripts': [],
            'unused_services': [],
            'security_risks': [],
            'large_files': [],
            'old_backups': [],
            'deprecated_configs': [],
            'orphaned_processes': [],
            'recommendations': []
        }

        # Common patterns for dead/legacy files
        self.dead_patterns = [
            r'.*\.bak$', r'.*\.old$', r'.*\.tmp$', r'.*~$',
            r'.*\.backup$', r'.*\.orig$', r'.*copy.*', r'.*Copy.*'
        ]

        # Risky file patterns
        self.risky_patterns = [
            r'.*\.key$', r'.*\.pem$', r'.*\.p12$', r'.*\.pfx$',
            r'.*password.*', r'.*secret.*', r'.*\.env.*'
        ]

    def scan_system(self, scan_paths: List[Path] = None) -> Dict[str, Any]:
        """Comprehensive legacy system scan"""
        print("🔍 Starting Phase 6 legacy system scan...")

        if not scan_paths:
            scan_paths = [
                Path.home(),
                Path('/usr/local/bin'),
                Path('/opt'),
                Path('/Applications') if Path('/Applications').exists() else None
            ]
            scan_paths = [p for p in scan_paths if p and p.exists()]

        # 1. Scan for dead scripts and files
        self._scan_dead_files(scan_paths)

        # 2. Check running processes and services
        self._scan_running_processes()

        # 3. Find large files and old backups
        self._scan_large_files(scan_paths)

        # 4. Security risk assessment
        self._scan_security_risks(scan_paths)

        # 5. Docker cleanup opportunities
        self._scan_docker_cleanup()

        # 6. Generate recommendations
        self._generate_recommendations()

        return self.scan_results

    def _scan_dead_files(self, scan_paths: List[Path]):
        """Find dead scripts, backup files, and unused configs"""
        print("🗑️ Scanning for dead files and scripts...")

        for scan_path in scan_paths:
            try:
                for file_path in scan_path.rglob("*"):
                    if file_path.is_file():
                        # Skip system directories and hidden files in /usr
                        if any(skip in str(file_path) for skip in ['/usr/', '/System/', '/.git/']):
                            continue

                        file_str = str(file_path)

                        # Check for dead file patterns
                        for pattern in self.dead_patterns:
                            if re.match(pattern, file_str):
                                self.scan_results['dead_scripts'].append({
                                    'path': file_str,
                                    'size_mb': file_path.stat().st_size / (1024*1024),
                                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                    'pattern': pattern
                                })
                                break

                        # Check for old files (>6 months) in temp-like directories
                        if any(temp_dir in file_str.lower() for temp_dir in ['tmp', 'temp', 'cache', 'downloads']):
                            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if mod_time < datetime.now() - timedelta(days=180):
                                self.scan_results['dead_scripts'].append({
                                    'path': file_str,
                                    'size_mb': file_path.stat().st_size / (1024*1024),
                                    'modified': mod_time.isoformat(),
                                    'reason': 'old_temp_file'
                                })

            except PermissionError:
                continue
            except Exception as e:
                print(f"⚠️ Error scanning {scan_path}: {e}")

    def _scan_running_processes(self):
        """Check for orphaned or suspicious processes"""
        print("⚙️ Scanning running processes...")

        try:
            # Get running processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.split('\n')[1:]  # Skip header

            suspicious_processes = []
            for process_line in processes:
                if not process_line.strip():
                    continue

                parts = process_line.split(None, 10)
                if len(parts) >= 11:
                    command = parts[10]

                    # Look for suspicious patterns
                    if any(pattern in command.lower() for pattern in [
                        'bitcoin', 'crypto', 'miner', 'torrent',
                        'backdoor', 'keylog', 'rootkit'
                    ]):
                        suspicious_processes.append({
                            'pid': parts[1],
                            'user': parts[0],
                            'command': command,
                            'cpu': parts[2],
                            'mem': parts[3]
                        })

            self.scan_results['orphaned_processes'] = suspicious_processes

        except Exception as e:
            print(f"⚠️ Error scanning processes: {e}")

    def _scan_large_files(self, scan_paths: List[Path]):
        """Find large files and old backups for cleanup"""
        print("📊 Scanning for large files and old backups...")

        large_files = []
        old_backups = []

        for scan_path in scan_paths:
            try:
                for file_path in scan_path.rglob("*"):
                    if file_path.is_file():
                        size_mb = file_path.stat().st_size / (1024*1024)

                        # Large files (>100MB)
                        if size_mb > 100:
                            large_files.append({
                                'path': str(file_path),
                                'size_mb': size_mb,
                                'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                            })

                        # Backup files
                        if any(pattern in str(file_path).lower() for pattern in [
                            'backup', '.tar.gz', '.zip', '.bak', '.dump'
                        ]):
                            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            old_backups.append({
                                'path': str(file_path),
                                'size_mb': size_mb,
                                'age_days': (datetime.now() - mod_time).days,
                                'modified': mod_time.isoformat()
                            })

            except PermissionError:
                continue
            except Exception as e:
                print(f"⚠️ Error scanning {scan_path} for large files: {e}")

        # Sort by size
        self.scan_results['large_files'] = sorted(large_files, key=lambda x: x['size_mb'], reverse=True)[:20]
        self.scan_results['old_backups'] = sorted(old_backups, key=lambda x: x['age_days'], reverse=True)[:20]

    def _scan_security_risks(self, scan_paths: List[Path]):
        """Identify potential security risks"""
        print("🔒 Scanning for security risks...")

        security_risks = []

        for scan_path in scan_paths:
            try:
                for file_path in scan_path.rglob("*"):
                    if file_path.is_file():
                        file_str = str(file_path)

                        # Check for risky file patterns
                        for pattern in self.risky_patterns:
                            if re.match(pattern, file_str.lower()):
                                security_risks.append({
                                    'path': file_str,
                                    'risk_type': 'sensitive_file',
                                    'pattern': pattern,
                                    'size_mb': file_path.stat().st_size / (1024*1024)
                                })
                                break

                        # Check for world-writable files
                        try:
                            mode = file_path.stat().st_mode
                            if mode & 0o002:  # World writable
                                security_risks.append({
                                    'path': file_str,
                                    'risk_type': 'world_writable',
                                    'permissions': oct(mode)
                                })
                        except:
                            pass

            except PermissionError:
                continue
            except Exception as e:
                print(f"⚠️ Error scanning {scan_path} for security risks: {e}")

        self.scan_results['security_risks'] = security_risks[:50]  # Limit results

    def _scan_docker_cleanup(self):
        """Check for Docker cleanup opportunities"""
        print("🐳 Scanning Docker for cleanup opportunities...")

        try:
            # Unused images
            result = subprocess.run(['docker', 'images', '--filter', 'dangling=true', '-q'],
                                  capture_output=True, text=True)
            dangling_images = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

            # Stopped containers
            result = subprocess.run(['docker', 'ps', '-a', '--filter', 'status=exited', '-q'],
                                  capture_output=True, text=True)
            stopped_containers = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

            # Unused volumes
            result = subprocess.run(['docker', 'volume', 'ls', '--filter', 'dangling=true', '-q'],
                                  capture_output=True, text=True)
            unused_volumes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0

            self.scan_results['docker_cleanup'] = {
                'dangling_images': dangling_images,
                'stopped_containers': stopped_containers,
                'unused_volumes': unused_volumes
            }

        except subprocess.CalledProcessError:
            # Docker not available
            self.scan_results['docker_cleanup'] = {'status': 'docker_not_available'}
        except Exception as e:
            print(f"⚠️ Error scanning Docker: {e}")

    def _generate_recommendations(self):
        """Generate cleanup and security recommendations"""
        recommendations = []

        # Dead files cleanup
        if self.scan_results['dead_scripts']:
            total_size = sum(item['size_mb'] for item in self.scan_results['dead_scripts'])
            recommendations.append({
                'priority': 'medium',
                'action': f"Remove {len(self.scan_results['dead_scripts'])} dead files to free {total_size:.1f}MB",
                'command': 'python3 scripts/legacy_scanner.py cleanup-dead --dry-run'
            })

        # Large files review
        if self.scan_results['large_files']:
            total_size = sum(item['size_mb'] for item in self.scan_results['large_files'][:10])
            recommendations.append({
                'priority': 'low',
                'action': f"Review top 10 large files ({total_size:.1f}GB total)",
                'command': 'python3 scripts/legacy_scanner.py review-large'
            })

        # Security risks
        if self.scan_results['security_risks']:
            recommendations.append({
                'priority': 'high',
                'action': f"Address {len(self.scan_results['security_risks'])} security risks",
                'command': 'python3 scripts/legacy_scanner.py fix-security'
            })

        # Docker cleanup
        docker_cleanup = self.scan_results.get('docker_cleanup', {})
        if docker_cleanup.get('dangling_images', 0) > 0:
            recommendations.append({
                'priority': 'low',
                'action': f"Clean {docker_cleanup['dangling_images']} dangling Docker images",
                'command': 'docker image prune -f'
            })

        self.scan_results['recommendations'] = recommendations

    def cleanup_dead_files(self, dry_run: bool = True) -> Dict[str, Any]:
        """Remove dead files identified in scan"""
        if not self.scan_results['dead_scripts']:
            return {'status': 'nothing_to_clean'}

        cleanup_results = {'removed': 0, 'space_freed_mb': 0, 'errors': []}

        for dead_file in self.scan_results['dead_scripts']:
            try:
                file_path = Path(dead_file['path'])
                if file_path.exists():
                    if not dry_run:
                        file_path.unlink()
                        cleanup_results['removed'] += 1
                        cleanup_results['space_freed_mb'] += dead_file['size_mb']
                    else:
                        print(f"Would remove: {dead_file['path']} ({dead_file['size_mb']:.1f}MB)")

            except Exception as e:
                cleanup_results['errors'].append(f"Error removing {dead_file['path']}: {e}")

        return cleanup_results

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate comprehensive legacy scan report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not output_file:
            output_file = f"reports/legacy_scan_{timestamp}.json"

        report = {
            'scan_timestamp': datetime.now().isoformat(),
            'summary': {
                'dead_files': len(self.scan_results['dead_scripts']),
                'security_risks': len(self.scan_results['security_risks']),
                'large_files': len(self.scan_results['large_files']),
                'recommendations': len(self.scan_results['recommendations'])
            },
            'details': self.scan_results
        }

        Path("reports").mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"📋 Legacy scan report saved: {output_file}")
        return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 legacy_scanner.py <command> [args...]")
        print("Commands:")
        print("  scan                  - Run full legacy system scan")
        print("  cleanup-dead [--live] - Remove dead files (dry-run by default)")
        print("  review-large          - Review large files")
        print("  fix-security          - Fix security issues")
        print("  report                - Generate report only")
        sys.exit(1)

    scanner = LegacyScanner()
    command = sys.argv[1]

    if command == "scan":
        results = scanner.scan_system()

        print("\n🎯 Legacy Scan Summary:")
        print(f"  Dead files: {len(results['dead_scripts'])}")
        print(f"  Security risks: {len(results['security_risks'])}")
        print(f"  Large files: {len(results['large_files'])}")
        print(f"  Recommendations: {len(results['recommendations'])}")

        if results['recommendations']:
            print("\n💡 Top Recommendations:")
            for rec in results['recommendations'][:3]:
                priority_emoji = {"high": "🚨", "medium": "⚠️", "low": "💡"}[rec['priority']]
                print(f"  {priority_emoji} {rec['action']}")

        scanner.generate_report()

    elif command == "cleanup-dead":
        scanner.scan_system()
        dry_run = '--live' not in sys.argv
        results = scanner.cleanup_dead_files(dry_run)

        if dry_run:
            print("🧹 Dry run complete. Use --live to actually remove files.")
        else:
            print(f"✅ Removed {results['removed']} files, freed {results['space_freed_mb']:.1f}MB")

    elif command == "review-large":
        scanner.scan_system()
        large_files = scanner.scan_results['large_files'][:10]

        print("📊 Top 10 Largest Files:")
        for i, file_info in enumerate(large_files, 1):
            print(f"  {i}. {file_info['path']} ({file_info['size_mb']:.1f}MB)")

    elif command == "fix-security":
        scanner.scan_system()
        risks = scanner.scan_results['security_risks']

        print("🔒 Security Risks Found:")
        for risk in risks[:10]:
            print(f"  • {risk['risk_type']}: {risk['path']}")
        print("\nReview these files manually and take appropriate action.")

    elif command == "report":
        scanner.scan_system()
        report_file = scanner.generate_report()
        print(f"Report generated: {report_file}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()