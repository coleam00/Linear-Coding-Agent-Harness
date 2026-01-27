"""
Orchestrator Session Runner
===========================

Runs orchestrated sessions where the main agent delegates to specialized agents.
"""

import traceback
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    TextBlock,
    ToolUseBlock,
)

from agent import SessionResult, SESSION_CONTINUE, SESSION_ERROR


async def run_orchestrated_session(
    client: ClaudeSDKClient,
    project_dir: Path,
) -> SessionResult:
    """
    Run an orchestrated session with an initial task prompt.

    Args:
        client: Claude SDK client (must already be configured with orchestrator
            prompt and agent definitions)
        project_dir: Project directory path, included in the initial message to
            tell the orchestrator where to work

    Returns:
        SessionResult with status and response text:
        - status="continue": Normal completion, agent can continue
        - status="error": Exception occurred during orchestration

    The orchestrator will use the Task tool to delegate to specialized agents
    (linear, coding, github, slack) based on the work needed.
    """
    initial_message = f"""
    Start a new session. Your working directory is: {project_dir}

    Begin by:
    1. Reading .linear_project.json to understand project state
    2. Checking Linear for current issue status
    3. Deciding what to work on next
    4. Delegating to appropriate agents
    """

    print("Starting orchestrated session...\n")

    try:
        await client.query(initial_message)

        response_text: str = ""
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        print(f"\n[Tool: {block.name}]", flush=True)

        print("\n" + "-" * 70 + "\n")
        return SessionResult(status=SESSION_CONTINUE, response=response_text)

    except ConnectionError as e:
        print(f"\nNetwork error in orchestrated session: {e}")
        print("Check your internet connection and Arcade MCP gateway availability.")
        traceback.print_exc()
        return SessionResult(status=SESSION_ERROR, response=str(e))

    except TimeoutError as e:
        print(f"\nTimeout in orchestrated session: {e}")
        print("The orchestration timed out. This may be due to slow MCP responses.")
        traceback.print_exc()
        return SessionResult(status=SESSION_ERROR, response=str(e))

    except Exception as e:
        error_type: str = type(e).__name__
        error_msg: str = str(e)

        print(f"\nError in orchestrated session ({error_type}): {error_msg}")
        print("\nFull traceback:")
        traceback.print_exc()

        # Provide actionable guidance based on error type
        error_lower = error_msg.lower()
        if "arcade" in error_lower or "mcp" in error_lower:
            print("\nThis appears to be an Arcade MCP Gateway error.")
            print("Check your ARCADE_API_KEY and ARCADE_GATEWAY_SLUG configuration.")
        elif "agent" in error_lower or "delegation" in error_lower:
            print("\nThis appears to be an agent delegation error.")
            print("Check the agent definitions and ensure all required tools are authorized.")
        elif "auth" in error_lower or "token" in error_lower:
            print("\nThis appears to be an authentication error.")
            print("Check your CLAUDE_CODE_OAUTH_TOKEN environment variable.")
        else:
            # Unexpected error type - make this visible
            print(f"\nUnexpected error type: {error_type}")
            print("This may indicate a bug or an unhandled edge case.")
            print("The orchestrator will retry, but please report this if it persists.")

        return SessionResult(status=SESSION_ERROR, response=error_msg)
