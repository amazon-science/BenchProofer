# refinement.md — django__django-13128

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveCombined` `do` block and its deep model `dispatchKind`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviorally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The resolve-time selection — `CombinedExpression.resolve_expression` (`django/db/models/expressions.py:476`)

The fix moves the type-driven node-kind selection out of `as_sql` and into
`resolve_expression`, so the result node already carries the right
`output_field` at annotation time (fixing the `FieldError: Expression contains
mixed types` the issue reports). Gold hunk (selection added, top of
`resolve_expression`):

```
+ if not isinstance(self, (DurationExpression, TemporalSubtraction)):
+     try:    lhs_type = lhs.output_field.get_internal_type()
+     except (AttributeError, FieldError): lhs_type = None
+     try:    rhs_type = rhs.output_field.get_internal_type()
+     except (AttributeError, FieldError): rhs_type = None
+     if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type:
+         return DurationExpression(self.lhs, self.connector, self.rhs).resolve_expression(...)
+     datetime_fields = {'DateField', 'DateTimeField', 'TimeField'}
+     if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type:
+         return TemporalSubtraction(self.lhs, self.rhs).resolve_expression(...)
  c = self.copy(); ... ; return c
```

| # | Solution.lean impl op (`resolveCombined`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `selfKind : NodeKind` | the receiver class (`isinstance(self, (DurationExpression, TemporalSubtraction))`) | R | `CombinedExpression↔combined`, `DurationExpression↔durationNode`, `TemporalSubtraction↔temporalNode` (mapping.md §2). G-CONF builds the receiver of each kind. |
| A2 | params `lt rt : Option FieldTag` | `lhs_type`/`rhs_type` = `{lhs,rhs}.output_field.get_internal_type()` with the `(AttributeError, FieldError)→None` guards | R | the resolved operand's internal-type string ↔ `some <tag>`; the exception→`None` collapse ↔ `none` (mapping.md §2). Abstracted INPUTS, not callee axioms (the recursive `resolve_expression` on leaf operands does not change which class is selected). |
| A3 | `if selfKind = combined then …` | `if not isinstance(self, (DurationExpression, TemporalSubtraction))` | I | guard: only a generic node performs the selection; a node already specialized keeps its kind. `selfKind ≠ combined ⇒ out = selfKind`. |
| A4 | `if isIntervalMix lt rt then out := durationNode` | `if 'DurationField' in {lhs_type, rhs_type} and lhs_type != rhs_type: return DurationExpression(...)` | I | `isIntervalMix lt rt := (lt = some durationTag ∨ rt = some durationTag) ∧ lt ≠ rt` transliterates the set-membership-and-inequality test exactly. |
| A5 | `else if conn = minus ∧ isTemporalTag lt ∧ lt = rt then out := temporalNode` | `if self.connector == self.SUB and lhs_type in datetime_fields and lhs_type == rhs_type: return TemporalSubtraction(...)` | I | `SUB ↔ minus`; `isTemporalTag lt := lt ∈ {dateTag,dateTimeTag,timeTag}` ↔ `lhs_type in {'DateField','DateTimeField','TimeField'}`; `lt = rt` ↔ `lhs_type == rhs_type`. Evaluated only when A4 is false (the `else` ladder ↔ the second `if` reached only after the first `return` is skipped). |
| A6 | `else out := combined` | fall-through to `c = self.copy(); … return c` | I | no selection fires ⇒ the node stays generic. |
| A7 | `return out` | the selected node's class is the observable | R | the recursive `.resolve_expression(...)` the gold applies to the chosen `DurationExpression`/`TemporalSubtraction` re-enters with `selfKind ≠ combined`, so it returns that same class (A3) — the observed node kind is exactly `out`. mapping.md §1. |

Discriminating content of the change — a **generic** node over **equal
point-in-time** operands under a **difference** connector must become the
temporal-difference node (and a duration-mixed pair the interval node), so the
resolved node carries a concrete `output_field` and no longer raises the
mixed-type `FieldError`. This lives in `dispatchKind`'s `durationNode`/
`temporalNode` arms. The pre-patch skeleton performed **no** such selection
(the equivalent block sat in `as_sql`, invisible to `resolve_expression`);
`Solution_prepatch.lean` reproduces that (`out := selfKind`; no selection) and
**fails** `out = dispatchKind selfKind conn lt rt` on exactly the
`combined`-node arms (G-DIFF: unsolved goal `NodeKind.combined = if isIntervalMix
… then durationNode else if … then temporalNode else combined`).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
resolve-time node-kind selection — is modeled **deeply** (the spelled-out
`dispatchKind` and the verified `do` block ARE the selection), not hidden behind
an axiom about the function under change. There are **no consumed axioms and no
A-reference deep models**: `lt`/`rt` are R-refined abstracted inputs (mapping.md
§2), and no unchanged callee is pinned by a contract. Hence no `axiom_check.py`
and G-AX skips.

## C. verify(Solution) ⇒ resolved

`resolveCombined` verifies only if its output equals `dispatchKind selfKind conn
lt rt` on every input — i.e. it performs the exact interval/temporal selection
(A4/A5) on generic nodes and is the identity on already-specialized nodes
(A3/A6). By R (`NodeKind`/`Connector`/`Option FieldTag` bijections, mapping.md
§2) the verified selection equals the gold patch's
`CombinedExpression.resolve_expression` selection observed as the resolved node
class; by G-CONF the R/I transliteration of `dispatchKind` agrees with
`patch.diff`'s behavior on 216 boundary + 100 000 fuzzed configs (seed 13128),
0 disagreements. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there is no axiom-soundness trust point (no axioms).
