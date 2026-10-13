# Requirements: Correct `__repr__` for repeated cross-validators

## Introduction

In `sklearn.model_selection`, the repeated cross-validator classes
`RepeatedKFold` and `RepeatedStratifiedKFold` (both subclasses of the internal
base `_RepeatedSplits` in `sklearn/model_selection/_split.py`) do not produce a
readable string representation. Calling `repr()` on an instance returns the
default Python object representation (e.g.
`<sklearn.model_selection._split.RepeatedKFold object at 0x...>`) instead of a
parameter-listing form comparable to other scikit-learn estimators and
cross-validators (e.g. `RepeatedKFold(n_repeats=10, n_splits=5,
random_state=None)`).

The root cause is twofold: the shared base class exposes no `__repr__`, and the
helper that renders estimator representations (`_build_repr` in the same module)
reads each constructor parameter as a direct instance attribute — but these
repeated cross-validators store their wrapped-splitter parameters (such as
`n_splits`) inside a `cvargs` mapping rather than as top-level attributes, so
those parameters render as `None`.

The goal is that `repr()` of these classes yields a faithful, human-readable
representation naming the class and its constructor parameters with their
configured values, without regressing the representation of any other object
that uses the shared helper.

## Requirement 1: Human-readable representation for repeated cross-validators

**User story:** As a user of scikit-learn, I want `repr()` of a `RepeatedKFold`
or `RepeatedStratifiedKFold` instance to describe the object and its
configuration, so that I can inspect and debug cross-validation setups.

**Acceptance criteria**

1. WHEN `repr()` is called on a `RepeatedKFold` instance, THEN the system SHALL
   return a string beginning with the class name `RepeatedKFold` immediately
   followed by a parenthesized parameter list, and SHALL NOT return the default
   Python object representation (no memory-address / `object at 0x...` form).
2. WHEN `repr()` is called on a `RepeatedStratifiedKFold` instance, THEN the
   system SHALL return a string beginning with the class name
   `RepeatedStratifiedKFold` immediately followed by a parenthesized parameter
   list, and SHALL NOT return the default Python object representation.
3. The returned string SHALL list the constructor parameters `n_repeats`,
   `n_splits`, and `random_state`, each rendered as `name=value`, separated by
   `, `, and enclosed in a single pair of parentheses.
4. The parameters in the returned string SHALL appear in ascending
   alphabetical order of their names (i.e. `n_repeats`, then `n_splits`, then
   `random_state`).
5. WHEN an instance is constructed with explicit values for `n_splits` and
   `n_repeats`, THEN the representation SHALL show exactly those configured
   integer values for the corresponding parameters.
6. WHEN `random_state` is left at its default, THEN the representation SHALL
   show `random_state=None`.
7. The rendered value for each parameter SHALL reflect the instance's actual
   configuration and SHALL NOT be substituted by `None` when the parameter's
   value is available on the object.

## Requirement 2: Resolve parameters stored on the wrapped-splitter arguments

**User story:** As a maintainer, I want the shared representation helper to find
parameter values even when a class stores some constructor arguments in its
`cvargs` mapping, so that composite cross-validators report their true settings.

**Acceptance criteria**

1. WHEN the representation helper resolves a constructor parameter and the
   object has no matching direct attribute (the direct lookup yields `None`),
   IF the object exposes a `cvargs` mapping containing that parameter name,
   THEN the helper SHALL use the value from `cvargs` for that parameter.
2. WHEN a repeated cross-validator stores `n_splits` inside its `cvargs`
   mapping, THEN the representation SHALL report the stored `n_splits` value
   rather than `None`.
3. IF a parameter value is genuinely `None` and absent from `cvargs`, THEN the
   helper SHALL render it as `None`.

## Requirement 3: Preserve existing representation behavior for other objects

**User story:** As a maintainer, I want the change to be non-disruptive, so that
every other estimator and splitter keeps its current representation.

**Acceptance criteria**

1. The system SHALL continue to derive the listed parameters from the class
   constructor signature (excluding `self` and variadic keyword parameters).
2. The system SHALL continue to omit parameters whose current value triggers a
   `DeprecationWarning` when accessed.
3. WHILE rendering an object that stores all of its constructor parameters as
   direct attributes, the system SHALL produce the same representation as
   before (the `cvargs` fallback SHALL only apply when the direct attribute
   lookup yields `None`).
4. The system SHALL keep the constructors and public parameters of
   `RepeatedKFold` and `RepeatedStratifiedKFold` unchanged (`n_splits`,
   `n_repeats`, `random_state`), and SHALL keep their splitting and
   split-counting behavior unchanged.
