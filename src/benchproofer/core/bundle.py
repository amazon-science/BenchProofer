# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The bundle: one task formalized in one backend, plus its `manifest.json`.

On disk::

    <root>/<benchmark>/<task-slug>/
        task.json              the normalized task, frozen at build time
        reference.patch        the benchmark's reference solution, when it is a diff
        <backend>/
            manifest.json      digests, provenance, and one verdict per gate
            solution.<ext>     spec and implementation, in marker regions
            twins/*.<ext>      pre-fix implementations: same spec, unfixed implementation
            twins/index.toml   each pre-fix implementation's refutation witness, if it has one
            rivals/index.toml  the property-based test suite's manifest
            rivals/*.<ext>     one rival implementation per case of the suite
            correspondence.md  the implementation's operations mapped to the golden patch's
            conformance.py     program comparing the implementation with the repository
            axioms.py          program checking what the spec assumes of its callees
            audit/index.toml   an independent review: submissions, rulings and judgments
            audit/*.<ext>      one implementation per submission the review filed
            audit/*.fuzz.py    one fuzzer per unchanged callee the review attacked
            notes.md           free-form record for reviewers
            evidence/          artifacts a gate wrote to support its verdict

The task and its reference are frozen once per task and shared by every backend,
so two formalizations of one task cannot drift onto different inputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..errors import BundleError
from ..util.digest import digest_file, digest_text, short
from ..util.fsio import (
    artifact_files,
    load_toml,
    read_json,
    read_text,
    write_json,
    write_text,
)
from .axioms import HARNESS as AXIOM_HARNESS
from .differential import HARNESS as DIFFERENTIAL_HARNESS
from .task import Task
from .verdict import Verdict

__all__ = [
    "PRESERVING",
    "REWRITTEN",
    "RULINGS",
    "SCHEMA_VERSION",
    "AuditRole",
    "Bundle",
    "Coverage",
    "Defect",
    "Fuzzer",
    "Judgment",
    "Manifest",
    "Operation",
    "OperationKind",
    "Review",
    "Rival",
    "RivalKind",
    "Ruling",
    "Submission",
    "SubmissionKind",
    "Twin",
    "freeze_task",
    "task_directory",
]

SCHEMA_VERSION: Literal[1] = 1

#: The three directions a property-based test suite attacks a specification from, each the only
#: detector of its own defect. `uniqueness` is a wrong implementation it has to refuse (too
#: weak); `soundness` a correct one written differently that it has to accept (too strong);
#: `admissibility` the reference implementation with a probe added, showing the specification
#: holds at inputs the task exercises, which catches a precondition that excludes them and that
#: no rival can reach, since every rival faces it too.
RivalKind = Literal["uniqueness", "soundness", "admissibility"]

#: What a review submitted an implementation to demonstrate: a `weakness` is wrong and
#: should be refuted, a `control` is correct and should be accepted. Only the intent:
#: both are re-run, and either can decide either question.
SubmissionKind = Literal["weakness", "control"]

#: The questions a review decides with a judgment, each reported by its own gate.
#: Strength is not among them: a reviewer addresses it with submissions Benchproofer re-runs.
AuditRole = Literal["faithfulness", "equivalence", "disclosure"]

#: How one operation of the shipped implementation corresponds to the one the
#: golden patch performs in its place. `identical` is the same operation;
#: `refinement` the same over types that spell the values more or less precisely;
#: `modeled` a callee computed by a definition under its `benchproofer:models` line; `axiom`
#: a callee assumed by contract; `unchanged` behavior the fix leaves alone, which
#: `correspondence.md` lists under `Not modeled`; `unbridged` the same on every input the
#: type bridge covers, differing only on inputs listed under `Outside the bridge`. `changed`
#: is anything else, and one is enough to make the two different programs.
OperationKind = Literal[
    "identical", "refinement", "modeled", "axiom", "unchanged", "unbridged", "changed"
]

#: The operation kinds that preserve behavior. `unbridged` does so only where
#: `correspondence.md` declares the inputs it differs on, which the equivalence auditor checks.
PRESERVING: frozenset[str] = frozenset(
    {"identical", "refinement", "modeled", "axiom", "unchanged", "unbridged"}
)

#: The checker outcome each rival kind has to get; a case that gets the other is the
#: finding `RivalKind` names for it.
RIVAL_EXPECTATION: dict[str, str] = {
    "uniqueness": "refute",
    "soundness": "verify",
    "admissibility": "verify",
}


def task_directory(bundle_root: Path, task: Task) -> Path:
    """Where a task's frozen inputs live, shared by every backend."""
    return Path(bundle_root) / task.benchmark / task.slug


def freeze_task(bundle_root: Path, task: Task, *, refresh: bool = False) -> Path:
    """Write a task's inputs once, leaving a task already on disk alone.

    A later ingestion cannot swap the inputs under a judged bundle. ``refresh``
    (``benchproofer ingest --refresh``) overwrites them, and bundles built from the old
    inputs then fail ``artifact.integrity``.
    """
    directory = task_directory(bundle_root, task)
    directory.mkdir(parents=True, exist_ok=True)
    frozen = directory / "task.json"
    if refresh or not frozen.exists():
        write_json(frozen, task.model_dump(mode="json"))
    reference = directory / "reference.patch"
    if task.reference.patch and (refresh or not reference.exists()):
        write_text(reference, task.reference.patch)
    return directory


class Rival(BaseModel):
    """One case of the property-based test suite.

    `witness` is a claim, proved at one concrete input, that the rival violates the
    specification. A reject case needs one under a backend with `witness_required`, where a
    rejection alone attributes nothing (`core.witness`).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    kind: RivalKind
    expect: Literal["verify", "refute"]
    file: str
    rationale: str
    witness: str = ""
    #: What a proof session on this case reported, empty where none ran. It tells a refused
    #: case nobody tried to prove (a defect of the case) from one a session failed to prove
    #: (a gap in the evidence), which the file cannot say.
    proof_session: str = ""
    #: What the checker said of this case against what it expected -- `refute`,
    #: `verify: unproved` -- so a reader of the index can tell a case that behaved from one
    #: that did not. `expect` alone reads the same either way.
    found: str = ""
    #: The digest of the file this record was written about (`digest_text`). A session that
    #: edits the case's file does not rewrite the rationale, so this is what says whether
    #: the rationale still describes what the bundle ships.
    digest: str = ""

    @model_validator(mode="after")
    def _coherent(self) -> Rival:
        expected = RIVAL_EXPECTATION[self.kind]
        if self.expect != expected:
            raise ValueError(f"kind {self.kind!r} requires expect={expected!r}")
        return self


class Twin(BaseModel):
    """What the bundle records about one pre-fix implementation besides its file.

    `witness` and `proof_session` are what they are on a reject case of the property-based test
    suite (`Rival`): the claim that the code before the fix violates the specification, and what
    a proof session on it reported.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    file: str
    rationale: str = ""
    witness: str = ""
    proof_session: str = ""
    #: As on `Rival`: what the checker said of this pre-fix implementation against the refusal
    #: expected of it, and the digest of the file the rationale was written about.
    found: str = ""
    digest: str = ""


#: A case of the property-based test suite or a pre-fix implementation, for the helpers that
#: treat the two records alike.
_Case = TypeVar("_Case", Rival, Twin)


class Submission(BaseModel):
    """One implementation a review submits to test the specification's reach.

    `file` is a complete solution file with the shipped specification unchanged, for the
    checker. `shadow`, for an implementation that cannot run as written, is the same change
    as a repository patch, for the benchmark's tests. A specification is too weak when it
    accepts what the oracle rejects and too strong when it refutes what the oracle accepts,
    so neither finding comes from the checker alone.

    `test` names a witness test, a Python program run where the benchmark's tests run: an
    attack's has to pass on the fixed code and fail with its equivalent patch in place of the
    golden patch, and `cites` says what of the statement or the tests it checks, which the
    attack validation auditor rules on; a control's has to pass on the fixed code where it
    returns what the control returns at the input of its `refutation`, a claim proved at that
    input that the specification refuses the control's result there.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    file: str
    kind: SubmissionKind = "weakness"
    shadow: str = ""
    claim: str = ""
    test: str = ""
    cites: str = ""
    refutation: str = ""

    @model_validator(mode="before")
    @classmethod
    def _unread(cls, data: Any) -> Any:
        """Drop what a record may carry that nothing reads (`_UNREAD_SUBMISSION`)."""
        return _without(data, _UNREAD_SUBMISSION)


#: Keys a submission's record may carry beside its files that nothing reads: what a proof
#: session on a control the prover refused reported, the refutation witness it wrote, and
#: the specification the submission was filed against.
_UNREAD_SUBMISSION = frozenset({"proof_session", "witness", "against"})


def _without(data: Any, keys: frozenset[str]) -> Any:
    """A record as read, without ``keys``, which an older record may carry and nothing reads."""
    if isinstance(data, dict):
        return {key: value for key, value in data.items() if key not in keys}
    return data


#: What the attack validation auditor may rule of an attack or a control that cannot be
#: determined by execution, by the kind of submission it is about: of an attack, whether it
#: succeeds; of a control, whether it is correct and the specification refuses it
#: (`too_strong`), correct and refused because the checker rejected a step of its own proof
#: (`unproved`), or not correct (`incorrect`).
RULINGS: dict[SubmissionKind, tuple[str, ...]] = {
    "weakness": ("succeeds", "fails"),
    "control": ("too_strong", "unproved", "incorrect"),
}


class Ruling(BaseModel):
    """The attack validation auditor's ruling on one submission execution cannot determine.

    `reads` makes it expire, as `Judgment.reads` does: the digests of the specification, the
    implementation, the submission's files and what its witness test cites when it was reached
    (`core.readings.ruling_reads`). It counts only while those are still what the submission
    reads, and only when it names the input and the sentence of the statement, the test or the
    obligation it rests on (`named`). `asked` is how many times the auditor was shown the
    submission with those files as they are, so that one it was asked about again and still
    left without a ruling counts neither way.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    #: The submission it is about.
    id: str
    #: One of `RULINGS` for the submission's kind, "" where the auditor gave none.
    ruling: str = ""
    #: The input the ruling rests on.
    input: str = ""
    #: The sentence of the statement, the test or the obligation it rests on.
    rests_on: str = ""
    why: str = ""
    asked: int = 1
    reads: dict[str, str] = Field(default_factory=dict)

    @property
    def named(self) -> bool:
        """True when it names both the input and what of the task it rests on."""
        return bool(self.input.strip() and self.rests_on.strip())


#: Keys a fuzzer's record may carry beside its program that nothing reads: whether the
#: golden patch changes the callee, and why.
_UNREAD = frozenset({"changed", "how"})


class Defect(BaseModel):
    """A defect a reviewer showed by running code, which no implementation it filed shows.

    An input the specification admits on which it promises what the repository does not do.
    The attack auditor files one beside its attacks, with the input as `conformance.py` takes
    it, and the input is put to `conformance.py` with the others on record (`core.replay`), so a
    disagreement there fails `impl.conformance`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    #: What is wrong, in one sentence.
    defect: str
    #: The function `conformance.py` compares the input on, by the name it reports.
    function: str = ""
    #: The input: the arguments that function is called with, as a Python tuple literal.
    input: str = ""
    #: What the repository does on that input, as the reviewer ran it.
    repository: str = ""
    #: What the specification states on it.
    specification: str = ""


class Fuzzer(BaseModel):
    """One program a review wrote to attack an unchanged callee, run by `audit.axiom_soundness`.

    The reviewer's counterpart to the bundle's `axioms.py`, which tends to exercise only
    what its author's assumption already covers.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    #: Audit-relative filename of the program, which is Python.
    file: str
    #: The unchanged callee this program attacks, as the `axioms` region names it.
    callee: str = ""
    claim: str = ""
    #: A digest of the `axioms` region the program was written against. A later review
    #: keeps the program only while that region is unchanged.
    against: str = ""

    @model_validator(mode="before")
    @classmethod
    def _unread(cls, data: Any) -> Any:
        """Drop the keys a fuzzer's record may have that nothing reads (`_UNREAD`)."""
        return _without(data, _UNREAD)


class Operation(BaseModel):
    """One operation of the implementation, set against the golden patch's own.

    Labelled with the kind of rewriting relating the two. An unlabelled or unrecognized
    correspondence is recorded as `changed`, since it has not been shown to preserve
    anything.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: OperationKind
    detail: str


class Coverage(BaseModel):
    """One behavior of a function the fix changes, and the obligation covering it, if one does.

    The faithfulness review lists one per behavior, so that coverage is a table a reader
    can check, and a repair is shown the rows naming a test that no obligation states. The
    verdict is the reviewer's: the table is what it was reached from.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    #: What the fixed code does, for which inputs.
    behavior: str
    #: The benchmark's test that checks it, empty when none does.
    tested_by: str = ""
    #: The obligation that states it, quoted, empty when none does.
    covered_by: str = ""
    note: str = ""

    @model_validator(mode="before")
    @classmethod
    def _unread(cls, data: Any) -> Any:
        """Drop the `kind` a record may carry, which nothing reads.

        It said what the fix does to the behavior; a row with a test needs an obligation
        whatever the fix does there.
        """
        return _without(data, frozenset({"kind"}))

    @property
    def uncovered(self) -> bool:
        """True when no obligation states this behavior."""
        return not self.covered_by.strip()

    @property
    def required(self) -> bool:
        """True when the benchmark's tests check this behavior."""
        return bool(self.tested_by.strip())


class Judgment(BaseModel):
    """One review role's conclusion, with the artifacts it was reached from.

    `reads` makes a judgment expire: the gate that reports it compares these digests with
    the bundle on disk and declines to speak when they differ. Kept per role, so a repair
    expires only the judgments it could have affected.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: AuditRole
    verdict: Literal["sound", "unsound", "uncertain"]
    summary: str = ""
    findings: tuple[str, ...] = ()
    #: What the role checked and found clean, each with what it ran. Apart from `findings`,
    #: which a repair is handed and the role's next session carries.
    checked: tuple[str, ...] = ()
    #: How the implementation's operations correspond to the golden patch's, filled in by
    #: the `equivalence` role. Apart from `findings` because they are what the verdict rests
    #: on, listed in the gate's details, rather than defects to hand to a repair.
    operations: tuple[Operation, ...] = ()
    #: What the fix changes, set against the obligations that cover it, filled in by the
    #: `faithfulness` role.
    coverage: tuple[Coverage, ...] = ()
    reads: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _unread(cls, data: Any) -> Any:
        """Drop `attacks`, a key an older review record carries that nothing reads."""
        return _without(data, frozenset({"attacks"}))

    def stale(self, digests: dict[str, str]) -> list[str]:
        """Which files this judgment was reached from no longer match it.

        A judgment that recorded nothing it read is vacuously current; the gate tells that
        apart from one known to apply.
        """
        return sorted(
            name for name, digest in self.reads.items() if digests.get(name) != digest
        )


class Review(BaseModel):
    """One adversarial review of one bundle: evidence, not a verdict.

    The gates re-run its submissions and check its judgments are current, so a review that
    calls a bundle sound certifies nothing on its own.
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = SCHEMA_VERSION
    #: Provider and model that authored the review.
    reviewer: str = ""
    #: Provider and model that drafted the bundle, copied from its `manifest.json`.
    author: str = ""
    #: True when the review was authored with no access to the drafting transcript;
    #: otherwise it is reported as self-review.
    independent: bool = False
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    submissions: tuple[Submission, ...] = ()
    #: What the attack auditor showed by running code that is not an attack, each input put to
    #: `conformance.py` with the others on record; replaced when the attack auditor is asked
    #: again about a changed specification, as its submissions are.
    defects: tuple[Defect, ...] = ()
    fuzzers: tuple[Fuzzer, ...] = ()
    #: The attack validation auditor's rulings on the submissions execution cannot determine.
    rulings: tuple[Ruling, ...] = ()
    judgments: tuple[Judgment, ...] = ()
    #: What each auditor that files programs rather than a judgment (`attack`, `fuzz`) read
    #: when it last ran, as `Judgment.reads` does. The auditor runs again when one changes;
    #: until then the gates re-run what it filed.
    examined: dict[str, dict[str, str]] = Field(default_factory=dict)

    def judgment(self, role: AuditRole) -> Judgment | None:
        """The judgment filed for one role, if the review filed one."""
        return next((entry for entry in self.judgments if entry.role == role), None)

    def ruling(self, submission: str) -> Ruling | None:
        """The attack validation auditor's ruling on one submission, if it filed one."""
        return next((entry for entry in self.rulings if entry.id == submission), None)


class Manifest(BaseModel):
    """The bundle's `manifest.json`: what was built, from what, and how it was judged."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = SCHEMA_VERSION
    benchmark: str
    task_id: str
    backend: str
    tool_version: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    task_digest: str = ""
    artifacts: dict[str, str] = Field(default_factory=dict)
    regions: dict[str, str] = Field(default_factory=dict)
    verdicts: dict[str, Verdict] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    notes: dict[str, Any] = Field(default_factory=dict)


class Bundle:
    """Filesystem access to one bundle.

    It holds nothing but paths, so every read goes to disk and another process's writes
    are never served stale.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    # ---- construction ---------------------------------------------------

    @classmethod
    def locate(cls, bundle_root: Path, task: Task, backend: str) -> Bundle:
        """Return the bundle path for a task and backend, without creating it."""
        return cls(task_directory(bundle_root, task) / backend)

    @classmethod
    def create(cls, bundle_root: Path, task: Task, backend: str) -> Bundle:
        """Create the directory layout and freeze the task and its reference."""
        freeze_task(bundle_root, task)
        bundle = cls.locate(bundle_root, task, backend)
        bundle.root.mkdir(parents=True, exist_ok=True)
        bundle.evidence_dir.mkdir(exist_ok=True)
        return bundle

    # ---- paths ----------------------------------------------------------

    @property
    def task_dir(self) -> Path:
        """The per-task directory holding frozen inputs shared by all backends."""
        return self.root.parent

    @property
    def backend_name(self) -> str:
        """The backend this bundle was built with, taken from the path."""
        return self.root.name

    @property
    def task_path(self) -> Path:
        """Path of the frozen normalized task."""
        return self.task_dir / "task.json"

    @property
    def reference_path(self) -> Path:
        """Path of the frozen reference patch."""
        return self.task_dir / "reference.patch"

    @property
    def manifest_path(self) -> Path:
        """Path of `manifest.json`."""
        return self.root / "manifest.json"

    @property
    def twins_dir(self) -> Path:
        """Directory holding pre-fix implementations."""
        return self.root / "twins"

    @property
    def rivals_dir(self) -> Path:
        """Directory holding the property-based test suite."""
        return self.root / "rivals"

    @property
    def audit_dir(self) -> Path:
        """Directory holding the adversarial review and the files it submitted."""
        return self.root / "audit"

    @property
    def evidence_dir(self) -> Path:
        """Directory gates write supporting artifacts into."""
        return self.root / "evidence"

    @property
    def correspondence_path(self) -> Path:
        """Path of the correspondence document."""
        return self.root / "correspondence.md"

    @property
    def axioms_path(self) -> Path:
        """Path of `axioms.py`, which grounds what the specification assumes."""
        return self.root / AXIOM_HARNESS

    @property
    def conformance_path(self) -> Path:
        """Path of `conformance.py`, which the conformance gate runs."""
        return self.root / DIFFERENTIAL_HARNESS

    @property
    def notes_path(self) -> Path:
        """Path of the reviewer-facing notes."""
        return self.root / "notes.md"

    @property
    def solution_path(self) -> Path:
        """Path of the solution file, whose extension the backend chooses."""
        matches = sorted(self.root.glob("solution.*"))
        if not matches:
            raise BundleError(f"no solution file in {self.root}")
        if len(matches) > 1:
            raise BundleError(f"multiple solution files in {self.root}: {matches}")
        return matches[0]

    @property
    def exists(self) -> bool:
        """True when the bundle directory is present."""
        return self.root.is_dir()

    def scratch(self, cache_dir: Path, *parts: str) -> Path:
        """A working directory this bundle alone owns, created on demand.

        Keyed by a digest of the bundle's location as well as its readable tail, since two
        bundle roots can hold the same benchmark, task and backend, and checkers name files
        after a bundle's contents. Outside the bundle, so nothing a checker leaves is taken
        for an artifact, and kept after the run, so a toolchain's cache persists.
        """
        located = self.root.resolve()
        label = "-".join(part for part in located.parts[-3:] if part not in ("", "/"))
        keyed = f"{label or 'bundle'}-{short(digest_text(located.as_posix()), 8)}"
        path = Path(cache_dir).joinpath("scratch", keyed, *parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ---- reads ----------------------------------------------------------

    def task(self) -> Task:
        """Load the frozen task."""
        if not self.task_path.exists():
            raise BundleError(f"missing {self.task_path}")
        return Task.model_validate(read_json(self.task_path))

    def solution(self) -> str:
        """Read the solution file."""
        return read_text(self.solution_path)

    def twins(self) -> list[tuple[str, str]]:
        """Read every pre-fix implementation as ``(name, source)``, sorted by name.

        Every file of the directory is a pre-fix implementation except its index (`twin_cases`).
        """
        if not self.twins_dir.is_dir():
            return []
        return [
            (path.stem, read_text(path))
            for path in sorted(self.twins_dir.iterdir())
            if path.is_file() and path != self.twins_index
        ]

    @property
    def twins_index(self) -> Path:
        """What the bundle records about its pre-fix implementations besides their files."""
        return self.twins_dir / "index.toml"

    def twin_cases(self, *, as_written: bool = False) -> dict[str, Twin]:
        """What the bundle records about each pre-fix implementation it ships, by name.

        A pre-fix implementation the index does not list is recorded as its file alone, and an
        entry naming no file there is ignored. A malformed index raises rather than reading as
        pre-fix implementations with no witness. A rationale the file beside it no longer bears
        is replaced (`_about`), unless ``as_written`` asks for the index as it reads.
        """
        recorded: dict[str, Twin] = {}
        if self.twins_index.exists():
            data = load_toml(self.twins_index)
            rows = data.get("twin", [])
            if not isinstance(rows, list):
                raise BundleError(f"{self.twins_index}: 'twin' must be an array of tables")
            try:
                recorded = {
                    entry.file: entry for entry in (Twin.model_validate(row) for row in rows)
                }
            except Exception as exc:
                raise BundleError(f"{self.twins_index}: {exc}") from exc
        found: dict[str, Twin] = {}
        for path in sorted(self.twins_dir.iterdir()) if self.twins_dir.is_dir() else ():
            if path.is_file() and path != self.twins_index:
                entry = recorded.get(path.name) or Twin(id=path.stem, file=path.name)
                found[path.stem] = entry if as_written else _about(entry, _read(path))
        return found

    def battery(self, *, as_written: bool = False) -> list[Rival]:
        """Parse `rivals/index.toml`, or [] when the bundle ships none.

        A malformed manifest raises rather than reading as a property-based test suite with no
        cases. A rationale the case's file no longer bears is replaced (`_about`), unless
        ``as_written`` asks for the index as it reads.
        """
        index = self.rivals_dir / "index.toml"
        if not index.exists():
            return []
        data = load_toml(index)
        rows = data.get("rival", [])
        if not isinstance(rows, list):
            raise BundleError(f"{index}: 'rival' must be an array of tables")
        try:
            cases = [Rival.model_validate(row) for row in rows]
        except Exception as exc:
            raise BundleError(f"{index}: {exc}") from exc
        if as_written:
            return cases
        return [_about(case, _read(self.rivals_dir / case.file)) for case in cases]

    def rival_source(self, rival: Rival) -> str:
        """Read one rival's source."""
        path = self.rivals_dir / rival.file
        if not path.exists():
            raise BundleError(f"rival {rival.id!r} names a missing file: {path}")
        return read_text(path)

    def audit(self) -> Review | None:
        """Parse the recorded review, or None when the bundle ships none.

        A malformed review raises rather than reading as a bundle nobody has audited.
        """
        index = self.audit_dir / "index.toml"
        if not index.exists():
            return None
        try:
            return Review.model_validate(load_toml(index))
        except Exception as exc:
            raise BundleError(f"{index}: {exc}") from exc

    def submission_source(self, submission: Submission) -> str:
        """Read one submitted implementation's source."""
        path = self.audit_dir / submission.file
        if not path.exists():
            raise BundleError(f"submission {submission.id!r} names a missing file: {path}")
        return read_text(path)

    def submission_shadow(self, submission: Submission) -> str | None:
        """Read one submission's executable form, or None when it ships none."""
        if not submission.shadow:
            return None
        path = self.audit_dir / submission.shadow
        if not path.exists():
            raise BundleError(
                f"submission {submission.id!r} names a missing equivalent patch: {path}"
            )
        return read_text(path)

    def submission_test(self, submission: Submission) -> str | None:
        """Read one submission's witness test, or None when it ships none."""
        if not submission.test:
            return None
        path = self.audit_dir / submission.test
        if not path.exists():
            raise BundleError(
                f"submission {submission.id!r} names a missing witness test: {path}"
            )
        return read_text(path)

    def fuzzer_source(self, fuzzer: Fuzzer) -> str:
        """Read one reviewer-written fuzzer's program."""
        path = self.audit_dir / fuzzer.file
        if not path.exists():
            raise BundleError(f"fuzzer {fuzzer.id!r} names a missing file: {path}")
        return read_text(path)

    def axioms(self) -> str | None:
        """Read `axioms.py`, which grounds the specification's assumptions, if shipped."""
        if not self.axioms_path.is_file():
            return None
        return read_text(self.axioms_path)

    def conformance(self) -> str | None:
        """Read `conformance.py`, which compares the implementation with the code, if any."""
        if not self.conformance_path.is_file():
            return None
        return read_text(self.conformance_path)

    def manifest(self) -> Manifest:
        """Load `manifest.json`, or build an empty one from the frozen task."""
        if self.manifest_path.exists():
            return Manifest.model_validate(read_json(self.manifest_path))
        task = self.task()
        return Manifest(
            benchmark=task.benchmark,
            task_id=task.task_id,
            backend=self.backend_name,
            task_digest=task.digest(),
        )

    # ---- writes ---------------------------------------------------------

    def save_manifest(self, manifest: Manifest) -> None:
        """Persist `manifest.json` atomically."""
        manifest.updated_at = datetime.now(timezone.utc)
        write_json(self.manifest_path, manifest.model_dump(mode="json"))

    def record(self, verdicts: list[Verdict]) -> Manifest:
        """Merge verdicts into `manifest.json`, preserving unrelated records."""
        manifest = self.manifest()
        for verdict in verdicts:
            manifest.verdicts[verdict.gate] = verdict
        manifest.artifacts = self.artifact_digests()
        self.save_manifest(manifest)
        return manifest

    def save_battery(self, cases: list[tuple[Rival, str]]) -> None:
        """Write one file per rival, then the manifest, so the suite is complete or absent."""
        self.rivals_dir.mkdir(parents=True, exist_ok=True)
        # A case whose file a session rewrote keeps neither the rationale nor the outcome
        # recorded about the file before it (`_about`).
        cases = [(_about(rival, source), source) for rival, source in cases]
        for rival, source in cases:
            write_text(self.rivals_dir / rival.file, source)
        tables = "\n".join(
            "[[rival]]\n"
            f"id = {_toml_string(rival.id)}\n"
            f"kind = {_toml_string(rival.kind)}\n"
            f"expect = {_toml_string(rival.expect)}\n"
            f"file = {_toml_string(rival.file)}\n"
            f"rationale = {_toml_string(rival.rationale)}\n" + _toml_proof_record(rival, source)
            for rival, source in cases
        )
        write_text(
            self.rivals_dir / "index.toml",
            "# The property-based test suite. Each case states the verdict the specification\n"
            "# has to reach; a case that behaves otherwise is a finding, not an error.\n\n"
            f"{tables}",
        )

    def save_twins(self, cases: list[tuple[Twin, str]]) -> None:
        """Replace the bundle's pre-fix implementations with ``cases``.

        The index is written only when a pre-fix implementation carries a witness or a proof
        session's record.
        """
        if self.twins_dir.is_dir():
            for path in self.twins_dir.iterdir():
                if path.is_file():
                    path.unlink()
        if not cases:
            return
        self.twins_dir.mkdir(parents=True, exist_ok=True)
        cases = [(_about(twin, source), source) for twin, source in cases]
        for twin, source in cases:
            write_text(self.twins_dir / twin.file, source)
        if not any(twin.witness.strip() or twin.proof_session.strip() for twin, _ in cases):
            return
        tables = "\n".join(
            "[[twin]]\n"
            f"id = {_toml_string(twin.id)}\n"
            f"file = {_toml_string(twin.file)}\n"
            f"rationale = {_toml_string(twin.rationale)}\n" + _toml_proof_record(twin, source)
            for twin, source in cases
        )
        write_text(
            self.twins_index,
            "# The pre-fix implementations: the code before the fix, written in the\n"
            "# specification's language. Each is the solution file with the code before the\n"
            "# fix in place of the fixed code, and the specification has to reject it;\n"
            "# `witness` is the claim that shows the specification rejects it under a checker\n"
            "# that replays the proof a file writes.\n\n"
            f"{tables}",
        )

    def save_audit(self, review: Review, sources: dict[str, str]) -> None:
        """Write a review: one file per submission, plus the index that describes them.

        The index is written last, so a review is complete or absent.

        Args:
            review: The review to record.
            sources: Audit-relative filename to contents, for every submission and
                fuzzer the review names.
        """
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        for name, text in sources.items():
            write_text(self.audit_dir / name, text)
        write_text(self.audit_dir / "index.toml", _render_review(review))

    def describes(self, verdict: Verdict) -> bool:
        """Whether every file ``verdict`` recorded reading still has the digest it recorded.

        A verdict names its inputs relative to the task directory (`Gate.run`), so one
        about a file since removed no longer describes the bundle either.
        """
        return all(
            (path := self.task_dir / name).is_file() and digest_file(path) == digest
            for name, digest in verdict.inputs.items()
        )

    def artifact_digests(self) -> dict[str, str]:
        """Digest every artifact in the bundle except `manifest.json` itself."""
        digests: dict[str, str] = {}
        for path in artifact_files(self.root):
            if path == self.manifest_path:
                continue
            digests[path.relative_to(self.root).as_posix()] = digest_file(path)
        for path in (self.task_path, self.reference_path):
            if path.exists():
                digests[f"../{path.name}"] = digest_file(path)
        return digests

    def write_evidence(self, name: str, text: str) -> str:
        """Write a gate's supporting artifact and return its bundle-relative path."""
        target = self.evidence_dir / name
        write_text(target, text)
        return target.relative_to(self.root).as_posix()

    def __repr__(self) -> str:
        return f"Bundle({self.root!s})"


def _render_review(review: Review) -> str:
    """Serialize a review as the TOML a person can also write by hand."""
    lines = [
        "# An independent adversarial review of this bundle. Nothing here is a verdict:",
        "# the implementations it submitted are re-run through the checker and the",
        "# benchmark's tests, and a judgment or a ruling counts toward a gate's result only",
        "# while the digests under its reads still match.",
        "",
        f"schema_version = {review.schema_version}",
        f"reviewer = {_toml_string(review.reviewer)}",
        f"author = {_toml_string(review.author)}",
        f"independent = {str(review.independent).lower()}",
        f"reviewed_at = {_toml_string(review.reviewed_at.isoformat())}",
        "",
    ]
    for submission in review.submissions:
        lines += [
            "[[submissions]]",
            f"id = {_toml_string(submission.id)}",
            f"kind = {_toml_string(submission.kind)}",
            f"file = {_toml_string(submission.file)}",
            f"shadow = {_toml_string(submission.shadow)}",
            f"claim = {_toml_string(submission.claim)}",
            *([f"test = {_toml_string(submission.test)}"] if submission.test else []),
            *([f"cites = {_toml_string(submission.cites)}"] if submission.cites else []),
            *(
                [f"refutation = {_toml_block(submission.refutation)}"]
                if submission.refutation.strip()
                else []
            ),
            "",
        ]
    for defect in review.defects:
        lines += [
            "[[defects]]",
            f"defect = {_toml_string(defect.defect)}",
            f"function = {_toml_string(defect.function)}",
            f"input = {_toml_string(defect.input)}",
            f"repository = {_toml_string(defect.repository)}",
            f"specification = {_toml_string(defect.specification)}",
            "",
        ]
    for fuzzer in review.fuzzers:
        lines += [
            "[[fuzzers]]",
            f"id = {_toml_string(fuzzer.id)}",
            f"file = {_toml_string(fuzzer.file)}",
            f"callee = {_toml_string(fuzzer.callee)}",
            f"claim = {_toml_string(fuzzer.claim)}",
            *([f"against = {_toml_string(fuzzer.against)}"] if fuzzer.against else []),
            "",
        ]
    for ruling in review.rulings:
        lines += [
            "[[rulings]]",
            f"id = {_toml_string(ruling.id)}",
            f"ruling = {_toml_string(ruling.ruling)}",
            f"input = {_toml_string(ruling.input)}",
            f"rests_on = {_toml_string(ruling.rests_on)}",
            f"why = {_toml_string(ruling.why)}",
            f"asked = {ruling.asked}",
            "",
            "[rulings.reads]",
            *(
                f"{_toml_string(name)} = {_toml_string(digest)}"
                for name, digest in ruling.reads.items()
            ),
            "",
        ]
    for judgment in review.judgments:
        lines += [
            "[[judgments]]",
            f"role = {_toml_string(judgment.role)}",
            f"verdict = {_toml_string(judgment.verdict)}",
            f"summary = {_toml_string(judgment.summary)}",
            f"findings = {_toml_array(judgment.findings)}",
            *([f"checked = {_toml_array(judgment.checked)}"] if judgment.checked else []),
            "",
        ]
        for operation in judgment.operations:
            lines += [
                "[[judgments.operations]]",
                f"kind = {_toml_string(operation.kind)}",
                f"detail = {_toml_string(operation.detail)}",
                "",
            ]
        for row in judgment.coverage:
            lines += [
                "[[judgments.coverage]]",
                f"behavior = {_toml_string(row.behavior)}",
                f"tested_by = {_toml_string(row.tested_by)}",
                f"covered_by = {_toml_string(row.covered_by)}",
                f"note = {_toml_string(row.note)}",
                "",
            ]
        lines += [
            "[judgments.reads]",
            *(
                f"{_toml_string(name)} = {_toml_string(digest)}"
                for name, digest in judgment.reads.items()
            ),
            "",
        ]
    for lane, reads in review.examined.items():
        lines += [
            f"[examined.{lane}]",
            *(
                f"{_toml_string(name)} = {_toml_string(digest)}"
                for name, digest in reads.items()
            ),
            "",
        ]
    return "\n".join(lines)


def _toml_array(values: tuple[str, ...] | list[str]) -> str:
    """Render a list of strings as a TOML array, one element per line when long."""
    if not values:
        return "[]"
    items = [_toml_string(value) for value in values]
    if sum(len(item) for item in items) <= 70:
        return "[" + ", ".join(items) + "]"
    return "[\n" + "".join(f"    {item},\n" for item in items) + "]"


def _toml_string(value: str) -> str:
    """Quote a value as a TOML basic string."""
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "")
    )
    return f'"{escaped}"'


def _toml_proof_record(case: Rival | Twin, source: str) -> str:
    """The lines of a `rivals/index.toml` or `twins/index.toml` table on how the case fared.

    `digest` is taken from the file being written rather than from the record, so it always
    names what the index sits beside, and `_about` can say whether a later edit left the
    rationale describing something else.
    """
    return (
        (f"witness = {_toml_block(case.witness)}\n" if case.witness.strip() else "")
        + (
            f"proof_session = {_toml_string(case.proof_session)}\n"
            if case.proof_session.strip()
            else ""
        )
        + (f"found = {_toml_string(case.found)}\n" if case.found.strip() else "")
        + f"digest = {_toml_string(digest_text(source))}\n"
    )


#: What a record says in place of a rationale written about a file that has since changed.
REWRITTEN = (
    "the case's file was rewritten after this rationale was recorded, so what it said is "
    "not about the case the bundle ships"
)


def _about(case: _Case, source: str | None) -> _Case:
    """``case`` with a rationale the source it is beside no longer bears replaced.

    A rationale says which mistake the case's file makes, and a session that edits the file
    may not rewrite it; what it found is about that file too. Read as describing the file, a
    stale rationale sends a reviewer and a repair after a mistake nothing in the bundle
    makes, so the digest the record was written against is what decides whether it still
    speaks. A record with no digest predates this and is left alone, since nothing says it is
    stale either. A repair that rewrote the rationale with the file is read before this
    (`pipeline.repair`), and the digest is taken again when the case is written.
    """
    if not case.digest or source is None:
        return case
    if case.digest == digest_text(source):
        return case
    return case.model_copy(update={"rationale": REWRITTEN, "found": ""})


def _read(path: Path) -> str | None:
    """The file at ``path``, or None where there is none to compare a record against."""
    return read_text(path) if path.is_file() else None


def _toml_block(value: str) -> str:
    """Quote a value that is source code, as a TOML multi-line literal string.

    Multi-line so a person can read it, and literal so its backslashes round-trip. Text a
    literal string cannot hold, containing `'''` or ending in `'`, falls back to the
    escaped basic string.
    """
    body = value.strip("\n").replace("\r", "")
    if "'''" in body or body.endswith("'"):
        return _toml_string(value)
    return f"'''\n{body}\n'''"
