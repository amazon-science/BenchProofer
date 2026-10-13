# refinement.md — django__django-14007

Operation-by-operation correspondence between `implementation_insertReturnedRows`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`SQLInsertCompiler.execute_sql` return path). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if returningFields.isEmpty then return []` | `if not self.returning_fields: return []` | R |
| 2 | `if canBatch then rows := batchRows` | `if can_return_rows_from_bulk_insert and len(self.query.objs) > 1: rows = self.connection.ops.fetch_returned_insert_rows(cursor)` | R |
| 3 | `else if canColumns then rows := [columnsRow]` | `elif can_return_columns_from_insert: assert len(objs)==1; rows = [self.connection.ops.fetch_returned_insert_columns(cursor, self.returning_params)]` | R |
| 4 | `else rows := [lastIdRow]` | `else: rows = [(self.connection.ops.last_insert_id(cursor, opts.db_table, opts.pk.column),)]` | R |
| 5 | `if anyConverter returningFields then rows := rows.map (convertRow returningFields)` | `cols = [field.get_col(opts.db_table) for field in self.returning_fields]; converters = self.get_converters(cols); if converters: rows = list(self.apply_converters(rows, converters))` | R |
| 6 | `return rows` | `return rows` | I |

Notes:

- **Every step is R or I — no A.** The added post-processing (applying each
  returning field's converter chain to the fetched rows) is modeled DEEPLY via
  `convertRow`/`applyChain`/`anyConverter`; SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op. The `axioms` region is empty; **G-AX skips**.
- **Ops 2–4** are the unchanged three backend pathways. The patch's only change to
  them is structural: `return X` becomes `rows = X` so that the converter step
  (op 5) can run on all of them uniformly. The raw rows each pathway produces
  (`fetch_returned_insert_rows`, `fetch_returned_insert_columns`,
  `last_insert_id`) are UNCHANGED and orthogonal to the fix, so they enter as
  grounded inputs (`batchRows`, `columnsRow`, `lastIdRow`); the R tag is the
  rows↔`List Row` and converter-chain↔`RetField.converters` bijection
  (mapping.md). None leaves an output component free: `result` is fully pinned.
- **Op 5 is the fix itself.** Pre-patch the three pathways `return` immediately,
  so the converter step never runs. The deep model: `get_converters` yields the
  per-field chains (carried in `RetField.converters`); `apply_converters` passes
  each row's cell `i` through field `i`'s chain (`convertRow` = positional `zip`
  + `applyChain` left-fold); the `if converters:` guard becomes `anyConverter`.
  The pre-patch impl (`Solution_prepatch.lean`) reproduces the bug by `return`ing
  the selected raw rows directly with no converter application — exactly the
  pre-patch control flow — so a field with a wrapping converter yields the raw,
  unwrapped value, failing the F2P assertion.
- The `opts = self.query.get_meta()` hoist and `field.get_col(opts.db_table)` in
  the patch are plumbing to obtain the column expressions fed to
  `get_converters`; their net effect is the per-field converter chain, which the
  model carries directly as `RetField.converters` (the bijection in mapping.md).
- **G-CONF** mechanically refutes the R/I legs (no A legs): a Python shadow of the
  impl is diffed against an in-process replica of the post-patch return path over
  ≥1e5 fuzzed inputs (all pathway flags × converter presence/absence).
