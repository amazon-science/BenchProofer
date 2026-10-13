"""Twin-artifact model for astropy__astropy-14539.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A tabular-data comparison reports, per column, how many ROWS of the column
  differ between two tables. Whatever the column's storage layout, the reported
  figure is row-granular: a row counts once if its two stored values disagree —
  as the comparator governing that column judges disagreement — in at least one
  compared position, and rows whose stored values agree everywhere they are
  compared do not count.
  Element i of the result is therefore the number of differing rows of column i.

  Some columns store, in each row, a whole sub-array of its own rather than a
  positional slot in one fixed-width frame shared by every row. Such a column is
  governed by the row-aware comparator, which inspects each row's sub-array and
  decides whether that row differs, and it decides that by folding a per-position
  CLOSENESS verdict, at the comparison's tolerances, over the row. The plain
  element-wise comparator governs columns whose rows are laid out as ordinary
  fixed-width values in one shared frame, and it judges a position by plain
  INEQUALITY.
  WHICH comparator governs a column is decided by HOW THAT COLUMN'S ROWS ARE
  ACTUALLY STORED, and by nothing else. It is a property of the materialised
  pair of columns the comparison holds in hand — whether a row's value is a
  sub-array object standing on its own, or a run of positions inside a shared
  frame — and it is NOT read off any name, spelling or declaration that
  accompanies the column. Two columns whose rows are stored the same way are
  governed by the same comparator however they are labelled, and a column whose
  rows hold their own sub-arrays is governed by the row-aware comparator even
  when its label is one this comparison does not otherwise single out. Deciding
  the routing from a label rather than from the storage is a different behaviour,
  and it is not the one described here wherever the two would disagree.

  The two comparators do not judge a position by the same test, so they do not
  in general report the same figure for the same pair of columns. The figure a
  column contributes is therefore the number of rows rejected by the verdict of
  the comparator GOVERNING THAT COLUMN — the closeness verdict for a column
  whose rows hold sub-arrays of their own, the plain inequality for a column
  whose rows sit in one shared fixed-width frame. Reporting the figure the OTHER
  comparator's verdict would have produced is not the behaviour, even where the
  two happen to coincide.

  The element-wise comparator compares the two sides as whole stored blocks and
  attributes each compared position to a slot of the LEADING axis of that
  comparison. Its figure is the number of those slots holding at least one
  reported position — row-granular in exactly the same sense as the other
  comparator's, and pinned for EVERY such column. When the two sides frame their
  rows under one and the same positional layout the leading axis is the column's
  rows and the slots ARE the rows. When the two sides frame their rows
  differently the comparator still lays the blocks against each other and still
  attributes every reported position to a leading-axis slot, and its figure is
  still the number of slots that hold one; that difference of framing is
  additionally reported by this comparison in its own right, but it does not
  leave the data figure unclaimed. Columns whose rows hold their own sub-arrays
  are the special case where each side lists one value per row, so their leading
  axis is always the rows themselves.

Modelling. The layout descriptor string is carried as `List[int]` of code
points — carried only, since it is not what decides the routing. How the rows are
stored is carried by the single observation `rows_hold_subarrays` of the
materialised pair of columns; it is read off the pair of columns the comparison
holds, and is pinned against that real observation by conformance_check.py
(G-CONF) and axiom_check.py (G-AX). No second observation accompanies it: which
comparator governs a column is settled by how its rows are stored and by nothing
further, so there is no further condition under which a column's figure goes
unclaimed.
  The comparison of the two columns is summarised once per per-position verdict,
because the verdicts differ, and each summary is indexed by the slots ITS OWN
comparator attributes positions to: `close_mismatches[i]` is the number of
positions of row i that the row-aware comparator's own per-position closeness
verdict rejects at the comparison's default tolerances, and
`unequal_mismatches[i]` is the number of positions that the element-wise
comparator's own plain-inequality verdict reports in leading-axis slot i of the
block comparison it performs. The two summaries are therefore indexed
independently and need not have the same length: the row-aware comparator's slots
are always the rows, while the element-wise comparator's are the rows exactly
when the two sides frame them alike.
Each summary is taken under the SAME positional alignment its comparator uses
to lay one row's two stored values against each other — NOT under a
length-difference penalty. Two stored values of unequal length therefore
summarise as agreeing (0) exactly when that alignment makes every compared
position agree, and a summary is defined for a row precisely when the alignment
is defined: a row whose two stored values cannot be aligned or compared at all
lies outside the comparison's domain and has no summary. So
`close_mismatches[i] == 0` iff the row-aware comparator judges row i's two
stored values equivalent, and `unequal_mismatches[i] == 0` iff the element-wise
one does.
  The two summaries are INCOMPARABLE: neither verdict refines the other, so no
ordering between them may be assumed in either direction. A position the
inequality test reports can still be close, because the closeness verdict is
computed in a fixed-precision arithmetic whose significand is narrower than the
integer range these sub-array-valued columns exist to carry, so it cannot
separate neighbouring values of that range. And a position the inequality test
does NOT report can still be rejected by the closeness verdict, because that
verdict is not reflexive on every value it accepts: it scales its operands
before comparing them, so a value with a non-finite component is not judged
close even to itself, while the inequality test finds no difference there. So
neither verdict reduces to the other, and neither reduces to an idealised
exact-equality test. WHICH of the two summaries governs a column is thus
observable in the figure it reports, and that figure is the whole of what this
specification pins: no separate claim is made about how a figure is arrived at,
only about which verdict's rows it counts.
Where a comparator's verdict is not defined for a column's storage at all, its
summary carries no information about that column: it is then pinned by nothing
beyond being a per-row count of positions, and the reported figure does not
depend on it. No column is therefore outside the comparison's domain for want of
the inapplicable comparator's summary. A column whose values this comparison
compares by NEITHER of the two verdicts above is outside what is described here.
  The number of differing rows is modelled deeply by the front-recursive fold
`row_granular_count`, applied to the summary of the verdict that governs the
column; `contains_cp` is the membership helper over the descriptor carrier.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def contains_cp(s: PSeq[int], cp: int) -> bool:
    """True iff the code point `cp` occurs in the sequence `s`. Front-recursive
    so a single unfold is available per loop step. The membership helper over the
    descriptor carrier — available to read the descriptor, which is NOT what
    decides which comparator governs a column."""
    if len(s) == 0:
        return False
    return s[0] == cp or contains_cp(s.drop(1), cp)


@Pure
def row_granular_count(m: PSeq[int]) -> int:
    """The number of rows that have at least one differing element.
    Front-recursive so a single unfold is available per loop step. Its value is
    a count of rows, so it is never negative: an impl that produces the figure
    without folding is not thereby unable to show the figure is a count."""
    Ensures(Result() >= 0)
    if len(m) == 0:
        return 0
    head = 1 if m[0] > 0 else 0  # type: int
    return head + row_granular_count(m.drop(1))
# pure-end


def count_differing_rows(fmt: List[int], close_mismatches: List[int],
                         unequal_mismatches: List[int],
                         rows_hold_subarrays: bool) -> int:
    """The figure one column contributes: the number of its rows that differ
    under the verdict of the comparator governing that column."""
    # pre-conditions-start
    Requires(Acc(list_pred(fmt), 1 / 2))
    Requires(Acc(list_pred(close_mismatches), 1 / 2))
    Requires(Acc(list_pred(unequal_mismatches), 1 / 2))
    # The two per-position verdicts index their summaries by the slots each
    # comparator itself attributes positions to, so NO relation is required
    # between the two lengths: requiring them equal would put out of domain
    # every column whose two sides frame their rows differently, which this
    # comparison really does compare.
    # Each per-row summary is a non-negative count of positions.
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(close_mismatches),
                 close_mismatches[k] >= 0),
         [[close_mismatches[k]]])))
    Requires(Forall(int, lambda k:
        (Implies(0 <= k and k < len(unequal_mismatches),
                 unequal_mismatches[k] >= 0),
         [[unequal_mismatches[k]]])))
    # NOTHING is required of the storage observation, and no relation is
    # required between it and the descriptor carrier. Either value of it, with
    # any descriptor, is a pair of columns this comparison really compares, so
    # requiring a relation would put real columns out of domain and let the
    # obligations below be met by excluding them instead of by meeting them.
    # No relation is required BETWEEN the two summaries either. Neither
    # per-position verdict refines the other — the closeness verdict fails to
    # separate neighbouring values of the integer range these columns carry, and
    # it also rejects a position whose two values are the same
    # non-finite-component value, which the inequality test does not report — so
    # an ordering in either direction would exclude columns this comparison
    # really compares.
    # TERMINATION: the per-column comparison is bounded work and MUST actually
    # complete (total correctness). Under partial-correctness semantics a
    # diverging body (e.g. an endless loop before the return) satisfies the
    # row-granular postcondition only vacuously yet never delivers the count to
    # its caller; the real per-column comparison always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fmt), 1 / 2))
    Ensures(Acc(list_pred(close_mismatches), 1 / 2))
    Ensures(Acc(list_pred(unequal_mismatches), 1 / 2))
    Ensures(Result() >= 0)
    # The contribution of the column is the number of differing ROWS — a row
    # counts once if at least one of its positions is rejected — under the
    # verdict of the comparator GOVERNING this column, and WHICH comparator that
    # is follows from how the column's rows are stored. A column whose rows hold
    # sub-arrays of their own is governed by the row-aware comparator, so it
    # reports the rows its CLOSENESS summary rejects. This holds of every such
    # column, with no side condition: each side of such a column lists one value
    # per row, so the two sides always frame their rows alike, and the figure is
    # a row count outright.
    Ensures(Implies(rows_hold_subarrays,
                    Result() == row_granular_count(ToSeq(close_mismatches))))
    # A column whose rows do NOT hold sub-arrays of their own is governed by the
    # element-wise comparator, so it reports the slots its PLAIN-INEQUALITY
    # summary reports. This holds of EVERY such column with no side condition:
    # that comparator attributes every reported position to a leading-axis slot
    # of the block comparison it performs whatever the two sides' framing, so
    # its figure is the number of such slots holding a reported position in
    # every case. A column is never left without a claimed figure on account of
    # how its two sides are framed.
    # So a column reports the figure of the verdict that governs IT; reporting
    # the other verdict's figure is a different behaviour wherever the two
    # verdicts disagree, and the figure is the only thing claimed — a figure that
    # agrees with the governing verdict's satisfies this claim however it was
    # obtained, and one that agrees only with the other verdict's fails it
    # however it was obtained.
    Ensures(Implies(not rows_hold_subarrays,
                    Result() == row_granular_count(ToSeq(unequal_mismatches))))
    # post-conditions-end
    # impl-start
    # How the column's rows are STORED selects the governing verdict, and the
    # column's figure is that verdict's summary folded row-granularly: a column
    # whose rows hold sub-arrays of their own counts the rows its closeness
    # summary rejects, every other column the leading-axis slots its
    # plain-inequality summary reports.
    total = 0
    if rows_hold_subarrays:
        i = len(close_mismatches)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(fmt), 1 / 2))
            Invariant(Acc(list_pred(close_mismatches), 1 / 2))
            Invariant(Acc(list_pred(unequal_mismatches), 1 / 2))
            Invariant(0 <= i and i <= len(close_mismatches))
            Invariant(total >= 0)
            Invariant(Forall(int, lambda k:
                (Implies(0 <= k and k < len(close_mismatches),
                         close_mismatches[k] >= 0),
                 [[close_mismatches[k]]])))
            Invariant(total ==
                      row_granular_count(ToSeq(close_mismatches).drop(i)))
            # The loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure i, discharging
            # MustTerminate(2) from the precondition.
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(close_mismatches).drop(i - 1)[0] ==
                   close_mismatches[i - 1])
            Assert(ToSeq(close_mismatches).drop(i - 1).drop(1) ==
                   ToSeq(close_mismatches).drop(i))
            if close_mismatches[i - 1] > 0:
                total = total + 1
            i = i - 1
    else:
        j = len(unequal_mismatches)
        while j > 0:
            # invariants-start
            Invariant(Acc(list_pred(fmt), 1 / 2))
            Invariant(Acc(list_pred(close_mismatches), 1 / 2))
            Invariant(Acc(list_pred(unequal_mismatches), 1 / 2))
            Invariant(0 <= j and j <= len(unequal_mismatches))
            Invariant(total >= 0)
            Invariant(Forall(int, lambda k:
                (Implies(0 <= k and k < len(unequal_mismatches),
                         unequal_mismatches[k] >= 0),
                 [[unequal_mismatches[k]]])))
            Invariant(total ==
                      row_granular_count(ToSeq(unequal_mismatches).drop(j)))
            # Same decreasing measure on the other branch's fold.
            Invariant(MustTerminate(j + 1))
            # invariants-end
            Assert(ToSeq(unequal_mismatches).drop(j - 1)[0] ==
                   unequal_mismatches[j - 1])
            Assert(ToSeq(unequal_mismatches).drop(j - 1).drop(1) ==
                   ToSeq(unequal_mismatches).drop(j))
            if unequal_mismatches[j - 1] > 0:
                total = total + 1
            j = j - 1
    return total
    # impl-end
