# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Specification leakage.

A specification is supposed to say what a correct solution achieves, not to restate
how the benchmark's own solution does it. When it restates the reference, the
formalized task stops measuring anything: an implementation can be recovered from the
specification by reading it.

The screen is the five rules of `benchproofer.core.leakage`, run over the solver-
visible view and judged against the task statement the solver also reads. A line,
path or symbol the statement already says verbatim is not a leak; one it does not say
is, however ordinary it looks. What each rule catches, and why a fragment that
localizes nothing is excluded from it, is documented there rather than here, because
the drafting prompt and this gate have to be about the same rules.

Which function or class each changed line sits in is what drafting recorded in the bundle's
`manifest.json` (`core.sites.changed`); a bundle with no such record has the names the diff
gives, in its hunk headers and on its changed lines. The gate reads no repository.

The screen is mechanical and therefore a floor. It reports a view that *reproduces*
the fix; it cannot report one that describes the fix in its own words, which is what
`audit.no_disclosure` is for.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.leakage import Edit, screen
from ..core.sites import RECORD, changed
from ..core.verdict import Level, SkipReason, Verdict
from .base import Gate, GateContext
from .support import join_lines

__all__ = ["LeakageGate"]

#: Findings quoted in the verdict itself. The rest are in the evidence file: a
#: summary long enough to need scrolling is one nobody reads.
QUOTED = 5
#: What the spec view is, said beside the term where a verdict uses it.
_VIEW = "what a solver is shown: the specification with the implementation and proof removed"


class LeakageGate(Gate):
    """Reject a specification that reproduces the reference solution."""

    id: ClassVar[str] = "spec.no_leakage"
    title: ClassVar[str] = "Leakage gate"
    rationale: ClassVar[str] = (
        "Catches a specification that embeds the golden patch, which "
        "would make the formalized task solvable by copying its own statement."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("solution.*", "../task.json", "../reference.patch")

    def judge(self, context: GateContext) -> Verdict:
        """Run the screen over the spec view and report what it found."""
        task = context.task
        if task.reference.is_empty:
            return self.undecided(
                SkipReason.NOT_APPLICABLE, f"{task.key} ships no golden patch"
            )
        recorded = context.bundle.manifest().provenance.get(RECORD)
        edit = Edit.of(task, changed(task, recorded).golden)
        if edit.is_empty:
            return self.undecided(
                SkipReason.NOT_APPLICABLE,
                "the golden patch adds no code to compare against",
            )

        view = context.backend.spec_view(context.solution)
        findings = screen(
            view,
            edit=edit,
            statement=task.statement,
            comment=context.backend.comment,
        )
        if not findings:
            return self.passed(
                f"the spec view ({_VIEW}) reproduces no line, path, or symbol of the "
                "golden patch, and narrates no change",
                screened_lines=len(edit.lines),
                screened_symbols=list(edit.symbols),
            )

        evidence = context.bundle.write_evidence(
            "leakage.txt",
            f"What a solver could read off this spec view ({_VIEW}):\n\n"
            + "\n".join(f"- {finding}" for finding in findings)
            + "\n\nEach line names the rule it broke and what in the view broke it.\n",
        )
        rules = sorted({finding.rule for finding in findings})
        return self.failed(
            f"the spec view ({_VIEW}) gives the golden patch away in {len(findings)} "
            f"place(s), breaking {join_lines(rules)}: "
            + join_lines([finding.detail for finding in findings[:QUOTED]]),
            rules=rules,
            findings=[str(finding) for finding in findings[:QUOTED]],
            evidence=[evidence],
        )
