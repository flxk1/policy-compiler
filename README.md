# policy-compiler

Read a written policy and produce executable governance norms.

The compiler takes policy text (or a path to a text document) and returns a validated
draft: the policy's actors, permissions, prohibitions, and obligations lowered to
deontic norms — `O` / `P` / `F` force bound to a bearer, an action, and its conditions —
together with the conflicts, undetermined rules, and residual spans the lowering
surfaced. It runs test cases against the draft. It stops there. Activation is a reserved
human step; the compiler never applies or activates a policy.

## Position

This is a ctrl-plane capability: an orchestrator over the loomground language planes. It
does not reimplement the lowering. The rule extraction and the deontic algebra belong to
the loomground packages; the compiler delegates to them, then enriches their output
in-grammar — lifting a bearer, a condition, a deadline, or a cross-reference the
deterministic pass left folded into the action. A meaning that resolves to no construct
is surfaced as a residual, never fabricated into a norm.

The output is the author stage that feeds a compliance fleet. Each norm is emitted in
the deontic projection shape (`operator`/`bearer`/`action`/`condition`/`exception`/
`negated`/`incident`/`counterparty`) that the
[`a2a-compliance`](../a2a-compliance) grounding seam — its `deontic`, `norm`, and
`mandate` planes — consumes directly. `CompiledPolicy.to_grounding_seam()` emits that
payload.

## Install

```
pip install -e .            # bare: advisory extraction, no loomground required
pip install -e '.[grounded]'  # optional: consume the loomground planes when present
```

The loomground planes are optional. With them installed, norms are lowered and grounded
through the planes and marked `grounded`. Without them, the compiler degrades to an
advisory modal-verb extractor and marks every norm `advisory` — the same norm shape,
honestly labelled. No loomground package is imported on the bare path.

## Use

```python
from policy_compiler import compile, check

draft = compile("The processor must delete personal data when a contract terminates.")
for norm in draft.norms:
    print(norm.provenance, norm.lg)

report = check("policy.txt", [
    {"actor": "processor", "action": "delete personal data", "expect": "obligatory"},
])
print(report.ok)
```

CLI:

```
policy-compiler compile <policy> [--json] [--advisory]
policy-compiler check   <policy> <cases.json> [--advisory]
```

`<policy>` is a path to a document or a literal policy string. `--advisory` forces the
plane-free path even where the planes are installed. `--json` emits the grounding-seam
payload.

## What a `CompiledPolicy` carries

- `norms` — the `O`/`P`/`F` norms, each with bearer, action, condition, exception,
  deadline, cross-references, rendered `.lg` form, and per-norm provenance
  (`grounded` + which planes grounded it, or `advisory`).
- `conflicts` — candidate clashes: incompatible forces on the same bearer and action.
  Flagged for oversight, never resolved.
- `undetermined` — statements carrying a deontic force that do not resolve to a
  well-formed duty (a missing bearer or action). Surfaced for a human to complete.
- `residuals` — normative spans the lowering could not place as a norm.
- `actors` — the parties the policy governs, with the roles they play.

`obligations()`, `permissions()`, and `prohibitions()` group the norms by force.

## Planes consumed

| plane | package | role here |
|---|---|---|
| deontic | `loomground-deontic` | render, project, and ground each `O`/`P`/`F` norm; conflict algebra |
| norm | `loomground-norm` | extract rules from prose and assign the deontic force |
| ingest | `loomground-ingest` | corroboration receipt (the plane accepts the text; node/edge counts) |
| governance | `loomground-governance` | validate emitted operators against the governance vocabulary |

Each is reached behind an availability check; any subset may be present. When a plane is
absent its dimension degrades to the advisory fallback for that dimension.

## Limits

- The advisory extractor is a modal-verb reader. It handles the common English deontic
  patterns (`must` / `shall` / `may` / `must not` / `is prohibited from` / `is required
  to` / …); it does not parse deeply nested or cross-referential drafting, and it reads
  one bearer per clause.
- Conflict detection flags same-bearer, same-action force clashes. It over-flags on
  purpose: two duties whose conditions could never fire together are still flagged, so a
  candidate is a prompt for oversight, not a decided contradiction. Scope-aware
  resolution is out of scope.
- Undetermined-versus-residual placement of a borderline span can differ between the
  grounded and advisory paths, because the planes and the fallback draw the
  well-formedness line at slightly different points. Both paths surface the span; neither
  drops it.
- The ingest receipt reports that the ingest plane accepted the text and how many
  nodes and edges it wrote to its collecting sink; the structured norms come from the
  norm and deontic planes, not from that summary.
- The compiler writes to no knowledge store and activates nothing. Ratifying or applying
  a compiled draft is a separate governed step outside this package.
