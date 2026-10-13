# refinement.md — operation correspondence (django__django-17084)

Maps every op in `implementation_requiresSubqueryWrap` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python computes two reference flags by OR-accumulating per-reference
attribute reads across all requested aggregates, then OR's both (together with
the pre-existing structural disjuncts) into the subquery-wrapping decision. We
model the loop op-for-op and the disjunction concretely.

| # | Lean impl op | patch.diff / base counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut refsSubquery := false` | `refs_subquery = False` (base, line 405) | I | identical accumulator initialization |
| 2 | `let mut refsWindow := false` | `refs_window = False` (**added** line 406) | I | identical accumulator initialization; the new accumulator the patch introduces |
| 3 | `for agg in aggregates do …` | `for alias, aggregate_expr in aggregate_exprs.items(): …` (loop over requested aggregates) | R | dict-of-aggregates ↔ `List AggregateExpr`; only `get_refs()` matters, alias keys irrelevant to the decision (mapping.md) |
| 4 | `refsSubquery := refsSubquery \|\| agg.refs.any (·.isSubqueryExpr)` | `refs_subquery \|= any(getattr(self.annotations[ref], "subquery", False) for ref in aggregate.get_refs())` | R | unchanged op; `any(getattr(..., "subquery", False))` ↔ `refs.any (·.isSubqueryExpr)` under the boolean-field bijection (mapping.md) |
| 5 | `refsWindow := refsWindow \|\| agg.refs.any (·.isWindowExpr)` | `refs_window \|= any(getattr(self.annotations[ref], "contains_over_clause", True) for ref in aggregate.get_refs())` (**added** lines 423-426) | R | the **changed op** modeled deeply: `any(getattr(..., "contains_over_clause", True))` ↔ `refs.any (·.isWindowExpr)`; the `True` default is resolved into `isWindowExpr` per mapping.md. NOT axiomatized. |
| 6 | `return otherConditions \|\| refsSubquery \|\| refsWindow` | the `if (isinstance(group_by, tuple) or is_sliced or has_existing_aggregation or refs_subquery or refs_window or qualify or distinct or combinator):` truth value, with `refs_window` **added** at line 459 | R/I | the pre-existing disjuncts are collapsed into `otherConditions` (R: their unchanged internal computation is out of scope); appending `\|\| refsWindow` to the disjunction is the identical concrete op (I) the patch performs |

No A-consumed rows: the proof discharges the disjunction directly (`Bool.or`
associativity/commutativity + the loop↔fold equality); no UNCHANGED callee
property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: the attribute reads (`getattr` of the two flags) are
reproduced concretely as boolean fields (R/I ops), not abstracted behind a model
that would need G-AX validation. No changed-inexpressible op.

The discriminating clause is row 5: the patch adds the `refsWindow` accumulator
and OR's it into the decision (row 6). The prepatch impl never computes or
includes the window flag, so it returns
`otherConditions || refsSubquery`, whereas the frozen
`problem_spec_requiresSubqueryWrap` requires
`otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates`.
Whenever some referenced annotation has `isWindowExpr = True` while
`otherConditions = false` and no reference is a subquery, the spec demands `True`
but the prepatch yields `False` — so the prepatch `correct_requiresSubqueryWrap`
cannot close (the G-DIFF signal). This is exactly the F2P scenario: an aggregate
(`Sum`) referencing a `Window` annotation must force the wrapping subquery.
