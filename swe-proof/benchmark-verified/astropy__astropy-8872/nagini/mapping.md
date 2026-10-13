# mapping.md — astropy__astropy-8872

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b750a0e6ee76fb6b8a099a4d16ec51977be46bf6`, states the type
abstraction, and gives the provenance of the deep model that `axiom_check.py`
(G-AX) validates against the real callee.

Repo file under change: `astropy/units/quantity.py`. The changed function is the
`Quantity` constructor `Quantity.__new__` (`astropy/units/quantity.py:272`).
There are two changed hunks, both deciding whether to coerce the input's element
type to the default real type when no explicit element type is requested.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `coerce_homogeneous_input(kind, fits_ref_real32, is_composite)` | the cast-to-float decision in the `isinstance(value, Quantity)` branch of `Quantity.__new__` (`astropy/units/quantity.py:299-301`) | modeled changed function: whether to coerce when the value already carries a unit (a `Quantity`) |
| `coerce_generic_input(kind, fits_ref_real32, is_composite)` | the cast-to-float decision for a plain value (`astropy/units/quantity.py:380-383`) | modeled changed function: whether to coerce when the value has no unit |
| `realizable(kind, fits_ref_real32, is_composite)` *(deep model — A-reference)* | the relationships a real `numpy.dtype` obeys among `dtype.kind`, `np.can_cast(np.float32, dtype)`, and `bool(dtype.fields)` | pure spec: the precondition restricting the input domain to genuine element types; validated against real numpy by axiom_check.py |
| `is_int_like(kind)` | `dtype.kind in 'iu'` | pure spec: the integer / unsigned-integer kinds |
| `KIND_BOOL/INT/UINT/REAL/COMPLEX/OBJECT/COMPOSITE` | the numpy `dtype.kind` tag characters `b i u f c O V` | pure spec: kind tags as code points |

The pre-patch repo predicates the change removes (for the refinement audit, not
referenced from the consumer spec view):

* hunk 1 (`quantity.py:299-301`):
  `if not (np.can_cast(np.float32, value.dtype) or value.dtype.fields): dtype = float`
* hunk 2 (`quantity.py:380-383`):
  `if dtype is None and (not (np.can_cast(np.float32, value.dtype) or value.dtype.fields) or value.dtype.kind == 'O'): value = value.astype(float)`

The post-patch predicates the change introduces:

* hunk 1: `if value.dtype.kind in 'iu': dtype = float`
* hunk 2: `if dtype is None and value.dtype.kind in 'iuO': value = value.astype(float)`

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `numpy.dtype` (the element type of `value`) | three observables `kind: int`, `fits_ref_real32: bool`, `is_composite: bool` | `kind` ↔ `ord(dtype.kind)`; `fits_ref_real32` ↔ `bool(np.can_cast(np.float32, dtype))`; `is_composite` ↔ `bool(dtype.fields)` |
| `dtype.kind` single-character tag | code point of the tag | `'b'`→98, `'i'`→105, `'u'`→117, `'f'`→102, `'c'`→99, `'O'`→79, `'V'`→86 (Nagini bans `str` indexing) |
| `dtype = float` / `value = value.astype(float)` (the coercion that fires) | the `bool` `Result()` of the modeled function (`True` = coerce to the default real type, `False` = preserve) | the patch performs the coercion exactly when the modeled predicate is `True` |
| surrounding control flow (`copy` short-circuit, `dtype is None` guard, `np.array(...)` view) | omitted | unchanged by the patch; not part of the modeled changed behavior. The `dtype is None` guard is the entry condition under which both hunks' decisions are reached; both modeled functions are the decision body under that guard. |

The string element kinds `'S'`/`'U'` and the entry guard `value.dtype.kind in
'OSU'` (the type-validity check at `quantity.py:372-377`, unchanged) are outside
the coercion decision and are not modeled; the F2P/P2P tests reaching this code
construct only numeric / object / composite dtypes.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `coerce_homogeneous_input` / `coerce_generic_input` ↔ the gold predicate
**Callee / operation:** the post-patch decision `value.dtype.kind in 'iu'`
(hunk 1) and `value.dtype.kind in 'iuO'` (hunk 2). There is **no axiomatized
callee**: the changed operation is a pure predicate over the dtype observables
and is modeled **deeply** as the boolean functions `is_int_like(kind)` and
`is_int_like(kind) or kind == KIND_OBJECT()`. The deep model is validated equal
to the real decision out-of-band by `axiom_check.py` (G-AX): for every relevant
real numpy dtype it asserts the model predicate equals `dtype.kind in 'iu'` /
`dtype.kind in 'iuO'`.

### 3.2 `realizable` ↔ real numpy dtype relationships (A-reference)
**Source facts (executed in axiom_check.py against real numpy):**

* `np.can_cast(np.float32, dtype)` (`fits_ref_real32`) is `True` exactly for the
  real kind `'f'` when it is at least 32 bits wide (`float32`, `float64`,
  `float128`), the complex kind `'c'`, and the per-element-object kind `'O'`
  (an object array can hold any Python value). It is `False` for the narrow
  real kind `float16`, and for the integer `'i'`, unsigned `'u'`, boolean `'b'`,
  and composite `'V'` kinds.
* `bool(dtype.fields)` (`is_composite`) is `True` exactly for the structured /
  void kind `'V'`.

`realizable` encodes precisely these relationships, so model.py's precondition
admits every real numpy dtype (axiom_check.py asserts `realizable` holds for
each) and excludes only combinations numpy never produces. The single
behavior-critical fact is that the narrow real kind `float16` has
`fits_ref_real32 == False` while sharing kind `'f'` with the wider reals — this
is exactly the discriminator that distinguishes the gold predicate (kind-only)
from the pre-patch predicate (width-based). The complex kind is included as a
preserved kind; the object kind is included with `fits_ref_real32 == True`
(numpy fact), and is coerced by the generic path only via its explicit kind
membership in hunk 2, not via the width test.

**Soundness check (G-AX):** `axiom_check.py` runs real `numpy` (`np.can_cast`,
`dtype.kind`, `dtype.fields`) on 19 boundary dtypes (bool, all int/uint widths,
float16/32/64 [+128 where present], complex64/128 [+256 where present], object,
multi-field and single-field composite) plus 20 000 fuzzed observable
combinations, asserting (a) `realizable` admits every real dtype, (b) the two
deep-model predicates equal the gold predicate on every dtype, and (c) the
float16 regression is pinned (preserved by the fix, coerced by the pre-patch
predicate). It imports only the standard library plus `numpy` — the very
library the gold patch's predicate reads. Exit 0 iff sound.
