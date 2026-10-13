# refinement.md — sympy__sympy-18199

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `nthRoots` `do` block, the deep `rootsBelow` model, and the axiomatized
callees) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses the
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The solver dispatch — `nthroot_mod(a, n, p, all_roots=True)`

Gold hunk (dispatch reorder + new non-prime helper):
```
+    if not isprime(p):
+        return _nthroot_mod_composite(a, n, p)
+    if a % p == 0:
+        return [0]
     if not is_nthpow_residue(a, n, p):
         return None
-    if not isprime(p):
-        raise NotImplementedError("Not implemented for composite p")
```

| # | Solution.lean impl op (`nthRoots`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `a n p : Int` | `a, n, p` (Python `int`) | R | `int ↔ Int` (mapping.md §2). |
| A2 | `if ¬ isPrime p then target := rootsBelow p.toNat a n p` | `if not isprime(p): return _nthroot_mod_composite(a, n, p)` | A-reference + I | the NEW non-prime operation is modeled **deeply**: `rootsBelow`/`isRoot` (pure region) ARE the complete in-range root set, grounded in `powerMod`. No opaque oracle axiom about the helper's result. The fold ops are **I** (transliterated by G-CONF); the equality of that deep model to the real solver over the validated regime is the **A-reference** G-AX validates. mapping.md §3.4–3.5. |
| A3 | `else if a % p = 0 then target := [0]` | `if a % p == 0: return [0]` | I | the zero-target singleton, transliterated directly. |
| A4 | `else if ¬ isNthResidue a n p then target := []` | `if not is_nthpow_residue(a, n, p): return None` | A-consumed + R | `None` ("no solution") ↔ `[]` (mapping.md §2); `isNthResidue` truth value gates the branch, and the postcondition pins the branch result exactly (`out = []`), so no same-spec impl may substitute a different value there. |
| A5 | `else target := primeRoots a n p` | the prime-field root set (`_nthroot_mod1` / `sqrt_mod` branches) | A-reference + I | the unchanged prime-field solver modeled as `primeRoots` (soundness contract), validated == real callee by G-AX. The result equality is asserted only for the prime, non-zero, residue regime. |
| A2b | the SAME method at the sub-inputs `(a, n, q)`, `q` prime, `q \| p` — admitted by the Requires, so pinned by the same postconditions | the re-entrant `nthroot_mod(a, n, q, True)` calls the new non-prime helper makes on each prime factor of `p` | R + I | the modeled body is **self-referential**: the non-prime branch's root set is assembled from the root sets over the prime factors. The refinement premise therefore needs the declared domain CLOSED under that re-entry, else an off-domain (hence unconstrained) return value feeds an on-domain required result. It is: `q` prime ⇒ `q ≥ 2 ∧ isPrime q`, and `a`, `n`, `all_roots` are carried through unchanged, so every sub-input satisfies `a ≥ 0 ∧ n > 2 ∧ p ≥ 2 ∧ (isPrime p ∨ compositeValidated a n p)`. `p ≥ 2` (not `p > 2`) is exactly that closure. mapping.md §3.6; checked executably by G-AX. |
| A6 | backward `while` fold copying `target` into `result` | the `return <list>` of the solver | R + I | the copy is observationally the identity on the `List Int` content; `loom_solve` + one `drop_step` lemma discharge it. |

Discriminating content of the change lives in two independently-fixed
behaviours:
- **Non-prime modulus** (A2): the pre-patch solver DECLINED a composite modulus;
  the post-patch solver returns the complete root set.
  `Solution_prepatch_1.lean` reproduces the decline (returns `[]`) and **fails**
  `out = rootsBelow p.toNat a n p` whenever a root exists (e.g. the enumerated
  non-squarefree triple `(1, 3, 8)`, admitted by `compositeValidated`, so the
  regime guard does not mask the discriminator) (G-DIFF).
- **Zero target, prime modulus** (A3): the pre-patch dispatch ran the residue
  check first, dropping the `x = 0` solution; the post-patch dispatch returns
  `[0]`. `Solution_prepatch.lean` reproduces the old order and **fails**
  `(isPrime p ∧ a % p = 0) ⇒ out.length = 1 ∧ out[0]! = 0` (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — solving
for a non-prime modulus — is modeled **deeply** (the spelled-out fold
`rootsBelow`, step A2, an A-reference + I), not hidden behind an oracle axiom
about the function under change. `primeRoots` (A5) and the predicates cover
**unchanged** callees; `compositeValidated` is a spec-domain restriction
grounded in the inputs (directive 8 clean). The consumed `powerMod` clauses
(range, zero-base) cover the unchanged `pow` builtin; `powerMod`'s prime-field
zero-divisor clause and `isNthResidue`'s `a%p=0` clause are VALIDATED-but-not-
strictly-consumed (the zero-target case is discharged by the literal `[0]`).

## C. verify(Solution) ⇒ resolved

`nthRoots` verifies only if its output equals the complete non-prime root set
`rootsBelow p a n p` (A2), the prime root set `primeRoots a n p` (A5), the
singleton `[0]` for the zero target (A3), and exactly `[]` when no residue
exists (A4 — pinned by its own postcondition, closing the branch), with every
returned entry an in-range root (soundness, grounded in `powerMod`). The
method is proven under TOTAL correctness (the copy loop carries a `decreasing`
measure), so a diverging impl does not verify.
The inference from "branch-wise pinned" to "equal to the gold dispatch" needs one
more premise, because the modeled body is not a leaf: it re-enters itself at the
prime factors of the modulus (A2b). A branch-wise-pinned model whose declared
domain OMITTED a re-entry sub-input would still be free to return anything there,
and that value would flow back into an on-domain required result — so the
pinning would not survive composition with the model's own recursion. The premise
holds here and is stated where it can be checked: the domain
`a ≥ 0 ∧ n > 2 ∧ p ≥ 2 ∧ (isPrime p ∨ compositeValidated a n p)` is CLOSED under
the re-entry (`q` prime ⇒ `q ≥ 2 ∧ isPrime q`; `a`, `n`, `all_roots` unchanged),
so every input any required output depends on — at the top level and at every
level of the re-entry — carries the postconditions above. `p ≥ 2` is that closure
exactly, `p ∈ {0, 1}` divides no modulus and is not modeled. G-AX asserts the
closure and the `p = 2` faithfulness executably (mapping.md §3.6), and the front
`n == 2` dispatch to the unchanged `sqrt_mod` stands ahead of the modeled body,
so `n = 2` is not a domain gap either (mapping.md §1, "Which body is modeled").

By R (`int ↔ Int`, `None`/raise ↔ `[]`) the verified solver equals the gold
dispatch on the tested inputs; by G-AX the deep model `rootsBelow` equals the
real non-prime solver over the validated regime (A-reference), `primeRoots`
equals the real prime-field solver (A-reference, down to `p = 2`), and `powerMod`
meets its clauses against real `pow` (A-consumed); by G-CONF the R/I
transliteration of the dispatch agrees with `patch.diff`'s behaviour on the
enumerated triples + the `p = 2` boundary + fuzz.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE).
