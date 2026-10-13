#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7982 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python. The modeled `do` block selects, at ONE directory level,
              the child entries to descend into: `descendableSeq` keeps each
              child for which `isDirectory and shouldRecurse` holds, in encounter
              order (the per-code-point backward fold computes exactly this
              left-to-right filter). The depth recursion of the walk is the
              I-tagged, unchanged recursive step (refinement.md §B): the shadow
              replicates it directly. The abstract booleans of `DirChild` are
              R-tagged observations: `isDirectory` ↔ the real `os.DirEntry`'s
              directory test resolving symbolic links, `shouldRecurse` ↔ the
              walk's recursion predicate. There are NO A-tagged callees in the
              impl region (no axioms in this bundle), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `_pytest.pathlib.visit`
              applied at base_commit, observed as the SET of entry paths it
              yields when walking a real on-disk directory tree (the harness
              applies patch.diff before this runs). `visit` yields every entry at
              each level and recurses into a child exactly when the (patched)
              guard accepts it, so the yielded-path set is the observable that
              the one-line guard change governs.

They must agree on every generated tree. Exit 0 iff zero disagreements; any
disagreement is a mechanical R/I-fidelity counterexample. At the UNPATCHED base
the guard tests `is_dir(follow_symlinks=False)`, which drops the contents of a
symlinked directory and disagrees with the shadow — G-CONF validates the PATCHED
behaviour only, as intended.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import shutil
import sys
import tempfile

SEED = 7982
N_FUZZ = 4000  # each input is a whole on-disk tree; far fewer, far heavier


# --- the recursion predicate the walk is driven with -------------------------
def recurse(direntry):
    """The walk's recursion predicate (the `recurse` argument of `visit`),
    abstracted as the R-input `shouldRecurse`. We model pytest's real default
    shape: do not recurse into a child whose basename matches a 'norecurse'
    pattern. Here: skip names beginning with '.' or equal to '__pycache__'. The
    exact predicate is opaque to the model; what matters is that SHADOW and
    ORACLE are driven with the SAME predicate."""
    name = os.path.basename(direntry.path)
    return not (name.startswith(".") or name == "__pycache__")


# --- the R/I shadow: descendableSeq + the I-tagged depth recursion -----------
def descendable_seq(entries):
    """`descendableSeq` (Solution.lean pure region), over real DirEntry objects.
    Keep each child for which `isDirectory and shouldRecurse` holds, in order.
        isDirectory   <- entry.is_dir()         (resolves symlinks)
        shouldRecurse <- recurse(entry)
    """
    out = []
    for e in entries:
        is_directory = e.is_dir()            # the post-patch directory test
        should_recurse = recurse(e)
        if is_directory and should_recurse:  # descend e
            out.append(e)
    return out


def shadow_visit(path):
    """The R/I shadow of the whole walk: yield every entry at each level, then
    recurse into exactly the `descendableSeq` selection (the unchanged I-tagged
    depth recursion). Returns the set of yielded entry paths, observed as the
    LITERAL path each entry was reached through (NOT symlink-resolved): a
    symlinked directory `s -> d` yields `s/child`, distinct from `d/child`, so
    whether the walk follows the link is observable. This is exactly what
    `visit` yields and what pytest collection keys on."""
    yielded = set()
    entries = sorted(os.scandir(path), key=lambda entry: entry.name)
    for entry in entries:
        yielded.add(os.path.normpath(entry.path))
    for entry in descendable_seq(entries):
        yielded |= shadow_visit(entry.path)
    return yielded


# --- the oracle: the patched real _pytest.pathlib.visit ----------------------
def oracle_visit(path):
    """patch.diff's behaviour: the patched `visit`. Returns the set of yielded
    entry paths, observed as the literal path each entry was reached through (so
    a followed symlinked directory's children are distinguishable from the
    target's own children)."""
    from _pytest.pathlib import visit
    return {os.path.normpath(entry.path) for entry in visit(path, recurse)}


# --- input generation: random on-disk directory trees w/ symlinks ------------
def _build_tree(rng, root, depth):
    """Populate `root` with a random mix of files, real subdirectories, symlinks
    to directories, symlinks to files, and broken symlinks. Returns nothing; the
    tree on disk is the input."""
    n = rng.randint(0, 4)
    made_dirs = []
    made_files = []
    for k in range(n):
        kind = rng.random()
        # bias names: some hidden ('.x'), some __pycache__, most ordinary
        r = rng.random()
        if r < 0.12:
            name = "." + "abc"[rng.randint(0, 2)] + str(k)
        elif r < 0.18:
            name = "__pycache__"
        else:
            name = "n%d_%d" % (depth, k)
        p = os.path.join(root, name)
        if os.path.lexists(p):
            continue
        if kind < 0.40:                       # real subdirectory
            os.mkdir(p)
            made_dirs.append(p)
            if depth > 0:
                _build_tree(rng, p, depth - 1)
        elif kind < 0.65:                     # regular file
            with open(p, "w") as fh:
                fh.write("x")
            made_files.append(p)
        elif kind < 0.85:                     # symlink to a directory
            tgt_dir = os.path.join(root, "_t_dir_%d" % k)
            if not os.path.lexists(tgt_dir):
                os.mkdir(tgt_dir)
                with open(os.path.join(tgt_dir, "f.txt"), "w") as fh:
                    fh.write("y")
            try:
                os.symlink(tgt_dir, p)
            except (OSError, NotImplementedError):
                pass
        elif kind < 0.95:                     # symlink to a file
            tgt_file = made_files[-1] if made_files else os.path.join(root, "_t_f_%d" % k)
            if not os.path.lexists(tgt_file):
                with open(tgt_file, "w") as fh:
                    fh.write("z")
            try:
                os.symlink(tgt_file, p)
            except (OSError, NotImplementedError):
                pass
        else:                                 # broken symlink
            try:
                os.symlink(os.path.join(root, "does_not_exist_%d" % k), p)
            except (OSError, NotImplementedError):
                pass


def make_input(rng):
    base = tempfile.mkdtemp(prefix="gconf7982_")
    _build_tree(rng, base, depth=rng.randint(0, 3))
    return base


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for _ in range(N_FUZZ):
        base = make_input(rng)
        count += 1
        try:
            shadow = shadow_visit(base)
            oracle = oracle_visit(base)
            if shadow != oracle:
                only_shadow = sorted(shadow - oracle)[:4]
                only_oracle = sorted(oracle - shadow)[:4]
                disagreements.append((base, only_shadow, only_oracle))
        finally:
            shutil.rmtree(base, ignore_errors=True)
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d trees:"
              % (len(disagreements), count))
        for base, sh_only, orc_only in disagreements:
            print("  tree=%r shadow_only=%r oracle_only=%r"
                  % (base, sh_only, orc_only))
        return 1
    print("G-CONF OK: R/I shadow of descendableEntries (descendableSeq + the "
          "unchanged depth recursion) agrees with patch.diff behaviour through "
          "the real patched _pytest.pathlib.visit on %d random directory trees "
          "(seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
