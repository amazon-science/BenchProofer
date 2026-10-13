# mapping.md — sympy__sympy-11618

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 360290c4c401e386db60723ddb0109ed499c9f6e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. **This bundle has no axioms** (the changed operation is
modeled deeply, in pure arithmetic), so there is no `axiom_check.py` and G-AX
skips.

Repo file under change: `sympy/geometry/point.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `distanceSq (sameKind : Bool) (s q : List Int)` | `Point.distance(self, p)` — `sympy/geometry/point.py:237` (body lines 268-270 pre-patch) | the modeled changed method, modeled by its **squared** value (see §2 row "sqrt") |
| `alignTo (xs : List Int) (n : Nat)` | the per-vector zero-extension built inline in the patched branch (`p1 = [0]*max(...)`, `p1[i] = ...`) / `Point.origin` semantics (`point.py:219`) | pure spec: conform a coordinate vector to the common ambient dimension by zero-padding |
| `sumSqZip (a b : List Int)` | `sum([(a - b)**2 for a, b in zip(...)])` (the squared-distance accumulation, `point.py:269-270`) | pure spec: sum of squared per-coordinate differences |
| `commonLen (sameKind) (s q)` | the dimension the comparison runs in: `min` via the truncating `zip` when `type(p) is type(self)`, else `max(len(p), len(self))` (patched branch) | pure spec: the ambient dimension |
| `distSq (sameKind) (s q)` | the whole squared argument of `sqrt(...)` in patched `distance` | pure spec: the squared Euclidean distance |

No callee of `distance` is changed or axiomatized: the patch rewrites only
`distance`'s own arithmetic. `sqrt`, `sum`, `zip`, `len` are unchanged Python
builtins / sympy functions used purely; none is abstracted behind an axiom (the
spec models the squared value directly — see §2).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.args` / `p.args` — a `Tuple` of coordinate values | `List Int` (`s` for self, `q` for p) | `Point(*cs).args` ↔ the `List Int` `cs`; `len(pt)` ↔ `l.length`; coordinate `i` ↔ `l[i]` |
| each coordinate (an integer-valued sympy expr) | Lean `Int` | G-CONF restricts the fuzz to **integer** coordinates: `Integer(k)` ↔ `(k : Int)`. (Order-only/precision is not the behavior here — the change is which coordinates are paired, not their numeric type; modeling over `Int` is exact for the integer inputs the F2P test and the fix concern.) |
| `type(p) is type(self)` (the patch's discriminator) | `sameKind : Bool` | `True` ↔ both points the same concrete class (both `Point2D`, both `Point3D`, or both base `Point`); `False` ↔ different classes. G-CONF computes it from the constructed points' real `type(...)`. |
| `sqrt(Σ (aᵢ-bᵢ)²)` — `distance`'s return | modeled by its **square** `distSq` (`Int`) | `distance` returns the principal square root; the modeled observable is the squared distance `distSq`, related by `distance(self,p)**2 = distSq`. `sqrt` is injective on `[0,∞)`, so pinning the squared value pins the distance. G-CONF bridges by squaring the real return (`self.distance(p)**2`), which sympy evaluates exactly for integer coordinates. |
| `[0]*max(...)` zero-padding, `p1[i] = ...` reindex | `alignTo` (take-then-zero-pad) | the patched branch embeds the shorter vector at the origin of the larger ambient space; `alignTo xs n` is that embedding. |

`min`/`max` of coordinate counts: when the points are the same class their
coordinate counts already coincide (so `min = max`); the `min` form is exactly
the truncating `zip(self.args, p.args)` the same-class path runs, and the `max`
form is the patched different-class branch's `max(len(p), len(self))`.

## 3. Callee provenance

**None.** The squared-distance computation is modeled **deeply** (`distSq` via
`alignTo`/`sumSqZip`, the spelled-out arithmetic fold). There is no unchanged
imperative or pure callee whose contract the proof consumes, hence no `axiom`
and no `axiom_check.py`. (`sqrt`, `sum`, `zip`, `len`, `range` are unchanged
language/sympy primitives used directly, not abstracted — the spec reproduces
their effect concretely, so they need no axiomatization; SPEC_GUIDE §0.7's "never
axiomatize the operation the patch changes" is honored, and there is no dead
axiom.)

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11618`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`alignTo`/`commonLen`/`sumSqZip` (all R/I-tagged ops) to Python and diffs the
shadow's squared distance against the **real patched** `Point.distance(...)**2`
over ≥10⁵ fuzzed integer-coordinate point pairs (and boundary cases incl. the
F2P `Point3D(1,0,2).distance(Point2D(2,0))`).
