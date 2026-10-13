# refinement.md — matplotlib__matplotlib-26113

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`accumulateBins` `do` block plus the deep `binAggregate`/`aggregateSeq` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The per-bin aggregate-selection site — `Axes.hexbin` (`lib/matplotlib/axes/_axes.py:5016-5020`)

Gold hunk:
```
  accum = np.array(
-     [reduce_C_function(acc) if len(acc) > mincnt else np.nan
+     [reduce_C_function(acc) if len(acc) >= mincnt else np.nan
       for Cs_at_i in [Cs_at_i1, Cs_at_i2]
       for acc in Cs_at_i[1:]],  # [1:] drops out-of-range points.
      float)
```

| # | Solution.lean impl op (`accumulateBins`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `reduceBin : List Float → Float` | `reduce_C_function` (a callable) | R + free input | `reduce_C_function` ↔ `reduceBin` (mapping.md §2/§3.1). FREE INPUT: the spec holds for every reducer; G-CONF instantiates concrete ones. |
| A2 | parameter `minPop : Nat` | `mincnt` after `if mincnt is None: mincnt = 0` | R | `int` (≥0 bin count) ↔ `Nat` (mapping.md §2). The `None→0` normalization is UNCHANGED and is folded into the input value. |
| A3 | parameter `bins : List (List Float)` | `[acc for Cs_at_i in [Cs_at_i1, Cs_at_i2] for acc in Cs_at_i[1:]]` | R + free input | the per-bin C-value lists, `[1:]`-dropped and concatenated (mapping.md §3.2). UNCHANGED binning code; folded into the free input. |
| A4 | `binAggregate reduceBin minPop b = if b.length ≥ minPop then some (reduceBin b) else none` | `reduce_C_function(acc) if len(acc) >= mincnt else np.nan` | I | the changed comparison is modeled **concretely**: `bin.length ≥ minPop` ⇔ `len(acc) >= mincnt`; `some (reduceBin b)` ⇔ `reduce_C_function(acc)`; `none` ⇔ `np.nan`. This is the discriminating clause. |
| A5 | result `out = aggregateSeq reduceBin minPop bins`: the per-bin map, in order, computed by the backward `while` fold | the list comprehension producing `accum` | I | `aggregateSeq`/the verified loop ARE the comprehension: one `binAggregate` per bin, order-preserving. The `np.array(..., float)` wrap is order/value identity (mapping.md §2). |

Discriminating content of the change — a bin whose population EQUALS `minPop` —
lives in `binAggregate`'s `bin.length ≥ minPop` (model) ⇔ `len(acc) >= mincnt`
(real). Pre-patch used strict `>` / `len(acc) > mincnt`; `Solution_prepatch.lean`
reproduces that (`if b.length > minPop`) and **fails** `out = aggregateSeq …` on
the boundary bin (G-DIFF). With the default `mincnt=1`, a singleton bin
(`len==1`) is the F2P-observed case: post-patch aggregated, pre-patch dropped.

## B. No axioms / no A legs

There are no axiomatized callees and no deep-model references requiring G-AX:

- `reduceBin` (`reduce_C_function`) and `bins` (the populations) are FREE INPUTS
  (mapping.md §3.1/§3.2) — the spec quantifies over all values, making no
  behavioural claim, so there is nothing to validate against a real callee.
- The one operation that genuinely CHANGED — the population threshold — is
  modeled DEEPLY and concretely as `bin.length ≥ minPop` (step A4, tag I), not
  hidden behind an axiom about the function under change.

Hence `meta.json axioms = []`, `deep_model_references = []`, and G-AX is
`skip` (no axiom_check.py), exactly as in django-11149.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed op (the `>` → `>=` threshold) is fully
expressible as `Nat` comparison `bin.length ≥ minPop`. No operation is hidden.

## D. verify(Solution) ⇒ resolved

`accumulateBins` verifies only if its output equals the exact per-bin map with
the `bin.length ≥ minPop` selection (A4) and order-faithful aggregation (A5). By
R (`reduce_C_function ↔ reduceBin`, `mincnt ↔ minPop`, bin-list ↔
`List (List Float)`, `np.nan ↔ none`) the verified computation equals the
post-patch comprehension `[reduce_C_function(acc) if len(acc) >= mincnt else
np.nan for ... acc in Cs_at_i[1:]]` on the tested inputs; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed inputs.
Downstream, matplotlib keeps the non-empty bins via `good_idxs =
~np.isnan(accum)`, so the `some`/`none` distinction is exactly what the F2P
`test_hexbin_mincnt_behavior_upon_C_parameter` observes (a `mincnt=1`,
singleton-population bin is now plotted). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust.
