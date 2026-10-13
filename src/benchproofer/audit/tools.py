# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a session runs to turn a claim about the code into a fact rather than an opinion.

A reviewer that can only argue about a specification reports impressions, and a reviewer
that can run the checker reports what the checker said. `verified-swebench` hands its
review agents a small toolkit for that -- the verifier, a same-spec check, the gate an
attack is judged by -- and this is the same toolkit for any backend and any benchmark:

* ``verify FILE`` puts a file to the bundle's checker;
* ``try FILE --as attack|control [--patch PATCH] [--test TEST] [--cites TEXT]
  [--refutation WITNESS]`` judges one submission exactly as `audit.spec_completeness` and
  `audit.spec_soundness` will: the checker, then `conformance.py` or the benchmark's tests,
  then the witness test and the refutation witness filed with it, and names each submission
  it leaves to the attack validation auditor;
* ``fuzz FILE [--callee NAME]`` runs one fuzzer exactly as `audit.axiom_soundness` will;
* ``run FILE`` runs a Python program where the benchmark's tests run, with the golden
  patch applied, to see what the real code does.

Each works on a copy of the bundle in the session's own workspace. None of them is a
verdict: what a session submits is re-run by the gates, over the bundle itself, whatever
these said while it worked. What a session is told of them is `core/templates/tools-rules.md`.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from ..backends.base import Backend, CheckResult
from ..config import Settings
from ..core.bundle import Bundle, Fuzzer, Review, SubmissionKind
from ..core.material import clip
from ..core.task import Task
from ..core.verdict import Level, Status
from ..errors import BenchproofError
from ..gates.audit import UNRULED, SpecCompletenessGate, SpecSoundnessGate
from ..gates.axioms import AxiomSoundnessGate
from ..gates.base import GateContext
from ..oracles.base import Program
from ..registries import BACKENDS, ORACLES
from ..util.fsio import read_text
from .session import Filed

__all__ = ["main"]

#: Longest checker or program output printed, in characters. Enough for a counterexample
#: and a traceback; a session that wants the rest has the log the evidence names.
OUTPUT_LIMIT = 8_000
#: What each spelling of a submission's purpose is filed as.
_KINDS: dict[str, SubmissionKind] = {"attack": "weakness", "control": "control"}


def main(argv: list[str] | None = None) -> int:
    """Run one tool over the bundle copy ``--bundle`` names, and print what it found.

    The `./tools` script passes ``--bundle``, so the usage does not show it, and a value
    that names no bundle is refused with what was expected rather than a traceback.
    """
    parser = argparse.ArgumentParser(prog="./tools", description=__doc__.split("\n\n")[0])
    parser.add_argument("--bundle", required=True, type=Path, help=argparse.SUPPRESS)
    commands = parser.add_subparsers(dest="command", required=True)
    verify = commands.add_parser("verify", help="put a file to the checker")
    verify.add_argument("file", type=Path)
    attempt = commands.add_parser("try", help="judge one submission as the review's gates will")
    attempt.add_argument("file", type=Path)
    attempt.add_argument("--as", dest="kind", choices=sorted(_KINDS), required=True)
    attempt.add_argument("--patch", type=Path, default=None)
    attempt.add_argument("--test", type=Path, default=None)
    attempt.add_argument("--cites", default="")
    attempt.add_argument("--refutation", type=Path, default=None)
    fuzz = commands.add_parser(
        "fuzz", help="run one fuzzer as audit.axiom_soundness (the axiom-soundness gate) will"
    )
    fuzz.add_argument("file", type=Path)
    fuzz.add_argument("--callee", default="")
    run = commands.add_parser(
        "run", help="run a Python program where the tests run, with the golden patch applied"
    )
    run.add_argument("file", type=Path)
    args = parser.parse_args(argv)

    bundle = Bundle(args.bundle.resolve())
    settings = Settings()
    try:
        backend = BACKENDS.get(bundle.backend_name)
        task = bundle.task()
    except BenchproofError:
        parser.error(
            f"--bundle {args.bundle} is not a bundle: it names the bundle directory, "
            "`bundles/<benchmark>/<task>/<backend>`, which `./tools` passes itself, so "
            "leave the option out"
        )
    if args.command == "verify":
        return _verify(bundle, backend, settings, args.file)
    if args.command == "try":
        return _try(
            bundle,
            task,
            backend,
            settings,
            args.file,
            _KINDS[args.kind],
            _Evidence(args.patch, args.test, args.cites, args.refutation),
        )
    if args.command == "fuzz":
        return _fuzz(bundle, task, backend, settings, args.file, args.callee)
    return _run(bundle, task, settings, args.file)


def _verify(bundle: Bundle, backend: Backend, settings: Settings, file: Path) -> int:
    """Put one file to the checker, and exit zero when it accepts."""
    result = backend.check(
        read_text(file),
        workdir=_scratch(bundle, "verify", file.stem),
        timeout_s=backend.budget(settings.verify_timeout_s),
    )
    print(f"status: {result.status}")
    print(f"detail: {result.detail or '-'}")
    if result.output.strip():
        print(clip(result.output, OUTPUT_LIMIT))
    if not result.verified:
        return 1
    # The axioms each claim rests on, where the backend can say: a file that elaborates
    # with a hole in its proof is accepted by the checker and refused by `spec.verifies`.
    closure = backend.closure(
        read_text(file),
        workdir=_scratch(bundle, "verify", f"{file.stem}-closure"),
        timeout_s=backend.budget(settings.verify_timeout_s),
    )
    if closure is None:
        return 0
    complete = "yes" if closure.closed else "no"
    print(f"proof complete (no sorry or extra axiom): {complete} -- {closure.detail}")
    return 0 if closure.closed else 1


@dataclass(frozen=True, slots=True)
class _Evidence:
    """What `try` files beside a submission's own file, as the attack auditor files it."""

    patch: Path | None = None
    test: Path | None = None
    cites: str = ""
    refutation: Path | None = None


def _try(
    bundle: Bundle,
    task: Task,
    backend: Backend,
    settings: Settings,
    file: Path,
    kind: SubmissionKind,
    evidence: _Evidence,
) -> int:
    """Judge one submission with the two gates that re-run submissions, and print the row.

    Then the gate's verdict, and what the gate established of a submission it leaves to the
    attack validation auditor.
    """
    copy = _alone(bundle, task, "try")
    filed = Filed(
        id=file.stem,
        kind=kind,
        claim="",
        file=f"{file.stem}{backend.extension}",
        source=read_text(file),
        patch=read_text(evidence.patch) if evidence.patch is not None else "",
        test=read_text(evidence.test) if evidence.test is not None else "",
        cites=evidence.cites,
        refutation=read_text(evidence.refutation) if evidence.refutation is not None else "",
    )
    copy.save_audit(Review(reviewer="trial", submissions=(filed.record(),)), filed.sources())
    # One submission is judged alone, so the gate is asked to count it as enough: how many
    # the run wants is a question about the whole review, not about this file.
    alone = settings.model_copy(update={"audit_min_attacks": 1, "audit_min_controls": 1})
    gate = SpecCompletenessGate() if kind == "weakness" else SpecSoundnessGate()
    verdict = gate.run(_context(copy, backend, alone))
    table = copy.evidence_dir / "audit-submissions.txt"
    if table.is_file():
        print(read_text(table).rstrip())
    print(f"{verdict.gate}: {verdict.status}: {verdict.summary}")
    left = verdict.details.get(UNRULED)
    for name, said in left.items() if isinstance(left, dict) else ():
        print(f"{name} is left to the attack validation auditor: {said}")
    return 0


def _fuzz(
    bundle: Bundle,
    task: Task,
    backend: Backend,
    settings: Settings,
    file: Path,
    callee: str,
) -> int:
    """Run one fuzzer with the gate that re-runs fuzzers, and print what it established."""
    copy = _alone(bundle, task, "fuzz")
    fuzzer = Fuzzer(id=file.stem, file=f"{file.stem}.fuzz.py", callee=callee)
    copy.save_audit(Review(reviewer="trial", fuzzers=(fuzzer,)), {fuzzer.file: read_text(file)})
    verdict = AxiomSoundnessGate().run(_context(copy, backend, settings))
    print(f"{verdict.gate}: {verdict.status}: {verdict.summary}")
    log = copy.evidence_dir / f"fuzz-{fuzzer.id}.log"
    if log.is_file():
        print(clip(read_text(log), OUTPUT_LIMIT))
    return 0


def _run(bundle: Bundle, task: Task, settings: Settings, file: Path) -> int:
    """Run a program where the benchmark's tests run, with the golden patch applied."""
    oracle = ORACLES.get(task.oracle.kind)
    available = oracle.availability()
    if not available:
        print(f"the task's environment is unavailable here: {available.detail}")
        return 2
    result = oracle.probe(
        task,
        Program(source=read_text(file), label=file.stem, with_reference=True),
        workdir=_scratch(bundle, "run", file.stem),
        timeout_s=settings.oracle_timeout_s,
    )
    print(f"status: {result.status}")
    print(f"detail: {result.detail or '-'}")
    if result.output.strip():
        print(clip(result.output, OUTPUT_LIMIT))
    return 0 if result.resolved else 1


def _context(bundle: Bundle, backend: Backend, settings: Settings) -> GateContext:
    """What the gates are given, the shipped solution taken as verified if recorded so.

    Every gate that re-runs a variant first asks whether the shipped solution verifies,
    and a trial that asked again would spend a checker run on a question the manifest's
    verdicts decided when the bundle was judged. A manifest that does not record a pass is asked
    again, as the gates ask it.
    """
    recorded = bundle.manifest().verdicts.get("spec.verifies")
    base = (
        CheckResult.ok("the shipped solution verified when the bundle was judged")
        if recorded is not None and recorded.status is Status.PASS
        else None
    )
    return GateContext(
        bundle=bundle, backend=backend, settings=settings, level=Level.AUDITED, _base=base
    )


def _alone(bundle: Bundle, task: Task, purpose: str) -> Bundle:
    """A fresh copy of the bundle with no review in it, for judging one program alone."""
    root = _scratch(bundle, purpose, "bundles")
    shutil.rmtree(root, ignore_errors=True)
    copy = Bundle.create(root, task, bundle.backend_name)
    shutil.copytree(bundle.root, copy.root, dirs_exist_ok=True)
    shutil.rmtree(copy.audit_dir, ignore_errors=True)
    return copy


def _scratch(bundle: Bundle, *parts: str) -> Path:
    """A working directory beside the bundle copy, inside the session's own workspace."""
    path = bundle.root.parents[3].joinpath(".tools", *parts)
    path.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    sys.exit(main())
