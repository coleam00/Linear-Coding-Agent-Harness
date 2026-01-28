# Windows Compatibility Analysis Report

## Summary

The multi-agent orchestrator harness works on Mac but fails on Windows due to three interconnected issues:
1. Custom agent types not being recognized by the Task tool
2. Unix-only command allowlist in security.py
3. Sandbox isolation not available on Windows

---

## Problem 1: Agent Type Registration Not Working (Primary Issue)

### Error Observed
```
[Error] Agent type 'linear' not found. Available agents: Bash, general-purpose, statusline-setup, Explore, Plan
```

### What's Happening

- The orchestrator prompt (`prompts/orchestrator_prompt.md` lines 21-28) instructs Claude to use the `Task` tool with `subagent_type='linear'`
- Custom agents ARE defined in `agents/definitions.py` and passed to the SDK via `agents=AGENT_DEFINITIONS` in `client.py:213`
- However, the Claude Agent SDK's `Task` tool only lists **built-in agent types**

### The Disconnect

The `ClaudeAgentOptions.agents` parameter is meant to register custom agent definitions, but these aren't being exposed through the `Task` tool's `subagent_type` parameter on Windows. Possible causes:

1. **SDK version difference** between Mac and Windows installations
2. **Different Claude Code backend behavior** based on platform
3. **Agent registration timing issue** - agents not available when Task tool introspects available types

### Why Mac Might Work

- Different SDK version installed
- Different Claude Code binary with different behavior
- Environment setup that enables custom agents

### Relevant Code Locations

- `client.py:213` - Where agents are passed to SDK:
  ```python
  ClaudeAgentOptions(
      ...
      agents=AGENT_DEFINITIONS,
      ...
  )
  ```

- `agents/definitions.py:100-136` - Agent definitions:
  ```python
  def create_agent_definitions() -> dict[str, AgentDefinition]:
      return {
          "linear": AgentDefinition(...),
          "github": AgentDefinition(...),
          "slack": AgentDefinition(...),
          "coding": AgentDefinition(...),
      }
  ```

- `prompts/orchestrator_prompt.md:21-28` - Prompt telling Claude to use custom agents:
  ```markdown
  | Agent | Model | Use For |
  |-------|-------|---------|
  | `linear` | haiku | Check/update Linear issues... |
  ```

---

## Problem 2: Unix-Only Command Allowlist

### Error Observed
```
[Error] Command 'dir' is not in the allowed commands list
```

### Analysis

`security.py:29-73` only contains Unix commands:

```python
ALLOWED_COMMANDS: set[str] = {
    # File inspection
    "ls",      # Windows equivalent: dir
    "cat",     # Windows equivalent: type
    "head",    # No direct Windows equivalent
    "tail",    # No direct Windows equivalent
    "wc",      # No direct Windows equivalent
    "grep",    # Windows equivalent: findstr
    "find",    # Windows equivalent: where (for executables)
    # Directory navigation
    "pwd",     # Windows equivalent: cd (with no args)
    # Environment inspection
    "which",   # Windows equivalent: where
    "env",     # Windows equivalent: set
    ...
}
```

### Missing Windows Commands

The following Windows commands should be added:
- `dir` - directory listing (ls equivalent)
- `type` - file content display (cat equivalent)
- `where` - find executables (which equivalent)
- `set` - environment variables (env equivalent)
- `findstr` - text search (grep equivalent)
- `copy` - file copy (cp equivalent)
- `move` - file move (mv equivalent)
- `del` - file delete (rm equivalent)
- `md` / `mkdir` - create directory (mkdir already present)
- `rd` / `rmdir` - remove directory
- `cls` - clear screen

---

## Problem 3: Sandbox Isolation Not Available on Windows

### Configuration

`client.py:85-112` enables sandboxing:

```python
def create_security_settings() -> SecuritySettings:
    return SecuritySettings(
        sandbox=SandboxConfig(enabled=True, autoAllowBashIfSandboxed=True),
        permissions=PermissionsConfig(...)
    )
```

### Analysis

The Claude Agent SDK uses **bwrap (bubblewrap)** or similar containerization on Linux/Mac for bash command isolation. Windows doesn't have native support for this mechanism.

Windows alternatives would require:
- Windows Sandbox (requires Hyper-V, Windows 10 Pro+)
- WSL-based isolation
- Container-based isolation (Docker)

If the SDK silently fails sandbox initialization on Windows, it might affect:
- How agents are registered
- How bash commands are executed
- Overall security model behavior

---

## Problem 4: Prompting Architecture Assumption

### The Issue

The orchestrator prompt assumes the Task tool can spawn custom agents defined via `AgentDefinition`:

```markdown
Use the Task tool to delegate to these specialized agents:

| Agent | Model | Use For |
|-------|-------|---------|
| `linear` | haiku | Check/update Linear issues, maintain claude-progress.txt |
| `coding` | sonnet | Write code, test with Puppeteer, provide screenshot evidence |
| `github` | haiku | Git commits, branches, pull requests |
| `slack` | haiku | Send progress notifications to users |
```

This instructs Claude to call:
```json
{"subagent_type": "linear", "prompt": "..."}
```

But the SDK's Task tool implementation may not support custom `subagent_type` values from `AgentDefinition` - it appears to only support hardcoded built-in types.

---

## Recommended Investigation Steps

### 1. Check SDK Version Parity

Run on both Mac and Windows:
```bash
pip show claude-agent-sdk
```

Compare versions to identify any differences.

### 2. Check SDK Documentation

Verify if the `agents` parameter in `ClaudeAgentOptions` is intended for:
- Task tool `subagent_type` values, OR
- A different mechanism (like inline agent calls)

### 3. Test Without Sandbox on Windows

Modify `client.py` to disable sandbox temporarily:

```python
def create_security_settings() -> SecuritySettings:
    return SecuritySettings(
        sandbox=SandboxConfig(enabled=False, autoAllowBashIfSandboxed=False),
        permissions=PermissionsConfig(...)
    )
```

### 4. Add Windows Commands to Allowlist

Update `security.py`:

```python
ALLOWED_COMMANDS: set[str] = {
    # Existing Unix commands...

    # Windows equivalents
    "dir",       # ls equivalent
    "type",      # cat equivalent
    "where",     # which equivalent
    "set",       # env equivalent (be careful with validation)
    "findstr",   # grep equivalent
    "copy",      # cp equivalent
    "move",      # mv equivalent
    "del",       # rm equivalent (needs validation like rm)
    "md",        # mkdir equivalent
    "rd",        # rmdir equivalent
}
```

### 5. Cross-Platform Command Handling

Consider using platform detection:

```python
import platform

if platform.system() == "Windows":
    ALLOWED_COMMANDS.update({"dir", "type", "where", "set", "findstr"})
```

---

## Potential Fixes

### Option A: Fix Agent Registration (Preferred)

Investigate why custom agents aren't being recognized and fix the SDK integration. This maintains the intended architecture.

### Option B: Use Built-in Agents

Modify the orchestrator prompt to use only built-in agent types (`general-purpose`) and embed the specialized logic in the prompts rather than separate agent definitions.

### Option C: Platform-Specific Configuration

Create Windows-specific configurations:
- Windows command allowlist
- Disabled sandbox mode
- Alternative agent invocation mechanism

---

## Files to Modify for Windows Compatibility

| File | Changes Needed |
|------|----------------|
| `security.py` | Add Windows commands to ALLOWED_COMMANDS |
| `client.py` | Conditionally disable sandbox on Windows |
| `prompts/orchestrator_prompt.md` | Possibly modify agent delegation approach |
| `agents/definitions.py` | Investigate agent registration mechanism |

---

## Conclusion

The primary issue is that custom agent definitions passed via `agents=AGENT_DEFINITIONS` are not being recognized by the Task tool on Windows. This is likely either:

1. A platform-specific SDK behavior difference
2. A version mismatch between Mac and Windows SDK installations
3. A fundamental misunderstanding of how custom agents integrate with the Task tool

The secondary issues (command allowlist, sandbox) are straightforward to fix but won't resolve the main problem of agent delegation.

**Next Steps:**
1. Verify SDK versions on both platforms
2. Check SDK documentation for custom agent usage
3. Consider whether the architecture needs adjustment for Windows support
