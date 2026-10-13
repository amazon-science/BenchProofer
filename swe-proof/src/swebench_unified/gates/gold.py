# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-GOLD — the gold-faithful impl verifies; prepatches re-fail. With no
separate *_gold file the shipped solution IS the gold-faithful impl, so this
reduces to G-VERIFY + G-DIFF. For lean the gold proof must also be genuinely
closed (clean `#print axioms`), not just compiling."""
from __future__ import annotations

from .base import Bundle, GateResult
from ._common import check_bundle_file, no_verdict, no_verdict_reason
from ._lean_axioms import check_proof_axioms

name = "G-GOLD"
applies_to = ("nagini", "velvet", "lean")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution", "prepatches")


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    gold = bundle.gold_solution if bundle.gold_solution.exists() else bundle.solution
    if not gold.exists():
        return GateResult(name, "error", f"{gold.name} missing")
    timeout = bundle.verify_timeout()
    r = check_bundle_file(bundle, gold, timeout)
    if no_verdict(r):
        # `no_verdict` names whether the host ran out of time or the environment
        # broke: this gate has no timeout status, so without it a wall clock and a
        # real defect are the same `error` to every caller. See
        # `_common.no_verdict_reason`.
        return GateResult(name, "error", f"no verdict on {gold.name}: {r.summary}",
                          {"no_verdict": no_verdict_reason(r)})
    if not r.success:
        return GateResult(name, "fail",
                          f"gold-faithful impl did not verify: {r.summary}")
    if bundle.backend.name == "lean":
        ax_ok, ax_detail, ax_data = check_proof_axioms(bundle, gold.read_text(), timeout)
        if not ax_ok:
            status = "error" if ax_data.get("no_verdict") else "fail"
            return GateResult(name, status, f"gold-faithful proof not clean: {ax_detail}")
    for v in bundle.prepatches:
        rv = check_bundle_file(bundle, v, timeout)
        if rv.success:
            return GateResult(name, "fail", f"{v.name} verified (should fail)")
        if no_verdict(rv):
            # See _common.no_verdict: "did not verify" here would be a rejection
            # this gate never witnessed.
            return GateResult(name, "error",
                              f"no verdict on {v.name}: {rv.summary}",
                              {"no_verdict": no_verdict_reason(rv)})
    return GateResult(name, "pass",
                      f"gold-faithful impl verifies ({gold.name}); prepatch(es) fail")
