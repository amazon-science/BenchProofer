# Requirements: Relative complement of a finite set with undetermined membership

## Introduction

In SymPy's set algebra (`sympy/sets/sets.py`), the relative complement
`Complement(other, self)` — equivalently `other - self` — is computed by
`Set._complement(self, other)`. When `other` is a `FiniteSet`, the complement is
formed by testing each element of `other` for membership in `self` (via
`self.contains(el)`) and deciding whether that element survives the difference.

The membership test `Set.contains` is three-valued: for a concrete element it
may return a definite `True` or `False`, but for an element whose membership
cannot be decided (for example a free `Symbol` tested against a numeric
`Interval`, or an element tested against a `ComplexRegion`) it returns neither —
it yields a symbolic/unevaluated result.

The defect: the `FiniteSet` branch retained every element whose membership test
was *not exactly* the sentinel `True`, thereby lumping "definitely not a member"
together with "membership undetermined". As a result, elements of undetermined
membership were silently asserted to lie outside `self` and dropped from any
unevaluated remainder. Concretely, the complement of a finite set holding two free symbols and a number
inside a numeric interval, taken against that interval, returned just the two
symbols — asserting they are outside the interval — when the correct result must
keep those symbols in an unevaluated difference against the interval.

The goal is to make the `FiniteSet` branch classify each element by a
three-valued membership outcome and assemble the result so that undetermined
elements remain in an unevaluated complement rather than being treated as
confirmed non-members.

## Requirement 1: Three-valued classification of finite-set elements

**User story:** As a user computing a relative complement of a finite set, I
want elements whose membership is undecidable to be kept in an unevaluated
difference, so that the result never asserts a fact about membership that SymPy
cannot actually determine.

**Acceptance criteria**

1. WHEN `Set._complement(self, other)` is evaluated with `other` a `FiniteSet`,
   THEN the system SHALL classify each element `el` of `other` by the outcome of
   `self.contains(el)` into exactly one of three groups: definite member
   (result is boolean-true), definite non-member (result is boolean-false), or
   undetermined (result is neither boolean-true nor boolean-false).
2. WHEN an element of `other` has a definite-member outcome, THEN the system
   SHALL exclude that element from the result entirely (it appears in no part of
   the returned set).
3. WHEN an element of `other` has a definite-non-member outcome, THEN the system
   SHALL retain that element as an explicit member of the resulting difference.
4. IF an element of `other` has an undetermined membership outcome, THEN the
   system SHALL retain that element only inside an unevaluated relative
   complement against `self`, and SHALL NOT place it among the explicitly
   confirmed members.
5. The system SHALL treat only a genuinely boolean-true membership result as
   "definite member"; a symbolic or otherwise non-boolean result SHALL NOT be
   interpreted as membership.

## Requirement 2: Assembly of the complement result

**User story:** As a user, I want the complement result to combine the confirmed
non-members and the undetermined elements into a single well-formed set, so that
downstream operations see a correct representation.

**Acceptance criteria**

1. WHEN at least one element is undetermined, THEN the system SHALL return the
   union of a finite set of the confirmed non-members with an unevaluated
   relative complement of the finite set of undetermined elements against
   `self`.
2. WHEN no element is undetermined, THEN the system SHALL return simply the
   finite set of the confirmed non-members (with no residual unevaluated
   complement term).
3. WHEN every element of `other` is a definite member, THEN the system SHALL
   return the empty set.
4. The system SHALL preserve the standard canonical form of a `FiniteSet` for
   the confirmed non-members (duplicate removal and ordering as SymPy normally
   applies), independent of the order in which `other`'s elements were iterated.
5. WHEN the complement of a finite set containing two free symbols together with
   a number that lies strictly inside a numeric interval is taken against that
   interval, THEN the system SHALL remove the interior number and SHALL yield a
   value equal to the unevaluated complement, against the same interval, of the
   finite set consisting of just the two symbols.

## Requirement 3: Preservation of existing complement behavior

**User story:** As a maintainer, I want the fix to leave all previously correct
complement, difference, and set-relation behavior intact, so that no regression
is introduced.

**Acceptance criteria**

1. WHEN `other` is a finite set every element of which is a definite non-member
   of `self`, THEN the system SHALL return a finite set equal to `other`
   unchanged.
2. WHEN `other` is a finite set every element of which is a definite member of
   `self`, THEN the system SHALL return the empty set.
3. The system SHALL keep the existing results for complements whose second
   operand is not a finite set — including intervals against the reals, unions,
   nested complements, product sets, and the empty set — unchanged from prior
   behavior.
4. The system SHALL keep unchanged the behavior of related set operations that
   depend on relative complement, including difference (`-`), symmetric
   difference, intersection, union, and subset/superset/disjointness queries.
5. WHEN a finite-set complement produces no residual unevaluated term and no
   surviving elements, THEN the system SHALL return the empty set rather than an
   empty unevaluated complement.
