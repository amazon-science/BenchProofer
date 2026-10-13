# refinement.md — django__django-12039

Maps every operation in the two `implementation_*` impls to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed**, **A-reference**,
**I** (identical concrete op). No consumed/reference axioms: the entire fix is
modeled R/I and validated by G-CONF.

## `implementation_renderColumns` ↔ `Columns.__str__` (patch hunk 1, lines 84-91)

| Lean op | patch.diff op | tag |
|---|---|---|
| `columns.zipIdx.map (fun p => …)` then `String.intercalate ", "` | `', '.join(col_str(column, idx) for idx, column in enumerate(self.columns))` | R: `enumerate`↔`zipIdx`, `', '.join`↔`String.intercalate ", "` |
| `let mut col := quoteName p.1` | `col = self.quote_name(column)` (new line, post-patch) | I (under `quoteName` R) |
| `match suffixes[p.2]? with \| some suffix => … \| none => pure ()` | `try: suffix = self.col_suffixes[idx] … except IndexError: pass` | R: bounded index + `IndexError` ↔ `getElem?` `some`/`none` (mapping.md) |
| `if suffix ≠ "" then col := col ++ " " ++ suffix` | `if suffix: col = '{} {}'.format(col, suffix)` | I: non-empty test + single-space join |
| `return col` | `return col` | I |

This is exactly the post-patch `col_str`: quote first, append the positional hint
only if it is truthy (non-empty), space-separated. The prepatch
(`Solution_prepatch_1.lean`) instead does `col ++ suffix` unconditionally with no
space — the original `self.quote_name(column) + self.col_suffixes[idx]` — which
G-DIFF confirms cannot satisfy the spec.

## `implementation_renderIndexColumns` ↔ `IndexColumns.__str__` (patch hunk 2, lines 111-122)

| Lean op | patch.diff op | tag |
|---|---|---|
| `columns.zipIdx.map (fun p => …)` then `String.intercalate ", "` | `', '.join(col_str(column, idx) for idx, column in enumerate(self.columns))` | R (as above) |
| `let mut col := quoteName p.1 ++ " " ++ (opclasses[p.2]?.getD "")` | `col = '{} {}'.format(self.quote_name(column), self.opclasses[idx])` | R: `opclasses[idx]` total-ized as `getD ""` (in-range for real inputs, mapping.md) |
| `match suffixes[p.2]? with \| some suffix => … \| none => pure ()` | `try: suffix = self.col_suffixes[idx] … except IndexError: pass` | R (as above) |
| `if suffix ≠ "" then col := col ++ " " ++ suffix` | `if suffix: col = '{} {}'.format(col, suffix)` | I: non-empty test + single-space join |
| `return col` | `return col` | I |

The prepatch (`Solution_prepatch_2.lean`) appends `' ' + suffix`
unconditionally — the original `col = '{} {}'.format(col, self.col_suffixes[idx])`
— leaving a trailing space for an empty hint (the `text_pattern_ops ` bug).
G-DIFF confirms it cannot satisfy the spec.

## Inexpressible ops

None. `self.quote_name` is universally quantified (no axiom). Every changed op is
R or I; nothing changed is left inexpressible or axiomatized.
