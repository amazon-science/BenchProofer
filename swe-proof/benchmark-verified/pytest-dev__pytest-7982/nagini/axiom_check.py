#!/usr/bin/env python3
"""G-AX executable soundness check for pytest-dev__pytest-7982.

The "resolves to a directory" classification that gates descent during a
directory walk is modelled DEEPLY in model.py as the pure predicate
`resolves_to_dir(kind)` (true for codes 1 and 2). It is NOT a consumed axiom;
G-AX validates that deep model against the REAL filesystem callee that the
patched code uses to classify an entry: `os.DirEntry.is_dir()` with its default
`follow_symlinks=True` (the link is followed when classifying it).

This check builds a real on-disk tree containing one instance of each modelled
classification code:

    0 = a non-directory entry (regular file)
    1 = a plain directory
    2 = a link whose target is a directory   <-- the discriminating case
    3 = a link whose target is not a directory / a broken link

scandirs the parent, and for every entry asserts:

    os.DirEntry.is_dir()                    ==  resolves_to_dir(kind)     # follow
    os.DirEntry.is_dir(follow_symlinks=False)  ==  (kind == 1)            # no-follow

The first equality is the soundness of the deep model (A-reference): the model
of the changed/desired behaviour equals what the real follow-symlinks
classification reports. The second documents the pre-patch (no-follow) callee
and confirms it disagrees exactly on code 2 -- the link-to-directory the F2P
test exercises. Many random trees of mixed entries are fuzzed as well.

Imports nothing repo-specific: `os`, `tempfile`, `random` are the standard
library. Exit 0 iff every observation matches the model.
"""
import os
import random
import sys
import tempfile


# --- model.py reference encoding (kept in lock-step with the pure region) ----

def resolves_to_dir(kind):
    """Reference of model.py's deep model `resolves_to_dir`: true iff the entry
    resolves to a directory (plain directory or link-to-directory)."""
    return kind == 1 or kind == 2


# --- build one tree with every classification code ----------------------------

def build_tree(root, codes):
    """Create one entry per requested classification code under `root`. Returns
    a dict mapping entry name -> intended code."""
    name_to_code = {}
    for idx, code in enumerate(codes):
        if code == 0:
            name = "file_%d" % idx
            p = os.path.join(root, name)
            with open(p, "w") as fh:
                fh.write("x")
        elif code == 1:
            name = "dir_%d" % idx
            os.mkdir(os.path.join(root, name))
        elif code == 2:
            # a link whose target is a (real) directory
            target = os.path.join(root, "target_dir_%d" % idx)
            os.mkdir(target)
            name = "link_to_dir_%d" % idx
            os.symlink(target, os.path.join(root, name))
        elif code == 3:
            # a link whose target is a regular file OR a broken link
            if idx % 2 == 0:
                target = os.path.join(root, "target_file_%d" % idx)
                with open(target, "w") as fh:
                    fh.write("y")
            else:
                target = os.path.join(root, "missing_%d" % idx)  # never created
            name = "link_to_nondir_%d" % idx
            os.symlink(target, os.path.join(root, name))
        else:
            raise AssertionError("unknown code %r" % code)
        name_to_code[name] = code
    return name_to_code


def check_tree(codes):
    with tempfile.TemporaryDirectory() as root:
        name_to_code = build_tree(root, codes)
        for entry in os.scandir(root):
            code = name_to_code.get(entry.name)
            if code is None:
                # skip the symlink targets we created as scaffolding
                continue

            # A-reference: the deep model == the real follow-symlinks callee
            # (the classification the patched code uses).
            follow = entry.is_dir()                          # follow_symlinks=True
            expected = resolves_to_dir(code)
            assert follow == expected, (
                "resolves_to_dir deep model unsound on %r (code %d): "
                "is_dir() gave %r, deep model gives %r"
                % (entry.name, code, follow, expected))

            # Document the pre-patch no-follow callee: True only for a plain
            # directory (code 1); in particular FALSE for the link-to-directory
            # (code 2) -- the exact disagreement the fix removes.
            nofollow = entry.is_dir(follow_symlinks=False)
            assert nofollow == (code == 1), (
                "no-follow classification unexpected on %r (code %d): "
                "is_dir(follow_symlinks=False) gave %r, expected %r"
                % (entry.name, code, nofollow, code == 1))

            if code == 2:
                # The discriminating case: follow says directory, no-follow does
                # not -- so the pre-patch walk would skip this selected link.
                assert follow is True and nofollow is False, (
                    "link-to-directory must follow=True, nofollow=False")


def main():
    # boundary: one entry of each code, and each code alone
    check_tree([0, 1, 2, 3])
    check_tree([2])
    check_tree([1])
    check_tree([0])
    check_tree([3])
    check_tree([])  # empty directory

    # fuzz: many random mixes of the four codes
    rng = random.Random(7982)
    for _ in range(2000):
        n = rng.randint(0, 8)
        codes = [rng.choice([0, 1, 2, 3]) for _ in range(n)]
        check_tree(codes)

    print("G-AX OK: resolves_to_dir deep model (== os.DirEntry.is_dir(), "
          "follow_symlinks=True) sound on boundary + 2000 fuzz trees; "
          "no-follow callee confirmed to disagree exactly on link-to-directory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
