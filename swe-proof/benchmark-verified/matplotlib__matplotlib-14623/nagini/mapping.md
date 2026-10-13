# mapping.md — matplotlib__matplotlib-14623

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d65c9ca20ddf81ef91199e6d819f9d3506ef477c`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo files under change:
`lib/matplotlib/axes/_base.py`, `lib/matplotlib/ticker.py`,
`lib/mpl_toolkits/mplot3d/axes3d.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `set_axis_interval(lo, hi)` | `Axes.set_xlim` — `lib/matplotlib/axes/_base.py:3161` (body 3267-3270); `Axes.set_ylim` — `:3540` (body 3647-3650); `Axes3D.set_xlim3d/set_ylim3d/set_zlim3d` — `lib/mpl_toolkits/mplot3d/axes3d.py:589/646/704` | the modeled changed function: capture the requested orientation, apply the conditioning callee, restore the orientation, store the interval |
| `conditioned_lo(lo, hi)` / `conditioned_hi(lo, hi)` *(axiom — A-consumed)* | the conditioning composition `self.<ax>.get_major_locator().nonsingular(lo, hi)` then `self.<ax>.limit_range_for_scale(lo, hi)`. For the log axis (the bug's locus): `LogLocator.nonsingular` — `lib/matplotlib/ticker.py:2378` + `LogScale.limit_range_for_scale` — `lib/matplotlib/scale.py:420` | UNCHANGED conditioning callee the modeled function calls; it always returns its output in ascending order |

The five `set_*lim*` sites are byte-for-byte the same hunk shape (capture
`swapped = a > b`; conditioning; `if swapped: swap`); one model function
`set_axis_interval` is the faithful skeleton of all five (refinement.md §A).

The repo symbol the second patch hunk edits, `Locator.nonsingular`
(`lib/matplotlib/ticker.py:1523`), is NOT a separately-modeled function: it is a
**coupled prerequisite** of the `set_*lim*` change folded into the conditioning
axiom (see §3.2 and refinement.md §B). Pre-patch it forwards to
`mtransforms.nonsingular(v0, v1, increasing=False, expander=.05)`
(`lib/matplotlib/transforms.py:2791`); the patch drops `increasing=False` so it
forwards to `mtransforms.nonsingular(v0, v1, expander=.05)` (default
`increasing=True`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `float` endpoints (`left`/`right`, `bottom`/`top`) | `int` | the tested behaviour — *which of two distinct admissible endpoints ends up first in the stored interval* — depends only on the order relation `<` / `>` of the endpoints, never on floating-point magnitude. The `int` carrier preserves that order relation exactly **within the order-faithful magnitude range** `(0, 1e15)`, which the `Requires` bounds (`lo, hi < 1e15`); above `1e16` distinct integers collapse to a single `float64` and the carrier stops being order-faithful, and at `≥1e15` the conditioning's relative-gap expansion fires (see §3.1) — both excluded by the bound and untested. No arithmetic on magnitudes is performed by the modeled function (only the orientation comparison `lo > hi` and a value-preserving swap), so `float`↔`int` is order-faithful for the modeled control/data flow on the bounded domain. `float_encoding` is therefore `null` (precision is NOT the behaviour). |
| the returned/stored 2-tuple `(left, right)` / `(bottom, top)` | `Tuple[int, int]` | `Result()[0]` ↔ first stored endpoint, `Result()[1]` ↔ second; the in-place `left, right = right, left` swap ↔ the model's three-statement temp swap (refinement.md A4, an I-step) |
| `self.viewLim.intervalx = (left, right)` (the store) | `return (a, b)` | the F2P test reads the stored interval back via `ax.get_ylim()`, which returns exactly the stored pair; the model returns that pair (refinement.md A6) |

The endpoints reaching the conditioning step are positive: for a log axis the
upstream `get_yscale() == 'log'` validation block (`_base.py:3250-3262` /
`3629-3641`) replaces any non-positive endpoint with the old limit, so the pair
the conditioning sees is positive — captured (together with the order-faithful
magnitude bound) by `Requires(lo > 0 and hi > 0 and lo < 1e15 and hi < 1e15)`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `conditioned_lo` / `conditioned_hi` ↔ the conditioning composition (A-consumed)
**Callee:** `self.<ax>.get_major_locator().nonsingular(lo, hi)` then
`self.<ax>.limit_range_for_scale(lo, hi)`. The axiom's load-bearing referent is
the **logarithmic** axis (the bug's locus), whose locator is `LogLocator`
(`ticker.py:2378`), **unchanged by the patch**:

```python
def nonsingular(self, vmin, vmax):
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        return 1, 10
    if vmin > vmax:
        vmin, vmax = vmax, vmin          # ALWAYS sorts ascending
    if vmax <= 0:
        ... ; return 1, 10
    minpos = self.axis.get_minpos()
    ...
    if vmin <= 0:
        vmin = minpos
    if vmin == vmax:                     # equal -> expand to surrounding decades
        vmin = _decade_less(vmin, self._base)
        vmax = _decade_greater(vmax, self._base)
    return vmin, vmax                    # vmin < vmax  (ascending)
```

followed by `LogScale.limit_range_for_scale` (`scale.py:420`), which only clamps
non-positive endpoints up to `minpos` (a no-op on positive endpoints). For two
**distinct positive** endpoints the composition returns them ascending with
their values preserved; for two **equal** endpoints it expands to a
strictly-ascending surrounding interval whose concrete magnitude is
**scale-dependent** (`(1, 10)` for log, `(4.75, 5.25)` for linear at `5,5`).
This is exactly what the axiom encodes, **at its weakest**:

  `conditioned_lo = min` , `conditioned_hi = max`  on **distinct** positive inputs;
  on **equal** inputs, ONLY the always-ascending relation
  `conditioned_lo < conditioned_hi` — **no concrete equal-case value is
  claimed** (a prior revision over-specified the equal case as `lo-1`/`hi+1`,
  values the real callee never produces; that over-claim was the G-AX defect and
  has been removed).

The axiom is the **weakest** contract the modeled function needs: only the
always-ascending order (distinct AND equal) + value-preservation on distinct;
not the equal-case expansion magnitudes, not the decade magnitudes. The proof
**consumes** its `Ensures` to discharge the orientation postconditions
(refinement.md A3/B), hence **A-consumed**.

**Order-faithful magnitude bound.** The axiom (and `set_axis_interval`)
`Requires` carries `lo > 0 and hi > 0 and lo < 1e15 and hi < 1e15`. The upper
bound is the range over which the `int` carrier is order-faithful and the
conditioning preserves distinct values exactly. Above it two things fail:
(i) at `≥1e15` (on the **linear** locator) the `mtransforms.nonsingular`
relative-gap rule (`tiny=1e-15`) expands a too-narrow distinct pair, breaking
the distinct-value-preservation `Ensures`; (ii) at `≥1e16` distinct integers
collapse to a single `float64`, so the `int↔float` carrier ceases to be
order-faithful at all. All tested `set_*lim*` inputs (the F2P/P2P calls) sit
well inside the bound, so the bound only excludes an untested precision-collision
regime; it does not weaken the modeled behaviour on any tested input.

**Soundness check (G-AX):** `axiom_check.py` builds real matplotlib axes,
exercises `get_major_locator().nonsingular(lo, hi)` then
`limit_range_for_scale(...)` and asserts the **literal** model `Ensures`:
exact min/max preservation on **distinct** inputs, and ONLY ascending on
**equal** inputs (with an explicit regression guard that the result is *not*
the old `lo-1`/`hi+1`). It fuzzes the **full in-domain range** `[1, 1e15)`
(boundary pairs incl. F2P `(10,1)`/`(1,10)`, multiple equal pairs, and
adjacent-integer pairs just below `1e15`; ~650 randomized pairs per scale incl.
a near-boundary band and equal-pair fuzz) — not the previous arbitrary
`[1, 1e5]` window that missed the over-specification. It also asserts the
`1e15` bound is **load-bearing**: the `≥1e15` (linear expansion) and `≥1e16`
(int→float collision) regimes are confirmed to lie outside the domain and to
actually violate, so without the bound the check would fail. For the log scale
this is sound pre- and post-patch (LogLocator unchanged), so it is the
always-valid referent; it also corroborates the linear scale and the
end-to-end orientation once the gold patch is applied (auto-detected). Imports
only `matplotlib`.

### 3.2 The coupled `ticker.py` `Locator.nonsingular` change (folded into §3.1)
**Callee:** the base `Locator.nonsingular` (`ticker.py:1523`), used by the
**linear** (default) axis. Pre-patch it calls
`mtransforms.nonsingular(v0, v1, increasing=False, expander=.05)`; with
`increasing=False`, `mtransforms.nonsingular` **preserves** a descending input
order (`transforms.py:2840` `if swapped and not increasing: swap back`). The
patch removes `increasing=False`, so post-patch the base locator (like
`LogLocator`) **always returns ascending**.

This change is a **coupled prerequisite**, not an independently-observable
fixed behaviour, and is therefore folded into the conditioning axiom rather than
modeled as a second function (refinement.md §B explains the coupling):

* The `set_*lim*` change adds a single `swapped`-capture-and-restore wrapped
  around the conditioning. That restore is correct **only if** the conditioning
  always returns ascending — which the axiom assumes.
* The log locator already always returns ascending (so the log path is the one
  that was *broken* at base_commit and is *fixed* by the `set_*lim*` change).
* The linear locator at base_commit preserved descending order, so the linear
  `set_xlim`/`set_ylim` inversion already worked **without** any restore. If the
  `set_*lim*` restore were added without the `ticker.py` change, the linear path
  would double-flip (locator preserves descending, then the restore flips it to
  ascending) and *break*. Removing `increasing=False` makes the linear locator
  ascending so the single uniform restore is correct for both scales.

Thus the two hunks are one coherent change: "make all locators normalise to
ascending, and let `set_*lim*` own the orientation restore." The axiom models
the post-change conditioning (always ascending) for **both** scales; G-AX checks
both. There is no second `model_prepatch_<k>` because at base_commit the only
*broken-then-repaired* behaviour is the log-scale inversion, exercised by the
single prepatch; the `ticker.py` change has no base_commit-observable failure of
its own (linear inversion already passed) — it only prevents a regression that
the `set_*lim*` change would otherwise introduce, which the PASS_TO_PASS linear
assertions of `test_inverted_limits` guard.
