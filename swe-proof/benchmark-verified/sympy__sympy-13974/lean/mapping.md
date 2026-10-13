# mapping.md — sympy__sympy-13974

## Symbol binding (file:line @ base_commit 84c125972a)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_tensorPow` / `problem_spec_tensorPow` / `specTensorPow` | `tensor_product_simp_Pow(e)` (new function added by the fix) | `sympy/physics/quantum/tensorproduct.py:347-353` (post-patch) |
| `QExpr.pow base exp` → tensor-product base branch | `if isinstance(e.base, TensorProduct): return TensorProduct(*[b**e.exp for b in e.base.args])` | `sympy/physics/quantum/tensorproduct.py:351-352` |
| `QExpr.pow base exp` → non-tensor base branch / non-`Pow` input | `if not isinstance(e, Pow): return e` and the trailing `else: return e` | `sympy/physics/quantum/tensorproduct.py:349-353` |
| `args.map (fun b => QExpr.pow b exp)` | `[b**e.exp for b in e.base.args]` | `sympy/physics/quantum/tensorproduct.py:352` |
| `QExpr.tp args` assembly | `TensorProduct(*[...])` | `sympy/physics/quantum/tensorproduct.py:352` |

## Modeled function

`tensor_product_simp_Pow(e)` is the new helper introduced by the fix. It
evaluates a `Pow` whose base is a `TensorProduct` by distributing the exponent
across each factor:

```python
def tensor_product_simp_Pow(e):
    if not isinstance(e, Pow):
        return e
    if isinstance(e.base, TensorProduct):
        return TensorProduct(*[ b**e.exp for b in e.base.args])
    else:
        return e
```

This is the core of the issue ("powers of tensor product expressions are not
possible to evaluate"): `(a ⊗ b)**n` should become `(a**n) ⊗ (b**n)`. The
caller `tensor_product_simp` is changed only to dispatch the `Pow`-with-
TensorProduct-base case to this new helper (`return tensor_product_simp_Pow(e)`
instead of the old `return tensor_product_simp(e.base) ** e.exp`); the consumed
behavior on the F2P inputs is exactly this distribution, which is what we model.
`tensor_product_simp_Mul` is also extended (Pow factors inside a Mul), but every
new Mul branch ultimately calls `tensor_product_simp_Pow` to do the actual
distribution — the single new behavior under spec.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean |
|---|---|
| an opaque factor / non-commutative `Symbol` | `QExpr.atom n` |
| `TensorProduct(*args)` (symbolic, ≥2 non-commutative factors) | `QExpr.tp args` |
| `Pow(base, exp)` i.e. `base ** exp` | `QExpr.pow base exp` |
| the evaluated output expression | `QExpr` |

The exponent `e.exp` is carried as an opaque `QExpr` (the bijection does not
destructure it — `b**exp` reproduces the per-factor power for any exponent,
symbolic or integer). G-CONF fuzzes both a commutative symbol and small/zero/
negative integer exponents.

## Callee provenance / flag deps

None. `tensor_product_simp_Pow` calls only `isinstance` (the structural
list/tuple dispatch, refined to the `QExpr` constructor match), the
`TensorProduct` constructor (refined to `QExpr.tp` assembly), and `**` (refined
to `QExpr.pow` formation). No unchanged repo callee is consumed as an axiom; no
deep-model A-reference. axiom_check.py is therefore a skip stub. No flag
dependency.

### Note on `TensorProduct(*[...])` constructor reduction

The real `TensorProduct.__new__` pulls commutative scalar factors out front and
collapses to a scalar product when fewer than two non-commutative factors
remain. The fuzz restricts `QExpr.tp` to ≥2 distinct non-commutative atoms (and
factors that stay non-commutative), so the constructor returns a genuine
symbolic `TensorProduct` and the structural `QExpr.tp` assembly is faithful —
this is the regime the F2P tests and the issue exercise.

## G-CONF fuzz seed

Pinned seed: `13974`. conformance_check.py generates random expressions across
all branches — `pow` of a tensor product (the fix), `pow` of a non-tp base, a
bare tensor product, and a bare atom — and diffs the Lean-impl Python shadow
against the real patched `tensor_product_simp_Pow` over ≥10⁵ inputs.
