"""Mock backend for end-to-end DRY-RUN mode (milestone M2).

Replays canned responses in order — proves the loop mechanics (read state ->
plan -> execute -> evaluate -> publish) without any API key or network access.
"""

from __future__ import annotations

from var_runner.backends.base import Backend, BackendResponse, parse_json_tool_call


class MockBackend(Backend):
    name = "mock"

    def __init__(self, model: str = "mock", responses: list[str] | None = None):
        super().__init__(model)
        self.responses = list(responses or [])
        self.calls: list[list[dict]] = []  # transcript of what was asked

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> BackendResponse:
        self.calls.append(messages)
        if not self.responses:
            raise RuntimeError("MockBackend exhausted: no canned responses left")
        text = self.responses.pop(0)
        call = parse_json_tool_call(text) if tools else None
        return BackendResponse(text, [call] if call else [], raw=None)
