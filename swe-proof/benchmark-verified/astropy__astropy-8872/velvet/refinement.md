# refinement.md — astropy__astropy-8872

Operation-by-operation correspondence between `Solution.lean`'s two impl regions
(`resolveElemGeneral`, `resolveElemFast`) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — none here),
or **I** (identical concrete op). Every step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The general-path site — `resolveElemGeneral` ↔ `Quantity.__new__` general path

Gold hunk (`astropy/units/quantity.py`, body of `__new__` after `value = np.array(...)`):
```
- if dtype is None and (not (np.can_cast(np.float32, value.dtype)
-                            or value.dtype.fields)
-                       or value.dtype.kind == 'O'):
+ if dtype is None and value.dtype.kind in 'iuO':
      value = value.astype(float)
```

| # | Solution.lean impl op (`resolveElemGeneral`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `input : ElemType` | `value.dtype` of the freshly built array | R | numpy `dtype` ↔ `ElemType` (mapping.md §2). G-CONF bridges via the category bijection. The guard `dtype is None` is the precondition of the modeled branch (an explicitly requested dtype short-circuits this decision); the spec models the `dtype is None` case the F2P test exercises. |
| A2 | dispatch arms `integral`/`object` → `.floatDouble` | `value.dtype.kind in 'iuO'` ⇒ `value.astype(float)` | I | `kind in 'iuO'` selects exactly integral (`'i'`,`'u'`) and boxed-object (`'O'`); `astype(float)` yields float64 ↔ `.floatDouble`. The match arms encode the same selection. |
| A3 | dispatch arms `floatHalf/Single/Double/Extended`, `boolean`, `complexFloat`, `structured` → preserved | the `else` (no `astype`): array kept as built | I | every non-(iuO) kind is preserved at its own dtype ↔ result `= input`. The key behavioral content — `floatHalf` preserved (not widened), `boolean` preserved — lives here. |
| A4 | result `out : ElemType` | the resulting `value.dtype` observed as `q.dtype` | R | the constructor's remaining steps (`view(cls)`, `_set_unit`, unit conversion) do not alter the element-type the F2P test reads via `q.dtype`; identity on `ElemType` (mapping.md §2). |

Discriminating content of the change — a narrow-width float (`floatHalf`) and a
`boolean` are PRESERVED, not converted to `floatDouble` — lives in the
`floatHalf => .floatHalf` / `boolean => .boolean` arms (model) ⇔ the removal of
the `not (np.can_cast(np.float32, value.dtype) or …)` test (real). The pre-patch
predicate was True for `float16` (`np.can_cast(np.float32, float16)` is False, as
float16 is narrower than float32) and for `bool`, wrongly upgrading them to
float64; `Solution_prepatch.lean` reproduces that and **fails** `out =
resultElemGeneral input` on the `floatHalf` and `boolean` clauses (G-DIFF).

## B. The fast-path site — `resolveElemFast` ↔ `Quantity.__new__` already-array path

Gold hunk (`astropy/units/quantity.py`, the `isinstance(value, Quantity)` fast
path with `dtype is None`):
```
- if not (np.can_cast(np.float32, value.dtype) or
-         value.dtype.fields):
+ if value.dtype.kind in 'iu':
      dtype = float
```

| # | Solution.lean impl op (`resolveElemFast`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `input : ElemType` | `value.dtype` of the already-built array on the fast path | R | same dtype ↔ `ElemType` bijection (mapping.md §2). Reached under `dtype is None` (the `if dtype is None:` guard above the hunk). |
| B2 | dispatch arm `integral` → `.floatDouble` | `value.dtype.kind in 'iu'` ⇒ `dtype = float` | I | `kind in 'iu'` selects exactly integral; an object kind cannot arise on this already-array path (mapping.md §1), so it is preserved like any other non-integral kind. |
| B3 | dispatch arms `floatHalf/Single/Double/Extended`, `boolean`, `complexFloat`, `object`, `structured` → preserved | the `else` (no `dtype = float`) | I | every non-integral kind preserved at its own dtype ↔ result `= input`. `floatHalf` and `boolean` preserved here is the behavioral content. |
| B4 | result `out : ElemType` | resulting `q.dtype` of the fast-path array | R | downstream `np.array(value, dtype=dtype, …)` builds with the resolved dtype; identity on `ElemType` for the element-type the F2P test reads (mapping.md §2). |

Discriminating content — `floatHalf` preserved (not widened) and `boolean`
preserved — lives in the `floatHalf => .floatHalf` / `boolean => .boolean` arms ⇔
the removal of the `not (np.can_cast(np.float32, value.dtype) or …)` test.
`Solution_prepatch_fast.lean` reproduces the pre-patch predicate and **fails**
`out = resultElemFast input` on the `floatHalf` and `boolean` clauses (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps, no axioms

Every step is R or I. The operation that genuinely *changed* — the boolean test
selecting the resulting element-type — is modeled **deeply** (the spelled-out
categorical dispatch over `ElemType`), not behind an axiom. There is no consumed
axiom and no A-reference deep model of a foreign callee: the decision is computed
solely from the input element-type (mapping.md §3). `np.can_cast`/`dtype.kind`
are numpy metadata reads, not borrowed-behavior callees; the spec encodes the
post-patch decision directly and G-CONF differential-tests it against the real
numpy-dtype predicate.

## D. verify(Solution) ⇒ resolved

`resolveElemGeneral`/`resolveElemFast` verify only if the resulting element-type
is the exact post-patch categorical decision: `floatHalf`/`boolean`/all float
widths preserved (A3/B3), integral→float and (general) object→float (A2/B2). By R
(`dtype ↔ ElemType`, the constructor's element-type-preserving continuation) the
verified decisions equal the patched `Quantity.__new__` dtype resolution on the
tested inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs. The F2P test `test_preserve_dtype` constructs
`u.Quantity(np.array([1.,2.], dtype=np.float16), u.yr)` and asserts the result
`dtype == float16`: this hits the general path (the input is a plain ndarray, not
a Quantity), where the spec's `floatHalf => .floatHalf` arm (A3) is exactly what
preserves it. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The one trust point (plan §1.1) is refinement fidelity (this doc,
G-EQ + G-CONF); there are no axioms to trust (G-AX skip).
