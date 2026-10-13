# refinement.md — sympy__sympy-15349

Operation correspondence between `implementation_toRotationMatrix` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

No axioms are declared or consumed: every matrix entry is a direct rational
arithmetic expression in the inputs. Every row is **R** or **I**. The R/I legs
are differential-tested by G-CONF over ≥1e5 fuzzed quaternions (3×3 and 4×4
forms); G-AX is a skip stub (no consumed callee axiom).

## `implementation_toRotationMatrix` ↔ `to_rotation_matrix`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `let s := scale q` (`(a²+b²+c²+d²)⁻¹`) | `s = q.norm()**-2` | R | `norm()**-2 = (sqrt(Σ component²))⁻² = (Σ component²)⁻¹` exactly for nonzero norm; `Real`/`sqrt` collapses to exact `Rat` reciprocal (mapping.md) |
| `m00 := 1 - 2*s*(c²+d²)` | `m00 = 1 - 2*s*(q.c**2 + q.d**2)` | I | identical arithmetic |
| `m01 := 2*s*(b*c - d*a)` | `m01 = 2*s*(q.b*q.c - q.d*q.a)` | I | identical |
| `m02 := 2*s*(b*d + c*a)` | `m02 = 2*s*(q.b*q.d + q.c*q.a)` | I | identical |
| `m10 := 2*s*(b*c + d*a)` | `m10 = 2*s*(q.b*q.c + q.d*q.a)` | I | identical |
| `m11 := 1 - 2*s*(b² + d²)` | `m11 = 1 - 2*s*(q.b**2 + q.d**2)` | I | identical |
| `m12 := 2*s*(c*d - b*a)` | `m12 = 2*s*(q.c*q.d - q.b*q.a)` | **R** | **the patched line.** `q.c*q.d - q.b*q.a` ↦ `c*d - b*a : ℚ`; the minus sign is the whole fix |
| `m20 := 2*s*(b*d - c*a)` | `m20 = 2*s*(q.b*q.d - q.c*q.a)` | I | identical |
| `m21 := 2*s*(c*d + b*a)` | `m21 = 2*s*(q.c*q.d + q.b*q.a)` | I | identical (note: `m21` keeps the plus — distinct slot from `m12`) |
| `m22 := 1 - 2*s*(b² + c²)` | `m22 = 1 - 2*s*(q.b**2 + q.c**2)` | I | identical |
| `match v with \| none => {rows:=3,cols:=3, get:=…3×3…}` | `if not v: return Matrix([[m00,m01,m02],[m10,m11,m12],[m20,m21,m22]])` | R | matrix object ↦ `Mat` (dims + entry accessor); row-major nested lists read by `getD` |
| `\| some (x,y,z) => m03/m13/m23 …; {rows:=4,cols:=4,…}` | `else: (x,y,z)=v; m03=x-x*m00-y*m01-z*m02; … m30=m31=m32=0; m33=1` | R | 4×4 augmented form; `m13` depends on the patched `m12`, so it is the second observable affected by the fix |

The result is the precise observable the F2P tests pin: every entry of
`q.to_rotation_matrix()` and `q.to_rotation_matrix((x,y,z))`.

The spec additionally pins the `Mat.get` accessor OUTSIDE the in-range window to
`0` (`∀ i j, dim ≤ i ∨ dim ≤ j → get i j = 0`), enforcing the structure's stated
"out-of-range reads as 0" convention. This is a modeling-closure clause, not a
Python behavior (real out-of-range access raises IndexError); it exists to
remove the accessor's only free degree of freedom, which the adversarial audit
(G-PANEL-1, 2026-08) exploited with a verifying same-spec impl that stashed
garbage in unobservable slots. The impl's nested-list `getD … 0` reads satisfy
it definitionally (`getD_getD_eq_zero` in the proof region).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: `m12` reads `2*s*(c*d + b*a)` (the pre-patch sign),
  while the frozen `problem_spec` requires `result.get 1 2 = 2*s*(c*d - b*a)`.
  Whenever `b*a ≠ 0` these differ, so the spec's `e12` clause is unsatisfiable by
  the prepatch impl and `correct_toRotationMatrix` is unclosable; the prepatch
  ships a `:= by sorry` proof that does not pass G-VERIFY (PLAN §4 G-DIFF: an
  unprovable/`sorry`-tripped prepatch is exactly the G-DIFF signal). The 4×4
  `m13` clause is a second discriminating slot via its dependence on `m12`.
  (FAIL_TO_PASS: `test_quaternion_conversions`; test_patch adds
  `test_quaternion_rotation_iss1593`.)

Single independently-fixed behavior → one `Solution_prepatch.lean`.
