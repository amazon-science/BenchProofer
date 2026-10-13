"""Twin-artifact model for pytest-dev__pytest-6202.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collected node's dotted path relative to its containing module is formed
  from an ordered list of name parts (one per surviving ancestor: enclosing
  classes and the node itself). The dotted path is EXACTLY the join of those
  parts with a single '.' separator between consecutive parts -- and nothing
  else. No further character substitution is applied to the joined string.

  In particular, when a part itself contains the two-character sequence '.['
  (as a parametrised test's name does, e.g. a part `testmethod_two[.[]`), that
  sequence is preserved verbatim in the result: the result is the faithful
  dot-join of the parts, so a '.[' occurring inside any part survives unchanged.

Each name part is modelled as `PSeq[int]` of Unicode code points (Nagini bans
`str` indexing) and the list of parts as `PSeq[PSeq[int]]`. The dot-join is
modelled DEEPLY as a front-recursive fold (`join_dot`) with separator code
point 46 ('.'); its equality to the real `str.join` callee is checked
out-of-band by axiom_check.py (G-AX), NOT consumed as an axiom.

The real `getmodpath` always RETURNS its dotted path (one finite pass over the
parts), so termination is part of the specified behaviour: `modpath_of` carries
a `MustTerminate` obligation (Nagini is partial-correctness by default, so
without the obligation a diverging implementation would satisfy the
postcondition vacuously).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the dot-join is modelled deeply below as
#  `join_dot` and validated == the real str.join callee out-of-band by
#  axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def join_dot(parts: PSeq[PSeq[int]]) -> PSeq[int]:
    """The dot-join of a sequence of name parts: parts[0] then, for each later
    part, a single '.' (code point 46) followed by that part. Front-recursive
    (one unfold per part) so a backward impl loop can discharge the value
    equality. The empty list joins to the empty sequence; a single part joins
    to itself."""
    if len(parts) == 0:
        return PSeq(0).take(0)
    if len(parts) == 1:
        return parts[0]
    return (parts[0] + PSeq(46)) + join_dot(parts.drop(1))
# pure-end


def modpath_of(parts: PSeq[PSeq[int]]) -> PSeq[int]:
    # pre-conditions-start
    # The path is built from at least one name part (the node's own name).
    Requires(len(parts) >= 1)
    # TERMINATION: the real getmodpath builds the path in one finite pass over
    # `parts` and always returns. Without this obligation a diverging
    # implementation satisfies the postcondition vacuously; the obligation
    # rejects any such implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The dotted path is EXACTLY the dot-join of the parts -- no further
    # substitution is applied. A '.[' inside any part therefore survives.
    Ensures(Result() == join_dot(parts))
    # post-conditions-end
    # impl-start
    result = parts[len(parts) - 1]  # type: PSeq[int]
    i = len(parts) - 1
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(parts) - 1)
        # `result` is the dot-join of the suffix parts[i:].
        Invariant(result == join_dot(parts.drop(i)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure i + 1.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(parts.drop(i - 1)[0] == parts[i - 1])
        Assert(parts.drop(i - 1).drop(1) == parts.drop(i))
        result = (parts[i - 1] + PSeq(46)) + result
        i = i - 1
    return result
    # impl-end
