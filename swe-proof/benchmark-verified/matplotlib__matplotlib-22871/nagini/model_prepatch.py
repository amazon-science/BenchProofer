"""Twin-artifact model for matplotlib__matplotlib-22871.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A sequence of tick instants is described by six parallel integer columns,
  one per calendar component, ordered from coarsest to finest:

      column 0 = year, 1 = month, 2 = day, 3 = hour, 4 = minute, 5 = second.

  All columns have the same length N (>= 1), one entry per tick.

  Two derived quantities are computed:

    * the labelling level L -- the finest component that the ticks share, found
      by scanning the columns from finest (5) to coarsest (0) and selecting the
      FIRST column (i.e. the highest-indexed one) whose entries are NOT all
      equal across the ticks. When every column is constant across the ticks
      (all ticks identical down to the second), L is the finest level, 5.

    * whether a separate summary label (the "offset") is shown. By default it
      is shown. It is suppressed ONLY when the labelling level is a coarse one
      (year or month, i.e. L < 2) AND the value 1 occurs somewhere in that
      labelling column. Otherwise -- in particular at a coarse labelling level
      whose column does NOT contain the value 1 -- the offset stays shown.

  The reported result carries the labelling level and a 0/1 flag for whether the
  offset is shown.

Modelling choices (Nagini fragment):
  * Each tick column is a ``List[int]`` (the integer calendar component).
    `col_varies` and `col_has_one` are structural predicates over a column --
    "the column is not constant" and "the value 1 is present in the column" --
    validated against the real column reductions out-of-band by axiom_check.py
    (G-AX); they are not consumed as axioms.
  * The six-iteration descending scan over the literal range of levels is
    transcribed as a straight-line cascade (the trip count is a compile-time
    constant; no data-dependent loop bound).
  * The result is returned as a small object with the two observed fields.

No string indexing or library import beyond typing / nagini_contracts is used.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The two structural predicates the behaviour composes --
# "the column is not constant" and "the value 1 is present in the column" --
# are modelled DEEPLY by `col_varies` / `col_has_one` below. They are not opaque
# callees the proof stands in for; their equality to the real column reductions
# is validated out-of-band by axiom_check.py (G-AX) as A-reference deep models.
# axioms-end


# pure-start
@Pure
def col_varies(col: List[int]) -> bool:
    """True iff the column is not constant across the ticks, i.e. two ticks
    disagree on this calendar component."""
    Requires(Acc(list_pred(col), 1 / 4))
    return Exists(int, lambda i: Exists(int, lambda j: (
        0 <= i and i < j and j < len(col) and col[i] != col[j])))


@Pure
def col_has_one(col: List[int]) -> bool:
    """True iff the value 1 occurs somewhere in the column."""
    Requires(Acc(list_pred(col), 1 / 4))
    return Exists(int, lambda i: (0 <= i and i < len(col) and col[i] == 1))
# pure-end


class TickLevel:
    """The two observed outputs of the labelling-level computation: the chosen
    labelling level and a 0/1 flag for whether the summary offset is shown."""

    def __init__(self, level: int, show_offset: int) -> None:
        Requires(0 <= level and level <= 5)
        Requires(show_offset == 0 or show_offset == 1)
        # Terminates: two field assignments, straight-line, no loop and no
        # further call. Level 1 leaves room strictly below determine_level's
        # level 6, which constructs a TickLevel on every return path.
        Requires(MustTerminate(1))
        Ensures(Acc(self.level) and Acc(self.show_offset))
        Ensures(self.level == level and self.show_offset == show_offset)
        self.level = level          # type: int
        self.show_offset = show_offset  # type: int


def determine_level(c0: List[int], c1: List[int], c2: List[int],
                    c3: List[int], c4: List[int], c5: List[int]) -> TickLevel:
    # pre-conditions-start
    # The six tick columns are READ-ONLY (directive 5: fractional permission).
    Requires(Acc(list_pred(c0), 1 / 2))
    Requires(Acc(list_pred(c1), 1 / 2))
    Requires(Acc(list_pred(c2), 1 / 2))
    Requires(Acc(list_pred(c3), 1 / 2))
    Requires(Acc(list_pred(c4), 1 / 2))
    Requires(Acc(list_pred(c5), 1 / 2))
    # There is at least one tick, and all columns share the same length.
    Requires(len(c0) >= 1)
    Requires(len(c1) == len(c0) and len(c2) == len(c0) and len(c3) == len(c0))
    Requires(len(c4) == len(c0) and len(c5) == len(c0))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(c0), 1 / 2))
    Ensures(Acc(list_pred(c1), 1 / 2))
    Ensures(Acc(list_pred(c2), 1 / 2))
    Ensures(Acc(list_pred(c3), 1 / 2))
    Ensures(Acc(list_pred(c4), 1 / 2))
    Ensures(Acc(list_pred(c5), 1 / 2))
    Ensures(Acc(Result().level) and Acc(Result().show_offset))
    Ensures(0 <= Result().level and Result().level <= 5)
    Ensures(Result().show_offset == 0 or Result().show_offset == 1)
    # The labelling level is the highest-indexed column that varies, found by
    # the finest-to-coarsest scan; if no column varies it is the finest, 5.
    Ensures(Implies(col_varies(c5), Result().level == 5))
    Ensures(Implies(not col_varies(c5) and col_varies(c4),
                    Result().level == 4))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4) and col_varies(c3),
                    Result().level == 3))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and col_varies(c2),
                    Result().level == 2))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and col_varies(c1), Result().level == 1))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and col_varies(c0),
                    Result().level == 0))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and not col_varies(c0),
                    Result().level == 5))
    # The offset is hidden (flag == 0) EXACTLY when the labelling level is a
    # coarse one (year or month) AND that column carries the value 1; otherwise
    # the offset stays shown (flag == 1), including at a coarse labelling level
    # whose column does not contain the value 1.
    Ensures(Implies(col_varies(c1) and not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2),
                    (Result().show_offset == 0) == col_has_one(c1)))
    Ensures(Implies(col_varies(c0) and not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1),
                    (Result().show_offset == 0) == col_has_one(c0)))
    # When the labelling level is a fine one (>= 2), or when no column varies,
    # the offset is always shown.
    Ensures(Implies(col_varies(c5) or col_varies(c4) or col_varies(c3)
                    or col_varies(c2),
                    Result().show_offset == 1))
    Ensures(Implies(not col_varies(c5) and not col_varies(c4)
                    and not col_varies(c3) and not col_varies(c2)
                    and not col_varies(c1) and not col_varies(c0),
                    Result().show_offset == 1))
    # post-conditions-end
    # impl-start
    # Default: the offset is shown. The descending scan over the six levels is
    # the literal range(5, -1, -1) transcribed as a straight-line cascade.
    if col_varies(c5):
        return TickLevel(5, 1)
    if col_varies(c4):
        return TickLevel(4, 1)
    if col_varies(c3):
        return TickLevel(3, 1)
    if col_varies(c2):
        return TickLevel(2, 1)
    if col_varies(c1):
        return TickLevel(1, 0)
    if col_varies(c0):
        return TickLevel(0, 0)
    # No column varies: every tick is identical down to the second. The scan
    # reaches the coarsest level with all entries equal and resets to the finest
    # level; the offset keeps its default (shown).
    return TickLevel(5, 1)
    # impl-end
