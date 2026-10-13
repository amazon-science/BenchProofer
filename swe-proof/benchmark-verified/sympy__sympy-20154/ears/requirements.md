# Requirements: independent partition dictionaries from `partitions()`

## Introduction

The `partitions()` generator in `sympy/utilities/iterables.py` yields, for a
positive integer `n` (with optional bounds `m` on the number of parts and `k`
on the largest part, and an optional `size` flag), the integer partitions of
`n`. Each partition is represented as a dictionary mapping a part value to its
multiplicity (e.g. the partition "three 2's" is `{2: 3}`).

For performance the generator historically maintained a single working
dictionary, mutated it in place between steps, and handed out that *same*
dictionary object at every step. As a consequence, any consumer that retained
more than one yielded value at a time — the common `list(partitions(...))`, a
list comprehension, de-duplication, or storing partitions for later use — ended
up holding several references to one object whose contents reflected only the
*final* partition. This produced results that look wrong (e.g. every element of
the materialized list equal to the last partition) and caused subtle bugs.

The goal is to make each yielded partition an independent object, so that
collecting or retaining yielded values reflects the partition that was current
at the moment of yielding, while preserving every existing aspect of which
partitions are generated, their contents, and their order.

## Requirement 1: Yielded partitions are independent snapshots

**User story:** As a caller of `partitions()`, I want each yielded partition to
be an independent object, so that collecting or retaining yielded values gives
the actual sequence of partitions rather than repeated copies of the last one.

**Acceptance criteria**

1. WHEN a caller iterates `partitions(n, m, k)` (with `size` defaulting to the
   partition-only form) and retains every yielded value, THEN `partitions`
   SHALL provide a distinct dictionary object at each step such that retaining
   all of them preserves each step's partition contents independently.
2. WHEN a caller materializes the generator with `list(partitions(n, m, k))` or
   an equivalent comprehension that keeps every yielded value, THEN the
   resulting list SHALL contain, in order, one entry per generated partition,
   each entry equal to the partition that was current at that step.
3. IF two or more generated partitions differ, THEN the materialized list of
   all yielded values SHALL contain the correspondingly differing dictionaries
   and SHALL NOT collapse to repeated copies of a single (e.g. the final)
   partition.
4. WHEN a caller feeds the yielded partitions through order-preserving
   de-duplication that compares yielded values, THEN consecutive distinct
   partitions SHALL be reported as distinct (equal partitions being treated as
   duplicates), reflecting the true generated sequence rather than a single
   repeated object.
5. WHEN a caller mutates or stores one yielded partition, THEN subsequent
   yielded values SHALL be unaffected, i.e. distinct yields SHALL NOT share
   mutable state.

## Requirement 2: Independence holds for the `size=True` form

**User story:** As a caller who requests the multiplicity count alongside each
partition, I want the same independence guarantee, so that the count/partition
pairs I retain remain individually correct.

**Acceptance criteria**

1. WHEN `partitions(n, m, k, size=True)` is iterated, THEN each step SHALL yield
   a pair whose first element is the total number of parts (the sum of the
   partition's multiplicities) and whose second element is the partition
   dictionary for that step.
2. WHEN a caller retains every yielded pair from the `size=True` form, THEN each
   retained partition dictionary SHALL independently reflect the partition
   current at its step, exactly as required for the partition-only form.
3. The first element of each yielded pair SHALL equal the sum of the
   multiplicities of the partition in that same pair.

## Requirement 3: Preserve which partitions are generated, their contents and order

**User story:** As a maintainer, I want the set, contents, and ordering of
generated partitions to remain exactly as before, so that only the sharing
behavior changes and no downstream result shifts.

**Acceptance criteria**

1. The system SHALL generate, for given `n`, `m`, `k`, exactly the same
   partitions, in the same order, as before the change — the independence
   guarantee SHALL NOT add, remove, reorder, or alter any partition.
2. Each yielded partition SHALL map every present part value to its multiplicity
   (a strictly positive count) and SHALL sum, over part-value × multiplicity, to
   `n`.
3. WHEN `k` is supplied, THEN every yielded partition SHALL contain only part
   values not exceeding `k`.
4. WHEN `m` is supplied, THEN every yielded partition SHALL have a total number
   of parts (sum of multiplicities) not exceeding `m`.
5. WHEN both `m` and `k` are supplied, THEN the generated partitions SHALL be
   exactly those simultaneously satisfying the `m` and `k` bounds, in the
   established order.
6. WHEN the inputs admit no partition (for example a non-positive `n`, a bound
   less than 1, or bounds whose product cannot reach `n`), THEN `partitions`
   SHALL yield exactly one empty partition (represented as an empty dictionary,
   or the pair of `0` and an empty dictionary in the `size=True` form),
   consistent with the convention that there is one way to partition under such
   inputs.
7. The system SHALL continue to accept SymPy integer inputs (e.g. a sympified
   integer for `n`) equivalently to plain Python integers, yielding the same
   partitions.
