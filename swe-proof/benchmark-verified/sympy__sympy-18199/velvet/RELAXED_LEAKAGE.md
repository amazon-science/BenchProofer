# RELAXED_LEAKAGE — sympy__sympy-18199 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition was prescribed by this bundle's own recorded audits. The
reference-improvement verdict (`verdict.md`, LEAK sub-verdict) derived it in
full: "This is a textbook public-statement ↔ gold mismatch … Faithful +
non-leaking is provably impossible because the public issue and the graded
test are about different things. The leak is the behavior itself, not lazy
de-narration. … Per `RELAXED_LEAKAGE.md` this is the unavoidable relaxed
category. CAVEAT (process defect …): the bundle does not currently DECLARE the
relaxation (no in-bundle RELAXED_LEAKAGE doc, no relaxed meta flag); per
policy it should be re-dispositioned to relaxed with the in-bundle doc +
flag." The subsequent re-audit's G-PANEL-3 LEAKAGE verdict found the identical
facet (the non-prime postcondition + `compositeValidated` enumeration) against
the bundle that still lacked this disposition. This file implements the
prescribed fix.

## The mismatch

The public `problem_statement` reports ONLY the zero-target bug:

> nthroot_mod function misses one root of x = 0 mod p. When in the equation
> x**n = a mod p , when a % p == 0. Then x = 0 mod p is also a root of this
> equation. … `nthroot_mod(17*17, 5, 17)` has a root `0 mod 17`. But it does
> not return it.

It never mentions composite / non-prime moduli. But the gold patch
(`sympy/ntheory/residue_ntheory.py`) makes TWO behavioral changes:

1. the public zero-target dispatch — `if a % p == 0: return [0]` before the
   residue check (the issue's report), and
2. a NON-public change: replacing
   `raise NotImplementedError("Not implemented for composite p")` with a new
   complete-root-set composite solver (`_nthroot_mod_composite`, CRT over
   prime-power factors).

The graded FAIL_TO_PASS test is solely `test_solve_modular`, whose changed
assertions exercise ONLY the composite cases (moduli 8 and 9, via
`solve_modular` reductions to `nthroot_mod` root sets). The zero-root
assertions of the public issue live in `test_nthroot_mod`, which is NOT in
the graded set. So the actually-graded discriminator of the gold edit is the
composite-modulus complete root set — behavior the public text never
mentions.

The leaking spec-view content is exactly that behavior:

- the non-prime postcondition
  `ensures (¬ isPrime p ∧ compositeValidated a n p) → out = rootsBelow p.toNat a n p`
  (the complete in-range root set for a non-prime modulus),
- the method docstring branch "(1) NON-PRIME MODULUS: the result is the
  COMPLETE set of in-range roots …", and
- the `compositeValidated` regime predicate, which enumerates the
  non-squarefree harness triples (e.g. `(1,3,8)`, `(4,4,9)`) on which the
  deep-model equality is explicitly validated.

## Why the leak is unavoidable

Faithfulness forces the composite behavior into the spec:

- The graded F2P test grades the composite root sets (moduli 8 and 9). A spec
  that is silent about non-prime moduli admits the composite-declining
  prepatch behavior (`Solution_prepatch_1.lean`, which returns no roots for a
  non-prime modulus) — a spec-too-weak (G-EQ / P1) defect, and its refined
  patch fails the graded test. To reject that prepatch (G-DIFF) while
  accepting gold, the spec MUST pin the complete-root-set semantics on
  non-prime moduli. That clause IS the non-public gold discriminator.
- The `compositeValidated` enumeration is likewise forced: the real composite
  solver's complete-root-set equality is only validated over squarefree
  moduli plus the explicitly-checked non-squarefree triples (G-AX shows the
  regime is LOAD-BEARING — outside it the real solver diverges from the
  complete set). The graded moduli 8 and 9 are non-squarefree, so a faithful
  regime bound must name triples with those moduli; dropping them would
  either un-cover the graded inputs or over-claim the equality out of regime
  (a G-PANEL-2 faithfulness defect).
- A spec derivable from the problem_statement alone could only pin the
  zero-target `[0]` root over a prime modulus. It could not discriminate the
  graded composite behavior at all.

Faithful + non-leaking is therefore provably impossible here; the recorded
verdict.md LEAK sub-review derived exactly this shape and prescribed this
disposition. This is the same faithful-must-leak shape as the dispositioned
sympy__sympy-13877 instance (structural-vs-algebraic pivot-test facet): the
discriminator exists only in the gold diff and the graded tests, and the spec
cannot be both faithful and silent about it.

## Core soundness is intact

- G-VERIFY: `Solution.lean` verifies (total correctness, `decreasing`
  measure on the copy loop); proof closes without sorry.
- G-DIFF: both prepatch twins fail on their discriminating postconditions —
  `Solution_prepatch.lean` (residue-check-first dispatch that drops the zero
  root) fails the `[0]`-singleton clause; `Solution_prepatch_1.lean`
  (composite declined → no roots) fails `out = rootsBelow p.toNat a n p` on
  admitted non-prime inputs.
- Spec tightness: the four postconditions pin the output EXACTLY on every
  branch of the precondition domain (non-prime → the grounded complete fold
  `rootsBelow`; prime & zero target → `[0]`; prime & residue → `primeRoots`;
  prime & non-residue → `[]`), plus a per-element soundness clause grounded
  in `powerMod`. Total-correctness semantics excludes divergence attacks. The
  modulus domain runs from `2` up, which is the closure of the domain under the
  modeled body's re-entry on the prime factors of the modulus, so the pinning
  covers every input a required result depends on (mapping.md §3.6). That
  domain bound is an input-side condition, observable from the caller, and is
  not one of the leaking clauses enumerated above.
- G-CONF: R/I shadow agrees with patch.diff behaviour (4006 inputs, 0
  disagreements). G-AX: powerMod/isNthResidue/primeRoots/rootsBelow contracts
  validated against the real callees, regime validated FAITHFUL +
  LOAD-BEARING (3685 checks incl. moduli 8, 9). G-RESOLVE: resolved (gold
  verbatim).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the composite-modulus complete-root-set behavior + its validated
regime enumeration).
