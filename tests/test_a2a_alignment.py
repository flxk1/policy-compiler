"""The compiled norms are shaped so the a2a-compliance grounding seam consumes them.

The consuming fleet reads a deontic projection (operator/bearer/action/condition/…) off
each norm and folds per-plane findings into a Grounding. This test builds those consumer
objects directly from the compiler's output.
"""

from __future__ import annotations

import json
import sys

import pytest

from conftest import A2A_REPO  # type: ignore
from policy_compiler import compile

# The keys loomground-deontic's project() emits; the seam expects exactly these.
_PROJECT_KEYS = {
    "operator", "bearer", "action", "condition",
    "exception", "negated", "incident", "counterparty",
}


def _load_a2a():
    if not (A2A_REPO / "interfaces" / "a2a_control.py").exists():
        pytest.skip(f"a2a-compliance not found at {A2A_REPO}")
    if str(A2A_REPO) not in sys.path:
        sys.path.insert(0, str(A2A_REPO))
    from interfaces.a2a_control import Grounding, PlaneFinding, SteerVerdict

    return Grounding, PlaneFinding, SteerVerdict


def test_projection_matches_deontic_shape(data_policy_path):
    c = compile(data_policy_path)
    assert c.norms
    for n in c.norms:
        proj = n.projected()
        assert set(proj.keys()) == _PROJECT_KEYS
        assert proj["operator"] in ("O", "P", "F")
        assert proj["bearer"] and proj["action"]


def test_norms_build_a2a_grounding_objects(data_policy_path):
    Grounding, PlaneFinding, SteerVerdict = _load_a2a()
    c = compile(data_policy_path)

    # Each norm becomes a deontic PlaneFinding the fleet can carry on a directive.
    findings = [
        PlaneFinding(plane="deontic", verdict=SteerVerdict.NOT_SATISFIED, detail=n.projected())
        for n in c.prohibitions()
    ]
    assert findings, "prohibitions should yield deontic findings"
    grounding = Grounding(
        verdict=SteerVerdict.NOT_SATISFIED,
        planes=findings,
        criterion_ref="policy-compiler/0.1",
    )
    assert grounding.planes[0].detail["operator"] == "F"
    assert grounding.verdict == SteerVerdict.NOT_SATISFIED


def test_grounding_seam_payload_is_serializable(data_policy_path):
    c = compile(data_policy_path)
    payload = c.to_grounding_seam()
    # A downstream consumer receives this over a channel; it must round-trip as JSON.
    restored = json.loads(json.dumps(payload))
    assert restored["mode"] in ("grounded", "advisory")
    assert restored["norms"]
    for norm in restored["norms"]:
        assert _PROJECT_KEYS.issubset(norm.keys())
        assert "provenance" in norm and "lg" in norm
    assert "conflicts" in restored and "residuals" in restored
