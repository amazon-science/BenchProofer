# refinement.md — astropy__astropy-14508

Operation-by-operation correspondence between `implementation_formatFloat`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_format_float`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut valueStr := normE inp.reprStr` | `value_str = str(value).replace("e", "E")` | R |
| 2 | `let strLen := valueStr.length` | `(str_len := len(value_str))` (the walrus in the `if`) | I |
| 3 | `if strLen > 20 then …` | `if (str_len := len(value_str)) > 20:` | I |
| 4 | `match valueStr.findIdx? (· = 'E') with | none => … | some idx => …` | `idx = value_str.find("E"); if idx < 0: … else: …` | R |
| 5 | `none => valueStr := valueStr.take 20` | `value_str = value_str[:20]` (no `E`, truncate decimals) | I |
| 6 | `some idx => valueStr := valueStr.take (20 - (strLen - idx)) ++ valueStr.drop idx` | `value_str = value_str[: 20 - (str_len - idx)] + value_str[idx:]` | I |
| 7 | `return valueStr` | `return value_str` | I |

Notes:

- **Op 1 is the fix.** Post-patch, `value_str` is built from `str(value)` — the
  value's *shortest* standard textual form — with any lower-case `e` upper-cased
  (`.replace("e","E")`). The pre-patch built it from `f"{value:.16G}"`, a
  fixed-precision form carried to 16 significant digits, plus an exponent-padding
  normalization and a `".0"` append. The patch DELETES that whole construction.
  In the model the two carriers are the grounded inputs `inp.reprStr`
  (`str(value)`) and `inp.fixedStr` (`f"{value:.16G}"`); the post-patch impl
  consumes `reprStr`, the pre-patch impl (`Solution_prepatch.lean`) consumes
  `fixedStr`. This is the single discriminating clause: a value such as
  `0.009125` whose `str()` form already fits must NOT be expanded to
  `0.009124999999999999`.
- **`normE` (R).** `str(value).replace("e","E")` maps every `e`→`E`; modeled as
  `List.map (e↦E)`. Tagged R because it refines the Python `str.replace` of a
  single substring `"e"` (which, for a numeric repr, only ever appears as the
  exponent marker) to a per-character map; the bijection is in mapping.md.
- **Ops 2,3,5,6,7 are I.** The 20-character budget logic is UNCHANGED by the
  patch (only the walrus rewrite of `str_len`, cosmetic). `value_str.find("E")`
  returns `-1` when absent → modeled as `Option`/`findIdx?` with the `none`
  branch = "no exponent marker"; the slice arithmetic is transliterated exactly:
  `value_str[:20]` = `take 20`; `value_str[:20-(str_len-idx)] + value_str[idx:]`
  = `take (20-(strLen-idx)) ++ drop idx`. (`idx < 0` ⇔ `findIdx? = none`.)
- **Op 4 is R** only in the `find→Option` carrier refinement (`-1` sentinel ↔
  `none`); the branch SELECTION and bodies are identical concrete ops.
- **No A tags.** The shortening rule is modeled DEEPLY; `str(value)` /
  `f"{value:.16G}"` are not callees the spec axiomatizes — they are the grounded
  textual observations of the value (the inputs). The `axioms` region is empty;
  **G-AX skips**.
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the POST-PATCH `_format_float`
  over ≥1e5 fuzzed `(reprStr, fixedStr)` inputs, including real `str(value)`
  outputs of random floats.
