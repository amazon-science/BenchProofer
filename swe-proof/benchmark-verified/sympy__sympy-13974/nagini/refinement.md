# refinement.md — sympy__sympy-13974

The operation-by-operation correspondence between `model.py`'s implementation
(the `power_of_collection` impl region, the `simp_pow_factor` routing impl region,
the deep `pointwise_pow` fold, and the live `pow_expr` axiom) and `patch.diff` (the
gold patch). Two behavioural sites are modeled: §A the per-factor distribution
(`tensor_product_simp_Pow`) and §B the routing decision that reaches it from a
non-commutative factor of a product (`tensor_product_simp_Mul`). Each step is
tagged **R**
(type refinement), **A** (axiomatized callee — split into **A-consumed**, where
the proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new helper — `tensor_product_simp_Pow` (`tensorproduct.py:364-371` post-patch)

Gold hunk (the heart of the fix):
```
+def tensor_product_simp_Pow(e):
+    """Evaluates ``Pow`` expressions whose base is ``TensorProduct``"""
+    if not isinstance(e, Pow):
+        return e
+    if isinstance(e.base, TensorProduct):
+        return TensorProduct(*[ b**e.exp for b in e.base.args])
+    else:
+        return e
```
and the `Pow` branch of `tensor_product_simp` (`tensorproduct.py:410-412`):
```
- return tensor_product_simp(e.base) ** e.exp
+ if isinstance(e.base, TensorProduct):
+     return tensor_product_simp_Pow(e)
+ else:
+     return tensor_product_simp(e.base) ** e.exp
```

| # | model.py impl op (`power_of_collection`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `args: List[int]` | `e.base.args` (the tensor factors of the `TensorProduct` base) | R | a `TensorProduct` ↔ the ordered list of its argument expressions; each factor ↔ a distinct opaque `int` handle (mapping.md §2). |
| A2 | parameter `exp: int` | `e.exp` (the exponent of the `Pow`) | R | the exponent expression ↔ one opaque `int` handle, held fixed across factors (mapping.md §2). |
| A3 | `result[k] == pow_expr(args[k], exp)` for every factor k — i.e. the result is `pointwise_pow(ToSeq(args), exp)`, the spelled-out per-factor fold raising each factor to the exponent, computed by the backward loop over `args` | `[ b**e.exp for b in e.base.args]` — the list comprehension raising each base argument to the exponent | A-consumed + I | the per-factor application `b ** e.exp` is the unchanged power constructor, modeled by the `pow_expr` axiom (A-consumed: the proof uses its `Ensures` that `pow_expr(b,exp) != b`, valid under the axiom's `Requires(exp != 1)` which `power_of_collection` discharges from its own matching precondition — faithful because a `Pow` node never carries exponent `1`). The list-comprehension control/data flow — iterate the factors, apply `**` to each, collect in order — is identically the loop's fold; the fold structure is **I**. |
| A4 | `result` returned (a `List[int]`, the per-factor result handles, in order) | `TensorProduct(*[...])` rebuilds the tensor product from the per-factor powers | R | the `TensorProduct` constructor over the per-factor results ↔ the returned ordered `List[int]`; factor k of the rebuilt tensor product ↔ `Result()[k]` (mapping.md §2). The F2P tests compare the rebuilt `TensorProduct` for structural equality, which is exactly equality of the per-factor argument lists. |

The discriminating content of the change — the exponent is applied to **each
factor** (`a_i ** e`) rather than left **outside** the tensor product
(`(a_1 x … x a_n) ** e`) — lives in `result[k] == pow_expr(args[k], exp)`
(model) ⇔ `b**e.exp for b in e.base.args` (real). The pre-patch `Pow` branch
`tensor_product_simp(e.base) ** e.exp` returns the base tensor product unchanged
and wraps the exponent outside, so each factor stays `args[k]`;
`model_prepatch.py` reproduces that (`result[k] == args[k]`, the identity fold)
and **fails** the postcondition `ToSeq(Result()) == pointwise_pow(ToSeq(args), exp)`
— which is exactly the spec sensing the change (G-DIFF). The failure is forced by
the `pow_expr` non-triviality axiom (`pow_expr(b,exp) != b` under `exp != 1`,
which the shared precondition discharges): the unchanged factor `args[k]` can
never equal the genuine power `pow_expr(args[k], exp)`.

## B. The routing decision — `simp_pow_factor` (`tensor_product_simp_Mul`, the non-commutative-factor walk, post-patch)

The same per-factor distribution must also be *reached* when the
power-of-a-tensor-product appears as ONE non-commutative factor of a `Mul`, not
only as the whole expression. The patch threads the new helper through
`tensor_product_simp_Mul` at the points where a non-commutative factor is
examined:

```
   elif n_nc == 1:
       if isinstance(nc_part[0], Pow):
           return  Mul(*c_part) * tensor_product_simp_Pow(nc_part[0])
       return e
   ...
       current = nc_part[0]
       if not isinstance(current, TensorProduct):
           if isinstance(current, Pow):
               if isinstance(current.base, TensorProduct):
                   current = tensor_product_simp_Pow(current)
           else:
               raise TypeError('TensorProduct expected, got: %r' % current)
```

(`tensorproduct.py:321-326, 330-338` post-patch — the `n_nc == 1` Pow case and
the leading-factor Pow case; the trailing-factor and `e.has(Pow)` fallback at
`:349-359, 361-363` are the same decision applied per-position.) Pre-patch the
`n_nc == 1` branch was a bare `return e` and the leading-factor case raised
`TypeError` for a non-`TensorProduct`; the fix detects a `Pow` whose base is a
`TensorProduct` and routes it through `tensor_product_simp_Pow`, otherwise leaves
the factor unchanged (a bare `TensorProduct` already passes through). This is the
**routing decision**, modeled by `simp_pow_factor(is_pow_of_tp, factors, exp)`.

| # | model.py impl op (`simp_pow_factor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `is_pow_of_tp: bool` | the `isinstance(nc_part[0], Pow) and isinstance(.base, TensorProduct)` guard on the examined non-commutative factor | R | the type-test on the factor ↔ one boolean carrier: the factor is either a power whose base is a tensor product (`True`) or already a bare tensor product (`False`); the two shapes the routing distinguishes (mapping.md §2). |
| B2 | parameters `factors: List[int]`, `exp: int` | the tensor factors of the examined factor's base (`current.base.args` / `nc_part[0].base.args`) and the power's exponent (`.exp`) | R | the base `TensorProduct` ↔ ordered factor list; the exponent ↔ one handle (same R as A1/A2). |
| B3 | `if is_pow_of_tp: return power_of_collection(factors, exp)` — delegate to the modeled per-factor distribution | `current = tensor_product_simp_Pow(current)` / `Mul(*c_part) * tensor_product_simp_Pow(nc_part[0])` — delegate to the same helper | I + (grounded in §A) | the routing CALLS the very helper modeled in §A; the postcondition `ToSeq(Result()) == pointwise_pow(ToSeq(factors), exp)` for this branch is GROUNDED in the existing deep model (it is exactly `power_of_collection`'s pinned output), not a fresh axiom. The dispatch (test the factor, delegate) is the identical control flow — **I**. |
| B4 | else branch: the bare-tensor-product passthrough — factor k stays factor k, `ToSeq(Result()) == ToSeq(factors)` | the `isinstance(current, TensorProduct)` case (no rewrite; the factor's args are walked unchanged) | I | a factor that is already a tensor product is not re-powered; the routing leaves it as-is, modeled by the identity fold (factor count + order preserved, each factor unchanged). |

The discriminating content of the routing change is that a `Pow`-of-`TensorProduct`
factor is **not** left alone (pre-patch `return e` / `TypeError`) but is replaced
by its per-factor distribution: `simp_pow_factor(True, factors, exp)` returns
`pointwise_pow(ToSeq(factors), exp)`, which `model_prepatch.py` cannot satisfy
because its reverted `power_of_collection` (the identity fold) leaves each factor
unchanged — the `is_pow_of_tp` branch of `simp_pow_factor` delegates to that
broken helper and so the same postcondition fails through it. The passthrough
branch (`is_pow_of_tp` False) is the unchanged behaviour and verifies in both.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The two operations that genuinely *changed* are
both modeled **deeply**, never hidden behind an axiom about the function under
change:

* the **distribution** of the exponent across the tensor factors (§A) — the
  spelled-out per-factor fold `pointwise_pow` consumed in `power_of_collection`
  (step A3); there is no `tensor_product_simp_Pow` axiom.
* the **routing decision** (§B) — whether a non-commutative factor that is a
  `Pow`-of-`TensorProduct` is distributed or a bare `TensorProduct` is passed
  through — is modeled by `simp_pow_factor` as a concrete branch that DELEGATES to
  the deep `power_of_collection` (B3) and an identity fold (B4); its branch
  postconditions are grounded in the existing carrier (`pointwise_pow(ToSeq(factors),
  exp)` and `ToSeq(factors)`), not an answer-key constant, and there is no
  `tensor_product_simp_Mul` axiom.

The only consumed axiom, `pow_expr` (**A-consumed**, the unchanged symbolic power
constructor `b ** e.exp` the new helper invokes per factor), covers an
**unchanged** callee; its determinism + non-triviality are exactly what the
per-factor fold needs and what G-AX validates against the real `**`.

## D. verify(model) ⇒ resolved

`power_of_collection` verifies only if its output is the exact per-factor
distribution `pointwise_pow(ToSeq(args), exp)` (A3) — each factor raised to the
exponent, in order, factor count preserved. `simp_pow_factor` verifies only if it
delegates a `Pow`-of-`TensorProduct` factor to that distribution (B3) and passes a
bare `TensorProduct` factor through unchanged (B4), so the spec now pins BOTH the
distribution and the decision that reaches it from inside a product. By R
(TensorProduct ↔ factor list, exponent ↔ handle, rebuilt TensorProduct ↔ result
list, factor-type test ↔ the boolean carrier) the verified functions equal
`TensorProduct(*[ b**e.exp for b in e.base.args])` (the helper) and the
`tensor_product_simp_Mul` non-commutative-factor routing into it on the tested
inputs; by A-consumed the per-factor `b ** e.exp` is the real, unchanged power
constructor (G-AX: determinism + non-triviality). The four F2P witnesses (bare
power `TP(A,B)**x`, `Mul`-with-one-power `x*TP(A,B)**2`, `Mul`-with-multiple
`x*(TP(A,B)**2)*TP(C,D)`, and `Add`-with-a-power `TP(A,B)-TP(C,D)**x`) all reduce
to the modeled distribution reached through the modeled routing, and axiom_check.py
asserts all four directly against the real gold-patched dispatcher (G-AX
end-to-end). Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the one audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
