# mapping.md — astropy__astropy-8872

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b750a0e6ee76fb6b8a099a4d16ec51977be46bf6`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `astropy/units/quantity.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveElemGeneral (input : ElemType)` | the default element-type decision in the GENERAL construction path of `Quantity.__new__` — `astropy/units/quantity.py:378-380` (the `if dtype is None and …: value = value.astype(float)` block following `value = np.array(...)`) | modeled changed function (site 2) |
| `resolveElemFast (input : ElemType)` | the default element-type decision in the FAST path taken when the input is already an array of the target kind — `astropy/units/quantity.py:298-300` (the `if not (np.can_cast(...) or …): dtype = float` block, post-patch `if value.dtype.kind in 'iu': dtype = float`) | modeled changed function (site 1) |
| `castsToFloatGeneral` / `castsToFloatFast` | the boolean predicate each site computes to decide conversion | pure spec: per-site conversion test |
| `resultElemGeneral` / `resultElemFast` | the resulting array element-type after the (possible) `astype(float)` | pure spec: resulting element-type |
| `ElemType` | a numpy array's element-type (`numpy.dtype`), reduced to the decision-relevant categories | the modeled value carrier |

The two sites are independent branches of the same constructor: site 1 (fast)
handles an input that is already an array of the target kind; site 2 (general)
handles an arbitrary input freshly turned into an array. Each is reverted in its
own `Solution_prepatch*.lean` (G-DIFF: two independently-observable fixed
behaviors).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a numpy `dtype` of an array offered for construction | `ElemType` | each `ElemType` constructor ↔ one numpy-`dtype` category, by `(dtype.kind, fields, width)`: `boolean ↔ kind 'b'`; `integral ↔ kind 'i' or 'u'`; `floatHalf/Single/Double/Extended ↔ kind 'f'` at width 16/32/64/>64 bits; `complexFloat ↔ kind 'c'`; `object ↔ kind 'O'`; `structured ↔ dtype.fields is truthy` (kind 'V' record). The representatives used by G-CONF: `float16/float32/float64/longdouble`, `bool_`, `int64`, `complex128`, `object_`, a 2-field record dtype. |
| the resulting element-type `q.dtype` | `ElemType` | same bijection; `.astype(float)` ↔ result `floatDouble` (the default real floating element-type is `np.dtype(float)` = float64). |
| `value.astype(float)` (conversion applied) | result `= defaultFloat` (`.floatDouble`) | converting any input lands on the double-width real floating element-type. |
| no conversion (`dtype` stays `None`, array kept) | result `= input` | the input element-type is preserved verbatim, including its width. |

The decision reacts ONLY to the input dtype's `kind`, its `fields`, and (in the
pre-patch predicate `np.can_cast(np.float32, dtype)`) its float WIDTH — exactly
the distinctions `ElemType` keeps apart. Real floating widths are split because
width is what the pre-patch predicate wrongly let drive conversion; the fix makes
width irrelevant for floats. `np.can_cast(np.float32, dtype)` is True iff `dtype`
is a float (or wider numeric) that can hold a float32 losslessly — False for
`float16` (narrower), which is why the pre-patch upgraded `float16` to `float64`.

## 3. Callee provenance (kind-A)

**None.** The modeled behavior is a pure categorical decision over the input
array's element-type, computed entirely from that element-type (the read-only
input). The surrounding constructor machinery — `np.array(value, dtype=…)`,
`value.astype(float)`, `value.view(cls)`, `_set_unit`, the units conversion — is
an UNCHANGED shared continuation reached identically whether or not conversion
fires; the patch changes only the boolean test that selects the element-type, not
that machinery. So there is **no consumed `axiom`** and **no A-reference deep
model** of a foreign callee. The decision is grounded in the input (directive 8):
the result element-type is a function of the input element-type alone, not an
opaque oracle. Therefore `axiom_check.py` is omitted and **G-AX is `skip`** (the
no-axiom-bundle convention; cf. `tasks/astropy__astropy-13236`).

`np.can_cast` / `dtype.kind` / `dtype.fields` are reads of numpy dtype metadata,
not callees with behavior the spec borrows; the spec encodes the post-patch
decision (`kind in 'iu'` / `kind in 'iuO'`) directly and G-CONF differential-tests
it against the real numpy-dtype predicate.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8872`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`resolveElemGeneral`/`resolveElemFast` (the categorical dispatch) to Python and
drives the patched dtype-resolution predicate (`kind in 'iu'` / `'iuO'`) on the
real numpy dtypes the bijection in §2 selects. All ops are R/I-tagged; there is
no A-tagged callee to leave as a real callee (§3), so the shadow is pure R/I.
