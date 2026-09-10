from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

FIXTURES = _REPO / "tests" / "fixtures"
# The consuming fleet's interface package lives in the sibling repo.
A2A_REPO = _REPO.parent / "a2a-compliance"


@pytest.fixture
def data_policy_path() -> str:
    return str(FIXTURES / "data_policy.txt")


@pytest.fixture(autouse=True)
def _reset_planes():
    """Every test starts with planes enabled; a test that wants advisory mode disables
    them explicitly. State is reset afterwards so tests do not leak modes into each
    other."""
    from policy_compiler import planes

    planes.enable()
    yield
    planes.enable()
