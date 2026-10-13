# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Inputs a conformance comparison is put to again, whichever `conformance.py` makes it.

A `conformance.py` reproduces its own disagreements from its seed, and nothing else: a rewritten
`conformance.py` draws other inputs, and a reviewer's input was never drawn. Pinned here are the
protocol lines that carry an input across, the record that keeps it, and what the gate
makes of a run that did or did not put it back.
"""

from __future__ import annotations

import ast

import pytest

from benchproofer.config import Settings
from benchproofer.core import replay
from benchproofer.core.bundle import Bundle
from benchproofer.core.differential import (
    ANSWERED_BY,
    REPLAY,
    arguments,
    inadmissible,
    inserted,
    names_entry,
    protocol_for,
    replayed,
    unparsed,
    with_replay,
    witnessed,
)
from benchproofer.core.readings import SPEC, readings
from benchproofer.core.verdict import Level, SkipReason, Status
from benchproofer.gates.conformance import ConformanceGate
from benchproofer.oracles.base import OracleResult
from benchproofer.util.fsio import read_json, write_text
from doubles import Rigged, Screening

SYMBOL = "change.make_change"


def run(bundle: Bundle, settings: Settings, output: str, ok: bool = True) -> Rigged:
    """A context whose environment prints ``output`` for the conformance program."""
    result = (
        OracleResult.ok("conformance exited 0", output=output)
        if ok
        else OracleResult.no("conformance exited 1", output=output)
    )
    return Rigged(
        bundle=bundle,
        settings=settings,
        level=Level.ORACLE,
        backend=Screening(),
        outputs={"conformance": result},
    )


COMPARED = f"benchproofer:compared {SYMBOL} 100000 amounts from a seeded draw\n"


def spec_of(bundle: Bundle) -> str:
    return readings(bundle, Screening())[SPEC]


# ---- the protocol --------------------------------------------------------


def test_an_argument_tuple_is_kept_in_one_spelling() -> None:
    assert arguments("(40,)") == "(40,)"
    assert arguments(" ( 40 , ) ") == "(40,)"
    assert arguments("(b'x', [1, 2], {'a': None})") == "(b'x', [1, 2], {'a': None})"


def test_what_is_not_a_tuple_literal_cannot_be_put_back() -> None:
    """A bare value is ambiguous about arity, and a call is not a value at all."""
    assert arguments("40") is None
    assert arguments("Decimal('1.5'),") is None
    assert arguments("(object(),)") is None


def test_a_witness_line_is_read_once_per_input_by_function() -> None:
    output = (
        f"benchproofer:disagrees {SYMBOL} 40 -> the repository returns 4, the shadow 3\n"
        f"benchproofer:witness {SYMBOL} (40,)\n"
        f"benchproofer:witness {SYMBOL} (40, )\n"
        f"benchproofer:witness {SYMBOL} forty\n"
    )

    assert witnessed(output) == {SYMBOL: ("(40,)",)}


def test_the_replay_lines_are_read_rather_than_reported_as_unparsed() -> None:
    output = (
        f"benchproofer:witness {SYMBOL} (40,)\n"
        f"benchproofer:rechecked {SYMBOL} 2\n"
        f"benchproofer:inadmissible {SYMBOL} 1: a negative amount\n"
    )

    assert unparsed(output) == ()
    assert replayed(output) == {SYMBOL: 2}
    assert inadmissible(output) == {
        SYMBOL: {1: f"benchproofer:inadmissible {SYMBOL} 1: a negative amount"}
    }


def test_the_protocol_says_how_to_read_what_is_handed_back() -> None:
    protocol = protocol_for(100_000)
    assert f'globals().get("{REPLAY}", {{}})' in protocol
    assert "benchproofer:witness <function>" in protocol
    assert "benchproofer:rechecked <function>" in protocol
    assert "benchproofer:inadmissible <function>" in protocol


def test_the_inputs_are_written_where_python_lets_a_module_start() -> None:
    """After the docstring and the `__future__` imports, which have to come first."""
    harness = '"""Compare."""\nfrom __future__ import annotations\n\nimport change\n'

    ran = with_replay(harness, {SYMBOL: ["(40,)", "(0,)"]})

    tree = ast.parse(ran)
    assigned = next(node for node in tree.body if isinstance(node, ast.Assign))
    assert ast.literal_eval(assigned.value) == {SYMBOL: [(40,), (0,)]}
    assert tree.body.index(assigned) == 2
    assert with_replay(harness, {}) == harness


@pytest.mark.parametrize(
    ("program", "expected"),
    [
        (
            '"""Compare."""\nfrom __future__ import annotations  # a\nimport change\n',
            '"""Compare."""\nfrom __future__ import annotations; X = 1  # a\nimport change\n',
        ),
        ("import change\n\nchange.run()\n", "X = 1; import change\n\nchange.run()\n"),
        (
            "#!/usr/bin/env python\n@cached\ndef run():\n    pass\n",
            "#!/usr/bin/env python\nX = 1\n@cached\ndef run():\n    pass\n",
        ),
    ],
    ids=["after-the-future-imports", "ahead-of-a-simple-statement", "before-a-decorated-def"],
)
def test_code_run_ahead_of_a_program_keeps_its_lines_where_python_allows(
    program: str, expected: str
) -> None:
    """A traceback then names the program's own lines, but for a compound first statement."""
    assert inserted(program, "X = 1") == expected


# ---- the record ----------------------------------------------------------


def test_an_input_is_recorded_once_and_with_who_found_it(sound: Bundle) -> None:
    first = replay.record(sound, {SYMBOL: ("(40,)",)}, source=replay.GATE, spec="s")
    again = replay.record(sound, {SYMBOL: ("(40,)", "(5,)")}, source=replay.GATE, spec="t")

    assert [item.arguments for item in first] == ["(40,)"]
    assert [(item.arguments, item.source, item.spec) for item in again] == [
        ("(5,)", replay.GATE, "t")
    ]
    assert [item.arguments for item in replay.stored(sound)] == ["(40,)", "(5,)"]


def test_the_record_keeps_the_first_inputs_found_for_a_function(sound: Bundle) -> None:
    many = tuple(f"({number},)" for number in range(replay.LIMIT + 5))

    replay.record(sound, {SYMBOL: many}, source=replay.GATE, spec="s")

    assert [item.arguments for item in replay.stored(sound)] == list(many[: replay.LIMIT])


def test_a_damaged_entry_is_skipped_rather_than_failing_the_read(sound: Bundle) -> None:
    write_text(
        sound.evidence_dir / replay.FILE,
        '[{"function": "f"}, {"function": "f", "arguments": "(1,)", "source": "g", '
        '"spec": ""}]',
    )

    assert [item.arguments for item in replay.stored(sound)] == ["(1,)"]


# ---- the gate ------------------------------------------------------------


def test_a_disagreement_s_input_is_kept_for_the_next_run(
    sound: Bundle, settings: Settings
) -> None:
    output = (
        f"benchproofer:disagrees {SYMBOL} 40 -> the repository returns 4, the shadow 3\n"
        f"benchproofer:witness {SYMBOL} (40,)\n{COMPARED}"
    )

    verdict = ConformanceGate().run(run(sound, settings, output, ok=False))

    assert verdict.status is Status.FAIL
    assert [(item.function, item.arguments, item.source) for item in replay.stored(sound)] == [
        (SYMBOL, "(40,)", replay.GATE)
    ]
    assert any(key.endswith(f"/evidence/{replay.FILE}") for key in verdict.inputs)


def test_every_input_on_record_is_handed_to_the_run(sound: Bundle, settings: Settings) -> None:
    replay.record(sound, {SYMBOL: ("(40,)",)}, source=replay.GATE, spec=spec_of(sound))
    rigged = run(sound, settings, f"{COMPARED}benchproofer:rechecked {SYMBOL} 1\n")

    verdict = ConformanceGate().run(rigged)

    assert verdict.status is Status.PASS
    assert f"{REPLAY} = {{{SYMBOL!r}: [(40,)]}}" in rigged.probed[0].source
    assert verdict.details["rechecked"] == {SYMBOL: 1}


def test_a_run_that_did_not_put_an_input_back_is_undecided(
    sound: Bundle, settings: Settings
) -> None:
    """Agreement over a draw that left out the input it disagreed on is not agreement."""
    replay.record(sound, {SYMBOL: ("(40,)", "(5,)")}, source=replay.GATE, spec=spec_of(sound))

    verdict = ConformanceGate().run(run(sound, settings, COMPARED))

    assert verdict.status is Status.SKIP
    assert verdict.skip_reason is SkipReason.INCONCLUSIVE
    assert verdict.details["not_rechecked"] == [
        f"{SYMBOL} (0 of 2 compared or declared inadmissible)"
    ]
    assert REPLAY in verdict.summary


@pytest.mark.parametrize("spec", ["this specification", "an earlier specification"])
def test_an_input_a_conformance_py_drew_may_not_be_declined_under_any_specification(
    sound: Bundle, settings: Settings, spec: str
) -> None:
    """A `conformance.py` built that value the way the repository's callers build it.

    So the run has to say what the two sides do on it, whichever specification was in force
    when it was drawn. Believing the declaration for an input drawn under an earlier one
    would let a precondition narrowed around a disagreement bury the input that shows it.
    """
    recorded = spec_of(sound) if spec == "this specification" else spec
    replay.record(sound, {SYMBOL: ("(40,)",)}, source=replay.GATE, spec=recorded)
    output = f"{COMPARED}benchproofer:inadmissible {SYMBOL} 0: out of range\n"

    verdict = ConformanceGate().run(run(sound, settings, output))

    assert verdict.status is Status.SKIP
    assert "declared inadmissible" in verdict.details["not_rechecked"][0]
    assert read_json(sound.evidence_dir / replay.FILE)[0]["spec"] == recorded


@pytest.mark.parametrize("disagrees", [False, True], ids=["declined", "disagrees"])
def test_a_reviewer_s_defect_input_is_compared_or_declared_outside_the_preconditions(
    disagrees: bool, sound: Bundle, settings: Settings
) -> None:
    """No run drew it, so a precondition that does not admit it shows the defect is not one.

    Compared, a disagreement on it fails the gate as one on a drawn input does.
    """
    replay.record(sound, {SYMBOL: ("(40,)",)}, source=replay.REVIEW, spec=spec_of(sound))
    output = (
        f"benchproofer:disagrees {SYMBOL} 40 -> the repository raises, the shadow returns 4\n"
        f"{COMPARED}benchproofer:rechecked {SYMBOL} 1\n"
        if disagrees
        else f"{COMPARED}benchproofer:inadmissible {SYMBOL} 0: a negative amount\n"
    )

    verdict = ConformanceGate().run(run(sound, settings, output, ok=not disagrees))

    assert verdict.status is (Status.FAIL if disagrees else Status.PASS)
    assert "not_rechecked" not in verdict.details


#: An `Outside the bridge` entry naming inputs the fixed function answers before the fix's
#: lines run.
ENTRY = (
    "a negative amount: make_change raises at change.py:9, before any line the patch changes"
)


@pytest.mark.parametrize("named", [True, False], ids=["names the entry", "names none"])
def test_an_input_an_outside_the_bridge_entry_names_may_be_skipped_drawn_or_handed(
    named: bool, sound: Bundle, settings: Settings
) -> None:
    """There the fixed function never reaches what the fix changes, so it is not compared.

    The declaration has to quote the entry, and the verdict keeps it for the equivalence
    auditor, which traces the input through the fixed function.
    """
    write_text(sound.correspondence_path, f"# Map\n\n## Outside the bridge\n\n* {ENTRY}\n")
    replay.record(sound, {SYMBOL: ("(-40,)",)}, source=replay.GATE, spec=spec_of(sound))
    reason = f"{ANSWERED_BY} {ENTRY if named else 'a negative amount is never drawn'}"
    skipped = [
        f"benchproofer:inadmissible {SYMBOL} 0: {reason}",
        f"benchproofer:excluded (-3,): {reason}",
    ]
    output = COMPARED + "".join(f"{line}\n" for line in skipped)

    verdict = ConformanceGate().run(run(sound, settings, output))

    assert verdict.status is (Status.PASS if named else Status.SKIP)
    assert verdict.details["outside"] == (skipped if named else [])
    assert not names_entry(f"{ANSWERED_BY} a negative amount", ENTRY)
