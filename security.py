"""
Security Hooks for Autonomous Coding Agent
==========================================

Pre-tool-use hooks that validate bash commands for security.
Uses an allowlist approach - only explicitly permitted commands can run.
"""

import os
import re
import shlex
from typing import Any, NamedTuple

from claude_agent_sdk import PreToolUseHookInput
from claude_agent_sdk.types import HookContext, SyncHookJSONOutput


class ValidationResult(NamedTuple):
    """Result of validating a command."""

    allowed: bool
    reason: str = ""




# Allowed commands for development tasks
# Minimal set needed for the autonomous coding demo
ALLOWED_COMMANDS: set[str] = {
    # File inspection
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "grep",
    "find",
    # File operations (agent uses SDK tools for most file ops, but these are needed occasionally)
    "cp",
    "mv",
    "mkdir",
    "rm",  # For cleanup; validated separately to prevent dangerous operations
    "touch",
    "chmod",  # For making scripts executable; validated separately
    "unzip",  # For extracting archives (e.g., Chrome for Puppeteer)
    # Directory navigation
    "pwd",
    "cd",
    # Text output
    "echo",
    "printf",
    # HTTP/Network (for testing endpoints)
    "curl",
    # Environment inspection
    "which",
    "env",
    # Python (for file creation scripts)
    "python",
    "python3",
    # Node.js development
    "npm",
    "npx",
    "node",
    # Version control
    "git",
    # Process management
    "ps",
    "lsof",
    "sleep",
    "pkill",  # For killing dev servers; validated separately
    # Script execution
    "init.sh",  # Init scripts; validated separately
}

# Commands that need additional validation even when in the allowlist
COMMANDS_NEEDING_EXTRA_VALIDATION: set[str] = {"pkill", "chmod", "init.sh", "rm"}


def split_command_segments(command_string: str) -> list[str]:
    """
    Split a compound command into individual command segments.

    Handles command chaining operators (&&, ||, ;). Pipes are handled separately
    by extract_commands(), which parses tokens within each segment and treats
    "|" as indicating a new command follows.

    Note: Semicolon splitting uses a simple regex pattern that may not correctly
    handle all edge cases with nested quotes. For security validation, this is
    acceptable as malformed commands will fail parsing and be blocked.

    Args:
        command_string: The full shell command

    Returns:
        List of individual command segments
    """
    # Split on && and || while preserving the ability to handle each segment
    # This regex splits on && or || that aren't inside quotes
    segments: list[str] = re.split(r"\s*(?:&&|\|\|)\s*", command_string)

    # Further split on semicolons
    result: list[str] = []
    for segment in segments:
        sub_segments: list[str] = re.split(r'(?<!["\'])\s*;\s*(?!["\'])', segment)
        for sub in sub_segments:
            sub = sub.strip()
            if sub:
                result.append(sub)

    return result


def extract_commands(command_string: str) -> list[str]:
    """
    Extract command names from a shell command string.

    Handles pipes, command chaining (&&, ||, ;), and subshells.
    Returns the base command names (without paths).

    Args:
        command_string: The full shell command

    Returns:
        List of command names found in the string
    """
    commands: list[str] = []

    # shlex doesn't treat ; as a separator, so we need to pre-process
    # Split on semicolons that aren't inside quotes (simple heuristic)
    # This handles common cases like "echo hello; ls"
    segments: list[str] = re.split(r'(?<!["\'])\s*;\s*(?!["\'])', command_string)

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        try:
            tokens: list[str] = shlex.split(segment)
        except ValueError:
            # Malformed command (unclosed quotes, etc.)
            # Return empty to trigger block (fail-safe)
            return []

        if not tokens:
            continue

        # Track when we expect a command vs arguments
        expect_command: bool = True

        for token in tokens:
            # Shell operators indicate a new command follows
            if token in ("|", "||", "&&", "&"):
                expect_command = True
                continue

            # Skip shell keywords that precede commands
            if token in (
                "if",
                "then",
                "else",
                "elif",
                "fi",
                "for",
                "while",
                "until",
                "do",
                "done",
                "case",
                "esac",
                "in",
                "!",
                "{",
                "}",
            ):
                continue

            # Skip flags/options
            if token.startswith("-"):
                continue

            # Skip variable assignments (VAR=value)
            if "=" in token and not token.startswith("="):
                continue

            if expect_command:
                # Extract the base command name (handle paths like /usr/bin/python)
                cmd: str = os.path.basename(token)
                commands.append(cmd)
                expect_command = False

    return commands


def validate_pkill_command(command_string: str) -> ValidationResult:
    """
    Validate pkill commands - only allow killing dev-related processes.

    Uses shlex to parse the command, avoiding regex bypass vulnerabilities.

    Args:
        command_string: The pkill command to validate

    Returns:
        ValidationResult with allowed status and reason if blocked
    """
    # Allowed process names for pkill
    allowed_process_names: set[str] = {
        "node",
        "npm",
        "npx",
        "vite",
        "next",
    }

    try:
        tokens: list[str] = shlex.split(command_string)
    except ValueError:
        return ValidationResult(allowed=False, reason="Could not parse pkill command")

    if not tokens:
        return ValidationResult(allowed=False, reason="Empty pkill command")

    # Separate flags from arguments
    args: list[str] = []
    for token in tokens[1:]:
        if not token.startswith("-"):
            args.append(token)

    if not args:
        return ValidationResult(allowed=False, reason="pkill requires a process name")

    # The target is typically the last non-flag argument
    target: str = args[-1]

    # For -f flag (full command line match), extract the first word as process name
    # e.g., "pkill -f 'node server.js'" -> target is "node server.js", process is "node"
    if " " in target:
        target = target.split()[0]

    if target in allowed_process_names:
        return ValidationResult(allowed=True)
    return ValidationResult(
        allowed=False,
        reason=f"pkill only allowed for dev processes: {allowed_process_names}",
    )


def validate_chmod_command(command_string: str) -> ValidationResult:
    """
    Validate chmod commands - only allow making files executable with +x.

    Args:
        command_string: The chmod command to validate

    Returns:
        ValidationResult with allowed status and reason if blocked
    """
    try:
        tokens: list[str] = shlex.split(command_string)
    except ValueError:
        return ValidationResult(allowed=False, reason="Could not parse chmod command")

    if not tokens or tokens[0] != "chmod":
        return ValidationResult(allowed=False, reason="Not a chmod command")

    # Look for the mode argument
    # Valid modes: +x, u+x, a+x, etc. (anything ending with +x for execute permission)
    mode: str | None = None
    files: list[str] = []

    for token in tokens[1:]:
        if token.startswith("-"):
            # Skip flags like -R (we don't allow recursive chmod anyway)
            return ValidationResult(allowed=False, reason="chmod flags are not allowed")
        elif mode is None:
            mode = token
        else:
            files.append(token)

    if mode is None:
        return ValidationResult(allowed=False, reason="chmod requires a mode")

    if not files:
        return ValidationResult(
            allowed=False, reason="chmod requires at least one file"
        )

    # Only allow +x variants (making files executable)
    # This matches: +x, u+x, g+x, o+x, a+x, ug+x, etc.
    if not re.match(r"^[ugoa]*\+x$", mode):
        return ValidationResult(
            allowed=False, reason=f"chmod only allowed with +x mode, got: {mode}"
        )

    return ValidationResult(allowed=True)


def validate_init_script(command_string: str) -> ValidationResult:
    """
    Validate init.sh script execution - only allow ./init.sh.

    Args:
        command_string: The init script command to validate

    Returns:
        ValidationResult with allowed status and reason if blocked
    """
    try:
        tokens: list[str] = shlex.split(command_string)
    except ValueError:
        return ValidationResult(
            allowed=False, reason="Could not parse init script command"
        )

    if not tokens:
        return ValidationResult(allowed=False, reason="Empty command")

    # The command should be exactly ./init.sh (possibly with arguments)
    script: str = tokens[0]

    # Allow ./init.sh or paths ending in /init.sh
    if script == "./init.sh" or script.endswith("/init.sh"):
        return ValidationResult(allowed=True)

    return ValidationResult(
        allowed=False, reason=f"Only ./init.sh is allowed, got: {script}"
    )


def validate_rm_command(command_string: str) -> ValidationResult:
    """
    Validate rm commands - prevent dangerous deletions.

    Blocks:
    - rm on system directories (/, /etc, /usr, /var, /home, /Users, etc.)
    - rm -rf with wildcards on sensitive paths

    Allows:
    - rm on project files, temp directories, node_modules, etc.

    Args:
        command_string: The rm command to validate

    Returns:
        ValidationResult with allowed status and reason if blocked
    """
    # Dangerous root paths that should never be deleted
    dangerous_paths: set[str] = {
        "/",
        "/etc",
        "/usr",
        "/var",
        "/bin",
        "/sbin",
        "/lib",
        "/opt",
        "/boot",
        "/root",
        "/home",
        "/Users",
        "/System",
        "/Library",
        "/Applications",
        "/private",
        "~",
    }

    try:
        tokens: list[str] = shlex.split(command_string)
    except ValueError:
        return ValidationResult(allowed=False, reason="Could not parse rm command")

    if not tokens or tokens[0] != "rm":
        return ValidationResult(allowed=False, reason="Not an rm command")

    # Collect flags and paths
    flags: list[str] = []
    paths: list[str] = []

    for token in tokens[1:]:
        if token.startswith("-"):
            flags.append(token)
        else:
            paths.append(token)

    if not paths:
        return ValidationResult(allowed=False, reason="rm requires at least one path")

    # Check each path for dangerous patterns
    for path in paths:
        # Normalize the path for comparison
        # Special case: "/" should remain "/" after normalization (rstrip("/") on "/" returns "")
        normalized = path.rstrip("/") or "/"

        # Block exact matches to dangerous paths
        if normalized in dangerous_paths:
            return ValidationResult(
                allowed=False,
                reason=f"rm on system directory '{path}' is not allowed",
            )

        # Block paths that start with dangerous roots (but allow subdirs of project paths)
        for dangerous in dangerous_paths:
            if dangerous == "/":
                continue  # Skip root, check separately
            # Block if path IS the dangerous path or is directly under it without much depth
            # e.g., block /Users but allow /Users/rasmus/projects/my-project/node_modules
            if normalized == dangerous or (
                normalized.startswith(dangerous + "/")
                and normalized.count("/") <= dangerous.count("/") + 1
            ):
                return ValidationResult(
                    allowed=False,
                    reason=f"rm too close to system directory '{dangerous}' is not allowed",
                )

        # Block rm /* patterns (removing everything in root)
        if path == "/*" or path.startswith("/*"):
            return ValidationResult(
                allowed=False, reason="rm on root wildcard is not allowed"
            )

    return ValidationResult(allowed=True)


def get_command_for_validation(cmd: str, segments: list[str]) -> str:
    """
    Find the specific command segment that contains the given command.

    Args:
        cmd: The command name to find
        segments: List of command segments

    Returns:
        The segment containing the command, or empty string if not found
    """
    for segment in segments:
        segment_commands: list[str] = extract_commands(segment)
        if cmd in segment_commands:
            return segment
    return ""


async def bash_security_hook(
    input_data: PreToolUseHookInput,
    tool_use_id: str | None = None,
    context: HookContext | None = None,
) -> SyncHookJSONOutput:
    """
    Pre-tool-use hook that validates bash commands using an allowlist.

    Only commands in ALLOWED_COMMANDS are permitted.

    Args:
        input_data: Dict containing tool_name and tool_input
        tool_use_id: Optional tool use ID
        context: Optional context

    Returns:
        Empty dict to allow, or dict with decision='block' to block
    """
    if input_data.get("tool_name") != "Bash":
        return {}

    command: str = input_data.get("tool_input", {}).get("command", "")
    if not command:
        return {}

    # Extract all commands from the command string
    commands: list[str] = extract_commands(command)

    if not commands:
        # Could not parse - fail safe by blocking
        return SyncHookJSONOutput(
            decision="block",
            reason=f"Could not parse command for security validation: {command}",
        )

    # Split into segments for per-command validation
    segments: list[str] = split_command_segments(command)

    # Check each command against the allowlist
    for cmd in commands:
        if cmd not in ALLOWED_COMMANDS:
            return SyncHookJSONOutput(
                decision="block",
                reason=f"Command '{cmd}' is not in the allowed commands list",
            )

        # Additional validation for sensitive commands
        if cmd in COMMANDS_NEEDING_EXTRA_VALIDATION:
            # Find the specific segment containing this command
            cmd_segment: str = get_command_for_validation(cmd, segments)
            if not cmd_segment:
                cmd_segment = command  # Fallback to full command

            if cmd == "pkill":
                result: ValidationResult = validate_pkill_command(cmd_segment)
                if not result.allowed:
                    return SyncHookJSONOutput(decision="block", reason=result.reason)
            elif cmd == "chmod":
                result = validate_chmod_command(cmd_segment)
                if not result.allowed:
                    return SyncHookJSONOutput(decision="block", reason=result.reason)
            elif cmd == "init.sh":
                result = validate_init_script(cmd_segment)
                if not result.allowed:
                    return SyncHookJSONOutput(decision="block", reason=result.reason)
            elif cmd == "rm":
                result = validate_rm_command(cmd_segment)
                if not result.allowed:
                    return SyncHookJSONOutput(decision="block", reason=result.reason)

    return {}
