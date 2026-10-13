# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Do the gates reach the verdicts the fixtures were built to provoke.

This is the group that tests Benchproofer's judgment rather than its plumbing. Each
packaged fixture is a bundle written to provoke exactly one reaction, and it declares
that reaction next to its artifacts, so a case compares the adjudication against a
claim a reviewer can read in the fixture itself:

* **coin-change-sound** is certified, which is the only way to know the gates are not
  merely rejecting everything.
* **coin-change-weak** has a specification that misses the point of the task. It is
  left incomplete, and the three gates that attack strength report that they could not
  decide, because a falsifier that finds no counterexample has not shown there is
  none.
* **running-total-leaky** restates the golden patch and is rejected, which no
  verification result would ever reveal.
* **safe-join-assumed** models an unchanged callee in its axioms region, and is
  certified because its axioms.py grounds the model against the real callee.

Two further cases cover the paths a reviewer relies on: a waiver, which has to be
recorded as a waiver rather than as a pass, and a bundle edited after it was judged,
which has to stop being certified.
"""

from __future__ import annotations

from ...core import markers
from ...core.bundle import Bundle
from ...core.verdict import Level, Outcome, Status
from ...errors import BenchproofError
from ...pipeline.adjudicate import GATE_ORDER, adjudicate, certify
from ...pipeline.build import build
from ...registries import BACKENDS
from ...util.fsio import write_text
from .. import fixtures
from ..fixtures import Fixture
from ..model import Case, Context, Failure, Observation, Procedure, check, equals
from ..scripted import ScriptedProvider, ScriptedSession

__all__ = ["CASES"]

#: The fixtures are judged at the strongest level they can reach offline: their
#: oracle runs assertions in a subprocess, so no container is involved.
LEVEL = Level.ORACLE

#: A different implementation, spliced in to stand for a bundle edited after it was
#: judged. It is wrong, but the point of the case is that nobody has to notice.
_SWAPPED = """def impl(cents):
    return (0, 0, 0, cents)
"""


def _staged(context: Context, name: str) -> tuple[Fixture, Bundle]:
    """Ingest the fixture tasks and copy one fixture into this case's bundle root."""
    target = fixtures.fixture(name)
    tasks = fixtures.tasks(context.settings)
    task = tasks.get(target.task_id)
    check(task is not None, f"the fixture corpus has no task {target.task_id!r}")
    assert task is not None  # noqa: S101 - narrowing after the check above
    return target, fixtures.stage(target, task, context.settings)


def _procedure(name: str) -> Procedure:
    """Build the case procedure for one fixture bundle."""

    def run(context: Context) -> list[Observation]:
        target, bundle = _staged(context, name)
        backend = BACKENDS.get(target.backend)
        adjudication = adjudicate(
            bundle,
            backend=backend,
            settings=context.settings,
            level=LEVEL,
        )
        certification = adjudication.certification

        # Every built-in gate has to have produced a verdict. A third-party gate may
        # have produced one too, which is not this case's business: certification
        # depends on the required set, so an installed plugin cannot change it.
        silent = sorted(set(GATE_ORDER) - set(adjudication.verdicts))
        check(
            not silent,
            f"{name}: gate(s) produced no verdict at all: {', '.join(silent)}",
        )
        errored = sorted(
            gate_id
            for gate_id, verdict in adjudication.verdicts.items()
            if verdict.status is Status.ERROR
        )
        check(
            not errored,
            f"{name}: gate(s) crashed, so their verdicts say nothing about the bundle: "
            f"{', '.join(errored)}",
        )
        unstamped = sorted(
            gate_id
            for gate_id, verdict in adjudication.verdicts.items()
            if not verdict.judge_digest or not verdict.tool_version
        )
        check(
            not unstamped,
            f"{name}: verdict(s) have no judge digest or tool version, so a stale "
            f"record would be undetectable: {', '.join(unstamped)}",
        )

        equals(
            certification.outcome,
            target.expected(LEVEL),
            f"{name}: outcome at level={LEVEL} ({certification.describe()})",
        )
        objected = tuple(
            sorted({*certification.failed, *certification.undecided, *certification.missing})
        )
        equals(
            objected,
            target.unfavorable_at(LEVEL),
            f"{name}: the gates that objected ({certification.describe()})",
        )

        recorded = certify(bundle, LEVEL)
        equals(
            recorded.outcome,
            certification.outcome,
            f"{name}: outcome recomputed from the written manifest.json",
        )

        observations = [
            Observation("outcome", certification.describe()),
            Observation("gates", f"{len(adjudication.verdicts)} ran"),
        ]
        observations.extend(
            Observation(
                gate_id,
                f"{adjudication.verdicts[gate_id].status}: "
                f"{adjudication.verdicts[gate_id].summary}",
            )
            for gate_id in objected
        )
        return observations

    return run


def waiver(context: Context) -> list[Observation]:
    """A waived failure certifies the bundle, and is recorded as waived."""
    target, bundle = _staged(context, "running-total-leaky")
    backend = BACKENDS.get(target.backend)
    gate_id = "spec.no_leakage"

    plain = adjudicate(
        bundle,
        backend=backend,
        settings=context.settings,
        level=LEVEL,
    )
    equals(plain.verdicts[gate_id].status, Status.FAIL, f"{gate_id} without a waiver")
    equals(plain.certification.outcome, Outcome.REJECTED, "outcome without a waiver")

    waived = adjudicate(
        bundle,
        backend=backend,
        settings=context.settings,
        level=LEVEL,
        waivers={gate_id: "the reason this case records"},
    )
    verdict = waived.verdicts[gate_id]
    equals(verdict.status, Status.WAIVED, f"{gate_id} with a waiver")
    check(
        verdict.summary,
        "the waived verdict records no summary, so manifest.json would not say what was "
        "waived or why the gate objected",
    )
    equals(waived.certification.outcome, Outcome.CERTIFIED, "outcome with a waiver")
    return [
        Observation("without", plain.certification.describe()),
        Observation("with", f"{waived.certification.describe()}, {gate_id}={verdict.status}"),
    ]


def tampered(context: Context) -> list[Observation]:
    """A bundle edited after it was judged stops being certified."""
    target = fixtures.fixture("coin-change-sound")
    tasks = fixtures.tasks(context.settings)
    provider = ScriptedProvider(source=target)
    backend = BACKENDS.get(target.backend)

    result = build(
        tasks[target.task_id],
        backend=backend,
        provider=provider,
        settings=context.settings,
        session=ScriptedSession(source=target),
    )
    check(
        result.usable,
        f"the build wrote no solution to judge: {'; '.join(result.formalization.notes)}",
    )
    bundle = result.bundle
    only = ("artifact.integrity",)

    before = adjudicate(
        bundle, backend=backend, settings=context.settings, level=Level.STATIC, only=only
    )
    equals(before.verdicts[only[0]].status, Status.PASS, "integrity before the edit")

    swapped = markers.replace_region(bundle.solution(), backend.comment, "impl", _SWAPPED)
    write_text(bundle.solution_path, swapped)

    after = adjudicate(
        bundle, backend=backend, settings=context.settings, level=Level.STATIC, only=only
    )
    verdict = after.verdicts[only[0]]
    equals(verdict.status, Status.FAIL, "integrity after the edit")
    equals(after.certification.outcome, Outcome.REJECTED, "outcome after the edit")
    return [
        Observation("before", before.verdicts[only[0]].summary),
        Observation("after", verdict.summary),
    ]


def _fixture_cases() -> tuple[Case, ...]:
    """One case per packaged fixture, or one failing case if the corpus is absent.

    The corpus is package data and this list is built when the module is imported, so
    an installation that lost it would otherwise break every command, including the
    `doctor` command whose job is to report what is wrong. A case that fails keeps the
    absence a finding, and keeps a suite from reporting green without having judged
    anything.
    """
    try:
        found = fixtures.fixtures()
    except BenchproofError as exc:
        reason = str(exc)

        def unavailable(_: Context) -> list[Observation]:
            raise Failure(reason)

        return (
            Case(
                id="gates.fixtures",
                summary="the packaged fixture corpus is readable",
                procedure=unavailable,
            ),
        )
    return tuple(
        Case(
            id=f"gates.{target.name}",
            summary=f"{target.name}: {target.summary}",
            procedure=_procedure(target.name),
            requires=fixtures.REQUIRES,
        )
        for target in found
    )


CASES: tuple[Case, ...] = (
    *_fixture_cases(),
    Case(
        id="gates.waiver",
        summary="a waived failure is recorded as waived and certifies the bundle",
        procedure=waiver,
        requires=fixtures.REQUIRES,
    ),
    Case(
        id="gates.tampered",
        summary="a bundle edited after it was judged is no longer certified",
        procedure=tampered,
        requires=fixtures.REQUIRES,
    ),
)
