"""
Multi-Agent Orchestrator
========================

Specialized agents for different domains, coordinated by an orchestrator.
"""

from pathlib import Path
from typing import TYPE_CHECKING

from agents.definitions import (
    AGENT_DEFINITIONS,
    LINEAR_AGENT,
    GITHUB_AGENT,
    SLACK_AGENT,
    CODING_AGENT,
)

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeSDKClient
    from agent import SessionResult

__all__ = [
    "AGENT_DEFINITIONS",
    "LINEAR_AGENT",
    "GITHUB_AGENT",
    "SLACK_AGENT",
    "CODING_AGENT",
    "run_orchestrated_session",
]


async def run_orchestrated_session(
    client: "ClaudeSDKClient",
    project_dir: Path,
) -> "SessionResult":
    """
    Lazy import to avoid circular dependency.

    agents.orchestrator imports from agent.py, and agent.py imports from agents/.
    This wrapper allows agents/__init__.py to export the function without importing at module level.
    """
    from agents.orchestrator import run_orchestrated_session as _run

    return await _run(client, project_dir)
