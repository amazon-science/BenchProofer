# mapping.md — django__django-15375

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = beb7ddbcee03270e833b2f74927ccfc8027aa693`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
records the provenance of the unchanged callees the direct model relies on.

Repo file under change: `django/db/models/aggregates.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prepareAggregate (terminal : Bool) (defaultVal : Option Int)` | `Aggregate.resolve_expression` — `django/db/models/aggregates.py:50` (the `default` branch, body lines 64–68) | the modeled changed function: prepares an aggregate expression as it is added to a query |
| `Resolved` (`isTerminal`, `hasFallback`) | the prepared expression's observable shape: its `is_summary` flag + whether it is the fallback wrapper | structure: the two fields of the prepared clause the query builder later dispatches on |
| `prepared` | the post-patch result of `resolve_expression` on `(summarize, default)` | pure spec: the prepared clause |

The pre-patch repo behaviour the change repairs (refinement audit only, not in
the consumer spec view): the fallback wrapper constructed at `aggregates.py:68`
inherits the class-default terminal marker (`Expression.is_summary = False`,
`django/db/models/expressions.py:155`) instead of the resolved aggregate's
marker. The downstream consumer is `Query.get_aggregation`
(`django/db/models/sql/query.py:476`: `if expression.is_summary:` moves terminal
clauses to the outer query), which on a `False`-marked wrapper leaves the
aggregate in the inner subquery and emits the broken `SELECT FROM (subquery)`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `summarize` parameter of `resolve_expression` (a `bool`: the clause is a terminal/top-level aggregation) | `terminal : Bool` | `True` ↔ `true`, `False` ↔ `false` |
| `default` keyword argument (`None` = no fallback; any expression/value = a fallback to substitute when the aggregation is empty) | `defaultVal : Option Int` | `None` ↔ `none`; any non-`None` default ↔ `some n`. Only **presence** is observable here — the value content flows unchanged into the wrapper's fallback slot (I-tagged, §refinement); modeled as `Int` for a concrete fuzzable carrier |
| the prepared expression's `is_summary` flag (the terminal/outer-level marker the query builder dispatches on at `query.py:476`) | `Resolved.isTerminal : Bool` | `expr.is_summary` (truthy) ↔ `isTerminal` |
| whether the prepared expression is the fallback wrapper (`Coalesce(c, default)`) vs the bare resolved aggregate `c` | `Resolved.hasFallback : Bool` | `isinstance(result, Coalesce)` ↔ `hasFallback` |

`is_summary` is normalized to a `bool` (`bool(expr.is_summary)`) before
comparison: the real attribute is set from the `summarize` arg, which the public
queryset API (`aggregate()`) passes as a genuine bool.

## 3. Callee provenance — facts the direct model depends on (checked by G-AX)

This bundle has **no consumed Lean axiom and no deep-model reference**: the
changed operation (preparing the fallback wrapper so it keeps the terminal
marker) is modeled **directly** by `Resolved` + `prepared` (refinement.md §C).
G-AX (`axiom_check.py`) validates — against REAL Django, in-container — the two
unchanged-callee facts the direct model rests on:

### 3.1 Base resolution sets the terminal marker to `summarize`
**Callee:** `Expression.resolve_expression` / `Func.resolve_expression`
(`django/db/models/expressions.py:155`, UNCHANGED by the patch). My model
encodes `c.isTerminal := terminal` — i.e. after `super().resolve_expression(...,
summarize=s)`, the resolved aggregate's `is_summary == s`. G-AX resolves a
`default`-free aggregate (`Sum('field')`, which never enters the changed
fallback branch) at `summarize ∈ {False, True}` and asserts
`resolved.is_summary == summarize`.

### 3.2 The fallback wrapper defaults its terminal marker to `False`
**Callee:** `Coalesce.__init__` (via `Func`/`Expression`, UNCHANGED). A freshly
constructed `Coalesce(c, default)` carries `is_summary == False` (the class
default `Expression.is_summary = False`). G-AX constructs a `Coalesce` directly
and asserts `coalesce.is_summary is False`. This is why the propagation is
**necessary**: without it the wrapper silently drops the terminal marker — the
exact pre-patch bug, and what `Solution_prepatch.lean` reproduces.

Both callees are unchanged by `patch.diff`; G-AX never re-runs the changed
default branch to establish 3.1/3.2 (no circularity). The patched function
itself is exercised only by G-CONF as the correctness oracle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15375`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `prepared` to Python (`(isTerminal, hasFallback)` from
`(terminal, defaultVal)`) and diffs it against the patched
`Aggregate.resolve_expression`'s observable
`(bool(result.is_summary), isinstance(result, Coalesce))` over the
`terminal × defaultVal` input grid plus fuzzed default values. There is no
A-tagged callee in the impl region, so the shadow is pure R/I.
