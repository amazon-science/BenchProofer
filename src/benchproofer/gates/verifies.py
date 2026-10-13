# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The specification is met by the implementation.

This is the gate that asks the verifier the question the bundle exists for.
Everything else is about whether the verdict means anything.

A rejection is a failure of the bundle. A checker that reaches no verdict, whether it
timed out, crashed, or gave up, is recorded as undecided: the bundle is then
incomplete rather than rejected, because a loaded machine must not be able to turn
a sound artifact into a finding.

Where the checker replays a proof the file writes, acceptance means the file
elaborated, which is weaker than the claim: `sorry` elaborates, and so does a proof
citing an axiom nobody established. So an accepting verdict is followed by a second
question -- which axioms each claim rests on -- and the gate passes only if both
verdicts are good. See `Backend.closure`.
"""

from __future__ import annotations

from typing import ClassVar

from ..backends.base import BackendKind
from ..core.verdict import Level, SkipReason, Verdict
from .base import Gate, GateContext

__all__ = ["VerifiesGate"]


class VerifiesGate(Gate):
    """Run the backend's checker over the solution."""

    id: ClassVar[str] = "spec.verifies"
    title: ClassVar[str] = "Verification check"
    rationale: ClassVar[str] = (
        "The bundle's central claim: the shipped implementation satisfies the "
        "shipped specification, as decided by the backend's checker."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("solution.*",)

    def judge(self, context: GateContext) -> Verdict:
        """Check the solution and translate the checker's verdict."""
        backend = context.backend
        available = backend.availability()
        if not available:
            return self.undecided(
                SkipReason.TOOLCHAIN_ABSENT,
                f"{backend.name} is unavailable: {available.detail}",
                hint=available.hint,
            )

        result = context.base_check()
        evidence = context.bundle.write_evidence("verifies.log", result.output + "\n")
        common = {
            "backend": backend.name,
            "backend_kind": str(backend.kind),
            "checker_duration_s": result.duration_s,
            "evidence": [evidence],
        }

        if result.verified:
            qualifier = (
                "proved" if backend.kind is BackendKind.PROVER else "no counterexample found"
            )
            closure = backend.closure(
                context.solution,
                workdir=context.scratch("check", "closure"),
                timeout_s=backend.budget(context.settings.verify_timeout_s),
            )
            if closure is None:
                return self.passed(f"{qualifier}: {result.detail}", **common)
            common["axioms"] = closure.depends
            if not closure.settled:
                # The proof was not found open: the question about it went unanswered.
                # Recording that as a rejection is how a slow machine becomes a defect in
                # an artifact, which is the same reason `UNKNOWN` is not `REFUTED`.
                return self.errored(f"{qualifier}, but {closure.detail}", **common)
            if not closure.closed:
                return self.failed(
                    f"the checker accepted the file, but {closure.detail}",
                    well_formed=True,
                    **common,
                )
            return self.passed(f"{qualifier}: {result.detail}; {closure.detail}", **common)
        if result.refuted:
            wording = (
                "the checker rejected the solution"
                if result.well_formed
                else "the checker could not read the solution"
            )
            return self.failed(
                f"{wording}: {result.detail}",
                well_formed=result.well_formed,
                **common,
            )
        if result.timed_out:
            return self.timed_out(f"the checker did not finish: {result.detail}", **common)
        return self.errored(f"the checker gave no verdict: {result.detail}", **common)
