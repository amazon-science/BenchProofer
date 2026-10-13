# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Artifact integrity.

Checks that the bundle is internally consistent and that nothing recorded earlier
has changed since. Every other gate reads these same files, so a bundle that fails
here makes the rest of `manifest.json` meaningless rather than merely incomplete.
"""

from __future__ import annotations

from typing import ClassVar

from ..core.verdict import Level, SkipReason, Verdict
from ..errors import BundleError, MarkerError
from ..util.digest import digest_file
from .base import Gate, GateContext
from .support import join_lines

__all__ = ["IntegrityGate"]


class IntegrityGate(Gate):
    """Verify that the bundle's files are present, parseable, and unchanged."""

    id: ClassVar[str] = "artifact.integrity"
    title: ClassVar[str] = "Artifact integrity"
    rationale: ClassVar[str] = (
        "Catches a bundle whose files were edited after they were judged, a "
        "solution whose marker regions are malformed, and a property-based test suite "
        "that names files it does not ship."
    )
    level: ClassVar[Level] = Level.STATIC
    sources: ClassVar[tuple[str, ...]] = ("../task.json",)

    def judge(self, context: GateContext) -> Verdict:
        """Compare the bundle against itself and against the manifest."""
        bundle = context.bundle
        if not bundle.exists:
            return self.undecided(SkipReason.ARTIFACT_ABSENT, f"no bundle at {bundle.root}")
        problems: list[str] = []

        try:
            solution = context.solution
        except BundleError as exc:
            return self.failed(str(exc))

        try:
            regions = context.backend.region_digests(solution)
        except MarkerError as exc:
            return self.failed(f"solution markers are malformed: {exc}")

        task = context.task
        manifest = bundle.manifest()

        if manifest.task_digest and manifest.task_digest != task.digest():
            problems.append("task.json changed since the bundle was created")

        recorded_regions = {k: v for k, v in manifest.regions.items() if k in regions}
        drifted = [name for name, value in recorded_regions.items() if regions[name] != value]
        if drifted:
            problems.append(f"region(s) changed since recording: {join_lines(drifted)}")

        stale: list[str] = []
        for relative, expected in manifest.artifacts.items():
            path = (bundle.root / relative).resolve()
            if not path.exists():
                stale.append(f"{relative} (missing)")
            elif digest_file(path) != expected:
                stale.append(relative)
        if stale:
            problems.append(f"artifact(s) changed since recording: {join_lines(stale)}")

        try:
            battery = bundle.battery()
        except BundleError as exc:
            return self.failed(f"the property-based test suite's index is unusable: {exc}")
        missing_rivals = [
            rival.id for rival in battery if not (bundle.rivals_dir / rival.file).is_file()
        ]
        if missing_rivals:
            problems.append(
                "the property-based test suite names missing file(s): "
                + join_lines(missing_rivals)
            )

        empty_twins = [name for name, source in bundle.twins() if not source.strip()]
        if empty_twins:
            problems.append(f"empty pre-fix implementation(s): {join_lines(empty_twins)}")

        if problems:
            return self.failed("; ".join(problems), problems=problems)

        if not manifest.artifacts and not manifest.regions:
            return self.passed(
                "bundle is self-consistent; this is the first recorded judgment",
                regions=sorted(regions),
                first_record=True,
            )
        return self.passed(
            f"{len(manifest.artifacts)} artifact(s) and "
            f"{len(recorded_regions)} region(s) unchanged",
            regions=sorted(regions),
        )
