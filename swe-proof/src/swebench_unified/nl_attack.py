# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Machine-checkable substrate for the ears backend's agentic audit
(G-EQ / G-PANEL-1) — the natural-language analog of adversary.py.

With no verifier, an ears audit claim is discharged by an executable PROBE: a
standalone python script that encodes behavior a cited requirement mandates
and exits 0 iff that behavior holds of the code it runs against. Probes run
inside the instance's official Docker image (docker_exec.run_in_container):

  probe <instance_id> <probe.py>                 # patched tree (gold applied)
  probe <instance_id> <probe.py> --base          # base_commit tree
  probe <instance_id> <probe.py> --patch F.diff  # an alternative patch applied

The audit protocol derived from these facts (build_one._derive_ears_verdict):
a requirements VIOLATION is a probe that fails on the patched tree; a
TOO-WEAK finding is an alternative patch that satisfies every probe yet does
not resolve; the positive control must fail at base and hold when patched
(discriminating power — the G-DIFF analog). Probes are plain scripts, not
pytest, so no test framework needs installing in old images.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from .docker_exec import ensure_image, run_in_container
from .paths import instance_dir

PROBE_TIMEOUT_DEFAULT = 600
# Printed by the probe wrapper before the probe body runs; its absence on a
# nonzero exit means the failure happened BEFORE the probe (patch apply, env).
_SENTINEL = "SBU_PROBE_RUNNING"


def run_probe(instance_id: str, probe: Path, *, patch_text: str | None = None,
              at_base: bool = False, timeout: int = PROBE_TIMEOUT_DEFAULT) -> dict:
    """Run one probe script in the instance image. Tree selection: default =
    gold patch applied; `patch_text` = that patch applied instead; `at_base` =
    unpatched base_commit. Returns {completed, holds, summary} — `holds` is
    exit 0; `completed` False on timeout/infra (callers must treat that as
    inconclusive, never as a verdict)."""
    out = {"completed": False, "holds": False, "summary": ""}
    probe = Path(probe)
    if not probe.is_file():
        out["summary"] = f"probe file missing: {probe}"
        return out
    err = ensure_image(instance_id)
    if err:
        out["summary"] = err
        return out
    work = Path(tempfile.mkdtemp(prefix="sbu_nl_probe_"))
    try:
        shutil.copy2(probe, work / "probe_impl.py")
        # Sentinel wrapper: the container command is `<apply patch> && python
        # /work/probe.py`, so a patch-apply failure exits nonzero WITHOUT the
        # probe ever running. The sentinel lets us tell the stages apart
        # STRUCTURALLY — a nonzero exit with no sentinel is infra (patch did
        # not apply / env broke), never a probe verdict. Without this, a
        # garbage candidate patch would read as "probe rejected it" (fail-open).
        (work / "probe.py").write_text(
            "import runpy, sys\n"
            f"print({_SENTINEL!r}, flush=True)\n"
            "sys.argv = ['probe_impl.py']\n"
            "runpy.run_path('/work/probe_impl.py', run_name='__main__')\n")
        gold_path: str | None = None
        apply_gold = False
        if at_base:
            pass  # unpatched tree
        elif patch_text is not None:
            (work / "candidate.patch").write_text(patch_text)
            gold_path = str(work / "candidate.patch")
            apply_gold = True
        else:
            gp = instance_dir(instance_id) / "patch.diff"
            if not gp.exists():
                out["summary"] = f"patch.diff missing at {gp}"
                return out
            gold_path = str(gp)
            apply_gold = True
        r = run_in_container(instance_id, str(work), "probe.py",
                             gold_patch_path=gold_path, apply_gold=apply_gold,
                             timeout=timeout)
        if r.returncode == 124:
            out["summary"] = f"probe timed out after {timeout}s (inconclusive)"
            return out
        # No sentinel + nonzero exit = the failure happened BEFORE the probe
        # body ran (patch did not apply, env broke) — infra, never a verdict.
        if r.returncode != 0 and _SENTINEL not in (r.stdout or ""):
            out["summary"] = ("probe never ran (patch apply / env failure): "
                              + ((r.stderr or r.stdout or "")[-300:]).strip())
            return out
        out["completed"] = True
        out["holds"] = r.returncode == 0
        tail = ((r.stdout or "") + ("\n" + r.stderr if r.stderr else "")).strip()
        tail = tail.replace(_SENTINEL, "").strip()
        out["summary"] = (f"exit={r.returncode}; " + tail[-400:]) if tail \
            else f"exit={r.returncode}"
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ears audit probe runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe", help="run a probe script in the instance image")
    p.add_argument("instance_id")
    p.add_argument("probe")
    tree = p.add_mutually_exclusive_group()
    tree.add_argument("--base", action="store_true",
                      help="run against the UNPATCHED base_commit tree")
    tree.add_argument("--patch", default=None, metavar="DIFF",
                      help="apply this patch file instead of the gold patch")
    p.add_argument("--timeout", type=int, default=PROBE_TIMEOUT_DEFAULT)
    args = ap.parse_args(argv)
    patch_text = Path(args.patch).read_text() if args.patch else None
    res = run_probe(args.instance_id, Path(args.probe), patch_text=patch_text,
                    at_base=args.base, timeout=args.timeout)
    tree_lbl = ("base" if args.base else
                ("candidate-patched" if args.patch else "gold-patched"))
    if not res["completed"]:
        print(f"INCONCLUSIVE ({tree_lbl}): {res['summary']}")
        return 3
    print(f"{'HOLDS' if res['holds'] else 'VIOLATED'} ({tree_lbl}): {res['summary']}")
    return 0 if res["holds"] else 1


if __name__ == "__main__":
    sys.exit(main())
