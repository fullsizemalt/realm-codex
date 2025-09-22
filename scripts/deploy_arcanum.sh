#!/bin/bash
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
