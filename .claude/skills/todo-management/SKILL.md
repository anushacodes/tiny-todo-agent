---
name: todo-management
description: Explains todo formatting conventions, priority rules, and task lifecycle management.
---

# Todo Management Conventions

Guidelines for managing tasks in the Tiny Todo Agent:

## Priority Rules
- **high**: Urgent or blocking tasks that need immediate attention.
- **medium**: Standard tasks to be worked on during regular sessions (default).
- **low**: Nice-to-have items, exploratory ideas, or future backlog.

## Lifecycle
- New tasks always start with status `pending`.
- When completed, tasks transition to `completed`.
- Tasks are identified by their unique numeric `id`.

## Formatting Recommendations
- Titles should be imperative and action-oriented (e.g. "learn Redis", "build auth flow").
- Always use the `todo-server` MCP tools to inspect or update `todos.json`.

