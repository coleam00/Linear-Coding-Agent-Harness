# ADR-004: Explicit Context Passing Between Agents

## Status
Accepted

## Context

In the multi-agent orchestration pattern (ADR-001), specialized agents are invoked via the Task tool. A critical question arises:

**How do agents share information?**

Options considered:
1. Shared memory/state between agents
2. Agents query external systems (Linear, files) themselves
3. Orchestrator explicitly passes all context

The challenge: when the orchestrator delegates to the Coding Agent to implement an issue, how does the Coding Agent know what to implement?

## Decision

Implement **explicit context passing** where the orchestrator:
1. Gathers all needed information before delegation
2. Passes complete context in the delegation prompt
3. Never tells an agent to "check" data already obtained

### Pattern

```
Orchestrator holds all context
    ↓
Delegation includes full context
    ↓
Agent works with provided context
    ↓
Agent returns results
    ↓
Orchestrator holds results for next delegation
```

### Example

**Wrong** (implicit context):
```
Orchestrator → Linear Agent: "Get next issue"
Linear Agent → Orchestrator: {issue_id: "APP-15"}
Orchestrator → Coding Agent: "Implement issue APP-15"  ← BAD
```

**Correct** (explicit context):
```
Orchestrator → Linear Agent: "Get next issue with full details"
Linear Agent → Orchestrator: {issue_id, title, description, test_steps}
Orchestrator → Coding Agent: "Implement issue APP-15: User Profile Page
                              Description: Create profile page with avatar...
                              Test Steps: 1. Navigate to /profile..."  ← GOOD
```

## Consequences

### Positive
- **No Hidden State**: All context is visible in prompts
- **Debuggability**: Can trace exactly what each agent received
- **Independence**: Agents don't need to know about external systems
- **Reliability**: No race conditions or stale data from separate queries
- **Testability**: Agents can be tested with static context

### Negative
- **Prompt Size**: Larger delegation prompts with full context
- **Orchestrator Complexity**: Orchestrator must gather and format all context
- **Redundancy**: Same information may be passed multiple times

### Neutral
- Orchestrator prompt includes explicit rules about context passing
- Linear agent returns structured data for easy passing

## Implementation

### Orchestrator Prompt Rules

From `orchestrator_prompt.md`:
```
CRITICAL: When delegating to agents, pass ALL relevant context.
- Never tell an agent to "check Linear" for data you already have
- Pass the full issue description, test steps, and context
- Include any previous agent responses that are relevant
```

### Context Structure

```typescript
interface IssueContext {
    issue_id: string;
    title: string;
    description: string;  // Full description
    test_steps: string[];
    priority: number;
}

interface ImplementationResult {
    files_changed: string[];
    screenshot_paths: string[];
    test_results: {
        passed: boolean;
        details: string;
    };
}
```

### Handoff Example

```
Step 1: Orchestrator → Linear Agent
"Get status and next issue details"
Response: {done: 10, todo: 40, next_issue: {id, title, description, steps}}

Step 2: Orchestrator → Coding Agent
"Implement issue APP-15: User Profile Page

Full Description:
Create a user profile page showing the user's avatar, name, email,
and settings. Include an edit button to modify profile fields.

Test Steps:
1. Navigate to http://localhost:3000/profile
2. Verify avatar image loads
3. Verify name and email display
4. Click edit button
5. Verify edit form appears

Provide screenshot evidence."

Response: {files_changed: [...], screenshots: [...], tests: {passed: true}}

Step 3: Orchestrator → Linear Agent
"Mark issue APP-15 as Done with the following evidence:
Files changed: src/pages/Profile.tsx, src/components/Avatar.tsx
Screenshot: screenshots/APP-15-profile.png
Test result: PASSED"
```

## Alternatives Considered

### Shared Memory Store
- **Rejected**: Adds infrastructure complexity
- Would need Redis/database for state
- Hard to debug invisible state

### Agents Query External Systems
- **Rejected**: Duplicate API calls, stale data risk
- Agent might query outdated Linear state
- Harder to trace information flow

### File-Based Context Sharing
- **Rejected**: Agents would need to coordinate file reads/writes
- Race conditions possible
- More complex than direct passing

## Related Decisions
- [ADR-001: Multi-Agent Orchestration](./ADR-001-multi-agent-orchestration.md) - Pattern requires this
- [ADR-005: Model Selection](./ADR-005-model-selection-strategy.md) - Haiku handles context passing
