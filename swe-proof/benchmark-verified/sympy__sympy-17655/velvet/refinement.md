# refinement.md — sympy__sympy-17655

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`scalePoint` `do` block and the deep `scaleCoords` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (modeled callee —
**A-consumed** where the proof uses an axiom's `ensures`, **A-reference** where a
deep model is validated == the real callee by G-AX), or **I** (identical
concrete op). EVERY step is R, A, or I — no kind-3 (changed inexpressible op).

The R/I legs are mechanically refuted by **G-CONF** (skipped here — the impl is
all-A; see below); the A legs and this narrative are audited by **G-EQ** and
**G-AX**. Claim: any impl verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reflected-multiplication site — the new `__rmul__` (`sympy/geometry/point.py:280`, post-patch)

Gold hunk:
```
+    def __rmul__(self, factor):
+        """Multiply a factor by point's coordinates."""
+        return self.__mul__(factor)
```

| # | Solution.lean impl op (`scalePoint`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `factor : Rat` | `factor` arg of `__rmul__` (the left scalar) | R | Python-native exact scalar (`int`/`Fraction`) ↔ `Rat` (mapping.md §2). The reflected-multiply hook fires precisely for such a left operand. |
| A2 | parameter `coords : List Rat` | `self.args` (the point's coordinate tuple) | R | coordinate tuple ↔ `List Rat`, ordered element-wise (mapping.md §2). |
| A3 | `out :| out = scaleCoords coords factor` — the delegation: result is the per-coordinate product of `coords` by `factor` | `return self.__mul__(factor)` — delegate to the unchanged point-by-scalar scaling | A-reference | the new operator's entire content is a call to the UNCHANGED `__mul__`; that callee is modeled **deeply** as `scaleCoords`/`map (· * factor)` (the `pure` region) and the `:|` choice binds `out` to exactly its result. The equality of that deep model to the real `__mul__` is the **A-reference** G-AX validates (mapping.md §3.1). No consumed axiom about the function under change. |
| A4 | `out` returned (`List Rat`); `out.length = coords.length` | `Point(coords, evaluate=False)` re-wrap of the scaled coordinates | R + I | the constructor wrapper is identity on the coordinate carrier (mapping.md §2); the dimension-preservation postcondition mirrors that the result is a point of the same dimension. |

Discriminating content of the change — left-multiplication of a number by a
point yields the **scaled point** (each coordinate `× factor`), not the input
unchanged / an unevaluated product — lives in `out = scaleCoords coords factor`.
The pre-patch has no `__rmul__`, so `number * point` never scales;
`Solution_prepatch.lean` reproduces that "factor never applied" behavior
(`out := coords`) and **fails** `out = scaleCoords coords factor` (G-DIFF), at
exactly that clause.

## B. No consumed axioms

There are no `axiom` declarations and no `:|`-stub *axiom* methods beyond the
single deep-model delegation (A3). The only modeled callee is the UNCHANGED
`Point.__mul__`, modeled deeply (`scaleCoords`, an A-reference), never
axiomatized as the function under change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The behavior that genuinely *changed* — adding a
left-multiplication that scales the point — is modeled **deeply** (the spelled-out
`scaleCoords` map, step A3, an A-reference), not hidden behind an axiom about the
patched operator.

## D. G-CONF skipped (all-A impl region)

The impl region of `scalePoint` is a SINGLE A-tagged operation (A3, the
delegation to the deep-modeled scaling callee). There are no R/I-tagged *computed*
ops in the `do` block to differential-test. Per the construction rules,
`meta.json conf_skip=true` and `conformance_check.py` is a skip stub. The
soundness G-CONF would provide is discharged by **G-AX**: `axiom_check.py`
validates `scaleCoords` == the real UNCHANGED `Point.__mul__` on boundary +
20000 fuzz point/factor pairs. (The `factor*point == point*factor` delegation
is the *patched* behaviour — G-AX runs at base_commit where `__rmul__` does not
yet exist — so it is validated by G-RESOLVE / the F2P harness, not G-AX.)

## E. verify(Solution) ⇒ resolved

`scalePoint` verifies only if its output equals the exact per-coordinate scaling
`scaleCoords coords factor` (A3) with the dimension preserved (A4). By R
(`Rat ↔` Python-native scalar, `List Rat ↔` coordinate tuple, constructor =
identity on content) the verified operator equals `self.__mul__(factor)` on the
tested inputs; by G-AX the deep model `scaleCoords` equals the real `Point.__mul__`
(A-reference) and `factor * point == point * factor` yields the scaled Point.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE: `5 * p4 == Point(5, 5)`, `5 * p4 == Point3D(5, 5, 5)`, run against the
patched repo). The single trust point is the A-reference soundness: the deep
model `scaleCoords` equals the real unchanged callee `Point.__mul__` (G-AX). The
new operator's *delegation to* that callee — left-multiply == right-multiply — is
exercised by the official harness at patch time (G-RESOLVE), where `__rmul__`
exists; G-AX runs at base_commit and so checks only the unchanged callee.
