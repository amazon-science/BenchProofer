"""Twin-artifact model for django__django-11095.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An administration view exposes a configured collection of related-record
  editors (each identified here by an integer class identifier). Two cooperating
  operations are specified.

    (1) A selection hook reports WHICH editors apply to a given access context
        (a request and an optional record). Its default report is exactly the
        configured collection, in the configured order — neither dropping,
        adding, nor reordering any entry.

    (2) The materialisation operation that turns the selection into live editor
        objects must build them from the SELECTION HOOK'S report, NOT from the
        configured collection directly: it instantiates one editor per reported
        identifier, in the reported order, and (when an access context is
        present) keeps exactly those whose access context grants any of the
        relevant permissions, in order. So a context in which the hook reports a
        narrowed (or otherwise altered) collection yields editors built from the
        narrowed report — were materialisation to read the configured collection
        instead, an altered report would be ignored.

The administration view is modelled as a minimal class carrying only the touched
collections: the configured editor identifiers (`configured`), the selection
hook's reported identifiers for the current context (`reported`), and a
per-reported-entry permission flag (`granted`) recording whether the access
context grants that entry. Lists of editor-class identifiers are modelled as
`List[int]`; the specification is carried over `PSeq[int]` via `ToSeq`. No
library callee is axiomatized: both operations are pure collection/control-flow
logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class AdminView:
    def __init__(self) -> None:
        Ensures(Acc(self.configured) and Acc(list_pred(self.configured)))  # type: ignore
        Ensures(Acc(self.reported) and Acc(list_pred(self.reported)))  # type: ignore
        Ensures(Acc(self.granted) and Acc(list_pred(self.granted)))  # type: ignore
        Ensures(len(self.configured) == 0)  # type: ignore
        Ensures(len(self.reported) == 0)  # type: ignore
        Ensures(len(self.granted) == 0)  # type: ignore
        self.configured = []  # type: List[int]
        self.reported = []  # type: List[int]
        self.granted = []  # type: List[int]


# axioms-start
# No consumed axioms: both operations are pure collection/control-flow logic,
# modelled deeply. The default hook reports the configured collection; the
# materialisation builds one live editor per reported identifier (kept when its
# context grants access). There is no unchanged library callee whose contract
# the proof depends on.
# axioms-end


# pure-start
@Pure
def kept(reported: PSeq[int], granted: PSeq[int]) -> PSeq[int]:
    """The subsequence of `reported` whose aligned `granted` flag is set, in the
    same order. Front-recursive so a single unfold is available per loop step: a
    context that grants every entry keeps the whole report."""
    Requires(len(reported) == len(granted))
    if len(reported) == 0:
        return PSeq(0).take(0)
    if granted[0] != 0:
        return PSeq(reported[0]) + kept(reported.drop(1), granted.drop(1))
    return kept(reported.drop(1), granted.drop(1))
# pure-end


def select_applicable_editors(self: AdminView, request: int, obj: Optional[int]) -> List[int]:
    # pre-conditions-start
    # Read-only over the whole view: fractional permission on every collection.
    Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Ensures(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Ensures(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) The default selection report is exactly the configured collection, in
    # the configured order: nothing dropped, added, or reordered.
    Ensures(ToSeq(Result()) == ToSeq(self.configured))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = len(self.configured)
    while i > 0:
        # invariants-start
        Invariant(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(self.configured))
        Invariant(ToSeq(result) == ToSeq(self.configured).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(self.configured).drop(i - 1)[0] == self.configured[i - 1])
        Assert(ToSeq(self.configured).drop(i - 1).drop(1) == ToSeq(self.configured).drop(i))
        result = [self.configured[i - 1]] + result
        i = i - 1
    return result
    # impl-end


def materialize_editors(self: AdminView, request: int, obj: Optional[int]) -> List[int]:
    # pre-conditions-start
    # Read-only over the whole view. The selection hook's report and its aligned
    # permission flags are index-aligned.
    Requires(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Requires(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Requires(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Requires(len(self.reported) == len(self.granted))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured, 1 / 2) and Acc(list_pred(self.configured), 1 / 2))
    Ensures(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
    Ensures(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(self.reported) == len(self.granted))
    # (2) The materialised editors are built from the SELECTION HOOK'S report
    # (self.reported), keeping exactly those whose access context grants the
    # entry, in order. The class identity of editor k is the reported identifier
    # it was built from. Pinned to `reported`, NOT to `configured`: an altered
    # report (a context the hook narrows) yields editors built from that report.
    Ensures(ToSeq(Result()) == kept(ToSeq(self.reported), ToSeq(self.granted)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = len(self.reported)
    while j > 0:
        # invariants-start
        Invariant(Acc(self.reported, 1 / 2) and Acc(list_pred(self.reported), 1 / 2))
        Invariant(Acc(self.granted, 1 / 2) and Acc(list_pred(self.granted), 1 / 2))
        Invariant(len(self.reported) == len(self.granted))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(self.reported))
        Invariant(len(ToSeq(self.reported).drop(j)) == len(ToSeq(self.granted).drop(j)))
        Invariant(ToSeq(result) == kept(ToSeq(self.reported).drop(j), ToSeq(self.granted).drop(j)))
        Invariant(MustTerminate(j + 1))
        # invariants-end
        Assert(ToSeq(self.reported).drop(j - 1)[0] == self.reported[j - 1])
        Assert(ToSeq(self.reported).drop(j - 1).drop(1) == ToSeq(self.reported).drop(j))
        Assert(ToSeq(self.granted).drop(j - 1)[0] == self.granted[j - 1])
        Assert(ToSeq(self.granted).drop(j - 1).drop(1) == ToSeq(self.granted).drop(j))
        cls = self.reported[j - 1]
        if self.granted[j - 1] != 0:
            result = [cls] + result
        j = j - 1
    return result
    # impl-end
