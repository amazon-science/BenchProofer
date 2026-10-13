# Requirements: Deconstruction of `Q` filter objects

## Introduction

`django.db.models.Q` objects (implemented in `django/db/models/query_utils.py`,
class `Q`, method `deconstruct`) encapsulate query filters that can be combined
logically. `deconstruct` returns a `(path, args, kwargs)` triple used for
serialization (e.g. migrations, pickling) so that `Q(*args, **kwargs)` recreates
an equivalent object.

Historically `deconstruct` special-cased a `Q` holding exactly one child that is
not itself a `Q`: it assumed that child was a length-2 key/value pair and
inlined it into `kwargs`. That assumption breaks when the single child is a
standalone conditional expression (such as an `Exists` object), which is not
subscriptable — attempting `child[0]` raises `TypeError: 'Exists' object is not
subscriptable`. Because `Q.__init__` and internal combination (`_combine`) pass
conditional expressions to `Q` and round-trip through `deconstruct`, this also
makes combining such a `Q` with an empty `Q` crash.

The goal is to make `deconstruct` handle every child uniformly: place all
children positionally into `args`, and reserve `kwargs` for the connector and
negation flags only. This removes the crash, makes the representation
consistent, and preserves round-trip reconstruction.

## Requirement 1: Uniform positional deconstruction of children

**User story:** As a developer serializing query filters, I want `Q.deconstruct`
to represent a filter's children consistently, so that any filter — including
those built from conditional expressions — can be deconstructed and rebuilt
without special-case failures.

**Acceptance criteria**

1. WHEN `deconstruct` is called on a `Q` object, THEN the method SHALL place all
   of the object's children, in their stored order, into the returned positional
   `args` tuple.
2. WHEN `deconstruct` is called on a `Q` object, THEN the returned `kwargs`
   mapping SHALL NOT contain any inlined key/value lookup entry derived from a
   child.
3. WHEN a `Q` object holds exactly one child that is a key/value lookup pair
   (e.g. built as `Q(x=1)`), THEN `deconstruct` SHALL return that child as a
   single `(lookup, value)` length-2 tuple inside `args` and SHALL return an
   empty `kwargs` (apart from connector/negation entries described in
   Requirements 3 and 4) — i.e. the single-child lookup SHALL NOT be inlined
   into `kwargs`.
4. WHEN a `Q` object holds two or more key/value lookup children, THEN
   `deconstruct` SHALL return all of them as length-2 tuples inside `args` in
   their stored order.
5. The system SHALL return the same import `path` as before, namely
   `'django.db.models.Q'` for the standard `Q` class (rewriting a
   `django.db.models.query_utils` module prefix to `django.db.models`).

## Requirement 2: Support standalone conditional-expression children

**User story:** As a developer, I want to wrap a conditional expression such as
`Exists(...)` in a `Q` object and deconstruct it, so that queries built from
boolean expressions can be serialized and combined without crashing.

**Acceptance criteria**

1. WHEN `deconstruct` is called on a `Q` object whose single child is a
   standalone conditional expression (e.g. `Q(Exists(queryset))`), THEN the
   method SHALL NOT raise a `TypeError` (or any other error) from attempting to
   subscript that child.
2. WHEN `deconstruct` is called on a `Q` object whose single child is a
   conditional expression, THEN the method SHALL return that expression object
   itself as the sole element of `args` and SHALL return an empty `kwargs`
   (apart from connector/negation entries).
3. IF a `Q` object holds a single child that is itself a `Q` object (a nested
   filter), THEN `deconstruct` SHALL return that nested `Q` as the sole element
   of `args` and SHALL return an empty `kwargs`.

## Requirement 3: Preserve connector reporting

**User story:** As a developer, I want the logical connector to be reported only
when it is non-default, so that reconstructed objects use the correct
combination semantics.

**Acceptance criteria**

1. WHEN the `Q` object's connector equals the default connector (AND), THEN
   `deconstruct` SHALL NOT include a `_connector` entry in `kwargs`.
2. IF the `Q` object's connector differs from the default (i.e. it is OR), THEN
   `deconstruct` SHALL include a `_connector` entry in `kwargs` carrying that
   connector value.

## Requirement 4: Preserve negation reporting

**User story:** As a developer, I want negated filters to be marked as negated in
their deconstruction, so that reconstruction reproduces the negation.

**Acceptance criteria**

1. IF the `Q` object is negated, THEN `deconstruct` SHALL include a `_negated`
   entry set to `True` in the returned `kwargs`.
2. WHEN the `Q` object is not negated, THEN `deconstruct` SHALL NOT include a
   `_negated` entry in `kwargs`.
3. WHEN a negated `Q` object holds a single key/value lookup child, THEN
   `deconstruct` SHALL return that child as a length-2 tuple inside `args` while
   still marking `_negated` as `True` in `kwargs`.

## Requirement 5: Round-trip reconstruction

**User story:** As a developer, I want a deconstructed `Q` object to be
faithfully rebuildable, so that serialized filters remain equivalent to the
originals.

**Acceptance criteria**

1. WHEN a `Q` object is deconstructed into `(path, args, kwargs)`, THEN
   rebuilding it as `Q(*args, **kwargs)` SHALL produce a `Q` object equal to the
   original, for filters using AND, OR, and negation.
2. The system SHALL keep combining a `Q` object with an empty `Q` object (via
   `&` or `|`, in either order) working without error, including when one operand
   wraps a conditional expression, and SHALL yield a combined filter that selects
   the same rows as the non-empty operand alone.
3. The system SHALL keep a queryset filtered with a `Q` wrapping a conditional
   expression (e.g. `Q(Exists(...))`) picklable and unpicklable, such that the
   unpickled queryset returns the same results as the original.
