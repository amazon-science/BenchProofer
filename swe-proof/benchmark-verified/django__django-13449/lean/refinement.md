# refinement.md — operation correspondence (django__django-13449)

Maps every op in `implementation_renderWindowSql` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python adds `Window.as_sqlite`. For a decimal output type it renders
the windowed expression and feeds the *whole* rendered string to the numeric-cast
wrapper (`SQLiteNumericMixin.as_sqlite` → `'CAST(%s AS NUMERIC)' % sql`); for a
non-decimal type it renders the bare windowed expression. We model the windowed
render and the cast wrapper as their equivalent fixed-order concatenations, and
the decimal branch deeply.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `operand : List Char` | the compiled source-expression SQL (`%(expression)s` slot); for the decimal path its inner decimal type is cleared so it renders cast-free | R | str ↔ List Char bijection (mapping.md); the operand text is passed through unchanged, and clearing its inner type is exactly what makes the modeled `operand` cast-free |
| 2 | `window : List Char` | the assembled window-clause SQL (`%(window)s` slot: `PARTITION BY …`/` ORDER BY …`/frame) | R | str ↔ List Char bijection; window-clause text passed through unchanged |
| 3 | `operand ++ " OVER (" ++ window ++ ")"` | substitution into the literal template `'%(expression)s OVER (%(window)s)'` by `Window.as_sql` (via `super().as_sqlite` / `as_sql`) | I | identical concrete op: substitution into a fixed literal template is fixed-order concatenation with the literal ` OVER (` and `)` separators |
| 4 | `let mut sql := <windowed expr>` then `if isDecimal then sql := "CAST(" ++ sql ++ " AS NUMERIC)"` | `as_sqlite` decimal branch: render `expression OVER (window)` then wrap the whole string via `SQLiteNumericMixin.as_sqlite`'s `'CAST(%s AS NUMERIC)' % sql`; non-decimal branch returns `self.as_sql(...)` | R/I | the **changed op** modeled deeply: the cast wraps the *entire* windowed expression as a unit. `'CAST(%s AS NUMERIC)' % sql` is the fixed-order concatenation `'CAST(' + sql + ' AS NUMERIC)'` (I); the branch selection is modeled deeply (R). NOT axiomatized. |
| 5 | `return …` | the returned `sql` of the call | I | the returned `params` list is unaffected by the fix and is out of model scope (mapping.md) |

No A-consumed rows: the proof discharges the concatenation directly; no UNCHANGED
callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: both callees (the template substitution and the cast
wrapper) are reproduced concretely as I ops, not abstracted behind a model that
needs G-AX validation. No changed-inexpressible op.

The discriminating clause is row 4 under `isDecimal = true`: the post-patch
rendering casts the whole `operand ++ " OVER (" ++ window ++ ")"` unit, i.e.
`"CAST(" ++ windowedExpr ++ " AS NUMERIC)"`. The prepatch impl casts only the
operand and appends ` OVER (window)` *outside* the cast, yielding
`"CAST(" ++ operand ++ " AS NUMERIC) OVER (" ++ window ++ ")"`, which differs from
the frozen `problem_spec_renderWindowSql` whenever `isDecimal = true` (and
`window` is anything — the suffix structure differs even for empty operand/window
because the closing `AS NUMERIC)` lands in a different position). Hence prepatch
`correct_renderWindowSql` cannot close — the G-DIFF signal. The `isDecimal = false`
branch is identical in both, matching the patch's non-decimal fall-through.
