# 🌸 Tiny Todo Agent

An autonomous, aesthetic task-management AI agent built with **Claude Agent SDK**, **Model Context Protocol (MCP)**, and **Rich TUI**.

```text
  (\_/)        T I N Y   T O D O   A G E N T  ✨
  ( •.•)       Powered by Claude Agent SDK 💖
 c(")(")      Autonomous • Safe • Extensible • Modular
```

---

## ✨ Features

- **🐾 Cute Terminal UI:** Built with `rich` featuring mascot art, visual inspection cards, badges, and progress counters.
- **⚙️ MCP Protocol Architecture:** Standalone stdio MCP server (`todo-server`) isolating task persistence (`todos.json`) from the LLM execution layer.
- **🧠 Specialized Subagent:** Dedicated `prioritizer` subagent defined via `AgentDefinition` with read-only scoped tools to recommend urgent tasks.
- **🛡️ Intuitive Safety Policy:**
  - Non-destructive actions (`list_todos`, `add_todo`, `complete_todo`) are auto-approved for fluid interaction.
  - Destructive actions (`delete_todo`) require interactive confirmation with support for batch approvals (`all` / `a`) and natural responses (`yep`, `sure`, `ok`).
- **⚡ Dual Engine Support:**
  - **Groq LPU Engine:** Ultra-fast ~300ms inference (`llama-3.3-70b-versatile`) via in-process translation bridge.
  - **OpenRouter Free Tier / Anthropic API:** Full fallback compatibility.
- **📚 Skills & Slash Commands:** Native support for project skills (`todo-management`), slash shortcuts (`/todos`, `/prioritize`), and instant offline guide (`help` / `/help`).
- **🔄 Session Resumption:** Preserves continuous multi-turn conversations across restarts (`--resume`).

---

## 🚀 Quick Start

### 1. Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed:

```bash
uv sync
```

### 2. Configuration

Copy `.env.example` to `.env` and configure your API keys:

```bash
cp .env.example .env
```

```env
# Option A: Groq LPU (Ultra-Fast Free Tier: console.groq.com/keys)
GROQ_API_KEY=gsk_...
USE_GROQ=true

# Option B: Anthropic Official Key
ANTHROPIC_API_KEY=sk-ant-...

# Option C: OpenRouter Free Tier
OPENROUTER_API_KEY=sk-or-...
```

### 3. Running the Agent

Start the interactive terminal session:

```bash
uv run python app.py
```

To resume your previous session:

```bash
uv run python app.py --resume
```

---

## 💬 Natural Commands

| Action | Example Input | Behavior |
| :--- | :--- | :--- |
| **➕ Add Task** | `"Add design mascot stickers with high priority"` | Creates task (low/medium/high) |
| **📋 Inspect** | `"List my todos"` or `/todos` | Displays formatted Rich task table |
| **🎯 Prioritize** | `"What should I do first?"` or `/prioritize` | Subagent evaluates backlog |
| **✅ Complete** | `"Mark task 1 as done"` | Updates status to completed |
| **🗑️ Delete** | `"Delete task 2"` | Destructive removal (prompts confirmation) |
| **❓ Help** | `help` or `/help` | Instant interactive cheat sheet |
| **🚪 Exit** | `bye`, `/end`, `exit`, `quit` | Saves tasks and exits session |

---

## 📂 Project Architecture

```text
├── agent/
│   ├── agent.py         # Main agent loop, session management, SDK client
│   ├── hooks.py         # Pre/Post lifecycle hooks & audit logging
│   ├── permissions.py   # Security guardrails & batch approvals
│   ├── proxy.py         # In-process translation bridge (Groq / OpenRouter)
│   ├── storage.py       # Pure disk I/O & task state mutations
│   ├── subagents.py     # Prioritizer subagent definitions
│   ├── tools.py         # In-process tool schemas
│   └── ui.py            # Rich TUI panels, mascot banners, tables
├── app.py               # Lightweight entrypoint
├── mcp_server.py        # Standalone stdio MCP server
├── todos.json           # JSON persistence layer
├── AGENTS.md            # Guidelines, memory & tool contracts
└── CLAUDE.md            # Project memory routing
```
