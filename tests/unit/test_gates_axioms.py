# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What the specification assumes of the world, and the two gates that check it.

A proof about realistic code is a proof modulo its assumptions, so an assumption has
to be declared and then put to the callee it stands for. Three things are pinned down
here, in that order:

* the protocol in `benchproofer.core.axioms`. It is shared by the stage that writes a
  `axioms.py`, the prompt that asks for one, and the gates that read one, so it is tested
  on its own rather than through any of them.
* `spec.axioms_grounded`, which runs the bundle's own `axioms.py`. Every unfavorable
  branch is paired with the case it must not be confused with: a specification that
  assumes nothing and one that assumes something without an `axioms.py`, an `axioms.py` that
  disagreed and one that merely crashed, an `axioms.py` that ran and one nothing could run.
* `audit.axiom_soundness`, which re-runs an independent reviewer's fuzzers. A fuzzer
  that broke on its own bug is set aside rather than counted as a refutation, and an
  assumption nobody attacked leaves the gate undecided rather than passing.

The benchmark's environment answers from a script (`tests/doubles.py`), so the
protocol lines a gate reads are given rather than produced: what each test asserts is
what the gate made of them.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from benchproofer.backends.base import CheckResult
from benchproofer.config import Settings
from benchproofer.core.axioms import (
    AFTER_REFERENCE,
    HARNESS,
    PROTOCOL,
    QUOTED,
    after_reference,
    against_reference,
    axiom_names,
    callees,
    calls,
    declared,
    directive_line,
    grounded,
    in_changed_file,
    refutations,
    refuted_lines,
    with_calls,
    with_declarations,
)
from benchproofer.core.bundle import Bundle, Fuzzer, Review
from benchproofer.core.markers import parse, wrap
from benchproofer.core.runnable import quotes_lines, unquoted
from benchproofer.core.task import Reference, Task
from benchproofer.core.verdict import Level, SkipReason, Status
from benchproofer.gates.axioms import AxiomsGroundedGate, AxiomSoundnessGate
from benchproofer.oracles.base import OracleResult
from benchproofer.util.fsio import read_text, write_json, write_text
from doubles import Rigged, Screening, revised

COMMENT = "#"
PARSE = "json.loads"
DUMP = "json.dumps"
AUTHOR = "provider:drafting-model"
REVIEWER = "provider:reviewing-model"

#: What the axioms region says about the callee it does not model: enough of the real
#: parser for the proof, and nothing about the inputs the task never hands it.
MODEL = '''\
def loads(text):
    """A model of the real parser over the inputs this task hands it."""
    return {"n": int(text[6:-1])}
'''
SPEC = """\
def property_a_written_count_reads_back(n):
    assert impl(dumps(n)) == n
"""
IMPL = """\
def impl(text):
    return loads(text)["n"]
"""


# ---- the files a bundle ships --------------------------------------------


def assuming(*assumed: str, modeled: bool = False) -> str:
    """A solution file whose axioms region models and declares each callee."""
    lines = (directive_line(COMMENT, callee, modeled=modeled) for callee in assumed)
    body = MODEL + "\n" + "\n".join(lines)
    return "\n".join(
        wrap(COMMENT, name, text)
        for name, text in (("axioms", body), ("spec", SPEC), ("impl", IMPL))
    )


def harness(source: str, *, trailer: str = "raise SystemExit(0)") -> str:
    """An `axioms.py` carrying the solution's axioms region verbatim."""
    return f"{parse(source, COMMENT)['axioms'].text}\n\n{trailer}\n"


def staged(bundle: Bundle, source: str, *, grounding: str | None = None) -> Bundle:
    """Put one solution, and optionally one `axioms.py`, in a bundle."""
    write_text(bundle.solution_path, source)
    if grounding is not None:
        write_text(bundle.axioms_path, grounding)
    return bundle


def reviewed(bundle: Bundle, *fuzzers: Fuzzer, write: bool = True) -> Review:
    """Record a review that wrote one program per fuzzer, as the audit stage does."""
    review = Review(reviewer=REVIEWER, author=AUTHOR, independent=True, fuzzers=tuple(fuzzers))
    sources = {fuzzer.file: f"# {fuzzer.id}\nraise SystemExit(0)\n" for fuzzer in fuzzers}
    bundle.save_audit(review, sources if write else {})
    return review


def attacking(identifier: str, callee: str = "", claim: str = "") -> Fuzzer:
    """One program a review wrote against what the specification assumes."""
    return Fuzzer(id=identifier, file=f"{identifier}.fuzz.py", callee=callee, claim=claim)


# ---- what the environment answered ---------------------------------------


def agreed(*reported: str) -> OracleResult:
    """A run that exercised each callee and found nothing that disagrees."""
    lines = "".join(
        f"benchproofer:grounded {callee} 200 inputs drawn from the model's domain\n"
        for callee in reported
    )
    return OracleResult.ok("exited 0", output=lines)


def disagreed(callee: str) -> OracleResult:
    """A run that caught the real callee doing something the model does not."""
    return OracleResult.no(
        "exited 1",
        output=f"benchproofer:refuted {callee} loads('1 ') is 1, the model says malformed\n",
    )


#: The line of `MODEL` a disagreement with it breaks, as a fuzzer quotes it.
BROKEN = 'return {"n": int(text[6:-1])}'


def broke(callee: str, text: str = "1 ") -> str:
    """One refutation a fuzzer printed, quoting the line of the assumption it breaks."""
    return (
        f"benchproofer:refuted {callee} loads({text!r}) is {text.strip()}, and "
        f"`{BROKEN}` says malformed"
    )


def fuzzed(*lines: str) -> OracleResult:
    """A fuzzer's run that printed these refutations."""
    return OracleResult.no("exited 1", output="".join(f"{line}\n" for line in lines))


def context(bundle: Bundle, settings: Settings, **rigging: object) -> Rigged:
    """A context that judges this bundle at level audited, with scripted answers."""
    return Rigged(
        bundle=bundle,
        backend=Screening(),
        settings=settings,
        level=Level.AUDITED,
        **rigging,  # type: ignore[arg-type]
    )


# ---- the protocol --------------------------------------------------------


def test_a_declaration_is_read_in_the_backends_own_comment_token_alone() -> None:
    """Otherwise a Dafny file would declare its assumptions in Python's comments."""
    line = directive_line("//", PARSE)

    assert callees(declared(line, "//")) == (PARSE,)
    assert declared(line, COMMENT) == ()


def test_every_declaration_is_reported_with_the_line_it_was_made_on() -> None:
    region = f"x = 1\n{directive_line(COMMENT, PARSE)}\n\n{directive_line(COMMENT, DUMP)}\n"

    assumptions = declared(region, COMMENT)

    assert [(one.callee, one.line) for one in assumptions] == [(PARSE, 2), (DUMP, 4)]


def test_a_model_is_declared_on_a_directive_of_its_own() -> None:
    """A definition computing what its callee computes is marked `models`, an axiom `axiom`.

    A directive names the callee and nothing after it: a line with another word on it is
    prose. The names under an `axiom` line are the ones no witness may evaluate.
    """
    line = directive_line(COMMENT, PARSE, modeled=True)
    region = (
        f"{line}\n{MODEL}{directive_line(COMMENT, DUMP)}\ndef dumps(value: dict) -> str: ...\n"
    )

    assert line == f"{COMMENT} benchproofer:models {PARSE}"
    assert [(one.callee, one.modeled) for one in declared(region, COMMENT)] == [
        (PARSE, True),
        (DUMP, False),
    ]
    assert axiom_names(region, COMMENT) == {"dumps"}
    for directive in (line, directive_line(COMMENT, DUMP)):
        assert declared(f"{directive} later\n{MODEL}", COMMENT) == ()


def test_one_callee_declared_twice_is_one_assumption() -> None:
    """Two models of one callee are still one thing `axioms.py` has to ground."""
    region = f"{directive_line(COMMENT, PARSE)}\n{directive_line(COMMENT, PARSE)}\n"

    assert len(declared(region, COMMENT)) == 2
    assert callees(declared(region, COMMENT)) == (PARSE,)


def test_a_report_is_read_out_of_whatever_else_the_program_printed() -> None:
    output = (
        "running 200 cases\n"
        f"benchproofer:grounded {PARSE} 200 inputs\n"
        f"benchproofer:grounded {PARSE} another 40\n"
        f"  benchproofer:refuted {DUMP} dumps(1.0) is '1.0'\n"
        f"see also benchproofer:grounded {DUMP}, which is prose and not a report\n"
    )

    assert grounded(output) == (PARSE,)
    assert refutations(output) == (DUMP,)


def test_a_refutation_is_read_whole_as_well_as_by_callee() -> None:
    """The callee says where to look; the line says on what, and what each side did."""
    output = (
        f"benchproofer:grounded {PARSE} 200 inputs\n"
        f"  benchproofer:refuted {DUMP} dumps(1.0) is '1.0', the model says '1'\n"
        f"benchproofer:refuted {DUMP} dumps(-0.0) is '-0.0', the model says '0'\n"
        f"see also benchproofer:refuted {PARSE}, which is prose and not a report\n"
    )

    assert refuted_lines(output) == (
        f"benchproofer:refuted {DUMP} dumps(1.0) is '1.0', the model says '1'",
        f"benchproofer:refuted {DUMP} dumps(-0.0) is '-0.0', the model says '0'",
    )


def test_the_tool_quotes_the_declarations_after_an_axioms_py_that_does_not_carry_them() -> None:
    """Copying them is the tool's job, since a model asked to copy them reflows them.

    After the program rather than before it, so every line the program's own output
    names is still the line the model wrote.
    """
    region = parse(assuming(PARSE), COMMENT)["axioms"].text
    program = "import json\n\nprint(json.loads('{\"n\": 1}'))\n"

    carried = with_declarations(program, region, COMMENT)

    assert carried.startswith(program)
    assert quotes_lines(carried, region, COMMENT)
    assert f"# {QUOTED.splitlines()[0]}" in carried
    assert f"# {directive_line(COMMENT, PARSE)}" in carried


def test_an_axioms_py_that_already_carries_the_declarations_is_left_as_it_is() -> None:
    """A model that runs is carried as code, and quoting it again would say it twice."""
    source = assuming(PARSE)
    program = harness(source)

    assert with_declarations(program, parse(source, COMMENT)["axioms"].text, COMMENT) == program


def test_the_first_declaration_line_an_axioms_py_lacks_is_named() -> None:
    region = parse(assuming(PARSE), COMMENT)["axioms"].text
    partial = "\n".join(f"# {line}" for line in region.splitlines() if "return" not in line)

    assert unquoted(partial, region, COMMENT) == 'return {"n": int(text[6:-1])}'
    assert unquoted(harness(assuming(PARSE)), region, COMMENT) == ""


def test_an_axioms_py_asks_for_the_fixed_tree_on_a_line_of_its_own() -> None:
    assert after_reference("# benchproofer:axioms apply-fix\n")
    assert not after_reference("print('# benchproofer:axioms apply-fix')\n")
    assert not after_reference("# benchproofer:axioms apply fix\n")
    assert "# benchproofer:axioms apply-fix" in AFTER_REFERENCE


def test_what_the_prompts_ask_for_is_what_the_gates_read() -> None:
    """The fragment a model is shown has to parse as the thing it describes."""
    assert after_reference(AFTER_REFERENCE)
    assert "benchproofer:grounded <callee>" in PROTOCOL
    assert "benchproofer:refuted <callee>" in PROTOCOL


#: A module of the repository whose functions an `axioms.py` calls, with a class beside
#: its function.
PACKAGE = {
    "pkg/__init__.py": "",
    "pkg/text.py": (
        "def squeeze(text):\n    return ' '.join(text.split())\n\n\n"
        "class Box:\n    def size(self):\n        return 1\n"
    ),
}
CALLEES = ("pkg.text.squeeze", "pkg.text.Box.size", "len", "nowhere.at_all")


def recorded(tmp_path: Path, program: str) -> dict[str, tuple[str, str]]:
    """What the recording `with_calls` puts in ``program`` reads of a run of it."""
    for path, text in PACKAGE.items():
        write_text(tmp_path / path, text)
    write_text(tmp_path / "run.py", with_calls(program, CALLEES))
    ran = subprocess.run(
        [sys.executable, "run.py"], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    return calls(ran.stdout)


def test_a_program_that_copies_a_callee_instead_of_calling_it_is_recorded_as_not_calling_it(
    tmp_path: Path,
) -> None:
    """Its module never imported, the callee did not run, whatever the program printed."""
    copied = (
        '"""Ground squeeze."""\n'
        "def squeeze(text):\n    return ' '.join(text.split())\n\n"
        "assert squeeze(' a  b ') == 'a b'\n"
    )

    found = recorded(tmp_path, copied)

    assert found["pkg.text.squeeze"] == (
        "no",
        "the run never imported pkg/text.py, which defines it",
    )
    assert found["len"][0] == "unknown" and "not Python code" in found["len"][1]
    assert found["nowhere.at_all"][0] == "unknown"


def test_a_program_that_calls_the_callee_is_recorded_as_calling_it(tmp_path: Path) -> None:
    """And a method of a module it imported but never called did not run."""
    calling = (
        '"""Ground squeeze."""\nfrom __future__ import annotations\n\n'
        "from pkg.text import squeeze\n\nassert squeeze(' a  b ') == 'a b'\n"
    )

    found = recorded(tmp_path, calling)

    assert found["pkg.text.squeeze"] == ("yes", "")
    assert found["pkg.text.Box.size"] == ("no", "its code never ran")


def test_the_recording_keeps_each_line_of_the_program_where_it_was() -> None:
    """A traceback names the program's own line numbers, which a repair then reads."""
    program = '"""Ground."""\nimport json\n\njson.loads("1")\n'

    ran = with_calls(program, (PARSE,))

    assert len(ran.splitlines()) == len(program.splitlines())
    assert ran.splitlines()[1:] == program.splitlines()[1:]
    assert with_calls(program, ()) == program


# ---- spec.axioms_grounded ------------------------------------------------


def test_a_specification_that_assumes_nothing_has_nothing_to_ground(
    sound: Bundle, settings: Settings
) -> None:
    verdict = AxiomsGroundedGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.NOT_APPLICABLE
    assert verdict.ok


def test_an_axioms_py_for_an_assumption_nobody_declared_is_about_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """An `axioms.py` with no declaration behind it is not a gate that does not apply."""
    write_text(sound.axioms_path, "raise SystemExit(0)\n")

    verdict = AxiomsGroundedGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "names no callee" in verdict.summary


@pytest.mark.parametrize("refused", [False, True], ids=["verifies", "checker refuses"])
def test_an_assumption_with_no_axioms_py_behind_it_fails(
    sound: Bundle, settings: Settings, refused: bool
) -> None:
    """Whatever the checker says of the solution: a repair writes `axioms.py` beside it."""
    bundle = staged(sound, assuming(PARSE))
    answers = (
        {"solution": CheckResult.no("cannot establish Ensures at line 9")} if refused else {}
    )

    verdict = AxiomsGroundedGate().run(context(bundle, settings, answers=answers))

    assert verdict.status is Status.FAIL
    assert f"without shipping {HARNESS}" in verdict.summary
    assert verdict.details["assumed"] == [PARSE]


def test_an_axioms_py_that_does_not_carry_the_region_is_not_about_the_model(
    sound: Bundle, settings: Settings
) -> None:
    """What it exercises would then be a second model nobody gave the checker."""
    bundle = staged(sound, assuming(PARSE), grounding="import json\nraise SystemExit(0)\n")
    rigged = context(bundle, settings, outputs={"axioms": agreed(PARSE)})

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert "does not contain the declarations of the axioms region" in verdict.summary
    assert rigged.probed == []


@pytest.mark.parametrize("docstring", [True, False], ids=["whole", "without the docstring"])
def test_an_axioms_py_may_quote_the_region_rather_than_run_it(
    docstring: bool, sound: Bundle, settings: Settings
) -> None:
    """Under a contract-carrying checker the declaration cannot run where the tests do.

    A `@ContractOnly` function names the verifier's contract library, which a task's image
    does not have, so an `axioms.py` that carries it as code dies on its import. Quoting it is
    the one way to carry it and still run, and the quotation may leave out the model's
    docstring, which is prose about the model rather than a line the checker reasons about.
    """
    region = parse(assuming(PARSE), COMMENT)["axioms"].text
    quoted = "\n".join(
        f"# {line}" for line in region.splitlines() if docstring or '"""' not in line
    )
    bundle = staged(
        sound, assuming(PARSE), grounding=f"import json\n{quoted}\nraise SystemExit(0)\n"
    )
    rigged = context(bundle, settings, outputs={"axioms": agreed(PARSE)})

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.PASS
    assert [program.label for program in rigged.probed] == ["axioms"]


def test_a_quoted_region_is_still_held_to_every_declaration_line(
    sound: Bundle, settings: Settings
) -> None:
    """Quoting relaxes how a line is carried, not which lines are."""
    region = parse(assuming(PARSE), COMMENT)["axioms"].text
    partial = "\n".join(f"# {line}" for line in region.splitlines() if "return" not in line)
    bundle = staged(
        sound, assuming(PARSE), grounding=f"import json\n{partial}\nraise SystemExit(0)\n"
    )
    rigged = context(bundle, settings, outputs={"axioms": agreed(PARSE)})

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert rigged.probed == []
    assert verdict.details["missing"] == 'return {"n": int(text[6:-1])}'


def test_a_solution_whose_regions_cannot_be_read_is_hygienes_finding(
    sound: Bundle, settings: Settings
) -> None:
    """One malformed file must not be reported as a defect by two gates."""
    bundle = staged(sound, "# benchproofer:begin spec\n", grounding="raise SystemExit(0)\n")

    verdict = AxiomsGroundedGate().run(context(bundle, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert "spec.hygiene (Hygiene check) is where that is reported" in verdict.summary


def test_an_axioms_py_that_agrees_with_the_real_callee_passes(
    sound: Bundle, settings: Settings
) -> None:
    source = assuming(PARSE)
    bundle = staged(sound, source, grounding=harness(source))
    rigged = context(bundle, settings, outputs={"axioms": agreed(PARSE)})

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.PASS
    assert f"{HARNESS} agrees with the real callee on 1 assumption(s): {PARSE}" in (
        verdict.summary
    )
    assert verdict.details["assumed"] == verdict.details["grounded"] == [PARSE]
    assert verdict.evidence == ["evidence/axioms.log"]
    assert f"benchproofer:grounded {PARSE}" in read_text(bundle.root / verdict.evidence[0])
    assert [(one.label, one.with_reference) for one in rigged.probed] == [("axioms", False)]


@pytest.mark.parametrize("agrees", [True, False], ids=["agrees", "disagrees"])
def test_a_modeled_callee_is_put_to_the_real_one_as_an_axiom_is(
    agrees: bool, sound: Bundle, settings: Settings
) -> None:
    """The definition is the specification's claim about its callee, so it is grounded."""
    source = assuming(PARSE, modeled=True)
    region = parse(source, COMMENT)["axioms"].text
    bundle = staged(sound, source, grounding=f"{region}\n\nraise SystemExit(0)\n")
    ran = agreed(PARSE) if agrees else disagreed(PARSE)

    verdict = AxiomsGroundedGate().run(context(bundle, settings, outputs={"axioms": ran}))

    assert verdict.status is (Status.PASS if agrees else Status.FAIL)
    assert verdict.details["assumed"] == [PARSE]
    assert verdict.details.get("refuted") == (None if agrees else [PARSE])


def test_a_disagreement_seen_happening_is_a_failure_under_a_falsifier_too(
    sound: Bundle, settings: Settings
) -> None:
    """Unlike an unrefuted property, an observed counterexample needs no budget.

    It is recorded with the lines that show it: a repair told only which callee disagreed
    cannot tell what part of the assumption is false.
    """
    source = assuming(PARSE)
    bundle = staged(sound, source, grounding=harness(source))
    rigged = context(bundle, settings, outputs={"axioms": disagreed(PARSE)})

    verdict = AxiomsGroundedGate().run(rigged)

    line = f"benchproofer:refuted {PARSE} loads('1 ') is 1, the model says malformed"
    assert verdict.status is Status.FAIL
    assert verdict.details["refuted"] == [PARSE]
    assert verdict.details["disagreement_lines"] == 1
    assert verdict.details["witnesses"] == [line]
    assert verdict.evidence == ["evidence/axioms.log", "evidence/axioms-refuted.txt"]
    assert read_text(bundle.root / verdict.evidence[1]) == f"{line}\n"


def test_an_axioms_py_that_fails_without_naming_a_disagreement_is_broken(
    sound: Bundle, settings: Settings
) -> None:
    """A crash in the bundle's own program is not a finding about the real callee."""
    source = assuming(PARSE)
    bundle = staged(sound, source, grounding=harness(source))
    rigged = context(bundle, settings, outputs={"axioms": OracleResult.no("exited 1")})

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert "does not run in the task's environment" in verdict.summary
    assert verdict.details["grounded"] == []


def test_an_axioms_py_that_passes_without_exercising_an_assumption_grounds_nothing(
    sound: Bundle, settings: Settings
) -> None:
    source = assuming(PARSE, DUMP)
    bundle = staged(sound, source, grounding=harness(source))
    rigged = context(bundle, settings, outputs={"axioms": agreed(PARSE)})

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["ungrounded"] == [DUMP]


def test_a_program_that_grounds_a_callee_it_never_calls_checked_nothing_about_it(
    sound: Bundle, settings: Settings
) -> None:
    """A copy of the callee's code agrees with the model whatever the callee does."""
    source = assuming(PARSE, DUMP)
    bundle = staged(sound, source, grounding=harness(source))
    ran = agreed(PARSE, DUMP)
    output = (
        f"{ran.output}benchproofer:calls {PARSE} no the run never imported json\n"
        f"benchproofer:calls {DUMP} yes\n"
    )
    rigged = context(
        bundle, settings, outputs={"axioms": OracleResult.ok("exited 0", output=output)}
    )

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert verdict.details["uncalled"] == {PARSE: "the run never imported json"}
    assert f"reports {PARSE} grounded without calling it" in verdict.summary
    # The program run is axioms.py with the recording ahead of its own statements.
    run = ast.parse(rigged.probed[0].source).body[0]
    assert isinstance(run, ast.Expr) and isinstance(run.value, ast.Call)
    recording = ast.literal_eval(run.value.args[0])
    assert "_benchproofer_calls" in recording and repr((PARSE, DUMP)) in recording


def test_whether_a_callee_ran_that_cannot_be_told_is_said_and_not_held_against_it(
    sound: Bundle, settings: Settings
) -> None:
    source = assuming(PARSE)
    bundle = staged(sound, source, grounding=harness(source))
    output = f"{agreed(PARSE).output}benchproofer:calls {PARSE} unknown it is not Python code\n"
    rigged = context(
        bundle, settings, outputs={"axioms": OracleResult.ok("exited 0", output=output)}
    )

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.PASS
    assert f"whether it calls {PARSE} could not be told" in verdict.summary
    assert verdict.details["calls_untold"] == {PARSE: "it is not Python code"}


def test_an_axioms_py_nothing_here_can_run_decides_nothing(
    sound: Bundle, settings: Settings
) -> None:
    """An environment this machine does not have is not a defect in the bundle."""
    source = assuming(PARSE)
    bundle = staged(sound, source, grounding=harness(source))
    rigged = context(
        bundle, settings, outputs={"axioms": OracleResult.unavailable("no container runtime")}
    )

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.ORACLE_UNAVAILABLE
    assert "no container runtime" in verdict.summary


def test_an_axioms_py_that_never_finishes_is_a_timeout_rather_than_a_disagreement(
    sound: Bundle, settings: Settings
) -> None:
    source = assuming(PARSE)
    bundle = staged(sound, source, grounding=harness(source))
    rigged = context(
        bundle, settings, outputs={"axioms": OracleResult.timeout("axioms ran out of time")}
    )

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.TIMEOUT
    assert not verdict.ok


def test_an_axioms_py_about_a_callee_the_fix_introduces_runs_against_the_fixed_tree(
    sound: Bundle, settings: Settings
) -> None:
    """At the base commit that callee does not exist, so there is nothing to ground."""
    source = assuming(PARSE)
    bundle = staged(
        sound,
        source,
        grounding=harness(source, trailer="# benchproofer:axioms apply-fix"),
    )
    rigged = context(bundle, settings, outputs={"axioms": agreed(PARSE)})

    verdict = AxiomsGroundedGate().run(rigged)

    assert verdict.status is Status.PASS
    assert [one.with_reference for one in rigged.probed] == [True]


def test_a_callee_is_in_a_changed_file_by_a_module_prefix_of_its_path() -> None:
    assert in_changed_file("pkg.change.tally", RENAMES)
    assert in_changed_file("change.tally", RENAMES)
    assert in_changed_file("pkg.change.Coins.split", RENAMES)
    assert not in_changed_file("pkg.changes.tally", RENAMES)
    assert not in_changed_file(PARSE, RENAMES)
    assert against_reference("raise SystemExit(0)\n", ["pkg.change.tally"], RENAMES)
    assert not against_reference("raise SystemExit(0)\n", [PARSE], RENAMES)


def test_a_callee_in_a_file_the_fix_changes_is_grounded_as_the_fix_leaves_it(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """The base commit is the reference only for callees the patch does not touch.

    At the base commit such a callee is the code before the fix, and a program exercising
    it runs into the defect the task is about. The bundle's `axioms.py` and a review's fuzzer
    run against the same tree.
    """
    callee = "pkg.change.tally"
    source = assuming(callee)
    staged(_patched(sound, coin_change), source, grounding=harness(source))
    reviewed(sound, attacking("fuzz-1", callee))
    rigged = context(
        sound,
        settings,
        outputs={"axioms": agreed(callee), "fuzz-fuzz-1": OracleResult.ok("exited 0")},
    )

    assert AxiomsGroundedGate().run(rigged).status is Status.PASS
    AxiomSoundnessGate().run(rigged)

    assert [(one.label, one.with_reference) for one in rigged.probed] == [
        ("axioms", True),
        ("fuzz-fuzz-1", True),
    ]


# ---- audit.axiom_soundness -----------------------------------------------


def test_a_specification_that_assumes_nothing_has_nothing_to_attack(
    sound: Bundle, settings: Settings
) -> None:
    """And the review is not even read: there is no assumption for a fuzzer to be about."""
    verdict = AxiomSoundnessGate().run(context(sound, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.NOT_APPLICABLE


def test_an_assumption_no_review_looked_at_is_not_one_a_review_attacked(
    sound: Bundle, settings: Settings
) -> None:
    bundle = staged(sound, assuming(PARSE))

    verdict = AxiomSoundnessGate().run(context(bundle, settings))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.ARTIFACT_ABSENT


def test_a_fuzzer_that_finds_no_disagreement_decides_the_assumption(
    sound: Bundle, settings: Settings
) -> None:
    bundle = staged(sound, assuming(PARSE))
    reviewed(bundle, attacking("fuzz-1", PARSE, claim="round trips every float"))
    rigged = context(bundle, settings, outputs={"fuzz-fuzz-1": OracleResult.ok("exited 0")})

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert verdict.summary == f"1 unchanged callee(s) survived an independent fuzzer: {PARSE}"
    assert verdict.details["fuzzers"] == ["fuzz-1"]
    assert verdict.details["reviewer"] == REVIEWER
    assert verdict.evidence == ["evidence/fuzz-fuzz-1.log"]


def test_a_fuzzer_that_disagrees_with_the_assumption_is_the_finding(
    sound: Bundle, settings: Settings
) -> None:
    bundle = staged(sound, assuming(PARSE))
    reviewed(bundle, attacking("fuzz-1", PARSE, claim="a trailing space parses"))
    rigged = context(bundle, settings, outputs={"fuzz-fuzz-1": fuzzed(broke(PARSE))})

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.FAIL
    assert "a trailing space parses" in verdict.summary
    assert verdict.details["refuted"] == [PARSE]


def test_each_fuzzers_refutations_are_recorded_with_the_lines_that_show_them(
    sound: Bundle, settings: Settings
) -> None:
    """The first few of each, so one fuzzer's many lines do not hide another's finding.

    Every line goes to the evidence too, apart from the rest of what the fuzzers printed.
    """
    many = fuzzed(*(broke(PARSE, f"{digit} ") for digit in range(5)))
    bundle = staged(sound, assuming(PARSE, DUMP))
    reviewed(bundle, attacking("fuzz-1", PARSE), attacking("fuzz-2", DUMP))
    rigged = context(
        bundle, settings, outputs={"fuzz-fuzz-1": many, "fuzz-fuzz-2": fuzzed(broke(DUMP))}
    )

    verdict = AxiomSoundnessGate().run(rigged)

    witnesses = verdict.details["witnesses"]
    assert [line.split(":", 1)[0] for line in witnesses] == ["fuzz-1"] * 3 + ["fuzz-2"]
    assert witnesses[-1] == f"fuzz-2: {broke(DUMP)}"
    assert verdict.details["refutation_lines"] == {"fuzz-1": 5, "fuzz-2": 1}
    assert "evidence/fuzz-refuted.txt" in verdict.evidence
    recorded = read_text(bundle.root / "evidence" / "fuzz-refuted.txt").splitlines()
    assert len(recorded) == 6
    assert recorded[4].startswith(f"fuzz-1: benchproofer:refuted {PARSE} loads('4 ')")


def test_a_fuzzer_that_broke_on_its_own_bug_is_set_aside_rather_than_counted(
    sound: Bundle, settings: Settings
) -> None:
    """A reviewer's program crashing is not a callee behaving otherwise."""
    bundle = staged(sound, assuming(PARSE))
    reviewed(bundle, attacking("fuzz-1", PARSE))
    rigged = context(
        bundle, settings, outputs={"fuzz-fuzz-1": OracleResult.no("NameError: parse")}
    )

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert f"left {PARSE} unattacked" in verdict.summary
    assert "set aside: fuzz-1 failed without naming a disagreement" in verdict.summary


def test_a_fuzzer_nothing_here_can_run_is_set_aside(sound: Bundle, settings: Settings) -> None:
    bundle = staged(sound, assuming(PARSE))
    reviewed(bundle, attacking("fuzz-1", PARSE))
    rigged = context(
        bundle, settings, outputs={"fuzz-fuzz-1": OracleResult.unavailable("no runtime")}
    )

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "set aside: fuzz-1 could not be run" in verdict.summary


def test_a_fuzzer_whose_program_the_review_never_wrote_is_set_aside(
    sound: Bundle, settings: Settings
) -> None:
    """Nothing is run for it either: there is no program to put to the environment."""
    bundle = staged(sound, assuming(PARSE))
    reviewed(bundle, attacking("fuzz-1", PARSE), write=False)
    rigged = context(bundle, settings)

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "set aside: fuzz-1 cannot be read" in verdict.summary
    assert rigged.probed == []
    assert verdict.evidence == []


def test_a_fuzzer_that_does_not_say_what_it_attacked_decides_none_of_it(
    sound: Bundle, settings: Settings
) -> None:
    bundle = staged(sound, assuming(PARSE, DUMP))
    reviewed(bundle, attacking("fuzz-1"))
    rigged = context(bundle, settings, outputs={"fuzz-fuzz-1": OracleResult.ok("exited 0")})

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert "does not say which unchanged callee it attacked" in verdict.summary
    assert verdict.details["unattacked"] == [PARSE, DUMP]


def test_a_fuzzer_may_leave_its_callee_implicit_when_only_one_is_assumed(
    sound: Bundle, settings: Settings
) -> None:
    """With one assumption on record there is nothing else the program can be about."""
    bundle = staged(sound, assuming(PARSE))
    reviewed(bundle, attacking("fuzz-1"))
    rigged = context(bundle, settings, outputs={"fuzz-fuzz-1": OracleResult.ok("exited 0")})

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.PASS
    assert PARSE in verdict.summary


def test_an_assumption_nobody_attacked_has_only_the_bundles_own_axioms_py_behind_it(
    sound: Bundle, settings: Settings
) -> None:
    """Which is the floor, so the gate declines rather than passing on the other one."""
    bundle = staged(sound, assuming(PARSE, DUMP))
    reviewed(bundle, attacking("fuzz-1", PARSE))
    rigged = context(bundle, settings, outputs={"fuzz-fuzz-1": OracleResult.ok("exited 0")})

    verdict = AxiomSoundnessGate().run(rigged)

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["unattacked"] == [DUMP]
    assert not verdict.ok


# ---- an assumption about the answer --------------------------------------


#: A fix that renames the function the task is about, so the patch names a symbol an
#: assumption could reach for, under a hunk header naming the function above it.
RENAMES, _ = revised(
    "pkg/change.py",
    "def outer():\n    return 0\n\n\ndef make_change(cents):\n    return cents\n",
    "def outer():\n    return 0\n\n\ndef make_change(cents, coins):\n    return cents\n",
    header="def outer():",
)


def _patched(bundle: Bundle, task: Task, patch: str = RENAMES) -> Bundle:
    """Freeze ``task`` with ``patch`` as its fix."""
    write_json(
        bundle.task_path,
        task.model_copy(update={"reference": Reference(patch=patch)}).model_dump(mode="json"),
    )
    return bundle


def test_a_callee_named_like_what_the_fix_edits_is_not_the_grounding_gates_to_judge(
    sound: Bundle, settings: Settings, coin_change: Task
) -> None:
    """A name match decides nothing: an edit may leave the callee's behaviour alone.

    Whether the golden patch changes the callee is the equivalence auditor's question.
    """
    callee = "pkg.change.make_change"
    source = assuming(callee)
    staged(_patched(sound, coin_change), source, grounding=harness(source))
    rigged = context(sound, settings, outputs={"axioms": agreed(callee)})

    assert AxiomsGroundedGate().run(rigged).status is Status.PASS
