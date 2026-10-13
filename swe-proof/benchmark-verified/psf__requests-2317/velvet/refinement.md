# refinement.md — psf__requests-2317

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `nativeToken` impl region and the deep `nativeSeq` copy
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The method-coercion site — `Session.request` (`requests/sessions.py:428`)

Gold hunk:
```
- method = builtin_str(method)
+ method = to_native_string(method)
```
(plus the import-list edit on `requests/sessions.py:16` dropping the now-unused
`builtin_str` — pure bookkeeping, no behaviour; see row A3.)

| # | Solution.lean impl op (`nativeToken`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `token : List Char` | the `method` argument (a `str` or a `bytes`) of `Session.request` | R | `str`/`bytes` ↔ `List Char` of character/byte values (mapping.md §2). For ASCII tokens the byte value equals the code point of its ASCII decode, so one carrier serves both text and byte forms; no `is_bytes` discriminator is needed because the native representation is the carried character sequence in either case. |
| A2 | `out = nativeSeq token`, the carried token characters, produced by the verified copy loop (`while` with invariant `result = nativeSeq (token.drop i)`, prepending `nativeChar c`); `nativeSeq` is the identity on the carried sequence (`nativeSeq_id`) | `to_native_string(method)` | A-reference | the changed coercion is modeled **deeply**: the copy loop in `nativeToken` IS the operation "return the token's own characters". There is no consumed `to_native_string` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `to_native_string` on boundary+fuzz tokens (as both `str` and `bytes`) and asserts `to_native_string == nativeSeq`. The real callee returns a `str` unchanged and ASCII-decodes a `bytes`; for an ASCII token both are the identity on the carried sequence (mapping.md §3.1). |
| A3 | (no node) | the import-list edit `from .compat import ... builtin_str` → without `builtin_str` (`sessions.py:16`) | I | removing an import the body no longer references is observationally a no-op; it changes no behaviour any test observes (it is a consequence of A2's swap). |

The discriminating content of the change — a byte-string method token must be
**decoded** to its characters (`b'GET'` → `GET`) rather than **rendered** as a
text object (`b'GET'` → the five characters `b'GET'`) — lives in
`nativeToken`'s postcondition `out = token` (equivalently `out = nativeSeq token`
and `out.length = token.length`). The pre-patch `str(method)` produced the
`b'...'`-wrapped sequence; `Solution_prepatch.lean` reproduces that exactly
(prefix `['b', '\'']`, content, suffix `['\'']`) — a length-`len+3` sequence —
and **fails** the postcondition `out = token` / `out = nativeSeq token` — exactly
the spec sensing the change (G-DIFF). This is the single behaviour the F2P
`test_encoded_methods` (`requests.request(b'GET', ...)` must be `r.ok`) observes;
for a native `str` token (the P2P `test_unicode_method_name`, `u('POST')`) both
pre- and post-patch coercions are the identity, matching `out = token` in either
case.

## A2b. Termination semantics (spec-strength repair)

The spec runs under `loom.semantics.termination "total"` (TotalCorrectness,
with an explicit `decreasing i` measure on the copy loop). An earlier revision
used partial correctness, under which a non-terminating same-spec impl
(`while true`) vacuously satisfied every postcondition — a spec-too-weak hole
found by the P2 audit (G-PANEL-1: a verifying wrong impl whose "faithful patch"
is an infinite loop that the resolve harness cannot complete). The real
`Session.request` coercion `to_native_string(method)` terminates on every
input, so total correctness is the faithful modeling: the contract now pins
both the value (`out = token`) AND termination, and a non-terminating impl no
longer verifies.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — coercing the method token to its native text form — is modeled
**deeply** (the spelled-out verified copy loop in `nativeToken`, an
**A-reference**), not hidden behind an axiom about the function under change:
there is **no consumed `to_native_string` axiom**, and the axioms region is
empty. The real callee `to_native_string` appears only as the **A-reference**
that G-AX validates the deep model against. The removed `str(...)` coercion is
exhibited concretely by `Solution_prepatch.lean` (the `b'...'`-wrapping byte
branch), which the spec rejects via the dominant `out = token` postcondition; no
separate oracle/predicate is needed because the wrong behaviour is value- and
length-distinguishable from the carried sequence.

## C. verify(Solution) ⇒ resolved

`nativeToken` verifies only if its output equals the token's own carried
characters (`out = token`, `out = nativeSeq token`, A2). By R (`str`/`bytes` ↔
`List Char`; ASCII byte value = decoded code point) the verified coercion equals
`to_native_string(method)` on the tested tokens; by G-AX the deep model
`nativeSeq` equals the real `to_native_string` (A-reference) over the ASCII
domain. The pre-patch `str(bytes)` `b'...'`-rendering returns a length-`len+3`
sequence and so cannot satisfy `out = token` (G-DIFF). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep-model reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-model /
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
