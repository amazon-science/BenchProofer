# refinement.md — django__django-11133

The operation-by-operation correspondence between `model.py`'s implementation
(the `coerce_to_octets` impl region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — repo `make_bytes()` (`django/http/response.py:232`), modeled as `coerce_to_octets`

Gold hunk:
```
- if isinstance(value, bytes):
+ if isinstance(value, (bytes, memoryview)):
      return bytes(value)
  if isinstance(value, str):
      return bytes(value.encode(self.charset))
  return str(value).encode(self.charset)
```

| # | model.py impl op (`coerce_to_octets`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `v: Value` (`kind`, `buf`, `cps`) | the `value` argument + its `isinstance` discrimination | R | a runtime `value` ↔ a `Value` whose `kind` records which `isinstance` arm matches and whose `buf`/`cps` carry the touched octet/code-point content (mapping.md §2). |
| A2 | `if v.kind == KIND_OCTETS or v.kind == KIND_VIEW:` | `if isinstance(value, (bytes, memoryview)):` | R | the post-patch type test. `KIND_OCTETS` ↔ `isinstance(value, bytes)`, `KIND_VIEW` ↔ `isinstance(value, memoryview)`; the disjunction ↔ the tuple `(bytes, memoryview)`. This is the widened guard the fix introduces. |
| A3 | `return Value(..., v.buf)` (output `data == v.buf`) | `return bytes(value)` | R | `bytes()` of a `bytes` or a `memoryview` yields exactly the underlying octets — a verbatim copy of the buffer, no decode/encode/render (mapping.md §2). The model carries those octets as `v.buf`; for both buffer kinds the result's `data` is `v.buf`. |
| A4 | `return Value(..., charset_encode(v.cps))` (the single `else` arm) covers BOTH `isinstance(value, str)` and the fallthrough | `if isinstance(value, str): return bytes(value.encode(self.charset))` **and** `return str(value).encode(self.charset)` | A-consumed | the unchanged charset encoder applied to the value's code points. `charset_encode` is the axiom (`@Pure @ContractOnly`) standing in for `str.encode(self.charset)`; the proof consumes only its purity/determinism. The patch's two non-buffer arms (`value.encode` for a `str`; `str(value).encode` for any other value) are **observationally identical under this abstraction**: both produce `charset_encode(cps)` where `cps` is the value's code points (for a `str`) or the code points of its native-text rendering `str(value)` (for any other value). The model carries the relevant code points in `v.cps` (mapping.md §2) and collapses the two arms into one — the spec cannot and need not distinguish text from non-text, only buffer from non-buffer. `bytes(...)` of an already-`bytes` encode result is the identity (R). |

The discriminating content of the change — a buffer **view** (`memoryview`)
being carried through verbatim rather than rendered as text — lives in arm A2's
inclusion of `KIND_VIEW` in the buffer branch. The pre-patch code tested only
`isinstance(value, bytes)`; `model_prepatch.py` reproduces that (its buffer
branch matches `KIND_OCTETS` only, so a `KIND_VIEW` value falls through to the
encode/render branch) and **fails** the postcondition
`Implies(is_buffer_kind(v.kind), Result().data == v.buf)`, which is exactly the
spec sensing the change (G-DIFF). That is the F2P behaviour: pre-patch,
`HttpResponse(memoryview(b'memoryview')).content` renders the repr
`b'<memory at 0x...>'` (the encode-of-`str(value)` branch); post-patch it is the
underlying octets `b'memoryview'` (`v.buf`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-consumed. The one operation that genuinely *changed*
— widening the type guard so a buffer **view** joins the verbatim-octet branch
— is modeled **directly** as the `kind == KIND_VIEW` disjunct of the buffer
guard (A2) and the `Result().data == v.buf` output (A3). It is NOT hidden behind
an axiom: the changed dispatch and its octet-passthrough result are spelled out
in the impl and pinned by the postcondition. The only consumed axiom,
`charset_encode` (**A-consumed**, A4), covers the **unchanged** stdlib
encoder (`str.encode`) the non-buffer branches invoke — never the operation the
patch changes. There is no A-reference deep model here (the buffer passthrough
is a verbatim copy, modeled by equality `Result().data == v.buf`, not by a
recomputed fold).

## C. verify(model) ⇒ resolved

`coerce_to_octets` verifies only if a buffer-bearing value (octet string OR
buffer view — the two `is_buffer_kind` arms) yields output octets equal to the
underlying buffer (A2/A3), and only if a non-buffer value yields the charset
encoding of its code points (A4). By R (value ↔ `Value`, `bytes()` verbatim
copy, `bytes(encode)` identity) the verified function equals the gold
`make_bytes` on every input class the tests exercise: `memoryview` → the buffer
octets verbatim (the F2P case), `bytes` → itself, `str` → its charset encoding,
other → encoding of `str(value)` (the P2P cases). By G-AX the encoder axiom is
sound for the unchanged `str.encode` callee (A-consumed). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
