# mapping.md — pydata__xarray-4966

## Symbol binding (file:line @ base_commit 37522e991a32ee3c0ad1a5ff8afe8e3eb1885550)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_unsignedDecode` / `problem_spec_unsignedDecode` / `correct_unsignedDecode` | `UnsignedIntegerCoder.decode` (the integer-reinterpretation it performs) | `xarray/coding/variables.py:305-327` |
| `decodeModel` (pure helper) | the body that decides the output array / dtype / fill value from the `_Unsigned` attribute and the array's integer kind | `variables.py:308-327` |
| `Kind` (pure helper) | `data.dtype.kind` restricted to the integer cases the routine distinguishes (`"i"` signed, `"u"` unsigned, anything else) | `variables.py:311,319` |
| `reinterpAsUnsigned` / `reinterpAsSigned` (pure helpers) | `np.asarray(dtype=unsigned_dtype/signed_dtype)` element-wise cast applied by `lazy_elemwise_func`, and the matching `_FillValue` cast | `variables.py:313-318, 320-326` (post-patch) |
| `DecodeInput.itemsize` | `data.dtype.itemsize` (bytes) → `bits = 8 * itemsize` | `variables.py:313,320` |

## What the function does (base_commit)

`UnsignedIntegerCoder.decode` unpacks `(dims, data, attrs, encoding)` and, when the
variable carries an `_Unsigned` attribute, may reinterpret the integer array
between signed and unsigned two's-complement representations of the same byte
width:

```python
if "_Unsigned" in attrs:
    unsigned = pop_to(attrs, encoding, "_Unsigned")          # moves _Unsigned attr->encoding
    if data.dtype.kind == "i":                               # array stored as signed
        if unsigned == "true":                               # ...but means unsigned
            unsigned_dtype = np.dtype("u%s" % data.dtype.itemsize)
            transform = partial(np.asarray, dtype=unsigned_dtype)
            data = lazy_elemwise_func(data, transform, unsigned_dtype)
            if "_FillValue" in attrs:
                attrs["_FillValue"] = unsigned_dtype.type(attrs["_FillValue"])
    # === base_commit STOPS HERE: an unsigned-kind array is NOT reinterpreted ===
    else:
        warnings.warn("variable %r has _Unsigned attribute but is not of integer type ...")
return Variable(dims, data, attrs, encoding)
```

The POST-PATCH routine adds the missing symmetric case: when the array is stored
as unsigned (`data.dtype.kind == "u"`) but the attribute declares `_Unsigned ==
"false"` (the array actually holds signed values), reinterpret it as the signed
dtype of the same itemsize (and convert any `_FillValue` the same way):

```python
    elif data.dtype.kind == "u":
        if unsigned == "false":
            signed_dtype = np.dtype("i%s" % data.dtype.itemsize)
            transform = partial(np.asarray, dtype=signed_dtype)
            data = lazy_elemwise_func(data, transform, signed_dtype)
            if "_FillValue" in attrs:
                attrs["_FillValue"] = signed_dtype.type(attrs["_FillValue"])
```

`np.asarray(arr_uN, dtype="iN")` is a same-width two's-complement reinterpretation:
for `bits = 8*itemsize` and `m = 2**bits`, an unsigned value `x ∈ [0, m)` maps to
`x - m` when `x ≥ m/2`, else `x` (e.g. `u1` `255 → -1`, `128 → -128`, `127 → 127`).
The existing signed→unsigned cast is the inverse (`x mod m`, e.g. `i1` `-1 → 255`).

The FAIL_TO_PASS tests (`test_decode_signed_from_unsigned[1,2,4,8]`) build a
`u{bits}` array whose single element is `(-1).astype(u{bits})` (i.e. `2**bits - 1`)
with `attrs={"_Unsigned": "false"}`, decode it, and assert the result dtype is
`i{bits}` and the value is `-1`. PASS_TO_PASS keeps the signed→unsigned direction
(`test_decode_unsigned_from_signed`).

## Lean modeling

- `DecodeInput` records the observable inputs the decision reads: `data : List Int`
  (the integer array values), `kind : Kind` (`data.dtype.kind`: `.signed`/`.unsigned`/
  `.other`), `itemsize : Nat` (`data.dtype.itemsize` in bytes), `fill : Option Int`
  (the `_FillValue` attribute, `none` when absent), `unsignedAttr : Option String`
  (the `_Unsigned` attribute value, `none` when the attribute is absent).
- `DecodeResult` records the touched output components: `data`, `kind`, `itemsize`,
  `fill`. Frame discipline: the impl pins every one of them. The output `itemsize`
  always equals the input (the cast preserves byte width); the `kind` flips only in
  the two reinterpreting branches; `data`/`fill` are mapped only there. The
  Variable's `dims`/`encoding`/other-attrs are untouched passthrough (identity),
  outside the modeled carrier — the patch never reads or writes them.
- `reinterpAsUnsigned bits x = x % 2^bits` and
  `reinterpAsSigned bits x = let r := x % 2^bits; if 2*r ≥ 2^bits then r - 2^bits else r`
  are exact arithmetic models of the two same-width casts (`%` is Lean's
  `Int.emod`, non-negative for a positive modulus).
- `decodeModel` is the post-patch decision (nested `match`/`if` over `unsignedAttr`
  then `kind`); `implementation_unsignedDecode` is the `Id.run do` skeleton mirroring
  it with early `return`s. The pre-patch impl drops the unsigned→signed branch
  (returns the unsigned array unchanged when `kind = .unsigned`), exactly the
  base_commit behavior.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| integer array values `data` | `data : List Int` | element-wise identity (each int = its numpy value) |
| `data.dtype.kind` | `kind : Kind` | `"i" ↔ .signed`, `"u" ↔ .unsigned`, else `↔ .other` |
| `data.dtype.itemsize` (bytes) | `itemsize : Nat` | identity; `bits = 8 * itemsize` |
| `attrs.get("_FillValue")` | `fill : Option Int` | present↔`some`, absent↔`none` |
| `attrs.get("_Unsigned")` | `unsignedAttr : Option String` | present↔`some <value>`, absent↔`none` |
| `np.asarray(arr, "uN")` / `unsigned_dtype.type(f)` | `reinterpAsUnsigned (8*itemsize)` | `x ↦ x mod 2^bits` |
| `np.asarray(arr, "iN")` / `signed_dtype.type(f)` | `reinterpAsSigned (8*itemsize)` | `x ↦ x - 2^bits if x ≥ 2^(bits-1) else x` |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The only behavior the patch changes
  — the two's-complement reinterpretation of the integer array and its fill value —
  is modeled DEEPLY as exact `Int` arithmetic (`reinterpAsSigned` / `reinterpAsUnsigned`);
  SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op. So the `axioms`
  region is empty and **G-AX skips**.
- `pop_to(attrs, encoding, "_Unsigned")` runs unconditionally inside the
  `"_Unsigned" in attrs` guard and only moves the attribute from `attrs` to
  `encoding`; it does not affect the modeled data/dtype/fill outputs, so it is folded
  into the `unsignedAttr = some _` case and not separately modeled.
- `lazy_elemwise_func(data, transform, dtype)` is a lazy element-wise `map` of the
  cast over the array — modeled as `List.map` of the reinterpret function. Its laziness
  is irrelevant to the observable values.
- **Flag dependency:** the reinterpretation fires only on the conjunction
  (`kind = .unsigned` ∧ `unsignedAttr = some "false"`) for the new branch, and
  (`kind = .signed` ∧ `unsignedAttr = some "true"`) for the existing one. G-CONF
  fuzzes all `(kind, unsignedAttr)` combinations and itemsizes.

## G-CONF fuzz seed

Pinned seed: **4966** (see `conformance_check.py` `SEED`). The oracle is the real
`np.asarray`/`np.dtype` cast driven over fuzzed `(values, kind, itemsize,
unsigned-attr, fill)` tuples; the shadow is the op-for-op transliteration of
`implementation_unsignedDecode`. Edge cases pin the F2P scenario (`u{bits}` max
value with `_Unsigned="false"` → `i{bits}` value `-1`) and the PASS_TO_PASS
direction.
