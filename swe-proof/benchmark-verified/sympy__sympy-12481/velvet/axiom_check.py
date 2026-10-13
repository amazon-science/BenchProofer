#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-12481.

The bundle consumes NO axioms. Its one kind-A construct is the A-reference deep
model `arrayForm` (Solution.lean pure region), which spells out the UNCHANGED
cycle-composition block of the constructor:

    c = Cycle(); for ci in args: c = c(*ci); aform = c.list()   (permutations.py:914-920)

G-AX validates that deep model against the REAL routine: for every well-formed
grouped input (some point named, and no group naming a point twice — mapping.md
§3),

    arrayForm(cycles) == (lambda: (c := Cycle(),
                          [c := c(*ci) for ci in cycles], c[-1].list())[-1])()

i.e. the UNCHANGED composition block run DIRECTLY:

    c = Cycle(); for ci in cycles: c = c(*ci); aform = c.list()   (:911-917)

CRITICAL (directive 7): the A-reference is an *unchanged* callee, so it must be
checked against that callee DIRECTLY — NOT by calling `Permutation([...])`, which
routes through `Permutation.__new__`, the FUNCTION UNDER CHANGE. G-AX runs against
the BASE (pre-patch) repo, where `__new__`'s duplicate guard raises ValueError on
exactly the non-disjoint inputs this patch makes legal; invoking it would conflate
the change with the unchanged composition (and falsely fail). The `Cycle()`
composition block is untouched by the patch, so the model's claim is observed on
both base and patched repos identically.

A group that repeats a point internally is NOT asserted: it raises earlier in
the unchanged Cycle.__init__ and lies outside the modeled frame (so the model
does not over-claim — directive 7). An argument naming NO point at all is also
outside the frame (`Cycle().list()` raises `must give size for empty Cycle`),
but a single EMPTY group beside a non-empty one is INSIDE it — the real
composition treats it as the identity factor — so those inputs are asserted here
as well, matching the frame `eachValid` states.

The OTHER reading of the argument (a flat list handed back as the explicit form
it already is) consumes no callee at all: the model returns `entries.flatten`,
which the refinement map tags I against `aform = list(args)`. So it has nothing
for G-AX to validate and nothing here mentions it.

Imports only sympy (the repo under test) + stdlib. Exit 0 iff every observation
meets the deep model.
"""
import random
import sys


# --- the deep model: Solution.lean arrayForm/composePoint, transliterated ----

def succ_in_cycle(first, cyc, x):
    if not cyc:
        return x
    if len(cyc) == 1:
        return first if x == cyc[0] else x
    a, b = cyc[0], cyc[1]
    if x == a:
        return b
    return succ_in_cycle(first, cyc[1:], x)


def cycle_step(cyc, x):
    if not cyc:
        return x
    return succ_in_cycle(cyc[0], cyc, x)


def compose_point(cycles, x):
    for c in cycles:
        x = cycle_step(c, x)
    return x


def array_form_model(cycles):
    n = (max((v for c in cycles for v in c), default=0)) + 1
    return [compose_point(cycles, i) for i in range(n)]


# --- the check ---------------------------------------------------------------

def real_composition(cycles):
    """The UNCHANGED composition block, run directly (permutations.py:911-917):
        c = Cycle(); for ci in args: c = c(*ci); aform = c.list()
    This is the real callee the A-reference `arrayForm` models. It is NOT
    `Permutation([...])` — that would route through `Permutation.__new__`, the
    function the patch changes (whose pre-patch guard rejects non-disjoint
    cycles on the very inputs at issue). See module docstring / directive 7."""
    from sympy.combinatorics.permutations import Cycle
    c = Cycle()
    for ci in cycles:
        c = c(*ci)
    return list(c.list())


def check_reference(cycles):
    real = real_composition(cycles)                                  # real callee
    model = array_form_model(cycles)                                 # deep model
    assert real == model, (
        "arrayForm deep model unsound on %r: real composition gave %r, "
        "deep model gives %r" % (cycles, real, model))


def random_group(rng):
    # k may be 0: an empty group is inside the modeled frame (the identity
    # factor) as long as the whole argument still names some point.
    k = rng.randint(0, 6)
    pool = list(range(0, 10))
    rng.shuffle(pool)
    return pool[:k]


def main():
    # boundary cases: disjoint, non-disjoint, singletons, nested overlaps, F2P
    boundary = [
        [[0, 1], [0, 2]],            # the F2P witness == Permutation(0,1,2)
        [[0, 1], [0, 1]],            # non-disjoint -> identity
        [[1, 2], [2, 3]],
        [[1], [4, 2]],
        [[5]],
        [[0, 1, 2], [3, 4]],
        [[0, 1], [2, 3], [0, 2]],
        [[1], [1, 2]],
        [[2, 3], [3, 2]],
        [[0, 1], [1, 2], [2, 0]],
        [[3, 1, 4], [1, 5], [9, 2, 6]],
        [[0]],
        [[0, 2], [1, 3], [0, 1], [2, 3]],
        [[0, 1], []],                # an empty group beside a non-empty one
        [[], [0, 1]],                # ... in either position
        [[], [3, 1, 4], []],
        [[4, 5]],                    # points that skip 0..3 (grouped: fine)
    ]
    for cycles in boundary:
        check_reference(cycles)

    rng = random.Random(12481)
    checked = 0
    while checked < 20000:
        g = rng.randint(1, 5)
        cycles = [random_group(rng) for _ in range(g)]
        if not any(cycles):          # names no point -> outside the frame
            continue
        checked += 1
        check_reference(cycles)

    print("G-AX OK: arrayForm deep model (== real cycle-composition array form) "
          "sound on %d boundary + 20000 fuzz grouped inputs." % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
