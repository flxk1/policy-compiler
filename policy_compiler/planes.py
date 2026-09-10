"""Guarded access to the loomground planes the compiler consumes.

The lowering belongs to the loomground plane packages; the compiler delegates to them
and never reimplements their algebra. Each plane is reached behind an availability
check: when a plane's package is not importable the check is false and the caller
degrades to the advisory fallback for that dimension. No plane is imported at module
top level, so the bare path carries no hard loomground dependency.

`disable()` forces every plane off regardless of what is installed, so the advisory
path is reachable in any environment. The environment variable
`POLICY_COMPILER_NO_LOOMGROUND` does the same at process start.
"""

from __future__ import annotations

import importlib
import os
from typing import Any, Optional

# Package name per plane. Absence of any of these degrades, never crashes.
_PLANE_PACKAGES = {
    "deontic": "deontic",
    "norm": "loomground_norm",
    "ingest": "loomground_ingest",
    "governance": "loomground_governance",
    "versum": "versum",
    "solver": "loomground_solver",
}

_FORCED_OFF = bool(os.environ.get("POLICY_COMPILER_NO_LOOMGROUND"))
_module_cache: dict[str, Optional[Any]] = {}


def disable() -> None:
    """Force all planes unavailable for this process (advisory mode)."""
    global _FORCED_OFF
    _FORCED_OFF = True
    _module_cache.clear()


def enable() -> None:
    """Undo `disable()`; planes are then available iff their packages import."""
    global _FORCED_OFF
    _FORCED_OFF = False
    _module_cache.clear()


def _load(plane: str) -> Optional[Any]:
    if _FORCED_OFF:
        return None
    if plane in _module_cache:
        return _module_cache[plane]
    pkg = _PLANE_PACKAGES.get(plane)
    module: Optional[Any]
    try:
        module = importlib.import_module(pkg) if pkg else None
    except Exception:
        module = None
    _module_cache[plane] = module
    return module


def available(plane: str) -> bool:
    """True iff `plane` is present and usable. Cheap and cached."""
    return _load(plane) is not None


def get(plane: str) -> Optional[Any]:
    """The plane's module, or None when unavailable. Callers must handle None."""
    return _load(plane)


def active_planes() -> list[str]:
    """Names of the planes the compiler will actually consume, in a stable order.
    Only deontic and norm carry the lowering; ingest and governance corroborate."""
    order = ["norm", "deontic", "ingest", "governance"]
    return [p for p in order if available(p)]
