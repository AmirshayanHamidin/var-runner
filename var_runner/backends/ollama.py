"""Ollama backend (local models, e.g. qwen2.5-coder:32b).

Credentials/endpoint: reads OLLAMA_HOST from the environment (default
http://localhost:11434). No key needed; nothing external is contacted.

Tool calling uses the JSON-mode shim (format="json" + a system prompt from
tools_system_prompt), because small local models are more reliable at emitting
one JSON object than at native tool-call protocols.

HONEST STATUS: written to the documented /api/chat interface but NOT exercised
against a live Ollama server by the autonomous build loop (none was available
to it). Treat it as untested until a human runs it.
"""

from __future__ import annotations

import json
import os
import urllib.request

from var_runner.backends.base import (
    Backend,
    BackendResponse,
    parse_json_tool_call,
    tools_system_prompt,
)

DEFAULT_HOST = "http://localhost:11434"


class OllamaBackend(Backend):
    name = "ollama"

    def __init__(self, model: str, timeout: float = 600.0):
        super().__init__(model)
        self.timeout = timeout

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> BackendResponse:
        host = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).rstrip("/")
        msgs = list(messages)
        body: dict = {"model": self.model, "messages": msgs, "stream": False}
        if tools:
            msgs.insert(0, {"role": "system", "content": tools_system_prompt(tools)})
            body["format"] = "json"
        req = urllib.request.Request(
            f"{host}/api/chat",
            data=json.dumps(body).encode(),
            headers={"content-type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode())
        text = data.get("message", {}).get("content", "")
        calls = []
        if tools:
            call = parse_json_tool_call(text)
            if call:
                calls.append(call)
        return BackendResponse(text, calls, raw=data)
