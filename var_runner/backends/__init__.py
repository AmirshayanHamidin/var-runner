"""Backend registry. Keys and endpoints come from environment variables only —
this package never stores, requests, or writes credentials.

    anthropic : ANTHROPIC_API_KEY (required), ANTHROPIC_BASE_URL (optional)
    ollama    : OLLAMA_HOST (optional, default http://localhost:11434)
    mock      : no environment needed; replays canned responses (dry-run mode)
"""

from __future__ import annotations

from var_runner.backends.base import Backend, BackendResponse, ToolCall


def get_backend(name: str, model: str) -> Backend:
    if name == "anthropic":
        from var_runner.backends.anthropic import AnthropicBackend
        return AnthropicBackend(model=model)
    if name == "ollama":
        from var_runner.backends.ollama import OllamaBackend
        return OllamaBackend(model=model)
    if name == "mock":
        from var_runner.backends.mock import MockBackend
        return MockBackend(model=model)
    raise ValueError(f"unknown backend {name!r}; expected anthropic|ollama|mock")


__all__ = ["Backend", "BackendResponse", "ToolCall", "get_backend"]
