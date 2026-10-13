# mapping.md — sympy__sympy-15349

## Instance
- repo: sympy/sympy
- base_commit: 768da1c6f6ec907524b8ebbf6bf818c92b56101b
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change (one behavior, one site)
`Quaternion.to_rotation_matrix(v=None)` returns the rotation transformation matrix
a quaternion induces. The matrix entries are quadratic expressions in the four
components `(a, b, c, d)` weighted by `2*s`, where `s = norm()**-2`. One entry —
the `(1, 2)` slot of the 3×3 block (`m12`) — had the wrong sign on its cross term:

```python
def to_rotation_matrix(self, v=None):                 # sympy/algebras/quaternion.py:489
    q = self
    s = q.norm()**-2
    m00 = 1 - 2*s*(q.c**2 + q.d**2)
    m01 = 2*s*(q.b*q.c - q.d*q.a)
    m02 = 2*s*(q.b*q.d + q.c*q.a)
    m10 = 2*s*(q.b*q.c + q.d*q.a)
    m11 = 1 - 2*s*(q.b**2 + q.d**2)
    m12 = 2*s*(q.c*q.d + q.b*q.a)        # PRE-PATCH (buggy: wrong sign)
    # m12 = 2*s*(q.c*q.d - q.b*q.a)      # POST-PATCH (gold)
    m20 = 2*s*(q.b*q.d - q.c*q.a)
    m21 = 2*s*(q.c*q.d + q.b*q.a)
    m22 = 1 - 2*s*(q.b**2 + q.c**2)
    if not v:
        return Matrix([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]])
    else:
        (x, y, z) = v
        m03 = x - x*m00 - y*m01 - z*m02
        m13 = y - x*m10 - y*m11 - z*m12     # depends on m12
        m23 = z - x*m20 - y*m21 - z*m22
        m30 = m31 = m32 = 0
        m33 = 1
        return Matrix([[m00, m01, m02, m03], [m10, m11, m12, m13],
                       [m20, m21, m22, m23], [m30, m31, m32, m33]])
```

The standard quaternion-to-rotation-matrix formula (Wikipedia) has `m12`
(equivalently the `R[1][2]` entry) carrying a **minus** on the `b*a` cross term;
the code had a plus. The fix flips that sign. The 4×4 case's `m13` entry is a
linear function of `m12`, so it is the second observable affected by the same
one-site change.

## Modeled function — `to_rotation_matrix`
| field | value |
|---|---|
| file @ base_commit | `sympy/algebras/quaternion.py` |
| function | `Quaternion.to_rotation_matrix` (def at line 489; patched line is `m12` at line 531/529-in-hunk) |
| role | sole modeled function; the whole matrix-building behavior is modeled deeply |

The observable the F2P test (`test_quaternion_conversions`, plus
`test_quaternion_rotation_iss1593` in the test_patch) pins is every entry of
`q.to_rotation_matrix()` and `q.to_rotation_matrix((x,y,z))`. The Lean
`implementation_toRotationMatrix q v` models exactly this, with `v = none` for the
3×3 form and `v = some (x,y,z)` for the 4×4 form.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)

| Lean | Python | note |
|---|---|---|
| `Quat.a/b/c/d : ℚ` | `q.a/q.b/q.c/q.d` | quaternion components; rational entries in the tests |
| `scale q : ℚ` = `(a²+b²+c²+d²)⁻¹` | `q.norm()**-2` = `sqrt(a²+b²+c²+d²)**-2` | reciprocal sum-of-squares; equals `1/(a²+b²+c²+d²)` exactly for the rational catalogue (the `sqrt` and its `**-2` cancel) |
| `Mat.rows/cols : Nat` | matrix `.rows`/`.cols` | 3×3 (no point) or 4×4 (point) |
| `Mat.get i j : ℚ` | `M[i, j]` | entry accessor; out-of-range reads `0` — a stated modeling convention (Python raises IndexError there, not an F2P observable). The spec PINS the out-of-range reads to `0` (`∀ i j, dim ≤ i ∨ dim ≤ j → get i j = 0`) so the accessor carries no free degrees of freedom: without this clause a same-spec attack can verify while stashing garbage in unobservable slots (the P1 finding of the 2026-08 audit). |
| `v : Option (ℚ×ℚ×ℚ)`, `none`/`some (x,y,z)` | `v=None` / `v=(x,y,z)` | translation-point argument |
| `implementation_toRotationMatrix q v` | `q.to_rotation_matrix(v)` | the produced matrix |

### Float ↦ Rat justification (SPEC_GUIDE §2)
The fix is a **sign** change on exact field arithmetic. The F2P tests use exact
symbolic/rational quaternions and assert exact-`Matrix` equality, so the
observable is an exact rational value, not a floating-point approximation.
Modeling components as `ℚ` is therefore an exact bijection for the catalogue
G-CONF fuzzes (rational `a,b,c,d` with nonzero norm, rational points). The
symbolic `cos/sin` cases in the test reduce, after `trigsimp`, to the same
rational sign relation; the rational model captures the discriminating algebra.

## Callee provenance / flag deps
- `q.norm()**-2` is modeled deeply as `scale q = (a²+b²+c²+d²)⁻¹`. `norm()` is
  `sqrt(a²+b²+c²+d²)`; squaring its reciprocal removes the `sqrt`, giving exactly
  `1/(a²+b²+c²+d²)`. This identity is exact for every real (in particular every
  rational) argument with nonzero sum-of-squares, so `norm` is NOT axiomatized —
  the composite `norm()**-2` is modeled directly (an R op) and validated against
  the real callee by G-CONF.
- The matrix entries (including the patched `m12`) are direct rational
  expressions in the inputs, modeled deeply. No `opaque`/`axiom` callee contract
  is needed anywhere in the bundle.
- No flag dependency. The only argument-shape branch is `v=None` vs a 3-tuple,
  modeled by `Option (ℚ×ℚ×ℚ)`.

## Out-of-range pin (P1 repair, 2026-08)
The adversarial audit's G-PANEL-1 exhibited a same-spec impl that verifies while
diverging from the faithful impl on out-of-range `get` reads (the only degree of
freedom the original spec left open). Although those slots are not F2P
observables (Python `M[i, j]` raises IndexError out of range), the modeled `Mat`
declares "out-of-range indices read as `0`" as its convention, so the spec now
enforces that convention: each branch adds
`∀ i j, dim ≤ i ∨ dim ≤ j → result.get i j = 0` (dim = 3 or 4). With every
in-range entry, both dimensions, and all out-of-range reads equality-pinned, the
result `Mat` is extensionally determined by the inputs — no admitted impl can
differ observably (or unobservably) from the gold behavior.

## Precondition
`a²+b²+c²+d² ≠ 0` (nonzero norm) is the binder hypothesis of `correct_*`; the
real method is only ever called on quaternions with nonzero norm (otherwise
`norm()**-2` is undefined). It is not part of `problem_spec` (kept a clean
input→output relation).

## G-CONF fuzz seed
Pinned seed: **15349** (used in `conformance_check.py`).
