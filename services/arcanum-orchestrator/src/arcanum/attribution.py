import os, json, datetime, pathlib, hashlib, time, re

class AttributionLogger:
    def __init__(self):
        self.chronicle_path = pathlib.Path(os.environ.get("ARCANUM_CHRONICLE_PATH", "docs/chronicle.md"))
        self.attribution_path = pathlib.Path("logs/attribution.jsonl")
        self.attribution_path.parent.mkdir(parents=True, exist_ok=True)

    def _redact_secrets(self, data: dict) -> dict:
        """Redact sensitive information from data"""
        if not isinstance(data, dict):
            return data

        redacted = {}
        for key, value in data.items():
            if any(secret_word in key.lower() for secret_word in ['key', 'token', 'password', 'secret']):
                redacted[key] = "[REDACTED]"
            elif isinstance(value, dict):
                redacted[key] = self._redact_secrets(value)
            elif isinstance(value, str) and len(value) > 20 and any(pattern in value for pattern in ['sk-', 'pk-']):
                redacted[key] = value[:8] + "[REDACTED]" + value[-4:]
            else:
                redacted[key] = value
        return redacted

    def _calculate_response_metrics(self, start_time: float, message: dict, output: dict) -> dict:
        """Calculate performance metrics for the interaction"""
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        # Estimate token counts (rough approximation)
        input_text = json.dumps(message)
        output_text = json.dumps(output)

        estimated_input_tokens = len(input_text.split())
        estimated_output_tokens = len(output_text.split())

        return {
            'latency_ms': latency_ms,
            'estimated_input_tokens': estimated_input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'total_estimated_tokens': estimated_input_tokens + estimated_output_tokens
        }

    def log_agent_interaction(self, agent_name: str, provider: str, message: dict,
                            output: dict, start_time: float, status: str = "success",
                            error: str = None) -> str:
        """Log a comprehensive agent interaction with attribution"""

        interaction_id = hashlib.sha256(
            f"{agent_name}{provider}{time.time()}".encode()
        ).hexdigest()[:12]

        timestamp = datetime.datetime.utcnow()

        # Calculate metrics
        metrics = self._calculate_response_metrics(start_time, message, output)

        # Create comprehensive attribution record
        attribution_record = {
            'interaction_id': interaction_id,
            'timestamp': timestamp.isoformat() + "Z",
            'agent': {
                'name': agent_name,
                'provider': provider,
                'model': self._extract_model_from_provider(provider)
            },
            'request': {
                'message': self._redact_secrets(message),
                'estimated_tokens': metrics['estimated_input_tokens']
            },
            'response': {
                'output': self._redact_secrets(output) if output else None,
                'estimated_tokens': metrics['estimated_output_tokens'],
                'status': status,
                'error': error
            },
            'performance': {
                'latency_ms': metrics['latency_ms'],
                'total_tokens': metrics['total_estimated_tokens']
            },
            'context': {
                'service': 'arcanum-orchestrator',
                'version': os.environ.get('ARCANUM_VERSION', '0.1.0'),
                'environment': os.environ.get('ENVIRONMENT', 'dev')
            }
        }

        # Write to structured attribution log (JSONL format for easy parsing)
        with open(self.attribution_path, 'a') as f:
            f.write(json.dumps(attribution_record) + '\n')

        # Continue writing to chronicle for backward compatibility
        self._append_chronicle_entry(attribution_record)

        return interaction_id

    def _extract_model_from_provider(self, provider: str) -> str:
        """Extract model information from provider"""
        model_mapping = {
            'claude': os.environ.get('CLAUDE_MODEL', 'claude-3-5-sonnet'),
            'gemini': os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
        }
        return model_mapping.get(provider, provider)

    def _append_chronicle_entry(self, attribution_record: dict):
        """Append to chronicle with enhanced format"""
        if not os.environ.get("ARCANUM_APPEND_JOURNAL", "false").lower() == "true":
            return

        self.chronicle_path.parent.mkdir(parents=True, exist_ok=True)

        agent = attribution_record['agent']
        performance = attribution_record['performance']

        entry = (
            "\n---\n"
            + f"title: \"AI Interaction — {agent['name']}\"\n"
            + "author: \"arcanum-orchestrator\"\n"
            + f"date: \"{attribution_record['timestamp']}\"\n"
            + f"interaction_id: \"{attribution_record['interaction_id']}\"\n"
            + "attribution:\n"
            + f"  - agent: \"{agent['name']}\"\n"
            + f"    provider: \"{agent['provider']}\"\n"
            + f"    model: \"{agent['model']}\"\n"
            + f"    latency_ms: {performance['latency_ms']}\n"
            + f"    status: \"{attribution_record['response']['status']}\"\n"
            + "---\n\n"
            + f"## Request Summary\n"
            + f"**Tokens**: ~{attribution_record['request']['estimated_tokens']}\n"
            + f"**Latency**: {performance['latency_ms']}ms\n\n"
        )

        if attribution_record['response']['status'] != 'success':
            entry += f"**Error**: {attribution_record['response']['error']}\n\n"

        entry += "## Full Details\n"
        entry += f"See attribution log: `{self.attribution_path}` (ID: {attribution_record['interaction_id']})\n\n---\n"

        if self.chronicle_path.exists():
            text = self.chronicle_path.read_text(encoding="utf-8")
            if text.startswith("# "):
                lines = text.splitlines()
                new_text = "\n".join([lines[0]]) + "\n" + entry + "\n".join(lines[1:])
            else:
                new_text = entry + text
        else:
            new_text = "# Chronicle (Ops Journal)\n\n" + entry

        self.chronicle_path.write_text(new_text, encoding="utf-8")

    def get_interaction_stats(self, hours_back: int = 24) -> dict:
        """Get interaction statistics for monitoring"""
        if not self.attribution_path.exists():
            return {'total_interactions': 0, 'avg_latency_ms': 0, 'success_rate': 1.0}

        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_back)
        cutoff_str = cutoff_time.isoformat() + "Z"

        interactions = []
        with open(self.attribution_path, 'r') as f:
            for line in f:
                record = json.loads(line.strip())
                if record['timestamp'] >= cutoff_str:
                    interactions.append(record)

        if not interactions:
            return {'total_interactions': 0, 'avg_latency_ms': 0, 'success_rate': 1.0}

        total_latency = sum(r['performance']['latency_ms'] for r in interactions)
        success_count = sum(1 for r in interactions if r['response']['status'] == 'success')

        return {
            'total_interactions': len(interactions),
            'avg_latency_ms': total_latency // len(interactions),
            'success_rate': success_count / len(interactions),
            'agents_used': list(set(r['agent']['name'] for r in interactions))
        }

# Maintain backward compatibility
_attribution_logger = AttributionLogger()

def append_chronicle_entry(action: str, provider: str, message: dict, output: dict):
    """Legacy function for backward compatibility"""
    start_time = time.time() - 1.0  # Approximate start time
    _attribution_logger.log_agent_interaction(
        agent_name=f"legacy-{provider}",
        provider=provider,
        message=message,
        output=output,
        start_time=start_time
    )
