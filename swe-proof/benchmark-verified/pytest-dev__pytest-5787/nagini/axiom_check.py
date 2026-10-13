#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-5787.

Drives the REAL patched pytest report (de)serializers end-to-end inside the
official SWE-bench container and asserts that the model's specified behaviour
holds of them.

The model spec (model.py) says:

  serialize(chain) carries every link in order, and deserialize is its inverse,
  so deserialize(serialize(chain)) == chain for chains of ANY length, in
  particular length >= 2 (a genuinely multi-stage / chained failure).

This is the A-reference check: the deep model (the per-link content-preserving
copy `copy_link`, and the whole-chain-preserving serialize/deserialize loops in
model.py) is validated == the real callees `BaseReport._to_json` /
`{TestReport,CollectReport}._from_json` (the `_report_to_json` /
`_report_kwargs_from_json` helpers). Each model link maps to one element of the
real ``ExceptionChainRepr.chain`` tuple ``(reprtraceback, reprcrash, desc)``.

NO DOUBLE MASK: the property under test is the COUNT and ORDER of links. The
inner test asserts it at exactly that level —
``len(loaded.longrepr.chain) == len(report.longrepr.chain)`` (>= 2 for the
chained cases) and a per-index match of each link's reconstructed traceback
text + description — never via a proxy filtered the same way on both sides. The
four F2P-relevant cases ({TestReport, CollectReport} x chained with/without an
explicit `from` cause) are enumerated and parametrized; a skip on any case is a
loud failure, and pytest's own exit code propagates.

PATCH-STATE CONTROL (the load-bearing correctness property of this script). The
SWE-bench instance image is checked out at `base_commit`, i.e. the UNPATCHED,
buggy tree (`_report_to_json` / `_report_kwargs_from_json` / the `chain` carry
are ABSENT; the pre-patch `_to_json`/`_from_json` collapse a chained failure to
its outermost link). A check that asserts the *fixed* whole-chain round trip
against that tree would (correctly) fail. So this script does NOT trust the
ambient in-tree pytest. It explicitly builds BOTH code states from the
in-container source and validates against each:

  * a PATCHED tree, produced by copying the repo checkout and applying the gold
    patch (`patch.diff`, mounted read-only by the harness at /work) — the whole
    chain (count >= 2 + order + per-link content) must SURVIVE the round trip;
    this is the deep model's claim;
  * the UNPATCHED tree (the bare checkout) — the round trip must COLLAPSE the
    chain (length drops below the original >= 2): this turns the implicit
    discrimination into an explicit two-state check and proves the observable
    the deep model relies on actually distinguishes fixed from buggy.

Detection is by forward/reverse `patch --dry-run`, so the script is correct
whether or not the harness pre-applies the gold patch. Each chosen tree is
pinned as the importable pytest via ``PYTHONPATH=<tree>/src`` (so it wins over
any ambient install), exactly the way the harness drives pytest. Imports
nothing repo-specific in this outer driver: only the standard library. Exit 0
iff the whole chain survives on the PATCHED tree AND collapses on the UNPATCHED
tree, for every F2P-relevant case.
"""
import os
import shutil
import subprocess
import sys
import tempfile


# --- locate the in-container repo checkout and the mounted gold patch --------
def _first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


# SWE-bench instance images check the repo out at /testbed; the harness mounts
# the bundle dir read-only at /work, so patch.diff is at /work/patch.diff.
REPO_CHECKOUT = _first_existing([
    os.environ.get("TESTBED"),
    "/testbed",
    os.getcwd(),
])
GOLD_PATCH = _first_existing([
    "/work/patch.diff",
    "/gold.patch",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "patch.diff"),
])


# The inner pytest module: it owns the `testdir` fixture, builds REAL chained-
# exception reports, runs the REAL _to_json/_from_json round trip, and decides
# whether the whole chain (count + order + per-link content) survives. It does
# NOT assert survival itself; instead it prints a machine-readable verdict line
# (SURVIVED / COLLAPSED) per case, so the outer driver can require survival on
# the patched tree and collapse on the unpatched tree. The outer driver still
# fails loud on any pytest error / skip (rc != 0 or missing verdict lines).
INNER_TEST = r'''
import pytest
from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport, CollectReport


def _build_report(testdir, chained_with_from, as_collect):
    """Run a tiny test module that raises a chained exception and return the
    real failure report (TestReport call-phase, or CollectReport)."""
    if chained_with_from:
        raise_line = "raise RuntimeError('runtime error') from e"
    else:
        raise_line = "raise RuntimeError('runtime error')"
    src = (
        "def foo():\n"
        "    raise ValueError('value error')\n"
        "def test_a():\n"
        "    try:\n"
        "        foo()\n"
        "    except ValueError as e:\n"
        "        " + raise_line + "\n"
    )
    if as_collect:
        # raise at import time -> a CollectReport carries the chained failure
        src += "test_a()\n"
    testdir.makepyfile(src)

    reprec = testdir.inline_run()
    if as_collect:
        reports = reprec.getreports("pytest_collectreport")
        failed = [r for r in reports if r.failed]
        assert len(failed) == 1, (
            "expected exactly 1 failed collect report, got %d (F2P "
            "CollectReport case skipped)" % len(failed))
        return failed[0]
    else:
        reports = reprec.getreports("pytest_runtest_logreport")
        call = [r for r in reports if getattr(r, "when", None) == "call"]
        assert len(call) == 1, (
            "expected exactly 1 call-phase report, got %d (F2P TestReport "
            "case skipped)" % len(call))
        assert call[0].failed, "call-phase report not failed (F2P skipped)"
        return call[0]


def _chain_of(longrepr):
    """The list of links of a failure representation, as the model sees it.

    Post-patch ``ExceptionChainRepr`` exposes ``.chain`` (the whole chain).
    The pre-patch round trip rebuilds a plain ``ReprExceptionInfo`` with no
    ``.chain`` -- a single collapsed link -- which this normalises to a
    length-1 list, so the COLLAPSE is observable as a length drop."""
    chain = getattr(longrepr, "chain", None)
    if chain is not None:
        return list(chain)
    return [(getattr(longrepr, "reprtraceback", None),
             getattr(longrepr, "reprcrash", None), None)]


def _fingerprint(link):
    """Content-bearing fingerprint of one link: traceback text + description."""
    reprtraceback, reprcrash, description = link
    return (str(reprtraceback), description)


class _TW:
    WRITE = object()

    def __init__(self):
        self.lines = []
        self.is_writing = False

    def sep(self, sep, line=None):
        self.lines.append((sep, line))

    def write(self, msg, **kw):
        self.lines.append((_TW.WRITE, msg))

    def line(self, line, **kw):
        self.lines.append(line)

    def markup(self, text, **kw):
        return text

    def get_write_msg(self, idx):
        flag, msg = self.lines[idx]
        assert flag == _TW.WRITE
        return msg

    fullwidth = 80


# report_class is CollectReport  <=>  as_collect  (mirrors the gold F2P test,
# whose `error_during_import` is `report_class is CollectReport`). Building a
# report of one class but calling the *other* class's `_from_json` would crash
# `cls(**kwargs)`; the invariant below keeps build-class == deserialize-class.
@pytest.mark.parametrize("report_class,with_from,as_collect", [
    (TestReport,    False, False),  # implicit context, call-time
    (TestReport,    True,  False),  # explicit `from`, call-time
    (CollectReport, False, True),   # implicit context, collect-time
    (CollectReport, True,  True),   # explicit `from`, collect-time
])
def test_chain_roundtrip(testdir, report_class, with_from, as_collect):
    case = "%s/from=%s" % (report_class.__name__, with_from)
    report = _build_report(testdir, with_from, as_collect)
    assert report.failed
    assert len(report.sections) == 0

    # add a section so the round trip also has to carry sections (as F2P does)
    report.longrepr.addsection("title", "contents", "=")

    original = report.longrepr
    original_chain = _chain_of(original)

    # genuinely-chained failures must have >= 2 links, else non-discriminating.
    # (Both an explicit `from` and an implicit handling-context build a chain.)
    assert isinstance(original, ExceptionChainRepr), type(original).__name__
    assert len(original_chain) >= 2, len(original_chain)

    # --- the REAL callees (pre- or post-patch, per the pinned tree) ---
    data = report._to_json()                  # (post-patch: _report_to_json)
    loaded = report_class._from_json(data)     # (post-patch: _report_kwargs_from_json)
    loaded_chain = _chain_of(loaded.longrepr)

    survived = (
        isinstance(loaded.longrepr, ExceptionChainRepr)
        and len(loaded_chain) == len(original_chain)
        and all(_fingerprint(original_chain[k]) == _fingerprint(loaded_chain[k])
                for k in range(len(original_chain)))
    )

    if survived:
        # sections survive alongside the chain; reconstructed object renders.
        assert loaded.longrepr.sections == [("title", "contents", "=")], \
            loaded.longrepr.sections
        loaded.longrepr.toterminal(_TW())
        print("GAX_VERDICT %s SURVIVED before=%d after=%d"
              % (case, len(original_chain), len(loaded_chain)))
    else:
        print("GAX_VERDICT %s COLLAPSED before=%d after=%d type=%s"
              % (case, len(original_chain), len(loaded_chain),
                 type(loaded.longrepr).__name__))
'''


# The four F2P-relevant cases, in the order the inner parametrize emits them.
CASES = [
    "TestReport/from=False",
    "TestReport/from=True",
    "CollectReport/from=False",
    "CollectReport/from=True",
]


def _copy_tree(dst):
    shutil.copytree(REPO_CHECKOUT, dst, symlinks=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    return dst


def _patch(tree, reverse):
    cmd = ["patch", "-p1", "--no-backup-if-mismatch", "-i", GOLD_PATCH]
    if reverse:
        cmd.insert(1, "-R")
    res = subprocess.run(cmd, cwd=tree, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, universal_newlines=True)
    return res.returncode == 0, res.stdout


def _dry_run(tree, reverse):
    cmd = ["patch", "-p1", "--dry-run", "-i", GOLD_PATCH]
    if reverse:
        cmd.insert(1, "-R")
    res = subprocess.run(cmd, cwd=tree, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, universal_newlines=True)
    return res.returncode == 0


def _build_both_trees(work):
    """Build a PATCHED and an UNPATCHED copy of the repo, regardless of whether
    the live checkout is at base_commit (the normal SWE-bench image state) or
    already has the gold patch applied. Detection is by forward/reverse
    dry-run, so the script is correct under either invocation. Returns
    (patched_tree, unpatched_tree)."""
    if not REPO_CHECKOUT:
        raise RuntimeError("could not locate repo checkout (expected /testbed)")
    if not GOLD_PATCH:
        raise RuntimeError("could not locate gold patch (expected /work/patch.diff)")
    base = _copy_tree(os.path.join(work, "base"))
    if _dry_run(base, reverse=False):
        # live checkout is UNPATCHED (base_commit): apply forward -> patched.
        patched = _copy_tree(os.path.join(work, "patched"))
        ok, out = _patch(patched, reverse=False)
        if not ok:
            raise RuntimeError("failed to apply gold patch:\n" + out)
        return patched, base
    if _dry_run(base, reverse=True):
        # live checkout is already PATCHED: reverse-apply a copy -> unpatched.
        unpatched = _copy_tree(os.path.join(work, "unpatched"))
        ok, out = _patch(unpatched, reverse=True)
        if not ok:
            raise RuntimeError("failed to reverse gold patch:\n" + out)
        return base, unpatched
    raise RuntimeError(
        "gold patch applies in neither direction against the checkout; the "
        "patch does not match this source tree")


def _run_inner(inner_path, src_tree):
    """Run the inner pytest module against `src_tree`'s pytest (pinned via
    PYTHONPATH); return (returncode, combined output)."""
    cmd = [sys.executable, "-m", "pytest", "-p", "pytester",
           "-p", "no:cacheprovider", "-q", "-s", "-rA", inner_path]
    env = dict(os.environ)
    # Put the chosen tree's `src` first so its _pytest wins over any ambient
    # install (this repo lays pytest out under <tree>/src/_pytest).
    env["PYTHONPATH"] = (os.path.join(src_tree, "src") + os.pathsep
                         + src_tree + os.pathsep + env.get("PYTHONPATH", ""))
    proc = subprocess.run(cmd, cwd=os.path.dirname(inner_path), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          universal_newlines=True)
    return proc.returncode, proc.stdout


def _verdicts(out):
    """Parse the per-case GAX_VERDICT lines into {case: 'SURVIVED'|'COLLAPSED'}."""
    res = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("GAX_VERDICT "):
            parts = line.split()
            res[parts[1]] = parts[2]
    return res


def main():
    with tempfile.TemporaryDirectory(prefix="gax5787_") as work:
        # Build the two code states explicitly from the in-container source,
        # robust to whether the live checkout is patched or at base_commit.
        patched, unpatched = _build_both_trees(work)

        inner = os.path.join(work, "test_chain_serialization.py")
        with open(inner, "w") as fh:
            fh.write(INNER_TEST)

        # === PATCHED tree: the whole chain MUST survive every case. ==========
        rc_p, out_p = _run_inner(inner, patched)
        if rc_p != 0:
            sys.stdout.write(out_p)
            print("G-AX FAIL: inner test errored on the PATCHED tree (pytest "
                  "rc=%s) -- could not exercise the real round trip." % rc_p)
            return 1
        v_p = _verdicts(out_p)
        for case in CASES:
            if case not in v_p:
                sys.stdout.write(out_p)
                print("G-AX FAIL: F2P-relevant case %r was skipped / not run on "
                      "the PATCHED tree (no verdict emitted)." % case)
                return 1
            if v_p[case] != "SURVIVED":
                sys.stdout.write(out_p)
                print("G-AX FAIL: PATCHED real round trip did NOT preserve the "
                      "whole exception chain for %r (verdict=%s). The deep "
                      "model (whole-chain round-trip identity) does not match "
                      "reality." % (case, v_p[case]))
                return 1

        # === UNPATCHED (base_commit) tree: the chain MUST collapse. ==========
        # Proves the count/order observable genuinely discriminates fixed from
        # buggy (G-DIFF made concrete against the real pre-patch callees).
        rc_u, out_u = _run_inner(inner, unpatched)
        # The inner module never asserts survival, so a clean rc=0 with COLLAPSED
        # verdicts is expected; a non-zero rc means the build/round-trip itself
        # broke (which would be a non-discriminating, inconclusive run).
        if rc_u != 0:
            sys.stdout.write(out_u)
            print("G-AX FAIL: inner test errored on the UNPATCHED tree (pytest "
                  "rc=%s) -- the differential run is inconclusive." % rc_u)
            return 1
        v_u = _verdicts(out_u)
        for case in CASES:
            if case not in v_u:
                sys.stdout.write(out_u)
                print("G-AX FAIL: F2P-relevant case %r was skipped / not run on "
                      "the UNPATCHED tree (no verdict emitted)." % case)
                return 1
            if v_u[case] != "COLLAPSED":
                sys.stdout.write(out_u)
                print("G-AX FAIL: UNPATCHED (base_commit) real round trip did "
                      "NOT collapse the chain for %r (verdict=%s). The observable "
                      "is not discriminating -- it cannot witness the fix."
                      % (case, v_u[case]))
                return 1

    print("G-AX OK: against the PATCHED tree, the real pytest report "
          "(de)serialization preserves the WHOLE exception chain (count + "
          "order + per-link traceback text + description + sections, and "
          "renders) for TestReport and CollectReport, chained with and without "
          "an explicit `from`; against the UNPATCHED (base_commit) tree the "
          "same round trip COLLAPSES the chain. The deep model (whole-chain "
          "round-trip identity, copy_link = identity) matches reality, and the "
          "count/order observable discriminates fixed from buggy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
