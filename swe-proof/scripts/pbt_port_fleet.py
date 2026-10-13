#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Run a wave of PBT port agents, then judge every cell mechanically.

One agent per (instance, backend) cell authors `properties.py` by porting the
nagini sibling's battery (prompts/shared/pbt_port.md). The agent's self-report
is NEVER the verdict: after it finishes, this script runs the real G-PBT gate
on the cell and records the stamped result. A cell counts as done only if the
gate says pass.

A manifest that does not pass is left in place with its verdict recorded, so a
later wave can repair it rather than re-derive it from nothing; `--resume`
skips cells whose recorded G-PBT is already a pass.

Concurrency is capped on three axes because they exhaust different resources:

  --jobs          concurrent AGENTS (>~20 concurrent Bedrock sessions stall).
  --gate-workers  concurrent `lake` builds WITHIN one cell's gate run. A lean
                  cell with 12 cases is ~30 builds at ~55s each, so the gate
                  stage dominates wall-clock and is where parallelism helps.
  --lean-slots    HOST-WIDE concurrent `lake` builds, enforced by an flock
                  semaphore in lean_verify.sh. This is the axis that actually
                  protects the host, because the other two cannot see each
                  other: during a wave the builds come from --jobs uncoordinated
                  AUTHORING agents iterating on their variants AND --jobs gates
                  each running --gate-workers builds. 24 x 8 is 192 builds
                  requested at once, more than `os.cpu_count()` on any host this
                  has run on; the semaphore holds it at the cap.

Calibrated on a 96-core / 371 GB machine: a lean build is a fixed ~55s
whatever the bundle (`import Mathlib` dominates), velvet 4-17s. Throughput
rises and flattens — 21.5/min at 24-way, 40 at 48, 55.4 at 72, 64.7 at 96 —
and per-build latency degrades gracefully with it (67s -> 89s). Peak RSS is
5.3 GB per build but almost all of it is shared mmap'd Mathlib oleans, so 16
concurrent builds cost ~3 GB of system memory total: this is CPU-bound, not
memory-bound. The default cap is three quarters of `os.cpu_count()` -- 72 on the
machine above, which took 85% of peak throughput -- leaving the remaining quarter
of the cores for the drivers and the agents themselves.

Usage:
  SBU_BENCHMARK=swe_bench_verified SBU_BENCHMARK_DIR=benchmark-verified \
    python scripts/pbt_port_fleet.py --backend lean --jobs 24 \
      [--instances a b c | --limit N] [--resume] [--gate-only] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402
from swebench_unified.paths import EXPERIMENTS_ROOT  # noqa: E402

# A lean cell may need many lake builds, and `import Mathlib` alone is ~55s of
# every one. Raised from 5400 after measuring the cost of the old value: over 202
# cells that PASSED, author wall time ran median 2067s, p90 3907s, p99 5408s,
# max 5775s -- so 5400 was inside the legitimate tail, and 9 of the 10 cells a
# wave lost to `no-manifest` were timeouts rather than stuck agents. A killed
# agent leaves nothing behind and the cell has to be authored again from
# scratch, which costs far more than waiting.
AGENT_TIMEOUT_DEFAULT = 10800
GATE_TIMEOUT_DEFAULT = 7200

# Per-BUILD cap, passed down as SBU_PBT_VERIFY_TIMEOUT. Raised from 600 for the
# same reason the agent timeout was raised from 5400: the old value was inside
# the legitimate tail, so it was condemning batteries for being slow. Measured
# over 5419 cases that PASSED, the module build ran median 23.8s, p90 71.4s,
# p99 126.3s, max 294.3s -- against a 300s cap, i.e. a distribution truncated at
# the wall, which is what a load artifact looks like rather than a natural tail.
# Independently: a file containing nothing but `import Mathlib` and a `decide`
# took 60-76s through lean_verify.sh at 96-way concurrency versus ~55s idle, and
# the slot semaphore's own wait measured 0.045s, so the inflation is CPU
# contention on the build itself. 1800 is ~6x the observed p999 (219s) and still
# well inside the 7200s per-cell gate budget for a 12-case battery at 8 workers.
VERIFY_TIMEOUT_DEFAULT = 1800

# HOST-WIDE lake-build slots, derived from the host rather than pinned to the one
# it was calibrated on: three quarters of the cores is 85% of peak build
# throughput and leaves the last quarter for the drivers and the agents. On the
# 96-core calibration machine this is the 72 that value used to be written as.
LEAN_SLOTS_DEFAULT = max(1, 3 * (os.cpu_count() or 96) // 4)

# The backend whose battery a port reads from (prompts/shared/pbt_port.md), and
# so also what makes a cell in scope: there is nothing to port without it.
REFERENCE_BACKEND = "nagini"


def _py() -> str:
    return os.environ.get("SBU_PYTHON") or sys.executable


def _env(benchmark: str, benchmark_dir: str, **extra) -> dict:
    env = dict(os.environ, SBU_BENCHMARK=benchmark,
               SBU_BENCHMARK_DIR=benchmark_dir)
    src = str(ROOT / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"]
                               if env.get("PYTHONPATH") else "")
    # A driver does not choose its own environment: a scheduler-started one
    # inherits a near-empty PATH, and then the tools every lane depends on are
    # simply absent. That is not a slow lane, it is a silent one -- an agent CLI
    # that cannot be found makes every audit role submit nothing, which the
    # derivation used to record as "0 attacks submitted", i.e. as a fact about
    # the spec. So the driver puts back what it knows its children need:
    #   * ~/.elan/bin  -- lean_verify.sh's toolchain
    #   * the interpreter running this driver, so `python` means THIS python
    #   * ~/.local/bin -- the usual home for a per-user agent CLI
    # (nagini_verify.sh discovers its own conda env, so PATH does not decide it.)
    for entry in (Path.home() / ".local" / "bin", Path(sys.executable).parent,
                  Path.home() / ".elan" / "bin"):
        env["PATH"] = f"{entry}{os.pathsep}{env.get('PATH', '')}"
    # An agent's Bash tool runs under zsh here, where a BARE output redirect
    # (`> file`, the ordinary way to truncate one) does not truncate: zsh runs
    # $NULLCMD, which defaults to `cat`, so it becomes `cat > file` reading the
    # tool's socket stdin and blocks FOREVER. Measured twice on
    # scikit-learn__scikit-learn-13135/velvet: the agent burned 1s of CPU across
    # 115 minutes holding that cell's lock, with a live `cat` whose fd 0 was a
    # socket in unix_stream_read_generic, until the 3h agent cap would have
    # reaped it. Both times the command contained `> $d/results.txt`.
    # `:` is what bash effectively does (truncate, run nothing), and zsh imports
    # NULLCMD from the environment, so setting it here fixes every agent the
    # fleets spawn without asking them to write zsh-flavoured redirects.
    env.setdefault("NULLCMD", ":")
    env.setdefault("READNULLCMD", ":")
    env.update({k: str(v) for k, v in extra.items()})
    return env


def run_capped(cmd: list[str], log: Path, env: dict,
               timeout_s: int | None) -> bool:
    """Run `cmd` in its OWN session, and on timeout kill the whole tree.

    `subprocess.run(timeout=...)` kills only the direct child. Every command a
    driver caps this way is a python step that launches an agent CLI, which
    launches a shell, which launches a verifier or a container -- so killing the
    step leaves the rest reparented to init, running, with nobody waiting on its
    result. Such an orphan runs for hours, and can sit at 100% of a core
    re-emulating attack files for a cell a live lane is already re-auditing. The
    leak also feeds itself, because the CPU an orphan holds is what makes the next
    role overrun its cap and leak the next one.

    `start_new_session` makes the child a group leader, so the group can be
    signalled as a unit; the /proc walk then catches anything that started its
    own session and left that group. Both are scoped to THIS child's subtree, so
    a concurrent sibling in the same threaded driver is never touched.

    Returns True if the command finished within the cap.
    """
    import signal
    sys.path.insert(0, str(ROOT / "src"))
    from swebench_unified.agent import _kill_descendants
    with log.open("w") as fh:
        p = subprocess.Popen(cmd, env=env, cwd=str(ROOT), stdout=fh,
                             stderr=subprocess.STDOUT, start_new_session=True)
        try:
            p.wait(timeout=timeout_s)
            return True
        except subprocess.TimeoutExpired:
            # Descendants first: SIGKILL erases the /proc parent links the walk
            # needs, so reaping the root before mapping the tree loses it.
            _kill_descendants(p.pid)
            for reap in (lambda: os.killpg(os.getpgid(p.pid), signal.SIGKILL),
                         p.kill):
                try:
                    reap()
                except (ProcessLookupError, PermissionError, OSError):
                    pass
            p.wait()
            return False


class CellBusy(Exception):
    """Another driver is already working this cell."""


class cell_lock:
    """Exclusive claim on one cell, held for as long as work is being done on it.

    `--resume` filters on the RECORDED gate status, which says nothing about a
    cell that is mid-flight: a second wave launched while the first is still
    running re-selects every unfinished cell in it. Measured — two lean waves
    overlapped on 21 cells, so two agents were authoring the same
    `properties.py`, and 5 files were written by the loser. A torn manifest would
    at least fail to load, but a cleanly interleaved one would be a battery
    neither agent designed, gated and shipped as if it were.

    An flock on a sidecar file, so the claim lives with the bundle (works across
    drivers, users, and terminals) and is released by the kernel if a driver is
    killed. Non-blocking: a busy cell is skipped, not queued, because the driver
    that holds it is already doing the work. The holder records its pid and wave
    tag in the file, and `CellBusy` carries that line, so a skip is traceable to
    a wave rather than requiring a walk of /proc.
    """

    def __init__(self, bundle: Path):
        self.path = bundle / ".pbt_port.lock"
        self.fh = None

    def __enter__(self):
        import fcntl
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Read-write, NOT "w": mode "w" truncates on open, BEFORE the flock is
        # attempted, so every driver that LOST the race wiped the winner's own
        # `pid` line. With six drivers up, `busy` then named no holder and the
        # only way to find one was to walk /proc/*/fd. The holder truncates
        # explicitly, once it has the lock.
        # O_CREAT|O_RDWR rather than "r+" with an "x+" fallback, because the
        # fallback would itself race: two drivers arriving at a never-locked cell
        # would both miss the file and one would die on FileExistsError.
        self.fh = os.fdopen(os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644),
                            "r+")
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            holder = self.fh.read(200).strip() or "unknown holder"
            self.fh.close()
            self.fh = None
            raise CellBusy(holder)
        self.fh.truncate(0)
        self.fh.write(f"pid {os.getpid()} tag {os.environ.get('SBU_WAVE_TAG', '?')}\n")
        self.fh.flush()
        return self

    def __exit__(self, *exc):
        # The sidecar is TRUNCATED, never unlinked, and that is a correctness
        # requirement rather than tidiness. An flock lives on the inode, so a
        # driver descheduled between its `open` and its `flock` holds a
        # descriptor on an inode that a releasing holder can unlink underneath
        # it: its `flock` then succeeds on the orphaned inode while the next
        # arrival creates a fresh file and locks that one. Two drivers each hold
        # "the" cell, which is the exact failure the lock exists to prevent --
        # observed as a bundle rewritten by a second worker while a repair agent
        # held the cell for three hours, with both sides reporting success.
        #
        # Leaving an empty file behind costs nothing: `.pbt_port.lock` is
        # gitignored, `gates/integrity.py` excludes it from bundle content, and
        # every reader probes the flock rather than the file's existence
        # (`pbt_certify.held`). Truncating clears the pid
        # line, so `release_misrouted` reads no holder and skips the cell
        # instead of attributing it to a process that has exited.
        if self.fh is not None:
            import fcntl
            try:
                self.fh.truncate(0)
                self.fh.flush()
            except OSError:
                pass
            fcntl.flock(self.fh, fcntl.LOCK_UN)
            self.fh.close()
        return False


def recorded_pbt(bundle: Path) -> tuple[str | None, str]:
    """The stamped G-PBT status/verdict from meta.json — the only truth."""
    try:
        gates = json.loads((bundle / "meta.json").read_text()).get("gates", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return None, ""
    g = gates.get("G-PBT")
    if not isinstance(g, dict) or not g.get("checked_at"):
        return None, ""
    data = g.get("data") or {}
    if data.get("pbt_missing_manifest"):
        return "skip", "missing-manifest"
    return g.get("status"), str(data.get("verdict", ""))


def timed_out(bundle: Path) -> bool:
    """Whether the last gate run hit the verifier cap without judging any case.

    Such a cell needs the SAME battery re-gated at a higher cap, not a new one
    authored: measured over 5419 passing cases the module build ran p99 126s
    against a 300s cap, so a timeout under a 96-way wave is the host rather than
    the battery, and re-authoring throws away work that may be perfectly sound.
    Borne out directly: of 13 such cells re-gated at 1800s, 8 passed SOUND on the
    UNCHANGED battery, so re-authoring would have discarded 8 sound batteries.

    Derived from the case outcomes, not from `data.pbt_timed_out` alone. The flag
    postdates the verdict split, so every record stamped before it reads
    MALFORMED-TESTS with a purely-inconclusive case list -- 4 of the first 12
    error cells were exactly that, and trusting the flag would have re-authored
    them. `inconclusive` is the one outcome that says nothing about the battery
    (it is what a verifier timeout produces), so a bad set consisting only of
    those means nothing was judged, whatever the stamped verdict says.
    """
    try:
        gates = json.loads((bundle / "meta.json").read_text()).get("gates", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    g = gates.get("G-PBT")
    if not isinstance(g, dict) or not g.get("checked_at"):
        return False
    data = g.get("data") or {}
    if data.get("pbt_timed_out"):
        return True
    bad = [c for c in data.get("cases") or [] if not c.get("ok")]
    return bool(bad) and all(c.get("outcome") == "inconclusive" for c in bad)


def author(iid: str, backend: str, benchmark: str, benchmark_dir: str,
           log_dir: Path, timeout_s: int, model: str | None,
           lean_slots: int) -> dict:
    """One port agent for one cell, in its own process.

    Out-of-process so a wedged agent can be killed by timeout without taking
    the wave with it, and so each cell's transcript lands in its own log.
    """
    script = (
        "import sys, json, os\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "from swebench_unified.agent import run_agent_step, DEFAULT_MODEL\n"
        "from swebench_unified.prompts import load_prompt\n"
        "from swebench_unified import paths\n"
        "from swebench_unified.backends import get_backend\n"
        f"iid, bk = {iid!r}, {backend!r}\n"
        "lang = get_backend(bk).language\n"
        "system = load_prompt('pbt_port_system', backend=bk)\n"
        "user = load_prompt('pbt_port', backend=bk, iid=iid, backend_name=bk,\n"
        "                   root=paths.tasks_root_rel(),\n"
        f"                   src_backend={REFERENCE_BACKEND!r},\n"
        "                   solution_filename=lang.solution_filename)\n"
        f"model = {model!r} or DEFAULT_MODEL\n"
        "out = run_agent_step(system_prompt=system, user_prompt=user,\n"
        f"                    cwd={str(ROOT)!r}, timeout_s={timeout_s},\n"
        "                     model=model, submit_step='pbt_author')\n"
        "print(json.dumps({'payload': getattr(out, 'payload', None)}, default=str))\n"
    )
    log = log_dir / f"{iid}.{backend}.author.log"
    t0 = time.monotonic()
    # SBU_AGENT_TRACE gives a per-tool-use line as the agent works. Without it
    # the log is empty until the process exits, so a wave of 60 is completely
    # opaque for its first hour and a wedged agent is indistinguishable from a
    # slow one.
    # ... and per-CELL, because the trace filename is keyed by pid, which says
    # nothing about which instance stalled.
    # The authoring agents are the load the gate's own pool cannot see: each one
    # iterates on its variants with as many `lake` builds as it likes. Passing
    # the slot cap down is what makes the host-wide bound actually total.
    with log.open("w") as fh:
        p = subprocess.run([_py(), "-c", script],
                           env=_env(benchmark, benchmark_dir,
                                    SBU_AGENT_TRACE=str(log_dir / "trace" / iid),
                                    SBU_LEAN_SLOTS=lean_slots),
                           cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
                           timeout=None)
    return {"rc": p.returncode, "wall_s": round(time.monotonic() - t0, 1)}


def gate(iid: str, backend: str, benchmark: str, benchmark_dir: str,
         log_dir: Path, timeout_s: int, workers: int,
         verify_timeout: int, lean_slots: int) -> dict:
    """The authoritative judgment: run G-PBT and stamp meta.json."""
    log = log_dir / f"{iid}.{backend}.gate.log"
    t0 = time.monotonic()
    cmd = [_py(), str(ROOT / "scripts" / "pbt_gate.py"), iid,
           "--backend", backend]
    ok = run_capped(cmd, log, _env(benchmark, benchmark_dir,
                                   SBU_PBT_WORKERS=workers,
                                   SBU_PBT_VERIFY_TIMEOUT=verify_timeout,
                                   SBU_LEAN_SLOTS=lean_slots), timeout_s)
    return {"timed_out": not ok, "wall_s": round(time.monotonic() - t0, 1)}


def run_cell(iid: str, backend: str, args, log_dir: Path) -> dict:
    bundle = ROOT / args.benchmark_dir / iid / backend
    row = {"iid": iid, "backend": backend}
    try:
        with cell_lock(bundle):
            return _run_cell_locked(iid, backend, args, log_dir, bundle, row)
    except CellBusy as e:
        row["status"] = "busy"
        row["detail"] = f"held by {e}; skipped"
        return row


def _run_cell_locked(iid: str, backend: str, args, log_dir: Path,
                     bundle: Path, row: dict) -> dict:
    # Re-check under the lock. `--resume` filtered the id list at LAUNCH; by the
    # time this cell's turn comes another driver may have finished it, and
    # re-authoring a passing cell would throw away a battery for nothing.
    if args.resume and not args.regate_passing and recorded_pbt(bundle)[0] == "pass":
        row["status"] = "already-passing"
        row["detail"] = "recorded pass before this cell's turn came"
        return row
    # A TIMED-OUT cell was never judged: no case reached a verdict, so there is
    # nothing to conclude about the battery and re-authoring would throw away a
    # manifest that may be perfectly sound. Re-gate it instead, at whatever cap
    # this wave carries. Only under --resume, so an explicit re-author (a plain
    # wave, or --instances) still overwrites.
    regate_only = args.resume and timed_out(bundle)
    if regate_only:
        row["regated"] = True
    if not args.gate_only and not regate_only:
        a = author(iid, backend, args.benchmark, args.benchmark_dir, log_dir,
                   args.agent_timeout, args.model, args.lean_slots)
        row["author_rc"] = a["rc"]
        row["author_s"] = a["wall_s"]
        if not (bundle / "properties.py").is_file():
            row["status"], row["detail"] = "no-manifest", "agent wrote nothing"
            return row
    elif not (bundle / "properties.py").is_file():
        row["status"], row["detail"] = "no-manifest", "no properties.py to gate"
        return row
    g = gate(iid, backend, args.benchmark, args.benchmark_dir, log_dir,
             args.gate_timeout, args.gate_workers, args.verify_timeout,
             args.lean_slots)
    row["gate_s"] = g["wall_s"]
    if g["timed_out"]:
        row["status"], row["detail"] = "gate-timeout", f"> {args.gate_timeout}s"
        return row
    st, verdict = recorded_pbt(bundle)
    row["status"] = "pass" if st == "pass" else (st or "unrecorded")
    row["detail"] = verdict
    return row


def _sibling_case_count(props: Path) -> int | None:
    """SPEC_TESTS cases in a manifest, read with `ast` and never imported.

    None when the file is absent or declares no SPEC_TESTS. Every dict literal
    whose `kind` is a spec kind is counted, rather than keying off the shape of
    the assignment: a manifest may build SPEC_TESTS by appending, or by binding
    each case to its own name first, and both undercount silently. The axiom lane
    cannot be mistaken for a spec case -- its kinds are the disjoint strings
    `axiom-soundness` / `axiom-containment`.
    """
    import ast
    try:
        tree = ast.parse(props.read_text())
    except (OSError, SyntaxError):
        return None
    if not any(isinstance(n, ast.Name) and n.id == "SPEC_TESTS"
               for n in ast.walk(tree)):
        return None
    kinds = ("uniqueness", "soundness", "admissibility")
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.Dict)
               for k, v in zip(node.keys, node.values)
               if isinstance(k, ast.Constant) and k.value == "kind"
               and isinstance(v, ast.Constant) and v.value in kinds)


def port_scope(backend: str, benchmark_dir: str, *,
               skip_done: bool = False) -> list[str]:
    """The cells to port, cheapest first: every one with a battery to port from.

    Scope is every cell with a sibling battery on the REFERENCE backend, not only
    the cells a battery would flip green: the battery is what attests to spec
    strength, and that is orthogonal to why some other gate is red. Ordering is by
    the sibling's case count, the port's real cost driver, so an interrupted wave
    has finished its cheap cells rather than a random sample.
    """
    root = ROOT / benchmark_dir
    rows: list[tuple[int, str]] = []
    for d in sorted(root.glob(f"*/{backend}")):
        iid = d.parent.name
        if skip_done and (d / "properties.py").is_file():
            continue
        n = _sibling_case_count(root / iid / REFERENCE_BACKEND / "properties.py")
        if n is not None:
            rows.append((n, iid))
    return [iid for _, iid in sorted(rows)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["velvet", "lean"])
    ap.add_argument("--benchmark", default=os.environ.get("SBU_BENCHMARK",
                                                         "swe_bench_verified"))
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--instances", nargs="*", default=None,
                    help="explicit cells; default = the worklist")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--jobs", type=int, default=8, help="concurrent AGENTS")
    ap.add_argument("--gate-workers", type=int, default=8,
                    help="concurrent verifier builds within one cell's gate")
    ap.add_argument("--lean-slots", type=int, default=LEAN_SLOTS_DEFAULT,
                    help="HOST-WIDE concurrent lake builds (flock semaphore in "
                         "lean_verify.sh); default is 3/4 of os.cpu_count() "
                         f"({LEAN_SLOTS_DEFAULT} here); 0 disables the cap")
    ap.add_argument("--verify-timeout", type=int, default=VERIFY_TIMEOUT_DEFAULT)
    ap.add_argument("--agent-timeout", type=int, default=AGENT_TIMEOUT_DEFAULT)
    ap.add_argument("--gate-timeout", type=int, default=GATE_TIMEOUT_DEFAULT)
    ap.add_argument("--model", default=None)
    ap.add_argument("--skip-authored", action="store_true",
                    help="skip cells that already have a properties.py, however "
                         "it fared; --resume is the usual choice instead")
    ap.add_argument("--resume", action="store_true",
                    help="skip cells whose recorded G-PBT is already a pass")
    ap.add_argument("--gate-only", action="store_true",
                    help="do not author; just judge existing manifests")
    ap.add_argument("--regate-passing", action="store_true",
                    help="re-judge cells that already record a pass (implies "
                         "--gate-only). For re-certifying the corpus after the "
                         "gate itself gets stricter: a recorded pass attests to "
                         "the harness that judged it, not to the current one")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tag", default="wave")
    args = ap.parse_args()
    # A re-certification wave never authors: the manifest is what is on trial, so
    # replacing it would destroy the evidence. Forced here rather than trusted to
    # the caller because the two flags together are what makes the pass safe, and
    # the supervisor passes --resume unconditionally.
    if args.regate_passing:
        args.gate_only = True
    # So a `busy` row names the WAVE holding the cell, not just a pid: with six
    # drivers up, `pid 828470` means nothing until you have run ps, and by then
    # the process may be gone.
    os.environ["SBU_WAVE_TAG"] = f"{args.tag}/port"

    if args.instances:
        ids = list(args.instances)
    else:
        ids = port_scope(args.backend, args.benchmark_dir,
                         skip_done=args.skip_authored)

    if args.resume and not args.regate_passing:
        ids = [i for i in ids
               if recorded_pbt(ROOT / args.benchmark_dir / i / args.backend)[0]
               != "pass"]
    if args.limit:
        ids = ids[:args.limit]

    log_dir = EXPERIMENTS_ROOT / "pbt_port" / f"{args.tag}.{args.backend}"
    print(f"# {len(ids)} cell(s) on {args.backend}, jobs={args.jobs}, "
          f"gate-workers={args.gate_workers}, lean-slots={args.lean_slots}; "
          f"logs -> {log_dir}")
    if args.dry_run:
        for i in ids:
            print(i)
        return 0
    log_dir.mkdir(parents=True, exist_ok=True)

    rows, t0 = [], time.monotonic()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_cell, i, args.backend, args, log_dir): i
                for i in ids}
        for fut in as_completed(futs):
            iid = futs[fut]
            try:
                row = fut.result()
            except Exception as e:  # a cell must never sink the wave
                row = {"iid": iid, "backend": args.backend, "status": "error",
                       "detail": f"{type(e).__name__}: {e}"}
            rows.append(row)
            done = len(rows)
            print(f"[{done}/{len(ids)}] {row['status']:<13} {iid} "
                  f"{row.get('detail', '')}", flush=True)

    summary = {}
    for r in rows:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    out = log_dir / "wave.json"
    out.write_text(json.dumps(
        {"backend": args.backend, "wall_s": round(time.monotonic() - t0, 1),
         "summary": summary, "rows": sorted(rows, key=lambda r: r["iid"])},
        indent=2))
    print(f"# {summary} in {round((time.monotonic() - t0) / 60, 1)} min -> {out}")
    if summary.get("pass", 0) == len(rows):
        return 0
    # `busy` is the one non-passing status that is not this wave's verdict on the
    # cell: another driver held it, and when that driver finishes the cell is
    # either done or free. Exit 3 so the supervisor retries instead of declaring
    # the worklist dry -- a second driver launched alongside a long-running first
    # one would otherwise skip everything the first holds and quit in a minute,
    # which is exactly what a second driver measured: 28 of its first 28 rows
    # were `busy`.
    if summary.get("busy"):
        print(f"# {summary['busy']} cell(s) were held by another driver; "
              "exiting 3 so a supervisor retries them")
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
