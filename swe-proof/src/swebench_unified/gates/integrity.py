# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-INTEGRITY — frozen-row identity + additions-only bundle contents,
adapted to the unified layout (inputs at tasks/<id>/, bundle at
tasks/<id>/<backend>/): instance.json JSON-equal to the frozen row with a
non-empty gold patch; instance root and bundle dir hold allowlisted entries
only."""
from __future__ import annotations

import json

from ..backends import BACKENDS
from .base import Bundle, GateResult, load_frozen_row

name = "G-INTEGRITY"
applies_to = ("nagini", "velvet", "lean", "ears")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution", "instance")

# Every file a bundle is allowed to contain. Anything else is an unexplained
# artifact, and this gate exists to refuse those; instance.json/patch.diff are
# absent because they live one level up, at the instance root.
#
# `.pbt_port.lock` is a caller-side mutex, not bundle content: a driver claims a
# cell by flocking that file for as long as it works on it. It has to be allowed,
# or the gate cannot be re-run BY the driver holding the cell -- which is the one
# caller that most needs to re-judge, since it just edited the bundle. It is
# gitignored and carries no artifact bytes (one `pid`/`tag` line), so allowing it
# does not widen what a released bundle may contain.
_COMMON = {"meta.json", "refinement.md", "mapping.md", "context", "BLOCKED.md",
           "axiom_check.py", "conformance_check.py", "__pycache__",
           "RELAXED_LEAKAGE.md", "result.json", "verdict.md",
           "properties.py", "pbt_result.json", ".pbt_port.lock"}

_PER_BACKEND = {
    "nagini": {"model.py", "model_gold.py"},
    "velvet": {"Solution.lean", "Solution_gold.lean", "lakefile.lean",
               "lean-toolchain", ".lake"},
    "lean": {"Solution.lean", "Solution_gold.lean", "lakefile.lean",
             "lean-toolchain", ".lake"},
    "ears": {"requirements.md"},
}

# Artifacts a backend's gate set can never read are DISALLOWED for it, so a
# bundle cannot carry dead files that look load-bearing (ears: the verifier-
# backed gates are explicit skips, so their inputs have no business existing).
_COMMON_EXCLUDED = {
    "ears": {"axiom_check.py", "conformance_check.py", "properties.py",
             "pbt_result.json", "refinement.md", "mapping.md"},
}

# Allowed at the instance root besides backend subdirs.
_INSTANCE_ROOT = {"instance.json", "patch.diff"}


def _prepatch_stem(bundle: Bundle) -> str:
    stem = bundle.backend.language.solution_filename.rpartition(".")[0]
    return f"{stem}_prepatch"


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    problems = []
    ip = bundle.instance_json
    if not ip.exists():
        return GateResult(name, "error", "instance.json missing")
    row = load_frozen_row(bundle.instance_id)
    if row is None:
        return GateResult(name, "error",
                          f"{bundle.instance_id} not in frozen dataset")
    if json.loads(ip.read_text()) != row:
        problems.append("instance.json differs from frozen row")
    if not row.get("patch", "").strip():
        problems.append("frozen row has empty gold patch")
    root_allowed = _INSTANCE_ROOT | set(BACKENDS)
    extra_root = [p.name for p in bundle.instance_root.iterdir()
                  if p.name not in root_allowed]
    if extra_root:
        problems.append(f"unexpected instance-root entries: {sorted(extra_root)}")
    if bundle.root.is_dir():
        allowed = ((_COMMON - _COMMON_EXCLUDED.get(bundle.backend.name, set()))
                   | _PER_BACKEND[bundle.backend.name])
        prepatch = _prepatch_stem(bundle)
        extra = [p.name for p in bundle.root.iterdir()
                 if p.name not in allowed and not p.name.startswith(prepatch)]
        if extra:
            problems.append(f"unexpected bundle entries: {sorted(extra)}")
    else:
        problems.append(f"no bundle dir at {bundle.root}")
    return GateResult(name, "pass" if not problems else "fail",
                      "; ".join(problems)
                      or "instance.json byte-identical; additions-only")
