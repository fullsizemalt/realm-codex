#!/usr/bin/env python3
"""
Phase 5: Media & Seedbox Hardening
Comprehensive media file management with rclone, checksums, and provenance tracking
"""

import os
import json
import hashlib
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

class MediaManager:
    def __init__(self, config_dir="config/media", db_path="media_inventory.db"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = Path(db_path)
        self.config_file = self.config_dir / "media_config.yaml"
        self.rclone_config = self.config_dir / "rclone.conf"

        # Initialize database
        self._init_database()

        # Default media paths to scan
        self.default_media_paths = [
            Path.home() / "Movies",
            Path.home() / "Music",
            Path.home() / "Pictures",
            Path.home() / "AUDIOBOOKSHELF",
            Path.home() / "Calibre Library",
            Path.home() / "Downloads"  # For incomplete/staging files
        ]

    def _init_database(self):
        """Initialize SQLite database for media inventory"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    checksum_md5 TEXT,
                    checksum_sha256 TEXT,
                    mime_type TEXT,
                    category TEXT,
                    added_date TEXT,
                    last_verified TEXT,
                    last_modified TEXT,
                    backup_status TEXT DEFAULT 'pending',
                    backup_location TEXT,
                    metadata_json TEXT,
                    tags TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT,
                    source_path TEXT,
                    destination TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    status TEXT,
                    files_processed INTEGER DEFAULT 0,
                    bytes_transferred INTEGER DEFAULT 0,
                    error_message TEXT,
                    rclone_log_path TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS quota_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    remote_name TEXT,
                    quota_limit_gb INTEGER,
                    current_usage_gb REAL,
                    last_updated TEXT,
                    usage_history_json TEXT
                )
            """)

    def scan_media_directories(self, custom_paths: Optional[List[Path]] = None) -> Dict[str, Any]:
        """Scan media directories and catalog files with checksums"""
        print("📂 Starting media directory scan...")

        paths_to_scan = custom_paths or self.default_media_paths
        scan_results = {
            'scanned_paths': [],
            'files_found': 0,
            'files_added': 0,
            'files_updated': 0,
            'total_size_gb': 0,
            'categories': {},
            'errors': []
        }

        for media_path in paths_to_scan:
            if not media_path.exists():
                print(f"⚠️ Path does not exist: {media_path}")
                continue

            print(f"🔍 Scanning: {media_path}")
            scan_results['scanned_paths'].append(str(media_path))

            try:
                for file_path in media_path.rglob("*"):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        result = self._process_media_file(file_path)

                        scan_results['files_found'] += 1
                        if result['action'] == 'added':
                            scan_results['files_added'] += 1
                        elif result['action'] == 'updated':
                            scan_results['files_updated'] += 1

                        # Track categories
                        category = result.get('category', 'unknown')
                        if category not in scan_results['categories']:
                            scan_results['categories'][category] = 0
                        scan_results['categories'][category] += 1

                        scan_results['total_size_gb'] += result.get('size_gb', 0)

            except Exception as e:
                error_msg = f"Error scanning {media_path}: {e}"
                print(f"❌ {error_msg}")
                scan_results['errors'].append(error_msg)

        print(f"✅ Scan complete: {scan_results['files_found']} files found")
        return scan_results

    def _process_media_file(self, file_path: Path) -> Dict[str, Any]:
        """Process individual media file: checksum, categorize, store in DB"""
        try:
            # Get file stats
            stat_info = file_path.stat()
            file_size = stat_info.st_size
            size_gb = file_size / (1024**3)
            last_modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()

            # Determine category based on extension and path
            category = self._categorize_file(file_path)

            # Check if file exists in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT checksum_md5, last_modified, backup_status FROM media_files WHERE file_path = ?",
                    (str(file_path),)
                )
                existing = cursor.fetchone()

            # Only calculate checksums for new files or if file was modified
            checksums = {}
            if not existing or existing[1] != last_modified:
                print(f"🔒 Calculating checksums for: {file_path.name}")
                checksums = self._calculate_checksums(file_path)
            else:
                # Use existing checksum
                checksums = {'md5': existing[0] if existing else None}

            # Get MIME type
            mime_type = self._get_mime_type(file_path)

            # Extract metadata (for media files)
            metadata = self._extract_metadata(file_path, category)

            # Insert or update in database
            with sqlite3.connect(self.db_path) as conn:
                if existing:
                    conn.execute("""
                        UPDATE media_files SET
                            file_size = ?, checksum_md5 = ?, checksum_sha256 = ?,
                            mime_type = ?, category = ?, last_modified = ?,
                            last_verified = ?, metadata_json = ?
                        WHERE file_path = ?
                    """, (
                        file_size, checksums.get('md5'), checksums.get('sha256'),
                        mime_type, category, last_modified, datetime.now().isoformat(),
                        json.dumps(metadata), str(file_path)
                    ))
                    action = 'updated'
                else:
                    conn.execute("""
                        INSERT INTO media_files (
                            file_path, file_size, checksum_md5, checksum_sha256,
                            mime_type, category, added_date, last_verified,
                            last_modified, metadata_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(file_path), file_size, checksums.get('md5'), checksums.get('sha256'),
                        mime_type, category, datetime.now().isoformat(),
                        datetime.now().isoformat(), last_modified, json.dumps(metadata)
                    ))
                    action = 'added'

            return {
                'action': action,
                'category': category,
                'size_gb': size_gb,
                'checksums': checksums,
                'metadata': metadata
            }

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return {'action': 'error', 'error': str(e)}

    def _calculate_checksums(self, file_path: Path) -> Dict[str, str]:
        """Calculate MD5 and SHA256 checksums for file"""
        checksums = {}

        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks for memory efficiency
                md5_hash = hashlib.md5()
                sha256_hash = hashlib.sha256()

                while chunk := f.read(8192):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)

                checksums['md5'] = md5_hash.hexdigest()
                checksums['sha256'] = sha256_hash.hexdigest()

        except Exception as e:
            print(f"⚠️ Error calculating checksums for {file_path}: {e}")

        return checksums

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on extension and path"""
        extension = file_path.suffix.lower()
        path_str = str(file_path).lower()

        # Video files
        if extension in ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v']:
            if 'movies' in path_str:
                return 'movies'
            return 'videos'

        # Audio files
        elif extension in ['.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma']:
            if 'audiobook' in path_str:
                return 'audiobooks'
            return 'music'

        # Images
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']:
            return 'images'

        # Documents/eBooks
        elif extension in ['.pdf', '.epub', '.mobi', '.azw', '.azw3', '.txt', '.doc', '.docx']:
            if 'calibre' in path_str or 'book' in path_str:
                return 'ebooks'
            return 'documents'

        # Archives
        elif extension in ['.zip', '.tar', '.gz', '.7z', '.rar', '.tar.gz']:
            return 'archives'

        # Software/Applications
        elif extension in ['.dmg', '.pkg', '.app', '.deb', '.rpm']:
            return 'software'

        return 'other'

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type using file command"""
        try:
            result = subprocess.run(
                ['file', '--mime-type', '-b', str(file_path)],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except Exception:
            return 'unknown'

    def _extract_metadata(self, file_path: Path, category: str) -> Dict[str, Any]:
        """Extract metadata from media files using exiftool or ffprobe"""
        metadata = {}

        try:
            if category in ['videos', 'movies']:
                # Use ffprobe for video metadata
                result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_format', '-show_streams', str(file_path)
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    metadata = json.loads(result.stdout)

            elif category in ['music', 'audiobooks']:
                # Use ffprobe for audio metadata
                result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
                    '-show_format', str(file_path)
                ], capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    probe_data = json.loads(result.stdout)
                    metadata = probe_data.get('format', {}).get('tags', {})

        except subprocess.TimeoutExpired:
            print(f"⚠️ Metadata extraction timeout for {file_path.name}")
        except Exception as e:
            print(f"⚠️ Metadata extraction error for {file_path.name}: {e}")

        return metadata

    def setup_rclone_remote(self, remote_name: str, remote_type: str, config_params: Dict[str, str]):
        """Configure rclone remote for backup/sync"""
        print(f"🔧 Setting up rclone remote: {remote_name}")

        try:
            # Create rclone config entry
            config_lines = [f"[{remote_name}]", f"type = {remote_type}"]
            for key, value in config_params.items():
                config_lines.append(f"{key} = {value}")

            # Add to rclone config file
            with open(self.rclone_config, 'a') as f:
                f.write("\\n".join(config_lines) + "\\n\\n")

            # Test the remote
            result = subprocess.run([
                'rclone', '--config', str(self.rclone_config),
                'lsd', f"{remote_name}:"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(f"✅ Remote {remote_name} configured successfully")
                return True
            else:
                print(f"❌ Remote test failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error setting up remote: {e}")
            return False

    def sync_to_remote(self, source_path: Path, remote_name: str,
                      destination_path: str = "", dry_run: bool = True) -> Dict[str, Any]:
        """Sync media files to remote with integrity verification"""
        print(f"🔄 Syncing {source_path} to {remote_name}:{destination_path}")

        # Record sync operation
        operation_id = self._record_sync_start('sync', str(source_path), f"{remote_name}:{destination_path}")

        try:
            # Build rclone command
            cmd = [
                'rclone', 'sync',
                '--config', str(self.rclone_config),
                '--checksum',  # Verify checksums
                '--verbose',
                '--log-file', f"logs/rclone_sync_{operation_id}.log",
                '--stats', '30s',
                '--transfers', '4',
                '--checkers', '8'
            ]

            if dry_run:
                cmd.append('--dry-run')

            cmd.extend([str(source_path), f"{remote_name}:{destination_path}"])

            print(f"🚀 Running: {' '.join(cmd)}")

            # Execute sync
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = time.time() - start_time

            # Parse results
            sync_result = {
                'operation_id': operation_id,
                'success': result.returncode == 0,
                'duration_seconds': duration,
                'dry_run': dry_run,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

            # Update operation record
            status = 'completed' if result.returncode == 0 else 'failed'
            self._record_sync_complete(operation_id, status, result.stderr if result.returncode != 0 else None)

            if result.returncode == 0:
                print(f"✅ Sync completed in {duration:.1f}s")
            else:
                print(f"❌ Sync failed: {result.stderr}")

            return sync_result

        except Exception as e:
            self._record_sync_complete(operation_id, 'error', str(e))
            print(f"❌ Sync error: {e}")
            return {'operation_id': operation_id, 'success': False, 'error': str(e)}

    def _record_sync_start(self, operation_type: str, source: str, destination: str) -> int:
        """Record sync operation start"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO sync_operations (operation_type, source_path, destination, started_at, status)
                VALUES (?, ?, ?, ?, 'running')
            """, (operation_type, source, destination, datetime.now().isoformat()))
            return cursor.lastrowid

    def _record_sync_complete(self, operation_id: int, status: str, error_message: Optional[str]):
        """Record sync operation completion"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE sync_operations SET
                    completed_at = ?, status = ?, error_message = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), status, error_message, operation_id))

    def check_quota_usage(self, remote_name: str) -> Dict[str, Any]:
        """Check quota usage for remote"""
        try:
            # Use rclone to get remote info
            result = subprocess.run([
                'rclone', '--config', str(self.rclone_config),
                'about', f"{remote_name}:"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                # Parse rclone about output
                lines = result.stdout.split('\\n')
                usage_info = {}

                for line in lines:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        usage_info[key.strip()] = value.strip()

                return {
                    'remote': remote_name,
                    'success': True,
                    'usage_info': usage_info,
                    'raw_output': result.stdout
                }
            else:
                return {
                    'remote': remote_name,
                    'success': False,
                    'error': result.stderr
                }

        except Exception as e:
            return {
                'remote': remote_name,
                'success': False,
                'error': str(e)
            }

    def generate_media_report(self) -> Dict[str, Any]:
        """Generate comprehensive media inventory report"""
        print("📊 Generating media inventory report...")

        with sqlite3.connect(self.db_path) as conn:
            # File count by category
            cursor = conn.execute("""
                SELECT category, COUNT(*), SUM(file_size)
                FROM media_files
                GROUP BY category
            """)
            categories = {}
            total_files = 0
            total_size = 0

            for category, count, size in cursor.fetchall():
                size = size or 0
                categories[category] = {
                    'count': count,
                    'size_gb': size / (1024**3),
                    'size_bytes': size
                }
                total_files += count
                total_size += size

            # Backup status
            cursor = conn.execute("""
                SELECT backup_status, COUNT(*)
                FROM media_files
                GROUP BY backup_status
            """)
            backup_status = dict(cursor.fetchall())

            # Recent sync operations
            cursor = conn.execute("""
                SELECT * FROM sync_operations
                ORDER BY started_at DESC
                LIMIT 10
            """)
            recent_syncs = [dict(zip([col[0] for col in cursor.description], row))
                          for row in cursor.fetchall()]

        return {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_files': total_files,
                'total_size_gb': total_size / (1024**3),
                'categories': categories,
                'backup_status': backup_status
            },
            'recent_operations': recent_syncs
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 media_manager.py <command> [args...]")
        print("Commands:")
        print("  scan [path1,path2,...]              - Scan media directories")
        print("  setup-remote <name> <type> <config> - Setup rclone remote")
        print("  sync <source> <remote:dest> [--live] - Sync to remote")
        print("  quota <remote>                      - Check quota usage")
        print("  report                              - Generate inventory report")
        sys.exit(1)

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    manager = MediaManager()
    command = sys.argv[1]

    if command == "scan":
        custom_paths = None
        if len(sys.argv) > 2:
            custom_paths = [Path(p.strip()) for p in sys.argv[2].split(',')]

        results = manager.scan_media_directories(custom_paths)
        print("\\n📋 Scan Results:")
        print(f"  Files found: {results['files_found']}")
        print(f"  Files added: {results['files_added']}")
        print(f"  Files updated: {results['files_updated']}")
        print(f"  Total size: {results['total_size_gb']:.2f} GB")
        print(f"  Categories: {results['categories']}")

    elif command == "setup-remote" and len(sys.argv) >= 4:
        remote_name = sys.argv[2]
        remote_type = sys.argv[3]
        # Simple config parsing - in practice would be more sophisticated
        config_params = {'provider': remote_type}
        manager.setup_rclone_remote(remote_name, remote_type, config_params)

    elif command == "sync" and len(sys.argv) >= 4:
        source = Path(sys.argv[2])
        destination = sys.argv[3]
        dry_run = '--live' not in sys.argv

        if ':' in destination:
            remote_name, remote_path = destination.split(':', 1)
            result = manager.sync_to_remote(source, remote_name, remote_path, dry_run)
            print(f"Sync result: {result}")
        else:
            print("❌ Destination must be in format 'remote:path'")

    elif command == "quota" and len(sys.argv) > 2:
        remote_name = sys.argv[2]
        result = manager.check_quota_usage(remote_name)
        print(f"Quota info: {result}")

    elif command == "report":
        report = manager.generate_media_report()

        # Save report
        report_file = f"reports/media_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("reports").mkdir(exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\\n📊 Media Inventory Report:")
        print(f"  Total files: {report['summary']['total_files']:,}")
        print(f"  Total size: {report['summary']['total_size_gb']:.2f} GB")
        print(f"  Categories: {report['summary']['categories']}")
        print(f"  Report saved: {report_file}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()