# refinement.md — astropy__astropy-8872

The operation-by-operation correspondence between `model.py`'s implementation
(the two `coerce_*_input` impl regions plus the deep `realizable` / `is_int_like`
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee/operation by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The homogeneous-path site — `coerce_homogeneous_input` (`quantity.py:299-301`)

Gold hunk:
```
- if not (np.can_cast(np.float32, value.dtype) or
-         value.dtype.fields):
+ if value.dtype.kind in 'iu':
      dtype = float
```

| # | model.py impl op (`coerce_homogeneous_input`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `kind: int`, `fits_ref_real32: bool`, `is_composite: bool` | the observables of `value.dtype`: `value.dtype.kind`, `np.can_cast(np.float32, value.dtype)`, `value.dtype.fields` | R | `numpy.dtype` ↔ the three observables (mapping.md §2): `kind == ord(dtype.kind)`, etc. |
| A2 | `return is_int_like(kind)`, i.e. `kind == KIND_INT() or kind == KIND_UINT()` | `value.dtype.kind in 'iu'` (the new post-patch test) | A-reference | the changed predicate is modeled **deeply** as the boolean `is_int_like(kind)`; there is no consumed axiom. G-AX (axiom_check.py) asserts `is_int_like(ord(dtype.kind)) == (dtype.kind in 'iu')` on every real numpy dtype. |
| A3 | `Result() == True` drives the (omitted) coercion `dtype = float` | `dtype = float` | R | the boolean result IS the coercion decision; the patch sets `dtype = float` exactly when the predicate is `True` (mapping.md §2). |

## B. The generic-path site — `coerce_generic_input` (`quantity.py:380-383`)

Gold hunk:
```
- if dtype is None and (not (np.can_cast(np.float32, value.dtype)
-                            or value.dtype.fields)
-                       or value.dtype.kind == 'O'):
+ if dtype is None and value.dtype.kind in 'iuO':
      value = value.astype(float)
```

| # | model.py impl op (`coerce_generic_input`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `kind`, `fits_ref_real32`, `is_composite` | the observables of `value.dtype` | R | as A1. |
| B2 | `return is_int_like(kind) or kind == KIND_OBJECT()` | `value.dtype.kind in 'iuO'` | A-reference | the changed predicate is modeled **deeply**; G-AX asserts `(is_int_like(ord(dtype.kind)) or ord(dtype.kind)==ord('O')) == (dtype.kind in 'iuO')` on every real numpy dtype. The `dtype is None` guard is the unchanged entry condition under which this decision is reached (mapping.md §2); it is identical (I) on both sides and is not part of the changed predicate. |
| B3 | `Result() == True` drives the (omitted) coercion `value = value.astype(float)` | `value = value.astype(float)` | R | the boolean result IS the coercion decision. |

## C. The discriminating change and the prepatch witnesses

The discriminating content of the change — a narrow real kind (`float16`, kind
`'f'`, `fits_ref_real32 == False`) must be **preserved**, whereas the pre-patch
width-based predicate `not (can_cast(float32, dtype) or dtype.fields)` coerced it
— lives in the equality postconditions `Result() == is_int_like(kind)` (site A)
and `Result() == (is_int_like(kind) or kind == KIND_OBJECT())` (site B), grounded
in the input `kind`.

* `model_prepatch.py` reverts site A's impl to the pre-patch predicate
  `not (fits_ref_real32 or is_composite)` and **fails** the postcondition
  `Result() == is_int_like(kind)` — on the realisable witness `kind == KIND_REAL`,
  `fits_ref_real32 == False`, `is_composite == False` (i.e. `float16`), where the
  old predicate yields `True` (coerce) but the spec requires `False` (preserve);
  also on `kind == KIND_BOOL`. This is exactly the spec sensing the change
  (G-DIFF).
* `model_prepatch_2.py` reverts site B's impl to the pre-patch predicate
  `(not (fits_ref_real32 or is_composite)) or kind == KIND_OBJECT()` and **fails**
  the postcondition `Result() == (is_int_like(kind) or kind == KIND_OBJECT())` on
  the same `float16` witness (old → coerce, spec → preserve). The two sites are
  independently fixed and each has its own failing prepatch.

Both prepatches keep the spec region (signatures, `Requires`/`Ensures`, all
pure helpers, the module docstring) byte-identical to `model.py` (G-DIFF
`same_spec`); only their impl regions differ.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The operations that genuinely *changed* —
the two coercion predicates — are modeled **deeply** (the spelled-out boolean
functions `is_int_like` and `is_int_like ∨ object`), validated == the real
post-patch test by G-AX, NOT hidden behind an axiom about the function under
change. There is **no consumed `@ContractOnly` axiom** (the `axioms` region is
empty); consequently there is no A-consumed row. `realizable` is an A-reference:
it encodes the real numpy dtype relationships and is validated against real
numpy by axiom_check.py.

## E. verify(model) ⇒ resolved

`coerce_homogeneous_input` / `coerce_generic_input` verify only if their boolean
output equals the kind-only decision (A2 / B2), for every realisable element
type (the `realizable` domain, A1/B1). By R (dtype ↔ observables; boolean result
↔ the `dtype = float` / `astype(float)` coercion) the verified decisions equal
the post-patch tests `dtype.kind in 'iu'` / `dtype.kind in 'iuO'`; by G-AX the
deep models equal those real tests and `realizable` admits exactly the real
dtypes. The post-patch tests preserve `float16` and `float32` and coerce
integer/object, which is precisely what the F2P `test_preserve_dtype` (extended
to assert `float16` and `float32` are preserved and `Decimal`→object→float is
coerced) demands. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the G-AX-validated deep model
— and the gold patch resolves (G-RESOLVE). The trust points are exactly the two
of PLAN §1.1: refinement fidelity (this document, G-EQ) and the soundness of the
deep model vs. the real operation (G-AX); there are no consumed axioms.
