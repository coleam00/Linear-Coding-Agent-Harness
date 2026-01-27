"""
Progress Tracking Utilities
===========================

Functions for tracking and displaying progress of the autonomous coding agent.
Progress is tracked via Linear issues, with local state cached in .linear_project.json.
"""

import json
from pathlib import Path
from typing import TypedDict

# Local marker file to track Linear project initialization
LINEAR_PROJECT_MARKER: str = ".linear_project.json"


class LinearProjectState(TypedDict, total=False):
    """Structure of the .linear_project.json state file."""

    initialized: bool
    created_at: str
    team_id: str
    project_id: str
    project_name: str
    meta_issue_id: str
    total_issues: int
    notes: str


def load_linear_project_state(project_dir: Path) -> LinearProjectState | None:
    """
    Load the Linear project state from the marker file.

    Args:
        project_dir: Directory containing .linear_project.json

    Returns:
        Project state dict or None if not initialized

    Raises:
        ValueError: If the state file exists but is corrupted or malformed

    Note:
        Returns None if file doesn't exist. Raises ValueError if file exists
        but cannot be parsed, to prevent silent state corruption.
    """
    marker_file: Path = project_dir / LINEAR_PROJECT_MARKER

    if not marker_file.exists():
        return None

    try:
        with open(marker_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Corrupted state file at {marker_file}: {e}\n"
            f"Delete the file to restart initialization, or restore from backup."
        ) from e
    except IOError as e:
        raise ValueError(
            f"Cannot read state file at {marker_file}: {e}\n"
            f"Check file permissions."
        ) from e

    # Validate structure
    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid state file at {marker_file}: expected object, got {type(data).__name__}"
        )

    return data  # type: ignore[return-value]


def is_linear_initialized(project_dir: Path) -> bool:
    """
    Check if Linear project has been initialized.

    Args:
        project_dir: Directory to check

    Returns:
        True if .linear_project.json exists and is valid with initialized=True
    """
    try:
        state = load_linear_project_state(project_dir)
        return state is not None and state.get("initialized", False)
    except ValueError:
        # Corrupted state file - treat as not initialized but log warning
        print(f"Warning: Corrupted state file in {project_dir}, treating as uninitialized")
        return False


def print_session_header(session_num: int, is_initializer: bool) -> None:
    """Print a formatted header for the session."""
    session_type: str = "ORCHESTRATOR (init)" if is_initializer else "ORCHESTRATOR (continue)"

    print("\n" + "=" * 70)
    print(f"  SESSION {session_num}: {session_type}")
    print("=" * 70)
    print()


def print_progress_summary(project_dir: Path) -> None:
    """
    Print a summary of current progress.

    Since actual progress is tracked in Linear, this reads the local
    state file for cached information. The agent updates Linear directly
    and reports progress in session comments.
    """
    try:
        state = load_linear_project_state(project_dir)
    except ValueError as e:
        print(f"\nProgress: Error loading state - {e}")
        return

    if state is None:
        print("\nProgress: Linear project not yet initialized")
        return

    total: int = state.get("total_issues", 0)
    meta_issue: str = state.get("meta_issue_id", "unknown")

    print(f"\nLinear Project Status:")
    print(f"  Total issues created: {total}")
    print(f"  META issue ID: {meta_issue}")
    print(f"  (Check Linear for current Done/In Progress/Todo counts)")
