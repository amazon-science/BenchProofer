#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""One command that answers "is this corpus releasable", and nothing else.

The release claim is a CONJUNCTION -- every cell green, every stamp describing
the artifact actually on disk, every battery importable, every record free of
build-time narration -- so it needs ONE executable definition, in which a check
that cannot be run counts as a failure rather than as silence.

WHAT COUNTS AS A FAILURE, deliberately not distinguished in the exit status: a
check that reports a defect, a check that could not measure a cell (held by a
driver, unreadable record), and a check that crashed or timed out. The middle one
still fails, because the question is not "is anything known to be broken" but "is
every cell known to be sound"; run this on a quiescent tree, and read busy cells
as a scheduling answer rather than a verdict about the corpus.

Nothing here is benchmark-specific: the backend list comes from the registry, and
adding a check means adding one CHECKS entry with the argv and how to read it.

Usage:
    scripts/release_gate.py [--benchmark-dir DIR] [--backends nagini velvet lean ears]
                            [--only NAME ...] [--skip NAME ...] [--list]
                            [--timeout SECONDS] [--json OUT]

Exit status is 0 only when every selected check passed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# The one package import this module may make before `main` exports the roots:
# `corpus_root` reads the environment when CALLED and binds nothing at import,
# unlike `paths` (see the ordering note in `main`).
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402


def corpus_backends(bench: Path) -> list[str]:
    """Every registry backend that actually ships bundles under `bench`.

    Taken from the corpus rather than from the backend's flavor. A backend with no
    verifier still ships a bundle per instance, and `green_check.py` judges each on
    the gates that do apply to it -- so restricting this to the proof backends
    would let the gate exit 0 having never asked the release question of a quarter
    of the released corpus. Registry-driven, so a new backend is covered by
    constructing bundles for it and nothing else.
    """
    from swebench_unified.backends import BACKENDS
    return [n for n in BACKENDS if any(bench.glob(f"*/{n}/meta.json"))]


@dataclass
class Check:
    name: str
    why: str                      # the release requirement this defends
    argv: list[str]               # relative to ROOT, run with the same python
    per_backend: bool = False     # run once per backend, with --backend <bk>
    # Some of these tools are classifiers that always exit 0 and print a table.
    # For those the verdict lives in the output, so a reader is given here rather
    # than pretending the exit status means something.
    read_output: Optional[Callable[[str], tuple[bool, str]]] = None
    # How many units of the corpus the check reports having looked at. A check
    # that measured ZERO is a failure however it exited: a tool pointed at the
    # wrong root prints a clean summary line having opened nothing. Every check
    # here prints a count of what it walked, so every one is verified to have
    # walked something rather than trusted to have.
    measured: Optional[Callable[[str], int]] = None
    timeout_s: int = 3600
    extra: dict = field(default_factory=dict)


def _green_verdict(out: str) -> tuple[bool, str]:
    """green_check.py is a classifier: it exits 0 whatever it finds."""
    bad = [ln for ln in out.splitlines()
           if ln.startswith(("NOTGREEN", "NORESULT"))]
    green = sum(1 for ln in out.splitlines() if ln.startswith("GREEN"))
    if bad:
        head = "; ".join(ln.split("\t")[1] for ln in bad[:6])
        return False, (f"{green} green, {len(bad)} not: {head}"
                       + (" ..." if len(bad) > 6 else ""))
    return True, f"{green} cells green"


def _n(out: str, *patterns: str) -> int:
    """The largest count matching any of `patterns` in a tool's summary.

    Largest, not first: these summaries print per-backend lines and then a total,
    and the total says how much of the corpus was looked at.
    """
    best = 0
    for pat in patterns:
        for m in re.finditer(pat, out):
            best = max(best, int(m.group(1)))
    return best


def _stale_verdict(out: str) -> tuple[bool, str]:
    """stale_fail_triage.py also exits 0 always; the count is in its summary.

    A "stale" fail is a recorded failure whose own digests no longer match the spec
    on disk -- a verdict about a spec the bundle no longer ships, which routes a
    repair agent at a defect that may already be fixed.

    Read the one line that states the count, rather than scanning every line that
    says "stale" for a digit: the tool's only "stale"-bearing line is a digit-free
    heading, so that conjunct could never fail, and a gate that fails open is worse
    than an absent one because the release report says the question was asked.
    """
    m = re.search(r"(\d+) stale fail label\(s\)", out)
    if m is None:
        return False, ("stale_fail_triage.py printed no stale count; the gate "
                       "cannot confirm the question was answered")
    n = int(m.group(1))
    if n:
        return False, f"{n} recorded failure(s) describe a spec no longer shipped"
    return True, "no stale failure verdicts"


def _reaudit_verdict(out: str) -> tuple[bool, str]:
    """audit_freshness.py is a classifier too; the count is in its last line.

    The OTHER half of freshness, required rather than advisory because
    `check_stamp_freshness.py` defers to it by construction. That tool decides a
    record by content -- right for a gate whose verdict is about the bytes it ran,
    wrong for an audit, whose conclusion is about the specification those bytes
    carry. A spec that gained obligations rejects strictly more implementations, so
    a green audit survives it; a spec that lost a conjunct is exactly what an audit
    exists to catch. Only spec_signature tells those apart, so skipping this check
    turns the deferral into silence.
    """
    m = re.search(r"(\d+) cell\(s\) need a fresh audit", out)
    if m is None:
        return False, "no verdict line (the classifier did not finish)"
    n = int(m.group(1))
    if n:
        names = re.findall(r"^  (\S+/\S+):", out, re.M)[:6]
        return False, (f"{n} cell(s) audited against a spec that has since been "
                       f"weakened or cannot be recovered: " + ", ".join(names)
                       + (" ..." if n > len(names) else ""))
    return True, "every audit verdict still describes the shipped spec"


CHECKS: list[Check] = [
    Check("green", "every cell's gates recorded and OK (the release claim itself)",
          ["scripts/green_check.py"], per_backend=True, read_output=_green_verdict,
          measured=lambda out: sum(1 for ln in out.splitlines()
                                   if ln.startswith(("GREEN", "NOTGREEN", "NORESULT"))),
          timeout_s=1800),
    # `--certify-unchanged` is not a relaxation. Without it every record written
    # before `sources` digests existed counts as UNVERIFIABLE, so the verdict is
    # dominated by absent digests rather than by measured defects. With it the same
    # tool decides those by content (a retained control, recorded region hashes) or
    # by showing nothing wrote the artifact after `checked_at`. Each proof is used
    # only in the direction that SHOWS a record current; a record that fails all of
    # them is reported `uncertified`, meaning "not shown", and `--strict` fails.
    Check("freshness",
          "every stamp describes the bytes on disk, so no cell is green on a "
          "verdict about a superseded spec",
          ["scripts/check_stamp_freshness.py", "--certify-unchanged", "--strict"],
          measured=lambda out: _n(out, r"(\d+) cell\(s\) checked"),
          timeout_s=5400),
    Check("audit-freshness",
          "every audit verdict still describes the spec on disk, by "
          "spec_signature -- the half of freshness a digest cannot decide",
          ["scripts/audit_freshness.py"], read_output=_reaudit_verdict,
          measured=lambda out: _n(out, r"TOTAL\s+(\d+)"),
          timeout_s=1800),
    Check("batteries",
          "every properties.py imports, since a broken battery caps its cell "
          "red no matter how strong the spec is",
          ["scripts/battery_integrity.py"],
          measured=lambda out: _n(out, r"(\d+)\s*(?:cell|batter)"),
          timeout_s=3600),
    # Coverage reads "N cell(s) examined" and NOT the not-green count: on a corpus
    # with nothing wrong the not-green count is 0, which `measured` would read as
    # "the check ran but looked at nothing" and turn into a FAILURE -- so the gate
    # would refuse exactly the corpus it exists to release.
    Check("stale-fails", "no repair is routed by a verdict about a spec that is gone",
          ["scripts/stale_fail_triage.py"], read_output=_stale_verdict,
          measured=lambda out: _n(out, r"(\d+) cell\(s\) examined"),
          timeout_s=1800),
    # These two walk every backend; what differs is how much of each one's question
    # applies, and each states its own scope in its output rather than leaving a
    # reader to infer it from a count:
    #
    #   * `pbt_certify.py` exempts nagini only from the WITNESS condition, which is
    #     inapplicable because Viper discharges the postcondition itself and there
    #     is no tactic script for a reshaped impl to break.
    #   * `pbt_audit_completeness.py`'s prompt is witness-shaped throughout (attack
    #     B' forges a witness), so on a backend with no witnesses it reports "not
    #     applicable" and names what does cover those cells: `audit_freshness.py`
    #     above, plus the G-PANEL-* role records.
    Check("audit-complete",
          "every cell carries a complete adversarial audit under the CURRENT "
          "audit prompt, not a partial or superseded one",
          ["scripts/pbt_audit_completeness.py"],
          measured=lambda out: _n(out, r"\d+ of (\d+) need an audit",
                                  r"not applicable over (\d+) cell"),
          timeout_s=1800),
    Check("certify",
          "each cell's own recorded evidence is internally consistent "
          "(scripts/pbt_certify.py's per-cell audit)",
          ["scripts/pbt_certify.py"],
          measured=lambda out: _n(out, r"\d+/(\d+) certified"),
          timeout_s=3600),
    Check("prose",
          "no record publishes build-time narration: scratch paths that no "
          "longer exist, one host's absolute paths, the audit machine's load",
          ["scripts/verdict_prose_lint.py"],
          measured=lambda out: _n(out, r"(\d+) cell\(s\) walked"),
          timeout_s=3600),
]


def check_env(bench: Path, benchmark: str) -> dict:
    """The environment every check needs to find the corpus.

    Passed to all of them, not only the one that has no flag for it: a check pointed
    at a different tree than the one being gated is worse than no check at all.
    SBU_BENCHMARK names WHICH benchmark's task records to resolve against; a wrong
    one turns every cell into "task record not found".
    """
    env = dict(os.environ)
    env["SBU_BENCHMARK_DIR"] = str(bench)
    env.setdefault("SBU_BENCHMARK", benchmark)
    return env


def run_check(c: Check, bench: Path, backends: list[str], timeout_s: int | None,
              py: str, env: dict) -> dict:
    """Run one check, possibly once per backend, and report a single verdict."""
    invocations: list[list[str]] = []
    base = [py] + c.argv
    # The tools disagree on the flag name for the corpus root, so the mapping is
    # explicit rather than assumed. Getting it wrong is not a crash: `pbt_certify.py
    # --dir` defaults to the same path this script does, so a wrong flag would
    # silently gate a DIFFERENT tree.
    root_flag = "--dir" if c.argv[0].endswith("pbt_certify.py") else "--benchmark-dir"
    if c.argv[0].endswith("pbt_audit_completeness.py"):
        root_flag = ""          # reads the corpus root from SBU_BENCHMARK_DIR
    if root_flag:
        base += [root_flag, str(bench)]
    if c.per_backend:
        for bk in backends:
            invocations.append(base + ["--backend", bk])
    else:
        invocations.append(base)

    t0 = time.monotonic()
    ok, details, outs = True, [], []
    for argv in invocations:
        try:
            p = subprocess.run(argv, cwd=str(ROOT), capture_output=True, text=True,
                               env=env, timeout=timeout_s or c.timeout_s)
            out = (p.stdout or "") + (p.stderr or "")
            outs.append(out)
            if c.read_output is not None:
                good, why = c.read_output(out)
            else:
                good = p.returncode == 0
                why = ("clean" if good else
                       f"exit {p.returncode}: " + _last_meaningful(out))
            # Coverage, checked after the verdict and able to overturn a clean one.
            if c.measured is not None:
                n = c.measured(out)
                if n <= 0:
                    good = False
                    why = ("measured 0 cells (the check ran but looked at "
                           "nothing): " + _last_meaningful(out))
                elif good:
                    why = f"{why} over {n} cell(s)"
        except subprocess.TimeoutExpired:
            # A check that did not finish has NOT passed. Its own reason, because
            # the remedy differs: a timeout is usually a corpus-wide sweep
            # competing with a live repair wave, not a defect.
            good, why = False, f"timed out after {timeout_s or c.timeout_s}s"
            outs.append("")
        except OSError as e:
            good, why = False, f"could not run: {e}"
            outs.append("")
        ok = ok and good
        details.append(why)
    return {"name": c.name, "ok": ok, "why": c.why, "seconds": round(time.monotonic() - t0, 1),
            "detail": "; ".join(details), "output": "\n".join(outs)[-4000:]}


def _last_meaningful(out: str) -> str:
    """The most informative tail line of a failing check, for the summary table."""
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if not ln.startswith("#"):
            return ln[:160]
    return lines[-1][:160] if lines else "(no output)"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--backends", nargs="*", default=None,
                    help="default: every backend with bundles in the corpus")
    ap.add_argument("--only", nargs="*", default=[], help="run only these checks")
    ap.add_argument("--skip", nargs="*", default=[], help="skip these checks")
    ap.add_argument("--list", action="store_true", help="print the checks and exit")
    ap.add_argument("--timeout", type=int, default=0,
                    help="override every check's timeout (seconds)")
    ap.add_argument("--json", default="", help="write the full report here")
    ap.add_argument("--benchmark", default=os.environ.get("SBU_BENCHMARK")
                    or "swe_bench_verified",
                    help="which benchmark's task records the cells resolve against")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    if args.list:
        for c in CHECKS:
            print(f"{c.name:16s} {c.why}")
        return 0

    bench = (ROOT / args.benchmark_dir) if not Path(args.benchmark_dir).is_absolute() \
        else Path(args.benchmark_dir)
    if not bench.is_dir():
        print(f"no such corpus root: {bench}", file=sys.stderr)
        return 2
    # Set BEFORE the first package import: `paths` binds the dataset location from the
    # active benchmark at import time, so a preflight run after that would measure a
    # different benchmark than the checks do.
    os.environ["SBU_BENCHMARK_DIR"] = str(bench)
    os.environ.setdefault("SBU_BENCHMARK", args.benchmark)
    if args.backends is None:
        args.backends = corpus_backends(bench)
    if not args.backends:
        print(f"no bundles under {bench}", file=sys.stderr)
        return 2

    selected = [c for c in CHECKS
                if (not args.only or c.name in args.only) and c.name not in args.skip]
    unknown = set(args.only) - {c.name for c in CHECKS}
    if unknown:
        print(f"unknown check(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    env = check_env(bench, args.benchmark)
    print(f"# release gate: {bench.name}, backends {' '.join(args.backends)}, "
          f"{len(selected)} check(s)", flush=True)
    # A fetched input, so an empty `data/` is the normal state of a fresh checkout.
    # Said once, up front, rather than left to each check that reads a task record to
    # fail its own way: the checks that do not need it (prose, batteries) still run.
    from swebench_unified.gates.base import frozen_dataset_complaint
    missing = frozen_dataset_complaint(bench)
    if missing:
        print(f"# WARNING: {missing}\n"
              f"#          every check that resolves a task record will fail",
              flush=True)
    results = []
    for c in selected:
        print(f"# running {c.name} ...", flush=True)
        r = run_check(c, bench, args.backends, args.timeout or None, args.python, env)
        results.append(r)
        print(f"{'PASS' if r['ok'] else 'FAIL'}  {c.name:16s} {r['seconds']:7.1f}s  "
              f"{r['detail']}", flush=True)
        if not r["ok"]:
            # The tail of a failing check, indented, so the summary line need not
            # carry a whole table and the reader is not sent to a log.
            for ln in r["output"].splitlines()[-12:]:
                print(f"      | {ln[:200]}", flush=True)

    failed = [r["name"] for r in results if not r["ok"]]
    print(f"# {len(results) - len(failed)}/{len(results)} check(s) passed"
          + (f"; FAILED: {', '.join(failed)}" if failed else "; releasable"))
    if args.json:
        Path(args.json).write_text(json.dumps(
            {"corpus": str(bench), "backends": args.backends, "checks": results},
            indent=2, sort_keys=True))
        print(f"# report -> {args.json}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
