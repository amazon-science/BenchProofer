# mapping.md — symbol binding & type bijection (sympy__sympy-17655)

## Modeled function
- **Lean** `implementation_scaleByFactor : Rat → List Rat → Option (List Rat)`
- **Python** the left scalar-by-point multiply added to `Point` —
  `sympy/geometry/point.py:281-284 @ f5e96594` (post-patch:
  `def __rmul__(self, factor): return self.__mul__(factor)`).

At `base_commit` `Point` defines only the right multiply (`__mul__`,
`point.py:250-279`); multiplying a scalar by a point on the LEFT had no handler,
so `scalar * point` raised (`GeometryError`, per the issue). The patch adds the
left-multiply, which forwards to `__mul__`, scaling each coordinate by the
factor: `coords = [simplify(x*factor) for x in self.args]; return Point(coords)`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| scalar `factor` (a sympified number) | `Rat` | exact rationals; `simplify(x*factor)` on numeric coords is exact rational arithmetic — no `Float`-order subtlety (DECISIONS.md) |
| point `self` / its `self.args` | `List Rat` | a point is its ordered coordinate tuple; `len(args) >= 2` always |
| coordinate `x` | `Rat` | one coordinate |
| result `Point(coords, evaluate=False)` | `some (coords : List Rat)` | a well-defined point |
| pre-patch raise / undefined left-multiply | `none` | the operation produced no point |

`evaluate=False` only suppresses re-evaluation of the constructed point; it does
not change the coordinate values. It is an I-tagged framing flag, not modeled.

## Callee provenance
- The per-coordinate scaling `simplify(x*factor)` is the operation the new
  left-multiply delegates to (via `__mul__`). It is modeled DEEPLY as `scaleSpec`
  (a front-recursive fold mapping each coordinate `x` to `x * factor`), an
  **A-reference** validated by G-AX against the real `Point.__mul__` body
  (`axiom_check.py`), NOT axiomatized.
- No UNCHANGED callee is consumed as an axiom; the axioms region is empty.

## Flag dependency
None. The new left-multiply unconditionally forwards to `__mul__`; there is no
flag controlling the per-coordinate map. G-AX/G-CONF fuzz the single behavior.

## G-CONF / G-AX fuzz seed
Pinned seed: **17655**. G-CONF runs >=10^5 fuzzed `(factor, coords)` inputs
(coords length 2..4, oversampling the issue's integer/float-ratio scalars);
G-AX runs 40k probes comparing `scaleSpec` to the real `Point.__mul__`.
