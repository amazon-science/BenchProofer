# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a smoke case makes of an answer it did not expect.

The suite is how an installation is checked, so a case is only as good as the
distinction it draws between "the tool misbehaved" and "this machine could not tell".
The backends case is where that distinction is sharpest: it has to fail a checker that
accepts a wrong implementation, and it has to *not* fail one that simply ran out of
budget, because a solver that gave up under load is not a checker that certifies
everything.

The stand-in checker is registered under a real backend name, so these run the case the
suite runs, through the same entry point the command line uses.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from benchproofer.backends.base import Backend, CheckResult
from benchproofer.backends.falsifier import FalsifierBackend
from benchproofer.config import Settings
from benchproofer.registries import BACKENDS
from benchproofer.smoke.model import Case, CaseStatus, Context, Observation
from benchproofer.smoke.runner import run_case
from benchproofer.smoke.suites import select

#: The backend whose case is hijacked. Any registered name would do; this one is in
#: the base install, so its requirement is met wherever the tests run.
NAME = "falsifier"

UNDECIDED = CheckResult.unknown("no verdict within 120s", timed_out=True)
ACCEPTED = CheckResult.ok("no counterexample found")


def checker(*, template: CheckResult, mutant: CheckResult) -> type[Backend]:
    """A stand-in checker with the two answers this case can get out of one."""

    class Stub(FalsifierBackend):
        def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
            return template if source == self.template() else mutant

    return Stub


@pytest.fixture
def installed() -> Iterator[Callable[[type[Backend]], None]]:
    """Put a stand-in checker behind the name the case looks up, for one test."""
    try:
        yield lambda backend: BACKENDS.register(NAME, backend)
    finally:
        BACKENDS.unregister(NAME)


@pytest.mark.parametrize(
    ("template", "mutant", "status", "because"),
    [
        (UNDECIDED, UNDECIDED, CaseStatus.SKIPPED, "no verdict on its own template"),
        (ACCEPTED, UNDECIDED, CaseStatus.SKIPPED, "no verdict on any of"),
        (ACCEPTED, ACCEPTED, CaseStatus.FAILED, "rejected none of"),
    ],
    ids=["undecided-template", "undecided-mutants", "accepts-everything"],
)
def test_a_backend_case_separates_a_checker_that_cannot_tell_from_one_that_is_wrong(
    installed: Callable[[type[Backend]], None],
    settings: Settings,
    tmp_path: Path,
    template: CheckResult,
    mutant: CheckResult,
    status: CaseStatus,
    because: str,
) -> None:
    installed(checker(template=template, mutant=mutant))

    result = run_case(select(f"backends.{NAME}")[0], settings=settings, workspace=tmp_path)

    assert result.status is status
    assert because in result.message


def test_a_case_runs_with_no_agent_session_whatever_the_machine_configures(
    settings: Settings, tmp_path: Path
) -> None:
    """A session the machine names reaches a real model, and every case scripts its own.

    Left on, a stage a case gives no session would open that one, so what the case
    observed would depend on that model and on the network, and a hermetic suite would
    spend money to run.
    """
    seen: list[str] = []

    def procedure(context: Context) -> Iterator[Observation]:
        seen.append(context.settings.session)
        return iter(())

    result = run_case(
        Case(
            id="registry.session",
            summary="what session a case is given",
            procedure=procedure,
        ),
        settings=settings.model_copy(update={"session": "claude-code"}),
        workspace=tmp_path,
    )

    assert result.status is CaseStatus.PASSED, result.message
    assert seen == [""]
