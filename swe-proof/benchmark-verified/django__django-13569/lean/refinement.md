# refinement.md — django__django-13569

Maps every operation in `randomGroupingColumns` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op). Every step is R, A, or I.

## Modeled function: `randomGroupingColumns` (`Random.get_group_by_cols`)

Post-patch repo code (`patch.diff`):
```python
def get_group_by_cols(self, alias=None):
    return []
```

Lean impl (`randomGroupingColumns`):
```lean
def randomGroupingColumns
    (self : OrderingExpr) (alias : Option String) : List GroupByCol :=
  Id.run do
    return []
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `self : OrderingExpr` parameter | `self` (the bound `Random` instance) | **R** | the random-value generator modeled by its emitted SQL function name; arity 0, no source expressions (mapping.md bijection). |
| 2 | `alias : Option String` parameter | `alias=None` keyword argument | **R** | the optional output alias; `Option String` models `None`/`str`. Ignored by the method body, exactly as in the real code. |
| 3 | `return []` | `return []` | **I** (the fixed op) | **the fix.** The added override returns the empty list unconditionally — a non-deterministic ordering term contributes no grouping columns. `return []` reproduces this exactly. Pre-patch there was no override, so the inherited default returned `[self]` (the buggy singleton). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `Random.get_group_by_cols`.

Refinement equivalence (R/I): the post-patch method returns a fixed empty list for
every receiver and alias; the Lean impl returns `[]` for every `self`/`alias`.
Both are constant-`[]` functions of the same (modeled) inputs, so the R/I legs are
byte-for-byte equal. The downstream consumer `SQLCompiler.get_group_by` extends
the GROUP BY with this list for each non-ref order_by term; an empty contribution
means a random ordering term adds nothing to the grouping — exactly the property
the FAIL_TO_PASS test depends on.

## Soundness check (verify ⟹ correct)

- `problem_spec_randomGroupingColumns self alias result := result = []` pins the
  result EXACTLY (full equality to the empty list) — directive 5 (frame): the sole
  output component is fully determined for every input. No component is left
  unconstrained; no ungrounded oracle (directive 8) — the postcondition is
  dischargeable only by actually returning the empty collection, so a wrong impl
  cannot echo an answer key.
- The prepatch impl returns `[self.function]` — the inherited-default behavior for
  a non-aggregate expression (`return [self]`), modeled as the singleton list of
  the random term's SQL fragment. It violates the spec on EVERY input (a
  one-element list is never `[]`), so its carried gold proof (`rfl`) cannot close
  (G-DIFF/G-PANEL): the LHS reduces to `[self.function]`, the RHS is `[]`.
- This discriminating behavior is precisely what the FAIL_TO_PASS test
  `test_aggregation_random_ordering` exercises: a queryset that aggregates
  (`Count('book')`) and orders randomly (`order_by('?')`). With `[self]`
  contributed (prepatch) the compiler injects `RANDOM()` into the `GROUP BY`,
  shattering the aggregation into one group per row (the wrong counts in the
  issue). With `[]` contributed (gold) the random term adds no grouping column, so
  the aggregation groups correctly.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `Random.get_group_by_cols` (constant `[]`) over hand-picked edge cases plus ≥1e5
  fuzzed `(function, alias)` inputs.
