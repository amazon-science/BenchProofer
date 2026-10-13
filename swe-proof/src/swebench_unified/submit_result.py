# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""In-process MCP server capturing structured outputs from agent steps.

Each step attaches a `submit_result` tool; downstream code reads the captured
payload, not the agent's free text. Built on claude_agent_sdk's in-process SDK
MCP server.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from claude_agent_sdk import create_sdk_mcp_server, tool

# Per-step payload schemas, kept loose: this only captures the agent's
# self-report; the orchestrator re-checks mechanically via the gate runner.
STEP_SCHEMAS: dict[str, dict] = {
    "construct": {
        "status": str,          # "green" | "blocked"
        "modeled_functions": list,
        "axioms": list,
        "verify_time_s": float,
        "prepatch_fails": bool,
        "patch_is_gold": bool,
        "notes": str,
    },
    "proof": {
        # ok = proof closes; stuck = needs a callee property; fail = spec/impl wrong
        "status": str,            # "ok" | "stuck" | "fail"
        "closed_theorems": list,  # correct_<name> names proven
        "stuck_goal": str,        # goal/proof state if stuck (else "")
        "needed_property": str,   # callee property the proof needs if stuck
        "notes": str,
    },
    "axiom_propose": {
        "verdict": str,         # "AXIOM-ADDED" | "NO-AXIOM"
        "axiom_added": str,     # the axiom declaration text (else "")
        "notes": str,
    },
    "pbt_author": {
        # G-PBT spec-lane manifest authoring (properties.py written to bundle)
        "status": str,          # "authored" | "skipped"
        "n_spec_cases": int,    # SPEC_TESTS authored
        "case_classes": list,   # e.g. ["uniqueness", "soundness", "admissibility"]
        "assessment": str,      # which classes apply/omitted and why
        "notes": str,
    },
    "spec_repair": {
        # Strengthening a spec that an audit proved too weak (a verifying attack
        # whose faithful patch does not resolve). Advisory like every
        # self-report: the orchestrator re-runs the gates and the audit. What the
        # payload adds is what no gate can re-derive — the CLAUSE added and the
        # argument that it is true of the real function and false of the attack,
        # plus the three checks that separate a real repair from one that merely
        # made the counterexample disappear.
        "verdict": str,            # REPAIRED | NO-REPAIR-NEEDED | BLOCKED
        "clause_added": str,       # the new postcondition text
        "why_true_of_repo": str,   # file:line at base_commit + the behavior
        "why_false_of_attack": str,
        "attack_now_verifies": bool,   # must be False for a real repair
        "prepatch_still_fails": bool,  # must be True: the spec must capture the fix
        "control_still_verifies": bool,  # must be True: no over-fitting
        "narrowed_precondition": bool,  # True = shrank the claim, not a repair
        "files_edited": list,
        "static_gates_line": str,
        "pbt_line": str,
        "notes": str,
    },
    "spec_mech": {
        # Re-authoring an artifact a MECHANICAL gate refuted: the model diverges
        # from the real patched function over the conformance shadow (G-CONF),
        # an axiom the model assumes is false of the real code (G-AX), the
        # solution does not verify (G-VERIFY), the spec admits a mutant (G-MUT).
        # Advisory like every self-report: the orchestrator re-runs the gate and
        # reads the stamped status back. What the payload adds is what the re-run
        # cannot distinguish -- a gate that passes because the artifact now
        # models the real behavior from one that passes because the measurement
        # stopped looking at the inputs that disagreed.
        "verdict": str,             # REPAIRED | NO-REPAIR-NEEDED | BLOCKED
        "gate": str,                # the gate that was failing
        "root_cause": str,          # what the artifact claimed vs what the real
                                    # function does, with repo file:line
        "attributed_to": str,       # "model" | "bridge" | "check-script" | "spec"
        "change_summary": str,      # what moved, and why that is the real behavior
        "oracle_unchanged": bool,   # must be True unless attributed_to is
                                    # "bridge"/"check-script": editing the
                                    # measurement to agree with the artifact is
                                    # forging the verdict, not repairing it
        "oracle_change_justification": str,  # required when oracle_unchanged is False
        "domain_narrowed": bool,    # True = excluded the diverging inputs
                                    # instead of modelling them
        "disagreements_before": int,
        "disagreements_after": int,  # must be 0
        "prepatch_still_fails": bool,  # must be True: spec still captures the fix
        "files_edited": list,
        "gate_line": str,           # the line the re-run gate printed
        "static_gates_line": str,
        "notes": str,
    },
    "spec_panel": {
        # Repairing a defect a JUDGMENT role found: the spec verifies and
        # resists every attack, yet is UNFAITHFUL (predicts what the real callee
        # does not do) or LEAKS the fix. Advisory like every self-report. What
        # the payload adds is what no gate can re-derive: that the reviewer's
        # witness was reproduced, and that the realignment moved the model
        # TOWARD the real callee rather than merely weakening the claim.
        "verdict": str,             # REPAIRED | NO-REPAIR-NEEDED | BLOCKED
        "defect": str,              # "unfaithful" | "leakage" | "both"
        "witness": str,             # the reviewer's input
        "real_output": str,         # what the real callee returns on it
        "model_output_after": str,  # what the repaired model returns on it
        "witness_agrees": bool,     # must be True: the divergence is closed
        "change_summary": str,      # what moved, and the repo file:line for it
        "weakened_postcondition": bool,  # True = deleted the claim, not a repair
        "narrowed_precondition": bool,   # True = excluded the witness, not a repair
        "prepatch_still_fails": bool,    # must be True: spec still captures the fix
        "attacks_rechecked": list,  # [{attack, verifies}] — verifies must be False
        "leak_line_removed": str,   # leakage only: the line, and how the
                                    # obligation survives without it
        "files_edited": list,
        "static_gates_line": str,
        "docker_gates_line": str,
        "notes": str,
    },
    "pbt_audit": {
        # Independent adversarial audit of a ported battery whose gate already
        # records SOUND. The verdict here is ADVISORY in the same way every
        # agent self-report is: what counts is the re-run gate status the
        # orchestrator reads back out of meta.json. What this payload is FOR is the
        # part no gate can re-derive — which cases were actually examined, and
        # with what evidence.
        "verdict": str,          # SHIP | REPAIRED | CORRUPT | SPEC-DEFECT
        "cases": list,           # [{id, verdict, evidence}] — one per case,
                                 # "unexamined" allowed but never implied
        "witnesses_rebuilt": int,  # reject cases whose two builds were re-run
        "attacks_tried": list,   # new wrong-impl / correct-reshape probes
        "spec_holes": list,      # inputs where the FROZEN spec is too weak/strong
        "omissions_reviewed": list,  # nagini cases dropped, with a per-case call
        "edited": bool,          # was properties.py changed
        "regate_verdict": str,   # the RE-RUN gate's recorded verdict after edits
        "notes": str,
    },
    "audit": {
        "gate": str,            # "G-EQ" | "G-PANEL-1" | "G-PANEL-2" | "G-PANEL-3"
        "verdict": str,         # ADVISORY only — the runner re-derives pass/fail
        "counterexample": str,  # empty if none
        "notes": str,
        # Machine-checked evidence for G-PANEL-1 / G-EQ (the runner re-runs
        # these; the agent's verdict is not trusted). Paths are ABSOLUTE (the
        # agent works in /tmp). attacks = same-spec wrong-impl files; each is
        # re-checked with adversary.check_attack. positive_control = a correct
        # impl that must verify. prepatch_reproduced = the known prepatch bug
        # was re-encoded as one of the attacks. patches (G-EQ) = {attack_path:
        # faithful_patch_text} run through run_resolve for any verifying attack.
        "attacks": list,               # [str absolute path, ...]
        "positive_control": str,       # absolute path, or ""
        "prepatch_reproduced": bool,
        "patches": dict,               # {attack_path: patch_text} (G-EQ only)
        # Evidence for the judgment roles (G-PANEL-2/3), evidence-gated:
        "diverging_input": str,        # faithfulness: the input where spec != repo
        "leaking_line": str,           # leakage: the spec-view line that leaks
    },
}


# The one field per step that is the step's DECISION. Everything else in a
# payload is evidence for it, and the orchestrator re-derives what it can, but a
# payload with no decision leaves the caller two bad options: stamp the cell
# fail-closed, or relaunch the agent from an empty context. Both throw away the
# run that just happened.
#
# So an incomplete submission is REFUSED at the tool, while the agent still has
# its findings in context and can resubmit for the price of one round trip.
# Absent and blank are the same thing here: a decision has to be readable.
# The mechanized audit roles are the ones where the decision is not just the
# verdict: their pass is DERIVED by re-running the evidence, against a floor of
# admissible attacks plus a verifying positive control (build_one owns both:
# MIN_ATTACKS_DEFAULT and _derive_audit_verdict). A payload with an empty
# `attacks` cannot come out as anything but "only 0 admissible attacks of 0
# submitted".
#
# Only `attacks`, though, not the rest of that floor. A role that FOUND a
# counterexample legitimately has no positive control and may not have
# reproduced the prepatch bug, and `prepatch_reproduced` already reads False
# when absent -- so requiring either would refuse an honest finding and leave
# the agent resubmitting a field it has nothing to put in.
_MECHANIZED = ("verdict", "attacks")

REQUIRED_KEYS: dict[str, tuple[str, ...]] = {
    # keys are submit_step names, i.e. what _audit.py/prove.py actually pass
    "audit_eq": _MECHANIZED,
    "audit_panel_1": _MECHANIZED,
    "audit_panel_2": ("verdict",),
    "audit_panel_3": ("verdict",),
    "axiom_propose": ("verdict",),
    "pbt_audit": ("verdict",),
    "spec_mech": ("verdict",),
    "spec_panel": ("verdict",),
    "spec_repair": ("verdict",),
    "construct": ("status",),
    "pbt_author": ("status",),
    "proof": ("status",),
}

# Which STEP_SCHEMAS entry documents a step's payload. The four audit roles
# share one schema, so the map exists only to keep the required keys checkable
# against a documented field (see tests/test_submit_required.py).
SCHEMA_OF_STEP: dict[str, str] = {
    "audit_eq": "audit", "audit_panel_1": "audit",
    "audit_panel_2": "audit", "audit_panel_3": "audit",
}


def missing_keys(step: str, payload: Any) -> list[str]:
    """Required keys of `step` that `payload` does not decide.

    Empty is the same as absent: a blank verdict adjudicates nothing and an
    empty attack list is evidence of nothing. `False` is NOT empty -- it is a
    decision, and the one the caller has to be able to read.
    """
    required = REQUIRED_KEYS.get(step, ())
    if not required:
        return []
    if not isinstance(payload, dict):
        return list(required)
    out = []
    for k in required:
        v = payload.get(k)
        if v is None or (isinstance(v, (str, list, dict, tuple))
                         and not (v.strip() if isinstance(v, str) else v)):
            out.append(k)
    return out


@dataclass
class SubmitCapture:
    payload: Optional[dict] = None
    submission_count: int = 0
    rejected_count: int = 0
    extra: dict = field(default_factory=dict)


def submit_handler(step: str, capture: SubmitCapture):
    """The tool body, as a plain callable over `capture`.

    Separated from the decorated tool because the SDK's server object does not
    expose its tools, so this is the only way to exercise the accept/refuse
    decision -- the part with the logic in it -- without a live agent.
    """
    async def handle(args: dict[str, Any]) -> dict:
        payload = args.get("payload", args)
        gaps = missing_keys(step, payload)
        if gaps:
            # Not counted as a submission: a caller that reads
            # `submission_count` is asking whether a decision arrived.
            capture.rejected_count += 1
            return {"content": [{"type": "text", "text":
                    "NOT captured. Missing or empty: "
                    + ", ".join(gaps)
                    + ". Fill each one in and call submit_result again; the "
                      "rest of your payload was fine."}],
                    "is_error": True}
        capture.payload = payload
        capture.submission_count += 1
        return {"content": [{"type": "text", "text": "result captured"}]}
    return handle


def make_submit_server(step: str):
    """Return (sdk_mcp_server, capture). The tool stores the last payload."""
    capture = SubmitCapture()
    required = REQUIRED_KEYS.get(step, ())
    need = (" Required: " + ", ".join(f"`{k}`" for k in required)
            + " (non-empty)." if required else "")
    handle = submit_handler(step, capture)

    @tool("submit_result",
          f"Submit the structured result for the {step} step.{need}",
          {"payload": dict})
    async def submit_result(args: dict[str, Any]):
        return await handle(args)

    server = create_sdk_mcp_server(name="submit", version="1.0.0",
                                   tools=[submit_result])
    return server, capture
