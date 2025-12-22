# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python harness for running long-running autonomous coding agents using the Claude Agent SDK. It implements a two-agent pattern where an initializer agent creates Linear issues from a spec, and subsequent coding agents implement those issues one-by-one.

## Commands

This project uses **uv** for dependency management and **poe** (poethepoet) for task running.

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Install with dev dependencies (includes poe)
uv sync --group dev

# Run the autonomous agent
uv run poe run

# Run with limited iterations (for testing)
uv run poe run-limited

# Run agent with custom options
uv run poe agent --project-dir ./my_project --max-iterations 5 --model claude-sonnet-4-5-20250929

# Run security hook tests
uv run poe test

# Check environment variables are set
uv run poe check-env

# List all available tasks
uv run poe --help
```

### Direct Python Execution (alternative)

```bash
# Run directly without poe
uv run python autonomous_agent_demo.py --project-dir ./my_project
uv run python autonomous_agent_demo.py --project-dir ./my_project --max-iterations 3
uv run python test_security.py
```

## Environment Setup

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required variables:

- `CLAUDE_CODE_OAUTH_TOKEN` - Generated via `claude setup-token`
- `LINEAR_API_KEY` - From <https://linear.app/YOUR-TEAM/settings/api>

The `.env` file is automatically loaded by poe tasks.

## Architecture

### Two-Agent Pattern

1. **Initializer Agent** (first run): Reads `prompts/app_spec.txt`, creates a Linear project with 50 issues, sets up project structure, creates `init.sh`, initializes git, and saves state to `.linear_project.json`

2. **Coding Agent** (subsequent runs): Queries Linear for highest-priority Todo issues, claims them (In Progress), implements with browser testing via Puppeteer, marks complete (Done), and updates META issue with session notes

### Core Modules

- `autonomous_agent_demo.py` - Entry point, argument parsing, main loop orchestration
- `agent.py` - Agent session logic, runs queries through SDK, handles auto-continuation between sessions
- `client.py` - Claude SDK client configuration with MCP servers (Linear, Puppeteer) and security settings
- `security.py` - Bash command allowlist hook with extra validation for `pkill`, `chmod`, and `init.sh`
- `progress.py` - Progress tracking utilities, reads `.linear_project.json` marker file
- `prompts.py` - Loads prompts from `prompts/` directory
- `linear_config.py` - Linear constants (statuses, priorities, marker filename)

### Security Model

Three-layer defense in depth:

1. **OS sandbox** - Enabled via `ClaudeCodeOptions` for bash isolation
2. **Filesystem permissions** - Restricted to project directory via `./**` patterns
3. **Bash allowlist hook** - Only permits commands in `security.ALLOWED_COMMANDS`

### MCP Integration

- **Linear** (HTTP transport at mcp.linear.app) - Issue tracking, project management
- **Puppeteer** (stdio) - Browser automation for UI verification

### Session Handoff

Agents communicate through Linear:

- Issue comments contain implementation details
- META issue tracks session summaries
- `.linear_project.json` marks initialization complete

## Project Structure

```text
linear-coding-agent-harness/
├── pyproject.toml           # uv project config & poe tasks
├── uv.lock                  # Lockfile (auto-generated)
├── .python-version          # Python version pin
├── .env.example             # Environment template
├── .env                     # Your credentials (git-ignored)
├── .venv/                   # Virtual environment (auto-created)
├── autonomous_agent_demo.py # Main entry point
├── agent.py                 # Agent session logic
├── client.py                # Claude SDK + MCP client configuration
├── security.py              # Bash command allowlist and validation
├── progress.py              # Progress tracking utilities
├── prompts.py               # Prompt loading utilities
├── linear_config.py         # Linear configuration constants
├── test_security.py         # Security hook tests
└── prompts/
    ├── app_spec.txt         # Application specification
    ├── initializer_prompt.md # First session prompt
    └── coding_prompt.md     # Continuation session prompt
```

## Modifying Allowed Commands

Edit `security.py` `ALLOWED_COMMANDS` set to add or remove bash commands. Commands in `COMMANDS_NEEDING_EXTRA_VALIDATION` require additional checks (e.g., `pkill` only allows dev processes like node/npm/vite).

## Changing Issue Count

Edit `prompts/initializer_prompt.md` and change "50 issues" to desired count. Also update the template for `.linear_project.json` in that prompt.

## Adding New Poe Tasks

Edit the `[tool.poe.tasks]` section in `pyproject.toml` to add new tasks:

```toml
[tool.poe.tasks]
my-task = { cmd = "python my_script.py", help = "Description of my task" }
```
