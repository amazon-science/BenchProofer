# refinement.md — sympy__sympy-19783

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `daggerProduct` and `identityProduct` `do` blocks, plus the deep
membership models) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed** where the proof
uses an axiom's `ensures`, **A-reference** where a deep model is validated ==
the real callee by G-AX), or **I** (identical concrete op). EVERY step is R, A,
or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs by **G-AX** (`axiom_check.py`); the narrative by
**G-EQ**. Claim: any impl verifying against this frozen spec, refined per the
maps below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The conjugate-object product — `Dagger.__mul__` (`dagger.py`, ADDED)

Gold hunk:
```python
+    def __mul__(self, other):
+        from sympy.physics.quantum import IdentityOperator
+        if isinstance(other, IdentityOperator):
+            return self
+
+        return Mul(self, other)
```

| # | Solution.lean impl op (`daggerProduct`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `self other : QExpr`; `require isDaggerClass self` | `self` (a `Dagger`), `other` | R | `QExpr` ↔ symbolic object (mapping.md §2). `self` is the conjugate-object receiver — its dispatch precondition. Neither operand is `mut` (read-only, directive 5). |
| A2 | `if isIdentityClass other then …` | `if isinstance(other, IdentityOperator):` | A-reference | the identity-membership test is the unchanged hierarchy inspection, deep-modeled as `isIdentityClass` and validated == real `isinstance(other, IdentityOperator)` by G-AX. |
| A3 | `return self` | `return self` | I | identical: the collapse returns the conjugate object itself (echoes the operand — no answer-key). |
| A4 | `return QExpr.mul self other` | `return Mul(self, other)` | I + R | the fall-through product; a RESULT-position `QExpr.mul` is realized as the real constructor **call** `Mul(·,·)` with default evaluation — literally the same op the gold body performs, so any normalization the real constructor applies is inherited identically (mapping.md §2, result side). Transliterated as such by G-CONF. |

Discriminating content: `Dagger(O) * IdentityOperator()` must collapse to
`Dagger(O)`, not stay `Mul(Dagger(O), I)`. `Solution_prepatch.lean` reproduces
the pre-patch reality (no `Dagger.__mul__` → product is always `Mul`) and
**fails** the clause `isIdentityClass other = true → self.mul other = self`
(G-DIFF). G-CONF flags it pre-patch on `Dagger(·)*I`.

## B. The identity product — `IdentityOperator.__mul__` (`operator.py:308`)

Gold hunk:
```python
-        if isinstance(other, Operator):
+        if isinstance(other, (Operator, Dagger)):
             return other
         return Mul(self, other)
```

| # | Solution.lean impl op (`identityProduct`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `self other : QExpr`; `require self = QExpr.ident` | `self` (the `IdentityOperator`), `other` | R | `self` is the identity receiver. Neither operand `mut` (directive 5). |
| B2 | `if isOperatorClass other \|\| isDaggerClass other then …` | `if isinstance(other, (Operator, Dagger)):` | A-reference | the widened membership test, deep-modeled as the disjunction `isOperatorClass ∨ isDaggerClass`; each disjunct validated == its real `isinstance` arm by G-AX. The `isDaggerClass` arm is the fix (the pre-patch tested `Operator` only). |
| B3 | `return other` | `return other` | I | identical: the collapse returns the other operand (echoes it — no answer-key). |
| B4 | `return QExpr.mul self other` | `return Mul(self, other)` | I + R | fall-through product; result-side realization = the real constructor call with default evaluation, identical to the gold body's op (mapping.md §2). |

Discriminating content: `IdentityOperator() * Dagger(O)` must collapse to
`Dagger(O)`, not stay `Mul(I, Dagger(O))`. `Solution_prepatch_2.lean` reproduces
the pre-patch test (`isOperatorClass other` only) and **fails** the clause
`isDaggerClass other = true → QExpr.ident.mul other = other` (G-DIFF). G-CONF
flags it pre-patch on `I*Dagger(·)`.

Two independently-observable fixed behaviors → two prepatches (one per method),
per SPEC_GUIDE §3 (G-DIFF needs one failing prepatch per fixed behavior). The
two F2P tests `test_dagger_mul` and `test_identity` exercise sites A and B
respectively.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The two operations that genuinely *changed* —
the product dispatch of each method — are modeled **deeply** as the `do` blocks
(the `if isIdentityClass …` / `if isOperatorClass ∨ isDaggerClass …` branches and
the `mul`/operand results), NOT hidden behind an axiom about the function under
change. The only borrowed facts are the three UNCHANGED membership tests
(A-references), validated by G-AX. No consumed axiom; no dead axiom.

## D. verify(Solution) ⇒ resolved

`daggerProduct` verifies only if its output equals `daggerProd self other`
(collapse against the identity, else `mul`); `identityProduct` only if its output
equals `identityProd self other` (collapse against operator-OR-conjugate, else
`mul`). By R (`QExpr` ↔ symbolic object, `mul` ↔ `Mul`) the verified dispatches
equal the gold `__mul__` bodies on the carrier image; by G-AX the membership deep
models equal the real `isinstance` tests (A-reference); by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs, 0
disagreements. Therefore a model satisfying this spec, refined by the maps above,
is the gold patch up to type refinement and audited membership tests — and the
gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1:
A-reference soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
