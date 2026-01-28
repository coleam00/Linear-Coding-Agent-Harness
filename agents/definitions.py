"""
Agent Definitions
=================

Specialized agent configurations using Claude Agent SDK's AgentDefinition.
Model selection is configurable via environment variables.

NOTE: Agent prompts use a "self-loading" pattern to avoid Windows command line
length limits. The SDK passes agents via --agents JSON flag, which exceeds
Windows' 8000 char limit when full prompts are embedded. Instead, we pass
minimal prompts that instruct agents to read their full instructions from files
copied to the project directory.

See: https://github.com/anthropics/claude-code/issues/21423
"""

import os
from pathlib import Path
from typing import Final, Literal, TypeGuard

from claude_agent_sdk.types import AgentDefinition

from arcade_config import (
    get_linear_tools,
    get_github_tools,
    get_slack_tools,
    get_coding_tools,
)

# File tools needed by multiple agents
FILE_TOOLS: list[str] = ["Read", "Write", "Edit", "Glob"]

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Directory name where agent prompts are copied in project directory
AGENT_PROMPTS_DIR_NAME = ".agent_prompts"

# Valid model options for AgentDefinition
ModelOption = Literal["haiku", "sonnet", "opus", "inherit"]

# Valid model values as a tuple for runtime validation
_VALID_MODELS: Final[tuple[str, ...]] = ("haiku", "sonnet", "opus", "inherit")

# Default models for each agent (immutable)
DEFAULT_MODELS: Final[dict[str, ModelOption]] = {
    "linear": "haiku",
    "coding": "sonnet",
    "github": "haiku",
    "slack": "haiku",
}


def _is_valid_model(value: str) -> TypeGuard[ModelOption]:
    """Type guard to validate model option values."""
    return value in _VALID_MODELS


def _get_model(agent_name: str) -> ModelOption:
    """
    Get the model for an agent from environment variable or default.

    Environment variables:
        LINEAR_AGENT_MODEL, CODING_AGENT_MODEL, GITHUB_AGENT_MODEL, SLACK_AGENT_MODEL

    Valid values: haiku, sonnet, opus, inherit
    """
    env_var = f"{agent_name.upper()}_AGENT_MODEL"
    value = os.environ.get(env_var, "").lower().strip()

    if _is_valid_model(value):
        return value  # Type checker knows this is ModelOption via TypeGuard

    default = DEFAULT_MODELS.get(agent_name)
    if default is not None:
        return default  # DEFAULT_MODELS is typed as dict[str, ModelOption]

    # Fallback for unknown agent names
    return "haiku"


def _get_self_loading_prompt(agent_name: str, prompt_filename: str) -> str:
    """
    Return a minimal prompt that tells the agent to read its full instructions.

    This keeps the agents JSON small enough to fit within Windows command line limits.
    The full prompt file is copied to the project's .agent_prompts/ directory at startup.
    """
    return f"""You are the {agent_name} agent. Your full instructions are in the file:
.agent_prompts/{prompt_filename}.md

IMPORTANT: Read that file NOW using the Read tool before doing anything else.
Follow all instructions in that file exactly."""


OrchestratorModelOption = Literal["haiku", "sonnet", "opus"]

# Valid orchestrator model values (no "inherit" option since orchestrator is root)
_VALID_ORCHESTRATOR_MODELS: Final[tuple[str, ...]] = ("haiku", "sonnet", "opus")


def _is_valid_orchestrator_model(value: str) -> TypeGuard[OrchestratorModelOption]:
    """Type guard to validate orchestrator model option values."""
    return value in _VALID_ORCHESTRATOR_MODELS


def get_orchestrator_model() -> OrchestratorModelOption:
    """
    Get the orchestrator model from environment variable or default.

    Environment variable: ORCHESTRATOR_MODEL
    Valid values: haiku, sonnet, opus (no "inherit" since orchestrator is root)
    Default: haiku
    """
    value = os.environ.get("ORCHESTRATOR_MODEL", "").lower().strip()
    if _is_valid_orchestrator_model(value):
        return value  # Type checker knows this is OrchestratorModelOption via TypeGuard
    return "haiku"


def create_agent_definitions() -> dict[str, AgentDefinition]:
    """
    Create agent definitions with models from environment configuration.

    Uses self-loading prompts to keep JSON size under Windows command line limits.
    Full prompts are read by agents from .agent_prompts/ directory at runtime.

    This is called at import time but reads env vars, so changes to
    environment require reimporting or restarting.
    """
    return {
        "linear": AgentDefinition(
            description="Manages Linear issues, project status, and session handoff. Use for any Linear operations.",
            prompt=_get_self_loading_prompt("linear", "linear_agent_prompt"),
            tools=get_linear_tools() + FILE_TOOLS,
            model=_get_model("linear"),
        ),
        "github": AgentDefinition(
            description="Handles Git commits, branches, and GitHub PRs. Use for version control operations.",
            prompt=_get_self_loading_prompt("github", "github_agent_prompt"),
            tools=get_github_tools() + FILE_TOOLS + ["Bash"],
            model=_get_model("github"),
        ),
        "slack": AgentDefinition(
            description="Sends Slack notifications to keep users informed. Use for progress updates.",
            prompt=_get_self_loading_prompt("slack", "slack_agent_prompt"),
            tools=get_slack_tools() + FILE_TOOLS,
            model=_get_model("slack"),
        ),
        "coding": AgentDefinition(
            description="Writes and tests code. Use when implementing features or fixing bugs.",
            prompt=_get_self_loading_prompt("coding", "coding_agent_prompt"),
            tools=get_coding_tools(),
            model=_get_model("coding"),
        ),
    }


# Create definitions at import time (reads env vars)
AGENT_DEFINITIONS: dict[str, AgentDefinition] = create_agent_definitions()

# Export individual agents for convenience
LINEAR_AGENT = AGENT_DEFINITIONS["linear"]
GITHUB_AGENT = AGENT_DEFINITIONS["github"]
SLACK_AGENT = AGENT_DEFINITIONS["slack"]
CODING_AGENT = AGENT_DEFINITIONS["coding"]
