# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Gate framework (docs/architecture.md §4). Gates are pure, read-only judgments of
the bundle as committed — the lean proof agent runs in construction P1.5,
never here. `mode="feedback"` (P1 leniency) vs `mode="strict"` (the real
verdict) is recorded in the result so a gate name never means two things.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol, Sequence

from .. import paths
from ..backends import Backend
from ..paths import PROJECT_ROOT, bundle_dir, instance_dir


@dataclass
class GateResult:
    gate: str
    # "relaxed" = G-LEAK's RELAXED_LEAKAGE.md escape hatch: screen failed but
    # the leak is a reviewed semantic necessity — counts as ok.
    status: str  # "pass" | "fail" | "skip" | "relaxed" | "error" | "timeout"
    detail: str = ""
    data: dict = field(default_factory=dict)
    mode: str = "strict"        # "strict" | "feedback"
    checked_at: str = ""        # ISO timestamp (stamped by run_gates)
    code_version: str = ""      # git describe (stamped by run_gates)
    # sha256 of the gate/judgment sources (stamped by run_gates). This is the
    # provenance a released bundle can be checked against; `code_version` cannot
    # be, since the tree is dirty whenever artifacts are being written.
    harness_digest: str = ""
    # Set by `guarded` when an exception escaped the gate body: the gate reached
    # no verdict at all. In-process signal for `_record`, never serialized.
    harness_error: bool = False

    @property
    def ok(self) -> bool:
        return self.status in ("pass", "skip", "relaxed")

    def to_json(self) -> dict:
        blob = asdict(self)
        blob.pop("harness_error", None)
        return blob


@dataclass
class Bundle:
    """Inputs at tasks/<id>/, constructed artifacts at tasks/<id>/<backend>/."""
    instance_id: str
    backend: Backend

    @property
    def instance_root(self) -> Path:
        return instance_dir(self.instance_id)

    @property
    def root(self) -> Path:
        return bundle_dir(self.instance_id, self.backend.name)

    @property
    def instance_json(self) -> Path:
        return self.instance_root / "instance.json"

    @property
    def patch_diff(self) -> Path:
        return self.instance_root / "patch.diff"

    @property
    def solution(self) -> Path:
        return self.root / self.backend.language.solution_filename

    @property
    def axiom_check(self) -> Path:
        return self.root / "axiom_check.py"

    @property
    def conformance_check(self) -> Path:
        return self.root / "conformance_check.py"

    @property
    def meta_path(self) -> Path:
        return self.root / "meta.json"

    @property
    def gold_solution(self) -> Path:
        stem, dot, ext = self.backend.language.solution_filename.rpartition(".")
        return self.root / f"{stem}_gold{dot}{ext}"

    @property
    def prepatches(self) -> list[Path]:
        stem, dot, ext = self.backend.language.solution_filename.rpartition(".")
        return sorted(self.root.glob(f"{stem}_prepatch*{dot}{ext}"))

    def solution_src(self) -> str:
        # BLOCKED bundles ship no solution; "" lets a sweep degrade to
        # skip/fail instead of crashing.
        return self.solution.read_text() if self.solution.exists() else ""

    def source_paths(self, reads: Sequence[str]) -> list[Path]:
        """The bundle files a gate declaring `reads` consumes.

        Logical names, not filenames, so a gate does not have to know that a
        solution is `model.py` on one backend and `Solution.lean` on another.
        """
        out: list[Path] = []
        for logical in reads:
            if logical == "solution":
                out.append(self.solution)
            elif logical == "prepatches":
                out.extend(self.prepatches)
            elif logical == "properties":
                out.append(self.root / "properties.py")
            elif logical == "instance":
                out.append(self.instance_json)
            elif logical == "axiom_check":
                out.append(self.axiom_check)
            elif logical == "conformance_check":
                out.append(self.conformance_check)
            elif logical == "patch":
                out.append(self.patch_diff)
            elif logical == "relaxed_leakage_doc":
                out.append(self.root / "RELAXED_LEAKAGE.md")
            else:
                raise ValueError(f"unknown gate read: {logical!r}")
        return [p for p in out if p.is_file()]

    def meta(self) -> dict:
        p = self.root / "meta.json"
        if p.exists():
            try:
                return json.loads(p.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def verify_timeout(self) -> int:
        return int(self.meta().get("gates", {}).get("G-VERIFY", {})
                   .get("timeout_seconds", 300))

    def float_encoding(self) -> str | None:
        """Nagini knob, declared in meta.json (G-HYGIENE checks it's used)."""
        return self.meta().get("float_encoding")


def load_frozen_row(instance_id: str) -> dict | None:
    """Frozen-dataset row for the instance. Reads paths.DATASET_JSONL at call
    time so tests can repoint it."""
    dataset = paths.DATASET_JSONL
    if not dataset.exists():
        return None
    with dataset.open() as fh:
        for line in fh:
            if f'"{instance_id}"' in line:
                row = json.loads(line)
                if row.get("instance_id") == instance_id:
                    return row
    return None


def frozen_dataset_complaint(tasks_root: Path | None = None) -> str:
    """"" when the frozen dataset can answer for this corpus, else why it cannot.

    `load_frozen_row` returns None both for "the dataset was never fetched" and for
    "a different benchmark is active", which is the right answer about one row and
    the wrong report for a whole run: a caller that walks a corpus then degrades
    silently, one row at a time, and ends in a count of records it could not decide
    with no line saying why. A fresh checkout is exactly that case -- nothing under
    `data/` is committed -- so the precondition is measured once, up front, against
    the corpus's own instance ids.
    """
    dataset = paths.DATASET_JSONL
    if not dataset.exists():
        return (f"frozen dataset not found at {dataset}; run "
                f"`swebench-unified fetch-dataset` for the benchmark this corpus "
                f"was built from, or point SBU_DATA_ROOT at an existing one")
    root = tasks_root or paths.TASKS_ROOT
    ids = [p.name for p in sorted(root.glob("*")) if (p / "instance.json").is_file()]
    sample = ids[:3]
    if sample and all(load_frozen_row(i) is None for i in sample):
        return (f"the frozen dataset at {dataset} holds none of {root.name}'s "
                f"instances (sampled {', '.join(sample)}); SBU_BENCHMARK names a "
                f"different benchmark than the one this corpus was built from")
    return ""


class Gate(Protocol):
    """One module per gate; unsupported backends get an explicit skip."""
    name: str
    applies_to: tuple[str, ...]
    needs_docker: bool

    def run(self, bundle: Bundle, *, mode: str = "strict") -> GateResult: ...


def _code_version() -> str:
    try:
        return subprocess.run(["git", "describe", "--always", "--dirty"],
                              capture_output=True, text=True, cwd=str(PROJECT_ROOT),
                              timeout=10).stdout.strip()
    except Exception:
        return "unknown"


# The modules whose bytes decide a verdict. `git describe --dirty` cannot stand
# in for these: construction writes benchmark artifacts into the tree, so it is
# dirty essentially always and every record is stamped `-dirty` for reasons having
# nothing to do with the harness. A consumer of a released bundle needs to know
# which JUDGE ran, which is what hashing the judging code answers.
#
# Every entry must NAME SOMETHING: an entry that resolves to nothing is skipped
# silently, so a stale name reads as coverage the digest does not have. The
# manifest reader lives in `gates/pbt.py` and is covered by the `gates` entry.
_HARNESS_FILES = ("gates", "pbt_witness.py", "variant_scope.py")


def _harness_digest(pkg: Path | None = None) -> str:
    """sha256 over the gate/judgment sources, first 12 hex chars.

    Order-stable (sorted by repo-relative path) and content-only, so it changes
    exactly when the code that reaches a verdict changes -- unlike the git
    describe stamp, which changes when any driver writes any artifact.

    `pkg` defaults to this package; it is a parameter only so a test can take the
    digest over a scratch tree instead of editing the live sources.
    """
    import hashlib
    pkg = pkg or Path(__file__).resolve().parent.parent
    paths: list[Path] = []
    for entry in _HARNESS_FILES:
        p = pkg / entry
        if p.is_dir():
            paths.extend(sorted(p.rglob("*.py")))
        elif p.is_file():
            paths.append(p)
    h = hashlib.sha256()
    for p in sorted(paths, key=lambda q: q.relative_to(pkg).as_posix()):
        h.update(p.relative_to(pkg).as_posix().encode())
        h.update(b"\0")
        try:
            h.update(p.read_bytes())
        except OSError:          # unreadable source: record the absence, do not crash
            h.update(b"<unreadable>")
        h.update(b"\0")
    return h.hexdigest()[:12]


def source_digests(bundle: Bundle, reads: Sequence[str]) -> dict[str, str]:
    """sha256 of each bundle file this gate read, keyed by filename.

    `harness_digest` binds a record to the code that judged; this binds it to the
    artifact that was judged. Both are needed, and neither substitutes for the
    other: a green record without them attests only that SOME solution at that
    path passed at that time. Solutions and batteries do get edited after a gate
    has run (adding a termination obligation, re-authoring a battery), and
    re-gating afterwards is a caller's convention rather than something a reader
    holding only the bundle can check. With the digests, "this stamp does not
    describe these files" is a mechanical question
    (`scripts/check_stamp_freshness.py`) instead of an argument about timestamps,
    which cannot answer it: any tree-wide operation rewrites mtimes without
    changing a byte.

    Absent files are omitted rather than recorded as empty: a gate that skipped
    because there was no battery must not claim to have digested one.
    """
    import hashlib
    out: dict[str, str] = {}
    for p in bundle.source_paths(reads):
        try:
            out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            continue
    return out


def _cached_harness_digest(_cache: list[str] = []) -> str:
    """Computed once per process: the sources cannot change under a running gate
    in any way this stamp could honestly report."""
    if not _cache:
        try:
            _cache.append(_harness_digest())
        except Exception:
            _cache.append("unknown")
    return _cache[0]


def stamp(result: GateResult, mode: str) -> GateResult:
    result.mode = mode
    result.checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result.code_version = _code_version()
    result.harness_digest = _cached_harness_digest()
    return result


def guarded(name: str, fn: Callable[[], GateResult]) -> GateResult:
    """Convert unexpected exceptions into an error result — a broken gate must
    never take down a sweep.

    An exception escaping a gate body is a bug in the HARNESS, not a judgment
    about the bundle: the gate never reached a verdict. Flag it as such so
    `_record` will not overwrite a real prior verdict with it. Without the flag an
    `error :: NameError` from a half-imported module is indistinguishable, in the
    record, from a battery that genuinely failed.
    """
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 — deliberate boundary catch-all
        return GateResult(name, "error", f"{type(e).__name__}: {e}",
                          harness_error=True)
