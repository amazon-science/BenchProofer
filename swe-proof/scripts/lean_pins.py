#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Does the Lean workspace match the pins it is documented to be built from?

`lean_shared/PINS.md` is the human-readable pin table; `lake-manifest.json` and
`lean-toolchain` are the machine-readable form. A recorded Lean verdict only
describes the prover that produced it, so a workspace built from other revisions
is a DIFFERENT prover and its verdicts do not describe the shipped artifact --
the same argument the fingerprint gate in scripts/lean_verify.sh makes about a
per-bundle workspace, applied to the canonical one.

One definition, in a file both callers can reach: `install.sh` runs it after
every build (fail closed, before anything trusts the workspace), and
tests/test_lean_pins.py runs it against the checkout, which is the only place a
drift COMMITTED to git gets caught -- install.sh cannot, because reaching its
check costs a full Mathlib build and an elan toolchain.

Not a library module: it is a program, imported by the test through the
`scripts` root pyproject puts on the path.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_SHARED = Path(__file__).resolve().parents[1] / "lean_shared"
# `| component | `pin` |`. Rows whose pin is not a dependency revision (the
# solver versions) simply never match a manifest package name.
_ROW = re.compile(r"\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|")
_TOOLCHAIN_ROW = "lean toolchain"


def pinned_revisions(shared: Path = DEFAULT_SHARED) -> dict[str, str]:
    """The PINS.md table, keyed by lowercased component name."""
    out = {}
    for line in (shared / "PINS.md").read_text().splitlines():
        if (row := _ROW.match(line)):
            out[row.group(1).strip().lower()] = row.group(2).strip()
    return out


def drift(shared: Path = DEFAULT_SHARED) -> list[str]:
    """Every disagreement between PINS.md and the workspace, most specific first.

    A missing row is drift too: the table has to carry one for each package the
    manifest resolves, transitive ones included, because most are requested by
    branch and the manifest revision is then the only thing that fixes them.
    """
    pinned = pinned_revisions(shared)
    problems = []

    want = pinned.get(_TOOLCHAIN_ROW)
    have = (shared / "lean-toolchain").read_text().strip()
    if want is None:
        problems.append(f"PINS.md has no '{_TOOLCHAIN_ROW}' row")
    elif have != want:
        problems.append(f"lean-toolchain is {have}, PINS.md pins {want}")

    packages = json.loads((shared / "lake-manifest.json").read_text()).get("packages", [])
    for pkg in packages:
        name = pkg.get("name", "?")
        want = pinned.get(name.lower())
        if want is None:
            problems.append(f"{name} is in lake-manifest.json with no PINS.md row")
        elif pkg.get("rev") != want:
            problems.append(f"{name} is at {pkg.get('rev')}, PINS.md pins {want}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="check the Lean workspace against lean_shared/PINS.md")
    ap.add_argument("--shared", type=Path, default=DEFAULT_SHARED,
                    help="the Lean workspace (default: lean_shared/)")
    args = ap.parse_args(argv)

    problems = drift(args.shared)
    if problems:
        print(f"FAIL: the workspace does not match {args.shared / 'PINS.md'}:")
        for item in problems:
            print(f"  {item}")
        print("The recorded Lean verdicts describe the pinned revisions, so a drifted")
        print("workspace is a different prover. Restore lake-manifest.json and")
        print("lean-toolchain from the checkout, or update PINS.md if the move is")
        print("intended.")
        return 1
    n = len(json.loads((args.shared / "lake-manifest.json").read_text())["packages"])
    print(f"pins OK: toolchain {(args.shared / 'lean-toolchain').read_text().strip()} "
          f"+ {n} dependencies match PINS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
