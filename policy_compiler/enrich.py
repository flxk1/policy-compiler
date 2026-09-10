"""In-grammar enrichment shared by the grounded and advisory paths.

The deterministic lowering names a bearer and an action but often leaves a trailing
condition, deadline, exception, or cross-reference folded into the action string. These
helpers lift those into their own fields. They only reshape what the text already
carries into the correct field of the same grammar; they never introduce a meaning the
span does not state.
"""

from __future__ import annotations

import re

_ARTICLE = re.compile(r"^(the|a|an|any|each|all|every)\s+", re.IGNORECASE)

# Condition clauses folded into an action string, longest markers first.
_CONDITION_MARKERS = (
    "provided that", "subject to", "in the event that", "as long as",
    "if ", "when ", "where ", "whenever ", "upon ", "once ",
)
_EXCEPTION_MARKERS = ("unless ", "except when ", "except where ", "except ", "save where ")

_CROSSREF = re.compile(
    r"\b(?:section|article|art\.?|clause|paragraph|para\.?|annex|schedule|§)\s*"
    r"[A-Za-z0-9]+(?:\.[0-9]+)*",
    re.IGNORECASE,
)
_DEADLINE_PHRASE = re.compile(
    r"\bwithin\s+\d+\s+(?:second|minute|hour|day|week|month|year|business day)s?\b",
    re.IGNORECASE,
)
# A trailing "in accordance with <ref>" phrase names authority, not part of the action.
_REF_PHRASE = re.compile(
    r",?\s*(?:in accordance with|pursuant to|in line with|as required by|"
    r"as set out in|as provided in)\s+.*$",
    re.IGNORECASE,
)


def strip_article(bearer: str) -> str:
    return _ARTICLE.sub("", bearer.strip()).strip()


def _split_on_marker(text: str, markers: tuple[str, ...]) -> tuple[str, str]:
    """Split `text` at the first marker; return (head, clause_without_marker). The
    clause keeps everything after the marker."""
    low = text.lower()
    best = None
    for m in markers:
        idx = low.find(m)
        if idx > 0 and (best is None or idx < best[0]):
            best = (idx, m)
    if best is None:
        return text, ""
    idx, m = best
    head = text[:idx].strip(" ,.;")
    clause = text[idx + len(m):].strip(" ,.;")
    return head, clause


def extract_cross_references(text: str) -> list[str]:
    return [m.group(0).strip() for m in _CROSSREF.finditer(text)]


def extract_deadline(text: str) -> str:
    # The deontic renderer prefixes "within [...]", so the stored value drops a leading
    # "within" to avoid a doubled word in the rendered form.
    m = _DEADLINE_PHRASE.search(text)
    if not m:
        return ""
    return re.sub(r"^within\s+", "", m.group(0).strip(), flags=re.IGNORECASE)


def enrich_fields(bearer: str, action: str, condition: str, exception: str) -> dict:
    """Return cleaned {bearer, action, condition, exception, deadline, cross_references}.
    Clauses already carried in `condition`/`exception` are preserved; clauses still
    folded into `action` are lifted out."""
    bearer = strip_article(bearer)
    cross_refs = extract_cross_references(action) or extract_cross_references(condition)

    # A deadline is its own field: lift the phrase out of the action, then drop any
    # trailing authority reference so the action reads as the bare act.
    deadline = extract_deadline(action) or extract_deadline(condition)
    if deadline:
        action = _DEADLINE_PHRASE.sub("", action).strip(" ,.;")
    action = _REF_PHRASE.sub("", action).strip(" ,.;")

    # An exception clause takes precedence over a condition when both markers appear,
    # because "except" scopes the action more narrowly than "if".
    if not exception:
        action, exc = _split_on_marker(action, _EXCEPTION_MARKERS)
        if exc:
            exception = exc
    if not condition:
        action, cond = _split_on_marker(action, _CONDITION_MARKERS)
        if cond:
            condition = cond

    action = action.strip(" ,.;")
    # A dangling preposition left by the deterministic pass reads badly on its own.
    action = re.sub(r"^(from|to|of|for)\s+", "", action).strip()

    return {
        "bearer": bearer,
        "action": action,
        "condition": condition.strip(" ,.;"),
        "exception": exception.strip(" ,.;"),
        "deadline": deadline,
        "cross_references": cross_refs,
    }
