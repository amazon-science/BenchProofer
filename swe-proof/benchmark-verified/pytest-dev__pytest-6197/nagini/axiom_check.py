#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-6197.

This bundle consumes NO opaque-callee axiom: the load primitive (the collector
hook that produces a container's underlying object) is modelled DEEPLY in
model.py as the in-line state transition `loaded := True; load_count += 1`.
What G-AX must validate is therefore the single A-reference claim that the deep
model makes about reality:

  (A-reference) the REAL behaviour of the patched code matches the two modelled
      phases on the discriminating observable, the load side effect:

        * the discovery phase (enumerating a directory-backed container's
          children) performs ZERO loads of the container's own underlying
          object  -> model.py `enumerate_children`: load_count unchanged;
        * the access phase (reading the container's underlying object) performs
          the load lazily, exactly once, only if not already loaded
          -> model.py `access_object`: container becomes loaded, <= 1 load.

The observable is made concrete exactly as the FAIL_TO_PASS tests do: a package
whose `__init__.py` raises on import. If discovery loaded it (the bug), the run
errors; if discovery does not load it (the fix), the run succeeds.

PATCH-STATE CONTROL (this is the load-bearing correctness property of this
script). The SWE-bench instance image is checked out at `base_commit`, i.e. the
UNPATCHED, buggy tree. A check that asserts the *fixed* behaviour against that
tree would (correctly) fail — and would give a false witness if developed on a
host whose installed package happens to be patched. So this script does NOT
trust the ambient installed/in-tree pytest. It explicitly builds BOTH code
states from the in-container source and validates against each:

  * a PATCHED tree, produced by copying the repo checkout and applying the gold
    patch (`patch.diff`, mounted read-only by the harness) — phase-1 must PASS
    here (discovery performs zero loads); this is the deep model's claim;
  * the UNPATCHED tree (the bare checkout) — phase-1 must FAIL here (discovery
    eagerly loads, so a package whose load raises breaks the run); this turns
    the implicit discrimination into an explicit two-state check and proves the
    observable the deep model relies on actually distinguishes fixed from buggy.

Lazy load on demand is also checked against the PATCHED tree: a test that
actually imports a package whose load raises observes the import error, proving
the object IS still loadable lazily (the deferral is not a silent drop).

Each pytest invocation runs in a throwaway temp directory and is pinned to the
chosen source tree via `PYTHONPATH` + `-p no:cacheprovider`, exactly the way the
harness drives pytest. Imports nothing repo-specific: only the standard library.
The script locates the repo checkout and the gold patch automatically, so it is
correct whether or not the harness pre-applies the gold patch. Exit 0 iff every
obligation holds in BOTH states.
"""
import os
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap


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


def _run_pytest(workdir, src_tree, extra_args=()):
    """Run pytest in workdir using `src_tree` as the importable pytest source
    (pinned via PYTHONPATH); return (returncode, combined output)."""
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"]
    cmd.extend(extra_args)
    env = dict(os.environ)
    env["PYTHONPATH"] = src_tree + os.pathsep + env.get("PYTHONPATH", "")
    # `src` is where _pytest lives in this repo layout; put it first so the
    # chosen tree's pytest wins over any ambient install.
    env["PYTHONPATH"] = os.path.join(src_tree, "src") + os.pathsep + env["PYTHONPATH"]
    proc = subprocess.run(
        cmd, cwd=workdir, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return proc.returncode, proc.stdout


def _copy_tree(dst):
    shutil.copytree(REPO_CHECKOUT, dst, symlinks=True,
                    ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    return dst


def _patch(tree, reverse):
    """Apply (or reverse) the gold patch in `tree`; return (ok, output)."""
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
    already has the gold patch applied (e.g. the harness ran with
    apply_gold=True). Detection is by forward/reverse dry-run, so the script is
    correct under either invocation. Returns (patched_tree, unpatched_tree)."""
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


def _write(path, contents):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(textwrap.dedent(contents))


def _make_disc_layout(tmp, pkgname):
    """A rootdir with a top-level passing test plus a package whose load
    (import of __init__.py) raises. A run that does not reference the package
    must succeed iff discovery performs zero loads of the package object."""
    root = os.path.join(tmp, "disc_" + pkgname)
    _write(os.path.join(root, "test_top.py"), "def test():\n    pass\n")
    _write(os.path.join(root, pkgname, "__init__.py"), "assert False\n")
    return root


def _make_src_layout(tmp):
    """A `src` subpackage NOT on the path: must not be loaded by being merely
    discovered (the second FAIL_TO_PASS scenario)."""
    root = os.path.join(tmp, "srclayout")
    _write(os.path.join(root, "src", "nope", "__init__.py"), "")
    _write(os.path.join(root, "test_top.py"),
           """
           import pytest
           def test():
               with pytest.raises(ImportError):
                   import nope
           """)
    return root


def check_discovery_zero_loads(tmp, pkgname, src_tree):
    """A-reference, phase (1) on the PATCHED tree: enumerating children of a
    directory-backed container performs ZERO loads of its own underlying
    object, so a package whose load raises does NOT break an unrelated run.
    (model.py enumerate_children: load_count unchanged.)"""
    root = _make_disc_layout(tmp, pkgname)
    rc, out = _run_pytest(root, src_tree)
    assert rc == 0, (
        "patched discovery loaded the container's underlying object (eager "
        "load during enumeration): pytest rc=%r on a package whose load "
        "raises.\nmodel.py enumerate_children requires load_count unchanged.\n%s"
        % (rc, out))


def check_discovery_loads_when_buggy(tmp, pkgname, src_tree):
    """The differential: phase (1) on the UNPATCHED tree FAILS. The buggy
    discovery eagerly loads the package object, so the raising __init__.py
    surfaces and the run errors. This proves the load observable genuinely
    distinguishes fixed from buggy (G-DIFF made concrete against real pytest).
    """
    root = _make_disc_layout(tmp, "buggy_" + pkgname)
    rc, out = _run_pytest(root, src_tree)
    assert rc != 0, (
        "UNPATCHED discovery did NOT eagerly load (expected the base_commit "
        "bug): rc=%r on a package whose load raises. The two-state check is "
        "not discriminating — phase-1 cannot witness the fix.\n%s" % (rc, out))


def check_src_layout_not_loaded(tmp, src_tree):
    """A-reference, phase (1), second FAIL_TO_PASS scenario on the PATCHED
    tree: a `src` subpackage not on the path is not loaded merely by being
    discovered."""
    root = _make_src_layout(tmp)
    rc, out = _run_pytest(root, src_tree)
    assert rc == 0, (
        "patched src-layout package was eagerly loaded / put on path during "
        "discovery: pytest rc=%r.\n%s" % (rc, out))


def check_access_loads_lazily(tmp, src_tree):
    """A-reference, phase (2) on the PATCHED tree: the underlying object IS
    still loadable on demand (the deferral does not silently drop it). A
    package that DOES contain tests must have its own object loaded to collect
    those tests, so a raising __init__ surfaces as an error once that package's
    own object is genuinely accessed. (model.py access_object: an access loads
    exactly once and leaves the container loaded.)"""
    root = os.path.join(tmp, "lazyload")
    _write(os.path.join(root, "pkg", "__init__.py"), "assert False\n")
    _write(os.path.join(root, "pkg", "test_inside.py"), "def test():\n    pass\n")
    rc, out = _run_pytest(root, src_tree, extra_args=["pkg"])
    assert rc != 0, (
        "accessing the underlying object of a package with a raising load did "
        "NOT surface the load (object was never loaded on demand): rc=%r.\n%s"
        % (rc, out))
    assert "assert False" in out or "AssertionError" in out or "error" in out.lower(), (
        "lazy load did not actually run the failing __init__ on access:\n%s" % out)


def main():
    significant = ["foobar", "foopkg", "pkg", "a", "z0", "_x"]
    rng = random.Random(6197)

    with tempfile.TemporaryDirectory() as work:
        # Build the two code states explicitly from the in-container source,
        # robust to whether the live checkout is patched or at base_commit.
        patched, unpatched = _build_both_trees(work)

        with tempfile.TemporaryDirectory() as tmp:
            # === PATCHED tree: the deep model's claims must HOLD =============
            # phase (1): discovery performs zero loads (boundary names).
            for name in significant:
                check_discovery_zero_loads(tmp, name, patched)
            # phase (1), second FAIL_TO_PASS scenario.
            check_src_layout_not_loaded(tmp, patched)
            # phase (2): object still loaded lazily on demand (deferral != drop)
            check_access_loads_lazily(tmp, patched)
            # randomized fuzz: arbitrary package-name layouts, still zero loads.
            alphabet = "abcdefghijklmnopqrstuvwxyz_0123456789"
            for _ in range(8):
                n = rng.randint(1, 8)
                first = rng.choice("abcdefghijklmnopqrstuvwxyz_")
                rest = "".join(rng.choice(alphabet) for _ in range(n))
                name = first + rest
                check_discovery_zero_loads(tmp, name, patched)

            # === UNPATCHED tree: the bug must be PRESENT (differential) ======
            # phase (1) FAILS on the base_commit checkout: discovery eagerly
            # loads, so the raising package breaks the run. Proves the load
            # observable discriminates fixed from buggy.
            for name in significant:
                check_discovery_loads_when_buggy(tmp, name, unpatched)

    print("G-AX OK: against the PATCHED tree, real pytest discovery performs "
          "zero loads of a container's underlying object (FAIL_TO_PASS "
          "scenarios + boundary + fuzz) and the object is still loaded lazily "
          "on demand (deferral != drop); against the UNPATCHED (base_commit) "
          "tree, discovery eagerly loads and the raising package breaks the "
          "run. The deep model matches reality on the load-side-effect "
          "observable, and that observable discriminates fixed from buggy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
