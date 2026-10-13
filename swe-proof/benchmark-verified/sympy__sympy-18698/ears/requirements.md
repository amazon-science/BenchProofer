# Requirements: Consistent square-free factor listing in `sqf_list`

## Introduction

SymPy's square-free factorization API is exposed through the polynomial tools
module (`sympy/polys/polytools.py`), chiefly the public functions `sqf_list`
and `sqf`, both routed through the internal helpers `_generic_factor_list` /
`_generic_factor` and ultimately `_symbolic_factor_list`. A square-free
factorization expresses a polynomial as a product of pairwise-coprime,
square-free factors, each raised to a distinct multiplicity (exponent). By the
definition of a square-free decomposition, **each multiplicity should occur at
most once** in the result: everything that shares a given multiplicity is a
single square-free factor.

The current implementation violates this. For a symbolic input built as a
product of several powers, `_symbolic_factor_list` collects the per-power
factors without consolidating those that end up carrying the same multiplicity.
As reported, the result

```
sqf_list( (x**2 + 1) * (x - 1)**2 * (x - 2)**3 * (x - 3)**3 )
```

returns two separate entries of multiplicity `3` — `(x - 3, 3)` and
`(x - 2, 3)` — instead of a single entry `(x**2 - 5*x + 6, 3)` (the product of
those two factors). The correct, consistent behavior (which the polynomial
backend already produces for a single dense polynomial, e.g.
`sqf_list( x**5 - 2*x**4 - 2*x**3 + 4*x**2 + x - 2 )`) lists exactly one factor
per multiplicity.

The goal is to make the square-free method (`sqf_list`, and by extension `sqf`)
always emit at most one factor per multiplicity, while leaving the
irreducible-factorization method (`factor_list` / `factor`) and all other
polynomial behavior unchanged.

## Requirement 1: One consolidated factor per multiplicity in `sqf_list`

**User story:** As a user computing a square-free factorization, I want each
multiplicity to appear at most once in the factor list, so that the output is a
genuine square-free decomposition and is consistent regardless of how the input
expression was written.

**Acceptance criteria**

1. WHEN `sqf_list` is called on a polynomial expression, THEN the returned list
   of `(factor, multiplicity)` pairs SHALL contain no two pairs with the same
   multiplicity.
2. WHEN two or more square-free factors of the input would carry the same
   multiplicity `k`, THEN `sqf_list` SHALL return a single pair for `k` whose
   factor is the product of all those factors.
3. The set of multiplicities appearing in the returned list SHALL equal the set
   of multiplicities that arise from the factorization — no multiplicity present
   before consolidation is dropped, and no new multiplicity is introduced.
4. WHEN `sqf_list` is called on
   `(x**2 + 1) * (x - 1)**2 * (x - 2)**3 * (x - 3)**3`, THEN the result SHALL be
   equal to `(1, [(x**2 + 1, 1), (x - 1, 2), (x**2 - 5*x + 6, 3)])` up to the
   ordering of the factor list — in particular, the two multiplicity-3 factors
   SHALL be reported as the single product factor `x**2 - 5*x + 6`.
5. WHEN `sqf_list` is called on an input whose square-free decomposition has a
   distinct polynomial for every multiplicity (for example
   `x**5 - 2*x**4 - 2*x**3 + 4*x**2 + x - 2`), THEN each such factor SHALL be
   returned unchanged with its own multiplicity, since no consolidation is
   needed.
6. The leading coefficient / content component returned as the first element of
   the `sqf_list` result SHALL be unchanged by this consolidation.

## Requirement 2: Consolidate multiplicity-1 factors of a symbolic product

**User story:** As a user calling `sqf_list` on a product of distinct symbolic
factors, I want factors that share multiplicity 1 to be combined, so that the
result still has at most one entry per multiplicity.

**Acceptance criteria**

1. WHEN `sqf_list` is called on an input whose square-free decomposition yields
   two or more distinct factors all carrying multiplicity 1, THEN the result
   SHALL report a single multiplicity-1 entry whose factor is the product of
   those factors.
2. IF the consolidated factor is later reported as an expression rather than a
   `Poly`, THEN it SHALL be the expanded product of the combined factors.

## Requirement 3: Preserve irreducible factorization (`factor_list` / `factor`)

**User story:** As a user of `factor_list` and `factor`, I want their behavior
to be unaffected, so that irreducible factorizations still list each
irreducible factor separately even when several share a multiplicity.

**Acceptance criteria**

1. WHEN `factor_list` is called on an input that factors into two or more
   distinct irreducible factors each of multiplicity 1, THEN the result SHALL
   keep those irreducible factors as separate `(factor, 1)` entries rather than
   combining them into a single product.
2. The consolidation of factors by multiplicity SHALL apply only to the
   square-free method and SHALL NOT alter the factor list produced by the
   irreducible-factorization method.
3. `factor` and `factor_list` SHALL continue to return every irreducible factor
   as its own `(factor, multiplicity)` entry, including cases where distinct
   irreducible factors share the same multiplicity.

## Requirement 4: Preserve existing square-free and polynomial API behavior

**User story:** As a maintainer, I want the rest of the polynomial API to keep
working exactly as before, so that the fix is a targeted correction and not a
regression.

**Acceptance criteria**

1. WHEN `sqf_list` or `sqf` is called on an input that already has at most one
   factor per multiplicity, THEN the returned factors, multiplicities, and
   coefficient SHALL be unchanged from prior behavior.
2. The relative ordering guarantees of `sqf_list` / `factor_list` results (the
   established sorting of the factor list) SHALL be preserved.
3. WHEN a polynomial has a non-trivial numeric content or leading coefficient,
   THEN that coefficient SHALL be reported as the first element of the result
   tuple exactly as before, unaffected by factor consolidation.
4. All other polynomial operations exposed by the module (construction,
   arithmetic, gcd/lcm, resultants, root finding, `sqf_norm`, `sqf`
   reconstruction into an expression, and related utilities) SHALL retain their
   existing behavior and results.
5. WHEN `sqf` (the expression form) is called, THEN the reconstructed
   square-free expression SHALL remain consistent with the consolidated
   `sqf_list` output, so that raising each returned factor to its multiplicity
   and multiplying reproduces the original polynomial.
