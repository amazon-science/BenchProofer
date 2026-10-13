# Requirements: correct subset and equality results for products of finite sets

## Introduction

SymPy models sets with classes in `sympy.sets` — among them `FiniteSet` (an
explicit finite collection of elements), `ProductSet` (the cartesian product of
several sets, whose members are tuples), and `Interval`. Two related public
operations are affected here:

- `Set.is_subset` (backed by the `is_subset_sets` multiple-dispatch handlers in
  `sympy/sets/handlers/issubset.py`), which decides whether one set is contained
  in another and returns a fuzzy result (`True`, `False`, or unknown).
- Set equality via `Eq(...)` / `Equality`, backed by the `_eval_is_eq`
  multiple-dispatch handlers in `sympy/sets/handlers/comparison.py`, together
  with the simplification path `Relational._eval_simplify` /
  `Equality._eval_simplify` in `sympy/core/relational.py`.

Reported defect: for `a = FiniteSet(1, 2)`, `b = ProductSet(a, a)` and the
finite set of its tuples `c = FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))`, the
call `b.is_subset(c)` returned no definite answer (unknown/`None`) even though
`b` and `c` denote the same collection. There was no dispatch handling a
`ProductSet` tested against a `FiniteSet`, so the subset test fell through to
the generic unknown result. As a consequence, simplifying an equality between
two set objects (for example `Eq(b, c).simplify()`) raised
`AttributeError: 'Complement' object has no attribute 'equals'`, because the
simplification code assumed the two sides were ordinary algebraic expressions
and tried to subtract them.

The goal is to (1) give a definite subset verdict when a product of finite sets
is tested against a finite set of tuples, (2) make general set-to-set equality
answer definitely whenever containment can be decided both ways, and (3) make
equality simplification robust when the two sides are sets rather than algebraic
expressions, so it returns a result instead of crashing — while leaving every
other subset and equality behavior unchanged.

## Requirement 1: Subset test of a finite product against a finite set of tuples

**User story:** As a user comparing sets, I want `is_subset` to give a definite
answer when a product of finite sets is compared against a finite set of tuples,
so that containment queries and downstream simplifications work.

**Acceptance criteria**

1. WHEN `is_subset` is evaluated for a `ProductSet` (whose factors are finite,
   so it enumerates finitely many tuples) against a `FiniteSet`, THEN the result
   SHALL be `True` if every tuple produced by the cartesian product of the
   factors is a member of the `FiniteSet`, and SHALL be `False` if at least one
   such tuple is not a member.
2. WHEN `a = FiniteSet(1, 2)`, `b = ProductSet(a, a)` and `c` is the finite set
   containing exactly the four tuples `(1, 1)`, `(1, 2)`, `(2, 1)`, `(2, 2)`,
   THEN `b.is_subset(c)` SHALL be the singleton value `True`.
3. WHEN a finite `ProductSet` is tested against a `FiniteSet` that omits at
   least one tuple of the product (for instance a finite set whose members are
   not tuples of the product at all), THEN the result SHALL be the singleton
   value `False`.
4. The membership test used per tuple SHALL be the existing `FiniteSet`
   containment semantics (structural equality of the concrete tuple against the
   set's elements); this requirement SHALL NOT change how a `FiniteSet` decides
   membership of an element.

## Requirement 2: Definite equality for general sets via containment both ways

**User story:** As a user, I want equality between two sets to resolve to a
definite truth value whenever containment can be decided in both directions, so
that `Eq` of equal collections is recognized as true and of unequal ones as
false.

**Acceptance criteria**

1. WHEN equality is evaluated between two general set operands for which no more
   specific rule applies, THEN the result SHALL be `True` if each operand is a
   subset of the other, `False` if either containment direction is definitely
   not satisfied, and SHALL remain undetermined only when a containment
   direction cannot be decided.
2. WHEN a `ProductSet` (whose members are tuples) is compared for equality
   against an `Interval` (a set of scalar reals), THEN `Eq(...)` SHALL evaluate
   to the singleton value `False`, because a set of tuples and a real interval
   can never denote the same collection.
3. The existing definite equality verdicts for other set pairings SHALL be kept:
   equality of two `ProductSet`s with different numbers of factors SHALL remain
   `False`; equality of two `FiniteSet`s, of two `Interval`s, and of a
   `FiniteSet` against an `Interval` SHALL keep their current results.

## Requirement 3: Equality simplification is robust for set-valued sides

**User story:** As a user, I want `Eq(...).simplify()` on set-valued relations to
return a result rather than raise an error, so that simplifying an equality of
sets is safe.

**Acceptance criteria**

1. WHEN a relation is simplified and, after simplifying its two sides, either
   side is not an algebraic expression (not an `Expr`, e.g. it is a set object
   such as a `Complement`, `ProductSet`, or `FiniteSet`), THEN the
   simplification SHALL return the relation with its simplified sides and SHALL
   NOT attempt to form the arithmetic difference of the two sides.
2. WHEN such a relation is simplified, THEN the operation SHALL NOT raise an
   `AttributeError` (or any error) arising from treating a set-valued side as an
   algebraic expression.
3. WHEN two set objects denote the same collection (for example the finite set
   of tuples `c` and the equal product `b` from Requirement 1), THEN
   `Eq(c, b).simplify()` SHALL evaluate to the singleton value `True`.
4. WHEN two set objects denote different collections (for example `a =
   FiniteSet(1, 2)` and the finite set of tuples `c`), THEN `Eq(a, c).simplify()`
   SHALL evaluate to the singleton value `False`.
5. WHEN an equality between set operands cannot be decided because a free symbol
   in one operand leaves a containment direction undetermined, THEN
   `Eq(...).simplify()` SHALL return that equality unchanged (unevaluated), equal
   to the original `Eq` object, rather than forcing it to a truth value or
   raising.
6. The `Equality`-specific simplification path that rewrites a single-symbol
   equation into a solved form SHALL apply this same guard: IF either side of
   the equality is not an algebraic expression, THEN it SHALL return the
   equality unchanged rather than attempting the single-symbol rewrite.

## Requirement 4: Preserve existing subset, superset, and product behavior

**User story:** As a user, I want the fix to be localized so that all other set
operations keep working exactly as before.

**Acceptance criteria**

1. The existing `is_subset` results for set pairings other than a finite
   `ProductSet` against a `FiniteSet` SHALL be kept unchanged (including the
   results for `FiniteSet`/`FiniteSet`, `FiniteSet`/`Interval`, `Interval`
   pairings, and unions).
2. The existing behavior of `is_proper_subset`, `is_superset`, and
   `is_proper_superset` SHALL be kept unchanged.
3. Iterating a `ProductSet` SHALL keep yielding exactly the tuples of the
   cartesian product of its factors, and `FiniteSet` / `ProductSet` membership
   (`contains`) SHALL keep its current results.
4. Simplification of relations whose sides are ordinary algebraic expressions
   SHALL keep its current behavior (the new guard SHALL take effect only when a
   side is not an algebraic expression).
