"""Conflicts, undetermined rules, and residual spans are surfaced, not swallowed."""

from __future__ import annotations

from policy_compiler import compile, planes


def test_conflict_is_surfaced(data_policy_path):
    # The fixture obliges and forbids the processor to delete personal data.
    c = compile(data_policy_path)
    assert c.conflicts, "the O-vs-F clash on 'delete personal data' should be flagged"
    clash = c.conflicts[0]
    assert {clash.operator_a, clash.operator_b} == {"O", "F"}
    assert "delete" in clash.action.lower()
    assert clash.resolution == "candidate-escalate"


def test_conflict_surfaced_in_advisory_mode(data_policy_path):
    planes.disable()
    c = compile(data_policy_path)
    assert c.mode == "advisory"
    assert any({x.operator_a, x.operator_b} == {"O", "F"} for x in c.conflicts)


def test_residuals_are_surfaced(data_policy_path):
    c = compile(data_policy_path)
    assert c.residuals, "normative spans with no extractable norm should be residuals"
    joined = " ".join(r.text.lower() for r in c.residuals)
    # These normative sentences carry no modal the lowering can place.
    assert "mandatory" in joined or "responsible" in joined


def test_undetermined_or_residual_for_subjectless_duty():
    # A modal with no subject cannot resolve a bearer; it must not become a silent norm.
    planes.disable()
    c = compile("Must retain audit logs for one year.")
    assert not c.norms, "a subjectless duty is not a well-formed norm"
    assert c.undetermined or c.residuals


def test_nothing_is_silently_dropped(data_policy_path):
    c = compile(data_policy_path)
    # Every normative sentence lands somewhere: a norm, an undetermined rule, or a residual.
    accounted = len(c.norms) + len(c.undetermined) + len(c.residuals)
    assert accounted >= 6
