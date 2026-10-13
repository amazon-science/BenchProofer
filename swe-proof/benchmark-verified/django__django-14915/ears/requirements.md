# Requirements: Make model-choice iterator values usable as mapping keys and set members

## Introduction

When a model-backed choice field renders its options, each option's value is
delivered to widget code as an instance of `ModelChoiceIteratorValue` (defined
in `django/forms/models.py`). This wrapper bundles the plain underlying choice
value together with the model object the option was produced from, while
comparing equal to the plain value via its `__eq__` method.

User code that customizes option rendering commonly tests such a value for
membership in a Python mapping or set — for example
`if value in {1: [...]}` or `if value in {1, 2}`. In Python, membership testing
against a `dict` or `set` requires the left-hand object to be *hashable*.
`ModelChoiceIteratorValue` defines `__eq__` but historically did not define a
compatible hash, which (per Python's data model) makes instances unhashable.
Consequently these membership checks raise `TypeError: unhashable type:
'ModelChoiceIteratorValue'`, a regression from earlier Django versions where the
option value was the plain value itself.

The goal is to make `ModelChoiceIteratorValue` hashable in a way that is
consistent with its equality semantics — the wrapper's hash must be derived from
the wrapped plain value alone — while preserving all existing wrapping,
stringification, and equality behavior.

## Requirement 1: The iterator value wrapper is hashable

**User story:** As a developer customizing choice-field option rendering, I want
the value passed to my widget code to be usable as a dictionary key or set
member, so that I can look up per-value metadata (e.g. `value in {1: [...]}`)
without a `TypeError`.

**Acceptance criteria**

1. The `ModelChoiceIteratorValue` class SHALL be hashable: obtaining the hash of
   any instance SHALL succeed rather than raising `TypeError`.
2. WHEN an instance of `ModelChoiceIteratorValue` is used as the left-hand
   operand of a membership test against a `dict`, THEN the operation SHALL
   complete without raising `TypeError: unhashable type`.
3. WHEN an instance of `ModelChoiceIteratorValue` is used as the left-hand
   operand of a membership test against a `set`, THEN the operation SHALL
   complete without raising `TypeError: unhashable type`.
4. WHEN an instance of `ModelChoiceIteratorValue` is inserted into a `dict` as a
   key or added to a `set`, THEN the operation SHALL succeed.

## Requirement 2: Hash is a deterministic function of the wrapped value alone

**User story:** As a developer, I want the wrapper's hash to be consistent with
its equality behavior, so that membership tests and dictionary lookups behave
intuitively with respect to the underlying plain value.

**Acceptance criteria**

1. WHEN the hash of a `ModelChoiceIteratorValue` instance is computed, THEN it
   SHALL equal the hash of the wrapped underlying value that the instance was
   constructed with.
2. The wrapper's hash SHALL depend only on the wrapped underlying value and
   SHALL NOT depend on the accompanying model object.
3. IF two `ModelChoiceIteratorValue` instances wrap underlying values that are
   equal (and thus hash equal), THEN their hashes SHALL be equal, regardless of
   the model objects they were built from.
4. WHEN the hash of a `ModelChoiceIteratorValue` instance is computed more than
   once for an unchanged wrapped value, THEN it SHALL return the same result
   each time (deterministic).
5. The hashing behavior SHALL be consistent with the existing equality behavior:
   because an instance compares equal to its own plain wrapped value, its hash
   SHALL match that value's hash so that a mapping keyed by the plain value can
   be probed with the wrapper.

## Requirement 3: Existing wrapping, stringification, and equality behavior are preserved

**User story:** As a maintainer, I want the change to add hashability without
altering any other observable behavior of the wrapper, so that existing option
rendering, comparisons, and value access continue to work unchanged.

**Acceptance criteria**

1. The `ModelChoiceIteratorValue` wrapper SHALL keep exposing the underlying
   plain value and the accompanying model object it was constructed with.
2. WHEN a `ModelChoiceIteratorValue` instance is converted to a string, THEN the
   result SHALL keep being the string form of the wrapped underlying value.
3. WHEN a `ModelChoiceIteratorValue` instance is compared for equality with a
   plain value, THEN it SHALL keep comparing equal exactly when the wrapped
   underlying value equals that plain value.
4. WHEN a `ModelChoiceIteratorValue` instance is compared for equality with
   another `ModelChoiceIteratorValue`, THEN it SHALL keep comparing equal
   exactly when their wrapped underlying values are equal.
5. The system SHALL keep producing `ModelChoiceIteratorValue`-wrapped values when
   iterating a model choice field's choices, so that option-rendering code
   receives the wrapper as before.
6. The rendering of choice-field options, including any custom per-option
   attributes computed by widget code, SHALL keep producing the same option
   context and markup it did before, aside from no longer raising `TypeError`
   for mapping/set membership tests on option values.
