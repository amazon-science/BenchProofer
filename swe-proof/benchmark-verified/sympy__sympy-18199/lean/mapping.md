# mapping.md — sympy__sympy-18199

## Symbol binding (file:line @ base_commit `ba80d1e493f21431b4bf729b3e0452cd47eb9566`)

| Lean | Python | location |
|---|---|---|
| `implementation_nthrootMod` / `problem_spec_nthrootMod` / `correct_nthrootMod` | `nthroot_mod(a, n, p, all_roots=True)` | `sympy/ntheory/residue_ntheory.py:745` (dispatch patched at 814-822) |
| `implementation_nthrootModComposite` / `problem_spec_nthrootModComposite` / `correct_nthrootModComposite` | `_nthroot_mod_composite(a, n, m)` | `sympy/ntheory/residue_ntheory.py:746-789` (added by the patch) |

Modeling decision: the public `nthroot_mod` is modeled with `all_roots=True`
semantics (the F2P witnesses all call it with `all_roots=True` or rely on the
full root set), so the result type is `List ℤ` (the ordered list of all roots),
not the `all_roots=False` `min`-or-`None` scalar.

Deep-model decision (the load-bearing one): the NON-single-prime path — the
operation the patch actually adds — is modeled DEEPLY. `rootSetIn a n m` (pure
region) is the complete, ordered, in-range root set of `x**n == a (mod m)`,
grounded structurally in the real congruence over `m`, NOT an opaque oracle over
the helper's result. `implementation_nthrootModComposite` returns exactly that
set.

The non-single-prime path carries TWO obligations of different strength, because
the real routine's guarantees are of two different strengths:

* the EXACT-SET clause, over the regime `dispatchValidated` = `n == 2` OR
  `modulusSquarefree m` OR `modulusRegularLift a n m`. The gold patch's
  report is mathematically UNSOUND off that regime (it emits
  spurious non-roots / drops genuine roots on `p**e`, e>=2 — e.g. for
  `x**6 == 89 mod 125` it returns 118 though `118**6 % 125 = 24`; the smallest
  witness is `x**3 == 3 mod 8`, where it returns `[5]` and `5**3 % 8 = 5`), so
  equality with the complete set is claimed only there. Over that regime the deep
  model equals the real callee (validated by G-AX).
* the UNCONDITIONAL report clause `reportsRootsFor`, for EVERY non-single-prime
  modulus with no regime condition: the report lies in `[0, m)`, is strictly
  increasing, and has exactly AS MANY entries as the congruence has solutions.
  That last conjunct COUNTS the solutions, so it carries three properties:
  non-emptiness when solvable (a solvable congruence always yields a report),
  never-phantom (an unsolvable one never yields a residue) and never-partial (a
  report with fewer entries than there are solutions is rejected, which no
  emptiness-level statement can see). Counting is the STRONGEST clause true of the
  real routine on this sub-domain: off the regime the report is not a superset of
  the true root set — it omits genuine roots (579 such inputs asserted to EXIST by
  G-CONF, so a later widening of this clause into off-regime completeness fails a
  gate) — yet its LENGTH still equals the number of solutions everywhere.
  Measured true of the
  real patched routine with ZERO violations over 61146 exhaustive off-regime
  inputs (composite `m < 300`, `n in 2..12`), 80000 fuzzed non-single-prime
  inputs (`m < 1200`, `n <= 40`), 33386 exhaustive exponent-two inputs, 30000
  singular-branch inputs and 30000 unsolvable-heavy prime-power inputs. The soundness
  clause is by contrast GUARDED by the regime, because off it the real routine
  genuinely does emit non-roots (measured: 4165 of 125376 inputs with composite
  `m < 200`, `n in 3..10`, `0 <= a < m`), so an unguarded soundness clause would
  be false of the real callee.

The regime is stated as arithmetic conditions on the INPUTS (`n`, and the
multiplicity structure of `m` relative to `a` and `n`), with no enumeration of
inputs; the reported list stays pinned to the grounded set, independent of it.

Precondition decision: the modeled contracts require `0 <= a` and `1 < n`. Both
are properties of the real callee's own domain rather than narrowings of the
patch's reach — a negative target makes the real routine raise
(`a must be >= 0`, reached from the per-prime sub-call), and at `n == 1` the real
prime path returns the target unreduced (`nthroot_mod(3, 1, 2, True) == [3]`), so
neither is a regime on which any postcondition here could be true.

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX

| Lean type | Python value |
|---|---|
| `a n m p : ℤ` | the `as_int`-normalized integer arguments |
| `List ℤ` result | `sorted(set(...))` list of integer residues in `[0, m)` |
| `rootSetIn a n m` | `sorted(x for x in range(m) if pow(x, n, m) == a % m)` |
| `modulusSquarefree m` | `all(e == 1 for e in factorint(m).values())` |
| `modulusRegularLift a n m` | for every `p, e` in `factorint(m)` with `e > 1`: `a % p and n % p`, and if `e >= 3` then `all(pow(r,n,p**e) == a % p**e for r in range(p) if pow(r,n,p) == a % p)` |
| `result.Pairwise (· < ·)` | the returned list is strictly increasing |

`x ^ n.toNat` with `n : ℤ`, `0 < n` ↔ `pow(x, n)`; `% m` ↔ Python `%` on
non-negative residues (both representatives in `[0, m)` since `0 ≤ x < m`,
`m > 1`). `(x^n - a) % m == 0` ↔ `pow(x, n, m) == a % m`.

## Callee provenance (opaque / axiom decls)

All are callees the changed code CALLS but does NOT change. Provenance and the
weakest property G-AX validates:

| Lean decl | Python callee | provenance | A-tag |
|---|---|---|---|
| `modulusIsPrime p` | `isprime(p)` (`sympy/ntheory/primetest.py`) | unchanged; gates the dispatch at line 814 | A-reference |
| `modulusSquarefree m` | `all(e == 1 for e in factorint(m).values())` (`factorint`) | unchanged; one leg of the regime over which the deep model is validated == the real routine | A-reference |
| `modulusRegularLift a n m` | the arithmetic predicate on the repeated prime factors of `m` given in the bijection table above (`factorint` + `pow`) | unchanged callees only; the second leg of that regime | A-reference |
| `primeUnitRoots a n p` | `nthroot_mod(a, n, p, True)` on a PRIME `p` with `a % p != 0` — the unchanged prime-modulus path (`_nthroot_mod1` / gcd-reduction below the patched lines) | the prime path's root-finding body is unchanged by the patch (only the dispatch order above it changed) | A-reference |
| `primeUnitRoots_sound` | soundness of the above ON A SINGLE-PRIME MODULUS: every returned `r` has `0 ≤ r < p` and `pow(r,n,p)==a%p` | the ONE axiom the proof CONSUMES (soundness clause). Its `modulusIsPrime p = true` hypothesis is load-bearing: that modulus regime is the callee's whole intended domain, and on any other the property is FALSE of the real callee (`a=5,n=3,m=8 -> [1]` but `1**3 % 8 = 1 != 5`; also `(3,3,8)`, `(7,3,15)`, `(2,5,27)`), so an unrestricted axiom would certify impls that emit genuine non-roots | A-consumed |

The internal root-assembly LOGIC of the new routine is NOT axiomatized and NOT
transliterated into the Lean impl: it is subsumed by the deep model
`rootSetIn` over the validated regime (§0.7 — the changed op is modeled deeply,
never hidden behind an oracle about the function under change).

## G-AX / G-CONF fuzz seed

`conf_seed = 18199` (pinned). G-AX validates: prime-path `nthroot_mod` soundness
under its declared Requires (`0 <= a`, `1 < n`, `1 < p`, and the modulus being a
single prime — the consumed axiom),
`isprime` vs trial division, and the two regime booleans against independently
re-derived references (with the regime and its complement both shown INHABITED).

G-AX runs WITHOUT the change applied, so it is deliberately confined to callees the
change does not touch: every obligation about the root-set VALUE for a modulus that
is not a single prime is a property of the CHANGED routine, and without the change
such a modulus aborts or reports nothing — a leg written to tolerate that is
vacuous rather than validating. Those obligations are therefore G-CONF's, which
runs WITH the change applied and probes, load-bearing in three parts: (i) that over
the regime (exponent two on every non-single-prime modulus; squarefree `m` at any
non-negative target; the regular-lift predicate on non-squarefree `m`) the real
patched `nthroot_mod(a,n,m,True)` equals the complete root set `rootSetIn`;
(ii) that for EVERY non-single-prime modulus, regime or not, the real report is
in-range, strictly increasing, and has exactly as many entries as the congruence
has solutions — together with the companion assertion that off the regime the
report nevertheless OMITS genuine roots, which is what makes counting rather than
containment the strongest clause claimable there; and (iii) that composite-modulus non-root
counterexamples for the unit-base solver EXIST, so a future widening of the
consumed axiom's single-prime domain fails a gate instead of being certified.
G-CONF diffs the R/I shadow of the dispatch (non-prime → deep root set; prime →
`[0]` or the prime-path roots) against the real patched function on the exact-set
obligation over the SAME regime, and on the unconditional report obligation over
every non-single-prime modulus including the regime's complement.

## Leakage disposition — relaxed, for one named facet

`meta.json relaxed_leakage = true` alongside the in-bundle `RELAXED_LEAKAGE.md`,
which states the measured basis in full. In brief: the maximal edit derivable
from the public `problem_statement` alone is the zero-target dispatch
(`if a % p == 0: return [0] if all_roots else 0`, ahead of the residue check).
Applied at `base_commit` with the frozen `test_patch`, it leaves the sole
FAIL_TO_PASS test failing — `1 failed, 129 deselected, 1 xfailed` — while
`patch.diff` on the same tree and interpreter gives `1 passed, 129 deselected,
1 xpassed`. The graded discriminator is therefore the non-single-prime root-set
behaviour at the moduli 8 and 9 (`(a,n,m) = (1,3,8)` and `(4,4,9)`, both INSIDE
the regime), which the public text never mentions; a spec silent about a
non-single-prime modulus admits the declining `Solution_prepatch.lean` and loses
its discriminating power. That facet — `reportsRootsFor`, the pinned
`result = rootSetIn` clause, and the `compositeValidated` / `dispatchValidated`
regime predicates — is what the relaxation covers, and nothing else: the
pre-patch diagnosis, the assembly algorithm and any changed/unchanged partition
of the touched file stay out of the spec view (`markers.spec_view` searched for
`declin`, `refus`, `raise`, `NotImplemented`, `component-wise`, `prime-power`,
`Hensel`, `CRT`, `orbit`, `unchanged` — zero hits), and the mechanical screen
G-LEAK runs reports the spec view clean on the current bytes.
