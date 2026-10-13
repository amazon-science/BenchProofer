# mapping.md — pydata__xarray-4966

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 37522e991a32ee3c0ad1a5ff8afe8e3eb1885550`, states the type
abstraction, and gives the provenance of each axiomatized callee.

Repo file under change: `xarray/coding/variables.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `decode_unsigned_attr(data, kind, unsigned, modulus, has_fill, fill)` | `UnsignedIntegerCoder.decode` — `xarray/coding/variables.py:305` (dispatch body lines 308-325) | the modeled changed method (integer (un)signed reinterpretation governed by the `_Unsigned` attribute) |
| `reinterpret(v, modulus, to_signed)` *(deep model — A-reference)* | the element-wise transform `np.asarray(data, dtype=…)` executed lazily through `lazy_elemwise_func(data, partial(np.asarray, dtype=target_dtype), target_dtype)` — `variables.py:314-315` (existing `i→u` branch) and `:319-320` (new `u→i` branch) | pure spec: the two's-complement reinterpretation of one fixed-width integer between the unsigned and signed views of the same bit pattern; the deep model of the unchanged callee `numpy.asarray`, validated `reinterpret == np.asarray(dtype=…)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `convert_fill(fill, modulus, to_signed)` | `new_fill = target_dtype.type(attrs["_FillValue"])` — `variables.py:316-318` (`i→u`) and the symmetric `:321-323` (`u→i`) added by the fix | pure spec: the same fixed-width reinterpretation applied to the scalar fill value |
| `KIND_SIGNED (0) / KIND_UNSIGNED (1)` | `data.dtype.kind == "i"` / `== "u"` (`variables.py:311`, new `:319`) | the storage signedness of the incoming integer array |
| `ATTR_FALSE (0) / ATTR_TRUE (1) / ATTR_OTHER (2)` | the popped `_Unsigned` attribute string `unsigned == "true"` / `== "false"` / neither (`variables.py:312`, new `:320`) | the requested target signedness encoded by the CF `_Unsigned` attribute |

The pre-patch repo behaviour the change adds to (for the refinement audit, not
referenced from the consumer spec view): at base_commit the method handles only
`data.dtype.kind == "i"` (`variables.py:311`); an unsigned-kind array
(`kind == "u"`) falls through to the `else` branch (`:319-325`), which emits a
`SerializationWarning` and applies **no** transform — leaving the unsigned bit
pattern unchanged. The fix inserts an `elif data.dtype.kind == "u":` branch that,
when `unsigned == "false"`, reinterprets the data (and any `_FillValue`) as the
signed view of the same width.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a fixed-width integer numpy array `data` (`dtype.kind ∈ {"i","u"}`, `dtype.itemsize == bits/8`) | `List[int]` of the per-element integer *values* (for `kind=="u"` each value lies in `[0, modulus)`, for `kind=="i"` in `[-modulus/2, modulus/2)`) | `data[k]` ↔ the integer value of element `k`; `len(data)` ↔ the number of elements; element order preserved |
| the result array of `decode` (`Variable(dims, data, …).values`) | `List[int]` of the transformed per-element values | element-wise correspondence |
| `data.dtype.itemsize` (1,2,4,8 bytes ⇒ 8,16,32,64 bits) | `modulus == 2**bits` (256, 65536, …) | `modulus` is the two's-complement wrap modulus for that width |
| `data.dtype.kind` (`"i"`/`"u"`) | `kind ∈ {0,1}` | `"i"` ↔ 0 (signed), `"u"` ↔ 1 (unsigned) |
| `unsigned = pop_to(attrs, encoding, "_Unsigned")` string `"true"`/`"false"`/other | `unsigned ∈ {0,1,2}` | `"false"` ↔ 0, `"true"` ↔ 1, anything else / unequal ↔ 2 |
| `attrs["_FillValue"]` scalar (present or not) | `has_fill: bool` + `fill: int` | `has_fill` ↔ `"_FillValue" in attrs`; `fill` ↔ its integer value |
| `lazy_elemwise_func(data, transform, target_dtype)` lazy wrapper | identity on the materialised element values (omitted) | the wrapper only defers the element-wise `func`; on materialisation `.values == func(data)` element-wise (`variables.py:69` `__array__` returns `self.func(self.array)`); the F2P tests read `decoded.values`, observing exactly the transformed elements |
| `Variable(dims, data, attrs, encoding)` constructor | identity on the data values + the (possibly converted) fill (omitted) | the F2P tests observe `decoded.dtype` and `decoded.values`; `dtype` is the target width/signedness pinned by `kind`+`unsigned`, `values` are the transformed elements |

numpy integer dtypes never overflow into Python bignums here — the test inputs
and reinterpretation stay within the fixed width — so modelling the per-element
*value* as an unbounded `int` constrained to the width's range is exact on the
tested domain.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reinterpret` / `convert_fill` deep model ↔ `numpy.asarray(dtype=…)` (A-reference)
**Callee:** `numpy.asarray(x, dtype=target_dtype)` (and the scalar form
`target_dtype.type(x)`), where `target_dtype` is the same-width opposite-sign
integer dtype (`np.dtype("i%s" % itemsize)` for the new `u→i` branch,
`np.dtype("u%s" % itemsize)` for the existing `i→u` branch). The changed
element transform is modelled **deeply** by the `@Pure` function `reinterpret`
in the `pure` region; there is **no `asarray` axiom** the proof consumes. The
deep model is validated equal to the real callee out-of-band by axiom_check.py
(G-AX).

numpy reinterprets a fixed-width integer between its signed and unsigned views
by preserving the bit pattern, i.e. by reduction modulo `2**bits`:

  * unsigned `v ∈ [0, 2**bits)` → signed: `v` if `v < 2**(bits-1)` else `v - 2**bits`
  * signed `v ∈ [-2**(bits-1), 2**(bits-1))` → unsigned: `v` if `v ≥ 0` else `v + 2**bits`

Both directions are `((v + 2**(bits-1)) mod 2**bits) - 2**(bits-1)` for the
signed view and `v mod 2**bits` for the unsigned view — exactly what
`reinterpret(v, modulus, to_signed)` encodes. G-AX asserts
`reinterpret(v, 2**bits, …) == np.asarray([v], dtype=target_dtype)[0]` over the
full small-width domains and randomized wide-width fuzz, in both directions,
plus the scalar `target_dtype.type(fill)` form for `convert_fill`. Docs:
https://numpy.org/doc/stable/reference/generated/numpy.asarray.html and the
fixed-width integer wrap-around rules
(https://numpy.org/doc/stable/reference/arrays.scalars.html). This is the single
behavioural change the F2P `test_decode_signed_from_unsigned` observes: an
unsigned-kind array with `_Unsigned == "false"` decodes to the signed view
(`255 → -1`, …, `iinfo.max → -1`), whereas pre-patch it was left unsigned.

There are **no consumed (`@ContractOnly`) axioms** in this bundle: the only
opaque callee (`numpy.asarray`/`dtype.type`) is the *changed* element transform,
which is therefore modelled deeply (A-reference) rather than axiomatized, per
SPEC_GUIDE §3. `lazy_elemwise_func`, `Variable`, and `pop_to` are pure
plumbing/identities on the observed element values (§2), not contracted callees.

**Soundness check (G-AX):** `axiom_check.py` runs the real `numpy.asarray` /
`np.dtype(...).type` on (a) the exhaustive value domain for widths 8 and 16 bits
in both directions, (b) boundary values (`0`, `max`, `min`, `2**(bits-1)`,
`2**(bits-1)-1`, `-1`) for widths 8/16/32/64, and (c) randomized fuzz across all
four widths, asserting every observation equals the deep model `reinterpret` /
`convert_fill`. It imports only `numpy` (the very module the patch calls);
nothing repo-specific. Exit 0 iff sound.
