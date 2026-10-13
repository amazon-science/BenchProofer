# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""pbt_audit_completeness: which cells still need an audit under this prompt.

Three of these tests pin mistakes that were actually made while measuring this,
each expensive in a different direction:

  - reading `pbt_audit["audited_at"]` as the audit's clock. It holds the WAVE TAG
    ('a6'), so the comparison silently does nothing and every cell reads as
    current -- a gap that hides.
  - demanding forgery evidence from every payload. The prompt requires attack B'
    only where the gold-side evidence is not a plain evaluation, and most cells
    are all-`decided`, so the strict reading manufactures re-audits that have
    nothing to find -- a gap that isn't there.
  - computing the weak-tier reason off the signature alone. A `shape` tier is a
    question an auditor answers with builds, so a reason that ignores the answer
    can never be cleared: the listed cells were already fully attested, and no
    action available could remove them -- a gap that cannot close.
"""
from __future__ import annotations

from pbt_audit_completeness import audit_clock, needs_audit

SINCE = __import__("datetime").datetime.fromisoformat("2026-08-13T00:47:00+00:00")


def cell(*, checked_at="2026-08-13T02:00:00+00:00", verdict="SHIP",
         tiers=("decided",), lanes=None, evidence=None) -> dict:
    """A meta.json blob with one passing reject case per requested tier."""
    sigs = {
        "decided": "Tactic `decide` proved that the proposition fTester 1 = false is false",
        "shape": "Tactic `rewrite` failed: Did not find an occurrence of the pattern",
        "reduced": "Application type mismatch: h2 has type True but is expected",
    }
    cases = [{"id": f"c{i}", "expect": "reject", "ok": True,
              "gold_signature": sigs[t]} for i, t in enumerate(tiers)]
    return {
        "gates": {"G-PBT": {
            "status": "pass", "checked_at": checked_at,
            "data": {"cases": cases,
                     "lanes": ({"uniqueness": 1, "soundness": 1,
                                "admissibility": 1} if lanes is None else lanes)},
        }},
        "pbt_audit": {"agent_verdict": verdict, "audited_at": "a6",
                      "witness_evidence": evidence if evidence is not None else []},
    }


def test_a_fully_attested_all_decided_cell_needs_nothing():
    """The baseline: audited after the prompt, every reject decided by the
    kernel, all three lanes present. No forgery evidence is required here."""
    assert needs_audit(cell(), SINCE) == []


def test_the_audit_clock_is_the_gates_timestamp_not_the_wave_tag():
    """`audited_at` is 'a6', a tag. If it were read as the clock the comparison
    would never fire and a pre-prompt audit would pass as current."""
    stale = cell(checked_at="2026-08-12T23:00:00+00:00")
    assert audit_clock(stale["gates"]["G-PBT"]) is not None
    assert "audited-before-forgery-prompt" in needs_audit(stale, SINCE)


def test_an_all_decided_battery_is_not_charged_for_missing_forgery_evidence():
    """Attack B' is mandatory only where `gold_signature` is not a plain
    evaluation, so charging every forgery-free payload nearly doubles the
    worklist with cells that have nothing to find."""
    assert "bprime-required-but-absent" not in needs_audit(
        cell(tiers=("decided", "decided")), SINCE)


def test_a_non_evaluation_signature_without_forgery_evidence_is_a_gap():
    """The other direction: a `shape`-tier reject is exactly the case the
    forgery test exists for, so a payload lacking it is not attested."""
    reasons = needs_audit(cell(tiers=("decided", "shape")), SINCE)
    assert "bprime-required-but-absent" in reasons
    assert "weak-gold-evidence" in reasons


def test_recorded_forgery_evidence_settles_the_non_evaluation_case():
    """A payload that ran the flipped-claim build clears B' regardless of tier;
    the weak-tier reason is separate and stands on its own."""
    ev = [{"id": "c1", "forgery_exit": "gold 0 / rival 1",
           "forgery_error": "gold: NO ERROR, exit 0"}]
    reasons = needs_audit(cell(tiers=("reduced",), evidence=ev), SINCE)
    assert "bprime-required-but-absent" not in reasons


def test_the_split_clean_forgery_spelling_settles_the_case_too():
    """A cell may record the flipped claim as two exits rather than one, when its
    naive forgery yields `No goals to be solved` and only the truncated CLEAN
    forgery separates the sides. Requiring the single-key spelling reports the
    cell that ran the SHARPER experiment as one that ran none -- and a driver
    relaunches on whatever this lists, so it would ask forever."""
    ev = [{"case": "c0", "gold_exit": 1,
           "clean_forgery_ref_exit": 0, "clean_forgery_rival_exit": 1}]
    reasons = needs_audit(cell(tiers=("shape",), evidence=ev), SINCE)
    assert "bprime-required-but-absent" not in reasons
    assert "weak-gold-evidence" not in reasons, "the same entry attests its case"


def test_an_entry_with_neither_forgery_spelling_still_attests_nothing():
    """The widening is two more key names, not a relaxation: an entry that only
    reports the witness's own exits has not run the flipped claim."""
    ev = [{"case": "c0", "gold_exit": 1, "rival_exit": 0, "probe_exit": 1}]
    reasons = needs_audit(cell(tiers=("shape",), evidence=ev), SINCE)
    assert "bprime-required-but-absent" in reasons
    assert "weak-gold-evidence" in reasons


def test_a_reduced_tier_signature_is_not_weak_evidence():
    """`has type True` means simp PROVED the equation the witness assumed
    violated: the strongest evidence in the corpus, not a broken script."""
    assert needs_audit(cell(tiers=("reduced",),
                            evidence=[{"id": "c0", "forgery_exit": "gold 0 / rival 1"}]),
                       SINCE) == []


def test_a_missing_admissibility_lane_is_reported_separately_from_an_absent_lanes_key():
    """`lanes` absent means the record predates `_lanes` and cannot answer the
    question; a present `lanes` without admissibility is a real omission. Both
    need a look, for different reasons, so they are not one bucket."""
    assert "no-admissibility-lane" in needs_audit(
        cell(lanes={"uniqueness": 1, "soundness": 1}), SINCE)
    unrecorded = needs_audit(cell(lanes=None), SINCE)
    blob = cell()
    blob["gates"]["G-PBT"]["data"].pop("lanes")
    assert "lanes-unrecorded" in needs_audit(blob, SINCE)
    assert unrecorded == []          # lanes=None means "use the default (complete)"


def test_a_weak_case_an_auditor_decided_with_builds_is_attested():
    """Otherwise the reason is unclearable and the worklist is a treadmill.

    `pbt_signature_tiers` is explicit that a `shape` signature is a QUESTION --
    "the deciding test is whether a witness claiming the OPPOSITE fails
    identically, which needs builds, not a regex". An auditor who ran that build
    and found the rejection genuine had nowhere to record it: the reason was
    computed off the signature alone, so it survived every audit. 28 of the 39
    cells on this worklist were fully attested and still listed, with no action
    available that could remove them.
    """
    ev = [{"id": "c0", "gold_exit": 1, "rival_exit": 0,
           "forgery_exit": "0 on gold / 1 on rival",
           "forgery_error": "gold: builds clean (exit 0)"}]
    assert needs_audit(cell(tiers=("shape",), evidence=ev), SINCE) == []


def test_attestation_is_per_case_not_per_cell():
    """A payload covering nine of a battery's ten weak cases leaves the tenth
    open. Recording signatures per case is what made that measurable instead of
    estimated, so the check reads them the same way."""
    ev = [{"id": "c0", "gold_exit": 1, "forgery_exit": "0 on gold / 1 on rival"}]
    reasons = needs_audit(cell(tiers=("shape", "shape"), evidence=ev), SINCE)
    assert "weak-gold-evidence" in reasons        # c1 has no entry


def test_a_case_keyed_evidence_entry_attests_the_same_as_an_id_keyed_one():
    """`case` is the other spelling auditors use for the identifier.

    The prompt asks for `id`, and most entries use it, but some say `case` and
    still name a real reject case id. Ignoring the synonym reported those cells at
    0 attested while their own records logged them as `audited ... REPAIRED` with
    the full per-case experiment in the payload. Whatever this script lists gets
    re-audited, so the disagreement was a treadmill: run the audit, record it, be
    asked for it again.
    """
    ev = [{"case": "c0", "gold_exit": 1, "rival_exit": 0,
           "forgery_exit": "flip-on-gold 0 / flip-on-rival 1"}]
    assert needs_audit(cell(tiers=("shape",), evidence=ev), SINCE) == []


def test_a_case_key_naming_something_that_is_not_a_case_attests_nothing():
    """The synonym is read, not trusted: a `case`-keyed entry may name an attack
    rather than a battery case, and must not discharge a real one."""
    ev = [{"case": "attack-D", "gold_exit": 1, "forgery_exit": "x"}]
    assert "weak-gold-evidence" in needs_audit(cell(tiers=("shape",), evidence=ev),
                                               SINCE)


def test_an_evidence_entry_without_the_witnesss_own_gold_result_attests_nothing():
    """The forgery result is only evidence NEXT TO the witness's own: the
    experiment is that the two differ, and one number alone is not a
    comparison."""
    ev = [{"id": "c0", "forgery_exit": "0 on gold / 1 on rival"}]
    assert "weak-gold-evidence" in needs_audit(
        cell(tiers=("shape",), evidence=ev), SINCE)


def test_a_pre_prompt_audits_evidence_cannot_settle_a_weak_case():
    """The clock is what makes "attested under the CURRENT prompt" decidable. A
    payload from before attack B' existed cannot hold the experiment, so its
    entries must not discharge the reason the experiment answers."""
    ev = [{"id": "c0", "gold_exit": 1, "forgery_exit": "0 on gold / 1 on rival"}]
    reasons = needs_audit(cell(tiers=("shape",), evidence=ev,
                               checked_at="2026-08-12T23:00:00+00:00"), SINCE)
    assert "audited-before-forgery-prompt" in reasons
    assert "weak-gold-evidence" in reasons


def test_a_case_with_no_id_cannot_be_attested():
    """Nothing in the payload can be tied to it, and the safe direction for an
    unidentifiable case is to keep asking."""
    blob = cell(tiers=("shape",),
                evidence=[{"id": "c0", "gold_exit": 1, "forgery_exit": "x"}])
    blob["gates"]["G-PBT"]["data"]["cases"][0].pop("id")
    assert "weak-gold-evidence" in needs_audit(blob, SINCE)


def test_a_failing_reject_case_is_not_asked_for_evidence():
    """`ok` false means the gate already failed the case; this script is about
    what a PASSING reject rests on."""
    blob = cell(tiers=("shape",))
    blob["gates"]["G-PBT"]["data"]["cases"][0]["ok"] = False
    assert needs_audit(blob, SINCE) == []


def test_a_cell_with_no_audit_at_all_is_never_silently_current():
    blob = cell()
    blob["pbt_audit"] = {}
    assert "never-audited" in needs_audit(blob, SINCE)


def test_an_unparseable_clock_is_a_finding_not_a_pass():
    """A record whose timestamp cannot be read cannot be certified by date."""
    assert "audit-has-no-clock" in needs_audit(cell(checked_at="not-a-time"), SINCE)
