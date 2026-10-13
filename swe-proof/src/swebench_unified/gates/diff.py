# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-DIFF — every prepatch twin FAILS verification under the identical spec.

Backend-independent: the spec identity is decided by same_spec and the verdict
by the backend's own verifier, so nothing here knows which language it judges."""
from __future__ import annotations

from ..markers import same_spec
from .base import Bundle, GateResult
from ._common import check_bundle_file, no_verdict, worst_no_verdict

name = "G-DIFF"
applies_to = ("nagini", "velvet", "lean")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution", "prepatches")


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    variants = bundle.prepatches
    if not variants:
        stem = bundle.backend.language.solution_filename.rpartition(".")[0]
        return GateResult(name, "error", f"no {stem}_prepatch* file")
    timeout = bundle.verify_timeout()
    tables = bundle.backend.language
    sol = bundle.solution_src()
    outcomes, all_fail, unjudged = {}, True, []
    silent = []
    for v in variants:
        if not same_spec(sol, v.read_text(), tables):
            return GateResult(
                name, "fail",
                f"{v.name} spec differs from {bundle.solution.name} (must be identical)")
        r = check_bundle_file(bundle, v, timeout)
        outcomes[v.name] = r.summary
        if r.success:
            all_fail = False
        elif no_verdict(r):
            unjudged.append(v.name)
            silent.append(r)
    detail = "; ".join(f"{k}: {v}" for k, v in outcomes.items())
    if all_fail and unjudged:
        # This gate's whole claim is that the twin was REJECTED. Where no
        # verdict came back there is nothing to pass on, and calling it a
        # rejection would vouch for a spec that may well admit the prepatch.
        #
        # `no_verdict` names WHY, because this status is the gate's only way to
        # say "the host ran out of time" and a caller cannot tell that from a
        # broken environment otherwise. A re-stamp sweep reads it to avoid
        # publishing a wall clock over a green record; see
        # `_common.no_verdict_reason`.
        return GateResult(name, "error",
                          f"no verdict on {', '.join(unjudged)}: {detail}",
                          {"variants": outcomes, "unjudged": unjudged,
                           "no_verdict": worst_no_verdict(silent)})
    return GateResult(name, "pass" if all_fail else "fail", detail,
                      {"variants": outcomes})
