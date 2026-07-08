import pytest

from var_runner.guardrails import Guardrails, GuardrailViolation, HONESTY_TEMPLATE


def test_allowlist_pass():
    g = Guardrails()
    g.check_url("https://raw.githubusercontent.com/x/y/main/README.md")
    g.check_url("https://github.com/x/y")


def test_allowlist_block():
    g = Guardrails()
    with pytest.raises(GuardrailViolation):
        g.check_url("https://evil.example.com/data")
    with pytest.raises(GuardrailViolation):
        g.check_url("https://github.com.evil.com/x")  # suffix spoof


def test_call_budget():
    g = Guardrails(max_backend_calls=2)
    g.count_backend_call()
    g.count_backend_call()
    with pytest.raises(GuardrailViolation):
        g.count_backend_call()


def test_time_budget():
    g = Guardrails(max_minutes=0.0)
    g._start -= 1.0  # simulate 1s elapsed
    with pytest.raises(GuardrailViolation):
        g.check_budget()


def test_publication_needs_honesty():
    g = Guardrails()
    with pytest.raises(GuardrailViolation):
        g.check_publication("# Results\n\nEverything was great.")
    g.check_publication("# Results\n\n" + HONESTY_TEMPLATE)


def test_incident_entry_format():
    e = Guardrails.incident_entry("stale cache re-ran B13", "2026-07-07")
    assert e == "[2026-07-07] INCIDENT: stale cache re-ran B13"
