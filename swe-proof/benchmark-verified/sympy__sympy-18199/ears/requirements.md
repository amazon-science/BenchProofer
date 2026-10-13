# Requirements: complete root set for modular n-th roots

## Introduction

The modular n-th root finder `nthroot_mod(a, n, p, all_roots=False)` in
`sympy/ntheory/residue_ntheory.py` solves the congruence `x**n ≡ a (mod p)`,
returning either the smallest root or, when `all_roots=True`, the list of all
roots in the range `[0, p)`.

Two behaviors are currently missing or incorrect:

1. **The zero root is dropped.** When the target `a` is divisible by the
   modulus (`a % p == 0`), `x = 0` is a genuine solution of `x**n ≡ a`, but the
   function never reports it. For example, with `a = 17*17`, `n = 5`, `p = 17`,
   the value `0` is a root modulo `17` yet is omitted.

2. **Composite moduli are unsupported.** When the modulus is not prime the
   function raises `NotImplementedError`, even though the equation has a
   well-defined solution set obtainable by factoring the modulus, solving modulo
   each prime-power component, and recombining the component solutions.

Because the public solver `solveset` (via the modular-inversion helpers
`_invert_modular` / `_solve_modular` in `sympy/solvers/solveset.py`) delegates to
`nthroot_mod` when inverting `Mod(base**exponent, m)`, these gaps also cause
`solveset` to return incomplete or unevaluated results for modular power
equations. The goal is to make `nthroot_mod` report the complete root set —
including the zero root and the composite-modulus case — so that downstream
modular equation solving is correct.

## Requirement 1: Report the zero root when the target vanishes modulo a prime

**User story:** As a user computing modular n-th roots, I want `x = 0` reported
whenever the target is a multiple of a prime modulus, so that the returned root
set is complete.

**Acceptance criteria**

1. WHEN `nthroot_mod(a, n, p)` is called with `p` prime, `n` a positive integer
   greater than 2, and `a % p == 0`, THEN the function SHALL report `0` as a
   root of `x**n ≡ a (mod p)`.
2. WHEN the conditions of criterion 1 hold, THEN the value returned SHALL be the
   list `[0]`.
3. The system SHALL ensure that any residue it reports as a root under these
   conditions actually satisfies `x**n ≡ a (mod p)` in the range `0 ≤ x < p`.

## Requirement 2: Solve congruences with a composite modulus

**User story:** As a user solving `x**n ≡ a (mod m)` where `m` is not prime, I
want the full set of solutions returned instead of an error, so that composite
moduli are handled.

**Acceptance criteria**

1. WHEN `nthroot_mod(a, n, m)` is called with `m` composite (not prime), THEN
   the function SHALL NOT raise `NotImplementedError` and SHALL instead compute
   residues for `x**n ≡ a (mod m)` by decomposing the modulus.
2. WHEN the modulus is composite, THEN the function SHALL obtain its result by
   factoring `m` into its prime-power components, determining roots of the
   congruence modulo each prime-power factor (lifting the roots found modulo the
   underlying prime to that prime power), and recombining one component root per
   factor across all factors by the Chinese Remainder Theorem to form residues
   in `0 ≤ x < m`.
3. WHEN the modulus is composite, THEN the returned list SHALL be sorted in
   increasing order and SHALL contain no duplicate residues.
4. WHEN the modulus is composite, THEN the residues returned SHALL be exactly
   those produced by the Chinese-Remainder recombination of criterion 2 — no
   others introduced — and each such residue, reduced modulo each prime dividing
   `m`, SHALL satisfy `x**n ≡ a` modulo that prime.
5. WHEN the modulus is composite and the decomposition finds no root of the
   congruence modulo some prime-power factor, THEN the recombination SHALL yield
   no residues and the function SHALL return an empty result rather than raising
   an error.

## Requirement 3: Preserve existing prime-modulus root finding

**User story:** As an existing user of `nthroot_mod`, I want the behavior for
prime moduli with a non-vanishing target to remain unchanged, so that current
results are not regressed.

**Acceptance criteria**

1. WHEN `nthroot_mod(a, n, p)` is called with `p` prime and `a % p != 0`, THEN
   the function SHALL return the same roots it did before: with `all_roots=True`
   the sorted list of all roots in `[0, p)`, and with `all_roots=False` the
   smallest such root.
2. IF `p` is prime, `a % p != 0`, and `a` is not an n-th power residue modulo
   `p`, THEN the function SHALL return `None`.
3. The system SHALL continue to accept the documented example inputs and produce
   their established results — for instance, roots `[8, 11]` for
   `nthroot_mod(11, 4, 19, True)` and the smallest root `23` for
   `nthroot_mod(68, 3, 109)`.
4. WHEN `n == 2`, THEN the function SHALL continue to delegate to the modular
   square-root routine and honor the `all_roots` flag.

## Requirement 4: Correct modular power equation solving in solveset

**User story:** As a user of `solveset`, I want modular equations of the form
`Mod(base**exponent, m) - a = 0` solved correctly, including composite moduli
and the zero-root case, so that the solution set is complete.

**Acceptance criteria**

1. WHEN `solveset` inverts an expression of the form `Mod(base**exponent, m)`
   for the unknown, THEN it SHALL obtain the constituent residues from the modular
   n-th root computation and form, for each residue `r`, the arithmetic
   progression of integers congruent to `r` modulo `m`.
2. WHEN the modular n-th root computation reports that the congruence has no
   solution, THEN `solveset` SHALL yield the empty solution set for that branch.
3. IF the modular n-th root computation returns roots (including the zero root or
   roots for a composite modulus) that were previously unavailable, THEN
   `solveset` SHALL include the corresponding solution progressions in its result
   rather than returning the equation unevaluated.
4. The system SHALL preserve the previously working behavior of modular inversion
   and modular equation solving for cases that were already handled correctly,
   including detection of modular expressions and the existing results for prime
   moduli.
