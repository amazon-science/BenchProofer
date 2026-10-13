# Requirements: Reverse enumeration of `OrderedSet`

## Introduction

`OrderedSet` in `django/utils/datastructures.py` is a set that preserves the
insertion order of its distinct elements. It already supports forward
enumeration (iterating yields elements in insertion order), membership tests,
length, truthiness, and element addition/removal. It does not, however, support
being passed to Python's built-in `reversed()`: because it defines no reverse
enumeration protocol, `reversed(an_ordered_set)` fails.

Because the collection is inherently ordered, it is natural for it to also be
enumerable in the opposite direction. The goal is to allow `reversed()` to be
called on an `OrderedSet` so that it yields the collection's elements in reverse
insertion order, without disturbing the existing forward-enumeration behavior or
any other behavior of `OrderedSet` and the surrounding data structures in
`django/utils/datastructures.py`.

## Requirement 1: Support reverse enumeration of an OrderedSet

**User story:** As a developer using `OrderedSet`, I want to call `reversed()` on
an instance, so that I can enumerate its elements from last-inserted to
first-inserted just as easily as I can enumerate them forward.

**Acceptance criteria**

1. WHEN `reversed()` is called on an `OrderedSet` instance, THEN `OrderedSet`
   SHALL return an object that enumerates the instance's elements without raising
   an error.
2. WHEN the object produced by calling `reversed()` on an `OrderedSet` is
   consumed, THEN it SHALL yield exactly the elements currently contained in the
   set, each exactly once, with no elements added or omitted.
3. WHEN the object produced by calling `reversed()` on an `OrderedSet` is
   consumed, THEN the elements SHALL be produced in the exact reverse of the
   set's insertion (forward-enumeration) order: the first element produced SHALL
   be the most recently inserted element, the second SHALL be the next-most
   recently inserted, and so on, so that the k-th element produced is the
   element at forward position (n − 1 − k) for a set of n elements.
4. The system SHALL ensure that, for any `OrderedSet`, the sequence obtained by
   consuming the result of `reversed()` equals the reverse of the sequence
   obtained by ordinary forward iteration over the same set.
5. WHEN an `OrderedSet` is empty, THEN calling `reversed()` on it SHALL produce
   an object that yields no elements.

## Requirement 2: The reverse enumerator is a one-shot iterator

**User story:** As a developer, I want the result of `reversed()` on an
`OrderedSet` to behave like a standard reverse iterator, so that it composes with
code that expects the iterator protocol.

**Acceptance criteria**

1. WHEN `reversed()` is called on an `OrderedSet`, THEN the returned object SHALL
   be an iterator (an instance of the standard iterator protocol, i.e. it is
   recognized as `collections.abc.Iterator`).
2. WHEN the object returned by `reversed()` on an `OrderedSet` has been fully
   consumed once, THEN it SHALL be exhausted and SHALL NOT re-yield the elements
   on a subsequent traversal of that same object.
3. WHEN `reversed()` is called on an `OrderedSet`, THEN producing and consuming
   the returned iterator SHALL NOT modify the `OrderedSet`: its contents, its
   forward-enumeration order, and its length SHALL be unchanged afterward.

## Requirement 3: Preserve existing OrderedSet behavior

**User story:** As a maintainer, I want the existing behavior of `OrderedSet` to
remain intact, so that adding reverse enumeration does not regress current
functionality.

**Acceptance criteria**

1. The system SHALL keep forward enumeration of an `OrderedSet` yielding its
   elements in insertion order.
2. The system SHALL keep constructing an `OrderedSet` from an iterable so that it
   retains each distinct element once, in first-insertion order.
3. WHEN membership of an item in an `OrderedSet` is tested, THEN the system SHALL
   report whether that item is contained in the set.
4. The system SHALL keep reporting the number of distinct elements of an
   `OrderedSet` as its length, and SHALL keep reporting an `OrderedSet` as truthy
   when it is non-empty and falsy when it is empty.
5. The system SHALL keep supporting adding an element to, removing an element
   from, and discarding an element from an `OrderedSet` with their existing
   semantics.

## Requirement 4: Preserve the surrounding data structures

**User story:** As a maintainer, I want the other data structures defined
alongside `OrderedSet` to keep working, so that this addition is fully isolated.

**Acceptance criteria**

1. The system SHALL keep the existing behavior of the other data structures
   defined in `django/utils/datastructures.py` (including the multi-value
   dictionary, the case-insensitive mapping, the immutable list, and the
   dictionary wrapper), including their construction, access, update, copying,
   pickling, representation, and error-raising behavior.
