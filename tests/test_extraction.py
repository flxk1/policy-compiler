"""Extraction: actors, permissions, prohibitions, obligations from synthetic policy text."""

from __future__ import annotations

from policy_compiler import compile


def test_extracts_the_three_forces(data_policy_path):
    c = compile(data_policy_path)
    # The fixture states a permission, obligations, and prohibitions.
    assert any(n.operator == "P" for n in c.norms), "no permission extracted"
    assert any(n.operator == "O" for n in c.norms), "no obligation extracted"
    assert any(n.operator == "F" for n in c.norms), "no prohibition extracted"


def test_permission_norm_shape(data_policy_path):
    c = compile(data_policy_path)
    perms = c.permissions()
    assert perms, "expected at least one permission"
    p = next(n for n in perms if "controller" in n.bearer.lower())
    assert p.operator == "P"
    assert "process" in p.action.lower()
    assert p.lg.startswith("P(")


def test_condition_and_deadline_are_lifted(data_policy_path):
    c = compile(data_policy_path)
    notify = next(n for n in c.norms if "notify" in n.action.lower())
    assert notify.operator == "O"
    assert notify.deadline, "deadline should be lifted out of the action"
    assert "72" in notify.deadline
    assert notify.cross_references, "the Article reference should be captured"
    assert any("33" in ref for ref in notify.cross_references)
    # The deadline phrase must not remain in the action string.
    assert "72" not in notify.action


def test_conditional_norms_carry_their_condition(data_policy_path):
    c = compile(data_policy_path)
    delete = next(
        n for n in c.norms if n.operator == "O" and "delete" in n.action.lower()
    )
    assert delete.condition, "the 'when a contract terminates' clause should be a condition"


def test_actors_are_collected(data_policy_path):
    c = compile(data_policy_path)
    names = {a.name.lower() for a in c.actors}
    assert "controller" in names
    assert "processor" in names
    assert any(a.as_bearer for a in c.actors)
