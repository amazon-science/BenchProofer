#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26291 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region, transliterated
              to Python over the real repo types via the mapping.md bijection
              (`Option Ctx` <-> `RendererBase | None`, `Region` compared by
              Bbox extents). The impl computes
                chosen = ctx if ctx is not None else hostContext(host)
                out    = placeWith(chosen, host)
              - the substitution `chosen` is the R/I leg (the impl match's
                `none -> hostContext host` fallback), transliterated explicitly.
              - `hostContext` / `placeWith` are the A-tagged UNCHANGED callees;
                per §4.1 they are NOT replaced by their (opaque) axiom models —
                the shadow runs the REAL callees `ax.figure._get_renderer()` and
                the unchanged downstream pipeline (invoked here by handing a
                CONCRETE renderer to the same patched `__call__`, whose body is
                that pipeline).
  * ORACLE  — `patch.diff`'s behaviour: the patched `__call__` applied to the
              raw (possibly-None) context — the real correctness oracle
              (G-RESOLVE). Its in-function `if renderer is None:` guard is the
              substitution under test.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the patched SWE-Bench instance image), stdlib + matplotlib
only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

SEED = 26291
N_FUZZ = 100_000


def _bounds(bbox):
    """Observable region extent (mapping.md §2: region equality == extent)."""
    return (round(bbox.x0, 6), round(bbox.y0, 6),
            round(bbox.x1, 6), round(bbox.y1, 6))


def shadow(locator, host, ctx):
    """computePlacement transliterated. The A-tagged callees hostContext /
    placeWith are the REAL repo callees: hostContext = host.figure._get_renderer();
    placeWith(c, host) = the unchanged downstream pipeline run with a CONCRETE
    context c (here invoked as locator(host, c) with c never None)."""
    # context substitution: explicit R/I leg (some c -> c | none -> hostContext host)
    if ctx is None:
        chosen = host.figure._get_renderer()      # hostContext host (REAL callee)
    else:
        chosen = ctx
    # placeWith chosen host (REAL unchanged downstream, concrete context)
    return _bounds(locator(host, chosen))


def oracle(locator, host, ctx):
    """patch.diff behaviour: the patched __call__ on the raw context. Its own
    `if renderer is None: renderer = ax.figure._get_renderer()` guard is the
    substitution we are differentially testing."""
    return _bounds(locator(host, ctx))


def main():
    rng = random.Random(SEED)

    fig, ax = plt.subplots()
    inset = inset_axes(ax, width=1.3, height=0.9)
    locator = inset.get_axes_locator()
    host = inset
    fig.canvas.draw()
    real_renderer = fig._get_renderer()

    # The observable input surface is present-vs-absent context (mapping.md §2):
    # a concrete renderer (`some r`) or None (`none`). Fuzz over both, weighted
    # to exercise the discriminating absent branch heavily.
    disagreements = 0
    n_none = 0
    n_some = 0
    for _ in range(N_FUZZ):
        if rng.random() < 0.5:
            ctx = None
            n_none += 1
        else:
            ctx = real_renderer
            n_some += 1
        s = shadow(locator, host, ctx)
        o = oracle(locator, host, ctx)
        if s != o:
            disagreements += 1
            if disagreements <= 5:
                print("DISAGREE ctx=%s shadow=%r oracle=%r"
                      % ("none" if ctx is None else "some", s, o),
                      file=sys.stderr)

    plt.close(fig)

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements (seed=%d)"
              % (disagreements, N_FUZZ, SEED), file=sys.stderr)
        return 1

    print("G-CONF OK: R/I shadow of computePlacement (context substitution) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d; %d absent / "
          "%d present context), 0 disagreements."
          % (N_FUZZ, SEED, n_none, n_some))
    return 0


if __name__ == "__main__":
    sys.exit(main())
