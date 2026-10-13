# refinement.md — django__django-15375

Maps every operation in `implementation_resolveAggregate` to its `patch.diff`
counterpart in the tail of `Aggregate.resolve_expression`
(`django/db/models/aggregates.py`, the `default`-wrapping arm). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch wrapping arm)
```python
if (default := c.default) is None:
    return c
if hasattr(default, 'resolve_expression'):
    default = default.resolve_expression(query, allow_joins, reuse, summarize)
c.default = None  # Reset the default argument before wrapping.
coalesce = Coalesce(c, default, output_field=c._output_field_or_none)
coalesce.is_summary = c.is_summary
return coalesce
```
The modeled value is the RETURNED NODE: whether it is the coalescing wrapper or
the bare aggregate, and its terminal-aggregation marker (`is_summary`).

## Operation correspondence
| # | Lean op (`implementation_resolveAggregate`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut terminal := isTerminalAggregation` | `c.is_summary` (set to `summarize` by `BaseExpression.resolve_expression`, `expressions.py:247`) | R | the aggregate's terminal marker; `c.is_summary : bool` ↔ `isTerminalAggregation : Bool` (mapping.md). |
| 2 | `if !hasFallback then return { wrapped := false, terminal := terminal }` | `if (default := c.default) is None: return c` | R | no fallback ⇒ return the bare aggregate (`wrapped = false`), keeping its terminal marker. Python `default is None` ↔ Lean `!hasFallback`; `hasFallback : Bool` ↔ `c.default is not None`. |
| 3 | `let mut wrapperTerminal := false` | `coalesce = Coalesce(c, default, output_field=c._output_field_or_none)` | R | a freshly constructed `Coalesce` has `is_summary` at its class default `False` (`expressions.py:155`; `Coalesce.__init__` does not set it). The wrapper node is born non-terminal. `default.resolve_expression(...)` and `c.default = None` are state plumbing that does not affect the two modeled observables, so they are not separate Lean ops. |
| 4 | `wrapperTerminal := terminal` | `coalesce.is_summary = c.is_summary` | I | **the fix** — copy the aggregate's terminal marker onto the wrapper. Boolean assignment ↔ boolean assignment. |
| 5 | `return { wrapped := true, terminal := wrapperTerminal }` | `return coalesce` | R | return the wrapper node (`wrapped = true`) carrying the propagated terminal marker. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of an
unchanged callee — `Coalesce`, `_output_field_or_none`, and
`default.resolve_expression` enter only as the observables `isTerminalAggregation`
/ `hasFallback` per mapping.md). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch the arm is `return Coalesce(c, default, output_field=c._output_field_or_none)`
— it returns the wrapper but never sets `coalesce.is_summary`, so the wrapper
keeps the class default `is_summary = False`. The prepatch impl mirrors this:
`wrapperTerminal := false` is returned unchanged (op #4 is dropped). It therefore
cannot satisfy `problem_spec_resolveAggregate` on the discriminating clause
`result.terminal = isTerminalAggregation` precisely when `hasFallback = true` and
`isTerminalAggregation = true` — i.e. a terminal `aggregate(... default=…)` call.
That is exactly the FAIL_TO_PASS scenario `test_aggregation_default_after_annotation`:
an `annotate(...).aggregate(value=Sum('...', default=0))` resolves the aggregate
as a terminal summary (`summarize=True`), so the wrapper must be marked terminal;
pre-patch it is not, and the wrapper is mis-placed in the SQL (the reported
`SELECT FROM (...)` crash). The carried gold proof fails to typecheck against the
buggy impl (G-DIFF), since `terminal = false ≠ isTerminalAggregation` in that case.
