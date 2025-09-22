#!/bin/bash
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
