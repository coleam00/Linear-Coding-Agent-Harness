# ADR-003: Arcade MCP Gateway Integration

## Status
Accepted

## Context

The system needs to integrate with three external services:
- **Linear**: Project and issue management (required)
- **GitHub**: Version control and PRs (optional)
- **Slack**: Team notifications (optional)

Integration options:
1. Direct API integration via HTTP
2. Individual MCP servers per service
3. Unified gateway via Arcade MCP

Each service has different authentication requirements:
- Linear: OAuth 2.0
- GitHub: OAuth 2.0 / Personal Access Token
- Slack: OAuth 2.0 (bot token)

## Decision

Use Arcade MCP Gateway as a unified integration layer:

```
┌─────────────────────────────────────────┐
│           Agent Harness                 │
│         (Claude SDK Client)             │
└─────────────────┬───────────────────────┘
                  │ MCP (HTTP)
                  ▼
┌─────────────────────────────────────────┐
│         Arcade MCP Gateway              │
│  https://api.arcade.dev/mcp/{slug}      │
└───────┬─────────────┬───────────────┬───┘
        │             │               │
        ▼             ▼               ▼
   ┌─────────┐   ┌─────────┐   ┌──────────┐
   │ Linear  │   │ GitHub  │   │  Slack   │
   │   API   │   │   API   │   │   API    │
   └─────────┘   └─────────┘   └──────────┘
```

### Configuration

```python
arcade_config = {
    "type": "http",
    "url": f"https://api.arcade.dev/mcp/{gateway_slug}",
    "headers": {
        "Authorization": f"Bearer {api_key}",
        "Arcade-User-ID": user_id
    }
}
```

## Consequences

### Positive
- **Unified Authentication**: Single API key for all services
- **Managed OAuth**: Arcade handles OAuth flows for each service
- **Tool Discovery**: Gateway advertises available tools
- **User Tracking**: Arcade-User-ID enables per-user tracking
- **Reduced Complexity**: No need to manage multiple MCP servers
- **Dashboard**: Arcade provides visibility into tool usage

### Negative
- **Vendor Dependency**: Reliance on Arcade availability
- **Cost**: Arcade API usage has associated costs
- **Latency**: Additional hop through gateway
- **Tool Subset**: Only tools exposed by Arcade are available

### Neutral
- Authorization flow handled by `authorize_arcade.py`
- Gateway slug configured per user/organization
- Tools can be selectively added to gateway

## Alternatives Considered

### Direct API Integration
- **Rejected**: Would require implementing each API client
- OAuth handling would be complex
- More code to maintain

### Separate MCP Servers
- **Rejected**: Would need to run and configure multiple servers
- Each server would need separate authentication
- Complex configuration

### Native SDK Integrations
- **Rejected**: No unified interface
- Would need to switch between different client libraries
- Inconsistent error handling

## Tool Counts

| Service | Tools | Required |
|---------|-------|----------|
| Linear | 39 | Yes |
| GitHub | 46 | No |
| Slack | 8 | No |
| **Total** | **93** | - |

## Authorization Flow

```bash
# Run once per service
python authorize_arcade.py linear   # Required
python authorize_arcade.py github   # Optional
python authorize_arcade.py slack    # Optional
```

The script:
1. Attempts to call a write tool (e.g., `Linear_CreateProject`)
2. Arcade returns authorization URL
3. User completes OAuth in browser
4. Script verifies with `WhoAmI` call

## Related Decisions
- [ADR-001: Multi-Agent Orchestration](./ADR-001-multi-agent-orchestration.md) - Agent structure
- [ADR-002: Defense-in-Depth Security](./ADR-002-defense-in-depth-security.md) - Tool permissions
