#!/usr/bin/env python3
"""
Phase 2 GitOps: Pull-based deployment system
Deploys services based on environment-specific configurations
"""

import yaml
import subprocess
import sys
import os
import tempfile
from pathlib import Path

class GitOpsDeployer:
    def __init__(self, environment="dev"):
        self.environment = environment
        self.config_dir = Path(f"config/environments/{environment}")
        self.temp_dir = Path(tempfile.mkdtemp())

    def load_service_config(self, service_name):
        """Load environment-specific service configuration"""
        config_file = self.config_dir / f"{service_name}.yaml"

        if not config_file.exists():
            print(f"❌ Configuration not found: {config_file}")
            return None

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        print(f"✅ Loaded {service_name} config for {self.environment}")
        return config

    def validate_config(self, config):
        """Validate service configuration"""
        required_fields = ['service', 'secrets']

        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False

        service = config['service']
        required_service_fields = ['name', 'image', 'port']

        for field in required_service_fields:
            if field not in service:
                print(f"❌ Missing required service field: {field}")
                return False

        print("✅ Configuration validation passed")
        return True

    def generate_docker_compose(self, config):
        """Generate Docker Compose file from configuration"""
        service = config['service']
        resources = service.get('resources', {})
        health_check = service.get('health_check', {})

        compose_data = {
            'version': '3.9',
            'services': {
                service['name']: {
                    'image': service['image'],
                    'ports': [f"{service['port']}:{service['port']}"],
                    'restart': 'unless-stopped',
                    'environment': []
                }
            }
        }

        # Add health check
        if health_check:
            compose_data['services'][service['name']]['healthcheck'] = {
                'test': ["CMD", "curl", "-f", f"http://localhost:{service['port']}{health_check.get('endpoint', '/healthz')}"],
                'interval': health_check.get('interval', '30s'),
                'timeout': health_check.get('timeout', '10s'),
                'retries': health_check.get('retries', 3),
                'start_period': '40s'
            }

        # Add resource limits
        if resources:
            compose_data['services'][service['name']]['deploy'] = {
                'resources': {
                    'limits': {
                        'memory': resources.get('memory', '512M'),
                        'cpus': str(resources.get('cpu', 0.5))
                    },
                    'reservations': {
                        'memory': resources.get('memory', '256M'),
                        'cpus': str(resources.get('cpu', 0.25))
                    }
                }
            }

        # Add environment variables for secrets
        env_vars = []
        for secret in config.get('secrets', []):
            env_vars.append(f"{secret['env_var']}=${{{secret['env_var']}}}")

        # Add model configuration
        models = service.get('models', {})
        if 'claude' in models:
            env_vars.extend([
                f"CLAUDE_MODEL={models['claude']['model']}",
                f"CLAUDE_MAX_TOKENS={models['claude']['max_tokens']}"
            ])
        if 'gemini' in models:
            env_vars.extend([
                f"GEMINI_MODEL={models['gemini']['model']}",
                f"GEMINI_MAX_TOKENS={models['gemini']['max_tokens']}"
            ])

        # Add feature flags
        features = service.get('features', {})
        if features.get('journal_logging'):
            env_vars.extend([
                "ARCANUM_APPEND_JOURNAL=true",
                "ARCANUM_CHRONICLE_PATH=../../docs/chronicle.md"
            ])

        env_vars.append("ARCANUM_SCHEMA_PATH=schemas/output.default.json")

        compose_data['services'][service['name']]['environment'] = env_vars

        return compose_data

    def deploy_service(self, service_name):
        """Deploy a service using GitOps approach"""
        print(f"🚀 Deploying {service_name} to {self.environment}...")

        # Load configuration
        config = self.load_service_config(service_name)
        if not config:
            return False

        # Validate configuration
        if not self.validate_config(config):
            return False

        # Validate with our config validator
        config_file = self.config_dir / f"{service_name}.yaml"
        result = subprocess.run([
            "python3", "scripts/validate_config.py", str(config_file)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Configuration validation failed: {result.stderr}")
            return False

        # Generate Docker Compose
        compose_data = self.generate_docker_compose(config)

        # Write temporary compose file
        temp_compose = self.temp_dir / "docker-compose.yaml"
        with open(temp_compose, 'w') as f:
            yaml.dump(compose_data, f, default_flow_style=False)

        print(f"📝 Generated Docker Compose: {temp_compose}")

        # Load secrets
        print("🔐 Loading secrets...")
        result = subprocess.run([
            "bash", "-c", "source scripts/load_secrets.sh && env"
        ], capture_output=True, text=True, cwd=Path.cwd())

        if result.returncode != 0:
            print(f"❌ Failed to load secrets: {result.stderr}")
            return False

        # Deploy using Docker Compose
        print("🐳 Deploying with Docker Compose...")
        env = os.environ.copy()

        # Extract secrets from the sourced environment
        for line in result.stdout.split('\n'):
            if '=' in line and ('API_KEY' in line):
                key, value = line.split('=', 1)
                env[key] = value

        deploy_result = subprocess.run([
            "docker-compose", "-f", str(temp_compose), "up", "-d"
        ], env=env, capture_output=True, text=True)

        if deploy_result.returncode != 0:
            print(f"❌ Deployment failed: {deploy_result.stderr}")
            return False

        # Wait and verify deployment
        print("⏳ Waiting for service to start...")
        import time
        time.sleep(10)

        # Health check
        port = config['service']['port']
        health_endpoint = config['service'].get('health_check', {}).get('endpoint', '/healthz')

        health_result = subprocess.run([
            "curl", "-sf", f"http://localhost:{port}{health_endpoint}"
        ], capture_output=True)

        if health_result.returncode == 0:
            print("✅ Deployment successful! Service is healthy.")
            return True
        else:
            print("❌ Deployment failed - health check failed")
            return False

    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 gitops_deploy.py <environment> <service>")
        print("Examples:")
        print("  python3 gitops_deploy.py dev arcanum")
        print("  python3 gitops_deploy.py prod arcanum")
        sys.exit(1)

    environment = sys.argv[1]
    service = sys.argv[2]

    # Change to script directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)

    deployer = GitOpsDeployer(environment)

    try:
        success = deployer.deploy_service(service)
        if success:
            print(f"\n🎉 {service} deployed successfully to {environment}!")
        else:
            print(f"\n💥 Failed to deploy {service} to {environment}")
            sys.exit(1)
    finally:
        deployer.cleanup()

if __name__ == "__main__":
    main()