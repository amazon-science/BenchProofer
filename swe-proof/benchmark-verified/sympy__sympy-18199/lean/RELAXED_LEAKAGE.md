# RELAXED_LEAKAGE — sympy__sympy-18199 (lean)

**Disposition: KEEP with relaxed leakage, for one named facet only —
the non-single-prime (composite) modulus root-set behaviour.**
`meta.json relaxed_leakage = true`; G-LEAK records status `relaxed`.

The governing rule is `prompts/lean/spec_guide.md` directive 6: *"Exception —
relaxed-leakage: for a proven `problem_statement` ↔ gold mismatch where a
faithful spec MUST name the discriminator, keep the instance with the leak
allowed. Do NOT relax to dodge ordinary de-narration."* Both halves of that
sentence are addressed below: the mismatch is measured, and the ordinary
de-narration has already been carried out, so nothing is being dodged.

## 1. The mismatch is measured, not asserted

The public `problem_statement` describes exactly one defect, on a PRIME modulus:

> nthroot_mod function misses one root of x = 0 mod p. When in the equation
> x**n = a mod p , when a % p == 0. Then x = 0 mod p is also a root of this
> equation. … `nthroot_mod(17*17, 5 , 17)` has a root `0 mod 17`. But it does
> not return it.

17 is prime; no composite modulus, no factorisation of the modulus, and no
refusal-to-answer branch is mentioned anywhere in the public text. `hints_text`
is "I will submit a pr regarding this." and is excluded from the leakage
judgement by the same directive.

The MAXIMAL edit derivable from that text alone is the zero-target dispatch. It
was applied to a tree extracted from `repos/sympy_sympy.git` at `base_commit`
ba80d1e493f21431b4bf729b3e0452cd47eb9566, ahead of the residue check in
`sympy/ntheory/residue_ntheory.py :: nthroot_mod`, and in the form that is
strictly more generous than the issue text asks for (both `all_roots` shapes):

```python
    if a % p == 0:
        return [0] if all_roots else 0
```

With `instance.json`'s `test_patch` applied, the sole FAIL_TO_PASS test was run
on that tree:

```
python -m pytest sympy/solvers/tests/test_solveset.py -k test_solve_modular -q
  -> FAILED ...::test_solve_modular - assert Cond...
     1 failed, 129 deselected, 1 xfailed, 5 warnings in 1.09s
```

The failing assertion is `solveset(Mod(x**3, 8) - 1, x, S.Integers)` against
`ImageSet(Lambda(n, 8*n + 1), S.Integers)` (and the companion at modulus 9) —
the two composite moduli the graded test was changed to cover.

Control on the same tree and the same interpreter, with `patch` (the gold edit)
applied instead of the public-text-only edit:

```
python -m pytest sympy/solvers/tests/test_solveset.py -k test_solve_modular -q
  -> 1 passed, 129 deselected, 1 xpassed, 6 warnings in 0.83s
```

So the graded discriminator is NOT the behaviour the public text reports. It is
the composite-modulus complete-root-set behaviour, reached through
`solveset -> _invert_modular -> nthroot_mod(..., all_roots=True)` at the moduli
8 and 9, where the pre-patch routine declines the input outright. A spec that
says nothing about a non-single-prime modulus admits the declining pre-patch
behaviour — `Solution_prepatch.lean` is exactly that implementation, and it must
FAIL verification for the bundle to have any discriminating power at all. That
is what forces composite-modulus content into the spec view, and that content is
by construction not derivable from the public text.

## 2. What the relaxation covers, and what it does not

Covered: the propositions about a non-single-prime modulus —
`reportsRootsFor` (in-range, strictly increasing, and carrying exactly as many
residues as the congruence has solutions), the pinned clause
`result = rootSetIn a n p` inside the regime, and the regime predicates
`compositeValidated` / `dispatchValidated` that delimit where the pinning is
claimed. Each is load-bearing: dropping any one of them either admits the
declining pre-patch twin (G-DIFF) or over-claims where the real routine and the
complete root set diverge (G-PANEL-2 faithfulness; the divergence is asserted to
exist by G-CONF, so a later widening is caught rather than certified).

NOT covered, and absent from the spec view rather than excused by this file:

* the pre-patch DIAGNOSIS. No spec-view line says the routine ever declined,
  refused or raised on an input; the report clause is stated as a solution
  COUNT, which is a property of the desired behaviour rather than a description
  of the previous failure mode.
* the gold ALGORITHM. No spec-view line mentions factoring the modulus, a
  per-prime-power component, lifting, an inverse-derivative branch, a residue
  orbit, or a CRT recombination. The regime is stated as an arithmetic
  condition on the inputs `a`, `n`, `m`.
* a changed/unchanged partition of the touched file. No spec-view line
  characterises any callee as untouched by this work.

Search of the projected spec view (`markers.spec_view`, the same projection the
gates judge) for those items: `declin`, `refus`, `raise`, `NotImplemented`,
`component-wise`, `prime-power`, `Hensel`, `CRT`, `orbit`, `unchanged` — zero
hits. The only surviving arithmetic vocabulary is "repeated prime factor", which
names a property of the modulus (its squarefreeness), not a step of the routine.

The four declared `opaque` callees carry behaviour-only docstrings and no
repository name: searching the spec view for `nthroot_mod`,
`_nthroot_mod_composite`, `factorint`, `cartes`, `crt`, `mod_inverse`,
`is_nthpow_residue` and `residue_ntheory` also returns zero hits, and the
mechanical screen G-LEAK runs (`leakage.screen`) reports the current spec view
clean — `passed=True`, `hard_failures=[]`, `warnings=[]`. What this file relaxes
is therefore the SEMANTIC leakage judgement about the facet named above, not a
lexical hit the screen caught.

## 3. Core soundness is intact

Observed on the current bytes (`Solution.lean`
e13040de36d49de9bf7e40a125d55f40c90d1d335cac0be20f9fd2f3fd2b195c):

* the shipped solution verifies — `scripts/lean_verify.sh` exit 0; both
  `correct_*` obligations close with the axiom set
  `[primeUnitRoots_sound, propext, Classical.choice, Quot.sound]`, no `sorry`.
* `Solution_prepatch.lean` does NOT verify (exit 3: the obligations cannot be
  closed for the declining implementation), so the bundle still separates the
  pre-patch behaviour from the gold.
* the obligations are not vacuous: `False` is not derivable from the hypothesis
  group of either `correct_*` theorem (residual goal `⊢ False` under
  `modulusIsPrime m = false` and
  `modulusSquarefree m = true ∨ modulusRegularLift a n m = true`), while the
  same appended-theorem shape with `True` in place of `False` verifies; and the
  empty report does not satisfy `problem_spec_nthrootMod` (four unsolved
  semantic goals, among them `0 = (rootSetIn …).length` for a non-single-prime
  modulus).
* the consumed axiom `primeUnitRoots_sound` is claimed only for
  `modulusIsPrime p = true`, which is the whole of that callee's intended
  domain; handed any other modulus it licenses nothing.

Only the secondary no-leakage property is relaxed, for the single facet named in
section 2.
