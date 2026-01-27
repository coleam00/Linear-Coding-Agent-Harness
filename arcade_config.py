"""
Arcade MCP Gateway Configuration
================================

Configuration for the Arcade MCP Gateway integration.
Customize the gateway slug and available tools here.

Setup:
1. Create an MCP Gateway at https://api.arcade.dev/dashboard/mcp-gateways
2. Add Linear, GitHub, and/or Slack tools to your gateway
3. Set ARCADE_GATEWAY_SLUG in your .env file
4. Run: python authorize_arcade.py
"""

import os
from typing import Literal, TypedDict


class ArcadeMcpConfig(TypedDict):
    """Configuration for Arcade MCP server."""

    type: Literal["http"]
    url: str
    headers: dict[str, str]


# Gateway configuration from environment
ARCADE_GATEWAY_SLUG: str = os.environ.get("ARCADE_GATEWAY_SLUG", "")
ARCADE_API_KEY: str = os.environ.get("ARCADE_API_KEY", "")
ARCADE_USER_ID: str = os.environ.get("ARCADE_USER_ID", "agent@local")

# Base URL for Arcade MCP Gateways
ARCADE_MCP_BASE_URL: str = "https://api.arcade.dev/mcp"

# Permission wildcard for all Arcade tools
ARCADE_TOOLS_PERMISSION: str = "mcp__arcade__*"


# =============================================================================
# Tool Definitions
# =============================================================================
# These are the tools available through the Arcade MCP Gateway.
# Tool names use the format: mcp__arcade__<Provider>_<ToolName>

# GitHub tools (46 tools) - Per Arcade docs
# Note: No CreateRepository tool - repos must be created via GitHub web UI or API
ARCADE_GITHUB_TOOLS: list[str] = [
    # User context
    "mcp__arcade__Github_WhoAmI",
    "mcp__arcade__Github_GetUserRecentActivity",
    "mcp__arcade__Github_GetUserOpenItems",
    "mcp__arcade__Github_GetReviewWorkload",
    "mcp__arcade__Github_GetNotificationSummary",   # Requires Classic PAT
    "mcp__arcade__Github_ListNotifications",        # Requires Classic PAT
    # Repository
    "mcp__arcade__Github_GetRepository",
    "mcp__arcade__Github_SearchMyRepos",
    "mcp__arcade__Github_ListOrgRepositories",
    "mcp__arcade__Github_ListRepositoryCollaborators",
    "mcp__arcade__Github_ListRepositoryActivities",
    "mcp__arcade__Github_CountStargazers",
    "mcp__arcade__Github_ListStargazers",
    "mcp__arcade__Github_SetStarred",
    # Branches & Files
    "mcp__arcade__Github_CreateBranch",
    "mcp__arcade__Github_GetFileContents",
    "mcp__arcade__Github_CreateOrUpdateFile",       # Fixed: was CreateFile
    "mcp__arcade__Github_UpdateFileLines",
    # Issues
    "mcp__arcade__Github_ListIssues",
    "mcp__arcade__Github_GetIssue",
    "mcp__arcade__Github_CreateIssue",
    "mcp__arcade__Github_UpdateIssue",
    "mcp__arcade__Github_CreateIssueComment",
    # Pull Requests
    "mcp__arcade__Github_ListPullRequests",
    "mcp__arcade__Github_GetPullRequest",
    "mcp__arcade__Github_CreatePullRequest",
    "mcp__arcade__Github_UpdatePullRequest",
    "mcp__arcade__Github_MergePullRequest",
    "mcp__arcade__Github_ManagePullRequest",        # Added: update PR properties
    "mcp__arcade__Github_CheckPullRequestMergeStatus",
    "mcp__arcade__Github_ListPullRequestCommits",
    # PR Reviews & Reviewers
    "mcp__arcade__Github_AssignPullRequestUser",
    "mcp__arcade__Github_ManagePullRequestReviewers",
    "mcp__arcade__Github_SubmitPullRequestReview",
    "mcp__arcade__Github_CreateReviewComment",
    "mcp__arcade__Github_CreateReplyForReviewComment",
    "mcp__arcade__Github_ListReviewCommentsOnPullRequest",
    "mcp__arcade__Github_ListReviewCommentsInARepository",
    "mcp__arcade__Github_ResolveReviewThread",
    # Labels
    "mcp__arcade__Github_ListRepositoryLabels",
    "mcp__arcade__Github_ManageLabels",
    # Projects V2
    "mcp__arcade__Github_ListProjects",
    "mcp__arcade__Github_ListProjectFields",
    "mcp__arcade__Github_ListProjectItems",
    "mcp__arcade__Github_SearchProjectItem",
    "mcp__arcade__Github_UpdateProjectItem",        # Added: update project item fields
]

# Slack tools (8 tools) - Uses Slack.* prefix per Arcade docs
# Channel creation not supported - agent must use existing channels
ARCADE_SLACK_TOOLS: list[str] = [
    # Identity & Users
    "mcp__arcade__Slack_WhoAmI",
    "mcp__arcade__Slack_GetUsersInfo",
    "mcp__arcade__Slack_ListUsers",
    # Channels/Conversations - Read
    "mcp__arcade__Slack_ListConversations",
    "mcp__arcade__Slack_GetConversationMetadata",
    "mcp__arcade__Slack_GetUsersInConversation",
    "mcp__arcade__Slack_GetMessages",
    # Messaging
    "mcp__arcade__Slack_SendMessage",
]

# Linear tools (39 tools)
ARCADE_LINEAR_TOOLS: list[str] = [
    "mcp__arcade__Linear_WhoAmI",
    "mcp__arcade__Linear_GetNotifications",
    "mcp__arcade__Linear_GetRecentActivity",
    "mcp__arcade__Linear_GetTeam",
    "mcp__arcade__Linear_ListTeams",
    "mcp__arcade__Linear_ListIssues",
    "mcp__arcade__Linear_GetIssue",
    "mcp__arcade__Linear_CreateIssue",
    "mcp__arcade__Linear_UpdateIssue",
    "mcp__arcade__Linear_ArchiveIssue",
    "mcp__arcade__Linear_TransitionIssueState",
    "mcp__arcade__Linear_CreateIssueRelation",
    "mcp__arcade__Linear_ManageIssueSubscription",
    "mcp__arcade__Linear_ListComments",
    "mcp__arcade__Linear_AddComment",
    "mcp__arcade__Linear_UpdateComment",
    "mcp__arcade__Linear_ReplyToComment",
    "mcp__arcade__Linear_ListProjects",
    "mcp__arcade__Linear_GetProject",
    "mcp__arcade__Linear_GetProjectDescription",
    "mcp__arcade__Linear_CreateProject",
    "mcp__arcade__Linear_UpdateProject",
    "mcp__arcade__Linear_ArchiveProject",
    "mcp__arcade__Linear_CreateProjectUpdate",
    "mcp__arcade__Linear_ListProjectComments",
    "mcp__arcade__Linear_AddProjectComment",
    "mcp__arcade__Linear_ReplyToProjectComment",
    "mcp__arcade__Linear_ListInitiatives",
    "mcp__arcade__Linear_GetInitiative",
    "mcp__arcade__Linear_GetInitiativeDescription",
    "mcp__arcade__Linear_CreateInitiative",
    "mcp__arcade__Linear_UpdateInitiative",
    "mcp__arcade__Linear_ArchiveInitiative",
    "mcp__arcade__Linear_AddProjectToInitiative",
    "mcp__arcade__Linear_ListCycles",
    "mcp__arcade__Linear_GetCycle",
    "mcp__arcade__Linear_ListLabels",
    "mcp__arcade__Linear_ListWorkflowStates",
    "mcp__arcade__Linear_LinkGithubToIssue",
]

# All Arcade tools combined
ALL_ARCADE_TOOLS: list[str] = (
    ARCADE_LINEAR_TOOLS + ARCADE_GITHUB_TOOLS + ARCADE_SLACK_TOOLS
)


def get_arcade_mcp_config() -> ArcadeMcpConfig:
    """
    Get the Arcade MCP server configuration.

    Returns:
        MCP server config dict for use in ClaudeAgentOptions.mcp_servers

    Raises:
        ValueError: If required environment variables are not set
    """
    if not ARCADE_API_KEY:
        raise ValueError(
            "ARCADE_API_KEY environment variable not set.\n"
            "Get your API key from: https://api.arcade.dev/dashboard/api-keys"
        )

    if not ARCADE_GATEWAY_SLUG:
        raise ValueError(
            "ARCADE_GATEWAY_SLUG environment variable not set.\n"
            "Create a gateway at: https://api.arcade.dev/dashboard/mcp-gateways\n"
            "Then set ARCADE_GATEWAY_SLUG=your-gateway-slug in .env"
        )

    return ArcadeMcpConfig(
        type="http",
        url=f"{ARCADE_MCP_BASE_URL}/{ARCADE_GATEWAY_SLUG}",
        headers={
            "Authorization": f"Bearer {ARCADE_API_KEY}",
            "Arcade-User-ID": ARCADE_USER_ID,
        },
    )


def validate_arcade_config() -> None:
    """
    Validate the Arcade configuration.

    Raises:
        ValueError: If configuration is invalid
    """
    if not ARCADE_API_KEY:
        raise ValueError("ARCADE_API_KEY not set")

    if not ARCADE_API_KEY.startswith("arc_"):
        raise ValueError(
            "ARCADE_API_KEY appears invalid. It should start with 'arc_'\n"
            "Get your API key from: https://api.arcade.dev/dashboard/api-keys"
        )

    if not ARCADE_GATEWAY_SLUG:
        raise ValueError("ARCADE_GATEWAY_SLUG not set")


def print_arcade_config() -> None:
    """Print the current Arcade configuration for debugging."""
    print("Arcade Configuration:")
    print(f"  Gateway: {ARCADE_GATEWAY_SLUG or '(not set)'}")
    print(f"  API Key: {ARCADE_API_KEY[:20]}..." if ARCADE_API_KEY else "  API Key: (not set)")
    print(f"  User ID: {ARCADE_USER_ID}")
    print(f"  URL: {ARCADE_MCP_BASE_URL}/{ARCADE_GATEWAY_SLUG}")
    print(f"  Tools: {len(ALL_ARCADE_TOOLS)} available")


# =============================================================================
# Tool Getters for Multi-Agent Architecture
# =============================================================================


def get_linear_tools() -> list[str]:
    """Get Linear-only tools for Linear agent."""
    return ARCADE_LINEAR_TOOLS


def get_github_tools() -> list[str]:
    """Get GitHub-only tools for GitHub agent."""
    return ARCADE_GITHUB_TOOLS


def get_slack_tools() -> list[str]:
    """Get Slack-only tools for Slack agent."""
    return ARCADE_SLACK_TOOLS


def get_coding_tools() -> list[str]:
    """Get tools for coding agent (file ops + Puppeteer)."""
    # Define inline to avoid circular dependency with client.py
    builtin_tools = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
    puppeteer_tools = [
        "mcp__puppeteer__puppeteer_navigate",
        "mcp__puppeteer__puppeteer_screenshot",
        "mcp__puppeteer__puppeteer_click",
        "mcp__puppeteer__puppeteer_fill",
        "mcp__puppeteer__puppeteer_select",
        "mcp__puppeteer__puppeteer_hover",
        "mcp__puppeteer__puppeteer_evaluate",
    ]
    return builtin_tools + puppeteer_tools
