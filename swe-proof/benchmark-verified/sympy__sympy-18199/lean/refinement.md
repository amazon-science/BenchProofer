# refinement.md — sympy__sympy-18199

Operation-by-operation correspondence between `Solution.lean`'s impl regions and
`patch.diff` (the gold patch). Tags: **R** (type refinement), **A-consumed**
(proof uses this axiom's property), **A-reference** (deep model / callee,
validated == real callee by G-AX), **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF**; the A legs and this
narrative are audited by **G-EQ**. `patch.diff` is the gold patch **verbatim**
(G-RESOLVE).

## The solver dispatch — `nthroot_mod(a, n, p, all_roots=True)`

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

| Lean op (`implementation_nthrootMod`) | patch.diff op | tag | justification |
|---|---|---|---|
| `if !(modulusIsPrime p) then return implementation_nthrootModComposite a n p` | `if not isprime(p): return _nthroot_mod_composite(a, n, p)` | I (control) + A-reference (`isprime`) + deep model | the NEW non-prime operation is modeled DEEPLY (see below); `isprime` is the unchanged gate. |
| `if a % p == 0 then return [0]` | `if a % p == 0: return [0]` | I — the public zero-root case, identical |
| `return primeUnitRoots a n p` | fall-through to the unchanged prime path (`is_nthpow_residue` gate, `_nthroot_mod1` / gcd reduction) returning the prime roots with `all_roots=True` | A-reference + A-consumed (`primeUnitRoots` = unchanged prime path; its soundness is `primeUnitRoots_sound`) |

Note: under `all_roots=True` and the grounded root-set spec, the prime-path
`is_nthpow_residue`-None case is the faithful image `[]` (the real prime path
returns `None`). The reordering of the composite check above the
`is_nthpow_residue` gate is exactly the `if !(modulusIsPrime p)` early return.

## The new helper — `_nthroot_mod_composite(a, n, m)` (deep model)

The non-single-prime routine's report is mathematically UNSOUND on prime-power
moduli `p**e` (e>=2): on
`x**6 == 89 mod 125` it returns `118` although `118**6 % 125 = 24 != 89`, and it
drops genuine roots. A grounded `correct_` over the TRUE root set is therefore
literally false of that op, so it is NOT transliterated line-for-line.

Instead the helper is modeled DEEPLY:

| Lean op | patch.diff op | tag |
|---|---|---|
| `implementation_nthrootModComposite a n m := rootSetIn a n m` | the complete in-range root set the helper is intended to return | A-reference (deep model) |

`rootSetIn a n m` is the complete, ordered, duplicate-free set of residues in
`[0, m)` solving `x**n == a (mod m)` — a structural fold over the real congruence,
not an oracle over the helper's output. The per-element soundness conjuncts are
stated through `isRootIn a n m x` (`0 <= x < m` and `x**n == a (mod m)`, the same
congruence unfolded at one residue), which is what keeps an impl that echoes an
oracle instead of solving the congruence from discharging them. The composite postcondition
(`result = rootSetIn a n m` plus soundness) is asserted over the ARITHMETIC
regime `compositeValidated a n m` = `modulusSquarefree m` OR
`modulusRegularLift a n m` (the public dispatch widens this to
`dispatchValidated` = `n == 2` OR `compositeValidated`):

- **exponent two, ANY non-single-prime modulus** — the quadratic case is handled by
  a dedicated square-root routine that returns the complete set over every modulus
  (measured: 33386 exhaustive inputs, 0 disagreements with `rootSetIn`);
- **squarefree `m`, ANY non-negative target** — no prime occurs more than once, so
  the report is the complete set (measured: 20000+
  fuzzed inputs, 0 disagreements). No coprimality condition is needed;
- **`modulusRegularLift a n m`** — every prime occurring more than once in `m`
  divides neither `a` nor `n`, plus a further arithmetic side condition relating
  `a` to the residues solving the congruence to that prime's multiplicity. It is
  a purely arithmetic condition on the INPUTS with no enumeration of them
  (measured: 2000+ admitted non-squarefree inputs, 0 disagreements).

Over that regime G-AX validates `real nthroot_mod(a,n,m,True) == rootSetIn`
(deep-model soundness+completeness against the real callee), and G-CONF confirms
the R/I shadow of the dispatch agrees with the real patched function. Outside the
regime the EXACT-SET claim is dropped, so the documented gold unsoundness is
neither certified nor echoed — but the sub-domain is NOT left free: the
UNCONDITIONAL report clause `reportsRootsFor` still binds it (next section). This
is a spec-domain restriction grounded in the INPUTS (directive 8 clean) — the
result stays pinned to `rootSetIn`, independent of the regime predicate.

## The unconditional report clause — what binds the regime's complement

For EVERY non-single-prime modulus, with no regime condition at all, the spec
requires the report to lie in `[0, m)`, be strictly increasing, and have exactly
AS MANY entries as the congruence has solutions. That solution COUNT is the
load-bearing conjunct: it is simultaneously

- **non-empty when solvable** — a solvable congruence always yields a report,
  and it is what the graded surface reaches at a
  quadratic congruence over a modulus with a fifth power of two in it, an input
  the regime's `n == 2` leg admits but which no enumeration of test triples had
  covered; and
- **never-phantom** — an unsolvable congruence never yields a residue; and
- **never-partial** — a report carrying *some* of the solutions is rejected. This
  is the strictly stronger content the count adds over any statement about
  emptiness: a rival that reports only the largest genuine root off the regime is
  in-range, strictly increasing, non-empty exactly when the true set is non-empty,
  and sound — yet it is wrong, and only the count sees it. (That rival was built
  and machine-checked to verify against the emptiness-level draft of this clause,
  which is why the clause counts.)

Why COUNTING and not CONTAINMENT is the ceiling here: off the regime the report is
not a superset of the true root set — it omits genuine roots at 579 measured
inputs, a fact G-CONF asserts must EXIST so that a later widening of this clause
into off-regime completeness is caught rather than certified — yet its LENGTH
equals the number of solutions at every measured input.

All three properties are properties of the real patched routine, not of the modeled
skeleton: the count is measured with ZERO mismatches over 60000 fuzzed
non-single-prime inputs and 47542 exhaustive off-regime inputs, and its weaker
emptiness consequences with ZERO violations over 61146 exhaustive off-regime inputs
(composite `m < 300`, `n in 2..12`), 80000 fuzzed non-single-prime inputs
(`m < 1200`, `n <= 40`), 33386 exhaustive exponent-two inputs, 30000
singular-branch inputs and 30000 unsolvable-heavy prime-power inputs. The
SOUNDNESS clause by contrast had to be GUARDED by the regime, because off it the
real routine genuinely emits non-roots (4165 of 125376 composite inputs; the
smallest is `x**3 == 3 mod 8`, reported `[5]` with `5**3 % 8 = 5 != 3`), so an
unguarded soundness clause would be FALSE of the real function. G-AX and G-CONF
both probe the report clause over the regime's complement.

## What the count-level ceiling leaves free off the regime — measured

Because counting is the ceiling, an implementation that off the regime reports
SOME strictly increasing in-range list of the right LENGTH satisfies the spec
even when its residues are not the true roots. That freedom is deliberate and
forced: the real patched routine off the regime both omits genuine roots and
emits non-roots, so any clause stronger than the count would assert arithmetic
the routine does not satisfy. It was probed rather than assumed. 18 rival
implementations were built region-for-region against the current spec view
(`markers.same_spec` true for every one, no unsound evasions, every one reaching
a verdict in 4.4–28.3 s under the cell's 300 s cap), so all 18 are admissible:

- 11 are REJECTED by the report clause — reporting nothing off the regime,
  truncating to the first root, reversing, padding by repetition, reporting a
  proper subset, or delegating a non-single-prime modulus to the unit-base prime
  solver — which is the count-level content doing its work;
- 7 VERIFY, and every one of them is a count-preserving off-regime relabeling:
  the first `k` canonical residues, the top `k`, or a parity split between the
  two, with `k` the number of solutions.

Each of those 7 was carried back to a faithful refined patch (the regime
predicates re-derived as real arithmetic per the bijection in `mapping.md`, the
deviation confined to the off-regime branch of the new helper) and run through
the correctness oracle: all 7 RESOLVE — FAIL_TO_PASS `test_solve_modular` plus
all 113 PASS_TO_PASS, patch applied. They are therefore correct echoes, not
counterexamples to `verify ⇒ correct`: the graded inputs `(1,3,8)` and `(4,4,9)`
lie INSIDE the regime, where the report stays pinned to `rootSetIn`, so the
off-regime freedom is unreachable by the graded behaviour. Strengthening the
clause to exclude these rivals would narrow the spec's claim to something the
patched routine does not satisfy off the regime, which is the opposite defect.

Leakage: this bundle carries a declared relaxation for the non-single-prime
facet (`meta.json relaxed_leakage = true` + `RELAXED_LEAKAGE.md`); the measured
basis — the public-text-only edit failing the sole graded test where `patch.diff`
passes it — is recorded there and summarised in `mapping.md`.

## Discriminators (G-DIFF)

Two independently-fixed behaviours distinguish the patched from the pre-patch
solver; `Solution_prepatch.lean` reproduces both bugs and FAILS verification:

- **Non-prime modulus**: the pre-patch solver reported nothing for a composite
  modulus, modelled as returning `[]`; that breaks
  `result = rootSetIn a n m` whenever a root exists (e.g. the squarefree witness
  `(2,3,15)` or `(1,3,8)`, both admitted by the arithmetic regime) AND,
  independently of any regime, the solution-counting conjunct of the unconditional
  report clause — so the prepatch twin fails on two separate clauses.
- **Zero target, prime modulus**: the pre-patch dispatch ran the residue check
  first, dropping the `x = 0` solution; the pre-patch impl omits the
  `a % p == 0 → [0]` branch, breaking that postcondition clause.

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A, I, or the deep model. The one operation that genuinely
*changed* — solving for a non-prime modulus — is modeled deeply
(`rootSetIn`), not hidden behind an oracle axiom about the function under change.
`primeUnitRoots` / `isprime` / `modulusSquarefree` / `modulusRegularLift` cover
UNCHANGED callees; `compositeValidated` / `dispatchValidated` are spec-domain
restrictions grounded in the inputs, and they restrict only the EXACT-SET clause —
the report clause holds unconditionally, so no sub-domain of the changed
operation is left unconstrained.

`primeUnitRoots_sound` is claimed only for a single-prime modulus, which is that
callee's whole intended domain. The restriction is load-bearing: on any other
modulus the property is FALSE of the real callee (`(5,3,8) -> [1]` but
`1**3 % 8 = 1 != 5`; likewise `(3,3,8)`, `(7,3,15)`, `(2,5,27)`), so an
unrestricted axiom would let an impl that delegates a composite modulus to the
prime solver discharge soundness from a false premise. G-CONF asserts those
counterexamples EXIST (they are only reachable with the change applied), so
re-widening the axiom fails a gate.

## verify(Solution) ⇒ resolved

`implementation_nthrootMod` verifies only if it returns the deep root set
`rootSetIn` for the non-prime case over the validated regime, `[0]` for the
prime zero-target case, and the prime-path roots otherwise, with every returned
entry an in-range root wherever the report is pinned (soundness,
`primeUnitRoots_sound` on its single-prime domain) — AND, off the regime, only if
its report is an in-range strictly-increasing list with exactly as many entries as
the congruence has solutions. That last obligation is what makes the regime's
complement inhabited by no wrong impl: reporting nothing for it, truncating it, reversing it,
padding it, reporting a proper subset of the roots, or delegating it to the prime
solver each fail a conjunct. By R (`int ↔ Int`,
`None`/raise ↔ `[]`) the verified solver equals the gold dispatch on the tested
inputs; by G-AX the deep model equals the real non-prime routine over the
validated regime and `primeUnitRoots` is sound against the real prime path; by
G-CONF the R/I dispatch agrees with `patch.diff` behaviour over the regime.
Therefore a model satisfying this spec is the gold patch up to type refinement
and audited callees on the tested inputs — and the gold patch resolves
(G-RESOLVE).
