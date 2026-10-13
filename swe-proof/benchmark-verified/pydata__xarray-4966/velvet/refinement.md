# refinement.md — pydata__xarray-4966

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`decodeUnsigned` `do` block, the dispatch `chooseMode`, and the deep reinterpret
model `applyCast`/`castSeq`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses an axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

Semantics: **total correctness** (`loom.semantics.termination "total"`, the
loop carries `decreasing i`). The real `decode` always terminates (one pass
over a finite array), and partial-correctness semantics would let a
non-terminating same-spec impl (`while True`) verify vacuously — the P1
weakness found by the 2026-08-05 audit. Total semantics closes that hole.

## A. The decode dispatch — `UnsignedIntegerCoder.decode` (`xarray/coding/variables.py:305`)

Gold hunk (added branch):
```python
            if data.dtype.kind == "i":
                if unsigned == "true":
                    unsigned_dtype = np.dtype("u%s" % data.dtype.itemsize)
                    transform = partial(np.asarray, dtype=unsigned_dtype)
                    data = lazy_elemwise_func(data, transform, unsigned_dtype)
                    ...
+           elif data.dtype.kind == "u":
+               if unsigned == "false":
+                   signed_dtype = np.dtype("i%s" % data.dtype.itemsize)
+                   transform = partial(np.asarray, dtype=signed_dtype)
+                   data = lazy_elemwise_func(data, transform, signed_dtype)
+                   ...
            else:
                warnings.warn(...)
```

| # | Solution.lean impl op (`decodeUnsigned`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `kind : IntKind`, `bits : Nat`, `attr : Option (List Char)`, `values : List Int` | `data.dtype.kind`, `8*data.dtype.itemsize`, `pop_to(attrs,…,"_Unsigned")`, the element values of `data` | R | type bijection (mapping.md §2). G-CONF bridges via that table. |
| A2 | `let cm := chooseMode kind attr bits` — `none → keep`; `signedInt` + `"true" → toUnsigned`; `unsignedInt` + `"false" → toSigned`; else `keep` | the `if "_Unsigned" in attrs` / `if kind=="i"` / `elif kind=="u"` nested dispatch selecting `transform` and the target dtype | I | identical control/data flow: the same three observations (`attr` presence, `kind`, attribute value) select the same transform and resulting kind. Transliterated by G-CONF. |
| A3 | `castSeq m values` computed by the backward `while` fold (`result := applyCast m x :: result`) | `data = lazy_elemwise_func(data, partial(np.asarray, dtype=target), target)` | A-reference + I | the changed elementwise op is modeled **deeply**: `applyCast`/`castSeq` ARE the per-element two's-complement reinterpret; the fold ops (`applyCast m x`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `np.asarray(dtype=…)` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A4 | `return { values := result, kind := k' }` (the resulting kind `k'` = `cm.2`) | the returned `Variable` with reinterpreted `data` and the new element dtype | R | the F2P test observes `decoded.values` and `decoded.dtype`; `Decoded.values`/`Decoded.kind` carry exactly those two observations (mapping.md §2). |

Discriminating content of the change — `kind = unsignedInt ∧ attr = some
"false"` ⇒ `toSigned bits` (so e.g. an element `255` at width 8 decodes to
`-1`) — lives in the `unsignedInt` arm of `chooseMode`. The pre-patch `decode`
had no `elif kind == "u"` branch, so an unsigned array fell through to the
warning unchanged; `Solution_prepatch.lean` reproduces that (its inline dispatch
maps `unsignedInt` to `keep`) and **fails** `out = decodeModel …` (G-DIFF) — the
unsolved goal is exactly the postcondition, the genuine behavioral divergence.

## B. The `_FillValue` re-cast lines — not modeled (behaviorally inert on F2P)

The gold hunk also re-casts a present `_FillValue` attribute through the target
dtype (`new_fill = signed_dtype.type(attrs["_FillValue"])`). This is **not
modeled**: every F2P test (`test_decode_signed_from_unsigned[1,2,4,8]`)
constructs `xr.Variable(("x",), …, attrs={"_Unsigned": "false"})` with **no**
`_FillValue` key, so `"_FillValue" in attrs` is `False` and the branch never
executes on any tested input. Omitting an inert sub-branch keeps the spec from
acquiring a liability (a numpy-scalar `.type()` cast that, on modern numpy,
raises `OverflowError` for the unsigned max — itself unobserved by F2P) with no
F2P observation behind it. The element-value and dtype behavior the tests
observe is fully captured by §A. No kind-3 op is hidden here: the omitted lines
are a guarded no-op on the tested inputs, recorded for the audit, not an
inexpressible changed op.

No separate failing prepatch for site B: there is no independently-observable
fixed behavior there on the F2P inputs (the branch is inert), and a prepatch must
keep the spec byte-identical (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every modeled step is R, A, or I. The one operation that genuinely *changed* —
adding the unsigned→signed reinterpret branch — is modeled **deeply** (the
spelled-out dispatch `chooseMode` plus the elementwise `applyCast`/`castSeq`,
steps A2–A3), not hidden behind an axiom about the function under change: there
is no consumed `decode` axiom. The only kind-A construct is the **A-reference**
deep model `applyCast` ↔ `np.asarray(dtype=…)` (an unchanged library callee),
validated by G-AX.

## D. verify(Solution) ⇒ resolved

`decodeUnsigned` verifies only if its output equals `decodeModel kind bits attr
values` — i.e. the dispatch picks `toSigned bits` for `unsignedInt ∧ "false"`
(A2) and the elements are the exact per-element reinterpret (A3) with the signed
resulting kind (A4). By R (the type bijection, mapping.md §2) the verified result
equals the patched `decode`'s observable content on the tested inputs; by G-AX
the deep model `castSeq`/`applyCast` equals the real `np.asarray(dtype=…)`
elementwise over all four widths (A-reference); by G-CONF the R/I transliteration
of the dispatch + reinterpret agrees with `patch.diff`'s behaviour on the fuzzed
element inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1:
axiom/deep-model soundness (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).
