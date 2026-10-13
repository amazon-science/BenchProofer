# mapping.md — django__django-13449

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 2a55431a5678af52f669ffe7dff3dd0bd21727f8`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `window_as_sqlite(operand, window, decimal_out)` | `Window.as_sqlite(self, compiler, connection)` — added at `django/db/models/expressions.py:1335` (post-patch); the changed function. Pre-patch `Window` (class `django/db/models/expressions.py:1256`) had NO `as_sqlite`, so its SQLite rendering was the inherited generic `Expression.as_sql` (`Window.as_sql`, line 1300). | the modeled changed function (SQLite rendering of a windowed expression) |
| `compile_operand(operand, operand_is_decimal)` *(axiom — A-consumed)* | `SQLiteNumericMixin.as_sqlite` — `django/db/models/expressions.py:18-28` (UNCHANGED) | the unchanged callee that renders an operand on SQLite: wraps `CAST(<sql> AS NUMERIC)` iff `output_field.get_internal_type() == 'DecimalField'`, else verbatim |
| `cast_numeric(x)` | the `'CAST(%s AS NUMERIC)' % sql` wrapping inside `SQLiteNumericMixin.as_sqlite` (line 26) AND the `super(Window, copy).as_sqlite(...)` wrapping the whole window in the patched `Window.as_sqlite` (line 1342) | pure spec: the numeric cast wrapper |
| `over_clause(inner, window)` | the `template = '%(expression)s OVER (%(window)s)'` substitution in `Window.as_sql` (line 1257 template; built at lines 1346-1349) | pure spec: the windowed fragment `<inner> OVER (<window>)` without cast |
| `kw_over / kw_over_close / cast_open / cast_close` | the literal template/cast tokens `' OVER ('`, `')'`, `'CAST('`, `' AS NUMERIC)'` | pure spec: the literal token sequences |
| `decimal_out` (bool) | `isinstance(self.output_field, fields.DecimalField)` — the patched `Window.as_sqlite` guard (line 1336) | abstracts "the windowed expression's declared output is the fixed-precision decimal type" |
| `operand_decimal` (bool) | `source_expressions[0].output_field.get_internal_type() == 'DecimalField'` — the property of the INNER operand's own declared output that its own `SQLiteNumericMixin.as_sqlite` reads when the window takes the non-decimal branch (`self.as_sql` compiles the source by its own type) | abstracts "the inner operand's own declared output is the fixed-precision decimal type" (independent of `decimal_out`: an explicit non-decimal `output_field` on the window over a decimal source column makes them differ) |

The patched `Window.as_sqlite` (gold) does:
```python
def as_sqlite(self, compiler, connection):
    if isinstance(self.output_field, fields.DecimalField):
        copy = self.copy()
        source_expressions = copy.get_source_expressions()
        source_expressions[0].output_field = fields.FloatField()
        copy.set_source_expressions(source_expressions)
        return super(Window, copy).as_sqlite(compiler, connection)   # mixin wraps WHOLE window
    return self.as_sql(compiler, connection)                          # no cast
```
`super(Window, copy).as_sqlite` is `SQLiteNumericMixin.as_sqlite`, which calls
`copy.as_sql(...)` (the full `<expr> OVER (<window>)`) and wraps it in
`CAST(... AS NUMERIC)` because `copy.output_field` is still a `DecimalField`.
The source expression's output field is forced to `FloatField` first, so the
inner operand (`Lag`, itself a `SQLiteNumericMixin`) is rendered WITHOUT its own
cast. Net: `CAST( <floatexpr> OVER (<window>) AS NUMERIC)`.

On the non-decimal branch (`return self.as_sql(...)`), the patch changes
NOTHING about the operand's rendering: `Window.as_sql` compiles the source
expression through `compiler.compile`, which dispatches to the operand's own
`SQLiteNumericMixin.as_sqlite` — so the operand keeps its OWN numeric cast iff
its OWN declared output is decimal. This matters when the two declared outputs
differ (e.g. an explicit `FloatField()` `output_field` on the `Window` over a
decimal source column): the real rendering is
`CAST(<operand> AS NUMERIC) OVER (<window>)` with NO outer cast. The model
captures this with the separate `operand_decimal` bool:
`over_clause(compile_operand(operand, operand_decimal), window)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| SQL fragment `str` (the `(sql, params)` text returned by `as_sql`/`as_sqlite`) | `List[int]` of token code points; specification over `PSeq[int]` via `ToSeq` | `s[k]` ↔ `ord(token)`; `str` `%`-template substitution and `CAST(%s AS NUMERIC)` ↔ list/`PSeq` concatenation `head + x + tail`; empty fragment ↔ `[]` |
| `params` list returned alongside the SQL | omitted | the bug and F2P test are about SQL *text structure* (the `near "OVER": syntax error`); params are threaded unchanged by every branch and are observationally identical, so they are not modeled |
| `isinstance(self.output_field, fields.DecimalField)` | `decimal_out: bool` | the only property of the window's output field the branch reads |
| the inner operand's own `output_field.get_internal_type() == 'DecimalField'` | `operand_decimal: bool` | the only property of the operand's own output field its rendering reads (consumed on the non-decimal window branch, where the operand renders by its own type) |
| `source_expressions[0].output_field = fields.FloatField()` then compile | `compile_operand(operand, False)` (operand rendered as non-decimal ⇒ verbatim) | forcing the source to a float output means the operand's own `SQLiteNumericMixin.as_sqlite` takes the non-decimal branch ⇒ no inner cast (decimal window branch only) |
| the inner operand's SQLite rendering (`compiler.compile(source_expression)` via `SQLiteNumericMixin.as_sqlite`) | `compile_operand(operand, operand_is_decimal)` axiom | §3 |

`str` indexing/iteration is banned in Nagini, so SQL fragments are `List[int]`;
the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `compile_operand` ↔ `SQLiteNumericMixin.as_sqlite` (A-consumed)
**Callee:** `django/db/models/expressions.py:18-28`, UNCHANGED by the patch:
```python
class SQLiteNumericMixin:
    def as_sqlite(self, compiler, connection, **extra_context):
        sql, params = self.as_sql(compiler, connection, **extra_context)
        try:
            if self.output_field.get_internal_type() == 'DecimalField':
                sql = 'CAST(%s AS NUMERIC)' % sql
        except FieldError:
            pass
        return sql, params
```
This is the operand-rendering callee that the windowed expression delegates to
(`super(Window, copy).as_sqlite` is exactly this method; the inner `Lag` source
also inherits it). The axiom encodes the **weakest** contract the proof needs:

  `compile_operand(operand, True)  == CAST(<operand> AS NUMERIC)` (= `cast_numeric(operand)`)
  `compile_operand(operand, False) == <operand>` (verbatim)

The proof of `window_as_sqlite` consumes **both** branches: the decimal-output
window branch consumes the **non-decimal** case
(`compile_operand(operand, False) == operand` — the patched code forces the
source expression to a `FloatField` output before compiling it, so the operand
returns un-cast), and the non-decimal-output window branch consumes the case
matching the operand's own declared type
(`compile_operand(operand, operand_decimal)` — the unchanged `as_sql` path
compiles the source by its own type, so a decimal-typed operand keeps its own
cast). The prepatch exercises the same operand-side rendering with no outer
cast ever added.

**Flag/config dependency (record for G-AX):** the cast is applied iff
`output_field.get_internal_type() == 'DecimalField'`; G-AX must fuzz both the
`DecimalField` and non-`DecimalField` (Float, Integer) output-field cases. The
`get_internal_type()` of `DecimalField` is the literal `'DecimalField'`
(`django/db/models/fields/__init__.py:1442`); `FloatField` (line 1725) returns
`'FloatField'`.

**Soundness check (G-AX):** `axiom_check.py` instantiates the REAL
`SQLiteNumericMixin.as_sqlite` (via a minimal stub whose `as_sql` returns a
chosen `(sql, [])`) against an SQLite `connection`, for `DecimalField`,
`FloatField`, `IntegerField` output fields, over 7 boundary operand SQLs plus
2000 randomized fuzz strings, and asserts the result equals the axiom's
`Ensures` exactly. It also exercises the patched `Window.as_sqlite`
end-to-end and asserts the numeric cast wraps the WHOLE `... OVER (...)` clause
(`CAST(` before `OVER`, ` AS NUMERIC)` after, and no `AS NUMERIC) OVER`),
i.e. the operand is rendered un-cast. Imports only Django (the repo under test)
and stdlib. Exit 0 iff sound.

The pre-patch repo facts the change relies on (for the refinement audit, not
referenced from the consumer spec view): `Window` did not inherit
`SQLiteNumericMixin`, so it had no `as_sqlite` and used the cast-less
`Window.as_sql`; meanwhile the inner `Lag` (a `Func`, `expressions.py:633`,
which IS a `SQLiteNumericMixin`) carried its own `DecimalField` output and
therefore got `CAST(... AS NUMERIC)` around just the `LAG(...)` operand —
producing `CAST(LAG(...) AS NUMERIC) OVER (...)`, the `near "OVER": syntax
error` of the issue.
