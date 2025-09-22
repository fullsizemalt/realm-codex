#!/usr/bin/env python3
"""
Phase 2 GitOps: Migrate arcanum service from env vars to secrets management
"""

import os
import sys
import subprocess
from pathlib import Path

def get_current_env_vars():
    """Extract current environment variables from running container"""
    try:
        result = subprocess.run([
            "docker", "inspect", "arcanum-orchestrator-arcanum-1",
            "--format", "{{.Config.Env}}"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print("❌ Failed to inspect arcanum container")
            return None

        env_vars = {}
        env_output = result.stdout.strip()[1:-1]  # Remove [ ]

        for env_line in env_output.split():
            if '=' in env_line:
                key, value = env_line.split('=', 1)
                env_vars[key] = value

        return env_vars

    except Exception as e:
        print(f"❌ Error extracting env vars: {e}")
        return None

def store_secrets(env_vars):
    """Store API keys as secrets"""
    secrets_to_migrate = {
        'ANTHROPIC_API_KEY': 'anthropic_api_key',
        'GOOGLE_API_KEY': 'google_api_key'
    }

    for env_key, secret_name in secrets_to_migrate.items():
        value = env_vars.get(env_key)

        if not value or value == '':
            print(f"⚠️  {env_key} is empty, skipping...")
            continue

        print(f"📦 Storing {env_key} as secret '{secret_name}'")

        # Store using our secrets manager
        result = subprocess.run([
            "python3", "scripts/secrets_manager.py", "store",
            secret_name, value, f"Migrated from {env_key}"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ {secret_name} stored successfully")
        else:
            print(f"❌ Failed to store {secret_name}: {result.stderr}")
            return False

    return True

def create_secret_loader_script():
    """Create script to load secrets into environment"""
    script_content = '''#!/bin/bash
# Phase 2 GitOps: Load secrets from secrets manager
# Usage: source load_secrets.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Load secrets into environment
export ANTHROPIC_API_KEY=$(python3 "$SCRIPT_DIR/secrets_manager.py" get anthropic_api_key)
export GOOGLE_API_KEY=$(python3 "$SCRIPT_DIR/secrets_manager.py" get google_api_key)

# Verify secrets were loaded
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not loaded"
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  Warning: GOOGLE_API_KEY not loaded"
fi

echo "✅ Secrets loaded from secrets manager"
'''

    script_path = Path("scripts/load_secrets.sh")
    with open(script_path, 'w') as f:
        f.write(script_content)

    os.chmod(script_path, 0o755)
    print(f"✅ Created secret loader script: {script_path}")

def update_docker_compose():
    """Update docker-compose to use secret loader"""
    compose_file = Path("services/arcanum-orchestrator/docker-compose.yaml")

    if not compose_file.exists():
        print(f"❌ Docker compose file not found: {compose_file}")
        return False

    # Read current compose file
    with open(compose_file, 'r') as f:
        content = f.read()

    # Add comment about secrets
    if "# Secrets loaded via load_secrets.sh" not in content:
        content = content.replace(
            "environment:",
            "environment:\n      # Secrets loaded via load_secrets.sh (Phase 2)"
        )

    # Update compose file
    with open(compose_file, 'w') as f:
        f.write(content)

    print("✅ Updated docker-compose.yaml with secrets comment")
    return True

def create_deployment_script():
    """Create deployment script that uses secrets"""
    script_content = '''#!/bin/bash
# Phase 2 GitOps: Deploy arcanum with secrets management

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

echo "🔄 Deploying arcanum with secrets management..."

# Validate configuration
echo "📋 Validating configuration..."
python3 scripts/validate_config.py services/arcanum-orchestrator/

# Load secrets
echo "🔐 Loading secrets..."
source scripts/load_secrets.sh

# Deploy service
echo "🚀 Deploying service..."
cd services/arcanum-orchestrator
docker-compose down
docker-compose up -d

# Wait for health check
echo "🏥 Waiting for health check..."
sleep 10

# Verify deployment
echo "✅ Verifying deployment..."
if curl -sf http://localhost:8080/healthz > /dev/null; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed - health check failed"
    exit 1
fi
'''

    script_path = Path("scripts/deploy_arcanum.sh")
    with open(script_path, 'w') as f:
        f.write(script_content)

    os.chmod(script_path, 0o755)
    print(f"✅ Created deployment script: {script_path}")

def main():
    print("🔄 Migrating arcanum service to secrets management...")

    # Change to realm-refactor directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    # Extract current environment variables
    print("📋 Extracting current environment variables...")
    env_vars = get_current_env_vars()

    if not env_vars:
        print("❌ Failed to extract environment variables")
        sys.exit(1)

    print(f"Found {len(env_vars)} environment variables")

    # Store secrets
    if not store_secrets(env_vars):
        print("❌ Failed to store secrets")
        sys.exit(1)

    # Create supporting scripts
    create_secret_loader_script()
    update_docker_compose()
    create_deployment_script()

    print("\n🎉 Migration complete!")
    print("\nNext steps:")
    print("1. Test deployment: ./scripts/deploy_arcanum.sh")
    print("2. Verify secrets: python3 scripts/secrets_manager.py list")
    print("3. Remove old .env files once confirmed working")

if __name__ == "__main__":
    main()