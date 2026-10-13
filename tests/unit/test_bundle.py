# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The bundle on disk: layout, frozen inputs, and `manifest.json`."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from benchproofer.config import Settings
from benchproofer.core.bundle import (
    REWRITTEN,
    Bundle,
    Fuzzer,
    Judgment,
    Operation,
    Review,
    Rival,
    Ruling,
    Submission,
    Twin,
    freeze_task,
)
from benchproofer.core.task import Task
from benchproofer.core.verdict import Status, Verdict
from benchproofer.errors import BundleError
from benchproofer.util.digest import digest_text
from benchproofer.util.fsio import read_json, read_text, write_text


def build(settings: Settings, task: Task, backend: str = "falsifier") -> Bundle:
    bundle = Bundle.create(settings.bundle_root, task, backend)
    write_text(bundle.root / "solution.py", "# benchproofer:begin spec\n")
    return bundle


def test_the_layout_is_benchmark_task_backend(settings: Settings, coin_change: Task) -> None:
    bundle = Bundle.create(settings.bundle_root, coin_change, "falsifier")

    assert (
        bundle.root
        == settings.bundle_root / coin_change.benchmark / "coin-change" / "falsifier"
    )
    assert bundle.root.is_dir()
    assert bundle.task_path.is_file()
    assert bundle.evidence_dir.is_dir()
    assert bundle.backend_name == "falsifier"


def test_the_frozen_task_is_shared_by_every_backend(
    settings: Settings, coin_change: Task
) -> None:
    first = Bundle.create(settings.bundle_root, coin_change, "falsifier")
    second = Bundle.create(settings.bundle_root, coin_change, "dafny")

    assert first.task_path == second.task_path
    assert first.task().digest() == coin_change.digest()


def test_freezing_again_leaves_a_judged_task_alone(
    settings: Settings, coin_change: Task
) -> None:
    """Re-ingesting must not swap the inputs under a bundle that was judged."""
    directory = freeze_task(settings.bundle_root, coin_change)
    edited = coin_change.model_copy(update={"statement": "something else"})

    freeze_task(settings.bundle_root, edited)
    assert read_json(directory / "task.json")["statement"] == coin_change.statement

    freeze_task(settings.bundle_root, edited, refresh=True)
    assert read_json(directory / "task.json")["statement"] == "something else"


def test_recording_a_verdict_preserves_the_ones_already_there(
    settings: Settings, coin_change: Task
) -> None:
    bundle = build(settings, coin_change)

    bundle.record([Verdict(gate="spec.hygiene", status=Status.PASS, summary="first")])
    bundle.record([Verdict(gate="spec.verifies", status=Status.FAIL, summary="second")])

    ledger = bundle.manifest()
    assert set(ledger.verdicts) == {"spec.hygiene", "spec.verifies"}
    assert ledger.verdicts["spec.hygiene"].summary == "first"
    assert ledger.artifacts["solution.py"]
    assert ledger.artifacts["../task.json"]


def test_a_manifest_is_synthesized_from_the_task_when_none_was_written(
    settings: Settings, coin_change: Task
) -> None:
    bundle = build(settings, coin_change)

    ledger = bundle.manifest()

    assert not bundle.manifest_path.exists()
    assert ledger.benchmark == coin_change.benchmark
    assert ledger.task_id == coin_change.task_id
    assert ledger.task_digest == coin_change.digest()
    assert ledger.verdicts == {}


def test_two_bundle_roots_do_not_share_a_scratch_directory(
    settings: Settings, coin_change: Task, tmp_path: Path
) -> None:
    """Two roots easily hold the same benchmark, task, and backend."""
    here = build(settings, coin_change)
    there = build(
        settings.model_copy(update={"bundle_root": tmp_path / "elsewhere"}), coin_change
    )

    assert here.root != there.root
    assert here.scratch(settings.cache_dir) != there.scratch(settings.cache_dir)
    assert here.scratch(settings.cache_dir) == here.scratch(settings.cache_dir)
    assert here.scratch(settings.cache_dir, "verify").is_dir()


@pytest.mark.parametrize(
    "leftover",
    [
        lambda bundle, settings: bundle.scratch(settings.cache_dir, "verify") / "output.txt",
        lambda bundle, settings: bundle.root / "__pycache__" / "shadow.cpython-311.pyc",
    ],
    ids=["checker-scratch", "bytecode"],
)
def test_what_a_judged_run_leaves_behind_is_not_an_artifact(
    leftover: Callable[[Bundle, Settings], Path], settings: Settings, coin_change: Task
) -> None:
    """Scratch lives outside the bundle; bytecode would tie manifest.json to an interpreter."""
    bundle = build(settings, coin_change)
    write_text(leftover(bundle, settings), "noise\n")

    assert bundle.artifact_digests().keys() == {
        "solution.py",
        "../task.json",
        "../reference.patch",
    }


def test_a_property_based_test_suite_round_trips_through_its_manifest(
    settings: Settings, coin_change: Task
) -> None:
    bundle = build(settings, coin_change)
    rival = Rival(
        id="uniqueness-1",
        kind="uniqueness",
        expect="refute",
        file="uniqueness-1.py",
        rationale='hands out no nickel, the bug the task is about ("40 cents")',
    )

    bundle.save_battery([(rival, "def impl(cents):\n    return ()\n")])

    # The digest is the file's, taken as it is written, so the record always says which
    # file its rationale was about.
    (read,) = bundle.battery()
    assert read == rival.model_copy(update={"digest": read.digest})
    assert read.digest == digest_text("def impl(cents):\n    return ()\n")
    assert bundle.rival_source(rival).startswith("def impl")


def test_a_review_round_trips_through_its_index(settings: Settings, coin_change: Task) -> None:
    """The index is the only record of a review, so everything a gate reads survives it."""
    bundle = build(settings, coin_change)
    review = Review(
        reviewer="model:reviewing",
        author="model:drafting",
        submissions=(
            Submission(
                id="attack-1",
                file="attack-1.py",
                claim="pennies only",
                test="attack-1.test.py",
                cites="test_forty_cents",
            ),
            Submission(
                id="control-1",
                file="control-1.py",
                shadow="control-1-shadow.py",
                claim="largest coin first",
                kind="control",
                refutation="example : ¬ spec 40 (impl 40) := by decide",
            ),
        ),
        rulings=(
            Ruling(
                id="attack-1",
                ruling="succeeds",
                input="make_change(40)",
                rests_on='"the change for 40 cents is a quarter, a dime and a nickel"',
                why="the fixed code returns a nickel there",
                asked=2,
                reads={"solution:spec-without-comments": "sha256:def"},
            ),
        ),
        judgments=(
            Judgment(
                role="equivalence",
                verdict="sound",
                summary="the same computation, written differently",
                operations=(
                    Operation(kind="identical", detail="one subtotal instead of four"),
                    Operation(kind="refinement", detail="a nat where the patch takes an int"),
                ),
                reads={"solution.py": "sha256:abc"},
            ),
        ),
    )

    bundle.save_audit(
        review,
        {
            "attack-1.py": "def impl(cents):\n    return ()\n",
            "control-1.py": "def impl(cents):\n    return ()\n",
            "control-1-shadow.py": "def make_change(cents):\n    return ()\n",
            "attack-1.test.py": "assert True\n",
        },
    )

    read = bundle.audit()
    assert read is not None
    assert (read.submissions[0].test, read.submissions[0].cites) == (
        "attack-1.test.py",
        "test_forty_cents",
    )
    assert bundle.submission_test(read.submissions[0]) == "assert True\n"
    assert bundle.submission_test(read.submissions[1]) is None
    assert read.submissions[1].refutation.strip() == review.submissions[1].refutation
    assert [(row.id, row.kind) for row in read.submissions] == [
        ("attack-1", "weakness"),
        ("control-1", "control"),
    ]
    assert read.rulings == review.rulings
    assert read.ruling("attack-1") == review.rulings[0] and read.ruling("control-1") is None
    assert read.judgments[0].operations == review.judgments[0].operations
    assert read.judgments[0].reads == {"solution.py": "sha256:abc"}
    assert bundle.submission_source(read.submissions[0]).startswith("def impl")
    assert bundle.submission_shadow(read.submissions[0]) is None
    assert (
        bundle.submission_shadow(read.submissions[1])
        == "def make_change(cents):\n    return ()\n"
    )


def test_the_programs_a_review_wrote_against_an_assumption_round_trip_too(
    settings: Settings, coin_change: Task
) -> None:
    """A gate needs a fuzzer's program and the callee it attacks."""
    bundle = build(settings, coin_change)
    fuzzer = Fuzzer(
        id="fuzz-1",
        file="fuzz-1.fuzz.py",
        callee="json.loads",
        claim="a trailing space parses, which the model calls malformed",
    )

    bundle.save_audit(
        Review(reviewer="model:reviewing", fuzzers=(fuzzer,)),
        {"fuzz-1.fuzz.py": "raise SystemExit(0)\n"},
    )

    read = bundle.audit()
    assert read is not None
    assert read.fuzzers == (fuzzer,)
    assert bundle.fuzzer_source(read.fuzzers[0]) == "raise SystemExit(0)\n"


@pytest.mark.parametrize(
    "recorded",
    [
        "",
        'changed = "loads now rejects a trailing comma"\n',
        'changed = true\nhow = "loads now rejects a trailing comma"\n',
    ],
    ids=["nothing recorded", "the reviewer's text", "a flag and its reason"],
)
def test_a_fuzzer_recorded_with_keys_nothing_reads_reads_as_its_program(
    recorded: str, settings: Settings, coin_change: Task
) -> None:
    """Whether the patch changes the callee, and why, are read past."""
    bundle = build(settings, coin_change)
    write_text(
        bundle.audit_dir / "index.toml",
        'schema_version = 1\n\n[[fuzzers]]\nid = "fuzz-1"\nfile = "fuzz-1.fuzz.py"\n'
        f'callee = "json.loads"\n{recorded}',
    )

    read = bundle.audit()

    assert read is not None
    assert read.fuzzers == (Fuzzer(id="fuzz-1", file="fuzz-1.fuzz.py", callee="json.loads"),)


def test_a_submission_recorded_with_a_proof_session_s_report_reads_as_its_files(
    settings: Settings, coin_change: Task
) -> None:
    """What a proof session on a refused control reported, and its witness, go unread."""
    bundle = build(settings, coin_change)
    write_text(
        bundle.audit_dir / "index.toml",
        'schema_version = 1\n\n[[submissions]]\nid = "control-1"\nkind = "control"\n'
        'file = "control-1.py"\nproof_session = "a proof session reported stuck"\n'
        'witness = """example : True := trivial"""\n',
    )

    read = bundle.audit()

    assert read is not None
    assert read.submissions == (
        Submission(id="control-1", file="control-1.py", kind="control"),
    )


def test_a_review_naming_a_file_it_did_not_write_says_which(
    settings: Settings, coin_change: Task
) -> None:
    """A review missing the implementation it submitted is not evidence about anything."""
    bundle = build(settings, coin_change)
    submission = Submission(id="attack-1", file="attack-1.py", claim="pennies only")
    bundle.save_audit(Review(reviewer="model:reviewing", submissions=(submission,)), {})

    with pytest.raises(BundleError, match="submission 'attack-1' names a missing file"):
        bundle.submission_source(submission)


def test_a_rival_that_states_the_wrong_expectation_is_refused() -> None:
    """A uniqueness case that expects the verifier to succeed proves nothing."""
    with pytest.raises(ValueError, match="expect='refute'"):
        Rival(
            id="uniqueness-1",
            kind="uniqueness",
            expect="verify",
            file="uniqueness-1.py",
            rationale="wrong on purpose",
        )


def test_the_index_says_what_a_case_found_and_not_only_what_it_expected(
    settings: Settings, coin_change: Task
) -> None:
    """A correct case the checker refused reads like one it accepted under `expect` alone."""
    bundle = build(settings, coin_change)
    gap = Rival(
        id="soundness-1",
        kind="soundness",
        expect="verify",
        file="soundness-1.py",
        rationale="the same answer by a loop",
        proof_session="a proof session reported stuck",
        found="verify: unproved",
    )

    bundle.save_battery([(gap, "def impl(cents):\n    return ()\n")])

    assert 'found = "verify: unproved"' in read_text(bundle.rivals_dir / "index.toml")
    assert bundle.battery()[0].found == "verify: unproved"


def test_a_malformed_property_based_test_suite_is_an_error_rather_than_no_cases(
    settings: Settings, coin_change: Task
) -> None:
    bundle = build(settings, coin_change)
    write_text(bundle.rivals_dir / "index.toml", "rival = 3\n")

    with pytest.raises(BundleError, match="array of tables"):
        bundle.battery()


def test_an_empty_property_based_test_suite_reads_as_no_cases(
    settings: Settings, coin_change: Task
) -> None:
    assert build(settings, coin_change).battery() == []


#: A pre-fix implementation with a refutation witness, as a checker that replays a proof needs
#: one.
WITNESSED = Twin(
    id="twin",
    file="twin.py",
    rationale="it never hands out a nickel",
    witness='example : ¬ Spec 40 (impl 40) := by\n  unfold Spec impl\n  decide  -- "40"\n',
    proof_session="twin: a proof session on its refutation witness (3 turn(s)) wrote a proof",
)


def test_a_pre_fix_implementation_s_witness_round_trips_through_its_index(
    settings: Settings, coin_change: Task
) -> None:
    """The file is the pre-fix implementation; the index, not read off it, is not one."""
    bundle = build(settings, coin_change)

    source = "def impl(cents):\n    return (0, 0, 0, cents)\n"
    bundle.save_twins([(WITNESSED, source)])

    assert bundle.twin_cases() == {
        "twin": WITNESSED.model_copy(update={"digest": digest_text(source)})
    }
    assert bundle.twins_index.is_file()
    assert [name for name, _ in bundle.twins()] == ["twin"]


def test_a_rationale_about_a_file_a_session_replaced_is_not_read_as_about_this_one(
    settings: Settings, coin_change: Task
) -> None:
    """A session that edits a case's file does not rewrite what the index says about it.

    Left standing, the rationale and the outcome send a reviewer and a repair after a
    mistake nothing in the bundle makes, so the digest the record was written against is
    what decides whether either still speaks.
    """
    bundle = build(settings, coin_change)
    bundle.save_twins([(WITNESSED, "def impl(cents):\n    return (0, 0, 0, cents)\n")])

    write_text(bundle.twins_dir / "twin.py", "def impl(cents):\n    return (1, 0, 0, 0)\n")

    ((name, _),) = bundle.twins()
    replaced = bundle.twin_cases()[name]
    assert replaced.rationale == REWRITTEN
    assert replaced.found == ""
    # What the file itself does not say is still read: the witness is a claim about the
    # specification rather than about which mistake the file makes.
    assert replaced.witness == WITNESSED.witness


def test_pre_fix_implementations_that_carry_nothing_but_their_file_are_written_without_an_index(
    settings: Settings, coin_change: Task
) -> None:
    """Pre-fix implementations with no witness and no proof record need no index."""
    bundle = build(settings, coin_change)
    bundle.save_twins([(WITNESSED, "def impl(cents):\n    return ()\n")])

    bundle.save_twins([(Twin(id="twin", file="twin.py"), "def impl(cents):\n    return ()\n")])

    assert not bundle.twins_index.exists()
    assert bundle.twin_cases() == {"twin": Twin(id="twin", file="twin.py")}


def test_a_pre_fix_implementation_the_index_does_not_list_is_still_a_pre_fix_implementation(
    settings: Settings, coin_change: Task
) -> None:
    """A pre-fix implementation the index does not list, as a repair may add, still counts."""
    bundle = build(settings, coin_change)
    write_text(bundle.twins_dir / "twin.py", "def impl(cents):\n    return ()\n")

    assert bundle.twin_cases() == {"twin": Twin(id="twin", file="twin.py")}


def test_a_malformed_twins_index_is_an_error_rather_than_no_witness(
    settings: Settings, coin_change: Task
) -> None:
    bundle = build(settings, coin_change)
    write_text(bundle.twins_dir / "twin.py", "def impl(cents):\n    return ()\n")
    write_text(bundle.twins_index, "twin = 3\n")

    with pytest.raises(BundleError, match="array of tables"):
        bundle.twin_cases()


def test_an_ambiguous_solution_file_is_refused(settings: Settings, coin_change: Task) -> None:
    bundle = build(settings, coin_change)
    write_text(bundle.root / "solution.dfy", "// two languages in one bundle\n")

    with pytest.raises(BundleError, match="multiple solution files"):
        _ = bundle.solution_path


def test_a_bundle_without_a_solution_says_so(settings: Settings, coin_change: Task) -> None:
    bundle = Bundle.create(settings.bundle_root, coin_change, "falsifier")

    with pytest.raises(BundleError, match="no solution file"):
        _ = bundle.solution_path
