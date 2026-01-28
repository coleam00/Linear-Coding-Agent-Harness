# Plan: Windows Compatibility Fix for Multi-Agent Orchestrator

## Summary

This plan addresses three issues preventing the multi-agent orchestrator from working on Windows:

1. **Custom agent types not recognized by Task tool** - The Claude Agent SDK's `agents` parameter for `ClaudeAgentOptions` registers custom agents, BUT these are NOT exposed via the Task tool's `subagent_type` parameter. This is a **known SDK limitation** (GitHub issue #18212), not a Windows-specific bug. The current workaround is to use filesystem-based agents in `.claude/agents/` directory OR embed agent instructions directly in the prompt when using `general-purpose` subagent type.

2. **Unix-only command allowlist** - The security hook in `security.py` only allows Unix commands (`ls`, `cat`, etc.) but Windows uses different commands (`dir`, `type`, etc.).

3. **Sandbox unavailable on native Windows** - The SDK sandbox uses bubblewrap (Linux) or Seatbelt (macOS). Native Windows is not supported; only WSL2 works. The sandbox must be disabled for native Windows.

**Approach**: Create filesystem-based agent definitions in `.claude/agents/`, add Windows commands to the allowlist with platform detection, and conditionally disable sandbox on Windows.

---

## External Research

### Documentation
- [Claude Agent SDK Subagents](https://platform.claude.com/docs/en/agent-sdk/subagents) - Official subagent documentation
  - Key finding: Custom agents via `agents` parameter work, BUT the Task tool's `subagent_type` only accepts built-in types
  - Filesystem-based agents in `.claude/agents/` directory ARE recognized by Claude Code
- [Claude Code Sandboxing](https://code.claude.com/docs/en/sandboxing) - Sandbox documentation
  - Native Windows NOT supported, only WSL2
  - Sandbox uses bubblewrap (Linux) and Seatbelt (macOS)

### Gotchas & Best Practices
- **GitHub Issue #18212**: Confirms custom agents via `agents` parameter are NOT available to Task tool's `subagent_type`
- **Windows subagent prompt limit**: On Windows, subagents with very long prompts may fail due to command line length limits (8191 chars)
- **Filesystem-based agents take precedence**: Programmatically defined agents take precedence over filesystem-based agents with the same name

### SDK Version
- Current version: `claude-agent-sdk==0.1.23`
- Latest features: Custom agents work via filesystem `.claude/agents/*.md`

---

## Patterns to Mirror

### Existing Filesystem Agent Pattern (`.claude/agents/py-sdk-agent.md`)

```markdown
---
name: agent-sdk-verifier-py
description: Use this agent to verify that a Python Agent SDK application...
model: sonnet
---

You are a Python Agent SDK application verifier...
```

This is the exact format we'll use for our custom agents.

### Existing Security Hook Pattern (`security.py:29-73`)

```python
ALLOWED_COMMANDS: set[str] = {
    # File inspection
    "ls",
    "cat",
    "head",
    ...
}
```

We'll extend this set with Windows equivalents and add platform detection.

### Existing Client Configuration (`client.py:85-112`)

```python
def create_security_settings() -> SecuritySettings:
    return SecuritySettings(
        sandbox=SandboxConfig(enabled=True, autoAllowBashIfSandboxed=True),
        ...
    )
```

We'll add platform detection to conditionally disable sandbox on Windows.

---

## Files to Change

| File | Action | Justification |
|------|--------|---------------|
| `.claude/agents/linear.md` | CREATE | Filesystem-based agent for Linear operations |
| `.claude/agents/coding.md` | CREATE | Filesystem-based agent for coding operations |
| `.claude/agents/github.md` | CREATE | Filesystem-based agent for GitHub operations |
| `.claude/agents/slack.md` | CREATE | Filesystem-based agent for Slack notifications |
| `security.py` | UPDATE | Add Windows commands and platform detection |
| `client.py` | UPDATE | Conditionally disable sandbox on Windows |
| `prompts/orchestrator_prompt.md` | UPDATE | Update agent delegation instructions for filesystem agents |

---

## NOT Building

- Native Windows sandbox support (not available in SDK)
- Cross-compilation or WSL detection
- Automatic platform-specific prompt shortening
- Migration of all agent definitions to filesystem (keep both for backwards compatibility)

---

## Tasks

### Task 1: Create filesystem-based Linear agent

**Why**: The Task tool recognizes agents in `.claude/agents/` directory. This provides a workaround for the SDK limitation where programmatic agents aren't exposed via `subagent_type`.

**Mirror**: `.claude/agents/py-sdk-agent.md` (existing filesystem agent format)

**Do**:

Create `.claude/agents/linear.md` with YAML frontmatter:

```markdown
---
name: linear
description: Manages Linear issues, project status, and session handoff. Use for any Linear operations.
model: haiku
allowed-tools:
  - mcp__arcade__Linear_WhoAmI
  - mcp__arcade__Linear_ListTeams
  - mcp__arcade__Linear_GetTeam
  - mcp__arcade__Linear_ListIssues
  - mcp__arcade__Linear_GetIssue
  - mcp__arcade__Linear_CreateIssue
  - mcp__arcade__Linear_UpdateIssue
  - mcp__arcade__Linear_TransitionIssueState
  - mcp__arcade__Linear_AddComment
  - mcp__arcade__Linear_ArchiveIssue
  - mcp__arcade__Linear_ListProjects
  - mcp__arcade__Linear_GetProject
  - mcp__arcade__Linear_CreateProject
  - mcp__arcade__Linear_UpdateProject
  - mcp__arcade__Linear_CreateProjectUpdate
  - mcp__arcade__Linear_ListWorkflowStates
  - mcp__arcade__Linear_ListLabels
  - Read
  - Write
  - Edit
  - Glob
---

[Content from prompts/linear_agent_prompt.md]
```

**Don't**:
- Don't remove the programmatic agent definition in `agents/definitions.py` (keep for backwards compatibility)
- Don't exceed 8191 characters total (Windows command line limit)

**Verify**: Check file exists and has correct frontmatter format

---

### Task 2: Create filesystem-based Coding agent

**Why**: Same reason as Task 1 - filesystem agents are recognized by Task tool.

**Mirror**: `.claude/agents/py-sdk-agent.md`

**Do**:

Create `.claude/agents/coding.md`:

```markdown
---
name: coding
description: Writes and tests code. Use when implementing features or fixing bugs.
model: sonnet
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - mcp__puppeteer__puppeteer_navigate
  - mcp__puppeteer__puppeteer_screenshot
  - mcp__puppeteer__puppeteer_click
  - mcp__puppeteer__puppeteer_fill
  - mcp__puppeteer__puppeteer_select
  - mcp__puppeteer__puppeteer_hover
  - mcp__puppeteer__puppeteer_evaluate
---

[Content from prompts/coding_agent_prompt.md]
```

**Don't**:
- Don't include Task tool (subagents cannot spawn subagents)

**Verify**: Check file exists and has correct frontmatter format

---

### Task 3: Create filesystem-based GitHub agent

**Why**: Same reason as Task 1.

**Mirror**: `.claude/agents/py-sdk-agent.md`

**Do**:

Create `.claude/agents/github.md`:

```markdown
---
name: github
description: Handles Git commits, branches, and GitHub PRs. Use for version control operations.
model: haiku
allowed-tools:
  - mcp__arcade__Github_GetRepository
  - mcp__arcade__Github_ListRepositoryBranches
  - mcp__arcade__Github_CreateBranch
  - mcp__arcade__Github_CreatePullRequest
  - mcp__arcade__Github_ListPullRequests
  - mcp__arcade__Github_GetPullRequest
  - mcp__arcade__Github_MergePullRequest
  - mcp__arcade__Github_ListCommits
  - Read
  - Write
  - Edit
  - Glob
  - Bash
---

[Content from prompts/github_agent_prompt.md]
```

**Verify**: Check file exists and has correct frontmatter format

---

### Task 4: Create filesystem-based Slack agent

**Why**: Same reason as Task 1.

**Mirror**: `.claude/agents/py-sdk-agent.md`

**Do**:

Create `.claude/agents/slack.md`:

```markdown
---
name: slack
description: Sends Slack notifications to keep users informed. Use for progress updates.
model: haiku
allowed-tools:
  - mcp__arcade__Slack_ListConversations
  - mcp__arcade__Slack_SendMessage
  - mcp__arcade__Slack_SendDm
  - Read
  - Write
  - Edit
  - Glob
---

[Content from prompts/slack_agent_prompt.md]
```

**Verify**: Check file exists and has correct frontmatter format

---

### Task 5: Add Windows commands to security allowlist

**Why**: Windows uses different command names than Unix. Without these, all bash commands fail on Windows.

**Mirror**: `security.py:29-73` (existing ALLOWED_COMMANDS set)

**Do**:

1. Add platform detection at top of `security.py`:

```python
import platform

IS_WINDOWS = platform.system() == "Windows"
```

2. Create Windows command equivalents set:

```python
# Windows-specific commands (equivalents to Unix commands)
WINDOWS_COMMANDS: set[str] = {
    # File inspection (equivalents to ls, cat, head, tail)
    "dir",          # ls equivalent
    "type",         # cat equivalent
    "more",         # head/less equivalent
    # File operations
    "copy",         # cp equivalent
    "move",         # mv equivalent
    "del",          # rm equivalent (needs validation like rm)
    "md",           # mkdir equivalent (mkdir also works)
    "rd",           # rmdir equivalent
    "ren",          # rename equivalent
    "xcopy",        # recursive copy
    "robocopy",     # robust copy
    # Directory navigation
    "cd",           # Same as Unix but also shows current dir
    "chdir",        # Alternative to cd
    # Text output
    "echo",         # Same as Unix (already in list)
    # Environment inspection
    "where",        # which equivalent
    "set",          # env equivalent (shows env vars)
    "ver",          # Version info
    "systeminfo",   # System information
    # Process management
    "tasklist",     # ps equivalent
    "taskkill",     # pkill equivalent (needs validation)
    # Network
    "curl",         # Same as Unix (if installed)
    # PowerShell (if allowed)
    "powershell",   # For complex operations
    "pwsh",         # PowerShell Core
}
```

3. Merge into ALLOWED_COMMANDS if on Windows:

```python
# Merge Windows commands if on Windows platform
if IS_WINDOWS:
    ALLOWED_COMMANDS = ALLOWED_COMMANDS | WINDOWS_COMMANDS
```

4. Add validation for `taskkill` (similar to `pkill`):

```python
def validate_taskkill_command(command_string: str) -> ValidationResult:
    """
    Validate taskkill commands - only allow killing dev-related processes.
    Similar to validate_pkill_command but for Windows.
    """
    allowed_process_names: set[str] = {
        "node.exe",
        "npm.exe",
        "npx.exe",
        "python.exe",
        "python3.exe",
    }

    try:
        tokens: list[str] = shlex.split(command_string)
    except ValueError:
        return ValidationResult(allowed=False, reason="Could not parse taskkill command")

    # Check for /IM (image name) flag
    for i, token in enumerate(tokens):
        if token.upper() == "/IM" and i + 1 < len(tokens):
            process_name = tokens[i + 1].lower()
            if process_name in {p.lower() for p in allowed_process_names}:
                return ValidationResult(allowed=True)
            return ValidationResult(
                allowed=False,
                reason=f"taskkill only allowed for dev processes: {allowed_process_names}"
            )

    return ValidationResult(allowed=False, reason="taskkill requires /IM flag with process name")
```

5. Add `del` validation (similar to `rm`):

```python
def validate_del_command(command_string: str) -> ValidationResult:
    """
    Validate del commands - prevent dangerous deletions on Windows.
    Similar to validate_rm_command.
    """
    dangerous_paths: set[str] = {
        "C:\\",
        "C:\\Windows",
        "C:\\Windows\\System32",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Users",
    }

    try:
        tokens: list[str] = shlex.split(command_string)
    except ValueError:
        return ValidationResult(allowed=False, reason="Could not parse del command")

    if not tokens or tokens[0].lower() != "del":
        return ValidationResult(allowed=False, reason="Not a del command")

    # Check paths
    for token in tokens[1:]:
        if token.startswith("/"):
            continue  # Skip flags like /S, /Q

        # Normalize path
        normalized = os.path.abspath(token) if not os.path.isabs(token) else token

        for dangerous in dangerous_paths:
            if normalized.upper().startswith(dangerous.upper()):
                depth = normalized.count("\\") - dangerous.count("\\")
                if depth <= 1:
                    return ValidationResult(
                        allowed=False,
                        reason=f"del too close to system directory '{dangerous}' is not allowed"
                    )

    return ValidationResult(allowed=True)
```

6. Update `COMMANDS_NEEDING_EXTRA_VALIDATION` for Windows:

```python
COMMANDS_NEEDING_EXTRA_VALIDATION: set[str] = {"pkill", "chmod", "init.sh", "rm"}

if IS_WINDOWS:
    COMMANDS_NEEDING_EXTRA_VALIDATION = COMMANDS_NEEDING_EXTRA_VALIDATION | {"taskkill", "del"}
```

7. Update `bash_security_hook` to call new validators:

```python
elif cmd == "taskkill":
    result = validate_taskkill_command(cmd_segment)
    if not result.allowed:
        return SyncHookJSONOutput(decision="block", reason=result.reason)
elif cmd == "del":
    result = validate_del_command(cmd_segment)
    if not result.allowed:
        return SyncHookJSONOutput(decision="block", reason=result.reason)
```

**Don't**:
- Don't allow `format` command
- Don't allow unrestricted PowerShell execution
- Don't bypass validation for dangerous commands

**Verify**:
```bash
python -c "from security import ALLOWED_COMMANDS, IS_WINDOWS; print(f'Windows: {IS_WINDOWS}, Commands: {len(ALLOWED_COMMANDS)}')"
```

---

### Task 6: Conditionally disable sandbox on Windows

**Why**: The Claude Agent SDK sandbox uses bubblewrap (Linux) and Seatbelt (macOS). Native Windows is not supported. Attempting to use sandbox on Windows will fail.

**Mirror**: `client.py:85-112` (existing security settings)

**Do**:

1. Add platform detection at top of `client.py`:

```python
import platform

IS_WINDOWS = platform.system() == "Windows"
```

2. Modify `create_security_settings()`:

```python
def create_security_settings() -> SecuritySettings:
    """
    Create the security settings structure.

    Note: Sandbox is disabled on Windows as it requires bubblewrap (Linux)
    or Seatbelt (macOS). On Windows, we rely on the permission system
    and security hooks for protection.

    Returns:
        SecuritySettings with sandbox and permissions configured
    """
    # Sandbox not available on native Windows
    # See: https://code.claude.com/docs/en/sandboxing
    sandbox_enabled = not IS_WINDOWS

    return SecuritySettings(
        sandbox=SandboxConfig(
            enabled=sandbox_enabled,
            autoAllowBashIfSandboxed=sandbox_enabled
        ),
        permissions=PermissionsConfig(
            defaultMode="acceptEdits",
            allow=[
                # ... existing permissions ...
            ],
        ),
    )
```

3. Update the print statement in `create_client()`:

```python
if IS_WINDOWS:
    print("   - Sandbox disabled (not available on native Windows)")
    print("   - Security relies on permission system and bash command allowlist")
else:
    print("   - Sandbox enabled (OS-level bash isolation)")
```

**Don't**:
- Don't disable permission system on Windows
- Don't disable security hooks on Windows

**Verify**:
```bash
python -c "from client import create_security_settings, IS_WINDOWS; s = create_security_settings(); print(f'Windows: {IS_WINDOWS}, Sandbox enabled: {s[\"sandbox\"][\"enabled\"]}')"
```

---

### Task 7: Update orchestrator prompt for filesystem agents

**Why**: The orchestrator prompt needs to be updated to reflect that agents are now filesystem-based and should use the correct subagent_type names.

**Mirror**: `prompts/orchestrator_prompt.md` (existing prompt)

**Do**:

Update the "Available Agents" section in `prompts/orchestrator_prompt.md`:

Change from:
```markdown
### Available Agents

Use the Task tool to delegate to these specialized agents:

| Agent | Model | Use For |
|-------|-------|---------|
| `linear` | haiku | Check/update Linear issues, maintain claude-progress.txt |
| `coding` | sonnet | Write code, test with Puppeteer, provide screenshot evidence |
| `github` | haiku | Git commits, branches, pull requests |
| `slack` | haiku | Send progress notifications to users |
```

To:
```markdown
### Available Agents

Use the Task tool to delegate to these specialized agents.

**Important**: These agents are defined in `.claude/agents/` and are available as custom subagent types:

| Agent | Model | Use For |
|-------|-------|---------|
| `linear` | haiku | Check/update Linear issues, maintain claude-progress.txt |
| `coding` | sonnet | Write code, test with Puppeteer, provide screenshot evidence |
| `github` | haiku | Git commits, branches, pull requests |
| `slack` | haiku | Send progress notifications to users |

**Delegation example**:
```
Task(
  subagent_type: "linear",
  description: "Update issue status",
  prompt: "Mark issue ABC-123 as Done with these screenshots: [paths]"
)
```

If a custom agent type is not recognized, fall back to `general-purpose` and include the agent's specific instructions in the prompt.
```

**Don't**:
- Don't remove existing delegation examples
- Don't change the agent roles or responsibilities

**Verify**: Read the updated file and check the formatting

---

## Validation Strategy

### Automated Checks

- [ ] `python -m py_compile security.py` - Security module compiles
- [ ] `python -m py_compile client.py` - Client module compiles
- [ ] `python -c "from security import ALLOWED_COMMANDS; print(len(ALLOWED_COMMANDS))"` - Commands load
- [ ] `python -c "from client import create_security_settings; print(create_security_settings())"` - Settings create

### New Tests to Write

| Test File | Test Case | What It Validates |
|-----------|-----------|-------------------|
| `test_security.py` | `test_windows_commands_included` | Windows commands in allowlist when on Windows |
| `test_security.py` | `test_taskkill_validation` | Dangerous taskkill commands blocked |
| `test_security.py` | `test_del_validation` | Dangerous del commands blocked |
| `test_client.py` | `test_sandbox_disabled_on_windows` | Sandbox config correct per platform |

### Manual/E2E Validation

```bash
# Test on Windows
python autonomous_agent_demo.py --project-dir test-win --max-iterations 1

# Expected: No "Agent type not found" error
# Expected: No "Command 'dir' not in allowed" error
# Expected: "Sandbox disabled" message in output
```

1. Run the orchestrator on Windows
2. Verify the orchestrator can delegate to `linear` agent (or falls back to `general-purpose`)
3. Verify `dir` command works in bash
4. Verify dangerous commands (`del C:\Windows`) are blocked
5. Verify the session progresses past the agent delegation step

### Edge Cases

- [ ] Test `taskkill /IM node.exe` - should be allowed
- [ ] Test `taskkill /IM explorer.exe` - should be blocked
- [ ] Test `del C:\Windows\System32` - should be blocked
- [ ] Test `del .\node_modules` - should be allowed
- [ ] Test filesystem agents are loaded: Check if `.claude/agents/*.md` files are parsed

### Regression Check

- [ ] Run on Mac/Linux to ensure sandbox still works
- [ ] Verify existing Unix commands still work
- [ ] Verify programmatic agent definitions still work (backwards compatibility)

---

## Risks

1. **Filesystem agents may not work with current SDK version**
   - Mitigation: Check SDK version and consider upgrading if needed
   - Fallback: Use `general-purpose` with full prompt injection

2. **Command line length limits on Windows (8191 chars)**
   - Mitigation: Keep agent prompts concise
   - Monitor: Check for truncation errors

3. **PowerShell commands may bypass validation**
   - Mitigation: Don't add unrestricted PowerShell to allowlist
   - Consider: Add PowerShell script validation if needed

4. **Security reduced without sandbox on Windows**
   - Mitigation: Rely on permission system and bash hook validation
   - Document: Clearly state Windows security limitations

---

## Implementation Order

1. Task 5 (security.py) - Foundation for Windows commands
2. Task 6 (client.py) - Disable sandbox on Windows
3. Tasks 1-4 (filesystem agents) - Create agent files
4. Task 7 (orchestrator prompt) - Update delegation instructions
5. Validation - Test on Windows
