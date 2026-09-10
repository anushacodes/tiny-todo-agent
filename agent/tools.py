from __future__ import annotations

import json
from typing import Any, Literal

from claude_agent_sdk import create_sdk_mcp_server, tool
from claude_agent_sdk.types import McpSdkServerConfig

from agent.storage import get_todos, insert_todo, mark_todo_completed, remove_todo


def _ok(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _err(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "is_error": True}


@tool(
    name="list_todos",
    description="List todos, optionally filtered by status.",
    input_schema={
        "type": "object",
        "properties": {"status": {"type": "string", "enum": ["all", "pending", "completed"]}},
    },
)
async def list_todos(args: dict[str, Any]) -> dict[str, Any]:
    status = str(args.get("status", "all"))
    todos = get_todos(status)
    if not todos:
        return _ok(f"No todos found (filter: {status}).")
    return _ok(json.dumps(todos, indent=2))


@tool(
    name="add_todo",
    description="Add a new todo with optional priority.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Task title"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        },
        "required": ["title"],
    },
)
async def add_todo(args: dict[str, Any]) -> dict[str, Any]:
    title = str(args.get("title", "")).strip()
    if not title:
        return _err("Error: Todo title cannot be empty.")
    raw = str(args.get("priority", "medium")).lower()
    priority: Literal["low", "medium", "high"] = raw if raw in ("low", "medium", "high") else "medium"  # type: ignore[assignment]
    todo = insert_todo(title, priority)
    return _ok(f"Added todo #{todo['id']}: '{todo['title']}' (priority: {todo['priority']})")


@tool(
    name="complete_todo",
    description="Mark a todo as completed by ID.",
    input_schema={
        "type": "object",
        "properties": {"id": {"type": "integer", "description": "Todo ID"}},
        "required": ["id"],
    },
)
async def complete_todo(args: dict[str, Any]) -> dict[str, Any]:
    todo_id = args.get("id")
    if todo_id is None:
        return _err("Error: Missing required 'id' parameter.")
    todo = mark_todo_completed(int(todo_id))
    if not todo:
        return _err(f"Error: Todo #{todo_id} not found.")
    return _ok(f"Marked todo #{todo_id} '{todo['title']}' as completed.")


@tool(
    name="delete_todo",
    description="Delete a todo by ID.",
    input_schema={
        "type": "object",
        "properties": {"id": {"type": "integer", "description": "Todo ID"}},
        "required": ["id"],
    },
)
async def delete_todo(args: dict[str, Any]) -> dict[str, Any]:
    todo_id = args.get("id")
    if todo_id is None:
        return _err("Error: Missing required 'id' parameter.")
    todo = remove_todo(int(todo_id))
    if not todo:
        return _err(f"Error: Todo #{todo_id} not found.")
    return _ok(f"Deleted todo #{todo_id} '{todo['title']}'.")


def create_todo_tools_server() -> McpSdkServerConfig:
    return create_sdk_mcp_server(name="todo-tools", version="1.0.0", tools=[list_todos, add_todo, complete_todo, delete_todo])
