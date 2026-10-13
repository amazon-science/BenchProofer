#!/usr/bin/env python3
"""G-CONF differential conformance for mwaskom__seaborn-3069 (plan §4.1).

Band: pure-data / decision (per-axis figure finalization).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable per-axis
finalization decision (the view limits set and whether the grid stays visible):

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`decidedLimits` / `decidedGrid`, the `finalizeAxis` do block)
              transliterated to Python over the real repo types via the
              mapping.md bijection.
  * ORACLE  — `patch.diff`'s behaviour: the per-axis decision of the gold-patched
              `Plotter._finalize_figure`, transliterated VERBATIM from the gold
              hunk (seaborn/_core/plot.py:1628 post-patch).

ORACLE CHOICE — why we transliterate the patched source decision instead of
running `Plot(...).plot()`:
  The patched decision lives inside `Plotter._finalize_figure`, which requires a
  live Figure/Axes, a configured matplotlib backend, resolved scales, and the
  full plot pipeline; the values it computes (`-.5, nticks-.5`, the y-swap, the
  `grid(False)` call) are installed as side effects on the axis via
  `set_{x,y}lim(...)` / `axis_obj.grid(...)`. The behaviour under test is the
  PURE per-axis decision: given (is-categorical, has-user-limit, is-y, ntick
  count, the resolved user/default limits, the style grid), what limits get set
  and is the grid shown. So, per the worker prompt, the ORACLE is the patched
  source decision transliterated verbatim:

      # gold seaborn/_core/plot.py, Plotter._finalize_figure, per (ax, axis):
      lo, hi = autoLo, autoHi
      if axis_key in p._limits:                 # user-pinned limits
          lo, hi = userLo, userHi
      grid = gridWasOn
      if isinstance(self._scales.get(axis_key), Nominal):
          grid = False                          # axis_obj.grid(False, which="both")
          if axis_key not in p._limits:
              nticks_ = nticks
              lo, hi = -.5, nticks_ - .5
              if axis == "y":
                  lo, hi = hi, lo               # set_{y}lim(hi, lo) -> inverted
      # installed: get_{x,y}lim() == (lo, hi); gridlines visible == grid

  The half-integer limits (-.5, nticks-.5) are exact dyadic floats; the model's
  Rat (-1/2, nticks-1/2) equals them bit-for-bit, so observable-equality is EXACT
  (no ULP tolerance). User/default limits are transported verbatim; the decision
  never arithmetically combines them.

There are no axiomatized callees: `len(axis_obj.get_major_ticks())` and the
default-margin limits are read-only environment observations (modeled as inputs),
and `axis_obj.grid` / `set_{x,y}lim` are effects that install the decided state.
Hence there is no axiom_check.py for this bundle (G-AX = skip).

Runs stdlib-only; the fuzz seed is pinned (mapping.md §4) for a deterministic
verdict.
"""
import random
import sys
from fractions import Fraction

SEED = 3069
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean decidedLimits / decidedGrid ---------------
def shadow_decision(is_cat, has_user, is_y, nticks, user_lo, user_hi,
                    auto_lo, auto_hi, grid_was_on):
    """decidedGrid / decidedLimits transliterated to Python (exact arithmetic
    via Fraction, mirroring the model's Rat). Returns (lo, hi, grid_visible)."""
    # decidedGrid isCategorical gridWasOn
    grid = False if is_cat else grid_was_on
    # decidedLimits isCategorical hasUserLimit isY nticks userLo userHi autoLo autoHi
    if has_user:
        lo, hi = user_lo, user_hi
    else:
        if is_cat:
            edge = Fraction(nticks) - Fraction(1, 2)
            if is_y:
                lo, hi = edge, Fraction(-1, 2)
            else:
                lo, hi = Fraction(-1, 2), edge
        else:
            lo, hi = auto_lo, auto_hi
    return (Fraction(lo), Fraction(hi), grid)


# --- the oracle: gold-patched _finalize_figure per-axis decision -------------
def oracle_decision(is_cat, has_user, is_y, nticks, user_lo, user_hi,
                    auto_lo, auto_hi, grid_was_on):
    """The gold patch's per-axis decision, transliterated verbatim from
    seaborn/_core/plot.py (post-patch). Uses native float for the half-integer
    literals exactly as the source does, then exposes them as Fraction; -.5 and
    nticks-.5 are dyadic so the conversion is exact."""
    # Pre-existing limit logic (lines 1635-1645): default margins, user override.
    lo, hi = auto_lo, auto_hi
    if has_user:                                  # axis_key in p._limits
        lo, hi = user_lo, user_hi
    grid = grid_was_on
    # Added categorical block (lines 1646-1656):
    if is_cat:                                    # isinstance(...Nominal)
        grid = False                              # axis_obj.grid(False, which="both")
        if not has_user:                          # axis_key not in p._limits
            lo, hi = -.5, nticks - .5             # native float, dyadic -> exact
            if is_y:                              # axis == "y"
                lo, hi = hi, lo
    return (Fraction(lo).limit_denominator(10**12),
            Fraction(hi).limit_denominator(10**12),
            grid)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    cases = []
    # --- boundary / sentinel cases (plan §4.1 step 4) ------------------------
    # The F2P tests: x-axis 3 categories -> (-.5, 2.5) grid off;
    #                y-axis 3 categories -> (2.5, -.5) grid off;
    #                pinned limit (-1, 2.1) survives on either axis.
    cases.append((True, False, False, 3, 0, 0, 0, 0, True))   # F2P x
    cases.append((True, False, True,  3, 0, 0, 0, 0, True))   # F2P y
    cases.append((True, True,  False, 3, -1, Fraction(21, 10), 0, 0, True))  # F2P x pinned
    cases.append((True, True,  True,  3, -1, Fraction(21, 10), 0, 0, True))  # F2P y pinned
    # nticks boundaries
    for n in (0, 1, 2, 3, 10, 100):
        for is_y in (False, True):
            cases.append((True, False, is_y, n, 0, 0, 0, 0, True))
            cases.append((True, False, is_y, n, 0, 0, 0, 0, False))
    # non-categorical: grid + limits left alone, both grid states
    for is_y in (False, True):
        for gw in (True, False):
            cases.append((False, False, is_y, 5, 0, 0, Fraction(-3), Fraction(7), gw))
            cases.append((False, True,  is_y, 5, Fraction(2), Fraction(8),
                          Fraction(-3), Fraction(7), gw))
    # categorical + pinned: pinned wins, grid still suppressed
    for is_y in (False, True):
        cases.append((True, True, is_y, 4, Fraction(-1), Fraction(21, 10),
                      Fraction(0), Fraction(3), True))

    # --- randomized fuzz -----------------------------------------------------
    def rand_lim():
        # mix of ints and exact rationals (resolved unit values are real floats;
        # we use exact fractions so observable-equality is exact)
        if rng.random() < 0.5:
            return Fraction(rng.randint(-1000, 1000))
        return Fraction(rng.randint(-10000, 10000), rng.randint(1, 100))

    for _ in range(N_FUZZ):
        is_cat = rng.random() < 0.5
        has_user = rng.random() < 0.5
        is_y = rng.random() < 0.5
        nticks = rng.randint(0, 200)
        grid_was_on = rng.random() < 0.5
        user_lo, user_hi = rand_lim(), rand_lim()
        auto_lo, auto_hi = rand_lim(), rand_lim()
        cases.append((is_cat, has_user, is_y, nticks, user_lo, user_hi,
                      auto_lo, auto_hi, grid_was_on))

    for c in cases:
        count += 1
        s = shadow_decision(*c)
        o = oracle_decision(*c)
        if s != o:
            disagreements.append((c, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for c, s, o in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (c, s, o))
        return 1
    print("G-CONF OK: R/I shadow of finalizeAxis agrees with the gold-patched "
          "_finalize_figure per-axis decision on %d input tuples (boundary + "
          "F2P + fuzz, seed=%d), 0 disagreements. Categorical ±1/2 tick-range "
          "limits (exact dyadic), y-axis inversion, grid suppression, and "
          "user/default-limit passthrough all confirmed; tick count and default "
          "margins abstracted as read-only inputs." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
