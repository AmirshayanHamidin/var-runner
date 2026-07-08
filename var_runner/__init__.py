"""var-runner: a model-agnostic runner for the Verified Autonomous Research (VAR) loop.

Implements the six VAR rules mechanically (see PROTOCOL.md in
github.com/AmirshayanHamidin/qrc-shot-wall): pre-registration before execution,
failures-as-results, git-as-lab-notebook, honest baselines, audit mode, and a
human sign-off gate.

No credentials are stored in this package. API keys and endpoints come
exclusively from environment variables (see backends/).
"""

__version__ = "0.1.0"

from var_runner.agenda import Agenda, parse_agenda, cache_busted_url
from var_runner.guardrails import Guardrails, GuardrailViolation
from var_runner.verify import verify_bytes, sha256_hex, VerifyResult

__all__ = [
    "Agenda",
    "parse_agenda",
    "cache_busted_url",
    "Guardrails",
    "GuardrailViolation",
    "verify_bytes",
    "sha256_hex",
    "VerifyResult",
]
