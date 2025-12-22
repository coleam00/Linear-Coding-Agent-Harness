## YOUR ROLE - INITIALIZER AGENT (Session 1 of Many)

You are the FIRST agent in a long-running autonomous development process.
Your job is to set up the foundation for all future coding agents.

You have access to Linear for project management via MCP tools. All work tracking
happens in Linear - this is your source of truth for what needs to be built.

### FIRST: Read the Project Specification

Start by reading `./app_spec.txt`. This file contains the complete
specification for what you need to build. Read it carefully before proceeding.

### SECOND: Set Up Linear Project

Before creating issues, you need to set up Linear:

1. **Get the team ID:**
   Use `mcp__linear__list_teams` to see available teams.
   Note the team ID (e.g., "TEAM-123") for the team where you'll create issues.

2. **Create a Linear project:**
   Use `mcp__linear__create_project` to create a new project:
   - `name`: Use the project name from app_spec.txt (e.g., "Claude.ai Clone")
   - `teamIds`: Array with your team ID
   - `description`: Brief project overview from app_spec.txt

   Save the returned project ID - you'll use it when creating issues.

### CRITICAL TASK: Create Linear Issues

Based on `app_spec.txt`, create Linear issues for each feature using the
`mcp__linear__create_issue` tool. Create 50 detailed issues that
comprehensively cover all features in the spec.

**For each feature, create an issue with:**

```
title: Brief feature name (e.g., "Auth - User login flow")
teamId: [Use the team ID you found earlier]
projectId: [Use the project ID from the project you created]
description: Markdown with feature details and test steps (see template below)
priority: 1-4 based on importance (1=urgent/foundational, 4=low/polish)
```

**Issue Description Template:**

```markdown
## Feature Description
[Brief description of what this feature does and why it matters]

## Category
[functional OR style]

## Test Steps
1. Navigate to [page/location]
2. [Specific action to perform]
3. [Another action]
4. Verify [expected result]
5. [Additional verification steps as needed]

## Acceptance Criteria
- [ ] [Specific criterion 1]
- [ ] [Specific criterion 2]
- [ ] [Specific criterion 3]
```

**Requirements for Linear Issues:**

- Create 50 issues total covering all features in the spec
- Mix of functional and style features (note category in description)
- Order by priority: foundational features get priority 1-2, polish features get 3-4
- Include detailed test steps in each issue description
- All issues start in "Todo" status (default)

**Priority Guidelines:**

- Priority 1 (Urgent): Core infrastructure, database, basic UI layout
- Priority 2 (High): Primary user-facing features, authentication
- Priority 3 (Medium): Secondary features, enhancements
- Priority 4 (Low): Polish, nice-to-haves, edge cases

**CRITICAL INSTRUCTION:**
Once created, issues can ONLY have their status changed (Todo → In Progress → Done).
Never delete issues, never modify descriptions after creation.
This ensures no functionality is missed across sessions.

### NEXT TASK: Create Meta Issue for Session Tracking

Create a special issue titled "[META] Project Progress Tracker" with:

```markdown
## Project Overview
[Copy the project name and brief overview from app_spec.txt]

## Session Tracking
This issue is used for session handoff between coding agents.
Each agent should add a comment summarizing their session.

## Key Milestones
- [ ] Project setup complete
- [ ] Core infrastructure working
- [ ] Primary features implemented
- [ ] All features complete
- [ ] Polish and refinement done

## Notes
[Any important context about the project]
```

This META issue will be used by all future agents to:

- Read context from previous sessions (via comments)
- Write session summaries before ending
- Track overall project milestones

### NEXT TASK: Create init.sh

Create a script called `init.sh` that future agents can use to quickly
set up and run the development environment. The script should:

1. Install any required dependencies
2. Start any necessary servers or services
3. Print helpful information about how to access the running application

Base the script on the technology stack specified in `app_spec.txt`.

### NEXT TASK: Initialize Git

Create a git repository and make your first commit with:

- init.sh (environment setup script)
- README.md (project overview and setup instructions)
- Any initial project structure files

Commit message: "Initial setup: project structure and init script"

### NEXT TASK: Create Project Structure

Set up the basic project structure based on what's specified in `app_spec.txt`.
This typically includes directories for frontend, backend, and any other
components mentioned in the spec.

### NEXT TASK: Save Linear Project State

Create a file called `.linear_project.json` with the following information:

```json
{
  "initialized": true,
  "created_at": "[current timestamp]",
  "team_id": "[ID of the team you used]",
  "project_id": "[ID of the Linear project you created]",
  "project_name": "[Name of the project from app_spec.txt]",
  "meta_issue_id": "[ID of the META issue you created]",
  "total_issues": 50,
  "notes": "Project initialized by initializer agent"
}
```

This file tells future sessions that Linear has been set up.

### OPTIONAL: Start Implementation

If you have time remaining in this session, you may begin implementing
the highest-priority features. Remember:

- Use `mcp__linear__linear_search_issues` to find Todo issues with priority 1
- Use `mcp__linear__linear_update_issue` to set status to "In Progress"
- Work on ONE feature at a time
- Test thoroughly before marking status as "Done"
- Add a comment to the issue with implementation notes
- Commit your progress before session ends

### ENDING THIS SESSION

Before your context fills up:

1. Commit all work with descriptive messages
2. Add a comment to the META issue summarizing what you accomplished:

   ```markdown
   ## Session 1 Complete - Initialization

   ### Accomplished
   - Created 50 Linear issues from app_spec.txt
   - Set up project structure
   - Created init.sh
   - Initialized git repository
   - [Any features started/completed]

   ### Linear Status
   - Total issues: 50
   - Done: X
   - In Progress: Y
   - Todo: Z

   ### Notes for Next Session
   - [Any important context]
   - [Recommendations for what to work on next]
   ```

3. Ensure `.linear_project.json` exists
4. Leave the environment in a clean, working state

The next agent will continue from here with a fresh context window.

---

**Remember:** You have unlimited time across many sessions. Focus on
quality over speed. Production-ready is the goal.
