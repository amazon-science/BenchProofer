# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""The inputs a conformance comparison is put to again, whoever found them.

A bundle's `conformance.py` reproduces its own disagreements from the seed it prints, but
a rewritten one draws other inputs. Each input on which a run found the implementation to
disagree with the repository is kept here, as the arguments the implementation is called
with, and handed to every later run of the bundle's `conformance.py`
(`differential.with_replay`), which compares it first. So is the input of each defect the
attack auditor files (`core.bundle.Defect`), on which it says the specification promises what
the repository does not do.

The record lives in the bundle's evidence, which neither the author nor a repair session
may write. Each input carries who found it and the specification view it was found under.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from ..util.fsio import read_json, write_json
from .differential import arguments

if TYPE_CHECKING:
    from .bundle import Bundle

__all__ = ["FILE", "GATE", "LIMIT", "REVIEW", "Witness", "by_function", "record", "stored"]

#: The evidence file the inputs are kept in.
FILE = "conformance-witnesses.json"
#: The source recorded for an input the conformance gate's own run found.
GATE = "impl.conformance"
#: The source recorded for the input of a defect the attack auditor filed. A run of
#: `conformance.py` did not draw it, so one may declare it outside what the preconditions admit.
REVIEW = "review"
#: How many inputs are kept for one function, the first found: a `conformance.py` printing
#: thousands of disagreements has made its point, and each kept input costs the next run.
LIMIT = 20


@dataclass(frozen=True, slots=True)
class Witness:
    """One input to compare again, and where it came from."""

    #: The dotted name `conformance.py` reports the function by.
    function: str
    #: The arguments as a tuple literal, in `differential.arguments`' spelling.
    arguments: str
    #: Who found it: `GATE` or `REVIEW`.
    source: str
    #: The digest of the specification view the input was found under.
    spec: str


def stored(bundle: Bundle) -> tuple[Witness, ...]:
    """Every input on record for this bundle, in recorded order.

    An entry that does not read back is skipped: one damaged entry says nothing about the
    others.
    """
    path = bundle.evidence_dir / FILE
    if not path.is_file():
        return ()
    try:
        entries = read_json(path)
    except ValueError:
        return ()
    kept: list[Witness] = []
    for entry in entries if isinstance(entries, list) else ():
        try:
            witness = Witness(**{key: str(entry[key]) for key in Witness.__slots__})
        except (KeyError, TypeError):
            continue
        if arguments(witness.arguments) == witness.arguments:
            kept.append(witness)
    return tuple(kept)


def by_function(witnesses: Iterable[Witness]) -> dict[str, list[Witness]]:
    """The inputs grouped by the function they are compared on, each in recorded order."""
    grouped: dict[str, list[Witness]] = {}
    for witness in witnesses:
        grouped.setdefault(witness.function, []).append(witness)
    return grouped


def record(
    bundle: Bundle, found: Mapping[str, Sequence[str]], *, source: str, spec: str
) -> tuple[Witness, ...]:
    """Add the inputs ``found`` to the bundle's record, and return the ones that are new.

    Args:
        bundle: The bundle whose evidence holds the record.
        found: Argument tuples by function, as `differential.witnessed` returns them.
            One that does not read back as a tuple literal is not recorded.
        source: Who found them: `GATE` or `REVIEW`.
        spec: The digest of the specification view they were found under.
    """
    on_record = list(stored(bundle))
    known = {(item.function, item.arguments) for item in on_record}
    counts: dict[str, int] = {}
    for item in on_record:
        counts[item.function] = counts.get(item.function, 0) + 1
    added: list[Witness] = []
    for function, items in found.items():
        for text in items:
            kept = arguments(text)
            if kept is None or (function, kept) in known or counts.get(function, 0) >= LIMIT:
                continue
            known.add((function, kept))
            counts[function] = counts.get(function, 0) + 1
            added.append(Witness(function=function, arguments=kept, source=source, spec=spec))
    if added:
        bundle.evidence_dir.mkdir(parents=True, exist_ok=True)
        write_json(bundle.evidence_dir / FILE, [asdict(item) for item in (*on_record, *added)])
    return tuple(added)
