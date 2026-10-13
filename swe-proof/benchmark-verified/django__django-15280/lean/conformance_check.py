#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_assignParents
against the patch.diff behaviour (post-patch reverse-relation assignment loop).

The patched Python loop is:

    for rel_obj in queryset:
        if not self.field.is_cached(rel_obj):
            instance = instances_dict[rel_obj_attr(rel_obj)]
            setattr(rel_obj, self.field.name, instance)

i.e. iterate the batch in order, and for each child that does NOT already have a
parent cached, assign the default parent looked up by the child's key; children
that already have a parent are left untouched. Modeled type bijection (mapping.md):
a child <-> {key:int, parent:Optional[int]}; `is_cached` <-> parent is not None;
`instances_dict[rel_obj_attr(rel_obj)]` <-> lookup(key).

The impl region is NOT all-A-tagged (it is pure I/R structure), so this runs a
real fuzz: the R/I shadow is diffed against an independent reconstruction of the
patched loop over >=10^5 fuzzed batches. exit 0 iff zero disagreements.

stdlib-only.
"""
import random
import sys

SEED = 15280          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(lookup, children):
    """R/I shadow of implementation_assignParents.

    acc := []; for c in children:
        if c.parent is None: acc += [{key, some(lookup(key))}]
        else:                acc += [c]
    return acc.
    """
    acc = []
    for c in children:
        key, parent = c
        if parent is None:
            acc.append((key, lookup(key)))
        else:
            acc.append((key, parent))
    return acc


def patched_loop(lookup, children):
    """Independent reconstruction of the post-patch django loop:
    skip already-cached children, otherwise assign the looked-up parent."""
    out = []
    for c in children:
        key, parent = c
        rel = list(c)
        if parent is None:                # not is_cached(rel_obj)
            rel = [key, lookup(key)]
        out.append((rel[0], rel[1]))
    return out


def rand_child(rng):
    key = rng.randint(-5, 5)             # small key space -> collisions in table
    # ~40% already have a parent cached (the bug-discriminating case)
    if rng.random() < 0.4:
        parent = rng.randint(-1000, 1000)
    else:
        parent = None
    return (key, parent)


def rand_lookup(rng):
    table = {k: rng.randint(-1000, 1000) for k in range(-5, 6)}
    return lambda k: table[k]


def main() -> int:
    rng = random.Random(SEED)
    disagreements = 0
    examples = []

    # Deterministic boundary cases first.
    L0 = lambda k: 100 + k
    fixed = [
        (L0, []),
        (L0, [(1, None)]),
        (L0, [(1, 7)]),                          # already cached -> kept
        (L0, [(1, None), (1, 7), (2, None)]),    # mixed
        (L0, [(3, -3), (3, None)]),              # same key, one cached one not
    ]

    cases = list(fixed)
    for _ in range(N):
        lookup = rand_lookup(rng)
        n = rng.randint(0, 12)
        children = [rand_child(rng) for _ in range(n)]
        cases.append((lookup, children))

    for lookup, children in cases:
        got = shadow(lookup, children)
        want = patched_loop(lookup, children)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((children, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for ch, g, w in examples:
            print(f"  in={ch!r} shadow={g!r} patched={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
