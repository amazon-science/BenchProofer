# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""A submission with no decision in it must be refused, not banked.

An audit role's payload carries a verdict plus the evidence for it. When the
verdict is absent the caller cannot record anything about the cell, so it
fail-closes and a re-audit lane picks the cell up later -- and the agent that
did the work is gone. The shape it happens in is pages of analysis under `notes`
with `verdict` never set, then several launches and minutes of backoff, and the
cell recorded as unadjudicated at the end of it.

Refusing at the tool costs one round trip while the findings are still in the
agent's context. These tests pin the two halves: an incomplete payload is not
banked and says what is missing, and a complete one is unaffected.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from swebench_unified.submit_result import (
    REQUIRED_KEYS, SCHEMA_OF_STEP, SubmitCapture, missing_keys, submit_handler,
)

ROOT = Path(__file__).resolve().parents[1]

# what _audit.py passes as submit_step for the judgment roles
JUDGE = "audit_panel_3"


def _call(step: str, payload):
    """Invoke the step's submit tool once, returning (result, capture)."""
    capture = SubmitCapture()
    handle = submit_handler(step, capture)
    return asyncio.run(handle({"payload": payload})), capture


def test_a_verdict_less_audit_payload_is_refused():
    """The exact shape that burned the corpus: rich notes, no verdict."""
    res, cap = _call(JUDGE, {"gate": "G-PANEL-3",
                             "notes": "LEAKAGE HUNT. Spec view regenerated..."})
    assert res.get("is_error") is True
    assert cap.payload is None and cap.submission_count == 0
    assert cap.rejected_count == 1
    text = res["content"][0]["text"]
    assert "verdict" in text and "again" in text


def test_a_blank_verdict_counts_as_missing():
    """`verdict: ""` adjudicates exactly as much as no key at all, and it is the
    likelier mistake: the agent filled the template and left the field alone."""
    assert missing_keys(JUDGE, {"verdict": "   ", "notes": "x"}) == ["verdict"]
    _, cap = _call(JUDGE, {"verdict": "", "notes": "x"})
    assert cap.payload is None


def test_a_complete_payload_is_captured_unchanged():
    """The common path must not gain a hurdle: the payload is stored verbatim,
    including whatever extra keys the step's schema documents."""
    good = {"gate": "G-EQ", "verdict": "SOUND", "attacks": ["/tmp/a1.py"],
            "positive_control": "/tmp/ctrl.py", "notes": "four families"}
    res, cap = _call("audit_eq", good)
    assert res.get("is_error") is not True
    assert cap.payload == good and cap.submission_count == 1
    assert cap.rejected_count == 0


def test_a_refusal_leaves_an_earlier_good_verdict_standing():
    """Submissions used to overwrite unconditionally. An agent that submits a
    verdict and then a follow-up payload it forgot to re-fill would otherwise
    erase its own decision."""
    cap = SubmitCapture()
    handle = submit_handler(JUDGE, cap)
    asyncio.run(handle({"payload": {"verdict": "SOUND", "notes": "a"}}))
    asyncio.run(handle({"payload": {"notes": "b"}}))
    assert cap.payload == {"verdict": "SOUND", "notes": "a"}
    assert cap.submission_count == 1 and cap.rejected_count == 1


def test_a_step_with_no_required_key_is_unconstrained():
    """Only steps whose decision the orchestrator cannot re-derive are gated. An
    unlisted step must keep working, or adding a step becomes a trap."""
    assert missing_keys("some_new_step", {}) == []
    res, cap = _call("some_new_step", {"anything": 1})
    assert res.get("is_error") is not True and cap.submission_count == 1


def test_a_mechanized_role_must_bring_its_evidence():
    """eq and panel_1 do not decide their own outcome: the runner re-runs the
    attacks and needs at least five admissible ones plus a verifying control. A
    payload with an empty attack list is guaranteed to come back "only 0
    admissible attacks of 0 submitted", so it is refused while the agent can
    still write them."""
    res, cap = _call("audit_eq", {"verdict": "SOUND", "attacks": [],
                                  "notes": "read the spec, found nothing"})
    assert res.get("is_error") is True and cap.payload is None
    assert "attacks" in res["content"][0]["text"]
    # a judgment role has no attacks to bring, and must not be asked for them
    assert missing_keys("audit_panel_2", {"verdict": "FAITHFUL"}) == []
    # and a role that FOUND something keeps its finding: no positive control and
    # no reproduced prepatch bug is an honest answer, not an empty submission
    assert missing_keys("audit_eq", {"verdict": "BROKEN",
                                     "attacks": ["/tmp/a1.py"],
                                     "counterexample": "/tmp/a1.py"}) == []


def test_a_false_bool_is_a_decision_not_an_omission():
    """`prepatch_reproduced: False` is an honest answer. Emptiness has to mean
    "nothing to read", or a required bool could never be answered no."""
    assert missing_keys("construct", {"status": "blocked"}) == []
    assert missing_keys("audit_eq", {"verdict": "WEAK", "attacks": ["/tmp/a"],
                                     "prepatch_reproduced": False}) == []


def test_every_required_key_exists_in_that_step_s_schema():
    """A required key that the step's documented schema does not have would
    reject every submission the prompt teaches the agent to make. The step names
    are submit_step strings, so this also pins them to a real schema entry --
    the mistake that made the first version of this gate a no-op, since the
    audit roles submit as `audit_eq`, not `audit`."""
    from swebench_unified.submit_result import STEP_SCHEMAS
    for step, keys in REQUIRED_KEYS.items():
        schema = STEP_SCHEMAS.get(SCHEMA_OF_STEP.get(step, step))
        assert schema is not None, step
        for k in keys:
            assert k in schema, (step, k)


def test_the_gated_steps_are_the_steps_that_exist():
    """Every submit_step the code actually passes should be gated, or a role can
    go on submitting nothing. Read out of the source so a new step shows up
    here rather than silently joining the ungated set."""
    import re
    src = ROOT / "src" / "swebench_unified"
    steps = set()
    for p in list(src.glob("*.py")) + list(src.glob("*/*.py")):
        text = p.read_text()
        for m in re.finditer(r"submit_step=[\"']([a-z_]+)[\"']", text):
            steps.add(m.group(1))
        # the audit roles are the one interpolated step name in the tree
        if "submit_step=f" in text and "audit_{role}" in text:
            steps |= {"audit_eq", "audit_panel_1",
                      "audit_panel_2", "audit_panel_3"}
    # `adversary` is exempt: its caller already treats a missing submission as a
    # failure to produce an attack and re-runs it (eval/adversary.py).
    assert steps - {"adversary"} <= set(REQUIRED_KEYS), steps - set(REQUIRED_KEYS)
