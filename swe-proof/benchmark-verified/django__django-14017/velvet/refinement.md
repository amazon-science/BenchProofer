# refinement.md — django__django-14017

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`combineConditions` `do` block plus the deep `combineResult` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no axioms** (A) in this
bundle. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The admissibility guard — `Q._combine`

Gold hunk (`django/db/models/query_utils.py:42-44`):
```
     def _combine(self, other, conn):
-        if not isinstance(other, Q):
+        if not(isinstance(other, Q) or getattr(other, 'conditional', False) is True):
             raise TypeError(other)
```

| # | Solution.lean impl op (`combineConditions`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `other : Operand` (`isFilterNode`, `isCondition`) | the `other` argument of `_combine` | R | the right operand ↔ its two touched observables: `isinstance(other, Q)` ↔ `isFilterNode`; `getattr(other, 'conditional', False) is True` ↔ `isCondition` (mapping.md §2). G-CONF bridges via `observe`. |
| A2 | parameter `combined : CombinedNode` | the node `_combine` builds from `self`/`other` when admissible (`query_utils.py:45-58`) | R | the construction is UNCHANGED by the patch and not inspected by the guard; abstracted as an opaque carrier supplied as a free input, so the spec quantifies over ALL combination results — strictly weaker than the real construction, no axiom owed (directive 7, mapping.md §3). G-CONF holds it fixed across both sides. |
| A3 | `if other.isFilterNode \|\| other.isCondition then Except.ok combined else Except.error .notCombinable` | `if not(isinstance(other, Q) or getattr(other, 'conditional', False) is True): raise TypeError(other)` … (else fall through to the unchanged combination) | I | the CHANGED guard, modeled deeply: admit when `other` is a filter-condition container OR advertises a boolean condition; otherwise reject. `Except.ok combined` ↔ falling through to build/return the combination; `Except.error .notCombinable` ↔ `raise TypeError(other)`. G-CONF refutes any divergence over the four operand classes. |
| A4 | result `Except CombineErr CombinedNode` | the value `_combine` returns, or the `TypeError` it raises | R + I | admission yields `Except.ok combined` (the unchanged node); rejection yields `Except.error .notCombinable` ↔ the raised `TypeError`. G-CONF compares the (ok/err) verdict on every input. |

Discriminating content of the change — an operand that is NOT a filter-condition
container but DOES advertise a boolean condition (`isFilterNode = false`,
`isCondition = true`) must be ADMITTED, not rejected — lives in the
`other.isCondition` disjunct of the guard (model) ⇔ the added `or getattr(other,
'conditional', False) is True` (real). The pre-patch guard admitted only when
`isinstance(other, Q)`; `Solution_prepatch.lean` reproduces that
(`if other.isFilterNode then Except.ok … else Except.error …`) and **fails** the
postcondition `out = combineResult other combined`, leaving the goal that
reduces to the missing case `other.isCondition = true` (G-DIFF) — exactly the
`Q() & Exists(...)` case the F2P `test_boolean_expression_combined` /
`test_boolean_expression_combined_with_empty_Q` exercise.

## B. No consumed axioms / no A-reference callee

The only operation that genuinely *changed* — the admissibility guard — is
modeled **deeply** (the `combineResult` def + the branch on `isFilterNode ||
isCondition`), not hidden behind an axiom about the function under change. The
unchanged combination is a free input, owed no contract. Hence: no module-level
`axiom`, no `axiom_check.py`, `gates.G-AX = skip` (cf. django__django-13590,
django__django-11149).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed guard is expressed concretely (A3); the two
type/attribute reads `isinstance(other, Q)` and `getattr(other, 'conditional',
False) is True` are abstracted to the booleans `isFilterNode` / `isCondition`
(R, mapping.md §2). Nothing inexpressible is hidden.

## D. verify(Solution) ⇒ resolved

`combineConditions` verifies only if its output equals `combineResult` — admit
(return the unchanged combination) exactly when `other` is a filter-condition
container OR advertises a boolean condition, and reject otherwise. By R
(`Operand ↔ other`, `CombinedNode ↔ the built node`, mapping.md §2) the verified
guard equals the gold patch's `if not(isinstance(other, Q) or getattr(other,
'conditional', False) is True)` dispatch on every tested operand; by G-CONF the
R/I transliteration agrees with `patch.diff`'s admissibility behaviour on ≥10⁵
inputs across the four operand classes (filter-condition container, condition-
advertising, non-condition, no-attribute). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there is no axiom trust point.
