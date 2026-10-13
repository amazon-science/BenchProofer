"""Twin-artifact model for django__django-12663.

Behavioural contract (stated as desired behaviour, not as an edit):

  A selected item carries two integer field identities: ``source`` and
  ``field``. ``output_field_identity`` returns a single field identity for the
  item, chosen as follows:

    * if ``source`` is a usable (nonzero) identity, the result is ``source``;
    * otherwise the result is ``field``.

  ``field`` is always a usable (nonzero) identity. ``source`` may be the
  sentinel identity ``0``, meaning "no usable source identity"; any nonzero
  ``source`` is a usable, distinct identity. The discriminating inputs are
  those where ``source`` is nonzero and differs from ``field``: there the
  result must be ``source``, never ``field``.

A selected item is modelled as a minimal object exposing only these two integer
identities. The choice is modelled deeply (pure choose-one-of-two logic); the
behaviour it stands on is validated out-of-band by axiom_check.py (G-AX) as an
A-reference, not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the choose-one-of-two selection is modelled deeply. The
# behaviour it stands on is validated against its real semantics out-of-band by
# axiom_check.py (G-AX) as an A-reference, not consumed here.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Selection:
    def __init__(self) -> None:
        # source: a field identity; 0 == "no usable source identity".
        # field:  a field identity, always usable (!= 0).
        # Terminates: two unconditional int field stores, no loop and no call.
        # Level 1 is strictly below every obligated caller (output_field_identity
        # is at 6), so an obligated caller may construct a Selection; without
        # this the constructor is unobligated and Nagini reports "Callee
        # __init__ might not take all unsatisfied obligations from the caller."
        Requires(MustTerminate(1))
        Ensures(Acc(self.source) and Acc(self.field))  # type: ignore
        Ensures(self.source == 0)  # type: ignore
        Ensures(self.field == 1)  # type: ignore
        self.source = 0  # type: int
        self.field = 1  # type: int


def output_field_identity(sel: Selection) -> int:
    # pre-conditions-start
    # The selected item is read-only: required (and ensured) at fractional
    # permission only. A full-permission read-only input referenced in the
    # postcondition could be satisfied by an implementation that overwrites the
    # item's fields instead of choosing between them, so permission is shared.
    Requires(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
    # The ``field`` identity is always usable (nonzero).
    Requires(sel.field != 0)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(sel.source, 1 / 2) and Acc(sel.field, 1 / 2))
    # The item is left exactly as it was (read-only).
    Ensures(sel.source == Old(sel.source))
    Ensures(sel.field == Old(sel.field))
    # The result is ``sel.source`` whenever it is a usable (nonzero) identity,
    # and ``sel.field`` otherwise. These two clauses together pin the selection
    # on every input: the discriminating case is an item whose ``source`` is
    # nonzero and differs from ``field`` (sel.source != 0 and
    # sel.source != sel.field) — there the result MUST be sel.source, never
    # sel.field.
    Ensures(Implies(sel.source != 0, Result() == sel.source))
    Ensures(Implies(sel.source == 0, Result() == sel.field))
    # post-conditions-end
    # impl-start
    # select = self.select[0]
    # return getattr(select, 'target', None) or select.field
    source = sel.source
    if source != 0:
        return source
    return sel.field
    # impl-end
