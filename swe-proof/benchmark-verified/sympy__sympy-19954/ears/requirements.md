# Requirements — Robust minimal block system enumeration in permutation groups

## Introduction

The permutation-group machinery in `sympy.combinatorics.perm_groups` computes
the collection of *minimal block systems* of a transitive group via
`PermutationGroup.minimal_blocks(self, randomized=True)`. This routine iterates
over candidate block systems (one representative cell `rep` per orbit of the
point stabilizer) and maintains three parallel, index-aligned collections:

- the block systems found so far (each a per-point labeling list),
- their numbered forms (used to detect duplicates), and
- the representative cells (point sets used to compare systems by cardinality
  and subset relation).

When a newly examined candidate makes one or more previously retained systems
non-minimal (a retained representative cell strictly contains the candidate's
cell), those retained systems must be discarded. The original implementation
performed this discard by deleting entries from two of the three collections
*while iterating by index over the third*. Because the collection being indexed
was not shrunk in step with the ones being deleted, later indices fell outside
the shrunken collections, raising `IndexError: list assignment index out of
range`. In-loop index-based deletion also risked misaligning the three
collections relative to one another.

This surfaced through any caller that enumerates minimal block systems. In
particular `PermutationGroup.sylow_subgroup(p)` calls `minimal_blocks()` and so
inherited the crash: computing the 2-Sylow subgroup of a dihedral group whose
degree is twice an odd number (e.g. `DihedralGroup(18)`, `DihedralGroup(50)`)
raised `IndexError` instead of returning a subgroup.

The goal is to make `minimal_blocks` remove superseded systems correctly and
without error, keeping the three collections mutually consistent, so that it
and its callers (notably `sylow_subgroup`) return correct results for all
transitive groups.

## Requirement 1: `minimal_blocks` does not raise on supersession

**User story:** As a user computing block systems of a permutation group, I
want `minimal_blocks` to complete without crashing when a later candidate
supersedes earlier ones, so that I can enumerate minimal block systems of any
transitive group.

**Acceptance criteria**

1. WHEN `PermutationGroup.minimal_blocks()` is called on a transitive group
   whose enumeration encounters a candidate block system whose representative
   cell is a strict subset of one or more previously retained representative
   cells, THEN `minimal_blocks` SHALL complete normally and SHALL NOT raise
   `IndexError` (or any other exception) arising from removing the superseded
   systems.
2. The system SHALL remove, from every collection it maintains, exactly those
   previously retained block systems whose representative cell strictly contains
   the current candidate's representative cell, and SHALL retain all others.
3. WHILE examining a single candidate, the system SHALL NOT shorten any of its
   maintained collections in a way that leaves them referenced by an index
   beyond their current length; removal SHALL be applied consistently so that no
   valid index is ever left dangling.

## Requirement 2: The three parallel collections stay index-aligned

**User story:** As a maintainer, I want the block-systems list, the numbered
forms, and the representative cells to remain positionally aligned after any
removal, so that duplicate detection and results are correct.

**Acceptance criteria**

1. WHEN one or more retained block systems are removed because they are
   superseded by the current candidate, THEN the system SHALL remove the
   corresponding entries from the block-systems collection, the numbered-form
   collection, and the representative-cell collection so that, after removal,
   entries at the same position across all three collections still describe the
   same block system.
2. IF the current candidate's representative cell is a strict subset of some
   retained representative cell, THEN the retained numbered form and retained
   block-system entry for that cell SHALL both be discarded together (never one
   without the other).
3. The system SHALL treat the current candidate as itself non-minimal, and
   SHALL NOT add it, WHEN some previously retained representative cell of
   strictly smaller cardinality is a subset of the current candidate's
   representative cell (i.e. the candidate is superseded by an already-retained
   finer system). This is the opposite direction of Requirement 2.2: there the
   retained entry is discarded because the candidate is finer; here the
   candidate is dropped because a retained entry is finer.

## Requirement 3: Correct minimal block systems are returned

**User story:** As a user, I want `minimal_blocks` to return the correct set of
minimal block systems, so that downstream algorithms compute correct results.

**Acceptance criteria**

1. WHEN `minimal_blocks()` is called on a transitive group, THEN it SHALL return
   a list containing exactly one representative for each distinct minimal block
   system, with no duplicated numbered form and with no system that is
   superseded by (strictly refined by) another returned system.
2. IF the group is not transitive, THEN `minimal_blocks()` SHALL return `False`.
3. The system SHALL continue to return the previously correct results for cases
   that already worked; for example, `DihedralGroup(6)` (transitive on six
   points) SHALL yield exactly two minimal block systems — one partitioning the
   six points into two blocks of three points each, and the other partitioning
   them into three blocks of two points each — and SHALL NOT include any trivial
   single-block (all points in one block) system.
4. WHEN a newly appended candidate is genuinely minimal and its numbered form is
   not already present, THEN the system SHALL append its block system, numbered
   form, and representative cell to the respective collections.

## Requirement 4: `sylow_subgroup` succeeds for affected groups

**User story:** As a user, I want `sylow_subgroup(p)` to return a valid Sylow
subgroup for the groups that previously triggered the crash, so that Sylow
computations are reliable.

**Acceptance criteria**

1. WHEN `sylow_subgroup(p)` is invoked on a group whose `minimal_blocks`
   computation encounters superseded candidate systems, THEN it SHALL return a
   permutation group and SHALL NOT propagate an `IndexError` from block-system
   enumeration.
2. WHEN `DihedralGroup(18).sylow_subgroup(p=2)` is computed, THEN the returned
   subgroup SHALL have order `4`.
3. WHEN `DihedralGroup(50).sylow_subgroup(p=2)` is computed, THEN the returned
   subgroup SHALL have order `4`.
4. The returned subgroup's order SHALL equal the largest power of `p` dividing
   the group's order, and the subgroup SHALL be a subgroup of the original
   group (consistent with the previously documented behavior, e.g.
   `DihedralGroup(6).sylow_subgroup(2)` having order `4`).

## Requirement 5: Related enumeration behavior is preserved

**User story:** As a user relying on primitivity and transitivity queries, I
want those to keep working unchanged, so that no regression is introduced by
the block-enumeration fix.

**Acceptance criteria**

1. The system SHALL keep `is_primitive` and `is_transitive` behaving as before;
   for example `DihedralGroup(10).is_primitive()` SHALL return `False`.
2. The system SHALL keep all other permutation-group operations that do not
   depend on the corrected removal step (order, stabilizer, orbits, subgroup
   membership, and related queries) behaving exactly as before this change.
