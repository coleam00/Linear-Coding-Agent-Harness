# Quickstart Guide

Get the multi-agent orchestrator running in 5 minutes.

## Prerequisites

- **Python 3.10+** with pip
- **uv** (fast Python package manager) - [install instructions](https://docs.astral.sh/uv/getting-started/installation/)
- **Node.js 18+** (for Puppeteer MCP server)
- **Claude CLI** authenticated (`claude login`)
- **Arcade account** at [arcade.dev](https://arcade.dev)
- **Linear account** at [linear.app](https://linear.app)

Optional:
- **GitHub account** (for auto-push to repos)
- **Slack workspace** (for notifications)

---

## Step 1: Clone and Install

```bash
git clone https://github.com/dynamous/Linear-Coding-Agent-Harness.git
cd Linear-Coding-Agent-Harness

# Create and activate virtual environment
uv venv
# Windows (PowerShell)
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install Python dependencies
uv pip install -r requirements.txt

# Install Puppeteer MCP server globally
npm install -g puppeteer-mcp-server
```

---

## Step 2: Set Up Arcade

### 2.1 Get Your API Key

1. Go to [arcade.dev/dashboard/api-keys](https://api.arcade.dev/dashboard/api-keys)
2. Create a new API key (starts with `arc_`)
3. Copy it for the next step

### 2.2 Create an MCP Gateway

1. Go to [arcade.dev/dashboard/mcp-gateways](https://api.arcade.dev/dashboard/mcp-gateways)
2. Click **Create Gateway**
3. Add these tool providers:
   - **Linear** (required)
   - **GitHub** (optional, for auto-push)
   - **Slack** (optional, for notifications)
4. Copy your gateway slug (e.g., `my-gateway-name`)

---

## Step 3: Configure Environment

```bash
# Copy the example config
cp .env.example .env
```

Edit `.env` with your values:

```bash
# Required
ARCADE_API_KEY=arc_xxxxxxxxxxxxx
ARCADE_GATEWAY_SLUG=your-gateway-slug
ARCADE_USER_ID=you@example.com

# Optional: GitHub auto-push
GITHUB_REPO=owner/repo-name

# Optional: Slack notifications (channel must already exist)
SLACK_CHANNEL=project-updates
```

---

## Step 4: Authorize Services

Run the authorization script to connect your accounts via OAuth:

```bash
# Authorize all services at once
python authorize_arcade.py

# Or authorize individually
python authorize_arcade.py linear
python authorize_arcade.py github
python authorize_arcade.py slack
```

Follow the links printed in the terminal to complete OAuth for each service.

---

## Step 5: Write Your App Spec

Create your app specification file:

```bash
# Option 1: Copy the example and customize it
cp prompts/app_spec_example.txt prompts/app_spec.txt

# Option 2: Create your own from scratch
```

Edit `prompts/app_spec.txt` to describe what you want to build:

```markdown
# My App Name

Brief description of the application.

## Tech Stack
- Frontend: React/Vue/Vanilla JS
- Backend: Node.js/Python/None

## Features (aim for 3-6)

### 1. Feature Name
- Description of the feature
- Acceptance criteria

### 2. Another Feature
- ...

## Success Criteria
- How to know it's working
```

> **Note:** `prompts/app_spec.txt` is gitignored so your custom specs won't be committed.
> The example file `prompts/app_spec_example.txt` is provided as a reference.

---

## Step 6: Run the Orchestrator

```bash
# Start a new project
python autonomous_agent_demo.py --project-dir my-app

# With custom output location
python autonomous_agent_demo.py --generations-base ~/projects/ai --project-dir my-app

# Limit iterations for testing
python autonomous_agent_demo.py --project-dir my-app --max-iterations 3

# Use Opus for more capable orchestration
python autonomous_agent_demo.py --project-dir my-app --model opus
```

Generated projects are created in `./generations/<project-dir>/` by default.

---

## What Happens Next

### First Run
1. Orchestrator reads your `app_spec.txt`
2. Linear Agent creates a project and issues in Linear
3. Creates a META issue to track overall progress
4. GitHub Agent initializes a git repo (if `GITHUB_REPO` is set)

### Subsequent Runs
1. Orchestrator loads state from `.linear_project.json`
2. Verifies previously completed features still work
3. Implements the next issue with visual testing
4. Commits and pushes code
5. Marks issues as Done in Linear

You can interrupt with `Ctrl+C` and resume by running the same command again.

---

## Troubleshooting

### "ARCADE_API_KEY not set"
Make sure your `.env` file exists and contains a valid API key.

### "Authorization required"
Re-run `python authorize_arcade.py` to refresh OAuth tokens.

### "MCP server not found"
Install Puppeteer: `npm install -g puppeteer-mcp-server`

### "Claude authentication failed"
Run `claude login` to authenticate the CLI.

---

## Model Configuration

Configure which model each agent uses in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRATOR_MODEL` | haiku | Coordinates agents |
| `LINEAR_AGENT_MODEL` | haiku | Issue management |
| `CODING_AGENT_MODEL` | sonnet | Writes code |
| `GITHUB_AGENT_MODEL` | haiku | Git operations |
| `SLACK_AGENT_MODEL` | haiku | Notifications |

Options: `haiku`, `sonnet`, `opus`

---

## Project Structure

```
Linear-Coding-Agent-Harness/
├── autonomous_agent_demo.py   # CLI entry point
├── agent.py                   # Main agent loop
├── agents/                    # Agent definitions
├── prompts/
│   ├── app_spec.txt           # YOUR APP DESCRIPTION
│   ├── orchestrator_prompt.md # Orchestrator behavior
│   └── *_agent_prompt.md      # Per-agent prompts
├── generations/               # Output directory
│   └── <project>/             # Your generated app
└── .env                       # Your configuration
```

---

## Next Steps

- Read `CLAUDE.md` for architecture details
- Customize prompts in `prompts/` directory
- Add commands to the allowlist in `security.py`
- Run `python test_security.py` to verify security settings
