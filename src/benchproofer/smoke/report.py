# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""What a smoke run produced, as a document.

The report keeps the four outcomes apart everywhere, including in the summary line,
because "38 passed" over a run that skipped nineteen cases would be a claim about
this machine that nobody checked. A run is only sound when nothing failed and
nothing errored; what it *covered* is a separate number, and both are printed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core.provenance import environment_report
from ..log import logger
from ..util.fsio import write_json, write_text
from .model import CaseResult, CaseStatus

__all__ = ["SuiteResult", "write_smoke_report"]

log = logger(__name__)


@dataclass(frozen=True, slots=True)
class SuiteResult:
    """Every case a run executed, and the machine it ran on."""

    suite: str
    results: tuple[CaseResult, ...]
    duration_s: float = 0.0
    environment: dict[str, Any] = field(default_factory=environment_report)

    @property
    def total(self) -> int:
        """How many cases the run covers, including the skipped ones."""
        return len(self.results)

    @property
    def sound(self) -> bool:
        """True when no case reported a defect and none of them errored."""
        return not self.of(CaseStatus.FAILED) and not self.of(CaseStatus.ERROR)

    def of(self, status: CaseStatus) -> tuple[CaseResult, ...]:
        """The results with one status, in the order they were produced."""
        return tuple(result for result in self.results if result.status is status)

    def counts(self) -> dict[str, int]:
        """Cases per status, with every status present even at zero."""
        counts = {str(status): 0 for status in CaseStatus}
        for result in self.results:
            counts[str(result.status)] += 1
        return counts

    def groups(self) -> dict[str, dict[str, int]]:
        """Cases per status, per group, so a gap shows up as a whole group skipped."""
        tally: dict[str, dict[str, int]] = {}
        for result in self.results:
            counts = tally.setdefault(
                result.case.group, {str(status): 0 for status in CaseStatus}
            )
            counts[str(result.status)] += 1
        return tally

    def headline(self) -> str:
        """One line naming every status, including the zeros."""
        counts = self.counts()
        parts = " ".join(f"{name}={counts[name]}" for name in counts)
        return f"{self.suite}: {self.total} cases in {self.duration_s:.1f}s ({parts})"

    def to_json(self) -> dict[str, Any]:
        """The run as a JSON-serializable document."""
        return {
            "suite": self.suite,
            "total": self.total,
            "sound": self.sound,
            "duration_s": round(self.duration_s, 3),
            "counts": self.counts(),
            "groups": self.groups(),
            "environment": self.environment,
            "cases": [
                {
                    "id": result.case.id,
                    "group": result.case.group,
                    "summary": result.case.summary,
                    "status": str(result.status),
                    "duration_s": round(result.duration_s, 3),
                    "requires": list(result.case.requires),
                    "slow": result.case.slow,
                    "message": result.message,
                    "observations": [
                        {"label": item.label, "detail": item.detail}
                        for item in result.observations
                    ],
                }
                for result in self.results
            ],
        }

    def to_markdown(self) -> str:
        """Render the run for a human reader."""
        counts = self.counts()
        lines = [
            f"# Benchproofer smoke run: {self.suite}",
            "",
            f"- cases: {self.total}",
            *(f"- {name}: {count}" for name, count in counts.items()),
            f"- wall clock: {self.duration_s:.1f}s",
            "",
            "A skipped case is not a passing case. It means this machine does not offer",
            "something the case needs, and the reason is recorded next to it.",
            "",
            "## Groups",
            "",
            "| group | " + " | ".join(str(status) for status in CaseStatus) + " |",
            "| --- | " + " | ".join("---" for _ in CaseStatus) + " |",
        ]
        groups = self.groups()
        for name in sorted(groups):
            cells = " | ".join(str(groups[name][str(status)]) for status in CaseStatus)
            lines.append(f"| {name} | {cells} |")

        lines += ["", "## Cases", ""]
        lines += ["| case | status | time | detail |", "| --- | --- | --- | --- |"]
        for result in self.results:
            lines.append(
                f"| `{result.case.id}` | {result.status} | {result.duration_s:.1f}s "
                f"| {_cell(result.detail)} |"
            )

        lines += [
            "",
            "## Environment",
            "",
            *(f"- {name}: {value}" for name, value in self.environment.items()),
            "",
        ]
        return "\n".join(lines)


def write_smoke_report(result: SuiteResult, directory: Path) -> tuple[Path, Path]:
    """Write ``smoke.json`` and ``smoke.md`` into a directory."""
    directory = Path(directory)
    document = directory / "smoke.json"
    rendered = directory / "smoke.md"
    write_json(document, result.to_json())
    write_text(rendered, result.to_markdown())
    log.info("wrote %s and %s", document, rendered)
    return document, rendered


def _cell(text: str, limit: int = 160) -> str:
    """Fit a detail into one table cell."""
    flat = " ".join(text.split()).replace("|", "\\|")
    return flat if len(flat) <= limit else f"{flat[: limit - 3]}..."
