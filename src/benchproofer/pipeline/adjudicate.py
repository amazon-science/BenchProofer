# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Adjudication: run the gates over a bundle and record what they found.

Judging is separate from building, and repeatable. Nothing here writes an artifact,
so a bundle can be re-judged after a gate is fixed, on another machine, or by
someone who did not build it, and `manifest.json` will show both records.

Which gates *run* and which gates are *required* are different questions. Every
registered gate runs, including third-party ones, because a recorded verdict is
worth having; the required set is what certification depends on, and it is fixed
here so that "certified" means the same thing in every report.

A gate that could not measure this time does not overwrite what the same gate code
measured from the same inputs (`_standing`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..backends.base import Backend
from ..config import Settings
from ..core.bundle import Bundle
from ..core.verdict import Certification, Level, SkipReason, Status, Verdict, classify
from ..errors import BundleError
from ..gates.base import Gate, GateContext
from ..log import logger, progress
from ..registries import GATES

__all__ = [
    "AUDITED_REQUIRED",
    "DISQUALIFYING",
    "ORACLE_REQUIRED",
    "REVIEWED",
    "STATIC_REQUIRED",
    "UNWAIVABLE",
    "Adjudication",
    "adjudicate",
    "bundles_under",
    "certify",
    "classified",
    "required_gates",
]

log = logger(__name__)

#: Gates a bundle must satisfy to be certified from the artifacts alone.
STATIC_REQUIRED: tuple[str, ...] = (
    "artifact.integrity",
    "spec.hygiene",
    "spec.no_leakage",
    "spec.verifies",
    "spec.discriminates",
    "spec.strength.mutation",
    "spec.strength.battery",
)
#: Additionally required when the benchmark's own oracle is available: the checks that
#: connect the verified artifact to the task the benchmark poses, and the one that
#: connects what the specification assumes of a callee to how the callee behaves.
ORACLE_REQUIRED: tuple[str, ...] = (
    *STATIC_REQUIRED,
    "impl.conformance",
    "spec.axioms_grounded",
    "oracle.reference_resolves",
)
#: Additionally required once a bundle has been reviewed: the questions no program
#: decides, and the implementations a program can only re-run rather than invent.
AUDITED_REQUIRED: tuple[str, ...] = (
    *ORACLE_REQUIRED,
    "audit.independence",
    "audit.spec_completeness",
    "audit.spec_soundness",
    "audit.faithfulness",
    "audit.equivalence",
    "audit.no_disclosure",
    "audit.axiom_soundness",
)
#: The gates that read a recorded review. A round of `pipeline.run` judges these only for a
#: bundle that has passed every gate before them, as `verified-swebench` orders its gates.
REVIEWED: tuple[str, ...] = tuple(
    gate for gate in AUDITED_REQUIRED if gate not in ORACLE_REQUIRED
)
#: The required set at each level of the ladder. Each entry contains the one below it,
#: which is what makes a higher certification mean strictly more.
REQUIRED: dict[Level, tuple[str, ...]] = {
    Level.STATIC: STATIC_REQUIRED,
    Level.ORACLE: ORACLE_REQUIRED,
    Level.AUDITED: AUDITED_REQUIRED,
}

#: Required gates that judge the task rather than anything drafted for it. When one fails,
#: the instance is dropped (`Outcome.DROPPED`) rather than rejected: `oracle.reference_resolves`
#: failing says the benchmark's own solution does not pass the benchmark's own tests here,
#: which no specification, implementation or proof could address.
DISQUALIFYING: tuple[str, ...] = ("oracle.reference_resolves",)

#: Execution order. Cheap and structural first, so a bundle that is malformed is
#: reported as malformed before a verifier spends minutes on it.
GATE_ORDER: tuple[str, ...] = (
    "artifact.integrity",
    "spec.hygiene",
    "spec.no_leakage",
    "spec.verifies",
    "spec.discriminates",
    "spec.strength.mutation",
    "spec.strength.battery",
    "impl.conformance",
    "spec.axioms_grounded",
    "oracle.reference_resolves",
    "audit.independence",
    "audit.faithfulness",
    "audit.equivalence",
    "audit.no_disclosure",
    "audit.axiom_soundness",
    "audit.spec_completeness",
    "audit.spec_soundness",
)


#: The gates no waiver may cover, because they are the claim rather than evidence for it:
#: `spec.verifies` is the checker accepting the file, `spec.hygiene` that it did so
#: without a construct that discharges an obligation by assertion, and
#: `artifact.integrity` that the file judged is the file shipped. Waiving another gate
#: gives a weaker certificate; waiving one of these would give a false one.
UNWAIVABLE: tuple[str, ...] = ("artifact.integrity", "spec.hygiene", "spec.verifies")

#: Verdicts that are measurements, favorable or not.
MEASURED: frozenset[Status] = frozenset({Status.PASS, Status.FAIL, Status.WAIVED})


def required_gates(level: Level) -> list[str]:
    """The gates certification depends on at one evidence level."""
    return list(REQUIRED[level])


def classified(
    verdicts: dict[str, Verdict], level: Level, bundle: Bundle | None = None
) -> Certification:
    """Classify ``verdicts`` against the gates ``level`` requires, `DISQUALIFYING` included.

    With ``bundle``, a verdict of a gate that reads the review (`REVIEWED`) is stale when a
    file it recorded reading no longer reads as it did. A round that stops before the
    review leaves such verdicts in `manifest.json`, about a bundle a repair has since replaced;
    the gates before them are judged again in every round that changed the bundle.
    """
    stale = (
        [
            gate
            for gate in REVIEWED
            if (verdict := verdicts.get(gate)) is not None and not bundle.describes(verdict)
        ]
        if bundle is not None
        else []
    )
    return classify(
        verdicts, required_gates(level), level, disqualifying=DISQUALIFYING, stale=stale
    )


@dataclass(frozen=True, slots=True)
class Adjudication:
    """One bundle, judged."""

    task_key: str
    bundle: Bundle
    backend: str
    level: Level
    verdicts: dict[str, Verdict]
    certification: Certification

    @property
    def certified(self) -> bool:
        """True when every required gate reached a favorable judgment."""
        return self.certification.certified


def adjudicate(
    bundle: Bundle,
    *,
    backend: Backend,
    settings: Settings,
    level: Level = Level.STATIC,
    only: tuple[str, ...] = (),
    waivers: dict[str, str] | None = None,
) -> Adjudication:
    """Judge one bundle.

    Args:
        bundle: The bundle to judge. Its artifacts are read, never written; gates
            write only into ``evidence/``.
        backend: The backend the bundle was built with.
        settings: Budgets and thresholds for this run.
        level: How much evidence to gather. `Level.ORACLE` additionally runs the
            gates that need the benchmark's own oracle, which usually means
            containers; `Level.AUDITED` additionally runs the gates that read a
            recorded review, which have nothing to read until one exists.
        only: Run just these gates, and classify from the whole of `manifest.json`.
            Used to add oracle evidence to bundles that were judged statically.
        waivers: Gate ids whose failures are recorded as waived, each with the reason
            given for it. The reason is recorded in the verdict and in the report.

    Returns:
        The verdicts from this invocation, and the certification computed from the
        bundle's full `manifest.json`, so evidence gathered by an earlier run still counts.

    Raises:
        BundleError: There is no bundle to judge, a waiver names a gate the central
            claim rests on, or ``only`` names a gate that is not registered.
    """
    if not bundle.exists:
        raise BundleError(f"no bundle at {bundle.root}")
    refused = sorted(set(waivers or {}) & set(UNWAIVABLE))
    if refused:
        raise BundleError(
            f"{', '.join(refused)} cannot be waived: a certificate over one of these "
            "would say the implementation satisfies the specification where nothing "
            "established that it does"
        )
    task = bundle.task()
    context = GateContext(
        bundle=bundle,
        backend=backend,
        settings=settings,
        level=level,
        waivers=dict(waivers or {}),
        reuse=True,
    )

    recorded = bundle.manifest().verdicts
    verdicts: dict[str, Verdict] = {}
    for gate in _gates(only):
        progress("running %s", gate.id)
        verdict = _standing(recorded.get(gate.id), gate.run(context))
        verdicts[gate.id] = verdict
        log.info("%s %s: %s (%s)", task.key, gate.id, verdict.status, verdict.summary)

    ledger = bundle.record(list(verdicts.values()))
    certification = classified(ledger.verdicts, level, bundle)
    return Adjudication(
        task_key=task.key,
        bundle=bundle,
        backend=backend.name,
        level=level,
        verdicts=verdicts,
        certification=certification,
    )


def certify(bundle: Bundle, level: Level = Level.STATIC) -> Certification:
    """Classify a bundle from its recorded `manifest.json`, without running anything.

    This is what a report reads. It never runs a gate, so a missing verdict stays
    missing instead of being filled in by whoever happens to be looking.
    """
    return classified(bundle.manifest().verdicts, level, bundle)


def bundles_under(root: Path) -> list[Bundle]:
    """Every bundle under a root, in a stable order.

    A bundle counts as present once it holds a solution or a `manifest.json`, so one that was
    built but never judged is still found, and so is one whose artifacts were removed
    but whose verdicts remain.
    """
    found: list[Bundle] = []
    for path in sorted(Path(root).glob("*/*/*")):
        if not path.is_dir():
            continue
        if (path / "manifest.json").is_file() or any(path.glob("solution.*")):
            found.append(Bundle(path))
    return found


def _standing(recorded: Verdict | None, fresh: Verdict) -> Verdict:
    """The verdict to record: the fresh one, unless it measured nothing `manifest.json` did.

    The recorded verdict stands only when it is a measurement and the fresh attempt, which
    measured nothing, read exactly the same inputs with exactly the same gate code: a crash,
    a timeout or a missing toolchain or oracle says nothing about the bundle. The attempt
    is kept beside the verdict, so a reader can see it was tried again.
    """
    if recorded is None or recorded.status not in MEASURED or not _unmeasured(fresh):
        return fresh
    if recorded.inputs != fresh.inputs or recorded.judge_digest != fresh.judge_digest:
        return fresh
    log.info(
        "%s: %s this time (%s); the %s measured from the same inputs stands",
        fresh.gate,
        fresh.status,
        fresh.summary[:200],
        recorded.status,
    )
    return recorded.model_copy(
        update={
            "details": {
                **recorded.details,
                "remeasured": {
                    "status": str(fresh.status),
                    "summary": fresh.summary[:400],
                    "at": fresh.judged_at.isoformat(),
                },
            }
        }
    )


def _unmeasured(verdict: Verdict) -> bool:
    """Whether a verdict measured nothing: a crash, a timeout, a missing toolchain or oracle."""
    return verdict.status in (Status.ERROR, Status.TIMEOUT) or verdict.skip_reason in (
        SkipReason.TOOLCHAIN_ABSENT,
        SkipReason.ORACLE_UNAVAILABLE,
    )


def _gates(only: tuple[str, ...]) -> list[Gate]:
    """Resolve the gates to run, in execution order."""
    loaded = GATES.load_all()
    if only:
        missing = [name for name in only if name not in loaded]
        if missing:
            raise BundleError(f"unknown gate(s): {', '.join(missing)}")
        loaded = {name: gate for name, gate in loaded.items() if name in only}
    order = {gate_id: index for index, gate_id in enumerate(GATE_ORDER)}
    return sorted(loaded.values(), key=lambda gate: (order.get(gate.id, len(order)), gate.id))
