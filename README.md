# Autonomous Coding Agent Demo (Linear-Integrated)

A minimal harness demonstrating long-running autonomous coding with the Claude Agent SDK. This demo implements a two-agent pattern (initializer + coding agent) with **Linear as the core project management system** for tracking all work.

## Key Features

- **Linear Integration**: All work is tracked as Linear issues, not local files
- **Real-time Visibility**: Watch agent progress directly in your Linear workspace
- **Session Handoff**: Agents communicate via Linear comments, not text files
- **Two-Agent Pattern**: Initializer creates Linear project & issues, coding agents implement them
- **Browser Testing**: Puppeteer MCP for UI verification
- **Claude Opus 4.5**: Uses Claude's most capable model by default

## Prerequisites

### 1. Install Claude Code CLI and uv

```bash
# Install Claude Code CLI (latest version required)
npm install -g @anthropic-ai/claude-code

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install Project Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd linear-coding-agent-harness

# Install dependencies (creates .venv automatically)
uv sync --group dev
```

### 3. Set Up Authentication

Copy the environment template and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your values:

```bash
# Claude Code OAuth Token - Generate with: claude setup-token
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token-here

# Linear API Key - Get from: https://linear.app/YOUR-TEAM/settings/api
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx
```

The `.env` file is automatically loaded by poe tasks.

### 4. Verify Installation

```bash
claude --version              # Should be latest version
uv run poe check-env          # Check environment variables
```

## Quick Start

```bash
# Run with default settings
uv run poe run

# Run with limited iterations (for testing)
uv run poe run-limited

# Run with custom options
uv run poe agent --project-dir ./my_project --max-iterations 5
```

## Available Tasks

Run `uv run poe --help` to see all available tasks:

| Task | Description |
|------|-------------|
| `poe run` | Run the autonomous agent with default settings |
| `poe run-limited` | Run agent with limited iterations (for testing) |
| `poe agent` | Run agent with custom options (--project-dir, --max-iterations, --model) |
| `poe test` | Run security hook tests |
| `poe check-env` | Check if required environment variables are set |

## How It Works

### Linear-Centric Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    LINEAR-INTEGRATED WORKFLOW               │
├─────────────────────────────────────────────────────────────┤
│  app_spec.txt ──► Initializer Agent ──► Linear Issues (50) │
│                                              │               │
│                    ┌─────────────────────────▼──────────┐   │
│                    │        LINEAR WORKSPACE            │   │
│                    │  ┌────────────────────────────┐    │   │
│                    │  │ Issue: Auth - Login flow   │    │   │
│                    │  │ Status: Todo → In Progress │    │   │
│                    │  │ Comments: [session notes]  │    │   │
│                    │  └────────────────────────────┘    │   │
│                    └────────────────────────────────────┘   │
│                                              │               │
│                    Coding Agent queries Linear              │
│                    ├── Search for Todo issues               │
│                    ├── Update status to In Progress         │
│                    ├── Implement & test with Puppeteer      │
│                    ├── Add comment with implementation notes│
│                    └── Update status to Done                │
└─────────────────────────────────────────────────────────────┘
```

### Two-Agent Pattern

1. **Initializer Agent (Session 1):**
   - Reads `app_spec.txt`
   - Lists teams and creates a new Linear project
   - Creates 50 Linear issues with detailed test steps
   - Creates a META issue for session tracking
   - Sets up project structure, `init.sh`, and git

2. **Coding Agent (Sessions 2+):**
   - Queries Linear for highest-priority Todo issue
   - Runs verification tests on previously completed features
   - Claims issue (status → In Progress)
   - Implements the feature
   - Tests via Puppeteer browser automation
   - Adds implementation comment to issue
   - Marks complete (status → Done)
   - Updates META issue with session summary

### Session Handoff via Linear

Instead of local text files, agents communicate through:
- **Issue Comments**: Implementation details, blockers, context
- **META Issue**: Session summaries and handoff notes
- **Issue Status**: Todo / In Progress / Done workflow

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code OAuth token (from `claude setup-token`) | Yes |
| `LINEAR_API_KEY` | Linear API key for MCP access | Yes |

## Command Line Options

When using `poe agent`:

| Option | Description | Default |
|--------|-------------|---------|
| `--project-dir`, `-p` | Directory for the project | `./my_project` |
| `--max-iterations`, `-m` | Max agent iterations | Unlimited |
| `--model` | Claude model to use | `claude-opus-4-5-20251101` |

## Project Structure

```text
linear-coding-agent-harness/
├── pyproject.toml           # uv project config & poe tasks
├── uv.lock                  # Lockfile (auto-generated)
├── .python-version          # Python version pin (3.12)
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
    ├── initializer_prompt.md # First session prompt (creates Linear issues)
    └── coding_prompt.md     # Continuation session prompt (works issues)
```

## Generated Project Structure

After running, your project directory will contain:

```
my_project/
├── .linear_project.json      # Linear project state (marker file)
├── app_spec.txt              # Copied specification
├── init.sh                   # Environment setup script
├── .claude_settings.json     # Security settings
└── [application files]       # Generated application code
```

## MCP Servers Used

| Server | Transport | Purpose |
|--------|-----------|---------|
| **Linear** | HTTP (Streamable HTTP) | Project management - issues, status, comments |
| **Puppeteer** | stdio | Browser automation for UI testing |

## Security Model

This demo uses defense-in-depth security (see `security.py` and `client.py`):

1. **OS-level Sandbox:** Bash commands run in an isolated environment
2. **Filesystem Restrictions:** File operations restricted to project directory
3. **Bash Allowlist:** Only specific commands permitted (npm, node, git, etc.)
4. **MCP Permissions:** Tools explicitly allowed in security settings

## Linear Setup

Before running, ensure you have:

1. A Linear workspace with at least one team
2. An API key with read/write permissions (from Settings > API)
3. The agent will automatically detect your team and create a project

The initializer agent will create:
- A new Linear project named after your app
- 50 feature issues based on `app_spec.txt`
- 1 META issue for session tracking and handoff

All subsequent coding agents will work from this Linear project.

## Customization

### Changing the Application

Edit `prompts/app_spec.txt` to specify a different application to build.

### Adjusting Issue Count

Edit `prompts/initializer_prompt.md` and change "50 issues" to your desired count.

### Modifying Allowed Commands

Edit `security.py` to add or remove commands from `ALLOWED_COMMANDS`.

### Adding New Poe Tasks

Edit `pyproject.toml` to add new tasks:

```toml
[tool.poe.tasks]
my-task = { cmd = "python my_script.py", help = "Description of my task" }
```

## Troubleshooting

**"CLAUDE_CODE_OAUTH_TOKEN not set"**
Run `claude setup-token` to generate a token, then export it.

**"LINEAR_API_KEY not set"**
Get your API key from `https://linear.app/YOUR-TEAM/settings/api`

**"Appears to hang on first run"**
Normal behavior. The initializer is creating a Linear project and 50 issues with detailed descriptions. Watch for `[Tool: mcp__linear__create_issue]` output.

**"Command blocked by security hook"**
The agent tried to run a disallowed command. Add it to `ALLOWED_COMMANDS` in `security.py` if needed.

**"MCP server connection failed"**
Verify your `LINEAR_API_KEY` is valid and has appropriate permissions. The Linear MCP server uses HTTP transport at `https://mcp.linear.app/mcp`.

## Viewing Progress

Open your Linear workspace to see:
- The project created by the initializer agent
- All 50 issues organized under the project
- Real-time status changes (Todo → In Progress → Done)
- Implementation comments on each issue
- Session summaries on the META issue

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run poe test

# Add a new dependency
uv add <package-name>

# Add a dev dependency
uv add --group dev <package-name>
```

## License

MIT License - see [LICENSE](LICENSE) for details.
