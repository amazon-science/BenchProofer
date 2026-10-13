# refinement.md — django__django-13449

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`windowNumericSql` `do` block and its deep model `windowSql` / `numericCast` /
`overClause`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** / **A-reference** (axiomatized callee — none here),
or **I** (identical concrete op). The R/I legs are mechanically refuted by
**G-CONF** (`conformance_check.py`, §4.1); the narrative is audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE; confirmed applies clean
at base_commit and identical to `instance.json` `patch`).

## A. The SQLite window-rendering site — `Window.as_sqlite`

The single F2P-observable behaviour the fix changes is *where the numeric cast
lands relative to the OVER clause* when the windowed expression's result is a
fixed-precision decimal. Gold hunk (the added `Window.as_sqlite`,
`django/db/models/expressions.py:1335`, plus `class Window(SQLiteNumericMixin,
Expression)`):

```
+    def as_sqlite(self, compiler, connection):
+        if isinstance(self.output_field, fields.DecimalField):
+            # Casting to numeric must be outside of the window expression.
+            copy = self.copy()
+            source_expressions = copy.get_source_expressions()
+            source_expressions[0].output_field = fields.FloatField()
+            copy.set_source_expressions(source_expressions)
+            return super(Window, copy).as_sqlite(compiler, connection)
+        return self.as_sql(compiler, connection)
```

`super(Window, copy).as_sqlite` is `SQLiteNumericMixin.as_sqlite`, which wraps
`copy.as_sql(...)` (the `expression OVER (window)` template) in
`CAST(%s AS NUMERIC)` because `copy.output_field` is still the `DecimalField`.
Rewriting the operand's `output_field` to `FloatField` means the operand's own
`as_sqlite` no longer self-casts, so the operand SQL inside the OVER expression
carries NO inner cast (mapping.md §1.1).

| # | Solution.lean impl op (`windowNumericSql`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `isDecimal : Bool`, `innerBase : List Char`, `win : List Char` | `isinstance(self.output_field, DecimalField)`; the operand SQL after the float-rewrite; the assembled window clause `''.join(window_sql).strip()` | R | type bijection (mapping.md §2). G-CONF supplies all three directly via the real `Window.as_sqlite` driven over a `SQLiteNumericMixin` operand. None is `mut` (directive 5): the rendering reads them and leaves them unchanged. |
| A2 | decimal branch `isDecimal → numericCast (overClause innerBase win)` | `isinstance(output_field, DecimalField)` true → `super().as_sqlite` = `CAST( <as_sql OVER expression> AS NUMERIC)` over the float-rewritten operand | I | `overClause innerBase win` ≡ `Window.as_sql`'s `expression OVER (window)`; `numericCast (...)` ≡ `SQLiteNumericMixin`'s `CAST(... AS NUMERIC)`. The CHANGED placement: the cast wraps the WHOLE OVER expression, and `innerBase` carries no inner cast. Transliterated concretely; G-CONF refutes any mismatch. |
| A3 | non-decimal branch `→ overClause innerBase win` | output not a `DecimalField` → `return self.as_sql(...)` (plain OVER template, no cast) | I | the unchanged plain-window rendering. Observable as `overClause innerBase win`. G-CONF covers it across float/integer/bigint tags. |
| A4 | output `out : List Char` | the SQL string `Window.as_sqlite` returns (`sql`, used by the compiler) | R | `str` ↔ `List Char` bijection (mapping.md §2); the rendered SQL string is the observable. |

The discriminating content of the change — on the decimal arm the cast wraps the
ENTIRE windowed expression, `CAST(<operand> OVER (<window>) AS NUMERIC)`, NOT the
operand alone — lives in `windowSql`'s decimal branch
`numericCast (overClause innerBase win)`. Pre-patch the cast wrapped the OPERAND
ALONE and the cast operand was then placed before the OVER clause, yielding
`CAST(<operand> AS NUMERIC) OVER (<window>)` (the invalid SQL the issue reports:
`near "OVER": syntax error`). `Solution_prepatch.lean` reproduces that placement
(`overClause (numericCast innerBase) win`) and **fails** `out = windowSql …`
exactly on the decimal clause (G-DIFF; the proof's `simp_all` cannot equate
`overClause (numericCast innerBase) win` with `numericCast (overClause innerBase
win)`).

## B. Supporting change (R — audit only)

The gold patch's other line, `class Window(SQLiteNumericMixin, Expression)`, only
makes `super(Window, copy).as_sqlite` resolve to `SQLiteNumericMixin.as_sqlite`
(the numeric-cast wrapper) — it adds the cast capability the decimal branch (A2)
uses and is otherwise inert (the mixin defines only `as_sqlite`). It is captured
by modeling `numericCast` as the cast wrapper in A2; no separate prepatch is
needed (a prepatch must keep the frozen spec byte-identical; G-DIFF). The single
independently observable fixed behaviour — the cast placement — is exercised by
the §A prepatch.

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the cast
placement relative to the OVER clause — is modeled **deeply** (the spelled-out
`windowSql` / `numericCast` / `overClause`, steps A2–A3, all I), not hidden
behind an axiom about the function under change. There is **no consumed axiom and
no A-reference**: the operand SQL, the window clause, and the decimal flag are
abstracted R-inputs (mapping.md §2), and the two string templates are unchanged
concrete repo operations, not foreign callees whose behaviour is assumed.

## D. verify(Solution) ⇒ resolved

`windowNumericSql` verifies only if its rendered SQL equals `windowSql` exactly —
in particular on the decimal arm the numeric cast wraps the entire OVER
expression (A2) and the operand carries no inner cast, and on the non-decimal arm
the expression renders as the plain OVER template (A3). By R (the `str ↔ List
Char` bijection of mapping.md §2) the verified rendering equals the patched
`Window.as_sqlite` output on every output-field tag and operand/window string;
by G-CONF the R/I transliteration of `windowSql` agrees with `patch.diff`'s
behaviour through the real patched `Window.as_sqlite` on the F2P scenario + 100
000 fuzzed inputs. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point (no axioms).
