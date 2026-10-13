# refinement.md — django__django-13417

The operation-by-operation correspondence between `model.py`'s implementation
(the `ordered` impl region and the `is_ordered` pure decision it is pinned to)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `QuerySet.ordered` (`django/db/models/query.py:1217`)

Gold hunk (the property body):
```
  if isinstance(self, EmptyQuerySet):
      return True
  if self.query.extra_order_by or self.query.order_by:
      return True
- elif self.query.default_ordering and self.query.get_meta().ordering:
+ elif (
+     self.query.default_ordering and
+     self.query.get_meta().ordering and
+     # A default ordering doesn't affect GROUP BY queries.
+     not self.query.group_by
+ ):
      return True
  else:
      return False
```

| # | model.py impl op (`ordered`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `is_empty: bool` | `isinstance(self, EmptyQuerySet)` | R | the repo expression is consumed only as a bool by `if ...: return True`; modelled as the bool it evaluates to (mapping.md §2). |
| A2 | `if is_empty: return True` | `if isinstance(self, EmptyQuerySet): return True` | I | identical control flow / return. |
| A3 | param `has_raw_order: bool` | `self.query.extra_order_by or self.query.order_by` | R | the disjunction `extra_order_by or order_by` is consumed only as a truth value; modelled as the single bool it evaluates to (the two repo attributes are tuples/lists used purely for truthiness — mapping.md §2). |
| A4 | `if has_raw_order: return True` | `if self.query.extra_order_by or self.query.order_by: return True` | I | identical control flow / return. |
| A5 | param `default_on: bool` | `self.query.default_ordering` | R | a bool attribute, consumed for truthiness (mapping.md §2). |
| A6 | param `model_has_order: bool` | `self.query.get_meta().ordering` | R | `Meta.ordering` is a list/tuple consumed only for truthiness; modelled as the bool it evaluates to (mapping.md §2). |
| A7 | param `is_grouped: bool` | `self.query.group_by` | R | `group_by` is `None` / `True` / a tuple, consumed here only via `not self.query.group_by`, i.e. purely for truthiness; modelled as the bool it evaluates to (mapping.md §2). |
| A8 | `elif default_on and model_has_order and not is_grouped: return True` | `elif (self.query.default_ordering and self.query.get_meta().ordering and not self.query.group_by): return True` | I (under A5/A6/A7 refinements) | identical boolean conjunction and control flow; the added `and not self.query.group_by` conjunct is the `and not is_grouped` conjunct. |
| A9 | `else: return False` | `else: return False` | I | identical. |

The discriminating content of the change — a grouped result set with only an
inherited default ordering must NOT be reported as ordered — lives in the
`and not is_grouped` conjunct of A8. The pre-patch body omits exactly this
conjunct; `model_prepatch.py` reproduces that omission (`elif default_on and
model_has_order:`) and **fails** the postcondition
`Result() == is_ordered(...)` (equivalently the pinned clause
`Implies(not is_empty and not has_raw_order and is_grouped, not Result())`),
which is the spec sensing the change (G-DIFF). Confirmed: prepatch fails on
`model_prepatch.py:60` "Postcondition ... Result() == is_ordered(...) might not
hold".

## B. No axioms, no kind-3 steps

`ordered` calls no library/utility callee that the patch leaves unchanged — the
five repo expressions it reads (`isinstance(...)`, `extra_order_by or
order_by`, `default_ordering`, `get_meta().ordering`, `group_by`) are simple
attribute/identity reads consumed purely for their truth value, refined to
`bool` parameters (R). There is therefore **no `@ContractOnly` axiom** in this
bundle (the `axioms` region is empty) and `axiom_check.py` has nothing to
execute beyond confirming the no-axiom status. Every step above is R or I;
there is no changed operation that is inexpressible (no kind-3).

## C. verify(model) ⇒ resolved

`ordered` verifies only if its result equals the exact five-input boolean
decision `is_ordered` (A8 supplies the new `not is_grouped` conjunct).
By the R-refinements (each repo truthy expression ↔ its bool value, mapping.md
§2) the verified decision is, expression-for-expression, the gold property
body. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to the truthy-to-bool type refinement — and the gold patch
resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ); there are no axioms (G-AX is vacuous here).
