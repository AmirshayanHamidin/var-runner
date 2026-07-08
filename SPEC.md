# var-runner — Specification (M1)

A model-agnostic Python package that implements the Verified Autonomous
Research (VAR) loop mechanically. Governing method: the six VAR rules in
[qrc-shot-wall/PROTOCOL.md](https://github.com/AmirshayanHamidin/qrc-shot-wall/blob/main/PROTOCOL.md).

## Design principle

The rules are enforced **in code**, not in prompts. A model (any model) drives
the loop, but the loop refuses to proceed when a rule would be broken:
no execution without a frozen pre-registration, no publication without an
Honesty section, no network outside the allowlist, no bar moved after data.

## Modules

| Module | Responsibility |
| --- | --- |
| `agenda.py` | Git-based state. Parse/serialize `RESEARCH_AGENDA.md` (Queue / Log / Guardrails sections). Cache-busted read URLs (`cache_busted_url`). |
| `backends/base.py` | `Backend.chat(messages, tools) -> BackendResponse`. JSON-mode tool-calling shim (`parse_json_tool_call`, `tools_system_prompt`) for models without native tool calls. |
| `backends/anthropic.py` | Claude Messages API. Key from `ANTHROPIC_API_KEY` env var only. |
| `backends/ollama.py` | Local models via `/api/chat` (e.g. `qwen2.5-coder:32b`). Endpoint from `OLLAMA_HOST` env var. |
| `backends/mock.py` | Canned-response backend powering DRY-RUN mode (M2). |
| `loop.py` | The state machine: READ state → pick queue item → PLAN (pre-registered hypothesis + numeric bars, hash-frozen BEFORE experiments) → EXECUTE (timeouts/budget-checked) → EVALUATE vs frozen bars → PUBLISH results + agenda in one batch. |
| `guardrails.py` | Hard rules as code: network allowlist, time/call budgets, mandatory `## Honesty` section template, incident-log entry formatter. Violations raise `GuardrailViolation`. |
| `verify.py` | Post-push byte-for-byte comparison (`verify_bytes`) with sha256 and first-diff offset. Web commits can fail silently; nothing counts as published until re-fetched and byte-identical. |
| `cli.py` | `var run --repo --backend --model --max-minutes [--dry-run]`. |

## Rule → code mapping

1. **Pre-register or it didn't happen** → `VARLoop.register_plan` requires numeric bars; `Plan.freeze()` hashes them; `execute()`/`evaluate()` call `check_frozen()` and raise if the hash changed.
2. **Failures are results** → `Evaluation` reports pass/fail per bar; a failed bar is a normal return value, never an exception.
3. **The repo is the lab notebook** → `read_state` only reads the live remote (cache-busted); `publish_batch` publishes write-up + agenda in one batch or not at all.
4. **Honest baselines** → agenda guardrail entries are loaded as code-level checks; baseline-tuning parity is asserted in the plan template (M2).
5. **Audit mode** → `Agenda.next_item() is None` signals the runner to switch from generating to auditing (M2 orchestration).
6. **Human sign-off gate** → the package has no "submit externally" capability at all, by construction.

## Credentials policy

No credentials are stored, requested, or written by this package — keys and
endpoints come from environment variables (`ANTHROPIC_API_KEY`,
`ANTHROPIC_BASE_URL`, `OLLAMA_HOST`) at call time. The mock backend needs none.

## Milestones

- **M1 (this spec):** spec + skeleton + unit tests. Pure Python; everything testable without API calls.
- **M2:** end-to-end DRY-RUN mode — mock backend replays canned responses through a full READ→PUBLISH cycle.
- **M3:** README with honest limitations, MIT license, usage docs including Ollama (`qwen2.5-coder:32b`).
