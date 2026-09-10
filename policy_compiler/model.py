"""Data model for a compiled policy.

The compiler's output is a validated draft, never an applied one. A `CompiledPolicy`
carries the extracted deontic norms, the conflicts and undetermined rules the
extraction surfaced, the residual spans it could not place, and per-norm provenance
recording whether a norm was grounded through a loomground plane or produced by the
advisory fallback.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


# Deontic operators, in the governance vocabulary: obligation, permission, prohibition.
OP_OBLIGATION = "O"
OP_PERMISSION = "P"
OP_PROHIBITION = "F"
VALID_OPERATORS = (OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION)

# Provenance tags. A norm is grounded when a loomground plane produced or verified it;
# advisory when the built-in fallback did, with no plane present to ground it.
PROV_GROUNDED = "grounded"
PROV_ADVISORY = "advisory"


@dataclass
class Span:
    """A stretch of the source text, kept so every derived object can cite its origin."""

    start: int
    end: int
    text: str


@dataclass
class Norm:
    """One executable governance norm: an O/P/F force bound to a bearer and an action,
    scoped by a condition and an exception.

    `projected` mirrors the loomground-deontic projection shape, which is the shape the
    a2a-compliance grounding seam consumes directly.
    """

    operator: str  # one of VALID_OPERATORS
    bearer: str
    action: str
    condition: str = ""
    exception: str = ""
    negated: bool = False
    deadline: str = ""
    counterparty: str = ""
    incident: str = ""
    cross_references: list[str] = field(default_factory=list)
    lg: str = ""  # the rendered .lg line
    provenance: str = PROV_ADVISORY
    grounded_via: list[str] = field(default_factory=list)  # planes that grounded this norm
    confidence: float = 0.0
    source: Optional[Span] = None

    @property
    def grounded(self) -> bool:
        return self.provenance == PROV_GROUNDED

    def projected(self) -> dict:
        """The loomground-deontic projection shape. This is what a downstream deontic
        consumer reads: operator/bearer/action/condition/exception/negated/incident/
        counterparty."""
        return {
            "operator": self.operator,
            "bearer": self.bearer,
            "action": self.action,
            "condition": self.condition,
            "exception": self.exception,
            "negated": self.negated,
            "incident": self.incident,
            "counterparty": self.counterparty,
        }


@dataclass
class Conflict:
    """A candidate normative conflict: incompatible forces on the same bearer and action.
    Flagged for oversight, never resolved by the compiler."""

    kind: str
    bearer: str
    action: str
    operator_a: str
    operator_b: str
    formula_a: str
    formula_b: str
    resolution: str = "candidate-escalate"
    confidence: float = 0.0


@dataclass
class Undetermined:
    """A statement that carries a deontic force but does not resolve to a well-formed
    duty — a missing bearer or action. Surfaced for a human to complete; not emitted as
    an enforceable norm."""

    reason: str
    detected_operator: str
    partial_bearer: str
    partial_action: str
    source: Optional[Span] = None


@dataclass
class Residual:
    """A span the lowering could not place as a norm. A meaning with no construct is
    surfaced here, never fabricated into a norm."""

    text: str
    note: str
    source: Optional[Span] = None


@dataclass
class Actor:
    """A party the policy governs or refers to, with the roles it plays across norms."""

    name: str
    as_bearer: bool = False
    as_counterparty: bool = False


@dataclass
class CompiledPolicy:
    """The validated draft. It is authored, not activated: applying or ratifying it is a
    reserved step outside the compiler."""

    norms: list[Norm] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    undetermined: list[Undetermined] = field(default_factory=list)
    residuals: list[Residual] = field(default_factory=list)
    actors: list[Actor] = field(default_factory=list)
    mode: str = "advisory"  # "grounded" when any plane grounded the extraction
    planes_used: list[str] = field(default_factory=list)
    source_chars: int = 0

    # Norms grouped by the four things a reader of a policy looks for.
    def obligations(self) -> list[Norm]:
        return [n for n in self.norms if n.operator == OP_OBLIGATION]

    def permissions(self) -> list[Norm]:
        return [n for n in self.norms if n.operator == OP_PERMISSION]

    def prohibitions(self) -> list[Norm]:
        return [n for n in self.norms if n.operator == OP_PROHIBITION]

    def to_grounding_seam(self) -> dict:
        """Emit the norms in the shape the a2a-compliance grounding seam consumes: each
        norm as its deontic projection plus its .lg form and honest provenance. The
        `deontic`/`norm`/`mandate` planes on the consuming side read O/P/F force, bearer,
        action, and condition off this payload."""
        return {
            "protocol": "policy-compiler/0.1",
            "mode": self.mode,
            "planes_used": list(self.planes_used),
            "norms": [
                {
                    **n.projected(),
                    "lg": n.lg,
                    "deadline": n.deadline,
                    "cross_references": list(n.cross_references),
                    "provenance": n.provenance,
                    "grounded_via": list(n.grounded_via),
                    "confidence": n.confidence,
                }
                for n in self.norms
            ],
            "conflicts": [asdict(c) for c in self.conflicts],
            "undetermined": [
                {
                    "reason": u.reason,
                    "detected_operator": u.detected_operator,
                    "partial_bearer": u.partial_bearer,
                    "partial_action": u.partial_action,
                }
                for u in self.undetermined
            ],
            "residuals": [{"text": r.text, "note": r.note} for r in self.residuals],
        }


@dataclass
class CaseResult:
    """The verdict of one test case run against the compiled norms."""

    actor: str
    action: str
    expected: str
    got: str
    passed: bool
    matched_norm: Optional[str] = None
    note: str = ""


@dataclass
class CheckReport:
    total: int = 0
    passed: int = 0
    results: list[CaseResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.total == self.passed
