# mapping.md — django__django-15382

## Symbol binding (file:line @ base_commit 770d3e6a4ce8e0a91a9e27156036c1985e74d4a3)
Modeled function: the rendering method of the existence-test-over-subquery
expression, `Exists.as_sql`, in `django/db/models/expressions.py:1212-1224`
(`class Exists(Subquery)`, `:1199`). The gold patch wraps the delegated render in
a `try/except`:

```python
def as_sql(self, compiler, connection, template=None, **extra_context):
    query = self.query.exists(using=connection.alias)
    try:
        sql, params = super().as_sql(
            compiler, connection, template=template, query=query, **extra_context,
        )
    except EmptyResultSet:
        if self.negated:
            return '', ()
        raise
    if self.negated:
        sql = 'NOT {}'.format(sql)
    return sql, params
```

`super().as_sql` is `Subquery.as_sql` (`:1178-1187`): it asks the inner query to
render (`query.as_sql(compiler, connection)`) and formats the `EXISTS(%(subquery)s)`
template. That inner render raises `django.core.exceptions.EmptyResultSet` when
the subquery is statically known to match no rows (e.g. `.none()`), which is the
"empty-result signal" below.

Pre-patch (`:1212-1223`), the `super().as_sql` call is NOT guarded, so an
`EmptyResultSet` from an empty subquery propagates out of `Exists.as_sql`
unconditionally — including for a NEGATED `Exists`. The compiler then drops the
whole `WHERE` block (the bug: `filter(~Exists(MyModel.objects.none()), …)` loses
its conditions). The fix: when negated, a `~Exists(empty)` is trivially true, so
it must render as the empty fragment `('', ())` instead of propagating.

Lean modeled function name: `compileExistenceCheck` (neutral — names the
*behavior* "render an existence test to SQL", sharing no substring with the
patched symbols `Exists`, `as_sql`, `negated`, `EmptyResultSet`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `compileExistenceCheck` (modeled function) | `Exists.as_sql` (`expressions.py:1212-1224` post-patch) |
| `negated : Bool` | `self.negated` (set by `Exists.__init__` / flipped by `__invert__`) |
| `inner : Except RenderFailure (String × List String)` | outcome of `super().as_sql(...)` = `Subquery.as_sql` (`:1178-1187`) |
| `inner = .ok (sql, params)` | `super().as_sql` returns `(sql, params)` normally |
| `inner = .error .emptyResult` | `super().as_sql` raises `EmptyResultSet` (empty subquery) |
| `inner = .error .other` | `super().as_sql` raises any OTHER exception (not caught by `except EmptyResultSet`) |
| result `.ok (sql, params)` | the `(sql, params)` tuple returned by `as_sql` |
| result `.ok ("", [])` | the `('', ())` empty fragment returned for a negated empty subquery |
| result `.error .emptyResult` | `EmptyResultSet` re-raised (`raise` in the `except` arm) |
| result `.error .other` | any other exception propagating uncaught through `as_sql` |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.negated` (bool) | `negated : Bool` |
| `super().as_sql(...)` returns `(sql:str, params:tuple)` | `inner = .ok (sql, params)` with `params : List String` |
| `super().as_sql(...)` raises `EmptyResultSet` | `inner = .error .emptyResult` |
| `super().as_sql(...)` raises any other exception | `inner = .error .other` |
| `sql = 'NOT {}'.format(sql)` | `if negated then "NOT " ++ sql` |
| `return '', ()` | `.ok ("", [])` |
| `raise` (re-raise `EmptyResultSet`) | `.error .emptyResult` |
| uncaught non-`EmptyResultSet` exception | `.error .other` |
| returned `(sql, params)` | `.ok (sql, params)` |

### Parameter modeling note
The bind parameters (`params`) are a sequence of opaque parameter tokens; the
modeled dispatch never inspects them — it passes them through unchanged in every
success branch, and replaces them by the empty list `()`/`[]` only in the negated
empty-result branch. They are therefore modeled as `List String` of arbitrary
tokens (the element type is irrelevant to the dispatch). The fragment string
`sql` is modeled as `String`; the only string operation is the textual `NOT `
prefix, mirroring `'NOT {}'.format(sql)`.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom and none is declared `opaque`.**
  The single callee whose value is used, `super().as_sql` (`Subquery.as_sql`,
  `:1178-1187`), is the source of the boundary input `inner`: rather than model
  its internals, its outcome (success `(sql, params)` OR `EmptyResultSet`) is the
  domain of `compileExistenceCheck`. The patch does NOT change `Subquery.as_sql`;
  it changes only how `Exists.as_sql` dispatches on that outcome together with
  `self.negated`. The modeled function is exactly that dispatch — pure, with no
  callee contract — so `axioms = []`, `deep_model_references = []`, and the impl
  region is entirely R/I (testable by G-CONF).
- **Flag dependency:** the behavior branches on `self.negated` (the negation flag
  of the `Exists`) and on whether the inner render raised `EmptyResultSet`. Both
  are coordinates of the modeled input; G-CONF fuzzes both.
- `query = self.query.exists(using=connection.alias)` is UNCHANGED by the patch
  and only mutates the inner query before `super().as_sql`; it does not affect the
  dispatch and is folded into the inner-render outcome.

## G-LEAK
The solver-visible `problem_statement` mentions `Exists`, `models.Exists`,
`MyModel.objects.none()`, `EmptyResultSet`, the `WHERE` block, and `filter`. The
spec view (Solution.lean minus impl+proof) names NONE of the patched symbols
(`Exists`, `as_sql`, `negated`, `EmptyResultSet`, `Subquery`, `super`) and never
narrates the bug→fix mechanism (no mention of a `try/except`, a dropped `WHERE`
block, or the added guard). It uses only neutral behavioral vocabulary:
"existence test", "subquery", "negated form", "empty-result signal", "rendered
SQL fragment", "bind parameters". The modeled-function identifier
`compileExistenceCheck` shares no substring with any patched def/class name.

## Pinned G-CONF fuzz seed
`15382`.
