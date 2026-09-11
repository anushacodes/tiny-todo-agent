from __future__ import annotations

import http.server
import json
import os
import re
import threading
import urllib.error
import urllib.request
from typing import Any

from agent.hooks import _log


def _anthropic_to_groq(payload: dict[str, Any], default_model: str = "llama-3.3-70b-versatile") -> dict[str, Any]:
    model = payload.get("model") or default_model
    if "openrouter" in model or "claude" in model or not model:
        model = default_model

    messages: list[dict[str, Any]] = []
    system = payload.get("system")
    if system:
        if isinstance(system, list):
            sys_text = "".join(b.get("text", "") for b in system if isinstance(b, dict))
        else:
            sys_text = str(system)
        if sys_text.strip():
            messages.append({"role": "system", "content": sys_text.strip()})

    for msg in payload.get("messages", []):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            if role == "assistant":
                text_parts = []
                tool_calls = []
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    btype = b.get("type")
                    if btype == "text":
                        text_parts.append(b.get("text", ""))
                    elif btype == "tool_use":
                        tool_calls.append({
                            "id": b.get("id", f"call_{len(tool_calls)}"),
                            "type": "function",
                            "function": {
                                "name": b.get("name", ""),
                                "arguments": json.dumps(b.get("input", {})),
                            },
                        })
                item: dict[str, Any] = {
                    "role": "assistant",
                    "content": "".join(text_parts) if text_parts else None,
                }
                if tool_calls:
                    item["tool_calls"] = tool_calls
                messages.append(item)
            elif role == "user":
                text_parts = []
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    btype = b.get("type")
                    if btype == "text":
                        text_parts.append(b.get("text", ""))
                    elif btype == "tool_result":
                        res = b.get("content", "")
                        if not isinstance(res, str):
                            res = json.dumps(res)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": b.get("tool_use_id", ""),
                            "content": res,
                        })
                if text_parts:
                    messages.append({"role": "user", "content": "".join(text_parts)})

    groq_payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    tools = payload.get("tools")
    if tools:
        groq_tools = []
        for t in tools:
            groq_tools.append({
                "type": "function",
                "function": {
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            })
        groq_payload["tools"] = groq_tools

    return groq_payload


def _groq_to_anthropic(groq_data: dict[str, Any], model_name: str = "llama-3.3-70b-versatile") -> dict[str, Any]:
    choices = groq_data.get("choices", [])
    choice = choices[0] if choices else {}
    msg = choice.get("message", {})
    content: list[dict[str, Any]] = []

    text = msg.get("content")
    if text:
        content.append({"type": "text", "text": text})

    for tc in msg.get("tool_calls", []):
        fn = tc.get("function", {})
        name = fn.get("name", "")
        args_str = fn.get("arguments", "{}")
        try:
            args_dict = json.loads(args_str)
        except Exception:
            args_dict = {}
        content.append({
            "type": "tool_use",
            "id": tc.get("id", f"call_{len(content)}"),
            "name": name,
            "input": args_dict,
        })

    finish_reason = choice.get("finish_reason")
    is_tool = finish_reason in ("tool_calls", "function_call") or any(b.get("type") == "tool_use" for b in content)
    stop_reason = "tool_use" if is_tool else "end_turn"
    usage = groq_data.get("usage", {})

    return {
        "id": "msg_" + str(groq_data.get("id", "res")),
        "type": "message",
        "role": "assistant",
        "model": model_name,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


class _ProxyHandler(http.server.BaseHTTPRequestHandler):
    provider: str = "groq"
    groq_key: str = ""
    openrouter_key: str = ""
    target_model: str = "llama-3.3-70b-versatile"

    def do_POST(self) -> None:
        content_length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if self.provider == "groq":
            self._handle_groq(payload)
        else:
            self._handle_openrouter(payload, body)

    def _handle_groq(self, payload: dict[str, Any]) -> None:
        if not self.groq_key:
            self._send_friendly_error(
                "⚠️ **GROQ_API_KEY Not Found in .env**\n\n"
                "To use the ultra-fast Groq LPU engine:\n"
                "1. Get a free API key at [console.groq.com/keys](https://console.groq.com/keys) (100% free, no credit card required).\n"
                "2. Add `GROQ_API_KEY=gsk_...` to your `.env` file.\n"
                "3. Restart the agent!"
            )
            return

        groq_model = self.target_model if self.target_model and "openrouter" not in self.target_model else "llama-3.3-70b-versatile"
        groq_payload = _anthropic_to_groq(payload, default_model=groq_model)
        forward_data = json.dumps(groq_payload).encode("utf-8")

        _log(f"[Proxy] Forwarding to Groq API (model={groq_model})")
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json",
            },
            data=forward_data,
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = resp.read()
                groq_json = json.loads(resp_data.decode("utf-8"))
                anthropic_resp = _groq_to_anthropic(groq_json, model_name=groq_model)
                out_bytes = json.dumps(anthropic_resp).encode("utf-8")
                _log(f"[Proxy] Groq responded 200 (tokens: {groq_json.get('usage', {})})")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(out_bytes)
        except urllib.error.HTTPError as err:
            err_data = err.read().decode("utf-8", errors="ignore")
            _log(f"[Proxy] Groq HTTP Error: {err.code} {err_data}")
            self._send_friendly_error(
                f"⚠️ **Groq API Error ({err.code})**\n\n"
                f"`{err_data}`\n\n"
                "Please verify your `GROQ_API_KEY` in `.env` or visit [console.groq.com](https://console.groq.com)."
            )
        except Exception as exc:
            _log(f"[Proxy] Groq connection error: {exc}")
            self._send_friendly_error(f"⚠️ **Groq Connection Error:** {exc}")

    def _handle_openrouter(self, payload: dict[str, Any], raw_body: bytes) -> None:
        show_thinking = os.getenv("SHOW_THINKING", "false").lower() in ("true", "1", "yes")
        try:
            payload["model"] = self.target_model
            payload["stream"] = False
            if not show_thinking:
                payload["reasoning"] = {"max_tokens": 0}

            for msg in payload.get("messages", []):
                c = msg.get("content")
                if isinstance(c, list):
                    msg["content"] = [b for b in c if not (isinstance(b, dict) and b.get("type") == "thinking")]

            forward_data = json.dumps(payload).encode("utf-8")
        except Exception:
            forward_data = raw_body

        _log(f"[Proxy] Forwarding to OpenRouter model={self.target_model}")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/messages",
            headers={
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            data=forward_data,
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                resp_data = resp.read()
                if not show_thinking:
                    try:
                        resp_json = json.loads(resp_data.decode("utf-8"))
                        if isinstance(resp_json, dict) and "content" in resp_json and isinstance(resp_json["content"], list):
                            resp_json["content"] = [b for b in resp_json["content"] if isinstance(b, dict) and b.get("type") != "thinking"]
                            for b in resp_json["content"]:
                                if isinstance(b, dict) and b.get("type") == "text" and "text" in b:
                                    b["text"] = re.sub(r"<think>.*?</think>", "", b["text"], flags=re.DOTALL).strip()
                        resp_data = json.dumps(resp_json).encode("utf-8")
                    except Exception:
                        pass
                _log(f"[Proxy] OpenRouter response: {resp.status} (bytes: {len(resp_data)})")
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp_data)
        except urllib.error.HTTPError as err:
            err_data = err.read()
            err_text = err_data.decode("utf-8", errors="ignore")
            _log(f"[Proxy] OpenRouter HTTP error: {err.code} {err_text}")
            if err.code == 429:
                self._send_friendly_error(
                    "⚠️ **OpenRouter Free Tier Limit Exceeded (50 requests/day)**\n\n"
                    "The daily quota for this free OpenRouter API key has been exhausted.\n\n"
                    "**Options to continue:**\n"
                    "1. **Switch to Groq (Recommended):** Add `GROQ_API_KEY=gsk_...` in `.env` (free at [console.groq.com/keys](https://console.groq.com/keys)).\n"
                    "2. **Set Anthropic Key:** Add `ANTHROPIC_API_KEY=sk-ant-...` in `.env`.\n"
                    "3. **New OpenRouter Key:** Generate a new key at [openrouter.ai](https://openrouter.ai/settings/keys)."
                )
                return
            self.send_response(err.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err_data)
        except Exception as exc:
            _log(f"[Proxy] OpenRouter connection error: {exc}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))

    def _send_friendly_error(self, message: str) -> None:
        friendly_msg = {
            "id": "msg_proxy_notice",
            "type": "message",
            "role": "assistant",
            "model": self.target_model,
            "content": [{"type": "text", "text": message}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }
        resp_bytes = json.dumps(friendly_msg).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(resp_bytes)

    def log_message(self, format: str, *args: object) -> None:
        pass


_server_instance: http.server.ThreadingHTTPServer | None = None
_server_port: int | None = None
_lock = threading.Lock()


def get_proxy_port(
    provider: str = "groq",
    groq_key: str = "",
    openrouter_key: str = "",
    model: str = "llama-3.3-70b-versatile",
) -> int:
    global _server_instance, _server_port
    with _lock:
        if _server_port is not None:
            return _server_port

        _ProxyHandler.provider = provider
        _ProxyHandler.groq_key = groq_key
        _ProxyHandler.openrouter_key = openrouter_key
        _ProxyHandler.target_model = model

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _ProxyHandler)
        _server_instance = server
        _server_port = server.server_port

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return _server_port


def get_openrouter_proxy_port(api_key: str, model: str = "openrouter/free") -> int:
    return get_proxy_port(provider="openrouter", openrouter_key=api_key, model=model)

