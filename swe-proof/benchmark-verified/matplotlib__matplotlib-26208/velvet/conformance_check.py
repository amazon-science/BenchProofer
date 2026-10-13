#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26208 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs.

The modeled behaviour is the *carry-over of a shared axis's conversion setting*
to a newly-created companion view, at two independent sites:

  * Axes.twinx (inheritSharedConvA) — gold adds `ax2.xaxis.units = self.xaxis.units`
  * Axes.twiny (inheritSharedConvB) — gold adds `ax2.yaxis.units = self.yaxis.units`

Lean is functional and has no aliasing, so Solution.lean models the setting
DEEPLY as `ConvSetting = Option Int` and the carry-over as a plain value copy
(`out = source`).  The two observables the F2P test exercises are:

    (a) `units is not None`                      -> isPresent out
    (b) `ax2.<axis>.units is ax1.<axis>.units`   -> out = source  (object identity)

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo type. Both methods compute
              `out = source`; observing the companion's setting yields exactly
              the source's setting object (identity preserved) and is-present
              exactly when the source's is. There are NO A-tagged callees in the
              impl region, so the shadow is pure R/I (conf_skip = false).
  * ORACLE  — `patch.diff`'s behaviour: build a real Figure/Axes, plot a
              categorical (string) sequence along the shared coordinate so the
              source axis acquires a real units converter, create the companion
              with the REAL patched `twinx`/`twiny`, and read back whether the
              companion axis's `units` is present and whether it IS (object
              identity) the source axis's `units`. The real correctness oracle
              (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements. Runs in-container
(the prebuilt SWE-Bench instance image); imports only stdlib + matplotlib
(Agg backend, no display). The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 26208
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean inheritSharedConvA/B, transliterated -------
# `out = source`.  We represent a ConvSetting as None (absent) or an int tag
# (present, identity).  `observe` reports (is_present, identity_tag).
def shadow_inherit(source):
    """ConvSetting copy: out = source.  Returns (is_present, identity_tag)."""
    out = source                       # the deep value copy (out := source)
    is_present = out is not None       # isPresent out
    return (is_present, out)           # identity tag is the value itself


# --- the oracle: the REAL patched twinx / twiny -------------------------------
def _oracle_twin(twin, plot_source):
    """Construct a real Figure/Axes; optionally plot a categorical sequence
    along the shared coordinate so the source axis acquires a units converter;
    then create the companion with the REAL patched twin{x,y} and read back
    (companion_present, companion_is_source) for the shared axis."""
    import matplotlib
    matplotlib.use("Agg", force=True)
    from matplotlib.figure import Figure

    axis_name = f"{twin}axis"          # 'xaxis' for twinx, 'yaxis' for twiny
    twin_func = f"twin{twin}"          # 'twinx' / 'twiny'

    fig = Figure()
    ax1 = fig.subplots()
    if plot_source:
        # plotting strings along BOTH coords engages the category units
        # machinery; the shared-coordinate axis then carries a real converter
        # and a non-None .units (mirrors the F2P test's ax1.plot(a, b)).
        a = ["0", "1"]
        b = ["a", "b"]
        ax1.plot(a, b)
    src_units = getattr(ax1, axis_name).units

    ax2 = getattr(ax1, twin_func)()
    comp_units = getattr(ax2, axis_name).units

    companion_present = comp_units is not None
    companion_is_source = comp_units is src_units
    return (companion_present, companion_is_source, src_units is not None)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): the two source states that
    # matter — a present setting (plotted) and an absent one (not plotted) —
    # at each of the two sites.
    boundary = [
        ("x", True),     # the F2P reproduction for twinx (present source)
        ("y", True),     # the F2P reproduction for twiny (present source)
        ("x", False),    # absent source (no plot) at twinx
        ("y", False),    # absent source (no plot) at twiny
    ]
    for b in boundary:
        yield b
    for _ in range(n):
        yield (rng.choice(("x", "y")), rng.choice((True, False)))


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    # The oracle builds a real Figure (tens of ms); the input space has only 4
    # equivalence classes (twin in {x,y} x plot_source in {T,F}). Evaluate the
    # real patched twin{x,y} once per class and reuse, so we can still diff over
    # 10^5 fuzzed inputs without rebuilding 10^5 figures.
    oracle_cache = {}
    for (twin, plot_source) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        key = (twin, plot_source)
        if key not in oracle_cache:
            oracle_cache[key] = _oracle_twin(twin, plot_source)
        comp_present, comp_is_source, src_present = oracle_cache[key]

        # Build the modeled `source` ConvSetting matching the oracle's source
        # state: present -> a non-None tag, absent -> None.  (The exact tag value
        # is irrelevant; identity is what both sides compare.)
        source = object() if src_present else None
        sh_present, sh_value = shadow_inherit(source)

        # (a) presence agrees:  isPresent out  ==  companion units is not None
        if sh_present != comp_present:
            disagreements.append((f"twin{twin}", plot_source, "presence",
                                  sh_present, comp_present))
        # (b) identity agrees:  out = source (shadow always True)  ==
        #     companion units IS source units (real object identity)
        shadow_is_source = (sh_value is source)   # always True for out = source
        if shadow_is_source != comp_is_source:
            disagreements.append((f"twin{twin}", plot_source, "identity",
                                  shadow_is_source, comp_is_source))
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for site, ps, kind, sh, orc in disagreements:
            print("  site=%s plot_source=%r aspect=%s shadow=%r oracle=%r"
                  % (site, ps, kind, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of inheritSharedConvA/inheritSharedConvB agrees "
          "with patch.diff behaviour (companion inherits the shared axis's "
          "conversion setting, same object, at both twinx and twiny) on %d "
          "inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
