"""Anthropic backend (Claude models).

Credentials: reads ANTHROPIC_API_KEY from the environment at call time.
Optional ANTHROPIC_BASE_URL overrides the endpoint. Nothing is ever written
to disk and no key is bundled with this package.

HONEST STATUS: this module is written to the documented Messages API but has
NOT been exercised against the live API by the autonomous build loop (no key
was available to it, by design). Treat it as untested until a human runs it.
"""

from __future__ import annotations

import json
import os
import urllib.request

from var_runner.backends.base import Backend, BackendResponse, ToolCall

API_VERSION = "2023-06-01"
DEFAULT_BASE = "https://api.anthropic.com"


class AnthropicBackend(Backend):
    name = "anthropic"

    def __init__(self, model: str, max_tokens: int = 4096, timeout: float = 120.0):
        super().__init__(model)
        self.max_tokens = max_tokens
        self.timeout = timeout

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> BackendResponse:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set; refusing to call the API")
        base = os.environ.get("ANTHROPIC_BASE_URL", DEFAULT_BASE).rstrip("/")
        system = "\n".join(m["content"] for m in messages if m["role"] == "system") or None
        body: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [m for m in messages if m["role"] != "system"],
        }
        if system:
            body["system"] = system
        if tools:
            body["tools"] = tools
        req = urllib.request.Request(
            f"{base}/v1/messages",
            data=json.dumps(body).encode(),
            headers={
                "content-type": "application/json",
                "x-api-key": key,
                "anthropic-version": API_VERSION,
            },
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode())
        text_parts, calls = [], []
        for block in data.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block["text"])
            elif block.get("type") == "tool_use":
                calls.append(ToolCall(block["name"], block.get("input", {})))
        return BackendResponse("\n".join(text_parts), calls, raw=data)
