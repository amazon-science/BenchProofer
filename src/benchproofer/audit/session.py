# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a review of one bundle is made of, whichever auditor asks it.

A review is asked six questions about a bundle nobody has told the reviewer how to
build, each by an auditor of its own (`audit.agents.Reviewers`). Three are addressed with a
file:

1. **attack**: a wrong implementation the shipped specification still accepts, and, when
   the checker accepts one that cannot run as written, the same attack as a patch to the
   repository, so the benchmark's own tests can say it is wrong;
2. **control**: a correct implementation, written differently from the shipped one, that
   the specification nonetheless refuses -- with its equivalent patch too, for the same reason;
3. **fuzzer**: for each callee the `axioms` region assumes or models, a program
   that runs the real callee looking for an input where it behaves otherwise;

and three are addressed with a judgment:

4. **faithfulness**: whether the specification describes the task it claims to;
5. **equivalence**: whether the implementation is the golden patch rather than
   a different one, operation by operation, an unchanged callee among them only where the
   golden patch does not change it;
6. **disclosure**: whether the specification gives away the implementation to a solver.

Last, once the gates have re-run the attacks and controls, the attack validation auditor
rules on each that cannot be determined by execution (`gates.audit._Outcome.left_open`):
whether an attack succeeds, and whether a control is correct and the specification refuses
it.

A judgment is worth what the reading behind it is worth, so each is recorded with a
digest of the files it read. A file is not taken on trust either: the gate that reports
it re-runs it through the checker, the oracle, or the environment the benchmark's tests
run in, which is why no auditor's word decides a submission the runs decide. The attack
validation auditor's ruling counts only for an attack or a control that cannot be determined
by execution, and only with the input and what of the task it rests on.

This module holds what the auditors share: the auditors and what each reads, the record a review
leaves (`Audit`), the system prompt an auditor is given, what the attack validation auditor is
shown (`unruled`) and what the equivalence auditor is shown a repair changed (`added_block`).
It writes no verdict of its own; adjudication happens afterwards, over what the review wrote to
disk.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ..backends.base import Backend, BackendKind
from ..core import markers, material, variant
from ..core.axioms import callees, declared_in
from ..core.bundle import (
    AuditRole,
    Bundle,
    Defect,
    Fuzzer,
    Judgment,
    Review,
    Ruling,
    Submission,
    SubmissionKind,
)
from ..core.readings import IMPL, SPEC, SPEC_UNCOMMENTED, TWINS
from ..core.task import Task
from ..errors import BenchproofError
from ..gates.audit import OUTSIDE, UNRULED, section_of
from ..log import logger
from ..util.digest import digest_text
from ..util.fsio import read_text
from . import prompts

__all__ = [
    "ASKS",
    "JUDGED_ROLES",
    "LANES",
    "LANE_OF",
    "LANE_READS",
    "SUBMISSION_GATES",
    "VERDICTS",
    "Audit",
    "Filed",
    "Fuzzed",
    "Lane",
    "added_block",
    "admitted",
    "assumed",
    "attack_stands",
    "axioms_digest",
    "examined",
    "kept_fuzzers",
    "roles_for",
    "unattacked",
    "unruled",
]

log = logger(__name__)

#: What each judgment role reads, as bundle-relative names or as the parts of the solution
#: `core.readings` names. A judgment expires when one of these changes, and only then: a
#: repair to a proof cannot invalidate a reading of the specification, nor one to a comment
#: a judgment of what the specification states, and pretending otherwise would make every
#: repair cost a full re-review. Faithfulness reads the type bridge too, in
#: `correspondence.md` and `conformance.py`: whether a clause states what a test checks
#: can rest on how the type bridge reads the repository's values. Equivalence reads
#: `conformance.py` and `axioms.py` as well: it checks that the repository side of
#: `conformance.py` calls the repository's code, a Python port of the implementation
#: `conformance.py` compares, and whether a repair made either program compare less than the
#: specification needs, which no gate checks.
ROLE_READS: dict[AuditRole, tuple[str, ...]] = {
    "faithfulness": (
        SPEC_UNCOMMENTED,
        TWINS,
        "correspondence.md",
        "conformance.py",
        "../task.json",
    ),
    "equivalence": (
        SPEC_UNCOMMENTED,
        IMPL,
        "correspondence.md",
        "conformance.py",
        "axioms.py",
        "../task.json",
        "../reference.patch",
    ),
    "disclosure": (SPEC, "../task.json"),
}
#: The roles a review is asked to judge, in the order it is asked.
JUDGED_ROLES: tuple[AuditRole, ...] = ("faithfulness", "equivalence", "disclosure")
#: The verdicts a judgment may reach; a reply naming anything else carries no judgment.
VERDICTS: tuple[str, ...] = ("sound", "unsound", "uncertain")

#: The parts a review is made of, each asked on its own: the attacks and controls, the
#: fuzzers, one per judged role, and the rulings on the attacks and controls that cannot be
#: determined by execution. An auditor is asked again when what it read changed, and until
#: then what it filed stands. The attack validation auditor comes last, so the faithfulness
#: auditor's coverage table is there for it.
Lane = Literal["attack", "fuzz", "faithfulness", "equivalence", "disclosure", "validation"]
LANES: tuple[Lane, ...] = ("attack", "fuzz", *JUDGED_ROLES, "validation")
#: Which auditor of the review each audit gate reads, for asking that auditor again. The two
#: submission gates are also read for the attack validation auditor, where they list attacks
#: or controls that cannot be determined by execution and that it has not ruled on
#: (`gates.audit.UNRULED`), which `pipeline.route` reads off their mark.
LANE_OF: dict[str, Lane] = {
    "audit.spec_completeness": "attack",
    "audit.spec_soundness": "attack",
    "audit.faithfulness": "faithfulness",
    "audit.equivalence": "equivalence",
    "audit.no_disclosure": "disclosure",
    "audit.axiom_soundness": "fuzz",
}
#: The gates that re-run the attack auditor's submissions, whose verdicts list the attacks and
#: controls that cannot be determined by execution and that the attack validation auditor has
#: not ruled on (`unruled`).
SUBMISSION_GATES: tuple[str, ...] = ("audit.spec_completeness", "audit.spec_soundness")
#: What the two auditors that file programs read. Both are about the specification: an attack
#: written to probe one specification says nothing about where the next one is weak, and a
#: fuzzer attacks what the specification assumes, which is part of it.
LANE_READS: dict[str, tuple[str, ...]] = {
    "attack": (SPEC, "../task.json"),
    "fuzz": (SPEC, "../task.json"),
}


def roles_for(task: Task) -> tuple[AuditRole, ...]:
    """The roles a review of this task can be asked to judge.

    Equivalence compares the shipped implementation with the golden patch, so a task that
    ships none cannot be asked about it. Leaving the role out is not
    the same as passing it: the gate reports an unjudged role as inconclusive, and this
    is what keeps the review stage from being asked for a judgment nobody could reach
    and the repair stage from chasing it.
    """
    if task.reference.is_empty:
        return tuple(role for role in JUDGED_ROLES if role != "equivalence")
    return JUDGED_ROLES


_KIND_NOTE = {
    BackendKind.PROVER: (
        "an accepting verdict means the implementation provably satisfies the "
        "specification for every input its preconditions admit, so an attack has to "
        "satisfy the specification rather than merely evade a test. The proof is part of "
        "what you submit, too, in whatever form this checker takes it -- a loop invariant, "
        "a decreases clause, an intermediate assertion, a proof region of its own -- "
        "because a file this checker rejects when its proof is missing a step is "
        "evidence about what you wrote and not about the specification."
    ),
    BackendKind.FALSIFIER: (
        "an accepting verdict means only that no counterexample was found within its "
        "search budget. An attack that survives because the search was shallow is a "
        "finding about the specification only if it is also plausible code."
    ),
}


#: The kinds of implementation the attack auditor files, each with the word its files, ids and
#: notes are named after, in the order the auditor's report is read.
ASKS: tuple[tuple[SubmissionKind, str], ...] = (("weakness", "attack"), ("control", "control"))


@dataclass(frozen=True, slots=True)
class Filed:
    """One implementation a review submitted, as the single file it consists of.

    `source` is a complete solution file: the reviewer's implementation spliced into the
    solution file, so the specification it is judged against is the shipped specification byte
    for byte, and what the benchmark makes of it is decided by the bundle's own
    `conformance.py`. An attack the checker accepts whose implementation cannot run as written
    has no `conformance.py` to go in, so `patch` holds the same attack as a change to the
    repository -- the golden patch with the attack's change in it -- for the tests to run on
    instead. It is filed as the submission's shadow. `test`, `cites` and `refutation` are the
    executed evidence `Submission` describes, `test` as the program's source.
    """

    id: str
    kind: SubmissionKind
    claim: str
    file: str
    source: str
    patch: str = ""
    test: str = ""
    cites: str = ""
    refutation: str = ""

    @property
    def shadow(self) -> str:
        """Where `patch` is filed in the audit directory, empty when there is none."""
        return f"{self.id}.patch" if self.patch else ""

    @property
    def tested(self) -> str:
        """Where `test` is filed in the audit directory, empty when there is none."""
        return f"{self.id}.test.py" if self.test else ""

    def record(self) -> Submission:
        """How this submission appears in the review index."""
        return Submission(
            id=self.id,
            kind=self.kind,
            file=self.file,
            shadow=self.shadow,
            claim=self.claim,
            test=self.tested,
            cites=self.cites,
            refutation=self.refutation,
        )

    def sources(self) -> dict[str, str]:
        """The files this submission contributes to the ``audit`` directory."""
        files = {self.file: self.source}
        if self.patch:
            files[self.shadow] = self.patch
        if self.test:
            files[self.tested] = self.test
        return files


@dataclass(frozen=True, slots=True)
class Fuzzed:
    """One program a review wrote against a callee the specification assumes.

    Always Python, whatever the checker reads: it runs where the benchmark's own tests
    run, against the callee itself rather than against a model of it.
    """

    id: str
    callee: str
    claim: str
    source: str
    #: The digest of the `axioms` region it was written against (`Fuzzer.against`).
    against: str = ""

    @property
    def file(self) -> str:
        """Name this program is filed under in the audit directory."""
        return f"{self.id}.fuzz.py"

    def record(self) -> Fuzzer:
        """How this program appears in the review index."""
        return Fuzzer(
            id=self.id,
            file=self.file,
            callee=self.callee,
            claim=self.claim,
            against=self.against,
        )


@dataclass(frozen=True, slots=True)
class Audit:
    """Everything one review produced for one bundle."""

    task_key: str
    backend: str
    provider: str
    model: str
    author: str = ""
    submissions: tuple[Filed, ...] = ()
    #: What an earlier review submitted that this one keeps, as it is on disk: all of it
    #: where the attack auditor filed nothing this time, and otherwise what was filed against
    #: the specification as it stands (`attack_stands`). Once a repair changed that, the
    #: auditor's own submissions replace the earlier ones, which are not run again.
    kept: tuple[Submission, ...] = ()
    #: What the attack auditor showed by running code that is not an attack, as the bundle
    #: records it after this review: this review's, beside an earlier review's while the
    #: specification that one attacked stands (`Review.defects`).
    defects: tuple[Defect, ...] = ()
    #: One program per unchanged callee this review attacked, empty when the
    #: specification assumes nothing.
    fuzzers: tuple[Fuzzed, ...] = ()
    #: Fuzzers an earlier review filed against the same assumptions, kept as they are on
    #: disk: while the assumption stands, a program that attacked it still does.
    kept_fuzzers: tuple[Fuzzer, ...] = ()
    #: The attack validation auditor's rulings as the bundle records them after this review:
    #: this review's, beside an earlier review's about the other submissions on record.
    rulings: tuple[Ruling, ...] = ()
    judgments: tuple[Judgment, ...] = ()
    #: Judgments of the roles this review did not ask again, because what each read is
    #: unchanged, kept as they are on disk.
    kept_judgments: tuple[Judgment, ...] = ()
    #: What the `attack` and `fuzz` auditors read, as `Review.examined` records it.
    examined: dict[str, dict[str, str]] = field(default_factory=dict)
    #: One record per agent session the review ran: its auditor, budget spent, and what it
    #: looked at.
    sessions: tuple[dict[str, Any], ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def reviewer(self) -> str:
        """Which model reviewed the bundle, as ``provider:model``."""
        return f"{self.provider}:{self.model}"

    @property
    def independent(self) -> bool:
        """Whether a different model reviewed the bundle than drafted it.

        A model reviewing its own work is not an independent review: it is the same
        judgment twice, and the gates say so rather than counting it. The models are
        compared and not the providers, since one model reached two ways is still one.
        """
        return bool(self.author) and _model(self.author) != _model(self.reviewer)

    def on_record(self) -> tuple[Submission, ...]:
        """Every submission the bundle carries after this review, kept ones first."""
        return (*self.kept, *(filed.record() for filed in self.submissions))

    def review(self) -> Review:
        """The index that describes this review, for the bundle to store."""
        submissions = self.on_record()
        ids = {item.id for item in submissions}
        return Review(
            reviewer=self.reviewer,
            author=self.author,
            independent=self.independent,
            submissions=submissions,
            defects=self.defects,
            fuzzers=(*self.kept_fuzzers, *(program.record() for program in self.fuzzers)),
            rulings=tuple(ruling for ruling in self.rulings if ruling.id in ids),
            judgments=(*self.kept_judgments, *self.judgments),
            examined=self.examined,
        )

    def sources(self) -> dict[str, str]:
        """Every file this review contributes, keyed by name in the audit directory."""
        files: dict[str, str] = {}
        for filed in self.submissions:
            files.update(filed.sources())
        files.update({program.file: program.source for program in self.fuzzers})
        return files

    def provenance(self) -> dict[str, Any]:
        """The review's record, for the bundle manifest."""
        return {
            "reviewer": self.reviewer,
            "author": self.author,
            "independent": self.independent,
            "submissions": [filed.id for filed in self.submissions],
            "kept": [item.id for item in self.kept],
            "fuzzers": [program.id for program in self.fuzzers],
            "kept_fuzzers": [program.id for program in self.kept_fuzzers],
            "judgments": {judgment.role: judgment.verdict for judgment in self.judgments},
            "kept_judgments": [judgment.role for judgment in self.kept_judgments],
            "sessions": list(self.sessions),
            "notes": list(self.notes),
        }


def _system(backend: Backend, lane: Lane) -> str:
    """One auditor's part of the system prompt (`system.md`), which `agent-system.md` includes.

    It names the checker and what its verdicts are worth. An auditor that files programs --
    attacks and controls in the checker's language, fuzzers aimed at what its axioms
    assume -- is also told what the drafter is told of how the file is written: how it
    states a callee the fix does not change (`Backend.callees`), and the backend's drafting
    guidance, which says how that language is written so the checker reads it, and so is the
    attack validation auditor, which may write a candidate or a control's proof to show a
    ruling. An auditor that judges a role writes no such program and judges by the review's own
    rules, the same for every backend, so it is given neither, and no drafting idiom becomes a
    standard the bundle is held to.
    """
    written = (
        ""
        if lane in JUDGED_ROLES
        else (
            f"## How the file is written\n\n{backend.callees()}\n\n{backend.guidance()}"
        ).rstrip()
    )
    return prompts.render(
        "system",
        backend=backend.name,
        language=backend.language,
        kind=str(backend.kind),
        kind_note=_KIND_NOTE[backend.kind],
        guidance=written,
    )


def _impl(source: str, backend: Backend) -> str:
    """The implementation regions of a file, which `variant.assemble` guarantees it has."""
    return markers.joined(markers.parse(source, backend.comment), "impl").strip()


def _among(body: str, bodies: Sequence[str], backend: Backend) -> bool:
    """Whether an implementation is one of ``bodies``, comments and spacing aside.

    The bodies are kept as written, because they are also what the reviewer is shown
    of its earlier submissions; only the comparison leaves the comments out.
    """
    found = variant.fingerprint(body, backend)
    return any(variant.fingerprint(other, backend) == found for other in bodies)


def axioms_digest(solution: str, backend: Backend) -> str:
    """A digest of the solution's `axioms` region, empty when it has none or no markers."""
    try:
        region = markers.parse(solution, backend.comment).get("axioms")
    except BenchproofError:
        return ""
    return digest_text(region.text) if region is not None and region.text.strip() else ""


def assumed(solution: str, backend: Backend) -> tuple[str, ...]:
    """The callees the solution's `axioms` region assumes, empty when it has none."""
    return callees(declared_in(solution, backend.comment))


def unattacked(solution: str, backend: Backend, kept: Sequence[Fuzzer]) -> tuple[str, ...]:
    """The unchanged callees no fuzzer of those ``kept`` attacks."""
    attacked = {fuzzer.callee for fuzzer in kept}
    return tuple(callee for callee in assumed(solution, backend) if callee not in attacked)


def kept_fuzzers(
    recorded: Review | None, solution: str, backend: Backend
) -> tuple[Fuzzer, ...]:
    """The fuzzers on record that still attack what this solution assumes.

    A fuzzer is kept while the `axioms` region it was written against is the one the
    solution ships and its callee is still assumed there. Once the assumption changes, a
    program written against the old one says nothing about the new one, and a new one is
    asked for.
    """
    if recorded is None:
        return ()
    against = axioms_digest(solution, backend)
    if not against:
        return ()
    still = set(assumed(solution, backend))
    return tuple(
        fuzzer
        for fuzzer in recorded.fuzzers
        if fuzzer.against == against and fuzzer.callee in still
    )


def attack_stands(recorded: Review | None, digests: dict[str, str]) -> bool:
    """Whether what the attack auditor last read still reads as it did, by ``digests``.

    While it does, what the auditor filed stands and the gates re-run it. Once the
    specification it attacked changed, the auditor is asked again, and what it files replaces
    what it filed before.
    """
    read = recorded.examined.get("attack") if recorded is not None else None
    return read is not None and all(
        digests.get(name) == read.get(name) for name in LANE_READS["attack"]
    )


def examined(
    recorded: Review | None, digests: dict[str, str], lanes: Sequence[str]
) -> dict[str, dict[str, str]]:
    """What the auditors that file programs read: this review's for the auditors it asked."""
    found = dict(recorded.examined) if recorded is not None else {}
    for lane in lanes:
        found[lane] = {name: digests[name] for name in LANE_READS[lane] if name in digests}
    return found


def _model(identity: str) -> str:
    """The model of a ``provider:model`` identity."""
    return identity.rpartition(":")[2]


#: How much of what repairs changed since drafting the equivalence auditor is shown.
ADDED_LIMIT = 8_000


def admitted(bundle: Bundle, backend: Backend) -> dict[str, str]:
    """What says which inputs the bundle's claim covers, for `added_block` to compare.

    The specification, and what `correspondence.md` lists under `Outside the bridge`.
    Empty when the solution cannot be read.
    """
    try:
        spec = backend.spec_view(bundle.solution())
    except BenchproofError:
        return {}
    return {
        "spec": spec,
        "outside": section_of(_text(bundle.correspondence_path) or "", OUTSIDE),
    }


def added_block(bundle: Bundle, backend: Backend) -> str:
    """What repairs changed in the specification and under `Outside the bridge` since drafting.

    Set against what `pipeline.build` recorded of the drafted bundle in `manifest.json`
    (`admitted`, as `provenance.drafted`), so the equivalence auditor checks each precondition
    and entry a repair added; and the inputs `conformance.py` did not compare because an entry
    names them, as `impl.conformance` recorded them about the bundle as it stands
    (`conformance-rules.md`), which the auditor checks as it checks the entry. Empty when there
    is neither.
    """
    manifest = bundle.manifest()
    record = manifest.provenance.get("drafted")
    now = admitted(bundle, backend)
    diff = ""
    if isinstance(record, dict) and record and now:
        diff = material.changes(
            [
                ("specification", str(record.get("spec") or ""), now["spec"]),
                ("Outside the bridge", str(record.get("outside") or ""), now["outside"]),
            ],
            ADDED_LIMIT,
            before="drafted",
            after="now",
        )
    verdict = manifest.verdicts.get("impl.conformance")
    skipped = (
        [str(line) for line in verdict.details.get("outside") or ()]
        if verdict is not None and bundle.describes(verdict)
        else []
    )
    sections = []
    if diff:
        sections.append(
            "## What repairs changed since drafting\n\n"
            "Repairs since the bundle was drafted changed its specification, or what "
            "`correspondence.md` lists under `Outside the bridge`, as below: the drafted text "
            "against the text now. Check each precondition and each `Outside the bridge` entry "
            "these lines add, as the rules above say of one a repair added.\n\n"
            f"```diff\n{diff}\n```"
        )
    if skipped:
        sections.append(
            "## What `conformance.py` did not compare\n\n"
            "`conformance.py` declared these inputs left out by the `Outside the bridge` entry "
            "each quotes, and did not compare on them. Check each as you check that entry: "
            "trace the input through the function before the fix and after it and see the "
            "same lines run, apart from the false test of a condition the golden patch "
            "adds.\n\n" + "\n".join(f"* {line}" for line in skipped)
        )
    return "\n\n".join(sections)


def _stamped(judgment: Judgment, digests: dict[str, str]) -> Judgment:
    """Record what this judgment's role read, so the gate can tell when it is stale."""
    read = {name: digests[name] for name in ROLE_READS[judgment.role] if name in digests}
    return judgment.model_copy(update={"reads": read})


def unruled(bundle: Bundle) -> dict[str, str]:
    """The attacks and controls the attack validation auditor is asked to rule on, by id.

    Those the `SUBMISSION_GATES` verdicts list (`gates.audit.UNRULED`) as ones that cannot be
    determined by execution, each with what the gates established about it. Only while a
    verdict still describes the bundle, since a review or a repair since then may have changed
    which those are.
    """
    found: dict[str, str] = {}
    verdicts = bundle.manifest().verdicts
    for gate in SUBMISSION_GATES:
        verdict = verdicts.get(gate)
        if verdict is None or not bundle.describes(verdict):
            continue
        listed = verdict.details.get(UNRULED)
        if isinstance(listed, dict):
            found.update({str(name): str(said) for name, said in listed.items()})
    return found


def _text(path: Path) -> str | None:
    """Read a bundle artifact, or None when it does not ship."""
    return read_text(path) if path.is_file() else None


def _author(bundle: Bundle) -> str:
    """Who drafted this bundle, as ``provider:model``, when the manifest says.

    An empty result is honest: a bundle from elsewhere need not record an author, and
    a review of it is independent in the only sense that matters.
    """
    drafted = bundle.manifest().provenance.get("formalization", {})
    if not isinstance(drafted, dict):
        return ""
    provider, model = drafted.get("provider"), drafted.get("model")
    return f"{provider}:{model}" if provider and model else ""


def _highest(already: Sequence[Submission] | Sequence[Fuzzer]) -> int:
    """The largest index the ids on record use, or 0 when there are none.

    A re-review numbers from here rather than from how many submissions are on record:
    a round that dropped a repeat left a gap, so counting would hand the next
    submission an id an earlier round already wrote a file under, and the index would
    list two submissions whose bodies are one file.
    """
    tails = (item.id.rpartition("-")[2] for item in already)
    return max((int(tail) for tail in tails if tail.isdigit()), default=0)
