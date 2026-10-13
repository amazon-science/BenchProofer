# mapping.md — django__django-13012

## Symbol binding (file:line @ base_commit 22a59c01c0)
Modeled function: the `get_group_by_cols` method newly added to
`ExpressionWrapper`, `django/db/models/expressions.py:849-871` (class
`ExpressionWrapper`, defined at line 849; the new method is inserted after
`get_source_expressions` at line 863-864).

```python
class ExpressionWrapper(Expression):
    def __init__(self, expression, output_field):
        super().__init__(output_field=output_field)
        self.expression = expression
    ...
    def get_source_expressions(self):
        return [self.expression]

    def get_group_by_cols(self, alias=None):          # <-- added by the patch
        return self.expression.get_group_by_cols(alias=alias)

    def as_sql(self, compiler, connection):
        return self.expression.as_sql(compiler, connection)
```

`ExpressionWrapper` wraps another expression (`self.expression`) to attach extra
context (its `output_field`) without altering what the inner expression
computes. Before the patch, `ExpressionWrapper` had no `get_group_by_cols`
override, so it inherited `BaseExpression.get_group_by_cols`
(`expressions.py:350-356`):

```python
def get_group_by_cols(self, alias=None):
    if not self.contains_aggregate:
        return [self]
    cols = []
    for source in self.get_source_expressions():
        cols.extend(source.get_group_by_cols())
    return cols
```

`contains_aggregate` (`expressions.py:221-222`) for the wrapper is
`any(expr and expr.contains_aggregate for expr in self.get_source_expressions())`,
i.e. it reflects whether the wrapped expression contains an aggregate.

So before the patch:
  * if the wrapped expression contains an aggregate → the wrapper returns the
    union of its sources' group-by columns (here, the single wrapped
    expression's columns), which happens to coincide with the patched behavior;
  * otherwise → the wrapper returns `[self]` — i.e. *the wrapper itself* as a
    grouping column. For a wrapped constant (`Value`, whose own
    `get_group_by_cols` returns `[]` — `expressions.py:706-707`) this wrongly
    forces the constant into the GROUP BY clause.

After the patch, the wrapper delegates unconditionally to the wrapped
expression's own `get_group_by_cols`, so a wrapped constant contributes `[]` and
is correctly omitted from GROUP BY.

Lean modeled function name: `wrapperGroupByCols` (names the *behavior* — the
group-by columns a wrapping expression contributes; the public
`problem_statement` already names `ExpressionWrapper`, `GROUP BY`, and
constant expressions).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `e : Expr` | the `ExpressionWrapper` instance `self` (`expressions.py:849`) |
| `e.innerCols` | `self.expression.get_group_by_cols(alias=alias)` — the columns the wrapped expression contributes (`expressions.py:863` is `self.expression`; its `get_group_by_cols` is the inner expression's own method) |
| `e.innerContainsAggregate` | `self.contains_aggregate` for the wrapper = whether the wrapped expression contains an aggregate (`expressions.py:221-222`) |
| `e.selfCol` | `self` re-used as a single grouping column, i.e. the `[self]` element the inherited default returns (`expressions.py:351`) |
| `result : List Col` | the list returned by `ExpressionWrapper.get_group_by_cols` |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.expression.get_group_by_cols(alias=alias)` (a list of column expressions) | `e.innerCols : List Col` |
| `self.contains_aggregate` (the wrapper's, == wrapped expr's) | `e.innerContainsAggregate : Bool` |
| `self` as the single grouping column | `e.selfCol : Col` |
| each column expression in a returned list | a `Col` (identity-only; `ref : Nat` distinguishes distinct columns) |
| the returned `list` of column expressions | `result : List Col`, order-preserving |

### Modeling note (the `Col` / `Expr` abstraction)
`get_group_by_cols` returns a Python `list` of expression objects; only the
*identity and multiplicity/order* of those column objects matters for GROUP BY
correctness. The model represents each distinct column object by a `Col` with a
distinct `ref : Nat`; a returned list maps to the corresponding `List Col`
order-preservingly. `e.innerCols` is the inner expression's already-computed
contribution — its computation is the inner expression's own, unchanged
behavior, supplied as input data (A-reference) rather than re-derived. The
discriminating case is a wrapped constant: `innerContainsAggregate = false` and
`innerCols = []`, where the pre-patch default returns `[e.selfCol]` (the bug) but
the patched delegation returns `[]`.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The new method's body is a
  single delegation to `self.expression.get_group_by_cols(alias=alias)`. The
  inner expression's `get_group_by_cols` is NOT changed by the patch; its result
  is modeled *deeply* as the input field `e.innerCols` (an A-reference — the
  patched method forwards to it verbatim; validated against the real callees by
  G-CONF). No property of that callee is consumed by the proof, so `axioms = []`
  and `axiom_check.py` is a skip stub (G-AX skips).
- No flag dependency: the patched method ignores all configuration; it forwards
  unconditionally. The `alias` keyword is threaded through unchanged and does not
  alter the correspondence (the model treats the inner contribution as a single
  observed value `e.innerCols`).

## G-LEAK
The solver-visible `problem_statement` publicly names `ExpressionWrapper`,
`GROUP BY`, constant expressions (`Value`), and the symptom (a constant placed in
the GROUP BY clause). The spec view (`Solution.lean` minus impl+proof) states only
the abstract contract: a wrapping expression contributes exactly the grouping
columns of the expression it wraps, and a wrapped constant therefore contributes
nothing. No gold-diff line is reproduced, no diff marker, no patched file path,
and no patched symbol name (`get_group_by_cols`) appears. The identifiers
(`wrapperGroupByCols`, `Expr`, `Col`, `innerCols`) describe the *behavior* — the
columns a wrapping expression contributes to a grouping clause — not the edit.

## Pinned G-CONF fuzz seed
`13012`.
