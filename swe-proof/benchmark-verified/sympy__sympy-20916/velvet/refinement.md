# refinement.md — sympy__sympy-20916

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `splitTrailingDigits` `do` block plus the deep `pure`-region models it
calls) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
property), **A-reference** (a deep model / opaque recognizer validated == its
real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A-reference legs are validated by **G-AX** (`axiom_check.py`); the narrative
is audited by **G-EQ**. Claim: any impl verifying against this frozen spec,
refined per the map below, produces the same trailing-digit decomposition as the
gold patch on the tested names, so the F2P test `test_super_sub` passes and the
harness resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — the trailing-digit step of `split_super_sub`

Gold hunk (`sympy/printing/conventions.py:10`):
```
- _name_with_digits_p = re.compile(r'^([a-zA-Z]+)([0-9]+)$')
+ _name_with_digits_p = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)
```
consumed by the unchanged post-loop step (`conventions.py:65-68`):
```
m = _name_with_digits_p.match(name)
if m:
    name, sub = m.groups()
    subs.insert(0, sub)
```
The observable the F2P `test_super_sub` checks is the `split_super_sub(text)`
triple `(name, supers, subs)`.

| # | Solution.lean impl op (`splitTrailingDigits`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `name : List Char` | the `name` produced by the unchanged parsing loop | R | `str` ↔ `List Char` over code points (mapping.md §2). G-CONF bridges via `Char.ofNat (ord ch)` and feeds separator-free names (loop = identity). |
| A2 | `letters := letterPrefix name` = `name.takeWhile isLetterU` | the `([^\W\d_]+)` capture (maximal leading run of the letter class) | A-reference + I | the `takeWhile`/`dropWhile` split is concrete (I); the letter class `isLetterU` is the **A-reference** recognizer G-AX validates == `re.match(r'[^\W\d_]', c, re.U)`. The greedy `+` boundary = end of the maximal letter run because letter and digit classes are disjoint (axiom `letter_not_digit`); G-AX confirms the composite. |
| A3 | `rest := afterLetters name` = `name.dropWhile isLetterU` | the remainder the `(\d+)$` tail must cover | I + A-reference | concrete complement of A2; uses the same A-reference recognizer. |
| A3′ | `digits := stripFinalNewline rest` (drop ONE final `'\n'` if present) | the `$` anchor with no `re.M`: Python's `$` matches at end-of-string **or immediately before one final newline**, and that tolerated `'\n'` is NOT captured by `(\d+)` (e.g. `match("w1\n").groups() == ("w","1")`; `"w1\n\n"`/`"w1\r"` do not match) | I | concrete per-code-point op mirroring the documented `re` `$` semantics; since `'\n'` is neither a letter nor a digit, a tolerated final newline always sits at the very end of `rest`, so dropping it there is exactly the anchor's tolerance. G-AX confirms the composite against the live `re` engine on `"w1\n"`-family probes. |
| A4 | accept iff `letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU` | the anchored match `^([^\W\d_]+)(\d+)$` succeeding: non-empty letter group, non-empty all-digit tail covering the rest (up to one tolerated final newline) | A-reference + I | the two non-emptiness tests + the all-`isDigitU` tail mirror `[^\W\d_]+` and `\d+$` being non-empty and the `$` anchor (the tail up to one final newline is entirely digits). `isDigitU` is the **A-reference** for `\d` (G-AX validates == `re.match(r'\d', c, re.U)`). The boolean combination is concrete (I). |
| A5 | on match `(letters, some digits)`; else `(name, none)` | `if m: name, sub = m.groups(); subs.insert(0, sub)` (split) vs `m is None` (name + subs left intact) | R + I | `some`/`none` ↔ match/no-match; `(group1, group2)` ↔ `(letters, digits)` (mapping.md §2) — group 2 excludes any tolerated final newline, as does `digits`. The downstream `subs.insert(0, sub)` is the observable G-CONF reconstructs: `subs = [digits]` on a split, `subs = []` otherwise. |

## B. The discriminating change

Pre-patch the recognizer was ASCII-only (`[a-zA-Z]+[0-9]+`): a name whose
leading letters or trailing digits lay outside ASCII never matched, so the
trailing digits were NOT split off. E.g. `split_super_sub("ω1")` returned
`("ω1", [], [])` (the symptom: a Greek-led name kept its trailing digit glued
on, so the printer never rendered it as a subscript). Post-patch the Unicode
classes (`[^\W\d_]+\d+`, `re.U`) match it, giving `("ω", [], ["1"])`.

`Solution_prepatch.lean` reproduces the ASCII recognizer by computing the split
with Lean's built-in ASCII `Char.isAlpha`/`Char.isDigit` (which are exactly
ASCII-only — `'ω'.isAlpha = false`, `('𝟙').isDigit = false`; the `$` anchor's
one-final-newline tolerance is unchanged by the patch, so the skeleton keeps
`stripFinalNewline`) and **fails** `out = peelDigits name`: the spec demands
the Unicode decomposition (`isLetterU`/`isDigitU`), and on a Unicode name like
`ω1` the ASCII split yields `("ω1", none)` while `peelDigits` yields
`("ω", some "1")` — the discriminating clause is exactly the
`letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU` acceptance with the Unicode
classes (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — recognizing a
letter block / digit block over the FULL code-point space rather than ASCII — is
modeled **deeply**: the structural split `peelDigits` (concrete `takeWhile` /
`dropWhile` / `all`, tagged I) over two **A-reference** recognizers
`isLetterU`/`isDigitU`. There is **no consumed axiom about the function under
change**; the only axioms are (1) the two A-reference recognizers (the unchanged
per-code-point character classes the regex is built from) and (2) three
structural facts about those classes (disjointness; `_` excluded), all
executable-validated by G-AX. None pins an output value of the function under
spec.

## D. verify(Solution) ⇒ resolved

`splitTrailingDigits` verifies only if its output equals `peelDigits name` for
all `name` — i.e. it splits off a trailing digit block exactly when the name is
a maximal Unicode-letter run followed by a non-empty all-Unicode-digit tail
(with at most one tolerated final newline, mirroring the `$` anchor). By
R (`str ↔ List Char` over code points, match ↔ `some`) the verified function
equals the post-patch `_name_with_digits_p` decomposition on every tested name;
by G-AX the recognizers `isLetterU`/`isDigitU` equal the real `[^\W\d_]`/`\d`
classes and the composite `peelDigits` equals the real `_name_with_digits_p`
split (A-reference); by G-CONF the R/I transliteration agrees with `patch.diff`'s
`split_super_sub` behaviour on ≥10⁵ fuzzed names. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited recognizers — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: A-reference soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
