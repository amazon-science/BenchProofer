# refinement.md — psf__requests-2317

The operation-by-operation correspondence between `model.py`'s implementation
(the `native_method` impl region and the deep `native_method` copy model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The method-coercion site — `Session.request` (`requests/sessions.py:428`)

Gold hunk:
```
- method = builtin_str(method)
+ method = to_native_string(method)
```
(plus the import-list edit on `requests/sessions.py:16` dropping the now-unused
`builtin_str` — pure bookkeeping, no behaviour; see row A4.)

| # | model.py impl op (`native_method`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `content: List[int]`, `is_bytes: bool` | the `method` argument (a `str` or a `bytes`) of `Session.request` | R | `str`/`bytes` ↔ `List[int]` of character/byte values + an `is_bytes` discriminator (mapping.md §2). For ASCII tokens the byte value equals the code point of its ASCII decode, so one carrier serves both. |
| A2 | the result is `ToSeq(content)` — the carried method characters, produced by the verified copy loop returning `result == content` | `to_native_string(method)` | A-reference | the changed coercion is modeled **deeply**: the copy loop in `native_method` (with invariant `ToSeq(result) == ToSeq(content).take(j)`) IS the operation "return the token's own characters". There is no consumed `to_native_string` axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `to_native_string` on boundary+fuzz tokens (as both `str` and `bytes`) and asserts `to_native_string == native_method`. The real callee returns a `str` unchanged and ASCII-decodes a `bytes`; for an ASCII token both are the identity on the carried sequence (mapping.md §3.1). |
| A3 | (no node) | the import-list edit `from .compat import ... builtin_str` → without `builtin_str` (`sessions.py:16`) | I | removing an import that the body no longer references is observationally a no-op; it changes no behaviour any test observes (it is a consequence of A2's swap). |

The discriminating content of the change — a byte-string method token must be
**decoded** to its characters (`b'GET'` → `GET`) rather than **rendered** as a
text object (`b'GET'` → the five characters `b'GET'`) — lives in
`native_method`'s postcondition `ToSeq(Result()) == ToSeq(content)`
(equivalently `len(Result()) == len(content)`).
The pre-patch `str(method)` produced the `b'...'`-wrapped sequence;
`model_prepatch.py` reproduces that exactly (prefix `[98, 39]`, content,
suffix `[39]`) — a length-`len+3` sequence — and **fails** the postcondition
`ToSeq(Result()) == ToSeq(content)` — exactly the spec sensing the
change (G-DIFF). This is the single behaviour the F2P `test_encoded_methods`
(`requests.request(b'GET', ...)` must be `r.ok`) observes; for a native `str`
token (the P2P `test_unicode_method_name`, `u('POST')`) both pre- and post-patch
coercions are the identity, matching `is_bytes == False` ⇒ `Result == content`
in either case.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — coercing the method token to its native text form — is modeled
**deeply** (the spelled-out verified copy loop in `native_method`, an
**A-reference**), not hidden behind an axiom about the function under change:
there is **no consumed `to_native_string` axiom**, and the axioms region is
empty. The real callee `to_native_string` appears only as the **A-reference**
that G-AX validates the deep model against. The removed `str(...)` coercion is
exhibited concretely by `model_prepatch.py` (the `b'...'`-wrapping byte branch),
which the spec rejects via the dominant `ToSeq(Result()) == ToSeq(content)`
postcondition; no separate oracle/predicate is needed because the wrong
behaviour is value- and length-distinguishable from the carried sequence.

## C. verify(model) ⇒ resolved

`native_method` verifies only if its output equals the token's own carried
characters (`ToSeq(Result()) == ToSeq(content)`, A2). By R (`str`/`bytes` ↔
`List[int]` + `is_bytes`; ASCII byte value = decoded code point) the verified
coercion equals `to_native_string(method)` on the tested tokens; by G-AX the
deep model `native_method` equals the real `to_native_string` (A-reference)
over the entire Requires domain (0..127 \ {39,92}). The pre-patch
`str(bytes)` `b'...'`-rendering returns a length-`len+3` sequence and so cannot
satisfy `ToSeq(Result()) == ToSeq(content)` (G-DIFF). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep-model reference — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: deep-model /
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).

**Termination obligation.** Nagini's default judgement is partial correctness,
so the value postcondition alone would be discharged vacuously by an
implementation that computes the right sequence and then never returns — and
such an implementation, refined faithfully into `Session.request`, hangs every
test to the harness wall-clock instead of resolving. `native_method` therefore
also `Requires(MustTerminate(len(content) + 2))`: the coercion of a finite
token is bounded work and must actually deliver its result. The copy loop
consumes the obligation with the strictly decreasing, bounded-below measure
`n - j`; any loop without such a measure leaks the obligation and the
verifier rejects it. With this obligation a verified model both returns the
correct native token AND returns at all, closing the divergence channel.
