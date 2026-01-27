# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant architectural decisions made during the development of the Linear-Coding-Agent-Harness.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](./ADR-001-multi-agent-orchestration.md) | Multi-Agent Orchestration Pattern | Accepted | 2025-01 |
| [ADR-002](./ADR-002-defense-in-depth-security.md) | Defense-in-Depth Security Model | Accepted | 2025-01 |
| [ADR-003](./ADR-003-arcade-mcp-gateway.md) | Arcade MCP Gateway Integration | Accepted | 2025-01 |
| [ADR-004](./ADR-004-context-passing.md) | Explicit Context Passing Between Agents | Accepted | 2025-01 |
| [ADR-005](./ADR-005-model-selection-strategy.md) | Per-Agent Model Selection Strategy | Accepted | 2025-01 |

## ADR Template

When creating new ADRs, use this template:

```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
[What is the issue that we're seeing that is motivating this decision or change?]

## Decision
[What is the change that we're proposing and/or doing?]

## Consequences

### Positive
- [List positive outcomes]

### Negative
- [List negative outcomes or trade-offs]

### Neutral
- [List neutral observations]

## Alternatives Considered
[What other options were considered and why were they rejected?]
```

## Decision Process

1. Create a new ADR file with the next available number
2. Fill in the template sections
3. Submit for review via PR
4. Update status when accepted
