# refinement.md — matplotlib__matplotlib-24177

The operation-by-operation correspondence between `model.py`'s implementation
(the `enclosing_upper_bound` impl region, the deep `seq_max` model + dominance
lemma) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, gathers an extent that encloses the
whole path on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The gather site — `_update_patch_limits` (`lib/matplotlib/axes/_base.py:2437`)

Gold hunk:
```
-        for curve, code in p.iter_bezier():
+        for curve, code in p.iter_bezier(simplify=False):
             _, dzeros = curve.axis_aligned_extrema()
             vertices.append(curve([0, *dzeros, 1]))
```
The gathered `vertices` feed `update_datalim(xys, ...)` (`:2457`), which sizes
the autoscaled view.

| # | model.py impl op (`enclosing_upper_bound`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `verts: List[int]` | the gathered `vertices` (one axis of the Nx2 array fed to `update_datalim`) | R | per-axis coordinate sequence ↔ `List[int]` (mapping.md §2). |
| A2 | integer coordinate values | `float` coordinates | R | the tested behaviour is WHICH vertices are gathered — whether the extreme-bearing vertex is included — not floating-point precision. The F2P test compares inclusion (`xlim ≥ maxx`), so the precision-independent integer carrier is faithful (no `--float-encoding`). |
| A3 | the loop folds the maximum over EVERY element of `verts` (`seq_max(ToSeq(verts))`); `lemma_seq_max_dominates` proves `Result() >= verts[k]` for all k (enclosing) and `lemma_seq_max_attained` proves `Result() == verts[j]` for some j (tightness) | `for curve, code in p.iter_bezier(simplify=False)` gathers every path vertex; `update_datalim` then takes the per-axis max/min as the extent | A-reference | the changed gather is modeled **deeply**: `seq_max` + the verified loop ARE the per-axis maximum over the full vertex set, the dominance lemma is the enclosing property, and the attained lemma pins the bound to a real datum (a max/min IS attained at some vertex). There is no consumed axiom for the maximum. G-AX (axiom_check.py) runs the real `iter_bezier(simplify=False)` gather and asserts its max ≥ every vertex (and min ≤ every vertex) — the deep model == the real full gather (mapping.md §3.1). `simplify=False` ⇒ the C condensation is bypassed ⇒ the gather visits all vertices ⇒ the model's "fold over all of `verts`" is faithful. |
| A4 | `Result()` returned (the enclosing upper end) | the extent's upper end inside `update_datalim` → `ax.get_{x,y}lim()` | R | the autoscaled limit ≥ every datum ⇔ `Result() >= verts[k]` for all k, AND it is attained (`Result() == verts[j]` for some j) because the data-limit extreme is the max/min OF the gathered data, not a padded value (mapping.md §2); the F2P `test_small_autoscale` asserts the limit encloses min/max of the actual vertices. The attained clause makes the spec self-sufficient: it excludes any over-approximating impl that returns `max + padding`, removing the spec's reliance on the refinement-map/G-EQ-map check (per SPEC_GUIDE directive 8 — an extent spec needs a tightness clause). |

The discriminating content of the change — gathering **all** vertices vs. only
the appearance-preserving **condensation** — lives in the choice of fold source:
`model.py` folds over `verts` (all), `model_prepatch.py` folds over
`subsel_at(s, ·)` for `idx ∈ [0, subsel_len(s))` (the subset). The axiom
guarantees only membership, so the prepatch can prove `Result() <= seq_max(verts)`
but NOT `Result() >= verts[k]` for a dropped extreme — it **fails** the enclosing
postcondition `Forall k. Result() >= verts[k]`, which is exactly the spec sensing
the change (G-DIFF).

## B. The pre-patch condensation — `iter_bezier()` default (`path.py:420`)

The pre-patch gather iterates `p.iter_bezier()` with the default `simplify=None`,
which lets `Path.cleaned`→`_path.cleanup_path` apply the condensation (drops
interior vertices on a long MOVETO/LINETO path). This is modeled by the
`subsel_len` / `subsel_at` axioms, consumed only by `model_prepatch.py`.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `subsel_len(verts)` axiom (`0 ≤ count ≤ len`) and `subsel_at(verts, idx)` axiom (membership: `== verts[j]` for some in-bounds j) | the pre-patch `p.iter_bezier()` gather source (the thing the fix removes by passing `simplify=False`) | A-consumed | the weakest sound contract on the condensation: it never invents vertices (membership) and never grows the count (mapping.md §3.2). The prepatch consumes these `Ensures` and is unable to discharge the enclosing postcondition — precisely because the axioms promise nothing about the extremes. G-AX confirms them against the real `iter_bezier`. |

Why no separate failing `model_prepatch_<k>`: the patch is a **single hunk**
toggling one keyword (`simplify=False`) at one call site — one independently
fixed behaviour. `model_prepatch.py` already exercises it: gathering over the
condensation (B1) versus all vertices (A3) is the whole change, and the prepatch
fails on the one enclosing clause.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely changed — the
gather source (all vertices vs. the condensation) — is modeled **deeply** (the
spelled-out `seq_max` fold over all of `verts`, an **A-reference** validated
against the real full gather), not hidden behind an axiom about the function
under change. The only consumed axiom, `subsel_*` (**A-consumed**), covers the
**unchanged** callee `Path.iter_bezier` in its pre-patch (condensing)
configuration; the patched full gather appears only as the **A-reference** that
G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`enclosing_upper_bound` verifies only if its result dominates every coordinate of
the full vertex set (A3, the enclosing postcondition). By R (per-axis sequence ↔
`List[int]`; precision-independence A2; extent-upper-end ↔ `Result()` A4) the
verified gather equals taking the per-axis max over `iter_bezier(simplify=False)`
on the tested outlines; by G-AX the deep `seq_max` model == the real full gather
(A-reference) and the real `iter_bezier()` condensation meets the membership
axioms it stands in for (A-consumed). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE: `test_small_autoscale` asserts
the autoscaled limits enclose `min/max` of the path). The trust points are the
two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document,
G-EQ).
