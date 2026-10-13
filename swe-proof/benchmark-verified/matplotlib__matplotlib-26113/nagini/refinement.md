# refinement.md — matplotlib__matplotlib-26113

The operation-by-operation correspondence between `model.py`'s implementation
(the `populated_bins` impl region and the deep `decision_agg` / `decision_count`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses an axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real code by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — the `accum` decision in `hexbin` (`lib/matplotlib/axes/_axes.py:5016-5020`)

Gold hunk:
```
- [reduce_C_function(acc) if len(acc) > mincnt else np.nan
+ [reduce_C_function(acc) if len(acc) >= mincnt else np.nan
   for Cs_at_i in [Cs_at_i1, Cs_at_i2]
   for acc in Cs_at_i[1:]],  # [1:] drops out-of-range points.
```

| # | model.py impl op (`populated_bins`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `occupancies: List[int]` | the iterable `[acc for Cs_at_i in [Cs_at_i1, Cs_at_i2] for acc in Cs_at_i[1:]]` of per-hexagon value lists | R | each `acc` (a Python list) ↔ its occupancy `len(acc)`; on the modeled domain (`mincnt >= 1`) the decision depends on `acc` only through `len(acc)` — every kept bin is nonempty, so its aggregate is a real value (mapping.md §2, §2a). |
| A2 | parameter `threshold: int`, `Requires(threshold >= 1)` | `mincnt`, a positive int per the documented regime (`mincnt : int > 0`, `_axes.py:4850-4852`) | R | identity on the positive integer threshold. The unset default (`None` → `0`, `_axes.py:5014-5015`) is outside the modeled boundary: at `mincnt = 0` the empty-bin outcome depends on the aggregator's value on `[]` (default `np.mean` → NaN cleared; `sum` → 0.0 populated), not on the occupancy comparison, so the occupancy-only carrier cannot express it; and the gold change is observation-equivalent there under the default aggregator (pre/post differ only on empty bins, which the default's NaN clears either way). The fixed, tested behaviour lives at `mincnt >= 1` (mapping.md §2a). |
| A3 | per element, `flag = occ >= threshold` (the loop body building `result`), pinned by the index-wise postcondition `Result()[k] == decision_agg(occupancies[k], threshold)` with `decision_agg(occ, t) == occ >= t` | `reduce_C_function(acc) if len(acc) >= mincnt else np.nan` | A-reference | the changed comparison is modeled **deeply**: `decision_agg` (`occ >= t`) is the spelled-out per-bin populated/cleared decision, and the verified loop pins every result element to it. No consumed axiom about `reduce_C_function` or `np.nan` exists — the proof never depends on one. The aggregated value vs NaN is abstracted to a `bool` populated-flag (mapping.md §2): `True` ↔ `reduce_C_function(acc)` (a real value), `False` ↔ `np.nan`. G-AX validates that this deep model equals the real value-aggregation decision (`len(acc) >= mincnt`) and that it coincides with the bare-count decision over boundary + fuzz. |
| A4 | `result` list of populated-flags returned (`List[bool]`) | the `accum` array of reals / NaNs (followed by `good_idxs = ~np.isnan(accum)` at `_axes.py:5022`) | R | `accum` is observed only through `~np.isnan(accum)` (which bins survive); a real value ↔ `True`, NaN ↔ `False` (mapping.md §2). |

The discriminating content of the change — the comparison `>` → `>=` — lives
in `decision_agg(occ, t) == occ >= t` (model) ⇔ `len(acc) >= mincnt` (real).
The pre-patch code used `len(acc) > mincnt`; `model_prepatch.py` reproduces
that (`flag = occ > threshold`) and **fails** the per-element loop invariant
`result[k] == decision_agg(occupancies[k], threshold)` (which feeds the
postcondition), which is exactly the spec sensing the change (G-DIFF).

## B. The consistency clause (the property the test demands)

The F2P test `test_hexbin_mincnt_behavior_upon_C_parameter[png]` asserts that
the `C`-given hexbin with `mincnt=1` renders identically to the `C`-absent
hexbin with `mincnt=1`. That is a *cross-regime* statement: the
value-aggregation regime's per-bin decision must equal the bare-count regime's.

In this (index-Forall) model the consistency is **folded directly into
`populated_bins`'s postcondition**: each result element must equal BOTH the
value-aggregation decision and the bare-count decision —
`Result()[k] == decision_agg(occupancies[k], threshold) and Result()[k] ==
decision_count(occupancies[k], threshold)`. There is no separate lemma
function; the consistency is a load-bearing conjunct on the actual result.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the conjunct `Result()[k] == decision_count(occupancies[k], threshold)` in `populated_bins`'s postcondition | the correctness obligation the `>` → `>=` change establishes: the `C`-given decision (`len(acc) >= mincnt`) now matches the `C`-absent decision (`count >= mincnt`, from `accum[accum < mincnt] = np.nan` at `_axes.py:5002-5003`) | I | `decision_agg(occ,t) == (occ >= t)` and `decision_count(occ,t) == not (occ < t) == (occ >= t)` are the same integer relation; the conjunction is provable from `flag = occ >= threshold` and **fails** under the pre-patch comparison (`occ > t ≠ occ >= t` at `occ == t`, e.g. `occ == t == 1`). This is the exact equality the test observes (at `mincnt=1`, inside the modeled domain `threshold >= 1`); `decision_count` is the unchanged bare-count oracle (mapping.md §3.1). The cross-regime equality is asserted only on the modeled domain — at the out-of-domain `mincnt = 0` it genuinely fails in the real code under the default aggregator (empty bin: value-aggregation clears via `np.mean([])` = NaN, bare-count keeps), which is an empty-bin payload effect outside the changed comparison's observable behaviour, not part of the fixed behaviour (mapping.md §2a). |

There is one independently-fixed behaviour (a single one-operator change), so a
single `model_prepatch.py` suffices; it reverts A3 to `occ > threshold` and
fails the per-element postcondition (both the `decision_agg` and the
`decision_count` conjunct collapse to the same failure) at the boundary
occupancy `occ == threshold` (e.g. `occ == threshold == 1`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-bin threshold comparison — is modeled **deeply**
(`decision_agg`, the spelled-out `occ >= t`, pinned by the verified loop on
every result element), not hidden behind an axiom about the function under
change. There is **no consumed `@ContractOnly` axiom** in this bundle: the
`reduce_C_function` callee and the `np.nan` marker are abstracted away (they do
not affect the populated/cleared decision), and the bare-count oracle
`decision_count` is itself spelled out. The deep model is validated against the
real `hexbin` decision by G-AX (axiom_check.py), an **A-reference**.

## D. verify(model) ⇒ resolved

`populated_bins` verifies only if every result element equals the exact per-bin
value-aggregation decision `occ >= threshold` (A3) AND only if that decision
coincides with the bare-count decision for that bin (B1), on the modeled domain
`threshold >= 1` (A2 — the documented `mincnt : int > 0` regime, where the F2P
test lives). By R (per-hexagon list ↔ its length; real-value/NaN ↔
`True`/`False`; positive `mincnt` ↔ `threshold`) the verified decision equals
`len(acc) >= mincnt` applied per bin in the real `hexbin` accum comprehension;
by G-AX the deep model `decision_agg` equals the real value-aggregation
decision (default `np.mean` and `sum` aggregators) and coincides with the
bare-count decision on that domain (the A-reference), and the excluded
`mincnt = 0` sub-domain is both inexpressible in the occupancy-only carrier
(empty-bin aggregator dependence) and observation-equivalent across pre/post
patch under the default aggregator (mapping.md §2a) — so nothing of the gold
change's tested behaviour escapes the boundary. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement
and the audited deep model — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: deep-model soundness (G-AX) and
refinement fidelity (this document, G-EQ).
