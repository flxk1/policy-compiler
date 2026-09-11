<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# policy-compiler

**What does this written policy oblige, permit, and forbid?**

Read a written policy and produce executable governance norms.

## Problem

A policy is prose. A runtime needs O/P/F norms bound to a bearer and an action before it can check an agent against one.

## Install

```
pip install "git+https://github.com/flxk1/policy-compiler.git@v0.1.0"
pip install "policy-compiler[grounded] @ git+https://github.com/flxk1/policy-compiler.git@v0.1.0"
```

Marketplace route and the two modes: [docs/install.md](docs/install.md).

## Usage

```python
from policy_compiler import compile, resolve
draft = compile("tests/fixtures/data_policy.txt")
for n in draft.norms:
    print(n.provenance, n.lg)
print(len(draft.conflicts), "conflicts", len(draft.undetermined), "undetermined", len(draft.residuals), "residuals")
print(resolve(draft, "processor", "delete personal data")[0])
```

## Example

```
in : tests/fixtures/data_policy.txt
out: advisory P(controller : process personal data for billing purposes)
     advisory O(processor : notify the controller)
     advisory F(Staff : sharing account credentials with third parties)
     advisory if [a contract terminates] then O(processor : delete personal data)
     advisory if [litigation is pending] then F(processor : delete personal data)
     1 conflicts 1 undetermined 2 residuals
     conflict
```

## Interface

- `compile(policy) → CompiledPolicy` · `policy` is policy text or a path to a text document
- `CompiledPolicy`: `norms` `conflicts` `undetermined` `residuals` `actors` `mode` `planes_used` · `obligations()` `permissions()` `prohibitions()` · `to_grounding_seam()`
- `Norm`: `operator` `bearer` `action` `condition` `exception` `deadline` `cross_references` `lg` `provenance` `source` · `projected()` · `grounded`
- `check(policy, cases) → CheckReport` with `total` `passed` `results` `ok` · `resolve(policy, actor, action) → (verdict, lg)`
- `Conflict` `Undetermined` `Residual` `Actor` `Span` `CaseResult` · `policy_compiler.planes.disable()` forces the plane-free path
- CLI `policy-compiler compile <policy> [--json] [--advisory]` · `policy-compiler check <policy> <cases.json>`
- Field detail: [docs/model.md](docs/model.md).

## Family

Applied reasoning. `pyproject.toml` declares `dependencies = []`, so every loomground plane is optional here: the `grounded` extra adds `loomground-deontic`, `loomground-norm`, `loomground-ingest` and `loomground-governance`, each reached behind an availability check, and an absent plane degrades that dimension to advisory extraction. `to_grounding_seam()` emits the payload [a2a-compliance](https://github.com/flxk1/a2a-compliance) reads. Position and the plane table: [docs/position.md](docs/position.md).

## Status

0.1.0 · 20 tests (18 pass, 2 skip while the planes are absent) · Python >=3.10 · Apache-2.0. The compiler stops at a validated draft; activation is a reserved human step. Bounds: [docs/limits.md](docs/limits.md).

## License

Apache-2.0 · `LICENSES/Apache-2.0.txt` · `REUSE.toml`
