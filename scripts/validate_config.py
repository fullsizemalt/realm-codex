#!/usr/bin/env python3
"""
Phase 1 Guardrail: Configuration validation gates
Validates YAML configuration files before deployment
"""

import yaml
import os
import sys
from pathlib import Path

class ConfigValidator:
    def __init__(self):
        self.schemas_dir = Path("schemas")
        self.errors = []

    def validate_yaml_syntax(self, file_path):
        """Validate YAML syntax"""
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            return True, "Valid YAML syntax"
        except yaml.YAMLError as e:
            return False, f"YAML syntax error: {e}"

    def validate_docker_compose(self, file_path):
        """Validate Docker Compose file structure"""
        try:
            with open(file_path, 'r') as f:
                compose_data = yaml.safe_load(f)

            # Basic validation
            if 'version' not in compose_data:
                return False, "Missing 'version' field"

            if 'services' not in compose_data:
                return False, "Missing 'services' field"

            # Check for guardrails in critical services
            services = compose_data.get('services', {})
            for service_name, service_config in services.items():
                if service_name == 'arcanum':  # Our critical service
                    if 'healthcheck' not in service_config:
                        return False, f"Critical service '{service_name}' missing healthcheck"

                    if 'restart' not in service_config:
                        return False, f"Critical service '{service_name}' missing restart policy"

                    deploy = service_config.get('deploy', {})
                    if 'resources' not in deploy:
                        return False, f"Critical service '{service_name}' missing resource limits"

            return True, "Docker Compose validation passed"

        except Exception as e:
            return False, f"Docker Compose validation error: {e}"

    def validate_alerts_config(self, file_path):
        """Validate alerts configuration"""
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)

            # Check required structure
            if 'alerts' not in config:
                return False, "Missing 'alerts' section"

            alerts = config['alerts']
            required_sections = ['services', 'notifications', 'rules']

            for section in required_sections:
                if section not in alerts:
                    return False, f"Missing '{section}' section in alerts config"

            # Validate services have required fields
            services = alerts.get('services', [])
            for service in services:
                if 'name' not in service:
                    return False, "Service missing 'name' field"
                if 'health_url' not in service:
                    return False, f"Service '{service.get('name', 'unknown')}' missing 'health_url'"

            return True, "Alerts configuration validation passed"

        except Exception as e:
            return False, f"Alerts config validation error: {e}"

    def validate_file(self, file_path):
        """Validate a specific configuration file"""
        file_path = Path(file_path)

        if not file_path.exists():
            return False, f"File not found: {file_path}"

        # Check YAML syntax first
        is_valid, message = self.validate_yaml_syntax(file_path)
        if not is_valid:
            return False, message

        # File-specific validations
        if file_path.name in ['docker-compose.yml', 'docker-compose.yaml']:
            return self.validate_docker_compose(file_path)
        elif file_path.name == 'alerts.yaml':
            return self.validate_alerts_config(file_path)
        else:
            return True, "Basic YAML validation passed"

    def validate_directory(self, directory):
        """Validate all YAML files in a directory"""
        directory = Path(directory)
        yaml_files = list(directory.glob("*.yml")) + list(directory.glob("*.yaml"))

        if not yaml_files:
            return True, "No YAML files found to validate"

        all_valid = True
        messages = []

        for yaml_file in yaml_files:
            is_valid, message = self.validate_file(yaml_file)
            if is_valid:
                messages.append(f"✅ {yaml_file.name}: {message}")
            else:
                messages.append(f"❌ {yaml_file.name}: {message}")
                all_valid = False

        return all_valid, "\n".join(messages)

def main():
    validator = ConfigValidator()

    if len(sys.argv) < 2:
        print("Usage: python3 validate_config.py <file_or_directory>")
        print("Examples:")
        print("  python3 validate_config.py config/alerts.yaml")
        print("  python3 validate_config.py services/arcanum-orchestrator/")
        sys.exit(1)

    target = sys.argv[1]
    target_path = Path(target)

    if target_path.is_file():
        is_valid, message = validator.validate_file(target_path)
    elif target_path.is_dir():
        is_valid, message = validator.validate_directory(target_path)
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)

    print(message)

    if is_valid:
        print("\n🎉 All validations passed!")
        sys.exit(0)
    else:
        print("\n💥 Validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()