# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The verified implementation agrees with the code the golden patch leaves.

Verification establishes that the implementation meets the specification. This gate
establishes the other half: that the implementation, executed, does what the
repository's own code does. Together they are the claim a formalized benchmark makes,
and without this half a bundle proves only that two documents agree with each other.

The check is a differential comparison, not a test run. `conformance.py` holds a
Python copy of the implementation, draws inputs, calls the real function in the
tree with the golden patch applied, calls the copy on the corresponding
inputs, and reports any disagreement. That makes the gate a refutation instrument: it
cannot show the copy is faithful, but one disagreement shows it is not, over
as many inputs as `conformance.py` can draw rather than the handful the repository's tests
happen to exercise.

Running the benchmark's test suite against the Python copy would not decide this
question. The copy is one function and a realistic fix spans several files, so
the suite would fail on the absence of the rest of the fix, which is a fact about the
benchmark's change and not about the implementation. See
`benchproofer.core.differential` for why the copy lives inside `conformance.py`
rather than being written over the function it is compared against.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import ClassVar

from ..core import replay
from ..core.differential import (
    BLOCKED,
    DIRECT,
    HARNESS,
    REPLAY,
    TRANSLITERATED,
    answered,
    blocked,
    carried,
    clipped,
    compared,
    comparisons,
    disagreements,
    excluded,
    executables,
    inadmissible,
    lacking,
    names_entry,
    provenance,
    replayed,
    seed,
    shapes_for,
    skipped_regions,
    uncopied,
    ungrounded,
    unparsed,
    unsupported,
    with_replay,
    witnessed,
    witnesses,
)
from ..core.markers import is_marker
from ..core.readings import SPEC, readings
from ..core.verdict import Level, SkipReason, Verdict
from ..errors import BenchproofError
from ..log import progress
from ..oracles.base import Oracle, OracleStatus, Program
from ..util.digest import digest_text
from .audit import OUTSIDE, listed_under
from .base import Gate, GateContext
from .support import join_lines

__all__ = ["ConformanceGate"]


class ConformanceGate(Gate):
    """Compare a Python copy of the verified implementation with the real code."""

    id: ClassVar[str] = "impl.conformance"
    title: ClassVar[str] = "Conformance gate"
    rationale: ClassVar[str] = (
        "Catches a bundle that verifies against a specification describing "
        "something other than the task the benchmark poses."
    )
    level: ClassVar[Level] = Level.ORACLE
    sources: ClassVar[tuple[str, ...]] = (
        "solution.*",
        HARNESS,
        "correspondence.md",
        f"evidence/{replay.FILE}",
        "../task.json",
    )

    def judge(self, context: GateContext) -> Verdict:
        """Run the bundle's `conformance.py` and read what it established."""
        task = context.task
        if task.reference.is_empty:
            return self.undecided(
                SkipReason.NOT_APPLICABLE,
                f"{task.key} ships no golden patch, so there is no repository "
                "code for the implementation to be compared with",
            )

        harness = context.bundle.conformance()
        if harness is None or not harness.strip():
            return self.failed(
                f"the bundle ships no {HARNESS} to compare the verified implementation "
                "with the fixed code",
            )

        backend = context.backend
        # One body per function the specification models, all of which `conformance.py` runs.
        bodies = executables(context.solution, backend)
        executable = "\n".join(bodies.values())
        how = (
            DIRECT
            if all(
                provenance(backend.extension, body, backend.foreign_tokens) == DIRECT
                for body in bodies.values()
            )
            else TRANSLITERATED
        )
        # A `conformance.py` that marks the implementation it carries is held to that region
        # rather than to the file, which is a sharper check and what lets the audited
        # auditor put a reviewer's submission through the same comparison. One without the
        # marker is read whole: its absence is not a defect in the comparison.
        marked = carried(harness)
        missing = (
            uncopied(
                harness,
                bodies,
                skipped=skipped_regions(harness, context.solution, backend.comment),
            )
            if how == DIRECT
            else None
        )
        if missing is not None:
            region, line = missing
            return self.failed(
                f"{HARNESS} does not contain the verified implementation verbatim, so "
                "what it compares is a second implementation rather than the one the "
                f"checker accepted: {lacking(missing)}",
                provenance=how,
                impl_digest=digest_text(executable),
                region=region,
                **({"missing": line} if line else {}),
            )

        oracle = self.needs_oracle(context)
        if isinstance(oracle, Verdict):
            return oracle

        target = context.settings.inputs_for(task.benchmark)
        # Every input on record is handed to the run, whichever `conformance.py` makes it, so
        # one a rewritten program no longer draws is compared all the same.
        on_record = replay.by_function(replay.stored(context.bundle))
        handed = {
            function: [item.arguments for item in items]
            for function, items in on_record.items()
        }
        progress(
            "running %s against the tree with the golden patch applied, for up to %d s",
            HARNESS,
            context.settings.harness_timeout_s,
        )
        result = oracle.probe(
            task,
            # Always against the golden patch: the function being compared is
            # the one the fix produces, and at the base commit it may not exist.
            Program(
                source=with_replay(harness, handed), label="conformance", with_reference=True
            ),
            workdir=context.scratch("conformance"),
            timeout_s=context.settings.harness_timeout_s,
        )
        evidence = context.bundle.write_evidence("conformance.log", result.output + "\n")
        spec = readings(context.bundle, backend).get(SPEC, "")
        recorded = replay.record(
            context.bundle, witnessed(result.output), source=replay.GATE, spec=spec
        )
        counted = compared(result.output)
        drawn = seed(result.output)
        declined = unsupported(result.output)
        set_aside = excluded(result.output)
        entries = listed_under(context.bundle, OUTSIDE)
        outside = [line for line in answered(result.output) if names_entry(line, entries)]
        common: dict[str, object] = {
            "oracle": oracle.name,
            # What was compared: the implementation itself, or a translation of it.
            # Recorded rather than pooled, because a translated comparison tests the
            # implementation as translated.
            "provenance": how,
            # Whether a reviewer's submission can be put through this `conformance.py`.
            "substitutable": marked is not None,
            "impl_digest": digest_text(executable),
            "compared_inputs": counted,
            "compared": [
                {"symbol": item.symbol, "inputs": item.inputs}
                for item in comparisons(result.output)
            ],
            "target_inputs": target,
            # What makes a disagreement reproducible. Recorded rather than required: a
            # `conformance.py` that reports no seed still compared what it says it compared, so
            # its absence weakens the record without invalidating it.
            "seed": drawn,
            "oracle_duration_s": round(result.duration_s, 3),
            "evidence": [evidence],
            "rechecked": {function: len(items) for function, items in handed.items()},
            "witnessed": len(recorded),
            # Drawn and set aside as a precondition excludes, which a reader can check.
            "excluded_lines": len(set_aside),
            # Drawn or handed and not compared because an `Outside the bridge` entry names
            # them, which the equivalence auditor checks by tracing.
            "outside": list(clipped(outside, OUTSIDE_LIMIT)),
        }

        if result.status is OracleStatus.UNAVAILABLE:
            return self.undecided(
                SkipReason.ORACLE_UNAVAILABLE,
                f"{HARNESS} could not be run here: {result.detail}",
                **common,
            )
        if result.timed_out:
            return self.timed_out(f"{HARNESS} did not finish: {result.detail}", **common)
        if result.status is OracleStatus.ERROR:
            return self.errored(f"{HARNESS} could not be run: {result.detail}", **common)

        adrift = ungrounded(result.output, harness)
        if adrift and result.resolved:
            return self.failed(
                f"{HARNESS} reports comparing {join_lines(adrift)}, which names no "
                "module it imports, so what it compared the implementation with is "
                "code of its own rather than the repository's",
                ungrounded=list(adrift),
                **common,
            )

        disagreed = disagreements(result.output)
        if disagreed:
            found, shown = witnesses(result.output)
            return self.failed(
                f"the repository's own code disagrees with the verified implementation "
                f"on {join_lines(disagreed)}, so the proof is about a different program",
                disagrees=list(disagreed),
                # Lines, not inputs: a `conformance.py` may stop printing after the first few.
                disagreement_lines=found,
                witnesses=list(shown),
                **common,
            )
        # After the disagreement, which is a finding whatever else `conformance.py` could not
        # do. A protocol line no reader parses comes first, since every check below reads
        # the report as though it were complete: a comparison printed that way would count
        # as none and a disagreement as agreement. The gaps `conformance.py` declared come
        # next, before anything reads its silence about those parts as agreement, and an
        # input it did not compare first among them, as the narrower gap.
        unread = unparsed(result.output)
        if unread:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"{HARNESS} printed {len(unread):,} line(s) starting with `benchproofer:` "
                f"that no line of the protocol parses, the first `{clipped(unread, 1)[0]}`, "
                "where the protocol has "
                + " or ".join(f"`{shape}`" for shape in shapes_for(unread[0]))
                + "; what those lines say was not read, so the run is undecided rather "
                "than taken to have reported only what its other lines do",
                unparsed_lines=len(unread),
                witnesses=list(clipped(unread)),
                expected=list(dict.fromkeys(s for line in unread for s in shapes_for(line))),
                **({"unsupported": list(declined)} if declined else {}),
                **common,
            )
        # An input set aside as excluded is not compared either, and counts as blocked
        # unless the line it quotes is one of the specification's or names an entry.
        unstated = _unstated(set_aside, context, entries)
        uncompared = (*blocked(result.output), *unstated)
        if uncompared:
            counts = _reasons(uncompared)
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"{HARNESS} did not compare {len(uncompared):,} input(s) the specification "
                f"admits: {_counted(counts)}. What it compared says nothing about them, and "
                "each line says why. "
                + " ".join(_REMEDIES[reason] for reason in _REASONS if counts.get(reason))
                + " A raise of the function compared, inside the call, is none of these: it is "
                "the function's behaviour, which conformance.py compares like a return and the "
                "specification states",
                blocked_lines=len(uncompared),
                blocked_by=counts,
                witnesses=list(clipped(uncompared)),
                **({"unsupported": list(declined)} if declined else {}),
                **common,
            )
        if declined:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"{HARNESS} reports it could not compare {join_lines(declined)}, so what "
                "it did compare establishes nothing about that part of the implementation",
                unsupported=list(declined),
                **common,
            )
        if not result.resolved:
            return self.failed(
                f"{HARNESS} failed without naming a disagreement ({result.detail}), so "
                "it does not run in the task's environment",
                **common,
            )
        if not counted:
            return self.failed(
                f"{HARNESS} ran and reported comparing nothing, so whatever it did "
                "establishes no agreement between the implementation and the repository",
                **common,
            )
        qualifier = (
            ", of the implementation as translated into Python" if how == TRANSLITERATED else ""
        )
        # A shortfall against the target is recorded and not penalized: it usually means
        # repository code too slow for the target to fit the budget, a fact about the
        # task rather than a defect in the artifacts. The count is on the verdict either
        # way, since agreement over a few thousand inputs is worth less than over a
        # hundred thousand.
        short = (
            f", short of the {target:,} aimed at"
            if counted < target
            else f", the {target:,} aimed at"
        )
        # A run with no reported seed cannot be repeated. It is said in the summary rather
        # than in the status, because the agreement it found is real.
        unrepeatable = "" if drawn else ", from a draw it reported no seed for"
        dropped = _unreplayed(on_record, result.output, entries)
        if dropped:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"{HARNESS} did not put back every input on record for it -- "
                f"{join_lines(dropped)} -- so an input on which the implementation was "
                "found to disagree with the repository went "
                f"uncompared; it has to read `{REPLAY}` as the protocol says",
                not_rechecked=list(dropped),
                **common,
            )
        # Last, because it is a second run of `conformance.py`, which a bundle pays for once and
        # only when it passes: whether `conformance.py` tells the fixed code from the code
        # before it, as `spec.discriminates` asks of a pre-fix implementation. One that does not
        # is noted beside the agreement it found, which stands, for the equivalence auditor to
        # weigh.
        blind = _undiscriminating(context, oracle, harness, handed)
        return self.passed(
            f"the implementation and the repository's own code agree over {counted:,} "
            f"compared input(s){short}{qualifier}{unrepeatable}"
            + (f"; note: {blind}" if blind else ", and disagree with the code before the fix"),
            **({"undiscriminating": blind} if blind else {}),
            **common,
        )


def _undiscriminating(
    context: GateContext,
    oracle: Oracle,
    harness: str,
    handed: Mapping[str, Sequence[str]],
) -> str:
    """Why a `conformance.py` cannot tell the fixed code from the code before the fix, or "".

    The same `conformance.py`, the same inputs, run against the task's base commit. There it
    should report a disagreement: the implementation is of the code the fix produces, so against
    the code it replaced the two come apart somewhere. A run that compares inputs and finds none
    is reading a value the fix leaves alone -- an emptied cache nobody reads back, a constant, a
    field the fix does not touch -- and its agreement with the fixed code does not cover the
    change. A run that cannot get that far is evidence of its own: code the `conformance.py`
    reaches only once the fix is applied is code the fix adds.
    """
    progress(
        "running %s again, against the task's base commit, for up to %d s: it passed, and "
        "this run shows whether it tells the fixed code from the code before the fix",
        HARNESS,
        context.settings.harness_timeout_s,
    )
    result = oracle.probe(
        context.task,
        Program(source=with_replay(harness, handed), label="conformance-base"),
        workdir=context.scratch("conformance", "base"),
        timeout_s=context.settings.harness_timeout_s,
    )
    counted = compared(result.output)
    if not result.resolved or disagreements(result.output) or not counted:
        return ""
    return (
        f"{HARNESS} reports the same agreement against the task's base commit, over "
        f"{counted:,} input(s) there with no disagreement, so what it compares does not "
        "depend on the fix and its evidence does not cover the change"
    )


#: Why `conformance.py` did not compare an input, by the word its line opens with, in the
#: order a summary counts them: the three reasons a `blocked` line may name (`ALIASES`),
#: a `blocked` line that names none of them, and an `excluded` line quoting nothing.
_REASONS: tuple[str, ...] = ("unbuildable", "refused", "copy-raised", BLOCKED, "excluded")
#: How a summary counts the inputs not compared for each reason.
_COUNTED: dict[str, str] = {
    "unbuildable": "{n:,} it could not build (`unbuildable`)",
    "refused": "{n:,} the repository refused to construct (`refused`)",
    "copy-raised": "{n:,} on which its copy of the implementation raised (`copy-raised`)",
    BLOCKED: "{n:,} it gave no reason word for (`blocked`)",
    "excluded": "{n:,} set aside as `excluded` by a line the specification does not have",
}
#: What a summary says of the inputs not compared for each reason.
_REMEDIES: dict[str, str] = {
    "unbuildable": (
        f"An input {HARNESS} could not build is a defect of {HARNESS}: it builds each value "
        "the way the repository's own callers or tests build it."
    ),
    "refused": (
        "A value the repository refuses to construct is one the specification admits and "
        "the repository never has: an `Outside the bridge` entry of the first kind names "
        f"such values, with {HARNESS} building each input from a repository value made the "
        "way the repository's callers make one, so that it draws none of them."
    ),
    "copy-raised": (
        f"A raise of {HARNESS}'s copy of the implementation is a defect of that copy, since "
        "the implementation raises nothing its specification does not declare."
    ),
    BLOCKED: (
        "A `blocked` line names no reason: it says `unbuildable`, `refused` or "
        "`copy-raised` instead."
    ),
    "excluded": (
        "An `excluded` line quotes the line of the specification stating the precondition "
        "as the specification writes it, or names an `Outside the bridge` entry."
    ),
}
#: How many of the lines that skip an input an `Outside the bridge` entry names a verdict
#: keeps, for the equivalence auditor to check.
OUTSIDE_LIMIT = 20
#: How much of a line of the specification an `excluded` line has to quote: a closing
#: bracket or a lone `by` is in every specification.
_STATED = 8


def _reasons(lines: Sequence[str]) -> dict[str, int]:
    """How many of the lines naming an input not compared give each reason (`_REASONS`)."""
    counts = Counter(
        word
        if (word := line.split(maxsplit=1)[0].removeprefix("benchproofer:")) in _REASONS
        else BLOCKED
        for line in lines
    )
    return {reason: counts[reason] for reason in _REASONS if counts[reason]}


def _counted(counts: Mapping[str, int]) -> str:
    """The counts of `_reasons`, in words."""
    return join_lines([_COUNTED[reason].format(n=n) for reason, n in counts.items()])


def _unstated(lines: Sequence[str], context: GateContext, entries: str) -> tuple[str, ...]:
    """The `excluded` lines that quote no line of the specification judged.

    Whitespace-normalized, and neither a comment nor a marker counts: a precondition is
    something the checker reads. One naming an `Outside the bridge` entry of ``entries``
    instead is stated too (`names_entry`).
    """
    if not lines:
        return ()
    comment = context.backend.comment
    try:
        view = context.backend.spec_view(context.solution)
    except BenchproofError:
        view = ""
    stated = [
        " ".join(line.split())
        for line in view.splitlines()
        if len("".join(line.split())) >= _STATED
        and not is_marker(line, comment)
        and not line.strip().startswith(comment)
    ]
    return tuple(
        line
        for line in lines
        if not names_entry(line, entries)
        and not any(quoted in " ".join(line.split()) for quoted in stated)
    )


def _unreplayed(
    on_record: dict[str, list[replay.Witness]], output: str, entries: str
) -> tuple[str, ...]:
    """What a run did with the inputs it was handed, where it fell short, by function.

    Each input has to be compared or declared inadmissible, and a declaration is the
    program's own word for skipping an input: believed for one the declaration says an
    `Outside the bridge` entry of ``entries`` names (`names_entry`), which the equivalence
    auditor checks, and for the input of a defect the attack auditor filed (`replay.REVIEW`),
    which no run drew: a precondition that does not admit it shows the defect is not one. One
    a run of the program drew may not be declined otherwise, whichever specification drew it:
    that run built the value the way the repository's callers build it, so the run has to say
    what the two sides do on it or why it could not compare it (`blocked`).
    Letting it skip an input instead would let a precondition narrowed around a
    disagreement bury the input that shows it.
    """
    compared_back = replayed(output)
    declined = inadmissible(output)
    short: list[str] = []
    for function, items in on_record.items():
        lines = declined.get(function, {})
        skipped = sorted(position for position in lines if position < len(items))
        wrongly = [
            position
            for position in skipped
            if items[position].source != replay.REVIEW
            and not names_entry(lines[position], entries)
        ]
        answered = compared_back.get(function, 0) + len(skipped)
        if answered < len(items):
            short.append(
                f"{function} ({answered} of {len(items)} compared or declared inadmissible)"
            )
        if wrongly:
            short.append(
                f"{function} input(s) {', '.join(map(str, wrongly))}, declared inadmissible "
                f"although a run of {HARNESS} drew them"
            )
    return tuple(short)
