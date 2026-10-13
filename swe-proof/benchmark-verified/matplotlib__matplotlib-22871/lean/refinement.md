# refinement.md — matplotlib__matplotlib-22871

Operation-by-operation correspondence between `implementation_tickOffset`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH level/offset
decision loop inside `ConciseDateFormatter.format_ticks`). Tags: **R** type
refinement, **A-consumed** proof uses an axiom, **A-reference** deep model
validated == real callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut level : Nat := 5` | initial label level before the scan (the `elif level == 0: level = 5` fallback value; also where the scan begins, `range(5,-1,-1)`) | R |
| 2 | `let mut showOffset : Bool := s0` | `show_offset = self.show_offset` (running flag carried into the loop) | R |
| 3 | `for lvl in levels do` (`levels = [5,4,3,2,1,0]`) | `for level in range(5, -1, -1):` | R |
| 4 | `let column := colVals td lvl` | `unique = np.unique(tickdate[:, level])` (the column's distinct values) | R / deep |
| 5 | `if 1 < column.dedup.length then` | `if len(unique) > 1:` | R / deep |
| 6 | `level := lvl` | (Python: `level` IS the loop var; the chosen value is the current `level`) | I |
| 7 | `if decide (lvl < 2) && column.contains 1 then showOffset := false` | `if level < 2 and np.any(unique == 1): show_offset = False` | R / deep |
| 8 | `return (level, showOffset)` | `break` (exits the loop with the current `level`/`show_offset`) | R |
| 9 | `else if lvl = 0 then level := 5` | `elif level == 0: level = 5` | R |
| 10 | `return (level, showOffset)` (loop fell through) | loop ends; `level`/`show_offset` carry to the rest of `format_ticks` | R |

Notes:

- **Every step is R or I — no A.** The two numpy reads the patch combines are
  modeled DEEPLY, not axiomatized:
  - `len(np.unique(tickdate[:, level])) > 1` ↔ `1 < (colVals td lvl).dedup.length`
    (step 5). `np.unique` returns the SORTED distinct values; the code consumes
    only its LENGTH here, and `len(np.unique(c)) = ` number of distinct elements
    of `c` = `c.dedup.length`. The sorted ORDER `np.unique` also produces is never
    read, so `dedup` (set-faithful, order-irrelevant) is exact for this use.
  - `np.any(unique == 1)` ↔ `(colVals td lvl).contains 1` (step 7). `1` is in the
    distinct values iff `1` is in the column, so `np.any(np.unique(c) == 1)` =
    `1 ∈ c` = `c.contains 1`.
  Because both are spelled out over the column taken as input, the callees
  (`np.unique`, `np.any`) are neither consumed axioms nor A-references; the
  `axioms` region is empty and **G-AX skips**.

- **R vs I.** Step 6 is **I** (the chosen level is literally the current scan
  index in both). Steps 1–5, 7–10 are **R**: the Python objects (the numpy column
  `tickdate[:, level]`, the `np.unique`/`len`/`np.any` reads, the `range` scan,
  the boolean flag) are refined to `List Nat` columns, `dedup.length`,
  `contains`, the `levels` list, and `Bool` per the mapping.md bijection.

- **Control-flow faithfulness.** Python's `break` (after deciding at the first
  varying component) is the Lean early `return` inside the `for` (step 8). The
  Python `elif level == 0: level = 5` (all components constant) is the
  `else if lvl = 0` arm (step 9); when it fires the loop simply continues to its
  natural end and the fall-through `return` (step 10) yields `(5, s0)`. The scan
  order, the single decision point, and the two mutated outputs all match.

- **The fix itself** is step 7: pre-patch sets `show_offset = False` whenever the
  varying level is year/month (`level < 2`); post-patch additionally requires
  `np.any(unique == 1)`. The pre-patch impl (`Solution_prepatch.lean`) keeps the
  unconditional `if decide (lvl < 2) then showOffset := false`, which the spec
  rejects on any configuration where a coarse component varies but never takes the
  value `1` (the F2P scenario: months Feb–Aug, no January, year must still show).
  Its `correct_tickOffset` is therefore unclosable (G-DIFF). The spec-validation
  `example`s (deleted before shipping) confirm the spec accepts the post-patch
  `(level, show_offset)` and rejects the pre-patch flag on that 4-tick Feb–Aug
  configuration.

- **Out of scope of this triple** (unchanged by the patch, not modeled): the
  `num2date(...).timetuple()[:6]` decomposition producing `tickdate` (its output
  is the input `td`), the subsequent per-tick label `strftime` formatting, the
  seconds/microseconds trailing-zero trimming, and the final
  `offset_string = tickdatetime[-1].strftime(offsetfmts[level])` (gated on
  `show_offset`). The patch touches none of them; the only behavioral change is
  the extra `np.any(unique == 1)` conjunct on the `show_offset` decision, which
  this triple isolates.

- **G-CONF** mechanically refutes the R/I legs: it transliterates the REAL
  post-patch decision loop (`np.unique` / `len` / `np.any(unique == 1)` over
  `tickdate[:, level]`) as the ORACLE and diffs `(level, show_offset)` against the
  impl shadow over the discrete edge matrix plus ≥1e5 fuzzed `tickdate` draws. No
  A legs.
