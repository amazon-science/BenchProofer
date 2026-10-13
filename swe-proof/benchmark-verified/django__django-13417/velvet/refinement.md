# refinement.md — django__django-13417

The operation-by-operation correspondence between `Solution.lean`'s `ordered`
impl region (and the `isOrdered` pure decision it is pinned to) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures` — none here),
**A-reference** (deep model validated == real callee — none here), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

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

| # | Solution.lean impl op (`ordered`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `isEmpty : Bool` | `isinstance(self, EmptyQuerySet)` | R | the repo expression is consumed only as a bool by `if ...: return True`; modelled as the bool it evaluates to (mapping.md §2). |
| A2 | `if isEmpty then return true` | `if isinstance(self, EmptyQuerySet): return True` | I | identical control flow / return. |
| A3 | param `hasRawOrder : Bool` | `self.query.extra_order_by or self.query.order_by` | R | the disjunction `extra_order_by or order_by` is consumed only as a truth value; modelled as the single bool it evaluates to (the two repo attributes are tuples/lists used purely for truthiness — mapping.md §2). |
| A4 | `if hasRawOrder then return true` | `if self.query.extra_order_by or self.query.order_by: return True` | I | identical control flow / return. |
| A5 | param `defaultOn : Bool` | `self.query.default_ordering` | R | a bool attribute, consumed for truthiness (mapping.md §2). |
| A6 | param `modelHasOrder : Bool` | `self.query.get_meta().ordering` | R | `Meta.ordering` is a list/tuple consumed only for truthiness; modelled as the bool it evaluates to (mapping.md §2). |
| A7 | param `isGrouped : Bool` | `self.query.group_by` | R | `group_by` is `None` / `True` / a tuple, consumed here only via `not self.query.group_by`, i.e. purely for truthiness; modelled as the bool it evaluates to (mapping.md §2). |
| A8 | `if defaultOn && modelHasOrder && !isGrouped then return true` | `elif (self.query.default_ordering and self.query.get_meta().ordering and not self.query.group_by): return True` | I (under A5/A6/A7 refinements) | identical boolean conjunction and control flow; the added `&& !isGrouped` conjunct is the gold's `and not self.query.group_by`. (`Solution.lean` nests `if/else` rather than `elif` because Velvet bans `elif`; the control flow is identical — the nested `else` branch is reached on exactly the same condition as the gold `elif`.) |
| A9 | `else return false` | `else: return False` | I | identical. |

The discriminating content of the change — a grouped result set with only an
inherited default ordering must NOT be reported as ordered — lives in the
`&& !isGrouped` conjunct of A8. The pre-patch body omits exactly this conjunct;
`Solution_prepatch.lean` reproduces that omission (`if defaultOn &&
modelHasOrder then`) and **fails** the postcondition `out = isOrdered(...)`
(equivalently the pinned clause
`(isEmpty = false ∧ hasRawOrder = false ∧ isGrouped = true) → out = false`),
which is the spec sensing the change (G-DIFF). Confirmed: prepatch fails with
the unsolved goal `isGrouped = false` under hypotheses `isEmpty = false`,
`hasRawOrder = false`, `defaultOn = true ∧ modelHasOrder = true` — i.e. the
grouped-with-default-ordering counterexample.

## B. No axioms, no kind-3 steps

`ordered` calls no library/utility callee that the patch leaves unchanged and
that Lean cannot express — the five repo expressions it reads (`isinstance(...)`,
`extra_order_by or order_by`, `default_ordering`, `get_meta().ordering`,
`group_by`) are simple attribute/identity reads consumed purely for their truth
value, refined to `Bool` parameters (R). There is therefore **no consumed axiom
and no A-reference** in this bundle (the `axioms` region is empty) and there is
no `axiom_check.py` (G-AX vacuous). Every step above is R or I; there is no
changed operation that is inexpressible (no kind-3).

## C. verify(Solution) ⇒ resolved

`ordered` verifies only if its result equals the exact five-input boolean
decision `isOrdered` (A8 supplies the new `!isGrouped` conjunct). By the
R-refinements (each repo truthy expression ↔ its bool value, mapping.md §2) the
verified decision is, expression-for-expression, the gold property body.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to the truthy-to-bool type refinement — and the gold patch resolves
(G-RESOLVE). The added F2P tests
(`test_annotated_default_ordering`, `test_annotated_values_default_ordering`)
construct a `GROUP BY` queryset on a model with `Meta.ordering` (so `isEmpty =
false`, `hasRawOrder = false`, `defaultOn = true`, `modelHasOrder = true`,
`isGrouped = true`) and assert `qs.ordered is False` — exactly the clause the
`!isGrouped` conjunct pins. The only trust point is refinement fidelity (this
document + mapping.md, G-EQ); there are no axioms (G-AX vacuous), and the R/I
boolean shadow is mechanically refuted by G-CONF.
