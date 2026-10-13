"""Twin-artifact model for django__django-12276.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A file-upload control decides whether the rendered control should advertise
  that a value is mandatory. The decision combines two facts:

    (1) the generic control-level decision for a visible control — whether a
        control of this kind would, in isolation, ask for a mandatory value;
        and

    (2) whether the field is already carrying a usable value.

  When the field is already carrying a usable value, the control must NOT
  advertise the value as mandatory (the existing value is kept simply by
  leaving the control untouched), regardless of the generic decision. When the
  field carries no such value, the decision is exactly the generic
  control-level one.

  So the decision is the conjunction:
        generic-control-decision  AND  (no usable value is already present).

The control is modelled as a minimal object carrying only the one field the
generic decision reads — whether the control is a non-interactive (hidden)
control. The presence of an already-usable value is modelled by its truth
value (a boolean): present (truthy) or absent (falsy), since the only
observation made of it is whether it is present. The generic control-level
decision is the unchanged base behaviour and is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class UploadControl:
    def __init__(self, hidden: bool) -> None:
        # Terminates outright: a single field store, no loop and no call. Level 1
        # is the floor, and it needs no room beneath it because it calls nothing
        # obligated; every obligated caller sits strictly above it.
        Requires(MustTerminate(1))
        Ensures(Acc(self.hidden) and self.hidden == hidden)  # type: ignore
        self.hidden = hidden


# axioms-start
@Pure
@ContractOnly
def generic_requires_value(hidden: bool) -> bool:
    """The unchanged generic control-level decision (the base behaviour the
    control inherits): a control advertises a mandatory value exactly when it
    is an interactive (non-hidden) control, independent of any already-present
    value. Provenance + executable soundness: mapping.md / axiom_check.py.
    """
    Ensures(Result() == (not hidden))
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def requires_value(control: UploadControl, value_present: bool) -> bool:
    # pre-conditions-start
    Requires(Acc(control.hidden, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(control.hidden, 1 / 2))
    # The decision is the conjunction of the generic control-level decision and
    # the absence of an already-usable value: a present value suppresses the
    # mandatory advertisement, and otherwise the generic decision stands.
    Ensures(Result() == (generic_requires_value(control.hidden) and not value_present))
    # Equivalently, fully decomposed over the two observed facts:
    Ensures(Implies(value_present, Result() == False))
    Ensures(Implies(not value_present, Result() == generic_requires_value(control.hidden)))
    # post-conditions-end
    # impl-start
    # Pre-patch behaviour: the control inherits only the generic control-level
    # decision and ignores whether a usable value is already present, so it
    # advertises a mandatory value even when one is already carried (the bug).
    return generic_requires_value(control.hidden)
    # impl-end
