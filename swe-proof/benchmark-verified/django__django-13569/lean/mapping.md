# mapping.md — django__django-13569

## Symbol binding (file:line @ base_commit 257f8495d6c93e30ab0f52af4c488d7344bcf112)

| Lean symbol | Python symbol | location |
|---|---|---|
| `randomGroupingColumns` / `problem_spec_randomGroupingColumns` | `Random.get_group_by_cols` (the method ADDED by the patch) | `django/db/models/functions/math.py:157-158` (post-fix) |
| `OrderingExpr` (Lean structure) | a `Random` SQL function expression instance (`django.db.models.functions.math.Random`) | `django/db/models/functions/math.py:144-155` |
| `GroupByCol` (`abbrev = String`) | a grouping-column expression as compiled to its `GROUP BY` SQL fragment | n/a (the contributed-column carrier) |

The modeled function is `Random.get_group_by_cols`. It is the only function whose
behavior changes. Its result is consumed by `SQLCompiler.get_group_by`
(`django/db/models/sql/compiler.py:128-132`), which extends the GROUP BY
`expressions` with `expr.get_group_by_cols()` for every non-ref `order_by` term.
The FAIL_TO_PASS test `test_aggregation_random_ordering` exercises a queryset that
both aggregates (`Count`) and orders randomly (`order_by('?')`): the random
ordering term must contribute NO grouping column, otherwise `RANDOM()` enters the
`GROUP BY` and breaks the aggregation (every row becomes its own group).

### What the function does

`Random` is a SQL `Func` of arity 0 emitting the `RANDOM()` (DB-specific) function.

- **base_commit (buggy):** `Random` defines no `get_group_by_cols`, so it inherits
  `BaseExpression.get_group_by_cols` (`django/db/models/expressions.py:349-355`):

  ```python
  def get_group_by_cols(self, alias=None):
      if not self.contains_aggregate:
          return [self]
      cols = []
      for source in self.get_source_expressions():
          cols.extend(source.get_group_by_cols())
      return cols
  ```

  `Random` is not an aggregate (`contains_aggregate` is `False`) and has zero
  source expressions, so this returns `[self]` — a single grouping column, the
  `Random` expression itself. When such a term sits in `order_by`, the compiler
  injects `RANDOM()` into the `GROUP BY`, breaking the grouping (the issue).

- **post-fix:** `Random.get_group_by_cols(self, alias=None)` is overridden to
  `return []` — the non-deterministic ordering term contributes no grouping
  columns, so random ordering never alters the aggregation grouping.

### Inputs ↔ Python expression bijection

| Lean input | Python expression | type | notes |
|---|---|---|---|
| `self` | the `Random` instance the method is called on | `OrderingExpr` | modeled by its emitted SQL function name; arity-0, no source expressions. Its only role is to be the receiver; its field is read by neither the buggy nor the fixed branch's *return value structure* except, in the buggy default, to form `[self]`. |
| `alias` | the `alias` keyword argument (`alias=None`) | `Option String` | the optional output alias passed by the compiler; both buggy and fixed code ignore it for `Random`. Modeled as `Option String` (`none ↔ None`). |

### result bijection

| Lean | Python | bijection |
|---|---|---|
| `result : List GroupByCol` (return of `randomGroupingColumns`) | the `list` returned by `Random.get_group_by_cols` | identity on the carrier: a list of grouping-column expressions, each modeled by the SQL fragment it compiles to. Post-fix the list is empty (`[]`); pre-patch it is the singleton `[self]` (the `RANDOM()` fragment). |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `Random` instance | `OrderingExpr` (`{ function : String }`) | the random-value generator, identified by its SQL function string (e.g. `"RANDOM"`); arity 0. |
| `alias` (`None` or a `str`) | `alias : Option String` | `None ↔ none`, `s ↔ some s`. |
| `get_group_by_cols(...)` return (`list` of expressions) | `result : List GroupByCol` | a contributed grouping-column list; post-fix `[]`; pre-patch `[self]` modeled as `[self.function]` (the single SQL fragment the random term would compile to). |

The method operates at the value level (it returns a fixed list with no
per-element computation), so `List String` is the apt model (§2 cheatsheet).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — a
  non-deterministic ordering term contributing no grouping columns — is modeled
  DEEPLY in Lean as returning the empty list, not axiomatized (SPEC_GUIDE §3: a
  deeply-modeled changed op is never axiomatized). The fixed method calls nothing;
  it is a leaf returning a constant `[]`. There is no `opaque`/`axiom` callee whose
  contract the proof consumes, so `axiom_check.py` is a skip stub and G-AX skips.
- **No flag dependency.** `get_group_by_cols` for `Random` takes only the optional
  `alias`; its return does not branch on any mode flag. The DB backend only
  affects the *name* of the random function (`RANDOM` / `RAND` /
  `DBMS_RANDOM.VALUE`), which is irrelevant to the grouping-column contribution
  (empty on every backend).
- **`BaseExpression.get_group_by_cols`** (`django/db/models/expressions.py:349`)
  is the inherited default that produces the pre-patch buggy `[self]`. It is not an
  unchanged callee whose property the proof consumes; it is the behavior the
  override REPLACES, captured directly in the prepatch impl skeleton.

## G-CONF fuzz seed

Pinned LCG seed: **13569** (see `conformance_check.py` `SEED`). Corpus: random
`function` strings (drawn from a small SQL-name alphabet) crossed with
`alias ∈ {None} ∪ {random strings}`, over ≥1e5 fuzzed inputs, diffed against an
in-process replica of the post-patch `Random.get_group_by_cols` (which returns
`[]` for every input).
