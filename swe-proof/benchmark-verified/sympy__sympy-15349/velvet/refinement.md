# refinement.md — sympy__sympy-15349

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `toOrientationMatrix` `do` block and the `rotMatrix`/`sFactor` pure models)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A** (axiomatized callee — none here), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are no A legs (no axioms). Claim: any impl verifying against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change — `Quaternion.to_rotation_matrix` (`sympy/algebras/quaternion.py:489`)

Gold hunk:
```
- m12 = 2*s*(q.c*q.d + q.b*q.a)
+ m12 = 2*s*(q.c*q.d - q.b*q.a)
```
A single sign correction in the row-1/column-2 entry of the orientation matrix.

| # | Solution.lean impl op (`toOrientationMatrix` / `rotMatrix`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `a b c d : Rat` | `q.a q.b q.c q.d` (`quaternion.py:524`, `q=self`) | R | SymPy `Rational` ↔ `Rat` (mapping.md §2), exact on the tested rational quaternions. |
| A2 | param `v : Option (Rat × Rat × Rat)` | `v=None` argument; `if not v` / `else (x,y,z)=v` (`quaternion.py:538,542`) | R | falsy ↔ `none`; `(x,y,z)` ↔ `some (x,y,z)` (mapping.md §2). |
| A3 | `s := sFactor a b c d = (a²+b²+c²+d²)⁻¹` | `s = q.norm()**-2` (`quaternion.py:525`) | R + I | `norm() = sqrt(Σ)`, so `norm()**-2 = 1/Σ`; the sqrt cancels (mapping.md §3.1). Exact rational identity; well-posed under the precondition `Σ ≠ 0`. |
| A4 | `m00 … m22` nine entries (closed-form arithmetic in `a,b,c,d,s`) | `m00 … m22` (`quaternion.py:526–536`) | I | transliterated component-for-component; `X**2 ↔ X^2`, `*`↔`*`, `±`↔`±`. |
| A4′ | `m12 := 2 * s * (c * d - b * a)` | `m12 = 2*s*(q.c*q.d - q.b*q.a)` (the **patched** line) | I | the discriminating entry: minus sign (orientation-preserving). The pre-patch had `+`; `Solution_prepatch.lean` reproduces `c*d + b*a` and **fails** `out = rotMatrix …` at exactly this entry (G-DIFF). |
| A5 | `match v` → `none`: `[[m00,m01,m02],[m10,m11,m12],[m20,m21,m22]]` | `if not v: return Matrix([[m00,m01,m02],[m10,m11,m12],[m20,m21,m22]])` (`quaternion.py:538–539`) | R + I | matrix ↔ row-major `List (List Rat)` (mapping.md §2). |
| A6 | `match v` → `some (x,y,z)`: 4×4 with `m03/m13/m23 = vᵢ - x·mᵢ₀ - y·mᵢ₁ - z·mᵢ₂` and bottom row `[0,0,0,1]` | the `else` branch (`quaternion.py:542–551`): `m03=x - x*m00 - y*m01 - z*m02`, …, `m30=m31=m32=0`, `m33=1` | R + I | verbatim; `m30=m31=m32=0`, `m33=1` ↔ literal `[0,0,0,1]`. |

## B. Discriminating content

The change is entirely localized to entry `m12`: `c*d + b*a` (pre-patch) →
`c*d - b*a` (gold). The frozen spec pins `m12 = 2*s*(c*d - b*a)` (clause A4′).
A verifying impl must produce that entry; the pre-patch positional arithmetic
(`c*d + b*a`, the same sign as the symmetric `m21`) cannot satisfy the spec —
`Solution_prepatch.lean` is rejected precisely at the `m12` slot (confirmed: the
unsolved goal differs only in the `(c*d + b*a)` vs `(c*d - b*a)` entry of row 1,
in both the `none` and `some` matrices). This is exactly the sign error the
issue's `q = Quaternion(cos(x/2), sin(x/2), 0, 0)` example exposes (one `sin(x)`
should be negative); with that quaternion `b*a = sin(x/2)·cos(x/2)` is the only
nonzero cross term and flips the sign of the `m12` entry.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The changed operation — a closed-form arithmetic entry of
a matrix — is modeled **deeply and concretely** as explicit rational arithmetic
(`rotMatrix`/`sFactor`); there is no axiom and no A-reference. The one operation
that delegates to an unchanged callee (`q.norm()**-2`) is an exact rational
identity (`(Σ)⁻¹`, the sqrt cancels under the square), modeled concretely and
validated end-to-end by G-CONF against the real `to_rotation_matrix`, NOT
consumed as an axiom (mapping.md §3.1). `meta.json axioms = []`,
`deep_model_references = []`, `conf_skip = false`.

## D. verify(Solution) ⇒ resolved

`toOrientationMatrix` verifies only if its output equals `rotMatrix` entry for
entry, including `m12 = 2*s*(c*d - b*a)` (A4′). By R (`Rational ↔ Rat`,
`Matrix ↔ List (List Rat)`, `None/(x,y,z) ↔ Option`) and the exact identity
`norm()**-2 = (a²+b²+c²+d²)⁻¹` (A3), the verified matrix equals the patched
`to_rotation_matrix(self, v)` on the tested rational quaternions; by G-CONF the
R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed inputs
(both the 3×3 and 4×4 forms). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The sole trust point is refinement fidelity (this doc +
G-CONF); there are no axioms to trust (G-AX skipped).
