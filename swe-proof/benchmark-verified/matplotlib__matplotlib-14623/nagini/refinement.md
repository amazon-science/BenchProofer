# refinement.md — matplotlib__matplotlib-14623

The operation-by-operation correspondence between `model.py`'s implementation
(the `set_axis_interval` impl region and the `conditioned_lo`/`conditioned_hi`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The orientation-restore site — `set_xlim` / `set_ylim` / `set_*lim3d`

Gold hunk (identical shape at all five sites; `set_xlim` shown):
```
+        swapped = left > right
         left, right = self.xaxis.get_major_locator().nonsingular(left, right)
         left, right = self.xaxis.limit_range_for_scale(left, right)
+        if swapped:
+            left, right = right, left

         self.viewLim.intervalx = (left, right)
```

| # | model.py impl op (`set_axis_interval`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `lo, hi: int` | `left, right` (`float`) args reaching the conditioning | R | `float` ↔ `int`, order-faithful: the tested behaviour depends only on the `<`/`>` order of the endpoints, not their magnitude (mapping.md §2). |
| A2 | `swapped = lo > hi` | `swapped = left > right` | I | the same orientation comparison; `>` over the order-faithful carrier. |
| A3 | `a = conditioned_lo(lo, hi)` ; `b = conditioned_hi(lo, hi)` | `left, right = ...get_major_locator().nonsingular(left, right)` then `...limit_range_for_scale(left, right)` | A-consumed | the conditioning composition is an UNCHANGED callee; the axiom is its **weakest** sufficient contract: always-ascending (`conditioned_lo < conditioned_hi`, distinct AND equal), value-preserving (exact min/max) on **distinct** inputs, and **no concrete value claimed** on equal inputs (only ascending — the equal-case magnitude is scale-dependent and is not modeled). The proof consumes only the always-ascending fact (for the orientation/equal postconditions) and the distinct value-preservation (for the value postcondition). G-AX runs the real callee against this literal Ensures (mapping.md §3.1). |
| A4 | `if swapped: tmp = a; a = b; b = tmp` | `if swapped: left, right = right, left` | I | the same conditional swap. The model uses an explicit three-statement temp swap rather than the tuple form `a, b = b, a` purely because Nagini 1.x does not reliably reason through the parallel-assignment swap (measured: the parallel form left the post-state un-provable; the temp form is the byte-equal concrete operation). Same control flow, same data flow. |
| A5 | `return (a, b)` | `self.viewLim.intervalx = (left, right)` (the store) | R | the modeled function returns the stored pair; the real code assigns it to the view interval, which `ax.get_*lim()` reads back unchanged (mapping.md §2). The F2P test compares `ax.get_ylim()` to the requested pair. |

The discriminating content of the change — *the stored interval must keep the
requested orientation* — lives in the `swapped`-capture (A2) + restore (A4)
wrapped around the always-ascending conditioning (A3). The pre-patch code omits
both; `model_prepatch.py` reproduces that (drops `swapped` and the `if swapped`
restore, returning the conditioned ascending pair directly) and **fails** the
postcondition `Implies(lo > hi, Result()[0] > Result()[1])` — exactly the spec
sensing the change (G-DIFF).

## B. The coupled `ticker.py` `Locator.nonsingular` change (no separate model)

Gold hunk (`lib/matplotlib/ticker.py`):
```
-        return mtransforms.nonsingular(v0, v1, increasing=False, expander=.05)
+        return mtransforms.nonsingular(v0, v1, expander=.05)
```

This hunk changes the **base** (linear) locator so that, like `LogLocator`, it
**always returns ascending** order (dropping `increasing=False` reverts
`mtransforms.nonsingular` to its `increasing=True` default, which swaps a
descending input to ascending). It is a **coupled prerequisite** of site A, not
an independently-fixed behaviour, so it is folded into the conditioning **axiom**
(A3) rather than modeled as a second function:

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the axiom clause "the conditioning ALWAYS returns ascending order" (`conditioned_lo < conditioned_hi`) | `ticker.py`: drop `increasing=False` so the base locator returns ascending | A-consumed | the axiom encodes the *post-change* conditioning behaviour, which is uniform across scales: `LogLocator` already always-ascending (unchanged), and the patched base linear `Locator` now also always-ascending. The proof consumes "always ascending" to prove the restore (A4) is what fixes orientation. G-AX checks both scales (mapping.md §3.1-3.2). |

Why no separate failing `model_prepatch` for site B: at `base_commit` the only
*broken-then-repaired* behaviour is the **log-scale** inversion (site A's
prepatch exercises it). The `ticker.py` hunk has **no** base_commit-observable
failure of its own — linear inversion already worked because the base locator
preserved descending order. The hunk exists solely to keep linear inversion
working *after* the site-A restore is introduced (without it, the linear path
would double-flip and regress). That regression-prevention is guarded by the
PASS_TO_PASS linear assertions of `test_inverted_limits` (`ax.get_xlim() == (-5, 4)`,
`ax.get_ylim() == (5, -3)`), not by a verification-failing skeleton. The shared,
frozen spec (which a prepatch must keep byte-identical, G-DIFF's `same_spec`)
already carries this as the axiom's always-ascending clause; the soundness of
that clause for both scales is audited by G-AX (real callee).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The two operations that genuinely *changed* —
the orientation capture-and-restore (site A) and the locator's always-ascending
normalisation (site B) — are modeled directly: the restore is spelled out in the
impl (A2/A4, **I**-steps over the order-faithful carrier), and the
always-ascending normalisation is the **A-consumed** conditioning axiom (an
*unchanged* callee for the log path, made uniform for the linear path by the
coupled hunk). There is no axiomatization of the function under change
(`set_*lim*` itself): its orientation logic is the modeled impl. The only
consumed axiom covers the conditioning composition the new code *calls* and does
not itself implement.

## D. verify(model) ⇒ resolved

`set_axis_interval` verifies only if its output keeps the requested orientation
(A2+A4 against the always-ascending conditioning A3/B1) and preserves the
endpoint values on distinct inputs. The proof consumes only the axiom's
**always-ascending** fact (`conditioned_lo < conditioned_hi`, which holds for
distinct AND equal endpoints) plus distinct-value preservation; it never used
the concrete equal-case magnitude. The axiom was therefore weakened to drop the
over-specified equal-case `lo-1`/`hi+1` values (the real callee never produces
them — it returns scale-dependent `(1,10)` log / `(4.75,5.25)` linear), and a
`< 1e15` order-faithful magnitude bound was added to the shared `Requires`; the
proof **still goes through unchanged** with the weaker axiom (G-VERIFY passes;
the `>=` mutant still dies on the equal-case ascending postcondition), and the
byte-identical-spec `model_prepatch` still fails the orientation clause
(G-DIFF). By R (float ↔ int order-faithful on the bounded domain; the
view-interval store read back by `get_*lim`) the verified function equals the
gold-patched `set_ylim`/`set_xlim`/`set_*lim3d` on the tested endpoints; by G-AX
the conditioning axiom soundly over-approximates the real callee on both scales,
and the end-to-end gold-patched `set_ylim` keeps the requested orientation.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited conditioning callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
