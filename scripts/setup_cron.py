#!/usr/bin/env python3
"""
Setup local cron job for automated codex updates
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_cron_job():
    """Setup cron job for automated codex updates"""

    # Get current directory
    repo_path = Path.cwd().resolve()

    # Create cron job entry
    cron_entry = f"""# Automated Realm Codex Updates
# Runs every 6 hours and generates fresh reports/documentation
0 */6 * * * cd {repo_path} && /usr/bin/make codex-update >/dev/null 2>&1

# Daily cleanup at 3 AM
0 3 * * * cd {repo_path} && /usr/bin/make quick-cleanup >/dev/null 2>&1

# Weekly deep scan on Sundays at 2 AM
0 2 * * 0 cd {repo_path} && /usr/bin/make legacy-scan >/dev/null 2>&1
"""

    print("🕐 Setting up automated codex updates...")
    print(f"📁 Repository path: {repo_path}")

    # Check if crontab exists
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing_crontab = result.stdout if result.returncode == 0 else ""
    except:
        existing_crontab = ""

    # Check if our jobs already exist
    if "Automated Realm Codex Updates" in existing_crontab:
        print("⚠️ Codex cron jobs already exist")
        response = input("Replace existing jobs? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return False

        # Remove existing codex jobs
        lines = existing_crontab.split('\n')
        filtered_lines = []
        skip_next = False

        for line in lines:
            if "Automated Realm Codex Updates" in line:
                skip_next = True
                continue
            elif skip_next and line.strip() and not line.startswith('#'):
                if "codex-update" in line or "quick-cleanup" in line or "legacy-scan" in line:
                    continue
                else:
                    skip_next = False
            elif skip_next and line.startswith('#'):
                continue
            elif skip_next and not line.strip():
                continue
            else:
                skip_next = False

            filtered_lines.append(line)

        existing_crontab = '\n'.join(filtered_lines).strip()

    # Combine existing and new crontab
    if existing_crontab:
        new_crontab = existing_crontab + '\n\n' + cron_entry
    else:
        new_crontab = cron_entry

    # Install new crontab
    try:
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)

        if process.returncode == 0:
            print("✅ Cron jobs installed successfully!")
            print("\n📋 Scheduled tasks:")
            print("  • Every 6 hours: Full codex update")
            print("  • Daily 3 AM: Quick cleanup")
            print("  • Weekly Sunday 2 AM: Deep legacy scan")
            print(f"\n🌐 Documentation auto-updates at: https://fullsizemalt.github.io/realm-codex/")
            return True
        else:
            print("❌ Failed to install cron jobs")
            return False

    except Exception as e:
        print(f"❌ Error setting up cron: {e}")
        return False

def remove_cron_jobs():
    """Remove codex cron jobs"""
    print("🗑️ Removing codex cron jobs...")

    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing_crontab = result.stdout if result.returncode == 0 else ""
    except:
        existing_crontab = ""

    if "Automated Realm Codex Updates" not in existing_crontab:
        print("ℹ️ No codex cron jobs found")
        return True

    # Remove codex jobs
    lines = existing_crontab.split('\n')
    filtered_lines = []
    skip_next = False

    for line in lines:
        if "Automated Realm Codex Updates" in line:
            skip_next = True
            continue
        elif skip_next and line.strip() and not line.startswith('#'):
            if "codex-update" in line or "quick-cleanup" in line or "legacy-scan" in line:
                continue
            else:
                skip_next = False
        elif skip_next and line.startswith('#'):
            continue
        elif skip_next and not line.strip():
            continue
        else:
            skip_next = False

        filtered_lines.append(line)

    new_crontab = '\n'.join(filtered_lines).strip()

    # Install filtered crontab
    try:
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)

        if process.returncode == 0:
            print("✅ Codex cron jobs removed")
            return True
        else:
            print("❌ Failed to remove cron jobs")
            return False

    except Exception as e:
        print(f"❌ Error removing cron jobs: {e}")
        return False

def show_cron_status():
    """Show current cron job status"""
    print("📋 Current Cron Status:")

    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)

        if result.returncode == 0:
            crontab = result.stdout

            if "Automated Realm Codex Updates" in crontab:
                print("✅ Codex automation is active")

                # Extract and show codex jobs
                lines = crontab.split('\n')
                in_codex_section = False

                for line in lines:
                    if "Automated Realm Codex Updates" in line:
                        in_codex_section = True
                        continue
                    elif in_codex_section and line.strip() and not line.startswith('#'):
                        if "codex-update" in line or "quick-cleanup" in line or "legacy-scan" in line:
                            print(f"  • {line.strip()}")
                        else:
                            break
                    elif in_codex_section and not line.strip():
                        break
            else:
                print("❌ Codex automation not configured")
                print("   Run: python3 scripts/setup_cron.py install")
        else:
            print("❌ No crontab configured")

    except Exception as e:
        print(f"❌ Error checking cron status: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 setup_cron.py <command>")
        print("Commands:")
        print("  install  - Install codex automation cron jobs")
        print("  remove   - Remove codex cron jobs")
        print("  status   - Show current cron status")
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        success = setup_cron_job()
        sys.exit(0 if success else 1)
    elif command == "remove":
        success = remove_cron_jobs()
        sys.exit(0 if success else 1)
    elif command == "status":
        show_cron_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()