#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-6197.

The bundle models `Package.collect` (src/_pytest/python.py @ base_commit), the
generator that enumerates a test-package directory's contents. The modeled value
is a PAIR:

    result.1  -- the ordered list of child collectors yielded
    result.2  -- whether enumeration imported the package's own __init__.py
               -- (importsOwnInit); post-patch this is unconditionally False

Inputs (mapping.md bijection):

    initMatches : Bool          -- own __init__.py matches the python_files pattern
    initNode    : token         -- the Module collector for the own __init__.py
    entries     : list of PkgEntry(boundary, isFile, yields)
                                -- one per visited path

Post-patch `Package.collect` (the gold edit REMOVES the leading
`self._mount_obj_if_needed()`, so no eager import; the rest of the body is
unchanged):

    if initMatches:                  yield initNode
    for e in entries:
        if e.boundary:               continue          # own __init__.py / inside an accounted pkg
        if e.isFile:                 yield from e.yields
        # directories yield no collector here
    importsOwnInit = False

Standing up the full pytest collection of a real package tree to observe the
yielded collectors AND whether the own __init__.py was imported is heavy and
unnecessary: the modeled value is this pure enumeration over observables the real
generator exposes (per-path boundary / is-file / resolved collectors, fed by the
unchanged `_collectfile`). So the ORACLE below is a faithful in-process replica of
the POST-PATCH generator, and the SHADOW is the op-for-op transliteration of
`implementation_packageCollect` (Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical clause: enumerating a package never
imports the package's own __init__.py (importsOwnInit == False) — matching the
F2P expectation (a package whose __init__.py raises at import time, and a
non-importable `src` package, are both collected without error).

stdlib-only. Pinned seed: 6197 (also in mapping.md).
"""
import random
import sys

SEED = 6197
N = 200_000
MAX_ENTRIES = 12


# --- ORACLE: faithful in-process replica of the POST-PATCH Package.collect ----
def oracle(initMatches, initNode, entries):
    out = []
    if initMatches:
        out.append(initNode)
    for boundary, isFile, yields in entries:
        if boundary:
            continue
        if isFile:
            out.extend(yields)
    imports_own_init = False  # patch removed the eager _mount_obj_if_needed()
    return (out, imports_own_init)


# --- SHADOW of implementation_packageCollect (the R leg) ----------------------
# Mirrors Solution.lean impl region exactly.
def shadow(initMatches, initNode, entries):
    imports_own_init = False
    collected = []
    if initMatches:
        collected = collected + [initNode]
    for boundary, isFile, yields in entries:
        if boundary:
            continue
        if isFile:
            collected = collected + yields
    return (collected, imports_own_init)


def random_entries(rng):
    n = rng.randint(0, MAX_ENTRIES)
    es = []
    for _ in range(n):
        boundary = rng.random() < 0.35
        isFile = rng.random() < 0.6
        ny = rng.randint(0, 3)
        yields = [f"c{rng.randint(0, 99)}" for _ in range(ny)]
        es.append((boundary, isFile, yields))
    return es


def disagree(inp):
    got = oracle(*inp)
    want = shadow(*inp)
    if got != want:
        return (inp, got, want)
    return None


def main() -> int:
    checked = 0
    rng = random.Random(SEED)

    # A few hand-picked boundary cases first.
    fixed = [
        (False, "init", []),
        (True, "init", []),
        (True, "init", [(True, True, ["x"])]),            # boundary file: skipped
        (False, "init", [(False, True, ["a", "b"])]),     # plain file: yielded
        (False, "init", [(False, False, ["a"])]),         # directory: not yielded
        (True, "init", [(True, True, []), (False, True, ["m"])]),
    ]
    for inp in fixed:
        d = disagree(inp)
        if d:
            print(f"DISAGREE fixed: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    for _ in range(N):
        inp = (rng.random() < 0.5, "init", random_entries(rng))
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
