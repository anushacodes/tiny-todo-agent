from __future__ import annotations

import json
from typing import Literal

from mcp.server.mcpserver import MCPServer

from agent.storage import get_todos, insert_todo, mark_todo_completed, remove_todo

server = MCPServer("todo-server")


@server.tool(name="list_todos", description="List todos, optionally filtered by status.")
def list_todos(status: str = "all") -> str:
    todos = get_todos(status)
    if not todos:
        return f"No todos found (filter: {status})."
    return json.dumps(todos, indent=2)


@server.tool(name="add_todo", description="Add a new todo with optional priority.")
def add_todo(title: str, priority: str = "medium") -> str:
    if not title.strip():
        return "Error: Todo title cannot be empty."
    raw = priority.lower()
    p: Literal["low", "medium", "high"] = raw if raw in ("low", "medium", "high") else "medium"  # type: ignore[assignment]
    todo = insert_todo(title, p)
    return f"Added todo #{todo['id']}: '{todo['title']}' (priority: {todo['priority']})"


@server.tool(name="complete_todo", description="Mark a todo as completed by ID.")
def complete_todo(id: int) -> str:
    todo = mark_todo_completed(id)
    if not todo:
        return f"Error: Todo #{id} not found."
    return f"Marked todo #{id} '{todo['title']}' as completed."


@server.tool(name="delete_todo", description="Delete a todo by ID.")
def delete_todo(id: int) -> str:
    todo = remove_todo(id)
    if not todo:
        return f"Error: Todo #{id} not found."
    return f"Deleted todo #{id} '{todo['title']}'."


if __name__ == "__main__":
    server.run("stdio")

