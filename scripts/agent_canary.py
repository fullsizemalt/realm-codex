#!/usr/bin/env python3
"""
Phase 4 AI Agents: Canary deployment system for agent configurations
Safely deploy agent changes with automatic rollback on SLO violations
"""

import yaml
import json
import time
import random
import hashlib
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

class AgentCanaryDeployer:
    def __init__(self):
        self.deployments_dir = Path("config/deployments")
        self.deployments_dir.mkdir(exist_ok=True)
        self.current_deployment_file = self.deployments_dir / "current.yaml"
        self.canary_config_file = self.deployments_dir / "canary_config.yaml"

    def create_canary_deployment(self, agent_name: str, new_config_file: str,
                               canary_percentage: int = 10, duration_minutes: int = 30) -> str:
        """Create a new canary deployment for an agent"""

        # Load current agent config
        current_config = self._load_agent_config(agent_name)
        if not current_config:
            print(f"❌ Current config not found for agent: {agent_name}")
            return None

        # Load new agent config
        new_config_path = Path(new_config_file)
        if not new_config_path.exists():
            print(f"❌ New config file not found: {new_config_file}")
            return None

        with open(new_config_path, 'r') as f:
            new_config = yaml.safe_load(f)

        # Generate deployment ID
        deployment_id = hashlib.sha256(
            f"{agent_name}{time.time()}".encode()
        ).hexdigest()[:12]

        # Create canary deployment record
        canary_deployment = {
            'deployment_id': deployment_id,
            'agent_name': agent_name,
            'created_at': datetime.utcnow().isoformat() + "Z",
            'canary_percentage': canary_percentage,
            'duration_minutes': duration_minutes,
            'status': 'active',
            'configs': {
                'current': current_config,
                'canary': new_config
            },
            'slo_violations': 0,
            'total_requests': 0,
            'canary_requests': 0,
            'rollback_conditions': {
                'max_error_rate': 0.05,  # 5% error rate triggers rollback
                'max_latency_increase': 1.5,  # 50% latency increase triggers rollback
                'min_requests_for_decision': 10  # Minimum requests before making rollback decision
            }
        }

        # Save canary deployment
        deployment_file = self.deployments_dir / f"canary_{deployment_id}.yaml"
        with open(deployment_file, 'w') as f:
            yaml.dump(canary_deployment, f, default_flow_style=False)

        # Update active canary configuration
        self._update_canary_config(agent_name, deployment_id, canary_percentage)

        print(f"✅ Canary deployment created: {deployment_id}")
        print(f"   Agent: {agent_name}")
        print(f"   Traffic: {canary_percentage}%")
        print(f"   Duration: {duration_minutes} minutes")

        return deployment_id

    def should_use_canary(self, agent_name: str) -> bool:
        """Determine if a request should use the canary configuration"""
        canary_config = self._load_canary_config()
        if not canary_config:
            return False

        agent_canary = canary_config.get('agents', {}).get(agent_name)
        if not agent_canary or agent_canary['status'] != 'active':
            return False

        # Use random selection based on canary percentage
        return random.randint(1, 100) <= agent_canary['canary_percentage']

    def get_agent_config(self, agent_name: str, force_canary: bool = False) -> Dict[str, Any]:
        """Get the appropriate agent configuration (current or canary)"""
        use_canary = force_canary or self.should_use_canary(agent_name)

        if use_canary:
            canary_config = self._get_canary_config_for_agent(agent_name)
            if canary_config:
                self._record_canary_usage(agent_name)
                return canary_config

        # Return current configuration
        return self._load_agent_config(agent_name)

    def record_request_result(self, agent_name: str, latency_ms: int, success: bool,
                            used_canary: bool = False):
        """Record the result of an agent request for canary analysis"""
        canary_config = self._load_canary_config()
        if not canary_config:
            return

        agent_canary = canary_config.get('agents', {}).get(agent_name)
        if not agent_canary or agent_canary['status'] != 'active':
            return

        deployment_id = agent_canary['deployment_id']
        deployment = self._load_deployment(deployment_id)
        if not deployment:
            return

        # Update deployment statistics
        deployment['total_requests'] += 1
        if used_canary:
            deployment['canary_requests'] += 1

        if not success:
            deployment['slo_violations'] += 1

        # Check for rollback conditions
        should_rollback = self._should_rollback(deployment)
        if should_rollback:
            self.rollback_deployment(deployment_id)
        else:
            # Save updated deployment
            self._save_deployment(deployment)

    def _should_rollback(self, deployment: Dict[str, Any]) -> bool:
        """Check if deployment should be rolled back based on SLO violations"""
        conditions = deployment['rollback_conditions']
        total_requests = deployment['total_requests']

        # Need minimum requests to make a decision
        if total_requests < conditions['min_requests_for_decision']:
            return False

        # Check error rate
        error_rate = deployment['slo_violations'] / total_requests
        if error_rate > conditions['max_error_rate']:
            print(f"🚨 Rollback triggered: Error rate {error_rate:.2%} > {conditions['max_error_rate']:.2%}")
            return True

        # Could add more sophisticated checks here (latency increases, etc.)

        return False

    def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback a canary deployment"""
        deployment = self._load_deployment(deployment_id)
        if not deployment:
            print(f"❌ Deployment not found: {deployment_id}")
            return False

        agent_name = deployment['agent_name']

        # Mark deployment as rolled back
        deployment['status'] = 'rolled_back'
        deployment['rolled_back_at'] = datetime.utcnow().isoformat() + "Z"
        self._save_deployment(deployment)

        # Remove from active canary config
        self._remove_from_canary_config(agent_name)

        print(f"🔄 Rolled back canary deployment: {deployment_id}")
        print(f"   Agent: {agent_name}")
        print(f"   Reason: SLO violations detected")

        return True

    def promote_deployment(self, deployment_id: str) -> bool:
        """Promote a successful canary deployment to production"""
        deployment = self._load_deployment(deployment_id)
        if not deployment:
            print(f"❌ Deployment not found: {deployment_id}")
            return False

        agent_name = deployment['agent_name']
        canary_config = deployment['configs']['canary']

        # Update the main agent configuration
        agent_file = Path(f"agents/{agent_name.replace('spirit-', '')}.yaml")
        if agent_file.exists():
            with open(agent_file, 'w') as f:
                yaml.dump(canary_config, f, default_flow_style=False)

        # Mark deployment as promoted
        deployment['status'] = 'promoted'
        deployment['promoted_at'] = datetime.utcnow().isoformat() + "Z"
        self._save_deployment(deployment)

        # Remove from active canary config
        self._remove_from_canary_config(agent_name)

        print(f"🚀 Promoted canary deployment: {deployment_id}")
        print(f"   Agent: {agent_name}")
        print(f"   New config is now live for 100% of traffic")

        return True

    def check_expired_deployments(self):
        """Check for and clean up expired canary deployments"""
        canary_config = self._load_canary_config()
        if not canary_config:
            return

        current_time = datetime.utcnow()

        for agent_name, agent_canary in canary_config.get('agents', {}).items():
            if agent_canary['status'] != 'active':
                continue

            deployment = self._load_deployment(agent_canary['deployment_id'])
            if not deployment:
                continue

            # Check if deployment has expired
            created_at = datetime.fromisoformat(deployment['created_at'].replace('Z', '+00:00'))
            duration = timedelta(minutes=deployment['duration_minutes'])

            if current_time > created_at + duration:
                # Auto-promote if no issues detected
                if deployment['slo_violations'] == 0 or deployment['total_requests'] == 0:
                    print(f"⏰ Auto-promoting expired deployment: {deployment['deployment_id']}")
                    self.promote_deployment(deployment['deployment_id'])
                else:
                    print(f"⏰ Auto-rolling back expired deployment with issues: {deployment['deployment_id']}")
                    self.rollback_deployment(deployment['deployment_id'])

    def list_active_deployments(self) -> List[Dict[str, Any]]:
        """List all active canary deployments"""
        canary_config = self._load_canary_config()
        if not canary_config:
            return []

        active_deployments = []
        for agent_name, agent_canary in canary_config.get('agents', {}).items():
            if agent_canary['status'] == 'active':
                deployment = self._load_deployment(agent_canary['deployment_id'])
                if deployment:
                    active_deployments.append(deployment)

        return active_deployments

    # Helper methods
    def _load_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load current agent configuration"""
        agent_file = Path(f"agents/{agent_name.replace('spirit-', '')}.yaml")
        if not agent_file.exists():
            return None

        with open(agent_file, 'r') as f:
            return yaml.safe_load(f)

    def _load_canary_config(self) -> Optional[Dict[str, Any]]:
        """Load canary configuration"""
        if not self.canary_config_file.exists():
            return None

        with open(self.canary_config_file, 'r') as f:
            return yaml.safe_load(f)

    def _load_deployment(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Load deployment record"""
        deployment_file = self.deployments_dir / f"canary_{deployment_id}.yaml"
        if not deployment_file.exists():
            return None

        with open(deployment_file, 'r') as f:
            return yaml.safe_load(f)

    def _save_deployment(self, deployment: Dict[str, Any]):
        """Save deployment record"""
        deployment_id = deployment['deployment_id']
        deployment_file = self.deployments_dir / f"canary_{deployment_id}.yaml"

        with open(deployment_file, 'w') as f:
            yaml.dump(deployment, f, default_flow_style=False)

    def _update_canary_config(self, agent_name: str, deployment_id: str, canary_percentage: int):
        """Update active canary configuration"""
        canary_config = self._load_canary_config() or {'agents': {}}

        canary_config['agents'][agent_name] = {
            'deployment_id': deployment_id,
            'canary_percentage': canary_percentage,
            'status': 'active'
        }

        with open(self.canary_config_file, 'w') as f:
            yaml.dump(canary_config, f, default_flow_style=False)

    def _remove_from_canary_config(self, agent_name: str):
        """Remove agent from active canary configuration"""
        canary_config = self._load_canary_config()
        if canary_config and agent_name in canary_config.get('agents', {}):
            del canary_config['agents'][agent_name]

            with open(self.canary_config_file, 'w') as f:
                yaml.dump(canary_config, f, default_flow_style=False)

    def _get_canary_config_for_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get canary configuration for specific agent"""
        canary_config = self._load_canary_config()
        if not canary_config:
            return None

        agent_canary = canary_config.get('agents', {}).get(agent_name)
        if not agent_canary:
            return None

        deployment = self._load_deployment(agent_canary['deployment_id'])
        if deployment:
            return deployment['configs']['canary']

        return None

    def _record_canary_usage(self, agent_name: str):
        """Record that canary config was used"""
        # This could increment metrics or logs for tracking
        pass

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent_canary.py <command> [args...]")
        print("Commands:")
        print("  deploy <agent> <config_file> [percentage] [duration_min] - Create canary deployment")
        print("  list                                                     - List active deployments")
        print("  rollback <deployment_id>                                - Rollback deployment")
        print("  promote <deployment_id>                                 - Promote deployment")
        print("  check-expired                                           - Check for expired deployments")
        sys.exit(1)

    deployer = AgentCanaryDeployer()
    command = sys.argv[1]

    if command == "deploy" and len(sys.argv) >= 4:
        agent_name = sys.argv[2]
        config_file = sys.argv[3]
        percentage = int(sys.argv[4]) if len(sys.argv) > 4 else 10
        duration = int(sys.argv[5]) if len(sys.argv) > 5 else 30

        deployment_id = deployer.create_canary_deployment(
            agent_name, config_file, percentage, duration
        )

    elif command == "list":
        deployments = deployer.list_active_deployments()
        if deployments:
            print(f"\n📋 Active canary deployments ({len(deployments)}):")
            for deployment in deployments:
                print(f"  • {deployment['deployment_id']} - {deployment['agent_name']}")
                print(f"    Traffic: {deployment['canary_percentage']}%")
                print(f"    Requests: {deployment['total_requests']} ({deployment['canary_requests']} canary)")
                print(f"    SLO violations: {deployment['slo_violations']}")
                print()
        else:
            print("No active canary deployments")

    elif command == "rollback" and len(sys.argv) > 2:
        deployment_id = sys.argv[2]
        deployer.rollback_deployment(deployment_id)

    elif command == "promote" and len(sys.argv) > 2:
        deployment_id = sys.argv[2]
        deployer.promote_deployment(deployment_id)

    elif command == "check-expired":
        deployer.check_expired_deployments()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()