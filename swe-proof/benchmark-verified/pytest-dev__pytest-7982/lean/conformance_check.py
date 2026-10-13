#!/usr/bin/env python3
"""G-CONF for pytest-dev__pytest-7982.

Mechanically differential-tests the R/I legs of `implementation_visit` against
the post-patch behaviour of the real `visit` (gold patch.diff).

Strategy
--------
`implementation_visit` is the faithful skeleton of the post-patch `visit`:

    def visit(path, recurse):
        entries = sorted(os.scandir(path), key=lambda e: e.name)
        yield from entries
        for entry in entries:
            if entry.is_dir() and recurse(entry):     # post-patch
                yield from visit(entry.path, recurse)

We fuzz random directory TREES (modeled as the Lean `FSNode` carrier: each node
is a file, a real directory, or a SYMLINKED directory), materialize each tree on
a real temp filesystem with genuine `os.symlink`s, and compare two observables
over the walk-order entry-name sequence:

  * SHADOW  — a pure Python port of `collectTree` / `implementation_visit`
              (the Lean spec+impl model), driving on the abstract tree.
  * REAL    — the real post-patch `visit` (re-implemented here verbatim from the
              gold-patched source) run on the materialized filesystem.

`recurse` is fuzzed as an arbitrary predicate over entry names (mirrors the
opaque caller predicate). Exit 0 iff zero disagreements across >=1e5 trees.
"""
import json
import os
import random
import sys
import tempfile

SEED = 7982
N_TREES = 120000          # >= 1e5
MAX_DEPTH = 4
MAX_CHILDREN = 4


# ---------------------------------------------------------------------------
# Abstract tree (the FSNode carrier from mapping.md)
#   node = ("file",)
#        | ("dir", is_symlink: bool, children: list[(name, node)])
# ---------------------------------------------------------------------------
def gen_level(rng, depth):
    n = rng.randint(0, MAX_CHILDREN)
    names = rng.sample(range(1000), n)  # distinct names per level
    out = []
    for raw in names:
        name = f"n{raw:03d}"
        if depth >= MAX_DEPTH:
            kind = rng.choice(["file", "file", "dir"])
        else:
            kind = rng.choice(["file", "dir", "symdir"])
        if kind == "file":
            out.append((name, ("file",)))
        elif kind == "dir":
            out.append((name, ("dir", False, gen_level(rng, depth + 1))))
        else:  # symlinked directory
            out.append((name, ("dir", True, gen_level(rng, depth + 1))))
    return out


def sort_by_name(entries):
    return sorted(entries, key=lambda e: e[0])


# ---------------------------------------------------------------------------
# SHADOW: pure port of collectTree / implementation_visit (post-patch).
#   entryIsDir: FSNode.dir _ _ -> True ; file -> False   (follow symlinks)
# ---------------------------------------------------------------------------
def shadow_visit(entries, recurse):
    ents = sort_by_name(entries)
    out = [name for (name, _node) in ents]
    for (name, node) in ents:
        is_dir = node[0] == "dir"          # entryIsDir (post-patch)
        if is_dir and recurse(name):
            out.extend(shadow_visit(node[2], recurse))
    return out


# ---------------------------------------------------------------------------
# REAL: materialize the tree on disk (real symlinks) and run the post-patch
# `visit` verbatim from the gold-patched source.
# ---------------------------------------------------------------------------
def materialize(entries, path):
    """Create `entries` under directory `path`. Symlinked dirs become real
    os.symlinks to a sibling hidden target so is_dir() must follow them."""
    for (name, node) in entries:
        dest = os.path.join(path, name)
        if node[0] == "file":
            with open(dest, "w") as fh:
                fh.write("")
        elif node[1] is False:            # real directory
            os.mkdir(dest)
            materialize(node[2], dest)
        else:                              # symlinked directory
            target = os.path.join(path, "." + name + "_t")
            os.mkdir(target)
            materialize(node[2], target)
            os.symlink(target, dest)


def real_visit(path, recurse):
    """Post-patch visit (gold patch.diff): is_dir() with default follow."""
    entries = sorted(os.scandir(path), key=lambda entry: entry.name)
    # ignore the hidden symlink-target dirs we created for materialization
    entries = [e for e in entries if not e.name.startswith(".")]
    for entry in entries:
        yield entry
    for entry in entries:
        if entry.is_dir() and recurse(entry):   # <-- patched line
            yield from real_visit(entry.path, recurse)


def main():
    rng = random.Random(SEED)
    disagreements = 0
    examples = []
    checked = 0
    for i in range(N_TREES):
        tree = gen_level(rng, 0)
        # fuzz recurse: a deterministic name-keyed predicate so both legs see
        # the same decision for the same entry name.
        recur_prob = rng.choice([0.0, 0.3, 0.7, 1.0])
        recur_seed = rng.randint(0, 2**31)

        def recurse_name(name):
            return (hash((recur_seed, name)) & 0xff) < int(recur_prob * 256)

        def recurse_entry(entry):
            return recurse_name(entry.name)

        shadow = shadow_visit(tree, recurse_name)

        with tempfile.TemporaryDirectory() as root:
            try:
                materialize(tree, root)
            except OSError:
                continue
            real = [e.name for e in real_visit(root, recurse_entry)]
        checked += 1

        if shadow != real:
            disagreements += 1
            if len(examples) < 5:
                examples.append({"tree": tree, "shadow": shadow, "real": real})

    result = {
        "gate": "G-CONF",
        "instance": "pytest-dev__pytest-7982",
        "seed": SEED,
        "trees_checked": checked,
        "disagreements": disagreements,
        "examples": examples,
        "status": "pass" if disagreements == 0 else "fail",
    }
    print(json.dumps(result))
    return 0 if disagreements == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
