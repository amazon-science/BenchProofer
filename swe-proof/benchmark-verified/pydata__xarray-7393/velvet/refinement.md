# refinement.md — pydata__xarray-7393

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`arrayDispatch` `do` block plus the pure deep model `arrayMaterialize`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(a deep model validated == the real callee by G-AX), or **I** (identical
concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
plan §4.1); the A legs and this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `PandasMultiIndexingAdapter.__array__` (`xarray/core/indexing.py:1530`)

The patch (a) defaults a missing requested dtype to the view's recorded dtype,
and (b) in the level branch wraps the level values in `np.asarray(..., dtype=dtype)`
so the result is tagged with the recorded/requested dtype rather than the
storage's native (promoted) dtype. The else branch is unchanged.

Gold hunk:
```
     def __array__(self, dtype: DTypeLike = None) -> np.ndarray:
+        if dtype is None:
+            dtype = self.dtype
         if self.level is not None:
-            return self.array.get_level_values(self.level).values
+            return np.asarray(
+                self.array.get_level_values(self.level).values, dtype=dtype
+            )
         else:
             return super().__array__(dtype)
```

| # | Solution.lean impl op (`arrayDispatch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `adapter : Int` | the `self` view in scope | R | the view ↔ an opaque `Int` handle (mapping.md §2); only `recordedDtype`/`isComponent`/`componentValues` are read, never decomposed. G-CONF bridges by replaying each real view and reading the observations. |
| A2 | param `dtype : Option Dtype` | the `dtype: DTypeLike = None` argument | R | `None ↔ Option.none`, an explicit dtype `↔ Option.some` (mapping.md §2). |
| A3 | `let d := dtype.getD (recordedDtype adapter)` | `if dtype is None: dtype = self.dtype` | I + A-reference | the default-resolution the patch adds; `Option.getD` ↔ "use the requested dtype, else `self.dtype`". `recordedDtype` = `self.dtype` is the UNCHANGED recorded-dtype observation (**A-reference**); `getD` is the **I** transliteration of `if dtype is None`. |
| A4 | `if isComponent adapter then …` | `if self.level is not None:` | A-reference + I | `isComponent` ↔ `self.level is not None`, the UNCHANGED structural observation (**A-reference**); the `if` dispatch is **I** (transliterated 1:1 by G-CONF). |
| A5 | `toDtype (componentValues adapter) d` (component branch: retag the stored level values to the resolved dtype) | `np.asarray(self.array.get_level_values(self.level).values, dtype=dtype)` | A-reference + I | **the discriminating clause.** `componentValues` ↔ `self.array.get_level_values(self.level).values` (UNCHANGED callee, **A-reference**, tagged with the storage's native dtype which may differ from the recorded one — mapping.md §3.1); `toDtype _ d` ↔ `np.asarray(_, dtype=dtype)` (UNCHANGED conversion, **A-reference**: its result's dtype is exactly `d` — mapping.md §3.2); the application/retag itself is **I**. This is the leg the bug lives in. |
| A6 | `else baseMaterialize adapter dtype` | `else: return super().__array__(dtype)` | A-reference + I | `baseMaterialize` ↔ `super().__array__(dtype)`, the UNCHANGED inherited non-level path (**A-reference**); the else dispatch is **I**. Unchanged by the patch — the non-level path already resolved the default and cast internally. |
| A7 | `return result` (yields the `MatArray`) | the function returns the materialized `np.ndarray` | R | the produced array ↔ `MatArray`; the only observation the F2P test makes is its `.dtype` (mapping.md §2). |

Discriminating content of the change — when the view exposes a single component
of a composite index, the materialized array must carry the view's
recorded/requested dtype, NOT the storage's native (promoted) dtype — lives in
the `if isComponent adapter then toDtype (componentValues adapter) d` leg (A5) ⇔
the new `np.asarray(self.array.get_level_values(self.level).values, dtype=dtype)`.
`Solution_prepatch.lean` reproduces the pre-patch level branch
(`componentValues adapter` returned directly, the storage's native dtype) and
**fails** `out = arrayMaterialize adapter dtype` precisely on that leg (G-DIFF;
confirmed: the prepatch's unsolved goal is the `isComponent adapter = true`
case, where the spec forces `toDtype (componentValues adapter) d` but the
prepatch yields `componentValues adapter`).

## B. No consumed axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. All five modeled callees (`recordedDtype`,
`isComponent`, `componentValues`, `toDtype`, `baseMaterialize`) are **unchanged**
by the patch — it adds a default-resolution line and wraps the level values in a
cast; it does not redefine any of them. They are modeled `opaque` with **NO
asserted `ensures`**, so there is **no consumed axiom** to over-claim
(directive 7): the contract assumes nothing about WHICH values or storage dtype
the level holds, only that the result is retagged to the resolved dtype. They are
tagged **A-reference** — G-AX validates the modeled facts against the real
callees (mapping.md §3): the level's native dtype really can differ from the
recorded dtype (so the retag is load-bearing, not dead), `np.asarray(_, dtype=d)`
really yields dtype `d`, and the inherited path already returns the recorded
dtype.

The operation that genuinely *changed* — retagging the component branch's array
to the resolved dtype (and defaulting the requested dtype) — is modeled
**directly** (A3/A5, I legs over A-reference callees), not hidden behind an axiom
about the function under change. There is no axiom about `__array__` itself.

## C. verify(Solution) ⇒ resolved

`arrayDispatch` verifies only if its output equals `arrayMaterialize adapter dtype`
for every view — including the `isComponent adapter = true` leg, which forces the
result to be `toDtype (componentValues adapter) d` whose dtype is the resolved
`d = dtype.getD (recordedDtype adapter)` (A5), and the else leg, which delegates
to `baseMaterialize` (A6). By R (the view ↔ `Int` handle, `dtype` ↔ `Option`,
the array ↔ `MatArray`) and the I transliteration of the default-resolution / the
level branch / the cast, the verified dispatch equals the gold patch's
`__array__` on the tested views; by G-AX the real `get_level_values(...).values`
carries a native dtype that differs from the recorded dtype on the issue's
int32/float32 coordinates (so the retag is the genuine repair), `np.asarray(_,
dtype=d)` yields dtype `d`, and the inherited path already returns the recorded
dtype; by G-CONF the R/I shadow of the dispatch agrees with `patch.diff`'s
behaviour on ≥10⁵ fuzzed views. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and audited callees —
and the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: callee-fact soundness (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).
