#!/usr/bin/env python3
"""
Phase 4 AI Agents: Agent Registry and Management System
Handles agent specifications, validation, and deployment
"""

import yaml
import json
import hashlib
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

class AgentRegistry:
    def __init__(self, agents_dir="agents", schema_file="schemas/agent.spec.v1.json"):
        self.agents_dir = Path(agents_dir)
        self.schema_file = Path(schema_file)
        self.schema = self._load_schema()
        self.registry_file = Path("config/agent_registry.yaml")

    def _load_schema(self) -> Dict[str, Any]:
        """Load the agent specification schema"""
        try:
            with open(self.schema_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Agent schema not found: {self.schema_file}")
            sys.exit(1)

    def validate_agent_spec(self, agent_path: Path) -> bool:
        """Validate an agent specification against basic requirements"""
        try:
            with open(agent_path, 'r') as f:
                agent_spec = yaml.safe_load(f)

            # Basic validation - check required fields
            required_fields = ['name', 'provider', 'model', 'purpose', 'version', 'slo']
            for field in required_fields:
                if field not in agent_spec:
                    print(f"❌ {agent_path.name}: Missing required field '{field}'")
                    return False

            # Validate SLO structure
            slo = agent_spec.get('slo', {})
            if 'latency_p95_ms' not in slo or 'success_rate' not in slo:
                print(f"❌ {agent_path.name}: Invalid SLO structure")
                return False

            # Validate version format (basic check)
            version = agent_spec.get('version', '')
            if not version or len(version.split('.')) != 3:
                print(f"❌ {agent_path.name}: Invalid version format (expected x.y.z)")
                return False

            print(f"✅ {agent_path.name}: Valid agent specification")
            return True

        except yaml.YAMLError as e:
            print(f"❌ {agent_path.name}: YAML error - {e}")
            return False
        except Exception as e:
            print(f"❌ {agent_path.name}: Error - {e}")
            return False

    def load_agent_spec(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Load and validate a specific agent specification"""
        agent_file = self.agents_dir / f"{agent_name}.yaml"

        if not agent_file.exists():
            print(f"❌ Agent not found: {agent_name}")
            return None

        if not self.validate_agent_spec(agent_file):
            return None

        with open(agent_file, 'r') as f:
            return yaml.safe_load(f)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all valid agents in the registry"""
        agents = []

        if not self.agents_dir.exists():
            print(f"❌ Agents directory not found: {self.agents_dir}")
            return agents

        for agent_file in self.agents_dir.glob("*.yaml"):
            if self.validate_agent_spec(agent_file):
                with open(agent_file, 'r') as f:
                    agent_spec = yaml.safe_load(f)
                    agent_spec['file'] = str(agent_file)
                    agents.append(agent_spec)

        return sorted(agents, key=lambda x: x['name'])

    def get_agent_hash(self, agent_name: str) -> Optional[str]:
        """Generate a hash for agent specification (for change detection)"""
        agent_spec = self.load_agent_spec(agent_name)
        if not agent_spec:
            return None

        # Remove dynamic fields for consistent hashing
        stable_spec = {k: v for k, v in agent_spec.items()
                      if k not in ['updated', 'file']}

        spec_str = json.dumps(stable_spec, sort_keys=True)
        return hashlib.sha256(spec_str.encode()).hexdigest()[:12]

    def check_agent_compatibility(self, agent1_name: str, agent2_name: str) -> bool:
        """Check if two agents are compatible for handoffs"""
        agent1 = self.load_agent_spec(agent1_name)
        agent2 = self.load_agent_spec(agent2_name)

        if not agent1 or not agent2:
            return False

        # Check if agents share the same output contract
        contract1 = agent1.get('collaboration', {}).get('output_contract')
        contract2 = agent2.get('collaboration', {}).get('output_contract')

        if contract1 and contract2 and contract1 == contract2:
            return True

        # Check explicit compatibility list
        compatible = agent1.get('collaboration', {}).get('compatible_agents', [])
        return agent2['name'] in compatible

    def update_registry(self):
        """Update the central agent registry file"""
        agents = self.list_agents()

        registry_data = {
            'updated': datetime.now().isoformat(),
            'agents': {},
            'compatibility_matrix': {},
            'deployment_status': {}
        }

        for agent in agents:
            agent_name = agent['name']
            registry_data['agents'][agent_name] = {
                'version': agent['version'],
                'provider': agent['provider'],
                'model': agent['model'],
                'purpose': agent['purpose'],
                'slo': agent['slo'],
                'hash': self.get_agent_hash(agent_name),
                'file': agent['file'].replace(str(Path.cwd()) + '/', '')
            }

        # Build compatibility matrix
        agent_names = list(registry_data['agents'].keys())
        for agent1 in agent_names:
            registry_data['compatibility_matrix'][agent1] = {}
            for agent2 in agent_names:
                if agent1 != agent2:
                    registry_data['compatibility_matrix'][agent1][agent2] = \
                        self.check_agent_compatibility(agent1, agent2)

        # Save registry
        self.registry_file.parent.mkdir(exist_ok=True)
        with open(self.registry_file, 'w') as f:
            yaml.dump(registry_data, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Registry updated: {len(agents)} agents registered")
        return registry_data

    def get_deployment_candidates(self, agent_name: str) -> Dict[str, Any]:
        """Get deployment readiness info for an agent"""
        agent_spec = self.load_agent_spec(agent_name)
        if not agent_spec:
            return {}

        deployment_info = {
            'agent': agent_name,
            'version': agent_spec['version'],
            'ready_for_deployment': True,
            'checks': {},
            'warnings': [],
            'blockers': []
        }

        # Check if system prompt file exists
        prompt_file = agent_spec.get('system_prompt_file')
        if prompt_file:
            prompt_path = Path(prompt_file)
            deployment_info['checks']['system_prompt'] = prompt_path.exists()
            if not prompt_path.exists():
                deployment_info['blockers'].append(f"System prompt file missing: {prompt_file}")
                deployment_info['ready_for_deployment'] = False

        # Check if output contract exists
        contract_file = agent_spec.get('collaboration', {}).get('output_contract')
        if contract_file:
            contract_path = Path(contract_file)
            deployment_info['checks']['output_contract'] = contract_path.exists()
            if not contract_path.exists():
                deployment_info['warnings'].append(f"Output contract missing: {contract_file}")

        # Check SLO targets are reasonable
        slo = agent_spec.get('slo', {})
        if slo.get('latency_p95_ms', 0) > 10000:
            deployment_info['warnings'].append("High latency target (>10s)")

        # Check for deprecated status
        if agent_spec.get('deprecated', False):
            deployment_info['warnings'].append("Agent is marked as deprecated")

        return deployment_info

    def compare_agent_versions(self, agent_name: str, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions of an agent (useful for canary deployments)"""
        # For now, return basic comparison
        # In a full implementation, you'd load historical versions
        return {
            'agent': agent_name,
            'version1': version1,
            'version2': version2,
            'changes_detected': version1 != version2,
            'breaking_changes': False,  # Would need deeper analysis
            'recommended_rollout': 'canary' if version1 != version2 else 'direct'
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent_registry.py <command> [args...]")
        print("Commands:")
        print("  list                    - List all agents")
        print("  validate <agent>        - Validate specific agent")
        print("  validate-all           - Validate all agents")
        print("  update-registry        - Update central registry")
        print("  deployment-check <agent> - Check deployment readiness")
        print("  compatibility <agent1> <agent2> - Check compatibility")
        sys.exit(1)

    registry = AgentRegistry()
    command = sys.argv[1]

    if command == "list":
        agents = registry.list_agents()
        if agents:
            print(f"\n📋 Found {len(agents)} valid agents:")
            for agent in agents:
                print(f"  • {agent['name']} (v{agent['version']}) - {agent['provider']}/{agent['model']}")
                print(f"    Purpose: {agent['purpose']}")
                print(f"    SLO: {agent['slo']['latency_p95_ms']}ms @ {agent['slo']['success_rate']:.1%}")
                print()
        else:
            print("No valid agents found")

    elif command == "validate" and len(sys.argv) > 2:
        agent_name = sys.argv[2]
        agent_file = Path(f"agents/{agent_name}.yaml")
        if agent_file.exists():
            registry.validate_agent_spec(agent_file)
        else:
            print(f"❌ Agent file not found: {agent_file}")

    elif command == "validate-all":
        agents = registry.list_agents()
        print(f"✅ Validated {len(agents)} agents successfully")

    elif command == "update-registry":
        registry.update_registry()

    elif command == "deployment-check" and len(sys.argv) > 2:
        agent_name = sys.argv[2]
        info = registry.get_deployment_candidates(agent_name)
        if info:
            print(f"\n🚀 Deployment check for {agent_name}:")
            print(f"Version: {info['version']}")
            print(f"Ready: {'✅' if info['ready_for_deployment'] else '❌'}")

            if info['blockers']:
                print("\n🚫 Blockers:")
                for blocker in info['blockers']:
                    print(f"  • {blocker}")

            if info['warnings']:
                print("\n⚠️ Warnings:")
                for warning in info['warnings']:
                    print(f"  • {warning}")

    elif command == "compatibility" and len(sys.argv) > 3:
        agent1, agent2 = sys.argv[2], sys.argv[3]
        compatible = registry.check_agent_compatibility(agent1, agent2)
        print(f"🔗 {agent1} ↔ {agent2}: {'✅ Compatible' if compatible else '❌ Not compatible'}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()