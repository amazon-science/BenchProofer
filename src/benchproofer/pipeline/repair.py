# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Repairing a bundle the gates would not certify.

A repair by an agent session edits the bundle as it stands, as `verified-swebench`'s
construct agent owns every file it wrote. The session may change every artifact the author
drafted -- the solution, the pre-fix implementation, the property-based test suite,
`correspondence.md`, `conformance.py` and `axioms.py` -- and nothing the review or the gates
wrote. It addresses every failing verdict, one that finds a case of the property-based test
suite or the pre-fix implementation defective as a case included, which it resolves by fixing
the case, never the specification. What it leaves is the bundle: its cases are spliced into
the specification it left (`_carried`), and nothing is drafted after it, so a file it leaves
missing fails its gate and goes to the next repair. A repair needs an agent session, and a run
with none raises.

Four rules keep a repair from being a way out:

* **The next review attacks what the repair leaves.** A repair that changes the
  specification is reviewed afresh: the attack auditor writes new attacks against it, the
  ones the gates ruled a weakness written again first (`audit.agents`), so a repair that
  addresses a finding by moving the weakness is found again.
* **Judgments expire with what they read.** A judgment records the digests of what it was
  reached from, so a repair that changed one of those needs a fresh review of it; one that
  changed only a proof leaves every judgment current.
* **What measures the specification is judged again.** Every case and pre-fix implementation
  is taken as the session left it, removals included, and their gates judge what is left:
  `spec.discriminates` fails a bundle with no pre-fix implementation, and
  `spec.strength.battery` one that lost a case its last verdict did not find defective as a
  case. `conformance.py` and `axioms.py` the session changed are taken as it left them: their
  gates run them again, and the review reads them.
* **A narrowing is found where it can be.** A repair that shuts out inputs the
  specification admitted is not taken on its report's word, nor refused on it: the gates
  judge what it left. `impl.conformance` hands `conformance.py` every input on record and
  refuses one a run drew that the program declares inadmissible without naming an `Outside
  the bridge` entry, and the next review holds each precondition and entry a repair added to
  the domain rule.

A repair addresses the verdicts `pipeline.route` sends to it.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, TypeVar

from ..backends.base import Backend
from ..config import Settings
from ..core import replay, sites
from ..core.axioms import callees, declared
from ..core.bundle import Bundle, Manifest, Rival, Twin
from ..core.differential import HARNESS
from ..core.markers import ELIDED_REGIONS, named, parse, transplant
from ..core.material import changes, has_pre_fix
from ..core.rounds import (
    ADDRESSING,
    NOT_REACHED,
    RECORD,
    archived,
    briefed,
    details,
    eligible,
    inputs_rules,
    outcome,
    outline,
    repaired,
    reported,
    sentence,
    since,
)
from ..core.scripts import SCRATCH, lay_out, script
from ..core.verdict import Level, Status, Verdict
from ..errors import BenchproofError
from ..formalize.session import AUTHORED, REVIEWED, TWIN, Draft, Formalizer
from ..gates.audit import SpecCompletenessGate, SpecSoundnessGate
from ..gates.battery import BatteryGate
from ..gates.verifies import VerifiesGate
from ..llm.agentic import AgentSession, StepOutcome
from ..llm.null import NullProvider
from ..llm.resolve import require_session
from ..log import logger
from ..registries import GATES, ORACLES
from ..util.fsio import read_text, read_text_or_empty, write_text
from .adjudicate import DISQUALIFYING, GATE_ORDER, required_gates
from .build import rival_entry, twin_entry

__all__ = ["RepairResult", "as_submitted", "chronicle", "repair"]

log = logger(__name__)

#: A case of the property-based test suite or a pre-fix implementation, as the bundle records
#: either.
_Case = TypeVar("_Case", Rival, Twin)
#: How much the repair record keeps, as a diff, of what a session whose work was not taken
#: left, and how many such sessions in a row the next one is told of, the last ones.
LEFT_CHARS = 6_000
RECALL = 4


@dataclass(frozen=True, slots=True)
class RepairResult:
    """What one repair produced: the files it wrote, and what its session reported."""

    task_key: str
    bundle: Bundle
    written: tuple[str, ...]
    #: The status the session reported, `REPAIRED`, `NO-REPAIR-NEEDED` or `BLOCKED`; empty
    #: for a session that filed no report.
    status: str = ""

    @property
    def changed(self) -> bool:
        """True when the repair wrote anything to the bundle."""
        return bool(self.written)


def _numbered(
    bundle: Bundle, verdicts: Sequence[Verdict]
) -> list[tuple[Verdict, list[tuple[str, str]]]]:
    """Each verdict in gate order, its findings numbered as a brief and `round.md` show them.

    A verdict is numbered by its gate's place in the order the gates run (`GATE_ORDER`), so a
    gate keeps its number in every list of a round's verdicts, whichever of them the list
    holds. A verdict that lists findings beneath its summary (`core.rounds.details`), or the
    review's submissions it names (`_submitted`), numbers them after its own number, `12.1`,
    `12.2`, in the order it lists them, and its summary is their heading; one that lists none
    is a finding of its own, its summary line.
    """
    order = {gate: index for index, gate in enumerate(GATE_ORDER, 1)}
    unknown = sorted({verdict.gate for verdict in verdicts} - order.keys())
    order |= {gate: len(GATE_ORDER) + index for index, gate in enumerate(unknown, 1)}
    numbered: list[tuple[Verdict, list[tuple[str, str]]]] = []
    for verdict in sorted(verdicts, key=lambda verdict: order[verdict.gate]):
        number = str(order[verdict.gate])
        listed = details(verdict) + _submitted(bundle, verdict)
        numbered.append(
            (
                verdict,
                [(f"{number}.{index}", text) for index, text in enumerate(listed, 1)]
                or [(number, _summary(verdict))],
            )
        )
    return numbered


def _submitted(bundle: Bundle, verdict: Verdict) -> list[str]:
    """Each of the review's submissions ``verdict`` names as wrongly accepted or refused.

    With its file and equivalent patch under `audit/`, the reviewer's statement of what it
    shows and what the gates ruled, so that a repair addressing it need not search the
    review's index for them.
    """
    if verdict.gate not in (SpecCompletenessGate.id, SpecSoundnessGate.id):
        return []
    named = [
        str(name)
        for key in ("too_weak", "too_strong")
        for name in verdict.details.get(key) or ()
    ]
    try:
        review = bundle.audit()
    except BenchproofError:
        review = None
    filed = {item.id: item for item in review.submissions} if review is not None else {}
    found = verdict.details.get("rulings")
    rulings: dict[str, Any] = found if isinstance(found, dict) else {}
    lines: list[str] = []
    for name in named:
        item = filed.get(name)
        if item is None:
            lines.append(f"`{name}`")
            continue
        files = f"`audit/{item.file}`" + (
            f", its equivalent patch `audit/{item.shadow}`" if item.shadow else ""
        )
        lines.append(
            f"`{name}` ({files}): {item.claim or 'no statement filed'}"
            + (f" The gates ruled: {rulings[name]}." if rulings.get(name) else "")
        )
    return lines


def _summary(verdict: Verdict) -> str:
    """A verdict's line in a brief: its gate, the gate's title, its status and its summary."""
    return f"`{verdict.gate}`{_beside(verdict.gate)} ({verdict.status}): {verdict.summary}"


def _briefed(bundle: Bundle, verdicts: list[Verdict]) -> tuple[list[str], dict[str, str]]:
    """The findings a repair session is briefed with, numbered for its report to address.

    Numbered by `_numbered`, which `round.md` is numbered by too. A verdict holding a finding
    the last session did not reach (`_left_open`) comes first.

    Returns:
        One entry per verdict, with its findings beneath it; and the text of each numbered
        finding by its number, which the repair record keeps beside the report.
    """
    unreached = _left_open(bundle)
    found = sorted(
        _numbered(bundle, verdicts),
        key=lambda item: not unreached.intersection(text for _, text in item[1]),
    )
    shown: list[str] = []
    texts: dict[str, str] = {}
    for verdict, findings in found:
        texts.update(findings)
        if "." not in findings[0][0]:
            shown.append(f"({findings[0][0]}) {findings[0][1]}")
            continue
        shown.append(
            "\n".join(
                [_summary(verdict), *(f"  * ({number}) {text}" for number, text in findings)]
            )
        )
    return shown, texts


def _left_open(bundle: Bundle) -> set[str]:
    """The findings the last round's repair session was briefed with and did not reach.

    Read off the repair record: the findings it was briefed with, and its report's entry for
    each. One it resolved or found no defect is not left open, where the round's work was
    taken: the review judges a resolution and a decline alike.
    """
    rounds = bundle.manifest().provenance.get("repairs")
    last = rounds[-1] if isinstance(rounds, list) and rounds else None
    session = last.get("session") if isinstance(last, dict) else None
    if not isinstance(session, dict):
        return set()
    entries = {} if "refused" in session else reported(session)
    return {
        text
        for number, text in briefed(session).items()
        if outcome(entries.get(number)) == NOT_REACHED
    }


def _beside(gate_id: str) -> str:
    """What a repair brief prints after a gate's id: the gate's title.

    A gate's title is the paper's name for it where the paper names it. The id alone is what
    Benchproofer and the bundle's manifest use, and it says little to a reader who has not
    seen the gate's code. Empty for a gate that is not registered or has no title.
    """
    try:
        title = GATES.get(gate_id).title
    except BenchproofError:
        return ""
    return f" -- {title}" if title else ""


def chronicle(
    bundle: Bundle,
    name: str,
    verdicts: dict[str, Verdict],
    earlier: list[tuple[str, Manifest]],
    again: Sequence[str],
) -> str:
    """The record of one round, `round.md`: what produced its bundle, and what did not pass.

    ``earlier`` is the rounds before it, by name and manifest (`core.rounds.archived`), and
    ``again`` the auditors it asked again, for a round no repair came before. What did
    not pass is numbered as a repair session's brief numbers it (`_numbered`).
    """
    previous, manifest = earlier[-1] if earlier else ("", None)
    entries = since(manifest, bundle.manifest())
    if not earlier:
        then = f", then {len(entries)} repair(s) of an earlier run" if entries else ""
        produced = f"Drafting{then}: this is the bundle the run began with."
    elif entries:
        produced = "\n".join(
            f"* After round {previous}, {head}: {did}" for head, did in map(repaired, entries)
        )
    else:
        lanes = ", ".join(f"`{lane}`" for lane in again) or "its auditors"
        produced = (
            f"No repair: this round asked the review again about the bundle round {previous} "
            f"judged ({lanes}), since what it last submitted showed too little."
        )
    shown, _ = _briefed(bundle, [verdict for verdict in verdicts.values() if not verdict.ok])
    failing = "\n".join(f"* {entry}" for entry in shown) or "Every gate it judged passed."
    return (
        f"# Round {name}\n\n## What produced this bundle\n\n{produced}\n\n"
        f"## What did not pass\n\n{failing}\n"
    )


def _history(earlier: Path) -> str:
    """The repair prompt's account of the rounds before the last one kept in ``earlier``.

    One entry per round, oldest first: each gate that did not pass with the first sentence
    of each of its findings (`core.rounds.outline`), then the first sentence of what the
    repair after it did. The last round is the one the session's findings come from, and
    with no round before it this is empty.
    """
    kept = archived(earlier)
    lines: list[str] = []
    for (name, manifest), (after, later) in pairwise(kept):
        lines.append(f"* Round {name} (`{earlier.name}/{name}/{RECORD}` has it in full):")
        lines += [f"  {line}" for line in outline(manifest.verdicts.values())]
        lines += [
            f"  * Then {head}: {sentence(did)}"
            for head, did in map(repaired, since(manifest, later))
        ] or [f"  * Then no repair: round {after} asked the review again."]
    if not lines:
        return ""
    return (
        "## What earlier rounds found\n\n"
        "The rounds of this run before the one these findings are from, oldest first: each "
        "gate that did not pass, with the first sentence of each of its findings, and what "
        "the repair after the round did.\n\n" + "\n".join(lines) + "\n\n"
    )


def repair(
    bundle: Bundle,
    *,
    backend: Backend,
    settings: Settings,
    verdicts: list[Verdict],
    history: Path | None = None,
    session: AgentSession | None = None,
) -> RepairResult:
    """Repair one bundle's artifacts to address what its gates found.

    An agent session edits a copy of the bundle, laid out as a bundle root so the tool's
    own `check` runs on it, beside this run's earlier rounds, whose findings its request
    lists one line each (`_history`), and a copy of the repository. Its request carries the
    rules of each file beside the solution the bundle lacks or the findings are about
    (`_wanted`), since nothing is drafted after it, and the unchanged callees those rounds let
    it take the result of as an input (`core.rounds.eligible`). The author's files it left
    in the copy are written into the bundle, its cases spliced into the specification it left
    (`_carried`); the calling loop judges the result. The previous artifacts are
    overwritten: a bundle is the current state of one formalization, and a rejected draft
    kept beside a repaired one could be shipped in place of the file that certified.

    What the session left is taken whether or not it filed a report, unless it left a
    solution file that cannot be read (`_unreadable`) or changed nothing a repair may change.
    The repair record (`provenance.repairs` in `manifest.json`) records what was repaired and
    why, keeps what a refused session left (`_left`), and the next session is told why it was
    refused and what it did (`_not_taken`).

    Args:
        bundle: The bundle to repair, which is modified in place.
        backend: The backend it was built with.
        settings: Budgets and thresholds.
        verdicts: The unfavorable verdicts to address: those `pipeline.route` sends to a
            repair.
        history: This run's earlier rounds of the bundle, one directory each, for the
            repair session to read.
        session: The agent session the repair uses; by default the one the run's settings
            name (`require_session`).

    Raises:
        BundleError: The bundle has no solution file or no frozen task.
        ProviderError: The session could not be started, or the run has none.
    """
    task = bundle.task()
    formalizer = Formalizer(
        # A repair sends no single request, so its formalizer is given the provider that
        # declines every request.
        provider=NullProvider(),
        backend=backend,
        settings=settings,
        workdir=bundle.scratch(settings.cache_dir, "repair"),
        session=session or require_session(settings, "repairing a bundle"),
        oracle=ORACLES.get(task.oracle.kind),
        changed=sites.changed(task, bundle.manifest().provenance.get(sites.RECORD)),
    )
    workspace = bundle.scratch(settings.cache_dir, "agent-repair")
    copy = lay_out(workspace, task, backend.name, settings)
    shutil.copytree(bundle.root, copy.root, dirs_exist_ok=True)
    rounds = workspace / "rounds"
    if history is not None and history.is_dir():
        shutil.copytree(history, rounds)
    else:
        rounds.mkdir()
    _lanes(bundle.scratch(settings.cache_dir, "review"), workspace / REVIEWED)
    checker = _checker(workspace, task.benchmark, task.task_id, backend, settings)
    # Every gate a program decides but the task's own check, which nothing the session does
    # changes, so what the session reports on is what the next round's gates will find.
    check = " ".join(
        [
            checker,
            *(
                f"--only {gate}"
                for gate in required_gates(Level.ORACLE)
                if gate not in DISQUALIFYING
            ),
        ]
    )
    addressing = [verdict.gate for verdict in verdicts]
    shown, texts = _briefed(bundle, verdicts)
    lacking = _lacking(bundle, backend)
    outcome = formalizer.repair_by_agent(
        task,
        workspace=workspace,
        bundle=copy.root,
        rounds=rounds,
        history=_history(rounds),
        scratch=workspace / SCRATCH,
        failing=shown,
        check=check,
        refused=_not_taken(bundle),
        checked=_checked(bundle, backend),
        on_record=_on_record(bundle),
        artifacts=_wanted(lacking, verdicts, shown),
        lacking=lacking,
        inputs_rules=inputs_rules(eligible(rounds, backend)),
    )
    status = str((outcome.payload or {}).get("status") or "")
    drafted = copy.root / backend.solution_filename()
    after = read_text(drafted) if drafted.is_file() else bundle.solution()
    edited = _edited(bundle, copy)
    record = _session_record(outcome, edited=edited, brief=texts)
    refusal = _unreadable(after, backend)
    if refusal or not edited:
        reason = refusal or "the session changed nothing a repair may change"
        record = {**record, "refused": reason, "left": _left(bundle, copy, backend, after)}
        log.info("the repair session for %s left the bundle as it was: %s", task.key, reason)
        _record_unchanged(bundle, addressing=addressing, session=record)
        return RepairResult(task_key=task.key, bundle=bundle, written=(), status=status)
    twins, rivals = _carried(copy, backend, solution=after, given=bundle)
    written = _written(bundle, copy, backend, solution=after, twins=twins, rivals=rivals)
    _record(bundle, backend, addressing=addressing, session=record)
    log.info(
        "repaired %s by a session (%s): %d artifact(s)",
        task.key,
        status or "no status",
        len(written),
    )
    return RepairResult(task_key=task.key, bundle=bundle, written=written, status=status)


#: The gates whose verdicts are about each file beside the solution, so that a repair
#: addressing one is given that file's rules (`_wanted`).
OWNERS: dict[str, tuple[str, ...]] = {
    "twins": ("spec.discriminates",),
    "rivals": (BatteryGate.id,),
    "correspondence.md": ("audit.equivalence",),
    HARNESS: ("impl.conformance",),
    "axioms.py": ("spec.axioms_grounded", "audit.axiom_soundness"),
}


def _lacking(bundle: Bundle, backend: Backend) -> list[str]:
    """The files beside the solution the bundle needs and does not have, in `AUTHORED` order.

    A pre-fix implementation where the task ships code the fix replaced, a property-based
    test suite, `correspondence.md`, `conformance.py` where the task has a golden patch, and
    `axioms.py` where the `axioms` region names a callee: what the gates that own them fail
    a bundle for lacking, and what drafting writes once the checker accepts the solution.
    """
    task = bundle.task()
    try:
        region = parse(bundle.solution(), backend.comment).get("axioms")
    except BenchproofError:
        region = None
    needed = {
        "twins": has_pre_fix(task) and not bundle.twins(),
        "rivals": not bundle.rivals_dir.joinpath("index.toml").is_file(),
        "correspondence.md": not bundle.correspondence_path.is_file(),
        HARNESS: not task.reference.is_empty and not bundle.conformance_path.is_file(),
        "axioms.py": region is not None
        and bool(callees(declared(region.text, backend.comment)))
        and not bundle.axioms_path.is_file(),
    }
    return [name for name in AUTHORED if needed[name]]


def _wanted(
    lacking: Sequence[str], verdicts: Sequence[Verdict], shown: Sequence[str]
) -> list[str]:
    """The files beside the solution whose rules a repair's request gives, in `AUTHORED` order.

    Those the bundle lacks, and those the findings are about: by the gate that found them
    (`OWNERS`), or by a finding that names the file.
    """
    gates = {verdict.gate for verdict in verdicts}
    text = "\n".join(shown)
    return [
        name
        for name in AUTHORED
        if name in lacking
        or gates.intersection(OWNERS[name])
        or (f"{name}/" if name in ("twins", "rivals") else name) in text
    ]


def _authored(bundle: Bundle) -> dict[str, str]:
    """Every file of the author's in a bundle, by bundle-relative name."""
    found = {path.name: read_text(path) for path in sorted(bundle.root.glob("solution.*"))}
    for name in AUTHORED:
        path = bundle.root / name
        if path.is_dir():
            for member in sorted(path.iterdir()):
                if member.is_file():
                    found[f"{name}/{member.name}"] = read_text(member)
        elif path.is_file():
            found[name] = read_text(path)
    return found


def _edited(bundle: Bundle, copy: Bundle) -> list[str]:
    """The author's files the session changed, added or removed, by bundle-relative name."""
    mine, theirs = _authored(bundle), _authored(copy)
    return sorted(
        name for name in mine.keys() | theirs.keys() if mine.get(name) != theirs.get(name)
    )


def _carried(
    copy: Bundle, backend: Backend, *, solution: str, given: Bundle
) -> tuple[list[Draft] | None, list[Draft] | None]:
    """The pre-fix implementations and cases the session left in ``copy``, in ``solution``.

    Each as the session left it, with the rationale and witness its index records, spliced
    into the repaired specification; one that does not splice into it is carried as the
    session left it, for its gate to judge. One it removed stays removed: `spec.discriminates`
    fails a bundle left with no pre-fix implementation, and `spec.strength.battery` one that
    lost a case its last verdict did not find defective as a case. ``given`` is the bundle the
    session was given, whose index says which rationales the session rewrote (`_rewritten`).

    Returns:
        The pre-fix implementations and the cases, either None where the index the session
        left cannot be read: that directory is then written as it left it, for its gate to
        report.
    """
    twins: list[Draft] | None
    try:
        records = _rewritten(
            copy.twin_cases(), copy.twin_cases(as_written=True), _recorded(given.twin_cases)
        )
    except BenchproofError:
        twins = None
    else:
        twins = [
            Draft(
                id=name,
                kind=TWIN,
                rationale=records[name].rationale,
                source=_spliced(solution, source, backend) or source,
                witness=records[name].witness,
            )
            for name, source in copy.twins()
        ]
    rivals: list[Draft] | None
    try:
        written = _rewritten(
            {rival.id: rival for rival in copy.battery()},
            {rival.id: rival for rival in copy.battery(as_written=True)},
            _recorded(lambda: {rival.id: rival for rival in given.battery()}),
        )
    except BenchproofError:
        rivals = None
    else:
        rivals = []
        for rival in written.values():
            try:
                source = copy.rival_source(rival)
            except BenchproofError:
                continue
            rivals.append(
                Draft(
                    id=rival.id,
                    kind=rival.kind,
                    rationale=rival.rationale,
                    source=_spliced(solution, source, backend) or source,
                    witness=rival.witness,
                )
            )
    return twins, rivals


def _recorded(read: Callable[[], dict[str, _Case]]) -> dict[str, _Case]:
    """What the bundle given to the session records of its cases, by ``read``.

    Nothing where its index cannot be read, so that no rationale of the session's is mistaken
    for the bundle's.
    """
    try:
        return read()
    except BenchproofError:
        return {}


def _written(
    bundle: Bundle,
    copy: Bundle,
    backend: Backend,
    *,
    solution: str,
    twins: Sequence[Draft] | None,
    rivals: Sequence[Draft] | None,
) -> tuple[str, ...]:
    """Write what the session left into ``bundle``, and name what was written.

    The solution, the pre-fix implementations and the cases ``_carried`` made of what it
    left -- or, where it left an index that cannot be read, that directory as it left it --
    and `correspondence.md`, `conformance.py` and `axioms.py` as it left them: one it
    removed is removed, and its gate fails the bundle for lacking it.
    """
    path = bundle.root / backend.solution_filename()
    write_text(path, solution)
    written = [path.name]
    if twins is None:
        written += _as_left(copy, bundle, "twins")
    else:
        bundle.save_twins(
            [(twin_entry(draft, backend.extension), draft.source) for draft in twins]
        )
        written += [f"twins/{twin.id}{backend.extension}" for twin in twins]
        if bundle.twins_index.is_file():
            written.append(f"twins/{bundle.twins_index.name}")
    if rivals is None:
        written += _as_left(copy, bundle, "rivals")
    else:
        _emptied(bundle.rivals_dir)
        if rivals:
            bundle.save_battery(
                [(rival_entry(draft, backend.extension), draft.source) for draft in rivals]
            )
            written += [f"rivals/{rival.id}{backend.extension}" for rival in rivals]
            written.append("rivals/index.toml")
    for name in ("correspondence.md", HARNESS, "axioms.py"):
        left = copy.root / name
        if left.is_file():
            write_text(bundle.root / name, read_text(left))
            written.append(name)
        else:
            (bundle.root / name).unlink(missing_ok=True)
    return tuple(written)


def _as_left(copy: Bundle, bundle: Bundle, directory: str) -> list[str]:
    """Make ``bundle``'s ``directory`` hold the files ``copy``'s holds, and name them."""
    source = copy.root / directory
    left = (
        {path.name: read_text(path) for path in sorted(source.iterdir()) if path.is_file()}
        if source.is_dir()
        else {}
    )
    _emptied(bundle.root / directory)
    for name, text in left.items():
        write_text(bundle.root / directory / name, text)
    return [f"{directory}/{name}" for name in left]


def _emptied(directory: Path) -> None:
    """Remove every file of ``directory``."""
    for path in directory.iterdir() if directory.is_dir() else ():
        if path.is_file():
            path.unlink()


def _rewritten(
    read: dict[str, _Case], written: dict[str, _Case], given: dict[str, _Case]
) -> dict[str, _Case]:
    """The cases the session left, each with the rationale it wrote where it wrote one.

    ``read`` is the session's index as a gate reads it, where a rationale the case's file no
    longer bears is replaced (`core.bundle`); ``written`` the same index as the session
    wrote it; ``given`` the bundle's record. A rationale that differs from the one the
    bundle gave the case is the session's own, about the file it left, so it stands.
    """
    return {
        name: (
            written[name]
            if name in written
            and (name not in given or written[name].rationale != given[name].rationale)
            else case
        )
        for name, case in read.items()
    }


def as_submitted(bundle: Bundle, backend: Backend, into: Path) -> Bundle:
    """A copy of ``bundle`` laid out as `repair` lays out what a session left, to judge early.

    `repair` splices each pre-fix implementation and case of the property-based test suite
    into the solution the session left, and records that solution's regions and the bundle's
    digests afterwards. So a bundle whose solution has been edited beside cases that still carry
    the one it replaced fails `artifact.integrity`, and reads as drifted to every gate that asks
    whether a case carries the shipped specification -- although none of what it says is wrong,
    and `repair` would clear all of it. This does to a copy what `repair` does, so that a run
    of the gates part way through an edit asks what the gates will ask of the repaired bundle.
    `conformance.py` and `axioms.py` are judged as they are, since `repair` leaves them so.

    Args:
        bundle: The bundle to copy, which is not modified.
        backend: The backend it was built with.
        into: A bundle root to create the copy under.
    """
    copy = Bundle.create(into, bundle.task(), bundle.backend_name)
    shutil.copytree(bundle.root, copy.root, dirs_exist_ok=True)
    solution = bundle.solution()
    for directory in (copy.twins_dir, copy.rivals_dir):
        for path in sorted(directory.iterdir()) if directory.is_dir() else ():
            if path.suffix != backend.extension:
                continue
            spliced = _spliced(solution, read_text(path), backend)
            if spliced is not None:
                write_text(path, spliced)
    _restamp(copy, backend, copy.manifest())
    return copy


def _spliced(solution: str, source: str, backend: Backend) -> str | None:
    """``solution`` carrying ``source``'s implementation and, where it has one, its proof.

    The proof goes with the implementation it is about: under a prover, a file with one
    implementation and another's proof is refused whatever the specification says. None
    when either file's markers cannot be read.
    """
    try:
        for kind in ELIDED_REGIONS:
            if named(parse(source, backend.comment), kind):
                solution = transplant(solution, source, backend.comment, kind)
    except BenchproofError:
        return None
    return solution


def _lanes(review: Path, into: Path) -> None:
    """Copy what each auditor left in its workspace's `scratch/` into ``into``, by auditor.

    An auditor's findings cite the files it wrote there, and a repair reads them as evidence.
    """
    for lane in sorted(review.iterdir()) if review.is_dir() else ():
        left = lane / SCRATCH
        if left.is_dir() and any(left.iterdir()):
            shutil.copytree(left, into / lane.name / SCRATCH, symlinks=True)


def _on_record(bundle: Bundle) -> tuple[str, ...]:
    """The functions the bundle has inputs on record for, by the name they are handed under."""
    return tuple(replay.by_function(replay.stored(bundle)))


def _checker(
    workspace: Path, benchmark: str, task_id: str, backend: Backend, settings: Settings
) -> str:
    """Write the script a repair session judges its copy of the bundle with, and name it."""
    return script(
        workspace / "check",
        [
            "benchproofer",
            "check",
            benchmark,
            "--backend",
            backend.name,
            "--bundle-root",
            (workspace / "bundles").as_posix(),
            "--id",
            task_id,
            # So the session's own run of the gates asks what the gates will ask of what it
            # leaves, rather than reporting the drift of an edit not yet carried through.
            "--as-submitted",
        ],
        settings,
        # The gates that run the repository's code too, as a round's own judgment does, and
        # not the review's: after the session's own arguments, so none of them changes it.
        pinned=["--level", str(Level.ORACLE)],
    )


def _unreadable(solution: str, backend: Backend) -> str:
    """Why the solution file a session left cannot be judged, or "" when it can.

    A file whose region markers cannot be read gives the gates nothing to judge, so the bundle
    is left as it was.
    """
    try:
        parse(solution, backend.comment)
    except BenchproofError as exc:
        return f"the repaired solution cannot be read: {exc}"
    return ""


def _left(bundle: Bundle, copy: Bundle, backend: Backend, solution: str) -> str:
    """What a session left of the specification, the type bridge and the programs, as a diff.

    ``solution`` is the solution file it left. Its workspace goes when the next session's
    is laid out, so for a session whose work was not taken this is the record of what it did.
    """
    return changes(
        [
            ("specification", _view(bundle.solution(), backend), _view(solution, backend)),
            *(
                (
                    name,
                    read_text_or_empty(bundle.root / name),
                    read_text_or_empty(copy.root / name),
                )
                for name in ("correspondence.md", HARNESS, "axioms.py")
            ),
        ],
        LEFT_CHARS,
        before="given",
        after="left",
    )


def _view(solution: str, backend: Backend) -> str:
    """The specification a solution file states, or the whole file where it cannot be read."""
    try:
        return backend.spec_view(solution)
    except BenchproofError:
        return solution


def _checked(bundle: Bundle, backend: Backend) -> str:
    """What the checker did on the solution when the gates last judged it.

    In the words of a session's request: the seconds it took, that it did not finish, or
    that nothing is on record, as the `spec.verifies` verdict in `manifest.json` says.
    """
    solution = f"`{backend.solution_filename()}`"
    verdict = bundle.manifest().verdicts.get(VerifiesGate.id)
    if verdict is not None and verdict.status is Status.TIMEOUT:
        return f"did not finish {solution} when the gates last judged it"
    seconds = verdict.details.get("checker_duration_s") if verdict is not None else None
    if not isinstance(seconds, (int, float)) or seconds <= 0:
        return f"has no time on record for {solution}"
    return f"took {seconds:.0f} s on {solution} when the gates last judged it"


def _not_taken(bundle: Bundle) -> str:
    """What a session is told of the sessions just before it whose work was not taken.

    Their edits went with their workspaces, and a bundle left as it was is not judged
    again, so nothing of theirs reaches the rounds: the repair record holds them. Each is
    given with why it was refused, its report's own account, and what it left (`_left`),
    in the words of `verified-swebench`'s `attempts_note`, revised. Empty when the last
    round's work was taken or no session ran.
    """
    history = bundle.manifest().provenance.get("repairs")
    refused: list[tuple[object, dict[str, Any]]] = []
    for entry in reversed(history if isinstance(history, list) else []):
        session = entry.get("session") if isinstance(entry, dict) else None
        if not isinstance(session, dict) or "refused" not in session or len(refused) >= RECALL:
            break
        refused.insert(0, (entry.get("round"), session))
    if not refused:
        return ""
    lines = [
        "## Repairs that were not taken",
        "",
        "The repair before this one was not taken, nor was any other listed here, so nothing "
        "they changed reached the bundle: you are given the bundle they were given, and the "
        "findings they were addressing still stand. Why each was not taken is Benchproofer's "
        "judgment, not its report's. Do not repeat an approach that was refused; if the same "
        "approach is still the right one, say why the refusal does not apply.",
    ]
    for number, session in refused:
        lines += ["", f"* Repair {number}, not taken: {session['refused']}."]
        for label, key in (
            ("Its report", "summary"),
            ("What it excluded, in its report's words", "excluded"),
        ):
            if text := str(session.get(key) or "").strip():
                lines.append(f"  * {label}: {text}")
        if left := str(session.get("left") or "").strip():
            lines += [
                "  * What it left, against the bundle it was given:",
                "",
                "    ```diff",
                *(f"    {line}" for line in left.splitlines()),
                "    ```",
            ]
    return "\n".join(lines) + "\n\n"


def _session_record(
    outcome: StepOutcome, *, edited: list[str], brief: dict[str, str]
) -> dict[str, Any]:
    """What the repair record keeps of one repair session, with the findings in its brief."""
    return {
        "by": "session",
        **outcome.record(
            (
                "status",
                "summary",
                "findings",
                "excluded",
                "checker",
            )
        ),
        "edited": edited,
        "briefed": brief,
    }


def _record_unchanged(
    bundle: Bundle, *, addressing: list[str], session: dict[str, Any]
) -> None:
    """Note in the repair record a repair round that left the bundle as it was."""
    manifest = bundle.manifest()
    history = manifest.provenance.get("repairs")
    rounds: list[Any] = list(history) if isinstance(history, list) else []
    rounds.append(
        {"round": len(rounds) + 1, ADDRESSING: addressing, "changed": False, "session": session}
    )
    manifest.provenance = {**manifest.provenance, "repairs": rounds}
    bundle.save_manifest(manifest)


def _record(
    bundle: Bundle, backend: Backend, *, addressing: list[str], session: dict[str, Any]
) -> None:
    """Note in the repair record which gates this repair addressed.

    The verdicts already recorded are left alone, and the next judgment replaces them. The
    evidence of each one whose inputs the repair changed is removed (`_superseded`).
    """
    manifest = bundle.manifest()
    cleared = _superseded(bundle, manifest)
    history = manifest.provenance.get("repairs")
    rounds: list[Any] = list(history) if isinstance(history, list) else []
    rounds.append(
        {
            "round": len(rounds) + 1,
            ADDRESSING: addressing,
            "session": session,
            **({"cleared_evidence": cleared} if cleared else {}),
        }
    )
    manifest.provenance = {**manifest.provenance, "repairs": rounds}
    _restamp(bundle, backend, manifest)


def _superseded(bundle: Bundle, manifest: Manifest) -> list[str]:
    """Remove the evidence that no recorded verdict still describes the bundle with.

    A gate writes its evidence when it runs, so after a repair `evidence/` describes the
    bundle the last round judged, and the review that comes before the next judgment reads
    it as though it described this one: a log of a `conformance.py` the repair replaced, the
    functions it reported, a failure a later pass did not overwrite. A verdict describes the
    bundle while every input it recorded reads as it did, and the evidence it names stays;
    the rest goes. The inputs on record for `conformance.py` (`core.replay`) stay
    whatever changed, since they are kept across rounds by design.

    Returns:
        The bundle-relative names of the files removed.
    """
    if not bundle.evidence_dir.is_dir():
        return []
    kept = {(bundle.evidence_dir / replay.FILE).relative_to(bundle.root).as_posix()}
    for verdict in manifest.verdicts.values():
        if bundle.describes(verdict):
            kept.update(verdict.evidence)
    removed: list[str] = []
    for path in sorted(bundle.evidence_dir.rglob("*")):
        name = path.relative_to(bundle.root).as_posix()
        if path.is_file() and name not in kept:
            path.unlink()
            removed.append(name)
    return removed


def _restamp(bundle: Bundle, backend: Backend, manifest: Manifest) -> None:
    """Record the regions of the solution on disk, and the digests of the files beside it.

    The solution is read off disk, which a repair that produced no readable file left as it
    was.
    """
    with suppress(BenchproofError):
        manifest.regions = backend.region_digests(bundle.solution())
    manifest.artifacts = bundle.artifact_digests()
    bundle.save_manifest(manifest)
