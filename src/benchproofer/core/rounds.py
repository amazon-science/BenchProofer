# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The rounds of one run's loop over a bundle, as the rounds after them read them.

`pipeline.run` keeps each round's bundle as that round judged it, one directory each under
`directory`: its manifest holds the verdicts that round reached, and `round.md` says what
produced the bundle and lists every finding of each gate that did not pass. A repair session and
the faithfulness auditor are shown the rounds before theirs one line per finding (`outline`),
with what each repair did (`repaired`). The repair record (`provenance.repairs` in
`manifest.json`) keeps each repair session's findings by the number its brief gave them, beside
its report's entry for each (`briefed`, `reported`), whose outcome says whether the session
resolved the finding, found it no defect, or did not reach it (`outcome`).

The rounds also decide which unchanged callees a repair may take the result of as an input of
the model (`eligible`), which the repair and the auditors that state the rule for callees are
shown (`inputs_rules`).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..errors import BenchproofError
from ..util.fsio import read_json, read_text_or_empty
from .axioms import declared
from .bundle import Bundle, Manifest
from .differential import clipped
from .markers import parse
from .prompts import SHARED
from .verdict import Status, Verdict, one_line

if TYPE_CHECKING:
    from ..backends.base import Backend

__all__ = [
    "ADDRESSING",
    "NOT_A_DEFECT",
    "NOT_REACHED",
    "OUTCOMES",
    "RECORD",
    "RESOLVED",
    "Failed",
    "addressed",
    "archived",
    "briefed",
    "details",
    "directory",
    "eligible",
    "inputs_rules",
    "outcome",
    "outline",
    "repaired",
    "reported",
    "sentence",
    "since",
]

#: The record of one round, beside its bundle.
RECORD = "round.md"
#: Detail keys listed beneath a verdict's summary, one finding each, in the order listed,
#: with the words that open each: the auditor's own findings first, in the order the auditor
#: numbered them, so that a finding referring to another by its number refers to the one
#: listed under that number; then the coverage rows no obligation states.
BRIEFED: tuple[tuple[str, str], ...] = (
    ("findings", ""),
    ("uncovered", "a tested behaviour no obligation states: "),
)
#: How much of a finding's first sentence `outline` keeps.
SENTENCE = 200
#: What a repair's report says it did about one finding: changed the bundle to resolve it,
#: found it no defect and changed nothing for it, or did not reach it.
RESOLVED = "resolved"
NOT_A_DEFECT = "not a defect"
NOT_REACHED = "not reached"
OUTCOMES: tuple[str, ...] = (RESOLVED, NOT_A_DEFECT, NOT_REACHED)
#: Outcomes a report wrote under a former name, by the outcome each is read as, so that a
#: repair record already on disk reads as it did when it was written.
_FORMER_OUTCOMES: dict[str, str] = {"answered": RESOLVED}
#: The key a repair record lists the gates its repair addressed under, and the one a record
#: written before it was named so holds them under instead.
ADDRESSING = "addressing"
_FORMER_ADDRESSING = "answering"


def directory(bundle: Bundle, cache_dir: Path) -> Path:
    """Where this run's rounds of ``bundle`` are kept."""
    return bundle.scratch(cache_dir) / "rounds"


def archived(path: Path) -> list[tuple[str, Manifest]]:
    """Each round kept under ``path``, oldest first: its directory's name and its manifest.

    A directory without a readable manifest is not a round the loop kept, and is skipped.
    """
    found: list[tuple[str, Manifest]] = []
    for entry in sorted(path.iterdir()) if path.is_dir() else ():
        try:
            found.append(
                (entry.name, Manifest.model_validate(read_json(entry / "manifest.json")))
            )
        except (OSError, ValueError):
            continue
    return found


def details(verdict: Verdict) -> list[str]:
    """The findings a verdict lists under `BRIEFED`, one line each.

    Its summary names only the first few of them.
    """
    found: list[str] = []
    for key, opening in BRIEFED:
        value = verdict.details.get(key)
        if isinstance(value, list):
            found += [f"{opening}{item}" for item in value if isinstance(item, str)]
    return found


def outline(verdicts: Iterable[Verdict]) -> list[str]:
    """Each verdict that does not pass, as a bullet of one line per finding.

    The gate and its summary's first sentence, and beneath it the first sentence of each of
    its findings.
    """
    lines: list[str] = []
    for verdict in verdicts:
        if not verdict.ok:
            lines.append(f"* `{verdict.gate}` ({verdict.status}): {sentence(verdict.summary)}")
            lines += [f"  * {sentence(line)}" for line in details(verdict)]
    return lines


def briefed(session: Mapping[str, Any]) -> dict[str, str]:
    """The findings a repair session was briefed with, by the number its brief gave each.

    ``session`` is what the repair record keeps of the session.
    """
    found = session.get("briefed")
    if not isinstance(found, dict):
        return {}
    return {str(number): text for number, text in found.items() if isinstance(text, str)}


def reported(session: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """The session's report's entry for each finding, by the number it gave the finding."""
    found = session.get("findings")
    return {
        str(entry["finding"]).strip(): entry
        for entry in (found if isinstance(found, list) else [])
        if isinstance(entry, dict) and entry.get("finding") is not None
    }


def outcome(entry: Mapping[str, Any] | None) -> str:
    """What a report's entry for a finding says the session did about it (`OUTCOMES`).

    An outcome under a former name (`_FORMER_OUTCOMES`) is read as the one it names now, and
    an entry from before reports had an outcome, whose `answered` flag is true, as resolved.
    An entry that names none of them, or no entry, is a finding the session did not reach.
    """
    said = entry.get("outcome") if entry is not None else None
    if said is None and entry is not None and entry.get("answered") is True:
        said = RESOLVED
    if isinstance(said, str):
        said = _FORMER_OUTCOMES.get(said, said)
    return said if said in OUTCOMES else NOT_REACHED


def addressed(record: Mapping[str, Any]) -> list[str]:
    """The gates one repair record says its repair addressed, under either key it is kept by."""
    found = record.get(ADDRESSING, record.get(_FORMER_ADDRESSING))
    return [str(gate) for gate in found] if isinstance(found, list) else []


def since(before: Manifest | None, after: Manifest) -> list[Any]:
    """The repairs ``after`` records beyond those ``before`` does, oldest first."""
    return _repairs(after)[len(_repairs(before)) :]


def repaired(entry: Any) -> tuple[str, str]:
    """One repair in the repair record: the gates it addressed, and what it did.

    What it did is why its work was not taken, where it was not, and then its report's
    summary.
    """
    record: dict[str, Any] = entry if isinstance(entry, dict) else {}
    found = record.get("session")
    session: dict[str, Any] = found if isinstance(found, dict) else {}
    gates = ", ".join(f"`{gate}`" for gate in addressed(record)) or "nothing"
    refused = session.get("refused")
    parts = (
        f"Its work was not taken: {refused}." if refused else "",
        str(session.get("summary") or "").strip(),
    )
    did = " ".join(part for part in parts if part) or "It filed no report."
    return f"repair {record.get('round', '?')} addressed {gates}", did


def sentence(text: str) -> str:
    """The first sentence of ``text``, on one line and cut to `SENTENCE` characters."""
    flat = " ".join(text.split())
    end = re.search(r"[.!?](?=\s|$)", flat)
    return one_line(flat[: end.end()] if end else flat, SENTENCE)


def _repairs(manifest: Manifest | None) -> list[Any]:
    """The repairs in a manifest's repair record, oldest first."""
    found = manifest.provenance.get("repairs") if manifest is not None else None
    return list(found) if isinstance(found, list) else []


#: The gate that runs the review's fuzzers against the axioms and the definitions of the
#: `axioms` region, and the gate that runs the checker on the solution file.
_FUZZED = "audit.axiom_soundness"
_CHECKED = "spec.verifies"


@dataclass(frozen=True, slots=True)
class Failed:
    """One round in which the way the rule for callees states a callee failed."""

    round: str
    #: What failed, as the list the repair and the auditors are shown says it.
    what: str
    #: The first few lines the fuzzer or the checker printed about the callee in that round.
    lines: tuple[str, ...]


def eligible(path: Path, backend: Backend) -> dict[str, tuple[Failed, ...]]:
    """The unchanged callees whose result a repair may take as an input, with the evidence.

    ``path`` is this run's rounds (`directory`). A callee is one when the way the rule for
    callees states it -- a definition under its `benchproofer:models` line, or an axiom over
    the call's arguments -- failed in two rounds with a repair between them, so a repair tried
    to state it again and failed. A round counts when `audit.axiom_soundness` refuted
    its axiom or definition, or when `spec.verifies` did not pass and the checker placed an
    error at a line of its declaration (`_placed`). Rounds judged with the same number of
    repairs on record, as a round that asked an auditor again about an unchanged bundle is,
    count once. A timeout of the whole check is placed at no line and counts for no callee,
    and a fuzzer's refutation counts the same whatever it shows, its line being free text.
    """
    found: dict[str, dict[int, list[Failed]]] = {}
    for name, manifest in archived(path):
        repairs = len(_repairs(manifest))
        for callee, failed in _failures(path / name, name, manifest, backend):
            found.setdefault(callee, {}).setdefault(repairs, []).append(failed)
    return {
        callee: tuple(failed for each in by.values() for failed in each)
        for callee, by in found.items()
        if len(by) > 1
    }


def _failures(
    root: Path, name: str, manifest: Manifest, backend: Backend
) -> Iterator[tuple[str, Failed]]:
    """Each callee whose statement failed in the round kept at ``root``, with what failed."""
    fuzzed = manifest.verdicts.get(_FUZZED)
    if fuzzed is not None and fuzzed.status is Status.FAIL:
        refuted = fuzzed.details.get("refuted")
        said = [line for line in fuzzed.details.get("witnesses") or () if isinstance(line, str)]
        for callee in refuted if isinstance(refuted, list) else ():
            line = re.compile(rf"benchproofer:refuted\s+{re.escape(str(callee))}(\s|$)")
            yield (
                str(callee),
                Failed(
                    name,
                    f"`{_FUZZED}` (the axiom-soundness gate) refuted it",
                    clipped([text for text in said if line.search(text)]),
                ),
            )
    checked = manifest.verdicts.get(_CHECKED)
    if checked is None or checked.ok:
        return
    printed = "\n".join(read_text_or_empty(root / evidence) for evidence in checked.evidence)
    solution = read_text_or_empty(root / backend.solution_filename())
    for callee, lines in _placed(solution, printed, backend).items():
        yield (
            callee,
            Failed(
                name,
                f"`{_CHECKED}` (the verification check) did not pass, and the checker reported "
                "an error on a line of its declaration in the `axioms` region",
                clipped(lines),
            ),
        )


def _placed(solution: str, printed: str, backend: Backend) -> dict[str, list[str]]:
    """The callees of ``solution``'s `axioms` region the checker placed an error under.

    ``printed`` is what the checker printed, read with the backend's `refusal_site`. A line of
    the region belongs to the callee whose `benchproofer:axiom` or `benchproofer:models` line
    comes last before it. Each callee has the checker's lines that placed an error there.
    """
    if not backend.refusal_site:
        return {}
    try:
        region = parse(solution, backend.comment, required=()).get("axioms")
    except BenchproofError:
        return {}
    if region is None:
        return {}
    starts = [
        (region.start + item.line, item.callee)
        for item in declared(region.text, backend.comment)
    ]
    found: dict[str, list[str]] = {}
    for text in printed.splitlines():
        site = re.match(backend.refusal_site, text)
        line = int(site.group("line")) if site is not None else 0
        owners = [callee for start, callee in starts if start <= line <= region.end]
        if owners:
            found.setdefault(owners[-1], []).append(text.strip())
    return found


def inputs_rules(found: Mapping[str, Sequence[Failed]]) -> str:
    """The rule for taking a listed callee's result as an input, with the list, or "".

    ``found`` is what `eligible` decided. The repair and the auditors that state the rule for
    callees are shown it only where it lists a callee, so a prompt with none states the rule
    for callees alone and reads as it would without it; where it lists one, it ends in a blank
    line, to stand before the next section.
    """
    if not found:
        return ""
    listed: list[str] = []
    for callee, failures in found.items():
        listed.append(f"* `{callee}`")
        for failed in failures:
            listed.append(
                f"  * round {failed.round}: {failed.what}{':' if failed.lines else '.'}"
            )
            listed += [f"    * `{line}`" for line in failed.lines]
    return SHARED.render("inputs-rules", callees="\n".join(listed)).rstrip() + "\n\n"
