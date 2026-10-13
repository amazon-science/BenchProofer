#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-10466.

There is NO consumed `@ContractOnly` axiom in this bundle: the deduplicate-and-
sort behaviour is the operation under specification and is modelled DEEPLY by
the pure `dedup_sort` (with `ins`) over `PSeq[int]` in model.py. G-AX therefore
validates that deep model against the REAL operation the gold patch performs:

  (A-reference) the deep model `dedup_sort` (model.py pure region) computes
      exactly the real `sorted(set(...))` that the patched `__iter__` applies to
      the projected `(source, line)` positions.

Two things are checked, both stdlib-only (`random`):

  1. `dedup_sort(xs) == sorted(set(xs))` for integer key lists `xs`
     (boundary + randomized fuzz). This is the deep-model == real-callee check.

  2. The integer-key abstraction is faithful: a `(source, line)` position is
     modelled by a single integer key under an ORDER- and EQUALITY-preserving
     identification (mapping.md). For any finite set of positions there is a
     strictly monotone injection positions -> ints, and under any such injection
     `sorted(set(positions))` maps element-for-element to `sorted(set(keys))`.
     We confirm this on randomized `(source, line)` position lists drawn from a
     small alphabet of source identities and line numbers (so collisions and
     duplicates are common), reproducing the F2P scenario exactly.

Exit 0 iff every obligation holds.
"""
import random
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def ins(x, s):
    """Reference implementation of model.py's pure `ins` (front-recursive)."""
    if len(s) == 0:
        return [x]
    if x < s[0]:
        return [x] + s
    if x == s[0]:
        return s
    return [s[0]] + ins(x, s[1:])


def dedup_sort(s):
    """Reference implementation of model.py's pure `dedup_sort`."""
    if len(s) == 0:
        return []
    return ins(s[-1], dedup_sort(s[:-1]))


# --- check 1: deep model == real sorted(set(...)) over integer keys ----------

def check_dedup_sort(xs):
    observed = dedup_sort(list(xs))          # deep model
    expected = sorted(set(xs))               # the real operation
    assert observed == expected, (
        "dedup_sort deep model unsound on %r: model gives %r, "
        "sorted(set(...)) gives %r" % (xs, observed, expected))


# --- check 2: integer-key abstraction faithful for (source, line) pairs ------

def check_position_abstraction(positions):
    """The real patched code computes sorted(set(positions)) over (source, line)
    tuples. Encode each distinct tuple by a strictly monotone integer key and
    confirm the ordered set of keys maps back, element-for-element, to the
    ordered set of tuples -- i.e. modelling positions as integer keys loses
    nothing of the dedup/sort behaviour."""
    real = sorted(set(positions))                       # over the real tuples
    # strictly monotone injection tuple -> int: index in the globally sorted,
    # deduplicated universe of tuples (order- and equality-preserving).
    universe = sorted(set(positions))
    key_of = {t: k for k, t in enumerate(universe)}
    keys = [key_of[t] for t in positions]               # model carrier
    model_keys = dedup_sort(keys)                        # ordered set of keys
    # decode back and compare to the real ordered set of tuples.
    inv = {k: t for t, k in key_of.items()}
    decoded = [inv[k] for k in model_keys]
    assert decoded == real, (
        "integer-key abstraction unsound on %r: decoded %r != real %r"
        % (positions, decoded, real))


def main():
    rng = random.Random(10466)

    # --- check 1: integer-key boundary cases --------------------------------
    boundary = [
        [],
        [0],
        [5, 5, 5],                       # all duplicates -> single element
        [3, 2, 1],                       # reversed -> sorted
        [1, 2, 3],                       # already sorted, distinct
        [2, 1, 2, 3, 1],                 # duplicates + unsorted
        [-1, -1, 0, 7, 7, 7, 2],
        [10, 9, 8, 8, 9, 10],
    ]
    for xs in boundary:
        check_dedup_sort(xs)

    # --- check 1: randomized integer fuzz -----------------------------------
    for _ in range(20000):
        n = rng.randint(0, 16)
        # small value range so duplicates are frequent.
        xs = [rng.randint(0, 8) for _ in range(n)]
        check_dedup_sort(xs)

    # --- check 2: (source, line) position abstraction, F2P-shaped -----------
    # the exact F2P scenario: same (source, line) recorded several times, in
    # scan order, across a few sources and line numbers.
    f2p = [('/path/to/filename', 1),
           ('/path/to/filename', 1),
           ('/path/to/filename', 2),
           ('/path/to/yetanother', 1)]
    check_position_abstraction(f2p)
    assert sorted(set(f2p)) == [('/path/to/filename', 1),
                                ('/path/to/filename', 2),
                                ('/path/to/yetanother', 1)], "F2P expectation drift"

    sources = ['/a.rst', '/b.rst', '/c.rst', '../../m/hair.rst', '../../m/metas.rst']
    lines = [0, 1, 2, 38, 92, 96, 121, 125]
    for _ in range(20000):
        n = rng.randint(0, 20)
        positions = [(rng.choice(sources), rng.choice(lines)) for _ in range(n)]
        check_position_abstraction(positions)

    print("G-AX OK: dedup_sort deep model == sorted(set(...)) over %d boundary "
          "+ 20000 integer fuzz inputs; integer-key abstraction faithful for "
          "(source, line) positions over 1 F2P + 20000 fuzz position lists"
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
