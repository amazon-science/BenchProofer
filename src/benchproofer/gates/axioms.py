# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What the specification assumes of the world, checked against the world.

A proof about realistic code is a proof modulo its assumptions. A task that parses
JSON, opens a socket, or calls into another subsystem of its own repository cannot be
verified at all unless some of those callees are assumed rather than modeled, and the
assumption is then exactly as good as the model behind it. An assumption nobody
checked is where a bundle stops being about the program the benchmark ships.

Two gates close that gap, from the two sides the rest of the ladder uses:

* `spec.axioms_grounded` runs the bundle's own `axioms.py` in the
  environment the benchmark's tests run in, and requires it to report every callee
  the `axioms` region declares, and to call each one. A program
  written by whoever wrote the assumption tends to exercise what the assumption
  already covers, which is why passing this is a floor rather than an argument.
* `audit.axiom_soundness` re-runs the fuzzers an independent review wrote against the
  same assumptions. That is the argument, and it is the same shape as
  `spec.strength.battery` against `audit.spec_completeness`: the bundle's own
  evidence first, then someone else's attempt to break it.

Whether the golden patch changes a callee the axioms region names, the other half of the paper's
axiom-soundness gate, is `audit.equivalence`'s: an `axiom` row stands only for a callee the
golden patch does not change.

Both read the protocol in `core.axioms`, and both treat a `benchproofer:refuted` line
as a counterexample rather than as a shortfall of a search. A disagreement between a
model and the callee it models was observed happening, which is evidence under a
falsifier exactly as much as under a prover.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from ..core.axioms import (
    HARNESS,
    against_reference,
    callees,
    calls,
    declared,
    declared_in,
    grounded,
    refutations,
    refuted_lines,
    with_calls,
)
from ..core.bundle import Fuzzer
from ..core.differential import clipped
from ..core.markers import parse
from ..core.runnable import quotes_lines, unquoted
from ..core.verdict import Level, SkipReason, Verdict
from ..errors import BundleError, MarkerError
from ..oracles.base import Oracle, OracleResult, OracleStatus, Program
from .audit import AuditGate
from .base import Gate, GateContext
from .support import join_lines

__all__ = ["AxiomSoundnessGate", "AxiomsGroundedGate"]


@dataclass(frozen=True, slots=True)
class _Attack:
    """What re-running one of a review's fuzzers established."""

    fuzzer: Fuzzer
    summary: str
    evidence: str = ""
    callee: str = ""
    #: The fuzzer named a disagreement between the assumption and the real callee.
    refuted: bool = False
    #: Every refutation it printed, whole: the input and what each side did on it.
    lines: tuple[str, ...] = ()
    #: The fuzzer ran to completion and found nothing, so its callee is attacked.
    settled: bool = False


def _region(context: GateContext) -> str | None:
    """The solution's `axioms` region, or None when its markers cannot be read.

    An unreadable file is not this gate's finding: `spec.hygiene` is where a malformed
    solution is reported, and a second gate reporting it would turn one defect into
    two.
    """
    try:
        regions = parse(context.solution, context.backend.comment)
    except MarkerError:
        return None
    axioms = regions.get("axioms")
    return "" if axioms is None else axioms.text


def _probe(
    context: GateContext,
    oracle: Oracle,
    source: str,
    label: str,
    assumed: Sequence[str],
) -> tuple[OracleResult, str]:
    """Run one grounding program through the oracle, and say where its log went.

    Against the tree with the golden patch applied where the program asks for it or an
    unchanged callee is defined in a file the fix changes (`against_reference`), which is
    the same tree for the bundle's own `axioms.py` and for a review's fuzzers.
    """
    patch = context.task.reference.patch or ""
    result = oracle.probe(
        context.task,
        Program(
            source=source,
            label=label,
            with_reference=against_reference(source, assumed, patch),
        ),
        workdir=context.scratch("axioms", label),
        timeout_s=context.settings.harness_timeout_s,
    )
    return result, context.bundle.write_evidence(f"{label}.log", result.output + "\n")


def _refutations(
    context: GateContext, name: str, found: Sequence[tuple[str, str]]
) -> list[str]:
    """Write every refutation a gate's programs printed, whole, and say where it went.

    ``found`` holds one ``(program, line)`` pair per line, the program empty where the
    gate ran only one. The verdict quotes the first few of each program's; this file
    keeps all of them, apart from everything else the programs printed, for a repair to
    read. It is written on every run, empty when nothing was refuted, so that a file left
    by an earlier judging never stands beside a verdict that did not read it, and it is
    named as evidence only when it holds something.
    """
    text = "".join(
        f"{program}: {line}\n" if program else f"{line}\n" for program, line in found
    )
    written = context.bundle.write_evidence(f"{name}-refuted.txt", text)
    return [written] if text else []


class AxiomsGroundedGate(Gate):
    """Run the bundle's own `axioms.py` over every callee its specification assumes."""

    id: ClassVar[str] = "spec.axioms_grounded"
    title: ClassVar[str] = "Unchanged callees agree with the real ones"
    rationale: ClassVar[str] = (
        "Catches a specification that assumes something false of a callee it did not "
        "model, which makes the proof about a program the benchmark does not ship."
    )
    level: ClassVar[Level] = Level.ORACLE
    sources: ClassVar[tuple[str, ...]] = ("solution.*", HARNESS, "../task.json")

    def judge(self, context: GateContext) -> Verdict:
        """Require an `axioms.py` for whatever is assumed, and require it to agree."""
        region = _region(context)
        harness = context.bundle.axioms()
        if region is None:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                "the solution's marker regions cannot be read, so what it assumes "
                "cannot be told; spec.hygiene (Hygiene check) is where that is reported",
            )
        assumed = callees(declared(region, context.backend.comment))
        if not assumed:
            if harness is None:
                return self.undecided(
                    SkipReason.NOT_APPLICABLE,
                    "the specification declares no unchanged callee, so there is nothing "
                    "to ground",
                )
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"the bundle ships {HARNESS} but the axioms region names no callee for "
                f"it to be about; add a '{context.backend.comment} benchproofer:axiom "
                f"<callee>' or '{context.backend.comment} benchproofer:models <callee>' line "
                "for each one",
            )
        if harness is None or not harness.strip():
            return self.failed(
                f"the specification assumes {join_lines(assumed)} without shipping "
                f"{HARNESS} to check any of them against the callee itself",
                assumed=list(assumed),
            )
        comment = context.backend.comment
        if context.backend.extension == ".py" and not quotes_lines(harness, region, comment):
            missing = unquoted(harness, region, comment)
            return self.failed(
                f"{HARNESS} does not contain the declarations of the axioms region, as code "
                "or quoted, so what it exercises is not what the checker was given"
                + (f"; the first line it lacks is `{missing}`" if missing else ""),
                assumed=list(assumed),
                **({"missing": missing} if missing else {}),
            )

        oracle = self.needs_oracle(context)
        if isinstance(oracle, Verdict):
            return oracle
        result, evidence = _probe(
            context, oracle, with_calls(harness, assumed), "axioms", assumed
        )
        reported = grounded(result.output)
        common = {
            "oracle": oracle.name,
            "assumed": list(assumed),
            "grounded": list(reported),
            "oracle_duration_s": round(result.duration_s, 3),
            "evidence": [evidence],
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

        refuted = refutations(result.output)
        lines = refuted_lines(result.output)
        common["evidence"] = [
            evidence,
            *_refutations(context, "axioms", [("", line) for line in lines]),
        ]
        if refuted:
            return self.failed(
                "the real callee disagrees with what the specification assumes of "
                f"{join_lines(refuted)}, so the proof is about a different program",
                refuted=list(refuted),
                # The lines, and not only the callees: which input, and what each side
                # did on it, is what tells a repair what part of the assumption is false.
                disagreement_lines=len(lines),
                witnesses=list(clipped(lines)),
                **common,
            )
        if not result.resolved:
            return self.failed(
                f"{HARNESS} failed without naming a disagreement ({result.detail}), so "
                "it does not run in the task's environment",
                **common,
            )
        ungrounded = [callee for callee in assumed if callee not in reported]
        if ungrounded:
            return self.failed(
                f"{HARNESS} passed without exercising {join_lines(ungrounded)}, which "
                "the specification assumes, so nothing was checked about them",
                ungrounded=ungrounded,
                **common,
            )
        recorded = calls(result.output)
        uncalled = {
            callee: recorded[callee][1]
            for callee in assumed
            if recorded.get(callee, ("", ""))[0] == "no"
        }
        if uncalled:
            return self.failed(
                f"{HARNESS} reports {join_lines(list(uncalled))} grounded without calling "
                f"it ({'; '.join(f'{callee}: {why}' for callee, why in uncalled.items())}), "
                "so the model was checked against something other than the callee the "
                "task's code calls",
                uncalled=uncalled,
                **common,
            )
        untold = {
            callee: recorded[callee][1] if callee in recorded else "the run left no record"
            for callee in assumed
            if recorded.get(callee, ("", ""))[0] != "yes"
        }
        if untold:
            common["calls_untold"] = untold
        return self.passed(
            f"{HARNESS} agrees with the real callee on {len(assumed)} assumption(s): "
            f"{join_lines(assumed)}"
            + (
                f"; whether it calls {join_lines(list(untold))} could not be told "
                f"({'; '.join(f'{callee}: {why}' for callee, why in untold.items())})"
                if untold
                else ""
            ),
            **common,
        )


class AxiomSoundnessGate(AuditGate):
    """Re-run the fuzzers an independent review wrote against the same assumptions.

    An assumption no fuzzer attacked leaves the gate undecided rather than passing. A
    fuzzer that fails without naming a disagreement is set aside rather than counted,
    since a program crashing on the reviewer's own bug has found nothing. Whether the golden
    patch changes a callee the axioms region names is the equivalence gate's question, not this
    one's.
    """

    id: ClassVar[str] = "audit.axiom_soundness"
    title: ClassVar[str] = "Axiom-soundness gate"
    rationale: ClassVar[str] = (
        f"Catches an assumption the bundle's own {HARNESS} confirms and an independent "
        f"fuzzer breaks, which is the case an {HARNESS} written by the assumption's own "
        "author is worst at finding."
    )
    sources: ClassVar[tuple[str, ...]] = (
        "solution.*",
        "audit/index.toml",
        "audit/*.fuzz.py",
        "../task.json",
    )

    def judge(self, context: GateContext) -> Verdict:
        """Run every fuzzer on record and report the disagreements they found."""
        assumed = callees(declared_in(context.solution, context.backend.comment))
        if not assumed:
            return self.undecided(
                SkipReason.NOT_APPLICABLE,
                "the specification declares no unchanged callee, so there is nothing for a "
                "fuzzer to attack",
            )
        review = self.review(context)
        if isinstance(review, Verdict):
            return review
        oracle = self.needs_oracle(context)
        if isinstance(oracle, Verdict):
            return oracle

        only = assumed[0] if len(assumed) == 1 else ""
        attacks = [
            self._attack(context, oracle, fuzzer, only, assumed) for fuzzer in review.fuzzers
        ]
        broken = [attack for attack in attacks if attack.refuted]
        written = _refutations(
            context,
            "fuzz",
            [(attack.fuzzer.id, line) for attack in broken for line in attack.lines],
        )
        common: dict[str, object] = {
            "reviewer": review.reviewer,
            "independent": review.independent,
            "oracle": oracle.name,
            "assumed": list(assumed),
            "fuzzers": [attack.fuzzer.id for attack in attacks],
            "evidence": [attack.evidence for attack in attacks if attack.evidence] + written,
        }
        if broken:
            return self.failed(
                "an independent fuzzer disagrees with what the specification assumes "
                f"of {join_lines(sorted({attack.callee for attack in broken}))}: "
                f"{join_lines([attack.summary for attack in broken])}",
                refuted=sorted({attack.callee for attack in broken}),
                # The first few lines of each fuzzer rather than of all of them together:
                # two fuzzers usually find two different things, and the first one's lines
                # would crowd out the second's.
                witnesses=[
                    f"{attack.fuzzer.id}: {line}"
                    for attack in broken
                    for line in clipped(attack.lines)
                ],
                refutation_lines={attack.fuzzer.id: len(attack.lines) for attack in broken},
                **common,
            )

        settled = {attack.callee for attack in attacks if attack.settled}
        aside = [attack.summary for attack in attacks if not attack.settled]
        trailer = f"; set aside: {join_lines(aside)}" if aside else ""
        unattacked = [callee for callee in assumed if callee not in settled]
        if unattacked:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"the review left {join_lines(unattacked)} unattacked, so that much has "
                f"only the bundle's own {HARNESS} behind it{trailer}",
                unattacked=unattacked,
                **common,
            )
        return self.passed(
            f"{len(settled)} unchanged callee(s) survived an independent fuzzer: "
            f"{join_lines(sorted(settled))}{trailer}",
            **common,
        )

    def _attack(
        self,
        context: GateContext,
        oracle: Oracle,
        fuzzer: Fuzzer,
        only: str,
        assumed: Sequence[str],
    ) -> _Attack:
        """Run one fuzzer and read what it established."""
        try:
            source = context.bundle.fuzzer_source(fuzzer)
        except BundleError as exc:
            return _Attack(fuzzer, f"{fuzzer.id} cannot be read: {exc}")
        callee = fuzzer.callee or only
        result, evidence = _probe(context, oracle, source, f"fuzz-{fuzzer.id}", assumed)
        refuted = refutations(result.output)
        if refuted:
            return _Attack(
                fuzzer,
                f"{fuzzer.id} refutes {join_lines(refuted)}"
                + (f" ({fuzzer.claim})" if fuzzer.claim else ""),
                evidence=evidence,
                callee=refuted[0],
                refuted=True,
                lines=refuted_lines(result.output),
            )
        if not result.decided:
            return _Attack(
                fuzzer, f"{fuzzer.id} could not be run: {result.detail}", evidence=evidence
            )
        if not result.resolved:
            return _Attack(
                fuzzer,
                f"{fuzzer.id} failed without naming a disagreement: {result.detail}",
                evidence=evidence,
            )
        if not callee:
            return _Attack(
                fuzzer,
                f"{fuzzer.id} found no disagreement but does not say which unchanged "
                "callee it attacked, so it decides none of them",
                evidence=evidence,
            )
        return _Attack(
            fuzzer,
            f"{fuzzer.id} found no disagreement about {callee}",
            evidence=evidence,
            callee=callee,
            settled=True,
        )
