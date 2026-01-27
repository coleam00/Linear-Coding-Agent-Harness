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
    """Load the orchestrator system prompt."""
    return (PROMPTS_DIR / "orchestrator_prompt.md").read_text()


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

    return ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            system_prompt=orchestrator_prompt,
            allowed_tools=[
                *BUILTIN_TOOLS,
                *PUPPETEER_TOOLS,
                *ALL_ARCADE_TOOLS,
            ],
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
