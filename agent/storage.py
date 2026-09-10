from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypedDict

DEFAULT_TODOS_FILE = Path(os.getenv("TODOS_FILE_PATH", "todos.json"))


class Todo(TypedDict):
    id: int
    title: str
    status: Literal["pending", "completed"]
    priority: Literal["low", "medium", "high"]
    created_at: str


def load_todos(file_path: Path = DEFAULT_TODOS_FILE) -> list[Todo]:
    if not file_path.exists():
        save_todos([], file_path)
        return []
    try:
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            return []
        data = json.loads(text)
        todos = data.get("todos", [])
        return todos if isinstance(todos, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos: list[Todo], file_path: Path = DEFAULT_TODOS_FILE) -> None:
    file_path.write_text(json.dumps({"todos": todos}, indent=2), encoding="utf-8")


def get_todos(status_filter: str = "all") -> list[Todo]:
    todos = load_todos()
    if status_filter in ("pending", "completed"):
        return [t for t in todos if t["status"] == status_filter]
    return todos


def insert_todo(title: str, priority: Literal["low", "medium", "high"] = "medium") -> Todo:
    todos = load_todos()
    next_id = max((t["id"] for t in todos), default=0) + 1
    todo: Todo = {
        "id": next_id,
        "title": title.strip(),
        "status": "pending",
        "priority": priority,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    todos.append(todo)
    save_todos(todos)
    return todo


def mark_todo_completed(todo_id: int) -> Todo | None:
    todos = load_todos()
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return None
    todo["status"] = "completed"
    save_todos(todos)
    return todo


def remove_todo(todo_id: int) -> Todo | None:
    todos = load_todos()
    todo = next((t for t in todos if t["id"] == todo_id), None)
    if not todo:
        return None
    save_todos([t for t in todos if t["id"] != todo_id])
    return todo
