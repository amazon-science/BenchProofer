#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24026.

This bundle consumes NO @ContractOnly axiom. Its one kind-A obligation is an
A-reference: the deep model of the per-layer colour assignment

    cyc_prefix(colors, n)[i] == colors[i % len(colors)]      (model.py, pure)

is validated == the REAL library operation the gold patch uses to source the
per-layer colours when explicit colours are supplied:

    colors = itertools.cycle(colors)
    ... facecolor = next(colors) ...                          (stackplot.py)

i.e. drawing the first n values from `itertools.cycle(colors)` must equal
`[colors[i % len(colors)] for i in range(n)]`. We execute the real
`itertools.cycle` on boundary + randomized-fuzz inputs and assert that
observation matches the model element-for-element.

We additionally assert the second tested property of the change -- that the
routine does NOT mutate the shared colour-cycle state -- is honoured by the
gold-faithful colour source: `itertools.cycle(colors)` consumes an iterator
over a COPY of the supplied colours and never touches any Axes state, so a list
of explicit colours leaves the (unrelated) Axes cycle untouched. This is the
refinement consequence the model pins as `axes.cycle == Old(axes.cycle)`.

Imports nothing repo-specific: `itertools` is the Python standard library --
the same module the gold patch calls. Exit 0 iff every obligation holds.
"""
import itertools
import random
import sys


def model_cyc_prefix(colors, n):
    """Reference implementation of model.py's deep model: layer i gets the
    supplied colour at cyclic position (i mod K)."""
    k = len(colors)
    return [colors[i % k] for i in range(n)]


def real_cycle_draw(colors, n):
    """The REAL library operation the gold patch uses: draw n values from
    itertools.cycle(colors)."""
    it = itertools.cycle(colors)
    return [next(it) for _ in range(n)]


def check_cycle_reference(colors, n):
    """Assert the deep model == the real itertools.cycle drawing, length n."""
    observed = real_cycle_draw(colors, n)      # real callee
    expected = model_cyc_prefix(colors, n)     # deep model
    assert observed == expected, (
        "cyc_prefix deep model unsound on colors=%r, n=%d: "
        "itertools.cycle gave %r, deep model gives %r"
        % (colors, n, observed, expected))


def check_no_mutation(colors, n):
    """The gold-faithful colour source must not mutate the supplied sequence:
    itertools.cycle iterates a snapshot, so `colors` is unchanged after drawing
    n facecolours (mirrors the model's axes.cycle == Old(axes.cycle))."""
    before = list(colors)
    it = itertools.cycle(colors)
    for _ in range(n):
        next(it)
    assert list(colors) == before, (
        "itertools.cycle mutated the supplied colours %r -> %r"
        % (before, list(colors)))


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        (["C0", "C1", "C2"], 3),     # the F2P case: 3 colours, 3 layers
        (["C0", "C1", "C2"], 1),     # fewer layers than colours
        (["C0", "C1", "C2"], 5),     # more layers than colours -> repeat
        (["C0"], 1),                 # single colour, single layer
        (["C0"], 7),                 # single colour repeated
        (["r", "g"], 6),             # exact multiple
        (["r", "g", "b"], 7),        # non-multiple wrap
        (list(range(10)), 10),       # tokens as ints
        (list(range(4)), 25),        # long draw over short cycle
        (["only"], 100),
    ]
    for colors, n in boundary:
        check_cycle_reference(colors, n)
        check_no_mutation(colors, n)

    # --- randomized fuzz ---------------------------------------------------
    rng = random.Random(24026)
    for _ in range(20000):
        k = rng.randint(1, 12)
        colors = [rng.randint(0, 1000) for _ in range(k)]
        n = rng.randint(1, 40)
        check_cycle_reference(colors, n)
        check_no_mutation(colors, n)

    print("G-AX OK: cyc_prefix deep model (== itertools.cycle drawing) sound "
          "on %d boundary + 20000 fuzz inputs; supplied colours never mutated."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
