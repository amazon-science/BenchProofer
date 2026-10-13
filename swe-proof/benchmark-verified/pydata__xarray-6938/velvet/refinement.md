# refinement.md — pydata__xarray-6938

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `reifyIndependent` `do` block) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (a deep model validated == the real callee by G-AX),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The behavioural fix — `IndexVariable.to_index_variable` (`variable.py:2882`)

Gold hunk:
```
 def to_index_variable(self) -> IndexVariable:
     """Return this variable as an xarray.IndexVariable"""
-    return self
+    return self.copy()
```

The pre-patch `return self` hands back the SAME object; the post-patch
`return self.copy()` returns a fresh, independent object. The F2P test
`test_to_index_variable_copy` observes exactly this: `a is not b`, and mutating
`b.dims` leaves `a.dims` unchanged.

| # | Solution.lean impl op (`reifyIndependent`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `self : Handle`; the live heap as `store : Handle → Payload`, frontier `nextFresh` | `self` (the `IndexVariable`) and the ambient object heap | R | object identity ↔ `Handle`; `obj.dims` ↔ `store (handle obj)` (mapping.md §2). G-CONF bridges via a Python dict store keyed by integer handles. |
| A2 | `let r := nextFresh` (a fresh handle, above every live one) | the new object `self.copy()` allocates | A-reference + I | the changed op is modeled **deeply**: allocation of a distinct identity IS what `copy()` does. The `nextFresh` bump is the **I** transliteration; the fact that the real `copy()` yields a distinct object (`res ≠ self`, `res = nextFreshOld`) is the **A-reference** G-AX validates against `IndexVariable.copy`. mapping.md §3.1. |
| A3 | `store := Function.update store r (store self)` (copy the source's payload into the fresh slot) | `self.copy()` copies the source's `dims` into the new object | A-reference + I | `_replace` copies `dims` (mapping.md §2). The slot copy is **I**; that the real copy's `dims` equals the source's at call time (`store res = storeOld self`) is **A-reference** (G-AX). |
| A4 | `nextFresh := nextFresh + 1`; `return r` | return the new object | I | bump the allocation frontier and return the fresh handle (`res = nextFreshOld`). |
| A5 | frame: `store self = storeOld self`, `∀ h ≠ res, store h = storeOld h` | `copy()` does NOT mutate the source or any other live object | A-reference + I | disjoint-slot property of `Function.update` (the fresh `r` aliases nothing live); the real `copy()`'s non-mutation of the source is **A-reference** (G-AX asserts mutating the copy leaves the source's `dims` unchanged). This is the directive-5 `mut`-frame obligation made explicit. |

Discriminating content of the change — the result is a **distinct** object whose
later mutation cannot reach the source — lives in `res ≠ self` together with the
freshness clauses (`res = nextFreshOld`) and the source frame. The pre-patch
`return self` makes the result alias the source; `Solution_prepatch.lean`
reproduces that and **fails** `res ≠ self` (and the unsatisfiable freshness
clauses) — G-DIFF.

## B. The inert hunks (type annotations + private-attribute rename)

The remaining gold hunks carry no behaviour (mapping.md §0) and appear in NO
`ensures`; they are therefore **I** (no-ops under the observable bijection):

| # | patch.diff op | tag | justification |
|---|---|---|---|
| B1 | return-type hints on `to_base_variable`, base `to_index_variable`, `to_index`, `level_names`, `name`, `name.setter`; `NoReturn` import | I | Python does not enforce annotations at runtime; no observable change. Not modeled. |
| B2 | `self.dims` → `self._dims` in `Variable.to_base_variable`/`to_index_variable`; `var: Variable` local annotation in `Dataset.swap_dims` | I | `dims` is a `@property` returning `self._dims` (`variable.py:573`); the read is observationally identical. Behaviour-preserving. |

No separate failing prepatch for site B: it is behaviour-neutral, so a prepatch
keeping the byte-identical spec (G-DIFF) could not distinguish it. Site A's
prepatch already exercises the only observable behaviour the instance fixes.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
returning an independent object rather than an alias — is modeled **deeply**: the
`do` block spells out a fresh allocation + slot copy over an explicit heap
(`Store`, following the Velvet memory-model examples), not hidden behind an axiom
about the function under change. There is **no consumed `copy` axiom**; the only
A rows are **A-reference** (the deep model validated == `IndexVariable.copy` by
G-AX). No `axiom` is shipped.

## D. verify(Solution) ⇒ resolved

`reifyIndependent` verifies only if the result is a distinct, freshly-allocated
handle (A2/A4: `res ≠ self`, `res = nextFreshOld`) carrying a copy of the
source's payload (A3: `store res = storeOld self`) with the source and all other
objects framed (A5). By R (object-identity ↔ `Handle`, `obj.dims` ↔ store slot)
this is exactly `return self.copy()`: a new object equal-in-`dims` to the source
whose later mutation cannot reach it — what the F2P test asserts (`a is not b`;
`b.dims = (...)` leaves `a.dims` unchanged). By G-AX the deep model equals the
real `IndexVariable.copy` (A-reference); by G-CONF the I transliteration of the
`do` block agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: A-reference soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
