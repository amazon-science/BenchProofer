# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Proofs written by an agent session, with the specification and implementation fixed.

The session is a double that plays the prover: it rewrites the file in its workspace and
reports. What is pinned is what the tool keeps of that, which does not depend on the
model: a file with another specification or implementation is refused whatever the
checker says, a loop annotation is the prover's to change, and what is kept is what the
checker accepted.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

import pytest
from test_session import Scripted, drafter, script

from benchproofer.backends.base import Backend, CheckResult
from benchproofer.config import Settings
from benchproofer.core import variant
from benchproofer.core.scripts import lay_out
from benchproofer.core.session import Journal
from benchproofer.core.task import Task
from benchproofer.errors import BundleError, ProviderError
from benchproofer.formalize.prove import ProofKind, Proved, Prover
from benchproofer.llm.agentic import EDIT, AgentSession, SessionSpec, StepOutcome
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import read_text, write_text
from doubles import Accepting

#: A file whose proof region holds a hole.
HOLE = """\
# benchproofer:begin spec
def spec(cents, out):
    assert sum(out) >= 0
# benchproofer:end spec

# benchproofer:begin impl
def impl(cents):
    total = 0
    while total < cents:
        invariant(total <= cents)
        total += 1
    return (0, 0, 0, total)
# benchproofer:end impl

# benchproofer:begin proof
# hole
# benchproofer:end proof
"""
PROVED = HOLE.replace("# hole", "# closed")


#: The words that open a probe's claim, which the session may prove and not restate.
OPENERS = ("example", "theorem")


class Proving(Accepting):
    """A prover whose checker accepts a file exactly when its proof is closed."""

    name = "proving"
    proof_carrying: ClassVar[bool] = True
    proof_annotations: ClassVar[tuple[str, ...]] = ("invariant",)
    banned_tokens: ClassVar[tuple[str, ...]] = ("sorry",)
    probe_claims: ClassVar[tuple[str, ...]] = OPENERS

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        if "# closed" in source:
            return CheckResult.ok("elaborated with no errors")
        return CheckResult.no("unsolved goals: total = cents")


class Writing(AgentSession):
    """A session that rewrites the file it is pointed at, then reports."""

    name = "writing"

    def __init__(self, rewrite: Callable[[str], str], status: str = "ok") -> None:
        super().__init__()
        self.rewrite = rewrite
        self.status = status
        self.asked: list[SessionSpec] = []

    def run(self, spec: SessionSpec) -> StepOutcome:
        self.asked.append(spec)
        target = next(spec.cwd.glob("bundles/**/solution.*"))
        write_text(target, self.rewrite(read_text(target)))
        payload: dict[str, Any] = {"status": self.status, "notes": "unfolded the loop"}
        return StepOutcome(text="", payload=payload, turns=4, tool_uses=6)


REFUSED = CheckResult.no("unsolved goals: total = cents")


def prove(
    session: AgentSession,
    settings: Settings,
    task: Task,
    source: str = HOLE,
    kind: ProofKind = "claim",
    backend: Backend | None = None,
) -> Proved:
    """Hand ``source``, refused, to a proof session of ``kind``, under `Proving` by default."""
    prover = Prover(
        session=session,
        backend=backend or Proving(),
        settings=settings,
        workdir=settings.cache_dir,
    )
    return prover.prove(task, source, REFUSED, label="solution", kind=kind)


def test_a_proof_the_checker_accepts_is_kept(settings: Settings, coin_change: Task) -> None:
    session = Writing(lambda text: text.replace("# hole", "# closed"))

    proved = prove(session, settings, coin_change)

    assert proved.kept and proved.check.verified
    assert proved.source == PROVED
    assert proved.session["status"] == "ok" and proved.session["turns"] == 4
    asked = session.asked[0]
    assert asked.tools == EDIT
    assert "unsolved goals" in asked.prompt
    assert "verify" in asked.prompt and (asked.cwd / "tools").is_file()
    told = " ".join(asked.prompt.split())
    assert "FILE is sent alone" in told and "keeps its working directory" in told


def test_a_loop_annotation_is_the_prover_s_to_change(
    settings: Settings, coin_change: Task
) -> None:
    """Under Velvet the invariants sit inside the implementation's `do` block."""
    session = Writing(
        lambda text: text.replace("# hole", "# closed").replace(
            "invariant(total <= cents)", "invariant(0 <= total and total <= cents)"
        )
    )

    assert prove(session, settings, coin_change).kept


def test_a_changed_specification_is_refused_however_it_checks(
    settings: Settings, coin_change: Task
) -> None:
    session = Writing(lambda text: text.replace("# hole", "# closed").replace(">= 0", ">= -1"))

    proved = prove(session, settings, coin_change)

    assert not proved.kept and proved.source == HOLE
    assert proved.refused == "it changes the specification"


def test_a_changed_implementation_is_refused(settings: Settings, coin_change: Task) -> None:
    session = Writing(
        lambda text: text.replace("# hole", "# closed").replace("total += 1", "total = cents")
    )

    assert prove(session, settings, coin_change).refused == "it changes the implementation"
    prompt = " ".join(session.asked[0].prompt.split())
    assert "and the code of the implementation in `impl`" in prompt


#: A probe: the reference implementation with a claim of its own beside it. Its assertion
#: sits in the implementation region, because that is where a probe goes, so a session asked
#: to prove it has to be allowed to write inside `impl`.
PROBED = HOLE.replace(
    "    return (0, 0, 0, total)\n",
    "    return (0, 0, 0, total)\n\n\nexample : spec 40 (impl 40) := by\n  # hole\n",
)


def test_a_probes_own_claim_is_the_prover_s_to_close(
    settings: Settings, coin_change: Task
) -> None:
    """A probe asserts what the specification says at one input, inside `impl`.

    Held to an implementation byte-identical to the one it was given, no session could ever
    prove one: the goal it has to close is in the region it may not touch.
    """
    session = Writing(lambda text: text.replace("  # hole", "  # closed"))

    proved = prove(session, settings, coin_change, PROBED, "probe")

    assert proved.kept
    assert "# closed" in proved.source
    assert "`example`" in session.asked[0].prompt


def test_a_probe_whose_assertion_the_session_rewrote_is_refused(
    settings: Settings, coin_change: Task
) -> None:
    """It would assert something the case was not offering as evidence."""
    session = Writing(
        lambda text: text.replace("  # hole", "  # closed").replace(
            "example : spec 40 (impl 40)", "example : spec 0 (impl 0)"
        )
    )

    proved = prove(session, settings, coin_change, PROBED, "probe")

    assert proved.refused == "it changes what the implementation's own claims state"


def test_the_rest_of_the_implementation_stays_fixed_around_a_probe(
    settings: Settings, coin_change: Task
) -> None:
    """Only the probe's proof is the session's; the code the probe is about is not."""
    session = Writing(
        lambda text: text.replace("  # hole", "  # closed").replace(
            "total += 1", "total = cents"
        )
    )

    proved = prove(session, settings, coin_change, PROBED, "probe")

    assert proved.refused == "it changes the implementation"


#: A Nagini file with an admissibility probe: a function of its own after the implementation
#: that calls it at a literal input and `Assert`s what the postcondition promises.
NAGINI_PROBE = """\
# benchproofer:begin spec
def spec(cents: int) -> int:
    Requires(cents >= 0)
    Ensures(Result() >= 0)
# benchproofer:end spec

# benchproofer:begin impl
def impl(cents: int) -> int:
    Requires(cents >= 0)
    Ensures(Result() >= 0)
    total = 0
    while total < cents:
        Invariant(total <= cents)
        total += 1
    return total


def admissibility_probe() -> None:
    r = impl(40)
    Assert(r >= 0)
# benchproofer:end impl
"""


@pytest.mark.parametrize(
    ("rewrite", "refused"),
    [
        (
            lambda text: text.replace(
                "    r = impl(40)\n", "    r = impl(40)\n    Assert(r == 40)\n"
            ),
            "",
        ),
        (
            lambda text: text.replace(
                "        Invariant(total <= cents)\n",
                "        Invariant(total <= cents)\n        Invariant(total >= 0)\n",
            ),
            "",
        ),
        (
            lambda text: text.replace("Assert(r >= 0)", "Assert(r >= -1)"),
            "it changes what the implementation's own claims state",
        ),
        (
            lambda text: text.replace("total += 1", "total = cents"),
            "it changes the implementation",
        ),
    ],
    ids=["an-added-assert", "an-added-invariant", "a-rewritten-claim", "a-rewritten-loop"],
)
def test_a_nagini_probe_may_gain_proof_annotations_and_keeps_its_claims(
    settings: Settings, rewrite: Callable[[str], str], refused: str
) -> None:
    """An `Assert` stating a fact the next step needs is the proof's, as an invariant is.

    What the probe asserts of the call stays as written, and the code it calls is fixed.
    """
    nagini = BACKENDS.get("nagini")
    prover = Prover(
        session=Writing(lambda text: text),
        backend=nagini,
        settings=settings,
        workdir=settings.cache_dir,
    )

    assert prover.inadmissible(NAGINI_PROBE, rewrite(NAGINI_PROBE), nagini.probe_claims) == (
        refused
    )


@pytest.mark.parametrize("name", ["nagini", "lean4", "velvet"])
def test_a_proof_session_is_told_how_its_checker_s_proofs_are_written(
    settings: Settings, coin_change: Task, name: str
) -> None:
    """A Nagini session writes annotations, not Lean tactics; a Lean one is told no `sorry`."""
    backend = BACKENDS.get(name)
    session = Writing(lambda text: text)

    prove(session, settings, coin_change, NAGINI_PROBE, "probe", backend)

    system = " ".join(session.asked[0].system.split())
    prompt = " ".join(session.asked[0].prompt.split())
    assert ("native_decide" in system) is (name != "nagini")
    assert ("`Invariant`, an `Assert` stating a fact the next step needs" in system) is (
        name == "nagini"
    )
    assert "is yours, is yours" not in prompt
    claims = " or ".join(f"`{word}`" for word in backend.probe_claims[-1:])
    assert claims in prompt
    if backend.proof_annotations:
        assert "which you may add, change or remove" in prompt


def test_another_checker_s_session_is_told_which_constructs_are_refused(
    settings: Settings, coin_change: Task
) -> None:
    session = Writing(lambda text: text)

    prove(session, settings, coin_change)

    system = " ".join(session.asked[0].system.split())
    assert "with none of `sorry`, which discharge one without establishing it" in system
    assert "native_decide" not in system


@pytest.mark.parametrize(
    ("kind", "said"),
    [
        ("claim", "That its implementation meets its specification on every input"),
        ("probe", "which is a finding about the specification and not about your proof"),
        ("witness", "`fail` says the witness cannot be proved because it is false"),
    ],
)
def test_each_kind_of_proof_session_is_told_what_failing_means(
    settings: Settings, coin_change: Task, kind: ProofKind, said: str
) -> None:
    """A witness claims the implementation is wrong, so its `fail` is the solution's `ok`."""
    session = Writing(lambda text: text)

    prove(session, settings, coin_change, PROBED if kind == "probe" else HOLE, kind)

    prompt = " ".join(session.asked[0].prompt.split())
    assert said in prompt
    assert "what the file claims is false, as above" in prompt


def test_only_a_checker_that_reports_axioms_is_said_to_report_them(
    settings: Settings, coin_change: Task
) -> None:
    """Lean prints them for a named claim only; Velvet and Nagini print no such line."""
    lean = BACKENDS.get("lean4")
    assert "for a proof made of `example`s alone" in " ".join(lean.closure_note.split())
    for name in ("nagini", "velvet"):
        assert BACKENDS.get(name).closure_note == ""
    session = Writing(lambda text: text)

    prove(session, settings, coin_change)

    assert "axioms each" not in " ".join(session.asked[0].prompt.split())


class Probing(Proving):
    """A prover that accepts a file exactly when every hole in it is closed."""

    name = "probing"

    def check(self, source: str, *, workdir: Path, timeout_s: float = 120.0) -> CheckResult:
        if "# hole" in source:
            return CheckResult.no("unsolved goals: spec 40 (impl 40)")
        return CheckResult.ok("elaborated with no errors")


#: The probe a drafter replies with: the reference implementation and a claim beside it.
PROBE_REGION = (
    "# benchproofer:begin impl\n"
    "def impl(cents):\n"
    "    total = 0\n"
    "    while total < cents:\n"
    "        invariant(total <= cents)\n"
    "        total += 1\n"
    "    return (0, 0, 0, total)\n"
    "\n"
    "\n"
    "example : spec 40 (impl 40) := by\n"
    "  # hole\n"
    "# benchproofer:end impl\n"
)


def probed(session: AgentSession, settings: Settings, task: Task) -> Any:
    """Draft one admissibility probe against a checker that refuses an open goal."""
    provider = Scripted(
        {
            "rival": [f"RATIONALE: the probe.\n\n```python\n{PROBE_REGION}```"],
            "retry": ["(none)"],
        }
    )
    return drafter(provider, settings, Probing(), session=session)._variant(
        "rival",
        "admissibility-1",
        "admissibility",
        "Write an admissibility rival.",
        PROVED,
        "",
        Journal(),
        allowed=("impl",),
        task=task,
    )


def test_a_refused_probe_is_handed_to_a_proof_session(
    settings: Settings, coin_change: Task
) -> None:
    """A probe the checker refuses on a step of its own proof is a case it had to accept.

    Its goal is in the implementation region, so the session may prove the probe's
    claims there, provided it states them word for word.
    """
    session = Writing(lambda text: text.replace("  # hole", "  # closed"))

    draft = probed(session, settings, coin_change)

    assert session.asked, "a probe the checker refused got no proof session"
    assert draft is not None and draft.check.verified
    assert "wrote a proof the checker accepts" in draft.proof_session


def test_a_probe_a_session_could_not_close_carries_that_to_the_gate(
    settings: Settings, coin_change: Task
) -> None:
    """The record is what lets the gate tell a gap from a case nobody has tried to prove."""
    session = Writing(lambda text: text.replace("  # hole", "  # hole, still"), status="stuck")

    draft = probed(session, settings, coin_change)

    assert draft is not None and not draft.check.verified
    assert "did not close it" in draft.proof_session


class Replaying(Probing):
    """A checker that replays the proof a file writes, so a refused variant needs a witness."""

    name = "replaying"
    witness_required = True
    witness_placement = "* State it as a claim about `spec` at one input."


#: The pre-fix implementation a drafter replies with: the code before the fix, its proof left
#: open, and a witness whose proof does not close yet either.
TWIN_REPLY = (
    "RATIONALE: it counts one past the amount.\n\n```python\n"
    "# benchproofer:begin impl\n"
    "def impl(cents):\n"
    "    total = 0\n"
    "    while total <= cents:\n"
    "        invariant(total <= cents + 1)\n"
    "        total += 1\n"
    "    return (0, 0, 0, total)\n"
    "# benchproofer:end impl\n"
    "# benchproofer:begin proof\n"
    "# hole\n"
    "# benchproofer:end proof\n"
    "```\n\n```lean\ntheorem twin_wrong : spec 3 (impl 3) = False\n# hole\n```"
)


def test_a_pre_fix_implementation_records_what_the_proof_session_on_its_witness_reported(
    settings: Settings, coin_change: Task, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pre-fix implementation is meant to be refused, so its only session is its witness's.

    What that session reported is recorded with the pre-fix implementation, so the gate that
    reads the witness -- and a redraft sent to answer it -- can see whether its proof was tried.
    """
    # Whether the pre-fix implementation runs as the fixed code does is not this case's
    # question.
    monkeypatch.setattr(variant, "coincides", lambda *_, **__: "")
    session = Writing(lambda text: text.replace("# hole", "# closed"))
    provider = Scripted({"twin": [TWIN_REPLY], "retry": ["(none)"]})
    formalizer = drafter(provider, settings, Replaying(), session=session)

    (draft,) = formalizer._twin(coin_change, PROVED, "", Journal())

    assert "# closed" in draft.witness
    assert "on its refutation witness" in draft.proof_session
    assert "wrote a proof the checker accepts" in draft.proof_session


def test_a_rival_records_what_the_proof_session_on_its_witness_reported(
    settings: Settings, coin_change: Task, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wrong case is meant to be refused, so the only session it has is its witness's.

    The property-based test suite reads the record to tell a witness whose proof is missing a
    step from one nobody tried to prove, as `spec.discriminates` reads the pre-fix
    implementation's.
    """
    monkeypatch.setattr(variant, "coincides", lambda *_, **__: "")
    session = Writing(lambda text: text.replace("# hole", "# closed"))
    provider = Scripted({"rival": [TWIN_REPLY], "retry": ["(none)"]})
    formalizer = drafter(provider, settings, Replaying(), session=session)

    draft = formalizer._variant(
        "rival",
        "uniqueness-1",
        "uniqueness",
        "Write a uniqueness rival.",
        PROVED,
        "",
        Journal(),
        allowed=variant.owned(PROVED, Replaying()),
        task=coin_change,
    )

    assert draft is not None and "# closed" in draft.witness
    assert "on its refutation witness" in draft.proof_session
    assert "wrote a proof the checker accepts" in draft.proof_session


class Unreachable(AgentSession):
    """A session the provider cannot start at all, as an expired credential leaves it."""

    name = "unreachable"

    def run(self, spec: SessionSpec) -> StepOutcome:
        raise ProviderError("the credential expired")


class Broken(AgentSession):
    """A session that failed over this file rather than over reaching the provider."""

    name = "broken"

    def run(self, spec: SessionSpec) -> StepOutcome:
        raise BundleError("the workspace holds no solution file")


def test_a_session_that_cannot_be_started_is_the_provider_s_failure(
    settings: Settings, coin_change: Task
) -> None:
    """Nothing about the file was read, so there is no proof that failed to be found.

    Recorded as a refusal it is charged to the file, and a run whose credential expired
    spends every repair it has on a path that asked nothing.
    """
    with pytest.raises(ProviderError):
        prove(Unreachable(), settings, coin_change)


def test_a_session_that_failed_over_the_file_is_still_a_refusal(
    settings: Settings, coin_change: Task
) -> None:
    """The file is what it could not be run on, so the file is what it is reported against."""
    proved = prove(Broken(), settings, coin_change)

    assert not proved.kept
    assert "the session could not run" in proved.refused


def test_a_proof_session_writes_its_own_files_under_a_scratch_directory(
    settings: Settings, coin_change: Task
) -> None:
    """The checker's workspace is shared between runs, so nothing of its own goes there."""
    session = Writing(lambda text: text.replace("# hole", "# closed"))

    prove(session, settings, coin_change)

    asked = session.asked[0]
    assert (asked.cwd / "scratch").is_dir()
    assert "`scratch/`" in asked.prompt


def test_a_banned_token_is_refused(settings: Settings, coin_change: Task) -> None:
    session = Writing(lambda text: text.replace("# hole", "# closed\nsorry"))

    assert prove(session, settings, coin_change).refused == "it uses `sorry`"


def test_a_proof_the_checker_still_refuses_is_not_kept(
    settings: Settings, coin_change: Task
) -> None:
    session = Writing(lambda text: text.replace("# hole", "# tried"), status="stuck")

    proved = prove(session, settings, coin_change)

    assert not proved.kept and proved.source == HOLE
    assert "still refuses" in proved.refused
    assert proved.session["status"] == "stuck"


class Drafting(Writing):
    """A session that drafts `HOLE` when asked for a solution, then proves as `Writing` does."""

    name = "drafting"

    def run(self, spec: SessionSpec) -> StepOutcome:
        if spec.submit != "draft":
            return super().run(spec)
        self.asked.append(spec)
        write_text(next(spec.cwd.glob("bundles/**/solution.*")), HOLE)
        payload = {"status": "BLOCKED", "summary": "one step of the loop would not close"}
        return StepOutcome(text="", payload=payload, turns=30, tool_uses=40)


def test_drafting_hands_a_refused_solution_to_the_prover(
    settings: Settings, coin_change: Task
) -> None:
    """The drafting session's file too: under a prover a refusal is often a proof short a step.

    And the proof session holds the specification fixed, which the drafting one does not.
    """
    session = Drafting(lambda text: text.replace("# hole", "# closed"))
    # The script's rivals are bodies alone, which a backend whose cases carry their proofs
    # sends back; what they become is not what this case is about.
    provider = Scripted({**script(), "retry": ["(none)"]})

    result = drafter(provider, settings, Proving(), session=session).run(coin_change)

    assert [spec.submit for spec in session.asked[:2]] == ["draft", "proof"]
    assert result.accepted and "# closed" in result.solution
    assert any("a proof session" in note and "was kept" in note for note in result.notes)


def test_a_session_script_carries_the_backend_s_environment(
    settings: Settings, coin_change: Task, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where a backend's workspace is lives outside the settings; the tools need it too."""
    monkeypatch.setenv("BENCHPROOFER_VELVET", "/opt/velvet/workspace")
    session = Writing(lambda text: text)

    prove(session, settings, coin_change)

    script = read_text(session.asked[0].cwd / "tools")
    (named,) = re.findall(r"^\. (\S+)$", script, re.MULTILINE)
    assert "BENCHPROOFER_VELVET=/opt/velvet/workspace" in read_text(Path(named))
    assert "/opt/velvet/workspace" not in script


def test_a_session_workspace_is_laid_out_afresh_each_time(
    settings: Settings, coin_change: Task
) -> None:
    """A proof, a repair and a drafting session each start from the same layout.

    Nothing an earlier session left survives into the next one's workspace: a probe of its
    own would read as part of the bundle.
    """
    root = settings.cache_dir / "workspace"
    lay_out(root, coin_change, "accepting", settings)
    write_text(root / "scratch" / "left.py", "")

    copy = lay_out(root, coin_change, "accepting", settings)

    assert copy.root == root / "bundles" / coin_change.benchmark / "coin-change" / "accepting"
    assert copy.task().key == coin_change.key
    assert [path.name for path in (root / "scratch").iterdir()] == []
    assert "benchproofer.audit.tools --bundle " + copy.root.as_posix() in read_text(
        root / "tools"
    )


#: A rival of `HOLE`, and a refutation witness for it whose proof does not close yet.
RIVAL = HOLE.replace("total += 1", "total += 2")
WITNESS = "theorem wrong_at_three : spec 3 (impl 3) = False\n# hole"


def prove_witness(
    session: AgentSession, settings: Settings, task: Task, claim: str = WITNESS
) -> tuple[str, Journal, str]:
    """Hand the refutation witness ``claim`` of `RIVAL` to `_prove_witness`."""
    formalizer = drafter(Scripted({}), settings, Proving(), session=session)
    journal = Journal()
    proved, tried = formalizer._prove_witness(
        task, RIVAL, claim, journal, label="rival-uniqueness-1", accepted=PROVED
    )
    return proved, journal, tried


def test_a_witness_whose_proof_does_not_close_goes_to_a_proof_session(
    settings: Settings, coin_change: Task
) -> None:
    """Its statement is held as written; its proof is the session's to write."""
    session = Writing(lambda text: text.replace("# hole", "# closed"))

    claim, journal, tried = prove_witness(session, settings, coin_change)

    assert claim == WITNESS.replace("# hole", "# closed")
    # What the session did is returned as well, for a variant that records it: the pre-fix
    # implementation.
    assert "wrote a proof the checker accepts" in tried
    assert "refutation witness" in session.asked[0].prompt
    assert any("was kept" in note for note in journal.notes)


def test_a_witness_whose_statement_the_session_changed_is_not_kept(
    settings: Settings, coin_change: Task
) -> None:
    session = Writing(
        lambda text: text.replace("# hole", "# closed").replace("impl 3", "impl 4")
    )

    claim, journal, tried = prove_witness(session, settings, coin_change)

    assert claim == WITNESS
    assert any("changed what the witness states" in note for note in journal.notes)
    assert "changed what the witness states" in tried


def test_a_witness_that_already_holds_is_left_alone(
    settings: Settings, coin_change: Task
) -> None:
    session = Writing(lambda text: text)
    closed = WITNESS.replace("# hole", "# closed")

    claim, _, tried = prove_witness(session, settings, coin_change, closed)

    assert (claim, tried) == (closed, "")
    assert session.asked == []


def test_a_witness_the_gates_refuse_before_building_it_gets_no_proof_session(
    settings: Settings, coin_change: Task
) -> None:
    """No proof makes a hypothesis the gate refuses one it admits, so none is spent on it."""
    session = Writing(lambda text: text.replace("# hole", "# closed"))
    assuming = (
        "theorem wrong_at_three (h : impl 3 = (0, 0, 0, 4)) : spec 3 (impl 3) = False\n# hole"
    )

    claim, journal, tried = prove_witness(session, settings, coin_change, assuming)

    assert (claim, tried) == (assuming, "")
    assert session.asked == []
    assert any(
        "refuse before building it" in note and "the witness binds (h : impl 3" in note
        for note in journal.notes
    )
