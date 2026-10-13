# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Specification strength, measured by mutation.

Corrupt one token of the implementation and ask the checker again. A specification worth
verifying against accepts no such corruption that computes something else; one that does
is under-constrained, and an implementation that satisfies it need not solve the task.

These rules keep the verdict honest:

* only the implementation region is mutated, so a mutant can never weaken the contract it
  is judged against;
* a mutant the checker could not read is not a program at all -- `+` turned into `-` over
  a sequence is the common one -- so it leaves the sample, and where every mutant ends that
  way the gate says so;
* a mutant the checker refuses is not counted, on any backend: the refusal can be the proof
  the file carries or the language catching the corruption rather than the specification,
  so it is evidence of nothing about the specification's strength;
* a mutant the checker could not decide is not counted either;
* a mutant the checker accepts that is not shown equal to the reference implementation
  survives, and any survivor fails the gate, named. Under a bounded refuter that is not a
  finding: a mutant that survives may simply have outlasted the search budget.

A mutant the checker accepts may be an equivalent program, which no specification can reject --
an edit to an initial value every path overwrites is the common one. So under a prover each one
is executed on the same drawn inputs as the reference implementation (`variant.run_beside`), and
one that returns what it returns on every admissible input drawn is set aside as equivalent and
named in the details and the evidence, so a reviewer can check the call. Where the checker
proves the specification admits one result per input (`gates.battery.determined`, the same lemma
the property-based test suite's uniqueness cases read), every accepted mutant is equivalent and
none has to be run: it satisfies the specification at every admissible input, and there is only
one result it could return there. Under a bounded refuter the specification is itself a set of
properties run on drawn inputs, so agreement there would say only that neither side failed one,
and nothing is set aside.

The evidence file carries every mutant whole -- where it is, the line before and after,
what the checker said, and what running it showed -- since it is what a repair reads to
see which lines the specification leaves unconstrained.
"""

from __future__ import annotations

from typing import ClassVar

from ..backends.base import BackendKind, CheckResult
from ..core.mutation import Mutant
from ..core.variant import run_beside
from ..core.verdict import Level, SkipReason, Verdict
from .base import Gate, GateContext
from .battery import determined
from .support import join_lines

__all__ = ["MutationGate"]


class MutationGate(Gate):
    """Fail a specification that accepts a mutant computing something else."""

    id: ClassVar[str] = "spec.strength.mutation"
    title: ClassVar[str] = "Mutation check"
    rationale: ClassVar[str] = (
        "Catches an under-constrained specification, which a one-token corruption "
        "of the shipped implementation still satisfies."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("solution.*",)

    def judge(self, context: GateContext) -> Verdict:
        """Generate mutants, check each one, and fail on any that survives."""
        backend = context.backend
        available = backend.availability()
        if not available:
            return self.undecided(
                SkipReason.TOOLCHAIN_ABSENT,
                f"{backend.name} is unavailable: {available.detail}",
                hint=available.hint,
            )
        blocked = self.needs_verified_base(context)
        if blocked is not None:
            return blocked

        mutants = backend.mutants(context.solution, limit=context.settings.mutation_limit)
        if not mutants:
            return self.undecided(
                SkipReason.NOT_APPLICABLE,
                "the implementation contains no token Benchproofer knows how to mutate",
            )

        refused: list[str] = []
        survived: list[str] = []
        equivalent: list[str] = []
        excluded: list[str] = []
        not_programs: list[str] = []
        entries: list[str] = []
        screened = backend.kind is BackendKind.PROVER

        for mutant in mutants:
            result = context.check(mutant.source, f"mutant-{mutant.id}")
            equivalence = "undecided: not run, since the checker did not accept it"
            if result.refuted_on_merits:
                outcome, bucket = "refused", refused
            elif result.verified:
                outcome, bucket = "survived", survived
                if not screened:
                    equivalence = (
                        "undecided: not run, since under a bounded refuter, running it would "
                        "only compare whether each side fails a property"
                    )
                elif lemma := determined(context):
                    outcome, bucket = "equivalent", equivalent
                    equivalence = (
                        "the checker proves the specification admits one result per input "
                        f"(`{lemma}`), and this mutant satisfies it, so it returns what the "
                        "reference implementation returns at every admissible input"
                    )
                else:
                    ran = run_beside(context.solution, mutant.source, backend)
                    if ran.answer == "agreed":
                        outcome, bucket = "equivalent", equivalent
                    equivalence = ran.why if ran.answer == "agreed" else f"not shown: {ran.why}"
            elif result.refuted:
                # The checker refused the file itself. The shipped solution verified in
                # this environment (`needs_verified_base`), so the refusal is the
                # mutation's doing: the operator produced text that is not a program.
                outcome, bucket = "not a program", not_programs
            else:
                outcome, bucket = "undecided", excluded
            bucket.append(mutant.id)
            entries.append(_entry(mutant, outcome, result, equivalence))

        evidence = context.bundle.write_evidence("mutation.txt", "\n\n".join(entries) + "\n")
        common = {
            "generated": len(mutants),
            "refused": refused,
            "survived": survived,
            "equivalent": equivalent,
            "excluded": excluded,
            "not_programs": not_programs,
            "evidence": [evidence],
        }

        if len(not_programs) == len(mutants):
            return self.undecided(
                SkipReason.NOT_APPLICABLE,
                f"every one of the {len(mutants)} mutant(s) is not a program the checker "
                "can read, so none is a rival implementation and specification strength "
                "was not measured",
                **common,
            )
        if not (refused or survived or equivalent):
            return self.errored(
                f"none of {len(mutants)} mutant(s) got a usable verdict from the checker, so "
                "specification strength was not measured",
                **common,
            )

        counted = [
            f"{len(refused)} refused by the checker, which are not counted: a refusal can be "
            "the proof or the language catching the mutant rather than the specification"
        ]
        if equivalent:
            counted.append(
                f"{len(equivalent)} set aside as computing what the reference implementation "
                "computes"
            )
        if excluded:
            counted.append(f"{len(excluded)} undecided: the checker reached no verdict")
        if not_programs:
            counted.append(f"{len(not_programs)} not programs the checker can read")
        if survived:
            return self.weakness(
                context,
                f"the checker accepts {len(survived)} of the {len(mutants)} mutant(s), and "
                "none of them is shown to compute what the reference implementation "
                f"computes: {join_lines(survived)}; of the others, {'; '.join(counted)}",
                **common,
            )
        return self.passed(
            f"no mutant survives: of the {len(mutants)} mutant(s), {'; '.join(counted)}",
            **common,
        )


def _entry(mutant: Mutant, outcome: str, result: CheckResult, equivalence: str) -> str:
    """One mutant, whole, as the evidence file records it."""
    said = f"{result.status}: {result.detail}" if result.detail else str(result.status)
    return "\n".join(
        (
            f"{mutant.id}: {outcome}",
            f"  operator:    {mutant.operator}",
            f"  line:        {mutant.line}",
            f"  before:      {mutant.before}",
            f"  after:       {mutant.after}",
            f"  checker:     {said}",
            f"  equivalence: {equivalence}",
        )
    )
