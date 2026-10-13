# refinement.md — astropy__astropy-8872

Two changed decision sites in `Quantity.__new__`, one Lean triple each. Tags:
**R** type-refinement, **A-consumed** proof uses axiom, **A-reference** deep model
validated == real callee, **I** identical concrete op.

## Site 1 — `implementation_resolveDtype` ↔ general-path coercion (~L377)

patch.diff hunk:
```
-        if dtype is None and (not (np.can_cast(np.float32, value.dtype)
-                                   or value.dtype.fields)
-                              or value.dtype.kind == 'O'):
+        if dtype is None and value.dtype.kind in 'iuO':
             value = value.astype(float)
```

| Lean impl op | patch.diff counterpart | tag |
|---|---|---|
| `let mut result := dt` | the stored value keeps its input dtype unless reassigned | I |
| `if promoteGeneral dt` i.e. `dt.kind = 'i' \|\| dt.kind = 'u' \|\| dt.kind = 'O'` | `value.dtype.kind in 'iuO'` (the new post-patch condition) | R (`'i'/'u'/'O'` chars ↔ numpy `kind` codes; `DType.kind` ≙ `dt.kind`) |
| `result := floatDType` | `value = value.astype(float)` → effective dtype `numpy.dtype(float)` | R (`floatDType` ↔ float64 dtype) |
| `return result` | the dtype the array is finally stored under | I |

The `dtype is None` guard is a binder precondition (the caller reaches this op
only when no explicit dtype was requested); it is not an impl op. No
changed-inexpressible op: the entire decision reduces to the input `kind`.

## Site 2 — `implementation_reuseDtype` ↔ fast-reuse coercion (~L296)

patch.diff hunk:
```
-                if not (np.can_cast(np.float32, value.dtype) or
-                        value.dtype.fields):
+                if value.dtype.kind in 'iu':
                     dtype = float
```

| Lean impl op | patch.diff counterpart | tag |
|---|---|---|
| `let mut result := dt` | reused input keeps its dtype unless `dtype` is set to `float` | I |
| `if promoteReuse dt` i.e. `dt.kind = 'i' \|\| dt.kind = 'u'` | `value.dtype.kind in 'iu'` (the new post-patch condition) | R |
| `result := floatDType` | `dtype = float` → array materialised as float64 | R |
| `return result` | the dtype the reused array is stored under | I |

This path differs from site 1 only by omitting the `'O'` (generic-object)
branch, mirrored exactly by `promoteReuse` omitting `dt.kind = 'O'`.

## Axioms

None. The coercion decision is modeled deeply from the element-type category, so
there is no consumed axiom and no A-reference callee. `axiom_check.py` is a skip
stub; `conformance_check.py` differential-tests both R/I legs (no A legs), so
`conf_skip = false`.

## How the spec sees the bug (G-DIFF)

The discriminating input is a lower-precision floating type (`kind = 'f'`,
`canHoldSingle = false`, modeling `numpy.float16`). The spec keeps it unchanged
(`promoteGeneral` / `promoteReuse` test only `kind`); the pre-patch skeletons
promote it (their gate fires when the type cannot hold a single-precision float),
so each prepatch's carried gold proof fails to close — exactly the
`test_preserve_dtype` float16 assertion added by the test patch.
