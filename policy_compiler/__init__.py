"""policy-compiler — read a written policy, produce executable governance norms.

The compiler extracts a policy's actors, permissions, prohibitions, and obligations;
lowers them to grounded deontic norms (O/P/F with bearer, action, and conditions) by
delegating to the loomground planes; surfaces conflicts, undetermined rules, and residual
spans; and runs test cases against the result. It stops at a validated draft. Activation
is a reserved human step; the compiler never applies or activates a policy.
"""

from __future__ import annotations

from .check import check, resolve
from .compile import compile
from .model import (
    Actor,
    CaseResult,
    CheckReport,
    CompiledPolicy,
    Conflict,
    Norm,
    Residual,
    Span,
    Undetermined,
)

__all__ = [
    "compile",
    "check",
    "resolve",
    "CompiledPolicy",
    "Norm",
    "Conflict",
    "Undetermined",
    "Residual",
    "Actor",
    "Span",
    "CaseResult",
    "CheckReport",
]

__version__ = "0.3.0"  # x-release-please-version
