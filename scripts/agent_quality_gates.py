#!/usr/bin/env python3
"""
Phase 4 AI Agents: Quality Gates for Agent Deployments
Automated checks to ensure agents meet standards before deployment
"""

import json
import yaml
import requests
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

class AgentQualityGates:
    def __init__(self, prometheus_url="http://localhost:9090", arcanum_url="http://localhost:8000"):
        self.prometheus_url = prometheus_url
        self.arcanum_url = arcanum_url
        self.agents_dir = Path("agents")
        self.quality_standards = {
            'min_success_rate': 0.95,  # 95% minimum success rate
            'max_latency_p95_ms': 5000,  # 5s maximum latency
            'min_sample_size': 10,  # Minimum interactions for reliable stats
            'max_cost_per_hour_cents': 100,  # Maximum cost threshold
            'required_files': ['system_prompt_file'],  # Required agent files
            'schema_compliance': True  # Must pass schema validation
        }

    def run_quality_gates(self, agent_name: str, canary_mode: bool = False) -> Dict[str, Any]:
        """Run all quality gates for an agent"""
        print(f"🚦 Running quality gates for agent: {agent_name}")

        results = {
            'agent': agent_name,
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'canary_mode': canary_mode,
            'overall_status': 'PASS',
            'gates': {},
            'warnings': [],
            'blockers': []
        }

        # Gate 1: Schema Validation
        schema_result = self._check_schema_compliance(agent_name)
        results['gates']['schema_validation'] = schema_result
        if not schema_result['passed']:
            results['overall_status'] = 'FAIL'
            results['blockers'].extend(schema_result['issues'])

        # Gate 2: Required Files
        files_result = self._check_required_files(agent_name)
        results['gates']['required_files'] = files_result
        if not files_result['passed']:
            results['overall_status'] = 'FAIL'
            results['blockers'].extend(files_result['issues'])

        # Gate 3: Performance SLOs (if enough data exists)
        slo_result = self._check_performance_slos(agent_name)
        results['gates']['performance_slos'] = slo_result
        if not slo_result['passed']:
            if slo_result['has_sufficient_data']:
                results['overall_status'] = 'FAIL'
                results['blockers'].extend(slo_result['issues'])
            else:
                results['warnings'].append("Insufficient performance data for SLO validation")

        # Gate 4: Cost Thresholds
        cost_result = self._check_cost_thresholds(agent_name)
        results['gates']['cost_thresholds'] = cost_result
        if not cost_result['passed']:
            if cost_result.get('severity') == 'critical':
                results['overall_status'] = 'FAIL'
                results['blockers'].extend(cost_result['issues'])
            else:
                results['warnings'].extend(cost_result['issues'])

        # Gate 5: Security Checks
        security_result = self._check_security_requirements(agent_name)
        results['gates']['security'] = security_result
        if not security_result['passed']:
            results['overall_status'] = 'FAIL'
            results['blockers'].extend(security_result['issues'])

        # Gate 6: Canary-specific checks
        if canary_mode:
            canary_result = self._check_canary_readiness(agent_name)
            results['gates']['canary_readiness'] = canary_result
            if not canary_result['passed']:
                results['overall_status'] = 'FAIL'
                results['blockers'].extend(canary_result['issues'])

        print(f"{'✅' if results['overall_status'] == 'PASS' else '❌'} Quality gates: {results['overall_status']}")

        return results

    def _check_schema_compliance(self, agent_name: str) -> Dict[str, Any]:
        """Validate agent specification against schema"""
        result = {'passed': False, 'issues': []}

        try:
            from .agent_registry import AgentRegistry
            registry = AgentRegistry()
            agent_spec = registry.load_agent_spec(agent_name)

            if agent_spec:
                result['passed'] = True
                result['spec_version'] = agent_spec.get('version', 'unknown')
            else:
                result['issues'].append(f"Agent specification failed validation: {agent_name}")

        except Exception as e:
            result['issues'].append(f"Schema validation error: {e}")

        return result

    def _check_required_files(self, agent_name: str) -> Dict[str, Any]:
        """Check that all required files exist"""
        result = {'passed': True, 'issues': [], 'files_checked': []}

        try:
            agent_file = self.agents_dir / f"{agent_name}.yaml"
            if not agent_file.exists():
                result['passed'] = False
                result['issues'].append(f"Agent specification file missing: {agent_file}")
                return result

            with open(agent_file, 'r') as f:
                agent_spec = yaml.safe_load(f)

            # Check for required files
            for file_key in self.quality_standards['required_files']:
                file_path = agent_spec.get(file_key)
                if file_path:
                    full_path = Path(file_path)
                    result['files_checked'].append(str(full_path))
                    if not full_path.exists():
                        result['passed'] = False
                        result['issues'].append(f"Required file missing: {file_path}")
                else:
                    result['issues'].append(f"Required file path not specified: {file_key}")

        except Exception as e:
            result['passed'] = False
            result['issues'].append(f"Error checking required files: {e}")

        return result

    def _check_performance_slos(self, agent_name: str) -> Dict[str, Any]:
        """Check agent performance against SLO targets"""
        result = {
            'passed': True,
            'issues': [],
            'has_sufficient_data': False,
            'metrics': {}
        }

        try:
            # Query Prometheus for agent metrics
            slo_status = self._get_agent_slo_status(agent_name)

            if slo_status and slo_status.get('total_interactions', 0) >= self.quality_standards['min_sample_size']:
                result['has_sufficient_data'] = True
                result['metrics'] = slo_status

                # Check success rate
                success_rate = slo_status.get('current_success_rate', 1.0)
                if success_rate < self.quality_standards['min_success_rate']:
                    result['passed'] = False
                    result['issues'].append(
                        f"Success rate {success_rate:.1%} below threshold {self.quality_standards['min_success_rate']:.1%}"
                    )

                # Check latency
                avg_latency = slo_status.get('current_avg_latency_ms', 0)
                if avg_latency > self.quality_standards['max_latency_p95_ms']:
                    result['passed'] = False
                    result['issues'].append(
                        f"Average latency {avg_latency}ms exceeds threshold {self.quality_standards['max_latency_p95_ms']}ms"
                    )
            else:
                result['issues'].append(f"Insufficient performance data (need ≥{self.quality_standards['min_sample_size']} interactions)")

        except Exception as e:
            result['issues'].append(f"Error checking performance SLOs: {e}")

        return result

    def _check_cost_thresholds(self, agent_name: str) -> Dict[str, Any]:
        """Check agent cost against thresholds"""
        result = {'passed': True, 'issues': [], 'severity': 'warning'}

        try:
            # Query cost metrics from Prometheus
            cost_query = f'rate(agent_cost_cents_total{{agent_name="{agent_name}"}}[1h])'
            cost_data = self._query_prometheus(cost_query)

            if cost_data and len(cost_data) > 0:
                hourly_cost = float(cost_data[0]['value'][1])
                result['hourly_cost_cents'] = hourly_cost

                if hourly_cost > self.quality_standards['max_cost_per_hour_cents']:
                    result['passed'] = False
                    result['severity'] = 'critical' if hourly_cost > (self.quality_standards['max_cost_per_hour_cents'] * 2) else 'warning'
                    result['issues'].append(
                        f"Cost rate {hourly_cost:.2f} cents/hour exceeds threshold {self.quality_standards['max_cost_per_hour_cents']}"
                    )
            else:
                result['issues'].append("No cost data available for analysis")

        except Exception as e:
            result['issues'].append(f"Error checking cost thresholds: {e}")

        return result

    def _check_security_requirements(self, agent_name: str) -> Dict[str, Any]:
        """Check security requirements for agent"""
        result = {'passed': True, 'issues': []}

        try:
            agent_file = self.agents_dir / f"{agent_name}.yaml"
            if agent_file.exists():
                with open(agent_file, 'r') as f:
                    content = f.read()

                # Check for hardcoded secrets (basic patterns)
                security_patterns = [
                    'sk-',  # OpenAI API keys
                    'pk-',  # Public keys
                    'password',
                    'secret',
                    'token'
                ]

                for pattern in security_patterns:
                    if pattern in content.lower() and not content.lower().startswith('#'):
                        result['passed'] = False
                        result['issues'].append(f"Potential hardcoded secret detected: {pattern}")

                # Check for proper environment variable usage
                if 'environ.get' not in content and ('password' in content.lower() or 'key' in content.lower()):
                    result['issues'].append("Consider using environment variables for sensitive configuration")

        except Exception as e:
            result['issues'].append(f"Error checking security requirements: {e}")

        return result

    def _check_canary_readiness(self, agent_name: str) -> Dict[str, Any]:
        """Check if agent is ready for canary deployment"""
        result = {'passed': True, 'issues': []}

        try:
            # Check if there's already an active canary for this agent
            canary_config_file = Path("config/deployments/canary_config.yaml")
            if canary_config_file.exists():
                with open(canary_config_file, 'r') as f:
                    canary_config = yaml.safe_load(f)

                if agent_name in canary_config.get('agents', {}):
                    existing_canary = canary_config['agents'][agent_name]
                    if existing_canary.get('status') == 'active':
                        result['passed'] = False
                        result['issues'].append(f"Active canary deployment already exists: {existing_canary['deployment_id']}")

            # Check baseline performance exists
            baseline_slo = self._get_agent_slo_status(agent_name)
            if not baseline_slo or baseline_slo.get('total_interactions', 0) < self.quality_standards['min_sample_size']:
                result['passed'] = False
                result['issues'].append("Insufficient baseline performance data for canary comparison")

        except Exception as e:
            result['issues'].append(f"Error checking canary readiness: {e}")

        return result

    def _get_agent_slo_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent SLO status from arcanum service"""
        try:
            response = requests.get(f"{self.arcanum_url}/agents/{agent_name}/slo", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return None

    def _query_prometheus(self, query: str) -> Optional[List[Dict]]:
        """Query Prometheus for metrics"""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('result', [])
        except requests.RequestException:
            pass
        return None

    def save_quality_report(self, results: Dict[str, Any], output_file: Optional[str] = None):
        """Save quality gate results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"reports/quality_gates_{results['agent']}_{timestamp}.json"

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"📋 Quality report saved: {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 agent_quality_gates.py <command> [args...]")
        print("Commands:")
        print("  check <agent_name>                    - Run quality gates for agent")
        print("  check-canary <agent_name>            - Run canary-specific quality gates")
        print("  batch-check [agent1,agent2,...]     - Run quality gates for multiple agents")
        print("  standards                            - Show quality standards")
        sys.exit(1)

    gates = AgentQualityGates()
    command = sys.argv[1]

    if command == "check" and len(sys.argv) > 2:
        agent_name = sys.argv[2]
        results = gates.run_quality_gates(agent_name)

        # Print summary
        print(f"\n📊 Quality Gates Summary for {agent_name}:")
        print(f"Overall Status: {'✅ PASS' if results['overall_status'] == 'PASS' else '❌ FAIL'}")

        if results['blockers']:
            print("\n🚫 Blockers:")
            for blocker in results['blockers']:
                print(f"  • {blocker}")

        if results['warnings']:
            print("\n⚠️ Warnings:")
            for warning in results['warnings']:
                print(f"  • {warning}")

        # Save report
        gates.save_quality_report(results)

    elif command == "check-canary" and len(sys.argv) > 2:
        agent_name = sys.argv[2]
        results = gates.run_quality_gates(agent_name, canary_mode=True)

        print(f"\n📊 Canary Quality Gates Summary for {agent_name}:")
        print(f"Overall Status: {'✅ PASS' if results['overall_status'] == 'PASS' else '❌ FAIL'}")

        gates.save_quality_report(results)

    elif command == "batch-check":
        agent_names = sys.argv[2].split(',') if len(sys.argv) > 2 else []
        if not agent_names:
            # Auto-discover agents
            agents_dir = Path("agents")
            if agents_dir.exists():
                agent_names = [f.stem for f in agents_dir.glob("*.yaml")]

        print(f"🔍 Running quality gates for {len(agent_names)} agents...")

        results_summary = {'passed': 0, 'failed': 0, 'agents': {}}

        for agent_name in agent_names:
            print(f"\n--- {agent_name} ---")
            results = gates.run_quality_gates(agent_name)

            if results['overall_status'] == 'PASS':
                results_summary['passed'] += 1
            else:
                results_summary['failed'] += 1

            results_summary['agents'][agent_name] = results['overall_status']
            gates.save_quality_report(results)

        print(f"\n🎯 Batch Quality Gates Summary:")
        print(f"Passed: {results_summary['passed']}")
        print(f"Failed: {results_summary['failed']}")

    elif command == "standards":
        print("📏 Quality Standards:")
        print(f"  • Minimum Success Rate: {gates.quality_standards['min_success_rate']:.1%}")
        print(f"  • Maximum Latency P95: {gates.quality_standards['max_latency_p95_ms']}ms")
        print(f"  • Minimum Sample Size: {gates.quality_standards['min_sample_size']} interactions")
        print(f"  • Maximum Cost/Hour: {gates.quality_standards['max_cost_per_hour_cents']} cents")
        print(f"  • Required Files: {', '.join(gates.quality_standards['required_files'])}")
        print(f"  • Schema Compliance: {'Required' if gates.quality_standards['schema_compliance'] else 'Optional'}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()