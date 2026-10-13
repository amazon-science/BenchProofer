"""Twin-artifact model for django__django-10554.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a combined result set (the concatenation of several sub-results) must be
  ordered, every ORDER BY term has to be rewritten as a 1-based POSITION into
  the result set's column list, because the term cannot be referred to by name
  across the combined sub-results. The rewrite scans the current column list
  for a column equal to the term:

    * if some column equals the term, the term is rewritten to the 1-based
      position of the FIRST such column;
    * otherwise the term names no column of the result set, and the outcome
      depends on whether the term is an ALIASED expression (a named/derived
      term that only makes sense relative to a column list) or a plain,
      self-describing column:
        - an aliased term that matches no column is rejected: ordering by it is
          impossible, so the request signals an error;
        - a plain column that matches no column is ADDED to the result set's
          column list, and the term is rewritten to its new (last) position.
          Adding the missing plain column is what lets a derived ordering over
          a combined result set succeed instead of failing.

  The pinned discrimination: an unmatched PLAIN column must be appended and
  referenced by its new position (never rejected), while an unmatched ALIASED
  term must be rejected; a matched term (plain or aliased) keeps the existing
  column list unchanged and is referenced by the first matching position.

Column identities are modelled as integers; the result set's column list is a
`List[int]` (mutated only on the append path). The pure sequence theory
`PSeq[int]` carries the position specification. The rejection of an unmatched
aliased term is a user-defined exception (a builtin exception in an `Exsures`
crashes the Nagini translator; mapping.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class OrderTermUnmatched(Exception):
    """Signals that an aliased ordering term matches no column of the result
    set and cannot be added, so the ordering request is rejected. Stands in for
    the database error the desired behaviour raises in that case; a builtin
    exception in an `Exsures` crashes the Nagini translator (mapping.md §2)."""


# axioms-start
# (No axiomatized callees. The whole observed behaviour — scanning the column
# list for the first match, then either appending the plain column or rejecting
# the aliased term — is modelled deeply below. The downstream rendering of a
# position into the result set is outside the pinned behaviour and is not
# modelled.)
# axioms-end


# pure-start
@Pure
def first_pos(src: int, cols: PSeq[int]) -> int:
    """The 1-based position of the FIRST column equal to `src` in `cols`, or 0
    if no column equals `src`. Front-recursive over the sequence so a single
    definitional unfold is available per loop step: the leading column either
    matches (position 1) or the result is shifted by one from the tail's
    position (0 staying 0 when the tail has no match)."""
    if len(cols) == 0:
        return 0
    if cols[0] == src:
        return 1
    if first_pos(src, cols.drop(1)) == 0:
        return 0
    return 1 + first_pos(src, cols.drop(1))
# pure-end


def relabel_order_term(cols: List[int], src: int, aliased: bool) -> int:
    # pre-conditions-start
    # `cols` is the result set's current column list. On the append path it is
    # genuinely mutated, so it is held at full permission (its exact post-state
    # is pinned below); the other two paths leave it unchanged. `src` and
    # `aliased` are plain scalars (no heap permission needed).
    Requires(list_pred(cols))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(cols))
    # Normal return == a valid 1-based position into the (possibly extended)
    # column list, and never 0.
    Ensures(Result() >= 1 and Result() <= len(cols))
    # MATCH: when some column already equals the term, the column list is left
    # exactly as it was and the term is referenced by the FIRST matching
    # position. The match-detection value first_pos(src, cols) is evaluated
    # entirely in the pre-state via Old(...) so it stays frame-stable even when
    # the append path mutates `cols` (a post-state re-evaluation of first_pos
    # over Old(cols) is unreliable in Nagini once `cols` has grown).
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) != 0,
                    ToSeq(cols) == Old(ToSeq(cols))
                    and Result() == Old(first_pos(src, ToSeq(cols)))))
    # APPEND: an unmatched PLAIN column is appended unchanged to the end of the
    # column list and referenced by its new (last) position. This is the path
    # that lets a derived ordering over a combined result set succeed.
    Ensures(Implies(Old(first_pos(src, ToSeq(cols))) == 0 and not aliased,
                    ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)
                    and Result() == len(cols)
                    and Result() == Old(len(cols)) + 1))
    # An unmatched ALIASED term never returns normally: the reject case must
    # signal an error rather than yield a position. This makes the raise
    # mandatory (the Exsures below only describes the state once a raise has
    # occurred; this clause forces that a raise occurs in the reject case).
    Ensures(not (Old(first_pos(src, ToSeq(cols))) == 0 and aliased))
    # REJECT: an unmatched ALIASED term raises and never mutates the column
    # list.
    Exsures(OrderTermUnmatched,
            list_pred(cols)
            and ToSeq(cols) == Old(ToSeq(cols))
            and Old(first_pos(src, ToSeq(cols))) == 0 and aliased)
    # post-conditions-end
    # impl-start
    # PRE-PATCH skeleton: scan for the first match exactly as the fixed version,
    # but the no-match branch rejects UNCONDITIONALLY (no append path) — an
    # unmatched plain column raises instead of being added. This breaks the
    # APPEND postcondition and the REJECT `Exsures` (which only sanctions the
    # raise when `aliased`).
    entry_fp = first_pos(src, ToSeq(cols))  # type: int
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    pos = 0  # type: int
    i = len(cols)
    while i > 0:
        # invariants-start
        Invariant(list_pred(cols))
        # The scan only reads the column list; it is unchanged on every path.
        Invariant(ToSeq(cols) == ToSeq(Old(cols)))
        Invariant(ToSeq(cols) == Old(ToSeq(cols)))
        Invariant(entry_fp == first_pos(src, ToSeq(cols)))
        Invariant(entry_fp == Old(first_pos(src, ToSeq(cols))))
        Invariant(0 <= i and i <= len(cols))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) == 0, pos == 0))
        Invariant(Implies(first_pos(src, ToSeq(cols).drop(i)) != 0,
                          pos == i + first_pos(src, ToSeq(cols).drop(i))
                          and 1 <= first_pos(src, ToSeq(cols).drop(i))
                          and first_pos(src, ToSeq(cols).drop(i)) <= len(cols) - i))
        Invariant(pos == 0 or (i + 1 <= pos and pos <= len(cols)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(len(ToSeq(cols).drop(i - 1)) > 0)
        Assert(ToSeq(cols).drop(i - 1)[0] == cols[i - 1])
        Assert(ToSeq(cols).drop(i - 1).drop(1) == ToSeq(cols).drop(i))
        # One definitional unfold of first_pos on the longer suffix drop(i-1):
        # head is cols[i-1], tail is drop(i).
        Assert(Implies(cols[i - 1] == src,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 1))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) == 0,
                       first_pos(src, ToSeq(cols).drop(i - 1)) == 0))
        Assert(Implies(cols[i - 1] != src
                       and first_pos(src, ToSeq(cols).drop(i)) != 0,
                       first_pos(src, ToSeq(cols).drop(i - 1))
                       == 1 + first_pos(src, ToSeq(cols).drop(i))))
        if cols[i - 1] == src:
            pos = i
        i = i - 1
    # Loop exited with i == 0, so the scanned suffix is the whole list.
    Assert(i == 0)
    Assert(ToSeq(cols).drop(0) == ToSeq(cols))
    Assert(ToSeq(cols) == ToSeq(Old(cols)))
    Assert(ToSeq(cols) == Old(ToSeq(cols)))
    Assert(entry_fp == first_pos(src, ToSeq(cols)))
    Assert(entry_fp == Old(first_pos(src, ToSeq(cols))))
    Assert(Implies(entry_fp == 0, pos == 0))
    Assert(Implies(entry_fp != 0, pos == entry_fp))
    if pos != 0:
        # MATCH: reference the first matching position; list unchanged.
        Assert(entry_fp != 0)
        Assert(pos == entry_fp)
        Assert(pos == Old(first_pos(src, ToSeq(cols))))
        Assert(pos >= 1 and pos <= len(cols))
        return pos
    # No column matched. PRE-PATCH: reject every unmatched term regardless of
    # whether it is aliased — there is no append path. This raises even for a
    # plain column (aliased == False), violating the APPEND postcondition (which
    # demands a normal return appending `src`) and the REJECT `Exsures` (whose
    # condition requires `aliased`).
    raise OrderTermUnmatched()
    # impl-end
