# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Building a bundle: a formalization session, written to disk.

The session decides what the artifacts say; this module decides where they go and
what `manifest.json` records about how they got there. Keeping the two apart means the
on-disk layout is defined in one place, and a project that drafts artifacts some
other way (by hand, or with its own tooling) can still produce bundles Benchproofer
will judge.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..audit.session import admitted
from ..backends.base import Backend
from ..config import Settings
from ..core.bundle import Bundle, Rival, Twin
from ..core.provenance import environment_report
from ..core.sites import RECORD
from ..core.task import Task
from ..formalize.session import Draft, Formalization, Formalizer
from ..gates.battery import distinct
from ..llm.agentic import AgentSession
from ..llm.base import Provider
from ..llm.resolve import require_session
from ..log import logger
from ..registries import ORACLES
from ..util.fsio import write_text

__all__ = ["BuildResult", "build", "rival_entry", "twin_entry", "write_formalization"]

log = logger(__name__)


@dataclass(frozen=True, slots=True)
class BuildResult:
    """What one build produced."""

    task_key: str
    bundle: Bundle
    formalization: Formalization
    written: tuple[str, ...]

    @property
    def usable(self) -> bool:
        """True when a solution file reached the bundle, accepted or not."""
        return any(name.startswith("solution.") for name in self.written)


def build(
    task: Task,
    *,
    backend: Backend,
    provider: Provider,
    settings: Settings,
    session: AgentSession | None = None,
) -> BuildResult:
    """Formalize one task and write the result into its bundle.

    A solution the checker rejected is written all the same. The bundle then fails
    ``spec.verifies``, which is the record Benchproofer is for: a task nobody could
    formalize with this backend, rather than a gap in the output.

    ``session`` is the agent session the stages that need one use; by default the one the
    run's settings name (`require_session`).

    Raises:
        ProviderError: The run has no agent session to draft the solution with, or the
            model could not be reached at all.
    """
    drafting = session or require_session(settings, "drafting the solution")
    bundle = Bundle.create(settings.bundle_root, task, backend.name)
    formalizer = Formalizer(
        provider=provider,
        backend=backend,
        settings=settings,
        workdir=bundle.scratch(settings.cache_dir, "formalize"),
        session=drafting,
        # Resolved here rather than passed in, because it is a fact about the task rather
        # than a choice a caller makes: which environment the task declares.
        oracle=ORACLES.get(task.oracle.kind),
    )
    formalization = formalizer.run(task)
    written = write_formalization(bundle, backend, formalization)
    # What the review sets every later repair against (`audit.session.added_block`), and
    # what the task's patches define or edit, which every stage after this one reads.
    manifest = bundle.manifest()
    manifest.provenance = {
        **manifest.provenance,
        "drafted": admitted(bundle, backend),
        RECORD: formalizer.record(task),
    }
    bundle.save_manifest(manifest)
    log.info(
        "built %s with %s: %s (%d artifact(s))",
        task.key,
        backend.name,
        "accepted" if formalization.accepted else str(formalization.check.status),
        len(written),
    )
    return BuildResult(
        task_key=task.key,
        bundle=bundle,
        formalization=formalization,
        written=written,
    )


def write_formalization(
    bundle: Bundle, backend: Backend, formalization: Formalization
) -> tuple[str, ...]:
    """Write a formalization's artifacts and update the bundle's `manifest.json`.

    Returns:
        The bundle-relative names of the files written, in write order.
    """
    written: list[str] = []
    if not formalization.solution.strip():
        # Nothing to judge, so the notes are all a reviewer gets: what the session was
        # asked, how many rounds it took, and what went wrong in each of them. A run
        # that gives up on a task points at them, so they have to be there.
        write_text(bundle.notes_path, _notes(formalization, written))
        _record(bundle, formalization, regions={})
        return (bundle.notes_path.name,)

    solution = bundle.root / backend.solution_filename()
    write_text(solution, formalization.solution)
    written.append(solution.name)
    _clear(bundle, formalization)

    twins = [
        (twin_entry(draft, backend.extension), draft.source) for draft in formalization.twins
    ]
    bundle.save_twins(twins)
    written.extend(f"twins/{twin.file}" for twin, _ in twins)
    if bundle.twins_index.exists():
        written.append(f"twins/{bundle.twins_index.name}")

    drafted = [
        (rival_entry(draft, backend.extension), draft.source) for draft in formalization.rivals
    ]
    cases = distinct(
        formalization.solution,
        [draft.source for draft in formalization.twins],
        drafted,
        backend,
    )
    shipped = {rival.id for rival, _ in cases}
    if left := [rival.id for rival, _ in drafted if rival.id not in shipped]:
        log.info(
            "%s: left out of the property-based test suite, each repeating another of the "
            "bundle's files: %s",
            formalization.task_key,
            ", ".join(left),
        )
    if cases:
        bundle.save_battery(cases)
        written.extend(f"rivals/{rival.file}" for rival, _ in cases)
        written.append("rivals/index.toml")

    if formalization.correspondence.strip():
        write_text(bundle.correspondence_path, formalization.correspondence)
        written.append(bundle.correspondence_path.name)

    if formalization.conformance.strip():
        write_text(bundle.conformance_path, formalization.conformance)
        written.append(bundle.conformance_path.name)

    if formalization.axioms.strip():
        write_text(bundle.axioms_path, formalization.axioms)
        written.append(bundle.axioms_path.name)

    write_text(bundle.notes_path, _notes(formalization, written))
    written.append(bundle.notes_path.name)

    _record(bundle, formalization, regions=backend.region_digests(formalization.solution))
    return tuple(written)


def _clear(bundle: Bundle, formalization: Formalization) -> None:
    """Remove what an earlier formalization drafted and this one did not.

    Every one of these artifacts is about the specification just written, so one left from
    before is about a specification the bundle no longer has: an `axioms.py` for axioms the new
    file does not assume, a pre-fix implementation or rival spliced into the old spec.
    """
    for directory in (bundle.twins_dir, bundle.rivals_dir):
        if directory.is_dir():
            for path in directory.iterdir():
                if path.is_file():
                    path.unlink()
    for path, drafted in (
        (bundle.correspondence_path, formalization.correspondence),
        (bundle.conformance_path, formalization.conformance),
        (bundle.axioms_path, formalization.axioms),
    ):
        if not drafted.strip():
            path.unlink(missing_ok=True)


def twin_entry(draft: Draft, extension: str) -> Twin:
    """Describe one pre-fix implementation for `twins/index.toml`."""
    return Twin(
        id=draft.id,
        file=f"{draft.id}{extension}",
        rationale=draft.rationale,
        witness=draft.witness,
        proof_session=draft.proof_session,
        found=draft.found,
    )


def rival_entry(draft: Draft, extension: str) -> Rival:
    """Describe one rival for `rivals/index.toml`."""
    return Rival(
        id=draft.id,
        kind=draft.kind,  # type: ignore[arg-type]
        expect=draft.expectation,  # type: ignore[arg-type]
        file=f"{draft.id}{extension}",
        rationale=draft.rationale,
        witness=draft.witness,
        proof_session=draft.proof_session,
        found=draft.found,
    )


def _record(bundle: Bundle, formalization: Formalization, *, regions: dict[str, str]) -> None:
    """Update the manifest with how this bundle was produced.

    Verdicts already in `manifest.json` are preserved. They are about the artifacts that
    were there before, so `artifact.integrity` is what notices that they are stale,
    rather than this function quietly discarding the evidence.
    """
    manifest = bundle.manifest()
    manifest.tool_version = environment_report()["tool_version"]
    manifest.regions = regions
    manifest.provenance = {
        **manifest.provenance,
        "formalization": formalization.provenance(),
        "environment": environment_report(),
    }
    manifest.artifacts = bundle.artifact_digests()
    bundle.save_manifest(manifest)


def _notes(formalization: Formalization, written: list[str]) -> str:
    """Write the account of how the session drafted the artifacts.

    Only what the session alone knows: the property-based test suite is in `rivals/index.toml`
    and the rounds in the manifest, where they are kept up to date.
    """
    lines = [
        f"# How {formalization.task_key} ({formalization.backend}) was drafted",
        "",
        f"- checker, on the drafted solution: {formalization.check.status}"
        + (f" ({formalization.check.detail})" if formalization.check.detail else ""),
        f"- provider: {formalization.provider}"
        + (f", model {formalization.model}" if formalization.model else ""),
        f"- artifacts: {', '.join(written) or 'none'}",
        "",
    ]
    if formalization.notes:
        lines += [
            "## What the session had to work around",
            "",
            *(f"- {note}" for note in formalization.notes),
            "",
        ]
    return "\n".join(lines)
