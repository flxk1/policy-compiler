"""Run test cases against a compiled policy.

A case asks what the policy says about an actor performing an action, and states the
expected verdict. The runner compiles the policy, matches the case against the norms by
bearer and action, and resolves a verdict under a fixed precedence: a prohibition
outranks an obligation, which outranks a permission; an unmatched case is undetermined.
"""

from __future__ import annotations

import os
from typing import Iterable, Union

from .compile import compile as compile_policy
from .model import CaseResult, CheckReport, CompiledPolicy

# Case verdict vocabulary and the synonyms a case may use for each.
_FORBIDDEN = {"forbidden", "prohibited", "denied", "f"}
_OBLIGATORY = {"obligatory", "required", "must", "mandatory", "o"}
_PERMITTED = {"permitted", "allowed", "may", "p"}
_UNDETERMINED = {"undetermined", "unknown", "silent", "none"}


def _canon_verdict(word: str) -> str:
    w = (word or "").strip().lower()
    if w in _FORBIDDEN:
        return "forbidden"
    if w in _OBLIGATORY:
        return "obligatory"
    if w in _PERMITTED:
        return "permitted"
    if w in _UNDETERMINED:
        return "undetermined"
    return w


def _norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def _matches(field: str, query: str) -> bool:
    """A case field matches a norm field when either contains the other after
    normalization. An empty query is a wildcard."""
    if not query:
        return True
    f, q = _norm(field), _norm(query)
    return bool(f) and (q in f or f in q)


def resolve(policy: CompiledPolicy, actor: str, action: str) -> tuple[str, str]:
    """Resolve the policy's verdict for (actor, action). Returns (verdict, matched_lg).
    Prohibition outranks obligation outranks permission; a conflicting match is reported
    as 'conflict'."""
    matched = [
        n for n in policy.norms if _matches(n.bearer, actor) and _matches(n.action, action)
    ]
    if not matched:
        return "undetermined", ""

    ops = {n.operator for n in matched}
    if "F" in ops and "O" in ops:
        lgs = "; ".join(n.lg for n in matched if n.operator in ("F", "O"))
        return "conflict", lgs
    for op, verdict in (("F", "forbidden"), ("O", "obligatory"), ("P", "permitted")):
        for n in matched:
            if n.operator == op:
                return verdict, n.lg
    return "undetermined", ""


def check(
    policy: Union[str, os.PathLike, CompiledPolicy],
    cases: Iterable[dict],
) -> CheckReport:
    """Compile `policy` (or use an already-compiled one) and run `cases` against it.

    Each case is a dict: {actor, action, expect}. `expect` accepts the verdict words or
    their synonyms (required/allowed/prohibited/…).
    """
    compiled = policy if isinstance(policy, CompiledPolicy) else compile_policy(policy)

    report = CheckReport()
    for case in cases:
        actor = case.get("actor", "")
        action = case.get("action", "")
        expected = _canon_verdict(case.get("expect", case.get("expected", "")))
        got, matched_lg = resolve(compiled, actor, action)
        passed = got == expected
        report.results.append(
            CaseResult(
                actor=actor,
                action=action,
                expected=expected,
                got=got,
                passed=passed,
                matched_norm=matched_lg or None,
                note=case.get("note", ""),
            )
        )
        report.total += 1
        report.passed += int(passed)
    return report
