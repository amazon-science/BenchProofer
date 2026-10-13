#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Author the G-PBT `properties.py` battery for ONE pro cell, then read the
verdict back read-only.

Why this exists rather than `build_one --pbt`: build_one's P1.8 authoring stage
is reachable only by re-running construction, which rewrites the instance's
frozen `instance.json`/`patch.diff`, re-stamps `meta.json` whole-file, and
(with --force) OVERWRITES `BLOCKED.md` with an 8-line auto-stub — destroying
multi-page analyses (CLAUDE.md, "Hygiene that bit twice"). This driver calls the
authoring step directly, exactly as `audit_one.py` calls `run_audit_stage`, and
touches nothing but `<bundle>/properties.py`.

Two modes:
  author (default)  prompts/shared/pbt_author.md  — derive the battery from the
                    bundle + gold patch + F2P tests.
  --port-from <bk>  prompts/shared/pbt_port.md    — port the sibling backend's
                    already-validated battery (Phase D of docs/pro-pbt-plan.md).
                    Refuses if the source battery does not exist.

After authoring it runs G-PBT with `record=False`. The stamp is deliberately NOT
written here: per CLAUDE.md "fix-then-re-derive", stamping is a separate
measured pass at bounded width (`pbt_stamp.py`), and a verdict measured while 100
authors are hammering the box is not one to commit.

Usage:
  python3 experiments/pro2026/pbt_author_one.py <instance_id> <backend> \
      [--port-from nagini] [--timeout 2400] [--force] [--json]

Exit: 0 authored (whatever the verdict), 1 no manifest written, 2 usage/refusal.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("SBU_BENCHMARK", "swe_bench_pro_python")
os.environ.setdefault("SBU_BENCHMARK_DIR", "benchmark-pro")
os.environ.setdefault("SBN_VERIFY_TIMEOUT", "900")
# BOTH knobs, and they are NOT the same one. `SBN_VERIFY_TIMEOUT` is what the
# backend verify scripts read; the G-PBT gate reads `SBU_PBT_VERIFY_TIMEOUT`
# (gates/pbt.py:167) whose default is only 300s, and it passes its own value DOWN
# per case, overwriting SBN_VERIFY_TIMEOUT. Measured 2026-08-18 on
# ansible-be2c376a: two rivals take 280.2s and 227.6s serially — inside 1.1x of
# 300s — so at the default cap they are recorded `inconclusive`, which forces
# MALFORMED-TESTS for the whole cell. Setting only SBN_VERIFY_TIMEOUT (as this
# file did until now) left every authoring-time read-back on the 300s cap, which
# is the likelier cause of the one Phase C MALFORMED-TESTS that later stamped
# SOUND than the concurrency I first blamed.
os.environ.setdefault("SBU_PBT_VERIFY_TIMEOUT", "900")

BENCHMARK_DIR = "benchmark-pro"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("instance_id")
    ap.add_argument("backend", choices=("nagini", "velvet", "lean"))
    ap.add_argument("--port-from", choices=("nagini", "velvet", "lean"),
                    default=None)
    ap.add_argument("--timeout", type=int,
                    default=int(os.environ.get("SBU_PBT_AUTHOR_TIMEOUT", "2700")))
    ap.add_argument("--model", default=None)
    ap.add_argument("--force", action="store_true",
                    help="re-author even if properties.py already exists")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    iid, bk = args.instance_id, args.backend
    bundle_dir = ROOT / BENCHMARK_DIR / iid / bk
    if not bundle_dir.is_dir():
        print(f"no such bundle: {bundle_dir}", file=sys.stderr)
        return 2
    manifest = bundle_dir / "properties.py"
    if manifest.is_file() and not args.force:
        print(f"properties.py already exists ({manifest.stat().st_size:,}B); "
              f"pass --force to re-author")
        return 0
    if bk == "nagini":
        # bound Z3 fan-out per cell (scripts/regate_fleet.py:66)
        os.environ.setdefault("SBU_MUTATION_WORKERS", "1")

    from swebench_unified import paths
    from swebench_unified.agent import DEFAULT_MODEL, run_agent_step
    from swebench_unified.prompts import load_prompt

    out: dict = {"iid": iid, "backend": bk, "mode": "author"}

    if args.port_from:
        src_bk = args.port_from
        if src_bk == bk:
            print("--port-from must name a DIFFERENT backend", file=sys.stderr)
            return 2
        src = ROOT / BENCHMARK_DIR / iid / src_bk / "properties.py"
        if not src.is_file():
            print(f"REFUSING: no source battery to port from ({src}). "
                  f"Author {src_bk} first (docs/pro-pbt-plan.md: nagini before "
                  f"the port).", file=sys.stderr)
            return 2
        out["mode"] = f"port:{src_bk}"
        user = load_prompt("pbt_port", backend=bk, iid=iid, backend_name=bk,
                           root=paths.tasks_root_rel(), src_backend=src_bk)
    else:
        user = load_prompt("pbt_author", backend=bk, iid=iid, backend_name=bk,
                           root=paths.tasks_root_rel())

    system = load_prompt("pbt_author_system", backend=bk)
    model = args.model or DEFAULT_MODEL

    print(f"[pbt_author_one] {bk}/{iid} ({out['mode']}) timeout={args.timeout}s",
          flush=True)
    t0 = time.monotonic()
    try:
        step = run_agent_step(system_prompt=system, user_prompt=user,
                              cwd=str(paths.PROJECT_ROOT),
                              timeout_s=args.timeout, model=model,
                              submit_step="pbt_author")
        out["payload"] = getattr(step, "payload", None)
    except Exception as e:  # a dead agent must not look like a clean skip
        out["agent_error"] = f"{type(e).__name__}: {e}"
        print(f"  agent error: {out['agent_error']}", flush=True)
    out["author_s"] = round(time.monotonic() - t0, 1)

    if not manifest.is_file():
        out["status"] = "no-manifest"
        print(f"  NO properties.py written after {out['author_s']}s")
        if args.json:
            print(json.dumps(out, indent=2, default=str))
        return 1
    out["status"] = "authored"
    out["bytes"] = manifest.stat().st_size

    # Read the verdict back, read-only. record=False deliberately: stamping is a
    # separate bounded-width pass (pbt_stamp.py).
    from swebench_unified.gates import run_gates
    try:
        res = run_gates(iid, bk, ["G-PBT"], mode="strict", record=False)
        r = res[0]
        out["verdict"] = (r.data or {}).get("verdict", "?")
        out["gate_status"] = r.status
        out["n_cases"] = (r.data or {}).get("n_cases", 0)
        out["n_failed"] = (r.data or {}).get("n_failed", 0)
        out["detail"] = str(r.detail)[:600]
        out["cases"] = [{k: c.get(k) for k in ("id", "kind", "expect", "ok",
                                               "outcome", "wall_s")}
                        for c in (r.data or {}).get("cases", [])]
    except Exception as e:
        out["verdict"] = "RUN-ERROR"
        out["detail"] = f"{type(e).__name__}: {e}"

    print(f"  {out['status']} {out['bytes']:,}B  verdict={out['verdict']} "
          f"({out.get('n_cases', 0)} cases, {out.get('n_failed', 0)} failed) "
          f"in {out['author_s']}s", flush=True)
    if args.json:
        print(json.dumps(out, indent=2, default=str))
    (Path(os.environ.get("SBU_PBT_RESULT_DIR", "/tmp"))
     / f"pbt_author_{bk}_{iid}.json").write_text(
        json.dumps(out, indent=2, default=str) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
