"""The fixture corpus that ships with the tool.

Four tasks and four bundles, packaged as data. They exist so that the parts of the
pipeline that do not depend on the network can be exercised anywhere, including in
continuous integration and on a machine that has no verifier toolchain installed:
the bundles are written for the ``falsifier`` backend, which needs nothing but the
Python environment the tool already requires.

Each bundle declares the classification it must reach, in its own ``fixture.toml``,
next to the artifacts::

    [expect]
    static = "rejected"

    [unfavorable]
    static = ["spec.no_leakage"]

so a case compares the adjudication against a claim recorded beside the files rather
than against a literal buried in the suite, and against the gate that has to object
rather than only the verdict it produces. No bundle ships a ``manifest.json``: the
`manifest.json` is written by the run that judges it, so a fixture cannot carry a verdict
nobody recomputed.

A bundle may also declare what a reviewer shown its artifacts concludes::

    [review.faithfulness]
    verdict = "unsound"
    findings = ["nothing in it requires the fewest coins"]

which is the one part of a review no program can derive. The implementations a review submits
are not declared: they are the bundle's own property-based test suite, so a scripted review
attacks with code the fixture already ships and the gates re-run it.

A bundle whose specification assumes a callee also declares the program a reviewer
writes against that assumption::

    [[fuzzer]]
    callee = "posixpath.normpath"
    program = '''...'''

which is the one thing a review contributes that the bundle does not already ship: the
bundle's own `axioms.py` for an assumption was written by whoever wrote the assumption.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from functools import cache
from importlib.resources import files
from pathlib import Path

from ...config import Settings
from ...core.bundle import Bundle
from ...core.task import Task
from ...core.verdict import Level, Outcome
from ...errors import BenchproofError
from ...pipeline.ingest import ingest
from ...util.fsio import BYPRODUCTS, artifact_files, load_toml

__all__ = [
    "BENCHMARK",
    "REQUIRES",
    "Attack",
    "Fixture",
    "Judged",
    "coexisting",
    "fixture",
    "fixtures",
    "root",
    "stage",
    "tasks",
    "tasks_file",
]

_PACKAGE = "benchproofer.smoke.fixtures"
#: The benchmark name the fixture tasks are ingested under.
BENCHMARK = "demo"
#: What judging a fixture bundle needs, as a smoke case's requirements: the tasks are
#: read by the jsonl adapter and judged by inline tests, and every bundle is written for
#: the falsifier backend.
REQUIRES = ("benchmark:jsonl", "backend:falsifier", "oracle:inline-tests")


@cache
def root() -> Path:
    """The directory holding the packaged fixtures.

    Raises:
        BenchproofError: The fixtures are not readable as ordinary files, which
            happens only if the package was installed as a zip archive.
    """
    path = Path(str(files(_PACKAGE)))
    if not path.is_dir():
        raise BenchproofError(
            f"the smoke fixtures are not available at {path}; install benchproofer "
            "from a directory rather than a zip archive"
        )
    return path


def tasks_file() -> Path:
    """Path of the JSON Lines file holding the fixture tasks."""
    return root() / "tasks.jsonl"


def tasks(settings: Settings) -> dict[str, Task]:
    """Ingest the fixture tasks under a bundle root, keyed by task id.

    Uses the ``jsonl`` adapter, so the path a fixture case takes through ingestion
    is the same one a user's own benchmark takes.
    """
    ingestion = ingest(
        "jsonl",
        settings,
        extras={"source": str(tasks_file()), "name": BENCHMARK},
    )
    return {task.task_id: task for task in ingestion.tasks}


@dataclass(frozen=True, slots=True)
class Judged:
    """What a reviewer shown a fixture's artifacts concludes about one question.

    The verdict, the findings and the correspondences are strings rather than the
    tool's own enumerations on purpose: a fixture is data, so it can declare a
    correspondence of a kind the tool does not recognize and let the gate that reads
    it be the one to complain.
    """

    role: str
    verdict: str
    summary: str
    findings: tuple[str, ...] = ()
    #: One ``(kind, detail)`` pair per correspondence, for an equivalence judgment.
    operations: tuple[tuple[str, str], ...] = ()
    #: One ``(behavior, tested_by, covered_by)`` row per behavior, for a faithfulness
    #: judgment.
    coverage: tuple[tuple[str, str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Attack:
    """A program an independent reviewer runs against a callee the specification assumes.

    Declared rather than shipped as a file: a fuzzer is not one of the bundle's own
    artifacts, it is what a review adds to it, and writing it into the bundle directory
    would make the fixture look like a bundle that had already been reviewed.
    """

    id: str
    callee: str
    claim: str
    program: str


@dataclass(frozen=True, slots=True)
class Fixture:
    """One fixture bundle and the classification it declares."""

    name: str
    task_id: str
    backend: str
    summary: str
    directory: Path
    #: Declared outcome per evidence level, keyed by the level's name.
    expectations: dict[str, str]
    #: Gates that must reach an unfavorable judgment, per evidence level.
    unfavorable: dict[str, tuple[str, ...]] = field(default_factory=dict)
    #: What a reviewer concludes about each question, keyed by the judgment's role.
    review: dict[str, Judged] = field(default_factory=dict)
    #: One program per unchanged callee a reviewer attacks, in the order they are asked for.
    fuzzers: tuple[Attack, ...] = ()

    def judgment(self, role: str) -> Judged:
        """What a reviewer concludes about one question.

        Raises:
            BenchproofError: The fixture declares nothing about that question, so a
                review of this bundle cannot be scripted.
        """
        found = self.review.get(role)
        if found is None:
            declared = ", ".join(sorted(self.review)) or "none"
            raise BenchproofError(
                f"fixture {self.name!r} declares no {role!r} judgment; declared: {declared}"
            )
        return found

    def expected(self, level: Level) -> Outcome:
        """The outcome this bundle must reach at one evidence level.

        Raises:
            BenchproofError: The fixture declares no outcome for that level, so
                there is nothing to compare an adjudication against.
        """
        declared = self.expectations.get(str(level))
        if declared is None:
            raise BenchproofError(
                f"fixture {self.name!r} declares no expected outcome for level={level}"
            )
        try:
            return Outcome(declared)
        except ValueError as exc:
            raise BenchproofError(
                f"fixture {self.name!r} declares outcome {declared!r} at level={level}, "
                f"which is not one of {', '.join(str(item) for item in Outcome)}"
            ) from exc

    def unfavorable_at(self, level: Level) -> tuple[str, ...]:
        """The gates this bundle must fail or leave undecided at one level."""
        return tuple(sorted(self.unfavorable.get(str(level), ())))

    def artifacts(self) -> list[str]:
        """Every artifact the fixture ships, as bundle-relative posix paths."""
        return sorted(
            path.relative_to(self.directory).as_posix()
            for path in artifact_files(self.directory)
            if path.name != "fixture.toml"
        )


def fixtures() -> list[Fixture]:
    """Every fixture bundle, in a stable order.

    Raises:
        BenchproofError: The corpus is absent. It is package data, so this means the
            installation is incomplete rather than that the caller asked for
            something wrong, and the message says where the files were expected.
    """
    directory = root() / "bundles"
    found = (
        [_read(entry) for entry in sorted(directory.iterdir()) if entry.is_dir()]
        if directory.is_dir()
        else []
    )
    if not found:
        raise BenchproofError(
            f"no fixture bundles under {directory}; this installation of benchproofer "
            "is missing packaged data, so reinstall it with `pip install -e .`"
        )
    return found


def coexisting() -> list[Fixture]:
    """The fixtures that can be staged into one bundle root together.

    A bundle lives at ``<root>/<benchmark>/<task>/<backend>``, so two fixtures that
    formalize the same task with the same backend are the same bundle on disk. The
    corpus ships such a pair deliberately, because comparing a sound formalization
    with a weak one of the same task is what makes the pair worth having. A case that
    stages several fixtures side by side takes this subset instead, so the number of
    bundles it stages is the number it gets.
    """
    seen: set[tuple[str, str]] = set()
    chosen: list[Fixture] = []
    for candidate in fixtures():
        key = (candidate.task_id, candidate.backend)
        if key not in seen:
            seen.add(key)
            chosen.append(candidate)
    return chosen


def fixture(name: str) -> Fixture:
    """One fixture bundle by directory name.

    Raises:
        BenchproofError: No fixture ships under that name.
    """
    for candidate in fixtures():
        if candidate.name == name:
            return candidate
    available = ", ".join(item.name for item in fixtures())
    raise BenchproofError(f"no fixture named {name!r}; available: {available}")


def stage(target: Fixture, task: Task, settings: Settings) -> Bundle:
    """Copy a fixture's artifacts into a fresh bundle under a bundle root.

    The bundle is created the way the build stage creates one, so the frozen task
    beside it is the one the gates will read.

    Raises:
        BenchproofError: The fixture ships a `manifest.json`, which would let a recorded
            verdict reach a gate run that did not produce it.
    """
    if (target.directory / "manifest.json").exists():
        raise BenchproofError(f"fixture {target.name!r} ships a manifest.json")
    bundle = Bundle.create(settings.bundle_root, task, target.backend)
    for entry in sorted(target.directory.iterdir()):
        if entry.name == "fixture.toml" or entry.name in BYPRODUCTS:
            continue
        if entry.is_dir():
            shutil.copytree(
                entry,
                bundle.root / entry.name,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(*BYPRODUCTS),
            )
        else:
            shutil.copy2(entry, bundle.root / entry.name)
    return bundle


def _read(directory: Path) -> Fixture:
    """Read one fixture's declaration."""
    path = directory / "fixture.toml"
    if not path.is_file():
        raise BenchproofError(f"{directory} has no fixture.toml")
    document = load_toml(path)
    expect = document.get("expect", {})
    if not isinstance(expect, dict) or not expect:
        raise BenchproofError(f"{path}: [expect] must declare an outcome per level")
    unfavorable = document.get("unfavorable", {})
    if not isinstance(unfavorable, dict):
        raise BenchproofError(f"{path}: [unfavorable] must map a level to a list of gates")
    review = document.get("review", {})
    if not isinstance(review, dict):
        raise BenchproofError(f"{path}: [review] must map a judgment role to a verdict")
    fuzzers = document.get("fuzzer", [])
    if not isinstance(fuzzers, list):
        raise BenchproofError(f"{path}: [[fuzzer]] must be an array of tables")
    return Fixture(
        name=directory.name,
        task_id=str(document["task_id"]),
        backend=str(document["backend"]),
        summary=str(document.get("summary", "")),
        directory=directory,
        expectations={str(key): str(value) for key, value in expect.items()},
        unfavorable={
            str(key): tuple(str(gate) for gate in value) for key, value in unfavorable.items()
        },
        review={str(role): _judged(path, str(role), body) for role, body in review.items()},
        fuzzers=tuple(_attack(path, index, body) for index, body in enumerate(fuzzers, 1)),
    )


def _attack(path: Path, index: int, body: object) -> Attack:
    """Read one declared fuzzer."""
    if not isinstance(body, dict) or not str(body.get("program", "")).strip():
        raise BenchproofError(f"{path}: [[fuzzer]] {index} must declare a program")
    return Attack(
        id=str(body.get("id", f"fuzz-{index}")),
        callee=str(body.get("callee", "")),
        claim=str(body.get("claim", "")),
        program=str(body["program"]),
    )


def _judged(path: Path, role: str, body: object) -> Judged:
    """Read one declared judgment."""
    if not isinstance(body, dict) or "verdict" not in body:
        raise BenchproofError(f"{path}: [review.{role}] must declare a verdict")
    operations = body.get("operations", [])
    if not isinstance(operations, list):
        raise BenchproofError(
            f"{path}: [[review.{role}.operations]] must be an array of tables"
        )
    return Judged(
        role=role,
        verdict=str(body["verdict"]),
        summary=str(body.get("summary", "")),
        findings=tuple(str(item) for item in body.get("findings", [])),
        operations=tuple(
            (str(item["kind"]), str(item.get("detail", ""))) for item in operations
        ),
        coverage=tuple(
            (
                str(item["behavior"]),
                str(item.get("tested_by", "")),
                str(item.get("covered_by", "")),
            )
            for item in body.get("coverage", [])
        ),
    )
