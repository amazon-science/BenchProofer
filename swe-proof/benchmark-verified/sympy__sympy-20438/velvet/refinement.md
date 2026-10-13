# refinement.md — sympy__sympy-20438

Operation-by-operation correspondence between `Solution.lean`'s three impl
regions (`everyElementMember`, `setsCoincide`, `guardedSimplify`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A** (axiomatized/modeled callee — **A-consumed** where the
proof uses an axiom's `ensures`, **A-reference** where a deep model is validated
== the real callee by G-AX), or **I** (identical concrete op). EVERY step is R,
A, or I. There is no kind-3 (changed-op-Velvet-cannot-express) step.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1) which runs the REAL patched repo functions as the oracle; the A leg
(the `fuzzy_and` deep model) is audited by **G-AX** (`axiom_check.py`).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

The three modeled behaviors are independent fixes to the same issue
("`is_subset` gives wrong results" — `problem_statement`). Each has its own
`Solution_prepatch_<k>.lean` reproducing the pre-patch bug and failing G-DIFF on
the discriminating clause.

## Behavior #1 — `everyElementMember` ↔ new `(ProductSet, FiniteSet)` subset rule

Gold hunk (`sympy/sets/handlers/issubset.py`):
```
+@dispatch(ProductSet, FiniteSet)  # type: ignore # noqa:F811
+def is_subset_sets(a_ps, b_fs): # noqa:F811
+    return fuzzy_and(b_fs.contains(x) for x in a_ps)
```

| # | Solution.lean impl op (`everyElementMember`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1a | parameter `memberships : List (Option Bool)` | `b_fs.contains(x) for x in a_ps` — the per-element membership verdicts | R + A-reference (input) | `Option Bool` ↔ `{True,False,None}` (mapping.md §2). The list entries ARE the real `b_fs.contains(x)` values in product-enumeration order; `contains` is unchanged, so each entry is a reference callee value. G-CONF computes the real `contains` on the real `ProductSet` elements to build the input. |
| 1b | the backward `while` fold computing `result := tand2 m result`, proven `result = triAll (memberships.drop i)` | `fuzzy_and(...)` over the verdicts | A-reference + I | the changed op is modeled **deeply**: `tand2`/`triAll` (pure region) and the verified loop ARE the three-valued conjunction. The fold ops (`tand2`, the loop) are **I** (concrete, transliterated by G-CONF as `tri_all`); the equality of that deep model to the real `fuzzy_and` is the **A-reference** G-AX validates (mapping.md §3.1). No consumed `fuzzy_and` axiom. |
| 1c | `return result` (`Option Bool`) | the rule's return value (later `tfn`-mapped at the `is_subset` boundary) | R | `tfn` is the identity on the three-valued domain (mapping.md §2), so the returned `Option Bool` is the observable verdict. |

Discriminating content: pre-patch there was **no** `(ProductSet, FiniteSet)`
rule, so the query fell through to the generic `(Set, Set)` rule returning
`None` — never inspecting the elements. `Solution_prepatch_1.lean` reproduces
that (`return none`) and **fails** `out = triAll memberships` (G-DIFF), since
the real verdict for the F2P case (`b.is_subset(c) is True`,
`b.is_subset(d) is False`) is definite, not unknown.

## Behavior #2 — `setsCoincide` ↔ changed `(Set, Set)` coincidence rule

Gold hunk (`sympy/sets/handlers/comparison.py`):
```
-    return None
+    return tfn[fuzzy_and(a.is_subset(b) for a, b in [(lhs, rhs), (rhs, lhs)])]
```
(The deletion of the dead `@dispatch(FiniteSet, Interval) return False` rule is
a no-op de-dup: an identical `(FiniteSet, Interval)` rule already precedes it;
behaviour-neutral, not modeled.)

| # | Solution.lean impl op (`setsCoincide`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 2a | parameters `subAB subBA : Option Bool` | `lhs.is_subset(rhs)`, `rhs.is_subset(lhs)` | R + A-reference (input) | `Option Bool` ↔ `{True,False,None}`. The two inputs ARE the real mutual-containment verdicts; `is_subset` is unchanged at this call site (it itself routes through behavior #1's new rule for the F2P case — G-CONF runs the fully-patched repo so the composition is exercised end to end). |
| 2b | `return tand2 subAB subBA`, proven `out = triAll [subAB, subBA]` | `tfn[fuzzy_and([...] )]` over the two verdicts | A-reference + I + R | the two-element `fuzzy_and` is the deep model `triAll [subAB, subBA]`, which `tand2_true_right` collapses to `tand2 subAB subBA` (proof). `tand2`/`triAll` == `fuzzy_and` is the A-reference (G-AX). `tfn` is the R-identity on the three-valued domain (mapping.md §2). |

Scope note (mapping.md §1): only **mixed** `FiniteSet`↔`ProductSet` pairs reach
this generic `(Set, Set)` rule; same-type pairs dispatch to their own specific
`_eval_is_eq` rules and are out of this model's scope. G-CONF restricts the
oracle to mixed pairs accordingly.

Discriminating content: pre-patch the generic rule returned `None`,
never consulting the containment facts. `Solution_prepatch_2.lean` reproduces
that (`return none`) and **fails** `out = triAll [subAB, subBA]` (G-DIFF), since
the F2P case `Eq(c, b).simplify() is S.true` / `Eq(a, c).simplify() is S.false`
needs the definite verdict.

## Behavior #3 — `guardedSimplify` ↔ the two `_eval_simplify` Expr guards

Gold hunks (`sympy/core/relational.py`, two structurally identical sites at the
`Relational` and `Equality` `_eval_simplify`):
```
+        from sympy.core.expr import Expr
   ...
+            if not isinstance(r.lhs, Expr) or not isinstance(r.rhs, Expr):
+                return r
```

| # | Solution.lean impl op (`guardedSimplify`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 3a | parameter `bothExpr : Bool` | `isinstance(r.lhs, Expr) and isinstance(r.rhs, Expr)` | R | the run-time type predicate the guard tests; G-CONF supplies the real value. |
| 3b | parameter `r : Int`, `normal : Int` | the relation object; the general-simplification result | R | the relation's identity is observed via an opaque `Int` token (mapping.md §2); `normal` is the result of the unchanged general path (a reference value G-CONF supplies). |
| 3c | `if bothExpr then return normal else return r` | `if not (Expr and Expr): return <relation unchanged>` else proceed | I | the guard's control flow, transliterated. Both sites share this single model (`Relational` and `Equality` differ only in what feeds `normal`; the guard is identical). |

Discriminating content: pre-patch the general path ran unconditionally and
formed `lhs - rhs`, raising `AttributeError` on non-`Expr` operands (the
`'Complement' object has no attribute 'equals'` traceback in
`problem_statement`). `Solution_prepatch_3.lean` reproduces that (`return
normal` always) and **fails** `bothExpr = false → out = r` (G-DIFF).

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The genuinely *changed* operations — the new subset
rule (#1), the new coincidence rule (#2), the new guard (#3) — are each modeled
**deeply** (the spelled-out `triAll` fold; the `tand2` conjunction; the explicit
`if bothExpr` guard), not hidden behind an axiom about the function under
change. The only A obligation is the **A-reference** `triAll`/`tand2` ==
`fuzzy_and` (an UNCHANGED stdlib callee), validated by G-AX. There are NO
consumed axioms.

## verify(Solution) ⇒ resolved

`everyElementMember` verifies only if its output equals the three-valued
conjunction of the real membership verdicts (#1); `setsCoincide` only if it
equals the three-valued conjunction of the real mutual-containment verdicts
(#2); `guardedSimplify` only if it returns the relation unchanged exactly when
the operands are not both expressions (#3). By R (the `Option Bool` ↔
three-valued, `tfn`/token identities) the verified impls equal the gold patch's
behaviour on the tested inputs; by G-AX the deep model `triAll`/`tand2` equals
the real `fuzzy_and` (A-reference); by G-CONF the R/I transliteration agrees
with `patch.diff`'s REAL patched functions on >10⁵ inputs (0 disagreements).
Therefore a model satisfying this spec, refined by the maps above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: deep-model
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
