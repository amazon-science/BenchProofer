# Requirements — Symmetric rich comparison of core sympy objects with foreign types

## Introduction

Python's data model asks a rich-comparison method (`__eq__`, `__ne__`, `__lt__`,
`__gt__`, `__le__`, `__ge__`) to return the `NotImplemented` singleton when it
cannot make sense of the other operand, so that the interpreter can delegate the
operation to the reflected method on the other operand. When a comparison method
instead returns a definite `False`, the interpreter treats the comparison as
resolved and never consults the other operand — which breaks the symmetry of
equality and inequality between a sympy object and an instance of an unrelated
user-defined class.

This affects the core comparison machinery in:

- `sympy/core/basic.py` — `Basic.__eq__` and `Basic.__ne__`.
- `sympy/core/numbers.py` — the `__eq__`/`__ne__` (and the reflected-dispatch
  path of the ordering operators) of the numeric types `Integer`, `Rational`,
  `Float`, and the `NumberSymbol` family. The special values `oo`
  (`S.Infinity`), `-oo` (`S.NegativeInfinity`), and `nan` (`S.NaN`) retain their
  existing equality method, which yields a definite result rather than
  delegating to the other operand; `zoo` (`S.ComplexInfinity`) delegates
  through the shared `Basic` equality path. The observable equality, inequality
  and ordering results of these special values are preserved (see Requirements
  3 and 4).

The goal: when the left operand is one of these sympy objects and the right
operand is of a type sympy cannot interpret, the comparison must cooperate with
the reflected method on the right operand so that `==`/`!=` are symmetric, while
preserving all existing comparison results between recognized sympy objects.

Throughout this document, "cannot be interpreted as a symbolic value" means that
sympy's attempt to coerce the operand into a symbolic/numeric object fails (a
sympification failure), as opposed to a value that coerces successfully but is of
a different kind or has different content.

## Requirement 1: Delegate equality when the other operand is uninterpretable

**User story:** As an author of a custom class that wants its instances to
compare as equal to certain sympy objects, I want sympy's equality method to
defer to my class's reflected method when it does not recognize my object, so
that equality between my instances and sympy objects is symmetric.

**Acceptance criteria**

1. WHEN a `Basic` instance is compared with `==` against an object that cannot
   be interpreted as a symbolic value, THEN `Basic.__eq__` SHALL return the
   `NotImplemented` singleton rather than a definite boolean.
2. WHEN a core finite numeric object (`Integer`, `Rational`, `Float`) or a
   `NumberSymbol` is compared with `==` against an object that cannot be
   interpreted as a numeric value, THEN that object's `__eq__` SHALL return the
   `NotImplemented` singleton rather than a definite boolean.
3. WHEN both a sympy object and the other operand's equality method return
   `NotImplemented` for a given pair, THEN the `==` operator SHALL evaluate to
   `False` and the `!=` operator SHALL evaluate to `True`, in both operand
   orders (i.e. the result SHALL be independent of which operand is on the left).
4. WHEN the left operand is a sympy object whose equality method delegates as
   described in criteria 1 and 2 (a `Basic` instance, a finite numeric object,
   or a `NumberSymbol`) and the other operand's own equality method reports that
   it is equal to that sympy object (returning a truthy result), THEN
   `sympy_object == other` and `other == sympy_object` SHALL both evaluate to
   `True`, and `sympy_object != other` and `other != sympy_object` SHALL both
   evaluate to `False`.

## Requirement 2: Inequality is the negation of the resolved equality operator

**User story:** As a user comparing sympy objects, I want `!=` to be the exact
logical negation of `==` as the interpreter resolves it, so that inequality is
consistent with equality even when delegation to a reflected method occurs.

**Acceptance criteria**

1. WHEN `!=` is evaluated for a sympy object whose `__ne__` is defined as the
   negation of equality, THEN `__ne__` SHALL negate the result of the `==`
   operator (i.e. the outcome after any reflected-method delegation) rather than
   negating the raw return value of the object's own `__eq__` method.
2. IF the `==` operator between a sympy object and the other operand resolves to
   `True`, THEN the corresponding `!=` comparison SHALL resolve to `False`, in
   both operand orders.
3. IF the `==` operator between a sympy object and the other operand resolves to
   `False`, THEN the corresponding `!=` comparison SHALL resolve to `True`, in
   both operand orders.
4. The system SHALL apply this negation-of-the-operator behavior uniformly to
   the `__ne__` methods of the affected comparison classes so that no `__ne__`
   returns the `NotImplemented` singleton to the caller as a final `!=` value
   when equality could be resolved by delegation.

## Requirement 3: Preserve existing equality results for recognized operands

**User story:** As a sympy user, I want all previously-correct equality and
inequality results between genuine sympy objects (and between sympy objects and
plain interpretable values) to remain unchanged, so that the delegation fix does
not regress established semantics.

**Acceptance criteria**

1. WHEN a sympy object is compared for equality with an operand that IS
   interpretable but is of a different kind or has different content, THEN `==`
   SHALL evaluate to `False` and `!=` SHALL evaluate to `True` (e.g. a bare
   `Basic` instance is not equal to the integer `0`).
2. WHEN two recognized sympy objects have the same kind and equal content, THEN
   `==` SHALL evaluate to `True` and `!=` SHALL evaluate to `False`.
3. WHEN a sympy object is compared with itself (identity), THEN `==` SHALL
   evaluate to `True`.
4. WHEN a finite numeric operand (such as an integer-, rational-, or
   float-valued sympy number) is compared with a foreign object whose equality
   method declares it equal to any finite number, THEN equality SHALL resolve to
   `True` symmetrically and inequality to `False` symmetrically.
5. WHEN a non-finite numeric value (`oo`, `-oo`, `zoo`, or `nan`) is compared
   with a foreign object whose equality method declares it NOT equal to
   infinities and NaN, THEN equality SHALL resolve to `False` symmetrically and
   inequality to `True` symmetrically.

## Requirement 4: Ordering comparisons with uninterpretable operands raise TypeError

**User story:** As a sympy user, I want an attempt to order a numeric sympy
object against a value that has no numeric meaning to fail loudly, so that
nonsensical orderings are never silently produced.

**Acceptance criteria**

1. WHEN a core numeric object (`Integer`, `Rational`, `Float`, `oo`, `-oo`,
   `zoo`, or `nan`) is used as the left operand of `<`, `>`, `<=`, or `>=`
   against an operand that cannot be interpreted as a numeric value, THEN the
   comparison SHALL raise `TypeError`.
2. WHEN such a numeric object is the right operand of an ordering comparison
   whose left operand (a foreign object) does not define that ordering, THEN the
   reflected ordering attempt SHALL also raise `TypeError`.
3. The system SHALL keep this behavior for every combination of the four
   ordering operators and both operand orders, for both finite and non-finite
   numeric values.

## Requirement 5: Symmetric ordering between numbers and named constants

**User story:** As a sympy user, I want ordered comparisons between a plain
number and a named mathematical constant (a `NumberSymbol` such as `pi`) to be
symmetric, so that reversing the operands yields the mirror-image relation.

**Acceptance criteria**

1. WHEN a `Rational` or `Float` is compared against a `NumberSymbol` with an
   ordering operator, THEN the comparison SHALL be delegated to the
   `NumberSymbol` using the correctly mirrored operator: a strict `<` on one
   side SHALL correspond to a strict `>` on the other, and a non-strict `<=`
   SHALL correspond to `>=`.
2. IF `x` is a `Rational` or `Float` and `c` is a `NumberSymbol`, THEN
   `(x < c)` SHALL equal `(c > x)`, `(x <= c)` SHALL equal `(c >= x)`,
   `(x > c)` SHALL equal `(c < x)`, and `(x >= c)` SHALL equal `(c <= x)`.
3. IF `x` is a `Rational` or `Float` and `c` is a `NumberSymbol`, THEN
   `(x == c)` SHALL equal `(c == x)` and `(x != c)` SHALL equal `(c != x)`.
