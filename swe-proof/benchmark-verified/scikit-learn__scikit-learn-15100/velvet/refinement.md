# refinement.md — scikit-learn__scikit-learn-15100

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `stripDiacritics` `do` block plus the deep `markFreeSeq` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/opaque callee — **A-consumed** where the proof uses a
property, here NONE since the callees are free; **A-reference** where a deep
model is validated == the real callee by G-AX), or **I** (identical concrete
op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the narrative is audited by **G-EQ**. Claim: any impl verifying against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The accent-strip site — `strip_accents_unicode(s)` (`text.py:114`)

Gold hunk (pre → post):
```
- normalized = unicodedata.normalize('NFKD', s)
- if normalized == s:
-     return s
- else:
-     return ''.join([c for c in normalized if not unicodedata.combining(c)])
+ try:
+     s.encode("ASCII", errors="strict")
+     return s
+ except UnicodeEncodeError:
+     normalized = unicodedata.normalize('NFKD', s)
+     return ''.join([c for c in normalized if not unicodedata.combining(c)])
```

| # | Solution.lean impl op (`stripDiacritics`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `s : List Char` | `s: str` arg of `strip_accents_unicode` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `canonicalDecompose s` | `unicodedata.normalize('NFKD', s)` | A (opaque, free) | UNCHANGED stdlib callee, no contract asserted (mapping.md §3.1). G-CONF runs the real `normalize` in the shadow; not consumed as an axiom (free function). |
| A3 | `isCombiningMark c` (the `if` guard inside the fold) | `unicodedata.combining(c)` read as `!= 0` | A (opaque, free) | UNCHANGED stdlib callee, no contract asserted (mapping.md §3.2). G-CONF runs the real `combining` in the shadow. |
| A4 | result is `markFreeSeq (canonicalDecompose s)`: keep each non-combining code point, drop each combining mark, computed by the backward `while` fold | `''.join([c for c in normalized if not unicodedata.combining(c)])`, applied **unconditionally** | I | the changed *application structure* is modeled **concretely**: `markFreeSeq` (pure region) and the verified loop ARE the comprehension. The fold ops (the `if isCombiningMark c then [] else [c]`, `++`, the loop) are **I** (transliterated 1:1 by G-CONF). |
| A5 | `result` returned (`List Char`) | the `''.join(...)` return value (the `return s` ASCII fast-path is behaviour-identical — see §B) | R / I | `''.join` of single-char fragments ↔ `List` `++` of `[c]`/`[]` (mapping.md §2). |

Discriminating content of the change — the strip is applied to ALL inputs, with
no `if normalized == s: return s` early-out — lives in the spec clause
`out = markFreeSeq (canonicalDecompose s)` holding for EVERY `s`. The pre-patch
returns `s` unchanged when `canonicalDecompose s = s` (already-decomposed
strings); `Solution_prepatch.lean` reproduces exactly that guard
(`return if canonicalDecompose s = s then s else result`) and **fails** the
postcondition for an already-decomposed `s` carrying a combining mark (G-DIFF).

## B. The gold ASCII fast-path is behaviour-preserving (not a separate site)

The gold patch replaces the buggy `if normalized == s: return s` guard with a
`try: s.encode("ASCII", "strict"); return s` fast-path. This is a pure
*optimization*, not a behaviour change vs. the maintainer-endorsed minimal fix
(`return ''.join([c for c in NFKD(s) if not combining(c)])`):

* If `s` is ASCII-encodable, it contains no accented or combining code points,
  so `NFKD(s) == s` and `combining(c) == 0` for every `c` — hence
  `''.join([c for c in NFKD(s) if not combining(c)]) == s`. Returning `s`
  directly gives the same result.
* If `s` is not ASCII-encodable, the `except` branch runs the full
  decompose-and-filter — identical to the unconditional comprehension.

So the gold's observable function equals `markFreeSeq ∘ canonicalDecompose` on
every input. The spec therefore models the unconditional strip (the behaviour
the F2P test and the issue demand); the ASCII fast-path is an R/I-invisible
performance refinement. G-CONF confirms `markFreeSeq(NFKD(s))` equals the gold
`strip_accents_unicode(s)` over the full fuzz corpus, including ASCII inputs.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — applying the
decompose-and-filter unconditionally — is modeled **concretely** (the spelled-out
fold `markFreeSeq`, step A4, an I leg), not hidden behind an axiom about the
function under change. The two A-tagged callees (`canonicalDecompose`,
`isCombiningMark`) are UNCHANGED stdlib routines, modeled as opaque free
functions with no asserted contract, so there is no consumed axiom and nothing
for G-AX (mapping.md §3).

## D. verify(Solution) ⇒ resolved

`stripDiacritics` verifies only if its output equals `markFreeSeq
(canonicalDecompose s)` for EVERY `s` (A4) — i.e. the strip is unconditional. By
R (`str ↔ List Char`, `''.join ↔ ++`) the verified function equals the
unconditional comprehension `''.join([c for c in NFKD(s) if not combining(c)])`;
by §B that equals the gold `strip_accents_unicode` (ASCII fast-path included) on
every input; by G-CONF the I transliteration of the fold composed with the real
`unicodedata` callees agrees with `patch.diff`'s behaviour on ≥10⁵ inputs
(including already-decomposed strings and standalone combining marks). Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and unchanged callees — and the gold patch resolves (G-RESOLVE).
Trust points: refinement fidelity (this doc, G-EQ + G-CONF). No axiom soundness
point (both callees free, G-AX skip).
