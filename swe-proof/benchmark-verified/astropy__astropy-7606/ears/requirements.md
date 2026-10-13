# Requirements: Robust equality comparison for units against arbitrary operands

## Introduction

In `astropy.units`, a unit object can be compared for equality with another
object using the `==` and `!=` operators. Both the base unit class
(`UnitBase`) and the class representing an unparseable/unrecognized unit
(`UnrecognizedUnit`) live in `astropy/units/core.py` and implement their own
`__eq__` (and, for `UnrecognizedUnit`, `__ne__`) methods.

Equality comparison works by attempting to interpret the right-hand operand as
a unit using the lenient constructor `Unit(other, parse_strict='silent')`. That
constructor raises an exception for operands that cannot be interpreted as a
unit — most notably `None`, but also values of unrelated types. The existing
code let that exception escape:

- `UnrecognizedUnit.__eq__` called `Unit(other, parse_strict='silent')` without
  guarding it, so a comparison such as `u.Unit('asdf', parse_strict='silent') == None`
  raised `TypeError` ("None is not a valid Unit") instead of simply reporting
  that the two objects are not equal.

Equality comparison against an arbitrary object is expected to be total: it
should return a boolean (or defer to the other operand) and never propagate an
exception to the caller. The goal is to make equality/inequality comparison of
both `UnitBase` and `UnrecognizedUnit` instances robust against operands that
cannot be interpreted as units, while preserving all existing equality,
inequality, and ordering semantics for genuine units.

## Requirement 1: Comparing an unrecognized unit with a non-unit operand must not raise

**User story:** As a user who has parsed an unknown unit string leniently, I
want to compare the resulting unit object with `None` or any unrelated object,
so that ordinary equality checks and membership tests do not crash my program.

**Acceptance criteria**

1. WHEN an `UnrecognizedUnit` instance is compared with `==` against an operand
   that cannot be interpreted as a unit (for example `None`), THEN the
   comparison SHALL complete without raising any exception and SHALL report the
   two objects as not equal (i.e. `unit == None` evaluates to a falsey result).
2. WHEN an `UnrecognizedUnit` instance is compared with `!=` against an operand
   that cannot be interpreted as a unit (for example `None`), THEN the
   comparison SHALL complete without raising any exception and SHALL report the
   two objects as unequal (i.e. `unit != None` evaluates to `True`).
3. WHEN an `UnrecognizedUnit` instance is tested for membership with the `in`
   operator against a collection that includes an operand which cannot be
   interpreted as a unit together with a genuine, recognized unit it does not
   equal, THEN the test SHALL complete without raising and SHALL report that the
   unit is not a member.
4. IF the lenient interpretation of the other operand fails with an error while
   evaluating equality of an `UnrecognizedUnit`, THEN the comparison SHALL treat
   the comparison as not applicable (deferring to Python's default object
   comparison) rather than allowing the error to propagate to the caller.

## Requirement 2: Equality semantics of an unrecognized unit with interpretable operands

**User story:** As a user working with an unrecognized unit, I want equality
comparison to give correct true/false answers for operands that can be
interpreted as units, so that comparisons against strings and other units behave
predictably.

**Acceptance criteria**

1. WHEN an `UnrecognizedUnit` instance is compared with `==` against a string
   equal to the name it was created from, THEN the comparison SHALL evaluate to
   `True`.
2. WHEN an `UnrecognizedUnit` instance is compared with `==` against another
   `UnrecognizedUnit` carrying the same name, THEN the comparison SHALL evaluate
   to `True`, and WHEN compared against an `UnrecognizedUnit` carrying a
   different name, THEN the comparison SHALL evaluate to `False`.
3. WHEN an `UnrecognizedUnit` instance is compared with `==` against a genuine,
   recognized unit, THEN the comparison SHALL evaluate to `False`, and the
   corresponding `!=` comparison SHALL evaluate to `True`.
4. The system SHALL keep the property that `is_equivalent` on an
   `UnrecognizedUnit` agrees with equality: it SHALL report equivalence for a
   same-named unrecognized unit and non-equivalence for a differently-named one.

## Requirement 3: Comparing a recognized unit with a non-unit operand must not raise

**User story:** As a user comparing ordinary units, I want equality checks
against `None` or unrelated objects to return a sensible boolean, so that
existing code that guards against `None` keeps working.

**Acceptance criteria**

1. WHEN a recognized `UnitBase` instance is compared with `==` against an
   operand that cannot be interpreted as a unit (for example `None`), THEN the
   comparison SHALL complete without raising and SHALL report the objects as not
   equal (i.e. `u.m == None` evaluates to a falsey result).
2. WHEN a recognized `UnitBase` instance is compared with `!=` against an
   operand that cannot be interpreted as a unit (for example `None`), THEN the
   comparison SHALL complete without raising and SHALL evaluate to `True`.
3. IF the lenient interpretation of the other operand fails with an error while
   evaluating equality of a `UnitBase` instance, THEN the comparison SHALL treat
   the comparison as not applicable (deferring to Python's default object
   comparison) rather than allowing the error to propagate to the caller.

## Requirement 4: Preserve existing equality and ordering semantics for genuine units

**User story:** As a maintainer, I want the fix to leave all established unit
comparison behavior intact, so that no existing functionality regresses.

**Acceptance criteria**

1. WHEN two recognized units representing the same physical quantity are
   compared with `==`, THEN the comparison SHALL evaluate to `True`; WHEN two
   recognized units representing different, non-convertible quantities are
   compared with `==`, THEN the comparison SHALL evaluate to `False`.
2. The system SHALL keep the total-ordering behavior of recognized units: WHEN
   convertible units are compared with `<`, `<=`, `>`, or `>=`, THEN the result
   SHALL reflect their relative scale, and WHEN units of non-convertible
   quantities are compared with an ordering operator, THEN a unit conversion
   error SHALL be raised.
3. The system SHALL preserve equality comparison of recognized units against
   equivalent string representations (a unit compared against a string naming
   the same unit SHALL evaluate to `True`).
4. WHEN equality comparison is attempted between a unit and an object of an
   unrelated type, THEN the unit's comparison SHALL either yield a correct
   boolean or defer to the other object's comparison, and SHALL never raise.
