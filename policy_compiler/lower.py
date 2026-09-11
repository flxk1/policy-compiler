"""Lowering: turn a span into deontic norms, delegating to the loomground planes.

When the norm plane is present, a span is lowered by `loomground_norm.extract_rules`
followed by `loomground_norm.formula_from_rule`, and the deontic plane renders and
grounds the result. When those planes are absent the advisory reader stands in and the
norm is marked advisory. Either way the compiler enriches the fields in-grammar and the
output is one uniform `Norm` shape.
"""

from __future__ import annotations

from typing import Optional

from . import planes
from .enrich import enrich_fields
from .extract import advisory_extract
from .model import (
    PROV_ADVISORY,
    PROV_GROUNDED,
    VALID_OPERATORS,
    Conflict,
    Norm,
    Span,
)


def _render_lg(operator: str, bearer: str, action: str, condition: str, negated: bool) -> str:
    """Fallback .lg renderer, used when the deontic plane is absent. Mirrors the plane's
    surface form: `if [cond] then OP(bearer : action)`."""
    act = ("¬" if negated else "") + action
    core = f"{operator}({bearer} : {act})"
    return f"if [{condition}] then {core}" if condition else core


def _lower_span_grounded(span: Span) -> list[dict]:
    """Delegate the span to the norm plane; return raw field dicts. The plane owns the
    rule extraction and the O/P/F assignment."""
    norm_mod = planes.get("norm")
    rows: list[dict] = []
    for facet in norm_mod.extract_rules(span.text):
        formula = norm_mod.formula_from_rule(facet)
        rows.append(
            {
                "operator": formula.operator,
                "bearer": formula.bearer,
                "action": formula.action,
                "condition": getattr(formula, "condition", "") or "",
                "exception": getattr(formula, "exception", "") or "",
                "negated": bool(getattr(formula, "negated", False)),
                "counterparty": getattr(formula, "counterparty", "") or "",
                "incident": getattr(formula, "incident", "") or "",
                "raw_sentence": span.text,
                "confidence": float(getattr(formula, "confidence", 0.0) or 0.0),
            }
        )
    return rows


def _build_formula(fields: dict):
    """Build a plane DeonticFormula from enriched fields so the plane can render and
    ground it. Returns None when the deontic plane is absent."""
    deo = planes.get("deontic")
    if deo is None:
        return None
    # The plane keys on its own modal CLASS names; it fails closed on anything else
    # (deontic >=0.2). `name()` is the plane's own operator-to-class map.
    op = fields["operator"]
    modal = deo.name(op) if hasattr(deo, "name") else {"O": "obligation", "P": "permission",
                                                       "F": "prohibition"}[op]
    formula = deo.formula_from_fields(
        modal,
        fields["bearer"],
        fields["action"],
        condition=fields.get("condition", ""),
        exception=fields.get("exception", ""),
        counterparty=fields.get("counterparty", ""),
        deadline=fields.get("deadline", ""),
        cross_references=list(fields.get("cross_references", [])),
        raw_sentence=fields.get("raw_sentence", ""),
        confidence=fields.get("confidence", 0.0),
    )
    # formula_from_fields keys the operator off the modal word; the enriched operator is
    # authoritative (it came from the plane's own rule extraction), so restore it.
    formula.operator = fields["operator"]
    return formula


def lower_span(span: Span) -> tuple[list[Norm], bool]:
    """Lower one span to zero or more norms. Second element is True when the span was
    grounded through a plane."""
    grounded = planes.available("norm")
    raw_rows = _lower_span_grounded(span) if grounded else advisory_extract(span)

    deo = planes.get("deontic")
    norms: list[Norm] = []
    for row in raw_rows:
        if row["operator"] not in VALID_OPERATORS:
            continue
        enriched = enrich_fields(
            row.get("bearer", ""),
            row.get("action", ""),
            row.get("condition", ""),
            row.get("exception", ""),
        )
        fields = {**row, **enriched}
        formula = _build_formula(fields)

        used: list[str] = []
        if grounded:
            used.append("norm")
        if formula is not None:
            used.append("deontic")
            lg = formula.render()
            confidence = float(getattr(formula, "confidence", 0.0) or 0.0)
        else:
            lg = _render_lg(
                fields["operator"], fields["bearer"], fields["action"],
                fields.get("condition", ""), bool(row.get("negated", False)),
            )
            confidence = fields.get("confidence", 0.0)

        norm = Norm(
            operator=fields["operator"],
            bearer=fields["bearer"],
            action=fields["action"],
            condition=fields.get("condition", ""),
            exception=fields.get("exception", ""),
            negated=bool(row.get("negated", False)),
            deadline=fields.get("deadline", ""),
            counterparty=fields.get("counterparty", ""),
            incident=fields.get("incident", ""),
            cross_references=list(fields.get("cross_references", [])),
            lg=lg,
            provenance=PROV_GROUNDED if used else PROV_ADVISORY,
            grounded_via=used,
            confidence=confidence,
            source=span,
        )
        norms.append(norm)
    return norms, grounded


def is_well_formed(norm: Norm) -> bool:
    """A norm is a duty only if it names a concrete bearer and action. When the deontic
    plane is present its own predicate decides; otherwise the same rule is applied
    locally."""
    deo = planes.get("deontic")
    if deo is not None:
        formula = _build_formula(
            {
                "operator": norm.operator,
                "bearer": norm.bearer,
                "action": norm.action,
                "condition": norm.condition,
                "exception": norm.exception,
                "counterparty": norm.counterparty,
                "deadline": norm.deadline,
                "cross_references": norm.cross_references,
                "raw_sentence": (norm.source.text if norm.source else norm.lg),
                "confidence": norm.confidence,
            }
        )
        if formula is not None:
            return bool(deo.is_grounded(formula))
    return bool(norm.bearer.strip()) and bool(norm.action.strip())


def detect_conflicts(norms: list[Norm]) -> list[Conflict]:
    """Surface candidate conflicts. Delegates to the deontic plane's algebra when
    present; otherwise applies the same same-bearer/same-action O-vs-F clash locally."""
    deo = planes.get("deontic")
    if deo is not None:
        formulae = []
        index = {}
        for n in norms:
            f = _build_formula(
                {
                    "operator": n.operator, "bearer": n.bearer, "action": n.action,
                    "condition": n.condition, "exception": n.exception,
                    "counterparty": n.counterparty, "deadline": n.deadline,
                    "cross_references": n.cross_references,
                    "raw_sentence": (n.source.text if n.source else n.lg),
                    "confidence": n.confidence,
                }
            )
            if f is not None:
                formulae.append(f)
                index[id(f)] = n
        out = []
        for c in deo.detect_conflicts(formulae):
            out.append(
                Conflict(
                    kind=c.get("kind", "deontic-conflict"),
                    bearer=c.get("bearer", ""),
                    action=c.get("action", ""),
                    operator_a=c.get("operator_a", ""),
                    operator_b=c.get("operator_b", ""),
                    formula_a=c.get("formula_a", ""),
                    formula_b=c.get("formula_b", ""),
                    resolution=c.get("resolution", "candidate-escalate"),
                    confidence=float(c.get("confidence", 0.0) or 0.0),
                )
            )
        return out
    return _detect_conflicts_local(norms)


def _detect_conflicts_local(norms: list[Norm]) -> list[Conflict]:
    def key(s: str) -> str:
        return " ".join(s.lower().split())

    out: list[Conflict] = []
    for i in range(len(norms)):
        for j in range(i + 1, len(norms)):
            a, b = norms[i], norms[j]
            if key(a.bearer) != key(b.bearer) or key(a.action) != key(b.action):
                continue
            ops = {a.operator, b.operator}
            # An obligation to do X and a prohibition against X clash; so does an
            # obligation against its own negation.
            clash = ops == {"O", "F"} or (
                a.operator == b.operator == "O" and a.negated != b.negated
            )
            if clash:
                out.append(
                    Conflict(
                        kind="deontic-conflict",
                        bearer=a.bearer,
                        action=a.action,
                        operator_a=a.operator,
                        operator_b=b.operator,
                        formula_a=a.lg,
                        formula_b=b.lg,
                        confidence=round(min(a.confidence, b.confidence), 3),
                    )
                )
    return out


def ingest_receipt(text: str) -> Optional[dict]:
    """Drive the text through the ingest plane's deontic ingester as a corroboration
    receipt: it confirms the plane accepts the text and reports node/edge counts. Returns
    None when the ingest plane is absent. The structured norms come from the norm and
    deontic planes, not from this summary."""
    ing = planes.get("ingest")
    if ing is None:
        return None
    try:
        registry = ing.IngesterRegistry()
        registry.register(ing.DeonticIngester())
        writer = ing.CollectingWriter()
        result = ing.ingest_text(text, registry=registry, writer=writer)
        return {
            "ok": bool(result.get("ok")),
            "nodes": result.get("nodes"),
            "edges": result.get("edges"),
            "dimension": result.get("dimension"),
        }
    except Exception:
        return None


def governance_operator_vocabulary() -> Optional[set[str]]:
    """The governance plane's declared operator vocabulary, used to validate that every
    emitted operator is expressible in the governance language. None when absent."""
    gov = planes.get("governance")
    if gov is None:
        return None
    try:
        vocab = gov.vocabulary()
        text = str(vocab)
        found = {op for op in VALID_OPERATORS if op in text}
        return found or set(VALID_OPERATORS)
    except Exception:
        return None
