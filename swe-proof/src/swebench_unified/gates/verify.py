# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-VERIFY — the committed solution verifies (docs/architecture.md §5); NO proof
agent runs here (lean proof search is construct P1.5, swebench_unified.prove).
nagini: declared float-encoding honored; velvet: elaborates cleanly (sorry
rejected); lean: compiles AND every correct_<name> theorem genuinely closed.
mode="feedback" (lean only): sorry-only counts as pass — the pre-proof P1
state — recorded in the detail.
"""
from __future__ import annotations

from .base import Bundle, GateResult
from ._common import check_bundle_file, no_verdict
from ._lean_axioms import check_proof_axioms

name = "G-VERIFY"
applies_to = ("nagini", "velvet", "lean")
needs_docker = False
agentic = False
# Bundle files this gate's verdict depends on; digested into the record
# so a stamp can be checked against the artifact it describes (base.source_digests).
reads = ("solution",)


def run(bundle: Bundle, *, mode: str = "strict") -> GateResult:
    sol = bundle.solution
    if not sol.exists():
        return GateResult(name, "error", f"{sol.name} missing")
    timeout = bundle.verify_timeout()
    r = check_bundle_file(bundle, sol, timeout)
    data = {"wall_time_s": round(r.wall_time_s, 1)}
    if r.timed_out:
        return GateResult(name, "timeout", f"timeout after {timeout}s", data)
    if no_verdict(r):
        # The checker did not judge this file, so it did not refuse it either.
        # Recorded as an error, which routes the cell back to measurement: read
        # as a fail it would send an intact bundle out to be re-authored.
        #
        # Keep what the checker said. A synthesised "did not reach a verdict
        # (exit 2)" with wall_time 0.0 and no other field is unactionable: a cell
        # stamped that way cannot be told apart from a broken bundle without
        # re-running the verifier by hand. The checker's own words are the only
        # thing in the record that distinguishes a resource failure from a damaged
        # artifact. The tail is bounded because a verifier that dies noisily can
        # emit megabytes.
        data["diagnosis"] = (
            (r.stderr or "").strip()[-2000:]
            or (r.stdout or "").strip()[-2000:]
            or "the checker wrote nothing to stdout or stderr")
        return GateResult(name, "error", r.summary, data)
    if not r.success:
        if bundle.backend.name == "lean" and mode == "feedback" and r.sorry_only:
            data["sorry_only"] = True
            return GateResult(
                name, "pass",
                f"sorry-only in {r.wall_time_s:.1f}s (tolerated in feedback "
                "mode: proof phase pending)", data)
        return GateResult(name, "fail", f"{r.summary} in {r.wall_time_s:.1f}s", data)
    if bundle.backend.name != "lean":
        return GateResult(name, "pass", f"{r.summary} in {r.wall_time_s:.1f}s", data)
    # lean: compiles; now confirm every correct_<name> is genuinely closed.
    ax_ok, ax_detail, ax_data = check_proof_axioms(bundle, bundle.solution_src(), timeout)
    data.update(ax_data)
    if not ax_ok:
        status = "error" if ax_data.get("no_verdict") else "fail"
        return GateResult(name, status, f"compiles but {ax_detail}", data)
    return GateResult(name, "pass",
                      f"verified in {r.wall_time_s:.1f}s; {ax_detail}", data)
