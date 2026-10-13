# refinement.md — django__django-11133

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`makeBytes` `do` block and the pure `bodyBytes` dispatch) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete op). EVERY
step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The dispatch site — `make_bytes` (`django/http/response.py:223`)

Gold hunk:
```
-        if isinstance(value, bytes):
+        if isinstance(value, (bytes, memoryview)):
             return bytes(value)
         if isinstance(value, str):
             return bytes(value.encode(self.charset))
         # Handle non-string types.
         return str(value).encode(self.charset)
```

| # | Solution.lean impl op (`makeBytes` / `bodyBytes`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `value : Body` (constructors `bytes`/`buffer`/`text`/`other`) | the `value` argument, classified by which `isinstance` branch it matches | R | runtime type ↔ `Body` (mapping.md §2). G-CONF bridges via the concrete `bytes`/`memoryview`/`str`/other realisations. |
| A2 | `match value with \| .bytes b => pure b` | `if isinstance(value, (bytes, memoryview)): return bytes(value)` (bytes case) | I + A-reference | concrete dispatch; `bytes(value)` on a plain `bytes` is identity on content (`.bytes b => b`). The identity `bytes(bytes_obj) == bytes_obj` is part of the A-reference validated by G-AX §3.1. |
| A3 | `\| .buffer b => pure b` | `if isinstance(value, (bytes, memoryview)): return bytes(value)` (memoryview case — **the added branch**) | I + A-reference | the new branch: a byte-buffer view yields its underlying bytes. Modeled deeply as `.buffer b => b`; the equality `list(bytes(memoryview)) == underlying bytes` is the **A-reference** G-AX validates (mapping.md §3.1). |
| A4 | `\| .text s => pure (encodeStr s)` | `if isinstance(value, str): return bytes(value.encode(self.charset))` | R + A-reference | UNCHANGED str branch; the encoder `value.encode(self.charset)` is the free input `encodeStr` (no property relied on, mapping.md §3.2). `bytes(value.encode(...))` ↔ `encodeStr s` (the `bytes(...)` wrapper is identity on an already-`bytes` result). |
| A5 | `\| .other => pure fallback` | `return str(value).encode(self.charset)` | R | UNCHANGED non-string branch; the render-then-encode chain is the free input `fallback` (mapping.md §3.2). |

Discriminating content of the change — a `memoryview` value yields its underlying
bytes `b` (A3), NOT the encoded textual rendering `fallback` — lives in
`bodyBytes (.buffer b) = b` (model) ⇔ the new `memoryview` arm of
`isinstance(value, (bytes, memoryview))` (real). The pre-patch guard
`isinstance(value, bytes)` excluded `memoryview`, so a buffer fell through to
`return str(value).encode(...)` (the repr); `Solution_prepatch.lean` reproduces
that (`.buffer _ => pure fallback`) and **fails** `out = bodyBytes …` on exactly
the `.buffer` clause (G-DIFF, confirmed unsolved goal
`fallback = bodyBytes encodeStr fallback value` with `value = Body.buffer i`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely changed — that a
byte-buffer view is now treated as binary and yields its content — is modeled
**deeply** (the `.buffer b => b` arm, A3), not hidden behind an axiom about the
function under change. There is **no consumed axiom**: the only non-trivial
semantic fact (`bytes(memoryview) == underlying bytes`, and `bytes(bytes)` =
identity) is an **A-reference** validated against the real builtin by G-AX, and it
is realised concretely in the model (the constructor carries the `List UInt8`
content directly). The other two callees (`encodeStr`, `fallback`) are UNCHANGED
and abstracted as free inputs with no relied-on property (mapping.md §3.2), so
they need no G-AX validation beyond their realisation in G-CONF.

## C. verify(Solution) ⇒ resolved

`makeBytes` verifies only if its output equals the exact per-shape dispatch
`bodyBytes`: a buffer yields its content `b` (A3), a plain `bytes` yields `b`
(A2), text yields `encodeStr s` (A4), other yields `fallback` (A5). By R (the
`bytes`/`memoryview`/`str` ↔ `Body` bijection, mapping.md §2) the verified routine
equals the gold-patched `make_bytes` on every input; by G-AX the deep model of the
binary branch equals the real `bytes(...)` builtin on both plain byte strings and
byte-buffer views (A-reference); by G-CONF the R/I transliteration of the dispatch
agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited builtin — and the gold patch resolves (G-RESOLVE). The
sole trust points are the A-reference soundness (G-AX) and refinement fidelity
(this doc, G-EQ + G-CONF).
