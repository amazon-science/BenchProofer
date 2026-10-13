# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Reviewing a bundle: an audit session, written to disk.

The session decides what the review says; this module decides where it goes and what
`manifest.json` records about how it got there. The gates read the review back off disk, so
a review written some other way -- a second tool, a human filling in `audit/index.toml`
-- is judged on exactly the same terms. The reviewer is shown the bundle's frozen copy
of the task, so a review can be repeated later against the same artifacts.

A review is made of auditors -- one for the attacks and controls, one for the fuzzers, one per
judged role, and one ruling on the attacks and controls that cannot be determined by execution
-- and only the auditors whose last judgment no longer describes the bundle are asked again
(`due`). Each auditor is an agent session on the reviewing model, and a run with no session
cannot review. The attack validation auditor is asked last, once the gates have re-run what is
on record (`review`), for `run` and `benchproofer audit` alike.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

from ..audit.agents import Reviewers
from ..audit.session import (
    LANES,
    SUBMISSION_GATES,
    Audit,
    Lane,
    attack_stands,
    kept_fuzzers,
    roles_for,
    unattacked,
    unruled,
)
from ..backends.base import Backend
from ..config import Settings
from ..core import replay
from ..core.bundle import Bundle
from ..core.provenance import environment_report
from ..core.readings import SPEC, readings
from ..core.verdict import Level
from ..llm.agentic import AgentSession
from ..llm.base import Provider
from ..llm.resolve import require_session
from ..log import logger
from ..registries import BACKENDS, ORACLES
from ..util.fsio import write_text
from .adjudicate import adjudicate

__all__ = ["AuditResult", "audit", "due", "needs_review", "review", "write_audit"]

log = logger(__name__)


@dataclass(frozen=True, slots=True)
class AuditResult:
    """What one review produced."""

    task_key: str
    bundle: Bundle
    audit: Audit
    written: tuple[str, ...]

    @property
    def usable(self) -> bool:
        """True when the review filed something a gate can act on.

        A review that submitted no implementation and filed no judgment is recorded all
        the same, and the gates report the roles as unjudged. This says whether the stage
        is worth re-running, not whether the bundle is any good.
        """
        return bool(self.audit.submissions or self.audit.judgments)


def audit(
    bundle: Bundle,
    *,
    backend: Backend,
    provider: Provider,
    settings: Settings,
    lanes: Sequence[Lane] | None = None,
    session: AgentSession | None = None,
) -> AuditResult:
    """Review one bundle adversarially and write the review into it.

    ``lanes`` are the parts of the review to ask; by default, the ones `due` names.
    ``session`` is the agent session the auditors run on; by default the one the run's
    settings name, on the reviewing model.

    Raises:
        BundleError: The bundle has no solution file or no frozen task to review.
        ProviderError: The run has no agent session to review with, or the model could not
            be reached at all.
    """
    task = bundle.task()
    asked = due(bundle, backend) if lanes is None else tuple(lanes)
    session = session or require_session(
        settings, "reviewing a bundle", settings.audit_model or settings.model
    )
    review = Reviewers(
        session=session,
        provider=provider,
        backend=backend,
        settings=settings,
        oracle=ORACLES.get(task.oracle.kind),
    ).run(bundle, task, asked)
    written = write_audit(bundle, review)
    log.info(
        "reviewed %s with %s (%s): %d submission(s), %s",
        task.key,
        backend.name,
        ", ".join(asked) or "no auditor",
        len(review.submissions),
        ", ".join(f"{judgment.role}={judgment.verdict}" for judgment in review.judgments)
        or "no judgment",
    )
    return AuditResult(task_key=task.key, bundle=bundle, audit=review, written=written)


def review(
    bundle: Bundle,
    *,
    backend: Backend,
    provider: Provider,
    settings: Settings,
    level: Level = Level.AUDITED,
    again: Sequence[Lane] = (),
) -> AuditResult | None:
    """Ask the auditors `due` names, and ``again``, in the review's own order.

    Every auditor but the attack validation auditor first, in one `audit`, so an auditor asked
    again in the same review is shown what the attack auditor files in it. The attack validation
    auditor rules on what the gates made of the submissions on record, so it is asked after the
    two gates that re-run them (`SUBMISSION_GATES`) have judged what is on record, and only
    where they list attacks or controls that cannot be determined by execution and that it has
    not ruled on (`unruled`). The gates that read the review then judge those two again with its
    rulings, reading what this run of them recorded rather than running the benchmark's tests on
    a submission twice (`gates.audit`).

    Returns:
        What the review produced, the attack validation auditor's rulings and session included;
        None when no auditor was asked.

    Raises:
        ProviderError: The model could not be reached at all (`audit`).
    """
    asked = {*again, *due(bundle, backend)}
    lanes = tuple(lane for lane in LANES if lane in asked and lane != "validation")
    first = (
        audit(bundle, backend=backend, provider=provider, settings=settings, lanes=lanes)
        if lanes
        else None
    )
    if first is None and "validation" not in asked:
        return None
    adjudicate(bundle, backend=backend, settings=settings, level=level, only=SUBMISSION_GATES)
    if not unruled(bundle):
        return first
    ruled = audit(
        bundle, backend=backend, provider=provider, settings=settings, lanes=("validation",)
    )
    if first is None:
        return ruled
    return replace(
        first,
        audit=replace(
            first.audit,
            rulings=ruled.audit.rulings,
            sessions=(*first.audit.sessions, *ruled.audit.sessions),
            notes=(*first.audit.notes, *ruled.audit.notes),
        ),
        written=tuple(dict.fromkeys((*first.written, *ruled.written))),
    )


def due(bundle: Bundle, backend: Backend | None = None) -> tuple[Lane, ...]:
    """The auditors whose last judgment no longer describes this bundle.

    Every auditor but the attack validation auditor, when the bundle has no review: that one
    rules on what the gates make of a review's submissions. Otherwise the attack auditor when
    what it read changed, since an attack written to probe one specification says nothing about
    where the next one is weak; the fuzz auditor when a callee the specification assumes has no
    fuzzer written against the assumption as it now stands (`unattacked`); a judged role when
    its judgment is missing or stale; and the attack validation auditor when the gates that
    re-ran the submissions on record list attacks or controls that cannot be determined by
    execution and that it has not ruled on (`unruled`), unless the attack auditor is due, whose
    new submissions the gates have yet to run. A role this task cannot support is never due.

    ``backend`` defaults to the one the bundle was built with.
    """
    review = bundle.audit()
    if review is None:
        return tuple(lane for lane in LANES if lane != "validation")
    backend = backend or BACKENDS.get(bundle.backend_name)
    digests = readings(bundle, backend)
    solution = bundle.solution()
    lanes: list[Lane] = []
    if not attack_stands(review, digests):
        lanes.append("attack")
    if unattacked(solution, backend, kept_fuzzers(review, solution, backend)):
        lanes.append("fuzz")
    for role in roles_for(bundle.task()):
        judgment = review.judgment(role)
        if judgment is None or judgment.stale(digests):
            lanes.append(role)
    if "attack" not in lanes and unruled(bundle):
        lanes.append("validation")
    return tuple(lanes)


def needs_review(bundle: Bundle) -> bool:
    """True when some auditor of this bundle's review no longer describes it (`due`)."""
    return bool(due(bundle))


def write_audit(bundle: Bundle, review: Audit) -> tuple[str, ...]:
    """Write a review's files and record in `manifest.json` how it was produced.

    The files of an earlier submission the review no longer keeps are removed: what it
    filed is in the archive of the round that judged it (`core.rounds`), and left here it
    would read as part of this review. The input of each defect the review holds joins the
    inputs on record that every run of `conformance.py` compares (`core.replay`).

    Returns:
        The bundle-relative names of the files written, in write order.
    """
    before = bundle.audit()
    sources = review.sources()
    bundle.save_audit(review.review(), sources)
    kept = {name for item in review.on_record() for name in (item.file, item.shadow, item.test)}
    for item in before.submissions if before is not None else ():
        for name in {item.file, item.shadow, item.test} - kept - {""}:
            (bundle.audit_dir / name).unlink(missing_ok=True)
    written = [f"audit/{name}" for name in sources]
    written.append("audit/index.toml")

    spec = readings(bundle, BACKENDS.get(bundle.backend_name)).get(SPEC, "")
    found: dict[str, list[str]] = {}
    for defect in review.defects:
        found.setdefault(defect.function, []).append(defect.input)
    replay.record(bundle, found, source=replay.REVIEW, spec=spec)
    write_text(bundle.audit_dir / "notes.md", _notes(review, spec))
    written.append("audit/notes.md")

    manifest = bundle.manifest()
    manifest.provenance = {
        **manifest.provenance,
        "review": review.provenance(),
        "environment": environment_report(),
    }
    manifest.artifacts = bundle.artifact_digests()
    bundle.save_manifest(manifest)
    return tuple(written)


def _notes(review: Audit, spec: str) -> str:
    """Write the reviewer-facing account of one review; ``spec`` digests the current spec."""
    lines = [
        f"# Review of {review.task_key} ({review.backend})",
        "",
        f"- reviewer: {review.reviewer}",
        f"- bundle drafted by: {review.author or 'not recorded'}",
        f"- independent of the drafting session: {'yes' if review.independent else 'no'}",
        "",
    ]
    if review.kept or review.submissions:
        # Every submission the bundle now carries, not just this round's, since the gates
        # judge the specification against all of them.
        attacked = review.examined.get("attack", {}).get(SPEC, "")
        earlier = (
            ", filed against an earlier specification, which its claim is about"
            if attacked and spec and attacked != spec
            else ", filed by an earlier review"
        )
        lines += ["## Implementations on record", ""]
        lines += [
            f"- `{item.id}` ({item.kind}{earlier}): {item.claim or 'no claim stated'}"
            for item in review.kept
        ]
        lines += [
            f"- `{item.id}` ({item.kind}): {item.claim or 'no claim stated'}"
            for item in review.submissions
        ]
        lines.append("")
    if review.defects:
        lines += ["## Defects the attack auditor showed, handed to `conformance.py`", ""]
        lines += [
            f"- {item.defect} Input to `{item.function}`: {item.input}. The repository: "
            f"{item.repository or 'not said'}. The specification: "
            f"{item.specification or 'not said'}."
            for item in review.defects
        ]
        lines.append("")
    if review.rulings:
        lines += ["## The attack validation auditor's rulings", ""]
        lines += [
            f"- `{item.id}`: {item.ruling or 'no ruling'}"
            + (f" on the input {item.input}" if item.input else "")
            + (f", resting on {item.rests_on}" if item.rests_on else "")
            + (f". {item.why}" if item.why else "")
            for item in review.rulings
        ]
        lines.append("")
    if review.judgments:
        # Whose measurement a number in an auditor's report is. An auditor writes and runs its
        # own programs in a workspace of its own, which no gate reads, so a count it reports --
        # draws made, inputs compared -- is that program's and not that of the bundle's
        # `conformance.py` or `axioms.py`. A reader who takes it for theirs reads the bundle as
        # better evidenced than it is; what the shipped programs did is recorded where the
        # gates put it.
        lines += [
            "## What each auditor reported",
            "",
            "In each auditor's own words, about programs it wrote and ran in a workspace of",
            "its own: a count below is that auditor's scratch run. What the bundle's own",
            "`conformance.py` and `axioms.py` compared is in `manifest.json` and `evidence/`.",
            "",
        ]
    for judgment in review.judgments:
        lines += [
            f"### {judgment.role}: {judgment.verdict}",
            "",
            judgment.summary or "no summary given",
            "",
        ]
        lines += [f"- {finding}" for finding in judgment.findings]
        if judgment.findings:
            lines.append("")
        if judgment.checked:
            lines += ["Checked and found clean:", ""]
            lines += [f"- {item}" for item in judgment.checked]
            lines.append("")
    if review.notes:
        lines += [
            "## What the review had to work around",
            "",
            *(f"- {note}" for note in review.notes),
            "",
        ]
    lines += [
        "Nothing here is a verdict. Every submission is re-run through the checker and",
        "the benchmark's tests, and a judgment counts toward the gates' results only while",
        "the files it was reached from are unchanged; `manifest.json` records what the",
        "gates concluded.",
        "",
    ]
    return "\n".join(lines)
