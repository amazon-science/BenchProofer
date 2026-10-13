# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Shared substrate for the agentic audit gates (G-EQ / G-PANEL): gates READ
the verdict recorded in meta.json by the P2 audit stage (the record_audit
convention); RUNNING an audit agent is construct-mode work (`run_audit`), and
its self-report is recorded, never trusted as a mechanical verdict."""
from __future__ import annotations

from .base import Bundle, GateResult

# record_audit's _VALID set. NOT "relaxed": leakage relaxation is a G-LEAK
# concept; a relaxed-leakage panel is recorded as "pass" + note.
VALID_AUDIT_STATUSES = ("pass", "fail", "blocked", "skip")


def recorded_verdict(bundle: Bundle, gate_name: str,
                     fallback_keys: tuple[str, ...] = ()) -> GateResult | None:
    """Recorded agentic verdict from meta.json (or a `fallback_keys` legacy
    entry), else None."""
    gates_blob = bundle.meta().get("gates", {})
    for key in (gate_name, *fallback_keys):
        entry = gates_blob.get(key)
        if not isinstance(entry, dict):
            continue
        status = entry.get("status")
        if status not in VALID_AUDIT_STATUSES:
            continue
        # Require the record_audit shape (a `note`): run_gates re-records this
        # gate's own result under the same key, and that echo must not read
        # back as a verdict or a one-time "skip" would self-perpetuate.
        if "note" not in entry:
            continue
        note = entry.get("note", "")
        data = {"recorded": True, "recorded_as": key}
        for k in ("model", "audited_by", "audit_verdict"):
            if k in entry:
                data[k] = entry[k]
        return GateResult(gate_name, status, note, data)
    return None


def run_audit(bundle: Bundle, role: str, *, timeout_s: int = 3600,
              scratch_out: dict | None = None) -> dict:
    """Construct-mode P2: run one audit agent for `role`, returning its
    payload; the CALLER records it into meta.json. Raises PromptNotFound.

    Each agent gets a FRESH, isolated scratch dir (passed as {scratch}) so it is
    not distracted by stale attack files left in a shared /tmp by prior runs. The
    scratch path is returned in the payload as `_scratch` so the CALLER can clean
    it AFTER the verdict derivation re-runs the agent's attack files (deleting it
    here would remove the very attacks _derive_audit_verdict must re-check).

    `scratch_out`, if given, receives `_scratch` the moment the directory exists,
    so a caller can clean up on the paths where this function RAISES and returns
    no payload at all. Handing the path back only in the return value leaked it
    exactly when the run went wrong -- a timeout, an auth failure -- which is also
    when the tree is largest and when its evidence is most worth keeping. The
    caller decides; this only makes the decision available to it."""
    import tempfile
    from ..agent import run_agent_step
    from ..prompts import load_prompt

    scratch = tempfile.mkdtemp(
        prefix=f"sbu_audit_{role}_{bundle.instance_id[:20]}_", dir="/tmp")
    if scratch_out is not None:
        scratch_out["_scratch"] = scratch
    system_prompt = load_prompt(f"audit_{role}", backend=bundle.backend.name)
    user_prompt = load_prompt(f"audit_{role}_task",
                              backend=bundle.backend.name,
                              instance_id=bundle.instance_id,
                              bundle_dir=str(bundle.root),
                              scratch=scratch)
    outcome = run_agent_step(system_prompt=system_prompt,
                             user_prompt=user_prompt,
                             cwd=str(bundle.root), timeout_s=timeout_s,
                             submit_step=f"audit_{role}")
    payload = outcome.payload or {}
    payload["_scratch"] = scratch
    return payload
