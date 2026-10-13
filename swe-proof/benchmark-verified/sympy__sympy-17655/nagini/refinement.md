# refinement.md — sympy__sympy-17655

The operation-by-operation correspondence between `model.py`'s implementation
(the `mul_right` / `mul_left` impl regions and the deep `scaled` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new left-multiplication — `Point.__rmul__` (`sympy/geometry/point.py`)

Gold hunk (inserted after `__mul__`, body lines 277-279):
```
+    def __rmul__(self, factor):
+        """Multiply a factor by point's coordinates."""
+        return self.__mul__(factor)
```

`__mul__` (unchanged, body lines 277-279) is:
```
        factor = sympify(factor)
        coords = [simplify(x*factor) for x in self.args]
        return Point(coords, evaluate=False)
```

| # | model.py op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `point: List[int]` (coordinate values), `factor: int` | `self.args` (a `Tuple` of SymPy coordinate expressions) and `factor` (a number) | R | a point ↔ its `List[int]` coordinate sequence; the tested coordinates (`1,1` / `1,1,1`) and factor (`5`) are concrete integers (mapping.md §2). `len(point)` ↔ the point's dimension `len(self)`. |
| A2 | `mul_right(point, factor)`: result coordinate `i` is `point[i] * factor`, computed by the loop and pinned by `ToSeq(Result()) == scaled(ToSeq(point), factor)` | `__mul__`: `coords = [simplify(x*factor) for x in self.args]; return Point(coords, evaluate=False)` | A-reference | the per-coordinate scaling is modelled **deeply** (`scaled` in the `pure` region + the verified `mul_right` loop). There is no consumed scaling axiom. `simplify(x*factor)` on the integer carrier is integer multiplication, and `Point(coords, evaluate=False)` is the point whose coordinates are exactly `coords`; G-AX (axiom_check.py) asserts `scaled(coords, factor)` == the coordinates of the real `Point(*coords) * factor`. (mapping.md §3.1) |
| A3 | `mul_left(factor, point)` impl `return mul_right(point, factor)` | `__rmul__`: `return self.__mul__(factor)` | I | identical delegation: left multiplication is defined as the right multiplication of the same point by the same factor. The model's `mul_left` calls the modeled `mul_right` (it is under spec, not an axiom). |
| A4 | `mul_left` postcondition `ToSeq(Result()) == scaled(ToSeq(point), factor)` and `len(Result()) == len(point)` | the observable behaviour the patch establishes: `factor * point` is the scaled point (same as `point * factor`) | A-reference + I | the commutativity property the F2P tests demand (`5 * p4 == Point(5,5)` / `5 * p4 == Point3D(5,5,5)`). It holds in the model because `mul_left` delegates to `mul_right` (I, A3), whose deep model is validated == the real `Point.__rmul__` / `Point.__mul__` by G-AX (A-reference; axiom_check.py confirms `factor * Point(*coords)` has coordinates `scaled(coords, factor)`). |

The discriminating content of the change — that left multiplication exists and
reproduces the per-coordinate scaling — lives in `mul_left`'s postcondition
`ToSeq(Result()) == scaled(ToSeq(point), factor)`. Pre-patch there is no
`__rmul__`, so `factor * point` does not scale (Python's fallback raises a
`TypeError`, or yields an unevaluated `Mul` for a SymPy factor — never a scaled
point). `model_prepatch.py` reproduces "no scaling on the left" (`mul_left`
returns the coordinates unchanged) and **fails** that postcondition, which is
exactly the spec sensing the change (G-DIFF). `mul_right` (the unchanged
`__mul__`) verifies in both twins.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding left scaling — is modeled **as a delegation to the modeled
right scaling** (I, A3), itself modeled **deeply** as the per-coordinate
multiplication `scaled` (A2/A4, A-reference), not hidden behind an axiom about
the function under change. There are **no consumed `@ContractOnly` axioms**:
the `axioms` region is empty. `sympify` / `simplify` / the `Point(...)`
constructor are observationally the identity on the integer coordinate carrier
for the tested inputs (mapping.md §2) and need no separate axiom.

## C. verify(model) ⇒ resolved

`mul_left` verifies only if its result equals the per-coordinate scaling
`scaled(ToSeq(point), factor)` (A4) — i.e. only if left multiplication produces
the same scaled point as right multiplication. By R (a point ↔ its `List[int]`
coordinates; `simplify`/`Point(...)` identities on the carrier) the verified
`mul_left` equals `self.__mul__(factor)` on the tested inputs; by G-AX the deep
model `scaled` equals the coordinates of the real `Point.__rmul__` /
`Point.__mul__` (A-reference). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited deep
model — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom/deep-model soundness (G-AX) and refinement fidelity
(this document, G-EQ).
