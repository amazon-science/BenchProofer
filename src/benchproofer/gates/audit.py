# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What an independent review found, checked again rather than believed.

These gates read the `audit/` directory, the only place something a reviewer produced
can affect a verdict, and saying a bundle is broken is not enough to make it so:

* `audit.spec_completeness` and `audit.spec_soundness` ignore what the review claims
  about its submissions. Each submission is a complete solution file carrying the
  shipped specification, re-run through the checker and the benchmark's own oracle
  (`_rerun`): the specification is too weak if it accepts an implementation the oracle
  rejects, and too strong if it refutes one the oracle accepts. Where those runs cannot
  tell right from wrong, the attack validation auditor's ruling decides (`_validated`).
* `audit.faithfulness`, `audit.equivalence` and `audit.no_disclosure` report a
  reviewer's judgment, since no program can decide those questions, but only while the
  files it was reached from keep the digests it recorded, so a repair costs a fresh
  review of what it touched and nothing more. The verdict decides, as
  `verified-swebench`'s panels do: what the judgment shows beside it is evidence for a
  reader and a repair, and never turns a pass into a failure.
* `audit.independence` records whether the reviewer is a different model from the
  author: a model attacking its own work grades its own homework.

A bundle with no review has not passed one, so every gate here skips as
`artifact_absent` when the directory is missing.
"""

from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import ClassVar, Literal, cast

from ..backends.base import BackendKind, CheckResult
from ..core import determinism, echo
from ..core.bundle import (
    RULINGS,
    AuditRole,
    Bundle,
    Coverage,
    Judgment,
    Review,
    Ruling,
    Submission,
    SubmissionKind,
)
from ..core.differential import (
    HARNESS,
    carried,
    clipped,
    compared,
    disagreements,
    executables,
    runs_in,
    substituted,
    unparsed,
    unsupported,
)
from ..core.markers import joined, parse
from ..core.provenance import judge_digest
from ..core.readings import readings, ruling_reads
from ..core.variant import fingerprint, run_beside, scope
from ..core.verdict import Level, SkipReason, Status, Verdict
from ..errors import BundleError, MarkerError
from ..oracles.base import Candidate, Oracle, OracleResult, OracleStatus, Program
from ..util.digest import digest_text
from ..util.fsio import read_json, read_text, write_json
from ..util.patch import is_diff, same_change
from .attribution import attributed
from .base import Gate, GateContext
from .reference import ATTEMPTS
from .support import join_lines, table

__all__ = [
    "INPUTS",
    "OUTSIDE",
    "UNRULED",
    "AuditGate",
    "DisclosureJudgmentGate",
    "EquivalenceJudgmentGate",
    "FaithfulnessJudgmentGate",
    "IndependenceGate",
    "SpecCompletenessGate",
    "SpecSoundnessGate",
    "entries_under",
    "listed_under",
    "section_of",
]

#: Where re-running a review's submissions is cached, so the two gates that read those
#: rows for opposite findings cost one pass of the checker and the oracle between them.
_SUBMISSIONS = "audit.submissions"
#: The evidence file recording what re-running each submission found, with what it was
#: computed from, so a later judgment of the same files reads the row rather than running
#: the benchmark's tests on the submission again (`_recorded`).
_RECORD = "audit-outcomes.json"
#: The detail `audit.spec_completeness` and `audit.spec_soundness` set on an undecided
#: verdict while a submission of their kind that cannot be determined by execution has no
#: ruling of the attack validation auditor (`_Outcome.left_open`), listing each by id with
#: what the gates established; `pipeline.route` asks that auditor (again).
UNRULED = "unruled"
#: How many times the attack validation auditor is shown an attack or a control with its
#: files as they are: asked once, and once more where it gave no ruling. One still without a
#: ruling is discarded, counting neither way (`_validated`).
_ASKED = 2
#: What `_Outcome.validated` holds for one discarded that way.
_DISCARDED = "discarded"
#: `correspondence.md`'s section declaring the inputs the type bridge does not cover.
OUTSIDE = "Outside the bridge"
#: `correspondence.md`'s section listing the unchanged callees whose result the model takes
#: as an input; no gate checks those calls.
INPUTS = "Callee results taken as inputs"
#: How much of a detail one row of the evidence table carries. A counterexample rarely
#: fits in less, and it is the part of the row a reader came for.
_DETAIL = 120


class AuditGate(Gate):
    """Shared plumbing for the gates that read a recorded review.

    Public, so a gate in another package can read the same review.
    """

    level: ClassVar[Level] = Level.AUDITED

    def review(self, context: GateContext) -> Review | Verdict:
        """Load the review, or the verdict to return when there is nothing to read."""
        try:
            review = context.bundle.audit()
        except BundleError as exc:
            return self.failed(f"the recorded review is unusable: {exc}")
        if review is None:
            return self.undecided(
                SkipReason.ARTIFACT_ABSENT,
                f"the bundle ships no review in {context.bundle.audit_dir.name}/; run "
                "'benchproofer audit' to have one written",
            )
        return review


class IndependenceGate(AuditGate):
    """Require the review to have been written by someone other than the author."""

    id: ClassVar[str] = "audit.independence"
    title: ClassVar[str] = "Review was not written by the bundle's author"
    rationale: ClassVar[str] = (
        "Catches a bundle reviewed by the language model that drafted it, whose judgments "
        "restate the drafting session's own opinion of its work."
    )
    sources: ClassVar[tuple[str, ...]] = ("audit/index.toml",)

    def judge(self, context: GateContext) -> Verdict:
        """Compare who reviewed the bundle with who drafted it."""
        review = self.review(context)
        if isinstance(review, Verdict):
            return review
        common = {"reviewer": review.reviewer, "author": review.author}
        if not review.author:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                "manifest.json does not record who drafted this bundle, so whether the "
                "review is independent of it cannot be established",
                **common,
            )
        if not review.independent:
            return self.failed(
                f"the bundle was reviewed by {review.reviewer}, which drafted it; a "
                "review of one's own work is not independent evidence",
                **common,
            )
        return self.passed(
            f"reviewed by {review.reviewer}, drafted by {review.author}", **common
        )


class _SubmissionGate(AuditGate):
    """Shared plumbing for the two gates that read a review's re-run submissions.

    Each submission is re-run once for both (`_rerun`). Set aside as deciding nothing: one aimed
    at a specification the bundle no longer ships, one reaching for a construct the solution
    file does not (`assume`, `sorry`, a directive that turns the checker off), and one repeating
    another's implementation, which counts once. A broken oracle cannot manufacture a finding
    here, since it would also reject the bundle's own Python copy of the implementation, which
    `impl.conformance` reports.

    Every submission on record is re-run before the number this run asks for is counted, so
    a shortfall never hides a defect. What is on record is the review of the specification
    as it stands: after a repair changes it, the attack auditor files fresh submissions in
    place of the earlier ones (`audit.agents`).
    """

    #: Which submissions count towards this gate's evidence bar, and what to call them.
    kind: ClassVar[SubmissionKind]
    noun: ClassVar[str]

    sources: ClassVar[tuple[str, ...]] = (
        "solution.*",
        "audit/index.toml",
        "audit/*",
        "../task.json",
    )

    @abstractmethod
    def wanted(self, context: GateContext) -> int:
        """How many decided submissions of this gate's kind the run asks for."""

    @abstractmethod
    def read(self, context: GateContext, rerun: _Rerun) -> Verdict:
        """Draw this gate's own conclusion from the re-run rows."""

    def judge(self, context: GateContext) -> Verdict:
        """Check every submission on record again, then read the rows for one question."""
        available = context.backend.availability()
        if not available:
            return self.undecided(
                SkipReason.TOOLCHAIN_ABSENT,
                f"{context.backend.name} is unavailable: {available.detail}",
                hint=available.hint,
            )
        review = self.review(context)
        if isinstance(review, Verdict):
            return review
        blocked = self.needs_verified_base(context)
        if blocked is not None:
            return blocked
        oracle = self.needs_oracle(context)
        if isinstance(oracle, Verdict):
            return oracle

        rerun = context.shared(_SUBMISSIONS, lambda: _rerun(context, review, oracle))
        if rerun.incomplete:
            return self.failed(f"the recorded review is incomplete: {rerun.incomplete}")
        return self.read(context, rerun)


class SpecCompletenessGate(_SubmissionGate):
    """Ask whether the review found a wrong implementation the specification accepts."""

    id: ClassVar[str] = "audit.spec_completeness"
    title: ClassVar[str] = "Completeness gate"
    rationale: ClassVar[str] = (
        "Catches a specification weak enough that an independent reviewer could write "
        "an implementation it accepts and the benchmark's own tests reject."
    )
    kind: ClassVar[SubmissionKind] = "weakness"
    noun: ClassVar[str] = "attack"

    def wanted(self, context: GateContext) -> int:
        """The number of attacks that must be decided for surviving them to count."""
        return max(1, context.settings.audit_min_attacks)

    def read(self, context: GateContext, rerun: _Rerun) -> Verdict:
        """Report the accepted-and-wrong submissions, whatever they were filed as.

        An attack the checker accepted is ruled by what the programs found and by its patch
        (`_attacked`): it succeeds where `conformance.py` tells it apart from the repository,
        fails where a program showed it agrees with the reference implementation, and is
        otherwise decided by its patch. One whose patch passes, with or without a witness test
        that holds, and one shown to agree whose patch is rejected cannot be determined by
        execution, and the attack validation auditor rules on them (`_Outcome.left_open`):
        while one has no ruling the gate is undecided (`UNRULED`), and one discarded counts
        neither way.

        Where the checker could not prove that the specification admits one result per
        input, and an accepted attack proves the solution file's claims, the lemma that
        would show it computes what the reference implementation computes is named for a
        repair to prove (`_lemma`).
        """
        too_weak = [row for row in rerun.outcomes if row.too_weak]
        if too_weak:
            lemma = _lemma(context, too_weak)
            return self.weakness(
                context,
                "attack(s) succeed, each a wrong implementation the specification accepts: "
                + join_lines(
                    [
                        f"{row.submission.id} ({_broke(context, row.failed) or row.detail})"
                        if row.failed or row.detail
                        else row.submission.id
                        for row in too_weak
                    ]
                )
                + (
                    "; the checker could not prove that the specification admits one "
                    "result per input. Where it does, state and prove "
                    + " and ".join(f"`{conjunct}`" for conjunct in lemma)
                    + " in the proof region, one theorem each: an attack proving the "
                    "solution file's claims then computes what the reference "
                    "implementation computes, and the attack validation auditor rules on "
                    "one whose equivalent patch the tests reject"
                    if lemma
                    else ""
                ),
                too_weak=_ids(too_weak),
                claims=[row.submission.claim for row in too_weak],
                **({"determinism": list(lemma)} if lemma else {}),
                **rerun.common,
            )
        filed = rerun.mine(self.kind)
        unruled = _unruled(self, filed, rerun)
        if unruled is not None:
            return unruled
        settled = [row for row in filed if row.settled]
        aside = rerun.clause([row for row in filed if not row.settled])
        wanted = self.wanted(context)
        if len(settled) < wanted:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"{len(settled)} of the {len(filed)} attack(s) on record were decided (an "
                "attack fails where the checker refutes it, or where it verifies and its "
                "implementation is shown correct, and succeeds where it verifies and its "
                "implementation is shown wrong, by the programs, the benchmark's tests or the "
                f"attack validation auditor) and this run asks for {wanted}, so the "
                f"specification has not been tested hard enough for surviving to mean "
                f"anything{aside}",
                filed=len(filed),
                required=wanted,
                **rerun.common,
            )
        refuted = [row for row in settled if row.checker == "refuted"]
        ruled = [row for row in settled if row.validated == "fails"]
        agreed = [row for row in settled if row.agreed and not row.validated]
        return self.passed(
            f"{len(settled)} attack(s) failed: the checker refuted {len(refuted)}, a program "
            f"found {len(agreed)} agreeing with the reference implementation, and the attack "
            f"validation auditor ruled that {len(ruled)} fail{aside}",
            refuted=_ids(refuted),
            agreed=_ids(agreed),
            validated=_ids(ruled),
            **rerun.common,
        )


class SpecSoundnessGate(_SubmissionGate):
    """Ask whether the specification accepts a correct implementation of its own task.

    The too-strong direction needs submissions of its own: a specification that refutes
    everything survives every attack while demanding the one implementation its author
    had in mind. Refuting a control the oracle accepts is a defect, a falsifier's
    refutation being a counterexample. A prover's refusal of a control is a gap (`_gap`):
    the attack auditor proves each control before it files it, as `verified-swebench` asks of
    its positive control, and one it could not get accepted counts neither for nor against
    the specification here, unless its refutation witness and its witness test show the
    specification is what refuses a correct implementation (`_refuted`), or the attack
    validation auditor rules so (`_validated`). That auditor rules on each such control,
    shown the reviewer's claim, which says what the attack auditor tried: correct and refused
    by the specification fails the gate, correct and refused for a proof it lacks is listed as
    unproved (`unproved`), and one not correct is discarded. While one has no ruling the gate
    is undecided (`UNRULED`).

    Only a control admits the specification, as `verified-swebench` asks for a positive
    control that is a file of its own rather than one of its attacks: an attack the checker
    accepted that the benchmark's tests pass may still break a behavior the statement asks
    for, which the attack validation auditor rules on (`_Outcome.left_open`). A correct
    implementation the specification refuses is a control's question, so the review files
    one as a control.
    """

    id: ClassVar[str] = "audit.spec_soundness"
    title: ClassVar[str] = "Soundness gate"
    rationale: ClassVar[str] = (
        "Catches a specification so strong that a correct implementation of the task "
        "fails it -- which makes the formalized task a different, harder one."
    )
    kind: ClassVar[SubmissionKind] = "control"
    noun: ClassVar[str] = "control"

    def wanted(self, context: GateContext) -> int:
        """The number of correct implementations the specification has to admit."""
        return max(1, context.settings.audit_min_controls)

    def read(self, context: GateContext, rerun: _Rerun) -> Verdict:
        """Report the refuted-but-correct controls."""
        too_strong = [row for row in rerun.outcomes if row.too_strong]
        if too_strong:
            return self.failed(
                "the specification refutes implementation(s) the benchmark's own tests "
                f"accept: {join_lines(_ids(too_strong))}",
                too_strong=_ids(too_strong),
                claims=[row.submission.claim for row in too_strong],
                **rerun.common,
            )
        filed = rerun.mine(self.kind)
        unruled = _unruled(self, filed, rerun)
        if unruled is not None:
            return unruled
        admitted = [row for row in filed if row.admitted]
        aside = rerun.clause([row for row in filed if not row.admitted])
        unproved = {
            row.submission.id: row.detail for row in filed if row.validated == "unproved"
        }
        listed = {"unproved": unproved} if unproved else {}
        wanted = self.wanted(context)
        if len(admitted) < wanted:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"{len(admitted)} of the {len(filed)} control(s) on record both verified "
                f"and were judged correct, and this run asks for {wanted}, so nothing "
                "establishes that the specification admits more than the one "
                f"implementation its own author had in mind{aside}",
                filed=len(filed),
                required=wanted,
                **listed,
                **rerun.common,
            )
        return self.passed(
            f"the specification accepts {len(admitted)} implementation(s) written "
            "differently from the shipped one that the benchmark's own tests accept: "
            f"{join_lines(_ids(admitted))}{aside}",
            admitted=_ids(admitted),
            **listed,
            **rerun.common,
        )


class _JudgmentGate(AuditGate):
    """Report one review role's judgment, for as long as it is still current.

    An unjudged role is inconclusive, never sound, and so is a judgment whose readings
    (`core.readings`) no longer have the digests it recorded: it is about another bundle.
    """

    #: Which role's judgment this gate reports.
    role: ClassVar[AuditRole]
    #: What the reviewer was asked, for the summary of an absent judgment.
    question: ClassVar[str]

    def filed(self, context: GateContext) -> Judgment | None:
        """The judgment this gate reports, when the bundle carries one."""
        review = self.review(context)
        return None if isinstance(review, Verdict) else review.judgment(self.role)

    def judge(self, context: GateContext) -> Verdict:
        """Read one judgment off the review and check that it still applies."""
        review = self.review(context)
        if isinstance(review, Verdict):
            return review
        judgment = review.judgment(self.role)
        if judgment is None:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"the review filed no {self.role} judgment, so nobody has said whether "
                f"{self.question}",
                reviewer=review.reviewer,
            )
        common = {
            "reviewer": review.reviewer,
            "independent": review.independent,
            "verdict": judgment.verdict,
            "findings": list(judgment.findings),
        }
        stale = judgment.stale(readings(context.bundle, context.backend))
        if stale:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"the {self.role} judgment was reached from {join_lines(stale)} as they "
                "were before, so it is about a different bundle; review this one again",
                stale=stale,
                **common,
            )
        if not judgment.reads:
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"the {self.role} judgment records nothing it was reached from, so "
                "there is no way to tell whether it is about this bundle",
                **common,
            )
        if judgment.verdict == "unsound":
            return self.failed(
                judgment.summary or f"the review rejects this bundle on {self.role}",
                **common,
            )
        if judgment.verdict == "uncertain":
            return self.undecided(
                SkipReason.INCONCLUSIVE,
                f"the review could not tell whether {self.question}"
                + (f": {judgment.summary}" if judgment.summary else ""),
                **common,
            )
        return self.passed(judgment.summary or f"the review found {self.role} sound", **common)


class FaithfulnessJudgmentGate(_JudgmentGate):
    """Report whether a reviewer found that the specification covers what the task requires.

    The verdict decides, as `verified-swebench`'s does, and it is about scope alone, as the
    SWE-Proof paper's is: every behavior the FAIL_TO_PASS tests, and the PASS_TO_PASS tests the
    test patch adds or edits, check, and every change the statement asks for, has an obligation,
    and nothing beyond those is demanded. The review lists the behaviors of the functions the
    fix changes, one row each, with the benchmark's test that checks the behavior and the
    obligation that states it (`Coverage`); the table goes into the verdict's details, and its
    rows naming a test and no obligation are what a repair is shown (`uncovered`).
    """

    id: ClassVar[str] = "audit.faithfulness"
    title: ClassVar[str] = "Review found the specification describes the task"
    rationale: ClassVar[str] = (
        "Catches a specification that omits something the task requires, or demands "
        "something it never asked for -- neither of which a program can decide."
    )
    role: ClassVar[AuditRole] = "faithfulness"
    question: ClassVar[str] = "the specification describes this task"
    sources: ClassVar[tuple[str, ...]] = (
        "solution.*",
        "correspondence.md",
        "audit/index.toml",
        "../task.json",
    )

    def judge(self, context: GateContext) -> Verdict:
        """Report the verdict with the coverage table it was reached from."""
        reported = super().judge(context)
        judgment = self.filed(context)
        if reported.status not in (Status.PASS, Status.FAIL) or judgment is None:
            return reported
        table = judgment.coverage
        details = {**reported.details, "coverage": [_row(row) for row in table]}
        uncovered = [row for row in table if row.required and row.uncovered]
        if uncovered:
            details["uncovered"] = [_row(row) for row in uncovered]
        return reported.model_copy(update={"details": details})


class EquivalenceJudgmentGate(_JudgmentGate):
    """Report whether the shipped implementation is the golden patch.

    The verdict decides, as `verified-swebench`'s does. The review sets the
    implementation's operations against the golden patch's one by one, each of a kind
    (`Operation`), and the rows go into the verdict's details as what it rests on; the
    rules tell the reviewer which kinds leave behavior alone and that a `changed` one makes
    the verdict `unsound`.
    """

    id: ClassVar[str] = "audit.equivalence"
    title: ClassVar[str] = "Equivalence gate"
    rationale: ClassVar[str] = (
        "Catches an implementation that quietly computes something other than the "
        "golden patch, which makes every later verdict about a different task "
        "than the one the benchmark's tests judge."
    )
    role: ClassVar[AuditRole] = "equivalence"
    question: ClassVar[str] = "the implementation is equivalent to the golden patch"
    sources: ClassVar[tuple[str, ...]] = (
        "solution.*",
        "correspondence.md",
        "audit/index.toml",
        "../task.json",
        "../reference.patch",
    )

    def judge(self, context: GateContext) -> Verdict:
        """Report the judgment with the operations it set against the golden patch.

        A bundle with no `correspondence.md` fails whatever the judgment: that file is the
        claim the judgment checks, and a repair is what writes it.
        """
        review = self.review(context)
        if isinstance(review, Verdict):
            return review
        path = context.bundle.correspondence_path
        if not (path.is_file() and read_text(path).strip()):
            return self.failed(
                f"the bundle ships no {path.name}, the account of how the implementation "
                "corresponds to the golden patch that this review checks"
            )
        reported = super().judge(context)
        judgment = self.filed(context)
        if judgment is None or not judgment.operations:
            return reported
        operations = [f"{item.kind}: {item.detail}" for item in judgment.operations]
        return reported.model_copy(
            update={"details": {**reported.details, "operations": operations}}
        )


class DisclosureJudgmentGate(_JudgmentGate):
    """Report whether a reviewer found the specification gives away the implementation.

    The reviewer reads the spec view blind, without the implementation or the golden patch,
    since the question is what a solver could recover; its rules ask each finding to quote
    the line of that view it rests on. The verdict decides, as `verified-swebench`'s does.

    `../reference.patch` is not among the sources: the verdict does not rest on it, so it
    must not expire when that file changes.
    """

    id: ClassVar[str] = "audit.no_disclosure"
    title: ClassVar[str] = (
        "Review found the specification does not give away the implementation"
    )
    rationale: ClassVar[str] = (
        "Catches a specification whose steps a solver could copy into code, "
        "which makes the formalized task easier than the one it came from."
    )
    role: ClassVar[AuditRole] = "disclosure"
    question: ClassVar[str] = "the specification does not give away the implementation"
    sources: ClassVar[tuple[str, ...]] = (
        "solution.*",
        "audit/index.toml",
        "../task.json",
    )


#: What the checker said about a submission, or which screen set it aside. Only
#: `verified` and `refuted` are verdicts about the specification: `undecided` is a fact
#: about the search, the two `scope` labels mean the checker's verdict would not be about
#: the solution file's specification, and `gap` a control a prover refused (`_gap`), which
#: the attack validation auditor rules on.
_Checker = Literal[
    "verified",
    "refuted",
    "undecided",
    "unreadable",
    "specification differs",
    "uses a construct the solution file does not",
    "proves a claim of its own",
    "duplicate",
    "gap",
]
#: What the benchmark's own tests, or the bundle's conformance.py, said about the
#: implementation. `undecided` covers both "nobody asked" and "they could not say", which
#: are equally uninformative; the detail beside it says which.
_Ruling = Literal["wrong", "correct", "undecided"]


@dataclass(frozen=True, slots=True)
class _Outcome:
    """One submission of a review, re-run against the bundle as it now stands."""

    submission: Submission
    checker: _Checker
    ruling: _Ruling = "undecided"
    detail: str = ""
    #: Why the benchmark's own tests reject the repository patch filed with it, "" where
    #: they accept it or nobody asked.
    rejected: str = ""
    #: The tests that patch failed.
    failed: tuple[str, ...] = ()
    #: True for an attack a program showed to agree with the reference implementation where
    #: that, and not its patch, decides it: executed on the same drawn inputs as it, or proved
    #: equal to it, or, for one whose patch the tests reject, put through `conformance.py`
    #: (`_attacked`).
    agreed: bool = False
    #: True for an attack whose patch the tests pass and whose witness test passes on the fixed
    #: code, fails with that patch and cites something (`_witnessed`).
    witnessed: bool = False
    #: The attack validation auditor's ruling on a submission that cannot be determined by
    #: execution (`RULINGS`), `_DISCARDED` for one it still gave none after it was asked
    #: again, "" for none (`_validated`).
    validated: str = ""

    @property
    def left_open(self) -> int:
        """Which of the four kinds execution cannot determine this submission is, or 0 for none.

        Each kind is a question about the task or about a proof that no run decides, which the
        attack validation auditor rules on:

        1. an attack the checker accepted that the tests do not reject, unless it was executed
           on the same drawn inputs as the reference implementation and agreed, or proved
           equal to it: a difference the tests do not see, or agreement over only the inputs
           `conformance.py` draws, does not say whether it breaks a behavior the task requires;
        2. an attack the checker accepted that a program showed to agree with the reference
           implementation (`agreed`), whose patch the tests reject: either the model cannot see
           a behavior the tests check, or the patch is not the attack;
        3. a control a prover refused (`gap`), or one the checker refuted that nothing could
           run against the repository (`_controlled`): it may be a correct implementation the
           specification refuses;
        4. an attack of the first kind whose witness test holds (`witnessed`): whether what
           the test cites asks for the behavior it checks is a question about the task, which
           no program checks.
        """
        if self.checker == "gap":
            return 3
        if self.submission.kind == "control":
            return 3 if self.checker == "refuted" and self.ruling == "undecided" else 0
        if self.checker != "verified" or self.ruling != "correct":
            return 0
        if self.agreed:
            return 2 if self.rejected else 0
        return 4 if self.witnessed else 1

    @property
    def opened(self) -> str:
        """What the gates established, where execution cannot determine it (`left_open`).

        "" for any other submission.
        """
        case = self.left_open
        if case == 3 and self.checker == "gap":
            return (
                "the prover refuses it, and nothing shows the specification is what refuses it"
            )
        if case == 3:
            return (
                "the checker refutes it, and nothing decided whether it is a correct "
                f"implementation: {self.detail}"
            )
        if case == 4:
            return (
                "the checker accepts it, the benchmark's tests do not reject it, and its "
                "witness test passes on the fixed code and fails with its equivalent patch; "
                "whether what the test cites asks for the behavior it checks is the attack "
                "validation auditor's to rule"
            )
        if case == 2:
            return "the checker accepts it, and the benchmark's tests reject its patch"
        if case == 1:
            return "the checker accepts it, and the benchmark's tests do not reject it"
        return ""

    @property
    def unruled(self) -> bool:
        """True where execution cannot determine it and no ruling has decided it yet."""
        return bool(self.left_open) and not self.validated

    @property
    def too_weak(self) -> bool:
        """The specification accepted an implementation shown wrong, or one ruled `succeeds`."""
        return (self.checker == "verified" and self.ruling == "wrong") or (
            self.validated == "succeeds"
        )

    @property
    def too_strong(self) -> bool:
        """The specification refuted a control shown correct, or one ruled `too_strong`."""
        if self.submission.kind != "control":
            return False
        return (self.checker == "refuted" and self.ruling == "correct") or (
            self.validated == "too_strong"
        )

    @property
    def admitted(self) -> bool:
        """The specification accepted an implementation shown correct.

        Shown by a run, or, for an attack that cannot be determined by execution, by the attack
        validation auditor's ruling that it fails.
        """
        return (
            self.checker == "verified"
            and self.ruling == "correct"
            and (not self.left_open or self.validated == "fails")
        )

    @property
    def settled(self) -> bool:
        """True when this submission decided the too-weak question either way."""
        return self.checker == "refuted" or self.admitted or self.too_weak

    @property
    def label(self) -> str:
        """Why this submission produced no evidence, for the census in a summary.

        The screen that set it aside, or for one the checker gave a verdict on, what the
        benchmark's tests made of it: `undecided` with its reason, or `not correct` where the
        tests reject a control; or, for an attack or a control that cannot be determined by
        execution, what the attack validation auditor made of it.
        """
        if self.validated:
            return _CENSUS[self.validated]
        if self.unruled:
            return "undecided: the attack validation auditor has not ruled on it"
        if self.checker == "undecided":
            return "undecided: the checker reached no verdict"
        if self.checker not in ("verified", "refuted"):
            return self.checker
        if self.ruling == "wrong":
            return "not correct"
        if self.ruling == "undecided":
            whether = (
                "the attack succeeds" if self.submission.kind == "weakness" else "it is correct"
            )
            return f"undecided: no verdict on whether {whether}"
        return self.ruling

    @property
    def ruled(self) -> str:
        """What the gates made of this submission, in one line, for the next review to read.

        Of an attack, whether it succeeds, with why; of a control, whether it is correct.
        """
        if self.submission.kind == "weakness":
            said = f"checker: {self.checker}; {self._attack()}"
        else:
            said = f"checker: {self.checker}; correctness: {self.ruling}"
            if self.too_strong:
                said += " (the specification refuses a correct implementation)"
        return f"{said}; {self.detail}" if self.detail else said

    def _attack(self) -> str:
        """Whether this attack succeeds, and why, as `ruled` says it."""
        if self.validated == "succeeds":
            return "the attack succeeds, by the attack validation auditor's ruling"
        if self.too_weak:
            return (
                "the attack succeeds: its implementation is wrong and the specification "
                "accepts it, a weakness of the specification"
            )
        if self.checker == "refuted":
            return "the attack fails: the checker refutes it"
        if self.validated == "fails":
            return "the attack fails, by the attack validation auditor's ruling"
        if self.admitted:
            return "the attack fails: its implementation is correct"
        return "undecided whether the attack succeeds"

    def row(self) -> tuple[str, str, str, str, str]:
        """This submission as one line of the evidence table."""
        return (
            self.submission.id,
            self.submission.kind,
            self.checker,
            self.ruling,
            self.detail[:_DETAIL],
        )


#: How the census of a summary names an attack or a control that cannot be determined by
#: execution, by the attack validation auditor's ruling on it, where that leaves it producing
#: no evidence for the gate counting.
_CENSUS: dict[str, str] = {
    "succeeds": "the attack succeeds",
    "fails": "the attack fails",
    "too_strong": "correct, and the specification refuses it",
    "unproved": "unproved: correct, but the checker rejected a step of its own proof",
    "incorrect": "discarded: not correct, by the attack validation auditor's ruling",
    _DISCARDED: (
        "discarded: no ruling of the attack validation auditor after it was asked again"
    ),
}
#: What the attack validation auditor's ruling says, by the ruling, for a submission's detail.
_RULED: dict[str, str] = {
    "succeeds": "that the attack succeeds",
    "fails": "that the attack fails",
    "too_strong": "that it is correct and the specification refuses it",
    "unproved": "that it is correct, and the checker rejected a step of its own proof",
    "incorrect": "that it is not correct",
}


@dataclass(frozen=True, slots=True)
class _Rerun:
    """Every submission of one review, re-run once for both gates that read them."""

    outcomes: tuple[_Outcome, ...]
    #: Details both gates report, so a reader of either verdict sees the same census.
    common: dict[str, object]
    #: Why nothing could be re-run: a submission the review names but does not ship.
    incomplete: str = ""

    def clause(self, unused: Sequence[_Outcome]) -> str:
        """Account for submissions that produced no evidence, as a clause or nothing.

        Each gate passes only the rows of its own kind: a control set aside says nothing
        about how hard the attacks tried, and the reverse.
        """
        groups: dict[str, list[str]] = {}
        for row in unused:
            groups.setdefault(row.label, []).append(row.submission.id)
        census = "; ".join(
            f"{len(ids)} {label} ({join_lines(ids)})" for label, ids in groups.items()
        )
        return f"; set aside: {census}" if census else ""

    def mine(self, kind: SubmissionKind) -> list[_Outcome]:
        """The submissions filed as one kind, which is what an evidence bar counts."""
        return [row for row in self.outcomes if row.submission.kind == kind]


def section_of(text: str, heading: str) -> str:
    """The section of a `correspondence.md` under ``heading``, its heading included, or "".

    ``heading`` is `OUTSIDE` or `INPUTS`. The heading starts with those words and may go on,
    `## Outside the bridge: the error code`; the section runs to the next heading as deep or
    shallower.
    """
    found = re.search(
        rf"^(?P<level>#+)[ \t]*{re.escape(heading)}\b.*$", text, re.MULTILINE | re.IGNORECASE
    )
    if found is None:
        return ""
    rest = text[found.end() :]
    after = re.search(rf"^#{{1,{len(found.group('level'))}}}\s", rest, re.MULTILINE)
    return text[found.start() : found.end() + (after.start() if after else len(rest))].strip()


def entries_under(text: str, heading: str) -> str:
    """What a `correspondence.md` declares under ``heading``, "" when it declares nothing.

    A heading that goes on after those words is part of what it declares; a section that
    is `Nothing.` alone declares nothing, and one with any other text under the heading
    declares that text, as the correspondence request tells its author.
    """
    first, _, rest = section_of(text, heading).partition("\n")
    named = re.sub(rf"^#+[ \t]*{re.escape(heading)}", "", first, flags=re.IGNORECASE)
    body = "\n".join(part for part in (named.strip(" \t:-\u2013\u2014"), rest.strip()) if part)
    return "" if body.rstrip(".").strip().lower() in ("", "nothing", "none") else body


def listed_under(bundle: Bundle, heading: str) -> str:
    """What ``bundle``'s `correspondence.md` declares under ``heading`` (`entries_under`)."""
    path = bundle.correspondence_path
    return entries_under(read_text(path), heading) if path.is_file() else ""


def _row(row: Coverage) -> str:
    """One coverage row as the verdict's details list it."""
    return (
        f"{row.behavior} | tested by: {row.tested_by or '-'} | "
        f"covered by: {row.covered_by or '-'}"
    )


def _rerun(context: GateContext, review: Review, oracle: Oracle) -> _Rerun:
    """Re-run every submission on record, and record what was established about it.

    The oracle, the expensive half, is asked only where its verdict could be a finding:
    about anything the checker accepted (too weak if the oracle rejects it), and about a
    refuted control (too strong if the oracle accepts it). A submission an earlier judgment
    re-ran from the same files is read off its record instead (`_recorded`), so the
    benchmark's tests run once on it. The attack validation auditor's rulings are then read
    over the attacks and controls that cannot be determined by execution (`_validated`).
    """
    outcomes: list[_Outcome] = []
    incomplete = ""
    # Seeded with the shipped implementation, so a submission repeating it is set aside
    # like any other repeat: it would verify and be judged correct, which says nothing new.
    seen: dict[str, str] = {}
    shipped = _fingerprint(context, context.solution)
    if shipped is not None:
        seen[shipped] = "the shipped implementation"
    recorded = _recorded(context) if context.reuse else {}
    within = _within(context)
    measured: dict[str, tuple[str, _Outcome]] = {}

    for submission in review.submissions:
        try:
            source = context.bundle.submission_source(submission)
            transcription = context.bundle.submission_shadow(submission)
            test = context.bundle.submission_test(submission)
        except BundleError as exc:
            incomplete = str(exc)
            break
        screened = _screen(context, submission, source, seen)
        if screened is not None:
            outcomes.append(screened)
            continue
        key = digest_text(
            "\0".join(
                (
                    within,
                    submission.kind,
                    source,
                    transcription or "",
                    test or "",
                    submission.cites,
                    submission.refutation,
                )
            )
        )
        found = recorded.get(submission.id)
        if found is not None and found[0] == key:
            outcome = replace(found[1], submission=submission)
        else:
            outcome = _measured(context, submission, source, transcription, test, oracle)
        outcomes.append(outcome)
        if _reusable(outcome):
            measured[submission.id] = (key, outcome)

    digests = readings(context.bundle, context.backend)
    rows = tuple(_validated(row, review.ruling(row.submission.id), digests) for row in outcomes)
    _record(context, measured)
    evidence = context.bundle.write_evidence(
        "audit-submissions.txt",
        table(
            ("submission", "filed as", "checker", "correctness", "detail"),
            [r.row() for r in rows],
        ),
    )
    return _Rerun(
        outcomes=rows,
        common={
            "reviewer": review.reviewer,
            "independent": review.independent,
            "submissions": len(review.submissions),
            "checked": sum(1 for row in rows if row.checker in ("verified", "refuted")),
            "oracle": oracle.name,
            "evidence": [evidence],
            # Whole, by id, since the evidence table keeps only the start of a row's detail.
            "rulings": {row.submission.id: row.ruled for row in rows},
        },
        incomplete=incomplete,
    )


def _measured(
    context: GateContext,
    submission: Submission,
    source: str,
    transcription: str | None,
    test: str | None,
    oracle: Oracle,
) -> _Outcome:
    """Put one submission the screens let through to the checker, the programs and the tests."""
    checked = context.check(source, f"submission-{submission.id}")
    if not checked.well_formed:
        # Not refused by the specification: counted as survived, a broken submission
        # would stand in for a defeated one.
        return _Outcome(submission, "unreadable", detail=checked.detail)
    if not checked.decided:
        # Not a refutation: read as one it would credit the specification with an
        # attack nobody ran, and turn an unfinished control into a too-strong finding.
        return _Outcome(submission, "undecided", detail=checked.detail)
    if not checked.verified and submission.kind == "weakness":
        return _Outcome(submission, "refuted", detail=checked.detail)
    if not checked.verified and (gap := _gap(context, checked)):
        # Not shown to be the specification's refusal, so the oracle is not asked, unless
        # a refutation witness and a run show it is (`_refuted`).
        return _refuted(context, submission, source, test, oracle, gap=gap)
    if checked.verified and submission.kind == "weakness":
        return _attacked(context, submission, source, transcription, test, oracle)
    outcome = _controlled(context, submission, source, oracle, verified=checked.verified)
    # A refused submission the oracle calls correct is the too-strong finding, so
    # what the checker refused it for leads the detail.
    if not checked.verified and checked.detail:
        joined_detail = (
            f"{checked.detail}; {outcome.detail}" if outcome.detail else checked.detail
        )
        outcome = replace(outcome, detail=joined_detail)
    return outcome


def _within(context: GateContext) -> str:
    """A digest of what every submission's row is computed from beside its own files.

    The checker, the solution file, `conformance.py`, the task and its golden patch, and
    whether the benchmark's tests pass the golden patch here (`_cannot_refute`).
    """
    digests = context.bundle.artifact_digests()
    resolves = context.bundle.manifest().verdicts.get("oracle.reference_resolves")
    return digest_text(
        "\0".join(
            (
                context.backend.name,
                context.solution,
                context.bundle.conformance() or "",
                digests.get("../task.json", ""),
                digests.get("../reference.patch", ""),
                str(resolves.status) if resolves is not None else "",
            )
        )
    )


def _reusable(row: _Outcome) -> bool:
    """Whether a later judgment of the same files may read ``row`` rather than re-run it.

    Not one the checker reached no verdict on, nor an attack it accepted that the
    benchmark's tests established nothing about: running those again may decide them.
    """
    if row.checker == "undecided":
        return False
    return not (row.checker == "verified" and row.ruling == "undecided")


def _recorded(context: GateContext) -> dict[str, tuple[str, _Outcome]]:
    """What the last judgment recorded of each submission it re-ran (`_RECORD`), by id.

    Each row with the digest of what it was computed from, and only where the gates that
    computed it are the ones running now. A row is rebuilt with a placeholder submission,
    which the caller replaces with the one on record.
    """
    path = context.bundle.evidence_dir / _RECORD
    if not path.is_file():
        return {}
    try:
        document = read_json(path)
    except (OSError, ValueError):
        return {}
    if not isinstance(document, dict) or document.get("judge") != judge_digest():
        return {}
    rows = document.get("rows")
    found: dict[str, tuple[str, _Outcome]] = {}
    for name, row in (rows if isinstance(rows, dict) else {}).items():
        try:
            found[str(name)] = (
                str(row["key"]),
                _Outcome(
                    Submission(id=str(name), file=""),
                    cast("_Checker", str(row["checker"])),
                    cast("_Ruling", str(row["ruling"])),
                    str(row["detail"]),
                    str(row["rejected"]),
                    tuple(str(test) for test in row["failed"]),
                    bool(row["agreed"]),
                    bool(row["witnessed"]),
                ),
            )
        except (KeyError, TypeError):
            continue
    return found


def _record(context: GateContext, rows: dict[str, tuple[str, _Outcome]]) -> None:
    """Write what re-running each submission found, for a later judgment (`_recorded`)."""
    write_json(
        context.bundle.evidence_dir / _RECORD,
        {
            "judge": judge_digest(),
            "rows": {
                name: {
                    "key": key,
                    "checker": row.checker,
                    "ruling": row.ruling,
                    "detail": row.detail,
                    "rejected": row.rejected,
                    "failed": list(row.failed),
                    "agreed": row.agreed,
                    "witnessed": row.witnessed,
                }
                for name, (key, row) in rows.items()
            },
        },
    )


def _validated(row: _Outcome, ruling: Ruling | None, digests: dict[str, str]) -> _Outcome:
    """``row`` with the attack validation auditor's ruling on it, where that ruling counts.

    Only an attack or a control that cannot be determined by execution is ruled on
    (`_Outcome.left_open`), and only by a ruling reached from the files as they are and the
    citation as it is (`ruling_reads`) that gives one of the rulings its kind allows
    (`RULINGS`) and names the input and what of the task it rests on. One the auditor was asked
    about again and still left without such a ruling is discarded.
    """
    if not row.left_open or ruling is None or not ruling.reads:
        return row
    if ruling.reads != ruling_reads(row.submission, digests):
        return row
    if ruling.ruling in RULINGS[row.submission.kind] and ruling.named:
        why = ruling.why.strip()
        said = (
            f"the attack validation auditor rules {_RULED[ruling.ruling]}, on the input "
            f"{ruling.input.strip()}, resting on {ruling.rests_on.strip()}"
            + (f": {why}" if why else "")
        )
        return replace(
            row, validated=ruling.ruling, detail=f"{row.detail}; {said}" if row.detail else said
        )
    if ruling.asked < _ASKED:
        return row
    said = (
        "the attack validation auditor was asked about it again and gave no ruling naming the "
        "input and what of the task it rests on, so it is discarded"
    )
    return replace(row, validated=_DISCARDED, detail=f"{row.detail}; {said}")


def _screen(
    context: GateContext, submission: Submission, source: str, seen: dict[str, str]
) -> _Outcome | None:
    """Set aside a submission the checker's verdict about would mean nothing.

    `seen` maps an implementation's fingerprint to the submission that filed it first,
    and is updated here, so a submission repeating another's code counts once.
    """
    fingerprint = _fingerprint(context, source)
    if fingerprint is None:
        return _Outcome(submission, "unreadable", detail="no readable marker regions")
    if not context.backend.same_spec(context.solution, source):
        return _Outcome(
            submission, "specification differs", detail="not the shipped specification"
        )
    admissible = scope(context.solution, source, context.backend)
    if not admissible:
        label = cast("_Checker", admissible.label)
        return _Outcome(submission, label, detail=admissible.reason)
    if fingerprint in seen:
        return _Outcome(submission, "duplicate", detail=f"same code as {seen[fingerprint]}")
    seen[fingerprint] = submission.id
    return None


def _fingerprint(context: GateContext, source: str) -> str | None:
    """Identify a submission by its implementation, or None when it cannot be read.

    Two submissions with the same code are one, whatever their claims say, and so are two
    that differ only in comments, indentation or blank lines (`variant.fingerprint`).
    """
    try:
        impl = joined(parse(source, context.backend.comment), "impl")
    except MarkerError:
        return None
    return fingerprint(impl, context.backend)


def _gap(context: GateContext, checked: CheckResult) -> str:
    """Why a prover's refusal of a control counts neither way, or "" under a falsifier.

    A falsifier's refutation is a counterexample wherever it is reported. A prover's refusal
    is either the specification ruling the control out or a proof the control lacks, and its
    verdict does not say which, so the attack validation auditor rules on it, shown the
    reviewer's claim, which says what the attack auditor tried.
    """
    if context.backend.kind is not BackendKind.PROVER:
        return ""
    return (
        "the prover's refusal does not say whether the specification or a proof the control "
        f"lacks refuses it; the checker said: {checked.detail or 'no reason'}"
    )


def _attacked(
    context: GateContext,
    submission: Submission,
    source: str,
    patch: str | None,
    test: str | None,
    oracle: Oracle,
) -> _Outcome:
    """Rule on an attack the checker accepted, by what the programs found and its patch.

    One the bundle's `conformance.py`, with the attack's code in place of the drafter's,
    tells apart from the repository (`_harnessed`) succeeds, its implementation wrong, and
    its patch is not asked. Every other attack's patch is put to the benchmark's tests
    (`_patched`). One a program showed to agree with the reference implementation fails, its
    implementation correct, since the specification accepted that behavior in its own
    implementation: the two files executed on the same drawn inputs agreed
    (`variant.run_beside`), the checker proves them equal (`_proved_equal`), or
    `conformance.py` agrees over the inputs it compared and executing the two on the same drawn
    inputs found no difference. A rejected patch of it the attack validation auditor rules on
    (`_Outcome.left_open`). Any other is decided by its patch, as `verified-swebench` decides
    every attack: one whose patch the tests reject succeeds.

    An attack whose patch the tests pass that auditor rules on too, unless executing the two on
    the same drawn inputs, or a proof, showed it equal to the reference implementation, which
    makes it fail: a difference the tests do not see, or agreement over only the inputs
    `conformance.py` draws, does not say whether it breaks a behavior the task requires. Where
    its witness test holds (`_witnessed`), what that auditor rules is whether what the test
    cites asks for the behavior it checks.

    Executing the two on the same drawn inputs and the proof come first, and where they show the
    two equal `conformance.py` is not run: it compares model values with repository ones, so of
    an attack equal to the reference implementation it would say what `impl.conformance` says.
    The test suite is not asked instead: over a tree with one file of a multi-file fix replaced,
    it fails for every submission alike.
    """
    ran = run_beside(context.solution, source, context.backend)
    equal = ran.why if ran.answer == "agreed" else ""
    if ran.answer == "not run":
        equal = _proved_equal(context, submission, source)
    ruling: _Ruling | None = "correct"
    why = equal
    if not equal:
        ruling, why = _harnessed(context, submission, source, oracle)
        if ruling == "wrong":
            return _Outcome(submission, "verified", "wrong", why)
        if ran.answer == "differs":
            ruling, why = None, ran.why
    patched = _patched(context, submission, patch, oracle, why=why)
    if ruling == "correct":
        outcome = _Outcome(
            submission,
            "verified",
            "correct",
            f"{why}; {patched.detail}" if patched.rejected else why,
            patched.rejected,
            patched.failed,
            agreed=bool(equal or patched.rejected),
        )
    else:
        told = ran.answer == "differs" and patched.ruling != "undecided"
        outcome = _Outcome(
            submission,
            "verified",
            patched.ruling,
            f"{why}; {patched.detail}" if told else patched.detail,
            patched.rejected,
            patched.failed,
        )
    if outcome.agreed or patched.ruling != "correct" or not patch:
        return outcome
    holds, said = _witnessed(context, submission, test, patch, oracle)
    if not said:
        return outcome
    return replace(outcome, detail=f"{outcome.detail}; {said}", witnessed=holds)


def _witnessed(
    context: GateContext, submission: Submission, test: str | None, patch: str, oracle: Oracle
) -> tuple[bool, str]:
    """Whether an attack's witness test holds, and what its two runs showed, "" without one.

    The test runs where the benchmark's tests run, once on the fixed code and once with the
    attack's equivalent patch in place of the golden patch (`Program.patch`). It holds when it
    passes the first time, fails the second, and cites something of the statement or the tests
    (`Submission.cites`); whether what it cites asks for the behavior it checks the attack
    validation auditor rules on. Otherwise it is evidence of nothing.
    """
    if not test or not test.strip():
        return False, ""
    if not submission.cites.strip():
        return False, (
            "its witness test cites no sentence of the statement and no test it checks, so it "
            "is evidence of nothing"
        )
    fixed = _on_fixed(context, submission, test, oracle)
    if not fixed.resolved:
        return False, (
            f"its witness test does not pass on the fixed code ({fixed.detail}), so it is "
            "evidence of nothing"
        )
    attacked = oracle.probe(
        context.task,
        Program(source=test, label=f"witness-{submission.id}-patched", patch=patch),
        workdir=context.scratch("audit", submission.id, "witness", "patched"),
        timeout_s=context.settings.oracle_timeout_s,
    )
    if attacked.status is OracleStatus.UNRESOLVED:
        lines = [line.strip() for line in attacked.output.splitlines() if line.strip()]
        last = lines[-1] if lines else ""
        return True, (
            f'its witness test, which cites "{submission.cites.strip()}", passes on the fixed '
            f"code ({fixed.detail}) and fails with its equivalent patch in place of the golden "
            f"patch ({attacked.detail}{f': {last}' if last else ''})"
        )
    if attacked.resolved:
        return (
            False,
            "its witness test passes with its equivalent patch too, so it shows nothing",
        )
    return False, (
        f"its witness test could not be run with its equivalent patch ({attacked.detail}), so "
        "it shows nothing"
    )


def _on_fixed(
    context: GateContext, submission: Submission, test: str, oracle: Oracle
) -> OracleResult:
    """A submission's witness test, run where the benchmark's tests run, on the fixed code."""
    return oracle.probe(
        context.task,
        Program(source=test, label=f"witness-{submission.id}", with_reference=True),
        workdir=context.scratch("audit", submission.id, "witness", "fixed"),
        timeout_s=context.settings.oracle_timeout_s,
    )


def _refuted(
    context: GateContext,
    submission: Submission,
    source: str,
    test: str | None,
    oracle: Oracle,
    *,
    gap: str,
) -> _Outcome:
    """A control a prover refused: a gap (`_gap`), unless its refutation witness shows more.

    Under a checker whose refusal needs a refutation witness to say anything
    (`Backend.witness_required`), the control's `refutation` is checked as the property-based
    test suite checks the witness of a case that expects `refute` (`attribution.attributed`): it
    holds of the control and
    fails against the reference implementation. Its witness test then runs once on the fixed
    code, and passes only where the fixed code returns what the control returns at the
    witness's input. Both holding, the specification refuses a correct implementation.
    """
    claim = submission.refutation
    if not (context.backend.witness_required and claim.strip()):
        return _Outcome(submission, "gap", detail=gap)
    objection = attributed(
        context, source, claim, slot=f"submission-{submission.id}", of="control"
    )
    if objection is not None:
        return _Outcome(
            submission,
            "gap",
            detail=f"{gap}; its refutation witness shows nothing: {objection}",
        )
    if not test or not test.strip():
        return _Outcome(
            submission,
            "gap",
            detail=(
                f"{gap}; the checker proves its refutation witness, and no witness test shows "
                "the fixed code returns what the control returns there"
            ),
        )
    ran = _on_fixed(context, submission, test, oracle)
    if not ran.resolved:
        return _Outcome(
            submission,
            "gap",
            detail=(
                f"{gap}; the checker proves its refutation witness, and its witness test does "
                f"not pass on the fixed code ({ran.detail}), so nothing shows the fixed code "
                "returns what the control returns there"
            ),
        )
    return _Outcome(
        submission,
        "refuted",
        "correct",
        "the checker proves its refutation witness, a claim that the specification refuses "
        "what the control returns at one input, and its witness test shows the fixed code "
        f"returns that there ({ran.detail})",
    )


def _controlled(
    context: GateContext,
    submission: Submission,
    source: str,
    oracle: Oracle,
    *,
    verified: bool,
) -> _Outcome:
    """Ask the benchmark's own code what one control's implementation is worth.

    Through the bundle's `conformance.py`, as `impl.conformance` puts the shipped
    implementation through it, with the control's code in place of the drafter's
    (`_harnessed`), so only the implementation varies and a disagreement names its input.
    A control `conformance.py` cannot run as written (a Nagini one over `PSeq`, one calling
    a helper it lacks) or could not decide is correct on the checker's acceptance alone,
    the rule `verified-swebench` holds a positive control to. One the checker refuses is
    then undecided rather than put to the oracle as a patch: the patch that resolves is the
    benchmark's own, and a reviewer handing that in would turn any refusal into a too-strong
    finding. Whether it is a correct implementation the specification refuses the attack
    validation auditor rules on (`_Outcome.left_open`).
    """
    checker: _Checker = "verified" if verified else "refuted"
    ruling, why = _harnessed(context, submission, source, oracle)
    if ruling is not None:
        return _Outcome(submission, checker, ruling, why)
    if verified:
        return _Outcome(
            submission,
            checker,
            "correct",
            f"{why}, so as a control it rests on the checker's acceptance alone",
        )
    return _Outcome(
        submission,
        checker,
        "undecided",
        f"{why}, and a control the checker refused is not put to the benchmark's tests "
        "as a patch, since the golden patch would resolve",
    )


def _harnessed(
    context: GateContext,
    submission: Submission,
    source: str,
    oracle: Oracle,
) -> tuple[_Ruling | None, str]:
    """Run the bundle's `conformance.py` with one submission's code in it.

    Returns:
        The ruling and why, or None and why `conformance.py` decided nothing about it: the
        implementation cannot run as written (a Nagini one over `PSeq`, one calling a helper
        `conformance.py` lacks), there is no `conformance.py`, it marks no implementation to
        replace, it cannot be spliced, it declares a gap, or it compared nothing. A report it
        printed that no reader parses is `undecided` instead, since what it said may have been a
        disagreement.
    """
    harness = context.bundle.conformance()
    if not runs_in(harness, source, context.backend):
        return None, "the implementation cannot run as written"
    if harness is None or not harness.strip():
        return None, f"the bundle ships no {HARNESS} to put it through"
    if carried(harness) is None:
        return None, f"{HARNESS} does not mark the implementation it contains"

    # The annotations go first: what runs cannot carry the contracts the checker reads.
    spliced = substituted(harness, executables(source, context.backend))
    if spliced is None:
        return None, f"{HARNESS} could not be run with it in it"

    result = oracle.probe(
        context.task,
        # Against the golden patch, for the same reason the conformance gate is:
        # the behavior a submission is being compared with is the one the fix produces.
        Program(source=spliced, label=f"submission-{submission.id}", with_reference=True),
        workdir=context.scratch("audit", submission.id),
        timeout_s=context.settings.oracle_timeout_s,
    )
    disagreed = disagreements(result.output)
    if disagreed:
        return "wrong", (
            f"the repository's own code disagrees with it on {join_lines(disagreed)}"
        )
    # After a disagreement, which is a finding whatever else the run could not do, and
    # before agreement, which neither check below leaves standing. An unparsed protocol
    # line may be a disagreement in a shape of its own, so it leads the detail, whose
    # start is all the evidence table keeps.
    unread = unparsed(result.output)
    if unread:
        more = f", and {len(unread) - 1:,} more like it" if len(unread) > 1 else ""
        return "undecided", (
            f"{HARNESS} printed `{clipped(unread, 1)[0]}`, which no line of the protocol "
            f"parses{more}, so what it says was not read"
        )
    # A declared gap limits agreement to the part compared, and the part this submission
    # changed may be the part `conformance.py` never reached.
    declined = unsupported(result.output)
    if declined:
        return None, (
            f"{HARNESS} could not compare {join_lines(declined)}, where the submission may "
            "have changed something"
        )
    counted = compared(result.output)
    if result.resolved and counted:
        return "correct", f"it agrees with the repository over {counted:,} compared input(s)"
    return None, f"{HARNESS} established nothing about it ({result.detail})"


def _proved_equal(context: GateContext, submission: Submission, source: str) -> str:
    """Why an accepted attack provably computes what the reference implementation does, or "".

    Files under a proof-carrying checker cannot be executed on the same drawn inputs
    (`core.echo`), so equality is proved: the specification admits one result per input (asked
    once per bundle) and the attack proves the solution file's claims, or each function the
    attack defines is proved equal to the reference one, on the inputs the precondition admits.
    A proof that does not close leaves the attack to its patch.
    """
    backend = context.backend
    if not backend.proof_carrying:
        return ""
    if _determined(context) and echo.keeps_claims(context.solution, source, backend):
        return (
            "the checker proves the specification admits one result per input, and the "
            "attack proves the solution file's claims about its implementation"
        )
    equal = echo.equality(context.solution, source, backend)
    if _proved(context, equal, f"echo-{submission.id}"):
        return (
            "the checker proves each function it defines equal to the reference "
            "implementation's"
        )
    return ""


def _proved(context: GateContext, probe: str, slot: str) -> bool:
    """Whether the checker accepts ``probe`` resting on no axiom beyond its own library."""
    backend = context.backend
    return bool(probe) and echo.holds(
        probe,
        backend,
        check=lambda text: context.check(text, slot),
        workdir=context.scratch("audit", slot, "closure"),
        timeout_s=backend.budget(context.settings.verify_timeout_s),
    )


def _determined(context: GateContext) -> bool:
    """Whether the checker proves the specification admits one result per input, once."""
    return context.shared(
        "audit.determined",
        lambda: _proved(
            context, echo.determined(context.solution, context.backend), "echo-determined"
        ),
    )


def _lemma(context: GateContext, rows: Sequence[_Outcome]) -> tuple[str, ...]:
    """The determinism lemma a repair can prove to show ``rows`` equal, or nothing.

    Its conjuncts (`core.determinism.conjuncts`), where the checker could not prove them,
    and one of the attacks proves every claim the solution file states about its
    implementation (`core.echo.keeps_claims`), which is what the lemma needs beside it.
    The probe offers the proof region's claims first, so a theorem stating a conjunct
    closes it.
    """
    backend = context.backend
    if not backend.proof_carrying:
        return ()
    conjuncts = determinism.conjuncts(context.solution, backend)
    if not conjuncts or _determined(context):
        return ()
    for row in rows:
        try:
            source = context.bundle.submission_source(row.submission)
        except BundleError:
            continue
        if echo.keeps_claims(context.solution, source, backend):
            return conjuncts
    return ()


@dataclass(frozen=True, slots=True)
class _Patched:
    """What the benchmark's own tests made of a repository patch."""

    ruling: _Ruling
    detail: str
    #: Why the tests reject it, "" where they accept it or nobody could ask.
    rejected: str = ""
    failed: tuple[str, ...] = ()


def _patched(
    context: GateContext,
    submission: Submission,
    patch: str | None,
    oracle: Oracle,
    *,
    why: str,
) -> _Patched:
    """Put an attack to the benchmark's own tests as the repository patch filed with it.

    The patch is the golden patch with the attack's change in it, so the tests fail
    only where the attack does: resolving makes it equivalent to the fix, failing a wrong
    implementation the specification accepted. A result that could be about something
    else leaves it undecided, as `verified-swebench` screens it: no patch, a reply that is
    not a diff, a patch that does not apply or breaks the code outright, or tests that
    cannot pass the golden patch here (`_cannot_refute`). ``why`` says what sent
    the attack here, for the summary of one that filed nothing to run.

    A patch that makes the fix's own change (`util.patch.same_change`) resolves by
    definition and is not run. A rejected patch is run again, up to `reference.ATTEMPTS`
    times, and resolving on any attempt counts, as the reference check counts it: a test
    that races on a loaded host or reaches the network fails a patch that resolves, and
    only one the tests reject every time is rejected. The tests it failed are those it
    failed every time.
    """
    if not patch or not patch.strip():
        return _Patched(
            "undecided",
            f"{why}, and the review filed no equivalent patch for it, so the benchmark's "
            "tests could not be run on it",
        )
    if not is_diff(patch):
        return _Patched(
            "undecided",
            f"{why}, and what the review filed for it is not a unified diff, so there was "
            "nothing to apply",
        )
    if same_change(patch, context.task.reference.patch or ""):
        return _Patched(
            "correct",
            "its equivalent patch makes the golden patch's change, which resolves the task "
            "by definition, so it was not run",
        )
    blind = _cannot_refute(context, oracle)
    if blind:
        return _Patched(
            "undecided", f"the benchmark's own tests cannot refute anything here: {blind}"
        )
    results: list[OracleResult] = []
    for attempt in range(1, ATTEMPTS + 1):
        results.append(
            oracle.judge(
                context.task,
                Candidate(patch=patch, label=f"submission-{submission.id}"),
                workdir=context.scratch("audit", submission.id, "patch", str(attempt)),
                timeout_s=context.settings.oracle_timeout_s,
            )
        )
        # Only a rejection is asked again: a run that resolved, or that said nothing about
        # the behavior, would say the same the next time.
        if results[-1].status is not OracleStatus.UNRESOLVED or results[-1].inert:
            break
    result = results[-1]
    if result.resolved:
        again = f" on attempt {len(results)} of {ATTEMPTS}" if len(results) > 1 else ""
        return _Patched(
            "correct", f"its equivalent patch resolves the task{again}: {result.detail}"
        )
    if result.status is OracleStatus.UNRESOLVED:
        if result.inert:
            # The patch broke the code rather than getting a behavior wrong, so what the
            # tests rejected is its editing. That is the screen a patch breaking a language
            # contract outright falls to.
            return _Patched(
                "undecided", f"its equivalent patch says nothing about it: {result.inert}"
            )
        failed = (
            tuple(name for name in result.failed if all(name in run.failed for run in results))
            or result.failed
        )
        failing = f" ({join_lines(list(failed[:3]))})" if failed else ""
        detail = (
            f"its equivalent patch does not resolve the task in {len(results)} attempt(s): "
            f"{result.detail}{failing}"
        )
        return _Patched("wrong", detail, rejected=detail, failed=failed)
    return _Patched(
        "undecided",
        f"the benchmark's tests established nothing about its patch: {result.detail}",
    )


def _cannot_refute(context: GateContext, oracle: Oracle) -> str:
    """Why the benchmark's tests cannot reject a patch for its behavior here, or nothing.

    Tests that do not pass the golden patch reject every patch alike. Read off the
    recorded `oracle.reference_resolves` verdict, or asked once per bundle without one.
    """
    recorded = context.bundle.manifest().verdicts.get("oracle.reference_resolves")
    if recorded is not None:
        if recorded.status is Status.PASS:
            return ""
        return (
            "oracle.reference_resolves (Resolution check) is "
            f"{recorded.status} ({recorded.summary[:_DETAIL]})"
        )
    gold: OracleResult = context.shared(
        "audit.reference",
        lambda: oracle.judge(
            context.task,
            Candidate.reference(context.task),
            workdir=context.scratch("audit", "reference"),
            timeout_s=context.settings.oracle_timeout_s,
        ),
    )
    return "" if gold.resolved else f"the golden patch does not resolve: {gold.detail}"


def _broke(context: GateContext, failed: Sequence[str]) -> str:
    """Which half of correct a rejected implementation broke, for a summary to say.

    The benchmark's tests are two sets, and failing each calls for the opposite repair, as
    `verified-swebench` tells its own. One failing a test the fix makes pass does not fix
    the reported bug. One passing all of those and failing a test the fix keeps passing
    fixes the bug and breaks something that used to work, a property the fix preserves. A
    failed test in neither set is named as it failed.
    """
    oracle = context.task.oracle
    fixing = [test for test in failed if test in oracle.tests]
    kept = [test for test in failed if test in oracle.regression]
    if fixing:
        return f"fails FAIL_TO_PASS test(s): {join_lines(fixing)}" + (
            f"; and PASS_TO_PASS test(s): {join_lines(kept)}" if kept else ""
        )
    if kept:
        return "passes every FAIL_TO_PASS test, and fails PASS_TO_PASS test(s): " + join_lines(
            kept
        )
    return join_lines(failed)


def _unruled(gate: _SubmissionGate, filed: Sequence[_Outcome], rerun: _Rerun) -> Verdict | None:
    """The undecided verdict while one of ``filed`` execution cannot determine has no ruling.

    Each such submission is listed under `UNRULED` with what the gates established, for the
    attack validation auditor to be asked about (`pipeline.route`); None where there is none.
    """
    waiting = {row.submission.id: f"{row.opened}; {row.detail}" for row in filed if row.unruled}
    if not waiting:
        return None
    return gate.undecided(
        SkipReason.INCONCLUSIVE,
        f"{len(waiting)} {gate.noun}(s) on record cannot be determined by execution "
        f"({join_lines(list(waiting))}), and the attack validation auditor has not ruled on "
        "them, so what they show is not decided",
        **{UNRULED: waiting},
        **rerun.common,
    )


def _ids(rows: list[_Outcome]) -> list[str]:
    """The submission ids of some rows, for a summary or a repair brief."""
    return [row.submission.id for row in rows]
