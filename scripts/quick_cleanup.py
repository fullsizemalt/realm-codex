#!/usr/bin/env python3
"""
Phase 6: Quick Cleanup Script
Fast cleanup of obvious waste and legacy items
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def quick_cleanup():
    """Quick cleanup of obvious targets"""
    cleanup_stats = {
        'removed_files': 0,
        'freed_space_mb': 0,
        'actions': []
    }

    print("🧹 Starting quick cleanup...")

    # 1. Clear Downloads older than 30 days
    downloads_path = Path.home() / "Downloads"
    if downloads_path.exists():
        cutoff_date = datetime.now() - timedelta(days=30)
        for item in downloads_path.iterdir():
            try:
                if item.is_file():
                    mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                    if mod_time < cutoff_date:
                        size_mb = item.stat().st_size / (1024*1024)
                        print(f"  Removing old download: {item.name} ({size_mb:.1f}MB)")
                        item.unlink()
                        cleanup_stats['removed_files'] += 1
                        cleanup_stats['freed_space_mb'] += size_mb
                        cleanup_stats['actions'].append(f"Removed old download: {item.name}")
            except Exception as e:
                print(f"  ⚠️ Could not remove {item.name}: {e}")

    # 2. Clean temp directories
    temp_dirs = [
        Path.home() / ".cache",
        Path("/tmp"),
        Path.home() / "Library/Caches" if Path.home().joinpath("Library/Caches").exists() else None
    ]

    for temp_dir in temp_dirs:
        if temp_dir and temp_dir.exists():
            try:
                # Only clean obviously safe temp files
                for item in temp_dir.rglob("*.tmp"):
                    if item.is_file():
                        try:
                            size_mb = item.stat().st_size / (1024*1024)
                            item.unlink()
                            cleanup_stats['removed_files'] += 1
                            cleanup_stats['freed_space_mb'] += size_mb
                        except:
                            pass
            except:
                pass

    # 3. Docker cleanup
    try:
        import subprocess
        print("🐳 Cleaning Docker...")

        # Remove dangling images
        result = subprocess.run(['docker', 'image', 'prune', '-f'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            cleanup_stats['actions'].append("Docker: Removed dangling images")

        # Remove stopped containers
        result = subprocess.run(['docker', 'container', 'prune', '-f'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            cleanup_stats['actions'].append("Docker: Removed stopped containers")

    except Exception as e:
        print(f"  ⚠️ Docker cleanup failed: {e}")

    # 4. Check for obvious large backups at home level
    for item in Path.home().iterdir():
        if item.is_file() and item.suffix in ['.tar.gz', '.zip', '.bak']:
            size_mb = item.stat().st_size / (1024*1024)
            age_days = (datetime.now() - datetime.fromtimestamp(item.stat().st_mtime)).days

            if size_mb > 100 and age_days > 30:
                print(f"  📦 Large backup found: {item.name} ({size_mb:.1f}MB, {age_days} days old)")
                cleanup_stats['actions'].append(f"Found large backup: {item.name} ({size_mb:.1f}MB)")

    return cleanup_stats

def main():
    results = quick_cleanup()

    print(f"\n✅ Quick cleanup complete:")
    print(f"  Files removed: {results['removed_files']}")
    print(f"  Space freed: {results['freed_space_mb']:.1f}MB")

    if results['actions']:
        print(f"\n📋 Actions taken:")
        for action in results['actions']:
            print(f"  • {action}")

if __name__ == "__main__":
    main()