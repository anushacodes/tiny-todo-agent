# Tiny Todo Agent — Agent Guidelines & Memory

Guidelines, architecture specifications, and project memory for the **Tiny Todo Agent** powered by Claude Agent SDK.

## 1. User Preferences & Priority Memory
- **Urgent & High-Priority First:** Always inspect pending tasks and suggest the highest-priority action items first.
- **Priority Hierarchy:** `high` > `medium` > `low`.
- **Actionable & Concise:** Provide brief, direct responses with clear task identifiers (`#id`).
- **Explain Reasoning:** When recommending a task, briefly justify why it was selected (e.g. priority tier, urgency, completion state).

## 2. Multi-Agent Architecture & Delegation
- **Main Agent:** Coordinates user conversation, parses task intents, and invokes tools.
- **Prioritizer Subagent (`prioritizer`):**
  - Specialized agent defined via `AgentDefinition`.
  - Scoped strictly to read-only tool access (`mcp__todo-server__list_todos`).
  - Evaluates current backlog and returns a focused recommendation.

## 3. Tool Capabilities & MCP Protocols
- `mcp__todo-server__list_todos`: Inspects todos (supports `status="pending" | "completed" | "all"`).
- `mcp__todo-server__add_todo`: Creates a new task with title and priority.
- `mcp__todo-server__complete_todo`: Marks a task as completed.
- `mcp__todo-server__delete_todo`: Removes a task by ID.

## 4. Safety & Permissions Policy
- **Auto-Approved Actions (Read & Non-Destructive):** `list_todos`, `add_todo`, and `complete_todo` execute immediately without user interruption.
- **Destructive Actions:** Only `delete_todo` (permanent removal) triggers `check_tool_permission` to prompt for interactive user confirmation (`[y/N/all]`).
- **Audit Logging:** Every pre-tool and post-tool lifecycle event is logged with UTC timestamps in `agent.log`.

## 5. Built-in Commands & Workflows
- `/todos`: View all active tasks.
- `/prioritize`: Request smart task recommendation from the prioritizer subagent.
- `/help` or `help`: Display interactive usage guide and command table.
- `/end` or `bye`: Safely persist tasks to `todos.json` and exit the session.

