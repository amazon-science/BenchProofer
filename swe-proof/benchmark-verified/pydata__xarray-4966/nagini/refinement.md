# refinement.md — pydata__xarray-4966

The operation-by-operation correspondence between `model.py`'s implementation
(the `decode_unsigned_attr` impl region, the deep `reinterpret`/`reinterpret_seq`
model, and the dispatch predicates) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE).

## A. The decode site — `UnsignedIntegerCoder.decode` (`xarray/coding/variables.py:305`)

Gold hunk (the inserted `elif` branch):
```
                     if "_FillValue" in attrs:
                         new_fill = unsigned_dtype.type(attrs["_FillValue"])
                         attrs["_FillValue"] = new_fill
+            elif data.dtype.kind == "u":
+                if unsigned == "false":
+                    signed_dtype = np.dtype("i%s" % data.dtype.itemsize)
+                    transform = partial(np.asarray, dtype=signed_dtype)
+                    data = lazy_elemwise_func(data, transform, signed_dtype)
+                    if "_FillValue" in attrs:
+                        new_fill = signed_dtype.type(attrs["_FillValue"])
+                        attrs["_FillValue"] = new_fill
             else:
                 warnings.warn(...)
```

| # | model.py impl op (`decode_unsigned_attr`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `data: List[int]` | `data` array of `variable` (`unpack_for_decoding`) | R | a fixed-width integer numpy array ↔ `List[int]` of per-element integer *values* (mapping.md §2). |
| A2 | `kind ∈ {KIND_SIGNED(0), KIND_UNSIGNED(1)}` | `data.dtype.kind == "i"` / `== "u"` (`:311`, new `:319`) | R | the storage signedness as a two-valued code; the F2P inputs are integer arrays so `kind ∈ {"i","u"}` (mapping.md §2). |
| A3 | `unsigned ∈ {ATTR_FALSE(0), ATTR_TRUE(1), ATTR_OTHER(2)}` | `unsigned = pop_to(attrs, encoding, "_Unsigned")` compared `== "true"` / `== "false"` (`:312`, new `:320`) | R | the popped attribute string as a three-valued code (`"false"`/`"true"`/neither); mapping.md §2. |
| A4 | `modulus == 2**bits` | `data.dtype.itemsize` (1/2/4/8 → 8/16/32/64 bits) feeding `"i%s" % data.dtype.itemsize` / `"u%s" % …` | R | the dtype width that fixes the wrap modulus of the reinterpretation (mapping.md §2). |
| A5 | dispatch `if transform_to_signed(kind, unsigned)` = `kind==1 and unsigned==0` | the inserted `elif data.dtype.kind == "u": if unsigned == "false":` | I | identical two-way integer/equality dispatch (the new branch). |
| A6 | dispatch `elif transform_to_unsigned(kind, unsigned)` = `kind==0 and unsigned==1` | the existing `if data.dtype.kind == "i": if unsigned == "true":` (`:311-312`) | I | identical dispatch (the pre-existing branch). |
| A7 | the transformed elements are `reinterpret_seq(ToSeq(data), modulus, True)` (signed view) / `…, False` (unsigned view), each element `reinterpret(v, modulus, …)` | `data = lazy_elemwise_func(data, partial(np.asarray, dtype=signed_dtype), signed_dtype)` (new) / `…, unsigned_dtype` (existing) | A-reference | the changed element transform is modelled **deeply**: `reinterpret`/`reinterpret_seq` (the spelled-out fixed-width two's-complement fold in the `pure` region) and the verified loops in `decode_unsigned_attr` ARE the reinterpretation. There is **no consumed `asarray` axiom** — the proof depends on none. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `numpy.asarray(dtype=…)` over exhaustive 8/16-bit domains + boundaries + 80k fuzz in both directions and asserts it equals `reinterpret`. `lazy_elemwise_func` only defers `np.asarray` element-wise (its `__array__` returns `func(array)`, `variables.py:69`); on the `decoded.values` the F2P test reads, the materialised elements are exactly `np.asarray(data, dtype=target)` element-wise (mapping.md §2, §3.1). |
| A8 | `fill_out(kind, unsigned, modulus, fill)` = `reinterpret(fill, modulus, True/False)` when transformed, else `fill` | `new_fill = signed_dtype.type(attrs["_FillValue"])` (new) / `unsigned_dtype.type(…)` (existing); guarded by `if "_FillValue" in attrs` | A-reference + I | the scalar fill is reinterpreted by the **same** fixed-width rule (`reinterpret`), validated against the real `np.dtype(target).type(fill)` by G-AX; `has_fill` ↔ the `"_FillValue" in attrs` guard (I). |
| A9 | the `else:` pass-through arm returns the elements unchanged | the gold `else: warnings.warn(...)` arm — no transform applied to `data` | R | `warnings.warn` does not touch the element values; the data passes through unchanged. The F2P/P2P tests observe `decoded.values`, on which `warn` is the identity (mapping.md §2). The modelled value `unsigned == ATTR_OTHER` covers a missing/uninterpretable `_Unsigned` (the configuration this arm reaches when neither inner condition fires). |
| A10 | `result` returned (a `List[int]`) | `Variable(dims, data, attrs, encoding)` | R | `Variable` is the identity on the element values + (possibly converted) fill the tests observe (`decoded.dtype` is pinned by `kind`+`unsigned`, `decoded.values` are the transformed elements); mapping.md §2. |

The discriminating content of the change — an **unsigned-stored** array
(`kind == "u"`) requested as **signed** (`unsigned == "false"`) is reinterpreted
to its signed view (`modulus-1 → -1`, …) rather than left unsigned — lives in
the `transform_to_signed` branch (model) ⇔ the inserted
`elif data.dtype.kind == "u": if unsigned == "false":` hunk (real). The pre-patch
code lacked this branch, so such an array fell through to the warning/pass-through
arm unchanged; `model_prepatch.py` reproduces that (the `transform_to_signed`
case flows into the pass-through arm, returning `data` unchanged) and **fails**
the postcondition
`Implies(transform_to_signed(kind, unsigned), ToSeq(Result()) == reinterpret_seq(ToSeq(data), modulus, True))`,
which is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps and no consumed axioms

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the element-wise fixed-width (un)signed reinterpretation
`np.asarray(dtype=…)` — is modelled **deeply** (the spelled-out two's-complement
`reinterpret`/`reinterpret_seq` consumed in `decode_unsigned_attr`, steps A7/A8,
an **A-reference**), not hidden behind an axiom about the operation under change:
there is **no consumed `asarray` axiom**. The `axioms` region is therefore empty.
Both directions of the reinterpretation are modelled (the new `u→i` branch the
fix adds and the symmetric existing `i→u` branch) so the skeleton mirrors the
whole post-patch `decode` dispatch, and so the deep model is exercised in the
direction the F2P tests observe (`u→i`) and the direction the P2P tests preserve
(`i→u`, `test_decode_unsigned_from_signed`). The plumbing callees
(`lazy_elemwise_func`, `Variable`, `pop_to`, `unpack_for_decoding`) are
identities on the observed element values (mapping.md §2), not contracted callees.

## C. verify(model) ⇒ resolved

`decode_unsigned_attr` verifies only if its output equals the exact element-wise
fixed-width reinterpretation in each transformed branch (A7) — in particular the
signed view for an unsigned-stored, `"false"`-requested array (the F2P behaviour)
— and the unchanged elements otherwise (A9), and the matching fill conversion
(A8). By R (numpy integer array ↔ `List[int]` of values; `lazy_elemwise_func` /
`Variable` / `pop_to` identities on the observed elements; `kind`/`unsigned`/
`modulus` codes) the verified operation equals the gold
`lazy_elemwise_func(data, partial(np.asarray, dtype=target), target)` on the
tested arrays; by G-AX the deep model `reinterpret` equals the real
`numpy.asarray(dtype=…)` (A-reference) in both directions over the exhaustive
small-width domains + boundaries + fuzz. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
deep model — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: deep-model/axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ); here there are no consumed axioms, only the
G-AX-validated A-reference deep model.
