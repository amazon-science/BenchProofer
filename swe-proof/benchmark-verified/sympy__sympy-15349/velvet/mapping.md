# mapping.md — sympy__sympy-15349

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 768da1c6f6ec907524b8ebbf6bf818c92b56101b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of every modeled/delegated operation.

Repo file under change: `sympy/algebras/quaternion.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `toOrientationMatrix (a b c d : Rat) (v : Option (Rat × Rat × Rat))` | `Quaternion.to_rotation_matrix(self, v=None)` — `sympy/algebras/quaternion.py:489` (body lines 524–551) | the modeled changed method (quaternion → orientation matrix) |
| `rotMatrix` (pure) | the closed-form matrix the method assembles from `m00`…`m33` (`quaternion.py:526–551`) | pure spec: the full matrix as an explicit arithmetic function of the components |
| `sFactor a b c d = (a²+b²+c²+d²)⁻¹` (pure) | `s = q.norm()**-2` (`quaternion.py:525`), where `norm()` = `sqrt(trigsimp(a²+b²+c²+d²))` (`quaternion.py:293–298`) | pure spec: the common scaling factor, with the square root cancelled (see §3) |

The four components `a, b, c, d` of `Solution.lean` bind to the read-only
properties `q.a, q.b, q.c, q.d` (`quaternion.py:66–80`), where `q = self`
(`quaternion.py:524`). The optional argument `v` binds to the parameter
`v=None`; `none ↔ v is falsy` (the `if not v` branch, `quaternion.py:538`) and
`some (x,y,z) ↔ v = (x,y,z)` (the `else` branch, `quaternion.py:541–551`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a quaternion component `q.a … q.d` (a SymPy `Rational`/`Integer` in the tested inputs) | `Rat` | `Rational(p, q)` ↔ `(p : Rat) / q`; exact, total on the rationals. The F2P inputs are integer/rational quaternions, so this is exact (see §3 on why `Rat` is faithful and not lossy). |
| the optional point `v` | `Option (Rat × Rat × Rat)` | `None`/falsy ↔ `none`; `(x, y, z)` of rationals ↔ `some (x, y, z)`. |
| a SymPy `Matrix` of rational entries | `List (List Rat)` (row-major) | `M` ↔ `[[M[i,j] for j] for i]`; `M.rows`/`M.cols` ↔ outer/inner `length`. Entry-wise equality of matrices ↔ list equality (same shape, same entries). |
| `q.norm()**-2` | `sFactor a b c d` | see §3 — the irrational `sqrt` cancels, leaving the exact rational `(a²+b²+c²+d²)⁻¹`. |

`Rat` is the carrier (not `Real`/`Float`) because the demonstrated behaviour is
**exact** closed-form arithmetic over rational/integer quaternions: the F2P test
compares SymPy expressions for exact equality (e.g. `to_rotation_matrix() ==
Matrix([[-S(2)/3, …]])`). An exact ordered field is faithful; IEEE rounding
would not be.

## 3. Operation provenance (no axioms — all R/I, checked by G-CONF)

There are **no axiomatized callees** (`axioms` region empty; `meta.json axioms
= []`, `deep_model_references = []`). Every operation of the method is either a
type refinement (R) or an identical concrete arithmetic op (I), and is
mechanically refuted by G-CONF (`conformance_check.py`). The two points that
deserve provenance:

### 3.1 `s = q.norm()**-2` modeled as `(a²+b²+c²+d²)⁻¹` (R/I, not an axiom)
`norm()` returns `sqrt(trigsimp(a² + b² + c² + d²))` (`quaternion.py:298`).
The method then uses `s = norm()**-2 = (sqrt(Σ))**-2 = 1/Σ` where
`Σ = a²+b²+c²+d²`. The square root **cancels** under the square, so `s` is the
exact rational `(a²+b²+c²+d²)⁻¹` — no irrational ever appears in `s`, and the
result entries are rational functions of the components. This is why `Rat` is a
faithful carrier and why `sFactor` is modeled concretely (an exact identity),
**not** axiomatized: the proof does not assume anything about `norm`; it uses
the closed rational form, and G-CONF validates that form against the real
`q.norm()**-2` end-to-end (the oracle runs the real `to_rotation_matrix`).
The precondition `a²+b²+c²+d² ≠ 0` is the well-posedness condition for the
reciprocal (a zero quaternion has no orientation matrix; `norm()**-2` would
divide by zero in the repo too).

### 3.2 The matrix entries (I)
The nine 3×3 entries and the homogeneous 4×4 extension are transliterated
**verbatim** from `quaternion.py:526–551` into `rotMatrix`/the impl, component
for component, with `q.X**2 ↔ X^2`, `*` ↔ `*`, `+/-` ↔ `+/-`. The single entry
whose sign the gold patch corrects — the row-1/column-2 entry — is written
`2*s*(c*d - b*a)` in the frozen spec (the orientation-preserving convention).
The bottom row `[0,0,0,1]` and the fourth-column displacement
`m_i3 = vᵢ - Σⱼ vⱼ·mᵢⱼ` are likewise verbatim.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15349`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `sFactor`/`rotMatrix` (all R/I ops) to Python over exact SymPy
`Rational` arithmetic and diffs against the patched real `to_rotation_matrix`
(both the no-point 3×3 and the point 4×4 forms). There are no A-tagged callees,
so the shadow is pure R/I (`conf_skip = false`).
