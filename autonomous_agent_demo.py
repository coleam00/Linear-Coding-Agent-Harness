#!/usr/bin/env python3
"""
Autonomous Coding Agent Demo
============================

A minimal harness demonstrating long-running autonomous coding with Claude.
This script implements an orchestrator pattern where a main agent delegates to
specialized sub-agents (linear, coding, github, slack) for different domains.

Example Usage:
    uv run python autonomous_agent_demo.py --project-dir my-app
    uv run python autonomous_agent_demo.py --project-dir my-app --max-iterations 5
    uv run python autonomous_agent_demo.py --generations-base ~/projects/ai --project-dir my-app
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agent import run_autonomous_agent

# Load environment variables from .env file
load_dotenv()


# Available Claude 4.5 models
AVAILABLE_MODELS: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-5-20250929",
    "opus": "claude-opus-4-5-20251101",
}

# Default orchestrator model (can be overridden by ORCHESTRATOR_MODEL env var or --model flag)
# Orchestrator just delegates, so haiku is sufficient and cost-effective
DEFAULT_MODEL: str = os.environ.get("ORCHESTRATOR_MODEL", "haiku").lower()
if DEFAULT_MODEL not in AVAILABLE_MODELS:
    DEFAULT_MODEL = "haiku"

# Default base path for generated projects
# Can be overridden by GENERATIONS_BASE_PATH env var or --generations-base flag
DEFAULT_GENERATIONS_BASE: Path = Path(
    os.environ.get("GENERATIONS_BASE_PATH", "./generations")
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Coding Agent Demo - Long-running agent harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start fresh project (creates ./generations/my-app/)
  uv run python autonomous_agent_demo.py --project-dir my-app

  # Use a custom generations base directory
  uv run python autonomous_agent_demo.py --generations-base ~/projects/ai --project-dir my-app

  # Use opus for orchestrator (more capable but costs more)
  uv run python autonomous_agent_demo.py --project-dir my-app --model opus

  # Limit iterations for testing
  uv run python autonomous_agent_demo.py --project-dir my-app --max-iterations 5

  # Use absolute path (bypasses generations base)
  uv run python autonomous_agent_demo.py --project-dir /absolute/path/to/project

Environment Variables:
  ARCADE_API_KEY             Arcade API key for Linear integration (required)
  ARCADE_USER_ID             User email for Arcade (optional, defaults to agent@local)
  GENERATIONS_BASE_PATH      Base directory for generated projects (default: ./generations)
        """,
    )

    parser.add_argument(
        "--generations-base",
        type=Path,
        default=None,
        help=f"Base directory for all generated projects (default: {DEFAULT_GENERATIONS_BASE}, or set GENERATIONS_BASE_PATH env var). "
        "Each project creates a subfolder here with its own git repo.",
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("./autonomous_demo_project"),
        help="Project name or path. Relative paths are placed inside the generations base directory.",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent iterations (default: unlimited)",
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=list(AVAILABLE_MODELS.keys()),
        default=DEFAULT_MODEL,
        help=f"Model for orchestrator (sub-agents have fixed models: coding=sonnet, others=haiku) (default: {DEFAULT_MODEL})",
    )

    return parser.parse_args()


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, 1 for error, 130 for keyboard interrupt)
    """
    args: argparse.Namespace = parse_args()

    # Claude Agent SDK uses local CLI auth automatically
    # No need to check for CLAUDE_CODE_OAUTH_TOKEN

    # Check for Arcade API key
    arcade_key: str | None = os.environ.get("ARCADE_API_KEY")
    if not arcade_key:
        print("Error: ARCADE_API_KEY environment variable not set")
        print("\nGet your API key from: https://api.arcade.dev/dashboard/api-keys")
        print("Or run: arcade login")
        print("\nThen set it:")
        print("  export ARCADE_API_KEY='arc_xxxxxxxxxxxxx'")
        return 1

    # Determine the generations base directory
    generations_base: Path = args.generations_base or DEFAULT_GENERATIONS_BASE
    if not generations_base.is_absolute():
        # Make relative paths absolute from current working directory
        generations_base = Path.cwd() / generations_base

    # Resolve project directory
    project_dir: Path = args.project_dir
    if project_dir.is_absolute():
        # User specified an absolute path - use it directly
        pass
    else:
        # Place relative paths inside the generations base directory
        # Strip any leading ./ for cleaner paths
        project_name = str(project_dir).lstrip("./")
        project_dir = generations_base / project_name

    # Ensure the generations base directory exists
    generations_base.mkdir(parents=True, exist_ok=True)

    # Resolve model short name to full model ID
    model_id: str = AVAILABLE_MODELS[args.model]

    # Run the agent
    try:
        asyncio.run(
            run_autonomous_agent(
                project_dir=project_dir,
                model=model_id,
                max_iterations=args.max_iterations,
            )
        )
        return 0
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("To resume, run the same command again")
        return 130  # Standard Unix exit code for SIGINT
    except Exception as e:
        error_type: str = type(e).__name__
        print(f"\nFatal error ({error_type}): {e}")
        print("\nCommon causes:")
        print("  1. Missing or invalid ARCADE_API_KEY in .env")
        print("  2. Invalid project directory path or permissions")
        print("  3. Missing Claude authentication (run: claude login)")
        print("  4. MCP server installation issues (puppeteer-mcp-server)")
        print("\nFull error details:")
        raise


if __name__ == "__main__":
    sys.exit(main())
