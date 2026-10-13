# refinement.md — sympy__sympy-19783

The operation-by-operation correspondence between `model.py`'s implementations
(`identity_mul`, `dagger_mul`, and the deep classification predicates) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX, NOT consumed), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This is a **multi-site** change with **two independently-fixed behaviours**,
each modeled as its own contracted function and each with its own
verification-failing prepatch skeleton (G-DIFF).

## Site 1 — `IdentityOperator.__mul__` (`operator.py:308-313`)

Gold hunk:
```
-        if isinstance(other, Operator):
+        if isinstance(other, (Operator, Dagger)):
             return other
         return Mul(self, other)
```

| # | model.py impl op (`identity_mul`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1.1 | parameter `other_kind: int` | the `other` argument | R | a SymPy operand ↔ its integer kind tag (mapping.md §2). |
| 1.2 | guard `is_operator_like(other_kind) or is_conjugate(other_kind)` | `isinstance(other, (Operator, Dagger))` | A-reference | the membership test is modeled **deeply** as the kind disjunction `k∈{0,1,2}`; G-AX (`check_classification`) asserts `is_operator_like(k) or is_conjugate(k)` ⇔ the real `isinstance(rep, (Operator, Dagger))` on a representative per kind. `IdentityOperator` ⊂ `Operator` (kind 1 operator-like); `Dagger` ⊄ `Operator` (kind 2 caught by the new `Dagger` disjunct — the discriminating fix). |
| 1.3 | collapse branch `return Product(False, other_kind, 1, other_kind)` | `return other` | R + A-reference | the method returns the right operand; `is_mul=False`, `result_kind=other_kind` records "collapsed to the right operand of that kind". G-AX (`check_identity_mul`) asserts the real `I*rep` equals exactly that operand. |
| 1.4 | fallthrough `return Product(True, other_kind, 1, other_kind)` | `return Mul(self, other)` | R + A-reference | the generic symbolic product; `is_mul=True`. `Mul(I, rep)` may canonicalize but is still the generic-product case. G-AX asserts the real `I*rep` equals `Mul(I, rep)`. |

Discriminating content: the new `Dagger` disjunct makes kind 2 collapse.
`model_prepatch.py` drops it (`if is_operator_like(other_kind)`), so for kind 2
it returns `is_mul=True` while the spec requires `is_mul=False` — **fails** the
postcondition `Result().is_mul == (not (is_operator_like or is_conjugate))`
(G-DIFF, site 1).

## Site 2 — `Dagger.__mul__` (`dagger.py`, new method)

Gold hunk (new method; also imports `Mul`):
```
+    def __mul__(self, other):
+        from sympy.physics.quantum import IdentityOperator
+        if isinstance(other, IdentityOperator):
+            return self
+        return Mul(self, other)
```

| # | model.py impl op (`dagger_mul`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 2.1 | parameter `other_kind: int`; LHS fixed as the conjugate (kind 2) | `self` (a `Dagger`), `other` | R | operand ↔ kind tag; `self` is a conjugate factor (kind 2). |
| 2.2 | guard `is_identity(other_kind)` | `isinstance(other, IdentityOperator)` | A-reference | modeled deeply as `k==1`; G-AX (`check_classification`) asserts `is_identity(k)` ⇔ the real `isinstance(rep, IdentityOperator)`. |
| 2.3 | collapse branch `return Product(False, 2, 2, other_kind)` | `return self` | R + A-reference | the method returns the conjugate `self`; `is_mul=False`, `result_kind=2`. G-AX (`check_dagger_mul`) asserts the real `Dag*I` equals `Dag` (kind 2). |
| 2.4 | fallthrough `return Product(True, 2, 2, other_kind)` | `return Mul(self, other)` | R + A-reference | the generic product; `is_mul=True`. G-AX asserts the real `Dag*rep` equals `Mul(Dag, rep)` (incl. `Dagger(O)*Dagger(O)==Dagger(O)**2`, the `Mul` canonicalization). |

Discriminating content: the whole method is new. `model_prepatch_2.py` models
its absence (the generic `Expr.__mul__` always builds `Mul`), returning
`is_mul=True` even for kind 1, while the spec requires `is_mul=False` —
**fails** the postcondition `Result().is_mul == (not is_identity(other_kind))`
(G-DIFF, site 2).

## No kind-3 (unexpressible-changed-op) steps

Every step is R or A-reference (or I). The two operations that genuinely
*changed* — the two `__mul__` methods — are modeled **deeply** (spelled-out
integer-kind dispatch), not hidden behind an axiom about the function under
change. There is therefore **no consumed axiom** (`axioms` region is empty):
the membership tests and product construction are the A-reference deep models,
validated `== the real methods` by axiom_check.py / G-AX. (`Mul` itself is the
unchanged SymPy product constructor; the patch does not change it — its
canonicalization is part of the generic-product reference the deep model is
checked against, not a consumed axiom.)

## verify(model) ⇒ resolved

`identity_mul` verifies only if it collapses exactly on kinds {0,1,2}
(operator-like OR conjugate) and is the generic product on kind 3 (step 1.2),
returning the right operand on collapse (1.3); `dagger_mul` verifies only if it
collapses exactly on kind 1 (identity), returning the conjugate (2.3). By R
(operand ↔ kind, return ↔ `Product`) these are the gold `__mul__` bodies; by
G-AX the deep classification predicates and the two dispatch functions equal the
real `IdentityOperator.__mul__` / `Dagger.__mul__` on every operand kind, and
the F2P discriminating equalities hold (`I*Dagger(O)==Dagger(O)`,
`Dagger(O)*I==Dagger(O)`, …). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and audited deep models —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: deep-model/A-reference soundness (G-AX) and refinement fidelity
(this document, G-EQ).
