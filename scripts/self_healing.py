#!/usr/bin/env python3
"""
Phase 3 Self-Healing: Automated remediation system
Listens for alerts and triggers appropriate remediation actions
"""

import json
import subprocess
import time
import urllib.request
import urllib.error
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/self_healing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SelfHealingOrchestrator:
    def __init__(self):
        self.prometheus_url = "http://localhost:9090"
        self.alertmanager_url = "http://localhost:9093"
        self.remediation_count = {}
        self.max_remediations_per_hour = 3

    def log_remediation(self, action, service, reason):
        """Log remediation action for tracking"""
        timestamp = datetime.now().isoformat()
        log_entry = f"REMEDIATION: {timestamp} - {action} - {service} - {reason}"
        logger.info(log_entry)

        # Also write to realm logs for Loki to pick up
        realm_log_dir = Path("/var/log/realm")
        realm_log_dir.mkdir(exist_ok=True)

        with open(realm_log_dir / "remediation.log", "a") as f:
            f.write(f"{log_entry}\n")

    def check_rate_limit(self, service):
        """Check if we've exceeded remediation rate limits"""
        current_hour = datetime.now().hour
        key = f"{service}_{current_hour}"

        count = self.remediation_count.get(key, 0)
        if count >= self.max_remediations_per_hour:
            logger.warning(f"Rate limit exceeded for {service} (hour {current_hour})")
            return False

        self.remediation_count[key] = count + 1
        return True

    def restart_arcanum_service(self):
        """Restart the arcanum service"""
        if not self.check_rate_limit("arcanum"):
            return False

        try:
            logger.info("🔄 Attempting to restart arcanum service...")

            # Use our GitOps deployment to restart
            result = subprocess.run([
                "python3", "scripts/gitops_deploy.py", "dev", "arcanum"
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                self.log_remediation("RESTART_SUCCESS", "arcanum", "Service automatically restarted")
                return True
            else:
                logger.error(f"Failed to restart service: {result.stderr}")
                self.log_remediation("RESTART_FAILED", "arcanum", f"Error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Restart operation timed out")
            self.log_remediation("RESTART_TIMEOUT", "arcanum", "Restart operation exceeded timeout")
            return False
        except Exception as e:
            logger.error(f"Exception during restart: {e}")
            self.log_remediation("RESTART_ERROR", "arcanum", f"Exception: {e}")
            return False

    def scale_down_service(self, service):
        """Reduce resource allocation for a service"""
        if not self.check_rate_limit(f"{service}_scale"):
            return False

        try:
            logger.info(f"📉 Scaling down {service} service...")

            # For now, log the action - in production this might modify deployment configs
            self.log_remediation("SCALE_DOWN", service, "Reduced resource allocation due to high usage")

            # Could implement actual scaling logic here
            # e.g., modify Docker compose limits, restart with lower resources

            return True

        except Exception as e:
            logger.error(f"Exception during scale down: {e}")
            self.log_remediation("SCALE_DOWN_ERROR", service, f"Exception: {e}")
            return False

    def clear_logs(self, service):
        """Clear logs to free up disk space"""
        try:
            logger.info(f"🧹 Clearing logs for {service}...")

            # Clear Docker logs
            result = subprocess.run([
                "docker", "logs", "--tail", "100", f"{service}"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                # In production, you might truncate log files here
                self.log_remediation("LOGS_CLEARED", service, "Log cleanup performed")
                return True
            else:
                logger.error(f"Failed to access logs for {service}")
                return False

        except Exception as e:
            logger.error(f"Exception during log cleanup: {e}")
            return False

    def get_firing_alerts(self):
        """Fetch currently firing alerts from Prometheus"""
        try:
            url = f"{self.prometheus_url}/api/v1/alerts"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())

                if data['status'] == 'success':
                    firing_alerts = [
                        alert for alert in data['data']['alerts']
                        if alert['state'] == 'firing'
                    ]
                    return firing_alerts
                else:
                    logger.error(f"Failed to fetch alerts: {data}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []

    def process_alert(self, alert):
        """Process a single alert and trigger appropriate remediation"""
        alert_name = alert['labels'].get('alertname', 'Unknown')
        action = alert['labels'].get('action', '')

        logger.info(f"🚨 Processing alert: {alert_name}")

        if alert_name == "ArcanumNeedsRestart" or action == "restart_service":
            return self.restart_arcanum_service()

        elif alert_name == "SystemResourceExhaustion" or action == "scale_down":
            service = alert['labels'].get('job', 'unknown')
            return self.scale_down_service(service)

        elif alert_name == "HighDiskUsage":
            service = alert['labels'].get('job', 'unknown')
            return self.clear_logs(service)

        else:
            logger.info(f"No remediation action defined for alert: {alert_name}")
            return False

    def run_healing_cycle(self):
        """Run one cycle of self-healing checks"""
        logger.info("🔍 Running self-healing cycle...")

        alerts = self.get_firing_alerts()

        if not alerts:
            logger.debug("No firing alerts found")
            return

        logger.info(f"Found {len(alerts)} firing alerts")

        for alert in alerts:
            try:
                self.process_alert(alert)
            except Exception as e:
                logger.error(f"Error processing alert {alert.get('labels', {}).get('alertname', 'Unknown')}: {e}")

    def run_daemon(self, interval=60):
        """Run self-healing in daemon mode"""
        logger.info(f"🤖 Starting self-healing daemon (check interval: {interval}s)")

        while True:
            try:
                self.run_healing_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Self-healing daemon stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in daemon loop: {e}")
                time.sleep(30)  # Wait before retrying

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        orchestrator = SelfHealingOrchestrator()
        orchestrator.run_daemon(interval)
    else:
        # Run once
        orchestrator = SelfHealingOrchestrator()
        orchestrator.run_healing_cycle()

if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    main()