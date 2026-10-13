# refinement.md — astropy__astropy-14182

Two independently-observable changed sites in the simple reStructuredText
fixed-width format, one Lean triple each. Tags: **R** type-refinement,
**A-consumed** proof uses axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

## Site 1 — `implementation_rstWrap` ↔ `RST.write` bracketing line (rst.py:63-66)

patch.diff hunk:
```
     def write(self, lines):
         lines = super().write(lines)
-        lines = [lines[1]] + lines + [lines[1]]
+        idx = len(self.header.header_rows)
+        lines = [lines[idx]] + lines + [lines[idx]]
         return lines
```

| Lean impl op | patch.diff counterpart | tag |
|---|---|---|
| `let idx := numHeaderRows` | `idx = len(self.header.header_rows)` | R (`numHeaderRows` ↔ `len(self.header.header_rows)`) |
| `let sep := lines.getD idx ""` | `lines[idx]` | R (`List.getD` total read ↔ Python in-range index; `lines` ↔ the list `super().write(lines)` returned) |
| `let mut out := [sep] ++ lines ++ [sep]` | `lines = [lines[idx]] + lines + [lines[idx]]` | I (list concatenation, sep at both ends) |
| `return out` | `return lines` | I |

`super().write(lines)` is UNCHANGED by the patch — it is the fixed-width renderer
that lays out the header rows then the column-rule line then the data rows. The
patch only changes WHICH index of its output is bracketed; the rendered list is
therefore taken as an input observation (`lines`), not re-modeled, so it is not a
callee axiom (no A-reference). The historical `lines[1]` is the special case
`numHeaderRows = 1`.

## Site 2 — `implementation_rstDataStart` ↔ data start line (rst.py)

patch.diff hunks (the removed class constant + the new `read` override):
```
 class SimpleRSTData(FixedWidthData):
-    start_line = 3
     end_line = -1
     splitter_class = FixedWidthTwoLineDataSplitter
...
+    def read(self, table):
+        self.data.start_line = 2 + len(self.header.header_rows)
+        return super().read(table)
```

| Lean impl op | patch.diff counterpart | tag |
|---|---|---|
| `return 2 + numHeaderRows` | `self.data.start_line = 2 + len(self.header.header_rows)` | R (`numHeaderRows` ↔ `len(self.header.header_rows)`; the assigned int line index ↔ `result : Nat`) |

The removed `start_line = 3` class attribute is the historical constant — exactly
the value `2 + numHeaderRows` takes at `numHeaderRows = 1`. `super().read(table)`
is unchanged and orthogonal to the start-line computation; it is not modeled.

## Axioms

None. Both index computations are modeled deeply from `numHeaderRows`, so there
is no consumed axiom and no A-reference callee. `axiom_check.py` is a skip stub;
`conformance_check.py` differential-tests both R/I legs (no A legs), so
`conf_skip = false`.

## How the spec sees the bug (G-DIFF)

The discriminator is `numHeaderRows > 1` (the F2P round-trip uses three header
rows: name, unit, dtype).

- `Solution_prepatch_1.lean` fixes the index in `implementation_rstWrap` at the
  constant `1`. The spec brackets at index `numHeaderRows`; for three header rows
  the rule line is at index 3, not 1, so the carried gold `rfl` proof cannot
  close — exactly the `out.getvalue().splitlines() == lines` write assertion in
  the F2P test.
- `Solution_prepatch_2.lean` fixes `implementation_rstDataStart` at the constant
  `3`. The spec requires `2 + numHeaderRows`; for three header rows that is 5,
  not 3, so the carried gold `rfl` proof cannot close — exactly the
  `QTable.read(...)` round-trip parse in the F2P test.

Both prepatches reduce to the historical constants at `numHeaderRows = 1`, so the
PASS_TO_PASS single-header-row tests are preserved.
