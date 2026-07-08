"""Command-line interface:  var run --repo <owner/name> --backend <b> --model <m> --max-minutes <n>"""

from __future__ import annotations

import argparse
import sys

from var_runner.backends import get_backend
from var_runner.guardrails import Guardrails
from var_runner.loop import VARLoop


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="var", description="Run the Verified Autonomous Research loop.")
    sub = p.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="execute one VAR loop increment")
    run.add_argument("--repo", required=True, help="GitHub repo, e.g. owner/name")
    run.add_argument("--backend", default="mock", choices=["anthropic", "ollama", "mock"])
    run.add_argument("--model", default="mock", help="model name, e.g. qwen2.5-coder:32b")
    run.add_argument("--max-minutes", type=float, default=30.0)
    run.add_argument("--dry-run", action="store_true",
                     help="mock everything; prove loop mechanics without keys or network")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        backend = get_backend(args.backend, args.model)
        guardrails = Guardrails(max_minutes=args.max_minutes)
        loop = VARLoop(backend, guardrails, dry_run=args.dry_run)
        # M1 scope: wiring only. The full run orchestration (agenda fetch,
        # plan generation via backend, code execution sandbox) lands in M2.
        print(f"var-runner {args.backend}:{args.model} on {args.repo} "
              f"(dry_run={args.dry_run}, budget={args.max_minutes} min) — loop initialized: {type(loop).__name__}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
