# mapping.md — django__django-13028

## Symbol binding (@ base_commit 78ad4b4b0201003792bfdbf1a7781cbc9ee03539)

- Modeled function: `Query.check_filterable`
  — `django/db/models/sql/query.py:1126` (def line) @ base_commit.
  Source (pre-patch):
  ```python
  def check_filterable(self, expression):
      """Raise an error if expression cannot be used in a WHERE clause."""
      if not getattr(expression, 'filterable', True):
          raise NotSupportedError(
              expression.__class__.__name__ + ' is disallowed in the filter '
              'clause.')
      if hasattr(expression, 'get_source_expressions'):
          for expr in expression.get_source_expressions():
              self.check_filterable(expr)
  ```

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python reality | Lean model | notes |
|---|---|---|
| the `expression` argument (any object) | `Expr` inductive | only the three observable facets the function touches are modeled |
| `hasattr(expression, 'resolve_expression')` | `Expr.isQueryExpr : Bool` | the NEW guard the fix adds; `True` ⇔ object exposes the resolve-expression protocol, i.e. it is a first-class query expression rather than a plain value |
| `getattr(expression, 'filterable', True)` | `Expr.filterable : Bool` | attribute-absence default (`True`) is folded into the explicit Bool: an object lacking the attribute is modeled with `filterable = true` |
| `hasattr(expression, 'get_source_expressions')` + the returned list | `Expr.children : List Expr` | an object without the method (or with an empty list) is modeled with `children = []`; the `hasattr` guard is subsumed by the empty-list case (`[].any = false`) |
| `raise NotSupportedError(...)` vs. normal return | `Bool` result of `implementation_checkFilterable` | `true` ⇔ the call (transitively) raises `NotSupportedError`; `false` ⇔ it returns normally. The exception message string is irrelevant to the fixed behavior and is not modeled. |
| `for expr in get_source_expressions(): self.check_filterable(expr)` (exception propagates out of the loop) | `children.any` via the mutual `…Any` list recursion; `||` short-circuit = first-raising child aborts the loop | observable result is "does it raise", so `any` is faithful |

### Default-attribute semantics (boundary the model encodes)
`not getattr(expression, 'filterable', True)` is `True` **only** when the object
has `filterable` explicitly falsey. Modeled as `!e.filterable` over the explicit
Bool, with the absent-attribute case pinned to `filterable = true`.

### Flag / protocol dependencies
- The fix's discriminator is the *presence of the resolve-expression protocol*
  (`isQueryExpr`). A genuine query expression has `isQueryExpr = true`; an
  ordinary model instance that merely owns a field named `filterable` has
  `isQueryExpr = false`. G-CONF fuzzes both polarities independently of
  `filterable`.

## Callee provenance
None consumed. `check_filterable` calls only `getattr`/`hasattr`/
`get_source_expressions` and recurses on itself. All are modeled structurally
over `Expr`; there is **no** unchanged external callee whose behavior the proof
must assume. ⇒ axioms region is empty; `axiom_check.py` is a skip stub.

## G-CONF fuzz seed
Pinned seed: `13028`. Generator builds random `Expr` trees (bounded depth 4,
≤4 children/node, each node's `isQueryExpr`/`filterable` drawn i.i.d.) and
compares the Lean-mirrored R/I shadow against the patched Python behavior over
≥10⁵ samples.
