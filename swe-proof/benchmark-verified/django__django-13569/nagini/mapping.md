# mapping.md — django__django-13569

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 257f8495d6c93e30ab0f52af4c488d7344bcf112`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
callee the deep model is validated against by G-AX). This bundle consumes NO
`@ContractOnly` axiom.

Repo files involved:
- `django/db/models/functions/math.py` — the changed file (the gold hunk).
- `django/db/models/expressions.py` — the unchanged base behaviour
  (`BaseExpression.get_group_by_cols`, `OrderBy.get_group_by_cols`).
- `django/db/models/sql/compiler.py` — the unchanged caller
  (`SQLCompiler.get_group_by`, the order-by → group-by gathering loop) that the
  F2P test exercises.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `random_group_by_cols(colid)` | `Random.get_group_by_cols(self, alias=None)` — `django/db/models/functions/math.py:157` (added by the gold hunk after `as_sqlite`, body lines 144-149 region) | the modeled changed function: the grouping columns a non-deterministic ordering term offers |
| `group_by_columns_for_ordering(nondet, ref, cols)` | the order-by gathering loop in `SQLCompiler.get_group_by` — `django/db/models/sql/compiler.py:128-131` (`for expr, (sql, params, is_ref) in order_by: if not is_ref: expressions.extend(expr.get_group_by_cols())`) | the unchanged caller slice that the F2P test observes; models how per-term contributions are gathered into the GROUP BY |
| `offered_cols(is_nondet, colid)` *(deep model — A-reference)* | per-term `get_group_by_cols()`: the default `BaseExpression.get_group_by_cols` (`expressions.py:349-355`, returns `[self]` for a non-aggregate leaf) vs. the new `Random.get_group_by_cols` (returns `[]`) | pure spec: columns one ordering term offers — its one column if deterministic, none if non-deterministic |
| `gathered(nondet, ref, cols)` *(deep model — A-reference)* | the concatenation `expressions.extend(expr.get_group_by_cols())` over `order_by` (skipping `is_ref`), via `OrderBy.get_group_by_cols` (`expressions.py:1231-1235`) which delegates to its source expression's `get_group_by_cols` | pure spec: the gathered grouping columns from a whole ordering list |

The pre-patch repo behaviour the change overrides (for the refinement audit, not
referenced from the consumer spec view): `Random`, lacking its own
`get_group_by_cols`, inherits `BaseExpression.get_group_by_cols`
(`expressions.py:349-355`). Since `Random.contains_aggregate` is `False` and
`Random` has no source expressions (`arity = 0`), that default returns `[self]`
— so a `RANDOM()` expression is injected into the GROUP BY. The gold hunk
overrides it to return `[]`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an expression object's `get_group_by_cols()` result (a `list` of expression objects) | `List[int]` of column identities | each contributed expression ↔ a distinct integer identity; an empty list ↔ `[]`; list concatenation/`extend` ↔ list `+` |
| a list of `order_by` 2-tuples `(expr, (sql, params, is_ref))` | three index-aligned `List[int]` — `nondet[k]`, `ref[k]`, `cols[k]` | `nondet[k] != 0` ↔ `expr`'s source is a non-deterministic (`Random`) ordering term; `ref[k] != 0` ↔ that tuple's `is_ref` is truthy; `cols[k]` ↔ the column identity a deterministic term would offer (its own identity) |
| `expr.contains_aggregate` / nested source expressions | folded into the two flags | the F2P scenario’s ordering terms are leaves (a bare `Random`, or a stored column); the relevant distinction is exactly non-deterministic vs. deterministic-leaf vs. reference |
| the `RANDOM()` SQL eventually emitted | not modeled (irrelevant to GROUP BY membership) | the tested property is *which columns enter GROUP BY*, observed by the F2P test as the row grouping; the SQL string is downstream |

Boolean flags are carried as `int` (`!= 0` is the truthy test) per the Nagini
modelling convention; identities are arbitrary distinct ints.

## 3. Deep-model references (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `random_group_by_cols` / `offered_cols(is_nondet=True)` ↔ `Random.get_group_by_cols` (A-reference)
**Callee:** `django.db.models.functions.Random.get_group_by_cols` (post-patch,
the gold hunk). The changed operation is modeled **deeply**: `random_group_by_cols`
returns the empty list, and `offered_cols(is_nondet, _)` returns `PSeq()` when
`is_nondet != 0`. There is **no `@ContractOnly` axiom** the proof consumes; the
deep model is validated equal to the real callee out-of-band by axiom_check.py
(G-AX): it asserts `Random().get_group_by_cols() == []` and, transitively,
`OrderBy(Random()).get_group_by_cols() == []`, so a non-deterministic ordering
term contributes no grouping column. Source (gold hunk):

```python
class Random(NumericOutputFieldMixin, Func):
    function = 'RANDOM'
    arity = 0
    ...
    def get_group_by_cols(self, alias=None):
        return []
```

Pre-patch, the absence of this method makes `Random` inherit
`BaseExpression.get_group_by_cols` (`expressions.py:349`), which returns
`[self]` for the non-aggregate, source-less `Random` — exactly the
`[Random()]` the issue reports leaking into `GROUP BY ..., RANDOM()`.

### 3.2 `offered_cols(is_nondet=False)` / `gathered` ↔ the order-by gathering (A-reference)
**Callees:** `OrderBy.get_group_by_cols` (`expressions.py:1231-1235`),
`BaseExpression.get_group_by_cols` default (`expressions.py:349-355`, returns
`[self]` for a deterministic leaf), and the gathering loop in
`SQLCompiler.get_group_by` (`compiler.py:128-131`). `offered_cols(is_nondet=0, c)`
returns `PSeq(c)` (a deterministic leaf offers its one column); `gathered` is
the front-fold that, skipping reference terms, concatenates each term's
`offered_cols`. G-AX validates this by simulating the real gathering loop on
synthetic ordering terms — deterministic `RawSQL` (whose `get_group_by_cols()`
is the default `[self]`) interleaved with `Random` and reference terms — and
asserting the gathered column-identity sequence equals model.py's `gathered`
over 3000 randomized term lists plus boundary cases. The control flow
`expressions.extend(expr.get_group_by_cols())` for `not is_ref` is mirrored
identically (kind I) by the impl loop; the per-term contribution is the
A-reference.

**Soundness check (G-AX):** `axiom_check.py` configures Django with an in-memory
SQLite backend and exercises the REAL `Random.get_group_by_cols`,
`OrderBy.get_group_by_cols`, and the gathering loop. It runs inside the official
SWE-bench container for this instance with the gold patch applied; outside a
Django-importable environment it prints `G-AX SKIP` and exits 0. Exit 0 iff
every observation matches the deep model. (Confirmed: 3003 observations pass
post-patch; A-reference 1 fails pre-patch with `Random.get_group_by_cols()`
returning `[Random()]`, matching the model's prepatch failure.)
