from var_runner.agenda import Agenda, cache_busted_url, parse_agenda

SAMPLE = """# RESEARCH AGENDA

## Queue

1. B14: third task family confirmatory sweep
- B15: crosstalk noise model
   continued detail line

## Log

- [2026-07-01] stale cache incident, guardrail added

## Guardrails

* no bar moved after data
* budgets enforced in code

## Unknown Section

- should be ignored
"""


def test_parse_sections():
    a = parse_agenda(SAMPLE)
    assert a.queue == [
        "B14: third task family confirmatory sweep",
        "B15: crosstalk noise model continued detail line",
    ]
    assert a.log == ["[2026-07-01] stale cache incident, guardrail added"]
    assert a.guardrails == ["no bar moved after data", "budgets enforced in code"]


def test_next_and_pop():
    a = parse_agenda(SAMPLE)
    assert a.next_item().startswith("B14")
    assert a.pop_item().startswith("B14")
    assert a.next_item().startswith("B15")
    empty = Agenda()
    assert empty.next_item() is None
    assert empty.pop_item() is None


def test_roundtrip():
    a = parse_agenda(SAMPLE)
    b = parse_agenda(a.to_markdown())
    assert (b.queue, b.log, b.guardrails) == (a.queue, a.log, a.guardrails)


def test_empty_agenda_markdown():
    md = Agenda().to_markdown()
    assert "## Queue" in md and "(empty)" in md


def test_cache_busted_url():
    assert cache_busted_url("https://x.com/a.md", ts=42) == "https://x.com/a.md?nocache=42"
    assert cache_busted_url("https://x.com/a.md?b=1", ts=42) == "https://x.com/a.md?b=1&nocache=42"
    assert "nocache=" in cache_busted_url("https://x.com/a.md")
