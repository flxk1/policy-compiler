"""Command-line interface.

    policy-compiler compile <policy> [--json] [--advisory]
    policy-compiler check   <policy> <cases.json> [--advisory]

`<policy>` is a path to a policy document or a literal policy string. `--advisory` forces
the plane-free path even where the loomground planes are installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from . import planes
from .check import check as run_check
from .compile import compile as compile_policy


def _print_human(compiled) -> None:
    print(f"mode: {compiled.mode}   planes: {', '.join(compiled.planes_used) or 'none'}")
    print(f"actors ({len(compiled.actors)}): " + ", ".join(a.name for a in compiled.actors))
    print()
    groups = (
        ("obligations", compiled.obligations()),
        ("permissions", compiled.permissions()),
        ("prohibitions", compiled.prohibitions()),
    )
    for label, items in groups:
        print(f"{label} ({len(items)}):")
        for n in items:
            tag = n.provenance
            print(f"  [{tag}] {n.lg}")
        print()
    if compiled.conflicts:
        print(f"conflicts ({len(compiled.conflicts)}):")
        for c in compiled.conflicts:
            print(f"  {c.operator_a} vs {c.operator_b} on {c.bearer!r} / {c.action!r}")
        print()
    if compiled.undetermined:
        print(f"undetermined ({len(compiled.undetermined)}):")
        for u in compiled.undetermined:
            print(f"  {u.detected_operator}?  {u.reason}: {u.partial_bearer!r} / {u.partial_action!r}")
        print()
    if compiled.residuals:
        print(f"residuals ({len(compiled.residuals)}):")
        for r in compiled.residuals:
            print(f"  {r.text!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="policy-compiler", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_compile = sub.add_parser("compile", help="compile a policy to a draft of norms")
    p_compile.add_argument("policy", help="path to a policy document, or literal text")
    p_compile.add_argument("--json", action="store_true", help="emit the grounding-seam JSON")
    p_compile.add_argument("--advisory", action="store_true", help="force the plane-free path")

    p_check = sub.add_parser("check", help="run test cases against a compiled policy")
    p_check.add_argument("policy", help="path to a policy document, or literal text")
    p_check.add_argument("cases", help="path to a JSON array of {actor, action, expect}")
    p_check.add_argument("--advisory", action="store_true", help="force the plane-free path")

    args = parser.parse_args(argv)
    if getattr(args, "advisory", False):
        planes.disable()

    if args.command == "compile":
        compiled = compile_policy(args.policy)
        if args.json:
            print(json.dumps(compiled.to_grounding_seam(), indent=2, ensure_ascii=False))
        else:
            _print_human(compiled)
        return 0

    if args.command == "check":
        with open(args.cases, encoding="utf-8") as fh:
            cases = json.load(fh)
        report = run_check(args.policy, cases)
        print(f"cases: {report.total}   passed: {report.passed}   failed: {report.total - report.passed}")
        for r in report.results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"  [{mark}] {r.actor!r} / {r.action!r}: expected {r.expected}, got {r.got}")
        return 0 if report.ok else 1

    return 2


if __name__ == "__main__":
    sys.exit(main())
