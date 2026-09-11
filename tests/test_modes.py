"""Grounded mode and advisory mode both work, and provenance is honest in each."""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from policy_compiler import compile, planes


def test_grounded_mode_marks_norms_grounded(data_policy_path):
    if not planes.available("norm") or not planes.available("deontic"):
        import pytest

        pytest.skip("loomground planes not installed in this environment")
    c = compile(data_policy_path)
    assert c.mode == "grounded"
    assert "deontic" in c.planes_used
    assert all(n.grounded for n in c.norms)
    assert all("deontic" in n.grounded_via for n in c.norms)


def test_advisory_mode_marks_norms_advisory(data_policy_path):
    planes.disable()
    c = compile(data_policy_path)
    assert c.mode == "advisory"
    assert c.planes_used == []
    assert all(not n.grounded for n in c.norms)
    assert all(n.provenance == "advisory" for n in c.norms)
    # The advisory path still extracts the same forces.
    assert any(n.operator == "P" for n in c.norms)
    assert any(n.operator == "F" for n in c.norms)


def test_no_hard_loomground_dependency_on_bare_path():
    """With every loomground module made unimportable, the compiler still runs and
    degrades to advisory. This proves the bare path carries no hard dependency."""
    script = textwrap.dedent(
        """
        import sys
        BLOCK = {"deontic", "loomground_norm", "loomground_ingest",
                 "loomground_governance", "versum", "loomground_solver"}

        class Blocker:
            def find_spec(self, name, path=None, target=None):
                root = name.split(".")[0]
                if root in BLOCK:
                    raise ModuleNotFoundError(name)
                return None

        sys.meta_path.insert(0, Blocker())
        for m in list(sys.modules):
            if m.split(".")[0] in BLOCK:
                del sys.modules[m]

        import policy_compiler
        c = policy_compiler.compile(
            "The vendor must not share credentials. The user may reset a password."
        )
        assert c.mode == "advisory", c.mode
        assert c.planes_used == [], c.planes_used
        ops = {n.operator for n in c.norms}
        assert "F" in ops and "P" in ops, ops
        print("OK")
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]),
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_a_present_deontic_plane_receives_its_own_modal_names():
    """The plane fails closed on an unknown modal (deontic >=0.2): send its class names."""
    deo = pytest.importorskip("deontic")
    from policy_compiler.lower import _build_formula

    f = _build_formula({"operator": "F", "bearer": "maker", "action": "delete the audit trail"})
    assert f is not None and f.operator == "F"
    assert deo.name("F") in deo.MODAL_TO_OP
