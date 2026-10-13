# Requirements: allow non-disjoint cycles in the `Permutation` constructor

## Introduction

The `Permutation` class in `sympy/combinatorics/permutations.py` can be
constructed from *cyclic form* — a list of cycles, where each inner list such as
`[a0, a1, ..., ak]` denotes the rule sending `a0 -> a1 -> ... -> ak -> a0` and
leaving every other point fixed. Historically the constructor rejected any
cyclic-form argument in which a point appeared in more than one cycle (i.e. the
cycles were *non-disjoint*), raising a `ValueError` about repeated elements.

This restriction is unnecessary. Non-disjoint cycles have a well-defined
meaning: the listed cycles are simply applied in left-to-right order (the first
cycle first), chaining through any point that appears in several of them. For
example, `Permutation([[0, 1], [0, 1]])` should compose the transposition
`(0 1)` with itself and yield the identity. More generally, when cycles overlap,
a point moved by an earlier cycle may be carried onward by a later cycle, so the
overall mapping can join points across cycles into a single longer orbit.

The goal is to make the constructor accept non-disjoint cyclic input and return
the permutation obtained by left-to-right composition of the cycles, while
preserving every other constructor behavior — in particular the rejection of
repeated elements in *array form* input, and the existing handling of size,
singletons, and malformed arguments. The affected code is the `Permutation`
class constructor (`Permutation.__new__`) in
`sympy/combinatorics/permutations.py`, which builds the array form of a
permutation from its arguments.

## Requirement 1: Accept non-disjoint cycles and compose them

**User story:** As a user constructing permutations from cyclic notation, I want
to pass cycles that share points, so that I can describe a permutation as a
product of cycles without pre-computing whether they are disjoint.

**Acceptance criteria**

1. WHEN the `Permutation` constructor is called with cyclic-form input (a list
   of lists of integers) in which some point occurs in more than one cycle, THEN
   the constructor SHALL return a `Permutation` object rather than raising an
   error.
2. WHEN cyclic-form input contains repeated points across cycles, THEN the
   constructor SHALL interpret the cycles as applied in left-to-right order (the
   first-listed cycle applied first, then the next to that result, and so on).
3. WHEN the constructor is given a list of cycles that together represent the
   identity mapping on the named points (for example a transposition followed by
   the same transposition), THEN the resulting permutation SHALL be equal to the
   identity permutation on those points.
4. WHEN the constructor is given two or more overlapping cycles, THEN the
   resulting permutation SHALL equal the single permutation obtained by composing
   those cycles in left-to-right order, and in particular SHALL equal the
   permutation built by any other supported route that applies the same cycles in
   the same order (for example the product of the same cycles constructed
   separately).
5. The resulting permutation's array form SHALL have one entry per point from
   `0` up to the largest point named in any cycle, and its `i`-th entry SHALL be
   the image of `i` under the left-to-right composition of all the cycles.

## Requirement 2: Preserve rejection of repeated elements in array form

**User story:** As a user, I want array-form input that is not a valid
permutation to still be rejected, so that malformed permutations are caught
early.

**Acceptance criteria**

1. WHEN the constructor is given array-form input (a flat list of integers, not
   a list of lists) that contains a repeated element, THEN the constructor SHALL
   raise a `ValueError`.
2. IF array-form input is rejected for containing a repeated element, THEN the
   raised error message SHALL state that there were repeated elements.
3. The constructor SHALL continue to raise a `ValueError` for array-form input
   that omits a required point (i.e. when the entries are not exactly the
   integers `0` through `n-1` for `n` entries).

## Requirement 3: Preserve existing cyclic-form and argument handling

**User story:** As a user relying on the constructor's existing behaviors, I want
all previously supported forms to keep working unchanged, so that this change
introduces no regressions.

**Acceptance criteria**

1. WHEN the constructor is given cyclic-form input with a `size` argument larger
   than the largest named point plus one, THEN the resulting permutation SHALL
   be extended with fixed points up to that size.
2. WHEN the constructor is given cyclic-form input, THEN points not named in any
   cycle SHALL be treated as fixed (mapped to themselves), and singleton cycles
   need not be listed except to indicate a larger maximum point.
3. WHEN the constructor is called with several separate cycle arguments (cycles
   passed as distinct positional arguments rather than one list of lists), THEN
   it SHALL build the permutation from the product of those cycles, unaffected by
   this change.
4. IF the constructor is given a malformed argument that mixes an integer with a
   sequence at the same level (a list whose elements are not uniformly sequences
   or uniformly integers), THEN it SHALL raise a `ValueError`.
5. The constructor SHALL preserve equality, multiplication, cyclic-form
   conversion, ranking, and printing behavior of the permutations it produces, so
   that permutations built from non-disjoint cycles behave identically to
   permutations built by any other supported route that yields the same mapping.
