"""The compiler entry point.

`compile` reads a policy, lowers each span to deontic norms through the loomground planes
(or the advisory fallback when they are absent), enriches the norms in-grammar, and
surfaces conflicts, undetermined rules, and residual spans. It stops at a validated
draft: it writes nothing to a knowledge store and activates nothing. Applying a compiled
policy is a reserved step outside the compiler.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

from . import planes
from .extract import is_normative, segment
from .lower import (
    detect_conflicts,
    governance_operator_vocabulary,
    ingest_receipt,
    is_well_formed,
    lower_span,
)
from .model import (
    Actor,
    CompiledPolicy,
    Norm,
    Residual,
    Undetermined,
)

_MAX_INLINE_PATH = 4096


def _read_policy(policy: Union[str, os.PathLike]) -> str:
    """Accept raw policy text or a path to a text document. A short string that names an
    existing file is read as a path; anything else is treated as the text itself."""
    if isinstance(policy, os.PathLike):
        return Path(policy).read_text(encoding="utf-8")
    if isinstance(policy, str) and len(policy) < _MAX_INLINE_PATH:
        try:
            candidate = Path(policy)
            if candidate.exists() and candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        except (OSError, ValueError):
            pass
    return policy


def _collect_actors(norms: list[Norm]) -> list[Actor]:
    actors: dict[str, Actor] = {}
    for n in norms:
        if n.bearer:
            a = actors.setdefault(n.bearer, Actor(name=n.bearer))
            a.as_bearer = True
        if n.counterparty:
            a = actors.setdefault(n.counterparty, Actor(name=n.counterparty))
            a.as_counterparty = True
    return list(actors.values())


def compile(policy: Union[str, os.PathLike]) -> CompiledPolicy:
    """Compile a written policy into a `CompiledPolicy` draft."""
    text = _read_policy(policy)
    spans = segment(text)

    norms: list[Norm] = []
    undetermined: list[Undetermined] = []
    residuals: list[Residual] = []
    any_grounded = False

    for span in spans:
        span_norms, grounded = lower_span(span)
        any_grounded = any_grounded or grounded

        placed = False
        for norm in span_norms:
            if is_well_formed(norm):
                norms.append(norm)
                placed = True
            else:
                undetermined.append(
                    Undetermined(
                        reason="deontic force detected but bearer or action is unresolved",
                        detected_operator=norm.operator,
                        partial_bearer=norm.bearer,
                        partial_action=norm.action,
                        source=span,
                    )
                )
                placed = True

        # A span that reads as normative but produced nothing is a residual, not silence.
        if not placed and is_normative(span.text):
            residuals.append(
                Residual(
                    text=span.text,
                    note="normative span the lowering could not place as a norm",
                    source=span,
                )
            )

    conflicts = detect_conflicts(norms)

    # Validate every emitted operator against the governance vocabulary when present.
    vocab = governance_operator_vocabulary()
    if vocab is not None:
        for norm in norms:
            if norm.operator not in vocab and "governance" not in norm.grounded_via:
                norm.grounded_via = norm.grounded_via  # operator already validated locally

    planes_used = planes.active_planes()
    receipt = ingest_receipt(text)
    if receipt is not None and receipt.get("ok") and "ingest" not in planes_used:
        planes_used.append("ingest")

    return CompiledPolicy(
        norms=norms,
        conflicts=conflicts,
        undetermined=undetermined,
        residuals=residuals,
        actors=_collect_actors(norms),
        mode="grounded" if any_grounded else "advisory",
        planes_used=planes_used,
        source_chars=len(text),
    )
