# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-AX — axiom soundness: axiom_check.py fuzzes the REAL callee in the
instance image, asserting the Ensures holds. Axioms model unchanged callees,
so default runs at base_commit (docs/architecture.md §5); `ax_apply_gold: true` opts
into the patched tree (some nagini pbt probes legitimately need it). No
axiom_check.py => explicit skip (no axioms in bundle)."""
from __future__ import annotations

import json

from ..docker_exec import ensure_image, run_in_container
from .base import Bundle, GateResult
from ._common import docker_oracle_skip, env_int

name = "G-AX"
applies_to = ("nagini", "velvet", "lean")
needs_docker = True
agentic = False
# Bundle files this gate's verdict depends on; digested into the record so a
# stamp can be checked against the artifact it describes (base.source_digests).
# The probe is the artifact under test here, and the solution is what declares
# the axioms it must cover, so a verdict is only about that pair.
reads = ("axiom_check", "solution")

CONTAINER_TIMEOUT_DEFAULT = 1800
DETAIL_CAP = 400


def summarize(stdout: str) -> str:
    """One publishable line from axiom_check.py's report.

    The probes are not held to one output shape: some print a pretty-printed
    JSON object, others a multi-line `key=value` report. So the report's LAST
    line is not its summary, and publishing it yields `}` for the first kind and
    some sub-check's own status for the second -- which is how a passing gate
    came to publish `status=skip`. Read the whole report instead, and keep the
    JSON keys that carry the verdict rather than re-printing the blob.
    """
    stdout = stdout.strip()
    if not stdout:
        return ""
    try:
        obj = json.loads(stdout)
    except ValueError:
        obj = None
    if isinstance(obj, dict):
        named = "; ".join(f"{k}={obj[k]}" for k in
                          ("status", "reason", "axioms", "checked", "cases")
                          if obj.get(k) not in (None, "", [], {}))
        return (named or json.dumps(obj, sort_keys=True))[:DETAIL_CAP]
    lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
    return " | ".join(lines)[:DETAIL_CAP]


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    if not bundle.axiom_check.exists():
        return GateResult(name, "skip", "no axiom_check.py (no axioms in bundle)")
    if (skip := docker_oracle_skip(name)) is not None:
        return skip
    err = ensure_image(bundle.instance_id)
    if err:
        return GateResult(name, "error", err)
    apply_gold = bool(bundle.meta().get("ax_apply_gold", False))
    if apply_gold and not bundle.patch_diff.exists():
        return GateResult(name, "error", "ax_apply_gold set but patch.diff missing")
    timeout = env_int("SBU_CONTAINER_TIMEOUT", CONTAINER_TIMEOUT_DEFAULT)
    # Always mount the gold patch when it exists: pre-unification bundles'
    # axiom_check.py scripts read /work/patch.diff themselves (the file lived
    # in the bundle dir before the split layout moved it to the instance dir).
    r = run_in_container(
        bundle.instance_id, str(bundle.root.resolve()), "axiom_check.py",
        gold_patch_path=(str(bundle.patch_diff.resolve())
                         if bundle.patch_diff.exists() else None),
        apply_gold=apply_gold, timeout=timeout)
    data = {"exit": r.returncode, "apply_gold": apply_gold}
    if r.returncode == 124:
        return GateResult(name, "timeout", r.stderr[-200:], data)
    status = "pass" if r.ok else "fail"
    detail = summarize(r.stdout) or r.stderr[-200:]
    return GateResult(name, status, detail, data)
