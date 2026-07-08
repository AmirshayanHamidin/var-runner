"""Hard rules as code (VAR rules 1, 2, 5).

Guardrails are enforced mechanically, not by prompt text: network allowlist,
time/call budgets, a mandatory Honesty section in every publication, and an
incident-log appender. Violations raise GuardrailViolation; the loop treats a
violation as a failed run to be reported, never silently retried.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

HONESTY_HEADING = "## Honesty"

HONESTY_TEMPLATE = """## Honesty

- What was pre-registered (hypothesis + numeric bars, committed before data):
- What the data showed vs the bars (pass/fail per bar, no bar moved):
- What did NOT work or did not reproduce:
- Limitations and untested assumptions:
"""


class GuardrailViolation(RuntimeError):
    """A hard rule was broken. The loop must stop and report, not retry."""


@dataclass
class Guardrails:
    allowed_hosts: list[str] = field(default_factory=lambda: ["github.com", "raw.githubusercontent.com"])
    max_minutes: float = 30.0
    max_backend_calls: int = 50
    _start: float = field(default_factory=time.monotonic)
    _calls: int = 0

    def check_url(self, url: str) -> None:
        host = urlparse(url).hostname or ""
        if not any(host == h or host.endswith("." + h) for h in self.allowed_hosts):
            raise GuardrailViolation(f"network allowlist: host {host!r} not in {self.allowed_hosts}")

    def check_budget(self) -> None:
        elapsed_min = (time.monotonic() - self._start) / 60.0
        if elapsed_min > self.max_minutes:
            raise GuardrailViolation(f"time budget exceeded: {elapsed_min:.1f} > {self.max_minutes} min")
        if self._calls > self.max_backend_calls:
            raise GuardrailViolation(f"backend call budget exceeded: {self._calls} > {self.max_backend_calls}")

    def count_backend_call(self) -> None:
        self._calls += 1
        self.check_budget()

    def check_publication(self, markdown: str) -> None:
        """Every published write-up must carry a filled Honesty section (VAR rule 2)."""
        if HONESTY_HEADING not in markdown:
            raise GuardrailViolation("publication rejected: missing mandatory '## Honesty' section")

    @staticmethod
    def incident_entry(description: str, ts: str) -> str:
        """Format an incident-log entry (VAR rule 5: incidents become guardrails)."""
        return f"[{ts}] INCIDENT: {description}"
