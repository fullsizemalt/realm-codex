#!/usr/bin/env python3
"""
Phase 1 Guardrail: Simple alert manager for realm services
Reads config/alerts.yaml and sends notifications based on monitoring results
"""

import yaml
import urllib.request
import urllib.error
import smtplib
import os
import time
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

class AlertManager:
    def __init__(self, config_path="config/alerts.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)

    def load_config(self):
        """Load alert configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file {self.config_path} not found")
            return {"alerts": {"enabled": False}}

    def log_alert(self, severity, message):
        """Log alert to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {severity.upper()}: {message}\n"

        # Write to general log
        with open("logs/alerts.log", "a") as f:
            f.write(log_entry)

        print(log_entry.strip())

    def send_email_alert(self, subject, message):
        """Send email alert (if configured)"""
        email_config = self.config.get("alerts", {}).get("notifications", {}).get("email", {})

        if not email_config.get("enabled", False):
            return False

        try:
            # Email implementation would go here
            # For now, just log that email would be sent
            self.log_alert("INFO", f"Email alert would be sent: {subject}")
            return True
        except Exception as e:
            self.log_alert("ERROR", f"Failed to send email: {e}")
            return False

    def send_slack_alert(self, message):
        """Send Slack alert (if configured)"""
        slack_config = self.config.get("alerts", {}).get("notifications", {}).get("slack", {})

        if not slack_config.get("enabled", False):
            return False

        try:
            # Slack implementation would go here
            self.log_alert("INFO", f"Slack alert would be sent: {message}")
            return True
        except Exception as e:
            self.log_alert("ERROR", f"Failed to send Slack alert: {e}")
            return False

    def check_service_health(self, service):
        """Check health of a specific service"""
        try:
            req = urllib.request.Request(service["health_url"])
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True, f"Service {service['name']} is healthy"
                else:
                    return False, f"Service {service['name']} returned status {response.status}"
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            return False, f"Service {service['name']} unreachable: {e}"

    def check_docker_container(self, service_name):
        """Check if Docker container is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={service_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return service_name in result.stdout
        except subprocess.TimeoutExpired:
            return False

    def alert(self, severity, message, service_name=None):
        """Send alert through configured channels"""
        if not self.config.get("alerts", {}).get("enabled", False):
            return

        # Format message
        formatted_message = message
        if service_name:
            formatted_message = message.replace("{{ service }}", service_name)

        # Log alert
        self.log_alert(severity, formatted_message)

        # Send notifications
        notifications = self.config.get("alerts", {}).get("notifications", {})

        if notifications.get("email", {}).get("enabled", False):
            subject = f"[{severity.upper()}] Realm Alert"
            self.send_email_alert(subject, formatted_message)

        if notifications.get("slack", {}).get("enabled", False):
            self.send_slack_alert(formatted_message)

    def monitor_services(self):
        """Monitor all configured services"""
        services = self.config.get("alerts", {}).get("services", [])
        rules = self.config.get("alerts", {}).get("rules", {})

        for service in services:
            service_name = service["name"]

            # Check Docker container
            if not self.check_docker_container(service_name):
                self.alert(
                    "critical",
                    rules.get("service_down", {}).get("message", f"Service {service_name} container is down"),
                    service_name
                )
                continue

            # Check health endpoint
            is_healthy, health_message = self.check_service_health(service)
            if not is_healthy:
                self.alert(
                    "warning",
                    rules.get("health_check_failed", {}).get("message", health_message),
                    service_name
                )
            else:
                # Log successful check (less verbose)
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ✅ {service_name} healthy")

def main():
    import sys

    # Change to script directory to find config files
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    alert_manager = AlertManager()

    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        print("Starting alert manager daemon...")
        while True:
            alert_manager.monitor_services()
            time.sleep(60)  # Check every minute
    else:
        print("Running single health check...")
        alert_manager.monitor_services()

if __name__ == "__main__":
    main()