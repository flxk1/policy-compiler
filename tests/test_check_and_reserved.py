"""check() runs cases against the compiled norms; the compiler never activates."""

from __future__ import annotations

import policy_compiler
from policy_compiler import check, compile


def test_check_resolves_each_force(data_policy_path):
    cases = [
        {"actor": "controller", "action": "process personal data", "expect": "permitted"},
        {"actor": "staff", "action": "sharing account credentials", "expect": "forbidden"},
        {"actor": "processor", "action": "notify the controller", "expect": "obligatory"},
        {"actor": "auditor", "action": "publish the report", "expect": "undetermined"},
    ]
    report = check(data_policy_path, cases)
    assert report.ok, [(r.actor, r.expected, r.got) for r in report.results if not r.passed]
    assert report.total == 4 and report.passed == 4


def test_check_reports_conflict_as_a_verdict(data_policy_path):
    # The processor is both obliged and forbidden to delete personal data.
    report = check(data_policy_path, [
        {"actor": "processor", "action": "delete personal data", "expect": "forbidden"},
    ])
    # The clash resolves to 'conflict', not a single force — so the expectation fails,
    # and the result names the conflict honestly.
    assert not report.ok
    assert report.results[0].got == "conflict"


def test_check_accepts_an_already_compiled_policy(data_policy_path):
    compiled = compile(data_policy_path)
    report = check(compiled, [
        {"actor": "controller", "action": "process", "expect": "permitted"},
    ])
    assert report.total == 1


def test_compiler_never_activates():
    # The compiler's public surface stops at a validated draft: there is no apply,
    # activate, ratify, or store-writing entry point.
    for reserved in ("apply", "activate", "ratify", "sign", "commit", "write"):
        assert not hasattr(policy_compiler, reserved), (
            f"compiler must not expose a reserved activation verb: {reserved}"
        )
    compiled = compile("The vendor must not share credentials.")
    for reserved in ("apply", "activate", "ratify"):
        assert not hasattr(compiled, reserved)
