# mapping.md — astropy__astropy-8872

## Symbol binding (file:line @ base_commit b750a0e6ee76fb6b8a099a4d16ec51977be46bf6)

The fix edits the constructor of the array subclass that attaches a unit to a
numeric array, in `astropy/units/quantity.py`. The constructor decides, in two
places, whether the element type of the stored array must be coerced to the
default floating type. Both decisions are the subject of this bundle.

| Lean symbol | Python site | location @ base_commit |
|---|---|---|
| `implementation_resolveDtype` | the "by default, cast any integer, boolean, etc., to float" decision applied to a freshly-arrayed value | `astropy/units/quantity.py` `Quantity.__new__`, the `if dtype is None and (...)` block ~L377 |
| `implementation_reuseDtype` | the dtype decision on the fast path that reuses an input already carrying a unit (no `dtype` given) | `astropy/units/quantity.py` `Quantity.__new__`, the `if not (np.can_cast(...) ...)` block ~L296 |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

A numpy `dtype` is modeled by the `DType` structure capturing exactly the three
observations the two code versions read:

| Lean `DType` field | Python `numpy.dtype` observation |
|---|---|
| `kind : Char` | `dt.kind` (`'i'` signed int, `'u'` unsigned int, `'f'` float, `'b'` bool, `'c'` complex, `'O'` object, `'V'` structured/void, `'S'`/`'U'` strings) |
| `canCastFloat32 : Bool` | `numpy.can_cast(numpy.float32, dt)` — whether the type can hold a single-precision float without loss (TRUE for float32/64/128 and complex; FALSE for float16, int, uint, bool) |
| `hasFields : Bool` | `bool(dt.fields)` — whether the dtype is structured |

`floatDType` ≙ the dtype produced by `value.astype(float)` / `dtype=float`,
i.e. `numpy.dtype(float)` = float64: `kind = 'f'`, `canCastFloat32 = true`,
`hasFields = false`.

The modeled result is the *effective dtype* the constructor will store the
array under (`dtype=float` if coerced, else the input dtype). The F2P test
`test_preserve_dtype` observes this through `Quantity(arr, unit).dtype`.

## Callee provenance + flag deps

No unchanged repo callee is consumed as an axiom. The whole coercion decision is
modeled deeply from `dt.kind` (and, for the pre-patch buggy skeletons,
`canCastFloat32` / `hasFields`), so the `axioms` region is empty and
`axiom_check.py` is a skip stub. `np.can_cast` / `dt.fields` / `dt.kind` are
pure numpy dtype observations, modeled as input fields rather than axiomatized
callees.

No flag dependency: `dtype is None` and `copy` are caller preconditions for
reaching each site, recorded as binder hypotheses, not callees to fuzz.

## G-CONF fuzz seed

Pinned seed: `8872`. `conformance_check.py` enumerates the closed set of real
numpy scalar dtypes plus structured dtypes and fuzzes ≥10^5 random
`(kind, canCastFloat32, hasFields)` triples drawn from real dtype observations.
