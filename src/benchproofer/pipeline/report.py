# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Reporting: what a corpus of bundles says, and what it does not.

A report is a projection of recorded verdicts. It runs nothing, computes no new
judgment, and classifies every bundle with `core.verdict.classify` rather than deciding
for itself what counts as done. Undecided and missing verdicts are reported in their
own columns instead of being folded into a pass rate, because a bundle nobody could
judge and a bundle that failed are different results.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core import material
from ..core.bundle import Bundle
from ..core.provenance import environment_report
from ..core.verdict import Certification, Level, Outcome, Status, Verdict
from ..gates.audit import INPUTS, SpecSoundnessGate, listed_under
from ..gates.battery import BatteryGate
from ..log import logger
from ..util.fsio import write_json, write_text
from .adjudicate import bundles_under, classified, required_gates

__all__ = ["BundleRow", "Report", "Unproved", "collect", "summarize", "write_report"]

log = logger(__name__)

#: How many bundles the Markdown report lists in each table before eliding the rest.
_LISTED = 40


@dataclass(frozen=True, slots=True)
class Unproved:
    """A correct case whose own proof the checker rejected, so the checker fell short there.

    A case of the property-based test suite `spec.strength.battery` names, or a control of the
    review the attack validation auditor ruled `unproved` (`audit.spec_soundness`).
    """

    case: str
    #: Why the case is held correct, and what the checker said.
    reason: str
    #: Whether a session tried to prove it and failed: a proof session (an agent session
    #: asked to prove the case), or the attack auditor, which proves each control it files.
    after_session: bool


@dataclass(frozen=True, slots=True)
class BundleRow:
    """One bundle's line in a report."""

    benchmark: str
    task_id: str
    backend: str
    path: str
    outcome: Outcome
    failed: tuple[str, ...] = ()
    undecided: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    #: Gates whose recorded verdict judged files the bundle no longer has.
    stale: tuple[str, ...] = ()
    #: Gates this bundle certifies over, each with the reason given for it. A waiver is
    #: the one way a certificate can mean less than it says, so it is reported next to
    #: the bundle rather than left in `manifest.json` for whoever thinks to look.
    waived: tuple[tuple[str, str], ...] = ()
    #: The correct cases of its property-based test suite, and the controls of its review,
    #: whose own proof the checker rejected.
    unproved: tuple[Unproved, ...] = ()
    #: The unchanged callees whose result the specification takes as an input, each as
    #: `correspondence.md` lists it, with its call site and reason; no gate checks the call.
    inputs: tuple[str, ...] = ()

    @property
    def key(self) -> str:
        """The bundle's identity: task and backend."""
        return f"{self.benchmark}/{self.task_id} [{self.backend}]"

    def waivers(self) -> str:
        """The waivers this bundle rests on, one phrase each."""
        return "; ".join(f"{gate} ({why})" for gate, why in self.waived)

    def reason(self) -> str:
        """Why this bundle is not certified, or an empty string when it is."""
        parts = []
        if self.failed:
            parts.append("failed " + ", ".join(self.failed))
        if self.undecided:
            parts.append("undecided " + ", ".join(self.undecided))
        if self.stale:
            parts.append("stale " + ", ".join(self.stale))
        if self.missing:
            parts.append("missing " + ", ".join(self.missing))
        return "; ".join(parts)


@dataclass(frozen=True, slots=True)
class Report:
    """A corpus of bundles, as their ledgers describe them."""

    level: Level
    rows: tuple[BundleRow, ...]
    gate_tally: dict[str, dict[str, int]]
    environment: dict[str, Any]

    @property
    def total(self) -> int:
        """How many bundles the report covers."""
        return len(self.rows)

    def counts(self) -> dict[str, int]:
        """Bundles per outcome, with every outcome present even at zero."""
        counts = {str(outcome): 0 for outcome in Outcome}
        for row in self.rows:
            counts[str(row.outcome)] += 1
        return counts

    def certified(self) -> tuple[BundleRow, ...]:
        """The certified bundles."""
        return tuple(row for row in self.rows if row.outcome is Outcome.CERTIFIED)

    def to_json(self) -> dict[str, Any]:
        """The report as a JSON-serializable document."""
        return {
            "level": str(self.level),
            "required_gates": required_gates(self.level),
            "total": self.total,
            "counts": self.counts(),
            "gates": self.gate_tally,
            "environment": self.environment,
            "bundles": [
                {
                    "benchmark": row.benchmark,
                    "task_id": row.task_id,
                    "backend": row.backend,
                    "path": row.path,
                    "outcome": str(row.outcome),
                    "failed": list(row.failed),
                    "undecided": list(row.undecided),
                    "missing": list(row.missing),
                    "stale": list(row.stale),
                    "waived": [{"gate": gate, "because": why} for gate, why in row.waived],
                    "unproved": [
                        {
                            "case": case.case,
                            "reason": case.reason,
                            "after_proof_session": case.after_session,
                        }
                        for case in row.unproved
                    ],
                    "inputs": list(row.inputs),
                }
                for row in self.rows
            ],
        }

    def to_markdown(self) -> str:
        """Render the report for a human reader."""
        counts = self.counts()
        lines = [
            f"# Benchproofer report (level={self.level})",
            "",
            f"- bundles: {self.total}",
            *(f"- {name}: {count}" for name, count in counts.items()),
            "",
            "A bundle is certified when every required gate reached a favorable",
            "judgment. Undecided and missing verdicts are not favorable: they mean the",
            "check did not happen, which is reported rather than assumed either way.",
            "A dropped bundle is one whose task failed a check about the benchmark",
            "itself: its own solution does not pass its own tests here.",
            "",
            "## Gates",
            "",
            "| gate | " + " | ".join(str(status) for status in Status) + " |",
            "| --- | " + " | ".join("---" for _ in Status) + " |",
        ]
        for gate_id in sorted(self.gate_tally):
            tally = self.gate_tally[gate_id]
            cells = " | ".join(str(tally.get(str(status), 0)) for status in Status)
            lines.append(f"| `{gate_id}` | {cells} |")

        waived = [row for row in self.rows if row.waived]
        if waived:
            lines += [
                "",
                f"## Waived ({len(waived)})",
                "",
                "A waived gate objected and was overruled, so these bundles are certified",
                "on less than the others. The reason is the one given on the command line.",
                "",
                "| bundle | waived |",
                "| --- | --- |",
            ]
            lines += [f"| {row.key} | {row.waivers()} |" for row in waived[:_LISTED]]
            if len(waived) > _LISTED:
                lines.append(f"| ... and {len(waived) - _LISTED} more | |")

        unproved = [(row, case) for row in self.rows for case in row.unproved]
        if unproved:
            lines += [
                "",
                f"## Correct cases whose own proof the checker rejected ({len(unproved)})",
                "",
                "Each case below is correct, and the checker rejected a step of its own proof",
                "rather than the specification: there the checker, not the specification,",
                "fell short. A case is one of the property-based test suite, or a control of",
                "the review the attack validation auditor ruled `unproved`. `failed` marks a",
                "case a session tried and could not prove: a proof session (an agent session",
                "asked to prove the case), or the attack auditor, which proves each control it",
                "files.",
                "",
                "| bundle | case | proof session | reason |",
                "| --- | --- | --- | --- |",
            ]
            lines += [
                f"| {row.key} | `{case.case}` | {'failed' if case.after_session else 'none'} | "
                f"{material.cell(case.reason)} |"
                for row, case in unproved[:_LISTED]
            ]
            if len(unproved) > _LISTED:
                lines.append(f"| ... and {len(unproved) - _LISTED} more | | | |")

        inputs = [(row, entry) for row in self.rows for entry in row.inputs]
        if inputs:
            lines += [
                "",
                f"## Callee results taken as inputs ({len(inputs)})",
                "",
                "The specification takes the result of each callee below as an input, as",
                "`correspondence.md` lists it with its call site and its reason, so the call",
                "itself -- which callee, with which arguments, how many times -- is not",
                "checked. That fails no gate.",
                "",
                "| bundle | callee result taken as an input |",
                "| --- | --- |",
            ]
            lines += [
                f"| {row.key} | {material.cell(entry)} |" for row, entry in inputs[:_LISTED]
            ]
            if len(inputs) > _LISTED:
                lines.append(f"| ... and {len(inputs) - _LISTED} more | |")

        unfinished = [row for row in self.rows if row.outcome is not Outcome.CERTIFIED]
        lines += ["", f"## Not certified ({len(unfinished)})", ""]
        if not unfinished:
            lines.append("None.")
        else:
            lines += ["| bundle | outcome | reason |", "| --- | --- | --- |"]
            for row in unfinished[:_LISTED]:
                lines.append(f"| {row.key} | {row.outcome} | {row.reason()} |")
            if len(unfinished) > _LISTED:
                lines.append(f"| ... and {len(unfinished) - _LISTED} more | | |")
        lines += [
            "",
            "## Environment",
            "",
            *(f"- {name}: {value}" for name, value in self.environment.items()),
            "",
        ]
        return "\n".join(lines)


def collect(
    bundle_root: Path,
    *,
    level: Level = Level.STATIC,
    benchmark: str | None = None,
    backend: str | None = None,
) -> Report:
    """Read every bundle's `manifest.json` under a root and classify it."""
    selected = [
        bundle
        for bundle in bundles_under(bundle_root)
        if _matches(bundle, benchmark=benchmark, backend=backend)
    ]
    return summarize(selected, level=level, root=bundle_root)


def summarize(
    bundles: list[Bundle], *, level: Level = Level.STATIC, root: Path | None = None
) -> Report:
    """Classify a specific set of bundles.

    Used when a report should cover exactly the bundles a run touched, rather than
    everything that happens to be on disk.
    """
    rows: list[BundleRow] = []
    tally: dict[str, dict[str, int]] = {}

    for bundle in bundles:
        manifest = bundle.manifest()
        certification: Certification = classified(manifest.verdicts, level, bundle)
        rows.append(
            BundleRow(
                benchmark=manifest.benchmark,
                task_id=manifest.task_id,
                backend=manifest.backend,
                path=_relative(bundle, root),
                outcome=certification.outcome,
                failed=tuple(certification.failed),
                undecided=tuple(certification.undecided),
                missing=tuple(certification.missing),
                stale=tuple(certification.stale),
                waived=tuple(
                    (gate_id, str(verdict.details.get("waived_because", "no reason recorded")))
                    for gate_id, verdict in sorted(manifest.verdicts.items())
                    if verdict.status is Status.WAIVED
                ),
                unproved=(
                    *_unproved(manifest.verdicts.get(BatteryGate.id), _SUITE),
                    *_unproved(manifest.verdicts.get(SpecSoundnessGate.id), _REVIEW),
                ),
                inputs=_bullets(listed_under(bundle, INPUTS)),
            )
        )
        for gate_id, verdict in manifest.verdicts.items():
            counts = tally.setdefault(gate_id, {})
            key = str(verdict.status)
            counts[key] = counts.get(key, 0) + 1

    rows.sort(key=lambda row: (row.benchmark, row.task_id, row.backend))
    return Report(
        level=level,
        rows=tuple(rows),
        gate_tally=tally,
        environment=environment_report(),
    )


def write_report(report: Report, directory: Path) -> tuple[Path, Path]:
    """Write ``report.json`` and ``report.md`` into a directory."""
    directory = Path(directory)
    document = directory / "report.json"
    rendered = directory / "report.md"
    write_json(document, report.to_json())
    write_text(rendered, report.to_markdown())
    log.info("wrote %s and %s", document, rendered)
    return document, rendered


#: Where a `spec.strength.battery` verdict lists the correct cases refused on their own proof:
#: those a proof session has not tried, then those it tried and could not prove.
_SUITE = (("unproved_reasons", False), ("gap_reasons", True))
#: Where an `audit.spec_soundness` verdict lists the controls ruled `unproved`, each of which
#: the attack auditor tried to prove.
_REVIEW = (("unproved", True),)


def _unproved(
    verdict: Verdict | None, keys: tuple[tuple[str, bool], ...]
) -> tuple[Unproved, ...]:
    """The correct cases ``verdict`` lists under ``keys`` as refused on their own proof.

    Each key with whether a session tried to prove the cases it lists, and each case with the
    reason the verdict gives.
    """
    details = verdict.details if verdict is not None else {}
    return tuple(
        Unproved(str(case), str(why), after_session=after)
        for key, after in keys
        if isinstance(found := details.get(key), dict)
        for case, why in found.items()
    )


def _bullets(text: str) -> tuple[str, ...]:
    """Each bullet of ``text``, with the lines under it; the text whole when it has none."""
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped[:2] in ("* ", "- "):
            found.append(stripped[2:].strip())
        elif stripped and found:
            found[-1] += f" {stripped}"
        elif stripped:
            found.append(stripped)
    return tuple(found)


def _matches(bundle: Bundle, *, benchmark: str | None, backend: str | None) -> bool:
    manifest = bundle.manifest()
    if benchmark and manifest.benchmark != benchmark:
        return False
    return not (backend and manifest.backend != backend)


def _relative(bundle: Bundle, root: Path | None) -> str:
    if root is None:
        return bundle.root.as_posix()
    try:
        return bundle.root.relative_to(Path(root)).as_posix()
    except ValueError:
        return bundle.root.as_posix()
