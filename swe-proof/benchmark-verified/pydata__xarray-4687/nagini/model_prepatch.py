"""Twin-artifact model for pydata__xarray-4687.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A conditional-selection operation takes three positional operands in a
  definite order -- a predicate operand, a first-choice operand, and a
  second-choice operand -- each carrying an attribute payload, and produces a
  result whose attribute payload is governed by an attribute-handling mode:

    * mode DEFAULT  -- the historical behaviour: the result carries no
      attribute payload (the empty payload), regardless of the operands.
    * mode PRESERVE -- the result carries exactly the attribute payload of the
      first-choice operand (the operand at positional slot one), so that an
      attribute payload on that operand survives the selection rather than
      being discarded.

The selection of which operand's payload survives is the load-bearing
behaviour: under PRESERVE the surviving payload is the one at positional slot
one (the first-choice operand), never that of the predicate operand
(slot zero) nor that of the second-choice operand (slot two), and never the
empty payload when the first-choice operand carries one.

Attribute payloads are modelled as `List[int]` (an opaque content-identified
payload; equality of payloads is content equality). The three operands'
payloads are presented in positional order as a `List[List[int]]` of length 3.
The DEFAULT mode resolves through an unchanged global-option reader, modelled
by the `default_mode_drops` axiom: under the ambient default configuration that
reader yields the dropping (empty-payload) behaviour.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def default_mode_drops() -> bool:
    """Unchanged global-option reader: when the attribute-handling mode is left
    unspecified, the ambient default configuration resolves it to the dropping
    behaviour (the result carries the empty attribute payload). Provenance and
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() == True)
# axioms-end


# pure-start
@Pure
def empty_payload() -> PSeq[int]:
    """The empty attribute payload."""
    return PSeq(0).take(0)
# pure-end


def select_payload(attrs: List[List[int]], mode: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(attrs), 1 / 2))
    Requires(len(attrs) == 3)
    Requires(Acc(list_pred(attrs[1]), 1 / 2))
    # mode 0 == DEFAULT (unspecified), mode 1 == PRESERVE
    Requires(mode == 0 or mode == 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(attrs), 1 / 2))
    Ensures(len(attrs) == 3)
    Ensures(Acc(list_pred(attrs[1]), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # DEFAULT mode drops every operand's payload: the result is empty.
    Ensures(Implies(mode == 0, ToSeq(Result()) == empty_payload()))
    # PRESERVE mode keeps exactly the first-choice operand's payload (index 1):
    # not the predicate operand's (index 0), not the second-choice operand's
    # (index 2), and not the empty payload when index 1 carries one.
    Ensures(Implies(mode == 1, ToSeq(Result()) == ToSeq(attrs[1])))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the attribute-handling mode is never threaded into
    # the underlying combine step, so the result always carries the dropping
    # (empty) payload regardless of the requested mode.
    result = []  # type: List[int]
    return result
    # impl-end
