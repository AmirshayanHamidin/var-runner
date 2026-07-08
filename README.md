# var-runner

A model-agnostic Python package that runs the **Verified Autonomous Research
(VAR) loop** mechanically. The six VAR rules — pre-registration with numeric
bars before any experiment, failures published as results, public git as the
only lab notebook, honest baselines, mandatory audit mode, human sign-off —
are enforced **in code**, not in prompts.

Governing method: [PROTOCOL.md](https://github.com/AmirshayanHamidin/qrc-shot-wall/blob/main/PROTOCOL.md)
in qrc-shot-wall (case study #1 of the protocol). Full design: [SPEC.md](SPEC.md).

## Quickstart (no API key needed)

```
pip install -e ".[test]"
python -m pytest tests/          # 26 unit tests, pure Python
python -m var_runner.cli run --repo owner/name --backend mock --dry-run
```

Backends: `anthropic` (key from `ANTHROPIC_API_KEY` env var), `ollama`
(endpoint from `OLLAMA_HOST`, e.g. `qwen2.5-coder:32b`), `mock` (canned
responses, no network). **No credentials are stored or requested by this
package — environment variables only.**

## HONEST STATUS OF LIVE BACKENDS

The `anthropic` and `ollama` modules are written to their documented APIs but
have **not been exercised against live endpoints** by the autonomous loop that
builds this repo (it has no keys, by design). They are untested until a human
runs them. The mock backend and all loop mechanics ARE tested.

## STATUS

*Maintained by the autonomous build loop. Read this section first each run
(cache-busted). This section is ground truth.*

### Milestones

- [x] **M1 — spec + skeleton + unit tests** (LANDED 2026-07-07: built & tested
  in run 1, published + verified 19/19 files byte-for-byte same day):
  `SPEC.md`, package modules (`agenda`, `guardrails`, `verify`, `loop`,
  `cli`, `backends/{base,anthropic,ollama,mock}`), 26 passing tests
  (`tests/`), `pyproject.toml`. All pure Python, no API calls needed.
- [ ] **M2 — end-to-end DRY-RUN mode**: orchestrate a full READ→PLAN→EXECUTE→
  EVALUATE→PUBLISH cycle in `cli.py` using MockBackend canned responses;
  integration test proving the cycle; audit-mode switch when queue empty.
- [ ] **M3 — docs**: README honest-limitations section, MIT LICENSE file,
  usage docs incl. Ollama (`qwen2.5-coder:32b`) walkthrough.
- [ ] **Project 3 (after M3)**: mine qrc-shot-wall history into
  `study/dataset/` (research-state → next pre-registration pairs, JSON);
  write `study/PREREG.md` (H1 +30pp rubric bar; H2 expected honest negative);
  CPU pilot only if feasible in 45s chunks, else `study/COLAB_INSTRUCTIONS.md`.

### Next step

M2: wire `VARLoop` orchestration into `cli.py` with a canned-response script
for MockBackend; add `tests/test_e2e_dryrun.py`.

### Incident log

- [2026-07-07] INCIDENT: run 1 could not publish to GitHub — browser
  extension disconnected and no user present to grant desktop access; no git
  credentials exist by design. M1 built and 26/26 tests passed locally;
  checksums recorded in RUN_REPORT_2026-07-07.md. Guardrail: verify Chrome
  connectivity at run start before building, and always record checksums.
  RESOLVED same day: user re-opened the browser; repo created, all 19 files
  pushed in 4 commits and verified byte-for-byte (SHA-256) via cache-busted
  raw re-fetch. M1 is landed.

## Layout

```
var_runner/           the package
  agenda.py           RESEARCH_AGENDA.md parse/serialize, cache-busted reads
  guardrails.py       hard rules as code (allowlist, budgets, Honesty gate)
  verify.py           post-push byte-for-byte verification
  loop.py             READ→PLAN→EXECUTE→EVALUATE→PUBLISH state machine
  cli.py              var run --repo --backend --model --max-minutes
  backends/           anthropic | ollama | mock (env-var config only)
tests/                26 unit tests (no network, no keys)
SPEC.md               full M1 specification and rule→code mapping
```

---

*Amirshayan Hamidin, 2026. Built autonomously under the VAR protocol.*
