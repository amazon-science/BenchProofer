# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Lean proof-phase driver (construct P1.5) — docs/architecture.md §3.

An agentic, bundle-mutating service invoked ONLY by the construction pipeline.
Gates never import this module; G-VERIFY re-judges the committed bundle
afterwards, which is what keeps a proof phase from being able to vouch for its
own output.

Semantics: ``cfg.proof_gen`` is a TOTAL wall-clock budget shared across
attempts (each agent call gets min(remaining, proof_gen)). Baseline: up to
``max_proof_attempts`` calls, a ``stuck`` has no escape hatch.
``axiom_refinement=True``: stuck triggers axiom_propose, then the next attempt
retries with the new axiom, bounded by ``max_axiom_iterations``.

"ok" ONLY ever comes from the mechanical G-VERIFY re-check — never the agent's
self-report; a self-reported "ok" whose check fails is treated as a plain
retry.
"""
from __future__ import annotations

import time

from .agent import run_agent_step, DEFAULT_MODEL
from .config import ProofConfig
from .paths import PROJECT_ROOT, tasks_root_rel
from .prompts import load_prompt


def _gverify(instance_id: str, backend_name: str):
    """Mechanical G-VERIFY re-check of the committed bundle; never trusts the
    proof agent's self-report. Unrecorded — the pipeline's final strict sweep
    is the verdict of record."""
    from .gates import run_gates
    return run_gates(instance_id, backend_name, ["G-VERIFY"],
                     mode="strict", record=False)[0]


def prove(instance_id: str, backend_name: str, cfg: ProofConfig,
          model: str | None = None) -> tuple[bool, str]:
    """P1.5 proof generation for one bundle. Returns (verify_ok, note).
    Prompts: proof_system / proof_agent, plus axiom_propose_system /
    axiom_propose under axiom refinement."""
    model = model or DEFAULT_MODEL
    system = load_prompt("proof_system", backend=backend_name)
    base = load_prompt("proof_agent", backend=backend_name, iid=instance_id,
                       root=tasks_root_rel())

    deadline = time.monotonic() + cfg.proof_gen
    attempts = 0
    last = ""

    def _remaining() -> int:
        return int(deadline - time.monotonic())

    def _attempt(note_extra: str) -> tuple[str, dict]:
        """One proof-agent call -> (verdict, payload). Verdict is MECHANICAL:
        'ok' only when G-VERIFY passes; on failure, the agent's self-report
        routes to 'fail' (spec/impl bug -> bounce to P1), 'stuck' (needs a
        callee property -> axiom-propose), or '' (plain retry)."""
        nonlocal attempts, last
        attempts += 1
        prompt = base + (f"\n\n## Proof attempt {attempts}: previous attempt "
                         f"did NOT close every correct_<name>:\n{note_extra}\n"
                         if note_extra else "")
        try:
            outcome = run_agent_step(
                system_prompt=system, user_prompt=prompt,
                cwd=str(PROJECT_ROOT),
                timeout_s=min(_remaining(), cfg.proof_gen),
                model=model, submit_step="proof")
            payload = outcome.payload or {}
        except Exception as e:  # agent CLI / timeout error -> plain retry
            last = f"(proof agent error: {e})"
            return "", {}
        vr = _gverify(instance_id, backend_name)
        last = vr.detail
        if vr.status == "pass":
            return "ok", payload   # mechanical PASS — the only 'ok' source
        # a self-reported 'ok' here is a lie (proof did not close) -> ''
        reported = (payload.get("status", "") or "")
        return (reported if reported in ("stuck", "fail") else ""), payload

    # ---- baseline mode ------------------------------------------------------
    if not cfg.axiom_refinement:
        for _ in range(cfg.max_proof_attempts):
            if _remaining() <= 0:
                return False, (f"proof budget ({cfg.proof_gen}s) exhausted "
                               f"after {attempts} attempt(s): {last}")
            verdict, payload = _attempt(last)
            if verdict == "ok":
                return True, f"G-VERIFY passes after {attempts} proof attempt(s): {last}"
            if verdict == "fail":
                return False, ("proof agent reports spec/impl bug (fail -> "
                               f"bounce to P1): {payload.get('notes', '')}")
            # 'stuck'/'' -> next attempt (baseline has no axiom escape hatch)
        return False, f"G-VERIFY still failing after {attempts} proof attempt(s): {last}"

    # ---- axiom-refinement mode ----------------------------------------------
    ax_system = load_prompt("axiom_propose_system", backend=backend_name)
    for _ in range(cfg.max_axiom_iterations + 1):
        if _remaining() <= 0:
            return False, (f"proof budget ({cfg.proof_gen}s) exhausted after "
                           f"{attempts} attempt(s): {last}")
        verdict, payload = _attempt(last)
        if verdict == "ok":
            return True, f"G-VERIFY passes after {attempts} proof attempt(s): {last}"
        if verdict == "fail":
            return False, ("proof agent reports spec/impl bug (fail -> bounce "
                           f"to P1): {payload.get('notes', '')}")
        if verdict != "stuck":
            continue  # transient/unknown -> retry while budget remains
        # stuck -> propose+validate a minimal callee axiom, then retry
        if _remaining() <= 0:
            break
        stuck = (f"goal: {payload.get('stuck_goal', '')}\n"
                 f"needed: {payload.get('needed_property', '')}")
        try:
            run_agent_step(
                system_prompt=ax_system,
                user_prompt=load_prompt("axiom_propose", backend=backend_name,
                                        iid=instance_id, stuck=stuck,
                                        root=tasks_root_rel()),
                cwd=str(PROJECT_ROOT),
                timeout_s=min(_remaining(), cfg.proof_gen),
                model=model, submit_step="axiom_propose")
        except Exception as e:
            last = f"(axiom-propose error: {e}); {last}"
    return False, (f"G-VERIFY still failing after {attempts} proof attempt(s) "
                   f"(axiom-refinement): {last}")
