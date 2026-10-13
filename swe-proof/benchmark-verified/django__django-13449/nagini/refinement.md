# refinement.md — django__django-13449

The operation-by-operation correspondence between `model.py`'s implementation
(the `window_as_sqlite` impl region, and the `compile_operand` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed**, the proof uses the axiom's
`Ensures`; or **A-reference**, a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed site — `Window.as_sqlite` (`django/db/models/expressions.py`)

Gold hunk (added method + `SQLiteNumericMixin` base):
```python
-class Window(Expression):
+class Window(SQLiteNumericMixin, Expression):
 ...
+    def as_sqlite(self, compiler, connection):
+        if isinstance(self.output_field, fields.DecimalField):
+            copy = self.copy()
+            source_expressions = copy.get_source_expressions()
+            source_expressions[0].output_field = fields.FloatField()
+            copy.set_source_expressions(source_expressions)
+            return super(Window, copy).as_sqlite(compiler, connection)
+        return self.as_sql(compiler, connection)
```

| # | model.py impl op (`window_as_sqlite`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `operand: List[int]`, `window: List[int]` | the source-expression SQL and the window SQL (`expr_sql` / `''.join(window_sql)` inside `as_sql`) | R | SQL fragment `str` ↔ `List[int]` token sequence (mapping.md §2). `window` abstracts the already-built `PARTITION BY ... ORDER BY ...` text, which the patch does not change. |
| A2 | `decimal_out: bool` and the `if decimal_out:` branch; `operand_decimal: bool` for the operand's own type | `if isinstance(self.output_field, fields.DecimalField):`; the operand's own `output_field.get_internal_type() == 'DecimalField'` read by its own rendering | R | `decimal_out` abstracts the `isinstance(self.output_field, fields.DecimalField)` guard — the only window-output property the branch reads; `operand_decimal` abstracts the corresponding property of the inner operand's own declared output, consumed only on the non-decimal window branch (mapping.md §2). |
| A3 | `inner = list(operand)` with `ToSeq(inner) == compile_operand(ToSeq(operand), False)` | `source_expressions[0].output_field = fields.FloatField(); copy.set_source_expressions(...)` then compiling the source | A-consumed | forcing the source operand to a `FloatField` output makes the operand's own `SQLiteNumericMixin.as_sqlite` take the NON-decimal branch, so the operand is rendered verbatim. The proof consumes `compile_operand(operand, False) == operand` (the axiom's non-decimal `Ensures`). G-AX validates that branch against the real `SQLiteNumericMixin.as_sqlite` (mapping.md §3.1). |
| A4 | `over = inner + [' OVER ('] + window + [')']`, i.e. `ToSeq(over) == over_clause(inner, window)` | `Window.as_sql` template `'%(expression)s OVER (%(window)s)'` (the cast-less window text that `super().as_sqlite` calls via `self.as_sql`) | R | the template substitution ↔ the concatenation `inner + kw_over() + window + kw_over_close()` (mapping.md §2: `%`-template ↔ list `+`). |
| A5 | `if decimal_out:` → `result = ['CAST('] + over + [' AS NUMERIC)']`, i.e. `cast_numeric(over)` | `super(Window, copy).as_sqlite(...)` = `SQLiteNumericMixin.as_sqlite`, which wraps the whole `copy.as_sql(...)` (the OVER clause) in `CAST(... AS NUMERIC)` because `copy.output_field` is still `DecimalField` | A-consumed + R | the outer wrap is the SAME `'CAST(%s AS NUMERIC)' % sql` operation of `SQLiteNumericMixin.as_sqlite` applied to the WHOLE window fragment (`compile_operand(over, True) == cast_numeric(over)`); modeled directly as `cast_numeric(over)` (the literal token wrap, R) since the wrapped argument is the full clause, not the operand. |
| A6 | `else:` branch — `inner2 = compile_operand(operand, operand_decimal)`-shaped rendering (own cast iff `operand_decimal`), then `result = inner2 + [' OVER ('] + window + [')']` | `return self.as_sql(compiler, connection)` — the UNCHANGED rendering: `as_sql` compiles the source via `compiler.compile`, which dispatches to the operand's own `SQLiteNumericMixin.as_sqlite` (own cast iff its own output is decimal), then substitutes the OVER template; no outer cast | A-consumed + R | the non-decimal window branch returns the cast-less `<inner> OVER (<window>)` where the inner term is the operand's OWN rendering, `compile_operand(operand, operand_decimal)` — verbatim when the operand's own type is non-decimal, `CAST(<operand> AS NUMERIC)` when it is decimal (e.g. an explicit non-decimal `output_field` on the window over a decimal source column). Same control flow; R on the carrier type; the operand rendering is the audited axiom. |

The discriminating content of the change — the numeric cast wraps the WHOLE
`<inner> OVER (<window>)` clause (A5 applied to `over`, with the operand
un-cast via A3) rather than wrapping the operand alone — is exactly the
property the F2P test `test_lag_decimalfield` observes (valid SQL vs. the
`near "OVER": syntax error`). `model_prepatch.py` reproduces the pre-patch
shape (`Window` has no `as_sqlite`; the inner operand carries its own cast iff
its own type is decimal, and nothing ever wraps the windowed fragment): for a
decimal-output window over a decimal operand it produces
`over_clause(cast_numeric(operand), window)` =
`CAST(<operand> AS NUMERIC) OVER (<window>)` and **fails** the postcondition
`ToSeq(Result()) == cast_numeric(over_clause(compile_operand(operand, False),
window))`, which is exactly the spec sensing the change (G-DIFF). On the
non-decimal window branch the prepatch coincides with the (unchanged) real
behaviour, so the postcondition failure is attributable to the decimal branch
alone.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — where the numeric cast is placed relative to the `OVER` clause — is
expressed **structurally** with `cast_numeric` / `over_clause` over `PSeq[int]`
(A4, A5): the model spells out that the cast wraps `over` (the whole clause)
and the operand is rendered un-cast (A3). The only consumed axiom,
`compile_operand` (**A-consumed**), covers the **unchanged** callee
`SQLiteNumericMixin.as_sqlite` that the operand rendering delegates to on both
window branches (A3: forced non-decimal; A6: the operand's own type) and that
the outer wrap (A5, the `super().as_sqlite` it stands in for) also performs.
There is no A-reference and no dead axiom.

## C. verify(model) ⇒ resolved

`window_as_sqlite` verifies only if, on the decimal branch, its output equals
`cast_numeric(over_clause(compile_operand(operand, False), window))` — the cast
around the WHOLE OVER clause with the operand un-cast (A3–A5) — and, on the
non-decimal branch, equals the cast-less clause over the operand's OWN
rendering, `over_clause(compile_operand(operand, operand_decimal), window)`
(A6). By R (SQL `str` ↔
`List[int]` tokens, `%`-template ↔ concatenation) the verified renderer equals
the patched `Window.as_sqlite` on the tested fragments; by G-AX the
`compile_operand` axiom is the real `SQLiteNumericMixin.as_sqlite` (A-consumed),
and the end-to-end check confirms the real `Window.as_sqlite` places the cast
exactly as the postcondition demands. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the one
audited callee — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
