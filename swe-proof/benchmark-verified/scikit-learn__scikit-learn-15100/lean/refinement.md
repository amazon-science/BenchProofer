# refinement.md — scikit-learn__scikit-learn-15100

Operation-by-operation correspondence between `implementation_stripAccents`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`strip_accents_unicode`). Tags: **R** type refinement, **A-consumed** proof uses
an axiom, **A-reference** deep model validated == real callee by G-AX/G-CONF,
**I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if s.all isAscii then return s` | `try: s.encode("ASCII", errors="strict"); return s` | R |
| 2 | (else fall-through) | `except UnicodeEncodeError:` | R |
| 3 | `let normalized := canonDecompose s` | `normalized = unicodedata.normalize('NFKD', s)` | A-reference |
| 4 | `return normalized.filter (fun c => !isCombiningMark c)` | `return ''.join([c for c in normalized if not unicodedata.combining(c)])` | A-reference + I |

Notes:

- **Op 1/2 is the fix.** Post-patch, the early-return guard tests whether the
  string is ASCII-encodable (`s.encode("ASCII", errors="strict")` raising
  `UnicodeEncodeError` for any non-ASCII code point). Pre-patch, the guard tested
  whether the canonical decomposition equaled the input
  (`unicodedata.normalize('NFKD', s) == s`). A string already supplied in
  decomposed form satisfies the pre-patch guard (it equals its own
  decomposition) and is wrongly returned unchanged — that is the reported bug.
  The post-patch guard returns the string unchanged ONLY when it is pure ASCII,
  so a decomposed accented string still falls through to the stripping branch.
  This is the single discriminating clause. The model expresses the ASCII test
  as `s.all isAscii` with `isAscii c := c.toNat < 128` — tagged **R** because it
  refines Python's `str.encode("ASCII", strict)`/`UnicodeEncodeError` mechanism
  to a total per-code-point predicate (bijection in mapping.md). The pre-patch
  guard (`canonDecompose s = s`) is what `Solution_prepatch.lean` uses.
- **Op 3 (A-reference).** `unicodedata.normalize('NFKD', s)` — canonical
  decomposition. Modeled as the opaque callee `canonDecompose`. The patch does
  NOT change this call; it is an unchanged dependency that the function reads.
  The proof consumes NO property of it (`correct_stripAccents` closes by
  `split <;> rfl` because spec and impl are structurally identical), so it is an
  **A-reference**, not a consumed axiom. Its modeling is validated against the
  real `unicodedata.normalize('NFKD', ·)` by G-CONF.
- **Op 4 (A-reference + I).** `''.join([c for c in normalized if not
  unicodedata.combining(c)])` — keep only the non-combining code points. The
  combining-mark test is the unchanged callee `unicodedata.combining`, modeled as
  the opaque `isCombiningMark` (A-reference, validated by G-CONF). The list
  comprehension + join is `List.filter (fun c => !isCombiningMark c)` — an
  identical concrete op (per-code-point filter then concatenation).
- **No A-consumed tags.** The two unchanged callees enter the executable impl as
  opaque references and the proof needs no property of either, so there is no
  consumed `axiom`. **G-AX is a skip stub**; the callees' modeling is checked by
  G-CONF against the real `unicodedata` routines.
- **G-CONF** mechanically refutes the R/I legs: the Python shadow of the impl
  (using the REAL `unicodedata.normalize`/`unicodedata.combining` for the
  A-reference ops, and `ord(c) < 128` for the R ASCII op) is diffed against an
  in-process replica of the POST-PATCH `strip_accents_unicode` over ≥1e5 fuzzed
  unicode strings, including pre-composed accents, decomposed sequences, bare
  combining marks, and multi-mark glyphs (the F2P inputs).
