# mapping.md — django__django-13449

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2a55431a5678af52f669ffe7dff3dd0bd21727f8`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `windowNumericSql (isDecimal, innerBase, win)` | the SQLite rendering of a windowed expression — added as `Window.as_sqlite` by the patch, `django/db/models/expressions.py:1335` (post-patch); composed of the inherited `SQLiteNumericMixin.as_sqlite` numeric-cast wrapper (`expressions.py:23`) over the `Window.as_sql` OVER template (`expressions.py:1300`) | the modeled changed function: assembles the SQL string for a windowed expression on the cast-on-decimal backend |
| `numericCast (sql)` *(pure deep model — I)* | `'CAST(%s AS NUMERIC)' % sql` of `SQLiteNumericMixin.as_sqlite` (`expressions.py:26`) | pure spec: wrap a SQL fragment in a numeric cast |
| `overClause (expr, win)` *(pure deep model — I)* | `Window.template = '%(expression)s OVER (%(window)s)'` filled by `Window.as_sql` (`expressions.py:1257`, `1328-1331`) | pure spec: the `expression OVER (window)` template |
| `windowSql (isDecimal, innerBase, win)` *(pure deep model — R/I)* | the composition the patched `Window.as_sqlite` realises: `isinstance(self.output_field, DecimalField)` selects whether the numeric cast (inherited mixin) wraps the whole `as_sql` OVER expression, else plain `as_sql` | pure spec: the full rendered SQL string, the F2P-observable behaviour |

There are **no axioms** and **no deep-model references** in this bundle: the
only behaviour the fix changes — *where the numeric cast lands relative to the
OVER clause* — is modeled directly over abstracted string inputs. The two string
operations involved (`numericCast`, `overClause`) are UNCHANGED, shared
rendering steps transliterated concretely; nothing about a foreign callee is
consumed as a contract (refinement.md §C).

### 1.1 The fix mechanism (audit only — how the three inputs arise)

The bug: `Window` did not define `as_sqlite`, so the compiler dispatched to the
inner operand's `as_sqlite`. The operand of a decimal `Lag` is a `Func`
(`SQLiteNumericMixin`) whose `output_field` is `DecimalField`, so the OPERAND
self-cast — yielding `CAST(LAG(...) AS NUMERIC)` — and `Window.as_sql` then
wrapped that in `... OVER (...)`, producing `CAST(LAG(...) AS NUMERIC) OVER (...)`
(invalid SQLite: the cast closes before `OVER`).

The patch makes `Window` a `SQLiteNumericMixin` and gives it its own
`as_sqlite`: when `self.output_field` is a `DecimalField` it copies the node,
rewrites the operand's `output_field` to `FloatField` (so the operand does NOT
self-cast → `innerBase` carries no inner cast), builds the OVER expression via
`super().as_sqlite` (= `SQLiteNumericMixin.as_sqlite` over `Window.as_sql`),
and the mixin's numeric cast then wraps the WHOLE OVER expression →
`CAST(LAG(...) OVER (...) AS NUMERIC)`. The three modeled inputs:

- `isDecimal` ← `isinstance(self.output_field, fields.DecimalField)` (and
  `Window.output_field` = the source expression's output field,
  `Window._resolve_output_field`, `expressions.py:1292`);
- `innerBase` ← the operand SQL AFTER the float-rewrite, i.e. with no inner cast
  (`source_expressions[0].output_field = FloatField()`);
- `win`      ← the assembled window clause `Window.as_sql` produces inside the
  OVER parentheses (`''.join(window_sql).strip()`, `expressions.py:1330`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a SQL string (operand SQL, window clause, rendered expression) | `List Char` | Python `str` `s` ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`; per-character `Char.ofNat (ord ch)` ↔ `ch` (SQL is ASCII/BMP, total and exact) |
| `isinstance(self.output_field, fields.DecimalField)` (`bool`) | `isDecimal : Bool` | identity; `True` iff the windowed expression's resolved output type is `DecimalField` |
| the operand SQL after the float-rewrite (no inner cast) | `innerBase : List Char` | the abstracted R-input: the SQL of the operand the window is computed over, WITHOUT a numeric cast of its own |
| the assembled window clause (`''.join(window_sql).strip()`) | `win : List Char` | the abstracted R-input: the text inside the OVER parentheses |
| `'CAST(%s AS NUMERIC)' % sql` | `numericCast sql = "CAST(" ++ sql ++ " AS NUMERIC)"` | string template ↔ `List Char` concatenation, character-for-character |
| `'%(expression)s OVER (%(window)s)' % {...}` | `overClause expr win = expr ++ " OVER (" ++ win ++ ")"` | string template ↔ `List Char` concatenation, character-for-character |

The three inputs (`isDecimal`, `innerBase`, `win`) are abstracted **inputs**
(R-tagged), supplied directly to `windowNumericSql` — they are NOT axiomatized
callees (the abstracted-input-not-axiom pattern; cf. sibling instance 13121).
Lean `String`/`List Char` is total and sound (no `List[int]` workaround needed).

## 3. Callee provenance and flag dependency

- **No consumed axioms; no A-reference deep models.** G-AX has nothing to check
  for this bundle (no `axiom_check.py`; gates.py skips G-AX when absent). Both
  string operations the rendering uses (`numericCast`, `overClause`) are
  unchanged repo string templates transliterated concretely (I-tagged), not
  foreign callees whose behaviour must be assumed.
- **Flag / type dependency (G-CONF must cover both arms):** the cast branch is
  gated on `isinstance(self.output_field, DecimalField)`. G-CONF therefore
  fuzzes the output-field tag over `{decimal, float, integer, bigint}` so both
  the decimal arm (the issue's crashing case → `isDecimal = true`) and the
  non-decimal arm (`isDecimal = false`, plain OVER, no cast) are exercised. The
  bug from the problem statement is the `decimal` arm.
- **Backend dependency:** the rendering modeled is the SQLite path
  (`as_sqlite`); SQLite is `connection.features.supports_over_clause = True` on
  the version under test, and is the backend whose `SQLiteNumericMixin` casts
  decimals. G-CONF drives the real `Window.as_sqlite` through a stub
  `vendor = "sqlite"` compiler/connection.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13449`**. It first runs
the F2P scenario (a decimal `Lag` over a partition+order window) plus a boundary
matrix over all four output-field tags × {full window, empty window, empty
operand, both empty}, then fuzzes 100 000 more `(tag, operand-SQL, window-clause)`
triples. The oracle drives the REAL patched `Window.as_sqlite` (through a
recording stub compiler/connection, no live DB) and observes the rendered SQL
string; the shadow transliterates `windowSql`/`numericCast`/`overClause` (all
R/I ops). There is no A-tagged callee to leave as a real call.
