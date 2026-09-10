"""Segmentation and the advisory (plane-free) extractor.

Segmentation splits a policy into spans and keeps each span's character offsets so every
norm, residual, and undetermined rule can cite its origin. The advisory extractor is the
fallback the compiler uses when the loomground norm plane is absent: a modal-verb reader
that produces the same norm shape the plane produces, marked advisory and ungrounded.
"""

from __future__ import annotations

import re

from .model import OP_OBLIGATION, OP_PERMISSION, OP_PROHIBITION, Span

# Modal cues, prohibition and permission before obligation so "must not" and "may not"
# are read as prohibitions rather than as a bare "must"/"may".
_MODALS: list[tuple[str, str]] = [
    (r"must\s+not", OP_PROHIBITION),
    (r"shall\s+not", OP_PROHIBITION),
    (r"may\s+not", OP_PROHIBITION),
    (r"is\s+prohibited\s+from", OP_PROHIBITION),
    (r"are\s+prohibited\s+from", OP_PROHIBITION),
    (r"is\s+forbidden\s+(?:to|from)", OP_PROHIBITION),
    (r"is\s+not\s+permitted\s+to", OP_PROHIBITION),
    (r"is\s+not\s+allowed\s+to", OP_PROHIBITION),
    (r"may(?:\s+only)?", OP_PERMISSION),
    (r"is\s+permitted\s+to", OP_PERMISSION),
    (r"is\s+allowed\s+to", OP_PERMISSION),
    (r"is\s+entitled\s+to", OP_PERMISSION),
    (r"can", OP_PERMISSION),
    (r"must", OP_OBLIGATION),
    (r"shall", OP_OBLIGATION),
    (r"is\s+required\s+to", OP_OBLIGATION),
    (r"are\s+required\s+to", OP_OBLIGATION),
    (r"is\s+obligated\s+to", OP_OBLIGATION),
    (r"has\s+to", OP_OBLIGATION),
    (r"have\s+to", OP_OBLIGATION),
    (r"needs\s+to", OP_OBLIGATION),
]
_MODAL_RE = re.compile(
    r"\b(?P<modal>" + "|".join(m for m, _ in _MODALS) + r")\b", re.IGNORECASE
)
_OP_BY_MODAL = [(re.compile(r"^" + m + r"$", re.IGNORECASE), op) for m, op in _MODALS]

# Words that mark a span as normative in intent. A normative span the extractor cannot
# turn into a norm becomes a residual rather than being silently dropped.
_NORMATIVE_SIGNAL = re.compile(
    r"\b(must|shall|may|required|prohibited|forbidden|permitted|obligation|obliged|"
    r"duty|responsible\s+for|ensure|comply|compliance|entitled|authori[sz]ed)\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT = re.compile(r"(?<=[.;])\s+|\n+")


def segment(text: str) -> list[Span]:
    """Split into spans on sentence and clause boundaries, preserving offsets. Empty
    fragments are dropped."""
    spans: list[Span] = []
    pos = 0
    for piece in _SENTENCE_SPLIT.split(text):
        if not piece:
            continue
        idx = text.find(piece, pos)
        if idx < 0:
            idx = pos
        s = piece.strip()
        if s:
            start = idx + (len(piece) - len(piece.lstrip()))
            spans.append(Span(start=start, end=start + len(s), text=s))
        pos = idx + len(piece)
    return spans


def is_normative(text: str) -> bool:
    return bool(_NORMATIVE_SIGNAL.search(text))


def _operator_for(modal: str) -> str:
    norm = re.sub(r"\s+", " ", modal.strip().lower())
    for rx, op in _OP_BY_MODAL:
        if rx.match(norm):
            return op
    return OP_OBLIGATION


def advisory_extract(span: Span) -> list[dict]:
    """Read one span with modal-verb heuristics. Returns raw field dicts
    {operator, bearer, action, raw_sentence} — one per modal found. Enrichment and
    well-formedness checks happen downstream, so this stays a thin reader."""
    text = span.text
    out: list[dict] = []
    for m in _MODAL_RE.finditer(text):
        modal = m.group("modal")
        bearer = text[: m.start()].strip(" ,.;")
        action = text[m.end():].strip(" ,.;")
        # A leading connective ("and", "but") left when a sentence carries two duties
        # is not part of the bearer.
        bearer = re.sub(r"^(and|but|or|;)\s+", "", bearer, flags=re.IGNORECASE).strip()
        out.append(
            {
                "operator": _operator_for(modal),
                "bearer": bearer,
                "action": action,
                "raw_sentence": text,
            }
        )
    return out
