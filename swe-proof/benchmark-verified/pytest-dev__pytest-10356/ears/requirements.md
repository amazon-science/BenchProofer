# Requirements: Consider MRO when collecting marks for classes

## Introduction

pytest lets users attach markers to a test class (e.g. `@pytest.mark.xfail(...)`).
Internally, the marks stored on an object are gathered by the helper
`get_unpacked_marks` in `src/_pytest/mark/structures.py`, which is consumed when
pytest builds the effective set of marks for a class and its tests. Historically
this helper read a single `pytestmark` attribute via ordinary attribute lookup.
Because Python resolves an attribute along a class's method resolution order
(MRO) to the *first* class that defines it, a class that inherits from two
independently-marked base classes only ever saw the marks of one base — the
marks of the other base(s) were silently lost.

The goal is to make mark collection for a class walk the class's full MRO and
gather the marks that each class in that hierarchy stored *itself*, so that a
subclass of multiple marked base classes exposes the marks of all of them. The
helper must also support a mode that returns only the marks applied *directly*
to a class (ignoring inherited ones), and the internal routine that appends a
new mark to an object must use that direct-only mode so that appending a mark
does not accidentally re-materialize inherited marks onto the object. Behavior
for non-class objects (e.g. test functions carrying a `pytestmark` attribute)
must be unchanged.

The affected code is `get_unpacked_marks` and `store_mark` in
`src/_pytest/mark/structures.py`; the unchanged coercion helper is
`normalize_mark_list` in the same module.

## Requirement 1: Gather marks across the full class hierarchy (MRO)

**User story:** As a test author who applies markers on separate base classes,
I want a class that inherits from all of them to carry every base's markers, so
that markers are not silently dropped by multiple inheritance.

**Acceptance criteria**

1. WHEN `get_unpacked_marks` is called with a class and the default
   (full-hierarchy) mode, THEN it SHALL return the marks obtained by visiting
   every class in the target class's MRO, in MRO order, and collecting the marks
   that each visited class stored on itself.
2. WHEN gathering marks along the MRO, THEN the subject SHALL read each class's
   *own* stored `pytestmark` entry (the value defined directly on that class,
   not one merely inherited through attribute lookup), so that each class in the
   hierarchy contributes exactly the marks it declares.
3. WHEN a class in the MRO has no `pytestmark` stored on itself, THEN that class
   SHALL contribute no marks (it SHALL neither raise nor duplicate marks from
   other classes).
4. The system SHALL preserve MRO order in the returned marks: marks from a class
   earlier in the MRO SHALL appear before marks from a class later in the MRO,
   and the target class's own marks SHALL appear first.
5. WHEN two or more classes in the MRO each contribute marks, THEN the subject
   SHALL include the marks from all of them (marks from later-in-MRO classes
   SHALL NOT be omitted or overwritten by earlier ones).
6. WHEN a class in the MRO stored its marks as a single bare mark value rather
   than a list, THEN the subject SHALL treat that value as one contributed mark;
   WHEN it stored a list, THEN each element SHALL be a contributed mark, in list
   order.
7. The system SHALL return the collected marks as a concrete list (a
   materialized sequence that can be compared and indexed directly), with each
   element coerced to a mark object via the existing normalization step.

## Requirement 2: Direct-only mode for a class

**User story:** As a maintainer of pytest's mark machinery, I want to be able to
ask for only the marks applied directly to a class, so that inheritance-aware
collection and direct collection are both available.

**Acceptance criteria**

1. WHEN `get_unpacked_marks` is called with a class and the caller requests only
   directly-applied marks (the non-MRO mode), THEN it SHALL return only the marks
   the target class stored on itself, ignoring any marks contributed by its base
   classes.
2. The system SHALL accept the mode selector as an optional keyword-only
   parameter whose default requests full-hierarchy (MRO-walking) collection, so
   that existing callers that pass only the object continue to get
   inheritance-aware behavior.
3. WHEN the direct-only mode is requested for a class that itself stored no
   marks, THEN the subject SHALL return an empty list.

## Requirement 3: Appending a mark uses direct-only collection

**User story:** As a test author who applies several markers to one class, I
want each applied marker to be appended without pulling in inherited marks, so
that a class's stored marks reflect only what was applied to it.

**Acceptance criteria**

1. WHEN a mark is stored on an object via `store_mark`, THEN the subject SHALL
   compute the object's existing marks using the direct-only (non-MRO) mode and
   SHALL set the object's `pytestmark` to those existing direct marks followed by
   the newly stored mark.
2. IF the object is a class that inherits marks from base classes, THEN storing a
   new mark on it SHALL NOT copy the inherited marks onto the object's own
   `pytestmark`; only the class's own previously-stored marks and the new mark
   SHALL be present in its stored attribute.
3. The system SHALL preserve the order in which marks are applied: a mark applied
   later SHALL appear after marks applied earlier on the same object.

## Requirement 4: Unchanged behavior for non-class objects

**User story:** As a test author who marks test functions, I want function-level
mark collection to behave exactly as before, so that this change does not alter
existing test behavior.

**Acceptance criteria**

1. WHEN `get_unpacked_marks` is called with an object that is not a class, THEN
   it SHALL read the object's `pytestmark` attribute via ordinary attribute
   lookup and return its normalized marks, exactly as it did previously.
2. IF a non-class object's `pytestmark` is a single value rather than a list,
   THEN the subject SHALL treat it as a one-element mark sequence.
3. IF a non-class object has no `pytestmark` attribute, THEN the subject SHALL
   return an empty result.

## Requirement 5: Preserve existing mark-inheritance and normalization behavior

**User story:** As a pytest user relying on established marker semantics, I want
all previously-working marker inheritance and normalization to keep working, so
that this fix does not regress existing behavior.

**Acceptance criteria**

1. The system SHALL keep coercing each collected entry to a mark object via the
   existing normalization step, and SHALL raise a `TypeError` if an entry cannot
   be resolved to a mark object.
2. The system SHALL keep the established single-inheritance behavior whereby a
   subclass carries the marks of its (single-chain) base classes.
3. The system SHALL keep the behavior that a mark applied to a subclass does not
   propagate onto its base class.
4. The system SHALL keep the behavior that a mark applied to one class does not
   leak onto an unrelated sibling class.
5. The system SHALL keep merging marks from multiple base classes in a way that
   preserves the closeness/ordering used to resolve the effective mark for a
   test.
6. WHEN a class is collected more than once during test collection, THEN its
   marks SHALL remain stable and SHALL NOT be duplicated or grow across repeated
   collection.
