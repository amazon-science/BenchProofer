# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Does adversarial review earn the audited level, and does repair earn it back.

The gates below the audited level measure a specification against programs the tool
generates. That is worth having and it is not enough: whether a specification is strong
enough to be worth proving anything about, and whether it describes the task it claims
to, are questions a program cannot pose to itself. So the top of the ladder rests on a
review by someone who did not write the bundle, and these cases run that whole loop
offline:

* **review.certified** reviews a sound bundle and certifies it at the audited level. Both
  strength findings are attempted -- a wrong implementation the specification accepts, and
  a correct one it refuses -- and the gates re-run both through the checker and the
  benchmark's own tests rather than believing the reviewer about either.
* **review.stale** rewrites the specification of a bundle that had already certified.
  Every judgment expires, every submission was aimed at a specification the bundle no
  longer ships, and the one gate that read none of it is unaffected.
* **review.loop** takes a bundle whose specification misses the point of the task through
  the full round trip: review, findings, repair, re-review, certification. The re-review
  attacks the repaired specification afresh, shown the attacks filed against the old one
  with what the gates ruled, and the repaired bundle certifies on what it files.
* **review.assumed** reviews a bundle whose specification models a callee in its axioms
  region. The review writes its own program against that model and the gate
  runs it, so what certifies the bundle is not only the `axioms.py` its author wrote.

The reviewer's part is played by `benchproofer.smoke.scripted.ScriptedSession`, whose auditors
draw their submissions from the fixture's own property-based test suite and their judgments from
the fixture's ``[review.*]`` sections, under a model name of its own, which
`benchproofer.smoke.scripted.reviewing` records, so the bundle is not reviewed by its own
author. The repair's part is played by a `ScriptedSession` that writes another fixture's files.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...backends.base import Backend
from ...config import Settings
from ...core import markers
from ...core.bundle import PRESERVING, Bundle, Review, Rival
from ...core.readings import SPEC, SPEC_UNCOMMENTED, readings
from ...core.verdict import Level, Outcome, SkipReason, Status
from ...pipeline.adjudicate import Adjudication, adjudicate
from ...pipeline.audit import AuditResult, audit, needs_review
from ...pipeline.build import build
from ...pipeline.repair import repair
from ...pipeline.route import Route, routed
from ...registries import BACKENDS
from ...util.fsio import read_text, write_text
from .. import fixtures
from ..model import Case, Context, Observation, check, equals
from ..scripted import MODEL, REVIEW_MODEL, ScriptedProvider, ScriptedSession, reviewing

__all__ = ["CASES"]

#: The level a reviewed bundle is judged at. It is the only one whose required set
#: includes the gates that read a review, so it is the only one these cases can use.
LEVEL = Level.AUDITED

#: The fixture whose artifacts pass every gate, and the one whose specification is too
#: weak to reject the bug its task is about.
SOUND = "coin-change-sound"
WEAK = "coin-change-weak"
#: The fixture whose specification assumes a callee instead of modeling it.
ASSUMED = "safe-join-assumed"
#: The callee it assumes, and the model of it the checker was given.
CALLEE = "posixpath.normpath"

#: Budgets tuned to what the fixtures ship: two wrong implementations and one correct
#: one written a different way, which is exactly the evidence the two strength gates ask
#: for. Asking for more would have the review repeat itself, and a repeat is dropped
#: rather than filed.
BUDGETS: dict[str, int] = {"audit_attacks": 2, "audit_min_attacks": 2, "audit_controls": 1}

#: The auditors a full review runs, in order. Written out rather than derived, because a
#: review that quietly stopped asking an auditor would otherwise still look like a review that
#: happened.
REVIEW_STAGES = ("attack", "faithfulness", "equivalence", "disclosure")

#: The auditors a review of a bundle that assumes a callee runs: the same review, plus the
#: auditor that writes a program per assumption, run after the submissions and before the
#: judgments.
ASSUMED_STAGES = ("attack", "fuzz", "faithfulness", "equivalence", "disclosure")

#: The gates that report a reviewer's judgment, and the two that re-run what a review
#: submitted. Kept apart because a repair expires the first kind, and the second set aside
#: what was aimed at the specification it replaced.
JUDGMENT_GATES = ("audit.faithfulness", "audit.equivalence", "audit.no_disclosure")
STRENGTH_GATES = ("audit.spec_completeness", "audit.spec_soundness")


@dataclass(frozen=True, slots=True)
class _Draft:
    """A bundle one of these cases built, and what it takes to judge or review it."""

    settings: Settings
    bundle: Bundle
    backend: Backend
    name: str

    def judge(self) -> Adjudication:
        """Run every gate over the bundle at the audited level."""
        return adjudicate(
            self.bundle, backend=self.backend, settings=self.settings, level=LEVEL
        )


def _drafted(context: Context, name: str, *, root: str) -> _Draft:
    """Formalize one fixture's task into a bundle root of this case's own.

    The bundle is built rather than copied into place, because only a build records who
    drafted it -- and without that, `audit.independence` cannot say whether the review
    was written by someone else, which is the whole point of the stage.
    """
    target = fixtures.fixture(name)
    settings = context.tuned(bundle_root=context.path(root), **BUDGETS)
    backend = BACKENDS.get(target.backend)
    result = build(
        fixtures.tasks(settings)[target.task_id],
        backend=backend,
        provider=ScriptedProvider(source=target),
        settings=settings,
        session=ScriptedSession(source=target),
    )
    check(
        result.usable,
        f"{name}: the build wrote no solution to review: "
        f"{result.formalization.check.status}; {'; '.join(result.formalization.notes)}",
    )
    return _Draft(settings=settings, bundle=result.bundle, backend=backend, name=name)


def _reviewed(
    draft: _Draft,
    source: str | None = None,
    stages: tuple[str, ...] = REVIEW_STAGES,
    session: ScriptedSession | None = None,
) -> Review:
    """Review a bundle with a script that answers as someone other than its author."""
    session = session or ScriptedSession(REVIEW_MODEL, source=source or draft.name)
    result = audit(
        draft.bundle,
        backend=draft.backend,
        provider=reviewing(source or draft.name),
        settings=draft.settings,
        session=session,
    )
    check(
        result.usable,
        f"{draft.name}: the review filed nothing a gate could act on: "
        f"{'; '.join(result.audit.notes)}",
    )
    equals(tuple(session.answered), stages, "auditors the review ran")
    return _recorded(draft, result)


def _recorded(draft: _Draft, result: AuditResult) -> Review:
    """The review as the gates will read it: off disk, not out of the session."""
    written = draft.bundle.audit()
    check(written is not None, f"{draft.name}: the review was not written into the bundle")
    assert written is not None  # noqa: S101 - narrowing after the check above
    session = result.audit
    equals(
        [row.id for row in written.submissions],
        [row.id for row in session.kept] + [filed.id for filed in session.submissions],
        "submissions the bundle records against what the session kept and filed",
    )
    return written


def _cased(rival: Rival) -> tuple[str, str, str, str]:
    """What `rivals/index.toml` says a case is, apart from how a drafter's check found it."""
    return (rival.id, rival.kind, rival.file, rival.rationale)


def _undecided(statuses: dict[str, Status], gates: tuple[str, ...], what: str) -> None:
    """Require a set of gates to have declined to judge rather than passed or failed."""
    for gate in gates:
        equals(statuses.get(gate), Status.SKIP, f"{gate} {what}")


def certified(context: Context) -> list[Observation]:
    """A reviewed bundle reaches the audited level, on evidence the gates checked again."""
    draft = _drafted(context, SOUND, root="certified")
    review = _reviewed(draft)

    # Both kinds, and no shadow for any of them: each runs as written, so the bundle's own
    # `conformance.py` is what asks the benchmark whether it is right, and a repository patch is
    # asked for only where an accepted attack cannot run. It takes both kinds for either
    # strength gate to have a finding either way.
    equals(
        [(row.id, row.kind, bool(row.shadow)) for row in review.submissions],
        [
            ("attack-1", "weakness", False),
            ("attack-2", "weakness", False),
            ("control-1", "control", False),
        ],
        "the implementations the review submitted",
    )
    equals(
        [(row.role, row.verdict) for row in review.judgments],
        [("faithfulness", "sound"), ("equivalence", "sound"), ("disclosure", "sound")],
        "the judgments the review filed",
    )
    equivalence = review.judgment("equivalence")
    check(equivalence is not None, "the review filed no equivalence judgment")
    assert equivalence is not None  # noqa: S101 - narrowing after the check above
    operations = equivalence.operations
    check(operations, "the equivalence judgment set no operation against the golden patch's")
    equals(
        [item.detail for item in operations if item.kind not in PRESERVING],
        [],
        "operations the review set against the golden patch that do not preserve behavior",
    )
    check(
        not needs_review(draft.bundle),
        "the bundle asks to be reviewed again immediately after a review of it",
    )

    adjudication = draft.judge()
    verdicts, certification = adjudication.verdicts, adjudication.certification
    objected = sorted({*certification.failed, *certification.undecided, *certification.missing})
    equals(objected, [], f"gates that objected ({certification.describe()})")
    equals(
        certification.outcome,
        Outcome.CERTIFIED,
        f"outcome at level={LEVEL} ({certification.describe()})",
    )

    # What each strength gate concluded, from re-running the submissions rather than
    # from what the review claimed about them.
    equals(
        verdicts["audit.spec_completeness"].details.get("refuted"),
        ["attack-1", "attack-2"],
        "attacks the specification refuted when the gate re-ran them",
    )
    equals(
        verdicts["audit.spec_soundness"].details.get("admitted"),
        ["control-1"],
        "controls the specification accepted and the benchmark's tests judged correct",
    )
    independence = verdicts["audit.independence"].details
    equals(
        (independence.get("author"), independence.get("reviewer")),
        (f"scripted:{MODEL}", f"scripted:{REVIEW_MODEL}"),
        "who drafted the bundle and who reviewed it",
    )

    table = read_text(draft.bundle.evidence_dir / "audit-submissions.txt")
    unlisted = [row.id for row in review.submissions if row.id not in table]
    equals(unlisted, [], "submissions missing from the evidence the strength gates wrote")
    return [
        Observation("outcome", certification.describe()),
        Observation("submissions", f"{len(review.submissions)} re-run: checker and oracle"),
        Observation("operations", f"{len(operations)} behavior-preserving"),
    ]


def stale(context: Context) -> list[Observation]:
    """Rewriting the specification expires the review of it, and nothing more."""
    draft = _drafted(context, SOUND, root="stale")
    review = _reviewed(draft)
    before = draft.judge().certification
    equals(
        before.outcome,
        Outcome.CERTIFIED,
        f"outcome before the specification changed ({before.describe()})",
    )

    # The weak fixture's specification, spliced into a bundle that had certified: a
    # plausible edit rather than a corruption, and one nobody has been asked to review.
    weakened = markers.parse(
        read_text(fixtures.fixture(WEAK).directory / "solution.py"), draft.backend.comment
    )["spec"].text
    write_text(
        draft.bundle.solution_path,
        markers.replace_region(
            draft.bundle.solution(), draft.backend.comment, "spec", weakened
        ),
    )

    after = draft.judge()
    statuses = {gate: verdict.status for gate, verdict in after.verdicts.items()}
    _undecided(statuses, JUDGMENT_GATES, "after the specification it read changed")
    _undecided(statuses, STRENGTH_GATES, "after the specification it attacked changed")
    for gate in JUDGMENT_GATES:
        verdict = after.verdicts[gate]
        equals(verdict.skip_reason, SkipReason.INCONCLUSIVE, f"why {gate} declined to judge")
        equals(
            verdict.details.get("stale"),
            [SPEC if gate == "audit.no_disclosure" else SPEC_UNCOMMENTED],
            f"what {gate} says its judgment was reached from",
        )
    for gate in STRENGTH_GATES:
        rulings = after.verdicts[gate].details.get("rulings", {})
        equals(
            sorted(name for name, said in rulings.items() if "specification differs" in said),
            sorted(row.id for row in review.submissions),
            f"submissions {gate} set aside as aimed at a specification this bundle dropped",
        )

    # The one audited gate that read none of it is unaffected: a repair costs a fresh
    # review of what it changed, not of everything.
    equals(
        statuses.get("audit.independence"),
        Status.PASS,
        "audit.independence, which reads no artifact the edit touched",
    )
    check(
        needs_review(draft.bundle),
        "the bundle does not ask to be reviewed again after its specification changed",
    )
    check(
        not after.certification.certified,
        f"an edited bundle is still certified ({after.certification.describe()})",
    )
    return [
        Observation("before", before.describe()),
        Observation("after", after.certification.describe()),
        Observation("expired", ", ".join(JUDGMENT_GATES + STRENGTH_GATES)),
    ]


def loop(context: Context) -> list[Observation]:
    """A bundle that fails review is repaired, reviewed again, and then certifies."""
    draft = _drafted(context, WEAK, root="loop")
    review = _reviewed(draft)

    first = draft.judge()
    completeness = first.verdicts["audit.spec_completeness"]
    equals(
        completeness.details.get("too_weak"),
        ["attack-1", "attack-2"],
        "wrong implementations the specification accepted",
    )
    # A falsifier that failed to refute has not shown the specification accepts them,
    # only that it found no counterexample, so the finding is undecided rather than a
    # failure. It still blocks certification, and a repair still addresses it.
    equals(
        completeness.skip_reason,
        SkipReason.INCONCLUSIVE,
        "why the completeness gate declined to judge",
    )
    equals(first.verdicts["audit.faithfulness"].status, Status.FAIL, "audit.faithfulness")
    # The specification is too weak, not too strong: it refuses nothing it should accept.
    equals(first.verdicts["audit.spec_soundness"].status, Status.PASS, "audit.spec_soundness")
    check(
        not first.certification.certified,
        f"a bundle its reviewer rejected was certified ({first.certification.describe()})",
    )

    findings = routed(first.verdicts, LEVEL)[Route.REPAIR]
    named = [verdict.gate for verdict in findings]
    for gate in ("audit.spec_completeness", "audit.faithfulness"):
        check(gate in named, f"{gate} objected but was not put to the repair: {named}")

    session = ScriptedSession(source=WEAK, repaired=SOUND)
    repaired = repair(
        draft.bundle,
        backend=draft.backend,
        settings=draft.settings,
        verdicts=findings,
        session=session,
    )
    equals(tuple(session.answered), ("repair",), "sessions the repair started")
    asked = session.asked[0].prompt
    unbriefed = [gate for gate in named if f"`{gate}`" not in asked]
    equals(unbriefed, [], "findings the repair session was not briefed with")
    equals(repaired.status, "REPAIRED", "what the repair session reported")
    kept = draft.bundle.audit()
    check(kept is not None, "the repair left the bundle with no review at all")
    assert kept is not None  # noqa: S101 - narrowing after the check above
    # The judgments stay on record, and every one of them read the specification the
    # repair replaced, so none of them still describes the bundle.
    digests = readings(draft.bundle, draft.backend)
    equals(
        [judgment.role for judgment in kept.judgments if not judgment.stale(digests)],
        [],
        "judgments still current after a repair",
    )
    check(
        needs_review(draft.bundle),
        "a repaired bundle does not ask to be reviewed again, so a repair could certify "
        "itself on a judgment of the artifacts it replaced",
    )

    # The session wrote every author file, so the repaired bundle is the sound fixture --
    # byte for byte, artifact for artifact, but for `rivals/index.toml`, whose `found`
    # lines record checks a drafter ran and a repair session does not.
    sound = fixtures.fixture(SOUND)
    index = (draft.bundle.rivals_dir / "index.toml").relative_to(draft.bundle.root)
    for relative in sound.artifacts():
        if relative == index.as_posix():
            continue
        equals(
            read_text(draft.bundle.root / relative),
            read_text(sound.directory / relative),
            f"{relative} after the repair",
        )
    equals(
        [_cased(rival) for rival in draft.bundle.battery()],
        [_cased(rival) for rival in Bundle(sound.directory).battery()],
        "the property-based test suite after the repair",
    )

    rereview = ScriptedSession(REVIEW_MODEL, source=SOUND)
    again = _reviewed(draft, SOUND, session=rereview)
    # The attack auditor is shown each attack filed against the specification the repair
    # replaced, with what the gates ruled, to write the weaknesses again first.
    shown = rereview.asked[REVIEW_STAGES.index("attack")].prompt
    for row in review.submissions:
        if row.kind == "weakness":
            check(
                f"`{row.id}`" in shown and "a weakness of the specification" in shown,
                f"the re-review's attack auditor was not shown {row.id} with its ruling",
            )
    final = draft.judge()
    certification = final.certification
    equals(
        certification.outcome,
        Outcome.CERTIFIED,
        f"outcome after the repair was reviewed ({certification.describe()})",
    )
    # What certifies the repaired bundle is the re-review's own submissions: those filed
    # against the specification the repair replaced are not run again, and their files
    # are gone from the review.
    filed = [row.id for row in again.submissions]
    equals(
        filed, ["attack-3", "attack-4", "control-2"], "submissions on record after re-review"
    )
    equals(
        final.verdicts["audit.spec_completeness"].details.get("refuted"),
        ["attack-3", "attack-4"],
        "the re-review's attacks that the repaired specification refuted",
    )
    left = [
        row.file for row in review.submissions if (draft.bundle.audit_dir / row.file).exists()
    ]
    equals(left, [], "files of submissions the re-review replaced still in audit/")
    account = read_text(draft.bundle.audit_dir / "notes.md")
    for row in again.submissions:
        check(
            f"`{row.id}`" in account,
            f"audit/notes.md does not account for {row.id}, which the review is judged on",
        )
    accepted = ", ".join(completeness.details.get("too_weak", []))
    return [
        Observation("review", f"{first.certification.describe()}, accepted {accepted}"),
        Observation("repair", f"{len(repaired.written)} artifacts"),
        Observation("re-review", certification.describe()),
    ]


def assumed(context: Context) -> list[Observation]:
    """An unchanged callee is grounded twice: by the bundle, and by a review of it."""
    draft = _drafted(context, ASSUMED, root="assumed")
    review = _reviewed(draft, stages=ASSUMED_STAGES)

    equals(
        [(row.id, row.callee) for row in review.fuzzers],
        [("fuzz-1", CALLEE)],
        "the programs the review wrote against what the specification assumes",
    )
    written = draft.bundle.fuzzer_source(review.fuzzers[0])
    check(
        written.strip() != (draft.bundle.axioms() or "").strip(),
        "the review's program is the bundle's own `axioms.py` again, so nothing independent "
        "was run against the assumption",
    )

    adjudication = draft.judge()
    verdicts, certification = adjudication.verdicts, adjudication.certification
    objected = sorted({*certification.failed, *certification.undecided, *certification.missing})
    equals(objected, [], f"gates that objected ({certification.describe()})")
    equals(
        certification.outcome,
        Outcome.CERTIFIED,
        f"outcome at level={LEVEL} ({certification.describe()})",
    )

    # Both sides of the assumption, each from the gate that ran a program rather than
    # from what anyone said about one.
    for gate, field in (
        ("spec.axioms_grounded", "grounded"),
        ("audit.axiom_soundness", "assumed"),
    ):
        verdict = verdicts[gate]
        equals(verdict.details.get(field), [CALLEE], f"the callee(s) {gate} decided")
        check(verdict.evidence, f"{gate} wrote no log, so its run cannot be re-read")
        for name in verdict.evidence:
            check(
                f"benchproofer:grounded {CALLEE}" in read_text(draft.bundle.root / name),
                f"{gate} kept a log that does not record the program agreeing about {CALLEE}",
            )
    return [
        Observation("outcome", certification.describe()),
        Observation("assumed", f"{CALLEE}, grounded by the bundle and by the review"),
        Observation("fuzzers", verdicts["audit.axiom_soundness"].summary),
    ]


CASES: tuple[Case, ...] = (
    Case(
        id="review.certified",
        summary="an independently reviewed bundle is certified at the audited level",
        procedure=certified,
        requires=fixtures.REQUIRES,
    ),
    Case(
        id="review.stale",
        summary="rewriting a reviewed specification expires the review of it",
        procedure=stale,
        requires=fixtures.REQUIRES,
    ),
    Case(
        id="review.loop",
        summary="a bundle that fails review is repaired, reviewed again, and certified",
        procedure=loop,
        requires=fixtures.REQUIRES,
    ),
    Case(
        id="review.assumed",
        summary="a callee the specification models survives an independent fuzzer",
        procedure=assumed,
        requires=fixtures.REQUIRES,
    ),
)
