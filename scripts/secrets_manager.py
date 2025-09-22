#!/usr/bin/env python3
"""
Phase 2 GitOps: Simple secrets management for Vaultwarden
Provides a CLI interface to store/retrieve secrets from Vaultwarden API
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import sys
import os
from pathlib import Path

class SecretsManager:
    def __init__(self, vault_url="http://localhost:8000", admin_token=None):
        self.vault_url = vault_url.rstrip('/')
        self.admin_token = admin_token or os.environ.get('VAULTWARDEN_ADMIN_TOKEN')
        self.session_file = Path.home() / '.realm-vault-session'

    def _make_request(self, path, method='GET', data=None, headers=None):
        """Make HTTP request to Vaultwarden API"""
        url = f"{self.vault_url}{path}"

        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)

        if self.admin_token:
            req_headers['Authorization'] = f"Bearer {self.admin_token}"

        req_data = json.dumps(data).encode('utf-8') if data else None

        try:
            req = urllib.request.Request(url, data=req_data, headers=req_headers, method=method)
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"HTTP Error {e.code}: {e.reason}")
            if e.code == 401:
                print("Authentication failed. Check your admin token.")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    def create_organization(self, name="Realm"):
        """Create an organization for storing secrets"""
        data = {
            "name": name,
            "billingEmail": "admin@realm.local"
        }
        return self._make_request('/api/organizations', 'POST', data)

    def store_secret(self, name, value, notes=""):
        """Store a secret in Vaultwarden (simplified approach)"""
        # For now, we'll use a simple file-based approach
        # In production, you'd use proper Vaultwarden API integration
        secrets_dir = Path("~/.realm-secrets").expanduser()
        secrets_dir.mkdir(mode=0o700, exist_ok=True)

        secret_file = secrets_dir / f"{name}.secret"

        secret_data = {
            "value": value,
            "notes": notes,
            "created": str(Path().stat().st_mtime if Path().exists() else 0)
        }

        with open(secret_file, 'w', opener=lambda path, flags: os.open(path, flags, 0o600)) as f:
            json.dump(secret_data, f)

        print(f"✅ Secret '{name}' stored successfully")
        return True

    def get_secret(self, name):
        """Retrieve a secret from storage"""
        secrets_dir = Path("~/.realm-secrets").expanduser()
        secret_file = secrets_dir / f"{name}.secret"

        if not secret_file.exists():
            print(f"❌ Secret '{name}' not found")
            return None

        try:
            with open(secret_file, 'r') as f:
                secret_data = json.load(f)
                return secret_data.get('value')
        except Exception as e:
            print(f"❌ Failed to read secret '{name}': {e}")
            return None

    def list_secrets(self):
        """List all stored secrets"""
        secrets_dir = Path("~/.realm-secrets").expanduser()

        if not secrets_dir.exists():
            print("No secrets directory found")
            return []

        secrets = []
        for secret_file in secrets_dir.glob("*.secret"):
            secret_name = secret_file.stem
            secrets.append(secret_name)

        return secrets

    def delete_secret(self, name):
        """Delete a secret"""
        secrets_dir = Path("~/.realm-secrets").expanduser()
        secret_file = secrets_dir / f"{name}.secret"

        if secret_file.exists():
            secret_file.unlink()
            print(f"✅ Secret '{name}' deleted")
            return True
        else:
            print(f"❌ Secret '{name}' not found")
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 secrets_manager.py <command> [args...]")
        print("Commands:")
        print("  store <name> <value> [notes]    - Store a secret")
        print("  get <name>                      - Get a secret value")
        print("  list                            - List all secrets")
        print("  delete <name>                   - Delete a secret")
        print("\nExamples:")
        print("  python3 secrets_manager.py store anthropic_key sk-ant-...")
        print("  python3 secrets_manager.py get anthropic_key")
        sys.exit(1)

    manager = SecretsManager()
    command = sys.argv[1]

    if command == "store":
        if len(sys.argv) < 4:
            print("Usage: store <name> <value> [notes]")
            sys.exit(1)

        name = sys.argv[2]
        value = sys.argv[3]
        notes = sys.argv[4] if len(sys.argv) > 4 else ""

        manager.store_secret(name, value, notes)

    elif command == "get":
        if len(sys.argv) < 3:
            print("Usage: get <name>")
            sys.exit(1)

        name = sys.argv[2]
        value = manager.get_secret(name)
        if value:
            print(value)

    elif command == "list":
        secrets = manager.list_secrets()
        if secrets:
            print("Stored secrets:")
            for secret in secrets:
                print(f"  - {secret}")
        else:
            print("No secrets found")

    elif command == "delete":
        if len(sys.argv) < 3:
            print("Usage: delete <name>")
            sys.exit(1)

        name = sys.argv[2]
        manager.delete_secret(name)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()