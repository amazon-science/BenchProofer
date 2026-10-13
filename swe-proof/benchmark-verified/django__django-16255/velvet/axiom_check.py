#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16255 (A-reference).

This bundle consumes NO axiom: the reported value is the greatest of the
collected per-entry stamps with an absent-marker fallback for the empty
collection, modeled DEEPLY over `List Int` by `latestStamp` in Solution.lean
(a running maximum seeded with the absent marker `none`).

The one operation that genuinely changed is the reduction itself — taking the
maximum of the collected stamps WITH an absent-marker default for the empty
collection (the real code's `max(values, default=None)`). G-AX validates that
deep model against the REAL Python builtin it stands for (the A-reference):

    latestStamp(values)  ==  max(values, default=None)

on boundary cases (empty, singletons, negatives, duplicates, sorted/reversed)
plus randomized fuzzing. Critically it exercises the EMPTY collection, where
the post-patch builtin returns `None` (the absent marker) rather than raising
`ValueError` — exactly the behavior the model's empty-section clause pins.

Imports nothing repo-specific: `max` is a Python builtin. stdlib only. Exit 0
iff every observation matches the deep model. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys


def latest_stamp(stamps):
    """Reference of Solution.lean's deep model `latestStamp`: the greatest
    collected stamp, or the absent marker (None) when empty. This is the
    running maximum seeded with `none`, transliterated from the Lean impl
    region under the mapping.md bijection (`Option Int` <-> Optional[int])."""
    result = None
    for v in stamps:
        if result is None or v > result:
            result = v
    return result


def check(values):
    """Assert the deep model == the REAL builtin reduction on `values`."""
    observed = max(values, default=None)          # real builtin (post-patch)
    expected = latest_stamp(values)               # deep model (Solution.lean)
    assert observed == expected, (
        "latestStamp deep model unsound on %r: max(...,default=None) gave %r, "
        "deep model gives %r" % (values, observed, expected))
    # The empty-section guarantee: the real builtin yields the absent marker and
    # does NOT raise (the pre-patch max([]) raised ValueError).
    if not values:
        assert observed is None, (
            "empty collection must report the absent marker, got %r" % (observed,))


def main():
    boundary = [
        [],                       # the empty section: must be None, must not raise
        [0],
        [5],
        [-1],
        [0, 0],
        [1, 2, 3],
        [3, 2, 1],
        [2, 2, 2],
        [-5, -3, -10],
        [10, -10, 0],
        [-1, -1, -2],
        [1000000000, 999999999],
        list(range(50)),
        list(range(50, 0, -1)),
    ]
    for v in boundary:
        check(v)

    rng = random.Random(16255)
    for _ in range(50000):
        n = rng.randint(0, 16)            # n == 0 fuzzes the empty section
        v = [rng.randint(-1000, 1000) for _ in range(n)]
        check(v)

    print("G-AX OK: latestStamp deep model (== max(values, default=None)) "
          "sound on %d boundary + 50000 fuzz inputs (incl. the empty section, "
          "which reports the absent marker and does not raise)" % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
