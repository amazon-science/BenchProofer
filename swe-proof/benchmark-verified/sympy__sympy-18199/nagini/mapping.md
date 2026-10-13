# mapping.md — sympy__sympy-18199

Binds every `model.py` symbol to its repository counterpart at
`base_commit = ba80d1e493f21431b4bf729b3e0452cd47eb9566`, states the type
abstraction, and gives the provenance of each modelled callee and the exact
behaviour each deep reference is validated against.

Repo file under change: `sympy/ntheory/residue_ntheory.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `nth_roots(a, n, p)` | `nthroot_mod(a, n, p, all_roots=True)` — `residue_ntheory.py:746` | the modeled changed function (complete-solution form of `x**n = a (mod p)`, `n > 2`) |
| `is_prime(p)` *(A-consumed: control)* | `isprime(p)` — `sympy/ntheory/primetest.py:476`, called at `residue_ntheory.py:776` (gold) | the unchanged primality test that dispatches prime vs non-prime; the proof consumes its truth value (no `Ensures`) |
| `is_squarefree(p)` *(A-consumed: control)* | "p has no repeated prime factor" — sympy `factorint(p)` exponents all 1 | the unchanged factorisation predicate; used ONLY inside `composite_validated` to delimit the validated non-prime modulus regime; no `Ensures` |
| `is_nth_residue(a, n, p)` *(A-consumed: control; `Ensures` validated-not-consumed)* | `is_nthpow_residue(a, n, p)` — `residue_ntheory.py:620`, called at `residue_ntheory.py:774` (gold) | the unchanged residue predicate; the proof consumes its truth value (control flow), NOT its `a%p==0 ⇒ True` `Ensures` (validated-but-dead — §3.3) |
| `power_mod(x, n, p)` *(A-consumed)* | the three-argument `pow(x, n, p)` used pervasively inside `nthroot_mod`/`_nthroot_mod_composite` (e.g. `pow(root, n)`, `pow(k, n)`, `pow(p, e)`) | the unchanged modular exponentiation; used to state "is a root" structurally. Consumed clauses: range bound + zero-base. Prime-field zero-divisor clause is validated-but-dead (§3.1) |
| `prime_roots(a, n, p)` *(A-reference)* | the prime-field body of `nthroot_mod` for prime `p`, non-zero target: the `(p-1)%n`/gcd branches + `_nthroot_mod1` (`residue_ntheory.py:700`) / `sqrt_mod` (`residue_ntheory.py:216`) | the unchanged prime-field root set; validated `== nthroot_mod(...,all_roots=True)` by axiom_check.py (G-AX), NOT a consumed proof axiom |
| `composite_roots(a, n, p)` *(deep model)* | `_nthroot_mod_composite(a, n, m)` — NEW in the gold patch body (`residue_ntheory.py`, CRT over prime-power factors) | the non-prime-modulus root set, now a CONTRACTED `@Pure` function whose body returns `roots_below(p, a, n, p)` — the COMPLETE in-range root set computed by structural recursion over the candidate residues. Its value is pinned IN the spec (not an opaque oracle); the real callee equals it over the regime its `Requires(composite_validated)` encodes, validated by axiom_check.py / G-AX (§3.4) |
| `roots_below(k, a, n, p)` | the complete-solution semantics of `nthroot_mod(a, n, m, all_roots=True)` for composite `m` (the residues in `[0, m)` solving the congruence) | pure deep model: the ascending sequence of EVERY residue `r` in `[0, k)` with `r**n == a (mod p)`, defined by recursion over the candidates and grounded in `power_mod` (== real `pow`). `composite_roots` returns `roots_below(p, …)`. This is the structural definition the composite root set is pinned to (§3.4) |
| `composite_validated(a, n, p)` | the validated modulus regime: `is_squarefree(p)` ∨ one of the enumerated non-squarefree test-suite triples | pure spec: a structural condition on the INPUTS bounding where the deep composite root set equals the real callee (the validated regime — §3.4); NOT an answer key for the result |
| `is_root(x, n, p, a)` | the defining membership test `0 <= x < p and pow(x, n, p) == a % p` | pure spec: a residue is a solution iff its modular n-th power equals the reduced right-hand side |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the guard
`if not isprime(p): raise NotImplementedError("Not implemented for composite p")`
(`residue_ntheory.py:776-777`) and the missing zero-root case (the pre-patch
order ran `is_nthpow_residue` first and never special-cased `a % p == 0`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the modulus `p` and exponent `n` and target `a`, Python `int`/`mpz` | `int` | identity on the integer values; `as_int(...)` is the identity for the integer inputs the tests pass |
| the complete-solution list `nthroot_mod(a,n,p,all_roots=True)` (a sorted Python/`mpz` list, or `None`/`[]` when there is no solution) | `List[int]` (the empty list when there is no solution) | element-wise `int` equality; the real callee's `None` for "no solution" ↔ the empty list (axiom_check normalises `None -> []`) |
| the per-prime-power / prime-field root set the solvers return | `PSeq[int]` then copied to `List[int]` | `ToSeq(Result()) == prime_roots/composite_roots(...)`; the copy loop preserves the sequence; the harness asserts compare ROOT SETS, so element order is an unconstrained R-detail |

The result list is the only full-permission object; there are no read-only
list/object inputs (the parameters are scalars), so directive-5 fractional
permission applies vacuously (no list parameter to share at `1/2`).

## 3. Callee / deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `power_mod` ↔ `pow(x, n, p)` (A-consumed)
**Callee:** Python's built-in three-argument `pow` (and the equivalent `mpz`
modular power) used throughout `nthroot_mod`/`_nthroot_mod_composite`. The
`power_mod` axiom carries three `Ensures` clauses. **Actually consumed by the
proof:** `0 <= pow < p` (the range bound discharges the result-list element
bounds and the loop invariants) and `x==0 ∧ n>0 ⇒ pow==0` (the zero-base
reduction). **Validated but NOT consumed (over-strong-yet-sound):** the
prime-field zero-divisor clause `isprime(p) ∧ n>0 ∧ 0<=x<p ∧ pow==0 ⇒ x==0`.
The zero-target postcondition is discharged by the impl returning the literal
singleton `[0]` (`len([0])==1`, `[0][0]==0`), so the proof never needs this
clause — a probe with it removed still verifies. It is a true property of `pow`
modulo a prime (a prime field has no zero divisors), G-AX-validated, and kept as
a faithful (though non-load-bearing) statement of the callee; it neither
strengthens nor weakens the function-level spec. All three clauses are asserted
by axiom_check.py on boundary + 20000 fuzz.

### 3.2 `is_prime` ↔ `isprime` (A-consumed)
**Callee:** `sympy.ntheory.primetest.isprime`, the unchanged primality test the
gold's new dispatch (`if not isprime(p)`) branches on. The model name `is_prime`
IS that predicate; no contract beyond "it is `isprime`" is consumed (the
dispatch only needs its truth value). axiom_check.py records it as the binding
witness.

### 3.3 `is_nth_residue` ↔ `is_nthpow_residue` (A-consumed)
**Callee:** `is_nthpow_residue(a, n, p)` (`residue_ntheory.py:620`), unchanged.
The model's predicate over-approximates the real one. Its single `Ensures`
clause `a % p == 0 ⇒ Result()` is **validated but NOT consumed by the proof**:
the prime zero-target case is discharged earlier (the impl branches on
`if a % p == 0: return [0]` *before* the residue check), and on the non-zero
prime path the `prime_roots` postcondition does not depend on this clause. A
probe with the clause removed still verifies. The clause is nevertheless a true,
sound over-approximation (`is_nthpow_residue` does return `True` when
`a % p == 0`, and a root `0` really exists), kept so the axiom faithfully states
the callee's relevant behaviour; axiom_check.py asserts both the real predicate
returns `True` and a real root `0` exists whenever `a % p == 0`. The proof's
only genuine use of `is_nth_residue` is its truth value gating the residue
branch (control flow), not the `Ensures`.

### 3.4 `composite_roots` (deep model `roots_below`) ↔ `_nthroot_mod_composite` via `nthroot_mod`
**Callee:** the patched `nthroot_mod(a,n,p,all_roots=True)` for composite `p`,
which dispatches to the NEW `_nthroot_mod_composite` (CRT over prime-power
factors). The model's `composite_roots` is now a CONTRACTED `@Pure` function
modelled DEEPLY, not an opaque A-reference: its body is `return roots_below(p, a,
n, p)`, where `roots_below(k, a, n, p)` is the structural recursive fold that
collects EVERY residue `r` in `[0, k)` with `r**n == a (mod p)` in ascending
order. So `composite_roots(a,n,p)` *is*, by definition, the COMPLETE in-range
root set `{r in [0,p): r**n == a (mod p)}` — grounded in `power_mod` (the real
`pow`), with no oracle. The function-level postcondition `ToSeq(Result()) ==
composite_roots(a,n,p)` therefore equates the output to that complete set, and
both soundness AND completeness are now pinned *in the spec* (the verifier knows
`composite_roots`'s value), not merely checked out of band.

**What G-AX validates.** Since the model now pins the composite output to the
COMPLETE root set, the only remaining trust point is that the REAL callee returns
that same complete set over the validated regime. G-AX validates
`nthroot_mod(...,all_roots=True)` == the complete root set (== `roots_below`,
computed by an independent brute-force oracle `brute_root_set`) as a SET OF ROOTS
(each side a subset of the other) over the `composite_validated` regime.

**The validated regime is encoded in `Requires`, not prose (directive 7/8).**
`composite_roots` carries `Requires(composite_validated(a, n, p))` and the
function-level composite postcondition is guarded by the same predicate
(`Implies(not is_prime(p) and composite_validated(a, n, p), ...)`); `nth_roots`
carries `Requires(is_prime(p) or composite_validated(a, n, p))` so the composite
branch can discharge it. This is the soundness boundary for the gold's partial
correctness: the deep model `composite_roots == roots_below(p, …)` is the
*complete and correct* congruence root set, but the real callee equals that
complete set only over a restricted domain — it returns non-roots and/or drops
roots for some non-squarefree moduli (brute-confirmed below). Asserting
`ToSeq(Result()) == composite_roots(a,n,p)` over *all* non-prime `p` would
therefore claim the model resolves the gold on inputs where the real callee
diverges from the complete set — an over-claim (directive 7). `composite_validated(a,
n, p)` is exactly the regime over which axiom_check.py validates that the real
callee equals the complete set, so the composite postcondition holds precisely
where the gold actually produces it; G-AX confirms this two ways (the gold equals
the complete set inside the regime; outside it the gold diverges, so the guard is
load-bearing). `composite_validated` is a structural condition on the INPUTS
(squarefree-ness of `p` plus a finite enumerated set), not an answer-key oracle for
the result (directive 8): the result is still pinned to the deep, grounded fold
`composite_roots == roots_below(p, …)`, never to `composite_validated`.

**Validated regime (the soundness boundary = `composite_validated`).**
axiom_check.py asserts the root-set equality on:
  * **every input the test suite actually checks** — both FAIL_TO_PASS
    `test_solve_modular` cases (`x**3 ≡ 1 (mod 8) -> {1}`,
    `x**4 ≡ 4 (mod 9) -> {4,5}`, reached via `solveset`→`_invert_modular`→
    `nthroot_mod(rhs,expo,m,all_roots=True)` — note 8 = 2³ and 9 = 3² are
    NON-squarefree and the gold is exactly correct on both), all of the gold's
    `test_residue` assertions (`(29,31,74)->{45}`, `(16,5,36)->{4,22}`,
    `(9,16,36)->{3,9,15,21,27,33}`, `(4,3,3249000)->{}`,
    `(36010,8,87382)->{40208,47174}`, `(0,12,37)->{0}`, `(0,7,100)->{0,..,90}`),
    and the issue's example `nthroot_mod(17*17,5,17)` containing `0`. Enumerated
    and asserted FIRST, unconditionally (no skip-guard).
  * **the squarefree-modulus regime** over ~24000 randomized `(a, n, m)`,
    `n > 2`, where the equality holds universally (0 violations).

**Known gold limitation (now formally EXCLUDED by `composite_validated`, not
merely documented).** `_nthroot_mod_composite`'s prime-power lifting is only
partially correct for **non-squarefree** moduli *outside* the enumerated test
set: for some `(a, n, p^e)`, `e ≥ 2`, the real `nthroot_mod(...,all_roots=True)`
returns a NON-root (brute-confirmed: e.g. `nthroot_mod(379,3,8,True)` yields
`[5]` though `5**3 ≡ 5 ≠ 379 ≡ 3 (mod 8)` — true root `3`;
`nthroot_mod(253,3,16,True)` yields `[1]` though the true root is `5`; ~7% of
non-squarefree `(a,n,p)` in a small box are affected). This is a genuine defect
of the gold patch (later tracked by follow-up sympy issues). The deep model
`composite_roots == roots_below(p, …)` pins the **correct, complete** congruence
root set; the refinement claim (model output == real callee) is asserted ONLY
over the squarefree regime plus the finite enumerated test-suite triples (all
non-squarefree triples there — 8, 9, 36, 100, 3249000 — are exactly the
harness-reached ones, on which the gold is brute-confirmed exact). This is
**excluded by the `composite_validated` `Requires`**: outside it the real callee
diverges from the complete set, so equating the output to `composite_roots` there
would be an over-claim. axiom_check.py validates this both ways: inside the regime
the gold == the complete brute-force set (so `ToSeq(Result()) == composite_roots`
is faithful); outside it the gold diverges (so the `composite_validated` guard is
load-bearing, not cosmetic — it cannot be widened back to "all non-prime `p`").
`verify ⇒ resolved` is preserved: the harness only exercises in-regime inputs.

### 3.5 `prime_roots` ↔ the prime-field body of `nthroot_mod` (A-reference)
**Callee:** the unchanged prime-field path of `nthroot_mod` for prime `p`,
non-zero target (`(p-1)%n`/gcd reductions + `_nthroot_mod1`/`sqrt_mod`). The
model's `prime_roots` is its deep reference; the *consumed* Ensures is soundness,
and the function postcondition `ToSeq(Result()) == prime_roots(a,n,p)` equates
the output to the full prime-field root set. G-AX validates `prime_roots ==
nthroot_mod(...,all_roots=True)` as a set of roots over the prime moduli among
the enumerated test inputs + squarefree fuzz (a prime modulus is squarefree), 0
violations.

Docs/source: `sympy/ntheory/residue_ntheory.py` (`nthroot_mod`,
`_nthroot_mod_composite`, `_nthroot_mod1`, `sqrt_mod`, `is_nthpow_residue`);
`sympy/ntheory/primetest.py` (`isprime`); Python built-in `pow`.

## G-CONF (differential conformance — `conformance_check.py`)

**Shadow.** The `# impl-start` / `# impl-end` region of `model.py` (`nth_roots`)
copied VERBATIM into `conformance_check.py`, with only the contract statements
(`Requires` / `Ensures` / `Invariant` / `Assert` / `MustTerminate`) and the
`# invariants-start/-end` markers removed — the model IS Python, so nothing is
transliterated. Its `@Pure` dependencies (`composite_roots`, `roots_below`,
`is_root`, `composite_validated`) are copied the same way; `PSeq`/`ToSeq` become
a small immutable tuple shim (`take`/`drop`/`+`/`len`/`[]`/`==`).

**`@ContractOnly` callees call the REAL repo functions** (so the axioms of §3 are
exercised, not assumed): `power_mod` → the 3-arg `pow` builtin (§3.1);
`is_prime` → `sympy.ntheory.primetest.isprime` (§3.2); `is_nth_residue` →
`is_nthpow_residue` (`residue_ntheory.py:620`, §3.3); `is_squarefree` → all
`factorint(p)` exponents == 1; `prime_roots` → the unchanged prime-field body of
`nthroot_mod` reached by calling `nthroot_mod(a, n, p, all_roots=True)` on a
prime modulus with `a % p != 0` (§3.5).

**Oracle.** The REAL PATCHED `nthroot_mod(a, n, p, all_roots=True)`
(`sympy/ntheory/residue_ntheory.py:746`, §1) — **called**, never
transliterated; the gate applies `patch.diff` before the script runs. A
pre-patch import is detected (`require_post_patch`) and exits 2 as an ERROR, so
an unpatched container cannot read as a pass.

**Type bridge (§2 inverted).** The integer carriers are the identity
(`int` ↔ repo `int`/`mpz`; `as_int` is the identity on them), so the only
bridging is on the result: `None` ("no solution") → `[]` and each element
through `int(...)`. Lists are compared ORDER-SENSITIVELY — stricter than §2,
which leaves element order an unconstrained R-detail — because the deep fold
emits ascending residues and `_nthroot_mod_composite` returns `sorted(set(…))`.

**Input domain.** Every compared triple satisfies `nth_roots`' `Requires`
(`a >= 0`, `n > 2`, `p > 2`, `is_prime(p) or composite_validated(a, n, p)`),
asserted by `requires_ok` rather than assumed. The `composite_validated` filter
is the model's own frozen precondition (copied verbatim), not a domain narrowed
to dodge a disagreement: §3.4 records that outside it the gold's prime-power
lifting genuinely diverges from the complete root set, which is why the frozen
spec claims nothing there. All four impl branches are counted and a run that
leaves any branch at zero FAILS, so a green verdict cannot come from skipping
the behaviour the gold patch changed.

**Recursion depth.** `roots_below` is structurally recursive with depth `p`, so
it is evaluated verbatim for `p <= 1500` and by an unrolled evaluation of the
SAME recurrence for the larger enumerated moduli (87382, 3249000). Both forms
are compared on every input where the recursion is evaluable, so the unrolled
form is validated rather than trusted.

**Inputs / seed.** Boundary first (both FAIL_TO_PASS `test_solve_modular`
shapes `x**3 ≡ 1 (mod 8)` and `x**4 ≡ 4 (mod 9)`, all six `composite_validated`
triples incl. the no-root `(4,3,3249000)` and zero-target `(0,7,100)`, the
gold's other `test_residue` assertions, the issue's `nthroot_mod(17*17,5,17)`,
and small-modulus / zero-target / unreduced-`a` / minimal-`n` edges), then
seeded fuzz to **100000** Requires-satisfying comparisons. **Pinned seed:
`SEED = 18199`.**

**Recorded verdict.** `G-CONF=pass` — 100000 comparisons, 0 disagreements,
branch coverage `{composite: 53115, prime_zero: 12389, prime_nonresidue: 14194,
prime_roots: 20302}`. Refutation capability was demonstrated by mutation: a
shadow that drops the prime zero-root case (the case the gold ADDED), a fold
that drops the residue 0, a fold that keeps only even residues, and a
`prime_roots` that returns only the smallest root are each caught and reported
as disagreements. An exhaustive scan of the squarefree composite regime
(133467 `(a, n, m)` triples, `3 <= m < 200`, `3 <= n < 20`) independently
confirms the real patched callee equals the complete root set there, so the
input domain is not hiding a divergence.
