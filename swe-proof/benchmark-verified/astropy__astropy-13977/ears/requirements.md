# Requirements — Quantity ufunc dispatch should defer to foreign operands

## Introduction

`astropy.units.Quantity` participates in NumPy's ufunc protocol through
`Quantity.__array_ufunc__` (in `astropy/units/quantity.py`). When a ufunc — a
unary or binary NumPy universal function, such as the addition (`np.add`) shown
in the issue — is applied to a `Quantity` together with some other object, this
method determines the unit conversions, calls the underlying NumPy machinery,
and re-wraps the result as a `Quantity`.

The problem: NumPy's dispatch treats any operand that exposes a `unit`
attribute as if it were a `Quantity`, and then tries to convert it. When the
foreign operand cannot actually be converted (for example a user-defined
"duck-type" wrapper around a `Quantity`, especially when the two operands carry
equivalent-but-different units), the conversion step raises `TypeError` or
`ValueError`. This aborts the whole operation instead of letting NumPy fall back
to the other operand's own handler (e.g. its reflected operator or its own
`__array_ufunc__`).

Per the NumPy subclassing guidance, `__array_ufunc__` should return the
`NotImplemented` sentinel when it cannot perform the requested operation, so
that another operand gets a chance to handle it. The goal of this change is to
make `Quantity.__array_ufunc__` return `NotImplemented` (rather than propagating
the error) precisely when at least one participating operand supplies its own
ufunc handler — while preserving every existing success and error behavior in
all other cases.

Affected module/function: `Quantity.__array_ufunc__` in
`astropy/units/quantity.py`.

## Requirement 1: Preserve normal ufunc results

**User story:** As a user performing arithmetic and other ufunc operations on
`Quantity` objects, I want the existing correct results to be unchanged, so that
adding this error-recovery behavior does not regress ordinary computations.

**Acceptance criteria**
1. WHEN a ufunc is applied to `Quantity` operand(s) and the operation can be
   carried out (unit determination, any required conversions, the underlying
   computation, and result re-wrapping all succeed), THEN `Quantity.__array_ufunc__`
   SHALL return exactly the value it would have returned before this change.
2. WHEN the completed operation yields a unit-carrying result, THEN the method
   SHALL return that result as a `Quantity` with the correct unit.
3. WHEN the completed operation yields a plain (non-unit) result — for example a
   boolean array from a comparison ufunc — THEN the method SHALL return that
   plain result unchanged rather than wrapping it in a `Quantity`.
4. IF the underlying computation returns `None` (as for the `at` method) or the
   `NotImplemented` sentinel, THEN the method SHALL return that value unchanged.
5. The system SHALL continue to honor a caller-supplied `out=` output argument,
   writing the result into it and returning it, exactly as before this change.
6. WHEN a reduction ufunc is invoked with an `initial=` keyword and a defined
   result unit, THEN the method SHALL continue to convert that initial value to
   the result unit as before.

## Requirement 2: Defer to foreign operands that define their own handler

**User story:** As an author of a class that wraps or mimics `Quantity` and
defines its own `__array_ufunc__`, I want `Quantity` to yield control when it
cannot handle my object, so that my class's reflected operators and ufunc
handler are invoked instead of an exception being raised.

**Acceptance criteria**
1. WHEN a ufunc operation involving a `Quantity` fails with a `TypeError` or a
   `ValueError` during unit determination, conversion, computation, or result
   handling, THEN `Quantity.__array_ufunc__` SHALL inspect every participating
   operand — all inputs together with any supplied output object(s) — before
   deciding how to respond.
2. IF at least one participating operand is of a type that supplies its own
   ufunc handler (i.e. a type whose `__array_ufunc__` is neither absent, nor the
   base `numpy.ndarray` handler, nor `Quantity`'s own handler), THEN the method
   SHALL return the `NotImplemented` sentinel instead of raising, so that the
   other operand's handler or reflected operator can be tried.
3. WHEN a plain `Quantity` is combined via a binary ufunc (arithmetic such as
   the `np.add` of the issue, or a comparison) with an object that defines its
   own `__array_ufunc__`, and the two carry equivalent but differing units, THEN
   the operation SHALL be dispatched to that object's handler and produce the
   same result (including its unit-aware value, or the plain boolean array for a
   comparison) that the handler would produce when given the underlying
   `Quantity` directly, rather than raising.
4. WHEN such a deferred operation is invoked with a pre-allocated output object
   that the foreign operand's handler fills in, THEN the overall operation SHALL
   return that same output object.
5. The deferral behavior SHALL apply regardless of ufunc arity — to unary
   ufuncs (a single operand) as well as to binary ufuncs — whenever a
   participating operand supplies its own ufunc handler and the operation would
   otherwise fail.

## Requirement 3: Preserve genuine errors when no operand can take over

**User story:** As a user who writes an operation that is truly invalid, I want a
clear error rather than a silent `NotImplemented`, so that mistakes are reported
as before.

**Acceptance criteria**
1. IF a ufunc operation fails with a `TypeError` or `ValueError` and none of the
   participating operands supplies its own ufunc handler (every operand defers to
   the default handling — that is, each is absent an override, or is a plain
   `numpy.ndarray`, or is a `Quantity`), THEN `Quantity.__array_ufunc__` SHALL
   re-raise the original exception unchanged.
2. WHEN two `Quantity` operands with physically incompatible units are combined
   by a ufunc that requires matching units, THEN the method SHALL raise the same
   unit-mismatch error as before (it SHALL NOT return `NotImplemented`).
3. WHEN a `Quantity` is combined via a ufunc with an ordinary object that neither
   defines its own ufunc handler nor is convertible to a numeric array (for
   example a plain `dict`), THEN the method SHALL raise `TypeError`, and the
   message SHALL begin by indicating an unsupported operand type for the ufunc in
   question.
4. IF the operation fails with an exception whose type is neither `TypeError` nor
   `ValueError`, THEN the method SHALL let that exception propagate unchanged.

## Requirement 4: Reflected operators become reachable

**User story:** As a user writing `x + q` where `x` is a foreign unit-aware
object and `q` is a `Quantity` with a different-but-equivalent unit, I want the
expression to succeed via `x`'s reflected operator, so that operand order does
not spuriously fail.

**Acceptance criteria**
1. WHEN a binary operation places a `Quantity` on the left and, on the right, an
   object that defines its own ufunc handling, and the `Quantity`-side attempt
   fails only because that object cannot be coerced, THEN the returned
   `NotImplemented` sentinel SHALL allow Python/NumPy to invoke the other
   object's reflected handling and yield a successful result.
