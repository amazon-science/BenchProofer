# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The tools a review session runs: the checker, and the gate a submission is judged by."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchproofer.audit.tools import main
from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.markers import replace_region
from benchproofer.util.fsio import write_text

#: A wrong implementation the sound fixture's specification refutes.
PENNIES = "def impl(cents):\n    return (0, 0, 0, cents)\n"


@pytest.fixture(autouse=True)
def hermetic(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    """The tools read their settings from the environment, as a session's shell sets it."""
    monkeypatch.setenv("BENCHPROOFER_OFFLINE", "true")
    monkeypatch.setenv("BENCHPROOFER_CACHE_DIR", str(settings.cache_dir))


def submitted(bundle: Bundle, tmp_path: Path, body: str) -> Path:
    path = tmp_path / "attack-1.py"
    write_text(path, replace_region(bundle.solution(), "#", "impl", body))
    return path


def test_verify_puts_a_file_to_the_bundles_checker(
    sound: Bundle, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_text(tmp_path / "shipped.py", sound.solution())

    assert main(["--bundle", str(sound.root), "verify", str(tmp_path / "shipped.py")]) == 0
    assert "status: verified" in capsys.readouterr().out

    wrong = submitted(sound, tmp_path, PENNIES)
    assert main(["--bundle", str(sound.root), "verify", str(wrong)]) == 1
    assert "status: refuted" in capsys.readouterr().out


def test_try_judges_one_submission_alone_by_the_gate_it_is_filed_for(
    sound: Bundle, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without the count the whole review is held to, which is not this file's question."""
    wrong = submitted(sound, tmp_path, PENNIES)

    main(["--bundle", str(sound.root), "try", str(wrong), "--as", "attack"])

    said = capsys.readouterr().out
    assert "attack-1" in said and "refuted" in said
    assert "audit.spec_completeness: pass" in said
    assert "audit.spec_soundness" not in said
    assert not sound.audit_dir.exists(), "a trial wrote into the bundle it was given"


def test_the_tools_usage_leaves_out_the_bundle_their_script_passes(
    sound: Bundle, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A value that names no bundle is refused with what was expected, not a traceback."""
    with pytest.raises(SystemExit) as shown:
        main(["--help"])
    assert shown.value.code == 0
    usage = capsys.readouterr().out
    assert usage.startswith("usage: ./tools [-h] {verify,try,fuzz,run}")
    assert "--bundle" not in usage

    with pytest.raises(SystemExit) as refused:
        main(["--bundle", "django__django-15499", "verify", str(tmp_path / "a.py")])
    assert refused.value.code == 2
    said = capsys.readouterr().err
    assert "--bundle django__django-15499 is not a bundle" in said
    assert "bundles/<benchmark>/<task>/<backend>" in said and "Traceback" not in said


def test_try_files_a_witness_test_and_what_it_cites_as_the_attack_auditor_files_them(
    sound: Bundle,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The gate is handed the same submission the review would record, so it judges it alike."""
    from benchproofer.gates.audit import SpecCompletenessGate

    seen: list[object] = []

    def judge(gate: SpecCompletenessGate, context: object) -> object:
        bundle = context.bundle  # type: ignore[attr-defined]
        review = bundle.audit()
        seen.append((review.submissions[0], bundle.submission_test(review.submissions[0])))
        return gate.passed("judged")

    monkeypatch.setattr(SpecCompletenessGate, "judge", judge)
    wrong = submitted(sound, tmp_path, PENNIES)
    write_text(tmp_path / "witness.py", "assert True\n")

    main(
        [
            "--bundle",
            str(sound.root),
            "try",
            str(wrong),
            "--as",
            "attack",
            "--test",
            str(tmp_path / "witness.py"),
            "--cites",
            "test_forty_cents",
        ]
    )

    ((submission, test),) = seen
    assert (submission.test, submission.cites, test) == (  # type: ignore[attr-defined]
        "attack-1.test.py",
        "test_forty_cents",
        "assert True\n",
    )
    assert "audit.spec_completeness: pass: judged" in capsys.readouterr().out


def test_try_names_each_submission_it_leaves_to_the_attack_validation_auditor(
    sound: Bundle,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """With what the gate established of it, such as a witness test that holds."""
    from benchproofer.core.verdict import SkipReason
    from benchproofer.gates.audit import UNRULED, SpecCompletenessGate

    held = (
        "the checker accepts it, the benchmark's tests do not reject it, and its witness test"
    )

    def judge(gate: SpecCompletenessGate, context: object) -> object:
        return gate.undecided(
            SkipReason.INCONCLUSIVE,
            "cannot be determined by execution",
            **{UNRULED: {"attack-1": held}},
        )

    monkeypatch.setattr(SpecCompletenessGate, "judge", judge)

    main(
        [
            "--bundle",
            str(sound.root),
            "try",
            str(submitted(sound, tmp_path, PENNIES)),
            "--as",
            "attack",
        ]
    )

    assert (
        f"attack-1 is left to the attack validation auditor: {held}" in capsys.readouterr().out
    )
