#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for matplotlib__matplotlib-24627.

The bundle models ONE routine: the child-clearing step inside the axes clear
operation (mapping.md). Standing up the full matplotlib Figure/Axes/Artist
machinery to drive the real clear is heavy and unnecessary — the modeled value
is a PURE transformation of the child list:

    new child list  := []
    former children := [ artist with .axes=None, .figure=None  for each child ]
                       (every other field preserved)

So the ORACLE below is a faithful in-process replica of the POST-PATCH behavior
(the gold edit empties the child list AND deparents each former child), and the
SHADOW is the op-for-op transliteration of `implementation_clearAxes`
(Solution.lean impl region), per refinement.md.

An artist is modeled as a dict {data, axes, figure} where `data` stands for all
state the clear must NOT touch, and `axes`/`figure` are owning identities
(`None` ⇒ deparented). This genuinely tests the soundness-critical behavior: a
former child's `.axes`/`.figure` must end up `None` while `data` is preserved.

stdlib-only. Pinned seed: 24627 (also in mapping.md).
"""
import random
import sys

SEED = 24627
N = 120_000


# --- ORACLE: faithful in-process replica of the POST-PATCH clear --------------
def oracle(children):
    new_children = []
    former = []
    for c in children:
        former.append({"data": c["data"], "axes": None, "figure": None})
    return new_children, former


# --- SHADOW of implementation_clearAxes (the R leg) ---------------------------
# Mirrors Solution.lean impl region exactly: new list empty; loop sets each
# former child's axes/figure to none, preserving data.
def shadow(children):
    old_children = children
    new_children = []
    former = []
    for chld in old_children:
        chld = {"data": chld["data"], "axes": None, "figure": None}
        former = former + [chld]
    return new_children, former


def disagree(children):
    got = oracle(children)
    want = shadow(children)
    if got != want:
        return (children, got, want)
    return None


def mk_artist(rng):
    return {
        "data": rng.randint(0, 1_000),
        "axes": rng.choice([None, rng.randint(0, 9)]),
        "figure": rng.choice([None, rng.randint(0, 9)]),
    }


def _edge_cases():
    return [
        [],                                              # empty axes
        [{"data": 7, "axes": 1, "figure": 2}],           # single parented child
        [{"data": 0, "axes": None, "figure": None}],     # already deparented
        [{"data": i, "axes": 1, "figure": 1} for i in range(5)],   # many children
        [{"data": 3, "axes": 1, "figure": None},
         {"data": 4, "axes": None, "figure": 2}],        # mixed parents
    ]


def main() -> int:
    checked = 0
    for children in _edge_cases():
        d = disagree(children)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.randint(0, 8)
        children = [mk_artist(rng) for _ in range(n)]
        d = disagree(children)
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
