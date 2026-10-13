# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What every auditor shares, apart from the sessions that ask it.

The review is the one place a model's own claims enter a bundle, so what is worth pinning
here is what the auditors are held to whichever of them asks: the system prompt each is
given, what each judged role reads and so when its judgment expires, who counts as an
independent reviewer, what the equivalence auditor is shown a repair changed, and what the
notes say of the submissions on record. The auditors themselves are pinned in
`test_audit_agents.py`.

Nothing here reaches a real checker, an oracle, or a network.
"""

from __future__ import annotations

import pytest

from benchproofer.audit import prompts
from benchproofer.audit.session import (
    JUDGED_ROLES,
    LANES,
    ROLE_READS,
    Audit,
    Filed,
    _stamped,
    _system,
    added_block,
    admitted,
    roles_for,
)
from benchproofer.backends.base import Backend
from benchproofer.core.bundle import Bundle, Judgment, Review, Submission
from benchproofer.core.prompts import SHARED
from benchproofer.core.readings import IMPL, SPEC, SPEC_UNCOMMENTED, TWINS, readings
from benchproofer.core.task import Reference, Task
from benchproofer.core.verdict import Status, Verdict
from benchproofer.pipeline.audit import write_audit
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import read_text, write_text
from doubles import Answering


def narrowed_since_drafting(bundle: Bundle, backend: Backend) -> None:
    """Record the bundle as drafted, then add a precondition and an `Outside the bridge` entry.

    As a repair session that narrowed without saying so would leave it.
    """
    manifest = bundle.manifest()
    manifest.provenance = {**manifest.provenance, "drafted": admitted(bundle, backend)}
    bundle.save_manifest(manifest)
    assert added_block(bundle, backend) == ""
    solution = bundle.solution()
    write_text(
        bundle.solution_path,
        solution.replace(
            "def property_change_uses_no_negative_coin(cents):\n",
            "def property_change_uses_no_negative_coin(cents):\n    assume(cents < 100)\n",
        ),
    )
    write_text(
        bundle.correspondence_path,
        read_text(bundle.correspondence_path)
        + "\n## Outside the bridge\n\n* an amount of a dollar or more\n",
    )


@pytest.mark.parametrize("current", [True, False], ids=["current", "since changed"])
def test_the_equivalence_auditor_is_shown_what_conformance_py_skipped_for_an_entry(
    current: bool, sound: Bundle
) -> None:
    """It traces each such input, as it checks the entry the declaration quotes."""
    line = (
        "benchproofer:inadmissible change.make_change 0: Outside the bridge: a negative "
        "amount, on which make_change raises before any line the patch changes"
    )
    manifest = sound.manifest()
    recorded = Verdict(gate="impl.conformance", status=Status.PASS, details={"outside": [line]})
    if not current:
        recorded.inputs = {f"{sound.root.name}/conformance.py": "an earlier digest"}
    manifest.verdicts = {**manifest.verdicts, recorded.gate: recorded}
    sound.save_manifest(manifest)

    shown = added_block(sound, Answering())

    assert (f"* {line}" in shown) is current
    assert (
        "trace the input through the function before the fix and after it" in shown
    ) is current


def test_every_auditor_is_told_a_broken_language_contract_is_no_evidence_either_way() -> None:
    """Stated once, in the system prompt every auditor shares, so no auditor goes without it.

    So is an attack that fails only through a method a test replaces on the object itself.
    """
    systems = [" ".join(_system(Answering(), lane).split()) for lane in LANES]
    for told in (
        "breaks a language contract is no evidence either way",
        "whose patch fails only through that replacement, shows a call the model does not "
        "represent, not a wrong result: it is no evidence that the specification is too weak",
    ):
        assert all(told in system for system in systems)
    assert "$review" in prompts.template("agent-system")


def test_a_reviewer_is_told_what_an_accepting_verdict_from_this_checker_is_worth() -> None:
    """An attack that outlasted a search budget is a different finding from a proof."""
    for lane in LANES:
        system = _system(Answering(), lane)
        assert "search budget" in system and "falsifier" in system


def test_the_fuzz_auditor_is_told_to_call_the_callee_as_the_task_does() -> None:
    """A call the task never makes refutes nothing the specification relies on.

    Neither does a pair of calls with the world changed between them, so what the call
    site fixes -- its other arguments, and the process and file system it runs in -- is
    what the reviewer is told to leave alone. What reaches outside the process may be
    stubbed as the repository's tests stub it, as `conformance.py` may.
    """
    assert "$fuzz_rules" in prompts.template("agent-fuzz")
    rules = " ".join(prompts.LIBRARY.rules("fuzz").split())
    assert "Call the callee the way the task's code calls it" in rules
    assert "hold fixed everything that call site fixes" in rules
    assert "file system" in rules
    assert "not the state of an object you pass to both" in rules
    assert "such as a request context or a site object a running server sets" in rules
    assert "the stub changes nothing the call reads" in rules


def test_a_refuting_input_is_of_the_declared_type_and_no_state_the_tests_never_build() -> None:
    """Nor an interpreter's limit, nor what earlier calls left behind; a raise still refutes.

    The rule on what earlier calls in the same process left behind is stated once, in the
    environment rules the fuzz and equivalence rules both include.
    """
    fuzz = " ".join(prompts.LIBRARY.rules("fuzz").split())
    assert "Each input is of the type the call site declares" in fuzz
    assert "a FAIL_TO_PASS test or a PASS_TO_PASS test the test patch adds or edits" in fuzz
    assert "`bool` is not `int` and `float` is not `int`" in fuzz
    assert "short of the interpreter's own limits" in fuzz
    assert "the limit on the digits of an int converted to a str" in fuzz
    assert "the wrong type wherever a call site can pass one" not in fuzz
    assert "a raise of the real callee where the assumption says it returns refutes" in fuzz
    assert (
        "An input on which the real callee does not return at all -- it runs without end, or "
        "for longer than any of the benchmark's tests waits -- refutes nothing where, as a "
        "result, the function the fix changes does not return either"
    ) in fuzz
    environment = " ".join(SHARED.template("environment-rules").split())
    assert "a state of the environment the benchmark's tests never build" in environment
    assert "a special file such as a FIFO or a device" in environment
    left = "what earlier calls in the same process left behind"
    equivalence = " ".join(prompts.LIBRARY.rules("equivalence").split())
    assert left in environment and fuzz.count(left) == equivalence.count(left) == 1
    assert left not in " ".join(prompts.template("equivalence-rules").split())


def test_state_the_tests_set_between_calls_is_an_input_every_program_may_set() -> None:
    """The environment rule and the fuzz rule beside it read one way.

    An option a test sets through a context manager is varied as the tests vary it, so a
    fuzzer that sets it between two calls compares two inputs, and the model takes it as a
    parameter.
    """
    environment = " ".join(SHARED.template("environment-rules").split())
    assert (
        "State the benchmark's tests set between calls -- an option such as one set through "
        "a `set_options` context manager, or a setting a test overrides -- is an input of the "
        "call: the model takes it as a parameter, and a program may set it between calls the "
        "way the tests do."
    ) in environment
    fuzz = " ".join(prompts.LIBRARY.rules("fuzz").split())
    assert "set it between your calls the way the tests do" in fuzz


def test_each_judged_role_reads_what_its_question_is_about() -> None:
    """This is what lets a narrow repair expire the judgments it actually affects."""
    reads = {role: set(ROLE_READS[role]) for role in JUDGED_ROLES}
    assert SPEC_UNCOMMENTED in reads["faithfulness"] & reads["equivalence"]
    assert SPEC in reads["disclosure"]
    assert "correspondence.md" in reads["equivalence"] & reads["faithfulness"]
    assert "conformance.py" in reads["faithfulness"] & reads["equivalence"]
    assert "axioms.py" in reads["equivalence"] - reads["faithfulness"]
    assert {"correspondence.md", "conformance.py", "axioms.py"}.isdisjoint(reads["disclosure"])
    assert IMPL in reads["equivalence"]
    assert IMPL not in reads["faithfulness"] | reads["disclosure"]
    assert TWINS in reads["faithfulness"]


def test_a_changed_pre_fix_implementation_expires_only_the_faithfulness_judgment(
    sound: Bundle,
) -> None:
    """The faithfulness auditor reads what the pre-fix implementation returns on each test."""
    backend = BACKENDS.get("falsifier")
    digests = readings(sound, backend)
    judgments = [
        _stamped(Judgment(role=role, verdict="sound", summary="fine"), digests)
        for role in JUDGED_ROLES
    ]
    for judgment in judgments:
        assert set(judgment.reads) == set(ROLE_READS[judgment.role]) & set(digests)
    write_text(sound.twins_dir / "added.py", "def f():\n    return 0\n")

    digests = readings(sound, backend)
    stale = {judgment.role for judgment in judgments if judgment.stale(digests)}
    assert stale == {"faithfulness"}


def test_a_changed_axioms_py_expires_only_the_equivalence_judgment(sound: Bundle) -> None:
    """The equivalence auditor checks that a repair did not make the programs compare less."""
    backend = BACKENDS.get("falsifier")
    write_text(sound.root / "axioms.py", "print('benchproofer:grounded c')\n")
    digests = readings(sound, backend)
    judgments = [
        _stamped(Judgment(role=role, verdict="sound", summary="fine"), digests)
        for role in JUDGED_ROLES
    ]
    write_text(sound.root / "axioms.py", "print('benchproofer:grounded d')\n")

    digests = readings(sound, backend)
    stale = {judgment.role for judgment in judgments if judgment.stale(digests)}
    assert stale == {"equivalence"}


def test_a_task_with_no_golden_patch_is_not_asked_the_equivalence_question(
    coin_change: Task,
) -> None:
    """An unjudged role is reported as unjudged; asking would invite a guess."""
    unanswered = coin_change.model_copy(update={"reference": Reference()})

    assert roles_for(unanswered) == ("faithfulness", "disclosure")
    assert roles_for(coin_change) == JUDGED_ROLES


@pytest.mark.parametrize(
    ("author", "independent"),
    [("scripted:drafting-model", True), ("scripted:reviewing-model", False), ("", False)],
    ids=["another-model", "the-same-model", "no-author-recorded"],
)
def test_a_review_is_independent_only_of_a_bundle_another_model_drafted(
    author: str, independent: bool
) -> None:
    """A bundle from elsewhere need not say who wrote it, and then claims no independence."""
    audit = Audit(
        task_key="demo/coin-change",
        backend="falsifier",
        provider="scripted",
        model="reviewing-model",
        author=author,
    )

    assert audit.reviewer == "scripted:reviewing-model"
    assert audit.independent is independent
    assert audit.review().independent is independent


# ---- what the review notes say of the submissions on record ---------------


def test_the_notes_tell_a_kept_claim_from_one_this_review_filed(sound: Bundle) -> None:
    """While the specification it attacked stands, a kept claim is about it too."""
    spec = readings(sound, BACKENDS.get(sound.backend_name))[SPEC]
    audit = Audit(
        task_key="demo/coin-change",
        backend=sound.backend_name,
        provider="provider",
        model="reviewing-model",
        kept=(Submission(id="attack-1", file="attack-1.py", claim="it stops early"),),
        submissions=(
            Filed(
                id="attack-2",
                kind="weakness",
                claim="pennies only",
                file="attack-2.py",
                source="",
            ),
        ),
        examined={"attack": {SPEC: spec}},
    )

    write_audit(sound, audit)

    notes = (sound.audit_dir / "notes.md").read_text()
    assert "- `attack-1` (weakness, filed by an earlier review): it stops early" in notes
    assert "- `attack-2` (weakness): pennies only" in notes


def test_the_notes_mark_a_claim_filed_against_an_earlier_specification(sound: Bundle) -> None:
    """Printed as current, it would describe a specification the bundle no longer ships.

    That is what is kept where the attack auditor filed nothing after a repair changed what it
    had attacked.
    """
    audit = Audit(
        task_key="demo/coin-change",
        backend=sound.backend_name,
        provider="provider",
        model="reviewing-model",
        kept=(Submission(id="attack-1", file="attack-1.py", claim="it stops early"),),
        examined={"attack": {SPEC: "an earlier digest"}},
    )

    write_audit(sound, audit)

    notes = (sound.audit_dir / "notes.md").read_text()
    assert (
        "- `attack-1` (weakness, filed against an earlier specification, which its claim is "
        "about): it stops early"
    ) in notes


def test_a_review_that_replaced_a_submission_removes_its_files(sound: Bundle) -> None:
    """What it filed is in the archive of the round that judged it, not in this review."""
    earlier = Submission(id="attack-1", file="attack-1.py", shadow="attack-1.patch")
    sound.save_audit(
        Review(reviewer="provider:reviewing-model", submissions=(earlier,)),
        {"attack-1.py": "def impl(cents):\n    return ()\n", "attack-1.patch": "--- a\n"},
    )
    audit = Audit(
        task_key="demo/coin-change",
        backend=sound.backend_name,
        provider="provider",
        model="reviewing-model",
        submissions=(
            Filed(id="attack-2", kind="weakness", claim="", file="attack-2.py", source="x\n"),
        ),
    )

    write_audit(sound, audit)

    assert sorted(path.name for path in sound.audit_dir.iterdir()) == [
        "attack-2.py",
        "index.toml",
        "notes.md",
    ]
