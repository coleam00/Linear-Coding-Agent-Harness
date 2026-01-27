"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

import shutil
from pathlib import Path


PROMPTS_DIR: Path = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        name: Prompt name (without .md extension)

    Returns:
        Prompt text content

    Raises:
        FileNotFoundError: If prompt file doesn't exist
        IOError: If prompt file cannot be read
    """
    prompt_path: Path = PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}\n"
            f"Expected prompts directory: {PROMPTS_DIR}\n"
            f"This may indicate an incomplete installation."
        )

    try:
        return prompt_path.read_text()
    except IOError as e:
        raise IOError(
            f"Failed to read prompt file {prompt_path}: {e}\n"
            f"Check file permissions."
        ) from e


def get_initializer_prompt() -> str:
    """Load the initializer prompt (legacy, for non-orchestrator mode)."""
    return load_prompt("initializer_prompt")


def get_coding_prompt() -> str:
    """Load the coding agent prompt (legacy, for non-orchestrator mode)."""
    return load_prompt("coding_prompt")


def get_initializer_task(project_dir: Path) -> str:
    """
    Get the task message for initializing a new project.

    This is sent to the orchestrator, which will delegate to specialized agents.
    """
    return f"""Initialize a new project in: {project_dir}

This is the FIRST session. The project has not been set up yet.

## INITIALIZATION SEQUENCE

### Step 1: Set Up Linear Project
Delegate to `linear` agent:
"Read app_spec.txt to understand what we're building. Then:
1. Create a Linear project with appropriate name
2. Create issues for ALL features from app_spec.txt (with test steps in description)
3. Create a META issue '[META] Project Progress Tracker' for session handoffs
4. Save state to .linear_project.json
5. Create claude-progress.txt with initial project summary
6. Return: project_id, total_issues created, meta_issue_id"

### Step 2: Initialize Git
Delegate to `github` agent:
"Initialize git repository:
1. git init
2. Create README.md with project overview
3. Create init.sh script to start dev server
4. Initial commit with these files + .linear_project.json + claude-progress.txt"

### Step 3: Start First Feature (if time permits)
Get the highest-priority issue details from linear agent, then delegate to `coding` agent:
"Implement this Linear issue:
- ID: [from linear agent]
- Title: [from linear agent]
- Description: [from linear agent]
- Test Steps: [from linear agent]

Requirements:
1. Implement the feature
2. Test via Puppeteer (mandatory)
3. Take screenshot evidence
4. Report: files_changed, screenshot_path, test_results"

### Step 4: Commit Progress
If coding was done, delegate to `github` agent to commit.
Then delegate to `linear` agent to update progress.

## OUTPUT FILES TO CREATE
- .linear_project.json (project state)
- claude-progress.txt (session history for fast reads)
- init.sh (dev server startup)
- README.md (project overview)

Remember: You are the orchestrator. Delegate tasks to specialized agents, don't do the work yourself."""


def get_continuation_task(project_dir: Path) -> str:
    """
    Get the task message for continuing work on an existing project.

    This is sent to the orchestrator, which will delegate to specialized agents.
    """
    return f"""Continue work on the project in: {project_dir}

This is a CONTINUATION session. The project has already been initialized.

## STRICT STARTUP SEQUENCE (follow in order)

### Step 1: Orient
- Run `pwd` to confirm working directory
- Read `claude-progress.txt` for recent session history
- Read `.linear_project.json` for project IDs

### Step 2: Get Status from Linear
Delegate to `linear` agent:
"Read .linear_project.json, then:
1. List all issues and count by status (Done/In Progress/Todo)
2. Check for any In Progress issues (interrupted work = priority)
3. Get the FULL DETAILS of the highest-priority issue to work on
4. Update claude-progress.txt with current status
5. Return the complete issue context: id, title, description, test_steps"

### Step 3: MANDATORY Verification Test (before ANY new work)
Delegate to `coding` agent:
"Run init.sh to start the dev server, then verify 1-2 completed features still work:
1. Navigate to the app via Puppeteer
2. Test a core feature end-to-end
3. Take a screenshot as evidence
4. Report: PASS/FAIL with screenshot path
If ANY verification fails, fix it before new work."

### Step 4: Implement Feature (only after Step 3 passes)
Delegate to `coding` agent with FULL context from Step 2:
"Implement this Linear issue:
- ID: [from linear agent]
- Title: [from linear agent]
- Description: [from linear agent]
- Test Steps: [from linear agent]

Requirements:
1. Implement the feature
2. Test via Puppeteer (mandatory)
3. Take screenshot evidence
4. Report: files_changed, screenshot_path, test_results"

### Step 5: Commit
Delegate to `github` agent:
"Commit changes for [issue title]. Include Linear issue ID in commit message."

### Step 6: Mark Done (only with screenshot evidence)
Delegate to `linear` agent:
"Mark issue [id] as Done. Add comment with:
- Files changed
- Screenshot evidence path
- Test results
Update claude-progress.txt with session summary."

## CRITICAL RULES
- Do NOT skip the verification test in Step 3
- Do NOT mark Done without screenshot evidence from coding agent
- Do NOT start Step 4 if Step 3 fails
- Pass FULL issue context to coding agent (don't make it query Linear)

Remember: You are the orchestrator. Delegate tasks to specialized agents, don't do the work yourself."""


def copy_spec_to_project(project_dir: Path) -> None:
    """
    Copy the app spec file into the project directory for the agent to read.

    Args:
        project_dir: Target project directory

    Raises:
        FileNotFoundError: If source spec file doesn't exist
        IOError: If copy operation fails
    """
    spec_source: Path = PROMPTS_DIR / "app_spec.txt"
    spec_dest: Path = project_dir / "app_spec.txt"

    if not spec_source.exists():
        raise FileNotFoundError(
            f"App spec template not found: {spec_source}\n"
            f"This indicates an incomplete installation."
        )

    if not spec_dest.exists():
        try:
            shutil.copy(spec_source, spec_dest)
            print(f"Copied app_spec.txt to {project_dir}")
        except IOError as e:
            raise IOError(
                f"Failed to copy app spec to {spec_dest}: {e}\n"
                f"Check disk space and permissions."
            ) from e
