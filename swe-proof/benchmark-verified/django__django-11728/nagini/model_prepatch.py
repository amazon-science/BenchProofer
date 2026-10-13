"""Twin-artifact model for django__django-11728.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A capture group inside a URL/route pattern is delimited by a run of
  parentheses: it opens with a `(` (already consumed before the scan begins,
  so the scan starts already one level deep) and closes at the *matching*
  closing parenthesis. Nesting is honoured -- an unescaped `(` opens a deeper
  level, an unescaped `)` closes one; a parenthesis immediately preceded by a
  backslash is escaped and does not change the nesting depth. The end of the
  group is the position of the parenthesis that returns the depth to zero.

  The desired behaviour, derived from the problem statement (a group that ends
  at the very end of the pattern -- with no trailing `/` or `$` -- must still be
  recognised and have its span determined), is:

    The captured span of a group extends through and INCLUDING its matching
    closing parenthesis, whether or not any further characters follow it. In
    particular, when the matching closing parenthesis is the final character of
    the scanned region, the span must still be reported (it must not require a
    trailing character to be detected).

  Concretely, scanning the region that begins immediately inside the opening
  parenthesis, the matching close lies at offset `k` (the first position whose
  arrival drives the depth to zero); the captured span end -- relative to the
  start of that scanned region -- is `k + 1`, i.e. one past the matching close,
  for every group whose matching close exists in the region (including when it
  is the last character).

The pattern is modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the depth-tracking scan is modelled deeply over `PSeq[int]`.
The two routines below differ only in the base offset at which their scan
region begins (a type-refinement binding documented in mapping.md); both report
the same scan-relative span end.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The depth-tracking scan
#  that determines a group's matching-close position is modelled DEEPLY below
#  over exact code-point arithmetic (close_off / step_bal). The str<->List[int]
#  carrier and the absolute position at which each scan region begins are the
#  type-refinement boundary documented in mapping.md, not axioms.)
# axioms-end


# pure-start
@Pure
def step_bal(c: int, prev: int, bal: int) -> int:
    """The unmatched-open-parenthesis depth after reading code point `c` whose
    predecessor was `prev`, starting from depth `bal`. An unescaped `(` (code
    40, predecessor not the backslash code 92) opens a level; an unescaped `)`
    (code 41) closes one; everything else leaves the depth unchanged."""
    if c == 40 and prev != 92:   # unescaped '('
        return bal + 1
    if c == 41 and prev != 92:   # unescaped ')'
        return bal - 1
    return bal


@Pure
def close_off(s: PSeq[int], bal: int, prev: int) -> int:
    """Offset within `s` of the character whose arrival first drives the
    running depth (starting at `bal`, predecessor `prev`) to zero -- i.e. the
    matching closing parenthesis of the group already open at depth `bal`.
    Front-recursive (a single unfold per scanned character). Total and
    terminating: if the depth never reaches zero within `s` it returns
    `len(s)`."""
    Ensures(Result() >= 0 and Result() <= len(s))
    if len(s) == 0:
        return 0
    nb = step_bal(s[0], prev, bal)
    if nb == 0:
        return 0
    return 1 + close_off(s.drop(1), nb, s[0])
# pure-end


def named_group_pattern_end(region: List[int], prev0: int) -> int:
    # pre-conditions-start
    # `region` is the slice beginning immediately inside the group's opening
    # parenthesis (depth already 1); `prev0` is the code point just before it
    # (so escape state is carried in). The group's matching close exists within
    # the region.
    Requires(Acc(list_pred(region), 1 / 2))
    Requires(close_off(ToSeq(region), 1, prev0) < len(region))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(region), 1 / 2))
    # The reported span end (relative to the region start) is one past the
    # matching close -- always, including when the close is the last character.
    Ensures(Result() == close_off(ToSeq(region), 1, prev0) + 1)
    Ensures(1 <= Result() and Result() <= len(region))
    # post-conditions-end
    # impl-start
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region):
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        # Termination: `i` rises by exactly 1 on every pass that reaches the
        # loop head again (the early `break` only exits sooner) and
        # `len(region)` is fixed, so `len(region) - i + 1` strictly decreases
        # and is >= 2 at every loop head, where `i < len(region)` holds.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        # PRE-PATCH (buggy): the depth==0 test is at the TOP of the loop body,
        # before the current character is processed. The depth only reaches
        # zero after the closing parenthesis has been read, so detection is
        # deferred to the NEXT iteration; when the closing parenthesis is the
        # final character of the region that next iteration never runs and the
        # span is never recorded.
        if bal == 0:
            res = i
            break
        val = region[i]
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
    return res
    # impl-end


def unnamed_group_pattern_end(region: List[int], prev0: int) -> int:
    # pre-conditions-start
    # `region` is the slice beginning immediately inside the unnamed group's
    # opening parenthesis (depth already 1); `prev0` is the preceding code
    # point. The matching close exists within the region.
    Requires(Acc(list_pred(region), 1 / 2))
    Requires(close_off(ToSeq(region), 1, prev0) < len(region))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(region), 1 / 2))
    Ensures(Result() == close_off(ToSeq(region), 1, prev0) + 1)
    Ensures(1 <= Result() and Result() <= len(region))
    # post-conditions-end
    # impl-start
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res
    # impl-end
