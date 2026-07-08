import pytest

from var_runner.backends.base import parse_json_tool_call
from var_runner.backends.mock import MockBackend
from var_runner.guardrails import Guardrails, GuardrailViolation, HONESTY_TEMPLATE
from var_runner.loop import VARLoop

AGENDA = b"""## Queue\n\n- item one\n\n## Log\n\n## Guardrails\n\n- rule\n"""


def make_loop(**kw):
    published = {}
    loop = VARLoop(
        MockBackend(), Guardrails(),
        fetch=lambda url: AGENDA,
        publish=lambda files: published.update(files),
        **kw,
    )
    return loop, published


def test_read_state():
    loop, _ = make_loop()
    a = loop.read_state("https://raw.githubusercontent.com/x/y/main/RESEARCH_AGENDA.md?nocache=1")
    assert a.next_item() == "item one"


def test_read_state_blocked_host():
    loop, _ = make_loop()
    with pytest.raises(GuardrailViolation):
        loop.read_state("https://elsewhere.net/agenda.md")


def test_execute_requires_registered_plan():
    loop, _ = make_loop()
    with pytest.raises(GuardrailViolation):
        loop.execute(lambda: {"acc": 0.9})


def test_bars_frozen_before_execute():
    loop, _ = make_loop()
    loop.register_plan("item one", "H1: acc improves", {"acc": 0.8})
    loop.plan.bars["acc"] = 0.1  # tamper after registration
    with pytest.raises(GuardrailViolation):
        loop.execute(lambda: {"acc": 0.9})


def test_full_cycle_pass_and_fail():
    loop, _ = make_loop()
    loop.register_plan("item one", "H1", {"acc": 0.8, "nmse_neg": -0.1})
    observed = loop.execute(lambda: {"acc": 0.85, "nmse_neg": -0.5})
    ev = loop.evaluate(observed)
    assert ev.passed == {"acc": True, "nmse_neg": False}
    assert not ev.all_passed  # failures are results, not errors


def test_missing_metric_is_violation():
    loop, _ = make_loop()
    loop.register_plan("item one", "H1", {"acc": 0.8})
    with pytest.raises(GuardrailViolation):
        loop.evaluate({"other": 1.0})


def test_registration_requires_numeric_bars():
    loop, _ = make_loop()
    with pytest.raises(GuardrailViolation):
        loop.register_plan("i", "H", {})
    with pytest.raises(GuardrailViolation):
        loop.register_plan("i", "H", {"acc": "high"})


def test_publish_requires_honesty_and_batches():
    loop, published = make_loop()
    files = {"RESULTS.md": b"# R\n\nno honesty here"}
    with pytest.raises(GuardrailViolation):
        loop.publish_batch(files, "RESULTS.md")
    files["RESULTS.md"] = ("# R\n\n" + HONESTY_TEMPLATE).encode()
    loop.publish_batch(files, "RESULTS.md")
    assert "RESULTS.md" in published


def test_dry_run_publishes_nothing():
    loop, published = make_loop(dry_run=True)
    files = {"RESULTS.md": ("# R\n\n" + HONESTY_TEMPLATE).encode()}
    loop.publish_batch(files, "RESULTS.md")
    assert published == {}


def test_json_tool_shim():
    call = parse_json_tool_call('prefix {"tool": "run", "arguments": {"x": 1}} suffix')
    assert call.name == "run" and call.arguments == {"x": 1}
    assert parse_json_tool_call("no json here") is None
    assert parse_json_tool_call('{"not_a_tool": 1}') is None


def test_mock_backend_replays_and_exhausts():
    mb = MockBackend(responses=["one", "two"])
    assert mb.chat([{"role": "user", "content": "a"}]).text == "one"
    assert mb.chat([{"role": "user", "content": "b"}]).text == "two"
    with pytest.raises(RuntimeError):
        mb.chat([{"role": "user", "content": "c"}])
