#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-7982 (nagini).

SHADOW: the impl region of model.py `descend_decisions`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped and PSeq
realized as an immutable tuple shim. The @Pure helpers `resolves_to_dir` /
`should_descend` copy over as plain functions (`should_descend` is used only
by contracts, so the impl body never calls it; it is kept for completeness).
There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`_pytest.pathlib.visit`, the directory walk whose per-entry descent decision
for one directory level is the modeled behaviour. The gate applies patch.diff
to /testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable.

Type bridge (mapping.md section 2): one directory level's sorted entry list
maps to two parallel sequences -- `kinds[i]` is the classification code of
entry i (0 = regular file, 1 = plain directory, 2 = link whose target is a
directory, 3 = link whose target is not a directory / broken) and
`selected[i]` is the caller predicate's verdict for entry i. To exercise the
real callee, each (kinds, selected) input is realized as an actual on-disk
tree: one entry per code under a walked root (link targets live in a sibling
scaffold directory so the walked level contains exactly the coded entries),
names chosen so the walk's sorted order equals index order, and every
directory target seeded with a marker file. The caller predicate is a lookup
table keyed by entry name (False for anything unanticipated, e.g. the marker
files). The real per-entry descent decision is then OBSERVED: the walk
descends into entry i iff the marker file beneath entry i's own path appears
in the walk's yielded stream (the walk lists a level's entries before
descending, so the marker is yielded exactly when the descent for that entry
executed).

Input domain: Requires demands only len(kinds) == len(selected); generation
keeps codes in {0,1,2,3} (the carrier's documented alphabet -- the bijection
in mapping.md covers exactly these four entry classifications, so other ints
have no filesystem realization) and selected free booleans.

>= 1e5 Requires-satisfying inputs:
  * exhaustive boundary: every kinds vector of length 0..4 over {0,1,2,3}
    crossed with every selected vector (sum over k of 8^k = 4681 inputs);
  * fuzz: 1500 random kinds vectors (length 0..10) x 64 random selected
    vectors each = 96000 inputs.
Total 100681. Pinned fuzz seed: 79820.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import itertools
import json
import os
import random
import sys
import tempfile

SEED = 79820
N_FUZZ_TREES = 1500
N_SELECTED_PER_TREE = 64
EXHAUSTIVE_MAX_LEN = 4


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure helpers from model.py, contracts stripped ---------------------------

def resolves_to_dir(kind):
    return kind == 1 or kind == 2


def should_descend(kind, selected):
    return resolves_to_dir(kind) and selected


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def descend_decisions(kinds, selected):
    result = PSeq(True).take(0)  # type: PSeq
    i = 0
    n = len(kinds)
    while i < n:
        # Classify the entry by following any link to its target, then require
        # the caller predicate to have selected it.
        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool
        old_result = result  # type: PSeq
        result = result + PSeq(decision)
        i = i + 1
    return result


# --- oracle: realize one directory level on disk and observe the real walk ----

MARKER = "marker"


def build_level(base, codes):
    """Create the walked root with one entry per classification code, names in
    index order; link targets go in a sibling scaffold dir so the walked level
    contains exactly the coded entries. Every directory target gets a marker
    file so a descent into it is observable in the yielded stream. Returns
    (root, names)."""
    root = os.path.join(base, "root")
    scaffold = os.path.join(base, "scaffold")
    os.mkdir(root)
    os.mkdir(scaffold)
    names = []
    for idx, code in enumerate(codes):
        name = "entry_%03d" % idx
        p = os.path.join(root, name)
        if code == 0:
            with open(p, "w") as fh:
                fh.write("x")
        elif code == 1:
            os.mkdir(p)
            with open(os.path.join(p, MARKER), "w") as fh:
                fh.write("m")
        elif code == 2:
            target = os.path.join(scaffold, "target_dir_%03d" % idx)
            os.mkdir(target)
            with open(os.path.join(target, MARKER), "w") as fh:
                fh.write("m")
            os.symlink(target, p)
        elif code == 3:
            if idx % 2 == 0:
                target = os.path.join(scaffold, "target_file_%03d" % idx)
                with open(target, "w") as fh:
                    fh.write("y")
            else:
                target = os.path.join(scaffold, "missing_%03d" % idx)  # broken
            os.symlink(target, p)
        else:
            raise AssertionError("unknown code %r" % (code,))
        names.append(name)
    return root, names


def real_decisions(visit_fn, root, names, selected):
    """Run the real walk over one prepared level with the given predicate
    verdicts and observe the per-entry descent decisions: entry i was
    descended into iff the marker beneath its own path was yielded."""
    verdicts = dict(zip(names, selected))

    def recurse(entry):
        return verdicts.get(entry.name, False)

    yielded = {e.path for e in visit_fn(root, recurse)}
    return [os.path.join(root, name, MARKER) in yielded for name in names]


def check_level(visit_fn, codes, selected_vectors):
    """Build one level, run every selected vector over it, diff shadow vs
    real. Returns (n_checked, error_string_or_None)."""
    checked = 0
    with tempfile.TemporaryDirectory() as base:
        root, names = build_level(base, codes)
        for selected in selected_vectors:
            shadow = descend_decisions(PSeq._wrap(codes), PSeq._wrap(selected))
            shadow_list = [shadow[i] for i in range(len(shadow))]
            real = real_decisions(visit_fn, root, names, selected)
            checked += 1
            if shadow_list != real:
                return checked, (
                    "DISAGREEMENT\n  kinds=%r\n  selected=%r\n  shadow=%r\n"
                    "  real=%r" % (list(codes), list(selected),
                                   shadow_list, real))
    return checked, None


def all_selected_vectors(n):
    return [list(bits) for bits in itertools.product([False, True], repeat=n)]


def main():
    from _pytest.pathlib import visit  # REAL patched repo function

    checked = 0

    # exhaustive boundary: every level of length 0..4, every predicate vector
    for k in range(EXHAUSTIVE_MAX_LEN + 1):
        sel_vecs = all_selected_vectors(k)
        for codes in itertools.product([0, 1, 2, 3], repeat=k):
            n, err = check_level(visit, list(codes), sel_vecs)
            checked += n
            if err:
                print(err)
                return 1

    # fuzz: random levels x random predicate vectors, pinned seed
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_TREES):
        n_entries = rng.randint(0, 10)
        codes = [rng.choice([0, 1, 2, 3]) for _ in range(n_entries)]
        sel_vecs = [[rng.random() < 0.5 for _ in range(n_entries)]
                    for _ in range(N_SELECTED_PER_TREE)]
        n, err = check_level(visit, codes, sel_vecs)
        checked += n
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real walk's per-entry descent decisions "
          "on %d inputs (4681 exhaustive boundary + %d fuzz, seed %d)."
          % (checked, N_FUZZ_TREES * N_SELECTED_PER_TREE, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
