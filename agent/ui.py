from __future__ import annotations

import json
import os
from typing import Any

from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_banner(resume_session_id: str | None = None) -> None:
    logo_art = (
        "[bold hot_pink]  (\\_/)[/bold hot_pink]        [bold bright_cyan]T I N Y   T O D O   A G E N T[/bold bright_cyan]  [bold bright_yellow]✨[/bold bright_yellow]\n"
        "[bold hot_pink]  ( •.•)[/bold hot_pink]       [bold medium_purple1]Powered by Claude Agent SDK[/bold medium_purple1] [bold pink1]💖[/bold pink1]\n"
        "[bold hot_pink] c(\\\")(\\\")[/bold hot_pink]      [dim cyan]Autonomous • Safe • Extensible • Modular[/dim cyan]"
    )

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(style="bold bright_yellow", justify="right")
    info_table.add_column(style="white")

    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_groq = bool(os.getenv("GROQ_API_KEY"))

    if has_anthropic:
        mode_str = "[bold bright_green]Anthropic Claude API[/bold bright_green] [dim](claude-3-5-sonnet)[/dim]"
    elif has_groq:
        mode_str = "[bold bright_cyan]⚡ Groq LPU Engine[/bold bright_cyan] [dim](llama-3.3-70b-versatile)[/dim]"
    else:
        mode_str = "[bold green]Free Cloud Router[/bold green] [dim](openrouter/free)[/dim]"

    info_table.add_row("🌸 Engine:", mode_str)
    if resume_session_id:
        info_table.add_row("🔄 Session:", f"[bold cyan]{resume_session_id}[/bold cyan]")

    info_table.add_row(
        "➕ Add Task:",
        '[italic white]"Add design mascot stickers with high priority"[/italic white]',
    )
    info_table.add_row(
        "📋 Inspect:",
        '[italic white]"List my todos"[/italic white] or [bold magenta]/todos[/bold magenta]',
    )
    info_table.add_row(
        "🎯 Prioritize:",
        '[italic white]"What should I do first?"[/italic white] or [bold magenta]/prioritize[/bold magenta]',
    )
    info_table.add_row(
        "✅ Complete:",
        '[italic white]"Mark task 1 as completed"[/italic white]',
    )
    info_table.add_row(
        "🗑️ Delete:",
        '[italic white]"Delete task 3"[/italic white]',
    )
    info_table.add_row(
        "❓ Help:",
        '[bold cyan]help[/bold cyan] or [bold cyan]/help[/bold cyan] for interactive guide',
    )
    info_table.add_row(
        "🚪 Exit:",
        "[dim white]Type 'bye', '/end', 'exit', or 'quit'[/dim white]",
    )

    body = Table.grid(padding=(1, 0))
    body.add_row(logo_art)
    body.add_row(info_table)

    panel = Panel(
        body,
        title="[bold bright_magenta]✨ ₍ᐢ. .ᐢ₎ WELCOME ✨[/bold bright_magenta]",
        subtitle="[bold pink1]🐾 Ready to organize your tasks 🐾[/bold pink1]",
        border_style="bright_magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def _unwrap_tool_response(response: Any, max_depth: int = 5) -> Any:
    data = response
    for _ in range(max_depth):
        if isinstance(data, str):
            stripped = data.strip()
            if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
                try:
                    data = json.loads(stripped)
                    continue
                except Exception:
                    break
            break
        elif isinstance(data, dict):
            if "result" in data:
                data = data["result"]
                continue
            elif "content" in data and isinstance(data["content"], list) and data["content"]:
                item = data["content"][0]
                if isinstance(item, dict) and "text" in item:
                    data = item["text"]
                    continue
                elif isinstance(item, str):
                    data = item
                    continue
            break
        else:
            break
    return data


def print_tool_call(tool_name: str, tool_input: dict[str, Any]) -> None:
    clean_name = tool_name.split("__")[-1]

    is_subagent = clean_name.lower() in ("agent", "task") or "prioritizer" in str(tool_input)
    is_skill = clean_name.lower() == "skill"

    if is_subagent:
        title = "[bold medium_purple1]🧠 Subagent Delegation • Prioritizer[/bold medium_purple1]"
        border_style = "medium_purple1"
        tag = "[bold medium_purple1]Delegate:[/bold medium_purple1]"
    elif is_skill:
        title = "[bold bright_cyan]📚 Project Skill Active[/bold bright_cyan]"
        border_style = "bright_cyan"
        tag = "[bold bright_cyan]Skill:[/bold bright_cyan]"
    else:
        title = f"[bold bright_yellow]⚙️  Tool Call • {clean_name}[/bold bright_yellow]"
        border_style = "bright_yellow"
        tag = "[bold yellow]Tool:[/bold yellow]"

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", justify="right")
    grid.add_column(style="bright_white")
    grid.add_row(tag, f"[bold white]{clean_name}[/bold white] [dim]({tool_name})[/dim]")

    if tool_input:
        param_parts: list[str] = []
        for k, v in tool_input.items():
            val = f"#{v}" if k == "id" else str(v)
            param_parts.append(f"[cyan]{k}:[/cyan] [bold white]{val}[/bold white]")
        grid.add_row("📥 Parameters:", "   •   ".join(param_parts))
    else:
        grid.add_row("📥 Parameters:", "[dim italic]none (all tasks)[/dim italic]")

    panel = Panel(
        grid,
        title=title,
        border_style=border_style,
        box=box.ROUNDED,
        padding=(0, 2),
    )
    console.print(panel)


def print_tool_result(tool_name: str, response: Any) -> None:
    clean_name = tool_name.split("__")[-1]
    is_subagent = clean_name.lower() in ("agent", "task") or "prioritizer" in str(tool_name)
    is_skill = clean_name.lower() == "skill"

    data = _unwrap_tool_response(response)
    subtitle: str | None = None
    body_renderable: Any

    if is_subagent:
        title = "[bold medium_purple1]🧠 Subagent Result • Prioritizer[/bold medium_purple1]"
        border_style = "medium_purple1"
    elif is_skill:
        title = "[bold bright_cyan]📚 Skill Result[/bold bright_cyan]"
        border_style = "bright_cyan"
    else:
        title = f"[bold bright_green]📦 Tool Result • {clean_name}[/bold bright_green]"
        border_style = "bright_green"

    if isinstance(data, list) and (clean_name == "list_todos" or (data and isinstance(data[0], dict) and "id" in data[0])):
        if not data:
            body_renderable = Text("✨ No tasks found in your list.", style="italic cyan")
            subtitle = "0 tasks"
        else:
            table = Table(
                box=box.SIMPLE,
                show_header=True,
                header_style="bold bright_cyan",
                padding=(0, 1),
                expand=True,
            )
            table.add_column("ID", style="bold bright_magenta", justify="center", width=5)
            table.add_column("Priority", justify="center", width=12)
            table.add_column("Status", justify="center", width=12)
            table.add_column("Task Title", style="bold white", ratio=1)
            table.add_column("Created", style="dim white", justify="right", width=16)

            prio_map = {
                "high": "[bold red]🔴 High[/bold red]",
                "medium": "[bold yellow]🟡 Medium[/bold yellow]",
                "low": "[bold blue]🔵 Low[/bold blue]",
            }

            for item in data:
                if not isinstance(item, dict):
                    continue
                tid = f"#{item.get('id', '-')}"
                prio = prio_map.get(str(item.get("priority", "medium")).lower(), str(item.get("priority", "")))
                is_done = str(item.get("status", "")).lower() == "completed"
                status = "[bold green]✅ Done[/bold green]" if is_done else "[bold bright_yellow]⏳ Pending[/bold bright_yellow]"
                raw_title = str(item.get("title", ""))
                task_title = f"[dim strike]{raw_title}[/dim strike]" if is_done else f"[bold white]{raw_title}[/bold white]"
                raw_date = str(item.get("created_at", ""))
                clean_date = raw_date[:16].replace("T", " ") if raw_date else ""
                table.add_row(tid, prio, status, task_title, clean_date)

            pending_count = sum(1 for x in data if isinstance(x, dict) and str(x.get("status")) != "completed")
            subtitle = f"{len(data)} total • {pending_count} pending"
            body_renderable = table

    elif isinstance(data, str):
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="bold cyan", justify="right")
        grid.add_column(style="bold white")

        lower = data.lower()
        if "added todo" in lower:
            grid.add_row("✨ Status:", f"[bold bright_green]{data}[/bold bright_green]")
            subtitle = "Task Added"
            body_renderable = grid
        elif "completed todo" in lower or "marked todo" in lower or "as completed" in lower:
            grid.add_row("✅ Status:", f"[bold bright_green]{data}[/bold bright_green]")
            subtitle = "Task Completed"
            body_renderable = grid
        elif "deleted todo" in lower:
            grid.add_row("🗑️ Status:", f"[bold bright_yellow]{data}[/bold bright_yellow]")
            subtitle = "Task Deleted"
            body_renderable = grid
        elif "error:" in lower or "not found" in lower:
            grid.add_row("⚠️ Status:", f"[bold red]{data}[/bold red]")
            subtitle = "Action Failed"
            body_renderable = grid
        elif "no todos found" in lower:
            body_renderable = Text("📋 " + data, style="italic cyan")
            subtitle = "Empty List"
        else:
            body_renderable = Text(data, style="bright_white")

    elif isinstance(data, (dict, list)):
        formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
        body_renderable = Text(formatted_json, style="bright_cyan")
    else:
        body_renderable = Text(str(data), style="bright_white")

    panel = Panel(
        body_renderable,
        title=title,
        subtitle=f"[dim]{subtitle}[/dim]" if subtitle else None,
        border_style=border_style,
        box=box.ROUNDED,
        padding=(0, 2),
    )
    console.print(panel)


def print_permission_prompt(tool_name: str, tool_input: dict[str, Any]) -> None:
    clean_name = tool_name.split("__")[-1]
    args_str = json.dumps(tool_input, indent=2) if tool_input else "{}"

    body = Table.grid(padding=(0, 1))
    body.add_column(style="bold bright_red", justify="right")
    body.add_column(style="white")
    body.add_row("🛡️  Action:", f"[bold bright_yellow]{clean_name}[/bold bright_yellow]")
    body.add_row("📝 Parameters:", f"[cyan]{args_str}[/cyan]")
    body.add_row("⚠️  Notice:", "[bright_white]This action will modify your task database.[/bright_white]")

    panel = Panel(
        body,
        title="[bold red]🔒 Permission Required[/bold red]",
        subtitle="[bold yellow]User Confirmation Needed[/bold yellow]",
        border_style="red",
        box=box.ROUNDED,
        padding=(0, 2),
    )
    console.print(panel)


def print_thinking(thought: str) -> None:
    panel = Panel(
        Text(thought.strip(), style="dim white"),
        title="[bold purple]🧠 Agent Reasoning (Thinking)[/bold purple]",
        border_style="purple",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.print(panel)


def print_assistant_message(content: str) -> None:
    md = Markdown(content.strip())
    panel = Panel(
        md,
        title="[bold hot_pink]🤖 Tiny Todo Assistant[/bold hot_pink]",
        subtitle="[dim hot_pink]✨ Task update complete ✨[/dim hot_pink]",
        border_style="hot_pink",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def print_error(error_message: str) -> None:
    panel = Panel(
        Text(error_message, style="bold red"),
        title="[bold red]❌ Error Occurred[/bold red]",
        border_style="red",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.print(panel)


def print_user_prompt() -> str:
    console.print("\n[bold hot_pink]🌸 todo-agent[/bold hot_pink] [bold bright_yellow]❯[/bold bright_yellow] ", end="")
    return input()


def print_farewell() -> None:
    panel = Panel(
        "[bold pink1]🐾 Goodbye! Have a wonderful and productive day! 🐾[/bold pink1]\n"
        "[dim hot_pink]✨ Your todos are safely saved in todos.json ✨[/dim hot_pink]",
        title="[bold bright_magenta]₍ᐢ. .ᐢ₎ Farewell! ✨[/bold bright_magenta]",
        border_style="hot_pink",
        box=box.ROUNDED,
        padding=(0, 2),
    )
    console.print(panel)


def print_help() -> None:
    table = Table(box=box.ROUNDED, border_style="bright_cyan", padding=(0, 1))
    table.add_column("Action", style="bold bright_magenta", width=16)
    table.add_column("Example Prompt / Command", style="bold bright_yellow")
    table.add_column("Behavior & Notes", style="white")

    table.add_row(
        "➕ Add Task",
        '"Add design mascot stickers with high priority"',
        "Creates a new task with low/medium/high priority. Prompts for confirmation.",
    )
    table.add_row(
        "📋 List Tasks",
        '"List my todos"  or  /todos',
        "Inspects pending and completed tasks. Auto-allowed without prompt.",
    )
    table.add_row(
        "🎯 Prioritize",
        '"What should I do next?"  or  /prioritize',
        "Delegates to the specialised prioritizer subagent with read-only scope.",
    )
    table.add_row(
        "✅ Complete",
        '"Mark task 1 as done"',
        "Changes status to completed. Prompts for confirmation.",
    )
    table.add_row(
        "🗑️ Delete",
        '"Delete task 2"',
        "Removes task from storage. Prompts for confirmation.",
    )
    table.add_row(
        "❓ Help",
        'help  or  /help',
        "Displays this guide instantly.",
    )
    table.add_row(
        "🚪 Exit",
        'bye, /end, exit, quit',
        "Saves all tasks and terminates session cleanly.",
    )

    panel = Panel(
        table,
        title="[bold bright_cyan]📖 TINY TODO AGENT • COMMAND & USAGE GUIDE 📖[/bold bright_cyan]",
        subtitle="[bold pink1]🐾 Safe Autonomous Agent with Claude Agent SDK 🐾[/bold pink1]",
        border_style="bright_cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


