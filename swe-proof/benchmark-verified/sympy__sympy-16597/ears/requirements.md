# Requirements — SymPy assumption boundedness (`sympy__sympy-16597`)

## Introduction

SymPy's old (three-valued) assumptions engine records `is_*` facts for a
quantity by forward-chaining a fixed set of implication rules. The rule source
lives in `sympy/core/assumptions.py` (the `_assume_rules` `FactRules`
declaration) and is mirrored, in compiled form, by
`sympy/assumptions/ask_generated.py` (`get_known_facts_cnf` /
`get_known_facts_dict`); the runtime closure that propagates those rules over a
`Symbol`/`Basic` object's assumptions is `sympy/core/facts.py`.

The defect: membership in a *bounded* number class did not imply finiteness. A
symbol declared even (or integer, rational, …) reported `is_finite` as unknown
(`None`) even though every such number is necessarily finite. Concretely,
`Symbol('m', even=True).is_finite` returned `None`.

The goal is to teach the assumptions engine that the ordinary bounded number
classes — rational, irrational, algebraic, transcendental, and everything below
integer (integer, even, odd, prime, composite) — are finite, and to let the
engine's automatically-derived contrapositives resolve the number-class facts of
the unbounded real objects (positive/negative infinity) that were previously
left unknown. Existing implications and the facts of concrete numbers must be
preserved.

Throughout, "quantity" means a `Symbol` or other `Basic` expression whose `is_*`
assumption properties are being queried, and a fact is *true* / *false* /
*unknown* when the corresponding `is_*` property returns `True` / `False` /
`None`.

## Requirement 1: Bounded number classes imply finiteness

**User story:** As a user relying on SymPy's assumptions, I want any quantity
known to be rational, irrational, algebraic, or transcendental to also be known
finite, so that finiteness-dependent logic (limits, sums, simplifications)
behaves correctly.

**Acceptance criteria**
1. WHEN a quantity is known to be rational, THEN the assumptions engine SHALL
   report that quantity as finite (true) and as real (true).
2. WHEN a quantity is known to be irrational, THEN the assumptions engine SHALL
   report that quantity as finite (true) and as real (true).
3. WHEN a quantity is known to be algebraic, THEN the assumptions engine SHALL
   report that quantity as finite (true) and as complex (true).
4. WHEN a quantity is known to be transcendental, THEN the assumptions engine
   SHALL report that quantity as finite (true), as complex (true), and as not
   algebraic (false).
5. The system SHALL treat a quantity as transcendental exactly when it is
   complex, finite, and not algebraic.
6. The system SHALL treat a quantity as irrational exactly when it is real,
   finite, and not rational.

## Requirement 2: The integer family is finite

**User story:** As a user, I want any integer-class quantity to be known finite,
so that declaring a symbol even/odd/integer/prime carries the expected
finiteness.

**Acceptance criteria**
1. WHEN a quantity is known to be integer, THEN the assumptions engine SHALL
   report that quantity as finite (true), rational (true), and real (true).
2. WHEN a quantity is known to be even, THEN the assumptions engine SHALL report
   that quantity as finite (true) and integer (true).
3. WHEN a quantity is known to be odd, THEN the assumptions engine SHALL report
   that quantity as finite (true) and integer (true).
4. WHEN a quantity is known to be prime, THEN the assumptions engine SHALL report
   that quantity as finite (true).
5. WHEN a quantity is known to be composite, THEN the assumptions engine SHALL
   report that quantity as finite (true).

## Requirement 3: Unbounded real objects resolve their number-class facts

**User story:** As a user working with `S.Infinity` and `S.NegativeInfinity`, I
want their number-class assumptions to reflect that they are not ordinary
(finite) numbers, so that querying them gives definite answers instead of
unknown.

**Acceptance criteria**
1. WHEN a quantity is known to be infinite (not finite), THEN the assumptions
   engine SHALL report that quantity as not rational (false), not irrational
   (false), not algebraic (false), and not transcendental (false).
2. WHEN a quantity is known to be infinite, THEN the assumptions engine SHALL
   report that quantity as not integer (false), and consequently not even
   (false), not odd (false), not prime (false), and not composite (false).
3. WHEN the positive infinity object is queried, THEN the assumptions engine
   SHALL report it as: not integer (false), not rational (false), not algebraic
   (false), not transcendental (false), not irrational (false), not even
   (false), not odd (false), not composite (false), and noninteger (true); and
   SHALL keep reporting it as real (true), complex (true), positive (true),
   finite (false), and infinite (true).
4. WHEN the negative infinity object is queried, THEN the assumptions engine
   SHALL report it as: not integer (false), not rational (false), not algebraic
   (false), not transcendental (false), not irrational (false), not even
   (false), not odd (false); and SHALL keep reporting it as real (true), complex
   (true), negative (true), finite (false), and infinite (true).
5. IF a quantity is real and known to be not integer, THEN the assumptions
   engine SHALL report that quantity as noninteger (true).

## Requirement 4: Symbol declarations seed finiteness

**User story:** As a user constructing symbols with assumptions, I want a symbol
declared with a bounded-class assumption to carry finiteness automatically, so
that no separate `finite=True` declaration is needed.

**Acceptance criteria**
1. WHEN a symbol is created with the integer assumption set true, THEN the
   assumptions engine SHALL report that symbol as finite (true) and real (true).
2. WHEN a symbol is created with the integer assumption true together with a
   sign/nonnegativity/nonpositivity assumption, THEN the assumptions engine SHALL
   still report that symbol as finite (true).
3. WHEN a symbol is created with the odd assumption true, THEN the assumptions
   engine SHALL report that symbol as finite (true) and integer (true).
4. WHEN a symbol is created with the even assumption true, THEN the assumptions
   engine SHALL report that symbol as finite (true) and integer (true).
5. WHEN a symbol is created with the rational assumption true, THEN the
   assumptions engine SHALL report that symbol as finite (true) and real (true).
6. WHEN a symbol is created with the irrational assumption true, THEN the
   assumptions engine SHALL report that symbol as finite (true) and real (true).

## Requirement 5: Negated bounded-class assumptions stay non-committal

**User story:** As a user, I want a symbol declared *not* to belong to a bounded
class to leave finiteness (and other higher facts) unknown, so that the engine
never over-concludes.

**Acceptance criteria**
1. WHEN a symbol is created with the even assumption set false, THEN the
   assumptions engine SHALL report its finiteness as unknown (None) and its
   integer fact as unknown (None).
2. WHEN a symbol is created with the odd assumption set false, THEN the
   assumptions engine SHALL report its finiteness as unknown (None) and its
   integer fact as unknown (None).
3. WHEN a symbol is created with the rational assumption set false, THEN the
   assumptions engine SHALL report its finiteness as unknown (None) and its real
   fact as unknown (None).
4. WHEN a symbol is created with the irrational assumption set false, THEN the
   assumptions engine SHALL report its finiteness as unknown (None) and its real
   fact as unknown (None).

## Requirement 6: Preserve existing assumption behavior (regression)

**User story:** As a maintainer, I want the finiteness additions to leave all
previously established facts intact, so that no existing consumer regresses.

**Acceptance criteria**
1. The system SHALL keep the pre-existing implication chain intact: integer
   implies rational, rational implies algebraic, algebraic implies complex, real
   implies complex and hermitian, and even implies integer and not odd.
2. The system SHALL keep reporting the number-class facts of concrete finite
   numbers unchanged — e.g. zero, one, and negative one remain integer, rational,
   real, and finite; explicit rationals remain rational, real, and finite; pi and
   E remain transcendental, irrational, real, complex, and finite; and the
   imaginary unit remains imaginary, complex, and finite.
3. WHEN the undefined/indeterminate objects (NaN and complex infinity) are
   queried, THEN the assumptions engine SHALL leave their number-class facts as
   before (no new definite integer/rational/finite conclusions introduced by this
   change).
4. WHILE evaluating whether a power expression is rational, IF the base is known
   rational and the exponent is known integer and it is not the case that the
   base is zero with a negative exponent, THEN the system SHALL report the power
   as rational (true), and SHALL otherwise leave the existing rationality
   determination unchanged.
5. WHEN a symbol declared irrational is used where a real value is expected (for
   example as an argument to the two-argument min/max constructions), THEN the
   system SHALL continue to accept it and behave as for any other real quantity.
