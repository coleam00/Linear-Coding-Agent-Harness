# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent orchestrator harness using the Claude Agent SDK. A central orchestrator delegates work to specialized agents (Linear, Coding, GitHub, Slack) that collaborate to build applications autonomously. All work is tracked in Linear.

## Commands

```bash
# Create and activate virtual environment (Python 3.10+ required)
uv venv
# Windows (PowerShell)
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Authorize Arcade services (run once, or per-service)
python authorize_arcade.py              # All services
python authorize_arcade.py linear       # Linear only
python authorize_arcade.py github       # GitHub only
python authorize_arcade.py slack        # Slack only

# Run the orchestrator
python autonomous_agent_demo.py --project-dir my-app

# With custom output location
python autonomous_agent_demo.py --generations-base ~/projects/ai --project-dir my-app

# Limit iterations for testing
python autonomous_agent_demo.py --project-dir my-app --max-iterations 3

# Use Opus for orchestrator
python autonomous_agent_demo.py --project-dir my-app --model opus

# Run security tests
python test_security.py
```

## Required Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `ARCADE_API_KEY` | Yes | From https://api.arcade.dev/dashboard/api-keys (starts with `arc_`) |
| `ARCADE_GATEWAY_SLUG` | Yes | Your MCP gateway slug from Arcade dashboard |
| `ARCADE_USER_ID` | Recommended | Your email for user tracking |
| `GITHUB_REPO` | No | Format: `owner/repo` for auto-push |
| `SLACK_CHANNEL` | No | Channel name (without #) for notifications |

Per-agent model configuration (options: haiku, sonnet, opus, inherit):
- `ORCHESTRATOR_MODEL` (default: haiku)
- `LINEAR_AGENT_MODEL` (default: haiku)
- `CODING_AGENT_MODEL` (default: sonnet)
- `GITHUB_AGENT_MODEL` (default: haiku)
- `SLACK_AGENT_MODEL` (default: haiku)

## Architecture

### Multi-Agent Orchestration Pattern

```
ORCHESTRATOR (coordinates all work)
    ├─→ LINEAR AGENT    - Issue management, status transitions, META issue updates
    ├─→ CODING AGENT    - Implements features, Puppeteer browser testing
    ├─→ GITHUB AGENT    - Git commits, branches, PRs (requires GITHUB_REPO)
    └─→ SLACK AGENT     - Notifications (requires pre-existing channel)
```

### Core Modules

- `autonomous_agent_demo.py` - CLI entry point, parses args
- `agent.py` - Main session loop with `run_autonomous_agent()` and `run_agent_session()`
- `client.py` - Creates ClaudeSDKClient with security settings and MCP servers
- `agents/definitions.py` - Agent definitions with per-agent model configuration
- `agents/orchestrator.py` - Runs orchestrated sessions via `run_orchestrated_session()`
- `arcade_config.py` - Arcade MCP gateway config, tool lists for Linear/GitHub/Slack
- `authorize_arcade.py` - OAuth flow for Arcade services
- `security.py` - Bash command allowlist and validation hooks
- `progress.py` - Progress tracking via `.linear_project.json` and `claude-progress.txt`
- `prompts.py` - Loads prompts from `prompts/` directory

### Security Model (Defense-in-Depth)

1. OS-level sandbox for bash execution
2. Filesystem restricted to project directory
3. Bash command allowlist in `security.py` (see `ALLOWED_COMMANDS`)
4. Extra validation for sensitive commands:
   - `pkill` - Only dev processes (node, npm, vite, next)
   - `chmod` - Only +x mode
   - `rm` - Blocks dangerous paths (/, /etc, /usr, /home, etc.)
   - `init.sh` - Only ./init.sh allowed

### MCP Servers

- **Arcade Gateway** (HTTP): Unified access to Linear, GitHub, Slack via `https://mcp.arcade.dev/gateway/{slug}`
- **Puppeteer** (stdio): `npx puppeteer-mcp-server` for browser automation

### Session Flow

**First Run:**
1. Orchestrator reads `app_spec.txt`
2. Linear agent creates project + issues + META issue
3. Writes `.linear_project.json` marker
4. GitHub agent initializes repo (if GITHUB_REPO set)

**Continuation:**
1. Orchestrator reads `.linear_project.json` and `claude-progress.txt`
2. Linear agent checks status counts
3. **Verification gate**: Test completed features before new work
4. Coding agent implements next issue with Puppeteer testing
5. GitHub agent commits/pushes
6. Linear agent marks Done (requires screenshot evidence)
7. Slack agent notifies (optional)

### Critical Design Principles

From the orchestrator prompt - agents don't share memory, so:
- Pass full context between agents (don't tell agent to "check Linear" - pass the data)
- Verification gate is MANDATORY before new work
- Screenshot evidence is MANDATORY before marking issues Done
- Fix regressions before any new work

### Agent Prompts

Located in `prompts/`:
- `orchestrator_prompt.md` - Coordination and delegation rules
- `linear_agent_prompt.md` - Issue management, `claude-progress.txt` format
- `coding_agent_prompt.md` - Implementation, Puppeteer testing patterns
- `github_agent_prompt.md` - Git workflow, commit message format, PR creation
- `slack_agent_prompt.md` - Notification patterns

## Customization

- `prompts/app_spec.txt` - Application specification to build
- `security.py:ALLOWED_COMMANDS` - Permitted bash commands
- `agents/definitions.py` - Agent model and tool configuration
