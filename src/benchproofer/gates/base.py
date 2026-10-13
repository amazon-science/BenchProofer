# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The gate interface.

A gate is a mechanical check that produces one `Verdict` about one bundle.
Subclasses implement `judge`; `run` is a template method that must not be
overridden, because it enforces the properties `manifest.json` relies on:

* Every verdict carries the version and source digest of the judge that made it,
  so a stale record is detectable rather than merely old.
* Every verdict names the artifacts it was computed from, with their digests.
* An unexpected exception becomes an `error` verdict, never a `fail`. A crashed
  gate is the tool's problem; recording it as a finding would attribute the
  tool's own defect to the artifact under review.
* A gate that does not apply says so explicitly, with a machine-readable reason,
  because an absent verdict and a favorable one must never read the same.
"""

from __future__ import annotations

import time
import traceback
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from ..core.bundle import Bundle
from ..core.provenance import judge_digest, tool_version
from ..core.task import Task
from ..core.verdict import Level, SkipReason, Status, Verdict
from ..errors import GateError, PluginError
from ..log import logger
from ..util.digest import digest_file

if TYPE_CHECKING:
    from ..backends.base import Backend, CheckResult
    from ..config import Settings
    from ..oracles.base import Oracle

__all__ = ["Gate", "GateContext"]

_log = logger(__name__)

_T = TypeVar("_T")


@dataclass
class GateContext:
    """Everything a gate is allowed to look at.

    Gates receive a context rather than reaching for global state, so a caller can
    judge a bundle with a different backend instance, a different evidence level,
    or a stub oracle without touching configuration.
    """

    bundle: Bundle
    backend: Backend
    settings: Settings
    level: Level = Level.STATIC
    #: Gates whose failures this run records as waived, with the reason given for each,
    #: which is what separates a waiver from suppressing the objection.
    #: `pipeline.adjudicate.UNWAIVABLE` lists the gates no reason can cover.
    waivers: dict[str, str] = field(default_factory=dict)
    #: Whether a gate may read what an earlier judgment of the same files recorded rather than
    #: run it again, as the gates that re-run a review's submissions do with the benchmark's
    #: tests (`gates.audit`). `pipeline.adjudicate` allows it; a caller judging one bundle
    #: under a changed checker or oracle of its own leaves it off.
    reuse: bool = False
    _task: Task | None = None
    _solution: str | None = None
    _base: CheckResult | None = None
    _shared: dict[str, Any] = field(default_factory=dict)

    @property
    def task(self) -> Task:
        """The frozen task, loaded once per context."""
        if self._task is None:
            self._task = self.bundle.task()
        return self._task

    @property
    def solution(self) -> str:
        """The solution file, read once per context."""
        if self._solution is None:
            self._solution = self.bundle.solution()
        return self._solution

    def oracle(self) -> Oracle:
        """Resolve the oracle the task declares.

        Raises:
            PluginError: The task names an oracle that is not registered.
        """
        from ..registries import ORACLES

        return ORACLES.get(self.task.oracle.kind)

    def scratch(self, *parts: str) -> Path:
        """A working directory only this bundle uses. See `Bundle.scratch`."""
        return self.bundle.scratch(self.settings.cache_dir, "gates", *parts)

    def check(self, source: str, slot: str) -> CheckResult:
        """Run the backend's checker over one variant of the solution.

        Gates that judge a bundle by how the checker reacts to a modified implementation (a
        pre-fix implementation, a mutant, a rival) all go through here, so they share one budget
        and one scratch layout.
        """
        return self.backend.check(
            source,
            workdir=self.scratch("check", slot),
            timeout_s=self.backend.budget(self.settings.verify_timeout_s),
        )

    def base_check(self) -> CheckResult:
        """The checker's verdict about the shipped solution, computed once.

        Several gates need it: one to report it, and the others because how the
        checker reacts to a *variant* of an implementation only means something if
        the implementation itself verifies. Caching it on the context keeps that from
        costing one verifier invocation per gate.
        """
        if self._base is None:
            self._base = self.check(self.solution, "solution")
        return self._base

    def shared(self, key: str, derive: Callable[[], _T]) -> _T:
        """Compute an expensive derivation once for every gate that reads it.

        `base_check` is the same idea with a name of its own. This is for derivations
        two gates draw different conclusions from -- re-running a review's submissions
        yields both the too-weak and the too-strong finding -- where doing the work per
        gate would double the verifier and oracle invocations to reach the same rows.
        """
        if key not in self._shared:
            self._shared[key] = derive()
        return self._shared[key]  # type: ignore[no-any-return]


class Gate(ABC):
    """Base class for gates."""

    #: Dotted registry id, matching the entry point.
    id: ClassVar[str]
    #: Short human-readable name used in reports.
    title: ClassVar[str] = ""
    #: What this gate would catch, in one sentence, shown by ``benchproofer gates``.
    rationale: ClassVar[str] = ""
    #: Evidence level at which this gate is meaningful.
    level: ClassVar[Level] = Level.STATIC
    #: Bundle-relative artifacts whose digests are recorded on the verdict. Globs
    #: are allowed; ``../`` reaches the frozen task directory.
    sources: ClassVar[tuple[str, ...]] = ()

    # ---- required -------------------------------------------------------

    @abstractmethod
    def judge(self, context: GateContext) -> Verdict:
        """Judge one bundle.

        Build the verdict with `self.passed`, `self.failed`, or `self.undecided`.
        Raise `GateError` when the check cannot be performed; do not report a
        failure you are not sure of.
        """

    # ---- optional -------------------------------------------------------

    def needs_verified_base(self, context: GateContext) -> Verdict | None:
        """Refuse to measure specification strength on an unverified implementation.

        Return None when the shipped implementation verifies, and otherwise a skip
        verdict to return from `judge`. A gate that corrupts an implementation, or
        swaps in another one, reads the checker's rejection as evidence that the
        specification is doing work. If the shipped implementation is itself
        rejected, every variant of it is rejected too, and the measurement would
        report strength that was never demonstrated.
        """
        result = context.base_check()
        if result.verified:
            return None
        if not result.decided:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"the checker reached no verdict on the shipped solution "
                f"({result.detail}), so this measurement would say nothing",
            )
        return self.undecided(
            SkipReason.INCONCLUSIVE,
            f"the shipped implementation does not verify ({result.detail}), so how the "
            "checker reacts to a variant of it (a copy with some regions replaced) is not "
            "evidence about the specification; "
            "spec.verifies (Verification check) is where that is recorded",
        )

    def needs_oracle(self, context: GateContext) -> Oracle | Verdict:
        """Resolve the benchmark's own correctness oracle, or say why there is none.

        Returns the oracle, or the verdict to return from `judge` in its place. Three
        things can stand in the way, and none of them is a finding about the bundle: a
        benchmark that ships no oracle, an oracle this installation does not register,
        and an oracle that cannot run on this machine.
        """
        if context.task.oracle.kind == "none":
            return self.undecided(
                SkipReason.ORACLE_UNAVAILABLE,
                f"{context.task.benchmark} declares no tests to judge correctness by, so there "
                "is nothing to put this bundle to",
            )
        try:
            oracle = context.oracle()
        except PluginError as exc:
            return self.errored(str(exc))
        available = oracle.availability()
        if not available:
            return self.undecided(
                SkipReason.ORACLE_UNAVAILABLE,
                f"the benchmark's tests ({oracle.name}) are unavailable: {available.detail}",
                hint=available.hint,
            )
        return oracle

    def applies(self, context: GateContext) -> str | None:
        """Return a reason to skip, or None to run.

        The default runs a gate whenever the requested evidence level is at least
        the gate's own level.
        """
        if not context.level.covers(self.level):
            return f"run is at level={context.level}"
        return None

    # ---- the recorded path ----------------------------------------------

    def run(self, context: GateContext) -> Verdict:
        """Judge one bundle and stamp the result. Do not override."""
        started = time.monotonic()
        reason = self.applies(context)
        if reason is not None:
            verdict = Verdict(
                gate=self.id,
                status=Status.SKIP,
                skip_reason=SkipReason.NOT_APPLICABLE,
                summary=reason,
            )
        else:
            try:
                verdict = self.judge(context)
            except GateError as exc:
                verdict = self.errored(str(exc))
            except Exception as exc:  # noqa: BLE001 - recorded, never raised on
                _log.debug("gate %s crashed: %s", self.id, exc, exc_info=True)
                verdict = self.errored(
                    f"{type(exc).__name__}: {exc}",
                    traceback="".join(traceback.format_exception(exc))[-4000:],
                )

        return self._stamp(verdict, context, time.monotonic() - started)

    def _stamp(self, verdict: Verdict, context: GateContext, duration_s: float) -> Verdict:
        because = context.waivers.get(self.id)
        if verdict.status is Status.FAIL and because is not None:
            verdict = verdict.model_copy(
                update={
                    "status": Status.WAIVED,
                    "summary": f"waived ({because}): {verdict.summary}",
                    "details": {
                        **verdict.details,
                        "waived_from": str(Status.FAIL),
                        "waived_because": because,
                    },
                }
            )
        return verdict.model_copy(
            update={
                "gate": self.id,
                "level": self.level,
                "duration_s": round(duration_s, 3),
                "judge_digest": judge_digest(),
                "tool_version": tool_version(),
                "inputs": verdict.inputs or self._input_digests(context.bundle),
            }
        )

    def _input_digests(self, bundle: Bundle) -> dict[str, str]:
        digests: dict[str, str] = {}
        for pattern in self.sources:
            base = bundle.task_dir if pattern.startswith("../") else bundle.root
            for match in sorted(base.glob(pattern.removeprefix("../"))):
                if match.is_file():
                    key = match.relative_to(bundle.root.parent).as_posix()
                    digests[key] = digest_file(match)
        return digests

    # ---- verdict constructors -------------------------------------------

    def passed(self, summary: str, **details: Any) -> Verdict:
        """Build a passing verdict."""
        return self._verdict(Status.PASS, summary, details)

    def failed(self, summary: str, **details: Any) -> Verdict:
        """Build a failing verdict. Use only when the finding is established."""
        return self._verdict(Status.FAIL, summary, details)

    def undecided(self, reason: SkipReason, summary: str, **details: Any) -> Verdict:
        """Build a skip verdict with an explicit reason."""
        verdict = self._verdict(Status.SKIP, summary, details)
        return verdict.model_copy(update={"skip_reason": reason})

    def weakness(self, context: GateContext, summary: str, **details: Any) -> Verdict:
        """Report that the specification admits something it should not.

        Under a prover, the checker accepting a wrong implementation is a proof
        that the specification is too weak, and that is a finding. Under a
        falsifier, it only means no counterexample turned up inside the search
        budget, so the same observation is recorded as inconclusive: a slow machine
        must not be able to manufacture a defect in a sound artifact.
        """
        from ..backends.base import BackendKind

        if context.backend.kind is BackendKind.PROVER:
            return self.failed(summary, **details)
        return self.undecided(
            SkipReason.INCONCLUSIVE,
            f"{summary}; {context.backend.name} is a falsifier, so this is a search "
            "shortfall rather than a demonstration of weakness",
            **details,
        )

    def timed_out(self, summary: str, **details: Any) -> Verdict:
        """Build a timeout verdict, which is undecided rather than failing."""
        return self._verdict(Status.TIMEOUT, summary, details)

    def errored(self, summary: str, **details: Any) -> Verdict:
        """Build an error verdict, recording a defect in the check itself."""
        return self._verdict(Status.ERROR, summary, details)

    def _verdict(self, status: Status, summary: str, details: dict[str, Any]) -> Verdict:
        evidence = details.pop("evidence", [])
        return Verdict(
            gate=self.id,
            status=status,
            summary=summary,
            level=self.level,
            details=details,
            evidence=list(evidence),
        )

    def __repr__(self) -> str:
        return f"<{type(self).__name__} id={self.id!r}>"
