# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The specification tells the fix from the bug.

The pre-fix implementation is checked in the same solution file, in place of the fixed
one: same specification, byte for byte, and the behavior the benchmark considers
wrong. The checker must reject it. If it does not, the specification is
satisfied by the bug the task is about, so verifying against it says nothing about
the task. This is the cheapest check that a specification is about the right thing, and
the only one that uses the benchmark's own notion of what was broken.

The pre-fix implementation must not assume what it should compute, like every other
variant: one that does is accepted for a reason that has nothing to do with the
specification. The bundle ships the pre-fix implementation, so one that assumes what it
should compute is a failure rather than a skip.

Under a checker that replays a proof script the file writes, the pre-fix implementation carries
a refutation witness, as a reject case of the property-based test suite does, and its rejection
is the specification's only when the witness attributes it (`gates.attribution`). A pre-fix
implementation with no witness, or one that does not discriminate, is an error rather than a
pass, since any reshaping of the implementation is refused the same way. The witness is asked of
a pre-fix implementation the checker reached no verdict on as well: its builds leave the pre-fix
implementation's own proof out, and that proof is what may have run out of budget.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.bundle import Twin
from ..core.material import has_pre_fix
from ..core.variant import scope
from ..core.verdict import Level, SkipReason, Verdict
from ..errors import BundleError
from .attribution import attributed
from .base import Gate, GateContext
from .support import besides, found, join_lines, table, unreadable

__all__ = ["DiscriminatesGate"]


class DiscriminatesGate(Gate):
    """Require the checker to reject every pre-fix implementation."""

    id: ClassVar[str] = "spec.discriminates"
    title: ClassVar[str] = "Discrimination check"
    rationale: ClassVar[str] = (
        "Catches a specification that the buggy code already satisfies, which "
        "would make verification independent of the task."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("solution.*", "twins/*")

    def judge(self, context: GateContext) -> Verdict:
        """Check every pre-fix implementation and require a refutation on the merits."""
        backend = context.backend
        available = backend.availability()
        if not available:
            return self.undecided(
                SkipReason.TOOLCHAIN_ABSENT,
                f"{backend.name} is unavailable: {available.detail}",
                hint=available.hint,
            )

        twins = context.bundle.twins()
        if not twins:
            return self._no_twins(context)
        blocked = self.needs_verified_base(context)
        if blocked is not None:
            return blocked

        try:
            recorded = context.bundle.twin_cases()
        except BundleError as exc:
            return self.failed(
                f"{context.bundle.twins_dir.name}/{context.bundle.twins_index.name} is "
                f"unusable: {exc}"
            )

        rows: list[tuple[str, str, str]] = []
        drifted: list[str] = []
        not_evidence: list[str] = []
        #: Why each of those is not evidence about the specification, by name.
        reasons: dict[str, str] = {}
        accepted: list[str] = []
        malformed: list[str] = []
        undecided: list[str] = []
        #: Pre-fix implementations whose rejection no witness attributes to the specification,
        #: by name, with why not and, where one ran, what a proof session on the witness
        #: reported.
        unattributed: dict[str, str] = {}

        for name, source in twins:
            if why := unreadable(source, backend):
                not_evidence.append(name)
                reasons[name] = (
                    f"{context.bundle.twins_dir.name}/{name}{backend.extension}: {why}"
                )
                rows.append((name, "regions unreadable", reasons[name]))
                continue
            if not backend.same_spec(context.solution, source):
                drifted.append(name)
                rows.append(
                    (
                        name,
                        "specification differs",
                        "its specification differs from the shipped one",
                    )
                )
                continue
            admissible = scope(context.solution, source, backend)
            if not admissible:
                not_evidence.append(name)
                reasons[name] = admissible.reason
                rows.append((name, admissible.label, admissible.reason))
                continue
            twin = recorded.get(name) or Twin(id=name, file=name)
            result = context.check(source, f"twin-{name}")
            outcome, detail = str(result.status), result.detail
            if result.verified:
                accepted.append(name)
            elif result.refuted and not result.well_formed:
                malformed.append(name)
            elif not result.decided and not backend.witness_required:
                undecided.append(name)
            elif (
                unowned := attributed(
                    context,
                    source,
                    twin.witness,
                    slot=f"witness-twin-{name}",
                    of="twin",
                )
            ) is not None:
                session = f"; {twin.proof_session}" if twin.proof_session else ""
                unattributed[name] = f"{unowned}{session}"
                outcome, detail = "unattributed", unattributed[name]
            elif not result.decided:
                outcome = "rejected at its witness's input"
            rows.append((name, outcome, detail[:120]))

        evidence = context.bundle.write_evidence(
            "discriminates.txt", table(("pre-fix implementation", "outcome", "detail"), rows)
        )
        # Every category that has a pre-fix implementation, not only the one the verdict is
        # about: a repair told about one of them spends a round on it and is told about the
        # next.
        defects = found(
            (
                ("drifted", drifted),
                ("not_evidence", not_evidence),
                ("accepted", accepted),
                ("unattributed", unattributed),
                ("malformed", malformed),
                ("undecided", undecided),
            )
        )
        common = {
            "twins": [name for name, _ in twins],
            "defects": defects,
            "evidence": [evidence],
        }

        if drifted:
            return self.failed(
                "pre-fix implementation(s) do not share the shipped specification: "
                + ", ".join(drifted)
                + besides(defects, "drifted"),
                drifted=drifted,
                **common,
            )
        if not_evidence:
            return self.failed(
                "pre-fix implementation(s) that are no evidence about the specification, "
                "for the reason given beside each: "
                + join_lines(f"{name} ({why})" for name, why in reasons.items())
                + besides(defects, "not_evidence"),
                not_evidence=not_evidence,
                **common,
            )
        if accepted:
            return self.weakness(
                context,
                f"the specification accepts the pre-fix implementation: {', '.join(accepted)}"
                + besides(defects, "accepted"),
                accepted=accepted,
                **common,
            )
        if unattributed:
            # An error rather than a failure or a skip: nothing says the specification fails to
            # tell the fix from the bug, and nothing says it does. The bundle's own pre-fix
            # implementation has not decided the question, and a repair that gives it a witness
            # that discriminates can.
            listed = join_lines(f"{name}: {why}" for name, why in unattributed.items())
            return self.errored(
                "rejection(s) of a pre-fix implementation for which no claim proved at one "
                "input shows that the specification, rather than the file's own proof, is "
                f"what rejects it: {listed}" + besides(defects, "unattributed"),
                unattributed=sorted(unattributed),
                reasons=unattributed,
                **common,
            )
        if malformed:
            return self.failed(
                "pre-fix implementation(s) the checker could not read, so their rejection is "
                f"not evidence: {', '.join(malformed)}" + besides(defects, "malformed"),
                malformed=malformed,
                **common,
            )
        if undecided:
            return self.timed_out(
                "the checker reached no verdict on pre-fix implementation(s): "
                + ", ".join(undecided)
                + besides(defects, "undecided"),
                undecided=undecided,
                **common,
            )
        return self.passed(
            f"{len(twins)} pre-fix implementation(s) rejected by the specification",
            **common,
        )

    def _no_twins(self, context: GateContext) -> Verdict:
        """Tell a task with no pre-fix state from a bundle missing its pre-fix implementation.

        Decided with the predicate the drafter decides by (`material.has_pre_fix`), so a fix
        that only adds -- which replaces nothing, and whose pre-fix implementation would
        therefore have no defect to translate -- is a task with no pre-fix implementation to
        ship rather than a bundle that lost one. A bundle that lost one fails, so a repair
        writes it: nothing else does once the first draft is written.
        """
        task = context.task
        if not has_pre_fix(task):
            return self.undecided(
                SkipReason.NOT_APPLICABLE,
                f"{task.key} ships no code the fix replaced, so it has no pre-fix "
                "implementation",
            )
        return self.failed(
            f"{task.key} ships a pre-fix state but the bundle has no pre-fix implementation in "
            f"{context.bundle.twins_dir.name}/",
        )
