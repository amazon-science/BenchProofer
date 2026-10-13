# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a checker's output is taken to mean.

A backend is a few lines of parsing around one executable, and the mistake that matters
is a checker that never ran, or that changed its wording, being read as acceptance. The
transcripts below are recorded from the pinned toolchains, and each backend reads them
with its executable replaced, so no toolchain needs to be installed.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from benchproofer.backends import _nagini_driver, crosshair, dafny, lean4, nagini, velvet
from benchproofer.backends.base import Backend, CheckStatus, Closure
from benchproofer.backends.support import LEAN_ERROR, crash_location, crashed, first_error
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import write_text
from benchproofer.util.proc import Completed

#: The module each backend's `run` lives in, by registry name.
MODULES = {
    "crosshair": crosshair,
    "dafny": dafny,
    "lean4": lean4,
    "nagini": nagini,
    "velvet": velvet,
}

NAGINI_VERIFIED = "Verification successful\nVerification took 18.16 seconds.\n"
NAGINI_REFUTED = (
    "Verification failed\n"
    "Errors:\n"
    "solution.py:6:13:6:30: error: Postcondition of inc might not hold. "
    "Assertion Result() == n + 2 might not hold.\n"
    "Verification took 16.80 seconds.\n"
)
NAGINI_UNTYPED = (
    "Translation failed\n"
    "solution.py:4:1:4:1: error: Type error: Encountered Any type. "
    "Type annotation missing?\n"
)
NAGINI_SYNTAX = (
    "Translation failed\nsolution.py:1:24:1:25: error: Type error: expected ':'  [syntax]\n"
)
#: Nagini's error formatter failing on what Viper reported, with no verdict printed.
NAGINI_CRASHED = (
    "Traceback (most recent call last):\n"
    '  File "nagini/__main__.py", line 292, in main\n'
    "    translate_and_verify(python_file, jvm, args)\n"
    '  File "nagini/verifier.py", line 118, in translate_and_verify\n'
    "    error.reason.string\n"
    "AttributeError: 'ConsistencyError' object has no attribute 'reason'\n"
)

DAFNY_VERIFIED = "Dafny program verifier finished with 2 verified, 0 errors\n"
DAFNY_REFUTED = (
    "solution.dfy(11,2): Error: cannot prove termination; try supplying a decreases "
    "clause for the loop\n"
    "Dafny program verifier finished with 1 verified, 1 error\n"
)
DAFNY_UNPARSED = "solution.dfy(3,0): Error: rbrace expected\n1 parse errors detected\n"

LEAN_REFUTED = (
    "solution.lean:14:2: error: omega could not prove the goal:\n"
    "a possible counterexample may satisfy the constraints\n"
)
#: A proof left unfinished, as the pinned toolchain prints it and as Lean up to 4.2 did.
LEAN_STUBBED = "solution.lean:9:0: warning: declaration uses `sorry`\n"
LEAN_STUBBED_OLD = "solution.lean:9:0: warning: declaration uses 'sorry'\n"
LEAN_UNPARSED = "solution.lean:4:11: error: unexpected token ':='; expected command\n"
#: A tactic the file's imports do not bring: `interval_cases` under `import Velvet.Std`.
LEAN_UNKNOWN_TACTIC = (
    "solution.lean:73:4: error: unknown tactic\n"
    "solution.lean:70:38: error: unsolved goals\nn : ℕ\nh : n < 3\n⊢ n * n < 9\n"  # noqa: RUF001
)
#: An undeclared name, printed with the diagnostic's own name in parentheses.
LEAN_UNDECLARED = (
    "solution.lean:31:8: error(lean.unknownIdentifier): Unknown identifier `ensures_1`\n"
)
#: An elaboration that ran out of budget, which both Lean backends can print.
LEAN_STARVED = (
    "solution.lean:7:0: error: (deterministic) timeout at `isDefEq`, maximum number of "
    "heartbeats (20) has been reached\n"
    "Note: Use `set_option maxHeartbeats <num>` to set the limit.\n"
)
#: A file with an instance the elaborator could not build, which then starves: it did
#: not elaborate, so it is unreadable rather than undecided.
LEAN_UNSYNTHESIZED = (
    "solution.lean:23:24: error: failed to synthesize\n"
    "  Decidable (Spec n out)\n"
    "Additional diagnostic information may be available using the "
    "`set_option diagnostics true` command.\n"
) + LEAN_STARVED

CROSSHAIR_REFUTED = "solution.py:6: error: false when calling solve(xs = [0])\n"
CROSSHAIR_UNPARSED = "solution.py:7: error: SyntaxError: invalid syntax\n"

#: A postcondition the body does not meet, with the obligation left over.
VELVET_REFUTED = (
    "solution.lean:17:21: error: unsolved goals\n"
    "case «ensures_1: out = n + n»\n"
    "n : ℤ\n"  # noqa: RUF001
    "require_1 : n ≥ 0\n"
    "⊢ n + 1 = n + n\n"
)
#: A solver that decided the obligation does not hold, beside a budget some later
#: declaration ran out of: the file is refuted.
VELVET_DECIDED = (
    "solution.lean:19:2: error: z3: the goal is false:\n(define-fun n () Int (- 1))\n"
) + LEAN_STARVED
VELVET_UNPARSED = (
    "solution.lean:13:14: error: unexpected token 'prove_correct'; expected term\n"
    "solution.lean:17:0: error: no obligation found\n"
)

#: A Lean file whose proof region states two claims and names a third in a comment.
LEAN_TWO_CLAIMS = """\
-- benchproofer:begin axioms
-- benchproofer:axiom shop.price
axiom price_nonneg : True
-- benchproofer:end axioms

-- benchproofer:begin spec
def Spec (n : Nat) (r : Nat) : Prop :=
  r = n + n
-- benchproofer:end spec

-- benchproofer:begin impl
def impl (n : Nat) : Nat :=
  2 * n
-- benchproofer:end impl

-- benchproofer:begin proof
-- theorem written_up_in_prose says the same thing with sorry in it
theorem doubles (n : Nat) : impl n = n + n := by omega
theorem impl_meets_spec (n : Nat) : Spec n (impl n) := by
  unfold Spec impl
  omega
-- benchproofer:end proof
"""


def _reports(*lines: str) -> str:
    """What `#print axioms` prints, given one line per claim."""
    return "".join(f"{line}\n" for line in lines)


def _answers(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    output: str,
    returncode: int,
    *,
    timed_out: bool = False,
) -> Backend:
    """A backend whose checker prints ``output`` and exits ``returncode``."""
    backend = BACKENDS.get(name)
    completed = Completed(
        command=("checker",),
        returncode=returncode,
        stdout=output,
        stderr="",
        duration_s=0.4,
        timed_out=timed_out,
    )
    monkeypatch.setattr(MODULES[name], "run", lambda *_, **__: completed)
    if hasattr(type(backend), "executable"):
        monkeypatch.setattr(type(backend), "executable", lambda _: Path("checker"))
    if hasattr(type(backend), "workspace"):
        monkeypatch.setattr(type(backend), "workspace", lambda _: Path("workspace"))
        monkeypatch.setattr(velvet, "lake_for", lambda _: Path("checker"))
    return backend


def _verdict(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    output: str,
    returncode: int,
    tmp_path: Path,
    *,
    timed_out: bool = False,
) -> tuple[CheckStatus, bool]:
    """What a backend concludes from one transcript: its status, and whether it read it."""
    backend = _answers(monkeypatch, name, output, returncode, timed_out=timed_out)
    result = backend.check("(source)", workdir=tmp_path / name, timeout_s=30.0)
    return result.status, result.well_formed


# ---- an accepting verdict --------------------------------------------------


@pytest.mark.parametrize(
    ("name", "output", "returncode"),
    [
        ("nagini", NAGINI_VERIFIED, 0),
        ("dafny", DAFNY_VERIFIED, 0),
        ("lean4", "", 0),
        ("velvet", "", 0),
        ("crosshair", "", 0),
    ],
)
def test_a_checker_that_accepted_the_file_is_read_as_verified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str, output: str, returncode: int
) -> None:
    assert _verdict(monkeypatch, name, output, returncode, tmp_path)[0] is CheckStatus.VERIFIED


# ---- a rejection on the merits --------------------------------------------


@pytest.mark.parametrize(
    ("name", "output", "returncode"),
    [
        ("nagini", NAGINI_REFUTED, 1),
        ("dafny", DAFNY_REFUTED, 4),
        ("lean4", LEAN_REFUTED, 1),
        ("lean4", LEAN_STUBBED, 0),
        ("lean4", LEAN_STUBBED_OLD, 0),
        ("velvet", VELVET_REFUTED, 1),
        ("velvet", VELVET_DECIDED, 1),
        ("velvet", LEAN_STUBBED, 0),
        ("velvet", LEAN_STUBBED_OLD, 0),
        ("crosshair", CROSSHAIR_REFUTED, 1),
    ],
)
def test_a_rejection_on_the_merits_counts_as_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str, output: str, returncode: int
) -> None:
    assert _verdict(monkeypatch, name, output, returncode, tmp_path) == (
        CheckStatus.REFUTED,
        True,
    )


# ---- a file the checker could not read ------------------------------------


@pytest.mark.parametrize(
    ("name", "output", "returncode"),
    [
        ("nagini", NAGINI_UNTYPED, 1),
        ("nagini", NAGINI_SYNTAX, 1),
        ("dafny", DAFNY_UNPARSED, 2),
        ("lean4", LEAN_UNPARSED, 1),
        ("lean4", LEAN_UNSYNTHESIZED, 1),
        ("lean4", LEAN_UNDECLARED, 1),
        ("lean4", LEAN_UNKNOWN_TACTIC, 1),
        ("velvet", VELVET_UNPARSED, 1),
        ("velvet", LEAN_UNSYNTHESIZED, 1),
        ("velvet", LEAN_UNDECLARED, 1),
        ("velvet", LEAN_UNKNOWN_TACTIC, 1),
        ("crosshair", CROSSHAIR_UNPARSED, 1),
    ],
)
def test_a_file_the_checker_could_not_read_is_not_evidence_about_the_spec(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str, output: str, returncode: int
) -> None:
    """Still a rejection, but `well_formed` marks it as saying nothing about the spec."""
    assert _verdict(monkeypatch, name, output, returncode, tmp_path) == (
        CheckStatus.REFUTED,
        False,
    )


# ---- a checker that did not answer ----------------------------------------


@pytest.mark.parametrize("name", sorted(MODULES))
def test_a_checker_that_never_ran_is_not_read_as_a_verdict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    """What a missing or broken installation looks like: non-zero, nothing to say."""
    missing = "[Errno 2] No such file or directory: 'checker'"

    assert _verdict(monkeypatch, name, missing, 127, tmp_path)[0] is CheckStatus.UNKNOWN


@pytest.mark.parametrize("name", ["lean4", "velvet"])
def test_a_checker_that_gave_up_inside_its_budget_is_not_read_as_a_rejection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    """Lean exits non-zero on an elaboration that ran out of heartbeats, as on a refutation."""
    assert _verdict(monkeypatch, name, LEAN_STARVED, 1, tmp_path) == (CheckStatus.UNKNOWN, True)


def test_a_checker_that_crashed_says_what_it_crashed_on(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _answers(monkeypatch, "nagini", NAGINI_CRASHED, 1)

    result = backend.check("(source)", workdir=tmp_path / "nagini", timeout_s=30.0)

    assert result.status is CheckStatus.UNKNOWN
    assert result.detail == (
        "nagini crashed: AttributeError: 'ConsistencyError' object has no attribute 'reason'"
    )


@pytest.mark.parametrize("name", sorted(MODULES))
def test_a_checker_stopped_at_its_budget_reports_that_it_was(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    backend = _answers(monkeypatch, name, "proving obligation 3", -1, timed_out=True)

    result = backend.check("(source)", workdir=tmp_path / name, timeout_s=30.0)

    assert result.status is CheckStatus.UNKNOWN and result.timed_out


# ---- summarizing a rejection ----------------------------------------------


@pytest.mark.parametrize(
    ("output", "marker", "quoted"),
    [
        (
            DAFNY_REFUTED,
            "error",
            "solution.dfy(11,2): Error: cannot prove termination; try supplying a decreases "
            "clause for the loop",
        ),
        (LEAN_REFUTED, "error:", "solution.lean:14:2: error: omega could not prove the goal:"),
        # Nagini's `Errors:` heading says nothing.
        (NAGINI_REFUTED, "error:", NAGINI_REFUTED.splitlines()[2]),
        # Named or not; a word ending in `Error:` is not one.
        (
            "solution.lean:2:0: warning: the old code raised ValueError: here\n"
            "solution.lean:5:2: error(lean.someOtherName): unsolved goals\n",
            LEAN_ERROR,
            "solution.lean:5:2: error(lean.someOtherName): unsolved goals",
        ),
        ("", "error", "rejected"),
    ],
)
def test_the_line_quoted_from_a_rejection_is_its_first_diagnostic(
    output: str, marker: str | re.Pattern[str], quoted: str
) -> None:
    assert first_error(output, marker) == quoted


@pytest.mark.parametrize("name", ["lean4", "velvet"])
def test_a_named_lean_diagnostic_is_quoted_as_the_diagnostic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    backend = _answers(monkeypatch, name, LEAN_UNDECLARED, 1)

    result = backend.check("(source)", workdir=tmp_path / name, timeout_s=30.0)

    assert result.detail == LEAN_UNDECLARED.strip()


#: What each checker handed its file by an absolute path prints on refusing it, with
#: `{file}` standing for that path.
_PLACED = {
    "crosshair": "{file}:7: error: SyntaxError: invalid syntax\n",
    "dafny": (
        "{file}(11,2): Error: a postcondition could not be proved on this return path\n"
        "Dafny program verifier finished with 1 verified, 1 error\n"
    ),
    "lean4": "{file}:14:2: error: omega could not prove the goal:\n",
    "velvet": "{file}:17:21: error: unsolved goals\n",
}


@pytest.mark.parametrize("name", sorted(_PLACED))
def test_a_diagnostic_is_recorded_without_the_directory_it_was_checked_in(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, name: str
) -> None:
    """The file's own name stays: it places the diagnostic at a line of the file."""
    workdir = tmp_path / "scratch" / "gates" / "check" / "rival-uniqueness-1"
    backend = BACKENDS.get(name)
    file = workdir / backend.solution_filename()
    backend = _answers(monkeypatch, name, _PLACED[name].format(file=file), 1)

    result = backend.check("(source)", workdir=workdir, timeout_s=30.0)

    assert result.refuted
    assert result.detail.startswith(backend.solution_filename())
    assert str(workdir) not in result.detail
    assert str(workdir) not in result.output


# ---- reading a crash -------------------------------------------------------


def test_a_run_that_died_handling_another_failure_is_quoted_from_the_last_one() -> None:
    """A chained traceback ends on the exception that actually stopped the run."""
    chained = (
        NAGINI_CRASHED
        + "\nDuring handling of the above exception, another exception occurred:\n\n"
        "Traceback (most recent call last):\n"
        '  File "nagini/__main__.py", line 300, in main\n'
        "    report(error)\n"
        "TypeError: report() missing 1 required positional argument\n"
    )

    assert crashed(chained) == "TypeError: report() missing 1 required positional argument"


@pytest.mark.parametrize("output", ["", NAGINI_REFUTED, NAGINI_UNTYPED])
def test_output_with_no_traceback_in_it_is_not_a_crash(output: str) -> None:
    assert crashed(output) is None


# ---- a proof that elaborated but is not closed -----------------------------
#
# The readings of `#print axioms`, asked after a file elaborated. A run that never
# reported has not found the proof open, so it leaves closure undecided.


def _closure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    output: str,
    *,
    returncode: int = 0,
    source: str = LEAN_TWO_CLAIMS,
    timed_out: bool = False,
) -> Closure | None:
    """What the Lean backend concludes from one `#print axioms` report."""
    backend = _answers(monkeypatch, "lean4", output, returncode, timed_out=timed_out)
    return backend.closure(source, workdir=tmp_path / "closure", timeout_s=30.0)


def test_each_claim_the_proof_region_states_is_asked_about_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """And a claim named only in a comment is not asked about, since it declares nothing."""
    _closure(monkeypatch, tmp_path, _reports("'doubles' does not depend on any axioms"))

    asked = (tmp_path / "closure" / "solution.lean").read_text()
    assert asked.count("#print axioms doubles") == 1
    assert asked.count("#print axioms impl_meets_spec") == 1
    assert "written_up_in_prose" not in asked.split("benchproofer:end proof")[1]


def test_a_proof_resting_on_leans_own_axioms_is_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    closure = _closure(
        monkeypatch,
        tmp_path,
        _reports(
            "'doubles' depends on axioms: [propext, Quot.sound]",
            "'impl_meets_spec' depends on axioms: [propext, Classical.choice]",
        ),
    )

    assert closure is not None
    assert closure.closed and closure.settled
    assert closure.depends["doubles"] == ["propext", "Quot.sound"]


def test_a_proof_resting_on_what_the_file_declares_is_closed_and_names_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A declared axiom, and an `opaque` constant, which `#print axioms` never lists."""
    opaque = LEAN_TWO_CLAIMS.replace(
        "axiom price_nonneg : True\n", "axiom price_nonneg : True\nopaque price : Nat → Nat\n"
    )
    closure = _closure(
        monkeypatch,
        tmp_path,
        _reports(
            "'doubles' does not depend on any axioms",
            "'impl_meets_spec' depends on axioms: [propext, price_nonneg]",
        ),
        source=opaque,
    )
    bare = _closure(
        monkeypatch,
        tmp_path,
        _reports(
            "'doubles' does not depend on any axioms",
            "'impl_meets_spec' does not depend on any axioms",
        ),
    )

    assert closure is not None and closure.closed
    assert closure.depends["doubles"] == []
    assert closure.detail == (
        "2 claim(s) proved; axioms used: propext, price_nonneg (declared in this file: "
        "price_nonneg); the file also declares price `opaque`, which `#print axioms` does "
        "not list"
    )
    assert bare is not None
    assert bare.detail == "2 claim(s) proved; axioms used: none"


@pytest.mark.parametrize(
    ("report", "named"),
    [
        # `sorry` written by a tactic, which no token screen sees.
        (_reports("'impl_meets_spec' depends on axioms: [sorryAx]"), "sorryAx"),
        (
            _reports(
                "'doubles' does not depend on any axioms",
                "'impl_meets_spec' depends on axioms: [propext, impl_is_correct]",
            ),
            "impl_is_correct",
        ),
    ],
)
def test_a_proof_resting_on_an_axiom_nothing_here_established_is_not_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, report: str, named: str
) -> None:
    closure = _closure(monkeypatch, tmp_path, report)

    assert closure is not None
    assert not closure.closed and closure.settled
    assert named in closure.detail


@pytest.mark.parametrize(
    ("output", "returncode", "named"),
    [
        # A claim Lean reported nothing about.
        (_reports("'doubles' does not depend on any axioms"), 0, "impl_meets_spec"),
        (LEAN_STARVED, 1, "reached no result"),
    ],
)
def test_a_question_that_never_came_back_leaves_closure_undecided(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, output: str, returncode: int, named: str
) -> None:
    closure = _closure(monkeypatch, tmp_path, output, returncode=returncode)

    assert closure is not None
    assert not closure.closed and not closure.settled
    assert named in closure.detail


def test_a_file_stating_no_claim_is_not_asked_about_closure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`spec.hygiene` reports a missing or claimless proof region itself."""
    bare = LEAN_TWO_CLAIMS.split("-- benchproofer:begin proof")[0]

    assert _closure(monkeypatch, tmp_path, "", source=bare) is None


@pytest.mark.parametrize("name", sorted(set(MODULES) - {"lean4"}))
def test_a_checker_that_replays_no_declaration_is_not_asked_about_closure(
    tmp_path: Path, name: str
) -> None:
    """Velvet included: `prove_correct` names a method, not a theorem the file writes."""
    backend = BACKENDS.get(name)

    assert backend.closure("(source)", workdir=tmp_path / name) is None


# ---- Nagini's float encoding ---------------------------------------------


def _recording(monkeypatch: pytest.MonkeyPatch) -> tuple[Backend, list[tuple[str, ...]]]:
    """Nagini, with the command lines it would have run kept rather than run."""
    backend = BACKENDS.get("nagini")
    seen: list[tuple[str, ...]] = []

    def run(argv: tuple[str, ...], **_: object) -> Completed:
        seen.append(tuple(argv))
        return Completed(
            command=argv,
            returncode=0,
            stdout=NAGINI_VERIFIED,
            stderr="",
            duration_s=0.1,
            timed_out=False,
        )

    monkeypatch.setattr(nagini, "run", run)
    monkeypatch.setattr(type(backend), "executable", lambda _: Path("checker"))
    return backend, seen


def test_a_file_that_declares_a_float_encoding_is_checked_under_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Without it Nagini leaves float operations uninterpreted."""
    backend, seen = _recording(monkeypatch)

    backend.check("# benchproofer:float-encoding real\nx = 1.0\n", workdir=tmp_path / "a")
    backend.check("x = 1.0\n", workdir=tmp_path / "b")

    assert seen[0][1:4] == ("--ide-mode", "--float-encoding", "real")
    assert "--float-encoding" not in seen[1]


def test_an_encoding_nagini_does_not_have_is_a_file_it_cannot_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend, seen = _recording(monkeypatch)

    result = backend.check("# benchproofer:float-encoding ieee64\n", workdir=tmp_path)

    assert not result.well_formed
    assert seen == []


def test_hygiene_refuses_an_encoding_nothing_honors_or_a_variant_could_change() -> None:
    """A declaration is a promise about how the specification reads floats."""
    backend = BACKENDS.get("nagini")
    stale = "# benchproofer:float-encoding real\nx = 1\n"
    inside = (
        "# benchproofer:begin spec\ndef f(x: float) -> float:\n    pass\n"
        "# benchproofer:end spec\n"
        "# benchproofer:begin impl\n# benchproofer:float-encoding real\n    return x\n"
        "# benchproofer:end impl\n"
    )

    assert any("uses no float" in problem for problem in backend.problems(stale))
    assert any("regions replaced) rewrites" in problem for problem in backend.problems(inside))
    assert (
        backend.problems("# benchproofer:float-encoding real\ny = 2.0  # float\nz: float\n")
        == []
    )


def test_hygiene_allows_only_the_type_check_silencer_for_an_undetermined_name() -> None:
    """A bare one, one naming another code, and one without the space are reported."""
    backend = BACKENDS.get("nagini")
    scoped = "class Mat:\n    def __init__(self) -> None:\n        Ensures(self.rows == 0)  "
    allowed = scoped + "# type: ignore[has-type]\n"

    assert backend.problems(allowed) == []
    assert backend.problems('note = "# type: ignore"\n') == []
    for silenced in ("# type: ignore", "# type: ignore[arg-type]", "#type:ignore"):
        (problem,) = backend.problems(scoped + silenced + "\n")
        assert f"{silenced!r} at line 3" in problem
    (both,) = backend.problems(scoped + "# type: ignore[has-type, attr-defined]\n")
    assert "silences the type check" in both


def test_a_variant_that_silences_the_type_check_reaches_for_an_escape() -> None:
    """Hygiene never reads a rival, so the screen that admits one has to."""
    assert "# type: ignore" in BACKENDS.get("nagini").escapes()
    assert "# type: ignore" not in BACKENDS.get("nagini").banned_tokens


# ---- the two Nagini errors that crash it without the driver -------------------------


def test_nagini_is_run_through_the_driver_where_its_interpreter_is_beside_it(
    tmp_path: Path,
) -> None:
    """The driver has to run in Nagini's environment."""
    launcher = tmp_path / "bin" / "nagini"
    write_text(launcher, "")
    assert nagini._launcher(launcher) == (str(launcher),)

    write_text(tmp_path / "bin" / "python", "")
    interpreter, driver = nagini._launcher(launcher)

    assert interpreter == str(tmp_path / "bin" / "python")
    assert Path(driver).name == "_nagini_driver.py" and Path(driver).is_file()


@pytest.mark.parametrize(
    ("output", "readable", "said"),
    [
        (
            "solution.py:163:20: error: Consistency error: Function kept_before has a "
            f"self-reference in its postcondition\n{_nagini_driver.INCONSISTENT}\n",
            False,
            "Consistency error: Function kept_before has a self-reference",
        ),
        (
            "Verification failed\nErrors:\nsolution.py:0:1:0:1: error: Loop invariant "
            "issubtype(typeof(oldrow), PSeq(int())) might not hold on entry.\n",
            True,
            "Loop invariant issubtype(typeof(oldrow), PSeq(int())) might not hold",
        ),
    ],
)
def test_what_the_driver_prints_is_read_as_a_verdict_rather_than_a_crash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, output: str, readable: bool, said: str
) -> None:
    """An inconsistent program is a file the checker could not read; the other a refutation."""
    backend = _answers(monkeypatch, "nagini", output, 1)

    result = backend.check("(source)", workdir=tmp_path / "nagini", timeout_s=30.0)

    assert result.status is CheckStatus.REFUTED
    assert result.well_formed is readable
    assert said in result.detail


def test_the_driver_answers_where_nagini_asks_a_position_it_does_not_have() -> None:
    class Position:
        @property
        def file_name(self) -> str:
            raise AttributeError("'NoPosition$' object has no attribute 'file'")

        @property
        def line(self) -> int:
            return 7

    _nagini_driver._positioned(Position, "file_name", "solution.py")
    _nagini_driver._positioned(Position, "line", 0)

    assert (Position().file_name, Position().line) == ("solution.py", 7)


def test_the_driver_prints_an_error_nagini_cannot_convert_and_stops(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class At:
        def line(self) -> int:
            return 12

        def column(self) -> int:
            return 4

    class Inconsistent:
        def pos(self) -> At:
            return At()

        def readableMessage(self) -> str:
            return "Consistency error: add a decreases clause"

    class Verified:
        reason = "an ordinary verification error"

    class Stopped(Exception):
        pass

    def stop(code: int) -> None:
        raise Stopped(code)

    passed: list[object] = []
    monkeypatch.setattr(_nagini_driver.os, "_exit", stop)
    convert = _nagini_driver._reporting(lambda *args: passed.append(args), "solution.py")

    convert(None, [Verified()], None, None, None)
    with pytest.raises(Stopped):
        convert(None, [Inconsistent()], None, None, None)

    assert len(passed) == 1
    assert capsys.readouterr().out.splitlines() == [
        "solution.py:12:4: error: Consistency error: add a decreases clause",
        _nagini_driver.INCONSISTENT,
    ]


# ---- a translator crash, located -------------------------------------------------

#: A module with a statement Nagini's translator would be asked to translate.
CRASHING = """\
def join(a, b, rows):
    out = rows + PSeq(a + b)  # type: PSeq[PSeq[int]]
    return out
"""


def _crash_in_translation(tree: ast.Module) -> BaseException:
    """Raise from two translator-shaped frames, each holding the node it translates."""

    def statement(node: ast.stmt) -> None:
        expression(node.value.right)  # type: ignore[attr-defined]

    def expression(node: ast.expr) -> None:
        if isinstance(node, ast.Call):
            raise AssertionError

    try:
        statement(tree.body[0].body[0])  # type: ignore[attr-defined]
    except AssertionError as exc:
        return exc
    raise AssertionError("the translator did not crash")


def test_the_driver_names_the_construct_a_translator_crash_was_on(tmp_path: Path) -> None:
    """The innermost node on the traceback is the one, quoted as the file spells it."""
    target = tmp_path / "solution.py"
    write_text(target, CRASHING)
    crash = _crash_in_translation(ast.parse(CRASHING))

    site = _nagini_driver.crash_site(crash.__traceback__, str(target))

    assert site == f"{target}:2:18: {_nagini_driver.CRASHED} `PSeq(a + b)`"


def test_a_crash_with_no_node_on_its_traceback_is_not_placed(tmp_path: Path) -> None:
    """A position the traceback does not carry is not made up."""
    try:
        raise AssertionError("alias")
    except AssertionError as exc:
        crash = exc

    assert _nagini_driver.crash_site(crash.__traceback__, str(tmp_path / "x.py")) is None


def test_a_located_crash_says_where_it_was_past_a_traceback_the_tail_cuts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The driver prints the place ahead of a traceback longer than the tail kept of it."""
    frames = "".join(
        f'  File "nagini_translation/translators/call.py", line {n}, in translate\n'
        "    return self.translate_contractfunc_call(node, ctx, impure)\n"
        for n in range(40)
    )
    site = f"solution.py:111:21: {_nagini_driver.CRASHED} `PSeq(a + b)`"
    output = f"{site}\nTraceback (most recent call last):\n{frames}AssertionError\n"
    backend = _answers(monkeypatch, "nagini", output, 1)

    result = backend.check("(source)", workdir=tmp_path / "nagini", timeout_s=30.0)

    assert result.status is CheckStatus.UNKNOWN
    assert result.detail == f"nagini crashed: AssertionError; {site}"
    assert result.output.splitlines()[0] == site
    assert result.output.count(site) == 1


def test_where_a_crash_was_placed_is_read_from_the_output_and_from_the_detail() -> None:
    """On a line of its own from the driver, or after the exception in a result's detail."""
    site = f"solution.py:111:21: {_nagini_driver.CRASHED} `PSeq(a + b)`"

    assert crash_location(f"{site}\nTraceback (most recent call last):\n") == site
    assert crash_location(f"nagini crashed: AssertionError; {site}") == site
    assert crash_location(NAGINI_CRASHED) == ""
    assert crash_location(f"prose about how {_nagini_driver.CRASHED} a construct") == ""


# ---- what the drafting guidance says ---------------------------------------------


def test_the_nagini_guidance_gives_the_forms_its_checker_accepts() -> None:
    """Empty collections a `@Pure` function can write, a contract's order, a recursion step.

    A result that expands the input element by element is a front-recursive fold, with the
    loop from the end that unfolds it once a step.
    """
    guidance = BACKENDS.get("nagini").guidance()

    for form in (
        "`PSeq(x).take(0)`",
        "`PSet(x) - PSet(x)`",
        "Requires, Decreases, Ensures, Exsures",
        "`(i + 1) - 1`",
        "`escaped(s) == entity(s[0]) + escaped(s.drop(1))`",
        "`ToSeq(acc) == escaped(ToSeq(xs).drop(i))`",
        "where it defines a notion the task uses",
    ):
        assert form in guidance
    assert "Never state it as equality to a fold" not in guidance


def test_the_nagini_guidance_leaves_the_abstraction_to_the_drafter() -> None:
    """How Nagini states an unchanged callee, which the shared rule says when to model."""
    guidance = BACKENDS.get("nagini").guidance()

    assert "whatever abstraction lets you state it cleanly" in guidance
    # A string admits no lone surrogate, and a mapping keeps its keys.
    assert "a Unicode scalar value, 0 to 0x10FFFF outside 0xD800 to 0xDFFF" in guidance
    assert "modeled with its keys and its values" in guidance
    assert "the specification's defect, not a proof the implementation lacks" in guidance
    assert "Never replace a callee's result" not in guidance
    assert "class of its own with no fields" not in guidance


def test_the_velvet_guidance_names_the_tactics_its_header_does_not_bring() -> None:
    """A rival or a probe cannot change the header, so a tactic outside it is refused."""
    guidance = BACKENDS.get("velvet").guidance()

    in_scope, _, missing = guidance.partition("but not Mathlib's")
    for tactic in ("`omega`", "`simp`", "`grind`", "`aesop`"):
        assert tactic in in_scope
    for tactic in ("`linarith`", "`ring`", "`norm_num`", "`interval_cases`"):
        assert tactic in missing


def test_the_velvet_guidance_names_its_documentation_and_the_example_forms_it_refuses(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A session that has to find them searches the disk, and copies what it finds."""
    package = tmp_path / ".lake" / "packages" / "Velvet" / "Velvet"
    write_text(package / "velvet_documentation.md", "# Velvet\n")
    write_text(package / "Examples" / "Examples_Total.lean", "import Velvet.Std\n")
    monkeypatch.setenv("BENCHPROOFER_VELVET", str(tmp_path))

    guidance = BACKENDS.get("velvet").guidance()

    assert f"Velvet's documentation is `{package / 'velvet_documentation.md'}`" in guidance
    assert f"its examples are under `{package / 'Examples'}`" in guidance
    for form in ('termination "partial"', "`import Auto`", "`import CaseStudies.TestingUtil`"):
        assert form in guidance
    assert "`Examples_Total.lean` is written under total correctness" in guidance
    monkeypatch.setenv("BENCHPROOFER_VELVET", str(tmp_path / "elsewhere"))
    assert "documentation" not in BACKENDS.get("velvet").guidance()


@pytest.mark.parametrize(
    ("binder", "reported"),
    [
        ("out : Int", False),
        ("out : String", False),
        ("out : Float", True),
        ("out : List Float", True),
        ("out : Rat", True),
        # A name that merely contains one of them is another type.
        ("out : FloatBox", False),
    ],
    ids=["int", "string", "float", "list-of-float", "rational", "another-type"],
)
def test_a_velvet_result_nothing_can_be_decided_of_is_reported_before_the_cases_are(
    binder: str, reported: bool
) -> None:
    """A refused case attributes its refusal with a witness closed by reduction.

    Over a carrier the kernel does not reduce there is no such claim to write, so every
    wrong case would come back unproved and nothing would be attributed. `spec.hygiene`
    says so of the file rather than leaving it to be discovered four cases later.
    """
    source = (
        "-- benchproofer:begin spec\n"
        f"method sized (xs : List Int) return ({binder})\n"
        "  ensures True\n"
        "-- benchproofer:end spec\n"
        "-- benchproofer:begin impl\n"
        "  do\n"
        "    return x\n"
        "-- benchproofer:end impl\n"
    )

    problems = BACKENDS.get("velvet").problems(source)

    assert bool(problems) is reported
    if reported:
        assert "no refutation witness about its result can be decided" in problems[0]


def test_a_velvet_witness_has_a_route_for_a_carrier_decide_will_not_reduce() -> None:
    """Over `String` operations `decide` reports the proposition undecidable, concrete or not.

    Prescribing `by decide` alone leaves every such case unproved, so the fallback that does
    close one is named where the form of a witness is.
    """
    placement = BACKENDS.get("velvet").witness_placement

    assert "example : theMethodTester arg1 arg2 = false := by decide" in placement
    assert "simp +ground +decide" in placement


def test_a_velvet_method_declares_one_return_binder() -> None:
    """Two is a syntax error, so what to do instead is said rather than discovered."""
    guidance = BACKENDS.get("velvet").guidance()

    assert "one `return` binder" in guidance
    assert "never a `Float`" in guidance


# ---- where a Lean file is elaborated ----------------------------------------


def test_velvet_found_as_a_package_of_a_workspace_counts_as_built(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A workspace that requires Velvet holds the compiled library in its package copy."""
    compiled = tmp_path / ".lake" / "packages" / "Velvet" / ".lake" / "build" / "lib" / "lean"
    (compiled / "Velvet").mkdir(parents=True)
    (compiled / "Velvet" / "Std.olean").write_bytes(b"")
    monkeypatch.setenv("BENCHPROOFER_VELVET", str(tmp_path))

    assert BACKENDS.get("velvet").workspace() == tmp_path


def test_a_lean_workspace_elaborates_the_file_with_its_packages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`lake env lean` from the workspace, which is what makes `import Mathlib` resolve."""
    workspace = tmp_path / "workspace"
    (workspace / ".lake").mkdir(parents=True)
    lake = tmp_path / "lean" / "bin" / "lake"
    lake.parent.mkdir(parents=True)
    lake.write_text("")
    monkeypatch.setenv("BENCHPROOFER_LEAN_WORKSPACE", str(workspace))
    ran: list[tuple[tuple[str, ...], Path]] = []

    def run(command: tuple[str, ...], *, cwd: Path, timeout_s: float) -> Completed:
        ran.append((command, cwd))
        return Completed(
            command=command, returncode=0, stdout="", stderr="", duration_s=0.1, timed_out=False
        )

    monkeypatch.setattr(MODULES["lean4"], "run", run)
    backend = BACKENDS.get("lean4")

    result = backend.check("import Mathlib\n", workdir=tmp_path / "work", timeout_s=30.0)

    assert result.verified
    assert ran[0][0][:3] == (str(lake), "env", "lean")
    assert ran[0][1] == workspace
    assert "may `import Mathlib`" in backend.guidance()
