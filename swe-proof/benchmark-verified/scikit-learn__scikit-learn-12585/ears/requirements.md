# Requirements: `clone` must tolerate estimator *classes* as parameter values

## Introduction

`sklearn.base.clone(estimator, safe=True)` constructs a fresh estimator that
carries the same parameters as the input, without copying any fitted data. It
recurses into an estimator's parameters (obtained via `get_params(deep=False)`)
and clones each one.

When a parameter value is an estimator **class** (a type object such as
`StandardScaler`) rather than an estimator **instance**, cloning currently
fails: the class advertises a `get_params` attribute (it is defined on the
class), so `clone` treats it as an estimator and calls `get_params(deep=False)`
as an unbound method, which raises `TypeError: get_params() missing 1 required
positional argument: 'self'`.

The affected code is the `clone` function in `sklearn/base.py`. The goal is to
make `clone` recognize that a value which is itself a type (a class object)
must not be treated as an estimator instance to introspect, and must instead be
handled on the non-estimator path. This must not disturb any of `clone`'s
existing behavior for instances, containers, and non-estimator leaf values.

## Requirement 1: Clone parameters that are estimator classes

**User story:** As a developer who stores estimator classes (not instances) as
parameters of a wrapper estimator, I want `clone` to succeed on such an
estimator, so that my wrapper can be cloned like any other estimator.

**Acceptance criteria**

1. WHEN `clone` is applied to an estimator one of whose parameters is a value
   that is itself a type (a class object, whether or not that class defines a
   `get_params` attribute), THEN `clone` SHALL complete without raising.
2. WHEN a parameter value is a type, THEN `clone` SHALL NOT attempt to call
   `get_params` on that value as if it were an estimator instance, and SHALL
   NOT raise a `TypeError` about a missing `self` argument.
3. WHEN cloning recurses into such a class-valued parameter (which occurs with
   the non-safe recursion used for parameter values), THEN the value produced
   for that parameter SHALL be the identical class object (the same object by
   identity as the original parameter value).
4. WHEN the enclosing estimator is cloned, THEN in the resulting estimator that
   parameter SHALL be the same class object as in the source estimator, so that
   an identity comparison between the source parameter and the cloned parameter
   holds.

## Requirement 2: Type values are routed to the non-estimator path

**User story:** As a maintainer, I want a value that is a type to follow the
same handling path as any value that is not a scikit-learn estimator, so that
the behavior is consistent and predictable.

**Acceptance criteria**

1. The system SHALL treat any value that is a type as *not* a cloneable
   estimator, regardless of whether that type exposes a `get_params` attribute.
2. IF `clone` is called with `safe=False` on a value that is a type, THEN
   `clone` SHALL return that value via a fallback copy (for a class object this
   yields the identical class object) rather than introspecting its parameters.
3. IF `clone` is called with `safe=True` on a top-level value that is a type,
   THEN `clone` SHALL raise a `TypeError` reporting that the object does not
   appear to be a scikit-learn estimator, exactly as it already does for other
   non-estimator values under `safe=True`.

## Requirement 3: Preserve existing clone behavior (regression protection)

**User story:** As a user of scikit-learn, I want all existing `clone`
behaviors to remain unchanged, so that the fix introduces no regressions.

**Acceptance criteria**

1. WHEN `clone` is applied to an estimator instance, THEN it SHALL return a new
   estimator of the same class whose `get_params(deep=False)` values equal the
   originals, while parameter *values* that are themselves estimators are
   cloned to new (non-identical) instances and non-estimator parameter values
   (e.g. numbers, strings, arrays) are preserved.
2. WHEN `clone` is applied to a `list`, `tuple`, `set`, or `frozenset` of
   estimators, THEN it SHALL return a container of the same kind whose elements
   are the clones of the originals, cloned element-wise.
3. WHEN a parameter is a NumPy array (or a sparse matrix), THEN `clone` SHALL
   produce an equal-valued copy, and WHEN a parameter is `NaN` or an empty
   array, THEN cloning SHALL succeed with equal values preserved.
4. IF an estimator's constructor does not set, or modifies, a parameter such
   that the re-read parameter is not identical to the value passed in, THEN
   `clone` SHALL raise a `RuntimeError` reporting that the object cannot be
   cloned because its constructor does not set or modifies that parameter.
5. WHEN `clone` is called with `safe=True` on a non-estimator value that is not
   a type (e.g. a plain object lacking `get_params`), THEN it SHALL raise a
   `TypeError`; and WHEN called with `safe=False` on such a value, THEN it
   SHALL return a deep copy of the value.
6. WHEN a value is neither a type nor a container of the recognized kinds, THEN
   `clone` SHALL route it exactly as before this change: an estimator instance
   (any value exposing a callable, bound `get_params`) is still introspected and
   rebuilt, and a non-estimator leaf is still handled on the non-estimator path.
   The only behavioral change SHALL be the added routing of type (class) values
   to the non-estimator path; no other input class SHALL change how `clone`
   treats it.
