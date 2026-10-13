# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Running smoke cases.

Three rules govern the runner, and all three exist to keep a green run meaningful.

*Requirements are resolved before anything runs.* Every distinct requirement of the
selected cases is probed once, sequentially, so the report can say what this machine
offered and no two cases race to run the same version check.

*Each case gets its own bundle root.* A case cannot see another's artifacts, so an
assertion about a bundle is an assertion about the bundle that case built. The
dataset cache is shared, because re-downloading a benchmark per case would make the
suite unusable.

*The four outcomes are not merged.* An exception the tool raised is a finding about
the tool; an exception the case itself raised is a defect in the suite. They are
recorded separately, and a run reports both rather than one total.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterable, Sequence
from pathlib import Path
from time import perf_counter

from ..config import Settings
from ..errors import BenchproofError
from ..log import logger
from ..util.parallel import mapped
from .model import Case, CaseResult, CaseStatus, Context, Failure, Observation, Unmet
from .probe import Probes
from .report import SuiteResult
from .suites import select

__all__ = ["Progress", "run_case", "run_cases", "run_suite"]

log = logger(__name__)


class Progress:
    """Hook for a caller that wants to follow a run.

    The default does nothing. The CLI passes an implementation that prints a line
    per case; a script can pass one that does anything else.
    """

    def start(self, total: int) -> None:
        """Called once, before the first case."""

    def finished(self, result: CaseResult) -> None:
        """Called once per case, in completion order."""

    def done(self, result: SuiteResult) -> None:
        """Called once, after the last case."""


def run_suite(
    suite: str,
    *,
    settings: Settings,
    workspace: Path,
    jobs: int = 1,
    include_slow: bool = False,
    progress: Progress | None = None,
) -> SuiteResult:
    """Run a named suite, a group, or a single case.

    Args:
        suite: What to run. See `suites.select`.
        settings: The run's settings. Each case receives a copy with its own bundle
            root and no agent session named; everything else, including
            `Settings.offline`, is used as given.
        workspace: Directory the run owns. Each case gets a subdirectory of it.
        jobs: How many cases to run at once.
        include_slow: Run the cases that download datasets or build containers, and
            select the ones a suite leaves out for taking minutes.
        progress: Optional hook.

    Returns:
        A `SuiteResult` covering every selected case, including the skipped ones.

    Raises:
        BenchproofError: ``suite`` names nothing.
    """
    return run_cases(
        select(suite, include_slow=include_slow),
        settings=settings,
        workspace=workspace,
        jobs=jobs,
        include_slow=include_slow,
        progress=progress,
        label=suite,
    )


def run_cases(
    cases: Sequence[Case],
    *,
    settings: Settings,
    workspace: Path,
    jobs: int = 1,
    include_slow: bool = False,
    progress: Progress | None = None,
    label: str = "custom",
) -> SuiteResult:
    """Run a specific set of cases and report what happened."""
    hook = progress or Progress()
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    probes = _resolved(cases, settings)
    hook.start(len(cases))

    started = perf_counter()

    def one(case: Case) -> CaseResult:
        result = run_case(
            case,
            settings=settings,
            workspace=workspace,
            include_slow=include_slow,
            probes=probes,
        )
        hook.finished(result)
        return result

    suite = SuiteResult(
        suite=label,
        results=tuple(mapped(cases, one, workers=jobs, prefix="smoke")),
        duration_s=perf_counter() - started,
    )
    hook.done(suite)
    return suite


def run_case(
    case: Case,
    *,
    settings: Settings,
    workspace: Path,
    include_slow: bool = False,
    probes: Probes | None = None,
) -> CaseResult:
    """Run one case, in its own workspace, and classify the outcome.

    Never raises: a case that falls over is reported as `CaseStatus.ERROR`, because
    a suite that stops at the first surprise reports less than one that finishes.
    """
    if case.slow and not include_slow:
        return CaseResult(
            case=case,
            status=CaseStatus.SKIPPED,
            message="slow case; include it with --slow",
        )

    resolver = probes if probes is not None else Probes(settings)
    unmet = resolver.unmet(case.requires)
    if unmet:
        return CaseResult(case=case, status=CaseStatus.SKIPPED, message=unmet)

    directory = _prepared(workspace / case.id)
    context = Context(
        case_id=case.id,
        # No agent session, whatever the machine is configured with. Every case scripts
        # its provider and its sessions from a fixture and passes them to the stage it
        # runs; a session the machine names would reach a real model, so what the case
        # observed would depend on that model and on the network.
        settings=settings.model_copy(
            update={"bundle_root": directory / "bundles", "session": ""}
        ),
        workspace=directory,
        probes=resolver,
    )

    started = perf_counter()
    try:
        observations = tuple(case.procedure(context))
    except Unmet as exc:
        return _result(case, CaseStatus.SKIPPED, started, message=str(exc))
    except Failure as exc:
        return _result(case, CaseStatus.FAILED, started, message=str(exc))
    except BenchproofError as exc:
        return _result(
            case,
            CaseStatus.FAILED,
            started,
            message=f"Benchproofer raised {type(exc).__name__}: {exc}",
        )
    except Exception as exc:
        # A case that falls over is a defect in the suite, not a finding about the
        # tool, and it must not stop the cases that follow.
        log.exception("case %s errored", case.id)
        return _result(case, CaseStatus.ERROR, started, message=f"{type(exc).__name__}: {exc}")
    return _result(case, CaseStatus.PASSED, started, observations=observations)


def _result(
    case: Case,
    status: CaseStatus,
    started: float,
    *,
    observations: tuple[Observation, ...] = (),
    message: str = "",
) -> CaseResult:
    return CaseResult(
        case=case,
        status=status,
        duration_s=perf_counter() - started,
        observations=observations,
        message=message,
    )


def _resolved(cases: Iterable[Case], settings: Settings) -> Probes:
    """Probe every requirement once, before any case runs."""
    probes = Probes(settings)
    for requirement in sorted({item for case in cases for item in case.requires}):
        availability = probes.resolve(requirement)
        log.debug("requirement %s: %s", requirement, availability.detail or availability)
    return probes


def _prepared(directory: Path) -> Path:
    """An empty directory for one case, replacing whatever a previous run left."""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    return directory
