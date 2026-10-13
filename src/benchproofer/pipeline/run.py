# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Running a whole corpus: build, review, judge, repair, report.

One task's failure never stops the others, and no task is worked on twice: the bundle on
disk is the state of the run, so a run started again picks up where the artifacts say it
stopped, and a task that raised is recorded as an error rather than retried silently.

A task goes round the loop -- judge, review, repair -- until it certifies, is dropped, or
the repair budget runs out, which is a result and not an error. Where each verdict that
does not pass goes -- to the repair, to its auditor asked again, holding the review, or
nowhere -- is `pipeline.route`'s. A round runs the gates a program decides first, and asks
the auditors, then the gates that read the review (`adjudicate.REVIEWED`), only of a
bundle none of whose verdicts goes to the repair or holds the review (`_held`), as
`verified-swebench` does: a review of a bundle already rejected is spent on files the
repair will change, and would read the evidence of the round before. Within the review, the
attack validation auditor is asked last, once the gates have re-run what the attack auditor
filed and only where they list an attack or a control that cannot be determined by execution
(`audit.review`). The loop is driven by the verdicts alone: a bundle is repaired because a gate
said something about it, and a repair that changed it is followed by another judgment. A repair
edits the bundle as it stands (`pipeline.repair`) and is shown every earlier round of this run,
what produced it and what did not pass (`core.rounds`). Every repair spends one of the repair
budget, whether its session's work was taken or not, so a task runs at most `max_repairs` repair
sessions. After a round that left the bundle as it was, the next round repairs again without
judging an unchanged bundle.

An auditor that showed too little is asked again about the unchanged bundle before
anything is repaired, by the rule `pipeline.route` states: a round that only does that
spends no repair and judges only the gates that read the review, and as no question is
asked twice of one bundle the loop stays bounded. A task whose benchmark solution fails the
benchmark's own tests here is dropped (`adjudicate.DISQUALIFYING`): that is asked before
anything is drafted for it, and a later judgment that finds it ends the loop.

A stage that could not reach a model or start a session at all ends the task on the
environment: the bundle keeps what the last round judged, and the rest of the budget is not
spent on rounds that cannot do anything either. An expired credential otherwise looks like a
model that had nothing to say, round after round.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from ..audit.session import Lane
from ..backends.base import Backend
from ..config import Settings
from ..core import replay
from ..core.bundle import Bundle
from ..core.rounds import RECORD, archived, directory
from ..core.task import Task
from ..core.verdict import Certification, Level, Outcome, Verdict
from ..errors import BenchproofError, ProviderError
from ..llm.base import Provider
from ..log import logger
from ..registries import BACKENDS, GATES
from ..util.fsio import write_text
from ..util.parallel import mapped
from .adjudicate import (
    DISQUALIFYING,
    REVIEWED,
    Adjudication,
    adjudicate,
    certify,
    classified,
)
from .audit import review
from .build import BuildResult, build
from .repair import RepairResult, chronicle, repair
from .report import Report, summarize
from .route import Question, Route, ask_again, routed

__all__ = ["Progress", "RunResult", "TaskOutcome", "execute", "judge_bundles"]

log = logger(__name__)

_Item = TypeVar("_Item")


@dataclass(frozen=True, slots=True)
class TaskOutcome:
    """What happened to one task in one run."""

    task_key: str
    bundle: Bundle
    #: True when this run drafted artifacts, as opposed to reusing them.
    built: bool = False
    #: True when this run ran gates, as opposed to reusing recorded verdicts.
    judged: bool = False
    #: True when this run had the bundle reviewed adversarially.
    reviewed: bool = False
    #: How many repairs this run made of the bundle, each one of the repair budget.
    repairs: int = 0
    #: How many rounds asked an auditor again about the unchanged bundle
    #: (`route.ask_again`). None spends a repair.
    reviewed_again: int = 0
    certification: Certification | None = None
    #: Set when the task could not be processed at all. Never a finding about the
    #: artifacts: an error here is the tool's or the environment's.
    error: str = ""
    #: Set when the run worked and produced nothing to judge, which is what a
    #: drafting stage that gave up looks like. The bundle stays unclassified, so it
    #: is reported as incomplete rather than as a failure of the tool.
    unfinished: str = ""

    @property
    def outcome(self) -> str:
        """The task's classification, or ``error`` when it could not be reached."""
        if self.error:
            return "error"
        if self.certification is None:
            return str(Outcome.INCOMPLETE)
        return str(self.certification.outcome)


@dataclass(frozen=True, slots=True)
class RunResult:
    """One run over a set of tasks or bundles."""

    #: Backends involved. Building uses one; judging bundles already on disk uses
    #: whichever backends those bundles were built with.
    backends: tuple[str, ...]
    level: Level
    outcomes: tuple[TaskOutcome, ...]
    report: Report

    @property
    def total(self) -> int:
        """How many tasks the run covered."""
        return len(self.outcomes)

    def errors(self) -> tuple[TaskOutcome, ...]:
        """Tasks that could not be processed."""
        return tuple(outcome for outcome in self.outcomes if outcome.error)

    def unfinished(self) -> tuple[TaskOutcome, ...]:
        """Tasks that produced nothing to judge, though nothing went wrong here."""
        return tuple(outcome for outcome in self.outcomes if outcome.unfinished)

    def describe(self) -> str:
        """One line for a terminal or a log."""
        counts = self.report.counts()
        failed = len(self.errors())
        parts = [f"{name}={count}" for name, count in counts.items()]
        if failed:
            parts.append(f"error={failed}")
        repairs = sum(outcome.repairs for outcome in self.outcomes)
        if repairs:
            parts.append(f"repairs={repairs}")
        reviewed_again = sum(outcome.reviewed_again for outcome in self.outcomes)
        if reviewed_again:
            parts.append(f"reviewed_again={reviewed_again}")
        return f"{self.total} task(s) at level={self.level}: " + ", ".join(parts)


class Progress:
    """Hook for a caller that wants to display progress.

    The default does nothing. The CLI passes an implementation that updates a
    terminal; a script can pass one that writes a line per task.
    """

    def start(self, total: int) -> None:
        """Called once, before any task is processed."""

    def finished(self, outcome: TaskOutcome) -> None:
        """Called once per task, in completion order."""

    def done(self, result: RunResult) -> None:
        """Called once, after the last task."""


def execute(
    tasks: list[Task],
    *,
    backend: Backend,
    provider: Provider,
    settings: Settings,
    level: Level = Level.STATIC,
    reviewer: Provider | None = None,
    rebuild: bool = False,
    judge: bool = True,
    skip_certified: bool = True,
    progress: Progress | None = None,
) -> RunResult:
    """Build, review, judge and repair every task, then report.

    Args:
        tasks: Frozen tasks, usually from `pipeline.ingest`.
        backend: Verification backend to formalize into.
        provider: Model provider used for drafting. Not consulted for a task whose
            artifacts already exist unless ``rebuild`` is set.
        settings: Budgets, thresholds, and the bundle root.
        level: Evidence level to judge at. At `Level.AUDITED` each bundle is also
            reviewed adversarially before it is judged. Certification is computed from
            the gates required *at this level*, so raising the level over a corpus judged
            at a lower one costs only the gates not asked before: `skip_certified` does
            not skip a bundle certified only below it, and the verdicts already in its
            `manifest.json` still count. Runs under different *settings* -- another threshold,
            input budget or toolchain -- mix silently in one bundle root, since the
            `manifest.json` records the verdict and not the run; give such a run its own
            `bundle_root`.
        reviewer: Model provider for that review. Defaults to ``provider``, which the
            `audit.independence` gate then reports as a self-review; pass a different
            model to satisfy it.
        rebuild: Draft artifacts again even when the bundle already has them.
        judge: Run the gates at all. False drafts artifacts and stops, which leaves
            every bundle unclassified rather than favorably classified. No bundle is
            reviewed or repaired either, both being responses to a verdict.
        skip_certified: Leave a bundle alone once it certifies at this level.
        progress: Optional observer.

    Returns:
        One `TaskOutcome` per task, in the order the tasks were given, plus a report
        over exactly the bundles this run touched.
    """

    def one(task: Task) -> TaskOutcome:
        return _process(
            task,
            backend=backend,
            provider=provider,
            reviewer=reviewer or provider,
            settings=settings,
            level=level,
            rebuild=rebuild,
            judge=judge,
            skip_certified=skip_certified,
        )

    return _drive(
        tasks, one, backends=(backend.name,), settings=settings, level=level, progress=progress
    )


def judge_bundles(
    bundles: list[Bundle],
    *,
    settings: Settings,
    level: Level = Level.STATIC,
    only: tuple[str, ...] = (),
    waivers: dict[str, str] | None = None,
    skip_certified: bool = False,
    progress: Progress | None = None,
) -> RunResult:
    """Judge bundles that already exist, each with the backend it was built with.

    This is the path for judging someone else's artifacts, or for re-judging after a
    gate changed. Nothing is drafted, so no model is consulted and no bundle is
    modified outside its ``evidence/`` directory and its `manifest.json`.

    Args:
        bundles: Bundles to judge, usually from `adjudicate.bundles_under`.
        settings: Budgets and thresholds.
        level: Evidence level to judge at.
        only: Run just these gates, and classify from the whole of `manifest.json`.
        waivers: Gate ids whose failures are recorded as waived, each with the reason
            given for it. `adjudicate` refuses one that names a gate the central
            claim rests on.
        skip_certified: Leave a bundle alone once it certifies at this level.
        progress: Optional observer.
    """
    backends = tuple(sorted({bundle.backend_name for bundle in bundles}))

    def one(bundle: Bundle) -> TaskOutcome:
        return _judge_one(
            bundle,
            settings=settings,
            level=level,
            only=only,
            waivers=waivers,
            skip_certified=skip_certified,
        )

    return _drive(
        bundles, one, backends=backends, settings=settings, level=level, progress=progress
    )


def _drive(
    items: list[_Item],
    worker: Callable[[_Item], TaskOutcome],
    *,
    backends: tuple[str, ...],
    settings: Settings,
    level: Level,
    progress: Progress | None,
) -> RunResult:
    """Run one worker over every item, then report on the bundles it touched."""
    watcher = progress or Progress()
    watcher.start(len(items))

    def one(item: _Item) -> TaskOutcome:
        outcome = worker(item)
        watcher.finished(outcome)
        return outcome

    outcomes = mapped(items, one, workers=settings.concurrency, prefix="task")
    report = summarize(
        [outcome.bundle for outcome in outcomes if outcome.bundle.exists],
        level=level,
        root=Path(settings.bundle_root),
    )
    result = RunResult(backends=backends, level=level, outcomes=tuple(outcomes), report=report)
    log.info("%s", result.describe())
    watcher.done(result)
    return result


def _judge_one(
    bundle: Bundle,
    *,
    settings: Settings,
    level: Level,
    only: tuple[str, ...],
    waivers: dict[str, str] | None,
    skip_certified: bool,
) -> TaskOutcome:
    """Judge one existing bundle, and never raise."""
    key = bundle.root.as_posix()
    try:
        key = bundle.manifest().task_id
        if skip_certified and certify(bundle, level).certified:
            return TaskOutcome(
                task_key=key, bundle=bundle, certification=certify(bundle, level)
            )
        adjudication = adjudicate(
            bundle,
            backend=BACKENDS.get(bundle.backend_name),
            settings=settings,
            level=level,
            only=only,
            waivers=waivers,
        )
        return TaskOutcome(
            task_key=key,
            bundle=bundle,
            judged=True,
            certification=adjudication.certification,
        )
    except BenchproofError as exc:
        log.warning("%s could not be judged: %s", key, exc)
        return TaskOutcome(task_key=key, bundle=bundle, error=str(exc))
    except Exception as exc:
        log.exception("%s raised", key)
        return TaskOutcome(task_key=key, bundle=bundle, error=f"{type(exc).__name__}: {exc}")


def _process(
    task: Task,
    *,
    backend: Backend,
    provider: Provider,
    reviewer: Provider,
    settings: Settings,
    level: Level,
    rebuild: bool,
    judge: bool,
    skip_certified: bool,
) -> TaskOutcome:
    """Take one task as far as it needs to go, and never raise."""
    bundle = Bundle.locate(settings.bundle_root, task, backend.name)
    try:
        if skip_certified and bundle.exists and certify(bundle, level).certified:
            log.info("%s already certified at level=%s", task.key, level)
            return TaskOutcome(
                task_key=task.key, bundle=bundle, certification=certify(bundle, level)
            )

        if judge and level.covers(Level.ORACLE):
            screened = _screen(task, backend=backend, settings=settings, level=level)
            if screened.certification.outcome is Outcome.DROPPED:
                log.info(
                    "%s is dropped before anything is drafted for it: %s",
                    task.key,
                    screened.certification.describe(),
                )
                return TaskOutcome(
                    task_key=task.key,
                    bundle=screened.bundle,
                    judged=True,
                    certification=screened.certification,
                )
            bundle = screened.bundle

        built: BuildResult | None = None
        if rebuild or not _has_solution(bundle):
            built = build(task, backend=backend, provider=provider, settings=settings)
            bundle = built.bundle
            if not built.usable:
                return TaskOutcome(
                    task_key=task.key,
                    bundle=bundle,
                    built=True,
                    unfinished=(
                        "no solution file was produced, so there is nothing to judge; "
                        f"see notes in {bundle.root}"
                    ),
                )

        if not judge:
            return TaskOutcome(task_key=task.key, bundle=bundle, built=built is not None)

        reviewed = False
        repairs = reviewed_again = 0
        budget = max(0, settings.max_repairs)
        # Every round of this run as it was judged, for a repair and the review to read; an
        # earlier run's rounds judged other code.
        history = directory(bundle, settings.cache_dir)
        shutil.rmtree(history, ignore_errors=True)
        # The auditors the next round asks again beside those `due` names, and the
        # questions asked again of the bundle as it stands (`route.ask_again`).
        again: tuple[Lane, ...] = ()
        asked: set[Question] = set()
        # False after a repair that left the bundle as it was, whose verdicts judging it
        # again would only repeat.
        changed = True
        # False for a round that only asks auditors again, which judges only the gates that
        # read the review.
        remeasure = True
        # The verdicts about the bundle as it stands, which a repair addresses. `manifest.json`
        # also holds verdicts a round did not reach, such as a review's from before the repair.
        current: dict[str, Verdict] = {}
        while True:
            if changed:
                judged, asked_lanes = _judge(
                    bundle,
                    backend=backend,
                    reviewer=reviewer,
                    settings=settings,
                    level=level,
                    again=again,
                    remeasure=remeasure,
                    current=current,
                )
                reviewed = reviewed or asked_lanes
                _archive(bundle, history, current, () if remeasure else again)
            if judged.certified:
                break
            if judged.certification.outcome is Outcome.DROPPED:
                log.info("%s is dropped: %s", task.key, judged.certification.describe())
                break
            again = ask_again(current, level, asked)
            if again:
                log.info(
                    "%s: the review showed too little, so %s is asked again before anything "
                    "is repaired",
                    task.key,
                    ", ".join(again),
                )
                reviewed_again += 1
                remeasure = False
                continue
            if repairs >= budget:
                break
            repaired = _repair(
                bundle,
                backend=backend,
                settings=settings,
                level=level,
                history=history,
                current=current,
            )
            if repaired is None:
                if routed(current, level)[Route.ASK_AGAIN]:
                    log.info(
                        "%s: the review fell short the same way on the same bundle, so the "
                        "task ends rather than asking that auditor a third time",
                        task.key,
                    )
                break
            repairs += 1
            changed = repaired.changed
            remeasure = True
            if changed:
                asked.clear()
            else:
                log.info(
                    "%s: the repair left the bundle as it was, so it is not judged again "
                    "before the next repair",
                    task.key,
                )

        return TaskOutcome(
            task_key=task.key,
            bundle=bundle,
            built=built is not None,
            judged=True,
            reviewed=reviewed,
            repairs=repairs,
            reviewed_again=reviewed_again,
            certification=judged.certification,
        )
    except ProviderError as exc:
        # The loop stops where it is, with the bundle as the last round judged it. Spending
        # the rest of the budget on rounds that cannot reach a model would read afterwards
        # as a bundle no repair could help.
        log.warning("%s ended on the environment rather than on the bundle: %s", task.key, exc)
        return TaskOutcome(task_key=task.key, bundle=bundle, error=str(exc))
    except BenchproofError as exc:
        log.warning("%s could not be processed: %s", task.key, exc)
        return TaskOutcome(task_key=task.key, bundle=bundle, error=str(exc))
    except Exception as exc:
        log.exception("%s raised", task.key)
        return TaskOutcome(
            task_key=task.key, bundle=bundle, error=f"{type(exc).__name__}: {exc}"
        )


def _judge(
    bundle: Bundle,
    *,
    backend: Backend,
    reviewer: Provider,
    settings: Settings,
    level: Level,
    again: Sequence[Lane],
    remeasure: bool,
    current: dict[str, Verdict],
) -> tuple[Adjudication, bool]:
    """Judge one round, and say whether an auditor was asked.

    Below `Level.AUDITED` every gate runs at once. At it, the gates a program decides run
    first; only a bundle none of them holds back (`_held`) is reviewed, and then the gates
    that read the review run, with `impl.conformance` where the review added defect inputs to
    those on record (`core.replay`), which its run compares. A round that only asks auditors
    again (``remeasure`` false) skips the first step, since the bundle is the one those gates
    just judged. ``current`` is left holding the verdicts about the bundle as it now stands.
    """
    if not level.covers(Level.AUDITED):
        judged = adjudicate(bundle, backend=backend, settings=settings, level=level)
        current.clear()
        current.update(judged.verdicts)
        return judged, False
    if remeasure:
        decided = tuple(name for name in GATES.names() if name not in REVIEWED)
        judged = adjudicate(
            bundle, backend=backend, settings=settings, level=level, only=decided
        )
        current.clear()
        current.update(judged.verdicts)
        held = _held(current)
        if held:
            log.info(
                "%s: %s did not pass, so the bundle is not reviewed until a repair "
                "addresses it",
                bundle.root.as_posix(),
                ", ".join(held),
            )
            return judged, False
    on_record = len(replay.stored(bundle))
    reviewed = review(
        bundle, backend=backend, provider=reviewer, settings=settings, level=level, again=again
    )
    asked = reviewed is not None
    gates = REVIEWED
    if len(replay.stored(bundle)) > on_record:
        gates = ("impl.conformance", *REVIEWED)
    judged = adjudicate(bundle, backend=backend, settings=settings, level=level, only=gates)
    current.update(judged.verdicts)
    return judged, asked


def _held(verdicts: dict[str, Verdict]) -> list[str]:
    """The gates a program decides whose verdicts keep the bundle from being reviewed.

    Those routed to the repair or to holding the review (`route`), and the failures of a
    task that is dropped. Not a verdict that stops, such as a gate's own crash: holding the
    review back for it would end the task with its budget unspent.
    """
    standing = classified(verdicts, Level.ORACLE)
    if standing.outcome is Outcome.DROPPED:
        return standing.failed
    routes = routed(verdicts, Level.ORACLE)
    return [verdict.gate for verdict in (*routes[Route.REPAIR], *routes[Route.HOLD])]


def _repair(
    bundle: Bundle,
    *,
    backend: Backend,
    settings: Settings,
    level: Level,
    history: Path,
    current: dict[str, Verdict],
) -> RepairResult | None:
    """Repair the bundle to address its unfavorable verdicts among ``current``.

    ``history`` is this run's earlier rounds, for a repair by an agent session to read.

    Returns:
        What the repair did. None when nothing is left a repair could address, as for a
        bundle held up only by a toolchain that is not installed; another round would do
        no better.

    Raises:
        ProviderError: The session could not be started. That is the environment's fault,
            and a round that spent itself on it would leave the bundle looking like one a
            repair could not help.
    """
    addressing = routed(current, level)[Route.REPAIR]
    if not addressing:
        return None
    log.info(
        "repairing %s to address %s",
        bundle.root.as_posix(),
        ", ".join(verdict.gate for verdict in addressing),
    )
    return repair(
        bundle,
        backend=backend,
        settings=settings,
        verdicts=addressing,
        history=history,
    )


def _archive(
    bundle: Bundle, history: Path, current: dict[str, Verdict], again: Sequence[Lane]
) -> None:
    """Keep the bundle as this round judged it, for the rounds that follow.

    A round's files exist nowhere else once a repair has edited them. Its manifest keeps the
    verdicts this round reached, ``current``, and not those of gates it did not run, and
    `round.md` says what produced the bundle -- drafting, the repairs since the round
    before, or the auditors ``again`` names asked again -- and what did not pass
    (`repair.chronicle`).
    """
    history.mkdir(parents=True, exist_ok=True)
    earlier = archived(history)
    target = Bundle(history / f"{sum(1 for entry in history.iterdir() if entry.is_dir()):02d}")
    shutil.copytree(bundle.root, target.root)
    manifest = target.manifest()
    manifest.verdicts = dict(current)
    target.save_manifest(manifest)
    record = chronicle(bundle, target.root.name, current, earlier, again)
    write_text(target.root / RECORD, record)


def _screen(task: Task, *, backend: Backend, settings: Settings, level: Level) -> Adjudication:
    """Judge the task's own checks (`DISQUALIFYING`) before anything is drafted for it.

    They need only the frozen task, so a task that fails one is dropped before the
    drafting, review and repair it would otherwise cost, none of which could address it.
    """
    bundle = Bundle.create(settings.bundle_root, task, backend.name)
    return adjudicate(
        bundle, backend=backend, settings=settings, level=level, only=DISQUALIFYING
    )


def _has_solution(bundle: Bundle) -> bool:
    """True when the bundle already holds a solution file."""
    return bundle.exists and any(bundle.root.glob("solution.*"))
