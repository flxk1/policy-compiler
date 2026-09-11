<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# What a `CompiledPolicy` carries

Defined in `policy_compiler/model.py`.

- `norms` — the `O`/`P`/`F` norms, each with bearer, action, condition, exception,
  deadline, cross-references, rendered `.lg` form, and per-norm provenance
  (`grounded` + which planes grounded it, or `advisory`).
- `conflicts` — candidate clashes: incompatible forces on the same bearer and action.
  Flagged for oversight, never resolved.
- `undetermined` — statements carrying a deontic force that do not resolve to a
  well-formed duty (a missing bearer or action). Surfaced for a human to complete.
- `residuals` — normative spans the lowering could not place as a norm.
- `actors` — the parties the policy governs, with the roles they play.
- `mode` — `grounded` when any plane grounded the extraction, else `advisory`.
- `planes_used` — the planes actually consumed, in a stable order.
- `source_chars` — the length of the policy text that was read.

`obligations()`, `permissions()`, and `prohibitions()` group the norms by force.
`to_grounding_seam()` emits the whole draft as the JSON payload a compliance fleet
reads; `policy-compiler compile <policy> --json` prints that same payload.

## Per-norm fields

`Norm` carries `operator`, `bearer`, `action`, `condition`, `exception`, `negated`,
`deadline`, `counterparty`, `incident`, `cross_references`, `lg`, `provenance`,
`grounded_via`, `confidence`, and `source` (a `Span` with the character offsets of the
originating text). `projected()` returns the eight-key deontic projection; `grounded` is
true when `provenance == "grounded"`.

## Check results

`check(policy, cases)` returns a `CheckReport` with `total`, `passed`, `results`
(a `CaseResult` per case: `actor`, `action`, `expected`, `got`, `passed`, `matched_norm`,
`note`) and the `ok` property. A case is a dict `{actor, action, expect}`; `expect`
accepts verdict synonyms (`required`, `allowed`, `prohibited`, …). `resolve()` applies a
fixed precedence — prohibition outranks obligation outranks permission — and reports
`conflict` when a bearer/action pair matches both an `O` and an `F` norm.
