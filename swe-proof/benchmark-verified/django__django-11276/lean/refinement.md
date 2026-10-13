# refinement.md — django__django-11276

Maps every op in `implementation_escape` (Solution.lean impl region) to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses this axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op).

The gold patch rewrites `escape`'s body from
`mark_safe(str(text).translate(_html_escapes))` to
`mark_safe(html.escape(str(text)))`. Under the type bijection (mapping.md),
`str(text)` and `mark_safe(·)` are character-preserving identities outside the
modeled boundary; the modeled boundary is the string→string HTML encoding, which
post-patch is `html.escape(·, quote=True)`.

| # | `implementation_escape` op (Lean) | `patch.diff` / post-patch counterpart (Python) | tag |
|---|---|---|---|
| 1 | domain `s : List Char` ← argument | `str(text)` — the stringified input, iterated per code point | R (str ↔ List Char, per-code-point) |
| 2 | `let mut acc : List Char := []` | accumulator for the produced characters; models the empty prefix of the encoder's output | I (structural) |
| 3 | `for c in s do` | the per-code-point walk `html.escape` performs over the input string | R (iterate str code points ↔ `for c in (s : List Char)`) |
| 4 | `acc := acc ++ escapeChar c` | append this code point's HTML encoding — `html.escape`'s per-char substitution: `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`, `"`→`&quot;`, `'`→`&#x27;`, else identity | **A-reference** (deep model of `html.escape`; validated == real callee by G-AX / G-CONF) |
| 5 | `return acc` | the assembled escaped string (before `mark_safe`) | I |
| — | (outside boundary) `mark_safe(·)` | tags result `SafeString`; character-preserving | not modeled (identity on char list) |
| — | (outside boundary) `str(text)` | object → str coercion; upstream of boundary | not modeled (domain is the char list) |

## Notes

- **No changed-inexpressible op.** Every op is R, A-reference, or I. There is no
  consumed callee axiom: the only callee the patch introduces (`html.escape`) IS
  the changed operation, so per §0.7 it is modeled deeply (row 4, `escapeChar` /
  `escapeSeq`), never axiomatized. `meta.json axioms = []`;
  `deep_model_references = ["html.escape"]`.
- **A-reference validation.** Row 4's `escapeChar` claims to equal the
  per-code-point behavior of `html.escape(·, quote=True)`. `axiom_check.py`
  (G-AX) drives the REAL `html.escape` over a boundary set + fuzz and asserts it
  agrees code-point-by-code-point with `escapeChar`; `conformance_check.py`
  (G-CONF) diffs the whole-string shadow of `implementation_escape` against the
  real `html.escape` over >10^5 fuzzed inputs.
- **R/I legs (rows 1,2,3,5)** are mechanically refuted by G-CONF; the A-reference
  narrative (row 4) by G-AX + G-EQ.
- **Discriminating clause (G-DIFF).** The single behavioral change is the
  apostrophe: `escapeChar '\''  = "&#x27;"`, whereas the pre-patch table produced
  `&#39;`. `Solution_prepatch.lean` reproduces the pre-patch `&#39;` mapping; its
  carried gold proof cannot close because `escapeSeq ['\''] = "&#x27;".toList ≠
  "&#39;".toList`.
