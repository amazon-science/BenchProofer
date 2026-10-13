# refinement.md — pydata__xarray-3677

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`combineKeyed` `do` block + the `combineCore` deep model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-reference** (deep
model validated == the real callee by G-AX), or **I** (identical concrete op).
There are no consumed axioms.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg + this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The operand-handling tail — `Dataset.merge` (`xarray/core/dataset.py:3597-3613`)

Gold hunk:
```
  _check_inplace(inplace)
+ other = other.to_dataset() if isinstance(other, xr.DataArray) else other
  merge_result = dataset_merge_method(
      self,
      other,
      ...
```

| # | Solution.lean impl op (`combineKeyed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `base : KeyedMap` | `self` (the receiving `Dataset`) | R | a variable mapping `{name: value}` ↔ `List (Nat × Int)` (mapping.md §2). G-CONF bridges names↔`Nat`, scalar values↔`Int`. |
| A2 | parameter `other : Operand` | `other` (the merge operand) | R | a `Dataset`/mapping ↔ `.keyed es`; a named `DataArray` ↔ `.single k v` (mapping.md §2). G-CONF bridges the two shapes. |
| A3 | `other' := match other with .single k v => .keyed (asKeyed k v) \| .keyed es => .keyed es` | `other = other.to_dataset() if isinstance(other, xr.DataArray) else other` | I | the **added** op. A lone keyed value is re-expressed as a one-entry collection (`to_dataset()` ↔ `asKeyed`); a collection passes through. Transliterated 1:1 by G-CONF. This is the single behavioural change `test_merge_dataarray` observes. |
| A4 | `combineCore base other'` | `dataset_merge_method(self, other, ...)` (→ `merge_core` → `coerce_pandas_values`) | A-reference + I | the unchanged core-combine callee, modeled deeply by `combineCore` and validated == the real callee by G-AX (mapping.md §3.1). Passing the (now normalized) operand to the combine is **I**; the equality of the deep model to the real combine (incl. the raw-`DataArray` crash) is the **A-reference**. |
| A5 | `return out` | `merge_result = ...; return self._replace(**merge_result._asdict())` | I | the fused result is handed back. In the modeled disjoint-name regime the result mapping is `base ++ es` (mapping.md §2). `_replace`/`_asdict` are pure repackaging of that mapping, observationally the identity under R. |

Discriminating content of the change — a `.single` operand (a raw `DataArray`)
is **re-expressed into a collection before the combine**, instead of being fed
to the combine directly — lives in `combineSpec base (.single k v) =
.ok (combineEntries base (asKeyed k v))` (model) ⇔ the added `other =
other.to_dataset() if isinstance(other, xr.DataArray) else other` (real). The
pre-patch tail fed the raw operand to the combine; `Solution_prepatch.lean`
reproduces that (`let out := combineCore base other`) and **fails**
`out = combineSpec base other` on the `.single` case (G-DIFF), because
`combineCore base (.single _ _) = .error .notKeyed ≠ .ok (...)` — the modeled
analogue of the real `AttributeError: 'DataArray' object has no attribute
'items'`.

## B. No consumed axioms

The only callee, the core-combine machinery (`dataset_merge_method`), is modeled
deeply (`combineCore`, an A-reference checked by G-AX), not consumed as an axiom.
The function under change (`Dataset.merge`'s operand-handling tail) is never
axiomatized (SPEC_GUIDE §0.7). The added `to_dataset()` re-expression is modeled
concretely (`coerceOperand`, step A3, **I**).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the added operand normalization — is modeled concretely (step A3, **I**), with
its abstract desired behavior pinned by `combineSpec` (normalize-then-combine).
The core-combine callee it feeds is unchanged and modeled deeply.

## D. verify(Solution) ⇒ resolved

`combineKeyed` verifies only if its output equals `combineSpec base other` for
**all** `base, other` — in particular the `.single` case must re-express the
operand into a one-entry collection and then combine (A3/A4), and the `.keyed`
case must combine the collection directly (A4). By R (`self/other ↔
KeyedMap/Operand`, only names/values observed) the verified tail equals the
patched `merge_result = dataset_merge_method(self, other.to_dataset() if
isinstance(other, xr.DataArray) else other, ...)` on the tested inputs; by G-AX
the deep model `combineCore` equals the real `dataset_merge_method` (incl. the
raw-`DataArray` crash, an A-reference); by G-CONF the R/I transliteration of the
coerce-then-combine tail agrees with `patch.diff`'s patched-`Dataset.merge`
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited callee — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: deep-model fidelity (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).
