# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The solution drafted by an agent session, in a workspace laid out for it.

The session is a double that writes the solution file it is pointed at and reports. What
is pinned is what does not depend on the model: what the workspace holds when the session
starts, what its request says and allows, what of its work is read back and where it goes,
and what happens in a run with no session.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest
from test_agentic import guarded
from test_session import REPORT, SOLUTION, Drafting, Scripted, drafter, script

from benchproofer.backends.base import CheckStatus
from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.task import SourceFile, Task
from benchproofer.errors import ProviderError
from benchproofer.formalize.session import Formalization
from benchproofer.gates.audit import INPUTS
from benchproofer.llm.agentic import EDIT, AgentSession, SessionSpec, StepOutcome
from benchproofer.llm.claude_code import confined
from doubles import Accepting, Refusing

#: The module, which `benchproofer.pipeline` shadows with its `build` function.
building = importlib.import_module("benchproofer.pipeline.build")

#: A test patch adding the test the fix is judged by, as a benchmark ships one.
TEST_PATCH = (
    "diff --git a/tests/test_change.py b/tests/test_change.py\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    "+++ b/tests/test_change.py\n"
    "@@ -0,0 +1,5 @@\n"
    "+from change import make_change\n"
    "+\n"
    "+\n"
    "+def test_forty_cents_takes_a_nickel():\n"
    "+    assert make_change(40) == (1, 1, 1, 0)\n"
)


def with_tests(task: Task) -> Task:
    """``task`` with a test patch, as a benchmark that adds its failing test ships it."""
    return task.model_copy(update={"metadata": {**task.metadata, "test_patch": TEST_PATCH}})


def draft(
    task: Task,
    settings: Settings,
    session: AgentSession | None,
    *,
    backend: Any = None,
    provider: Scripted | None = None,
) -> Formalization:
    """Formalize ``task`` with ``session`` drafting the solution and the rest scripted."""
    asked = provider or Scripted(script())
    return drafter(asked, settings, backend or Accepting(), session=session).run(task)


def test_the_drafting_session_works_in_a_workspace_laid_out_as_a_repair_s(
    coin_change: Task, settings: Settings
) -> None:
    """The bundle, the task, the repository with the tests as the benchmark runs them.

    The solution file starts as the backend's template, so the session has the shape before
    it; the test patch is applied to its copy of the repository, so a test the benchmark adds
    reads there whole; the golden patch is beside it, unapplied, with the files it touches
    as they read after it; and `./tools` and `scratch/` are where a repair's are.
    """
    session = Drafting()

    draft(with_tests(coin_change), settings, session)

    seen = session.seen
    (solution,) = [name for name in seen if name.endswith("/accepting/solution.py")]
    assert seen[solution] == Accepting().template()
    bundle = solution.rsplit("/", 2)[0]
    assert "make_change" in seen[f"{bundle}/task.json"]
    assert "nickels = remainder // 5" in seen[f"{bundle}/reference.patch"]
    assert "pennies = remainder - dimes * 10" in seen["repository/change.py"]
    assert "assert make_change(40) == (1, 1, 1, 0)" in seen["repository/tests/test_change.py"]
    assert seen["tests.patch"].startswith("diff --git a/tests/test_change.py")
    assert "nickels = remainder // 5" in seen["fixed/change.py"]
    assert "benchproofer.audit.tools" in seen["tools"]
    assert (session.asked[0].cwd / "scratch").is_dir()


def test_an_oracle_s_test_files_are_written_into_the_repository_whole(
    coin_change: Task, settings: Settings
) -> None:
    """As the pytest oracle stages them, with no diff to apply and none said not to apply."""
    test = "from change import make_change\n\n\ndef test_forty():\n    assert make_change(40)\n"
    shipped = (
        SourceFile(path="conftest.py", content="import pytest\n"),
        SourceFile(path="tests/test_change.py", content=test),
    )
    task = coin_change.model_copy(
        update={"oracle": coin_change.oracle.model_copy(update={"files": shipped})}
    )
    session = Drafting()

    result = draft(task, settings, session)

    assert session.seen["repository/tests/test_change.py"] == test
    assert session.seen["repository/conftest.py"] == "import pytest\n"
    assert "tests.patch" not in session.seen
    assert "written into it whole" in session.asked[0].prompt
    assert "does not apply" not in session.asked[0].prompt
    assert not any("does not apply" in note for note in result.notes)


def test_a_test_patch_that_does_not_apply_is_noted_and_pointed_at(
    coin_change: Task, settings: Settings
) -> None:
    """The session is told to read the tests in `tests.patch`, and the notes say why."""
    stale = (
        "diff --git a/tests/test_missing.py b/tests/test_missing.py\n"
        "--- a/tests/test_missing.py\n"
        "+++ b/tests/test_missing.py\n"
        "@@ -1,1 +1,2 @@\n"
        " from change import make_change\n"
        "+assert make_change(40) == (1, 1, 1, 0)\n"
    )
    task = coin_change.model_copy(
        update={"metadata": {**coin_change.metadata, "test_patch": stale}}
    )
    session = Drafting()

    result = draft(task, settings, session)

    assert "repository/tests/test_missing.py" not in session.seen
    assert session.seen["tests.patch"] == stale
    assert (
        "`tests.patch`, beside `repository/`, does not apply to it" in session.asked[0].prompt
    )
    assert any("the test patch does not apply to the repository" in n for n in result.notes)


def test_the_drafting_request_carries_the_rules_and_what_to_read_first(
    coin_change: Task, settings: Settings
) -> None:
    """The system prompt every drafter gets, and the sites rules, in the request itself.

    A file a session is asked to read it may skip, so the rules are inline; what it is asked
    to read is the material, which need not fit in the request: the tests are named,
    not pasted, and so are the functions the fix edits.
    """
    session = Drafting()
    formalizer = drafter(Scripted(script()), settings, Accepting(), session=session)

    formalizer.run(with_tests(coin_change))

    (request,) = session.asked
    assert request.system == formalizer._system()
    assert "## Callees the fix does not change" in request.system
    assert "costs a request" not in request.system and "asked next" not in request.system
    prompt = request.prompt
    for rule in (
        "Model the fix, not a re-imagining of it.",
        "Read the changed functions AND their callees",
        "**No leakage.**",
        "## The tests the benchmark judges the fix by",
        "the PASS_TO_PASS tests that call a function the fix changes",
        "Do not read, search for, copy, or consult any pre-existing formalization",
        "a principled BLOCKED beats a faked specification",
    ):
        assert rule in prompt, rule
    assert "* in `change.py`: `make_change`" in prompt
    assert "(`oracle.tests`)" in prompt and "(`oracle.regression`)" in prompt
    assert "`./tools verify bundles/" in prompt
    assert "is applied, so each test reads as the benchmark runs it" in prompt
    # The material is on disk, so none of it is pasted in.
    assert "### The diff the benchmark applies to its tests" not in prompt
    assert "## The functions the fix edits, as they read after it" not in prompt
    assert "Reply with one fenced code block" not in prompt
    assert f"{settings.draft_timeout_s / 60:.0f} minutes" in prompt
    assert (request.max_turns, request.timeout_s) == (200, 3600.0)
    assert (settings.draft_turns, settings.draft_timeout_s) == (200, 3600.0)
    assert request.submit == "draft" and set(request.required) == {"status", "summary"}
    assert request.fields["status"]["enum"] == ["VERIFIED", "BLOCKED"]  # type: ignore[index]
    assert request.tools == EDIT and request.report
    told = " ".join(prompt.split())
    assert "FILE is sent alone" in told and "`./tools try FILE --as attack`" in told
    assert "The checker enforces a timeout" not in told
    # The read guard refuses a search from `/`, so the prompt does not ask for one.
    assert "search from `/`" not in told


def test_the_drafting_session_may_write_only_its_solution_file_and_its_scratch(
    coin_change: Task, settings: Settings
) -> None:
    """All else it could write is the task, the repository or the bundle's manifest.json."""
    session = Drafting()
    draft(coin_change, settings, session)

    (request,) = session.asked
    (solution,) = request.writable
    scratch = request.cwd / "scratch"
    assert solution.name == "solution.py"
    hook = confined(request)

    def decided(path: Path) -> str:
        return guarded(hook, "Write", file_path=str(path))

    assert decided(solution) == ""
    assert decided(scratch / "mapping.md") == ""
    assert decided(solution.parent / "manifest.json") == "deny"
    assert decided(solution.parent / "conformance.py") == "deny"
    assert decided(request.cwd / "repository" / "change.py") == "deny"


def test_the_session_s_file_is_carried_where_a_drafted_reply_s_is(
    coin_change: Task, settings: Settings
) -> None:
    """Only the solution comes from the session; every later artifact is drafted by request."""
    provider = Scripted(script())

    result = draft(coin_change, settings, Drafting(), provider=provider)

    assert result.solution == SOLUTION and result.accepted and result.rounds == 1
    assert "solution" not in provider.asked
    assert {"twin", "rival", "correspondence", "conformance"} <= set(provider.asked)
    assert result.twins and result.rivals and result.correspondence and result.conformance
    assert any(
        "a drafting session (41 turn(s), 77 tool use(s), 612s) reported VERIFIED" in note
        for note in result.notes
    )


@pytest.mark.parametrize(
    ("left", "why"),
    [
        (None, "wrote no solution file"),
        ("def impl(cents):\n    return (0, 0, 0, cents)\n", "cannot be read"),
    ],
    ids=["template", "no-regions"],
)
def test_a_session_that_leaves_no_readable_file_leaves_nothing_to_draft_against(
    coin_change: Task, settings: Settings, left: str | None, why: str
) -> None:
    """As a reply with no readable file does: the bundle gets the notes and nothing else."""
    provider = Scripted(script())
    blocked = {"status": "BLOCKED", "summary": "x", "blocked": "the callee is a C extension"}

    result = draft(coin_change, settings, Drafting(left, blocked), provider=provider)

    assert result.solution == "" and result.rounds == 0
    assert result.check.status == CheckStatus.UNKNOWN and why in result.check.detail
    assert provider.asked == []
    assert any("the callee is a C extension" in note for note in result.notes)
    assert result.session["status"] == "BLOCKED"


def test_a_refused_session_file_ends_drafting(coin_change: Task, settings: Settings) -> None:
    """As a refused reply does: nothing else is drafted against it, and repair takes it up.

    The drafting session read the callees and the checker's output already, so no further
    session is asked about the file.
    """
    session = Drafting()

    result = draft(coin_change, settings, session, backend=Refusing())

    assert [request.submit for request in session.asked] == ["draft"]
    assert result.solution == SOLUTION and not result.accepted
    assert any("so no further artifact was drafted" in note for note in result.notes)


def test_a_drafting_session_that_cannot_start_ends_the_task(
    coin_change: Task, settings: Settings
) -> None:
    """An expired credential is the environment failing, as a provider that cannot answer."""

    class Unstartable(Drafting):
        def run(self, request: SessionSpec) -> StepOutcome:
            raise ProviderError("the credential expired")

    with pytest.raises(ProviderError):
        draft(coin_change, settings, Unstartable())


def test_a_session_that_fails_after_writing_its_file_has_drafted_it(
    coin_change: Task, settings: Settings
) -> None:
    """What it left in the file is taken whatever it reports, as its prompt tells it."""

    class Failing(Drafting):
        def run(self, request: SessionSpec) -> StepOutcome:
            super().run(request)
            raise ProviderError("the tool exited 1")

    result = draft(coin_change, settings, Failing())

    assert result.solution == SOLUTION and result.accepted and result.twins
    assert result.session == {
        "by": "session",
        "model": "a-model",
        "detail": "the tool exited 1",
    }
    assert any("failed part-way: the tool exited 1" in note for note in result.notes)


def test_a_run_with_no_session_drafts_nothing_and_says_what_to_install(
    coin_change: Task, settings: Settings
) -> None:
    """The build stops before it makes a bundle, on the environment rather than the task."""
    provider = Scripted(script())

    with pytest.raises(ProviderError, match=r"install `benchproofer\[agent\]`"):
        building.build(coin_change, backend=Accepting(), provider=provider, settings=settings)
    with pytest.raises(ProviderError, match="drafting the solution needs an agent session"):
        draft(coin_change, settings, None, provider=provider)

    assert provider.asked == []
    assert not Bundle.locate(settings.bundle_root, coin_change, Accepting().name).exists


def test_a_build_records_the_drafting_session_as_a_repair_s_is_recorded(
    coin_change: Task, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Its report, what it spent and what it looked at, under the drafting record."""
    session = Drafting()
    monkeypatch.setattr(building, "require_session", lambda *_: session)
    monkeypatch.setattr(building.ORACLES, "get", lambda _: None)

    built = building.build(
        coin_change, backend=Accepting(), provider=Scripted(script()), settings=settings
    )

    recorded = built.bundle.manifest().provenance["formalization"]
    assert recorded["session"] == {
        "by": "session",
        "model": "a-model",
        **REPORT,
        "turns": 41,
        "tool_uses": 77,
        "duration_s": 612.0,
        "detail": "",
        "actions": ["Read repository/change.py", "Bash ./tools verify"],
    }
    assert "solution" not in [request["stage"] for request in recorded["requests"]]
    assert "a drafting session" in built.bundle.notes_path.read_text()


def test_correspondence_md_starts_from_what_the_drafter_reported_leaving_out(
    coin_change: Task, settings: Settings
) -> None:
    """The drafter is asked for both sections, and the request that writes them is shown them.

    Only the drafter knows what it left out and why, so `Not modeled` and `Outside the
    bridge` are drafted from its report rather than written again from the patch.
    """
    left_out = "* `change.py`'s module docstring: documentation, with no behavior to specify"
    outside = "* a negative amount: the third kind, `make_change` raises at change.py:9"
    session = Drafting(payload={**REPORT, "not_modeled": left_out, "outside": outside})
    provider = Scripted(script())

    draft(coin_change, settings, session, provider=provider)

    request = session.asked[0]
    assert {"not_modeled", "outside"} <= set(request.fields)
    assert "starts its `Not modeled` and `Outside the bridge`" in " ".join(
        request.prompt.split()
    )
    asked = provider.sent[provider.asked.index("correspondence")][0].content
    assert "## What the drafter reported leaving out" in asked
    assert f"### Not modeled\n\n{left_out}" in asked
    assert f"### Outside the bridge\n\n{outside}" in asked
    # A drafter that reports neither adds no section.
    quiet = Scripted(script())
    draft(coin_change, settings, Drafting(), provider=quiet)
    assert (
        "What the drafter reported"
        not in quiet.sent[quiet.asked.index("correspondence")][0].content
    )


def test_drafting_is_not_offered_a_callee_s_result_as_an_input(
    coin_change: Task, settings: Settings
) -> None:
    """Drafting states every unchanged callee by a definition or an axiom, never as a parameter.

    Only a repair is offered the result of a callee as an input, for a callee this run's rounds
    list (`rounds.eligible`), so neither the drafting session nor the request writing
    `correspondence.md` is told of it, and the report has no field for one.
    """
    session = Drafting(payload=REPORT)
    provider = Scripted(script())

    draft(coin_change, settings, session, provider=provider)

    request = session.asked[0]
    index = provider.asked.index("correspondence")
    correspondence = provider.sent[index][0].content
    assert "inputs" not in request.fields
    for text in (request.prompt, request.system, correspondence, provider.systems[index]):
        flat = " ".join(text.split())
        assert INPUTS not in flat
        assert "as an input" not in flat and "input of the model" not in flat
    assert "It has four sections" in correspondence


def test_fields_a_report_wrote_inside_another_field_are_read_out_of_it(
    coin_change: Task, settings: Settings
) -> None:
    """A submit call that lost its structure leaves `<name>` sections in an earlier field."""
    packed = {
        "status": "VERIFIED",
        "summary": (
            'Models make_change.</summary>\n<callees">none</callees>\n'
            '<modeled">["change.make_change"]</modeled>\n<outside">Nothing.</outside>'
        ),
    }

    result = draft(coin_change, settings, Drafting(payload=packed))

    assert result.session["summary"] == "Models make_change."
    assert result.session["callees"] == "none"
    assert result.session["modeled"] == ["change.make_change"]
    assert result.session["outside"] == "Nothing."
    assert [note for note in result.notes if "inside another field" in note]
    # A report whose fields arrived as fields is taken as it is.
    plain = draft(coin_change, settings, Drafting())
    assert plain.session["summary"] == REPORT["summary"]
    assert not [note for note in plain.notes if "inside another field" in note]
