# refinement.md — pydata__xarray-4966

Maps every operation in `implementation_unsignedDecode` to its `patch.diff`
counterpart in `xarray/coding/variables.py::UnsignedIntegerCoder.decode` (see
mapping.md). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (post-patch `UnsignedIntegerCoder.decode`, the integer-reinterpretation)
```python
if "_Unsigned" in attrs:
    unsigned = pop_to(attrs, encoding, "_Unsigned")
    if data.dtype.kind == "i":
        if unsigned == "true":
            unsigned_dtype = np.dtype("u%s" % data.dtype.itemsize)
            transform = partial(np.asarray, dtype=unsigned_dtype)
            data = lazy_elemwise_func(data, transform, unsigned_dtype)
            if "_FillValue" in attrs:
                attrs["_FillValue"] = unsigned_dtype.type(attrs["_FillValue"])
    elif data.dtype.kind == "u":                      # <-- ADDED by the fix
        if unsigned == "false":
            signed_dtype = np.dtype("i%s" % data.dtype.itemsize)
            transform = partial(np.asarray, dtype=signed_dtype)
            data = lazy_elemwise_func(data, transform, signed_dtype)
            if "_FillValue" in attrs:
                attrs["_FillValue"] = signed_dtype.type(attrs["_FillValue"])
    else:
        warnings.warn(... "not of integer type. Ignoring attribute." ...)
return Variable(dims, data, attrs, encoding)
```

## Operation correspondence
| # | Lean op (`implementation_unsignedDecode`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut data := inp.data` / `let mut kind := inp.kind` / `let mut fill := inp.fill` | `dims, data, attrs, encoding = unpack_for_decoding(variable)`; the mutable `data`, dtype, and `attrs["_FillValue"]` | I | initialize the touched output components to their input values. |
| 2 | `match inp.unsignedAttr with \| none => return …` | `if "_Unsigned" in attrs:` (the `none` branch = attribute absent, pass through) | R | `"_Unsigned" in attrs ↔ unsignedAttr = some _`; absent ↔ `none`. Frame: all output components pinned to input. |
| 3 | `some u => if kind = Kind.signed then …` | `unsigned = pop_to(...)` then `if data.dtype.kind == "i":` | R | `pop_to` only relocates the attribute (attrs→encoding) and yields its string value `u`; `data.dtype.kind == "i" ↔ kind = .signed`. (`pop_to` does not touch data/dtype/fill — folded into the `some u` case.) |
| 4 | `if u = "true" then data := data.map (reinterpAsUnsigned bits); kind := .unsigned; fill := fill.map (reinterpAsUnsigned bits)` | `if unsigned == "true": … np.asarray(dtype="u%s"%itemsize) via lazy_elemwise_func; attrs["_FillValue"] = unsigned_dtype.type(...)` | A-reference | `np.asarray(arr, "uN")` / `uN.type(f)` modeled DEEPLY as the exact same-width wrap `reinterpAsUnsigned (8*itemsize) x = x % 2^bits`; `lazy_elemwise_func ≡ List.map`. Validated == real cast by G-CONF (the impl is concrete arithmetic, no `opaque` callee ⇒ no consumed axiom). |
| 5 | `else if kind = Kind.unsigned then if u = "false" then data := data.map (reinterpAsSigned bits); kind := .signed; fill := fill.map (reinterpAsSigned bits)` | `elif data.dtype.kind == "u": if unsigned == "false": … np.asarray(dtype="i%s"%itemsize); attrs["_FillValue"] = signed_dtype.type(...)` | A-reference | THE FIX. `data.dtype.kind == "u" ↔ kind = .unsigned`; `np.asarray(arr, "iN")` / `iN.type(f)` modeled DEEPLY as two's-complement `reinterpAsSigned (8*itemsize) x = (let r=x%2^bits; if 2*r≥2^bits then r-2^bits else r)`. Validated == real cast by G-CONF. |
| 6 | (no further branch; `Kind.other` falls through unchanged) | `else: warnings.warn(...)` (non-integer kind: attribute ignored, data unchanged) | R | the warning is a side effect with no observable effect on the modeled output components; modeled as the pass-through `.other` case. |
| 7 | `return { data, kind, itemsize := inp.itemsize, fill }` | `return Variable(dims, data, attrs, encoding)` | I | `itemsize` (byte width) is preserved by every cast (`uN`/`iN` have the same `itemsize`), pinned to the input; `dims`/`encoding`/other-attrs are untouched passthrough outside the modeled carrier. |

Every op is R, I, or **A-reference** (deep-modeled changed cast). There is **no
consumed callee axiom** and **no `opaque` callee** in `Solution.lean`: SPEC_GUIDE
§3 forbids axiomatizing a deeply-modeled changed op, and the casts are the op the
patch changes. Therefore `meta.json axioms = []`; `deep_model_references` records
the two A-reference casts; `axiom_check.py` is a skip stub.

## R/A-reference legs ⇒ G-CONF
The whole impl is R / I / A-reference (all concrete arithmetic — no axiom gates
it), so `conformance_check.py` mechanically differential-tests the impl shadow
against the REAL patched `UnsignedIntegerCoder.decode` over ≥10⁵ fuzzed inputs.
`conf_skip = false`.

## How the prepatch encodes the bug
`Solution_prepatch.lean` drops op #5 entirely: when `kind = .unsigned` there is
no branch, so an array stored as unsigned with `_Unsigned = "false"` is returned
**unchanged** (still unsigned, value `2^bits-1` rather than `-1`). This is exactly
the `base_commit` behavior the FAIL_TO_PASS tests
(`test_decode_signed_from_unsigned[1,2,4,8]`) expose: a `u{bits}` array holding
`(-1).astype(u{bits}) = 2^bits-1` with `_Unsigned="false"` must decode to dtype
`i{bits}` value `-1`. The prepatch cannot satisfy `problem_spec_unsignedDecode`
on the `.unsigned ∧ u="false"` clause (result kind must flip to `.signed` and the
value must be reinterpreted), so `correct_unsignedDecode` is unclosable ⇒ G-DIFF
fails as required. PASS_TO_PASS (`test_decode_unsigned_from_signed`) exercises the
unchanged op #4 direction, which the prepatch keeps.
