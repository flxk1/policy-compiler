<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Limits

- The advisory extractor is a modal-verb reader. It handles the common English deontic
  patterns (`must` / `shall` / `may` / `must not` / `is prohibited from` / `is required
  to` / …); it does not parse deeply nested or cross-referential drafting, and it reads
  one bearer per clause. The cue table is `policy_compiler/extract.py`.
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
