#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Wide agentic fleet for the G-PBT authoring lane (Phases C and D).

## The concurrency split this driver exists to enforce

CLAUDE.md's first rule is that gate verdicts are MEASUREMENTS and lie under load
(the pro repair queue shrank 73 -> 51 -> 24 -> ~11 purely by re-deriving it at
96-way -> 16-way -> 4-way -> serial; ~90% of first-reported defects were
measurement error). It also records that CONSTRUCTION and prose edits parallelise
fine — EARS ran 32-way cleanly.

Authoring a `properties.py` is construction. So this driver runs WIDE (default 80
on the 192-core host), while the verifier load that authors generate is bounded
independently by `pbt_verify.py`'s cross-process semaphore
(SBU_PBT_SLOTS_{NAGINI,LEAN,VELVET}). Fleet width and verifier width are separate
dials on purpose:

    authors: 80 concurrent    (API-bound, ~0 CPU each)
    nagini verifiers: 24      (x4 Z3 threads each = ~96 cores)
    lean/velvet verifiers: 40 (~1-2 cores each)

The G-PBT stamps are NOT written here — `pbt_stamp.py` re-derives them afterwards
at bounded width, because a verdict measured while 80 authors hammer the box is
not one to commit.

## Hazards this driver is built around (all previously measured)

* A `wait`-on-each-batch shell driver let one hung cell block ten others — hence
  ThreadPoolExecutor with an enforced per-cell timeout.
* Resolve/verify legs orphan `pytest`/JVM processes that pin a core indefinitely
  (one found alive after 31.8 hours). `--purge-every` sweeps them periodically.
* `pkill -f <pattern>` matches the driver's own shell and kills the wrapper
  (exit 144), and inflates `pgrep -c`. Orphan purging here kills by explicit PID
  and never by pattern.
* A timeout in a THREADED fleet must kill only its own agent subtree; agent.py
  scopes that with SBU_AGENT_MARK, which is why each cell runs as its own
  subprocess (`pbt_author_one.py`) rather than in-process.

Usage:
  python3 experiments/pro2026/pbt_fleet.py --cells <cells.json> [--jobs 80]
      [--port-from nagini] [--limit N] [--timeout 2700] [--dry-run]
      [--out results.json]

`--cells` accepts either a list of `[backend, iid]` pairs or a list of
`benchmark-pro/<iid>/<backend>` / `.../meta.json` path strings (the form
`pbt_targets.py` and `green_except_pbt.py --commit-list` emit).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = "swe_bench_pro_python"
BENCHMARK_DIR = "benchmark-pro"


def load_cells(spec: Path, backends: list[str] | None) -> list[tuple[str, str]]:
    raw = json.loads(spec.read_text())
    out: list[tuple[str, str]] = []
    for item in raw:
        if isinstance(item, str):
            parts = Path(item).parts
            iid, bk = parts[1], parts[2]
        elif isinstance(item, dict):
            iid, bk = item["iid"], item["backend"]
        else:
            bk, iid = item[0], item[1]
        if backends and bk not in backends:
            continue
        out.append((iid, bk))
    return sorted(set(out))


# --------------------------------------------------------------------------
# orphan purge — by explicit PID, never by pattern (see module docstring)
# --------------------------------------------------------------------------

def purge_orphans(max_age_s: int = 5400) -> int:
    """SIGKILL verifier/eval processes older than max_age_s whose parent is init
    (ppid 1) — i.e. their driver died and left them pinning a core. Returns the
    count killed."""
    import signal
    killed = 0
    try:
        clk = os.sysconf("SC_CLK_TCK")
        with open("/proc/uptime") as fh:
            uptime = float(fh.read().split()[0])
    except (OSError, ValueError):
        return 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            with open(f"/proc/{pid}/stat") as fh:
                data = fh.read()
            after = data[data.rfind(")") + 2:].split()
            ppid = int(after[1])
            starttime = int(after[19])
            comm = data[data.find("(") + 1:data.rfind(")")]
        except (OSError, ValueError, IndexError):
            continue
        if ppid != 1:
            continue
        if comm not in ("java", "z3", "pytest", "python", "python3", "lean",
                        "lake"):
            continue
        age = uptime - (starttime / clk)
        if age < max_age_s:
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as fh:
                cmd = fh.read().decode("utf8", "replace")
        except OSError:
            continue
        if not any(k in cmd for k in ("nagini", "viper", "silicon", "carbon",
                                      "lake env lean", "pytest", "sbu_verify")):
            continue
        try:
            os.kill(pid, signal.SIGKILL)
            killed += 1
        except (ProcessLookupError, PermissionError):
            pass
    return killed


# --------------------------------------------------------------------------

def run_cell(iid: str, bk: str, log_dir: Path, timeout: int,
             port_from: str | None, force: bool, result_dir: Path) -> dict:
    env = dict(os.environ, SBU_BENCHMARK=BENCHMARK,
               SBU_BENCHMARK_DIR=BENCHMARK_DIR,
               SBN_VERIFY_TIMEOUT=env_or("SBN_VERIFY_TIMEOUT", "900"),
               # the gate reads SBU_PBT_VERIFY_TIMEOUT (default 300s), NOT
               # SBN_VERIFY_TIMEOUT -- see pbt_author_one.py for the measurement
               SBU_PBT_VERIFY_TIMEOUT=env_or("SBU_PBT_VERIFY_TIMEOUT", "900"),
               SBU_PBT_RESULT_DIR=str(result_dir),
               # pbt_author_one's final G-PBT read-back calls the gate directly,
               # which does NOT hold pbt_verify.py's semaphore and defaults to
               # SBU_PBT_WORKERS=8. Measured 2026-08-17 mid-sweep: 46 live nagini
               # verifiers against 32 semaphore slots, the overshoot being read-
               # backs of cells finishing at the same moment. Capped at 2 so the
               # unthrottled path cannot push the box past its core count (a
               # verifier timeout is recorded inconclusive => MALFORMED-TESTS, so
               # overshoot costs adjudication rounds).
               SBU_PBT_WORKERS=env_or("SBU_PBT_WORKERS", "2"))
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"]
                               if env.get("PYTHONPATH") else "")
    if bk == "nagini":
        env.setdefault("SBU_MUTATION_WORKERS", "1")

    cmd = [str(ROOT / ".venv" / "bin" / "python"),
           str(ROOT / "experiments" / "pro2026" / "pbt_author_one.py"),
           iid, bk, "--timeout", str(timeout)]
    if port_from:
        cmd += ["--port-from", port_from]
    if force:
        cmd.append("--force")

    log = log_dir / f"{bk}_{iid}.log"
    t0 = time.monotonic()
    rc: int | None = None
    note = ""
    try:
        with log.open("wb") as fh:
            # +240s over the agent's own budget so the inner process gets to
            # write its result json and clean up before we cut it off.
            p = subprocess.run(cmd, cwd=str(ROOT), env=env, stdout=fh,
                               stderr=subprocess.STDOUT, timeout=timeout + 240)
            rc = p.returncode
    except subprocess.TimeoutExpired:
        note = f"driver timeout at {timeout + 240}s"
    except Exception as e:
        note = f"{type(e).__name__}: {e}"

    rec = {"iid": iid, "backend": bk, "rc": rc, "note": note,
           "wall_s": round(time.monotonic() - t0, 1), "log": str(log)}
    rp = result_dir / f"pbt_author_{bk}_{iid}.json"
    if rp.is_file():
        try:
            rec.update(json.loads(rp.read_text()))
        except json.JSONDecodeError:
            rec["note"] = (rec["note"] + " unparsable result json").strip()
    manifest = ROOT / BENCHMARK_DIR / iid / bk / "properties.py"
    rec["has_manifest"] = manifest.is_file()
    return rec


def env_or(name: str, default: str) -> str:
    return os.environ.get(name) or default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", required=True, type=Path)
    ap.add_argument("--jobs", type=int, default=80)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--backends", nargs="*", default=None)
    ap.add_argument("--port-from", default=None,
                    choices=("nagini", "velvet", "lean"))
    ap.add_argument("--timeout", type=int, default=2700,
                    help="per-cell agent budget in seconds")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skip-existing", action="store_true", default=True)
    ap.add_argument("--no-skip-existing", dest="skip_existing",
                    action="store_false")
    ap.add_argument("--purge-every", type=int, default=600,
                    help="seconds between orphan purges (0 disables)")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "experiments" / "pro2026" / "pbt_fleet_results.json")
    ap.add_argument("--log-dir", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cells = load_cells(args.cells, args.backends)
    if args.skip_existing and not args.force:
        before = len(cells)
        cells = [(i, b) for i, b in cells
                 if not (ROOT / BENCHMARK_DIR / i / b / "properties.py").is_file()]
        if before != len(cells):
            print(f"skipping {before - len(cells)} cell(s) that already have a "
                  f"properties.py (--force to re-author)")
    if args.limit:
        cells = cells[:args.limit]

    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_dir = args.log_dir or (ROOT / "experiments" / "pro2026" / "pbt_logs" / stamp)
    log_dir.mkdir(parents=True, exist_ok=True)
    result_dir = Path("/tmp") / f"pbt_results_{stamp}"
    result_dir.mkdir(parents=True, exist_ok=True)

    by_bk = Counter(b for _, b in cells)
    print(f"cells: {len(cells)}  {dict(by_bk)}")
    print(f"jobs: {args.jobs}   per-cell timeout: {args.timeout}s   "
          f"mode: {'port from ' + args.port_from if args.port_from else 'author'}")
    print(f"logs: {log_dir}")
    if args.dry_run:
        for iid, bk in cells[:20]:
            print(f"  {bk:7} {iid}")
        if len(cells) > 20:
            print(f"  ... and {len(cells) - 20} more")
        return 0
    if not cells:
        print("nothing to do")
        return 0

    results: list[dict] = []
    t0 = time.monotonic()
    last_purge = t0
    done = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_cell, iid, bk, log_dir, args.timeout,
                          args.port_from, args.force, result_dir): (iid, bk)
                for iid, bk in cells}
        for fut in as_completed(futs):
            iid, bk = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:
                rec = {"iid": iid, "backend": bk,
                       "note": f"driver crash: {type(e).__name__}: {e}",
                       "has_manifest": False}
            results.append(rec)
            done += 1
            v = rec.get("verdict", "-")
            print(f"[{done}/{len(cells)}] {bk:7} {v:18} "
                  f"{rec.get('n_cases', 0):>3}c/{rec.get('n_failed', 0)}f "
                  f"{rec.get('wall_s', 0):>6.0f}s  {iid[:56]}"
                  + (f"  !! {rec['note']}" if rec.get("note") else ""),
                  flush=True)
            args.out.write_text(json.dumps(results, indent=1, default=str) + "\n")
            if args.purge_every and time.monotonic() - last_purge > args.purge_every:
                n = purge_orphans()
                last_purge = time.monotonic()
                if n:
                    print(f"  [purge] killed {n} orphaned verifier process(es)",
                          flush=True)

    mins = (time.monotonic() - t0) / 60
    verdicts = Counter(r.get("verdict", "-") for r in results)
    wrote = sum(1 for r in results if r.get("has_manifest"))
    print(f"\n=== {len(results)} cell(s) in {mins:.1f} min "
          f"({wrote} wrote a manifest) ===")
    for v, n in verdicts.most_common():
        print(f"  {v:24} {n}")
    print(f"results: {args.out}")
    n = purge_orphans()
    if n:
        print(f"final purge: killed {n} orphan(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
