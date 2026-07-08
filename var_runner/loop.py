"""The VAR loop state machine.

    READ state -> pick queue item -> PLAN (pre-registered hypothesis + numeric
    bars, committed BEFORE experiments) -> EXECUTE (generated code, with
    timeouts/chunking) -> EVALUATE vs the bars -> PUBLISH results + updated
    agenda in one batch.

Mechanical enforcement of VAR rule 1: the plan is hashed and frozen before
execute() may run; evaluate() compares against the frozen bars, and any
attempt to alter bars after registration raises GuardrailViolation.

This module deliberately does not know how to talk to git hosting; the runner
supplies `fetch` (url -> bytes) and `publish` (dict of path -> bytes) callables,
so the same loop works over the GitHub web editor, a local clone, or a dry run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from var_runner.agenda import Agenda, parse_agenda
from var_runner.backends.base import Backend
from var_runner.guardrails import Guardrails, GuardrailViolation, HONESTY_TEMPLATE
from var_runner.verify import sha256_hex


@dataclass
class Plan:
    item: str
    hypothesis: str
    bars: dict[str, float]  # metric name -> numeric bar, frozen at registration
    _frozen_hash: str = field(default="", repr=False)

    def freeze(self) -> str:
        payload = json.dumps(
            {"item": self.item, "hypothesis": self.hypothesis, "bars": self.bars},
            sort_keys=True,
        ).encode()
        self._frozen_hash = sha256_hex(payload)
        return self._frozen_hash

    def check_frozen(self) -> None:
        if not self._frozen_hash:
            raise GuardrailViolation("plan was never frozen: pre-register before executing")
        if self.freeze_hash_now() != self._frozen_hash:
            raise GuardrailViolation("bars were modified after registration (VAR rule 1)")

    def freeze_hash_now(self) -> str:
        payload = json.dumps(
            {"item": self.item, "hypothesis": self.hypothesis, "bars": self.bars},
            sort_keys=True,
        ).encode()
        return sha256_hex(payload)


@dataclass
class Evaluation:
    passed: dict[str, bool]
    observed: dict[str, float]

    @property
    def all_passed(self) -> bool:
        return all(self.passed.values())


class VARLoop:
    def __init__(self, backend: Backend, guardrails: Guardrails,
                 fetch=None, publish=None, dry_run: bool = False):
        self.backend = backend
        self.guardrails = guardrails
        self.fetch = fetch
        self.publish = publish
        self.dry_run = dry_run
        self.plan: Plan | None = None

    # -- READ ---------------------------------------------------------------
    def read_state(self, agenda_url: str) -> Agenda:
        self.guardrails.check_url(agenda_url)
        raw = self.fetch(agenda_url)
        return parse_agenda(raw.decode("utf-8"))

    # -- PLAN ---------------------------------------------------------------
    def register_plan(self, item: str, hypothesis: str, bars: dict[str, float]) -> Plan:
        if not bars:
            raise GuardrailViolation("pre-registration requires at least one numeric bar")
        if not all(isinstance(v, (int, float)) for v in bars.values()):
            raise GuardrailViolation("all bars must be numeric")
        self.plan = Plan(item=item, hypothesis=hypothesis, bars=dict(bars))
        self.plan.freeze()
        return self.plan

    # -- EXECUTE ------------------------------------------------------------
    def execute(self, run_experiment) -> dict[str, float]:
        """run_experiment() -> {metric: observed_value}. Requires a frozen plan."""
        if self.plan is None:
            raise GuardrailViolation("no plan registered: PLAN must precede EXECUTE")
        self.plan.check_frozen()
        self.guardrails.check_budget()
        return dict(run_experiment())

    # -- EVALUATE -----------------------------------------------------------
    def evaluate(self, observed: dict[str, float]) -> Evaluation:
        self.plan.check_frozen()
        passed = {}
        for metric, bar in self.plan.bars.items():
            if metric not in observed:
                raise GuardrailViolation(f"metric {metric!r} was pre-registered but not measured")
            passed[metric] = observed[metric] >= bar
        return Evaluation(passed=passed, observed=observed)

    # -- PUBLISH ------------------------------------------------------------
    def publish_batch(self, files: dict[str, bytes], writeup_path: str) -> None:
        """Publish results + agenda in ONE batch (VAR rule 3). The write-up
        must contain a filled Honesty section (rule 2)."""
        if writeup_path not in files:
            raise GuardrailViolation(f"write-up {writeup_path!r} missing from publish batch")
        self.guardrails.check_publication(files[writeup_path].decode("utf-8"))
        if self.dry_run:
            return
        self.publish(files)

    @staticmethod
    def honesty_template() -> str:
        return HONESTY_TEMPLATE
