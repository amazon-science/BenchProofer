# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Adversarial counterexample audit — the scored difference between the ears
audited eval modes (5/6/3) and their unaudited twins (0/1/3).

Per PASSED submission: an adversary agent gets the lean sibling's FORMAL spec
view (ground truth), the bundle's EARS requirements (privileged — provided
whether or not the evaluated agent's mode showed them), the issue, the hidden
tests, and a checkout with the agent patch applied. It hunts for a concrete
behavior where the accepted patch violates the ground truth despite passing
the hidden tests, encoded as a standalone python counterexample script
(exit 0 iff the CORRECT behavior holds). Every claim is then validated
MECHANICALLY — the agent's verdict is never trusted:
  run_probe under the AGENT patch  → must NOT hold (violation is real)
  run_probe under the GOLD patch   → must hold (the expectation is correct)
Categories: real (demotes pass) / bad_test / not_reproduced / inconclusive /
clean. Prompt text lives in the registry (adversary_system / adversary_task).

Only `real` moves a grade, and only downward: the gold-patch check is what
separates a genuine ground-truth violation from a probe that is simply wrong
about the required behavior.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from ..paths import PROJECT_ROOT, TASKS_ROOT, mirror_dir
from ..prompts import load_prompt

AGENT_TIMEOUT = int(os.environ.get("SBU_ADVERSARY_TIMEOUT", "1800"))


def _lean_spec_view(instance_id: str) -> str | None:
    """Ground truth: the lean formal sibling's spec regions."""
    sol = TASKS_ROOT / instance_id / "lean" / "Solution.lean"
    if not sol.exists():
        return None
    try:
        from ..backends import get_backend
        from ..markers import spec_view
        return spec_view(sol.read_text(), get_backend("lean").language)
    except Exception:  # noqa: BLE001 — a raw view beats no ground truth
        return sol.read_text()


def _mirror(instance_id: str) -> Path:
    row = json.loads((TASKS_ROOT / instance_id / "instance.json").read_text())
    return mirror_dir(row["repo"])


def _materialize_worktree(instance_id: str, patch: str, dest: Path) -> bool:
    row = json.loads((TASKS_ROOT / instance_id / "instance.json").read_text())
    mirror = _mirror(instance_id)
    if dest.exists():
        subprocess.run(["git", "-C", str(mirror), "worktree", "remove",
                        str(dest), "--force"], capture_output=True)
        shutil.rmtree(dest, ignore_errors=True)
    r = subprocess.run(["git", "-C", str(mirror), "worktree", "add", "-f",
                        str(dest), row["base_commit"]],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return False
    p = subprocess.run(["git", "-C", str(dest), "apply", "-"],
                       input=patch, capture_output=True, text=True)
    return p.returncode == 0


def _cleanup_worktree(instance_id: str, dest: Path) -> None:
    mirror = _mirror(instance_id)
    subprocess.run(["git", "-C", str(mirror), "worktree", "remove", str(dest),
                    "--force"], capture_output=True)
    shutil.rmtree(dest, ignore_errors=True)
    subprocess.run(["git", "-C", str(mirror), "worktree", "prune"],
                   capture_output=True)


def categorize(under_agent: dict, under_gold: dict | None) -> tuple[str, str]:
    """Pure mapping from the two mechanical probe legs to a category.
    under_gold is only consulted when the agent leg shows a violation."""
    if not under_agent["completed"]:
        return "inconclusive", f"agent-leg: {under_agent['summary']}"
    if under_agent["holds"]:
        return "not_reproduced", "behavior HOLDS under the agent patch"
    assert under_gold is not None
    if not under_gold["completed"]:
        return "inconclusive", f"gold-leg: {under_gold['summary']}"
    if not under_gold["holds"]:
        return "bad_test", "expectation FAILS under gold too (auditor wrong)"
    return "real", "violated under agent patch; holds under gold"


def _validate(instance_id: str, cex: Path, agent_patch: str) -> tuple[str, str]:
    from ..nl_attack import run_probe
    under_agent = run_probe(instance_id, cex, patch_text=agent_patch)
    under_gold = None
    if under_agent["completed"] and not under_agent["holds"]:
        under_gold = run_probe(instance_id, cex)
    return categorize(under_agent, under_gold)


def audit_product(instance_id: str, agent_patch: str, out_dir: Path, *,
                  tag: str = "eval", backend: str = "ears",
                  timeout: int = AGENT_TIMEOUT) -> dict:
    """Audit ONE passed submission; returns the record (also persisted to
    out_dir/record.json, which makes the call resumable). category="real" is
    the only demoting outcome; inconclusive is surfaced, never a demotion —
    infra noise must not masquerade as a ground-truth violation."""
    patch_sha = hashlib.sha256(agent_patch.encode()).hexdigest()[:16]
    rec: dict = {"instance_id": instance_id, "patch_sha": patch_sha,
                 "audited_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    out_dir.mkdir(parents=True, exist_ok=True)
    done_marker = out_dir / "record.json"
    if done_marker.exists():
        # reuse ONLY a record for THIS patch: a crashed run_one can resume
        # with a different submission, and a stale verdict must not stick
        try:
            cached = json.loads(done_marker.read_text())
            if cached.get("patch_sha") == patch_sha:
                return cached
        except json.JSONDecodeError:
            pass                                   # rewrite a corrupt record
    if not agent_patch.strip():
        rec.update(category="inconclusive", detail="empty agent patch")
        done_marker.write_text(json.dumps(rec, indent=2))
        return rec

    from ..agent import run_agent_step

    # unique per-attempt scratch/worktree: the uuid suffix makes duplicate
    # scheduling of one (run, instance) — or two processes sharing a run_id —
    # unable to rmtree each other's live dirs
    nonce = uuid.uuid4().hex[:8]
    scratch = Path("/tmp") / f"adv_{tag}_{instance_id}_{nonce}"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "agent.patch").write_text(agent_patch)
    (scratch / "formal_spec.lean").write_text(
        _lean_spec_view(instance_id) or "-- unavailable")
    wt = Path("/tmp") / f"adv_{tag}_wt_{instance_id}_{nonce}"
    try:
        if not _materialize_worktree(instance_id, agent_patch, wt):
            rec.update(category="inconclusive", detail="worktree/apply failed")
            done_marker.write_text(json.dumps(rec, indent=2))
            return rec
        system = load_prompt("adversary_system", backend=backend)
        task = load_prompt("adversary_task", backend=backend,
                           instance_id=instance_id, scratch=scratch, wt=wt,
                           bundle=TASKS_ROOT / instance_id / backend,
                           inst=TASKS_ROOT / instance_id, root=PROJECT_ROOT)
        try:
            outcome = run_agent_step(system_prompt=system, user_prompt=task,
                                     cwd=str(PROJECT_ROOT), timeout_s=timeout,
                                     submit_step="adversary")
            payload = outcome.payload or {}
        except Exception as e:  # noqa: BLE001
            rec.update(category="inconclusive", detail=f"agent error: {e}")
            done_marker.write_text(json.dumps(rec, indent=2))
            return rec
        rec["agent_verdict"] = str(payload.get("verdict", ""))
        rec["diverging_input"] = str(payload.get("diverging_input", ""))[:400]
        rec["notes"] = str(payload.get("notes", ""))[:800]
        cex = payload.get("counterexample")
        if outcome.submission_count == 0 or rec["agent_verdict"] not in (
                "clean", "counterexample"):
            # "clean" must be an EXPLICIT verdict — an auditor that dies or
            # wanders off without submitting is a non-audit, not a clean bill
            rec.update(category="inconclusive",
                       detail=f"no/malformed verdict "
                              f"(submissions={outcome.submission_count}, "
                              f"verdict={rec['agent_verdict']!r})")
        elif rec["agent_verdict"] != "counterexample" or not cex:
            rec.update(category="clean", detail="no counterexample claimed")
        else:
            cex_path = Path(str(cex))
            if cex_path.is_file():
                saved = out_dir / "cex.py"
                shutil.copy2(cex_path, saved)
                rec["cex"] = str(saved)
                cat, detail = _validate(instance_id, saved, agent_patch)
                rec.update(category=cat, detail=detail)
            else:
                rec.update(category="inconclusive",
                           detail="claimed counterexample file missing")
        done_marker.write_text(json.dumps(rec, indent=2))
        return rec
    finally:
        _cleanup_worktree(instance_id, wt)
        shutil.rmtree(scratch, ignore_errors=True)
