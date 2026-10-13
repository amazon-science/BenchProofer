"""Twin-artifact model for django__django-13363.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two date/time database casting expressions each select the time-zone name
  that the cast is performed in, and hand that name to an (unchanged) backend
  routine that builds the SQL. The selection must honour an OPTIONAL explicit
  time zone attached to the expression:

    * When time-zone support is OFF, the cast uses no time zone at all
      (the selected name is absent / `None`).
    * When time-zone support is ON and an explicit time zone HAS been supplied,
      the cast uses the name of THAT supplied time zone.
    * When time-zone support is ON and NO explicit time zone was supplied, the
      cast falls back to the name of the ambient/currently-active time zone.

  In particular, supplying an explicit time zone that differs from the ambient
  one must change the selected name to the supplied one (it must NOT be
  silently discarded in favour of the ambient name).

Both casting expressions select the name by the same rule; they differ only in
which unchanged backend routine ultimately consumes it. The model therefore
returns the selected name itself (an `Optional[List[int]]` of code points, with
`None` for "no time zone"); a time zone is abstracted by its name string, so the
ambient name and a supplied time zone's name are both `List[int]`.

No callee is axiomatized: the selection is conditional logic over the inputs,
modelled deeply; the unchanged name-of-a-time-zone lookup is the identity under
the name abstraction, and the unchanged backend SQL builder is a downstream,
deterministic consumer of the selected name (see refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def selected_tzname(use_tz: bool, tzinfo: Optional[List[int]],
                    current_name: List[int]) -> Optional[List[int]]:
    """The time-zone name the cast should use.

    Absent (`None`) when time-zone support is off; the supplied time zone's
    name when one is supplied; otherwise the ambient time zone's name."""
    Requires(Acc(list_pred(current_name), 1 / 8))
    Requires(Implies(tzinfo is not None, Acc(list_pred(tzinfo), 1 / 8)))
    if not use_tz:
        return None
    if tzinfo is not None:
        return tzinfo
    return current_name
# pure-end


def date_cast_tzname(use_tz: bool, tzinfo: Optional[List[int]],
                     current_name: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    # The ambient name and the (optional) supplied time-zone name are read-only;
    # required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(current_name), 1 / 2))
    Requires(Implies(tzinfo is not None, Acc(list_pred(tzinfo), 1 / 2)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(current_name), 1 / 2))
    Ensures(Implies(tzinfo is not None, Acc(list_pred(tzinfo), 1 / 2)))
    # The selected name is exactly the rule above: absent when off; the supplied
    # time zone's name when supplied; the ambient name otherwise. Pins the
    # discriminating behaviour (a supplied time zone is honoured, not discarded).
    Ensures(Result() is selected_tzname(use_tz, tzinfo, current_name))
    # post-conditions-end
    # impl-start
    tzname = None  # type: Optional[List[int]]
    if use_tz:
        tzname = current_name
    return tzname
    # impl-end


def time_cast_tzname(use_tz: bool, tzinfo: Optional[List[int]],
                     current_name: List[int]) -> Optional[List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(current_name), 1 / 2))
    Requires(Implies(tzinfo is not None, Acc(list_pred(tzinfo), 1 / 2)))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(current_name), 1 / 2))
    Ensures(Implies(tzinfo is not None, Acc(list_pred(tzinfo), 1 / 2)))
    Ensures(Result() is selected_tzname(use_tz, tzinfo, current_name))
    # post-conditions-end
    # impl-start
    tzname = None  # type: Optional[List[int]]
    if use_tz:
        if tzinfo is None:
            tzname = current_name
        else:
            tzname = tzinfo
    return tzname
    # impl-end
