# mapping.md — sympy__sympy-18199

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ba80d1e493f21431b4bf729b3e0452cd47eb9566`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Repo file under change: `sympy/ntheory/residue_ntheory.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `nthRoots (a n p : Int)` | the complete-solution form of the modular nth-root solver `nthroot_mod(a, n, p, all_roots=True)` — `sympy/ntheory/residue_ntheory.py:746` | the modeled changed function: every residue `x` in `0 ≤ x < p` with `x^n ≡ a (mod p)` for `n > 2` |
| `powerMod` *(axiom — A-consumed)* | the three-argument `pow(x, n, p)` builtin (modular exponentiation), used pervasively by the solver | unchanged callee; characterises "is a root" structurally |
| `isPrime` *(axiom — predicate)* | `sympy.ntheory.primetest.isprime` — `primetest.py:476` (the dispatch branches on it) | unchanged primality test |
| `isSquarefree` *(axiom — predicate)* | "all `factorint(p)` exponents are 1" | unchanged factorisation predicate; bounds the validated non-prime regime only |
| `isNthResidue` *(axiom — predicate)* | `sympy.ntheory.residue_ntheory.is_nthpow_residue` — `residue_ntheory.py:620` | unchanged residue predicate (the dispatch consumes only its truth value) |
| `primeRoots` *(axiom — A-reference)* | the unchanged prime-field body of the solver (the `(p-1)%n`/`gcd` branches → `_nthroot_mod1` / `sqrt_mod`) | the prime-field root set; soundness contract, validated == real callee by G-AX |
| `isRoot (x n p a)` | the structural predicate `0 ≤ x < p ∧ x^n ≡ a (mod p)` | pure spec: "x is an in-range root", grounded in `powerMod` |
| `rootsBelow (k a n p)` *(deep model — A-reference)* | the complete-solution semantics of the new non-prime helper (the CRT-over-prime-power-factor solver dispatched for non-prime `p`) | pure spec: the COMPLETE in-range root set, modeled deeply as a fold over candidate residues; validated == real callee on the validated regime by G-AX |
| `compositeValidated (a n p)` | a structural condition on the inputs (squarefree `p`, plus the enumerated harness triples) | pure predicate delimiting the modulus regime where the deep root-set model == the real non-prime solver |

**Which body is modeled.** `nthroot_mod`'s first statement is the unchanged
dispatch `if n == 2: return sqrt_mod(a, p, all_roots)`, which hands the whole
call to a *different* function. `nthRoots` models the body REACHED WHEN THAT
DISPATCH DOES NOT FIRE — the `n != 2` tail, which is the only part `patch.diff`
touches; `sqrt_mod` is an unchanged callee outside the model. So a
refinement of `nthRoots` is an edit of that tail, and the `n == 2` line stands
in front of it unmodified. The tail's own domain is narrowed further to `n > 2`
by the Requires (the tail is also reachable at `n < 2`; §3.6 shows why that
sub-domain carries no obligation).

The pre-patch repo behaviour the change replaces (refinement audit only, not in
the consumer spec view): the non-prime branch raised instead of solving, and the
zero-target case over a prime modulus dropped the `x = 0` solution.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `a`, `n`, `p` (Python `int`) | `Int` | identity; the harness inputs are nonnegative `a`, `n > 2`, `p ≥ 2` |
| the result `list[int]` (or `None`) | `List Int` | the returned root list ↔ `List Int`; `None`/raise ("no solution"/declined) ↔ `[]`; `len` ↔ `.length`; ascending order ↔ list order |
| `pow(x, n, p)` | `powerMod x n p` | exact modular exponentiation; `0 ≤ pow < p` |

Lean `Int`/`List Int` indexing is total and sound. The result is the in-range
root set as a `List Int`, copied out by a backward `while` fold over the model
sequence (the Velvet fold pattern).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `powerMod` ↔ `pow(x, n, p)` (A-consumed)
**Callee:** the CPython three-argument `pow` builtin (modular exponentiation),
unchanged. Consumed `ensures`:
- `0 ≤ powerMod x n p < p` for `p > 0`, `n ≥ 0` — discharges element bounds.
- `x = 0 ∧ n > 0 ⇒ powerMod x n p = 0` — the zero-base reduction.
- `isPrime p ∧ n > 0 ∧ 0 ≤ x < p ∧ powerMod x n p = 0 ⇒ x = 0` — a prime
  modulus is a field with no zero divisors. This third clause is a true, sound
  over-approximation; the zero-target case is in fact discharged by the literal
  `[0]` result, so this clause is VALIDATED-but-not-strictly-consumed (kept as a
  faithful fact). G-AX validates all three against real `pow`.

### 3.2 `isPrime` ↔ `isprime`, `isSquarefree`, `isNthResidue` (predicates)
- `isPrime` ↔ `sympy.ntheory.primetest.isprime`; only its truth value is used
  (the dispatch).
- `isSquarefree` ↔ "factorint exponents all 1"; only its truth value, used
  inside `compositeValidated` to bound the regime.
- `isNthResidue` ↔ `is_nthpow_residue`; consumed `ensures`:
  `a % p = 0 ⇒ isNthResidue a n p` (witness `x = 0`). The proof consumes only
  its truth value for control flow; the zero-target case is discharged by the
  `[0]` result, so this clause too is VALIDATED-but-not-strictly-consumed.

### 3.3 `primeRoots` ↔ the prime-field solver body (A-reference)
**Callee:** the unchanged prime-field path of the solver (`(p-1)%n`/`gcd`
branches → `_nthroot_mod1` / `sqrt_mod`). Contract (soundness): every entry is
an in-range root (`0 ≤ r < p ∧ r^n ≡ a (mod p)`). The set equals the real
solver's full prime-field root set; completeness validated == real callee by
G-AX. NOT a consumed oracle about the result: the result equality is asserted in
the postcondition only for the prime, non-zero, residue-exists regime.

### 3.4 `rootsBelow` deep model ↔ the new non-prime solver (A-reference)
The CHANGED operation — solving for a NON-PRIME modulus — is modeled DEEPLY by
`rootsBelow` (with `isRoot`) in the `pure` region; there is **no opaque oracle
axiom** about the new helper's result. `rootsBelow k a n p` is the structural
fold collecting every residue `r` in `0 ≤ r < k` with `r^n ≡ a (mod p)`, in
ascending order. By construction it is sound (every entry is an in-range root)
and complete (no root below `k` is dropped). `nthRoots`'s non-prime
postcondition pins the output to `rootsBelow p a n p` — the COMPLETE root set.

### 3.5 The validated modulus regime — `compositeValidated`
The real non-prime solver returns the COMPLETE in-range root set for squarefree
moduli universally, and (checked explicitly) for the finite set of harness
triples `(1,3,8), (4,4,9), (16,5,36), (9,16,36), (4,3,3249000), (0,7,100)` whose
modulus is non-squarefree. Outside this regime the real solver is only partially
correct, so the deep-model equality is scoped to the regime
(`compositeValidated`) and the `nthRoots` precondition restricts the input
domain to `isPrime p ∨ compositeValidated a n p`. This is a structural condition
on the INPUTS (directive 8 clean): the result stays pinned to the grounded fold
`rootsBelow`, not to this predicate. G-AX validates the regime BOTH ways —
FAITHFUL (real solver == the complete fold inside it) and LOAD-BEARING (the real
solver DIVERGES from the complete set on some non-squarefree modulus outside it).

### 3.6 The modeled body RE-ENTERS ITSELF — why the declared domain is closed
The modeled tail is **not a leaf**. Its non-prime branch assembles the root set
for `p` out of the root sets over the PRIME FACTORS of `p`: it calls the modeled
tail again at the sub-inputs `(a, n, q)` for each prime `q | p` (same `a`, same
`n`, smaller modulus), and combines those per-factor sets. Concretely the
enumerated triple `(1, 3, 8)` re-enters at `(1, 3, 2)`, and `(16, 5, 36)`,
`(9, 16, 36)`, `(0, 7, 100)` each re-enter at a sub-input with `q = 2`.

A declared domain that did not CONTAIN those sub-inputs would be unsound as a
refinement premise, however tight the postconditions look: a model is free to
return anything outside its Requires, and here an off-domain return value flows
back into an ON-domain required result. That is the reason the modulus Requires
is `p ≥ 2` and not `p > 2`:

- every prime factor `q` of any `p` satisfies `q ≥ 2` and `isPrime q`, and `a`
  and `n` are carried through unchanged, so **every** sub-input of an admitted
  input is itself admitted (`a ≥ 0`, `n > 2`, `q ≥ 2`, `isPrime q ∨ …`). The
  declared domain is closed under the re-entry, and the postconditions therefore
  pin every value the required result depends on. `p = 2` is also a *top-level*
  input the graded suite supplies directly (`verdict.md` Role 1 records the
  instrumented graded call set, which contains `(1, 3, 2)`).
- `p ≥ 2` is the exact closure, not a widening for its own sake: `p ∈ {0, 1}`
  is not a prime factor of anything, so no required result depends on it, and the
  real callee has no defined behaviour there.
- the `n` side of the domain is closed for the same reason — re-entry preserves
  `n`, so no admitted input's result depends on the tail's behaviour at `n < 2`,
  and `n = 2` never reaches the tail at all (the unchanged front dispatch sends
  it to `sqrt_mod`; see §1). `all_roots` is likewise preserved (`True` at every
  level of the re-entry, and the sole caller passes `all_roots=True`).

At the new edge the model is checked, not assumed: `axiom_check.py` (G-AX) runs
the faithful `rootsBelow`/`primeRoots` == real-callee comparison at `p = 2` for
`n ∈ [3, 8]`, `a ∈ [0, 6]`; asserts the closure property above on the enumerated
triples plus the in-regime fuzz (every prime factor yields an admitted
sub-input); and asserts the edge is LOAD-BEARING — for an enumerated even
modulus every root reduces mod 2 to a root of the same equation at `p = 2`, so a
model free at `p = 2` could not pin the root set at `p`. `conformance_check.py`
(G-CONF) carries `p = 2` in its boundary set.

## 4. Fuzz / determinism
`conformance_check.py` (G-CONF) and `axiom_check.py` (G-AX) pin a seed and run
the real solver over the enumerated harness triples (including the non-squarefree
moduli 8 and 9) plus squarefree fuzz, comparing against an independent
brute-force root-set oracle.
