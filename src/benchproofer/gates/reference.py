# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The golden patch passes the benchmark's tests.

This gate judges the benchmark's tests, not the bundle. If they reject the golden patch the
benchmark itself ships, then they are misconfigured here: a missing image, an unapplied test
patch, a test id that no longer exists. Every conclusion drawn from those tests is void,
including a favorable conformance verdict, so a bundle whose task fails this check cannot be
certified at level `oracle`.

Running it costs one run of the benchmark's tests per task, which is why it is a gate of its
own rather than a precondition buried inside another one: the result is recorded, with the
output that produced it. A golden patch that does not resolve is run again, up to `ATTEMPTS`
times, and resolving on any attempt counts, as `verified-swebench`'s G-RESOLVE counts it: the
golden patch resolves deterministically, and a test that races on a loaded host or reaches
the network does not, so one unlucky run does not show the tests misconfigured.

Nothing a draft or a repair writes is among its sources, so a pass or a failure recorded
from the same `task.json` and `reference.patch` by the same gate code is returned as it
is, and the benchmark's tests run once per task rather than once per round.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.provenance import judge_digest
from ..core.verdict import Level, SkipReason, Status, Verdict
from ..oracles.base import Candidate, OracleStatus
from .base import Gate, GateContext

__all__ = ["ATTEMPTS", "ReferenceResolvesGate"]

#: How many times the golden patch is run before a failure to resolve is believed.
ATTEMPTS = 3


class ReferenceResolvesGate(Gate):
    """Check that the benchmark's tests accept the task's golden patch."""

    id: ClassVar[str] = "oracle.reference_resolves"
    title: ClassVar[str] = "Resolution check"
    rationale: ClassVar[str] = (
        "Catches benchmark tests misconfigured here, whose verdicts about anything else "
        "would be meaningless."
    )
    level: ClassVar[Level] = Level.ORACLE
    sources: ClassVar[tuple[str, ...]] = ("../task.json", "../reference.patch")

    def judge(self, context: GateContext) -> Verdict:
        """Run the benchmark's tests on the golden patch, unless they ran on these sources."""
        recorded = context.bundle.manifest().verdicts.get(self.id)
        if (
            recorded is not None
            and recorded.status in (Status.PASS, Status.FAIL)
            and recorded.judge_digest == judge_digest()
            and recorded.inputs == self._input_digests(context.bundle)
        ):
            return recorded
        task = context.task
        oracle = self.needs_oracle(context)
        if isinstance(oracle, Verdict):
            return oracle
        candidate = Candidate.reference(task)
        if candidate.is_empty and not task.context.files:
            return self.undecided(
                SkipReason.ARTIFACT_ABSENT,
                f"{task.key} ships no golden patch to check the benchmark's tests with",
            )

        results = []
        for attempt in range(1, ATTEMPTS + 1):
            results.append(
                oracle.judge(
                    task,
                    candidate,
                    workdir=context.scratch("reference", str(attempt)),
                    timeout_s=context.settings.oracle_timeout_s,
                )
            )
            if results[-1].resolved:
                break
        # The attempt that resolved; failing that, the last that ran to a verdict, before
        # one that never did.
        result = next(
            (r for r in reversed(results) if r.status is OracleStatus.UNRESOLVED), results[-1]
        )
        if results[-1].resolved:
            result = results[-1]
        evidence = context.bundle.write_evidence("reference.log", result.output + "\n")
        common = {
            "oracle": oracle.name,
            "oracle_duration_s": round(sum(r.duration_s for r in results), 3),
            "attempts": len(results),
            "evidence": [evidence],
        }

        if result.resolved:
            retried = (
                f" (on attempt {len(results)} of {ATTEMPTS}: an earlier one did not resolve)"
                if len(results) > 1
                else ""
            )
            return self.passed(
                f"the benchmark's tests ({oracle.name}) accept the golden patch: "
                f"{result.detail}" + retried,
                **common,
            )
        if result.status is OracleStatus.UNRESOLVED:
            return self.failed(
                f"the benchmark's tests ({oracle.name}) reject the golden patch in "
                f"{len(results)} attempt(s), so they are misconfigured for this task: "
                f"{result.detail}",
                failed_tests=list(result.failed[:20]),
                **common,
            )
        if result.status is OracleStatus.UNAVAILABLE:
            return self.undecided(
                SkipReason.ORACLE_UNAVAILABLE,
                f"the benchmark's tests could not be run here: {result.detail}",
                **common,
            )
        if result.timed_out:
            return self.timed_out(
                f"the benchmark's tests did not finish: {result.detail}", **common
            )
        return self.errored(f"running the benchmark's tests failed: {result.detail}", **common)
