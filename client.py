"""
Claude SDK Client Configuration
===============================

Functions for creating and configuring the Claude Agent SDK client.
Uses Arcade MCP Gateway for Linear + GitHub + Slack integration.
"""

import json
from pathlib import Path
from typing import Literal, TypedDict, cast

from dotenv import load_dotenv

load_dotenv()

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, McpServerConfig
from claude_agent_sdk.types import HookCallback, HookMatcher

from arcade_config import (
    ALL_ARCADE_TOOLS,
    ARCADE_TOOLS_PERMISSION,
    get_arcade_mcp_config,
    validate_arcade_config,
)
from agents.definitions import AGENT_DEFINITIONS
from security import bash_security_hook


# Valid permission modes for the Claude SDK
PermissionMode = Literal["acceptEdits", "acceptAll", "reject", "ask"]


class SandboxConfig(TypedDict):
    """Sandbox configuration for bash command isolation."""

    enabled: bool
    autoAllowBashIfSandboxed: bool


class PermissionsConfig(TypedDict):
    """Permissions configuration for file and tool operations."""

    defaultMode: PermissionMode
    allow: list[str]


class SecuritySettings(TypedDict):
    """Complete security settings structure."""

    sandbox: SandboxConfig
    permissions: PermissionsConfig


# Puppeteer MCP tools for browser automation
PUPPETEER_TOOLS: list[str] = [
    "mcp__puppeteer__puppeteer_navigate",
    "mcp__puppeteer__puppeteer_screenshot",
    "mcp__puppeteer__puppeteer_click",
    "mcp__puppeteer__puppeteer_fill",
    "mcp__puppeteer__puppeteer_select",
    "mcp__puppeteer__puppeteer_hover",
    "mcp__puppeteer__puppeteer_evaluate",
]

# Built-in tools
BUILTIN_TOOLS: list[str] = [
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
]

# Prompts directory
PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_orchestrator_prompt() -> str:
    """
    Return a minimal self-loading prompt for the orchestrator.

    The full orchestrator instructions are copied to .agent_prompts/ at startup.
    This keeps the command line under Windows' 8000 char limit when combined
    with the agents JSON.
    """
    return """You are the ORCHESTRATOR agent coordinating specialized agents to build applications.

IMPORTANT: Your full instructions are in the file:
.agent_prompts/orchestrator_prompt.md

Read that file NOW using the Read tool before doing anything else.
Follow all instructions in that file exactly.

Quick reference (read full file for details):
- Delegate to: linear, coding, github, slack agents via Task tool
- ALWAYS pass full context between agents (they don't share memory)
- MANDATORY: Run verification test before new work
- MANDATORY: Require screenshot evidence before marking issues Done"""


def create_security_settings() -> SecuritySettings:
    """
    Create the security settings structure.

    Returns:
        SecuritySettings with sandbox and permissions configured
    """
    return SecuritySettings(
        sandbox=SandboxConfig(enabled=True, autoAllowBashIfSandboxed=True),
        permissions=PermissionsConfig(
            defaultMode="acceptEdits",
            allow=[
                # Allow all file operations within the project directory
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                # Bash permission granted here, but actual commands are validated
                # by the bash_security_hook (see security.py for allowed commands)
                "Bash(*)",
                # Allow Puppeteer MCP tools for browser automation
                *PUPPETEER_TOOLS,
                # Allow all Arcade MCP Gateway tools (Linear + GitHub + Slack)
                ARCADE_TOOLS_PERMISSION,
            ],
        ),
    )


def write_security_settings(project_dir: Path, settings: SecuritySettings) -> Path:
    """
    Write security settings to project directory.

    Args:
        project_dir: Directory to write settings to
        settings: Security settings to write

    Returns:
        Path to the settings file

    Raises:
        IOError: If settings file cannot be written
    """
    project_dir.mkdir(parents=True, exist_ok=True)
    settings_file: Path = project_dir / ".claude_settings.json"

    try:
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
    except IOError as e:
        raise IOError(
            f"Failed to write security settings to {settings_file}: {e}\n"
            f"Check disk space and file permissions.\n"
            f"Agent cannot start without security settings."
        ) from e

    return settings_file


def create_client(project_dir: Path, model: str) -> ClaudeSDKClient:
    """
    Create a Claude Agent SDK client with multi-layered security.

    Args:
        project_dir: Directory for the project
        model: Claude model to use

    Returns:
        Configured ClaudeSDKClient

    Raises:
        ValueError: If required environment variables are not set

    Security layers (defense in depth):
    1. Sandbox - OS-level bash command isolation prevents filesystem escape
       (bwrap/docker-style isolation)
    2. Permissions - File operations restricted to project_dir only
       (enforced by SDK before tool execution)
    3. Security hooks - Bash commands validated against an allowlist
       (runs pre-execution via PreToolUse hook, see security.py for ALLOWED_COMMANDS)

    Execution: Permissions checked first, then hooks run, finally sandbox executes.
    """
    # Validate Arcade configuration
    validate_arcade_config()

    # Get Arcade MCP configuration
    arcade_config = get_arcade_mcp_config()

    # Create and write security settings
    security_settings: SecuritySettings = create_security_settings()
    settings_file: Path = write_security_settings(project_dir, security_settings)

    print(f"Created security settings at {settings_file}")
    print("   - Sandbox enabled (OS-level bash isolation)")
    print(f"   - Filesystem restricted to: {project_dir.resolve()}")
    print("   - Bash commands restricted to allowlist (see security.py)")
    print(f"   - MCP servers: puppeteer (browser), arcade ({arcade_config['url']})")
    print()

    # Load orchestrator prompt as system prompt
    orchestrator_prompt = load_orchestrator_prompt()

    # NOTE: We don't set allowed_tools here because:
    # 1. MCP servers automatically expose their tools
    # 2. The full tools list is ~3700 chars which exceeds Windows cmd limit
    #    when combined with agents JSON (~5600 chars)
    # 3. Permissions are controlled via security_settings and hooks instead
    return ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            system_prompt=orchestrator_prompt,
            mcp_servers=cast(
                dict[str, McpServerConfig],
                {
                    "puppeteer": {"command": "npx", "args": ["puppeteer-mcp-server"]},
                    "arcade": arcade_config,
                },
            ),
            hooks={
                "PreToolUse": [
                    HookMatcher(
                        matcher="Bash",
                        hooks=[cast(HookCallback, bash_security_hook)],
                    ),
                ],
            },
            agents=AGENT_DEFINITIONS,
            max_turns=1000,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),
        )
    )
