# Requirements: complete diophantine results are independent of the `syms` ordering

## Introduction

`sympy.solvers.diophantine.diophantine` is the public entry point for solving
Diophantine equations. It returns a set of solution tuples, where each tuple
gives the value of every variable in the equation. By default the components of
each tuple follow the internal canonical variable ordering (the equation's free
symbols sorted by SymPy's default sort key). Two keyword options affect the
result:

- `syms` — an optional sequence of the equation's variables that lets the caller
  choose the order in which the components appear in the returned tuples.
- `permute` — when `True`, the function returns not only the base solution but
  all applicable sign permutations and/or value permutations of it (for example,
  for a sum of even powers the full set of signed permutations of the base
  solution).

The function is recursive: when the caller supplies a `syms` ordering that
differs from the internal canonical ordering, `diophantine` computes the
solution set using the canonical ordering by calling itself, and then rewrites
each returned tuple into the caller-requested order.

A defect appears in that reorder-and-recurse path: the recursive call is made
without forwarding the `permute` option. As a result, when the caller passes a
`syms` order that differs from the canonical order *and* `permute=True`, the
inner solve runs with `permute=False`, so only the base solution is produced and
then reordered. The caller receives an incomplete result. When the requested
`syms` order happens to coincide with the canonical order, the reorder branch is
skipped and permutation works, so the returned solution set silently depends on
the order in which the variables are listed.

The goal is to make the returned solution set depend only on the equation and
the `permute` setting — never on the chosen `syms` order — so that requesting a
permuted result yields the complete set of solutions regardless of variable
order, with the components arranged according to `syms`.

## Requirement 1: Permuted results are complete regardless of `syms` order

**User story:** As a user solving a Diophantine equation, I want
`permute=True` to return the full set of solutions no matter which order I list
the variables in `syms`, so that the result does not silently depend on variable
ordering.

**Acceptance criteria**

1. WHEN `diophantine` is called with `permute=True` and an explicit `syms`
   sequence whose order differs from the equation's internal canonical variable
   ordering, THEN `diophantine` SHALL return the same set of solutions (up to the
   component ordering imposed by `syms`) that it returns for the same equation
   and `permute=True` under the canonical variable ordering.
2. WHEN `diophantine` is called with `permute=True` for an equation admitting
   several sign/value permutations of its base solution, THEN the returned set
   SHALL contain every such permutation, regardless of the `syms` order supplied.
3. WHEN the same equation is solved with `permute=True` under two different
   `syms` orderings, THEN the two returned solution sets SHALL contain the same
   number of solutions and SHALL be equal after reordering each tuple's
   components into a common variable order.
4. WHEN `diophantine` is called with `permute=True` and a `syms` sequence, THEN
   each returned tuple SHALL list its components in the order given by `syms`.

## Requirement 2: `syms` reordering preserves the requested option semantics

**User story:** As a user, I want choosing a custom variable order via `syms` to
change only the arrangement of the returned tuple components, so that it never
changes which solutions are returned.

**Acceptance criteria**

1. WHEN `diophantine` reorders its results to match an explicit `syms` sequence,
   THEN it SHALL compute the underlying solution set using the same `permute`
   setting that was passed by the caller.
2. IF `permute` is `False` (its default) and an explicit `syms` sequence is
   given, THEN `diophantine` SHALL return exactly the base solution set with each
   tuple's components arranged in the `syms` order, unchanged from prior
   behavior.
3. The system SHALL keep the mapping between each variable and its solution value
   consistent with the `syms` order, so that reordering the tuples never
   misassigns a value to the wrong variable.

## Requirement 3: Existing diophantine behavior is unchanged (regression protection)

**User story:** As a maintainer, I want all previously-correct solving behavior
to keep working, so that fixing the ordering defect introduces no regressions.

**Acceptance criteria**

1. WHEN `diophantine` is called with `permute=True` and no `syms` sequence (or a
   `syms` sequence already equal to the canonical order), THEN it SHALL continue
   to return the complete permuted solution set exactly as before.
2. WHEN `diophantine` is called without `permute` (default `False`), THEN it
   SHALL continue to return the base solution set, whether or not a `syms`
   sequence is supplied.
3. The system SHALL continue to solve linear, binary quadratic, univariate,
   general-sum-of-squares, general-sum-of-even-powers, general-Pythagorean, and
   ternary quadratic equations, and to handle sign-only, sign-and-value, and
   restricted-sign permutations, unchanged.
4. WHEN `syms` is supplied but is not a sequence, THEN `diophantine` SHALL raise a
   `TypeError` indicating that `syms` must be given as a sequence, as before.
5. The system SHALL continue to return an empty set for equations with no integer
   solutions and to return the trivial all-zero solution where it applies,
   unchanged.
