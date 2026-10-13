# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A record written under a value's former name reads as it did.

Bundles, manifests and review records already on disk hold the values Benchproofer wrote
when they were made. Each reader of a renamed value accepts the former one, so such a record
reads the same as one written under the name the value has now.
"""

from __future__ import annotations

from typing import Any

from benchproofer.audit.agents import _repair_answers
from benchproofer.core import rounds
from benchproofer.core.bundle import Bundle
from benchproofer.core.verdict import SkipReason, Status, Verdict
from benchproofer.gates.battery import removable
from benchproofer.pipeline.repair import _left_open
from benchproofer.pipeline.route import Route, route
from benchproofer.util.fsio import read_json, write_json


def _repaired(bundle: Bundle, entry: dict[str, Any]) -> None:
    """Record one repair round whose session was briefed with one finding."""
    manifest = bundle.manifest()
    manifest.provenance = {**manifest.provenance, "repairs": [entry]}
    bundle.save_manifest(manifest)


def _former(value: Any, renamed: dict[str, str]) -> Any:
    """``value`` with every key ``renamed`` names under its former name, at any depth."""
    if isinstance(value, dict):
        return {renamed.get(key, key): _former(item, renamed) for key, item in value.items()}
    return value


def _on_disk(bundle: Bundle, verdict: Verdict, renamed: dict[str, str]) -> Verdict:
    """``verdict`` as a manifest.json on disk holds it with detail keys under former names.

    ``renamed`` maps a key's name now to its former one. The bundle's manifest is written
    with the verdict, its detail keys renamed in the file itself, and read back.
    """
    bundle.record([verdict])
    written = read_json(bundle.manifest_path)
    recorded = written["verdicts"][verdict.gate]
    recorded["details"] = _former(recorded["details"], renamed)
    write_json(bundle.manifest_path, written)
    return bundle.manifest().verdicts[verdict.gate]


def _session(outcome: str) -> dict[str, Any]:
    """A repair session's record whose report gives its one finding ``outcome``."""
    return {
        "summary": "pinned the nickel count",
        "briefed": {"1": "the specification accepts attack-1"},
        "findings": [{"finding": "1", "outcome": outcome, "witness": "40 cents"}],
    }


def test_a_report_s_outcome_answered_reads_as_resolved(sound: Bundle) -> None:
    """`answered` is what a report gave a finding its change resolved, before `resolved`."""
    assert rounds.outcome({"finding": "1", "outcome": "answered"}) == rounds.RESOLVED
    read: dict[str, Any] = {}
    for outcome in ("answered", rounds.RESOLVED):
        _repaired(sound, {"round": 1, "session": _session(outcome)})
        read[outcome] = (_repair_answers(sound), _left_open(sound))
    assert read["answered"] == read[rounds.RESOLVED]
    answers, _ = read[rounds.RESOLVED][0]
    assert answers == {"the specification accepts attack-1": "The repair resolved it: 40 cents"}
    assert read[rounds.RESOLVED][1] == set()


def test_a_repair_record_s_answering_reads_as_addressing() -> None:
    """`answering` is the key a repair record listed the gates it addressed under."""
    gates = ["spec.strength.battery", "spec.discriminates"]
    former = {"round": 2, "answering": gates, "session": {"summary": "split the case"}}
    now = {"round": 2, rounds.ADDRESSING: gates, "session": {"summary": "split the case"}}
    assert rounds.addressed(former) == rounds.addressed(now) == gates
    assert rounds.repaired(former) == rounds.repaired(now)
    assert rounds.repaired(now)[0] == (
        "repair 2 addressed `spec.strength.battery`, `spec.discriminates`"
    )


def test_a_battery_verdict_s_answered_by_lemma_loads_and_reads_as_before(sound: Bundle) -> None:
    """`answered_by_lemma` is the key the uniqueness cases the lemma decides were listed under.

    Nothing reads the list back but a person or a repair reading the verdict, so the verdict
    loads with its details as written, and every reader of the gate's details reads it as
    one written under `decided_by_lemma`.
    """
    now = Verdict(
        gate="spec.strength.battery",
        status=Status.FAIL,
        summary="rival(s) the checker accepts",
        details={
            "decided_by_lemma": ["uniqueness-1"],
            "defects": {"too_weak": ["soundness-1"]},
        },
    )
    former = _on_disk(sound, now, {"decided_by_lemma": "answered_by_lemma"})
    assert former.details["answered_by_lemma"] == ["uniqueness-1"]
    assert rounds.details(former) == rounds.details(now)
    assert removable(former.details) == removable(now.details)


def test_a_verdict_s_out_of_scope_cases_read_as_not_evidence(sound: Bundle) -> None:
    """`out_of_scope` is the category a case whose verdict is no evidence was named under.

    A repair may remove a case the gate last named there, under either name.
    """
    now = Verdict(
        gate="spec.strength.battery",
        status=Status.FAIL,
        summary="rival(s) whose verdict is not evidence about the specification",
        details={
            "not_evidence": ["uniqueness-1"],
            "defects": {"not_evidence": ["uniqueness-1"]},
        },
    )
    former = _on_disk(sound, now, {"not_evidence": "out_of_scope"})
    assert former.details == {
        "out_of_scope": ["uniqueness-1"],
        "defects": {"out_of_scope": ["uniqueness-1"]},
    }
    assert removable(former.details) == removable(now.details) == {"uniqueness-1"}


def test_a_conformance_verdict_s_replayed_loads_and_reads_as_before(sound: Bundle) -> None:
    """`replayed` is the key the count of inputs on record each function rechecked was under.

    Nothing reads it back but a person or a repair reading the verdict, so the verdict loads
    with its details as written, and the readers of the gate's details read it as one
    written under `rechecked`.
    """
    now = Verdict(
        gate="impl.conformance",
        status=Status.PASS,
        summary="the implementation and the repository's own code agree",
        details={"rechecked": {"make_change": 3}, "compared_inputs": 1000},
    )
    former = _on_disk(sound, now, {"rechecked": "replayed"})
    assert former.details["replayed"] == {"make_change": 3}
    assert former.details["compared_inputs"] == now.details["compared_inputs"]
    assert rounds.details(former) == rounds.details(now)


def test_a_conformance_verdict_s_unreplayed_loads_and_reads_as_before(sound: Bundle) -> None:
    """`unreplayed` is the key the functions whose inputs on record went uncompared were under.

    Nothing reads it back but a person or a repair reading the verdict, so the verdict loads
    with its details as written, goes where one written under `not_rechecked` goes, and the
    readers of the gate's details read it as that one.
    """
    now = Verdict(
        gate="impl.conformance",
        status=Status.SKIP,
        skip_reason=SkipReason.INCONCLUSIVE,
        summary="conformance.py did not put back every input on record for it",
        details={
            "not_rechecked": ["make_change (0 of 2 compared or declared inadmissible)"],
            "rechecked": {"make_change": 2},
        },
    )
    former = _on_disk(sound, now, {"not_rechecked": "unreplayed", "rechecked": "replayed"})
    assert former.details == {
        "unreplayed": ["make_change (0 of 2 compared or declared inadmissible)"],
        "replayed": {"make_change": 2},
    }
    assert route(former) is route(now) is Route.REPAIR
    assert rounds.details(former) == rounds.details(now)


def test_a_report_entry_from_before_outcomes_reads_by_its_answered_flag() -> None:
    """Before reports gave each finding an outcome, they said whether the repair answered it."""
    assert rounds.outcome({"finding": "1", "answered": True}) == rounds.RESOLVED
    assert rounds.outcome({"finding": "1", "answered": False}) == rounds.NOT_REACHED
