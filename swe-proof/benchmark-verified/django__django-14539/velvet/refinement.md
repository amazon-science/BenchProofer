# refinement.md — django__django-14539

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `peelTrailingPunctuation` `do` block, with the deep models
`stripTrailingPunct` / `trailingPunctCount`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized/opaque callee —
**A-consumed** where the proof uses a value-level fact about the callee,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ** and **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The trailing-punctuation peel site — `trim_punctuation` (`django/utils/html.py:283-288`)

`trim_punctuation` is a closure nested in `urlize`. The gold patch changes only
the trailing-punctuation block; the wrapping-punctuation loop and the outer
`while trimmed_something` loop are unchanged. The modeled `method`
`peelTrailingPunctuation` is exactly that block: given the current `middle`
(`token`) and `trail` (`tail`), it computes the new `(middle, trail)`.

Gold hunk:
```
-                trail = middle[len(stripped):] + trail
-                middle = middle[:len(stripped) - len(middle_unescaped)]
+                punctuation_count = len(middle_unescaped) - len(stripped)
+                trail = middle[-punctuation_count:] + trail
+                middle = middle[:-punctuation_count]
```

| # | Solution.lean impl op (`peelTrailingPunctuation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `token : List Char`, `tail : List Char` | `middle`, `trail` (`str`) args of the block | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges `s ↔ s` directly (str). |
| A2 | `let decoded := entityDecode token` | `middle_unescaped = html.unescape(middle)` | A-reference | `entityDecode` is the OPAQUE model of the unchanged stdlib callee `html.unescape`; no value-level axiom is consumed. G-AX validates `entityDecode ≡ html.unescape` and, crucially, that it never lengthens (so the Nat subtraction below is exact). mapping.md §3.1. |
| A3 | `let stripped := stripTrailingPunct decoded` | `stripped = middle_unescaped.rstrip(TRAILING_PUNCTUATION_CHARS)` | A-reference + I | `stripTrailingPunct` (reverse / drop-while / reverse over `.,:;!`) is the DEEP model of `str.rstrip(TRAILING_PUNCTUATION_CHARS)`. The ops (`reverse`, `dropWhile`, `reverse`) are concrete (**I**); the equality of that deep model to the real `.rstrip` is the **A-reference** G-AX validates. mapping.md §3.2. |
| A4 | `let punctuationCount := decoded.length - stripped.length` | `punctuation_count = len(middle_unescaped) - len(stripped)` | I | identical arithmetic; `.length` ↔ `len(...)`. Equals the spec's `trailingPunctCount token`. |
| A5 | guard `if decoded ≠ stripped then` | `if middle_unescaped != stripped:` | I | identical branch condition. |
| A6 | `core := token.take (token.length - punctuationCount)` | `middle = middle[:-punctuation_count]` | I + R | for `0 < pc ≤ len`, `token.take (len - pc)` ↔ `middle[:-pc]` (mapping.md §2: negative-index slice ↔ `take (len - pc)`; G-AX A-reference 1 guarantees `pc ≤ len`). |
| A7 | `newTail := token.drop (token.length - punctuationCount) ++ tail` | `trail = middle[-punctuation_count:] + trail` | I + R | for `0 < pc ≤ len`, `token.drop (len - pc)` ↔ `middle[-pc:]`. **This is the fixed line.** The pre-patch sliced at `len(stripped)` (a DECODED-length index) — see `Solution_prepatch.lean`. |
| A8 | `return { core, tail := newTail }` | `return ..., middle, trail` (block result) | R | the `Split` structure carries the two updated locals; the outer loop reads them back. |

The frozen postconditions pin BOTH outputs:
```
ensures res.core = token.take (token.length - trailingPunctCount token)
ensures res.tail = token.drop (token.length - trailingPunctCount token) ++ tail
```
where `trailingPunctCount token = (entityDecode token).length −
(stripTrailingPunct (entityDecode token)).length`. The cut index is
`token.length − pc`, i.e. measured from the END of the ENCODED token — the
whole point of the fix.

## B. The discriminator — why the prepatch fails

The bug: the pre-patch peels the suffix at `middle[len(stripped):]`, i.e.
`token.drop (stripped.length)` where `stripped.length = decoded.length − pc`.
That is a DECODED-length index applied to the ENCODED token. It agrees with the
spec only when `decoded.length = token.length` (no entities). When an entity
makes `decoded.length < token.length`, `drop (decoded.length − pc) ≠
drop (token.length − pc)`, so the **`res.tail` postcondition (`ensures_1`)
fails**. `Solution_prepatch.lean` reproduces `newTail := token.drop
stripped.length ++ tail` and `prove_correct` fails exactly on that clause
(G-DIFF), reproducing the issue's `...&lt</a>lt!` vs `...&lt</a>!`.

Note the `core`/`middle` clause is unchanged by the bug
(`middle[:len(stripped)-len(middle_unescaped)] == middle[:-pc]`, both index from
the end); the discriminating clause is **`res.tail`** only. The frozen spec is
strong enough that the bug cannot satisfy it (G-PANEL attacker-1 target).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the
suffix-slice index — is modeled **directly** with `take`/`drop` over the
encoded `List Char` (A6/A7, I+R), not hidden behind an axiom. The only opaque
callee, `entityDecode` (`html.unescape`), is UNCHANGED by the patch and carries
no consumed value-level axiom — it is an A-reference whose soundness
obligations (functionality + non-lengthening) G-AX checks against the real
callee.

## D. verify(Solution) ⇒ resolved

`peelTrailingPunctuation` verifies only if both outputs equal the END-anchored
peel (A6/A7). By R (`str ↔ List Char`, negative-slice ↔ `take/drop (len−pc)`,
valid because G-AX proves `pc ≤ len`) the verified peel equals the gold-patched
block on the tested `str` inputs; by G-AX the deep models (`stripTrailingPunct
== str.rstrip`, `entityDecode == html.unescape` non-lengthening, end-to-end peel
== gold block) hold; by G-CONF the R/I transliteration agrees with `patch.diff`
behaviour on ≥10⁵ inputs (and the real patched `urlize` reproduces the issue's
example, the G-CONF anchor). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and an audited unchanged
callee — and the gold patch resolves (G-RESOLVE). Trust points are exactly the
two of plan §1.1: A-reference soundness (G-AX) and refinement fidelity (this
doc, G-EQ + G-CONF).
