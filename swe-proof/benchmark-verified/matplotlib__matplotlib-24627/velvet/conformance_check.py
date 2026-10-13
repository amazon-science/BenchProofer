#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24627 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs.

The modeled behaviour is the *deparenting on clear* semantics of the per-axes
clear routine (`_AxesBase.__clear`, reached by `Axes.clear()`/`Axes.cla()`):

    pre-patch : clearing empties the axes' child collection but leaves each
                former child's `.axes` / `.figure` still pointing at the axes.
    post-patch: clearing additionally unsets BOTH links on every former child.

Lean is functional and has no aliasing / in-place attribute mutation, so
Solution.lean models the observable contract DEEPLY: an `Artist` is viewed
through `hasAxes` / `hasFigure`, and clearing returns

    deparentAll children   = every former child with hasAxes = hasFigure = false

i.e. for every artist that was attached, after the clear `.axes is None` and
`.figure is None`.

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type. `clearAxes` returns, for each
              former child, the deparented link state (axes unset, figure
              unset). There are NO A-tagged callees in the impl region, so the
              shadow is pure R/I (conf_skip = false).
  * ORACLE  — `patch.diff`'s behaviour: build a REAL axes via plt.subplots(),
              attach a fuzzed number/mix of real artists, record them, call
              ax.clear(), then read each recorded artist's `.axes` / `.figure`.
              The real correctness oracle (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements. Runs in-container
(the prebuilt SWE-Bench instance image), stdlib + matplotlib (the repo under
test). The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 24627
N_FUZZ = 2_000  # each iteration builds a real Figure; this dominates wall-time


# --- the R/I shadow: Solution.lean clearAxes / deparentAll, transliterated ----
# `deparent a = (hasAxes := false, hasFigure := false)` for every former child.
# The shadow returns, for each attached artist, its post-clear link state: both
# unset. It is independent of the artists' kinds (the model sees only the link
# bits), so it returns a list of `(False, False)` of the same length.
def shadow_clear(n_children):
    """clearAxes over `n_children` attached artists -> the deparented link state
    of each, in order. deparent sets both hasAxes and hasFigure to False."""
    return [(False, False) for _ in range(n_children)]


# --- the oracle: the REAL patched clear routine ------------------------------
def oracle_clear(artist_kinds):
    """Attach the requested artists to a real Axes, record them, call clear(),
    then read back each former child's (.axes is not None, .figure is not None).
    Returns the list of post-clear link-state pairs, in attachment order."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    recorded = []
    try:
        for kind in artist_kinds:
            if kind == "line":
                (ln,) = ax.plot([1, 2, 3])
                recorded.append(ln)
            elif kind == "line_empty":
                (ln,) = ax.plot([], [])
                recorded.append(ln)
            elif kind == "image":
                im = ax.imshow([[1, 2], [3, 4]])
                recorded.append(im)
            elif kind == "text":
                txt = ax.text(0.5, 0.5, "x")
                recorded.append(txt)
            elif kind == "scatter":
                sc = ax.scatter([0, 1], [0, 1])
                recorded.append(sc)
            else:
                raise AssertionError("unknown artist kind %r" % (kind,))
        # sanity: every recorded artist is attached before the clear
        for art in recorded:
            assert art.axes is ax, "precondition: artist not attached to axes"
            assert art.figure is fig, "precondition: artist not attached to figure"
        ax.clear()
        return [(art.axes is not None, art.figure is not None)
                for art in recorded]
    finally:
        plt.close(fig)


KINDS = ["line", "line_empty", "image", "text", "scatter"]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    boundary = [
        [],                                  # clear with no children
        ["line"],                            # the problem_statement reproduction
        ["image"],
        ["line", "image"],                   # the F2P test's mix
        ["line", "line", "line", "line", "image"],  # F2P: 4 lines + 1 image
        ["text"],
        ["scatter"],
        ["line", "image", "text", "scatter", "line_empty"],
    ]
    for b in boundary:
        yield b
    for _ in range(n):
        k = rng.randint(0, 6)
        yield [rng.choice(KINDS) for _ in range(k)]


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for kinds in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_clear(len(kinds))
        oracle = oracle_clear(kinds)
        if shadow != oracle:
            disagreements.append((kinds, shadow, oracle))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for kinds, sh, orc in disagreements:
            print("  kinds=%r shadow=%r oracle=%r" % (kinds, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of clearAxes agrees with patch.diff behaviour "
          "(every former child deparented: .axes and .figure both unset) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
