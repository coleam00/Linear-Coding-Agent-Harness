# Autonomous Coding Agent Demo (Multi-Agent Orchestration)

A minimal harness demonstrating long-running autonomous coding with the Claude Agent SDK. This demo implements a multi-agent orchestrator pattern where specialized agents (Linear, Coding, GitHub, Slack) collaborate through a central orchestrator to build complete applications.

> **Note:** This project requires macOS or Linux. Windows users must use WSL (Windows Subsystem for Linux).

## Key Features

- **Multi-Agent Orchestration**: Orchestrator delegates to specialized agents (Linear, Coding, GitHub, Slack)
- **Linear Integration**: All work tracked as Linear issues with real-time status updates
- **GitHub Integration**: Optional automatic commit and PR creation via Arcade MCP
- **Slack Notifications**: Optional progress updates to Slack channels
- **Configurable Output**: Projects created in isolated directories with separate git repos
- **Browser Testing**: Puppeteer MCP for UI verification
- **Model Configuration**: Per-agent model selection (Haiku, Sonnet, or Opus)

## Prerequisites

### 0. Set Up Python Virtual Environment (Recommended)

**Option A: Using uv (recommended)**
```bash
# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate
```

**Option B: Using standard Python**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate
```

### 1. Install Claude Code CLI and Python SDK

```bash
# Install Claude Code CLI
curl -fsSL https://claude.ai/install.sh | bash

# Install Python dependencies
uv pip install -r requirements.txt  # If using uv
pip install -r requirements.txt     # If using standard Python
```

### 2. Set Up Environment

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` and configure:

**Required:**
1. **ARCADE_API_KEY** - Get from https://api.arcade.dev/dashboard/api-keys
2. **ARCADE_GATEWAY_SLUG** - Create a gateway at https://api.arcade.dev/dashboard/mcp-gateways, configure the Auth Header setting, and add Linear, GitHub, and Slack tools
3. **ARCADE_USER_ID** - Your email for user tracking
4. **GENERATIONS_BASE_PATH** - Set to a directory **outside** this repo (e.g., `~/projects/ai-generations`). This is required for git/GitHub operations to work correctly.

**Recommended:**
5. **GITHUB_REPO** - Create a new GitHub repository and set this to `owner/repo-name`. The agent will commit and push code here.
6. **SLACK_CHANNEL** - Create a Slack channel (agents cannot create channels) and set this to the channel name without `#`.

Then authorize Arcade tools:
```bash
uv run python authorize_arcade.py  # If using uv
python3 authorize_arcade.py        # If using standard Python
```

### 3. Verify Installation

```bash
claude --version              # Should be latest version
uv pip show claude-agent-sdk  # If using uv
pip show claude-agent-sdk     # If using standard Python
```

## Quick Start

**1. Set up your app specification:**
```bash
# Copy the example spec or create your own
cp prompts/app_spec_example.txt prompts/app_spec.txt

# Edit the spec to describe the application you want to build
```

**2. Run the orchestrator:**
```bash
# Basic usage
uv run python autonomous_agent_demo.py --project-dir my-app

# Limit iterations for testing
uv run python autonomous_agent_demo.py --project-dir my-app --max-iterations 3

```

**Model configuration:** Edit the model settings in `.env`. We recommend Haiku for Linear, Slack, and GitHub agents. For more capable (but higher cost) results, use Opus for the orchestrator and coding agents.

## How It Works

### Multi-Agent Orchestration

```
┌───────────────────────────────────────────────────────────────┐
│                   MULTI-AGENT ARCHITECTURE                    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│                    ┌─────────────────┐                        │
│                    │  ORCHESTRATOR   │  (Haiku by default)    │
│                    │   Coordinates   │                        │
│                    └────────┬────────┘                        │
│                             │                                 │
│           ┌─────────────────┼─────────────────┐               │
│           │                 │                 │               │
│      ┌────▼─────┐    ┌─────▼──────┐   ┌─────▼──────┐        │
│      │  LINEAR  │    │   CODING   │   │   GITHUB   │        │
│      │  (Haiku) │    │  (Sonnet)  │   │  (Haiku)   │        │
│      └──────────┘    └────────────┘   └────────────┘        │
│           │                 │                 │               │
│      ┌────▼─────┐          │                 │               │
│      │  SLACK   │          │                 │               │
│      │ (Haiku)  │          │                 │               │
│      └──────────┘          │                 │               │
│                            │                 │               │
│     ┌──────────────────────▼─────────────────▼──────┐        │
│     │         PROJECT OUTPUT (Isolated Git)         │        │
│     │  GENERATIONS_BASE_PATH/project-name/          │        │
│     └───────────────────────────────────────────────┘        │
└───────────────────────────────────────────────────────────────┘
```

### Agent Responsibilities

1. **Orchestrator Agent:**
   - Reads project state from `.linear_project.json`
   - Queries Linear for current status
   - Decides what to work on next
   - Delegates to specialized agents via Task tool
   - Coordinates handoff between agents

2. **Linear Agent:**
   - Creates and updates Linear projects and issues
   - Manages issue status transitions (Todo → In Progress → Done)
   - Adds comments with implementation details
   - Maintains META issue for session tracking

3. **Coding Agent:**
   - Implements features based on Linear issues
   - Writes and tests application code
   - Uses Puppeteer for browser-based UI testing
   - Validates previously completed features

4. **GitHub Agent (Optional):**
   - Commits code changes to git
   - Creates branches and pushes to remote
   - Creates pull requests when features are ready
   - Requires `GITHUB_REPO` env var

5. **Slack Agent (Optional):**
   - Posts progress updates to Slack channels
   - Notifies on feature completion
   - Requires existing Slack channel (cannot create channels)

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ARCADE_API_KEY` | Arcade API key from https://api.arcade.dev/dashboard/api-keys | Yes |
| `ARCADE_GATEWAY_SLUG` | Your Arcade MCP gateway slug | Yes |
| `ARCADE_USER_ID` | Your email for user tracking | Recommended |
| `GENERATIONS_BASE_PATH` | Base directory for generated projects (must be outside this repo) | Yes |
| `GITHUB_REPO` | GitHub repo in format `owner/repo` for auto-push | Recommended |
| `SLACK_CHANNEL` | Slack channel name (without #) for notifications | Recommended |
| `ORCHESTRATOR_MODEL` | Model for orchestrator: haiku, sonnet, opus (default: haiku) | No |
| `LINEAR_AGENT_MODEL` | Model for Linear agent (default: haiku) | No |
| `CODING_AGENT_MODEL` | Model for coding agent (default: sonnet) | No |
| `GITHUB_AGENT_MODEL` | Model for GitHub agent (default: haiku) | No |
| `SLACK_AGENT_MODEL` | Model for Slack agent (default: haiku) | No |

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir` | Project name or path (relative paths go in generations base) | `./autonomous_demo_project` |
| `--generations-base` | Base directory for all generated projects | `./generations` or `GENERATIONS_BASE_PATH` |
| `--max-iterations` | Max agent iterations | Unlimited |
| `--model` | Orchestrator model: haiku, sonnet, or opus | `haiku` or `ORCHESTRATOR_MODEL` |

## Project Structure

```
linear-agent-harness/
├── autonomous_agent_demo.py  # Main entry point
├── agent.py                  # Agent session logic
├── client.py                 # Claude SDK + MCP client configuration
├── security.py               # Bash command allowlist and validation
├── progress.py               # Progress tracking utilities
├── prompts.py                # Prompt loading utilities
├── arcade_config.py          # Arcade MCP gateway configuration
├── authorize_arcade.py       # Arcade authorization flow
├── agents/
│   ├── definitions.py        # Agent definitions with model config
│   └── orchestrator.py       # Orchestrator session runner
├── prompts/
│   ├── app_spec.txt              # Your application specification
│   ├── app_spec_example.txt      # Example specification to copy
│   ├── orchestrator_prompt.md    # Orchestrator agent prompt
│   ├── linear_agent_prompt.md    # Linear agent prompt
│   ├── coding_agent_prompt.md    # Coding agent prompt
│   ├── github_agent_prompt.md    # GitHub agent prompt
│   └── slack_agent_prompt.md     # Slack agent prompt
└── requirements.txt          # Python dependencies
```

## Generated Project Structure

Projects are created in isolated directories with their own git repos:

```
generations/my-app/           # Or GENERATIONS_BASE_PATH/my-app/
├── .linear_project.json      # Linear project state (marker file)
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── .claude_settings.json     # Security settings
├── .git/                     # Separate git repository
└── [application files]       # Generated application code
```

## MCP Servers Used

| Server | Transport | Purpose |
|--------|-----------|---------|
| **Arcade Gateway** | HTTP | Unified access to Linear, GitHub, and Slack via Arcade MCP |
| **Puppeteer** | stdio | Browser automation for UI testing |

The Arcade Gateway provides access to:
- **Linear**: Project management, issues, status, comments (39 tools)
- **GitHub**: Repository operations, commits, PRs, branches (46 tools, optional)
- **Slack**: Messaging and notifications (8 tools, optional)

## Security Model

This demo uses defense-in-depth security (see `security.py` and `client.py`):

1. **OS-level Sandbox:** Bash commands run in an isolated environment
2. **Filesystem Restrictions:** File operations restricted to project directory
3. **Bash Allowlist:** Only specific commands permitted (npm, node, git, curl, rm with validation, etc.)
4. **MCP Permissions:** Tools explicitly allowed in security settings
5. **Dangerous Command Validation:** Commands like `rm` are validated to prevent system directory deletion

## Setup Guide

### 1. Arcade Gateway Setup

1. Get API key from https://api.arcade.dev/dashboard/api-keys
2. Create MCP gateway at https://api.arcade.dev/dashboard/mcp-gateways
3. **Important:** Configure the gateway's Auth Header setting to use your API key for authentication
4. Add Linear, GitHub, and Slack tools to your gateway
5. Run `python3 authorize_arcade.py` to complete OAuth authorization for each service

### 2. Linear Workspace

Ensure you have:
- A Linear workspace with at least one team
- Linear tools added to your Arcade gateway
- The orchestrator will automatically detect your team and create projects

### 3. GitHub Integration (Optional)

To enable GitHub integration:
1. Create a GitHub repository
2. Add GitHub tools to your Arcade gateway
3. Set `GITHUB_REPO=owner/repo-name` in `.env`
4. The GitHub agent will commit and push code automatically

### 4. Slack Integration (Optional)

To enable Slack notifications:
1. Create a Slack channel (agents cannot create channels)
2. Add Slack tools to your Arcade gateway
3. Set `SLACK_CHANNEL=channel-name` in `.env`

## Customization

### Changing the Application

Edit `prompts/app_spec.txt` to specify a different application to build.

### Adjusting Issue Count

The number of issues created is determined by the features listed in `prompts/app_spec.txt`. Add or remove features to adjust the issue count.

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

## Troubleshooting

**"ARCADE_API_KEY not set"**
Get your API key from https://api.arcade.dev/dashboard/api-keys and set it in `.env`

**"ARCADE_GATEWAY_SLUG not set"**
Create a gateway at https://api.arcade.dev/dashboard/mcp-gateways and add Linear tools

**"Authorization required"**
Run `python3 authorize_arcade.py` to complete the OAuth flow

**"Command blocked by security hook"**
The agent tried to run a disallowed command. Add it to `ALLOWED_COMMANDS` in `security.py` if needed.

**"MCP server connection failed"**
Verify your Arcade API key is valid and your gateway has the required tools configured.

**"GitHub agent requires GITHUB_REPO"**
If you want GitHub integration, set `GITHUB_REPO=owner/repo-name` in `.env`

**"Slack channel not found"**
Agents cannot create Slack channels. Create the channel manually and set `SLACK_CHANNEL` to the channel name (without #).

## Viewing Progress

**Linear Workspace:**
- View the project created by the orchestrator
- Watch real-time status changes (Todo → In Progress → Done)
- Read implementation comments on each issue
- Check session summaries on the META issue

**GitHub (if configured):**
- View commits pushed to your repository
- Review pull requests created by the GitHub agent

**Slack (if configured):**
- Receive progress updates in your configured channel
- Get notifications when features are completed

## License

MIT License - see [LICENSE](LICENSE) for details.
