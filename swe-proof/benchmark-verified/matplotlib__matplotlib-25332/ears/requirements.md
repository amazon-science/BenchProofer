# Requirements: Make the grouping container picklable so figures with aligned labels serialize

## Introduction

Matplotlib's `Grouper` class (`lib/matplotlib/cbook.py`) maintains a partition of
objects into disjoint sets. So that the grouped objects can still be
garbage-collected, `Grouper` does not store the objects themselves; it stores
*weak references* to them. Internally the partition lives in `Grouper._mapping`,
a dictionary whose keys are `weakref.ref(x)` handles and whose values are lists
of `weakref.ref(x)` handles.

A `Figure` keeps two such groupers in `Figure._align_label_groups` (a `{"x":
Grouper(), "y": Grouper()}` dict, `lib/matplotlib/figure.py`). Calling
`Figure.align_labels`, `Figure.align_xlabels`, or `Figure.align_ylabels` joins
axes into these groupers so their x/y axis labels line up.

Weak-reference objects cannot be pickled. Consequently, once a figure has had
its labels aligned, its `_align_label_groups` groupers hold weak references and
any attempt to pickle the figure fails with a `TypeError` ("cannot pickle
'weakref.ReferenceType' object"). Pickling the same figure *before* aligning
labels works, which localizes the defect to the grouping container's
serialization.

The goal is to make `Grouper` serialize and deserialize correctly — surviving a
pickle round trip while preserving the partition it holds — so that figures
containing aligned labels can be pickled and unpickled like any other figure.
This is achieved by giving `Grouper` explicit pickle-protocol serialization
support that resolves its stored weak references to strong references when
capturing state and re-wraps them as weak references when restoring state, in
`lib/matplotlib/cbook.py`. No other behavior of `Grouper` or of figure pickling
may change.

## Requirement 1: A grouping container survives serialization

**User story:** As a user who serializes matplotlib objects, I want a `Grouper`
to be picklable, so that containers holding grouped objects do not make an
otherwise-serializable structure unpicklable.

**Acceptance criteria**
1. WHEN a `Grouper` (including one that has had objects joined into groups) is
   serialized via the standard pickling protocol, THEN the operation SHALL
   succeed rather than raising a `TypeError` about pickling a weak reference.
2. WHEN a `Grouper` is captured for serialization, THEN its captured state SHALL
   contain no live weak-reference objects: every stored handle SHALL be
   represented by the object it refers to (its referent) rather than by a weak
   reference to that object.
3. The captured state SHALL preserve the full partition structure — for every
   entry of the internal mapping, the referent of the key together with the
   referents of every member of that key's group — so that no grouping
   information is lost during capture.
4. WHEN a captured `Grouper` state is restored, THEN every recorded referent
   (both keys and group members) SHALL be wrapped back into a weak reference,
   restoring the container to the same internal weak-reference-keyed
   representation it uses when constructed directly.

## Requirement 2: Serialization round trip preserves the grouping

**User story:** As a user, I want a `Grouper` recovered from its serialized form
to report the same grouping as the original through its membership and sibling
queries, so that deserialized objects are grouped the same way as the originals
for the purposes of those queries.

**Acceptance criteria**
1. WHEN a `Grouper` is serialized and then deserialized, THEN the restored
   `Grouper` SHALL report the same partition into groups as the original when
   observed through its membership test and its sibling query: for every object,
   the set of objects grouped with it (its siblings, including itself) in the
   restored container SHALL equal the corresponding set in the original.
   Equivalently, two objects are reported as siblings in the restored container
   exactly when they were reported as siblings in the original. This requirement
   constrains ONLY the group membership recovered by the container's
   membership/sibling operations. It does NOT require the restored container to
   reproduce the internal per-group list-object identity that the direct
   "are these two objects joined" identity query relies on; that identity query
   is not required to report two objects as joined after a round trip even when
   they share a group, and no acceptance criterion here mandates its
   preservation across serialization.
2. WHEN the restored `Grouper` is queried for the siblings of a member, THEN it
   SHALL return the same group of members (as objects) that the original would
   return for that member.
3. IF the original `Grouper` was empty (no objects joined), THEN the
   deserialized `Grouper` SHALL also be empty.

## Requirement 3: Figures with aligned labels are picklable

**User story:** As a user, I want to pickle a figure after aligning its labels,
so that label alignment does not prevent saving or transmitting a figure.

**Acceptance criteria**
1. WHEN a figure has had its x and/or y axis labels aligned (via the figure's
   label-alignment methods) and the figure is then pickled, THEN pickling SHALL
   succeed rather than raising a `TypeError` about pickling a weak reference.
2. WHEN such a figure is unpickled, THEN the reconstructed figure SHALL be a
   valid figure whose label-alignment grouping information is restored in the
   same weak-reference-backed form used by a freshly constructed figure.
3. The system SHALL preserve the ability to pickle a figure that has NOT had its
   labels aligned; introducing serialization support for the grouping container
   SHALL NOT break pickling of figures in that case.

## Requirement 4: Preserve all existing grouping and pickling behavior

**User story:** As a maintainer, I want the existing `Grouper` operations and the
existing figure-pickling guarantees to remain unchanged, so that adding
serialization support does not regress anything.

**Acceptance criteria**
1. The system SHALL preserve the existing `Grouper` operations — joining
   objects, testing membership, testing whether two objects are joined, listing
   the disjoint groups, retrieving an object's siblings, and removing an object —
   with their current semantics when exercised on a `Grouper` in normal use
   (that is, one not recovered from serialization), unaffected by the added
   serialization support. This criterion concerns the behavior of these
   operations on a live container; it does NOT impose any cross-serialization
   preservation guarantee beyond those stated in Requirement 2.
2. The system SHALL continue to allow already-supported figures, axes, artists,
   transforms, colormaps, norms, and related plotting objects to be pickled and
   unpickled successfully, including a fully populated figure that exercises a
   broad range of plot types together with label alignment.
3. WHEN a comprehensively populated figure — one combining many plot types and
   also having its labels aligned — is pickled and then unpickled, THEN the
   round trip SHALL complete without error and the reconstructed figure SHALL
   render equivalently to the original.
