# refinement.md — astropy__astropy-14365

Two independently-fixed behaviors, two CLEVER triples. Every impl op is tagged
**R** (type refinement), **A-consumed**, **A-reference**, or **I** (identical op).

## patch.diff (gold) operations
- **P1** `_line_type`: `re.compile(_type_re)` → `re.compile(_type_re, re.IGNORECASE)`
  — make line-category recognition case-insensitive.
- **P2** `_get_tables_from_qdp_file` value loop: `if v == "NO":` →
  `if v.upper() == "NO":` — make the missing-value sentinel test case-insensitive.

## Triple 1 — `implementation_classify` ↔ P1

| # | Lean impl op | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `matchCategory true line` | the recognizer match with `re.IGNORECASE` set (`_line_type_re.match(line)` returning the category, post-fix) | **A-reference** |

- `matchCategory` is the UNCHANGED regex recognizer; the patch only flips its
  mode flag (`re.IGNORECASE`), modeled by the `Bool` argument `true`. The patch
  does not alter the pattern/engine. The fix is the *selection of the
  case-insensitive mode*, captured by `implementation_classify = matchCategory
  true line` vs the prepatch's `matchCategory false line`.
- The spec `result = matchCategory true line` is discharged by `rfl` — it
  consumes **no** property axiom about the callee. The semantic content of the
  fix (the mode the issue demands actually IS case-insensitive — equal-up-to-case
  lines get the same category, and lower-case `read serr`/`no`/`nan` lines now
  classify as command/new/data instead of unrecognized) is the A-reference
  property validated by `axiom_check.py` (G-AX) against the real patched
  `_line_type`.
- No R/I leg → contributes nothing to G-CONF.

## Triple 2 — `implementation_readRow` ↔ P2

| # | Lean impl op | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `let mut acc := []` | `values = []` | **I** |
| 2 | `for v in tokens do …` | `for v in line.split(delimiter): …` (token iteration; the split itself is the I/O bridge, see mapping.md) | **I** |
| 3 | `if v.map Char.toUpper = ['N','O']` | `if v.upper() == "NO":` (the FIXED case-insensitive sentinel test) | **R** |
| 4 | `acc := acc ++ [Cell.missing]` | `values.append(np.ma.masked)` | **R** |
| 5 | `acc := acc ++ [Cell.number (parseNumber v)]` | `values.append(int(v) or float(v))` | **A-reference** (`parseNumber`) + **R** (the cell-tagging structure) |
| 6 | `return acc` | (`values` is the row) | **I** |

- **R rows** (3,4,5-structure): the case-fold sentinel decision and the
  cell-tagging (`missing` vs `number`) structure of the loop. Modeled deeply, not
  axiomatized — they ARE the changed behavior. Op 3 is the discriminator: the
  prepatch uses `v = ['N','O']` (case-sensitive) and fails G-DIFF.
- **A-reference** `parseNumber` (op 5 payload): the UNCHANGED number parser
  (`int(v)` else `float(v)`). The fix never reaches it for sentinel tokens; the
  spec only states a non-sentinel token maps to `number (parseNumber v)`. No
  property axiom consumed; validated by G-AX as the real parser.
- `Char.toUpper` (Lean) ↔ Python `str.upper()` for ASCII letters: the QDP
  sentinel `NO` and all case-variants are ASCII, so the ASCII-letter case fold is
  faithful (mapping.md bijection; G-CONF fuzzes this leg).
- The R/I legs of Triple 2 are mechanically differential-tested by G-CONF
  (`conformance_check.py`), with `parseNumber` left as the real repo parser.

## No changed-inexpressible op
Every changed operation is expressed: P1 as the mode-selection A-reference
(case-invariance validated by G-AX), P2 as the deeply-modeled case-fold sentinel
test + cell tagging (R, differential-tested by G-CONF). No op is axiomatized that
the patch changes.
