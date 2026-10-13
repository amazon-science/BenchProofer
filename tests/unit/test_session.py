# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The formalization session, driven by a scripted model.

A session is where a bundle's artifacts come from, so what is worth pinning is what each
stage is shown, what it keeps for the gate to judge whatever the checker said, and what it
sends back: a `conformance.py` whose run establishes nothing, once.

The checker and the model are both local: a backend that accepts every file, a provider
that replies from a fixed script, and a drafting session that writes the solution file
without reaching a model. Nothing here needs a verifier or a key.
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

import doubles
from benchproofer.audit.session import admitted
from benchproofer.backends.base import Backend, BackendKind, CheckResult
from benchproofer.config import Settings
from benchproofer.core import differential
from benchproofer.core.markers import parse, wrap
from benchproofer.core.prompts import SHARED
from benchproofer.core.runnable import quotes_lines
from benchproofer.core.session import Journal
from benchproofer.core.sites import RECORD
from benchproofer.core.task import Reference, SourceFile, Task
from benchproofer.errors import ProviderError
from benchproofer.formalize import prompts
from benchproofer.formalize.session import Draft, Formalization, Formalizer
from benchproofer.gates.audit import OUTSIDE, entries_under
from benchproofer.llm.agentic import AgentSession, SessionSpec, StepOutcome
from benchproofer.llm.base import Completion, Message
from benchproofer.oracles.base import Oracle, OracleResult, Program
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import read_text, write_text
from doubles import Accepting, revised

#: The module, which `benchproofer.pipeline` shadows with its `build` function.
building = importlib.import_module("benchproofer.pipeline.build")


SOLUTION = """\
# benchproofer:begin impl
def impl(cents):
    quarters = cents // 25
    return (quarters, 0, 0, cents - quarters * 25)
# benchproofer:end impl


# benchproofer:begin spec
def property_change_sums_to_the_amount(cents):
    quarters, dimes, nickels, pennies = impl(cents)
    assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents
# benchproofer:end spec
"""
#: What `SOLUTION` obliges, as the tool reads it: the property and its assertion.
PROPERTY = "- `def property_change_sums_to_the_amount(cents):` -> `make_change`, `change.py`\n"
ASSERTION = (
    "- `assert quarters * 25 + dimes * 10 + nickels * 5 + pennies == cents`"
    " -> `make_change`, `cents`\n"
)
#: The same solution, whose specification assumes a callee it did not model. The
#: session has to draft an `axioms.py` for it, and the gate fails the bundle without one.
ASSUMING = (
    "# benchproofer:begin axioms\n"
    "# benchproofer:axiom os.cpu_count\n"
    "def cpu_count():\n"
    "    return 8\n"
    "# benchproofer:end axioms\n\n\n" + SOLUTION
)
HARNESS = (
    "```python\n"
    "# benchproofer:axiom os.cpu_count\n"
    "def cpu_count():\n"
    "    return 8\n\n\n"
    "import os\n\n"
    "assert cpu_count() == os.cpu_count()\n"
    'print("benchproofer:grounded os.cpu_count 1 input")\n'
    "```"
)
BODY = "```python\ndef impl(cents):\n    return (0, 0, 0, cents)\n```"
OTHER_BODY = "```python\ndef impl(cents):\n    return (cents, 0, 0, 0)\n```"
#: The `impl` region copied line for line, under the name the task's tests use.
SHADOW = (
    "```python\n# benchproofer:target change.py\n"
    "def impl(cents):\n"
    "    quarters = cents // 25\n"
    "    return (quarters, 0, 0, cents - quarters * 25)\n\n\n"
    "def make_change(cents):\n"
    "    return impl(cents)\n```"
)
#: `conformance.py`: the implementation's runnable form inside the sentinels
#: that mark it, then a comparison against the real function, then the protocol line
#: saying what it covered. The region is what lets a reviewer's submission be put
#: through the same comparison later.
DIFFERENTIAL = (
    "```python\n"
    "import change\n\n\n"
    "def shadow(cents):\n"
    "    # benchproofer:begin impl\n"
    "    quarters = cents // 25\n"
    "    return (quarters, 0, 0, cents - quarters * 25)\n"
    "    # benchproofer:end impl\n\n\n"
    "for cents in range(100):\n"
    "    assert change.make_change(cents) == shadow(cents)\n"
    'print("benchproofer:compared change.make_change 100 every amount under 100")\n'
    "```"
)
#: A phrase of each prompt template, most specific first. A template reworded without
#: updating this list makes `_stage` fail by name rather than take a wrong branch.
STAGES = (
    ("That reply could not be used", "retry"),
    ("Benchproofer read that program back", "conformance-repair"),
    ("Benchproofer ran that program", "conformance-run"),
    ("Write the pre-fix", "twin"),
    ("rival.", "rival"),
    ("Write `correspondence.md`", "correspondence"),
    ("tries to refute that claim", "conformance"),
    ("Write `axioms.py`.", "axioms"),
)


class Scripted(doubles.Scripted):
    """The scripted model, keyed by the formalization prompts."""

    stages = STAGES


class Restricted(Accepting):
    """A checker whose hygiene gate will police what the file imports."""

    name = "restricted"
    allowed_imports = ("hypothesis", "math")


class Failing(Scripted):
    """The scripted model, except that one stage's request never arrives."""

    def __init__(self, script: Mapping[str, Sequence[str | Completion]], *, on: str) -> None:
        super().__init__(script)
        self.on = on

    def complete(
        self,
        messages: list[Message],
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> Completion:
        if self.stage(messages[-1].content) == self.on:
            raise ProviderError("the endpoint refused the request")
        return super().complete(
            messages, system=system, max_tokens=max_tokens, temperature=temperature
        )


def script(**overrides: Sequence[str | Completion]) -> dict[str, Sequence[str | Completion]]:
    """A script every stage of which produces a usable artifact."""
    replies: dict[str, Sequence[str | Completion]] = {
        "twin": [f"RATIONALE: it never hands out a nickel.\n\n{BODY}"],
        "rival": [f"RATIONALE: an attack.\n\n{BODY}", f"RATIONALE: another.\n\n{OTHER_BODY}"],
        "correspondence": [PROPERTY + ASSERTION],
        "conformance": [f"Compared.\n\n{DIFFERENTIAL}"],
        "conformance-repair": [f"Compared.\n\n{DIFFERENTIAL}"],
        "conformance-run": [f"Compared.\n\n{DIFFERENTIAL}"],
        "axioms": [f"Here it is.\n\n{HARNESS}"],
    }
    replies.update(overrides)
    return replies


REPORT: dict[str, object] = {
    "status": "VERIFIED",
    "summary": "Models make_change over integer cents; the coins sum to the amount.",
    "modeled": ["change.make_change"],
    "callees": "none: the changed code calls nothing it does not define",
    "checker": "status: accepted",
}


class Drafting(AgentSession):
    """A drafting session that writes the solution file in its workspace, then reports.

    What it saw is kept, since what a drafter is shown is the point of the cases about it:
    the request, and every file of the workspace as it was laid out when the session ran.
    Asked for anything but a draft, it submits nothing.
    """

    name = "drafting"

    def __init__(
        self, solution: str | None = SOLUTION, payload: dict[str, object] | None = None
    ) -> None:
        super().__init__(model="a-model")
        self.solution = solution
        self.payload = REPORT if payload is None else payload
        self.asked: list[SessionSpec] = []
        self.seen: dict[str, str] = {}

    def run(self, request: SessionSpec) -> StepOutcome:
        self.asked.append(request)
        if request.submit != "draft":
            return StepOutcome(text="")
        self.seen = {
            path.relative_to(request.cwd).as_posix(): read_text(path)
            for path in sorted(request.cwd.rglob("*"))
            if path.is_file()
        }
        if self.solution is not None:
            write_text(next(request.cwd.glob("bundles/**/solution.py")), self.solution)
        return StepOutcome(
            text="done",
            payload=self.payload or None,
            duration_s=612.0,
            turns=41,
            tool_uses=77,
            actions=("Read repository/change.py", "Bash ./tools verify"),
        )


def drafter(
    provider: Scripted,
    settings: Settings,
    backend: Backend | None = None,
    *,
    session: AgentSession | None = None,
    oracle: Oracle | None = None,
) -> Formalizer:
    """A formalizer over a local checker and a scripted model."""
    return Formalizer(
        provider=provider,
        backend=backend or Accepting(),
        settings=settings,
        workdir=settings.cache_dir / "work",
        session=session,
        oracle=oracle,
    )


def formalize(
    task: Task,
    settings: Settings,
    provider: Scripted,
    *,
    backend: Backend | None = None,
    session: AgentSession | None = None,
    oracle: Oracle | None = None,
    solution: str = SOLUTION,
) -> Formalization:
    """Run one session against a local checker and a scripted model.

    The solution is ``session``'s, by default a drafting session that writes ``solution``.
    """
    drafting = session if session is not None else Drafting(solution)
    return drafter(provider, settings, backend, session=drafting, oracle=oracle).run(task)


def asked(provider: Scripted) -> str:
    """Everything the session put to the model, as one document."""
    return "\n".join(message.content for turn in provider.sent for message in turn)


def test_a_build_records_what_the_drafted_bundle_admits(
    coin_change: Task, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The equivalence auditor is shown each later repair's changes against it."""
    monkeypatch.setattr(building.ORACLES, "get", lambda _: None)

    built = building.build(
        coin_change,
        backend=Accepting(),
        provider=Scripted(script()),
        settings=settings,
        session=Drafting(),
    )

    drafted = built.bundle.manifest().provenance["drafted"]
    assert drafted == admitted(built.bundle, Accepting())
    assert "property_change" in drafted["spec"]
    # And what the golden patch edits, read from the working copy drafting laid out.
    assert built.bundle.manifest().provenance[RECORD] == {
        "golden_patch": {"change.py": [["def make_change"]]},
        "test_patch": {},
        "test_cases": {},
    }


#: What an obligation has to be about, which every prompt that states it includes.
FRAME = " ".join(SHARED.rules("frame").split())


def test_a_request_with_no_sites_section_is_told_the_obligation_rule_with_the_tests(
    coin_change: Task, settings: Settings
) -> None:
    """A fix that names no function has no sites section, so the tests section says it."""
    task = coin_change.model_copy(
        update={"reference": Reference(files=coin_change.reference.files)}
    )
    session = Drafting()

    formalize(task, settings, Scripted(script()), session=session)

    opening = " ".join(session.asked[0].prompt.split())
    assert "## The code this is about" not in opening
    assert opening.count(FRAME) == 1


def test_conformance_is_drafted_with_what_the_refinement_map_sets_outside_the_bridge(
    coin_change: Task, settings: Settings
) -> None:
    """It does not compare on the inputs the fixed function answers before the fix's lines."""
    entry = "* a negative amount: `make_change` raises before the changed lines (change.py:9)"
    listed = f"{PROPERTY}{ASSERTION}\n## Outside the bridge\n\n{entry}\n"
    provider = Scripted(script(correspondence=[listed]))

    formalize(coin_change, settings, provider)

    drafting = provider.sent[provider.asked.index("conformance")][0].content
    assert entry in drafting
    # Its rules say how to declare such an input instead of comparing it, quoting the entry.
    told = " ".join(drafting.split())
    assert "prints its `excluded` or `inadmissible` line with `Outside the bridge:`" in told
    assert "quote at least five words of the entry exactly" in told
    # A `correspondence.md` that sets nothing outside the bridge adds nothing to the request.
    plain = Scripted(script())
    formalize(coin_change, settings, plain)
    listing = "lists under `Outside the bridge`"
    assert listing not in plain.sent[plain.asked.index("conformance")][0].content


def test_the_refinement_map_costs_one_request(coin_change: Task, settings: Settings) -> None:
    """Nothing reads it mechanically, so nothing sends it back: the review checks it.

    It declares the inputs its bridge carries nothing for, which is what the equivalence
    auditor may set a difference aside on, and nothing else.
    """
    provider = Scripted(script())

    result = formalize(coin_change, settings, provider)

    assert provider.turns("correspondence") == 1
    assert result.correspondence == PROPERTY + ASSERTION
    assert not [note for note in result.notes if "correspondence" in note]
    request = provider.sent[provider.asked.index("correspondence")][0].content
    assert "## Outside the bridge" in request
    assert "Reply with the four sections" in request
    assert "`unbridged`" in request


def test_a_uniqueness_case_is_shown_the_pre_fix_implementation_and_the_cases_before_it(
    coin_change: Task, settings: Settings
) -> None:
    """A rival repeating the mistake of the pre-fix implementation tests nothing new.

    Whether two cases are the same case is `spec.strength.battery`'s to decide, over every
    case and by behavior as well as by text; drafting's part is to show the drafter what it
    may not repeat. So a repeat is kept here and the gate refuses it, rather than being
    dropped on its text, which an added assertion defeats.
    """
    provider = Scripted(script(rival=[f"RATIONALE: the same attack again.\n\n{BODY}"]))

    result = formalize(coin_change, settings, provider)

    assert [rival.id for rival in result.rivals] == [
        "uniqueness-1",
        "uniqueness-2",
        "soundness-1",
    ]
    assert "the one the fix replaced" in asked(provider)
    assert "already written the case(s) below" in asked(provider)


def test_a_reply_benchproofer_cannot_read_is_answered_with_a_retry(
    coin_change: Task, settings: Settings
) -> None:
    """A reply with nothing usable is asked for again, once."""
    unusable = "I would rather talk about something else."
    provider = Scripted(script(conformance=[unusable], retry=script()["conformance"]))

    result = formalize(coin_change, settings, provider)

    assert provider.turns("retry") == 1
    assert result.conformance
    assert any("the reply contains no fenced code block" in note for note in result.notes)
    # A reply that finished and could not be read is a shape problem, not a length one.
    assert "a shorter reply" not in asked(provider)


def test_a_reply_that_ran_out_of_room_says_so_instead_of_being_quoted_back_empty(
    coin_change: Task, settings: Settings
) -> None:
    """A model that reasons before it answers can stop before writing anything.

    Then the reply shows nothing about what went wrong, so the note names where it
    stopped, and the turn the tool would otherwise quote back is one an endpoint is
    entitled to refuse.
    """
    cut_off = Completion(text="", model="script", stop_reason="max_tokens")
    provider = Scripted(script(correspondence=[cut_off], retry=script()["correspondence"]))

    result = formalize(coin_change, settings, provider)

    assert result.correspondence
    assert any(f"{settings.max_output_tokens}-token limit" in note for note in result.notes)
    assert all(message.content.strip() for turn in provider.sent for message in turn)
    # And the round is answered by asking for less: a second one spent the same way
    # would end the same way.
    assert "a shorter reply" in asked(provider)


def test_a_response_the_provider_stopped_itself_is_not_reported_as_a_bad_reply(
    coin_change: Task, settings: Settings
) -> None:
    """A refusal is the run's shortfall, not the model's, so the note says which it is.

    Recording it as a malformed reply would read as a model that answered badly, and a
    reader deciding whether to trust the artifacts needs to know that no answer came.
    """
    declined = Completion(text="", model="script", stop_reason="refusal")
    provider = Scripted(script(correspondence=[declined], retry=script()["correspondence"]))

    result = formalize(coin_change, settings, provider)

    assert result.correspondence
    assert any("the provider stopped the response (refusal)" in note for note in result.notes)


def test_a_stage_the_provider_never_answered_costs_that_artifact_and_no_more(
    coin_change: Task, settings: Settings
) -> None:
    """An endpoint that fails part way through a session loses one artifact, not the run.

    What was drafted before the failure is still worth judging, and the gate that reads
    the missing file will report it missing, so the session records why it stopped asking
    instead of raising and taking the accepted specification down with it.
    """
    provider = Failing(script(), on="conformance")

    result = formalize(coin_change, settings, provider)

    assert result.accepted and not result.conformance
    assert result.twins and result.rivals and result.correspondence
    assert any("the provider failed" in note for note in result.notes)


def test_a_request_carries_the_response_budget_the_settings_name(
    coin_change: Task, settings: Settings
) -> None:
    """One setting decides it, so a model that needs more room is configured, not patched."""
    provider = Scripted(script())

    formalize(coin_change, settings.model_copy(update={"max_output_tokens": 4321}), provider)

    assert set(provider.budgets) == {4321}


def test_the_drafter_is_shown_the_tests_the_benchmark_judges_the_fix_by(
    coin_change: Task, settings: Settings
) -> None:
    """Shown the fix alone, a drafter cannot tell which function the tests read.

    So the request names both test lists, with the rule that says what the model's
    parameters and result may be, and `conformance.py` is drafted with the diff the
    benchmark applies to its tests.
    """
    task = coin_change.model_copy(
        update={
            "reference": Reference(patch=coin_change.reference.patch, symbols=("make_change",)),
            "oracle": coin_change.oracle.model_copy(
                update={
                    "files": (
                        SourceFile(path="tests.patch", content="+assert make_change(7) == 1\n"),
                    ),
                    "regression": ("tests.test_change.test_zero",),
                }
            ),
        }
    )
    provider = Scripted(script())
    session = Drafting()

    formalize(task, settings, provider, session=session)

    opening = session.asked[0].prompt
    assert "## The tests the benchmark judges the fix by" in opening
    assert "`tests.test_change.test_zero`" in opening
    assert "A value the fix itself computes is never a parameter" in opening
    assert "is a constant of the model, not a\n  parameter" in opening
    # An obligation on what the changed function does, which unchanged code turns into the
    # value a test checks, states the behaviour only with a frame: said once.
    assert " ".join(opening.split()).count(FRAME) == 1
    # And a repair reads the same block, which the session already passes it: the interface
    # a fix has to be modeled at is read off the tests, drafting or correcting.
    assert "$tests" in prompts.template("repair-agent")
    # And `conformance.py` is drafted with them, to compare the inputs they build first.
    harness = provider.sent[provider.asked.index("conformance")][0].content
    assert "+assert make_change(7) == 1" in harness
    assert (
        "Compare first every input the FAIL_TO_PASS tests and the PASS_TO_PASS\n"
        "tests the test patch adds or edits hand these functions"
    ) in harness
    assert "such as a request context or a\nsite object a running server sets" in harness


def test_the_drafter_is_told_the_model_admits_what_the_tests_hand_a_changed_function(
    coin_change: Task, settings: Settings
) -> None:
    """The input cases the golden patch distinguishes, over every input the tests hand it.

    A PASS_TO_PASS test's inputs included: a model that leaves one out says nothing of what
    that test checks, and no attack can reach it. Only the three kinds of `Outside the
    bridge` entry leave one out.
    """
    session = Drafting()

    formalize(coin_change, settings, Scripted(script()), session=session)

    opening = " ".join(session.asked[0].prompt.split())
    assert (
        "The input cases the golden patch distinguishes are the input cases the model "
        "distinguishes, and each input case's modeled result corresponds to what the golden "
        "patch computes."
    ) in opening
    # The domain rule is the system prompt's, and the three kinds of entry the sites'.
    system = " ".join(session.asked[0].system.split())
    assert " ".join(SHARED.rules("domain").split()) in system
    assert " ".join(SHARED.rules("outside").split()) in opening
    assert "it may be left out of the obligations" in opening


def test_an_unchanged_branch_past_a_condition_the_fix_adds_is_left_out_as_the_third_kind(
    coin_change: Task, settings: Settings
) -> None:
    """Not by an axiom: code inside a changed function is not a callee.

    The third kind of `Outside the bridge` entry covers an input on which the fixed function
    runs only what the golden patch leaves as it was, a false test of an added condition
    aside, and its check traces the input before the fix and after it. A behavior a FAIL_TO_PASS
    test or a PASS_TO_PASS test the test patch adds or edits checks is never left out so, and
    `conformance.py` skips those inputs in the same words.
    """
    session = Drafting()

    formalize(coin_change, settings, Scripted(script()), session=session)

    opening = " ".join(session.asked[0].prompt.split())
    system = " ".join(session.asked[0].system.split())
    assert (
        "it tests a condition the golden patch adds, finds it false, and goes on into a branch "
        "the patch leaves as it was"
    ) in opening
    assert (
        "A behavior checked by a FAIL_TO_PASS test, or by a PASS_TO_PASS test the test patch "
        "adds or edits, is never left out this way."
    ) in opening
    assert (
        "trace one input the entry names through the function before the fix and after it, "
        "and see the same lines run, apart from the false test of a condition the golden "
        "patch adds"
    ) in opening
    assert "by an `Outside the bridge` entry of the third kind, and only so" in opening
    assert "Code inside a changed function is not a callee either" in system
    assert "no axiom represents it" in system
    assert "of the third kind names, on which the fixed function runs only what" in " ".join(
        differential.protocol_for(100).split()
    )


def test_the_system_prompt_states_the_rule_for_callees_the_fix_does_not_change(
    coin_change: Task, settings: Settings
) -> None:
    """Modeled, or an axiom as weak as the golden patch's own calls allow, never a parameter.

    The requests for the pre-fix implementation and the property-based test suite's rivals,
    which write the solution file's regions, and the repair are sent this system prompt. Only a
    repair's brief may relax it, for the callees this run's rounds list (`rounds.eligible`).
    """
    provider = Scripted(script())

    formalize(coin_change, settings, provider)

    system = " ".join(provider.systems[0].split())
    assert "making its result a parameter" not in system
    assert " ".join(SHARED.rules("callee").split()) in system
    # How to mark each on a line of its own.
    for line in ("models <callee>\n", "axiom <callee>\n"):
        assert f"    # benchproofer:{line}" in provider.systems[0]
    for text in (system, BACKENDS.get("nagini").guidance()):
        assert not re.search(r"weakest \w+ (that is enough for )?the (proof|obligations)", text)


def test_a_session_is_told_which_imports_the_hygiene_gate_allows(
    coin_change: Task, settings: Settings
) -> None:
    """A rule enforced mechanically and never stated costs a round and gains nothing.

    A session copying a golden patch that reaches for the clock or a source of randomness
    writes the import the golden patch had, so the list is named along with the way out.
    """
    provider = Scripted(script())

    formalize(coin_change, settings, provider, backend=Restricted())

    assert "may import `hypothesis`, `math`, and nothing else" in provider.systems[0]
    assert "`axioms` region" in provider.systems[0]


def test_a_session_whose_checker_polices_no_list_is_still_told_of_the_tool_s_limit(
    coin_change: Task, settings: Settings
) -> None:
    """Which of a language's modules are fine is that language's business.

    Where the file runs is Benchproofer's, and a file that includes one of its own is
    checked without it.
    """
    provider = Scripted(script())

    formalize(coin_change, settings, provider)

    assert "may import" not in provider.systems[0]
    assert "has to come with the toolchain" in provider.systems[0]


def test_each_request_after_the_solution_is_shown_the_task_and_told_what_it_writes(
    coin_change: Task, settings: Settings
) -> None:
    """Its rules name the statement, the tests, the golden patch and the code.

    The tests are the FAIL_TO_PASS tests and the PASS_TO_PASS tests the test patch adds or
    edits. One block, rendered once, goes into each request; the system prompt is the one for
    what the request writes: the solution file's rules for a region of it, a program's
    for `conformance.py` and `axioms.py`, the document's for `correspondence.md`.
    """
    provider = Scripted(script())

    formalize(coin_change, settings, provider, solution=ASSUMING)

    sent = {stage: provider.sent[provider.asked.index(stage)][0].content for stage in STAGED}
    systems = {stage: provider.systems[provider.asked.index(stage)] for stage in STAGED}
    blocks = set()
    for stage, prompt in sent.items():
        start = prompt.index("## The statement")
        assert coin_change.statement.strip()[:40] in prompt, stage
        assert "## The tests the benchmark judges the fix by" in prompt, stage
        assert "## The golden patch" in prompt, stage
        blocks.add(prompt[start : prompt.index("## The golden patch")])
    assert len(blocks) == 1
    assert systems["twin"] == systems["rival"]
    assert systems["twin"].startswith("You are formalizing one task")
    for stage in ("conformance", "axioms"):
        assert systems[stage].startswith("You are writing a Python program"), stage
    assert systems["correspondence"].startswith("You are writing `correspondence.md`")
    counted = " ".join(SHARED.rules("tests").split())
    assert all(counted in " ".join(system.split()) for system in systems.values())


#: The stages that write an artifact after the solution, each by one request.
STAGED = ("twin", "rival", "correspondence", "conformance", "axioms")


def test_a_system_prompt_is_handed_only_the_fields_its_template_names(
    settings: Settings,
) -> None:
    """The program's and the document's leave the solution file's guidance unread."""

    class Unread(Accepting):
        def guidance(self) -> str:
            raise AssertionError("the guidance was read")

    formalizer = drafter(Scripted({}), settings, Unread())

    assert formalizer._system("program-system").startswith("You are writing a Python program")
    assert formalizer._system("correspondence-system").startswith("You are writing")
    with pytest.raises(AssertionError, match="the guidance was read"):
        formalizer._system()


def test_a_specification_that_assumes_a_callee_is_asked_to_ground_it(
    coin_change: Task, settings: Settings
) -> None:
    """A proof is worth what its assumptions are worth, so the bundle ships an `axioms.py`."""
    provider = Scripted(script())

    result = formalize(coin_change, settings, provider, solution=ASSUMING)

    assert provider.turns("axioms") == 1
    assert "benchproofer:grounded os.cpu_count" in result.axioms
    assert not [note for note in result.notes if "axioms" in note]
    comparison = " ".join(provider.sent[provider.asked.index("conformance")][0].content.split())
    assert "must call the **real** function" in comparison


def test_an_axioms_py_reply_that_copies_the_solution_file_is_not_taken_as_one(
    coin_change: Task, settings: Settings
) -> None:
    """`axioms.py` has to contain the assumption, which invites copying the file it is in.

    A copy of the solution grounds nothing: it never calls the real callee, and it is
    not a program that prints the protocol. So the reply is spent asking again, and a
    second one no better leaves the bundle for the gate to fail rather than shipping a
    `axioms.py` that would be read as agreement.
    """
    whole = f"Here it is.\n\n```python\n{ASSUMING}```"
    provider = Scripted(script(axioms=[whole], retry=[whole]))

    result = formalize(coin_change, settings, provider, solution=ASSUMING)

    assert provider.turns("axioms") == 1 and provider.turns("retry") == 1
    assert not result.axioms
    assert any("no axioms.py was drafted" in note for note in result.notes)


def test_a_session_drafts_the_whole_bundle_when_every_stage_answers(
    coin_change: Task, settings: Settings
) -> None:
    provider = Scripted(script())

    result = formalize(coin_change, settings, provider)

    assert result.accepted and result.rounds == 1
    assert [twin.id for twin in result.twins] == ["twin"]
    assert [rival.kind for rival in result.rivals] == [
        "uniqueness",
        "uniqueness",
        "soundness",
    ]
    assert "benchproofer:begin impl" in result.conformance
    # Every pre-fix implementation and rival shares the accepted specification by construction.
    assert all(
        Accepting().same_spec(draft.source, result.solution)
        for draft in (*result.twins, *result.rivals)
    )
    assert "solution" not in [request["stage"] for request in result.provenance()["requests"]]


#: A solution modelling two functions, the second of which is where a pre-fix defect sits.
TWO_FUNCTIONS = f"""\
{SOLUTION}

# benchproofer:begin impl.2
def rest(cents):
    return cents - cents // 25 * 25
# benchproofer:end impl.2


# benchproofer:begin spec.2
def property_the_rest_is_under_a_quarter(cents):
    assert 0 <= rest(cents) < 25
# benchproofer:end spec.2
"""
#: The solution with a proof region of its own.
WITH_PROOF = (
    f"{SOLUTION}\n\n# benchproofer:begin proof\nSHIPPED = True\n# benchproofer:end proof\n"
)
#: The script's rivals with their region marked, as a reply owning two regions has to.
MARKED = [
    "RATIONALE: an attack.\n\n```python\n"
    + wrap("#", "impl", body.removeprefix("```python\n").removesuffix("```"))
    + "\n```"
    for body in (BODY, OTHER_BODY)
]


def test_a_pre_fix_implementation_is_offered_every_implementation_region_the_accepted_file_has(
    coin_change: Task, settings: Settings
) -> None:
    """The pre-fix difference sits in whichever function the fix changed.

    Offered only the first implementation region, a pre-fix implementation that rewrites the
    second is refused for writing a region it was not offered, however many times it is asked,
    and the bundle ships no pre-fix implementation for `spec.discriminates` to judge. This
    accepted file carries no proof, so the offer here is every `impl` region and nothing else.
    """
    twin = (
        "RATIONALE: the rest ignores the quarters already handed out.\n\n```python\n"
        "# benchproofer:begin impl.2\ndef rest(cents):\n    return cents\n"
        "# benchproofer:end impl.2\n```"
    )
    provider = Scripted(script(twin=[twin], rival=MARKED))

    result = formalize(coin_change, settings, provider, solution=TWO_FUNCTIONS)

    assert [draft.id for draft in result.twins] == ["twin"]
    regions = parse(result.twins[0].source, "#")
    assert regions["impl.2"].text == "def rest(cents):\n    return cents"
    assert regions["impl"].text == parse(TWO_FUNCTIONS, "#")["impl"].text
    offered = provider.sent[provider.asked.index("twin")][-1].content
    assert "Write the `impl` and `impl.2` regions" in offered
    assert provider.turns("retry") == 0


def test_a_pre_fix_implementation_is_offered_the_proof_of_the_implementation_it_rewrites(
    coin_change: Task, settings: Settings
) -> None:
    """A pre-fix implementation that could not touch the proof would ship the solution file's.

    That script is tuned to the fixed implementation, so it stops closing over the pre-fix one
    whether or not the specification tells the two programs apart -- and the refusal that
    follows would be read as the specification rejecting the bug. So a pre-fix implementation is
    offered what any other variant owns (`variant.owned`).
    """
    twin = (
        "RATIONALE: it never hands out a nickel.\n\n```python\n"
        + wrap("#", "impl", "def impl(cents):\n    return (0, 0, 0, cents)")
        + "\n"
        + wrap("#", "proof", "TWIN = True")
        + "\n```"
    )
    provider = Scripted(script(twin=[twin], rival=MARKED))

    result = formalize(coin_change, settings, provider, solution=WITH_PROOF)

    regions = parse(result.twins[0].source, "#")
    assert regions["proof"].text.strip() == "TWIN = True"
    offered = provider.sent[provider.asked.index("twin")][-1].content
    assert "Write the `impl` and `proof` regions" in offered


# ---- a `conformance.py` the stage can already see the gate will refuse ----

#: A `conformance.py` importing a helper the task's own code does not define: the specification
#: was written around a tidy function invented for the purpose, and the repository keeps
#: that logic inline.
INVENTED = (
    "```python\n"
    "from change import make_change, cache_entry_valid\n\n\n"
    "def shadow(cents):\n"
    "    # benchproofer:begin impl\n"
    "    quarters = cents // 25\n"
    "    return (quarters, 0, 0, cents - quarters * 25)\n"
    "    # benchproofer:end impl\n\n\n"
    "for cents in range(100):\n"
    "    assert cache_entry_valid(cents) == shadow(cents)\n"
    'print("benchproofer:compared change.cache_entry_valid 100 amounts")\n'
    "```"
)


def test_a_conformance_py_importing_a_name_the_task_lacks_is_asked_for_again(
    coin_change: Task, settings: Settings
) -> None:
    """A stage that can see the gate will refuse what it wrote asks again.

    What it reads off the file is decidable without a run, so shipping the draft with a
    note costs a full judging pass to be told what was already known here. It asks in the
    conversation that wrote `conformance.py`, so the redraft is a correction of a program the
    model can see, not a fresh attempt.
    """
    provider = Scripted(script(conformance=[f"Compared.\n\n{INVENTED}"]))

    result = formalize(coin_change, settings, provider)

    assert "cache_entry_valid" not in result.conformance
    assert "change.make_change" in result.conformance
    assert any("cannot establish anything" in note for note in result.notes)
    assert any("fail on its import line" in note for note in result.notes)
    opening, drafted, objection = provider.sent[provider.asked.index("conformance-repair")]
    assert "tries to refute that claim" in opening.content
    assert drafted.role == "assistant"
    assert "cache_entry_valid" in drafted.content
    assert "fail on its import line" in objection.content


def test_a_conformance_py_that_is_unusable_twice_is_kept_and_reported(
    coin_change: Task, settings: Settings
) -> None:
    """The repair loop is what addresses it next; the session does not drop the artifact.

    An artifact withheld leaves the gate reporting a missing `conformance.py`, which reads as a
    bundle nobody got to rather than one whose `conformance.py` was wrong.
    """
    twice = f"Compared.\n\n{INVENTED}"
    provider = Scripted(script(conformance=[twice], **{"conformance-repair": [twice]}))

    result = formalize(coin_change, settings, provider)

    assert "cache_entry_valid" in result.conformance
    assert any("still unusable" in note for note in result.notes)


# ---- a `conformance.py` run once where the gate will run it ------------


class Running(Oracle):
    """An environment whose program runs print what the script says, in order.

    The last output is reused once the script runs out, so a case lists only the runs it
    is about.
    """

    name = "running"
    summary = "prints what the script says"

    def __init__(self, *answers: OracleResult) -> None:
        self.answers = answers
        self.probed: list[Program] = []

    def judge(self, task, candidate, *, workdir, timeout_s=300.0):  # type: ignore[no-untyped-def]
        raise AssertionError("drafting never asks for a judgment")

    def probe(
        self, task: Task, program: Program, *, workdir: Path, timeout_s: float = 300.0
    ) -> OracleResult:
        self.probed.append(program)
        return self.answers[min(len(self.probed), len(self.answers)) - 1]


#: What a `conformance.py` prints when it compared what it was asked to.
COMPARED = "benchproofer:seed 7\nbenchproofer:compared change.make_change 100 amounts"
#: A `conformance.py` that died building its first input, before it compared anything.
CRASHED = OracleResult.no(
    "exit status 1",
    output=(
        "Traceback (most recent call last):\n"
        '  File "conformance.py", line 12, in <module>\n'
        "ValueError: refusing to construct a non-normalized amount"
    ),
)
#: A `conformance.py` nothing read off the file objects to, so what it does is up to the run.
CARRIED = (
    "```python\n"
    "import change\n\n"
    f"{SOLUTION.split('# benchproofer:begin spec')[0]}\n"
    "for cents in range(100):\n"
    "    assert change.make_change(cents) == impl(cents)\n"
    'print("benchproofer:compared change.make_change 100 every amount under 100")\n'
    "```"
)
#: The redraft, told apart from the first draft by a comment of its own.
FIXED = CARRIED.replace("import change\n", "import change  # normalized inputs\n")


def carrying(*redrafts: str, **overrides: Sequence[str | Completion]) -> Scripted:
    """A model whose `conformance.py` is `CARRIED`, redrafted after a run as ``redrafts``."""
    replies = script(conformance=[f"Compared.\n\n{CARRIED}"], **overrides)
    if redrafts:
        replies["conformance-run"] = [f"Redrafted.\n\n{body}" for body in redrafts]
    return Scripted(replies)


def test_a_conformance_py_that_dies_before_comparing_is_sent_back_with_what_it_printed(
    coin_change: Task, settings: Settings
) -> None:
    oracle = Running(CRASHED, OracleResult.ok(output=COMPARED))
    provider = carrying(FIXED)

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert "normalized inputs" in result.conformance
    assert [program.label for program in oracle.probed] == ["conformance", "conformance"]
    assert all(program.with_reference for program in oracle.probed)
    sent = dict(zip(provider.asked, provider.sent, strict=True))
    _, drafted, ran = sent["conformance-run"]
    assert drafted.role == "assistant"
    assert "refusing to construct a non-normalized amount" in ran.content
    assert "failed without naming a disagreement" in ran.content
    assert any("cannot establish anything" in note for note in result.notes)


def test_a_copy_that_is_not_verbatim_is_sent_back_with_the_line_it_lacks(
    coin_change: Task, settings: Settings
) -> None:
    """A renamed call is the program's to undo, so the redraft is told which line it lost."""
    renamed = CARRIED.replace(
        "    quarters = cents // 25\n", "    quarters = shadow_div(cents)\n"
    )
    provider = Scripted(
        script(
            conformance=[f"Compared.\n\n{renamed}"],
            **{"conformance-repair": [f"Compared.\n\n{CARRIED}"]},
        )
    )

    result = formalize(coin_change, settings, provider)

    objection = provider.sent[provider.asked.index("conformance-repair")][-1].content
    assert "not contain the verified implementation verbatim" in objection
    assert (
        "the first line of the `impl` region it lacks is `quarters = cents // 25`" in objection
    )
    assert "outside the region" in objection
    assert "shadow_div" not in result.conformance


def test_a_function_the_program_reports_skipped_need_not_have_its_body_copied(
    coin_change: Task, settings: Settings
) -> None:
    """It is not compared, so a copy of it would only push the program to compare it."""
    watching = (
        SOLUTION + "\n\n# benchproofer:begin spec.2\ndef property_dispensed(cents):\n"
        "    assert dispense(cents) == cents\n# benchproofer:end spec.2\n"
        "\n\n# benchproofer:begin impl.2\ndef dispense(cents):\n    return cents\n"
        "# benchproofer:end impl.2\n"
    )
    skipping = CARRIED.replace(
        "\n```",
        '\nprint("benchproofer:skipped dispense: it needs a coin dispenser")\n```',
    )
    # The cases the script writes carry one region of two, which is not what this is about.
    provider = Scripted(script(conformance=[f"Skipped.\n\n{skipping}"], retry=[BODY]))

    result = formalize(coin_change, settings, provider, solution=watching)

    assert "conformance-repair" not in provider.asked
    assert "benchproofer:skipped dispense" in result.conformance
    assert "return cents" not in result.conformance
    # Without the report, the same program is sent back for the body it lacks.
    silent = Scripted(script(conformance=[f"Compared.\n\n{CARRIED}"], retry=[BODY]))
    formalize(coin_change, settings, silent, solution=watching)
    objection = silent.sent[silent.asked.index("conformance-repair")][-1].content
    assert (
        "the first line of the `impl.2` region it lacks is `def dispense(cents):`" in objection
    )
    request = " ".join(provider.sent[provider.asked.index("conformance")][0].content.split())
    assert "its body need not be copied into the program, since it is not compared" in request


def test_a_redraft_the_provider_never_answered_keeps_conformance_py_drafted(
    coin_change: Task, settings: Settings
) -> None:
    """The gate still judges what was drafted, and the rest of the session still runs."""
    oracle = Running(CRASHED)
    provider = Failing(script(conformance=[f"Compared.\n\n{CARRIED}"]), on="conformance-run")

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert result.conformance == CARRIED.removeprefix("```python\n").removesuffix("```")
    assert any("conformance round 2: the provider failed" in note for note in result.notes)


def test_a_redraft_that_is_not_a_program_keeps_the_first_draft(
    coin_change: Task, settings: Settings
) -> None:
    """The gate still judges what was drafted, and the repair session is what addresses it."""
    oracle = Running(CRASHED, OracleResult.ok(output=COMPARED))
    provider = carrying("I would normalize the amounts first.")

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert provider.turns("conformance-run") == 1
    assert "retry" not in provider.asked
    assert result.conformance == CARRIED.removeprefix("```python\n").removesuffix("```")
    assert len(oracle.probed) == 1
    assert any("still unusable after its redraft" in note for note in result.notes)


#: A run of `conformance.py` that compared and found the repository answering differently.
DISAGREED = OracleResult.no(
    "exit status 1",
    output=(
        "benchproofer:seed 7\n"
        "benchproofer:compared change.make_change 100 amounts\n"
        "benchproofer:disagrees change.make_change [cents=30] repo=(1,0,0,5) impl=(1,0,1,0)"
    ),
)
#: A `conformance.py` that gave up on part of the comparison and said so.
DECLINED = OracleResult.ok(
    output=(
        "benchproofer:seed 7\n"
        "benchproofer:compared change.make_change 100 amounts\n"
        "benchproofer:skipped change.tally: takes a callback, not an amount"
    )
)
#: A run that compared, but could not build one admitted input for the repository.
UNBUILT = OracleResult.ok(
    output=(
        f"{COMPARED}\n"
        "benchproofer:blocked change.make_change [cents=-1]: this program could not build "
        "it: ValueError: refusing to construct a negative amount"
    )
)


@pytest.mark.parametrize(
    "answer",
    [
        DISAGREED,
        replace(DISAGREED, output=DISAGREED.output + "\n" + UNBUILT.output.splitlines()[-1]),
    ],
    ids=["alone", "beside-an-unbuilt-input"],
)
def test_a_disagreement_is_left_for_the_gate(
    coin_change: Task, settings: Settings, answer: OracleResult
) -> None:
    """A disagreement is the program's own claim about the comparison, and not sent back.

    A model asked about it can answer by changing the measurement -- no longer drawing
    the input the repository raises on -- which turns a finding about the specification
    into a pass. So it stays the gate's even beside a defect `conformance.py` could fix.
    """
    oracle = Running(answer)
    provider = carrying()

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert len(oracle.probed) == 1
    assert provider.turns("conformance-run") == 0
    assert result.conformance == CARRIED.removeprefix("```python\n").removesuffix("```")


def test_a_declared_gap_is_sent_back_once_asking_for_a_bridge(
    coin_change: Task, settings: Settings
) -> None:
    """`skipped` is as often a function easily reached as one nothing here can call.

    So it is put back once, with a way to reach it -- construct the object around a stub
    -- and with the rules against weakening the comparison, which stay as they were.
    """
    oracle = Running(DECLINED, OracleResult.ok(output=COMPARED))
    provider = carrying(FIXED)

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert "normalized inputs" in result.conformance
    assert len(oracle.probed) == 2
    _, drafted, asked_for = provider.sent[provider.asked.index("conformance-run")]
    assert drafted.role == "assistant"
    assert "`change.tally: takes a callback, not an amount` as skipped" in (asked_for.content)
    assert "by reaching it another\nway" in asked_for.content
    assert "a stub of your own in that callable's place" in asked_for.content
    assert "The comparison is not yours to weaken" in asked_for.content


@pytest.mark.parametrize(
    ("redraft", "runs"), [(FIXED, 2), (CARRIED, 1)], ids=["redrafted", "unchanged"]
)
def test_a_declared_gap_the_redraft_keeps_is_believed(
    coin_change: Task, settings: Settings, redraft: str, runs: int
) -> None:
    """Once per session: asked again, a model would be asked to stop saying it."""
    oracle = Running(DECLINED)
    provider = carrying(redraft)

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert provider.turns("conformance-run") == 1
    assert len(oracle.probed) == runs
    assert any("the report stands" in note for note in result.notes)
    assert not any("still unusable" in note for note in result.notes)


@pytest.mark.parametrize(
    "line",
    [
        UNBUILT.output.splitlines()[-1],
        "benchproofer:blocked change.make_change [cents=-1]: the repository refuses it: "
        "ValueError: an amount is never negative",
        "benchproofer:blocked change.make_change [cents=40]: this program's copy of the "
        "implementation raised: TypeError: can only concatenate tuple",
        "benchproofer:refused [cents=-1]: ValueError: an amount is never negative",
    ],
    ids=["not built", "refused", "copy raised", "named by its reason"],
)
def test_an_input_conformance_py_did_not_compare_is_left_to_the_gate(
    coin_change: Task, settings: Settings, line: str
) -> None:
    """Read as the gate reads it, whatever the reason the line gives.

    Sent back, the program could be asked to stop drawing a value the specification admits,
    which hides a finding about the specification's domain rather than answering it.
    """
    oracle = Running(OracleResult.ok("exit status 0", output=f"{COMPARED}\n{line}\n"))
    provider = carrying()

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert len(oracle.probed) == 1
    assert provider.turns("conformance-run") == 0
    assert "import change\n" in result.conformance


def test_a_report_line_no_reader_parses_is_sent_back_verbatim_with_its_shape(
    coin_change: Task, settings: Settings
) -> None:
    """Told only that it compared nothing, a program that did compare cannot see why.

    The line is what the redraft has to change, so it is quoted as printed, beside the
    shape the protocol gives a line of its kind, rather than summarized as silence.
    """
    misread = (
        "benchproofer:compared change.make_change[amounts under a dollar] 100 "
        "every amount under 100"
    )
    oracle = Running(
        OracleResult.ok(output=f"benchproofer:seed 7\n{misread}"),
        OracleResult.ok(output=COMPARED),
    )
    provider = carrying(FIXED)

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert "normalized inputs" in result.conformance
    assert len(oracle.probed) == 2
    follow_up = provider.sent[provider.asked.index("conformance-run")][-1].content
    assert f"`{misread}`" in follow_up
    assert f"`{differential.SHAPES['compared']}`" in follow_up
    assert "no space in it" in follow_up
    assert "reported comparing nothing" not in follow_up


@pytest.mark.parametrize(
    ("answer", "said"),
    [
        (OracleResult.ok(output="benchproofer:seed 7"), "reported comparing nothing"),
        (OracleResult.timeout("no answer in 900 s"), "did not finish within"),
        (
            OracleResult.no(
                "exit status 1",
                output=(
                    "benchproofer:skipped change.make_change: import failed: "
                    "ModuleNotFoundError: No module named 'coins'"
                ),
            ),
            "because an import failed",
        ),
        (
            OracleResult.ok(
                output=(
                    "Traceback (most recent call last):\n"
                    "ImportError: cannot import name 'make_change'\n"
                    "benchproofer:skipped change.make_change: nothing to call"
                )
            ),
            "because an import failed",
        ),
        (
            OracleResult.no(
                "exit status 1",
                output="benchproofer:skipped change.make_change: needs a live account",
            ),
            "having compared nothing",
        ),
    ],
    ids=["nothing", "timeout", "import-said", "import-raised", "compared-nothing"],
)
def test_a_conformance_py_still_establishing_nothing_is_kept_after_its_redraft(
    coin_change: Task, settings: Settings, answer: OracleResult, said: str
) -> None:
    """Labelled `skipped`, a program that never started is sent back as a crash is."""
    oracle = Running(answer)
    provider = carrying(FIXED)

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert provider.turns("conformance-run") == 1
    assert len(oracle.probed) == 2
    assert said in provider.sent[provider.asked.index("conformance-run")][-1].content
    assert "normalized inputs" in result.conformance
    assert any("still unusable after its redraft" in note for note in result.notes)


def test_a_conformance_py_the_environment_cannot_run_is_left_to_the_gate(
    coin_change: Task, settings: Settings
) -> None:
    oracle = Running(OracleResult.unavailable("docker is not running"))
    provider = carrying()

    result = formalize(coin_change, settings, provider, oracle=oracle)

    assert provider.turns("conformance-run") == 0
    assert any("could not be run while drafting" in note for note in result.notes)


def test_the_drafting_prompts_state_what_the_conformance_gate_holds_a_conformance_py_to(
    coin_change: Task, settings: Settings
) -> None:
    """A rule the gate enforces and the prompt never states costs a round for nothing.

    The solution and `conformance.py` are both told which functions the comparison may reach.
    `conformance.py` is told that a call keeps its spelling inside the region, since one renamed
    to a shadow is a line the verbatim rule finds missing, and to draw a projected input
    from the repository side, since an abstract input no repository value has would
    otherwise be reported blocked. Read with its line breaks folded, so a template
    reflowed says the same thing.
    """
    provider = Scripted(script())
    session = Drafting()

    formalize(coin_change, settings, provider, session=session)

    sent = dict(zip(provider.asked, provider.sent, strict=True))
    opening = session.asked[0].prompt
    harness = " ".join(sent["conformance"][-1].content.split())
    assert (
        "* in `change.py`: `make_change`" in opening
        and "Model the fix, not a re-imagining" in opening
    )
    assert (
        "* in `change.py`: `make_change`" in harness
        and "bridge any type simplifications" in harness
    )
    assert "keeps its spelling inside the region" in harness
    assert "`serialize_value = shadow_serialize_value`" in harness
    assert "build the repository value first" in harness
    assert "read the specification's input off it" in harness
    assert "with the projection where the draw starts from the repository" in harness


# ---- what `axioms.py` is drafted with ----------------------------------------


#: An `axioms.py` that calls the real callee and copies none of the model it checks.
BARE = (
    "```python\n"
    "import os\n\n"
    "assert cpu_count() == os.cpu_count()\n"
    'print("benchproofer:grounded os.cpu_count 1 input")\n'
    "```"
)


def test_the_tool_writes_the_declarations_into_axioms_py(
    coin_change: Task, settings: Settings
) -> None:
    """A model asked to copy them reflows them, and the gate then runs nothing at all."""
    provider = Scripted(script(axioms=[f"Here.\n\n{BARE}"]))

    result = formalize(coin_change, settings, provider, solution=ASSUMING)

    region = parse(ASSUMING, "#", required=())["axioms"].text
    assert result.axioms.startswith("import os\n")
    assert quotes_lines(result.axioms, region, "#")
    assert "#     return 8" in result.axioms
    assert not [note for note in result.notes if "axioms" in note]


@pytest.mark.parametrize(
    ("kind", "check", "session", "found"),
    [
        ("uniqueness", CheckResult.no("cents=40"), "", "refute"),
        ("uniqueness", CheckResult.ok("accepted"), "", "refute: verified"),
        ("soundness", CheckResult.ok("accepted"), "", "verify"),
        ("soundness", CheckResult.no("unsolved goals"), "", "verify: refuted"),
        (
            "soundness",
            CheckResult.no("unsolved goals"),
            "a proof session reported stuck",
            "verify: unproved, correct but the checker rejected a step of its own proof",
        ),
        (
            "soundness",
            CheckResult.unknown("no answer in 300s"),
            "",
            "verify: undecided, the checker reached no verdict",
        ),
    ],
    ids=["refused", "accepted wrongly", "accepted", "refused wrongly", "gap", "no answer"],
)
def test_what_a_case_found_is_recorded_beside_what_it_expected(
    kind: str, check: CheckResult, session: str, found: str
) -> None:
    """A reader of the shipped index cannot tell from `expect` alone whether a case behaved.

    A correct case the checker refused on a step of its own proof reads exactly like one it
    accepted, and the one a proof session was already spent on is the gap the property-based
    test suite reports rather than a case to draft again.
    """
    draft = Draft(
        id="case-1",
        kind=kind,
        rationale="a case",
        source=SOLUTION,
        check=check,
        proof_session=session,
    )

    assert draft.found == found


# ---- a case the checker must accept, drafted wrongly ---------------------

IMPL_REGION = SOLUTION.split("# benchproofer:begin spec")[0].strip()
PROBE = "def admissibility_probe():\n    assert impl(40) == (1, 0, 0, 15)\n"
#: A wrong implementation, for the cases meant to be refused.
WRONG = "def impl(cents):\n    return (0, 0, 0, cents)"
#: The same, in its marked region.
MARKED_WRONG = wrap("#", "impl", WRONG)


class Proving(Accepting):
    """A prover that accepts every file, wrong or not."""

    name = "proving"
    kind = BackendKind.PROVER


class Fussy(Proving):
    """A prover that refuses a loop on its merits."""

    name = "fussy"

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        if "while " in source:
            return CheckResult.no(
                "Loop invariant might not be preserved.",
                output="Verification failed\nLoop invariant might not be preserved.",
            )
        return CheckResult.ok("all obligations discharged")


def drafted(
    provider: Scripted,
    settings: Settings,
    task: Task,
    kind: str,
    backend: Backend,
    *,
    solution: str = SOLUTION,
    allowed: tuple[str, ...] = ("impl",),
) -> tuple[Draft, Journal]:
    """Draft one case of ``kind`` by `_variant`: a rival, or the pre-fix implementation."""
    journal = Journal()
    twin = kind == "twin"
    draft = drafter(provider, settings, backend)._variant(
        "twin" if twin else "rival",
        "twin" if twin else f"{kind}-1",
        kind,
        "Write the pre-fix implementation." if twin else "Write a rival.",
        solution,
        "",
        journal,
        allowed=allowed,
        task=task,
    )
    assert draft is not None
    return draft, journal


def replied(*regions: str) -> Scripted:
    """A model whose rival replies are ``regions``, in order."""
    replies = [f"RATIONALE: a case.\n\n```python\n{region}\n```" for region in regions]
    return Scripted({"rival": replies})


def test_a_probe_written_after_the_region_is_carried_into_it_without_a_redraft(
    coin_change: Task, settings: Settings
) -> None:
    """After the region's end line is where a model puts a function asked for after the body.

    A splice that read the region alone would lose the probe there and file the solution
    file unchanged, and asking again for the same placement would get the same reply back.
    Carried into the region, it is the probe the model meant.
    """
    after = f"RATIONALE: a probe.\n\n```python\n{IMPL_REGION}\n\n{PROBE}```"
    provider = Scripted({"rival": [after]})

    draft, _ = drafted(provider, settings, coin_change, "admissibility", Fussy())

    assert provider.turns("rival") == 1
    impl = parse(draft.source, "#")["impl"].text
    assert impl.endswith(f"\n\n\n{PROBE.rstrip()}")


def test_a_second_probe_is_drafted_where_a_pass_to_pass_test_hands_the_fix_an_input(
    coin_change: Task, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The model's domain admits what the PASS_TO_PASS tests hand a changed function too.

    So where the test patch adds or edits one, or one calls a function the fix changes, a
    second probe is asked for at the inputs of those tests, shown to it, and is an
    admissibility case like the first, judged by the same gate. Where none does, the suite
    has the one probe at the FAIL_TO_PASS tests' inputs.
    """
    shown = (
        "### `tests/test_change.py::test_quarter`, which calls `make_change`, in "
        "`tests/test_change.py`\n\n```python\ndef test_quarter():\n"
        "    assert make_change(25) == (1, 0, 0, 0)\n```"
    )
    probe = f"RATIONALE: a probe.\n\n```python\n{IMPL_REGION}\n\n{PROBE}```"

    def battery(regression: str) -> tuple[list[str], list[str]]:
        monkeypatch.setattr(Formalizer, "_regression", lambda self, task: regression)
        provider = Scripted({"rival": [probe]})
        drafts = drafter(provider, settings, Proving())._battery(
            coin_change, SOLUTION, "", Journal(), ()
        )
        probes = [
            " ".join(message.content.split())
            for turn in provider.sent
            for message in turn
            if "Write an admissibility case" in message.content
        ]
        return [draft.id for draft in drafts if draft.kind == "admissibility"], probes

    ids, (first, second) = battery(shown)

    assert ids == ["admissibility-1", "admissibility-2"]
    assert "of the shape the FAIL_TO_PASS tests use" in first and "test_quarter" not in first
    assert "of the shape the PASS_TO_PASS tests below use" in second
    assert "inputs the PASS_TO_PASS tests hand a function the fix changes" in second
    assert " ".join(shown.split()) in second
    assert battery("")[0] == ["admissibility-1"]


class Tactic(Proving):
    """A prover whose accepting verdict replays a proof script the file carries.

    So a rejection is what reshaping an implementation produces, and a reject case has to
    carry a refutation witness for its rejection to attribute anything.
    """

    name = "tactic"
    witness_required = True
    banned_tokens = ("sorry", "assume(")
    witness_placement = "* State it over the tester this checker derives for the method."


def test_a_reject_case_is_asked_for_the_witness_form_its_checker_has(
    coin_change: Task, settings: Settings
) -> None:
    """Where the specification is not a proposition, there is nothing to negate directly.

    The form a witness takes belongs to the checker, as an admissibility probe's placement
    does, so the request carries the backend's own rather than one wording for all of them.
    """
    formalizer = drafter(Scripted({}), settings, Tactic())

    prompt = formalizer._rival_prompt(coin_change, SOLUTION, "uniqueness", [], ("impl",))

    assert "the tester this checker derives for the method" in prompt
    assert "no `benchproofer:` sentinel" in prompt
    # A case the checker has to accept has nothing to attribute, so it is asked for none.
    assert "refutation witness" not in formalizer._rival_prompt(
        coin_change, SOLUTION, "soundness", [], ("impl",)
    )


def test_a_pre_fix_implementation_is_asked_for_a_witness_that_the_code_before_the_fix_is_wrong(
    coin_change: Task, settings: Settings
) -> None:
    """Its refusal is `spec.discriminates`'s whole question, and alone it attributes nothing.

    So it is asked in its own terms: the claim is about the code before the fix, at the
    inputs the task's failing tests exercise, and not about a rival.
    """
    prompt = drafter(Scripted({}), settings, Tactic())._twin_prompt(coin_change, SOLUTION)

    assert "refutation witness" in prompt
    assert "the code before the fix violates the specification" in prompt
    assert "the inputs of the FAIL_TO_PASS tests are where to look" in prompt
    assert "only because it uses a name\n  the golden patch adds" in prompt
    # A claim at one input binds nothing.
    assert "binds no hypothesis and no\n  value, and a binder is refused" in prompt
    assert "your rival" not in prompt
    assert "the tester this checker derives for the method" in prompt
    # Under a checker whose rejection needs no witness, a pre-fix implementation is asked for
    # none.
    unwitnessed = drafter(Scripted({}), settings, Proving())
    assert "refutation witness" not in unwitnessed._twin_prompt(coin_change, SOLUTION)


#: A pre-fix implementation's witness: the specification refuses the code before the fix at 40
#: cents.
TWIN_CLAIM = "example : \u00ac property_change_sums_to_the_amount 40 := by decide"


def test_a_pre_fix_implementation_carries_the_witness_its_reply_offers(
    coin_change: Task, settings: Settings
) -> None:
    reply = (
        f"RATIONALE: it never hands out a nickel.\n\n```python\n{MARKED_WRONG}\n```\n\n"
        f"```lean\n{TWIN_CLAIM}\n```"
    )
    provider = Scripted({"twin": [reply]})

    (draft,) = drafter(provider, settings, Tactic())._twin(coin_change, SOLUTION, "", Journal())

    assert draft.witness.strip() == TWIN_CLAIM
    assert provider.turns("twin") == 1


def test_a_pre_fix_implementation_with_no_witness_is_noted_for_the_gate_that_reads_it(
    coin_change: Task, settings: Settings
) -> None:
    reply = f"RATIONALE: it never hands out a nickel.\n\n```python\n{MARKED_WRONG}\n```"
    journal = Journal()

    (draft,) = drafter(Scripted({"twin": [reply]}), settings, Tactic())._twin(
        coin_change, SOLUTION, "", journal
    )

    assert draft.witness == ""
    assert any(
        "for the discrimination check no claim proved at one input" in note
        for note in journal.notes
    )


def test_a_pre_fix_implementation_owning_one_unmarked_region_is_read_before_its_witness(
    coin_change: Task, settings: Settings
) -> None:
    """One region needs no sentinels, and the witness after it is a block too.

    Read by its last block, such a reply would splice the witness in as the implementation.
    """
    reply = (
        f"RATIONALE: it never hands out a nickel.\n\n```python\n{WRONG}\n```\n\n"
        f"```lean\n{TWIN_CLAIM}\n```"
    )

    draft, _ = drafted(Scripted({"twin": [reply]}), settings, coin_change, "twin", Tactic())

    assert parse(draft.source, "#")["impl"].text.strip() == WRONG
    assert draft.witness.strip() == TWIN_CLAIM


def test_a_pre_fix_implementation_whose_proof_gives_up_gets_the_accepted_proof_back(
    coin_change: Task, settings: Settings
) -> None:
    """No honest proof of the code before the fix closes, so the pre-fix one may use `sorry`.

    The gate refuses such a file unread. Under a checker whose refusal needs a witness it is the
    witness that attributes the refusal, so the solution file's proof in its place loses nothing
    the pre-fix implementation claims -- and a case meant to verify keeps what it wrote, since
    there a proof that gives up is the finding.
    """
    reply = (
        f"RATIONALE: it never hands out a nickel.\n\n```python\n{MARKED_WRONG}\n"
        + wrap("#", "proof", "sorry")
        + f"\n```\n\n```lean\n{TWIN_CLAIM}\n```"
    )
    provider = Scripted({"twin": [reply], "rival": [reply]})
    journal = Journal()

    (draft,) = drafter(provider, settings, Tactic())._twin(coin_change, WITH_PROOF, "", journal)

    regions = parse(draft.source, "#")
    assert regions["proof"].text.strip() == "SHIPPED = True"
    assert regions["impl"].text.strip().endswith("return (0, 0, 0, cents)")
    assert draft.witness.strip() == TWIN_CLAIM
    assert provider.turns("twin") == 1
    assert any("the solution file's proof was put back" in note for note in journal.notes)
    kept, _ = drafted(
        provider,
        settings,
        coin_change,
        "soundness",
        Tactic(),
        solution=WITH_PROOF,
        allowed=("impl", "proof"),
    )
    assert parse(kept.source, "#")["proof"].text.strip() == "sorry"


def rival_reply(body: str, witness_claim: str = "") -> str:
    """A rival reply writing ``body`` as its implementation, with a witness where given."""
    reply = "RATIONALE: an attack.\n\n```python\n" + wrap("#", "impl", body) + "\n```"
    return f"{reply}\n\n```python\n{witness_claim}\n```" if witness_claim else reply


def test_a_witness_the_reply_wrapped_in_sentinels_of_its_own_is_still_read(
    coin_change: Task, settings: Settings
) -> None:
    """`markers.REGIONS` has no `witness`, and the prompt asks for a marker nowhere.

    Read as part of the file, such a block names an unknown region and the whole reply is
    refused -- so the rival is lost too, over a sentinel that is plainly not the file's.
    """
    claim = "example : ¬ Spec 3 (impl 3) := by decide"
    reply = rival_reply(
        WRONG, f"# benchproofer:begin witness\n{claim}\n# benchproofer:end witness"
    )
    provider = Scripted({"rival": [reply]})

    draft, _ = drafted(provider, settings, coin_change, "uniqueness", Tactic())

    assert draft.witness.strip() == claim
    assert provider.turns("rival") == 1


def test_a_wrong_rival_the_checker_accepts_is_kept_rather_than_retried_away(
    coin_change: Task, settings: Settings
) -> None:
    """The other half of the asymmetry: that verdict is the finding the suite exists for."""
    provider = replied(IMPL_REGION.replace("cents - quarters * 25", "cents"))

    draft, _ = drafted(provider, settings, coin_change, "uniqueness", Fussy())

    assert provider.turns("rival") == 1
    assert draft.found == "refute: verified"


#: A Lean solution file, whose implementation Python cannot run.
LEAN = """\
-- benchproofer:begin spec
theorem sums (c : Nat) : (change c).1 * 25 + (change c).2 = c := by sorry
-- benchproofer:end spec
-- benchproofer:begin impl
def change (c : Nat) : Prod Nat Nat :=
  (c / 25, c % 25)
-- benchproofer:end impl
"""


@pytest.mark.parametrize("backend", ["lean4", "accepting"])
def test_an_implementation_python_cannot_run_is_ported_line_by_line(
    backend: str, coin_change: Task, settings: Settings
) -> None:
    """A port kept to the model's structure is one a reviewer can check against it."""
    lean = backend == "lean4"
    provider = Scripted(script())
    formalizer = drafter(provider, settings, BACKENDS.get("lean4") if lean else Accepting())

    formalizer._conformance(coin_change, LEAN if lean else SOLUTION, Journal())

    request = " ".join(provider.sent[provider.asked.index("conformance")][0].content.split())
    port = "Port it line by line and keep its structure"
    assert (port in request) is lean
    assert ("annotations taken out, exactly as written>" in request) is not lean
    assert ("in Lean 4, which Python cannot run" in request) is lean
    assert "nagini_contracts" not in request
    if lean:
        assert "end each line of the port with a comment naming that line" in request


def test_a_program_is_told_what_the_tasks_image_runs_and_what_is_on_its_import_path(
    coin_change: Task, settings: Settings
) -> None:
    """The tests passed there, so what they run can be run there, test modules as they do."""
    provider = Scripted(script())
    session = Drafting(ASSUMING)

    formalize(coin_change, settings, provider, session=session)

    rule = " ".join(SHARED.rules("image").split())
    for stage in ("conformance", "axioms"):
        assert rule in " ".join(provider.systems[provider.asked.index(stage)].split()), stage
    assert rule in " ".join(session.asked[0].prompt.split())
    assert "Django's `tests/`" in rule and "a browser engine" in rule


def test_an_empty_outside_the_bridge_section_is_one_line_and_read_so(
    coin_change: Task, settings: Settings
) -> None:
    """A reason written beside `Nothing.` is read as an entry, and the request says so."""
    provider = Scripted(script())

    formalize(coin_change, settings, provider)

    request = " ".join(provider.sent[provider.asked.index("correspondence")][0].content.split())
    assert "the section is the one line `Nothing.`, with no reason given" in request
    assert entries_under("## Outside the bridge\n\nNothing.\n", OUTSIDE) == ""
    reasoned = "## Outside the bridge\n\nEvery input is set against the fix.\n\nNothing.\n"
    assert entries_under(reasoned, OUTSIDE) != ""


def test_a_callee_is_named_by_its_dotted_python_path_under_every_backend() -> None:
    """The path is what decides whether `axioms.py` runs against the fixed code."""
    for name in ("nagini", "lean4", "velvet"):
        text = " ".join(BACKENDS.get(name).callees().split())
        assert (
            "`<callee>` on either line is the callee itself, as the dotted Python path" in text
        )


def test_the_drafter_is_told_of_a_file_the_fix_writes_that_is_not_python(
    coin_change: Task, settings: Settings
) -> None:
    """Listing the Python names the fix changes alone tells the drafter they are all of it."""
    quirk, _ = revised("quirks/array_at.user.js", "", "Array.prototype.at = f;\n")
    task = coin_change.model_copy(
        update={
            "reference": coin_change.reference.model_copy(
                update={"patch": (coin_change.reference.patch or "") + quirk}
            )
        }
    )
    session = Drafting()

    formalize(task, settings, Scripted(script()), session=session)

    opening = " ".join(session.asked[0].prompt.split())
    assert "It also writes these files, which are not Python: * `quirks/array_at.user.js`" in (
        opening
    )
    assert "model it as the code there computes it" in opening


def test_a_witness_request_names_the_axioms_no_witness_evaluates_or_assumes(
    coin_change: Task, settings: Settings
) -> None:
    """Where every refutation needs one of them, no admissible witness exists: it says so."""
    formalizer = drafter(Scripted({}), settings, Tactic())

    prompt = formalizer._rival_prompt(coin_change, ASSUMING, "uniqueness", [], ("impl",))
    plain = formalizer._rival_prompt(coin_change, SOLUTION, "uniqueness", [], ("impl",))

    text = " ".join(prompt.split())
    assert "declares `cpu_count` under `benchproofer:axiom` lines." in text
    assert "no admissible witness exists: say so in the rationale" in text
    assert "under `benchproofer:axiom` lines." not in " ".join(plain.split())


def test_a_probe_inside_the_method_restates_the_specification_rather_than_calling_it(
    coin_change: Task, settings: Settings
) -> None:
    """A call there recurses, so a Velvet probe proves the clauses at literal inputs."""
    velvet = drafter(Scripted({}), settings, BACKENDS.get("velvet"))
    python = drafter(Scripted({}), settings, Accepting())

    probe = " ".join(
        velvet._rival_prompt(coin_change, LEAN, "admissibility", [], ("impl",)).split()
    )
    called = " ".join(
        python._rival_prompt(coin_change, SOLUTION, "admissibility", [], ("impl",)).split()
    )

    assert "cannot call the method, which would be a recursive call" in probe
    assert "call what the specification declares at that input" not in probe
    assert "call what the specification declares at that input" in called
