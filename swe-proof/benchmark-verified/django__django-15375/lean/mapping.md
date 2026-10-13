# mapping.md — django__django-15375

## Symbol binding (file:line @ base_commit beb7ddbcee)
Modeled function: the tail of `Aggregate.resolve_expression`,
`django/db/models/aggregates.py:50-68` (the arm reached when the aggregate
carries a non-`None` `default`). After the aggregate has been resolved (and its
`is_summary` flag set to the `summarize` argument by
`BaseExpression.resolve_expression`, `expressions.py:247`), if a `default` was
supplied the method wraps the resolved aggregate `c` in a `Coalesce(c, default,
…)` and returns the wrapper. The gold patch additionally copies the aggregate's
terminal-aggregation marker onto the wrapper (`coalesce.is_summary =
c.is_summary`) before returning it.

Lean modeled function name: `resolveAggregate` (deliberately neutral — it names
the *behavior* "produce the resolved aggregate node", not the patched method; see
G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `resolveAggregate` (modeled tail) | `Aggregate.resolve_expression`, `aggregates.py:50-68` |
| `isTerminalAggregation` | `c.is_summary` after resolve, i.e. the `summarize` argument; set at `expressions.py:247` (`c.is_summary = summarize`). `is_summary` class default is `False` (`expressions.py:155`) |
| `hasFallback` | `(default := c.default) is not None`, `aggregates.py:63` — whether a fallback value was supplied to the aggregate |
| `result.wrapped` | the returned node is `Coalesce(c, default, …)` (the wrapper) rather than the bare `c` |
| `result.terminal` | the returned node's `is_summary` flag |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `c.is_summary : bool` (terminal-aggregation marker, = `summarize`) | `isTerminalAggregation : Bool` |
| `c.default is not None : bool` | `hasFallback : Bool` |
| returned node identity: `Coalesce(...)` wrapper vs bare aggregate `c` | `result.wrapped : Bool` (`true` = wrapper) |
| returned node's `.is_summary : bool` | `result.terminal : Bool` |

### Node-identity / marker modeling note
The real method returns either a `Coalesce` instance or the bare resolved
aggregate `c`; what the downstream SQL compiler observes about that node is (a)
whether it is the coalescing wrapper and (b) its `is_summary` flag (which decides
whether the node is emitted as a terminal summary column or as an inner-query
column). We model exactly those two observables as the `ResolvedExpr` structure
`{ wrapped, terminal }`. `Coalesce.__init__` does not set `is_summary`, so a
freshly built `Coalesce` has the class-default `is_summary = False` until
explicitly assigned — this is what the pre-patch code returns, and what the gold
fix overwrites with `c.is_summary`.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `Coalesce(...)` construction is
  modeled as producing a wrapper node whose terminal marker starts `False`
  (`wrapperTerminal := false`) and is then set; `c.is_summary` /
  `c._output_field_or_none` / `default.resolve_expression` enter only insofar as
  they determine the two observables (`isTerminalAggregation`, `hasFallback`) and
  are supplied as the inputs. No A row.
- Flag dependency: the wrapping fires iff `c.default is not None`
  (`hasFallback = true`). The terminal marker that must be propagated is
  `c.is_summary`, which equals the `summarize` argument the aggregate was
  resolved with (`isTerminalAggregation`). The `aggregate()` terminal path
  resolves with `summarize=True`; the `annotate()` path with `summarize=False`.

## G-CONF
Whole impl is R/I (node-identity + boolean marker propagation). `conf_skip =
false`. Pinned fuzz seed: **15375** (also in conformance_check.py).

## G-LEAK
The solver-visible `problem_statement` describes `aggregate()` / `annotate()` /
`default` / `Coalesce` / `Sum` at the API level, but the spec view names none of
the patched symbols: not `resolve_expression`, not `is_summary`, not `summarize`,
not `aggregates`, and reproduces no gold-diff line. The only def/class symbol the
gold patch touches is `resolve_expression` (the hunk section header); it does not
appear in the spec view. Comments describe the abstract behavior (a terminal
aggregation, a coalescing wrapper, a fallback value), never the edit or its
diagnosis.
