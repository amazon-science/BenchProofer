# mapping.md — sympy__sympy-15875

## Symbol binding (base_commit 207b1a2d2e0a78a4cb31752afb46127db0bb6abd)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_zeroStatus` / `problem_spec_zeroStatus` | `Add._eval_is_zero(self)` | `sympy/core/add.py:531-568` |
| (impl) per-summand classification loop | `for a in self.args: … is_real / is_imaginary / (I*a).is_real …` | `add.py:538-552` |
| (impl) `z == terms.length → some true` | `if z == len(self.args): return True` | `add.py:553-554` |
| (impl) `nz == 0 ∨ nz == terms.length → none` | `if len(nz) == 0 or len(nz) == len(self.args): return None` | `add.py:555-556` |
| (impl) `b`-branch on `realSumZero` | `b = self.func(*nz); if b.is_zero: …; if b.is_zero is False: return False` | `add.py:557-568` |
| input `realSumZero : Option Bool` | `self.func(*nz).is_zero` — the recursive zero-test of the sub-sum of the real, definitely-nonzero terms | `add.py:557-558` |

`self.args` is the post-construction (auto-evaluated, flattened) argument tuple
of the sum. The classification of each argument `a` uses only the unchanged
assumption queries `a.is_real`, `a.is_zero`, `a.is_imaginary`,
`(ImaginaryUnit*a).is_real`. We model the commutative path
(`self.is_commutative is not False`, `add.py:533-537`); the non-commutative
early `return None` is outside the modeled behavior (the F2P expression and all
numeric/real/imaginary sums are commutative).

## Type bijection (G-CONF uses this)

A summand `a ∈ self.args` is classified into one `Summand` constructor by the
exact ladder the function walks:

| Python predicate on `a` | `Summand` | meaning |
|---|---|---|
| `a.is_real and a.is_zero` | `realZero` | real term known to be zero |
| `a.is_real and a.is_zero is False` | `realNonzero` | real term known nonzero |
| `a.is_real and a.is_zero is None` | `realUnknown` | real term, zero-ness undetermined → forces undetermined |
| `not a.is_real and a.is_imaginary` | `imaginary` | purely imaginary (nonzero) term |
| `not a.is_real and not a.is_imaginary and (I*a).is_real` | `imagOrZero` | `I*a` real (imaginary-or-zero) |
| none of the above | `indeterminate` | unclassifiable → forces undetermined |

| Python value | Lean | notes |
|---|---|---|
| `self.args` (tuple) | `terms : List Summand` | one constructor per argument, in arg order |
| `self.func(*nz).is_zero` (`True`/`False`/`None`) | `realSumZero : Option Bool` (`some true`/`some false`/`none`) | recursive zero-test of the real-nonzero sub-sum |
| return `True` / `False` / `None` | `some true` / `some false` / `none` | the three-valued zero verdict |
| `len(nz)` | `terms.countP isRealNonzero` | count of `realNonzero` summands |
| `z` (count of real-zero args) | `terms.countP isRealZero` | |
| `len(self.args)` | `terms.length` | |
| `im` flag | `terms.any isImag` | a purely-imaginary summand present |
| `im_or_z` flag | `terms.any isImagOrZero` | an imaginary-or-zero summand present |

Order independence: `realUnknown` / `indeterminate` cause an immediate
`return None` in the loop, so their position does not change the verdict —
presence of any such summand ⟹ `none`, expressible with `List.any`.

## Callee provenance / flag deps

No unchanged outside callee is consumed as an axiom. The three-valued recursive
zero-test of the real-nonzero sub-sum is supplied as the input `realSumZero`
(grounding the verdict directly in the inputs, exactly as a three-valued
classifier input). The per-summand assumption queries (`is_real`, `is_zero`,
`is_imaginary`, `(I*a).is_real`) are folded into the `Summand` classification
(the type bijection above) and are exercised end-to-end by G-CONF on the real
expressions. → no `opaque`/`axiom` decls; `axiom_check.py` is a skip stub.

## G-CONF fuzz seed (pinned)

`seed = 15875` (used in `conformance_check.py`). Term palette: integers
(`0`, `±k`), real symbols (`real=True`, and `real=True, nonzero=True`),
imaginary terms (`k*I`, `(1+I)**2`, imaginary symbols), `I*real-symbol`
(imaginary-or-zero), and plain symbols (indeterminate); `0..6` terms per sum,
`≥10⁵` cases. Only genuine `Add` instances are scored (single-term / collapsed
sums are skipped).
