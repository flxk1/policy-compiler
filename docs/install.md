<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright 2026 flxk1 -->
# Install routes

From the `loomground-plugins` marketplace (publication pending):

```
/plugin marketplace add flxk1/loomground-plugins
/plugin install policy-compiler@loomground
```

Directly from GitHub, with pip:

```
pip install "git+https://github.com/flxk1/policy-compiler.git"
```

For local development:

```
pip install -e .              # bare: advisory extraction, no loomground required
pip install -e '.[grounded]'  # optional: consume the loomground planes when present
pip install -e '.[test]'      # pytest
```

## The two modes

The loomground planes are optional. With them installed, norms are lowered and grounded
through the planes and marked `grounded`. Without them, the compiler degrades to an
advisory modal-verb extractor and marks every norm `advisory` — the same norm shape,
honestly labelled. No loomground package is imported on the bare path
(`policy_compiler/planes.py` imports each plane lazily, behind an availability check;
`tests/test_modes.py::test_no_hard_loomground_dependency_on_bare_path` proves it with
every loomground module made unimportable).

`policy_compiler.planes.disable()`, the `--advisory` CLI flag, and the
`POLICY_COMPILER_NO_LOOMGROUND` environment variable each force the plane-free path
regardless of what is installed.
