# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Specification strength, attacked deliberately.

Mutation is a floor; a property-based test suite is an argument. Each case is a hand-written
variant of the solution file, shipped with the outcome its author claims the checker will
produce:

* a **uniqueness** rival is wrong in a way the specification should forbid. The checker
  must reject it; if it verifies, the specification is too weak.
* a **soundness** rival is correct but written differently from the shipped
  implementation. The checker must accept it; if it is rejected, the specification is too
  strong: it pins down one implementation rather than the task, and a solver with a
  different correct implementation would be marked wrong.
* an **admissibility** case is the *accepted* implementation with a probe added, asserting
  the specification at concrete inputs the task exercises. The checker must accept it; if
  it is rejected, the precondition excludes those inputs. No rival can show that, because
  every rival is judged against the same precondition: a specification whose `require`
  admits nothing the task exercises verifies vacuously, and every other gate agrees with
  it.

A property-based test suite missing a kind of case fails without a case being run, so a repair
writes the case. So does one that has lost a case its last verdict judged and did not find
defective as a case (`REMOVABLE`): every verdict records the cases it judged (`rivals`), and a
case leaves the suite only once a verdict has named it defective, whoever removed it.
Admissibility cases are asked for only under a prover, since a probe establishes something only
when its assertions are discharged rather than searched for. The uniqueness kind is decided
instead by a lemma, stated from the specification's own predicate and accepted by the checker,
that any two results the specification admits are equal (`core.determinism`): then no wrong
implementation it admits exists, for any input rather than the one a rival would pick.

Every case carries the shipped specification and differs from the solution file only where the
specification is not; one that changes the specification, or reaches for a construct that
discharges an obligation rather than meeting it, is no evidence about the specification. The
bundle ships its cases, so such a case is a failure rather than a skip. Under a checker that
replays a proof script the file writes, a rejection alone attributes nothing, since a merely
reshaped rival fails exactly as a wrong one does: a reject case there carries a refutation
witness, and one whose witness does not discriminate is a gate error (`gates.attribution`). The
witness is asked of a reject case the checker reached no verdict on as well, since its builds
leave out the case's own proof, which is what may have run out of budget.

Under a prover, a refused case the checker had to accept may be missing a step of its own proof
rather than refused by the specification. It is reported `unproved`, a defect of the case that a
repair fixes in the case, when running it decides the question: a correct rival that returns
what the reference implementation returns on every admissible input drawn (`variant.coincides`),
or a probe whose every call the precondition admits and whose every assertion holds
(`variant.probe_holds`). Where running cannot decide it, a checker that places a failed
obligation at the clause stating it still can: a refusal that lies wholly inside the case's own
regions (`variant.refused_inside`) is its proof not closing. Under a checker that replays the
proof the case writes, a specification too strong to admit the case would produce that refusal
too; that question is left to the control the review has to show the checker accepting. A probe
is read that way only under such a checker: one that discharges the obligation itself places a
call the precondition refuses at the call, inside the probe, which is the precondition's
finding. Unproved is still a failure, since the property-based test suite has not shown a
correct case verifying, and agreement on drawn inputs only ever moves a refusal from the
specification to the case.

Where the implementation region holds definitions elaborated before any proof of them
(`Backend.definitions_in_impl`), a refusal there means the rival is not an implementation at
all, so it is no evidence about the specification. A case a proof session has already worked on
(`Rival.proof_session`) and that is still unproved is recorded as a **gap** -- correct,
unproved, named in the verdict, and not failed.

A case that carries another's implementation -- the solution file, the pre-fix implementation,
or an earlier case -- asks a question the bundle has already asked, so it is set aside: named in
the verdict, not run, and no evidence. The property-based test suite is judged on the cases that
remain, which fail it for the repeat only by leaving a kind without a case. The screen is
`variant.fingerprint` over the implementation regions, which works under every checker, and
behavior where it can be asked: a uniqueness case that runs as the pre-fix implementation or
as another uniqueness case runs (`variant.coincides`), or that the checker proves equal to one
(`core.echo.equality`), is set aside even where the two files differ by an assertion. An
admissibility case is exempt from the comparison against the solution file, which it carries by
construction.

A case meant to be wrong that the specification accepts is a weakness only if it is wrong.
One that under a prover returns what the reference implementation returns on every input
drawn missed its bug and is no evidence of a weakness.

A case whose marker regions cannot be read is no evidence either: nothing else can be asked
of it, so it is named with its file and what is wrong with its regions, for a repair to fix.

The evidence file carries each case whole -- its file, its claim, what the checker said,
and what running it showed -- since it is what a repair reads.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar

from ..backends.base import Backend, BackendKind, CheckResult
from ..core import echo
from ..core.bundle import Rival
from ..core.variant import (
    coincides,
    probe_holds,
    probe_problem,
    refused_inside,
    refused_within,
    restates,
    scope,
)
from ..core.verdict import Level, SkipReason, Verdict
from ..errors import BundleError
from .attribution import attributed
from .base import Gate, GateContext
from .support import besides, found, join_lines, unreadable

__all__ = ["REMOVABLE", "UNIQUENESS", "BatteryGate", "balanced", "distinct", "removable"]

#: The kind of case that is a wrong implementation the specification has to refuse. Named,
#: because it is the one a lemma can decide instead (`core.determinism`).
UNIQUENESS = "uniqueness"
#: Kinds every property-based test suite must contain to be judged: one wrong implementation the
#: specification has to refuse, and one correct one it has to admit.
BALANCED: tuple[str, ...] = (UNIQUENESS, "soundness")
#: The third kind, asked for only where a probe's assertions are discharged rather than
#: searched for. See the module docstring.
PROBED: tuple[str, ...] = ("admissibility",)
#: The categories of this gate's `defects` that find a case defective as a case rather than
#: the specification wrong: a case a verdict names under one of them may leave the suite.
#: `out_of_scope` is the former name of `not_evidence`, under which a verdict already on disk
#: names its cases.
REMOVABLE: frozenset[str] = frozenset(
    {
        "drifted",
        "not_evidence",
        "out_of_scope",
        "set_aside",
        "malformed",
        "unproved",
        "undecided",
        "unattributed",
    }
)


def removable(details: Mapping[str, Any]) -> set[str]:
    """The cases a verdict of this gate, by its ``details``, finds defective as cases."""
    defects = details.get("defects")
    if not isinstance(defects, dict):
        return set()
    return {str(case) for key in REMOVABLE for case in defects.get(key) or ()}


def balanced(backend: Backend) -> tuple[str, ...]:
    """The kinds of case a property-based test suite has to contain under this checker."""
    if backend.kind is BackendKind.PROVER:
        return (*BALANCED, *PROBED)
    return BALANCED


def _kept(context: GateContext) -> set[str]:
    """The cases the last verdict of this gate leaves the suite bound to keep.

    The ones it recorded (`rivals`) less those it found defective as cases (`removable`);
    none where there is no such verdict, or no `manifest.json` that can be read, which
    `artifact.integrity` reports.
    """
    try:
        last = context.bundle.manifest().verdicts.get(BatteryGate.id)
    except BundleError:
        return set()
    listed = last.details.get("rivals") if last is not None else None
    if last is None or not isinstance(listed, list):
        return set()
    return {str(case) for case in listed} - removable(last.details)


class BatteryGate(Gate):
    """Run the property-based test suite and require every case to behave as claimed."""

    id: ClassVar[str] = "spec.strength.battery"
    title: ClassVar[str] = "Property-based falsification"
    rationale: ClassVar[str] = (
        "Catches a specification that accepts a wrong implementation, or rejects a "
        "correct one written differently from the shipped implementation."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("solution.*", "rivals/*")

    def judge(self, context: GateContext) -> Verdict:
        """Check each case against the outcome its manifest entry claims.

        Every verdict records the cases the suite has to keep (`rivals`): the ones it judged,
        or, where it judged none, the ones the verdict before it left the suite bound to keep
        (`_kept`), so that a case removed while the suite cannot be judged is still missed.
        """
        kept = _kept(context)
        carried = {"rivals": sorted(kept)} if kept else {}
        backend = context.backend
        available = backend.availability()
        if not available:
            return self.undecided(
                SkipReason.TOOLCHAIN_ABSENT,
                f"{backend.name} is unavailable: {available.detail}",
                hint=available.hint,
                **carried,
            )
        blocked = self.needs_verified_base(context)
        if blocked is not None:
            return blocked.model_copy(update={"details": {**blocked.details, **carried}})

        try:
            battery = context.bundle.battery()
        except BundleError as exc:
            return self.failed(
                f"the property-based test suite's index is unusable: {exc}", **carried
            )
        ids = [rival.id for rival in battery]
        removed = sorted(kept.difference(ids))
        if removed:
            return self.failed(
                "case(s) of the property-based test suite are gone that its last verdict "
                f"judged and did not find defective as cases: {', '.join(removed)}. A case "
                "leaves the suite only once this gate has found it defective as a case, so "
                "write each back",
                removed=removed,
                rivals=sorted(kept.union(ids)),
            )
        verdict = self._suite(context, battery)
        return verdict.model_copy(update={"details": {**verdict.details, "rivals": ids}})

    def _suite(self, context: GateContext, battery: list[Rival]) -> Verdict:
        """Judge ``battery``, the bundle's property-based test suite, case by case."""
        backend = context.backend
        if not battery:
            return self.failed(
                "the bundle ships no property-based test suite in "
                f"{context.bundle.rivals_dir.name}/",
            )
        try:
            sources = {rival.id: context.bundle.rival_source(rival) for rival in battery}
        except BundleError as exc:
            return self.failed(str(exc))
        unreadable = _unreadable(context, battery, sources)
        #: Cases that repeat another of the bundle's files, by id, with what each repeats.
        aside = _repeats(context, [r for r in battery if r.id not in unreadable], sources)
        kinds = {rival.kind for rival in battery}
        remaining = {rival.kind for rival in battery if rival.id not in aside}
        absent = [kind for kind in balanced(backend) if kind not in remaining]
        lemma = determined(context) if UNIQUENESS in absent else ""
        if lemma:
            absent.remove(UNIQUENESS)
        if absent and kinds.isdisjoint(absent):
            return self.failed(
                f"the property-based test suite has no {', '.join(absent)} case",
                kinds=sorted(kinds),
            )

        entries: list[str] = []
        too_weak: list[str] = []
        too_strong: list[str] = []
        drifted: list[str] = []
        #: Cases that are no evidence about the specification, by id, with the reason
        #: each is not. Both halves are reported: the ids so a caller can select them,
        #: the reasons because the bare fact is not actionable on its own.
        not_evidence: dict[str, str] = {}
        #: Correct rivals the checker could not prove, by id, with its first error.
        unproved: dict[str, str] = {}
        #: The same, for a case a proof session has already spent its budget on: a gap in
        #: the bundle's evidence rather than a case to fix.
        gaps: dict[str, str] = {}
        malformed: list[str] = []
        undecided: list[str] = []
        #: Reject cases whose rejection no witness attributes to the specification, by id.
        unattributed: dict[str, str] = {}
        #: The same, for a uniqueness case the determinism lemma decides instead: the lemma
        #: already proves no second result the specification admits exists, so what this
        #: one case failed to attribute is asked and decided for every input.
        by_lemma: dict[str, str] = {}
        excluded: list[str] = []

        for rival in battery:
            source = sources[rival.id]
            path = f"{context.bundle.rivals_dir.name}/{rival.file}"

            if rival.id in unreadable:
                not_evidence[rival.id] = unreadable[rival.id]
                entries.append(_entry(rival, path, "regions unreadable", unreadable[rival.id]))
                continue
            if not backend.same_spec(context.solution, source):
                drifted.append(rival.id)
                entries.append(_entry(rival, path, "specification differs"))
                continue
            admissible = scope(context.solution, source, backend)
            if not admissible:
                not_evidence[rival.id] = admissible.reason
                entries.append(_entry(rival, path, admissible.label, admissible.reason))
                continue
            if rival.kind == "admissibility" and (
                why := probe_problem(context.solution, source, backend)
            ):
                not_evidence[rival.id] = why
                entries.append(_entry(rival, path, "not a probe", why))
                continue
            if rival.id in aside:
                entries.append(_entry(rival, path, "set aside", aside[rival.id]))
                continue

            result = context.check(source, f"rival-{rival.id}")
            outcome, reason = str(result.status), ""
            running = "undecided: not run, since only a correct case the checker refused is run"
            if not result.decided and not (
                backend.witness_required and rival.expect == "refute"
            ):
                undecided.append(rival.id)
            elif not result.well_formed:
                # A file the checker could not read is rejected whatever it claimed,
                # so this says nothing in either direction, for either kind of case.
                malformed.append(rival.id)
            elif rival.expect == "refute":
                if (
                    result.verified
                    and backend.kind is BackendKind.PROVER
                    and (same := coincides(context.solution, source, backend))
                ):
                    # A case that missed its bug, which a repair fixes.
                    not_evidence[rival.id] = f"{_NOT_WRONG}: {same}"
                    outcome, running = "not wrong", same
                elif result.verified:
                    too_weak.append(rival.id)
                elif (
                    unowned := attributed(
                        context, source, rival.witness, slot=f"witness-{rival.id}", of="rival"
                    )
                ) is not None:
                    if rival.kind == UNIQUENESS and (lemma := lemma or determined(context)):
                        by_lemma[rival.id] = f"{unowned}; {_BY_LEMMA}"
                        outcome = "decided by the determinism lemma"
                        reason = by_lemma[rival.id]
                    else:
                        # What a proof session on the witness reported ends the reason, as
                        # `spec.discriminates` ends a pre-fix implementation's.
                        session = f"; {rival.proof_session}" if rival.proof_session else ""
                        unattributed[rival.id] = f"{unowned}{session}"
                        outcome, reason = "unattributed", unattributed[rival.id]
                elif not result.decided:
                    outcome = "rejected at its witness's input"
            elif result.refuted:
                # A refused probe is its own finding, kept apart from a refused rival:
                # one says the specification pins down an implementation, the other that
                # its precondition excludes the task's own inputs. They call for
                # different repairs, and the second is the one no rival can reach.
                if rival.kind == "admissibility":
                    running = (
                        "undecided: executed, a call the probe makes is outside the "
                        "precondition, an assertion failed, or running it could not decide "
                        "the question"
                    )
                    if probe_holds(context.solution, source, backend):
                        why = running = _HOLDS
                    elif backend.witness_required and refused_inside(
                        source, f"{result.detail}\n{result.output}", backend
                    ):
                        why = _INSIDE
                    else:
                        why = ""
                        excluded.append(rival.id)
                    if why:
                        unproved[rival.id] = f"{why}; the checker said: " + (
                            result.detail or "no reason"
                        )
                        outcome = "unproved"
                elif backend.kind is not BackendKind.PROVER:
                    too_strong.append(rival.id)
                    running = (
                        "undecided: not run, since under a bounded refuter a refusal is a "
                        "counterexample"
                    )
                elif same := coincides(context.solution, source, backend):
                    unproved[rival.id] = f"{same}; the checker said: " + (
                        result.detail or "no reason"
                    )
                    outcome, running = "unproved", same
                elif backend.definitions_in_impl and (
                    lines := refused_within(
                        source, f"{result.detail}\n{result.output}", backend
                    )
                ):
                    # Not an implementation at all, so a repair rewrites it; neither a
                    # proof session nor a gap can stand in for that.
                    why = (
                        f"{_ILL_FORMED}, at line(s) {join_lines([str(n) for n in lines])}: "
                        + (result.detail or "no reason")
                    )
                    not_evidence[rival.id] = why
                    outcome, reason = "not a program", why
                elif refused_inside(source, f"{result.detail}\n{result.output}", backend):
                    unproved[rival.id] = f"{_INSIDE}; the checker said: " + (
                        result.detail or "no reason"
                    )
                    outcome = "unproved"
                    running = (
                        f"undecided: {_BESIDE}, an input told the two apart, or running "
                        "both could not decide the question; every refusal lies inside the "
                        "case's own implementation"
                    )
                else:
                    too_strong.append(rival.id)
                    running = (
                        f"undecided: {_BESIDE}, an input told the two apart, or running "
                        "both could not decide the question"
                    )
            if rival.id in unproved and rival.proof_session:
                # A proof session already spent its round on this case, so asking for its
                # proof again would ask for the round that just failed.
                gaps[rival.id] = f"{unproved.pop(rival.id)}; {rival.proof_session}"
                outcome, reason = "unproved after a proof session", gaps[rival.id]
            entries.append(_entry(rival, path, outcome, reason, result, running))

        evidence = context.bundle.write_evidence("battery.txt", "\n\n".join(entries) + "\n")
        # Every category that has a case, not only the one the verdict is about: a repair
        # told about one of them spends a round on it and is told about the next.
        defects = found(
            (
                ("drifted", drifted),
                ("not_evidence", not_evidence),
                ("too_weak", too_weak),
                ("too_strong", too_strong),
                ("precondition", excluded),
                ("set_aside", aside),
                ("unproved", unproved),
                ("unattributed", unattributed),
                ("malformed", malformed),
                ("undecided", undecided),
            )
        )
        common = {
            "cases": len(battery),
            "kinds": sorted(kinds),
            # Every correct case the checker refused on its own proof, with why, whatever the
            # verdict is about: the run report lists them (`pipeline.report`).
            "unproved_reasons": unproved,
            "gaps": sorted(gaps),
            "gap_reasons": gaps,
            "determinism": lemma,
            "decided_by_lemma": sorted(by_lemma),
            "defects": defects,
            "evidence": [evidence],
        }

        if drifted:
            return self.failed(
                f"case(s) do not share the shipped specification: {', '.join(drifted)}"
                + besides(defects, "drifted"),
                drifted=drifted,
                **common,
            )
        if not_evidence:
            return self.failed(
                "case(s) that are no evidence about the specification, for the reason "
                f"given beside each: {_listed(not_evidence)}"
                + besides(defects, "not_evidence"),
                not_evidence=sorted(not_evidence),
                reasons=not_evidence,
                **common,
            )
        if too_weak:
            return self.weakness(
                context,
                f"the specification accepts wrong implementation(s): {', '.join(too_weak)}"
                + besides(defects, "too_weak"),
                too_weak=too_weak,
                **common,
            )
        if too_strong:
            return self.failed(
                f"the specification rejects correct implementation(s): {', '.join(too_strong)}"
                + besides(defects, "too_strong"),
                too_strong=too_strong,
                **common,
            )
        if excluded:
            return self.failed(
                "the checker refused a probe on the reference implementation itself "
                f"({', '.join(excluded)}), so either the precondition excludes the inputs "
                "this task exercises -- which would make every other gate's agreement "
                "vacuous -- or the probe asks for something the checker cannot discharge "
                "here. Read the probe against the task to tell which; both are findings, "
                "and only one is about the specification" + besides(defects, "precondition"),
                precondition=excluded,
                **common,
            )
        if absent:
            # After the findings, which the cases that remain establish whatever they lack.
            return self.failed(
                f"no {', '.join(absent)} case remains once the case(s) repeating another of "
                "the bundle's files are set aside, so the property-based test suite leaves "
                f"that question undecided: {_listed(aside)}" + besides(defects, "set_aside"),
                set_aside=sorted(aside),
                reasons=aside,
                **common,
            )
        if unproved:
            # After the findings, which a repair addresses in the specification; before the
            # errors, since this one a repair resolves by fixing the case alone.
            return self.failed(
                "case(s) the checker had to accept and refused on a step of their own "
                "proof rather than on the specification, so each is a case to fix: "
                f"{_listed(unproved)}" + besides(defects, "unproved"),
                unproved=sorted(unproved),
                reasons=unproved,
                **common,
            )
        if unattributed:
            # An error rather than a failure: nothing here says the specification is weak, only
            # that the property-based test suite cannot decide the question. After the findings,
            # because a case that established one stands whatever the rest failed to establish.
            listed = join_lines(f"{case}: {why}" for case, why in unattributed.items())
            return self.errored(
                "case(s) expecting `refute` for which no claim proved at one input shows that "
                "the specification, rather than the case's own proof, is what rejects it: "
                f"{listed}" + besides(defects, "unattributed"),
                unattributed=sorted(unattributed),
                reasons=unattributed,
                **common,
            )
        if malformed:
            return self.failed(
                f"case(s) the checker could not read, so their rejection is not "
                f"evidence: {', '.join(malformed)}" + besides(defects, "malformed"),
                malformed=malformed,
                **common,
            )
        if undecided:
            return self.timed_out(
                f"the checker reached no verdict on case(s): {', '.join(undecided)}"
                + besides(defects, "undecided"),
                undecided=undecided,
                **common,
            )
        judged = [rival for rival in battery if rival.id not in aside]
        summary = f"{len(judged)} case(s) behaved as claimed ({_census(judged)})"
        if lemma:
            summary += (
                "; whether the specification admits only one result per input is decided by "
                "a determinism lemma the checker accepts (a theorem that any two results the "
                f"specification admits for one input are equal), `{lemma}`, so no wrong "
                "implementation the specification admits exists"
            )
        if by_lemma:
            summary += (
                f"; {len(by_lemma)} uniqueness case(s) for which no witness shows the "
                "specification rejects it, decided by that lemma instead: "
                f"{_listed(by_lemma)}"
            )
        if gaps:
            # Named in the summary rather than buried in the details: a property-based test
            # suite with a gap has asked its question and not decided it, and a reader
            # comparing two bundles has to be able to see which one did.
            summary += (
                f"; {len(gaps)} correct case(s) whose own proof the checker rejected even "
                "after a proof session (an agent session asked to prove the case), recorded "
                f"as such: {_listed(gaps)}"
            )
        if aside:
            summary += (
                f"; {len(aside)} case(s) repeating another of the bundle's files, set aside "
                f"and not counted toward the gate's result: {_listed(aside)}"
            )
        return self.passed(summary, **common)


def determined(context: GateContext) -> str:
    """What the checker proves about the specification admitting one result, or "".

    Here because this is where the lemma takes the place of a case: a specification that pins
    its result admits no wrong implementation to write, so the lemma decides the uniqueness
    kind for every input at once, and it decides a drafted uniqueness case whose refusal no
    witness attributes to the specification. Computed once per bundle, since mutation reads
    the same lemma about the same file.
    """
    backend = context.backend
    return context.shared(
        "spec.determined",
        lambda: echo.determines(
            context.solution,
            backend,
            check=lambda text: context.check(text, "determinism"),
            workdir=context.scratch("determinism"),
            timeout_s=backend.budget(context.settings.verify_timeout_s),
        ),
    )


def _unreadable(
    context: GateContext, battery: list[Rival], sources: dict[str, str]
) -> dict[str, str]:
    """The cases whose marker regions cannot be read, by id, with the file and what is wrong."""
    return {
        rival.id: f"{context.bundle.rivals_dir.name}/{rival.file}: {why}"
        for rival in battery
        if (why := unreadable(sources[rival.id], context.backend))
    }


def _repeats(
    context: GateContext, battery: list[Rival], sources: dict[str, str]
) -> dict[str, str]:
    """Which cases are not a case of their own, by id, with what each repeats.

    Every case is compared with the reference implementation, with each pre-fix implementation,
    and with the cases before it, by `variant.fingerprint` over their implementation regions. A
    uniqueness case is compared by behavior too, against the pre-fix implementation and the
    other uniqueness cases: a rival that computes what the pre-fix implementation computes
    attacks the mistake `spec.discriminates` already asks about, however differently it is
    written, and a pair of rivals that compute the same thing is one rival shipped twice. An
    admissibility case carries the reference implementation by construction, so that comparison
    is not made of it.
    """
    backend = context.backend
    twins = [
        (f"the pre-fix implementation {name}", source)
        for name, source in context.bundle.twins()
    ]
    found: dict[str, str] = {}
    kept: list[tuple[str, str, str]] = []
    for rival in battery:
        source = sources[rival.id]
        earlier = [*twins, *((what, other) for what, _, other in kept)]
        if same := _restated(rival, source, context.solution, earlier, backend):
            found[rival.id] = _REPEATS.format(what=same)
        elif rival.kind == UNIQUENESS:
            against = [
                *twins,
                *((what, other) for what, kind, other in kept if kind == UNIQUENESS),
            ]
            for index, (what, other) in enumerate(against, 1):
                if why := _behaves(context, what, other, source, f"{rival.id}-{index}"):
                    found[rival.id] = why
                    break
        if rival.id not in found:
            kept.append((f"case {rival.id}", rival.kind, source))
    return found


def distinct(
    solution: str, twins: Sequence[str], cases: Sequence[tuple[Rival, str]], backend: Backend
) -> list[tuple[Rival, str]]:
    """``cases`` less each one that carries another of the bundle's files, for writing.

    So that a bundle does not ship a case this gate sets aside as asking nothing of its own. The
    comparison is the one `_repeats` makes of the text, against the reference implementation,
    each pre-fix implementation and the cases kept before it; the one by behaviour runs the
    files or the checker, which writing a bundle does not. A repeat is kept where no other case
    of its kind is, since this gate then reports the kind as left without a case, which a repair
    addresses.
    """
    kept: list[tuple[str, str]] = [("a pre-fix implementation", twin) for twin in twins]
    repeats: set[str] = set()
    for rival, source in cases:
        if _restated(rival, source, solution, kept, backend):
            repeats.add(rival.id)
        else:
            kept.append((f"case {rival.id}", source))
    kinds = {rival.kind for rival, _ in cases if rival.id not in repeats}
    return [
        (rival, source)
        for rival, source in cases
        if rival.id not in repeats or rival.kind not in kinds
    ]


def _restated(
    rival: Rival,
    source: str,
    solution: str,
    others: Sequence[tuple[str, str]],
    backend: Backend,
) -> str:
    """Which of the bundle's files ``source`` carries, comments and layout aside, or "".

    ``others`` are the pre-fix implementations and the earlier cases, each with how it is named.
    An admissibility case carries the reference implementation by construction, so that
    comparison is not made of it.
    """
    carried = [*([] if rival.kind == "admissibility" else [(_ACCEPTED, solution)]), *others]
    return next((what for what, other in carried if restates(other, source, backend)), "")


def _behaves(context: GateContext, what: str, other: str, source: str, slot: str) -> str:
    """Why ``source`` computes what ``other`` computes, or "".

    Executed on the same drawn inputs where the files run (`variant.coincides`), and proved
    equal where the checker proves (`core.echo.equality`). Neither is asked of a file the other
    cannot be put beside, and sampled agreement only ever sets a case aside, as it does
    everywhere else here.
    """
    backend = context.backend
    if same := coincides(other, source, backend):
        return _RUNS_AS.format(what=what, how=same)
    probe = echo.equality(other, source, backend)
    if probe and echo.holds(
        probe,
        backend,
        check=lambda text: context.check(text, f"equal-{slot}"),
        workdir=context.scratch("equality", slot),
        timeout_s=backend.budget(context.settings.verify_timeout_s),
    ):
        return _PROVED_AS.format(what=what)
    return ""


#: How the reference implementation is named where a case carries it.
_ACCEPTED = "the reference implementation"
#: How a case was run against the reference implementation, where it was.
_BESIDE = "executed on the same drawn inputs as the reference implementation"
#: Why a case that carries another of the bundle's files is not a case of its own.
_REPEATS = (
    "it contains {what}, comments and layout aside, so it asks nothing the bundle has not "
    "asked already and what the checker says about it is evidence about that other file"
)
#: The same, shown by running the two rather than by comparing their text.
_RUNS_AS = (
    "executed on the same drawn inputs, it computes what {what} computes ({how}), so it "
    "asks nothing the bundle has not asked already"
)
#: The same, proved by the checker.
_PROVED_AS = (
    "the checker proves each function it defines equal to {what}'s, so it asks nothing the "
    "bundle has not asked already"
)
#: Why a correct case whose own definition the checker refused is not a test.
_ILL_FORMED = (
    "the checker refused its own implementation region, where the definitions are "
    "elaborated before any proof of them, so it is not an implementation of the "
    "specification and what the checker said is not about the specification"
)
#: What running a refused probe showed, when it shows the refusal is the probe's own.
_HOLDS = (
    "executed, the precondition admits every call the probe makes and the reference "
    "implementation meets every assertion, so the checker refused a step of the probe's "
    "own proof -- a value asserted in another shape than the postcondition states it, or a "
    "definition left unfolded -- rather than the task's inputs"
)
#: Where the checker placed its refusal of a correct case, when that shows it is the case's.
_INSIDE = (
    "every refusal the checker placed lies inside the case's own implementation -- a loop "
    "invariant, an assertion, a permission, a callee's precondition -- and none at a clause "
    "of the specification, so what failed is a step of the case's proof"
)
#: Why a uniqueness case nothing attributes still leaves the uniqueness kind decided.
_BY_LEMMA = (
    "the checker accepts the determinism lemma, which proves no second result the "
    "specification admits exists, so the question this case failed to decide is decided "
    "for every input"
)
#: Why a case meant to be wrong that runs as the reference implementation is not a test.
_NOT_WRONG = (
    "executed on the same drawn inputs, it computes what the reference implementation "
    "computes, so it is not a wrong implementation and its verifying says nothing about "
    "the specification"
)


def _entry(
    rival: Rival,
    path: str,
    outcome: str,
    reason: str = "",
    result: CheckResult | None = None,
    running: str = "undecided: the checker was not run on it",
) -> str:
    """One case, whole, as the evidence file records it."""
    lines = [
        f"{rival.id}: {outcome}",
        f"  source:      {path}",
        f"  kind:        {rival.kind}, expects {rival.expect}",
    ]
    if reason:
        lines.append(f"  reason:      {reason}")
    if result is not None:
        said = f"{result.status}: {result.detail}" if result.detail else str(result.status)
        lines.append(f"  checker:     {said}")
    lines.append(f"  equivalence: {running}")
    if result is not None and result.output.strip():
        lines += ["  output:", *(f"    {line}" for line in result.output.strip().splitlines())]
    return "\n".join(lines)


def _listed(cases: dict[str, str]) -> str:
    """Cases with the reason for each, for a one-line summary."""
    return join_lines(f"{case} ({why})" for case, why in cases.items())


def _census(battery: list[Rival]) -> str:
    counts: dict[str, int] = {}
    for rival in battery:
        counts[rival.kind] = counts.get(rival.kind, 0) + 1
    return ", ".join(f"{count} {kind}" for kind, count in sorted(counts.items()))
