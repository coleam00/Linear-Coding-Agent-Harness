# Architecture Documentation

This directory contains comprehensive architecture documentation for the Linear-Coding-Agent-Harness multi-agent orchestrator system.

## Documentation Structure

| Document | Description |
|----------|-------------|
| [01-system-context.md](./01-system-context.md) | High-level system context, stakeholders, and external integrations |
| [02-container-architecture.md](./02-container-architecture.md) | Container/service architecture and deployment view |
| [03-component-architecture.md](./03-component-architecture.md) | Internal module structure and relationships |
| [04-agent-architecture.md](./04-agent-architecture.md) | Multi-agent orchestration patterns and agent specifications |
| [05-security-architecture.md](./05-security-architecture.md) | Defense-in-depth security model and validation |
| [06-data-architecture.md](./06-data-architecture.md) | Data models, state management, and flow patterns |
| [07-mcp-integration.md](./07-mcp-integration.md) | MCP server configurations and tool specifications |
| [08-adr/](./08-adr/) | Architecture Decision Records |

## Quick Links

- **System Overview**: Start with [System Context](./01-system-context.md)
- **How Agents Work**: See [Agent Architecture](./04-agent-architecture.md)
- **Security Model**: See [Security Architecture](./05-security-architecture.md)
- **Design Decisions**: Browse [ADRs](./08-adr/)

## Diagram Conventions

All diagrams use Mermaid syntax for version-controlled, text-based diagrams. Render them using:
- GitHub (native Mermaid support)
- VS Code with Mermaid extension
- [mermaid.live](https://mermaid.live)

## Architecture Principles

1. **Multi-Agent Delegation**: Orchestrator coordinates specialized agents without shared memory
2. **Defense-in-Depth Security**: Multiple layers from OS sandbox to command validation
3. **Context Passing**: Full context passed between agents (never assume shared state)
4. **Verification Gate**: Test completed features before starting new work
5. **Evidence-Based Completion**: Screenshot proof required before marking issues Done
