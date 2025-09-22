#!/bin/bash
# Phase 1 Guardrail: Basic monitoring for arcanum-orchestrator
# Usage: ./monitor_arcanum.sh [--once|--daemon]

SERVICE_NAME="arcanum-orchestrator"
HEALTH_URL="http://localhost:8080/healthz"
METRICS_URL="http://localhost:8080/metrics"
LOG_FILE="$HOME/realm-refactor/logs/monitor.log"

# Create logs directory
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_health() {
    local start_time=$(date +%s)

    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        local end_time=$(date +%s)
        local response_time=$(( end_time - start_time ))
        log "✅ $SERVICE_NAME healthy (${response_time}s)"
        return 0
    else
        log "❌ $SERVICE_NAME unhealthy or unreachable"
        return 1
    fi
}

check_docker() {
    if docker ps --filter "name=arcanum" --format "table {{.Names}}\t{{.Status}}" | grep -q "Up"; then
        log "🐳 Docker container running"
        return 0
    else
        log "🚨 Docker container not running"
        return 1
    fi
}

alert() {
    local message="$1"
    log "🚨 ALERT: $message"

    # Add notification methods here (email, Slack, etc.)
    # For now, just log prominently
    echo "ALERT: $message" >> "$HOME/realm-refactor/logs/alerts.log"
}

monitor_once() {
    log "--- Health Check ---"

    if ! check_docker; then
        alert "Arcanum Docker container is down"
        return 1
    fi

    if ! check_health; then
        alert "Arcanum service health check failed"
        return 1
    fi

    log "All checks passed"
    return 0
}

monitor_daemon() {
    log "Starting daemon mode monitoring for $SERVICE_NAME"

    while true; do
        monitor_once
        sleep 60  # Check every minute
    done
}

case "${1:-}" in
    --once)
        monitor_once
        ;;
    --daemon)
        monitor_daemon
        ;;
    *)
        echo "Usage: $0 [--once|--daemon]"
        echo "  --once   Run health check once"
        echo "  --daemon Run continuous monitoring"
        exit 1
        ;;
esac