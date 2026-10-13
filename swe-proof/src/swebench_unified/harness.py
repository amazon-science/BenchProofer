# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""G-RESOLVE: run the official SWE-bench harness on a candidate patch.diff —
the correctness ORACLE (vanilla SWE-bench semantics, unchanged). The patch is
fed as a prediction, applied at base_commit in the prebuilt image, graded on
hidden FAIL_TO_PASS + PASS_TO_PASS. Runs via `python -m
swebench_unified.run_evaluation` (documented harness repairs, see
harness_patches.py).
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import shlex
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .paths import DATASET_JSONL, EXPERIMENTS_ROOT, REPORTS_ROOT, RUN_PREFIX, python_bin

MODEL_NAME = "sbu_patch"


def _kill_eval_containers(run_id: str) -> int:
    """Remove the harness containers belonging to `run_id`. Returns how many.

    The harness names each container `sweb.eval.<instance>.<run_id>` and removes it
    in a `finally`, which SIGKILL does not run; the docker daemon is not this
    process's child, so nothing else drops it and a container left behind by an
    exited caller survives for as long as the daemon does.

    Advisory: a docker that will not answer is not a reason to fail a resolve that
    already has its verdict.
    """
    from .docker_exec import _sg_docker
    try:
        # Through the shared resolver, like every other docker call: spelled as a
        # bare `docker` here it fails silently wherever the daemon needs a wrapper,
        # and "0 containers removed" then reads as "none were left behind".
        out = _sg_docker(["ps", "-q", "--filter", f"name={run_id}"],
                         timeout=60).stdout.split()
        for cid in out:
            _sg_docker(["rm", "-f", cid], timeout=120)
        return len(out)
    except (OSError, subprocess.SubprocessError):
        return 0


def _run_capped(cmd: list[str], timeout: int) -> subprocess.CompletedProcess:
    """Run `cmd` in its OWN process group and kill the whole group on overrun.

    `subprocess.run(timeout=...)` signals only the direct child, which here is a
    shell (the daemon-access wrapper) that execs the harness: killing it alone
    leaves `python -m run_evaluation` and its containers running with nobody to
    read the result, competing for the bounded oracle slots.

    `start_new_session=True` makes the group killable as a unit, and it is also
    what lets an out-of-band janitor clean up a tree this process never got to
    signal: the group leader is the tree root, so `kill -- -<pgid>` reaches every
    descendant.
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        # Reap, so the tree does not linger as a zombie holding the pipe fds.
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.communicate(timeout=30)
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err)


def _env_int(name: str, default: int) -> int:
    # Local copy of gates._common.env_int: importing that package pulls in
    # gates/__init__, which imports this module.
    v = os.environ.get(name)
    return int(v) if v and v.isdigit() else default

# How many harness containers may run concurrently across every process on this
# host; `SBU_RESOLVE_SLOTS` overrides it. Do not raise it without measuring: past
# some concurrency the oracle stops producing a report at all rather than
# reporting more slowly, and a resolve with no report is indistinguishable from a
# defect in the artifact under test.
RESOLVE_SLOTS_DEFAULT = 12
_SLOT_DIR = Path(os.environ.get("SBU_RESOLVE_SLOT_DIR") or "/tmp/sbu_resolve_slots")


@contextlib.contextmanager
def resolve_slot():
    """Hold one of RESOLVE_SLOTS host-wide harness slots for the duration.

    A directory of flock'd files is the semaphore: it works ACROSS processes
    (unlike threading.Semaphore) and the kernel drops the lock if a holder is
    killed, so a killed process cannot leak a slot and starve every other run.
    Set SBU_RESOLVE_SLOTS=0 to disable (single-cell debugging).
    """
    slots = _env_int("SBU_RESOLVE_SLOTS", RESOLVE_SLOTS_DEFAULT)
    if slots <= 0:
        yield
        return
    _SLOT_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        for i in range(slots):
            # O_RDWR|O_CREAT, never mode "w": truncating before the flock would
            # let a second process clobber a live holder's file.
            fd = os.open(_SLOT_DIR / f"slot{i}", os.O_RDWR | os.O_CREAT, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(fd)
                continue
            try:
                yield
                return
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
        time.sleep(5)


@contextlib.contextmanager
def instance_slot(instance_id: str):
    """Serialize the harness PER INSTANCE, not just per host.

    `--cache_level env` tells the harness to delete the instance image when it
    finishes. Two runs on the SAME instance therefore destroy each other: the one
    that ends first removes the image the other is still using, and the loser
    reports `docker.errors.ImageNotFound` -- which reads downstream as "the oracle
    could not decide", i.e. as a defect in the artifact under test rather than in
    the schedule. It is the normal case, not a corner: judging one cell resolves
    several patches for one instance (gold, prepatch, each attack).

    The instance lock is taken BEFORE the host-wide slot, deliberately: a waiter
    must not sit on one of the slots while it queues, or the queue and the pool
    consume each other. Serializing costs nothing real -- resolving is a pure
    function of (instance, patch).
    """
    if _env_int("SBU_RESOLVE_SLOTS", RESOLVE_SLOTS_DEFAULT) <= 0:
        yield
        return
    _SLOT_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", instance_id)[:120]
    fd = os.open(_SLOT_DIR / f"inst_{safe}", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)          # blocking: order matters, not speed
        yield
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


@dataclass
class ResolveResult:
    resolved: bool
    completed: bool
    instance_id: str
    report: dict
    note: str = ""
    attempts: int = 1
    flaky: bool = False  # resolved on some attempts but not all (network-flaky)


def _frozen_row(instance_id: str) -> dict | None:
    with DATASET_JSONL.open() as fh:
        for line in fh:
            if f'"{instance_id}"' in line:
                row = json.loads(line)
                if row.get("instance_id") == instance_id:
                    return row
    return None


_HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
# A body line that ends a hunk rather than belonging to it.
_HUNK_ENDERS = ("@@ ", "diff --git ", "--- ", "+++ ", "index ")


def _renumber_hunks(patch: str) -> tuple[str, int]:
    """Correct `@@` line COUNTS that disagree with the hunk body they head.

    An author who adds lines to a hunk and leaves its header counts alone writes a
    diff that `patch` refuses outright: it reads the promised number of lines and
    calls whatever follows malformed. The harness then raises before grading
    anything, so no report is written and the run is INCONCLUSIVE, and no number of
    re-runs helps because every pass re-runs the same unusable payload.

    This is a metadata repair, not an edit: not one body line changes, so the edits
    `patch` performs are exactly the ones the author wrote down. That matters for
    what the oracle may conclude -- a spec is only implicated by a FAITHFUL
    embedding of the rival, and correcting a count makes the applied text more
    faithful to the payload, never less.

    Deliberately conservative:
      * A hunk whose counts already agree is left byte-identical, including the
        `@@ -5 +5 @@` spelling with the count omitted. Rewriting well-formed
        payloads would change every patch's sha, and `_census`/`resolve_cache`
        key on it -- a cosmetic pass would invalidate the whole cache.
      * A body containing a line that is none of ' ', '-', '+', '\\' ends the
        hunk rather than being guessed at.
      * Binary patches are returned untouched; there are no countable lines.
    Returns (patch, hunks_corrected).
    """
    if "GIT binary patch" in patch:
        return patch, 0
    lines = patch.split("\n")
    out: list[str] = []
    fixed = 0
    i, n = 0, len(lines)
    while i < n:
        m = _HUNK_RE.match(lines[i])
        if m is None:
            out.append(lines[i])
            i += 1
            continue
        j = i + 1
        old = new = 0
        while j < n:
            ln = lines[j]
            if any(ln.startswith(e) for e in _HUNK_ENDERS):
                break
            if ln.startswith("\\"):          # "\ No newline at end of file"
                j += 1
                continue
            if ln == "":
                # Trailing element from the final newline: not a body line. Mid
                # body, git writes a blank context line as "" often enough that
                # treating it as context is the faithful reading.
                if j == n - 1:
                    break
                old += 1
                new += 1
                j += 1
                continue
            c = ln[0]
            if c == " ":
                old += 1
                new += 1
            elif c == "-":
                old += 1
            elif c == "+":
                new += 1
            else:
                break
            j += 1
        want_old = int(m.group(2)) if m.group(2) is not None else 1
        want_new = int(m.group(4)) if m.group(4) is not None else 1
        if (want_old, want_new) == (old, new):
            out.append(lines[i])             # byte-identical: do not churn shas
        else:
            out.append(f"@@ -{m.group(1)},{old} +{m.group(3)},{new} @@"
                       f"{m.group(5)}")
            fixed += 1
        out.extend(lines[i + 1:j])
        i = j
    return "\n".join(out), fixed


def _write_predictions(instance_id: str, patch: str) -> Path:
    patch, fixed = _renumber_hunks(patch)
    if fixed:
        print(f"[harness] {instance_id}: corrected {fixed} hunk header(s) whose "
              f"line counts disagreed with the body", flush=True)
    pred = [{
        "instance_id": instance_id,
        "model_name_or_path": MODEL_NAME,
        "model_patch": patch if patch.endswith("\n") else patch + "\n",
    }]
    tmp = Path(tempfile.mkdtemp(prefix="sbu_pred_", dir="/tmp")) / "preds.json"
    tmp.write_text(json.dumps(pred))
    return tmp


def _per_instance_report(run_id: str, instance_id: str) -> Path:
    # harness writes report.json relative to its CWD (EXPERIMENTS_ROOT below).
    return (EXPERIMENTS_ROOT / "logs" / "run_evaluation" / run_id /
            MODEL_NAME / instance_id / "report.json")


# The harness raises EvaluationError and writes NO report when it cannot grade an
# instance at all. Its own run log names the cause on that line; everything before
# it is a container/pip transcript, so the tail is enough.
_FAILURE_MARKERS = ("EvaluationError:", ">>>>> Patch Apply Failed",
                    ">>>>> Init Test Failed", ">>>>> Test Timeout",
                    ">>>>> Some Tests Failed")


def _no_report_reason(run_id: str, instance_id: str) -> str:
    """Why the harness produced no report, from its per-instance run log; "" if unknown.

    The two causes call for opposite responses -- an unusable candidate patch is a
    fact about the payload, a container or image failure is a fact about the host --
    and both are otherwise reported as "harness error or image pull failure". Read
    here because the run directory is purged per attempt, so this is the only
    chance.
    """
    log = (EXPERIMENTS_ROOT / "logs" / "run_evaluation" / run_id /
           MODEL_NAME / instance_id / "run_instance.log")
    try:
        with log.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - 65536))
            text = fh.read().decode("utf-8", "replace")
    except OSError:
        return ""
    lines = [ln.strip() for ln in text.splitlines()]
    # LAST occurrence: the harness logs the same traceback more than once.
    hits = [k for k, ln in enumerate(lines)
            if any(m in ln for m in _FAILURE_MARKERS)]
    if not hits:
        return ""
    # The two following lines as well: `patch` puts its actual complaint ("Only
    # garbage was found in the patch input") AFTER the marker line, not on it.
    return " ".join(x for x in lines[hits[-1]:hits[-1] + 3] if x)[:300]


def _census(instance_id: str, patch_sha: str) -> None:
    """Append one line per oracle run, so repeated work is observable.

    Resolving is a pure function of (instance, patch), and the in-process
    `resolve_cache` cannot see other processes, so a cross-process record is the
    only way to see how often the same pair is resolved twice.

    Advisory only. Never raise: an unwritable census must not fail a resolve.
    """
    try:
        p = EXPERIMENTS_ROOT / "resolve_census.tsv"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as fh:      # O_APPEND: line-atomic across processes
            fh.write(f"{time.time():.0f}\t{instance_id}\t{patch_sha}\t{os.getpid()}\n")
    except OSError:
        pass


def run_resolve(instance_id: str, patch: str, run_id: str | None = None,
                timeout: int = 3600, retries: int = 2) -> ResolveResult:
    """Apply `patch` as the prediction for `instance_id`; return the harness's
    resolved verdict. Runs `run_evaluation` with the daemon reachable
    (`docker_exec.resolve_docker_cmd`). On a non-resolved verdict, retries up to
    `retries` times to distinguish a real failure (consistent) from network
    flakiness (flips to resolved)."""
    from .benchmarks import active
    bench = active()
    if not bench.supports_docker_oracle:
        return ResolveResult(False, False, instance_id, {},
                             f"benchmark {bench.name!r} has no wired Docker "
                             "oracle (G-RESOLVE unavailable)")
    row = _frozen_row(instance_id)
    if row is None:
        return ResolveResult(False, False, instance_id, {}, "not in frozen dataset")
    if bench.resolve_style == "pro":
        from .pro_oracle import run_resolve_pro
        return run_resolve_pro(instance_id, patch, row,
                               timeout=timeout, retries=retries)
    # Content-address the run_id by the patch.
    # swebench's run_evaluation SHORT-CIRCUITS on an existing per-instance
    # report.json without checking it was computed for the SAME patch, so a
    # reused run_id returns a STALE verdict. The patch hash makes the run_id
    # unique per patch; we also purge any stale report dir per attempt.
    patch_sha = hashlib.sha1((patch or "").encode("utf-8")).hexdigest()[:10]
    # -pid: run dirs are single-use (purged before, deleted after), so two
    # processes resolving the same instance and patch would otherwise share a dir
    # and rmtree each other's in-flight report.
    base_run_id = (run_id or f"sbu-resolve-{RUN_PREFIX}-{instance_id}") \
        + f"-{patch_sha}-p{os.getpid()}"
    _census(instance_id, patch_sha)
    # Imported here rather than at module scope: `docker_exec` reaches back into
    # `.benchmarks` and `.gates.base`, and this module is imported by both.
    from .docker_exec import DockerUnavailable, docker_argv, resolve_docker_cmd
    try:
        # Resolved before any temporary state is written, so an unreachable daemon
        # is one legible answer rather than three attempts each failing inside the
        # harness. A failed MEASUREMENT, never a verdict: completed=False.
        resolve_docker_cmd()
    except DockerUnavailable as e:
        return ResolveResult(False, False, instance_id, {}, str(e))

    def _one(attempt_run_id: str) -> ResolveResult:
        preds = _write_predictions(instance_id, patch)
        REPORTS_ROOT.mkdir(parents=True, exist_ok=True)
        EXPERIMENTS_ROOT.mkdir(parents=True, exist_ok=True)
        # purge any pre-existing report for this run_id so the harness cannot
        # short-circuit on a stale verdict.
        run_dir = EXPERIMENTS_ROOT / "logs" / "run_evaluation" / attempt_run_id
        shutil.rmtree(run_dir, ignore_errors=True)
        inner = " ".join([
            shlex.quote(python_bin()), "-m", "swebench_unified.run_evaluation",
            "--dataset_name", bench.dataset_name,
            "--predictions_path", str(preds),
            "--max_workers", "1",
            "--run_id", attempt_run_id,
            "--namespace", bench.namespace or "none",
            "--instance_image_tag", bench.image_tag,
            "--cache_level", "env",
            "--timeout", str(timeout),
            "--report_dir", str(REPORTS_ROOT),
            "--instance_ids", instance_id,
        ])
        # The harness is the process that must reach the daemon, so the whole
        # `cd && python -m run_evaluation` runs under the resolved access, not
        # just the docker calls it makes.
        cmd = docker_argv(f"cd {shlex.quote(str(EXPERIMENTS_ROOT))} && {inner}")
        try:
            try:
                # The slot is held only around the container run, so queueing
                # never counts against this attempt's own timeout.
                # Instance lock OUTSIDE the host slot: see `instance_slot`.
                with instance_slot(instance_id), resolve_slot():
                    proc = _run_capped(cmd, timeout + 600)
            except subprocess.TimeoutExpired:
                # The group is already dead; the container is not, because the
                # daemon owns it and the harness's own cleanup never ran.
                n = _kill_eval_containers(attempt_run_id)
                return ResolveResult(
                    False, False, instance_id, {},
                    f"harness timed out ({timeout}s)"
                    + (f"; removed {n} orphaned container(s)" if n else ""))
            finally:
                # Drop the throwaway predictions dir. Only safe once the harness
                # has exited: deleting it while a concurrent harness is still
                # initializing makes that one fall back to dataset row 0.
                shutil.rmtree(preds.parent, ignore_errors=True)
            rep_path = _per_instance_report(attempt_run_id, instance_id)
            if not rep_path.exists():
                # The per-instance run log FIRST: it names the actual cause, where
                # the process output only carries the run summary ("Instances with
                # errors: 1"), which is the same for an unapplicable patch as for a
                # dead container. At the FRONT so a truncating caller keeps the part
                # that attributes the failure.
                why = _no_report_reason(attempt_run_id, instance_id)
                tail = " | ".join(
                    ln.strip() for ln in
                    ((proc.stderr or "") + "\n" + (proc.stdout or "")).splitlines()
                    if ln.strip())[-400:]
                return ResolveResult(False, False, instance_id, {},
                                     "no report — "
                                     + (why or "harness error or image pull failure")
                                     + f" (rc={proc.returncode}; {rep_path}"
                                     + (f"; {tail}" if tail else "") + ")")
            rep = json.loads(rep_path.read_text())
            inst = rep.get(instance_id, rep)
            resolved = bool(inst.get("resolved", False))
            return ResolveResult(resolved, True, instance_id, rep,
                                 "resolved" if resolved else "patch did not resolve")
        finally:
            # The run_id is single-use, so delete its logs dir on EVERY path
            # once the report is read — keeping it would re-introduce the
            # stale-cache short-circuit and bloat disk. Also drop the stray
            # summary JSON; test_output logs stay in REPORTS_ROOT.
            shutil.rmtree(run_dir, ignore_errors=True)
            stray = EXPERIMENTS_ROOT / f"{MODEL_NAME}.{attempt_run_id}.json"
            try:
                stray.unlink()
            except OSError:
                pass

    # A correct patch resolves DETERMINISTICALLY; only network-flaky tests flip.
    # "Resolved on ANY attempt" counts as resolved, flagged flaky when attempts
    # disagree — prevents a false `verified ∧ ¬resolved`.
    #
    # An attempt that never COMPLETED (harness timeout, image pull failure) is a
    # failed MEASUREMENT, not a verdict about the patch, so it is retried too. The
    # asymmetry to avoid is retrying the deterministic outcome and not the
    # transient one, which turns a loaded host into an inconclusive verdict on a
    # sound cell.
    last = incomplete = None
    n = n_incomplete = 0
    for k in range(retries + 1):
        n += 1
        attempt = _one(base_run_id if k == 0 else f"{base_run_id}-retry{k}")
        if attempt.resolved:
            attempt.attempts = n
            if n > 1:
                attempt.flaky = True
                attempt.note = (f"resolved on attempt {n}/{retries + 1} "
                                "(flaky: earlier attempt failed or did not complete)")
            return attempt
        if attempt.completed:
            last = attempt
        else:
            incomplete = attempt
            n_incomplete += 1
    if last is None:
        # Every attempt failed to complete: report the measurement failure, and
        # say how many times we tried so a reader can tell this apart from a
        # single unlucky run. `incomplete` is necessarily set here — the loop
        # runs at least once and every non-resolved attempt lands in one of the
        # two slots.
        assert incomplete is not None
        incomplete.attempts = n
        incomplete.note = f"{incomplete.note} (no attempt completed in {n} tries)"
        return incomplete
    last.attempts = n
    # A later attempt may have failed to COMPLETE while an earlier one produced a
    # real not-resolved verdict; the verdict is what we report, and the dropped
    # attempt is noted so the record is not read as a clean triple-check.
    last.note = (f"patch did not resolve in {n} attempts (consistent — not flaky)"
                 + (f"; {n_incomplete} attempt(s) did not complete"
                    if n_incomplete else ""))
    return last


# ---------------------------------------------------------------------------
# Is the oracle able to judge this instance AT ALL?
#
# A patch that adds one inert file and touches no source. It has no context lines
# to match, so it applies in ANY repo at ANY commit -- one probe works for every
# instance, with no clone and no knowledge of the tree.
#
# It exists because "did not resolve" is a claim about a PATCH, and the harness
# cannot make that claim when it could not run the tests: a suite that reaches the
# network fails inside a sealed container whatever is applied, which recorded as a
# fail reads as "the gold patch does not fix the bug".
#
# PASS_TO_PASS is the discriminator, and it is exact rather than heuristic: those
# tests pass at the base commit BY DEFINITION of the dataset. If they fail with no
# source change, the environment cannot run this instance and nothing about any
# patch was measured.
BASE_PROBE_PATCH = """\
diff --git a/.sbu_resolve_probe b/.sbu_resolve_probe
new file mode 100644
--- /dev/null
+++ b/.sbu_resolve_probe
@@ -0,0 +1 @@
+base probe: this run applies no change to any source file
"""

_BASE_LANE_CACHE: dict[str, tuple[bool | None, list[str], str]] = {}


def base_lane_intact(instance_id: str, *, timeout: int = 3600,
                     retries: int = 1) -> tuple[bool | None, list[str], str]:
    """Does this instance's PASS_TO_PASS lane hold with NO source change?

    Returns (intact, failing_tests, note). `intact is None` means the probe
    itself never completed, which is a failed measurement and says nothing either
    way -- callers must not read it as "the environment is fine".

    Cached per process and per instance: the answer is a property of the image and
    the host, not of the patch under test, and the probe costs a full harness run.
    """
    if instance_id in _BASE_LANE_CACHE:
        return _BASE_LANE_CACHE[instance_id]
    res = run_resolve(instance_id, BASE_PROBE_PATCH,
                      run_id=f"sbu-baseprobe-{RUN_PREFIX}-{instance_id}",
                      timeout=timeout, retries=retries)
    if not res.completed:
        out: tuple[bool | None, list[str], str] = (
            None, [], f"base probe did not complete: {res.note}")
    else:
        inst = res.report.get(instance_id, res.report)
        if not inst.get("patch_successfully_applied", True):
            # The probe adds a new file, so this cannot be a conflict; it means
            # the harness could not apply anything at all here.
            out = (None, [], "base probe patch did not apply")
        else:
            failures = sorted(
                (inst.get("tests_status") or {}).get("PASS_TO_PASS", {})
                .get("failure", []))
            out = (not failures, failures,
                   "PASS_TO_PASS holds with no source change" if not failures
                   else (f"{len(failures)} PASS_TO_PASS test(s) fail with no "
                         f"source change, so this environment cannot run the "
                         f"instance: " + ", ".join(failures[:6])
                         + (" ..." if len(failures) > 6 else "")))
    _BASE_LANE_CACHE[instance_id] = out
    return out
