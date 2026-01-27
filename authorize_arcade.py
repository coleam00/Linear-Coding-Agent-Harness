#!/usr/bin/env python3
"""
Authorize Arcade Services
=========================

Run this script to connect your Linear, GitHub, and Slack accounts via OAuth.

Usage:
    python authorize_arcade.py          # Authorize all services
    python authorize_arcade.py linear   # Authorize Linear only
    python authorize_arcade.py github   # Authorize GitHub only
    python authorize_arcade.py slack    # Authorize Slack only
"""

import sys
import traceback
from dotenv import load_dotenv
import os

load_dotenv()

from arcadepy import Arcade

# Tools that require write authorization per service
# Based on actual agent prompt requirements
SERVICES = {
    "linear": {
        "verify_tool": "Linear.WhoAmI",
        "extract_name": lambda o: o.get("name", str(o)),
        # All write tools the Linear agent actually uses
        "auth_tools": [
            "Linear.CreateProject",      # First run: create project
            "Linear.CreateIssue",        # First run: create 5-6 issues + META
            "Linear.UpdateIssue",        # Update issue fields
            "Linear.TransitionIssueState",  # Move Todo→InProgress→Done
            "Linear.AddComment",         # Add implementation details
        ],
    },
    "github": {
        "verify_tool": "Github.WhoAmI",
        "extract_name": lambda o: o.get("profile", {}).get("name") or o.get("profile", {}).get("login") or str(o),
        # All write tools the GitHub agent actually uses
        "auth_tools": [
            "Github.CreateBranch",       # Create feature branches
            "Github.CreatePullRequest",  # Open PRs
            "Github.UpdatePullRequest",  # Update PR details
            "Github.MergePullRequest",   # Merge PRs
            "Github.CreateIssueComment", # Comment on PRs
        ],
    },
    "slack": {
        "verify_tool": "Slack.WhoAmI",
        "extract_name": lambda o: o.get("name") or o.get("real_name") or str(o),
        # Note: Channel creation not supported by Arcade's Slack integration
        # Agent must use existing channels
        "auth_tools": [
            "Slack.SendMessage",  # Send to channel by name, ID, or user
        ],
    },
}


def authorize_service(client: Arcade, user_id: str, service: str) -> bool:
    """Authorize all write tools for a service and return True if all successful."""
    config = SERVICES[service]
    auth_tools = config["auth_tools"]  # All tools that require write permissions
    verify_tool = config["verify_tool"]  # Tool to verify connection
    extract_name = config["extract_name"]

    print(f"\n{'='*60}")
    print(f"  {service.upper()} ({len(auth_tools)} tools to authorize)")
    print(f"{'='*60}")

    all_authorized = True

    for i, auth_tool in enumerate(auth_tools, 1):
        print(f"\n[{i}/{len(auth_tools)}] Authorizing: {auth_tool}")

        auth_response = client.tools.authorize(
            tool_name=auth_tool,
            user_id=user_id,
        )

        if auth_response.status == "completed":
            print(f"  Already authorized")
        else:
            print(f"  Authorization required. Click this link:\n")
            print(f"    {auth_response.url}")
            print("\n  Waiting for authorization...")

            try:
                if auth_response.id is None:
                    print(f"  Error: No authorization ID returned")
                    all_authorized = False
                    continue
                client.auth.wait_for_completion(auth_response.id)
                print(f"  Authorized!")
            except KeyboardInterrupt:
                print(f"\n\nAuthorization interrupted by user.")
                print(f"Stopped at: {auth_tool}")
                print(f"\nTo resume, run: python authorize_arcade.py {service}")
                raise  # Let KeyboardInterrupt propagate to exit cleanly

    # Verify connection
    if all_authorized:
        print(f"\nVerifying {service.title()} connection...")
        try:
            result = client.tools.execute(
                tool_name=verify_tool,
                input={},
                user_id=user_id,
            )
            output = result.output.value if result.output else None
            name = extract_name(output) if isinstance(output, dict) else str(output)
            print(f"Connected as: {name}")
        except ConnectionError as e:
            print(f"Verification failed due to network error: {e}")
            print("Check your internet connection and try again.")
            all_authorized = False
        except Exception as e:
            error_type: str = type(e).__name__
            print(f"Verification failed ({error_type}): {e}")
            print(f"\nFailed while verifying {service.title()} with tool: {verify_tool}")
            print("\nFull error details:")
            traceback.print_exc()
            print("\nThis may indicate:")
            print("  - Invalid API credentials")
            print("  - Expired OAuth token (re-run authorization)")
            print("  - MCP gateway connectivity issues")
            print(f"\nCheck your configuration at: https://api.arcade.dev/dashboard/mcp-gateways")
            all_authorized = False

    return all_authorized


def main() -> None:
    """
    Main entry point for Arcade authorization.

    Exits with:
        0: All authorizations complete
        1: Error or incomplete authorizations
    """
    api_key = os.environ.get("ARCADE_API_KEY")
    user_id = os.environ.get("ARCADE_USER_ID", "agent@local")

    if not api_key:
        print("Error: ARCADE_API_KEY not set in .env")
        sys.exit(1)

    # Parse args
    if len(sys.argv) > 1:
        services = [s.lower() for s in sys.argv[1:] if s.lower() in SERVICES]
        if not services:
            print(f"Unknown service. Available: {', '.join(SERVICES.keys())}")
            sys.exit(1)
    else:
        services = list(SERVICES.keys())

    print("Arcade Service Authorization")
    print(f"User: {user_id}")
    print(f"API Key: {api_key[:20]}...")
    print(f"Services: {', '.join(services)}")

    client = Arcade(api_key=api_key)

    results = {}
    for service in services:
        results[service] = authorize_service(client, user_id, service)

    # Summary
    print(f"\n{'='*60}")
    print("  AUTHORIZATION SUMMARY")
    print(f"{'='*60}")
    total_tools = 0
    for service, success in results.items():
        tool_count = len(SERVICES[service]["auth_tools"])
        total_tools += tool_count
        status = f"OK ({tool_count} tools)" if success else f"INCOMPLETE ({tool_count} tools)"
        print(f"  {service.title()}: {status}")

    print(f"\n  Total: {total_tools} write tools across {len(results)} services")

    if all(results.values()):
        print("\n  All authorizations complete! You can now run the agent.")
    else:
        print("\n  Some authorizations are incomplete. Re-run to complete them.")


if __name__ == "__main__":
    main()
