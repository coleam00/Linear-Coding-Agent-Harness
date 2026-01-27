# ADR-005: Per-Agent Model Selection Strategy

## Status
Accepted

## Context

The Claude model family includes models with different capability/cost trade-offs:

| Model | Capability | Cost | Latency |
|-------|------------|------|---------|
| Opus | Highest | Highest | Slower |
| Sonnet | High | Medium | Medium |
| Haiku | Good | Lowest | Fastest |

Different agents have different complexity requirements:
- **Orchestrator**: Coordination logic, delegation decisions
- **Linear Agent**: API calls, text manipulation
- **Coding Agent**: Complex code implementation, debugging
- **GitHub Agent**: Git commands, PR descriptions
- **Slack Agent**: Simple notifications

Using Opus for all agents would be:
- Expensive (especially for 50+ issue projects)
- Slower than necessary
- Overkill for simple tasks

## Decision

Implement per-agent model selection with sensible defaults:

| Agent | Default Model | Rationale |
|-------|---------------|-----------|
| Orchestrator | Haiku | Simple coordination, cost-efficient |
| Linear Agent | Haiku | API calls, text manipulation |
| Coding Agent | **Sonnet** | Complex implementation needs capability |
| GitHub Agent | Haiku | Git commands, structured output |
| Slack Agent | Haiku | Simple notifications |

### Override via Environment

```bash
ORCHESTRATOR_MODEL=opus     # More capable orchestration
LINEAR_AGENT_MODEL=sonnet   # More complex issue handling
CODING_AGENT_MODEL=opus     # Maximum implementation capability
GITHUB_AGENT_MODEL=sonnet   # Complex PR descriptions
SLACK_AGENT_MODEL=sonnet    # Richer notifications
```

### CLI Override

```bash
uv run python autonomous_agent_demo.py --model opus  # Orchestrator only
```

## Consequences

### Positive
- **Cost Optimization**: ~80% of agents use Haiku
- **Performance**: Haiku is faster for simple tasks
- **Flexibility**: Can upgrade specific agents as needed
- **Capability Match**: Sonnet for coding where it matters most

### Negative
- **Configuration Complexity**: Multiple model settings to manage
- **Debugging**: Different models may behave differently
- **Testing**: Need to test with each model option

### Neutral
- Environment variables override defaults
- CLI --model only affects orchestrator
- "inherit" option available for sub-agents

## Cost Analysis

Assuming 50 issues, ~3 delegations per issue:

### All-Opus Scenario
```
Orchestrator: 150 calls × Opus cost = $$$
Linear: 100 calls × Opus cost = $$$
Coding: 50 calls × Opus cost = $$$
GitHub: 50 calls × Opus cost = $$$
Total: $$$$
```

### Optimized Scenario (Default)
```
Orchestrator: 150 calls × Haiku cost = $
Linear: 100 calls × Haiku cost = $
Coding: 50 calls × Sonnet cost = $$
GitHub: 50 calls × Haiku cost = $
Total: $$ (significant savings)
```

## Implementation

```python
# agents/definitions.py

ModelOption = Literal["haiku", "sonnet", "opus", "inherit"]

DEFAULT_MODELS = {
    "linear": "haiku",
    "coding": "sonnet",
    "github": "haiku",
    "slack": "haiku"
}

def _get_model(agent_name: str, default: ModelOption) -> ModelOption:
    env_var = f"{agent_name.upper()}_AGENT_MODEL"
    return os.getenv(env_var, default)

# Usage in agent definitions
AgentDefinition(
    name="coding",
    model=_get_model("coding", "sonnet"),  # Reads CODING_AGENT_MODEL or defaults to sonnet
    ...
)
```

## Alternatives Considered

### Single Model for All
- **Rejected**: Wasteful for simple agents
- Unnecessarily slow
- Higher cost without benefit

### Dynamic Model Selection
- **Rejected**: Non-deterministic behavior
- Hard to debug
- Complex implementation

### User-Selected Per-Call
- **Rejected**: Too much user overhead
- Would interrupt autonomous operation

### Haiku-Only
- **Rejected**: Coding agent needs more capability
- Implementation quality would suffer

## Upgrade Path

For complex projects or higher quality needs:

```bash
# High-quality mode
export ORCHESTRATOR_MODEL=sonnet
export CODING_AGENT_MODEL=opus
export GITHUB_AGENT_MODEL=sonnet

# Run
uv run python autonomous_agent_demo.py --project-dir complex-app
```

## Related Decisions
- [ADR-001: Multi-Agent Orchestration](./ADR-001-multi-agent-orchestration.md) - Agent structure
- [ADR-004: Context Passing](./ADR-004-context-passing.md) - Why orchestrator is simple
