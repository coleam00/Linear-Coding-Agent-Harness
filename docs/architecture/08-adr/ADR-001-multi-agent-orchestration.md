# ADR-001: Multi-Agent Orchestration Pattern

## Status
Accepted

## Context

The system needs to autonomously build web applications with work tracked in Linear. This requires:
- Project and issue management (Linear)
- Code implementation (complex reasoning)
- Version control (GitHub)
- Team notifications (Slack)

A single monolithic agent would:
- Require access to all tools (100+ tools)
- Need a very long system prompt covering all domains
- Be difficult to maintain and extend
- Have a large context window with mixed concerns

## Decision

Implement a hub-and-spoke multi-agent orchestration pattern:

1. **Orchestrator Agent (Hub)**: Coordinates all work, delegates to specialized agents
2. **Specialized Agents (Spokes)**: Domain-specific agents with focused tools and prompts
   - Linear Agent: Issue management
   - Coding Agent: Implementation
   - GitHub Agent: Version control
   - Slack Agent: Notifications

The orchestrator uses the Claude Agent SDK's Task tool to delegate to specialized agents.

```
                    ┌─────────────────┐
                    │  ORCHESTRATOR   │
                    │   (Hub Agent)   │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
      ┌────▼─────┐    ┌─────▼──────┐   ┌─────▼──────┐
      │  LINEAR  │    │   CODING   │   │   GITHUB   │
      │  Agent   │    │   Agent    │   │   Agent    │
      └──────────┘    └────────────┘   └────────────┘
```

## Consequences

### Positive
- **Separation of Concerns**: Each agent has focused responsibility and toolset
- **Maintainability**: Agent prompts can be modified independently
- **Cost Optimization**: Use cheaper models (Haiku) for simple agents, capable models (Sonnet) only where needed
- **Extensibility**: New agents can be added without modifying existing ones
- **Testability**: Agents can be tested in isolation

### Negative
- **Context Overhead**: Orchestrator must pass full context between agents (no shared memory)
- **Latency**: Each delegation adds round-trip time
- **Complexity**: Coordination logic in orchestrator prompt is complex
- **Debugging**: Issues can span multiple agent interactions

### Neutral
- Each iteration creates a fresh client (prevents context exhaustion)
- State is persisted in files (`.linear_project.json`, `claude-progress.txt`)

## Alternatives Considered

### Single Monolithic Agent
- **Rejected**: Too many tools, mixed concerns, difficult to maintain
- Would require 100+ tools in single agent
- System prompt would be extremely long

### Peer-to-Peer Agents
- **Rejected**: Complex coordination, unclear ownership
- Agents would need to know about each other
- No clear authority for decision making

### Queue-Based Agents
- **Rejected**: Added infrastructure complexity
- Would need message queue system
- Harder to debug real-time

## Related Decisions
- [ADR-004: Context Passing](./ADR-004-context-passing.md) - How agents share context
- [ADR-005: Model Selection](./ADR-005-model-selection-strategy.md) - Per-agent model choices
