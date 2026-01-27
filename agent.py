"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
"""

import asyncio
import traceback
from pathlib import Path
from typing import Literal, NamedTuple

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from client import create_client
from progress import print_session_header, print_progress_summary, is_linear_initialized
from prompts import (
    get_initializer_prompt,
    get_coding_prompt,
    get_initializer_task,
    get_continuation_task,
    copy_spec_to_project,
)


# Configuration
AUTO_CONTINUE_DELAY_SECONDS: int = 3


# Type-safe literal union - no runtime overhead
SessionStatus = Literal["continue", "error"]

# Constants for code clarity
SESSION_CONTINUE: SessionStatus = "continue"
SESSION_ERROR: SessionStatus = "error"


class SessionResult(NamedTuple):
    """Result of running an agent session.

    Attributes:
        status: "continue" if session completed normally, "error" if exception occurred
        response: Response text from the agent, or error message if status is "error"
    """

    status: SessionStatus
    response: str


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
) -> SessionResult:
    """
    Run a single agent session using Claude Agent SDK.

    Args:
        client: Claude SDK client
        message: The prompt to send
        project_dir: Project directory path

    Returns:
        SessionResult with status and response text:
        - status=CONTINUE: Normal completion, agent can continue
        - status=ERROR: Exception occurred, will retry with fresh session
    """
    print("Sending prompt to Claude Agent SDK...\n")

    try:
        # Send the query
        await client.query(message)

        # Collect response text and show tool use
        response_text: str = ""
        async for msg in client.receive_response():
            # Handle AssistantMessage (text and tool use)
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        print(f"\n[Tool: {block.name}]", flush=True)
                        input_str: str = str(block.input)
                        if len(input_str) > 200:
                            print(f"   Input: {input_str[:200]}...", flush=True)
                        else:
                            print(f"   Input: {input_str}", flush=True)

            # Handle UserMessage (tool results)
            elif isinstance(msg, UserMessage):
                for block in msg.content:
                    if isinstance(block, ToolResultBlock):
                        result_content = block.content
                        is_error: bool = bool(block.is_error) if block.is_error else False

                        # Check if command was blocked by security hook
                        if "blocked" in str(result_content).lower():
                            print(f"   [BLOCKED] {result_content}", flush=True)
                        elif is_error:
                            # Show errors (truncated)
                            error_str: str = str(result_content)[:500]
                            print(f"   [Error] {error_str}", flush=True)
                        else:
                            # Tool succeeded - just show brief confirmation
                            print("   [Done]", flush=True)

        print("\n" + "-" * 70 + "\n")
        return SessionResult(status=SESSION_CONTINUE, response=response_text)

    except ConnectionError as e:
        print(f"\nNetwork error during agent session: {e}")
        print("Check your internet connection and try again.")
        traceback.print_exc()
        return SessionResult(status=SESSION_ERROR, response=str(e))

    except TimeoutError as e:
        print(f"\nTimeout during agent session: {e}")
        print("The API request timed out. Will retry with fresh session.")
        traceback.print_exc()
        return SessionResult(status=SESSION_ERROR, response=str(e))

    except Exception as e:
        error_type: str = type(e).__name__
        error_msg: str = str(e)

        print(f"\nError during agent session ({error_type}): {error_msg}")
        print("\nFull traceback:")
        traceback.print_exc()

        # Provide actionable guidance based on error type
        error_lower = error_msg.lower()
        if "auth" in error_lower or "token" in error_lower:
            print("\nThis appears to be an authentication error.")
            print("Check your CLAUDE_CODE_OAUTH_TOKEN environment variable.")
        elif "rate" in error_lower or "limit" in error_lower:
            print("\nThis appears to be a rate limit error.")
            print("The agent will retry after a delay.")
        elif "linear" in error_lower:
            print("\nThis appears to be a Linear API error.")
            print("Check your LINEAR_API_KEY and Linear project access.")
        elif "arcade" in error_lower or "mcp" in error_lower:
            print("\nThis appears to be an Arcade MCP Gateway error.")
            print("Check your ARCADE_API_KEY and ARCADE_GATEWAY_SLUG configuration.")
        else:
            # Unexpected error type - make this visible
            print(f"\nUnexpected error type: {error_type}")
            print("This may indicate a bug or an unhandled edge case.")
            print("The agent will retry, but please report this if it persists.")

        return SessionResult(status=SESSION_ERROR, response=error_msg)


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: int | None = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)

    Raises:
        ValueError: If max_iterations is not positive
    """
    if max_iterations is not None and max_iterations < 1:
        raise ValueError(f"max_iterations must be positive, got {max_iterations}")

    print("\n" + "=" * 70)
    print("  AUTONOMOUS CODING AGENT DEMO")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited (will run until completion)")
    print()

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Check if this is a fresh start or continuation
    # We use .linear_project.json as the marker for initialization
    is_first_run: bool = not is_linear_initialized(project_dir)

    if is_first_run:
        print("Fresh start - will use initializer agent")
        print()
        print("=" * 70)
        print("  NOTE: First session takes 10-20+ minutes!")
        print("  The agent is creating 50 Linear issues and setting up the project.")
        print("  This may appear to hang - it's working. Watch for [Tool: ...] output.")
        print("=" * 70)
        print()
        # Copy the app spec into the project directory for the agent to read
        copy_spec_to_project(project_dir)
    else:
        print("Continuing existing project (Linear initialized)")
        print_progress_summary(project_dir)

    iteration: int = 0

    while True:
        iteration += 1

        # Check max iterations
        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            print("To continue, run the script again without --max-iterations")
            break

        # Print session header
        print_session_header(iteration, is_first_run)

        # Prevents context window exhaustion in long-running loops
        client: ClaudeSDKClient = create_client(project_dir, model)

        # Choose task message based on session type
        # Task messages provide high-level objectives that the agent interprets
        # Agent will delegate work to specialized sub-agents (linear, coding, github, slack)
        if is_first_run:
            prompt: str = get_initializer_task(project_dir)
            is_first_run = False  # Only use initializer once
        else:
            prompt = get_continuation_task(project_dir)

        # Run session with async context manager
        # Initialize result to satisfy type checker (will be reassigned in try or except)
        result: SessionResult = SessionResult(status=SESSION_ERROR, response="uninitialized")
        try:
            async with client:
                result = await run_agent_session(client, prompt, project_dir)
        except ConnectionError as e:
            print(f"\nFailed to connect to Claude SDK: {e}")
            print("Check your authentication and network connection.")
            traceback.print_exc()
            result = SessionResult(status=SESSION_ERROR, response=str(e))
        except Exception as e:
            error_type: str = type(e).__name__
            print(f"\nUnexpected error in session context ({error_type}): {e}")
            print("This error occurred during SDK client initialization or cleanup.")
            print("This may indicate an SDK bug, resource exhaustion, or configuration issue.")
            traceback.print_exc()
            result = SessionResult(status=SESSION_ERROR, response=str(e))

        # Handle status
        if result.status == SESSION_CONTINUE:
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir)
        elif result.status == SESSION_ERROR:
            print("\nSession encountered an error")
            print("Will retry with a fresh session...")

        # Always wait before next iteration
        await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        # Small delay between sessions
        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nProject directory: {project_dir}")
    print_progress_summary(project_dir)

    # Print instructions for running the generated application
    print("\n" + "-" * 70)
    print("  TO RUN THE GENERATED APPLICATION:")
    print("-" * 70)
    print(f"\n  cd {project_dir.resolve()}")
    print("  ./init.sh           # Run the setup script")
    print("  # Or manually:")
    print("  npm install && npm run dev")
    print("\n  Then open http://localhost:3000 (or check init.sh for the URL)")
    print("-" * 70)

    print("\nDone!")
