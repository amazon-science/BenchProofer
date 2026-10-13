"""Twin-artifact model for pydata__xarray-2905.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an arbitrary incoming value is prepared for storage, there is a single
  normalization step that decides whether to replace the value with the
  contents exposed under its ``values`` attribute (so that an already
  self-describing container is not nested inside another container).

  The desired behaviour: this replacement is performed ONLY when the value is
  one of the specific self-describing container kinds the system recognizes.
  For every other value — INCLUDING a plain object that merely happens to
  expose a ``values`` attribute — the value must pass through this step
  UNCHANGED, so that such objects are stored as themselves rather than being
  silently coerced to whatever their ``values`` attribute holds. Merely
  exposing a ``values`` attribute is NOT sufficient to trigger the replacement.

The incoming value is modelled as a minimal class carrying only the facts this
step inspects: whether it is one of the recognized self-describing container
kinds, whether it exposes a ``values`` attribute, and the identity tags of the
value itself and of its ``values`` contents. The step returns the identity tag
of the value that survives normalization.

A real-world invariant constrains the inputs: every recognized self-describing
container kind does expose a ``values`` attribute (so being a recognized kind
is a strictly more specific condition than merely exposing the attribute).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


class Incoming:
    """A value arriving at the normalization step. ``identity`` tags the value
    itself; ``values_identity`` tags what its ``values`` attribute holds (only
    meaningful when ``exposes_values``)."""

    def __init__(self, is_recognized_container: bool, exposes_values: bool,
                 identity: int, values_identity: int) -> None:
        Requires(Implies(is_recognized_container, exposes_values))
        Ensures(Acc(self.is_recognized_container, 1 / 2))  # type: ignore
        Ensures(Acc(self.exposes_values, 1 / 2))           # type: ignore
        Ensures(Acc(self.identity, 1 / 2))                 # type: ignore
        Ensures(Acc(self.values_identity, 1 / 2))          # type: ignore
        Ensures(self.is_recognized_container == is_recognized_container)  # type: ignore
        Ensures(self.exposes_values == exposes_values)     # type: ignore
        Ensures(self.identity == identity)                 # type: ignore
        Ensures(self.values_identity == values_identity)   # type: ignore
        Ensures(Implies(self.is_recognized_container, self.exposes_values))  # type: ignore
        self.is_recognized_container = is_recognized_container
        self.exposes_values = exposes_values
        self.identity = identity
        self.values_identity = values_identity


# axioms-start
# (no @ContractOnly callees: the changed decision is modelled deeply below.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def normalize_self_describing(data: Incoming) -> int:
    # pre-conditions-start
    Requires(Acc(data.is_recognized_container, 1 / 2))
    Requires(Acc(data.exposes_values, 1 / 2))
    Requires(Acc(data.identity, 1 / 2))
    Requires(Acc(data.values_identity, 1 / 2))
    # the real-world invariant: a recognized container always exposes .values.
    Requires(Implies(data.is_recognized_container, data.exposes_values))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(data.is_recognized_container, 1 / 2))
    Ensures(Acc(data.exposes_values, 1 / 2))
    Ensures(Acc(data.identity, 1 / 2))
    Ensures(Acc(data.values_identity, 1 / 2))
    # the read-only input is unchanged.
    Ensures(data.is_recognized_container == Old(data.is_recognized_container))
    Ensures(data.exposes_values == Old(data.exposes_values))
    Ensures(data.identity == Old(data.identity))
    Ensures(data.values_identity == Old(data.values_identity))
    # The surviving value is the .values contents iff the input is a recognized
    # self-describing container; otherwise the value passes through unchanged.
    Ensures(Implies(data.is_recognized_container,
                    Result() == data.values_identity))
    Ensures(Implies(not data.is_recognized_container,
                    Result() == data.identity))
    # post-conditions-end
    # impl-start
    if data.is_recognized_container:
        result = data.values_identity
    else:
        result = data.identity
    return result
    # impl-end
