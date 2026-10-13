# refinement.md — psf__requests-2931

The operation-by-operation correspondence between `model.py`'s implementation
(the `serialize_request_body` and `normalize_query_string` impl regions, plus
the `to_native` axiom they rest on) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses this axiom's
`Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

This is a genuine **two-site** change in `requests/models.py`; each site is its
own contracted+implemented function in `model.py`.

## A. The body site — `_encode_params` str/bytes branch (`models.py:84`)

Gold hunk:
```
  if isinstance(data, (str, bytes)):
-     return to_native_string(data)
+     return data
```

| # | model.py impl op (`serialize_request_body`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `v: Value` (`is_bytes` tag + `data: PSeq[int]`) | `data` (a `str` or `bytes`) | R | `str`/`bytes` ↔ `Value` carrier: `is_bytes` is the type tag, `data` the code-point/octet content (mapping.md §2). |
| A2 | `r = Value(v.is_bytes, v.data)` then `return r` | `return data` | I + R | returning the value verbatim. `Value(v.is_bytes, v.data)` is the same value: same type tag, same content (the constructor is the identity packaging, post-state pinned by `Value.__init__`'s Ensures). Under R this *is* `return data`. |

The discriminating content of the change lives in the postcondition
`Result().is_bytes == v.is_bytes` ∧ `Result().data == v.data`: the body path
preserves the value's type **and** content. This is exactly what the F2P test
`test_binary_put` observes — `isinstance(request.body, bytes)` after sending a
binary (`bytes`) payload. The pre-change code applied the native-string decoder
to the body; `model_prepatch.py` reproduces that (`to_native(v.is_bytes,
v.data)` packaged as `Value(False, ...)`) and **fails** verification, because
the decoder's `Requires(Implies(v_is_bytes, is_ascii(v_data)))` is not
established for an arbitrary binary body (the actual UTF-8 payload
`b"\xc3\xb6\xc3\xb6\xc3\xb6"` is non-ASCII, so the real call raises). Even were
the input ASCII, the same skeleton violates `Result().is_bytes == v.is_bytes`
(it forces the native-text tag). Either way the frozen spec senses the change
(G-DIFF).

## B. The query site — `prepare_url` params coercion (`models.py:388`)

Gold hunk (added immediately before `enc_params = self._encode_params(params)`):
```
+ if isinstance(params, (str, bytes)):
+     params = to_native_string(params)
```

| # | model.py impl op (`normalize_query_string`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `nd = to_native(v.is_bytes, v.data)` | `to_native_string(params)` | A-consumed | `to_native` is the weakest contract on the unchanged callee `to_native_string` the spec needs (identity on content for ASCII octets / native text; mapping.md §3.1). The proof **consumes** its `Ensures(Result() == v_data)` to discharge `Result().data == v.data`, and its `Requires(Implies(v_is_bytes, is_ascii(v_data)))` is discharged by site B's own precondition (a query value, if binary, is ASCII). G-AX confirms the axiom against the real `to_native_string`. |
| B2 | `r = Value(False, nd)` then `return r` | `params = ...` (now native text), then fed to `_encode_params` | R + I | the coerced query value is native text: tag `is_bytes == False`, content `nd == v.data`. `to_native_string` always returns native `str` on Python 3, so the reassigned `params` is `str` — modeled by the `False` tag. |

Site B postcondition `Result().is_bytes == False` ∧ `Result().data == v.data`
pins the long-standing query behaviour: a binary (`bytes`) query value of ASCII
octets becomes native text with the same characters, native text is unchanged.
This is what the P2P test `test_params_bytes_are_encoded` observes
(`params=b'test=foo'` ⇒ URL `?test=foo`).

### Why site B needs no separate failing `model_prepatch`
Sites A and B are **coupled**: before the patch the native-string coercion of a
str/bytes value happened *inside* `_encode_params` (site A); the patch removes
it there and re-adds it for the query value at site B. The net effect for query
parameters is therefore **unchanged** — site B is a behaviour-preserving
relocation, not an independently-observable fix. The single independently-fixed
behaviour (the F2P test) is site A's body-preservation, and `model_prepatch.py`
exercises exactly that. A second prepatch reverting site B would have to keep
the frozen spec byte-identical (G-DIFF `same_spec`) yet model a query coercion
that still yields native text — there is no such behaviourally-distinct buggy
variant, because the pre-patch world produced the same query result by the other
route. Site B's correctness is therefore carried by the A-consumed `to_native`
axiom (G-AX) and its query-normalization postcondition, exactly as the django
exemplar carries its callee-swap site by an axiom + postcondition rather than a
second verification-failing skeleton.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the body path no longer decoding the value to native text — is modeled
**directly** (site A returns the value verbatim: `Value(v.is_bytes, v.data)`,
postcondition `Result().is_bytes == v.is_bytes` ∧ `Result().data == v.data`),
not hidden behind an axiom about the function under change. There is **no
A-reference** in this bundle: the one consumed axiom, `to_native`
(**A-consumed**, site B), is an **unchanged** utility callee (`to_native_string`)
that the surviving query path still invokes; the body path's removal of that
call is the spelled-out change, not an axiom.

## D. verify(model) ⇒ resolved

`serialize_request_body` verifies only if its output equals the input value
exactly — same type tag (A2, the F2P discriminator) and same content. By R
(`str`/`bytes` ↔ `Value`) the verified body path equals `return data`, so a
binary payload stays `bytes` (F2P `test_binary_put`). `normalize_query_string`
verifies only if its output is native text with the same content (B1+B2); by
A-consumed (`to_native` == real `to_native_string`, G-AX) and R that equals the
gold `params = to_native_string(params)`, so the query behaviour is retained
(P2P `test_params_bytes_are_encoded`). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the one
audited callee — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX, the `to_native` axiom) and
refinement fidelity (this document, G-EQ).
