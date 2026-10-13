# Requirements: `Relational.as_set()` returns a condition set for unsolvable univariate relations

## Introduction

In SymPy, a univariate relational expression (an `Equality`, `Unequality`, or
inequality such as `GreaterThan`/`LessThan`/`StrictGreaterThan`/
`StrictLessThan`) can be converted into the real-number set of values that
satisfy it via the `Boolean.as_set()` method. For a single `Relational`, this
conversion is performed by `Relational._eval_as_set` in
`sympy/core/relational.py`, which delegates to
`solve_univariate_inequality` (in `sympy/solvers/inequalities.py`) to compute
the solution set.

When the underlying equation or inequality is transcendental or otherwise not
solvable in closed form, `solve_univariate_inequality` raises
`NotImplementedError`. Today that exception propagates out of
`as_set()`, so calling `.as_set()` on something like `Eq(x*cos(x) - 3*sin(x),
0)` fails with `NotImplementedError` instead of producing a usable result.

The goal is to make `.as_set()` on a univariate `Relational` degrade
gracefully: when no explicit solution set can be computed, it must return a
symbolic condition set describing the solutions (the set of real values `x`
that satisfy the relation) rather than raising. The affected code is
`Relational._eval_as_set` in `sympy/core/relational.py`; the returned symbolic
set is a `ConditionSet` (from `sympy/sets/conditionset.py`) over the reals
(`S.Reals`). All existing conversions that already succeed must be preserved
unchanged.

## Requirement 1: Graceful fallback when a univariate relation has no explicit solution set

**User story:** As a user converting a symbolic relation to a set, I want
`.as_set()` to return a meaningful condition set when the relation cannot be
solved explicitly, so that my code does not crash with `NotImplementedError`
on transcendental or otherwise unsolvable relations.

**Acceptance criteria**

1. WHEN `as_set()` is called on a univariate `Relational` whose solution set
   cannot be computed explicitly (the internal solver signals that it is
   unable to solve the equation or inequality), THEN `as_set()` SHALL return a
   set object rather than raising `NotImplementedError`.
2. WHEN such an unsolvable univariate `Relational` is converted, THEN the
   returned object SHALL be the set of real values of the free symbol that
   satisfy the relation, expressed as a condition set (a `ConditionSet`) whose
   bound variable is that free symbol, whose defining condition is the
   relation itself, and whose base set is the real numbers (`S.Reals`).
3. WHEN the returned condition set is compared for equality against an
   independently constructed condition set built from the same free symbol,
   the same relational condition, and the reals as base set, THEN the two
   SHALL compare equal.
4. IF the internal solver signals inability to solve the relation, THEN the
   fallback SHALL be triggered ONLY by that specific signal and SHALL NOT
   suppress unrelated errors.

## Requirement 2: Preserve exact solution sets for solvable univariate relations

**User story:** As a user relying on the existing behavior of `.as_set()`, I
want relations that can be solved explicitly to keep returning their exact
solution sets, so that adding the fallback does not regress established
results.

**Acceptance criteria**

1. WHEN `as_set()` is called on a univariate relation whose solution set can be
   computed explicitly, THEN it SHALL return that exact solution set (the same
   result the solver produced before the fallback was introduced) and SHALL
   NOT return a condition set fallback.
2. WHEN a solvable inequality that bounds the free symbol against a constant is
   converted, THEN the result SHALL be the corresponding real interval — open
   at any strict bound, closed at any non-strict bound, and unbounded toward the
   relevant infinity — and SHALL NOT be a condition set fallback.
3. WHEN a solvable equality is converted, THEN the result SHALL be the finite
   set of the real values that satisfy it, and SHALL NOT be a condition set
   fallback.
4. WHEN a solvable inequation (a `Ne` relation) is converted, THEN the result
   SHALL be the real line with the excluded value removed, expressed as the
   union of the open intervals lying on either side of that value, and SHALL
   NOT be a condition set fallback.
5. WHEN a solvable polynomial inequality is converted, THEN the result SHALL be
   its exact real solution set (the union of the intervals determined by the
   polynomial's real roots), and SHALL NOT be a condition set fallback.
6. The system SHALL continue to require that the relation passed to the
   single-relation conversion be univariate (exactly one free symbol).
