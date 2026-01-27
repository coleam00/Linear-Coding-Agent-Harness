# ADR-002: Defense-in-Depth Security Model

## Status
Accepted

## Context

Autonomous coding agents execute bash commands and write files. Without security controls:
- Agents could access or modify system files
- Agents could execute dangerous commands (rm -rf /, sudo, etc.)
- Agents could escape sandbox restrictions
- Malicious prompts could exploit agent capabilities

Security must balance:
- **Agent capability**: Agents need to build real applications
- **System safety**: Prevent damage to host system
- **User trust**: Users must trust the system to run autonomously

## Decision

Implement a five-layer defense-in-depth security model:

```
Layer 1: OS-level Sandbox
    ↓
Layer 2: Filesystem Restrictions (project directory only)
    ↓
Layer 3: Bash Command Allowlist (73 commands)
    ↓
Layer 4: Sensitive Command Validation (pkill, chmod, rm, init.sh)
    ↓
Layer 5: MCP Permissions (explicit tool allowlists)
```

### Layer Details

1. **OS Sandbox**: Claude Agent SDK sandbox feature isolates execution
2. **Filesystem**: All file operations restricted to project directory
3. **Bash Allowlist**: Only 73 specific commands permitted
4. **Extra Validation**: Sensitive commands (rm, pkill, chmod) have additional checks
5. **MCP Permissions**: Only allowed MCP tools can be invoked

### Implementation

```python
# Security hook validates every bash command
def bash_security_hook(hook_input):
    command = hook_input.tool_input.get("command")
    for cmd in extract_commands(command):
        if cmd not in ALLOWED_COMMANDS:
            return {"decision": "block", "reason": f"Command not allowed: {cmd}"}
        if cmd in EXTRA_VALIDATION_COMMANDS:
            result = validate_command(cmd, args)
            if not result.allowed:
                return {"decision": "block", "reason": result.reason}
    return {}  # Allow
```

## Consequences

### Positive
- **Defense-in-Depth**: Multiple layers provide redundancy
- **Fail-Secure**: Unknown commands are blocked by default
- **Auditability**: All command validation is logged
- **Flexibility**: Allowlist can be extended for specific needs
- **Trust Model**: Users can understand exactly what's permitted

### Negative
- **Maintenance**: Allowlist must be updated for new legitimate commands
- **False Positives**: Legitimate commands may be blocked initially
- **Complexity**: Five layers add implementation complexity
- **Performance**: Every bash command goes through validation

### Neutral
- Security settings written to `.claude_settings.json` per project
- Validation runs synchronously before command execution

## Alternatives Considered

### Capability-Based Security
- **Rejected**: Too coarse-grained for bash commands
- Would need to allow all bash or none

### Container-Only Isolation
- **Rejected**: Insufficient for command-level control
- Containers can still run dangerous internal commands

### LLM-Based Security Review
- **Rejected**: Non-deterministic, could be bypassed by prompt injection
- Defense must be deterministic

### No Restrictions (Trust Agent)
- **Rejected**: Unacceptable risk for autonomous operation
- Prompt injection could lead to system damage

## Validation Rules

### pkill
- Only allowed for: node, npm, npx, vite, next
- Blocked for: python, bash, chrome, system processes

### chmod
- Only allowed: +x (execute permission)
- Blocked: numeric modes, -R, +w, +r

### rm
- Blocked paths: /, /etc, /usr, /var, /home, /Users, ~/
- Allowed: project files, node_modules

### init.sh
- Only allowed: ./init.sh or */init.sh
- Blocked: other scripts, bash init.sh

## Related Decisions
- [ADR-001: Multi-Agent Orchestration](./ADR-001-multi-agent-orchestration.md) - Architecture context
