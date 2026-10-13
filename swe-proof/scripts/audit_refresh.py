#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Re-run the adversarial audit stage (P2) over a lane of cells, and report
what the fresh measurement did to each cell's standing.

An audit verdict is evidence about the spec view it ran against. When a later
wave edits that view -- moves a postcondition, adds an axiom, narrows a
precondition -- the recorded verdict still SAYS "no weaker implementation
verifies", but it says it about a spec the bundle no longer ships. Some edits
preserve the claim (adding a proof obligation can only reject more
implementations, so everything the audited spec rejected is still rejected) and
some do not, and only the second kind needs the battery run again.

This driver is the instrument for the second kind. It differs from
`scripts/audit_recheck.py`, which replays the attacks RETAINED in verdict.md at
a higher verifier cap: that one is right when the original run was inconclusive
for an infra reason, because the same battery still challenges the same spec.
It cannot help once the spec has moved, and it says so rather than guessing --
the retained positive control is the unmodified solution AS OF THE AUDIT, so
against a moved spec it reads as "changed the spec" and the replay fails closed.
A moved spec needs attacks aimed at the spec that is there now, which means a
live reviewer.

What this records is `run_audit_stage`'s own derivation: the pass/fail comes
from re-running the agent's submitted attacks through the verifier and the
resolve oracle, never from the agent's verdict string. A cell that was green and
comes back failing is the POINT of running this, not a regression to hide: the
green stamp was resting on evidence about a spec that is gone, and the fresh
fail is the first honest thing said about the spec that is here. Those cells are
reported as `now-red` and belong in the repair lane.

SCOPE THE MEASUREMENT TO THE ROLE THAT IS RED. The audit is three reviewer
agents, and a red cell usually names one of them. `--only-failing` re-derives
just that one, which is three times cheaper and, more importantly, strictly safer:
each role is a fresh adversary authoring its own attacks, so re-running all three
to clear one puts two passing roles back on the dice, and a role that comes back
red is a real finding the lane now has to repair. Use it on a lane of red cells.
Do NOT use it on a lane of green cells being re-derived for freshness -- there the
whole claim is that every role speaks to the bytes on disk, so all three must run.

The one exception is not a preference, it is arithmetic: a repair EDITS the spec,
so the moment it lands, the two roles that were not re-run hold verdicts about
bytes that no longer exist. Scoping to the failing role then produces a cell that
is green on one fresh judgment and two stale ones. That is not the dice-rolling
this scoping exists to avoid -- a role with no valid measurement is not a passing
role being risked, it is a role that has not been measured -- so `--only-failing`
also re-derives any role whose recorded `sources` digests disagree with the spec
on disk (`stale_roles`). Measured 2026-08-15: 10 GREEN cells reached green exactly
this way, every one of them a panel role that passed before a later edit to
`model.py`/`Solution.lean`.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \\
    python scripts/audit_refresh.py --lane-file F [--jobs N] [--timeout S]
      [--passes N] [--only-failing | --only eq,panel_2] [--out report.json]

The lane file is `<instance_id>\\t<backend>` per line (the same shape every
other driver here takes). Cells held by another writer are skipped rather than
waited on, and `--passes` re-queues exactly those until nothing is held, so a
lane run alongside a live fleet still covers its whole list. Anything still held
when the passes run out is printed as NOT measured, because a lane that quietly
skips half its cells and exits 0 reads as a lane that cleared them.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

# `corpus_root` imports only `os`, so this stays true of the argument parsing below.
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402


# Which reviewer AGENT informs which gate. `eq` scores two gates from one
# payload, so a cell red on G-EQ, on G-PANEL-1, or on both needs that one agent.
# Mirrors `build_one._AUDIT_AGENTS` inverted; kept here rather than imported so
# this module's argument parsing does not pull in the construct stack.
_GATE_AGENT = {"G-EQ": "eq", "G-PANEL-1": "eq",
               "G-PANEL-2": "panel_2", "G-PANEL-3": "panel_3"}


def failing_roles(bundle: Path) -> list[str] | None:
    """The reviewer agents this cell is actually red on, or None if it is red on
    no audit gate at all.

    A red cell usually names ONE role. Re-deriving the other two is not just
    three times the cost: each is a fresh adversary that authors its own attacks
    against the current spec, so a full re-audit of a cell red on G-PANEL-3 puts
    two passing roles back on the dice to clear a third -- and a role that comes
    back red is a genuine finding the lane then has to repair. Narrowing the
    measurement to the failing role is the only way to re-gate a stale label
    without opening that exposure.

    None (rather than an empty list) for "no audit gate is failing", because the
    caller must skip such a cell rather than run zero agents: an empty role set
    would leave every stale entry standing and report an audit that changed
    nothing, which reads as a confirmation.
    """
    try:
        meta = json.loads((bundle / "meta.json").read_text())
    except (OSError, ValueError):
        return None
    gates = meta.get("gates") or {}
    roles = []
    for gate, role in _GATE_AGENT.items():
        entry = gates.get(gate)
        if isinstance(entry, dict) and str(entry.get("status")) in ("fail", "error"):
            if role not in roles:
                roles.append(role)
    return roles or None


def stale_roles(bundle: Path) -> list[str]:
    """The reviewer agents whose recorded verdict does not describe this spec.

    A gate record carries the sha256 of every bundle file it read
    (`gates/base.source_digests`), so "this stamp is about bytes that are gone" is
    a mechanical question rather than an argument about mtimes. Answered by the
    same code the corpus checker uses, so the two can never drift into disagreeing
    about which cells are stale.

    Only `changed`/`vanished` count. An `unverifiable` record -- one written before
    digests existed and carrying none -- means "not shown", never "moved": folding
    those in would re-audit most of the corpus on no evidence at all, which is the
    reverse of the point.

    `deferred` is the case that made this function useless for a whole year of
    lanes. Every gate here IS an audit gate, and `check_stamp_freshness` reports an
    audit gate's digest mismatch as `deferred` rather than `changed` -- deferred to
    `audit_freshness`, which knows that a changed spec file is not by itself a
    stale audit (a comment edit, an added termination obligation). Dropping those
    with everything else meant the ONLY kinds this could ever see for these four
    gates were `vanished` and `unverifiable`, so `--only-failing` never re-derived
    a moved audit role however far the spec had moved from it. So ask the
    authority instead of inheriting its deferral.
    """
    from audit_freshness import NEEDS_AUDIT, verdict_for
    from check_stamp_freshness import check_cell

    roles: list[str] = []
    deferred: list[str] = []
    for gate, _, kind in check_cell(bundle, set(_GATE_AGENT)):
        if kind == "deferred":
            deferred.append(gate)
            continue
        if kind not in ("changed", "vanished"):
            continue
        role = _GATE_AGENT[gate]
        if role not in roles:
            roles.append(role)
    if deferred:
        # One question per cell, not per gate: all four roles read the same spec
        # file, so the verdict is about the cell. Cells with no `deferred` record
        # are not asked at all, which keeps the git work off the common path.
        verdict, _ = verdict_for(bundle, bundle.name)
        if verdict in NEEDS_AUDIT:
            for gate in deferred:
                role = _GATE_AGENT[gate]
                if role not in roles:
                    roles.append(role)
    return roles


def refresh_cell(iid: str, backend: str, args) -> dict:
    """Re-audit one cell. Returns a row; never raises."""
    from green_check import classify
    from pbt_port_fleet import CellBusy, cell_lock

    from swebench_unified.agent import AgentAuthError
    from swebench_unified.construct.build_one import (final_status_of,
                                                      run_audit_stage)

    bundle = ROOT / args.benchmark_dir / iid / backend
    row: dict = {"instance_id": iid, "backend": backend, "outcome": "",
                 "detail": "", "before": "", "after": ""}
    if not (bundle / "meta.json").is_file():
        row["outcome"], row["detail"] = "no-bundle", "no meta.json"
        return row
    roles: list[str] | None = list(args.only) if args.only else None
    if args.only_failing:
        red = failing_roles(bundle) or []
        # A role whose stamp no longer describes the spec has no measurement to
        # keep, so it joins the red ones. Reported separately: a lane needs to be
        # able to tell "re-derived the role that failed" from "re-derived a role
        # whose verdict a repair had already invalidated".
        moved = [r for r in stale_roles(bundle) if r not in red]
        roles = red + moved
        if moved:
            row["stale_roles"] = ",".join(moved)
        if not roles:
            row["outcome"] = "no-audit-fail"
            row["detail"] = ("red on no audit gate and every audit stamp matches "
                             "the spec on disk; --only-failing has nothing to "
                             "re-derive here")
            return row
    try:
        with cell_lock(bundle):
            row["before"] = classify(bundle, backend, iid)[0]
            if roles:
                # Recorded so a report never has to guess how wide the
                # measurement was: "still-red" after one role means something
                # different from "still-red" after three.
                row["roles"] = ",".join(roles)
            t0 = time.time()
            try:
                results = run_audit_stage(iid, backend, timeout_s=args.timeout,
                                          roles=roles)
            except AgentAuthError as e:
                # Says nothing about this cell: no agent authenticated, so the
                # audit gates are exactly as they were. Naming it separately
                # keeps a host-wide credential outage out of the corpus as a
                # verdict about a spec.
                row["outcome"] = "auth-outage"
                row["detail"] = f"nothing recorded: {e}"
                return row
            row["seconds"] = round(time.time() - t0)
            row["audit"] = " ".join(f"{r.gate}={r.status}" for r in results)
            after, why = classify(bundle, backend, iid)
            row["after"] = after
            if after == "GREEN":
                row["outcome"] = ("stayed-green" if row["before"] == "GREEN"
                                  else "now-green")
                row["detail"] = final_status_of(results)
            else:
                row["outcome"] = ("now-red" if row["before"] == "GREEN"
                                  else "still-red")
                row["detail"] = why[:200]
            return row
    except CellBusy as e:
        row["outcome"], row["detail"] = "busy", f"held by {e}; skipped"
        return row
    except Exception as e:                     # infra, not a verdict
        row["outcome"] = "error"
        row["detail"] = f"{type(e).__name__}: {e}"
        return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane-file", required=True,
                    help="<instance_id>\\t<backend> per line")
    ap.add_argument("--benchmark", default=os.environ.get("SBU_BENCHMARK",
                                                          "swe_bench_verified"))
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--jobs", type=int, default=4)
    # `build_one.AUDIT_ROLE_TIMEOUT_DEFAULT`, repeated as a literal only because
    # this CLI imports that module lazily. A role has to read the bundle, stand
    # up the instance image, author five admissible attacks and verify each one,
    # and at 1500s that is not a cap on a slow role, it is a cap on every role: a
    # lane run at 1500s recorded INCONCLUSIVE with "0 attacks of 0 submitted" on
    # cell after cell, twice each because the retry inherits the same cap. A cap
    # that no role can meet does not measure a spec, it just writes a fail with
    # nothing behind it. 5400s was still under the tail for the same reason at a
    # smaller scale: a role killed there had authored 21 attacks and run 10
    # resolves, and the kill threw all of it away.
    ap.add_argument("--timeout", type=int, default=10800,
                    help="per-role agent wall-clock cap")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default=None)
    # A `busy` row is not a result, it is a cell this pass never looked at, and
    # a lane run against a live fleet is mostly busy on its first pass: the
    # authoring and re-gate drivers hold a cell for up to an hour at a time. One
    # pass therefore reports `busy=22 still-red=3` and exits 0, which reads as a
    # finished lane and drops a `.done` the watchdog will not retry. Re-passing
    # the skipped cells is the whole reason the lock is non-blocking, so the
    # driver does it itself, bounded: it stops as soon as a pass skips nothing,
    # and never runs more passes than asked for.
    ap.add_argument("--passes", type=int, default=1,
                    help="re-run the cells left `busy`, up to this many passes")
    ap.add_argument("--pass-sleep", type=int, default=300,
                    help="seconds between passes; a held cell is held for a "
                         "verifier's worth of time, so retrying at once just "
                         "re-reads the same lock")
    # Scoping. `--only-failing` is the one to reach for on a red lane; `--only`
    # is for the case where the roles are known up front and identical across
    # the lane. Neither belongs on a lane of GREEN cells being re-derived for
    # freshness -- there the point is that every role speaks to the current
    # bytes, so all three have to run.
    ap.add_argument("--only", default="",
                    help="comma-separated reviewer agent roles to re-derive "
                         "(eq, panel_2, panel_3); default all three")
    ap.add_argument("--only-failing", action="store_true",
                    help="per cell, re-derive only the role(s) whose gate is "
                         "recorded fail/error, plus any whose recorded verdict "
                         "no longer matches the spec on disk; skip a cell only "
                         "when neither applies")
    args = ap.parse_args()
    args.only = [r.strip() for r in args.only.split(",") if r.strip()]
    if args.only and args.only_failing:
        ap.error("--only and --only-failing are alternatives")

    os.environ["SBU_BENCHMARK"] = args.benchmark
    os.environ["SBU_BENCHMARK_DIR"] = args.benchmark_dir

    cells = []
    for line in Path(args.lane_file).read_text().split("\n"):
        parts = line.split()
        if len(parts) >= 2:
            cells.append((parts[0], parts[1]))
    if args.limit:
        cells = cells[:args.limit]

    rows: list[dict] = []
    todo = list(cells)
    for attempt in range(1, max(1, args.passes) + 1):
        print(f"# pass {attempt}/{args.passes}: {len(todo)} cell(s), "
              f"jobs={args.jobs}, role cap={args.timeout}s", flush=True)
        busy: list[tuple[str, str]] = []
        done = 0
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(refresh_cell, i, b, args): (i, b) for i, b in todo}
            for f in as_completed(futs):
                iid, backend = futs[f]
                done += 1
                row = f.result()
                # Only a row that MEASURED something belongs in the report; a
                # busy cell is re-queued instead, so the tally counts cells and
                # not attempts.
                if row["outcome"] == "busy":
                    busy.append((iid, backend))
                else:
                    rows.append(row)
                print(f"[p{attempt} {done}/{len(todo)}] {row['outcome']:12s} "
                      f"{backend:7s} {iid:38s} "
                      f"{'[' + row['roles'] + '] ' if row.get('roles') else ''}"
                      f"{row['detail'][:100]}", flush=True)
                if args.out:  # written as we go: a long lane is worth resuming
                    Path(args.out).write_text(json.dumps(rows, indent=1))
        todo = busy
        if not todo:
            break
        if attempt < args.passes:
            print(f"# {len(todo)} cell(s) were held; re-passing in "
                  f"{args.pass_sleep}s", flush=True)
            time.sleep(args.pass_sleep)

    tally: dict[str, int] = {}
    for r in rows:
        tally[r["outcome"]] = tally.get(r["outcome"], 0) + 1
    print("# " + "  ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    if todo:
        # Named, because it is the difference between "these cells are fine" and
        # "nobody looked at these cells".
        print(f"# {len(todo)} cell(s) still held after {args.passes} pass(es), "
              f"NOT measured:")
        for iid, backend in sorted(todo):
            print(f"#   {iid}\t{backend}")
    red = [f"{r['instance_id']}\t{r['backend']}" for r in rows
           if r["outcome"] == "now-red"]
    if red:
        print("# cells the fresh audit turned red (-> repair lane):")
        for line in red:
            print("#   " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
