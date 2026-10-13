# refinement.md — scikit-learn__scikit-learn-15100

The operation-by-operation correspondence between `model.py`'s implementation
(`strip_marks`, the deep `strip_combining` fold, the `lemma`, and the live
`nfkd` / `is_combining` / `is_fixed_form_guard` axioms) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom's `Ensures`, **A-reference** where
a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single changed function — `strip_accents_unicode` (`text.py:114`)

Gold hunk (body):
```
-    normalized = unicodedata.normalize('NFKD', s)
-    if normalized == s:
+    try:
+        s.encode("ASCII", errors="strict")
         return s
-    else:
+    except UnicodeEncodeError:
+        normalized = unicodedata.normalize('NFKD', s)
         return ''.join([c for c in normalized if not unicodedata.combining(c)])
```

The change is purely the **early-return guard**: the decision of when to return
`s` unchanged moves from "the decomposition already equals `s`" (pre) to "`s` is
pure ASCII" (post). The general transformation
`''.join(c for c in normalize('NFKD', s) if not combining(c))` is **unchanged**.

| # | model.py impl op (`strip_marks`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `s: List[int]`, returned `List[int]` | `s: str` argument / return of `strip_accents_unicode` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| 2 | `in_fixed_form = is_fixed_form_guard(s)` | `s.encode("ASCII", errors="strict")` inside `try` | A-consumed | the new guard; `is_fixed_form_guard` is the weakest contract: success ⇔ `all_ascii(s)` (mapping.md §3.3). The proof consumes `Result() == all_ascii(ToSeq(s))`. |
| 3 | `if in_fixed_form:` then copy-loop building `out` and `return out` | `return s` (the `try` body) | R + I | the guard branch returns the input. `str` immutability ⇒ "return s" ↔ "return a value-equal fresh copy" (R, mapping.md §2); the copy loop is the identity materialisation (I). Permission: the fresh copy lets `s` keep its read-only 1/2 (directive 5) while `Result()` carries full permission. |
| 4 | the ASCII branch proves `ToSeq(out) == strip_combining(nfkd(ToSeq(s)))` via `nfkd(s)==s` (all_ascii ⇒ identity) and `strip_combining(s)==s` (`lemma_ascii_is_fixed_point`) | the fast path's correctness: an ASCII string has no accents, so returning it unchanged equals the general transform | A-consumed + A-reference | `nfkd` axiom (§3.1) gives `nfkd(s)==s`; `is_combining` axiom (§3.2) feeds the lemma `strip_combining(s)==s`; the deep model `strip_combining` (§3.4) is the A-reference. Together they prove the fast path is behaviour-preserving — exactly the patch comment's claim. |
| 5 | `normalized = decompose(s)` | `normalized = unicodedata.normalize('NFKD', s)` (the `except` body) | A-consumed | `decompose` is the runtime carrier of the `nfkd` axiom (`ToSeq(Result()) == nfkd(ToSeq(s))`), the same unchanged callee (mapping.md §3.1). |
| 6 | backward loop over `normalized`: keep `c` iff `not is_combining(c)`, building `strip_combining` of the suffix | `''.join([c for c in normalized if not unicodedata.combining(c)])` | A-reference + I | the UNCHANGED selection is modeled **deeply** as the front-recursive fold `strip_combining`; the loop's per-element keep/drop test `not is_combining(c)` is identical (I) to `not combining(c)`; G-AX validates `strip_combining(nfkd(s))` == the real comprehension (mapping.md §3.4). |
| 7 | postcondition `ToSeq(Result()) == strip_combining(nfkd(ToSeq(s)))` | the function's observable output | A-reference | the result is pinned to the deep per-element selection over the real decomposition — grounded in the input carrier `s`, not an opaque oracle (directive 8): a verifying impl must actually decompose then drop combining marks. |

## Why the prepatch fails on the right clause (G-DIFF)

`model_prepatch.py` keeps the byte-identical spec and restores the pre-patch
guard `if ToSeq(normalized) == ToSeq(s): return <copy of s>`. On an input that
is **already in decomposed form yet carries combining marks** (e.g.
`chr(110)+chr(771)` = `n` + combining tilde, the issue's `s2`), the guard fires
(`nfkd(s) == s`) and the impl returns `s`, but the postcondition demands
`ToSeq(Result()) == strip_combining(nfkd(ToSeq(s)))` and `strip_combining(s) !=
s` whenever `s` contains a combining mark. The prepatch therefore **fails**
exactly the postcondition `ToSeq(Result()) == strip_combining(nfkd(ToSeq(s)))`
(verifier error at the early-return branch) — the spec sensing the bug. This is
the single independently-fixed behaviour (one prepatch).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The operation that
genuinely *changed* — the early-return guard — is modeled with an expressible
predicate (`all_ascii`, the strict-ASCII test) backed by the `is_fixed_form_guard`
runtime axiom; it is not hidden behind an axiom about the function under change.
The UNCHANGED selection is modeled **deeply** (`strip_combining`, an
A-reference), and the two genuinely-unchanged stdlib callees (`normalize`,
`combining`) are the only **A-consumed** axioms, each the weakest contract the
proof needs and each G-AX-checked.

## verify(model) ⇒ resolved

`strip_marks` verifies only if its output equals `strip_combining(nfkd(s))`
unconditionally (step 7) — the exact transform the gold patch computes on the
`except` path, and (by the lemma + axioms) also on the ASCII fast path. By R
(`str` ↔ `List[int]`, immutable-return-copy) the verified function equals
`strip_accents_unicode` on every `str` input; by G-AX the deep model
`strip_combining(nfkd(.))` equals the real comprehension (A-reference) and the
`nfkd`/`is_combining`/`is_fixed_form_guard` axioms hold against the real callees
(A-consumed). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
