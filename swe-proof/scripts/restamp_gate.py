#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Re-run a NAMED subset of gates on already-constructed bundles and re-record
the stamps, without re-running the rest of the gate set.

A gate stamp is only evidence about the artifact bytes it actually measured, so
when a later step adds the input a gate needs -- a conformance shadow written
after G-CONF had already recorded `conf_missing_script`, say -- the old stamp is
stale rather than wrong and the cell is blocked on a measurement nobody will
retake. `scripts/regate_resume.py` does retake it, but pays for every other gate
and the agentic audit to get there: hours per cell for a stamp that takes minutes.

Holds the same per-cell flock the authoring fleets hold, so a cell another driver
is actively rewriting is SKIPPED rather than measured mid-edit -- or, with
`--wait`, waited for. A re-stamp can also DEMOTE a record it was only meant to
refresh, which is what `undo_timeouts` guards. Prints one line per cell and a
trailing summary; exit 0 iff every requested gate on every cell landed in a
green-eligible status, 3 iff the pass measured nothing because every cell stayed
busy (which is not a verdict about any cell).

`--benchmark-dir` is authoritative: see `_export_benchmark_dir` for why it has to
be exported into the environment before anything else is imported.

Usage:
  restamp_gate.py --benchmark-dir <corpus> --gates G-CONF --cells cells.tsv
  restamp_gate.py --benchmark-dir <corpus> --gates G-PBT,G-MUT \
      --cell <instance_id> nagini --wait 10800 --poll 120
where each cells.tsv line is `<instance_id>\t<backend>`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path


def _export_benchmark_dir(argv: list[str]) -> None:
    """Make `--benchmark-dir` the root the GATES resolve against, not just the
    root this script checks for a meta.json.

    `paths.TASKS_ROOT` is read from `SBU_BENCHMARK_DIR` once, at import time, and
    falls back to `benchmark`. `run_gates` resolves every artifact through it and
    takes no root argument, so without this the flag reaches only the existence
    check in `one()`: the check clears against the real corpus and the gates then
    run against the fallback root. That does not fail loudly -- each gate reports a
    missing solution, a stub bundle is created holding those errors, and this
    script prints `blocked` for a cell whose real record it never touched.

    Exported here rather than in `main()` because the read happens at import: the
    same pre-scan `cli.py` does, for the same reason. An explicit environment
    variable that DISAGREES with the flag is a caller bug either way round, so it
    is refused rather than silently overridden.
    """
    want = ""
    for i, a in enumerate(argv):
        if a == "--benchmark-dir" and i + 1 < len(argv):
            want = argv[i + 1]
        elif a.startswith("--benchmark-dir="):
            want = a.split("=", 1)[1]
    if not want:
        return
    have = os.environ.get("SBU_BENCHMARK_DIR")
    if have and Path(have) != Path(want):
        raise SystemExit(
            f"--benchmark-dir {want!r} disagrees with SBU_BENCHMARK_DIR "
            f"{have!r}; the gates would resolve against the second and the "
            f"existence check against the first")
    os.environ["SBU_BENCHMARK_DIR"] = want


_export_benchmark_dir(sys.argv)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from pbt_port_fleet import CellBusy, cell_lock  # noqa: E402

OK = ("pass", "skip", "relaxed")


def prior_gates(bundle: Path, gates: list[str]) -> dict:
    """The records for `gates` as they stand BEFORE this tool runs them."""
    try:
        blob = (json.loads((bundle / "meta.json").read_text()).get("gates") or {})
    except (OSError, ValueError):
        return {}
    return {g: blob[g] for g in gates if isinstance(blob.get(g), dict)}


def _is_wall_clock(result) -> bool:
    """Whether `result` says the host ran out of time rather than what it found.

    THREE spellings, because the gates disagree on how to say it and only one of
    them is a status:

    * `status == "timeout"` -- verify.py, ax.py and conf.py, which return a
      verdict-shaped timeout.
    * `error` + `data["verdict"] == "TIMED-OUT"` -- G-PBT, which has no timeout
      status.
    * `error` + `data["no_verdict"] == "timeout"` -- G-DIFF, G-GOLD and G-MUT,
      which report a check that never came back as an `error` naming the file
      rather than the cause; `_common.no_verdict_reason` supplies the cause, and
      the alternative was matching prose each of the three assembles differently.

    `no_verdict == "crash"` is deliberately NOT a wall clock: a broken verifier
    environment reproduces on a quiet host and is a finding.
    """
    if result.status == "timeout":
        return True
    if result.status != "error":
        return False
    data = getattr(result, "data", None)
    if not isinstance(data, dict):
        return False
    return (data.get("verdict") == "TIMED-OUT"
            or data.get("no_verdict") == "timeout")


def undo_timeouts(bundle: Path, results, prior: dict) -> list[str]:
    """Put back any green record this run replaced with a WALL-CLOCK timeout.

    A re-stamp exists to refresh evidence about bytes that have not moved, so it
    must be able to report a non-measurement -- and must never publish one as a
    verdict. `run_gates` already refuses to overwrite a record with a harness
    error, on exactly that reasoning. A verifier timeout is not a harness error:
    several gates read a bare `bundle.verify_timeout()` with no environment
    override, so under fleet load a cell that verifies in seconds can still miss
    its cap, and by the time `one()` labels the row the red record is on disk.

    Only a wall clock -- matched on the recorded reason rather than on the status,
    because the gates spell it three ways (`_is_wall_clock`) -- and only over a
    green-eligible prior. Every other non-pass status these gates return is a real
    measurement: `fail` means the verifier ran and the proof did not close, and the
    `error` returns name defects like an unimportable battery or a missing
    conformance script. A wall clock is the one outcome that is definitionally a
    statement about the host rather than about the artifact.

    WHY THIS CANNOT HIDE A DEFECT, since the suppressed case includes "the solution
    was edited into something that no longer verifies": restoring leaves the cell
    EXACTLY as this tool found it, and the record it restores carries no `sources`
    digests -- that absence is why the cell is on this lane at all. So
    `check_stamp_freshness` still reports the cell uncertified and `--strict` still
    fails the release gate on it; the guard subtracts a false red and adds no green.
    The cell is reported `unmeasured` here so it goes back on the lane for a quieter
    host.
    """
    from swebench_unified.atomic_io import write_json_atomic
    hit = [r.gate for r in results
           if _is_wall_clock(r) and prior.get(r.gate, {}).get("status") in OK]
    if not hit:
        return []
    meta_path = bundle / "meta.json"
    try:
        meta = json.loads(meta_path.read_text())
    except (OSError, ValueError):
        return []
    for g in hit:
        meta.setdefault("gates", {})[g] = prior[g]
    write_json_atomic(meta_path, meta, sort_keys=True)
    return hit


def parse_cells(path: Path) -> list[tuple[str, str]]:
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"[\t ,]+", line)
        if len(parts) < 2:
            raise SystemExit(f"cell line needs '<iid> <backend>': {line!r}")
        out.append((parts[0], parts[1]))
    return out


def unmeasured_rows(rows: list[dict]) -> list[dict]:
    """The cells this pass wrote no record for, for a resuming relaunch.

    `busy` belongs here as much as `unmeasured` does: both mean the pass took no
    measurement of the cell, which is the only question a relaunch asks, and the
    per-cell line names which. Leaving `busy` out makes an all-busy pass write an
    empty file, which a resuming caller reads as "no cells left". `blocked` is
    deliberately NOT here -- that cell got a real record and it is red, so
    re-running it is a treadmill; route a repair at it instead.
    """
    return [r for r in rows if r.get("status") in ("unmeasured", "busy")]


@contextmanager
def cell_lock_waiting(bundle: Path, wait: int = 0, poll: int = 120):
    """`cell_lock`, retried for `wait` seconds while another driver holds it.
    Raises `CellBusy` when the whole wait ran out.

    `wait=0` is the default: skip a busy cell, which costs one pass of the lane and
    is right for a sweep over many cells. Waiting is right for the opposite shape
    of work -- one named cell whose one gate needs re-measuring, where a holder may
    keep the cell for hours and a skip means the measurement never happens at all.

    A fresh `cell_lock` per attempt, because a failed `__enter__` closes its
    descriptor. The retry wraps the CLAIM only, never the body: a `CellBusy` raised
    out of the work would otherwise re-enter the lock and run it twice.
    """
    deadline = time.monotonic() + max(0, wait)
    while True:
        lock = cell_lock(bundle)
        try:
            lock.__enter__()
            break
        except CellBusy as e:
            left = deadline - time.monotonic()
            if left <= 0:
                raise
            print(f"# {bundle.parent.name}/{bundle.name}: held by {e}; retrying "
                  f"in {poll}s ({left / 60:.0f}m of wait left)", flush=True)
            time.sleep(min(poll, max(1, int(left))))
    try:
        yield lock
    finally:
        lock.__exit__(None, None, None)


def one(iid: str, backend: str, gates: list[str], bench_dir: Path,
        wait: int = 0, poll: int = 120) -> dict:
    from swebench_unified.gates import run_gates
    row: dict = {"instance_id": iid, "backend": backend}
    bundle = bench_dir / iid / backend
    if not (bundle / "meta.json").exists():
        row.update(status="missing", detail="no meta.json")
        return row
    try:
        with cell_lock_waiting(bundle, wait, poll):
            # Read INSIDE the lock. The prior record is what `undo_timeouts`
            # restores, so reading it before the claim would restore whatever was
            # there before the holder's own writes -- and with --wait that gap is
            # hours rather than microseconds.
            prior = prior_gates(bundle, list(gates))
            results = run_gates(iid, backend, list(gates), mode="strict",
                               record=True)
            restored = undo_timeouts(bundle, results, prior)
    except CellBusy as e:
        row.update(status="busy", detail=f"held by {e}; "
                   f"{'not re-gated after ' + str(wait) + 's' if wait else 'skipped'}")
        return row
    row["gates"] = {r.gate: r.status for r in results}
    row["detail"] = " | ".join(f"{r.gate}={r.status}: {(r.detail or '')[:160]}"
                               for r in results)
    if restored:
        row["restored"] = restored
        row["detail"] += (f" || timed out under load, prior record kept for "
                          f"{','.join(restored)}; re-run on a quiet host")
        row["status"] = "unmeasured"
    else:
        row["status"] = ("ok" if all(r.status in OK for r in results) else "blocked")
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", required=True)
    # nargs, so BOTH conventions in the tooling work here: the comma string job
    # specs pass and the space-separated list the gates CLI takes. Feeding one
    # spelling to a parser expecting the other stamps meta.json under a key like
    # 'G-VERIFY,G-DIFF' -- a record for a gate that does not exist, which
    # green_check reads as a real error the cell can never clear.
    ap.add_argument("--gates", required=True, nargs="+",
                    help="gate names, comma- or space-separated, e.g. G-CONF,G-AX")
    ap.add_argument("--cells",
                    help="TSV of '<instance_id>\\t<backend>' lines")
    ap.add_argument("--cell", nargs=2, action="append", default=[],
                    metavar=("INSTANCE_ID", "BACKEND"),
                    help="one cell on the command line, repeatable; the "
                         "alternative to --cells for a single named cell")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--wait", type=int, default=0,
                    help="seconds to keep polling for a busy cell's lock "
                         "(default 0: skip it and let the next pass take it)")
    ap.add_argument("--poll", type=int, default=120,
                    help="seconds between lock attempts while --wait runs")
    ap.add_argument("--unmeasured-out", default="",
                    help="write the cells this pass took no measurement of here, "
                         "as a lane TSV, so a relaunch can pick up exactly those")
    args = ap.parse_args()

    if bool(args.cells) == bool(args.cell):
        ap.error("give exactly one of --cells <tsv> or --cell <iid> <backend>")
    gates = [g.strip() for raw in args.gates for g in str(raw).split(",")
             if g.strip()]
    cells = parse_cells(Path(args.cells)) if args.cells else \
        [(i, b) for i, b in args.cell]
    bench_dir = Path(args.benchmark_dir)
    print(f"# {len(cells)} cell(s), gates={gates}, jobs={args.jobs}"
          + (f", wait={args.wait}s poll={args.poll}s" if args.wait else ""),
          flush=True)

    rows = []
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = [ex.submit(one, i, b, gates, bench_dir, args.wait, args.poll)
                for i, b in cells]
        for f in futs:
            r = f.result()
            rows.append(r)
            print(f"[{r['instance_id']}/{r['backend']}] {r['status']} :: "
                  f"{r.get('detail', '')}", flush=True)

    n_ok = sum(1 for r in rows if r["status"] == "ok")
    unmeasured = unmeasured_rows(rows)   # `busy` counts; see unmeasured_rows
    print(f"# ok={n_ok} blocked={sum(1 for r in rows if r['status'] == 'blocked')} "
          f"busy={sum(1 for r in rows if r['status'] == 'busy')} "
          f"unmeasured={len(unmeasured)} "
          f"missing={sum(1 for r in rows if r['status'] == 'missing')}", flush=True)
    if unmeasured and args.unmeasured_out:
        Path(args.unmeasured_out).write_text(
            "".join(f"{r['instance_id']}\t{r['backend']}\n" for r in unmeasured))
        print(f"# {len(unmeasured)} unmeasured cell(s) -> {args.unmeasured_out}",
              flush=True)
    return exit_code(rows)


def exit_code(rows: list[dict]) -> int:
    """0 iff every cell landed green-eligible, 3 iff the pass measured NOTHING
    because every cell stayed busy, 1 otherwise.

    3 is its own code because it is not a verdict about any cell: the holder was
    another driver, nothing was written, and a caller that read it as a red gate
    would route a repair at a cell nobody looked at.
    """
    if rows and all(r.get("status") == "busy" for r in rows):
        return 3
    return 0 if sum(1 for r in rows if r.get("status") == "ok") == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
