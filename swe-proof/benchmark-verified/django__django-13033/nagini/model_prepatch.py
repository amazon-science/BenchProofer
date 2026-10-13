"""Twin-artifact model for django__django-13033.

Behavioural contract (the observable ORM behaviour under specification).

A queryset can be ordered by a lookup path: a sequence of one or more name
segments joined by the lookup separator (e.g. ``record__root`` or
``record__root_id``). When the path resolves to a field that is a relation to
another model, the resolver decides one of two outcomes:

  * ``mode == 1`` -- sort by the related model's own default sort order (this
    expands the related model's declared ordering, which can flip the
    direction and add a join to the related table); or
  * ``mode == 0`` -- sort directly by the named target column (ascending, with
    no extra join to the related table).

The contract pins exactly when each outcome is required. The related model's
default sort order is substituted (``mode == 1``) only when ALL of the
following hold:

  * the resolved target field points to another model, AND
  * the related model declares a default sort order, AND
  * the named target is NOT the related field's own column, AND
  * the named target is NOT the primary-key shortcut.

When the named target IS the related field's own column (the path's terminal
token names that column directly), the query must sort by that column directly
(``mode == 0``); the related model's default sort order is NOT applied -- so a
queryset ordered by a related field's own column sorts ascending by that
column with a single join, while a queryset ordered by the related field
itself adopts the related model's default sort order.

``relation_own_column`` is the related field's own column token; ``name`` is
the whole lookup path; ``path_segments`` is that path decomposed into its
segments, with ``path_terminal(path_segments)`` its terminal segment. Strings
are modelled as ``PSeq[int]`` of Unicode code points and the lookup path as
``PSeq[PSeq[int]]`` of its segments (Nagini bans ``str`` indexing).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The decisive predicate is modelled deeply over the
# segment sequence; the unchanged machinery it guards -- join/target trimming
# and recursive expansion over the related model's sort order -- is not part of
# the modelled predicate and is represented only by the abstract `mode`
# outcome.)
# axioms-end


# pure-start
@Pure
def PK() -> PSeq[int]:
    # 'pk' -- the primary-key shortcut token.
    return PSeq(112, 107)


@Pure
def path_terminal(path_segments: PSeq[PSeq[int]]) -> PSeq[int]:
    """The terminal segment of a non-empty lookup path."""
    Requires(len(path_segments) > 0)
    return path_segments[len(path_segments) - 1]
# pure-end


def ordering_mode(name: PSeq[int],
                  path_segments: PSeq[PSeq[int]],
                  relation_own_column: PSeq[int],
                  points_to_relation: bool,
                  has_default_ordering: bool) -> int:
    # pre-conditions-start
    # The lookup path has at least one segment.
    Requires(len(path_segments) > 0)
    # A multi-segment path carries separators and preceding segments, so the
    # whole path token is never equal to its terminal segment alone (the
    # split-then-rejoin invariant of a multi-segment lookup path).
    Requires(Implies(len(path_segments) > 1, name != path_terminal(path_segments)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == 0 or Result() == 1)
    # The related model's default sort order is substituted (mode 1) exactly
    # when the target points to a relation with a default sort order, the named
    # target is not the related field's own column, and is not the primary-key
    # shortcut.
    Ensures((Result() == 1) ==
            (points_to_relation and has_default_ordering
             and relation_own_column != path_terminal(path_segments)
             and name != PK()))
    # post-conditions-end
    # impl-start
    if (points_to_relation and has_default_ordering
            and relation_own_column != name
            and name != PK()):
        return 1
    return 0
    # impl-end
