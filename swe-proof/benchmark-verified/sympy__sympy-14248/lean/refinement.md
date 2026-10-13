# refinement.md — sympy__sympy-14248

Modeled routine: `_print_MatAdd` (the additive-term recombination), modeled as
`implementation_renderSum : List String → String`. The `str.py` and `latex.py`
patch bodies share this algorithm verbatim; the model covers both. Every op below
is **I** (identical concrete op) or **R** (type refinement). There is **no callee**
— no A-consumed and no A-reference. `conf_skip = false` (impl region is all R/I).

## patch.diff (`_print_MatAdd`, str.py:314 / latex.py:1479) ↔ implementation_renderSum

| # | patch.diff op | Lean impl op | tag | bijection |
|---|---|---|---|---|
| 1 | `terms = [self.parenthesize(arg, …) for arg in expr.args]` (the rendered summand list) | function input `terms : List String` | R | `list[str]` ↔ `List String`; the already-rendered summand list IS the modeled input. The renderer that produces it is upstream / out of scope. |
| 2 | `l = []` | `let mut l : List String := []` | I | empty working list |
| 3 | `for t in terms:` | `for t in terms do` | I | iterate summands in order |
| 4 | `if t.startswith('-'):` | `if t.startsWith "-" then` | R | `str.startswith('-')` ↔ `String.startsWith "-"` |
| 5 | `sign = "-"; t = t[1:]; l.extend([sign, t])` | `l := l ++ ["-", t.drop 1]` | R | `t[1:]` ↔ `t.drop 1`; `l.extend([a,b])` ↔ `l ++ [a,b]` |
| 6 | `else: sign = "+"; l.extend([sign, t])` | `else l := l ++ ["+", t]` | I/R | `"+"` connective + verbatim body appended |
| 7 | `sign = l.pop(0)` | `let firstSign := l.headD "+"; let rest := l.tail` | R | `l.pop(0)` returns head and removes it; modeled as `headD "+"` (value) + `tail` (remainder). `headD`'s default is irrelevant for non-empty `l`; for empty `terms` the join is `""` either way. |
| 8 | `if sign == '+': sign = ""` | `let firstSign := if firstSign = "+" then "" else firstSign` | I | elide a leading `+`; keep a leading `-` |
| 9 | `return sign + ' '.join(l)` | `return firstSign ++ String.intercalate " " rest` | R | `' '.join` ↔ `String.intercalate " "`; `+` ↔ `++` |

## pure helpers
`signParts` is the spec-side functional fold mirroring ops 2–6 (front append fold);
`renderSum` mirrors ops 7–9. They are the logical predicate's witness, proven equal
to the imperative loop by the proof agent (Route-B accumulator induction over
`List.forIn_cons`).

## Edge handling
- Empty `terms`: `l = []`, `headD "+" = "+"` → `""`, `intercalate " " [] = ""` → result `""`. Matches Python: `l.pop(0)` would raise on empty, but `expr.args` of a `MatAdd` is never empty, so this branch is unreachable in practice and the Lean total model returns `""` harmlessly.
- Single term `["A"]` → `"A"`; `["-A"]` → `"-A"` (first connective elided / kept).

## G-CONF
The R/I legs are differential-tested by `conformance_check.py` over ≥10⁵ fuzzed
`List[str]` inputs (seed 14248): oracle = faithful post-patch `_print_MatAdd`,
shadow = op-for-op transliteration of `implementation_renderSum`.
