# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Whether the verified implementation is about the repository's own code.

Verification relates two documents. This gate relates the implementation to the
program the benchmark actually ships, by running both and comparing, so the cases here
are about the two ways that can go wrong: a comparison that was never really made, and
one that was made and disagreed.

Three things are pinned down, in that order:

* the protocol in `benchproofer.core.differential`. It is shared by the stage that
  writes a `conformance.py`, the prompt that asks for one, and the gate that reads one, so it is
  tested on its own rather than through any of them.
* what the gate refuses to read as evidence: a `conformance.py` that does not carry the shadow
  it claims to compare, one that crashed rather than disagreed, and one that agreed
  over too few inputs to have looked.
* what it records when the comparison holds, including how far the compared program is
  from the one the checker accepted.

The benchmark's environment answers from a script (`tests/doubles.py`), so the protocol
lines the gate reads are given rather than produced: what each test asserts is what the
gate made of them.
"""

from __future__ import annotations

import ast
from dataclasses import replace

import pytest

from benchproofer.config import Settings
from benchproofer.core.bundle import Bundle
from benchproofer.core.differential import (
    ALIASES,
    DIRECT,
    HARNESS,
    SHAPES,
    TRANSLITERATED,
    blocked,
    carried,
    compared,
    comparisons,
    disagreements,
    executables,
    lacking,
    protocol_for,
    provenance,
    runs_as_written,
    runs_in,
    seed,
    shapes_for,
    skipped_regions,
    substituted,
    unbound,
    uncopied,
    ungrounded,
    unparsed,
)
from benchproofer.core.markers import wrap
from benchproofer.core.runnable import executable_view
from benchproofer.core.task import Reference, Task
from benchproofer.core.verdict import Level, SkipReason, Status
from benchproofer.gates import conformance
from benchproofer.gates.conformance import ConformanceGate
from benchproofer.oracles.base import OracleResult
from benchproofer.pipeline.route import Route, route
from benchproofer.registries import BACKENDS
from benchproofer.util.fsio import read_text, write_json, write_text
from doubles import Rigged, Screening

SYMBOL = "change.make_change"
OTHER = "change.coins"
COMMENT = "#"
#: A shadow of an implementation that returns one of the verifier's own values: the
#: same steps, with the borrowed value replaced by the Python one it models.
TRANSLATED = "# benchproofer:target change.py\ndef impl(x):\n    return (x,) + (x,)\n"
#: What makes the file above a comparison rather than a copy of the shadow.
HARNESS_TAIL = (
    "\nimport change\n\n"
    "assert impl(1) == (1, 1)\n"
    f'print("benchproofer:compared {SYMBOL} 100000 amounts")\n'
)


class Borrowing(Screening):
    """A Python-flavored backend that borrows values from its verifier, as Nagini does."""

    name = "borrowing"
    foreign_tokens = ("PSeq",)


class Annotating(Screening):
    """A Python-flavored backend whose implementations carry contracts, as Nagini's do."""

    name = "annotating"
    annotation_tokens = ("Invariant(", "Requires(", "Ensures(")


# ---- what the environment answered ---------------------------------------


def agreed(inputs: int = 100_000, symbol: str = SYMBOL) -> OracleResult:
    """A run that compared that many inputs and found no disagreement."""
    return OracleResult.ok(
        "conformance exited 0",
        output=f"benchproofer:compared {symbol} {inputs} amounts from a seeded draw\n",
    )


def disagreed(symbol: str = SYMBOL) -> OracleResult:
    """A run that caught the repository's code doing something the shadow does not."""
    return OracleResult.no(
        "conformance exited 1",
        output=(
            f"benchproofer:disagrees {symbol} 40 -> the repository returns "
            "(1, 1, 1, 0), the shadow returns (1, 1, 0, 5)\n"
            f"benchproofer:compared {symbol} 100000 amounts from a seeded draw\n"
        ),
    )


def context(bundle: Bundle, settings: Settings, **rigging: object) -> Rigged:
    """A context that judges this bundle at level oracle, with scripted answers."""
    rigging.setdefault("backend", Screening())
    return Rigged(
        bundle=bundle,
        settings=settings,
        level=Level.ORACLE,
        **rigging,  # type: ignore[arg-type]
    )


def judged(bundle: Bundle, settings: Settings, result: OracleResult | None = None) -> Rigged:
    """A context whose environment answers the conformance program with ``result``."""
    return context(bundle, settings, outputs={"conformance": result or agreed()})


# ---- the protocol --------------------------------------------------------


def test_a_report_is_read_out_of_whatever_else_the_program_printed() -> None:
    """Only lines that start with the prefix count, and every pass over a function counts."""
    output = (
        "drawing inputs\n"
        f"benchproofer:compared {SYMBOL} 60000 amounts under 60000\n"
        f"  benchproofer:compared {SYMBOL} 40000 boundary amounts\n"
        f"benchproofer:disagrees {OTHER} [] -> the repository raises, the shadow returns 0\n"
        f"see also benchproofer:compared {OTHER} 5, which is prose and not a report\n"
    )

    assert compared(output) == 100_000
    assert [item.symbol for item in comparisons(output)] == [SYMBOL, SYMBOL]
    assert disagreements(output) == (OTHER,)


#: An input conformance.py did not compare, with its reason.
UNBUILT_LINE = (
    f"benchproofer:blocked {SYMBOL} [cents=-1]: this program could not build it: "
    "ValueError: an amount is never negative"
)


def test_an_input_conformance_py_did_not_compare_is_read_whole_and_apart() -> None:
    """Neither a disagreement nor a gap in the whole comparison: one input not compared."""
    output = (
        f"benchproofer:compared {SYMBOL} 99999 amounts\n"
        f"  {UNBUILT_LINE}\n"
        "see also benchproofer:blocked, which is prose and not a report\n"
    )

    assert blocked(output) == (UNBUILT_LINE,)
    assert disagreements(output) == ()


def test_a_line_without_a_count_reports_nothing_rather_than_zero() -> None:
    """A `conformance.py` that says what it compared but not how much has not said it."""
    assert comparisons(f"benchproofer:compared {SYMBOL} many amounts\n") == ()
    assert compared(f"benchproofer:compared {SYMBOL} many amounts\n") == 0


#: A comparison over a hundred thousand inputs, printed with a description inside the
#: function's name, so that the name has spaces in it and no reader parses the line.
MISREAD = (
    f"benchproofer:compared {SYMBOL}[the amounts under a dollar, boundaries first] "
    "100000 drawn from random.Random(7)"
)


def test_a_protocol_line_no_reader_parses_is_reported_as_printed_rather_than_skipped() -> None:
    """Skipped, a comparison over any number of inputs reads as no comparison at all.

    Only lines that start with the prefix are meant for the protocol, so prose that
    mentions it is not reported, and a line any reader parses is not reported either.
    """
    output = (
        "benchproofer:seed 7\n"
        f"  {MISREAD}\n"
        f"benchproofer:compared {SYMBOL} 400 boundary amounts\n"
        f"benchproofer:disagrees {SYMBOL} 40 -> the repository returns 4, the shadow 3\n"
        "benchproofer:skipped change.tally: takes a callback\n"
        "benchproofer:note the draw took 3 seconds\n"
        "see also benchproofer:compared, which is prose and not a report\n"
    )

    assert unparsed(output) == (MISREAD, "benchproofer:note the draw took 3 seconds")
    assert compared(output) == 400
    assert unparsed(agreed().output) == ()
    assert unparsed(disagreed().output) == ()


def test_a_misread_line_is_pointed_at_the_shape_the_prompts_asked_for() -> None:
    """A line whose word the protocol has is shown that line's shape; any other, all of them."""
    assert shapes_for(MISREAD) == (SHAPES["compared"],)
    assert shapes_for("  benchproofer:disagrees") == (SHAPES["disagrees"],)
    assert shapes_for("benchproofer:note the draw took 3 seconds") == tuple(SHAPES.values())


@pytest.mark.parametrize("word", sorted(ALIASES))
def test_a_line_in_a_word_naming_a_reason_reads_as_a_blocked_line(word: str) -> None:
    """A program that names the reason in place of the word is read the same."""
    line = f"benchproofer:{word} [cents=40]: TypeError: bad operand"

    assert blocked(f"{line}\n") == (line,)
    assert unparsed(f"{line}\n") == ()
    assert shapes_for(line) == (SHAPES[word],)
    assert SHAPES[word] in protocol_for(100_000)


def test_a_blocked_line_naming_no_reason_is_read_and_shown_the_three_that_do() -> None:
    line = "benchproofer:blocked"

    assert blocked("benchproofer:blocked f [cents=40]: it failed\n")
    assert shapes_for(line) == tuple(SHAPES[word] for word in ALIASES)
    assert f"{line} " not in protocol_for(100_000)


def test_what_the_prompts_ask_for_is_what_the_gate_reads() -> None:
    """Every line shape the gate reads is the one a model is shown, with this run's target."""
    protocol = protocol_for(100_000)
    assert all(shape in protocol for shape in SHAPES.values())
    assert "100,000" in protocol
    assert "2,000 inputs" in protocol_for(2_000)
    assert "$" not in protocol


@pytest.mark.parametrize(
    ("extension", "body", "foreign", "expected"),
    [
        # Only Python runs in the repository's environment.
        (".py", "", (), DIRECT),
        (".lean", "", (), TRANSLITERATED),
        # Nagini is Python, and `PSeq` is Viper's: no interpreter in the image has it.
        (".py", "return xs[0]", ("PSeq",), DIRECT),
        (".py", "return PSeq(a) + PSeq(b)", ("PSeq",), TRANSLITERATED),
        # A type comment is read by the verifier and never by the interpreter.
        (".py", "result = old_key()  # type: PSeq[int]\nreturn result", ("PSeq",), DIRECT),
        # A string literal is data the interpreter has.
        (".py", 'return "PSeq"', ("PSeq",), DIRECT),
        # The name is what Python cannot run, however the call around it is spaced.
        (".py", "    items = ToSeq (xs)\n    return items", ("ToSeq",), TRANSLITERATED),
        (".py", "    x = ToSeq(a)\n    return x", ("ToSeq(",), TRANSLITERATED),
        (".py", "    x = ToSequence(a)\n    return x", ("ToSeq",), DIRECT),
    ],
)
def test_only_code_the_repository_can_run_as_written_is_compared_directly(
    extension: str, body: str, foreign: tuple[str, ...], expected: str
) -> None:
    """The weakest link in the guarantee is named in the verdict rather than implied."""
    assert provenance(extension, body, foreign) == expected


# ---- what there is to compare -------------------------------------------


def test_a_task_that_ships_no_reference_has_no_code_to_compare_against(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """Not a pass: a benchmark with no solution cannot say what the fixed code does."""
    write_json(
        sound.task_path,
        coin_change.model_copy(update={"reference": Reference()}).model_dump(mode="json"),
    )

    verdict = ConformanceGate().run(judged(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.NOT_APPLICABLE


@pytest.mark.parametrize(
    "harness",
    [
        # Code equivalent to the implementation is not the verified code.
        "import change\n\ndef make_change(cents):\n    return (0, 0, 0, cents)\n",
        # Nor is a `conformance.py` that writes its own check and carries nothing.
        "import change\n\nassert change.make_change(40) == (1, 1, 1, 0)\n",
    ],
)
def test_a_conformance_py_without_the_implementation_verbatim_compares_something_else(
    sound: Bundle, settings: Settings, harness: str
) -> None:
    write_text(
        sound.conformance_path,
        harness + f'print("benchproofer:compared {SYMBOL} 100000 amounts")\n',
    )

    verdict = ConformanceGate().run(judged(sound, settings))

    assert verdict.status is Status.FAIL
    assert "verbatim" in verdict.summary
    assert verdict.details["provenance"] == DIRECT


#: A solution modeling two functions, the second of which a program may skip.
TWO = "\n".join(
    wrap(COMMENT, name, text)
    for name, text in (
        ("spec", "def make_change(cents):\n    pass"),
        ("impl", "    return (0, 0, 0, cents)"),
        ("spec.2", "def watch(ledger):\n    pass"),
        ("impl.2", "    return ledger.broker.poll()"),
    )
)


@pytest.mark.parametrize(
    ("report", "regions"),
    [
        ('print("benchproofer:skipped watch: needs a message broker")', ("impl.2",)),
        ('print("benchproofer:skipped change.Ledger.watch: needs a broker")', ("impl.2",)),
        ('print("benchproofer:skipped `impl.2`: needs a broker")', ("impl.2",)),
        (
            'FN = "change.watch"\nprint(f"benchproofer:skipped {FN}: needs a broker")',
            ("impl.2",),
        ),
        ('print(f"benchproofer:skipped {name}: needs a broker")', ()),
        ('print("benchproofer:compared change.watch 3 inputs")', ()),
    ],
    ids=[
        "by-name",
        "by-dotted-path",
        "by-region",
        "named-by-a-constant",
        "unknown",
        "compared",
    ],
)
def test_a_region_whose_function_is_reported_skipped_is_read_off_the_program(
    report: str, regions: tuple[str, ...]
) -> None:
    """Read before any run, so the program has to write the report out."""
    assert skipped_regions(report, TWO, COMMENT) == regions


def test_a_region_whose_function_is_skipped_need_not_be_copied() -> None:
    """It is not compared, so requiring a copy of it only invites one that nothing runs."""
    bodies = {"impl": "return (0, 0, 0, cents)", "impl.2": "return ledger.broker.poll()"}
    program = "def shadow(cents):\n    return (0, 0, 0, cents)\n"

    assert uncopied(program, bodies) == ("impl.2", "return ledger.broker.poll()")
    assert uncopied(program, bodies, skipped=("impl.2",)) is None
    assert uncopied(program, bodies, skipped=("impl",)) is not None


def test_a_bundle_with_no_conformance_py_fails_for_a_repair_to_write_one(
    sound: Bundle, settings: Settings
) -> None:
    """Never a pass: nothing was compared, and nothing but a repair writes the program."""
    sound.conformance_path.unlink()

    verdict = ConformanceGate().run(judged(sound, settings))

    assert verdict.status is Status.FAIL
    assert route(verdict) is Route.REPAIR
    assert f"ships no {HARNESS}" in verdict.summary


@pytest.mark.parametrize(
    ("impl", "copy"),
    [
        # Nagini's loop annotations are part of the region the checker read and cannot be
        # part of anything Python runs.
        (
            "def impl(x):\n"
            "    Invariant(0 <= x)\n"
            "    Invariant(Forall(int, lambda k: (\n        k == k,\n        [[k]])))\n"
            "    # what the loop maintains\n"
            "    return x",
            "def impl(x):\n    return x\n",
        ),
        # A type comment is read by the checker and not by the interpreter; a `#` inside a
        # literal is still code `conformance.py` has to carry.
        (
            'def impl(x):\n    total = x  # type: int\n    mark = "#"  # type: str\n'
            "    return total",
            'def impl(x):\n    total = x\n    mark = "#"\n    return total\n',
        ),
    ],
)
def test_what_the_checker_reads_and_python_does_not_is_not_a_missing_line(
    sound: Bundle, settings: Settings, impl: str, copy: str
) -> None:
    """A runnable copy of an annotated implementation cannot carry the annotations."""
    write_text(
        sound.solution_path,
        "\n".join(
            (
                wrap(COMMENT, "spec", "def property_it_holds(x):\n    assert impl(x) == x"),
                wrap(COMMENT, "impl", impl),
            )
        ),
    )
    write_text(
        sound.conformance_path,
        f'import change\n\n{copy}print("benchproofer:compared {SYMBOL} 100000 amounts")\n',
    )

    verdict = ConformanceGate().run(
        context(sound, settings, backend=Annotating(), outputs={"conformance": agreed()})
    )

    assert verdict.status is Status.PASS, verdict.summary
    assert verdict.details["provenance"] == DIRECT


def test_an_implementation_the_repository_cannot_run_is_not_held_to_a_copy(
    sound: Bundle, settings: Settings
) -> None:
    """Demanding a verbatim copy of code Python cannot run asks for an impossible file.

    A Nagini implementation returning a `PSeq` has no Python copy, only a translation,
    and the translation is what the comparison is then about. The verdict says so rather
    than reporting the bundle as having shipped a second implementation.
    """
    write_text(
        sound.solution_path,
        "\n".join(
            (
                wrap(COMMENT, "spec", "def property_it_holds(x):\n    assert impl(x) == x"),
                wrap(COMMENT, "impl", "def impl(x):\n    return PSeq(x) + PSeq(x)"),
            )
        ),
    )
    write_text(sound.conformance_path, TRANSLATED + HARNESS_TAIL)

    verdict = ConformanceGate().run(
        context(sound, settings, backend=Borrowing(), outputs={"conformance": agreed()})
    )

    assert verdict.status is Status.PASS
    assert verdict.details["provenance"] == TRANSLITERATED
    assert "translated" in verdict.summary


# ---- what the comparison established ------------------------------------


def test_the_comparison_always_runs_against_the_benchmarks_own_fix(
    sound: Bundle, settings: Settings
) -> None:
    """At the base commit the function compared against is the unfixed one.

    The second run is the one asking whether `conformance.py` can tell those two apart, so it is
    the only one against the base commit.
    """
    rigged = judged(sound, settings)

    ConformanceGate().run(rigged)

    assert [program.label for program in rigged.probed] == ["conformance", "conformance-base"]
    assert rigged.probed[0].with_reference
    assert not rigged.probed[1].with_reference
    assert rigged.probed[0].source == read_text(sound.conformance_path)


def test_a_conformance_py_that_agrees_with_the_code_before_the_fix_too_is_noted_and_passes(
    sound: Bundle, settings: Settings
) -> None:
    """Its agreement with the fixed code stands, and says nothing about the change itself.

    So the verdict passes on its other checks and says so, for the review to weigh.
    """
    rigged = judged(sound, settings)
    rigged.outputs["conformance-base"] = agreed()

    verdict = ConformanceGate().run(rigged)

    assert verdict.status is Status.PASS
    assert "; note: conformance.py reports the same agreement against the task's base " in (
        verdict.summary
    )
    assert verdict.summary.endswith("its evidence does not cover the change")
    assert "100,000 input(s) there" in verdict.details["undiscriminating"]


def test_a_conformance_py_that_disagrees_with_the_code_before_the_fix_reaches_the_fix(
    sound: Bundle, settings: Settings
) -> None:
    """A `conformance.py` that cannot run there at all has told them apart too."""
    rigged = judged(sound, settings)
    rigged.outputs["conformance-base"] = disagreed()

    verdict = ConformanceGate().run(rigged)

    assert verdict.status is Status.PASS
    assert "disagree with the code before the fix" in verdict.summary


def test_a_disagreement_is_a_finding_recorded_with_the_lines_that_show_it(
    sound: Bundle, settings: Settings
) -> None:
    """The function's name says where to look; the line says on what, and what each did."""
    verdict = ConformanceGate().run(judged(sound, settings, disagreed()))

    assert verdict.status is Status.FAIL
    assert verdict.details["disagrees"] == [SYMBOL]
    assert verdict.details["disagreement_lines"] == 1
    assert verdict.details["witnesses"] == [
        f"benchproofer:disagrees {SYMBOL} 40 -> the repository returns (1, 1, 1, 0), "
        "the shadow returns (1, 1, 0, 5)"
    ]


def test_a_conformance_py_that_crashed_is_not_read_as_a_disagreement(
    sound: Bundle, settings: Settings
) -> None:
    """A program that does not run in the task's environment establishes nothing."""
    verdict = ConformanceGate().run(
        judged(sound, settings, OracleResult.no("conformance exited 1", output="Traceback\n"))
    )

    assert verdict.status is Status.FAIL
    assert "without naming a disagreement" in verdict.summary
    assert "disagrees" not in verdict.details


def test_an_environment_that_could_not_run_conformance_py_says_so(
    sound: Bundle, settings: Settings
) -> None:
    """A missing container is not evidence about the bundle either way."""
    verdict = ConformanceGate().run(
        judged(sound, settings, OracleResult.unavailable("docker is not installed"))
    )

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.ORACLE_UNAVAILABLE


def test_a_conformance_py_that_timed_out_is_reported_as_a_timeout(
    sound: Bundle, settings: Settings
) -> None:
    verdict = ConformanceGate().run(
        judged(sound, settings, OracleResult.timeout("conformance did not finish"))
    )

    assert verdict.status is Status.TIMEOUT


def test_agreement_over_fewer_inputs_than_the_target_is_recorded_not_penalized(
    sound: Bundle, settings: Settings
) -> None:
    """The usual cause is repository code too slow to afford the target.

    That is a fact about the task and not a defect in the artifacts, so rejecting the
    bundle for it would throw away a real comparison over a real limit. What the
    verdict owes a reader is the number, because agreement over twelve inputs is not
    worth what agreement over a hundred thousand is.
    """
    verdict = ConformanceGate().run(judged(sound, settings, agreed(inputs=12)))

    assert verdict.status is Status.PASS
    assert verdict.details["compared_inputs"] == 12
    assert verdict.details["target_inputs"] == settings.conformance_inputs
    assert "short of the 100,000 aimed at" in verdict.summary


def test_a_conformance_py_that_compared_nothing_established_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """Exit zero with no `compared` line is not agreement; it is silence."""
    silent = OracleResult.ok("conformance exited 0", output="done\n")

    verdict = ConformanceGate().run(judged(sound, settings, silent))

    assert verdict.status is Status.FAIL
    assert "reported comparing nothing" in verdict.summary


@pytest.mark.parametrize("by_benchmark", [False, True])
def test_the_target_the_verdict_records_is_the_one_this_run_asked_for(
    sound: Bundle, settings: Settings, by_benchmark: bool
) -> None:
    """The setting, or the benchmark's own figure where one is set.

    A verdict recording another target than the prompt asked for would report a shortfall
    nobody asked to avoid.
    """
    update: dict[str, object] = (
        {"conformance_inputs_by_benchmark": {sound.task().benchmark: 10}}
        if by_benchmark
        else {"conformance_inputs": 10}
    )
    rigged = replace(context(sound, settings), settings=settings.model_copy(update=update))
    rigged.outputs = {"conformance": agreed(inputs=12)}

    verdict = ConformanceGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.details["target_inputs"] == 10
    assert "short of" not in verdict.summary


def test_agreement_over_enough_inputs_is_what_the_gate_is_for(
    sound: Bundle, settings: Settings
) -> None:
    """A run that reported no seed still passes, and says so: what it lacks is a way back."""
    verdict = ConformanceGate().run(judged(sound, settings))

    assert verdict.status is Status.PASS
    assert verdict.details["compared_inputs"] == 100_000
    assert verdict.details["provenance"] == DIRECT
    assert verdict.details["compared"] == [{"symbol": SYMBOL, "inputs": 100_000}]
    assert verdict.evidence == ["evidence/conformance.log"]
    assert verdict.details["seed"] == ""
    assert "reported no seed" in verdict.summary


def test_the_protocol_asks_for_a_deadline_rather_than_a_loop_bound(
    settings: Settings,
) -> None:
    """A hard-coded count reports the drafter's guess, not what the task could afford.

    A shortfall against a guessed count says nothing about the repository. Bounding the
    draw by the clock makes it attributable.
    """
    asked = protocol_for(settings.conformance_inputs, settings.harness_timeout_s * 2 / 3)

    assert "Do not write that number into a loop bound" in asked
    assert "1,200 seconds" in asked


def test_how_many_inputs_are_reachable_is_a_property_of_the_benchmark() -> None:
    """One figure cannot fit every corpus, so it is per benchmark with a fallback.

    A pure function takes 100,000 calls in under a second; a task reached through object
    construction and I/O may take that long for a thousand.
    """
    settings = Settings()

    assert settings.inputs_for("deepswe") == 1_000
    assert settings.inputs_for("swe-bench") == settings.conformance_inputs == 100_000


def test_a_seed_is_recorded_so_a_disagreement_can_be_looked_at_again() -> None:
    """A disagreement nobody can reproduce is a rumour.

    Re-judging draws the inputs again, and a `conformance.py` seeded from the clock reports a
    failing input the next run never reaches.
    """
    assert seed("benchproofer:seed 20260923\n") == "20260923"
    assert seed("benchproofer:compared change.make_change 10 amounts\n") == ""


def test_a_seeded_run_records_the_seed_and_says_nothing_more(
    sound: Bundle, settings: Settings
) -> None:
    seeded = OracleResult.ok(
        "conformance exited 0",
        output=(
            "benchproofer:seed 20260923\n"
            f"benchproofer:compared {SYMBOL} 100000 amounts from a seeded draw\n"
        ),
    )

    verdict = ConformanceGate().run(judged(sound, settings, seeded))

    assert verdict.status is Status.PASS
    assert verdict.details["seed"] == "20260923"
    assert "no seed" not in verdict.summary


# ---- a gap `conformance.py` declared ------------------------------


def test_a_conformance_py_that_could_not_model_something_says_so_rather_than_comparing_the_rest(
    sound: Bundle, settings: Settings
) -> None:
    """The one way a bundle certifies on nothing, and it is silent by construction.

    A `conformance.py` that meets a construct it cannot execute can compare the part it does
    understand, exit zero, and be read as agreement about the whole implementation. So a
    declared gap is an explicit skip -- and `INCONCLUSIVE` rather than `NOT_APPLICABLE`,
    because the answer arrived and does not support the conclusion it would be used for.
    """
    declared = OracleResult.ok(
        "conformance exited 0",
        output=(
            "benchproofer:skipped the implementation returns a PSeq, which no "
            "interpreter here has\n"
            f"benchproofer:compared {SYMBOL} 100000 amounts\n"
        ),
    )

    verdict = ConformanceGate().run(judged(sound, settings, declared))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["unsupported"] == [
        "the implementation returns a PSeq, which no interpreter here has"
    ]
    assert "could not compare" in verdict.summary


#: A run that compared, and did not compare one admitted input.
UNBUILT = f"benchproofer:compared {SYMBOL} 99999 amounts\n{UNBUILT_LINE}\n"
#: One input not compared, for each reason a line can give, by the word naming the reason,
#: and in the word that names none, each with what the summary counts it as and says of it.
BLOCKS = {
    "not built": (
        UNBUILT_LINE.replace("benchproofer:blocked", "benchproofer:unbuildable"),
        "1 it could not build (`unbuildable`)",
        "is a defect of conformance.py: it builds each value",
    ),
    "refused": (
        f"benchproofer:refused {SYMBOL} [cents=-1]: ValueError: an amount is never negative",
        "1 the repository refused to construct (`refused`)",
        "an `Outside the bridge` entry of the first kind names such values",
    ),
    "copy raised": (
        f"benchproofer:copy-raised {SYMBOL} [cents=40]: TypeError: can only concatenate tuple",
        "1 on which its copy of the implementation raised (`copy-raised`)",
        "is a defect of that copy",
    ),
    "no reason word": (
        UNBUILT_LINE,
        "1 it gave no reason word for (`blocked`)",
        "says `unbuildable`, `refused` or `copy-raised` instead",
    ),
}


@pytest.mark.parametrize(("line", "counted", "said"), list(BLOCKS.values()), ids=list(BLOCKS))
def test_an_input_conformance_py_did_not_compare_leaves_the_gate_undecided_whatever_the_reason(
    line: str, counted: str, said: str, sound: Bundle, settings: Settings
) -> None:
    """The function and the implementation were never compared on it.

    Read as a raise of the repository's, it would fail a specification over a call that
    never happened; skipped in silence, it would pass one over a comparison narrower than
    it says. The line says why, and the verdict counts each reason apart and says what
    addresses it: the program, for what it could not build or its copy raised on, and an
    entry of the first kind, for a value the repository refuses. A raise of the function
    itself is none of these, and the summary says so.
    """
    output = f"benchproofer:compared {SYMBOL} 99999 amounts\n{line}\n"

    verdict = ConformanceGate().run(
        judged(sound, settings, OracleResult.ok("conformance exited 0", output=output))
    )

    assert unparsed(output) == ()
    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert f"did not compare 1 input(s) the specification admits: {counted}." in verdict.summary
    assert said in verdict.summary
    assert "A raise of the function compared, inside the call, is none of these" in (
        verdict.summary
    )
    assert "narrowing" not in verdict.summary
    assert verdict.details["blocked_lines"] == 1
    assert verdict.details["witnesses"] == [line]


def test_the_inputs_not_compared_are_counted_by_reason() -> None:
    lines = [
        f"benchproofer:refused {SYMBOL} [cents=-1]: ValueError",
        f"benchproofer:refused {SYMBOL} [cents=-2]: ValueError",
        f"benchproofer:copy-raised {SYMBOL} [cents=4]: TypeError",
        "benchproofer:excluded [cents=-3]: no such line",
    ]

    assert conformance._reasons(lines) == {"refused": 2, "copy-raised": 1, "excluded": 1}


#: An input drawn and set aside, quoting the precondition that excludes it.
EXCLUDED = (
    "benchproofer:excluded [cents=-1]: AMOUNTS = st.integers(min_value=0, max_value=10000)"
)


def test_an_input_a_precondition_of_the_specification_excludes_is_no_refusal(
    sound: Bundle, settings: Settings
) -> None:
    """The specification never claimed the repository has that value.

    One set aside by a line the specification does not have is counted as blocked: as far
    as the specification says, the input is one it admits and the function never ran on.
    """
    compared = f"benchproofer:compared {SYMBOL} 99999 amounts\n"
    unstated = "benchproofer:excluded [cents=-2]: cents >= 0 always holds"

    kept = ConformanceGate().run(
        judged(sound, settings, OracleResult.ok("exited 0", output=f"{compared}{EXCLUDED}\n"))
    )
    counted = ConformanceGate().run(
        judged(sound, settings, OracleResult.ok("exited 0", output=f"{compared}{unstated}\n"))
    )

    assert kept.status is Status.PASS and kept.details["excluded_lines"] == 1
    assert counted.status is Status.SKIP and counted.details["blocked_lines"] == 1
    assert counted.details["witnesses"] == [unstated]
    assert (
        "set aside as `excluded` by a line the specification does not have" in counted.summary
    )


@pytest.mark.parametrize(
    "beside",
    [
        "benchproofer:skipped the third branch needs a socket\n"
        f"benchproofer:compared {SYMBOL} 100000 amounts\n",
        UNBUILT,
    ],
    ids=["a declared gap", "an input conformance.py could not build"],
)
def test_a_disagreement_is_a_finding_whatever_else_conformance_py_could_not_do(
    sound: Bundle, settings: Settings, beside: str
) -> None:
    """What `conformance.py` did manage to compare, it compared: the refutation stands."""
    both = OracleResult.no(
        "conformance exited 1",
        output=beside
        + f"benchproofer:disagrees {SYMBOL} 40 -> the repository returns 4, the shadow "
        "returns 3\n",
    )

    verdict = ConformanceGate().run(judged(sound, settings, both))

    assert verdict.status is Status.FAIL
    assert verdict.details["disagrees"] == [SYMBOL]


def test_a_comparison_printed_in_a_shape_no_reader_parses_is_undecided_and_quoted(
    sound: Bundle, settings: Settings
) -> None:
    """`conformance.py` compared, and said so in a line the gate could not read.

    Read as having compared nothing, the verdict would tell a repair to make a program
    that already compares do so, and never say which line went unread. The line is
    quoted as printed, beside the shape the protocol gives it.
    """
    verdict = ConformanceGate().run(
        judged(sound, settings, OracleResult.ok("conformance exited 0", output=MISREAD))
    )

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert f"`{MISREAD}`" in verdict.summary
    assert f"`{SHAPES['compared']}`" in verdict.summary
    assert "comparing nothing" not in verdict.summary
    assert verdict.details["unparsed_lines"] == 1
    assert verdict.details["witnesses"] == [MISREAD]
    assert verdict.details["expected"] == [SHAPES["compared"]]


def test_a_line_no_reader_parses_keeps_agreement_over_the_rest_from_passing(
    sound: Bundle, settings: Settings
) -> None:
    """A misspelled `disagrees` line is a disagreement nobody read.

    So agreement read off the lines that did parse is not agreement over the run. A
    disagreement that does parse is still the finding it always is.
    """
    stray = f"benchproofer:disagree {SYMBOL} 40 -> the repository returns 4, the shadow 3"
    beside = OracleResult.ok("conformance exited 0", output=f"{agreed().output}{stray}\n")

    undecided = ConformanceGate().run(judged(sound, settings, beside))
    found = ConformanceGate().run(
        judged(sound, settings, replace(disagreed(), output=f"{disagreed().output}{stray}\n"))
    )

    assert undecided.status is Status.SKIP
    assert undecided.skip_reason is SkipReason.INCONCLUSIVE
    assert undecided.details["witnesses"] == [stray]
    assert undecided.details["expected"] == list(SHAPES.values())
    assert found.status is Status.FAIL
    assert found.details["disagrees"] == [SYMBOL]


def test_a_bare_name_does_not_say_which_repository_function_was_reached() -> None:
    """The tautology this is against: comparing the shadow with a paraphrase of itself.

    A `conformance.py` that reimplements the repository's side agrees with the shadow whatever
    the repository does, and the report is what gives it away: it has no path to name,
    because there was nothing to import.
    """
    harness = "from change import make_change\n"
    assert ungrounded(f"benchproofer:compared {SYMBOL} 10 amounts\n", harness) == ()
    assert ungrounded("benchproofer:compared make_change 10 amounts\n", harness) == (
        "make_change",
    )
    assert ungrounded("benchproofer:compared other.module.f 10 x\n", harness) == (
        "other.module.f",
    )


def test_a_comparison_against_conformance_pys_own_code_is_not_evidence(
    sound: Bundle, settings: Settings
) -> None:
    """Reported as a finding rather than as agreement, which is what it looks like."""
    verdict = ConformanceGate().run(judged(sound, settings, agreed(symbol="make_change")))

    assert verdict.status is Status.FAIL
    assert verdict.details["ungrounded"] == ["make_change"]


def test_a_conformance_py_is_held_to_the_region_it_marks_rather_than_to_the_file(
    sound: Bundle, settings: Settings
) -> None:
    """Which is sharper: a copy of the implementation elsewhere in the file is not it.

    The marked region is also what a reviewer's submission is substituted into, so a
    gate that read the whole file would pass a `conformance.py` whose region holds one program
    and whose comments hold another.
    """
    marked = read_text(sound.conformance_path)

    assert carried(marked) is not None
    assert ConformanceGate().run(judged(sound, settings)).status is Status.PASS

    elsewhere = marked.replace(
        "# benchproofer:begin impl", "# benchproofer:begin proof"
    ).replace("# benchproofer:end impl", "# benchproofer:end proof")
    write_text(sound.conformance_path, elsewhere)

    verdict = ConformanceGate().run(judged(sound, settings))

    # No `impl` region, so the file is read whole -- and the implementation is still in
    # it, so this passes for the reason the fallback exists.
    assert verdict.status is Status.PASS
    assert verdict.details["substitutable"] is False


def test_a_labelled_comparison_names_the_function_the_program_calls(
    sound: Bundle, settings: Settings
) -> None:
    """`module.function[case]` says which of several comparisons of the function a line is.

    The function is the one before the label, which is the one the program calls.
    """
    verdict = ConformanceGate().run(judged(sound, settings, agreed(symbol=f"{SYMBOL}[large]")))

    assert verdict.status is Status.PASS, verdict.summary


#: A Nagini-shaped file that models two functions, both runnable once their contracts
#: are taken out.
TWO_FUNCTIONS = (
    "from nagini_contracts.contracts import *\n\n"
    + wrap("#", "spec", "def first(x: int) -> int:\n    Ensures(Result() == x)")
    + "\n"
    + wrap("#", "impl", "    return x")
    + "\n\n"
    + wrap("#", "spec.2", "def second(x: int) -> int:\n    Ensures(Result() == x + 1)")
    + "\n"
    + wrap("#", "impl.2", "    y = x + 1\n    return y")
    + "\n"
)
#: A `conformance.py` carrying both, each in the region of the same name.
TWO_SHADOWS = (
    "def shadow_first(x):\n"
    + wrap("#", "impl", "    return x")
    + "\n\ndef shadow_second(x):\n"
    + wrap("#", "impl.2", "    y = x + 1\n    return y")
    + "\n"
)


def test_a_name_conformance_py_never_binds_is_what_keeps_an_implementation_out_of_it() -> None:
    """Only the implementation's own names count, and builtins are bound everywhere."""
    runnable = {"impl": "    return helper(x)", "impl.2": "    return len([x])"}

    assert unbound(TWO_SHADOWS, runnable) == ("helper",)
    assert unbound(TWO_SHADOWS, {"impl": "    return x", "impl.2": "    return x"}) == ()
    assert runs_in(TWO_SHADOWS, TWO_FUNCTIONS, BACKENDS.get("nagini"))


def test_each_function_a_file_models_is_carried_into_its_own_conformance_py_region() -> None:
    backend = BACKENDS.get("nagini")
    bodies = executables(TWO_FUNCTIONS, backend)

    assert bodies == {"impl": "    return x", "impl.2": "    y = x + 1\n    return y"}
    assert runs_as_written(TWO_FUNCTIONS, backend)
    assert carried(TWO_SHADOWS) == "    return x\n    y = x + 1\n    return y"

    spliced = substituted(TWO_SHADOWS, {"impl": "return 0", "impl.2": "return 1"})

    assert spliced is not None
    assert "def shadow_first(x):\n# benchproofer:begin impl\n    return 0\n" in spliced
    assert "# benchproofer:begin impl.2\n    return 1\n# benchproofer:end impl.2" in spliced


def test_a_copy_that_is_not_verbatim_is_placed_by_its_region_and_first_missing_line() -> None:
    """A renamed call reads as a defect of the solution unless the line is named."""
    renamed = TWO_SHADOWS.replace("    y = x + 1\n", "    y = shadow_first(x) + 1\n")

    assert uncopied(TWO_SHADOWS, executables(TWO_FUNCTIONS, BACKENDS.get("nagini"))) is None
    missing = uncopied(renamed, executables(TWO_FUNCTIONS, BACKENDS.get("nagini")))

    assert missing == ("impl.2", "y = x + 1")
    assert "`impl.2` region" in lacking(missing)
    assert "`y = x + 1`" in lacking(missing)
    assert "outside the region" in lacking(missing)


def test_the_verdict_on_a_copy_that_is_not_verbatim_names_the_line_it_lacks(
    sound: Bundle, settings: Settings
) -> None:
    write_text(sound.solution_path, TWO_FUNCTIONS)
    write_text(
        sound.conformance_path,
        "import change\n\n"
        + TWO_SHADOWS.replace("    y = x + 1\n", "    y = shadow_first(x) + 1\n")
        + f'print("benchproofer:compared {SYMBOL} 100000 amounts")\n',
    )

    verdict = ConformanceGate().run(
        context(sound, settings, backend=BACKENDS.get("nagini"), outputs={})
    )

    assert verdict.status is Status.FAIL
    assert verdict.details["region"] == "impl.2"
    assert verdict.details["missing"] == "y = x + 1"


def test_a_conformance_py_that_does_not_carry_every_function_takes_no_substitution() -> None:
    """A body with nowhere to go would leave the comparison running the drafter's code."""
    one = TWO_SHADOWS.split("\n\n", 1)[0] + "\n"

    assert substituted(one, {"impl": "return 0", "impl.2": "return 1"}) is None
    assert substituted(TWO_SHADOWS, {"impl": "return 0"}) is None


#: A Nagini body with branches whose only statements are annotations: an `else:` holding a
#: multi-line `Assert`, a header wrapped over two lines, a header with a trailing comment,
#: and a branch whose annotation is followed by real code, which keeps its block.
ANNOTATED_BRANCHES = """\
    result = []  # type: List[int]
    if has_name:
        result.append(name)
        Assert(ToSeq(result)
               == PSeq(name))
    else:
        Assert(ToSeq(result)
               == PSeq())
    if (has_name and
            len(result) > 0):
        Assert(len(result) == 1)
    elif not has_name:  # nothing was appended
        # the empty list is the answer
        Assert(len(result) == 0)
    for item in result:
        Invariant(Acc(list_pred(result)))
        item = item + 0
    return result"""


def test_a_block_left_holding_only_annotations_gets_a_pass_where_they_stood() -> None:
    """Python refuses a block with no statement, so the view would run nowhere.

    Every block the stripping empties gets one `pass`, at the indentation its first
    annotation had, however its header is written; a block that keeps a statement of its
    own is left as it was. The trailing comments go with the same stripping, so what is
    left is code and nothing else, and it parses.
    """
    view = executable_view(ANNOTATED_BRANCHES, BACKENDS.get("nagini").annotation_tokens, "#")

    assert view.splitlines() == [
        "    result = []",
        "    if has_name:",
        "        result.append(name)",
        "    else:",
        "        pass",
        "    if (has_name and",
        "            len(result) > 0):",
        "        pass",
        "    elif not has_name:",
        "        pass",
        "    for item in result:",
        "        item = item + 0",
        "    return result",
    ]
    ast.parse(f"def named(has_name, name):\n{view}")
    compile(f"def build(has_name, name):\n{view}\n", "view", "exec")


def test_a_submission_whose_branch_held_only_annotations_is_spliced_into_a_program() -> None:
    """A reviewer's attack that restates what the checker knows in an `else:` is still code.

    Spliced into `conformance.py` without a `pass`, the program would not compile and the
    oracle could say nothing about the submission; with it, the comparison runs.
    """
    backend = BACKENDS.get("nagini")
    submission = (
        "from nagini_contracts.contracts import *\n\n"
        + wrap(
            "#", "spec", "def build(has_name: bool, name: int) -> List[int]:\n    Ensures(True)"
        )
        + "\n"
        + wrap("#", "impl", ANNOTATED_BRANCHES)
        + "\n"
    )
    harness = "def shadow(has_name, name):\n" + wrap("#", "impl", "    return []") + "\n"

    spliced = substituted(harness, executables(submission, backend))

    assert spliced is not None
    compile(spliced, HARNESS, "exec")
    assert "    else:\n        pass\n" in spliced
