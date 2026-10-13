# refinement.md — sympy__sympy-20916

Maps every operation in `implementation_splitTrailingDigits` (Solution.lean impl
region) to its `patch.diff` counterpart (the post-patch regex
`^([^\W\d_]+)(\d+)$` with `re.U`, applied via `_name_with_digits_p.match(name)`
at `sympy/printing/conventions.py:65-68`). Tags: **R** type refinement,
**A-consumed** proof uses this axiom's property, **A-reference** deep-model
validated == real callee (G-AX/G-CONF), **I** identical concrete op.

The fix is a regex character-class widening: the base class goes from ASCII
`[a-zA-Z]` to Unicode-letter `[^\W\d_]` and the subscript class from ASCII
`[0-9]` to Unicode-digit `\d`, both under `re.U`. The changed decision (the
letters-then-digits split) is modeled DEEPLY over the observable `name`; the two
character-classification primitives are the UNCHANGED library categories the
`re` engine consults, so they are A-reference (not axiomatized: the fix does not
change *what a Unicode letter/digit is*, only that those broader classes are
used).

| # | Lean op (impl region) | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `name : List Char` | the base token `name` passed to `_name_with_digits_p.match` | **R** — Python `str` ↔ `List Char`, per code point (mapping.md) |
| 2 | `isUnicodeLetter` | the regex class `[^\W\d_]` under `re.U` (a Unicode alphabetic char) | **A-reference** — unchanged library Unicode category; validated == real `re` classification by G-AX; drives G-CONF |
| 3 | `isUnicodeDigit` | the regex class `\d` under `re.U` (a Unicode decimal digit) | **A-reference** — unchanged library Unicode category; validated == real `re` classification by G-AX; drives G-CONF |
| 4 | `base := name.takeWhile isUnicodeLetter` | group 1 `([^\W\d_]+)` matches a maximal leading letter run | **R** — regex greedy `+` on the letter class ↔ `takeWhile` the letter predicate |
| 5 | `rest := name.dropWhile isUnicodeLetter` | what remains after group 1 (group 2 + the `$` position) | **R** — regex remainder ↔ `dropWhile` the letter predicate |
| 6 | `digits := rest.takeWhile isUnicodeDigit` | group 2 `\d+`: the maximal digit run after the letters | **R** — regex greedy `+` on `\d` ↔ `takeWhile` the digit predicate |
| 7 | `trailer := rest.dropWhile isUnicodeDigit` | what follows group 2, where `$` must match | **R** — post-group-2 remainder ↔ `dropWhile` the digit predicate |
| 8 | `!base.isEmpty` | group 1 `+` requires ≥1 letter | **R** — regex `+` ≥1 ↔ `¬ base.isEmpty` |
| 9 | `!digits.isEmpty` | group 2 `\d+` requires ≥1 digit | **R** — regex `+` ≥1 ↔ `¬ digits.isEmpty` |
| 10 | `trailer.isEmpty \|\| trailer == ['\n']` | the `$` anchor: matches at end of input OR just before ONE final `'\n'` (non-MULTILINE `re` semantics) | **R** — Python `$` end rule ↔ trailer empty or exactly `['\n']` |
| 11 | `return (base, some digits)` | `m` matches ⇒ `name, sub = m.groups()` (split performed; a tolerated final `'\n'` is outside both groups and dropped) | **I** — successful split carrier |
| 12 | `return (name, none)` | `m is None` ⇒ `name` left unchanged, no subscript peeled | **I** — no-split carrier |

Why the split is `takeWhile letter` + `takeWhile digit` + trailer check and not
two independent `match`es: the regex `^([^\W\d_]+)(\d+)$` is anchored at both
ends and the two classes are disjoint (`[^\W\d_]` excludes digits, `\d` is
digits). So a match exists iff the name is a maximal letter prefix (`takeWhile
isUnicodeLetter`) followed by a non-empty maximal digit run (`takeWhile
isUnicodeDigit` of the remainder) after which `$` matches. Crucially, Python's
non-MULTILINE `$` matches at end of string OR just before one final `'\n'`
(G-PANEL-2 found the earlier `tail.all isUnicodeDigit` model missed this:
oracle splits `"a1\n"` to `('a','1')`). Hence the trailer (what follows the
digit run) must be empty or exactly `['\n']`; any other trailer — including
`"\r"`, `"\n\n"`, a letter after a digit, or a non-final newline — means no
split. This is verified against Python's real `re` engine by G-CONF (rows 1,
4–12 are R/I; rows 2–3 A-reference are the class the engine evaluates), with
`\n`/`\r` in both the edge set and the fuzz alphabet.

## Prepatch (Solution_prepatch.lean)

Models the OLD regex `^([a-zA-Z]+)([0-9]+)$` (no `re.U`) as `takeWhile
Char.isAlpha` + `all Char.isDigit` — i.e. ASCII-only classification. Its
`correct_` (gold `simp` proof carried over) fails to typecheck against the spec
(the spec's `splitTrailingDigits` uses `isUnicodeLetter`/`isUnicodeDigit`; the
prepatch impl uses ASCII `Char.isAlpha`/`Char.isDigit`), leaving the
discriminating goal `ASCII classification = Unicode classification` — exactly the
G-DIFF signal that the spec sees the bug: the pre-patch impl fails to split
`ω1 → (ω, [1])`, `w𝟙 → (w, [𝟙])` (the F2P cases), whereas the spec splits them.

conf_skip = **false** (rows 1, 4–10 are R/I; G-CONF differential-tests them
against the real `re` engine, with the A-reference classes supplied by that
engine).
