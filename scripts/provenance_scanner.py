#!/usr/bin/env python3
"""
Phase 5: Provenance Scanner
Track file origins, detect duplicates, extract metadata for audit trails
"""

import os
import json
import hashlib
import sqlite3
import subprocess
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

class ProvenanceScanner:
    def __init__(self, db_path="media_inventory.db"):
        self.db_path = Path(db_path)
        self._init_provenance_tables()

        # Common download patterns
        self.download_patterns = {
            'browser_downloads': r'.*Downloads.*',
            'torrent_files': r'.*\.torrent$',
            'temp_files': r'.*\.(tmp|temp|partial)$',
            'duplicate_patterns': [r'.*\(\d+\)\..*', r'.*copy.*', r'.*duplicate.*'],
            'suspicious_extensions': ['.exe', '.scr', '.bat', '.cmd', '.com', '.pif']
        }

    def _init_provenance_tables(self):
        """Initialize provenance tracking tables"""
        with sqlite3.connect(self.db_path) as conn:
            # File provenance tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_provenance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    origin_type TEXT,
                    download_url TEXT,
                    download_date TEXT,
                    browser_used TEXT,
                    referrer_domain TEXT,
                    original_filename TEXT,
                    quarantine_status TEXT,
                    risk_score INTEGER DEFAULT 0,
                    scan_date TEXT
                )
            """)

            # Duplicate detection
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_duplicates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    checksum TEXT,
                    file_paths TEXT,
                    file_count INTEGER,
                    total_size_bytes INTEGER,
                    potential_savings_bytes INTEGER,
                    detected_date TEXT
                )
            """)

            # EXIF and metadata
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE,
                    exif_json TEXT,
                    creation_date TEXT,
                    camera_model TEXT,
                    gps_coordinates TEXT,
                    software_used TEXT,
                    privacy_concerns TEXT,
                    extracted_date TEXT
                )
            """)

    def scan_file_provenance(self, file_path: Path) -> Dict[str, Any]:
        """Extract provenance information for a file"""
        provenance_data = {
            'file_path': str(file_path),
            'origin_type': 'unknown',
            'risk_score': 0,
            'download_info': {},
            'quarantine_info': {},
            'scan_date': datetime.now().isoformat()
        }

        try:
            # Check macOS quarantine attributes (download source)
            quarantine_info = self._get_quarantine_attributes(file_path)
            if quarantine_info:
                provenance_data['quarantine_info'] = quarantine_info
                provenance_data['origin_type'] = 'download'

                # Extract download URL and referrer
                if 'download_url' in quarantine_info:
                    provenance_data['download_info']['url'] = quarantine_info['download_url']
                    domain = urlparse(quarantine_info['download_url']).netloc
                    provenance_data['download_info']['domain'] = domain

                    # Risk assessment based on domain
                    provenance_data['risk_score'] = self._assess_domain_risk(domain)

            # Check if file matches download patterns
            file_str = str(file_path).lower()
            for pattern_name, pattern in self.download_patterns.items():
                if pattern_name != 'duplicate_patterns' and re.match(pattern, file_str):
                    if provenance_data['origin_type'] == 'unknown':
                        provenance_data['origin_type'] = pattern_name

            # Check for suspicious characteristics
            if file_path.suffix.lower() in self.download_patterns['suspicious_extensions']:
                provenance_data['risk_score'] += 50

            # Store in database
            self._store_provenance_data(provenance_data)

        except Exception as e:
            print(f"❌ Error scanning provenance for {file_path}: {e}")

        return provenance_data

    def _get_quarantine_attributes(self, file_path: Path) -> Dict[str, Any]:
        """Extract macOS quarantine attributes containing download info"""
        try:
            # Use xattr to get quarantine information
            result = subprocess.run([
                'xattr', '-p', 'com.apple.quarantine', str(file_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                # Parse quarantine string: format is usually like "0083;5f8b9c2d;Safari;download_url"
                quarantine_str = result.stdout.strip()
                parts = quarantine_str.split(';')

                quarantine_data = {
                    'quarantine_raw': quarantine_str,
                    'quarantine_flags': parts[0] if len(parts) > 0 else None,
                    'timestamp': parts[1] if len(parts) > 1 else None,
                    'browser_used': parts[2] if len(parts) > 2 else None,
                }

                # Try to get download URL from other attributes
                url_result = subprocess.run([
                    'xattr', '-p', 'com.apple.metadata:kMDItemWhereFroms', str(file_path)
                ], capture_output=True, text=True)

                if url_result.returncode == 0:
                    # This contains binary plist data, try to extract URLs
                    try:
                        # Convert from binary plist to readable format
                        plist_result = subprocess.run([
                            'plutil', '-convert', 'json', '-o', '-', '-'
                        ], input=url_result.stdout, capture_output=True, text=True)

                        if plist_result.returncode == 0:
                            urls_data = json.loads(plist_result.stdout)
                            if isinstance(urls_data, list) and len(urls_data) > 0:
                                quarantine_data['download_url'] = urls_data[0]
                                if len(urls_data) > 1:
                                    quarantine_data['referrer_url'] = urls_data[1]
                    except:
                        pass

                return quarantine_data

        except Exception:
            pass

        return {}

    def _assess_domain_risk(self, domain: str) -> int:
        """Simple domain risk assessment"""
        risk_score = 0

        # Known safe domains
        safe_domains = [
            'github.com', 'apple.com', 'microsoft.com', 'google.com',
            'adobe.com', 'mozilla.org', 'dropbox.com', 'icloud.com'
        ]

        # Known risky patterns
        risky_patterns = [
            r'.*\.tk$', r'.*\.ml$', r'.*\.ga$',  # Free TLDs
            r'.*bit\.ly.*', r'.*tinyurl.*',       # URL shorteners
            r'.*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}.*'  # IP addresses
        ]

        if domain in safe_domains:
            return 0

        for pattern in risky_patterns:
            if re.match(pattern, domain):
                risk_score += 30

        # Length-based heuristics
        if len(domain) > 50:
            risk_score += 20
        if domain.count('-') > 3:
            risk_score += 10

        return min(risk_score, 100)

    def _store_provenance_data(self, provenance_data: Dict[str, Any]):
        """Store provenance data in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_provenance (
                    file_path, origin_type, download_url, download_date,
                    browser_used, referrer_domain, risk_score, scan_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                provenance_data['file_path'],
                provenance_data['origin_type'],
                provenance_data['download_info'].get('url'),
                provenance_data['quarantine_info'].get('timestamp'),
                provenance_data['quarantine_info'].get('browser_used'),
                provenance_data['download_info'].get('domain'),
                provenance_data['risk_score'],
                provenance_data['scan_date']
            ))

    def extract_exif_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract EXIF data and privacy-sensitive information"""
        metadata = {
            'file_path': str(file_path),
            'exif_data': {},
            'privacy_concerns': [],
            'extracted_date': datetime.now().isoformat()
        }

        try:
            # Use exiftool if available
            result = subprocess.run([
                'exiftool', '-json', '-all', str(file_path)
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                exif_data = json.loads(result.stdout)[0]
                metadata['exif_data'] = exif_data

                # Check for privacy concerns
                privacy_fields = [
                    'GPS*', 'Location*', 'Coordinates',
                    'SerialNumber', 'CameraSerialNumber',
                    'UserComment', 'ImageDescription',
                    'Software', 'ProcessingSoftware'
                ]

                for field, value in exif_data.items():
                    if any(pattern.replace('*', '') in field for pattern in privacy_fields):
                        if 'GPS' in field or 'Location' in field or 'Coordinates' in field:
                            metadata['privacy_concerns'].append(f"Location data: {field}")
                        elif 'Serial' in field:
                            metadata['privacy_concerns'].append(f"Device serial: {field}")
                        elif field in ['Software', 'ProcessingSoftware']:
                            metadata['privacy_concerns'].append(f"Software info: {value}")

                # Store in database
                self._store_metadata(metadata)

        except subprocess.TimeoutExpired:
            print(f"⚠️ EXIF extraction timeout for {file_path.name}")
        except FileNotFoundError:
            # exiftool not installed, try basic approach
            metadata['exif_data'] = {'error': 'exiftool not available'}
        except Exception as e:
            print(f"❌ EXIF extraction error for {file_path}: {e}")

        return metadata

    def _store_metadata(self, metadata: Dict[str, Any]):
        """Store metadata in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_metadata (
                    file_path, exif_json, creation_date, camera_model,
                    gps_coordinates, software_used, privacy_concerns, extracted_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata['file_path'],
                json.dumps(metadata['exif_data']),
                metadata['exif_data'].get('CreateDate'),
                metadata['exif_data'].get('Model'),
                json.dumps({k: v for k, v in metadata['exif_data'].items() if 'GPS' in k}),
                metadata['exif_data'].get('Software'),
                json.dumps(metadata['privacy_concerns']),
                metadata['extracted_date']
            ))

    def detect_duplicates(self, scan_paths: List[Path]) -> Dict[str, Any]:
        """Detect duplicate files by checksum"""
        print("🔍 Scanning for duplicate files...")

        checksums = {}
        total_files = 0

        for scan_path in scan_paths:
            if not scan_path.exists():
                continue

            for file_path in scan_path.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    total_files += 1
                    if total_files % 100 == 0:
                        print(f"  Processed {total_files} files...")

                    try:
                        # Calculate MD5 for duplicate detection
                        md5_hash = hashlib.md5()
                        with open(file_path, 'rb') as f:
                            for chunk in iter(lambda: f.read(4096), b""):
                                md5_hash.update(chunk)

                        checksum = md5_hash.hexdigest()
                        file_size = file_path.stat().st_size

                        if checksum not in checksums:
                            checksums[checksum] = []

                        checksums[checksum].append({
                            'path': str(file_path),
                            'size': file_size
                        })

                    except Exception as e:
                        print(f"❌ Error processing {file_path}: {e}")

        # Find duplicates
        duplicates = {checksum: files for checksum, files in checksums.items() if len(files) > 1}

        # Calculate potential savings
        total_savings = 0
        for checksum, files in duplicates.items():
            file_size = files[0]['size']
            duplicate_count = len(files) - 1  # Keep one copy
            total_savings += file_size * duplicate_count

        # Store duplicate information
        with sqlite3.connect(self.db_path) as conn:
            for checksum, files in duplicates.items():
                conn.execute("""
                    INSERT OR REPLACE INTO file_duplicates (
                        checksum, file_paths, file_count, total_size_bytes,
                        potential_savings_bytes, detected_date
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    checksum,
                    json.dumps([f['path'] for f in files]),
                    len(files),
                    files[0]['size'],
                    files[0]['size'] * (len(files) - 1),
                    datetime.now().isoformat()
                ))

        return {
            'total_files_scanned': total_files,
            'duplicate_groups': len(duplicates),
            'total_duplicates': sum(len(files) - 1 for files in duplicates.values()),
            'potential_savings_gb': total_savings / (1024**3),
            'duplicate_details': duplicates
        }

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate security and privacy report"""
        print("📋 Generating security report...")

        with sqlite3.connect(self.db_path) as conn:
            # High-risk files
            cursor = conn.execute("""
                SELECT file_path, origin_type, download_url, risk_score
                FROM file_provenance
                WHERE risk_score > 30
                ORDER BY risk_score DESC
            """)
            high_risk_files = [dict(zip([col[0] for col in cursor.description], row))
                             for row in cursor.fetchall()]

            # Files with privacy concerns
            cursor = conn.execute("""
                SELECT file_path, privacy_concerns, gps_coordinates
                FROM file_metadata
                WHERE privacy_concerns != '[]' AND privacy_concerns IS NOT NULL
            """)
            privacy_concerns = [dict(zip([col[0] for col in cursor.description], row))
                              for row in cursor.fetchall()]

            # Download sources summary
            cursor = conn.execute("""
                SELECT
                    CASE
                        WHEN download_url LIKE '%github.com%' THEN 'GitHub'
                        WHEN download_url LIKE '%dropbox.com%' THEN 'Dropbox'
                        WHEN download_url LIKE '%google.com%' THEN 'Google'
                        ELSE 'Other/Unknown'
                    END as source_category,
                    COUNT(*) as file_count
                FROM file_provenance
                WHERE download_url IS NOT NULL
                GROUP BY source_category
            """)
            download_sources = dict(cursor.fetchall())

        return {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'high_risk_files': len(high_risk_files),
                'privacy_concern_files': len(privacy_concerns),
                'download_sources': download_sources
            },
            'high_risk_files': high_risk_files[:10],  # Top 10
            'privacy_concerns': privacy_concerns[:10],  # Top 10
            'recommendations': self._generate_security_recommendations(high_risk_files, privacy_concerns)
        }

    def _generate_security_recommendations(self, high_risk_files, privacy_concerns) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if high_risk_files:
            recommendations.append("Review high-risk downloaded files and consider quarantine")

        if privacy_concerns:
            recommendations.append("Remove GPS/location data from images before sharing")
            recommendations.append("Consider using exiftool to strip metadata: exiftool -all= image.jpg")

        if len(high_risk_files) > 10:
            recommendations.append("Implement stricter download policies")

        return recommendations

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 provenance_scanner.py <command> [args...]")
        print("Commands:")
        print("  scan-provenance <path>        - Scan file provenance")
        print("  extract-exif <path>          - Extract EXIF metadata")
        print("  find-duplicates <path1,path2> - Find duplicate files")
        print("  security-report              - Generate security report")
        sys.exit(1)

    scanner = ProvenanceScanner()
    command = sys.argv[1]

    if command == "scan-provenance" and len(sys.argv) > 2:
        scan_path = Path(sys.argv[2])
        if scan_path.is_file():
            result = scanner.scan_file_provenance(scan_path)
            print(f"📋 Provenance for {scan_path.name}:")
            print(f"  Origin: {result['origin_type']}")
            print(f"  Risk Score: {result['risk_score']}/100")
            if result['download_info']:
                print(f"  Downloaded from: {result['download_info'].get('domain', 'unknown')}")
        else:
            print(f"❌ File not found: {scan_path}")

    elif command == "extract-exif" and len(sys.argv) > 2:
        file_path = Path(sys.argv[2])
        result = scanner.extract_exif_metadata(file_path)
        print(f"📋 EXIF data for {file_path.name}:")
        if result['privacy_concerns']:
            print(f"  ⚠️ Privacy concerns: {result['privacy_concerns']}")
        else:
            print("  ✅ No privacy concerns detected")

    elif command == "find-duplicates" and len(sys.argv) > 2:
        paths = [Path(p.strip()) for p in sys.argv[2].split(',')]
        result = scanner.detect_duplicates(paths)
        print(f"🔍 Duplicate scan results:")
        print(f"  Files scanned: {result['total_files_scanned']:,}")
        print(f"  Duplicate groups: {result['duplicate_groups']}")
        print(f"  Total duplicates: {result['total_duplicates']}")
        print(f"  Potential savings: {result['potential_savings_gb']:.2f} GB")

    elif command == "security-report":
        report = scanner.generate_security_report()

        # Save report
        report_file = f"reports/security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("reports").mkdir(exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"🔒 Security Report:")
        print(f"  High-risk files: {report['summary']['high_risk_files']}")
        print(f"  Privacy concerns: {report['summary']['privacy_concern_files']}")
        print(f"  Download sources: {report['summary']['download_sources']}")
        print(f"  Report saved: {report_file}")

        if report['recommendations']:
            print("\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()