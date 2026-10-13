# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared plumbing for the verifier-backed gates: the gate layer's single place
that knows nagini's `check()` takes the float-encoding knob and the lean flavors'
do not, so gates stay generic.

The GATE layer's single place, not the pipeline's: the eval and construct paths
branch on the same knob at call sites that never come through here, so a new
per-bundle knob has to be taught all of them. docs/adding_a_backend.md section 1
enumerates them, and `grep -rn float_encoding src/` is the check that the list is
still complete.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..verify import VerifyResult
from .base import Bundle


def check_bundle_file(bundle: Bundle, path: Path, timeout: int) -> VerifyResult:
    if bundle.backend.name == "nagini":
        return bundle.backend.check(path, timeout,
                                    float_encoding=bundle.float_encoding())
    return bundle.backend.check(path, timeout)


def check_bundle_source(bundle: Bundle, src: str, timeout: int) -> VerifyResult:
    from ..verify import verify_source_via

    def _check(path: Path, t: int) -> VerifyResult:
        return check_bundle_file(bundle, path, t)

    return verify_source_via(_check, src,
                             bundle.backend.language.solution_filename, timeout)


def no_verdict(r) -> bool:
    """The checker returned without accepting or rejecting the file.

    One home for the policy every gate that reads a REJECTION depends on. Such a
    gate concludes from `success == False`, and that flag is also False when the
    checker never judged anything: it hit its cap, its environment broke, or the
    JVM under Viper died. Counted as a rejection, each of those turns a spec
    weakness the file was probing into evidence that the spec is strong. So the
    absence of a verdict has to be visible at every one of those sites.

    Duck-typed: gate tests build stand-in results, and one that predates
    `crashed` means "reached a verdict", so a missing attribute reads as False
    rather than raising.
    """
    return bool(getattr(r, "timed_out", False) or getattr(r, "crashed", False))


def no_verdict_reason(r) -> str:
    """WHICH non-verdict this is: "timeout", "crash", or "" if `r` did decide.

    `no_verdict` deliberately collapses the two, because for the gate the effect
    is identical -- neither one is a rejection. For the caller deciding what to do
    NEXT they are opposites. A timeout is a statement about the machine: the same
    bytes on a quieter one reach a verdict, so the answer is to measure again.
    A crash is a statement about the artifact or its environment: measuring again
    reproduces it, and it is a finding.

    That distinction is what a re-stamp sweep needs: `restamp_gate.undo_timeouts`
    stops a refresh from publishing a non-measurement over a green record, and a
    gate with no `timeout` status of its own (G-DIFF, G-GOLD) has no other way to
    say which of the two it hit. Reported structurally rather than by matching the
    detail text, because the detail is prose assembled per gate and each one
    spells it differently.

    Duck-typed for the same reason as `no_verdict`.
    """
    if getattr(r, "timed_out", False):
        return "timeout"
    if getattr(r, "crashed", False):
        return "crash"
    return ""


def worst_no_verdict(results) -> str:
    """`no_verdict_reason` over several checks: "crash" if any crashed, else
    "timeout" if any timed out, else "".

    A crash dominates: a gate reporting several unjudged files is a wall clock
    only if EVERY one of them was a wall clock. One broken environment among them
    is a finding, and suppressing the whole record would suppress that too.
    """
    reasons = {no_verdict_reason(r) for r in results}
    if "crash" in reasons:
        return "crash"
    return "timeout" if "timeout" in reasons else ""


def env_int(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v and v.isdigit() else default


def docker_oracle_skip(gate_name: str):
    """A GateResult(skip) when the active benchmark can't run this Docker gate,
    else None. G-RESOLVE needs `supports_docker_oracle`; G-CONF/G-AX run our
    generated check scripts and additionally need `supports_generated_script_
    gates`. Lets an unsupported benchmark yield a clean skip, never a `blocked`
    construction."""
    from ..benchmarks import active
    from .base import GateResult
    bench = active()
    needs_generated = gate_name in ("G-CONF", "G-AX")
    ok = (bench.supports_docker_oracle
          and (bench.supports_generated_script_gates or not needs_generated))
    if ok:
        return None
    return GateResult(gate_name, "skip",
                      f"benchmark {bench.name!r} does not support {gate_name} "
                      "(no wired Docker oracle / generated-script env)",
                      {"docker_oracle_unavailable": True})
