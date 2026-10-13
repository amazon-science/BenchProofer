# refinement.md — sympy__sympy-20438

Operation-by-operation correspondence between `model.py`'s implementation (the
`product_subset_of_finite` and `finite_sets_equal` impl regions plus the deep
`all_in` fold and the live `member` axiom) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (proof uses this
axiom's `Ensures`), **A-reference** (a deep model validated == the real callee
by `axiom_check.py` / G-AX, NOT consumed), or **I** (identical concrete op).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`, the real
correctness oracle, G-RESOLVE).

## A. The containment site — new `is_subset_sets(ProductSet, FiniteSet)`

Gold hunk (`sympy/sets/handlers/issubset.py`):
```
+@dispatch(ProductSet, FiniteSet)  # type: ignore # noqa:F811
+def is_subset_sets(a_ps, b_fs): # noqa:F811
+    return fuzzy_and(b_fs.contains(x) for x in a_ps)
```

| # | model.py impl op (`product_subset_of_finite`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `elems: List[int]` | iterating `for x in a_ps` (the Cartesian product `iproduct(*a_ps.sets)`) | R | a product element (tuple) ↔ opaque `int` handle; ordered enumeration ↔ `List[int]` (mapping.md §2). |
| A2 | param `finite_id: int` | the receiver `b_fs` (a `FiniteSet`) | R | a `FiniteSet` ↔ a collection identifier (mapping.md §2). |
| A3 | `member(finite_id, e)` per element | `b_fs.contains(x)` per element | A-consumed | `member` is the unchanged membership callee `FiniteSet.contains`; the proof consumes only its purity/totality (no value `Ensures`). G-AX confirms it returns a definite, deterministic bool (mapping.md §3.1). |
| A4 | `res = member(finite_id, e) and res` folded over the loop; postcondition `Result() == all_in(ToSeq(elems), finite_id)` | `fuzzy_and(b_fs.contains(x) for x in a_ps)` | A-reference + I | the changed operation is modeled **deeply**: `all_in` (the spelled-out front-recursive conjunction in the `pure` region) and the verified loop ARE the per-element conjunction. There is no consumed `is_subset` axiom. `fuzzy_and` over fully-decidable concrete terms IS boolean conjunction; the `tfn[...]` wrapper maps `True→S.true`/`False→S.false`. G-AX validates the deep fold **== the real `ProductSet.is_subset(FiniteSet)`** directly on the enumerated elements (no double-mask). |

Discriminator: pre-patch had NO `(ProductSet, FiniteSet)` rule, so the dispatcher
returned `None` (issue: `b.is_subset(c)` prints nothing) and the
intersection fallback gave wrong results. `model_prepatch.py` reproduces "the
containment fact is never computed" (returns `len(elems)==0`, independent of
`member`) and **fails** the postcondition
`Result() == all_in(ToSeq(elems), finite_id)` — the spec sensing the change
(G-DIFF), on the `b ⊆ c` witness (true answer `True`).

## B. The equality site — new `(Set, Set)` rule of `_eval_is_eq`

Gold hunk (`sympy/sets/handlers/comparison.py`):
```
-    return None
+    return tfn[fuzzy_and(a.is_subset(b) for a, b in [(lhs, rhs), (rhs, lhs)])]
```

| # | model.py impl op (`finite_sets_equal`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `product_subset_of_finite(elems_a, id_b)` | `lhs.is_subset(rhs)` | R + A-reference | the containment decision of site A, reused (model: the same verified function; real: `is_subset`). |
| B2 | `product_subset_of_finite(elems_b, id_a)` | `rhs.is_subset(lhs)` | R + A-reference | the reverse containment. |
| B3 | `return a_sub_b and b_sub_a`; postcondition `Result() == (all_in(a,id_b) and all_in(b,id_a))` | `tfn[fuzzy_and(a.is_subset(b) for a,b in [(lhs,rhs),(rhs,lhs)])]` | I | mutual-subset conjunction; `fuzzy_and`/`tfn` over the two decidable containments is the boolean `and` (mapping.md §2/§3.2). |

Discriminator: pre-patch `(Set,Set)` returned `None` (equality undecided; the
issue's `Eq(b,c).simplify()` even crashed). `model_prepatch_2.py` reproduces
"equality is not reduced to mutual subset" (returns `False`, independent of
membership) and **fails** the postcondition
`Result() == (all_in(a,id_b) and all_in(b,id_a))` on the `Eq(c,b) is S.true`
witness (true answer `True`). This is an INDEPENDENTLY-fixed behavior, hence its
own failing prepatch (G-DIFF, one per independently-observable fix).

## C. The routing site — the `isinstance(_, Expr)` guard of equality simplification

Gold hunks (`sympy/core/relational.py`, `Relational._eval_simplify` `:303` and
`Equality._eval_simplify` `:558`):
```
 r = r.func(*[i.simplify(**kwargs) for i in r.args])
 if r.is_Relational:
+    if not isinstance(r.lhs, Expr) or not isinstance(r.rhs, Expr):
+        return r
     dif = r.lhs - r.rhs
     ...
```
```
 e = super()._eval_simplify(**kwargs)
 if not isinstance(e, Equality):
     return e
+if not isinstance(e.lhs, Expr) or not isinstance(e.rhs, Expr):
+    return e
 free = self.free_symbols
 ...
```

| # | model.py impl op (`simplify_equality_route`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | param `both_arith: bool` | `isinstance(r.lhs, Expr) and isinstance(r.rhs, Expr)` (the negated guard condition) | R | "both operands are arithmetic (number-like)" ↔ both operands are `Expr`; a `bool` flag carries the operand-kind discriminator the real guard tests (mapping.md §2/§4). |
| C2 | `if both_arith: return ARITH_PATH()` | the fall-through past the guard into `dif = r.lhs - r.rhs` … (the unchanged arithmetic-reduction path) | R + I | when both operands are `Expr` the guard does not fire and the unchanged arithmetic path runs; its result is opaque to this model, carried by the distinguished token `ARITH_PATH()`. |
| C3 | `else: return collection_outcome(finite_sets_equal(...))`; postconditions `Implies(not both_arith, Result() != ARITH_PATH())` and `Result() == collection_outcome(all_in(a,id_b) and all_in(b,id_a))` | `if not isinstance(...): return r` — the relation is returned unchanged so the arithmetic subtraction is NOT attempted, and the collection-equality rule `_eval_is_eq(Set,Set)` (site B) decides it | R + A-reference + I | the guard ROUTES a non-`Expr` (collection) equality away from the arithmetic path (pre-patch: `dif = lhs - rhs` then `dif.equals(0)` → `AttributeError`) to the collection rule. The model pins the collection outcome to the **deep** `finite_sets_equal`/`all_in` fold of site B (A-reference, validated by G-AX), and `collection_outcome(_) != ARITH_PATH()` pins that the arithmetic path is never taken for a collection. G-AX (`check_route`) asserts the real `Eq(A,B).simplify()` on collection operands does NOT raise and reaches a defined collection decision. |

Discriminator: pre-patch had NO guard, so a collection equality fell through to
`dif = r.lhs - r.rhs` / `dif.equals(0)`, raising
`AttributeError: '<Set>' object has no attribute 'equals'` (the issue's
`Eq(b,c).simplify()` traceback) — the collection rule was never reached.
`model_prepatch_3.py` reproduces "no guard": `simplify_equality_route` returns
`ARITH_PATH()` unconditionally (the collection case still routed into the
arithmetic path) and **fails** the postcondition
`Implies(not both_arith, Result() != ARITH_PATH())` — the spec sensing the change
(G-DIFF), on a collection operand. This is an INDEPENDENTLY-fixed behavior
(the routing guard, separate from the two decision rules), hence its own failing
prepatch.

## D. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-consumed, A-reference, or I. The three operations that genuinely
*changed* — the ProductSet⊆FiniteSet decision (A), the set-equality decision (B),
and the operand-kind routing guard (C) — are modeled **deeply**: the two decisions
via the spelled-out `all_in` fold consumed by `product_subset_of_finite` /
`finite_sets_equal`, and the routing via a verified branch that defers to that same
deep fold and forbids the arithmetic-path token on the collection branch. NONE is
hidden behind an axiom about the function under change. The only consumed axiom,
`member` (**A-consumed**, A3), covers the **unchanged** callee `FiniteSet.contains`
the new code invokes; the three real behaviours
(`ProductSet.is_subset(FiniteSet)`, `Eq(A,B).simplify()` value, and the
non-raising collection routing of `Eq(A,B).simplify()`) appear only as the
**A-references** G-AX validates against.

## E. verify(model) ⇒ resolved

`product_subset_of_finite` verifies only if its result equals the exact
per-element membership conjunction `all_in` (A4); `finite_sets_equal` verifies
only if its result equals the mutual-subset conjunction (B3);
`simplify_equality_route` verifies only if a collection equality is decided by
the deep collection fold AND the arithmetic-path token is never returned for a
collection operand (C3). By R (tuple↔handle, FiniteSet↔id,
`fuzzy_and`/`tfn`↔boolean, `Expr`-ness↔`both_arith`) the verified decisions and
routing equal the gold rules/guard on the tested concrete inputs; by G-AX the
deep folds equal the real `ProductSet.is_subset(FiniteSet)` and
`Eq(A,B).simplify()` value (A-reference), the real collection routing of
`Eq(A,B).simplify()` does not raise and reaches the collection rule
(A-reference 3, `check_route`), and the real `FiniteSet.contains` meets the
`member` axiom (A-consumed). The `relational.py` guard is now modeled as
`simplify_equality_route` (C) rather than left as prose around the decisions; the
gold patch ships it verbatim and resolves (G-RESOLVE). A model satisfying this
spec — refined by the map above — is the gold patch up to type refinement and
audited callees. The trust points are the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
