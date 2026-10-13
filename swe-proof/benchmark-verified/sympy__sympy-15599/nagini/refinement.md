# refinement.md — sympy__sympy-15599

The operation-by-operation correspondence between `model.py`'s implementation
(the `reduce_coefficients` impl region, the deep `reduced_factor` model, and the
`residue` reference symbol) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where the model symbol is validated == the real callee by axiom_check.py / G-AX
and the proof depends only on the symbol being a deterministic `@Pure`, not on
its `Ensures`), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The product-reduction site — `Mod.eval.doit`, `Mul` branch

Gold hunk (`sympy/core/mod.py`, inserted at the end of the `elif isinstance(p,
Mul):` block):
```python
+ if q.is_Integer and q is not S.One:
+     _ = []
+     for i in non_mod_l:
+         if i.is_Integer and (i % q is not S.Zero):
+             _.append(i%q)
+         else:
+             _.append(i)
+     non_mod_l = _
+
+ p = Mul(*(non_mod_l + mod_l))
```

| # | model.py impl op (`reduce_coefficients`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `is_int: List[int]`, `value: List[int]` | the list `non_mod_l` of sympy factor objects | R | each factor ↔ `(is_int[k], value[k])`: tag = `is_Integer`, value = `int(factor)` for integer factors (mapping.md §1, §2). |
| A2 | parameter `m: int`, `Requires(m >= 2)` | the divisor `q` under the guard `q.is_Integer and q is not S.One` | R | `int(q) == m`; integer divisor `!= 1` ↔ `m >= 2` over the tested positive divisors (mapping.md §2 modeled-domain note). The guard `q.is_Integer and q is not S.One` ↔ the precondition `m >= 2`. |
| A3 | loop `for k in range(n)`, building `result` factor by factor | the `for i in non_mod_l:` loop building `_` | I | same control flow: one output factor produced per input factor, in order. |
| A4 | per factor: `if is_int[k]==1 and residue(value[k],m)!=0: v = residue(value[k],m) else: v = value[k]` | `if i.is_Integer and (i % q is not S.Zero): _.append(i%q) else: _.append(i)` | A-reference | the changed per-factor rewrite is modeled **deeply** by `reduced_factor` (no consumed `reduce_factor` axiom); the deep model is validated == the real rewrite by G-AX (A-reference, mapping.md §3.1). The single numeric primitive `i % q` ↔ the `residue` reference symbol (A-reference, §3.2): `is_Integer` ↔ `is_int==1`; `(i % q is not S.Zero)` ↔ `residue(value,m) != 0`; `i % q` ↔ `residue(value,m)`. The proof discharges `v == reduced_factor(...)` by **structural identity** — the impl's branch reuses the very same `residue(...)` calls as `reduced_factor`, so determinism of the `@Pure residue` suffices and its `Ensures` are *not* consumed; `residue`'s **value** is validated `== Integer.__mod__` by G-AX (axiom_check.py `check_residue_axiom`). |
| A5 | `result = result + [v]` | `_.append(...)` | I | append the rewritten factor; the loop invariant pins `result[b] == reduced_factor(is_int[b], value[b], m)` for `b < k`. |
| A6 | `return result` (the rewritten value list) | `non_mod_l = _` then `p = Mul(*(non_mod_l + mod_l))` | R | the modeled function returns the rewritten `non_mod_l` factor list; the gold then reassembles the product `Mul(*(non_mod_l + mod_l))` and `Mod.eval` continues to gcd-extraction / the re-`doit`. `Mul` reconstruction and the `mod_l` factors are unchanged and outside the spec (mapping.md §1): the discriminating content is entirely in which integer coefficients are shrunk, which is what `result` carries. |

The discriminating content of the change — an integer coefficient `c` with
`c % m != 0` becomes `c % m` rather than staying `c` — lives in
`reduced_factor(1, c, m) == residue(c, m)` (model) ⇔ the `_.append(i%q)` branch
(real). The pre-patch code has **no** such block, so `non_mod_l` passes through
unchanged; `model_prepatch.py` reproduces that (the impl returns `value[k]`
unchanged) and **fails** the postcondition
`Result()[k] == reduced_factor(is_int[k], value[k], m)` on any integer factor
with `c % m != 0 ∧ c % m != c` (e.g. `c=3, m=2`, the `Mod(3*i, 2)` case) — which
is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-factor integer-coefficient reduction — is modeled **deeply**
(the spelled-out `reduced_factor` used in the verified `reduce_coefficients`
loop, step A4, an **A-reference**), not hidden behind an axiom about the function
under change: there is no consumed `reduce_factor` axiom. The `residue` symbol
(`Integer.__mod__`, an **unchanged** numeric primitive the new block invokes) is
likewise **A-reference**, not A-consumed: the proof never relies on its `Ensures`
(weakening them to `True` still verifies — confirmed) but only on `residue`
being a deterministic `@Pure`, giving the structural identity
`impl v == reduced_factor(...)`. Its **value** is validated `== Integer.__mod__`
by G-AX (axiom_check.py `check_residue_axiom`), which is exactly the A-reference
discipline. There is no consumed axiom in this bundle.

## C. verify(model) ⇒ resolved

`reduce_coefficients` verifies only if its output is, factor by factor, the
exact per-factor reduction: an integer factor not divisible by `m` shrunk to its
residue, everything else unchanged (A4, the postcondition `Forall k …`). By R
(factor list ↔ parallel `List[int]`, integer divisor `!= 1` ↔ `m >= 2`, `Mul`
reconstruction is the identity on the carried factor multiset) the verified
rewrite equals the gold's `non_mod_l = [… i%q …]; p = Mul(*(non_mod_l + mod_l))`
on the tested products. By G-AX the deep model `reduced_factor` equals the real
factor rewrite (A-reference) and the `residue` symbol's value equals the real
`Integer.__mod__` (A-reference — its `Ensures` are *not* proof-consumed, only its
determinism is). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited callee — and the
gold patch resolves (G-RESOLVE: `test_Mod`'s `Mod(3*i,2)==Mod(i,2)`,
`Mod(8*i,4)==0`, `Mod(8*i/j,4)==4*Mod(2*i/j,1)` all pass post-gold, and the P2P
`Mod(4*i,4)==0`, `(3*i*x)%(2*i*y)==i*Mod(3*x,2*y)`,
`Mod(Mod(x+2,4)*4,4)==0` are preserved). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
