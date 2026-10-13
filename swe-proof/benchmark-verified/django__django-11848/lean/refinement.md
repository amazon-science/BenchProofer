# refinement.md — django__django-11848

Operation correspondence between `implementation_expandYear` (Solution.lean) and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: the two-digit-year expansion block of `parse_http_date`

The patch replaces the hard-coded pivot (`year < 70 → +2000 else +1900`) with a
computation relative to the current year: place the two-digit year in the current
century, rolling back one century when that would put it more than 50 years in
the future. `current_year` is read from `datetime.datetime.utcnow().year`; under
the type bijection it is the modeled input `currentYear`.

| # | `implementation_expandYear` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `year : Int` input | `year = int(m.group('year'))` | R | Python `int` ↔ Lean `Int` (mapping.md). Entry point of the modeled block. |
| 2 | `currentYear : Int` input | `current_year = datetime.datetime.utcnow().year` | R | The reference current year, modeled as an explicit input (the test mocks `utcnow`, confirming the block is a pure function of `(year, currentYear)`). Python `int` ↔ Lean `Int`. |
| 3 | `let mut y := year; if year < 100 then …; return y` | `if year < 100:` guarding the expansion (values ≥ 100 unchanged) | I | identical control flow: only two-digit years are rewritten. |
| 4 | `let currentCentury := currentYear - currentYear % 100` | `current_century = current_year - (current_year % 100)` | I | identical integer arithmetic; `%` agrees for `currentYear ≥ 0` (mapping.md). |
| 5 | `if year - currentYear % 100 > 50 then y := y + currentCentury - 100` | `if year - (current_year % 100) > 50: year += current_century - 100` | I | identical branch condition and update — the "more than 50 years in the future ⇒ past century" case. |
| 6 | `else y := y + currentCentury` | `else: year += current_century` | I | identical default-century update. |

Every op is I (with the two input bindings R). There is **no consumed axiom** and
**no opaque callee** (the `axioms` region is empty). `currentYear % 100` is the
only operation whose Lean/Python semantics could differ; on the modeled domain
(`currentYear ≥ 0`, real-world year) Lean `Int.emod` and Python `%` coincide,
which G-CONF exercises over fuzzed inputs.

The proof discharges by integer arithmetic / case analysis on `year < 100` and on
the pivot comparison; no induction is required.

## Prepatch (G-DIFF)

`Solution_prepatch.lean` carries the pre-patch impl (hard-coded `year < 70 →
+2000 else +1900`, ignoring `currentYear`). Its `correct_expandYear` is
unclosable: e.g. for `year = 70, currentYear = 2020`, the spec demands `result =
2070` (`year + cc = 2070 ≤ 2070 = currentYear + 50`) but the prepatch yields
`1970`, violating both `result % 100 = year` is fine but `result = year + cc`
fails (1970 ≠ 2070). One independently-observable fixed behavior ⇒ one prepatch.
