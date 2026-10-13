# mapping.md — django__django-13028

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 78ad4b4b0201003792bfdbf1a7781cbc9ee03539`, states the type
abstraction, and gives the provenance of the one abstracted (A-reference)
behaviour.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check_operands(is_expr, permitted)` | `Query.check_filterable(self, expression)` — `django/db/models/sql/query.py:1125` (changed disallow test at body line 1127) | the modeled changed function (the filter-operand guard) |
| `OperandNotAllowed` (user-defined `Exception`) | `django.db.utils.NotSupportedError` (raised at `query.py:1128`; defined `django/db/utils.py:48`, subclass of `DatabaseError`) | the rejection the guard raises; a user-defined stand-in (a builtin/db-layer exception in an `Exsures` crashes the Nagini translator) |
| the loop over the carriers | the guard's recursion: top-level call + `for expr in expression.get_source_expressions(): self.check_filterable(expr)` (`query.py:1132-1134`, UNCHANGED) | the screen is applied to the operand and every nested operand; modelled as one loop over the flattened walk (A-reference, §3) |

The guard is invoked from `Query.build_filter` on both the referenced expression
and the comparison's right-hand `value` (`query.py:1258-1259, 1268-1269`); the
F2P regression is the `value` call on a plain model instance.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `expression` operand and every operand nested inside it (reached via `get_source_expressions`) | two index-aligned `List[int]`, `is_expr` and `permitted`, in the guard's pre-order walk order | one `(is_expr[i], permitted[i])` pair per visited operand; `len(is_expr) == len(permitted)` (a single walk shape) |
| `hasattr(expression, 'resolve_expression')` (`query.py:1127`, the ADDED conjunct) | `is_expr[i] ∈ {0, 1}` | `True` ↔ 1, `False` ↔ 0: whether operand i is a query-expression operand (participates in query resolution) |
| `getattr(expression, 'filterable', True)` (`query.py:1127`) | `permitted[i] ∈ {0, 1}` | truthy ↔ 1, falsy ↔ 0; an operand that exposes NO `filterable` attribute takes the `getattr` default `True` ⇒ `permitted = 1`. The model collapses the attribute to its effective boolean: `permitted[i]==0` iff the operand has a `filterable` marker that is falsy |
| `not getattr(expression, 'filterable', True)` | `permitted[i] == 0` | the "not-permitted" test |
| raising `NotSupportedError(...)` (the class-name + message string) | `raise OperandNotAllowed()` | the message payload (`expression.__class__.__name__ + ' is disallowed...'`) is the rejection's text, not observed by the accept/reject behaviour the F2P tests assert; abstracted away |

`str` indexing/iteration is banned in Nagini, and the operand's contents are
irrelevant to the pinned behaviour, so the operand is abstracted to the two
per-operand booleans the guard actually tests.

## 3. Provenance of the abstracted recursion (A-reference — checked by G-AX / axiom_check.py)

**No `@ContractOnly` axiom is consumed by the proof.** The guard's decision is
modelled deeply (the conjunction `is_expr[i]==1 and permitted[i]==0` over the
walk). The single abstracted element is the unchanged recursion's collapse into a
flattened operand list.

**Behaviour (A-reference):** the post-patch `check_filterable` rejects an operand
tree iff at least one operand in the recursive walk satisfies
`hasattr(op, 'resolve_expression') and not getattr(op, 'filterable', True)`;
otherwise it returns normally. The recursion guard
`hasattr(expression, 'get_source_expressions')` (`query.py:1132`) walks an
operand's sub-operands; this guard, and the recursion, are UNCHANGED by the patch
(`4edad1ddf6203326e0be4bdb105beecb0fe454c4` introduced the `filterable` check;
the gold patch only adds the `resolve_expression` conjunct to the disallow test).
Source (post-patch):
```python
def check_filterable(self, expression):
    """Raise an error if expression cannot be used in a WHERE clause."""
    if (
        hasattr(expression, 'resolve_expression') and
        not getattr(expression, 'filterable', True)
    ):
        raise NotSupportedError(
            expression.__class__.__name__ + ' is disallowed in the filter clause.'
        )
    if hasattr(expression, 'get_source_expressions'):
        for expr in expression.get_source_expressions():
            self.check_filterable(expr)
```
Because the same disallow test is applied to every operand in the walk, the
guard raises iff SOME operand in the flattened pre-order traversal is
simultaneously a query expression and not-permitted — exactly the model
predicate `Exists k. is_expr[k]==1 and permitted[k]==0`.

**Soundness check (G-AX):** `axiom_check.py` (1) runs a faithful in-Python
reference of this post-patch guard (the conjunction + recursive
`get_source_expressions` walk) over an exhaustive boundary space (every single
operand shape, and every depth-2 root×child(×child) combination — 258 trees) and
20 000 randomized operand trees (depth ≤ 4, branching ≤ 3), asserting the
reference's accept/reject decision equals `model_rejects(flatten(tree))`; and (2)
when Django is importable (the official container), runs the REAL
`Query.check_filterable` on representative operands and asserts its raise/no-raise
outcome matches the model decision — including the **F2P case** (a plain data
object with `filterable=False` and no `resolve_expression` ⇒ ACCEPT, not the
pre-patch raise), the query-expression-not-permitted case (⇒ REJECT), and the
recursion (a disallowed expression nested inside a permitted one ⇒ REJECT; a
plain not-permitted data operand nested inside an expression ⇒ ACCEPT). It
imports only `django` (the very module under change) and stdlib; exit 0 iff every
observation matches the model.
