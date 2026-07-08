"""Model-agnostic backend interface.

A backend turns a message list into a BackendResponse. Tool calling is
normalized to a JSON-mode shim: backends that lack native tool calling are
instructed to reply with a single JSON object {"tool": name, "arguments": {...}}
which parse_json_tool_call() extracts.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class BackendResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: object = None


class Backend:
    """Subclasses implement chat(). They must read credentials from env vars
    only, and must count every call against Guardrails when one is supplied."""

    name = "base"

    def __init__(self, model: str):
        self.model = model

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> BackendResponse:
        raise NotImplementedError


_JSON_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)


def parse_json_tool_call(text: str) -> ToolCall | None:
    """JSON-mode tool-calling shim: extract {"tool": ..., "arguments": {...}}
    from a model reply. Returns None if no well-formed call is present."""
    m = _JSON_OBJ_RE.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(obj, dict) and isinstance(obj.get("tool"), str) and isinstance(obj.get("arguments"), dict):
        return ToolCall(obj["tool"], obj["arguments"])
    return None


def tools_system_prompt(tools: list[dict]) -> str:
    """Prompt fragment teaching a JSON-only model to emit tool calls."""
    specs = json.dumps(tools, indent=2)
    return (
        "You can call tools. To call one, reply with ONLY a JSON object:\n"
        '{"tool": "<name>", "arguments": {...}}\n'
        f"Available tools:\n{specs}\n"
        "If no tool is needed, reply with plain text."
    )
