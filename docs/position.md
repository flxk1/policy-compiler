<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Position

This is a ctrl-plane capability: an orchestrator over the loomground language planes. It
does not reimplement the lowering. The rule extraction and the deontic algebra belong to
the loomground packages; the compiler delegates to them, then enriches their output
in-grammar — lifting a bearer, a condition, a deadline, or a cross-reference the
deterministic pass left folded into the action. A meaning that resolves to no construct
is surfaced as a residual, never fabricated into a norm.

The output is the author stage that feeds a compliance fleet. Each norm is emitted in
the deontic projection shape (`operator`/`bearer`/`action`/`condition`/`exception`/
`negated`/`incident`/`counterparty`) that the
[a2a-compliance](https://github.com/flxk1/a2a-compliance) grounding seam — its `deontic`,
`norm`, and `mandate` planes — consumes directly. `CompiledPolicy.to_grounding_seam()`
emits that payload.

## Planes consumed

| plane | package | role here |
|---|---|---|
| deontic | `loomground-deontic` | render, project, and ground each `O`/`P`/`F` norm; conflict algebra |
| norm | `loomground-norm` | extract rules from prose and assign the deontic force |
| ingest | `loomground-ingest` | corroboration receipt (the plane accepts the text; node/edge counts) |
| governance | `loomground-governance` | validate emitted operators against the governance vocabulary |

Each is reached behind an availability check (`policy_compiler/planes.py`); any subset
may be present. When a plane is absent its dimension degrades to the advisory fallback
for that dimension.
