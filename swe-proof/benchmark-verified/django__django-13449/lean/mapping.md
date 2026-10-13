# mapping.md — symbol binding & type bijection (django__django-13449)

## Modeled function
- **Lean** `implementation_renderWindowSql : List Char → List Char → Bool → List Char`
- **Python** the SQLite rendering of a windowed expression — `Window.as_sqlite`
  (added by the patch) together with the inherited numeric-cast wrapper
  `SQLiteNumericMixin.as_sqlite` — `django/db/models/expressions.py:18-29`
  (`SQLiteNumericMixin`) and `1256-1342 @ base_commit` (`Window`).

A window expression renders, on every backend, via the class template
`'%(expression)s OVER (%(window)s)'` (`Window.template`, line 1257): the compiled
source-expression SQL, the literal ` OVER (`, the assembled window clause
(`PARTITION BY …`/` ORDER BY …`/frame), and the literal `)`. On SQLite, an
expression whose declared output type is a fixed-point decimal must additionally
be wrapped in a numeric cast `CAST(%s AS NUMERIC)` (`SQLiteNumericMixin`, line
26) so the value is filtered/compared as numeric rather than text.

The observable question the F2P test pins is **what the numeric cast wraps**:

```text
# decimal output, the whole windowed expression cast as a unit:
CAST(LAG("t"."amount", 7) OVER (PARTITION BY … ORDER BY …) AS NUMERIC)

# pre-patch: only the operand is cast, leaving a bare OVER (… ) suffix:
CAST(LAG("t"."amount", 7) AS NUMERIC) OVER (PARTITION BY … ORDER BY …)
```

The second is invalid SQL (the `OVER` clause dangles outside the cast), which is
exactly the `near "OVER": syntax error` in the issue. Post-patch the cast spans
the entire `expression OVER (window)` unit.

### How the patch achieves it (control/data flow the skeleton mirrors)
`Window.as_sqlite`: when the output type is decimal, it (1) clears the inner
operand's decimal type so the operand renders **without** its own inner cast,
then (2) delegates to the numeric-cast wrapper, which renders the full
`expression OVER (window)` text and wraps that whole string in
`CAST(… AS NUMERIC)`. When the output type is not decimal it falls through to the
plain template render. So, modeled abstractly: render the bare windowed
expression `base = operand ++ " OVER (" ++ window ++ ")"`, then — only for a
decimal output type — wrap the *entire* `base` in the numeric cast.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| compiled source-expression SQL (e.g. `LAG("t"."amount", 7)`) — cast-free operand text | `operand : List Char` | per-character; the operand carries no inner numeric cast (its decimal type is cleared before delegation) |
| assembled window-clause SQL (`PARTITION BY … ORDER BY … <frame>`) | `window : List Char` | per-character; passed through unchanged by the fix |
| output type is a fixed-point decimal | `isDecimal : Bool` | selects the numeric-cast branch |
| rendered SQL string (output `sql`) | `List Char` | per-character; the returned `params` list is unaffected by the fix and is not modeled |

The template `'%(expression)s OVER (%(window)s)'` substitution into the *literal*
template is, semantically, the fixed-order concatenation
`operand + ' OVER (' + window + ')'`. The cast wrapper `'CAST(%s AS NUMERIC)' % sql`
is the fixed-order concatenation `'CAST(' + sql + ' AS NUMERIC)'`. Both are
reproduced exactly as **I** (identical concrete ops), not axiomatized.

## Callee provenance
- `Window.as_sql` / the template substitution renders `operand OVER (window)`.
  UNCHANGED by the patch; reproduced concretely as the literal-driven
  concatenation above (I-tagged) — no `opaque`/axiom needed.
- The numeric-cast wrapper (`'CAST(%s AS NUMERIC)' % sql`) is UNCHANGED; it is
  reproduced concretely (I-tagged). The **changed op** is *which string* is fed
  to that wrapper (the whole windowed expression vs the bare operand); that is
  modeled deeply via the branch structure, NOT axiomatized.
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub.

## Flag dependency
The numeric cast is emitted only when the output type is a fixed-point decimal
(`isDecimal = true`). G-CONF fuzzes both flag values; the non-decimal branch is
identical pre- and post-patch, so the discriminating behavior lives entirely in
the `isDecimal = true` branch.

## Scope note
The patch's mechanical step of clearing the inner operand's decimal type (so the
operand renders without its own inner cast) is precisely what makes the modeled
`operand` cast-free; it is captured by taking `operand` to be the bare operand
text. The `params` list threads through both `as_sql` and the cast wrapper
unchanged and is out of model scope.

## G-CONF fuzz seed
Pinned seed: **13449**. ≥10^5 fuzzed inputs over operand / window text alphabets
plus both decimal-flag values.
