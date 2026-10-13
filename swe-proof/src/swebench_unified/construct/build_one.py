# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Per-instance construction loop -- the agentic lifecycle
(docs/architecture.md §3), parameterized by backend. The layout is split:
immutable inputs at <root>/<id>/, the bundle at <root>/<id>/<backend>/, so one
frozen input set is shared by every backend rather than copied per backend.

The stages in the order `build_one` runs them; the phase numbers are the ones
the records and the prompts use, so they are not consecutive here:

  P0    prepare              freeze the inputs, materialize a /tmp worktree
                             at base_commit
  P1    construct            the construction agent, driven by feedback-mode
                             CONSTRUCT gates and the elaborate check, for
                             <= max_rounds refine rounds
  P1.5  prove (lean only)    ../prove.py; "ok" only from the mechanical
                             G-VERIFY re-check, never the agent's self-report
  P1.8  author_pbt_manifest  optional: the G-PBT spec-lane manifest
  P1.6  run_gate_sweeps      the strict STATIC sweep, then the DOCKER gates
        + P1.7               if static is clean
  P2    run_audit_stage      optional: the adversarial audit (audit_stage.py)

Writes result.json with final_status (ok | blocked | timeout). Resumable: an
already-ok bundle is skipped unless --force. A principled BLOCKED (no solution
file + meta.json status=blocked + BLOCKED.md) is terminal without clobbering
the agent's breadcrumb.

P2 lives in four siblings, none of it on the construction path: `audit_roles`
holds the role table, `audit_verdict` re-derives a gate status from the
artifacts an agent submitted, `verdict_record` composes verdict.md, and
`audit_stage` drives the agents.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from .. import paths
from ..backends.registry import BACKENDS
from ..config import CONSTRUCT_TIMEOUT_DEFAULT, VERIFY_TIMEOUT_DEFAULT, ProofConfig
from ..gates import CONSTRUCT_GATES, DOCKER_GATES, STATIC_GATES, run_gates
from ..gates._common import check_bundle_file
from ..gates.base import Bundle, GateResult, load_frozen_row
from ..greenness import is_green
from .audit_stage import run_audit_stage

# This module is the import surface for the audit stage as well as the entry
# point for a build, and `run_audit_stage` is imported from here by STRING in a
# subprocess (`from swebench_unified.construct.build_one import
# run_audit_stage`). Re-export rather than move a caller.
from .audit_roles import (  # noqa: F401
    AUDIT_ROLE_TIMEOUT_DEFAULT, MIN_ATTACKS_DEFAULT, _AUDIT_AGENTS,
    _GATE_DERIVE_ROLE, _GATE_ROLE_LABEL, _ROLE_READS)
from .audit_stage import _elide  # noqa: F401
from .audit_verdict import (  # noqa: F401
    _derive_audit_verdict, _derive_ears_verdict, _patch_payload_text,
    _ungradeable_because_of_the_patch)
from .verdict_record import (  # noqa: F401
    CONTROL_IS_BASELINE, DIFF_CAPTION, DIFF_LEAD_IN, _attack_excerpt,
    _keeps_prior_verdict, _render_attack_block, compose_verdict_md,
    merge_verdict_md)

# Declared so the re-exports above are part of the surface for a type checker
# too, not only at runtime; the underscored ones are read by the gate tests.
__all__ = [
    "AUDIT_ROLE_TIMEOUT_DEFAULT", "CONTROL_IS_BASELINE", "DIFF_CAPTION",
    "DIFF_LEAD_IN", "MIN_ATTACKS_DEFAULT", "_AUDIT_AGENTS", "_GATE_DERIVE_ROLE",
    "_GATE_ROLE_LABEL", "_ROLE_READS", "_attack_excerpt",
    "_derive_audit_verdict", "_derive_ears_verdict", "_elide",
    "_keeps_prior_verdict", "_patch_payload_text", "_render_attack_block",
    "_ungradeable_because_of_the_patch", "already_green",
    "author_pbt_manifest", "build_one", "cleanup_worktree", "compose_verdict_md",
    "construct", "final_status_of", "main", "merge_verdict_md", "prepare",
    "result_path", "run_audit_stage", "run_gate_sweeps",
]


def _mirror(repo: str, repo_path: str | None = None) -> Path:
    """Local git dir for a task repo. `repo_path` (CLI --repo) points directly
    at a user-supplied clone; else the mirror the clone step made, named by
    `paths.mirror_dir` so this and setup_repos.py cannot disagree."""
    if repo_path:
        return Path(repo_path).expanduser()
    return paths.mirror_dir(repo)


def _worktree_path(instance_id: str, backend_name: str) -> Path:
    # Keyed by (run-prefix, backend, instance): backends may build the same
    # instance in parallel and must not clobber each other's worktree.
    return Path("/tmp") / f"wt_{paths.RUN_PREFIX}_{backend_name}_{instance_id}"


def prepare(instance_id: str, backend_name: str, row: dict,
            repo_path: str | None = None) -> tuple[Path, str | None]:
    """P0: freeze instance.json + patch.diff into the INSTANCE root, stamp
    cold provenance into the bundle's meta.json, materialize a worktree at
    base_commit. Returns (worktree_path, error)."""
    inst = paths.instance_dir(instance_id)
    inst.mkdir(parents=True, exist_ok=True)
    (inst / "instance.json").write_text(json.dumps(row))
    (inst / "patch.diff").write_text(row["patch"])
    bundle = paths.bundle_dir(instance_id, backend_name)
    bundle.mkdir(parents=True, exist_ok=True)
    # build_one is cold-only (the worker prompt's COLD directive)
    meta_p = bundle / "meta.json"
    meta = {}
    if meta_p.exists():
        try:
            meta = json.loads(meta_p.read_text())
        except json.JSONDecodeError:
            meta = {}
    meta["spec_provenance"] = "cold"
    meta_p.write_text(json.dumps(meta, indent=2))
    mirror = _mirror(row["repo"], repo_path)
    if not mirror.exists():
        hint = ("check --repo PATH" if repo_path else
                "clone it (SBU_REPOS_ROOT or scripts/setup_repos.py) or pass --repo PATH")
        return Path(), f"no repo clone at {mirror} ({hint})"
    wt = _worktree_path(instance_id, backend_name)
    if wt.exists():
        subprocess.run(["git", "-C", str(mirror), "worktree", "remove", str(wt),
                        "--force"], capture_output=True)
        shutil.rmtree(wt, ignore_errors=True)
    r = subprocess.run(["git", "-C", str(mirror), "worktree", "add", "-f",
                        str(wt), row["base_commit"]], capture_output=True, text=True)
    if r.returncode != 0:
        return Path(), f"worktree add failed: {r.stderr.strip()[:200]}"
    return wt, None


def cleanup_worktree(instance_id: str, backend_name: str, row: dict,
                     repo_path: str | None = None) -> None:
    wt = _worktree_path(instance_id, backend_name)
    mirror = _mirror(row["repo"], repo_path)
    subprocess.run(["git", "-C", str(mirror), "worktree", "remove", str(wt),
                    "--force"], capture_output=True)
    shutil.rmtree(wt, ignore_errors=True)


def _elaborate_check(instance_id: str, backend_name: str) -> tuple[bool, str]:
    """P1 elaborate check: nagini/velvet — checker must PASS outright; lean —
    sorry-only (exit 3) is valid, the proof comes in P1.5. Keyed on the exit
    code, never on output strings, which a checker may reword."""
    from ..backends import get_backend
    bundle = Bundle(instance_id, get_backend(backend_name))
    sol = bundle.solution
    if not sol.exists():
        return False, f"{sol.name} missing"
    r = check_bundle_file(bundle, sol, VERIFY_TIMEOUT_DEFAULT)
    if r.success:
        return True, "checker passes"
    if backend_name == "lean" and r.sorry_only:  # exit 3: only sorry/admit remains
        return True, "spec+impl+statement elaborate (only sorry remains)"
    return False, (f"spec/impl do not pass the {backend_name} checker "
                   f"(exit {r.returncode}): {r.summary}")


def _counterexamples(results: list[GateResult]) -> str:
    bad = [r for r in results if not r.ok]
    if not bad:
        return ""
    return "\n".join(f"- {r.gate}: {r.status} — {r.detail}" for r in bad)


def construct(instance_id: str, backend_name: str, wt: Path, max_rounds: int,
              construct_timeout: int, model: str | None) -> tuple[bool, str]:
    """P1: run the construction agent (spec + impl; lean proof left as `by
    sorry`) with <= max_rounds refine iterations driven by gate
    counterexamples + the elaborate check. Returns (ok, note)."""
    from ..agent import DEFAULT_MODEL, run_agent_step
    from ..prompts import load_prompt

    model = model or DEFAULT_MODEL
    system = load_prompt("construct_system", backend=backend_name)
    base_prompt = load_prompt("worker", backend=backend_name, iid=instance_id,
                              root=paths.tasks_root_rel())
    base_prompt += (f"\n\n## Worktree (already materialized)\n"
                    f"The repo at base_commit is checked out at `{wt}` "
                    f"(changed file(s) per the gold patch.diff). Do NOT create "
                    f"your own worktree. Write the bundle into "
                    f"`{paths.tasks_root_rel()}/{instance_id}/{backend_name}/`.\n")

    prev = ""
    for rnd in range(1, max_rounds + 1):
        prompt = base_prompt
        if prev:
            prompt += (f"\n\n## Refine round {rnd}: the previous attempt FAILED "
                       f"— fix these (never weaken a contract):\n{prev}\n")
        try:
            run_agent_step(system_prompt=system, user_prompt=prompt,
                           cwd=str(paths.PROJECT_ROOT), timeout_s=construct_timeout,
                           model=model, submit_step="construct")
        except Exception as e:  # agent CLI / timeout error -> retry the round
            prev = f"(agent error: {e}); re-attempt"
            continue
        elaborates, enote = _elaborate_check(instance_id, backend_name)
        results = run_gates(instance_id, backend_name, list(CONSTRUCT_GATES),
                            mode="feedback", record=False)
        gates_ok = all(r.ok for r in results)
        if elaborates and gates_ok:
            return True, f"spec+impl built after {rnd} round(s) ({enote})"
        prev = (("" if elaborates else f"- elaboration: {enote}\n")
                + _counterexamples(results))
    return False, f"construction still failing after {max_rounds} rounds:\n{prev}"


def author_pbt_manifest(instance_id: str, backend_name: str,
                        timeout_s: int, model: str | None) -> str:
    """P1.8: author the bundle's properties.py (G-PBT spec-lane manifest) with
    one agent step. Requires a green spec+impl (region surgery reads the frozen
    solution). Returns a note; the manifest itself is judged mechanically by
    G-PBT in the strict sweep, never by the agent's self-report."""
    from ..agent import DEFAULT_MODEL, run_agent_step
    from ..prompts import load_prompt

    model = model or DEFAULT_MODEL
    system = load_prompt("pbt_author_system", backend=backend_name)
    user = load_prompt("pbt_author", backend=backend_name, iid=instance_id,
                       backend_name=backend_name, root=paths.tasks_root_rel())
    try:
        run_agent_step(system_prompt=system, user_prompt=user,
                       cwd=str(paths.PROJECT_ROOT), timeout_s=timeout_s,
                       model=model, submit_step="pbt_author")
    except Exception as e:
        return f"pbt authoring agent error: {e}"
    p = paths.bundle_dir(instance_id, backend_name) / "properties.py"
    return "authored properties.py" if p.exists() else "no properties.py written"


def final_status_of(results: list[GateResult]) -> str:
    if any(r.status in ("fail", "error") for r in results):
        return "blocked"
    if any(r.status == "timeout" for r in results):
        return "timeout"
    return "ok"


def run_gate_sweeps(instance_id: str, backend_name: str, *,
                    skip_docker: bool) -> list[GateResult]:
    """P1.6 then P1.7: the full STATIC sweep in strict mode, and the DOCKER gates
    only if static came back clean -- a docker gate pulls an image and runs the
    instance's test suite, which a bundle that already failed a static gate must
    not be made to pay for."""
    results = run_gates(instance_id, backend_name, list(STATIC_GATES),
                        mode="strict", record=True)
    if not skip_docker and final_status_of(results) == "ok":
        results += run_gates(instance_id, backend_name, list(DOCKER_GATES),
                             mode="strict", record=True)
    return results


def result_path(instance_id: str, backend_name: str) -> Path:
    return paths.bundle_dir(instance_id, backend_name) / "result.json"


def already_green(instance_id: str, backend_name: str) -> bool:
    """This cell is finished, so a resumed run skips it unless --force.

    Two questions, because the cheap one does not travel. `result.json` is this
    builder's own completion marker and is not part of a bundle: the shipped
    corpora carry none for the proof backends, so a fresh clone asking only that
    would spend an agent run on all 500 already-green cells of a green corpus --
    the reproduction step reading as a build from scratch.

    The answer that does travel is the RECORDED gate verdicts, read through
    `greenness.is_green` -- the same predicate the release gate, the review site
    and the repair drivers use. Nothing is re-derived here: a driver with its own
    notion of green disagrees with the gate about exactly the cells it is
    spending on. Strictly harder to satisfy than the marker (it demands every
    mechanical gate, real G-CONF/G-PBT verdicts and a complete audit), so this
    cannot skip a cell that still needs work.
    """
    p = result_path(instance_id, backend_name)
    if p.exists():
        try:
            if json.loads(p.read_text()).get("final_status") == "ok":
                return True
        except json.JSONDecodeError:
            pass
    meta = paths.bundle_dir(instance_id, backend_name) / "meta.json"
    try:
        gates = json.loads(meta.read_text()).get("gates") or {}
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    return bool(gates) and is_green(gates)


def _persist(out: dict, start: float) -> dict:
    """Write result.json for ANY terminal status. Resume/skip keys off this
    file, so without it a blocked instance is re-run from scratch."""
    out["wall_time_s"] = round(time.monotonic() - start, 1)
    p = result_path(out["instance_id"], out["backend"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2))
    return out


def _is_principled_block(instance_id: str, backend_name: str) -> bool:
    """The agent may legitimately ship NO solution file and instead write
    meta.json(status=blocked) + BLOCKED.md; record as terminal without
    clobbering its BLOCKED.md."""
    from ..backends import get_backend
    bundle = Bundle(instance_id, get_backend(backend_name))
    if bundle.solution.exists():
        return False
    return bundle.meta().get("status") == "blocked"


def build_one(instance_id: str, backend_name: str, *, max_rounds: int = 8,
              proof_cfg: ProofConfig | None = None,
              construct_timeout: int = CONSTRUCT_TIMEOUT_DEFAULT,
              skip_docker: bool = False, audit: bool = False, pbt: bool = False,
              force: bool = False, model: str | None = None,
              repo_path: str | None = None) -> dict:
    start = time.monotonic()
    proof_cfg = proof_cfg or ProofConfig()
    out: dict = {"instance_id": instance_id, "backend": backend_name}
    # per-phase wall-clock, recorded on every terminal path
    out["phase_times"] = {}

    def _phase(name: str, t0: float) -> None:
        out["phase_times"][name] = round(time.monotonic() - t0, 1)

    if already_green(instance_id, backend_name) and not force:
        out["final_status"] = "ok"
        out["note"] = "already green (skipped; use --force to rebuild)"
        return out  # existing (richer) result.json stands; don't overwrite

    row = load_frozen_row(instance_id)
    if row is None:
        out["final_status"] = "blocked"
        out["note"] = "not in frozen dataset"
        return _persist(out, start)

    # A parent's wall-clock SIGTERM would skip the `finally:` below, leaking a
    # /tmp worktree big enough that an N-way run exhausts the tmpfs inode table.
    # Clean the worktree, then restore the default disposition and re-raise so
    # the parent's timeout still records 124: a wall-clock kill must stay
    # distinguishable from a verification failure.
    def _on_term(signum, frame):
        cleanup_worktree(instance_id, backend_name, row, repo_path)
        signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)

    # signal.signal is only legal in the MAIN thread, so skip the handlers when
    # a caller runs build_one inside a ThreadPoolExecutor: the `finally:` still
    # cleans the worktree on every non-signal path, and the parent process owns
    # signal handling.
    import threading
    _in_main = threading.current_thread() is threading.main_thread()
    prev_term = signal.signal(signal.SIGTERM, _on_term) if _in_main else None
    prev_int = signal.signal(signal.SIGINT, _on_term) if _in_main else None

    bundle_root = paths.bundle_dir(instance_id, backend_name)
    t_prepare = time.monotonic()
    wt, err = prepare(instance_id, backend_name, row, repo_path)
    _phase("p0_prepare", t_prepare)
    if err:
        if _in_main:
            signal.signal(signal.SIGTERM, prev_term)
            signal.signal(signal.SIGINT, prev_int)
        out["final_status"] = "blocked"
        out["note"] = f"P0 prepare failed: {err}"
        return _persist(out, start)

    try:
        # P1 — construct spec + impl (lean: proof left as `by sorry`)
        t_construct = time.monotonic()
        construct_ok, cnote = construct(instance_id, backend_name, wt,
                                        max_rounds, construct_timeout, model)
        _phase("p1_construct", t_construct)
        out["construct_note"] = cnote
        if not construct_ok:
            if _is_principled_block(instance_id, backend_name):
                # leave the agent's own BLOCKED.md untouched
                out["final_status"] = "blocked"
                out["note"] = "principled BLOCKED (no solution file by design)"
            else:
                (bundle_root / "BLOCKED.md").write_text(
                    f"# BLOCKED: {instance_id} ({backend_name})\n\n"
                    f"Construction (spec+impl) did not pass in {max_rounds} "
                    f"rounds.\n\n{cnote}\n")
                out["final_status"] = "blocked"
                out["note"] = cnote
            return _persist(out, start)  # finally: still cleans the worktree

        # P1.5 — lean only: close every correct_<name> under the total
        # proof_gen budget; "ok" only from the mechanical G-VERIFY re-check.
        if backend_name == "lean":
            from ..prove import prove
            t_prove = time.monotonic()
            proof_ok, pnote = prove(instance_id, backend_name, proof_cfg, model)
            _phase("p1_5_prove", t_prove)
            out["proof_note"] = pnote
            if not proof_ok:
                (bundle_root / "BLOCKED.md").write_text(
                    f"# BLOCKED: {instance_id} ({backend_name})\n\nProof did "
                    f"not close within the {proof_cfg.proof_gen}s proof "
                    f"budget.\n\n{pnote}\n")
                out["final_status"] = "blocked"
                out["note"] = pnote
                return _persist(out, start)

        # P1.8 — optional G-PBT manifest authoring (needs the green frozen
        # solution; judged mechanically by G-PBT in the strict sweep below).
        # ears: G-PBT is an explicit skip and properties.py is disallowed by
        # G-INTEGRITY, so never author one.
        if pbt and backend_name == "ears":
            out["pbt_author_note"] = "skipped: G-PBT not applicable to ears"
            pbt = False
        if pbt:
            t_pbt = time.monotonic()
            out["pbt_author_note"] = author_pbt_manifest(
                instance_id, backend_name, construct_timeout, model)
            _phase("p1_8_pbt_author", t_pbt)

        # P1.6 + P1.7 — the strict gate sweeps
        t_gates = time.monotonic()
        results = run_gate_sweeps(instance_id, backend_name,
                                  skip_docker=skip_docker)
        _phase("gates", t_gates)
        out["gates"] = {r.gate: r.status for r in results}
        out["final_status"] = final_status_of(results)
        if out["final_status"] != "ok":
            (bundle_root / "BLOCKED.md").write_text(
                f"# BLOCKED: {instance_id} ({backend_name})\n\nGate failures:\n"
                + _counterexamples(results) + "\n")
            return _persist(out, start)
        # clear any stale BLOCKED.md now that it's green
        bm = bundle_root / "BLOCKED.md"
        if bm.exists():
            bm.unlink()

        # P2 — optional agentic audit (G-EQ / G-PANEL)
        if audit:
            t_audit = time.monotonic()
            audit_results = run_audit_stage(instance_id, backend_name)
            _phase("p2_audit", t_audit)
            out["audit"] = {r.gate: r.status for r in audit_results}
    finally:
        cleanup_worktree(instance_id, backend_name, row, repo_path)
        if _in_main:
            signal.signal(signal.SIGTERM, prev_term)
            signal.signal(signal.SIGINT, prev_int)

    return _persist(out, start)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="unified per-instance construction run (P0->P1->[P1.5]->gates->[P2])")
    ap.add_argument("--backend", required=True,
                    choices=sorted(BACKENDS))
    ap.add_argument("--instance", required=True)
    ap.add_argument("--max-rounds", type=int, default=8,
                    help="P1 construction refine rounds")
    # proof phase (lean only)
    ap.add_argument("--proof-gen-timeout", type=int, default=VERIFY_TIMEOUT_DEFAULT,
                    help="TOTAL wall-clock budget for the P1.5 proof phase (default 300s)")
    ap.add_argument("--max-proof-attempts", type=int, default=1)
    ap.add_argument("--axiom-refinement", action="store_true",
                    help="enable the stuck->axiom-propose->validate loop in P1.5")
    ap.add_argument("--max-axiom-iterations", type=int, default=10)
    ap.add_argument("--construct-timeout", type=int, default=CONSTRUCT_TIMEOUT_DEFAULT)
    ap.add_argument("--skip-docker", action="store_true")
    ap.add_argument("--audit", action="store_true",
                    help="run agentic G-EQ/G-PANEL after gates")
    ap.add_argument("--pbt", action="store_true",
                    help="author the G-PBT spec-lane manifest (properties.py) "
                         "before the strict sweep")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default=None)
    ap.add_argument("--repo", default=None, metavar="PATH",
                    help="path to a local clone/bare mirror of this instance's "
                         "task repo (else repos/<owner>_<name>.git under "
                         "SBU_REPOS_ROOT)")
    args = ap.parse_args(argv)

    proof_cfg = ProofConfig(
        proof_gen=args.proof_gen_timeout,
        max_proof_attempts=args.max_proof_attempts,
        axiom_refinement=args.axiom_refinement,
        max_axiom_iterations=args.max_axiom_iterations,
    )
    out = build_one(args.instance, args.backend, max_rounds=args.max_rounds,
                    proof_cfg=proof_cfg,
                    construct_timeout=args.construct_timeout,
                    skip_docker=args.skip_docker, audit=args.audit,
                    pbt=args.pbt, force=args.force, model=args.model,
                    repo_path=args.repo)
    print(f"[{args.instance}/{args.backend}] {out['final_status']}: "
          f"{out.get('note', out.get('proof_note', out.get('construct_note', '')))} "
          f"{out.get('gates', '')}")
    return 0 if out["final_status"] in ("ok", "timeout") else 1


if __name__ == "__main__":
    sys.exit(main())
