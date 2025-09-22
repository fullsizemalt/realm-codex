"""
Phase 4 AI Agents: Agent-specific metrics collection
Integrates with Prometheus for SLO monitoring
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import time
import json
from .attribution import _attribution_logger

# Agent-specific metrics
AGENT_REQUESTS = Counter(
    'agent_requests_total',
    'Total requests per agent',
    ['agent_name', 'provider', 'model', 'status']
)

AGENT_LATENCY = Histogram(
    'agent_latency_seconds',
    'Request latency per agent',
    ['agent_name', 'provider', 'model'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

AGENT_TOKEN_USAGE = Counter(
    'agent_tokens_total',
    'Token usage per agent',
    ['agent_name', 'provider', 'model', 'type']  # type: input, output
)

AGENT_SLO_VIOLATIONS = Counter(
    'agent_slo_violations_total',
    'SLO violations per agent',
    ['agent_name', 'slo_type']  # slo_type: latency, success_rate
)

ACTIVE_AGENTS = Gauge(
    'active_agents',
    'Number of active agents',
    ['provider']
)

AGENT_COST_ESTIMATES = Counter(
    'agent_cost_cents_total',
    'Estimated cost in cents per agent',
    ['agent_name', 'provider', 'model']
)

# Agent registry info
AGENT_INFO = Info(
    'agent_info',
    'Agent configuration information',
    ['agent_name']
)

class AgentMetricsCollector:
    def __init__(self):
        self.agent_specs = {}
        self.load_agent_specs()

    def load_agent_specs(self):
        """Load agent specifications for SLO comparison"""
        try:
            import yaml
            from pathlib import Path

            agents_dir = Path("config/agent_registry.yaml")
            if agents_dir.exists():
                with open(agents_dir, 'r') as f:
                    registry = yaml.safe_load(f)
                    self.agent_specs = registry.get('agents', {})
        except Exception as e:
            print(f"Warning: Could not load agent specs: {e}")

    def record_agent_interaction(self, agent_name: str, provider: str, model: str,
                               start_time: float, status: str, input_tokens: int = 0,
                               output_tokens: int = 0, error: str = None) -> str:
        """Record metrics for an agent interaction"""

        # Calculate latency
        latency_seconds = time.time() - start_time

        # Record basic metrics
        AGENT_REQUESTS.labels(
            agent_name=agent_name,
            provider=provider,
            model=model,
            status=status
        ).inc()

        AGENT_LATENCY.labels(
            agent_name=agent_name,
            provider=provider,
            model=model
        ).observe(latency_seconds)

        # Record token usage
        if input_tokens > 0:
            AGENT_TOKEN_USAGE.labels(
                agent_name=agent_name,
                provider=provider,
                model=model,
                type='input'
            ).inc(input_tokens)

        if output_tokens > 0:
            AGENT_TOKEN_USAGE.labels(
                agent_name=agent_name,
                provider=provider,
                model=model,
                type='output'
            ).inc(output_tokens)

        # Check SLO violations
        self._check_slo_violations(agent_name, latency_seconds, status)

        # Estimate cost (rough approximation)
        estimated_cost = self._estimate_cost(provider, model, input_tokens, output_tokens)
        if estimated_cost > 0:
            AGENT_COST_ESTIMATES.labels(
                agent_name=agent_name,
                provider=provider,
                model=model
            ).inc(estimated_cost)

        # Update agent info
        self._update_agent_info(agent_name, provider, model)

        return f"metrics_recorded_{agent_name}_{int(time.time())}"

    def _check_slo_violations(self, agent_name: str, latency_seconds: float, status: str):
        """Check if interaction violates agent SLOs"""
        agent_spec = self.agent_specs.get(agent_name, {})
        slo = agent_spec.get('slo', {})

        # Check latency SLO
        max_latency_ms = slo.get('latency_p95_ms', float('inf'))
        if latency_seconds * 1000 > max_latency_ms:
            AGENT_SLO_VIOLATIONS.labels(
                agent_name=agent_name,
                slo_type='latency'
            ).inc()

        # Check success rate SLO (would need windowed calculation for accuracy)
        if status != 'success':
            AGENT_SLO_VIOLATIONS.labels(
                agent_name=agent_name,
                slo_type='success_rate'
            ).inc()

    def _estimate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in cents based on token usage"""
        # Rough cost estimates (would need real pricing data)
        cost_per_1k_tokens = {
            'claude-3-5-sonnet': {'input': 0.3, 'output': 1.5},
            'gemini-1.5-flash': {'input': 0.075, 'output': 0.3},
        }

        model_costs = cost_per_1k_tokens.get(model, {'input': 0.1, 'output': 0.5})

        input_cost = (input_tokens / 1000) * model_costs['input']
        output_cost = (output_tokens / 1000) * model_costs['output']

        return input_cost + output_cost

    def _update_agent_info(self, agent_name: str, provider: str, model: str):
        """Update agent information metric"""
        agent_spec = self.agent_specs.get(agent_name, {})

        info_data = {
            'provider': provider,
            'model': model,
            'version': agent_spec.get('version', 'unknown'),
            'purpose': agent_spec.get('purpose', 'unknown'),
            'slo_latency_ms': str(agent_spec.get('slo', {}).get('latency_p95_ms', 0)),
            'slo_success_rate': str(agent_spec.get('slo', {}).get('success_rate', 0))
        }

        AGENT_INFO.labels(agent_name=agent_name).info(info_data)

    def update_active_agents_count(self):
        """Update count of active agents by provider"""
        provider_counts = {}
        for agent_name, spec in self.agent_specs.items():
            provider = spec.get('provider', 'unknown')
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        for provider, count in provider_counts.items():
            ACTIVE_AGENTS.labels(provider=provider).set(count)

    def get_agent_slo_status(self, agent_name: str, hours_back: int = 1) -> dict:
        """Get current SLO status for an agent"""
        # This would integrate with attribution logs for real SLO calculation
        stats = _attribution_logger.get_interaction_stats(hours_back)

        agent_spec = self.agent_specs.get(agent_name, {})
        slo = agent_spec.get('slo', {})

        return {
            'agent': agent_name,
            'current_success_rate': stats.get('success_rate', 1.0),
            'target_success_rate': slo.get('success_rate', 0.95),
            'current_avg_latency_ms': stats.get('avg_latency_ms', 0),
            'target_latency_p95_ms': slo.get('latency_p95_ms', 5000),
            'slo_compliance': {
                'success_rate_ok': stats.get('success_rate', 1.0) >= slo.get('success_rate', 0.95),
                'latency_ok': stats.get('avg_latency_ms', 0) <= slo.get('latency_p95_ms', 5000)
            }
        }

# Global metrics collector instance
_metrics_collector = AgentMetricsCollector()

def record_agent_metrics(agent_name: str, provider: str, model: str, start_time: float,
                        status: str, input_tokens: int = 0, output_tokens: int = 0,
                        error: str = None) -> str:
    """Convenience function for recording agent metrics"""
    return _metrics_collector.record_agent_interaction(
        agent_name=agent_name,
        provider=provider,
        model=model,
        start_time=start_time,
        status=status,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        error=error
    )