# refinement.md — sympy__sympy-15599

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`reduceModFactors` `do` block plus the deep `reduced`/`reduceFactor` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** / **A-reference**), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). There are **no A legs** in this bundle: the changed behavior is modeled
deeply over the read-only input list `factors`, and the upstream computation
that produces that list (the factor split) is unchanged (mapping.md §3). So
there are no axioms, no `axiom_check.py`, and G-AX is a skip.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed behavior — `Mod.eval.doit`, `Mul` branch (`sympy/core/mod.py`)

Gold hunk 3 appends, inside `elif isinstance(p, Mul):`, just before
`# XXX other possibilities?`:
```python
    if q.is_Integer and q is not S.One:
        _ = []
        for i in non_mod_l:
            if i.is_Integer and (i % q is not S.Zero):
                _.append(i%q)
            else:
                _.append(i)
        non_mod_l = _

    p = Mul(*(non_mod_l + mod_l))
```
i.e. replace each integer-literal factor of the product by its residue mod `q`
(unless that residue is zero, in which case the factor is kept), then rebuild
the product. This is what makes `Mod(3*i, 2)` reduce to `Mod(i, 2)`.

| # | Solution.lean impl op (`reduceModFactors`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `factors : List Factor` (read-only, **not** `mut`) | the local `non_mod_l` list as built by the unchanged factor-split loop, just before the patched block | R | factor-list ↔ `List Factor` via the row bijection `Integer ↔ .num`, non-integer factor ↔ `.sym` (mapping.md §2). `factors` is read-only: the impl never mutates it (directive 5 — no `mut` on `factors`; a fresh `result` is built). |
| A2 | `require q ≠ 0`, `require q ≠ 1` | the block guard `q.is_Integer and q is not S.One` (with `q == S.Zero` raised earlier at `mod.py:39`, so `q ≠ 0` in scope) | R | the modeled regime: integer `q` other than 1. `q` is integral throughout this branch (mapping.md §3.2), so the `Int` carrier with `q ≠ 0 ∧ q ≠ 1` captures the guard. |
| A3 | `let mut result : List Factor := []` | the patch's `_ = []` accumulator | I | initialise the rewritten factor list empty. |
| A4 | loop body `result := reduceFactor q (factors[i-1]!) :: result`, where `reduceFactor q (.num n) = if Int.fmod n q ≠ 0 then .num (Int.fmod n q) else .num n` and `reduceFactor q (.sym k) = .sym k` | the per-factor `if i.is_Integer and (i % q is not S.Zero): _.append(i%q) else: _.append(i)` | R + I | the per-factor decision is **I** (concrete control: integer-literal-with-non-zero-residue ⇒ rewrite, else keep); the residue value is **R**: Python `i % q` on integers is the floored remainder = `Int.fmod n q` (mapping.md §2; verified across both sign combinations). The backward fold builds the list in the same order the forward Python loop does. |
| A5 | `return result` (= `reduced q factors` by the loop invariant) | `non_mod_l = _` (the rewritten list), then `p = Mul(*(non_mod_l + mod_l))` | I + R | reading the rewritten list out ↔ `result`; `out = reduced q factors` pins the result to the exact per-factor rewrite. Rebuilding the product (`Mul(*…)`) and the empty-`mod_l` regime are accounted for by mapping.md §3.2/§3.3 — `mod_l` is empty in the modeled regime, so `non_mod_l + mod_l = non_mod_l`. |

Discriminating content of the change — an **integer coefficient** of a product
with a **non-zero residue** modulo `q` is collapsed to that residue (`3 → 1` for
`q = 2`), while a coefficient with a **zero residue** is **kept** (so
`Mod(8*i, 4)` stays divisible: `8 % 4 = 0`, factor unchanged, and downstream gcd
extraction yields `0`). This lives in `out = reduced q factors`. The pre-patch
skeleton (`Solution_prepatch.lean`) passes every factor through unchanged
(`result := f :: result`), so for any input containing an integer factor with a
non-zero residue it has `out ≠ reduced q factors` — `prove_correct` **fails**
(G-DIFF; the verifier leaves the unprovable goal
`factors[i-1]! = reduceFactor q factors[i-1]!`, false exactly at a
non-zero-residue integer factor such as `3` under `q = 2`).

## B. The factor-split loop — no axiom

The `for arg in p.args: both_l[isinstance(arg, cls)].append(arg)` loop
(`mod.py:117-119`) that builds `non_mod_l` is **not changed** by the patch and is
**not axiomatized**. Its sole role is producing the pre-reduction factor list
that is the read-only input `factors`. There is therefore no consumed axiom and
no A-reference deep model of a callee — `reduced` is a deep model of the changed
function's **own** new behavior, not of a callee (mapping.md §3.1).

## C. The other gold-patch hunks (audited inert at the modeled site)

`patch.diff` also contains:
- hunk 1: `from sympy.core.numbers import nan, Integer` + `from
  sympy.core.compatibility import integer_types` — added imports, no behavior.
- hunk 2: `return (p % q)` → `return p%q` — pure whitespace, no behavior.
- hunk 3 (first part): `if type(d) is int:` → `if isinstance(d, integer_types):`
  — broadens an integer type-test in the *by-ratio* path (`mod.py:64-70`),
  unrelated to the `Mul` branch. Observably inert for the modeled regime
  (integer/symbol products), where control reaches the `Mul` branch, not the
  by-ratio path. Tagged **I** (no behavioral effect at the modeled site).

These are not modeled (they carry no behavior the F2P test observes at the
modeled site); the residue-rewrite block (§A) is the behavioral change.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — rewriting each
integer factor of a product to its residue mod `q` — is modeled **deeply** by
`reduceFactor`/`reduced` and the verified `while` loop (steps A3-A5), not hidden
behind any axiom. No row is A. The only non-trivial R is the floored-mod value
bridge (`Int.fmod n q` ↔ Python `i % q`), and G-CONF compares the shadow's
per-factor rewrite against the **real patched** loop on the real `non_mod_l`.

## E. verify(Solution) ⇒ resolved

`reduceModFactors` verifies only if `out = reduced q factors` (A5): the exact
per-factor residue rewrite with `Int.fmod` (A4). By R (`Integer ↔ .num`,
non-integer factor ↔ `.sym`, `Int.fmod` ↔ Python `%`, mapping.md §2) the
verified `out` equals the post-patch `non_mod_l` on every pre-reduction factor
list the real factor-split loop produces in the modeled regime; by G-CONF the
R/I transliteration of `reduced`/`reduceFactor` agrees with the **real patched**
per-factor loop on the real `non_mod_l` over ≥10⁵ fuzzed inputs (incl. the F2P
shapes `Mod(3*i,2)`, `Mod(8*i,4)`, `Mod(8*i/j,4)`, `Mod(4*i,4)`), with the
site-decomposition assertion `Mod(p,q) == Mod(Mul(*reduced),q)` confirming the
factor list is the whole modeled story, 0 disagreements. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE: F2P `test_Mod`). The single
trust point is refinement fidelity (this doc, G-CONF + G-EQ); there are no
axioms (G-AX skip).
