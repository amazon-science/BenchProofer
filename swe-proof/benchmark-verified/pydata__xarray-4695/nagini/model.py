"""Twin-artifact model for pydata__xarray-4695.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A label-based selection facade receives a mapping from axis names to label
  selectors and forwards it to an underlying label selector. The underlying
  selector exposes, besides the axis mapping, a small predefined collection of
  RESERVED option names (here: the inexact-match option, modelled as a single
  reserved name). The facade must forward EVERY entry of the incoming mapping as an
  axis selector, and must leave the reserved option at its default value,
  for ANY incoming mapping -- including a mapping whose axis name happens to
  coincide with a reserved option name.

  Concretely, given the incoming mapping presented as a parallel pair of
  sequences (axis-name ids `names`, label selectors `values`):

    * the axis selectors actually forwarded to the underlying selector are the
      WHOLE incoming mapping -- the forwarded axis-name sequence equals `names`
      in full, with no entry diverted away because its name collides with a
      reserved option name (`forward_axis_names`); and

    * the value bound to the reserved option is its DEFAULT sentinel, never a
      label selector taken from the incoming mapping (`bound_reserved_option`).

The load-bearing behaviour is that an axis whose name equals the reserved
option name (RESERVED_NAME) is still forwarded as an axis selector and does
NOT leak into the reserved option slot. The reserved option therefore stays
at DEFAULT_OPTION for every input, and the forwarded axes are complete.

Mapping entries are modelled as parallel `List[int]`: `names[k]` is an opaque
axis-name id, `values[k]` the (opaque) label selector for that axis. Names and
the reserved sentinels are small int ids. The specification is carried over
`PSeq[int]` via `ToSeq`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed axioms: the forwarding/routing behaviour is modelled deeply)
# axioms-end


# pure-start
@Pure
def RESERVED_NAME() -> int:
    """Axis-name id that collides with a reserved option name of the underlying
    selector (the inexact-match option). The discriminating input."""
    return 7


@Pure
def DEFAULT_OPTION() -> int:
    """Default value of the reserved option (its unset sentinel). Distinct from
    every label selector id used as a mapping value (selectors are >= 0)."""
    return -1


@Pure
def option_after_namekeyed(names: PSeq[int], values: PSeq[int]) -> int:
    """The value the reserved option would take under a NAME-KEYED routing that
    diverts a colliding axis into the reserved slot: the value of the last
    mapping entry whose axis name equals RESERVED_NAME, else the default
    sentinel. Front-recursive so one unfold is available per loop step. This is
    the routing the correct facade must NOT perform; it appears here only so
    the impl can compute and reject it."""
    Requires(len(names) == len(values))
    if len(names) == 0:
        return DEFAULT_OPTION()
    if names[len(names) - 1] == RESERVED_NAME():
        return values[len(values) - 1]
    return option_after_namekeyed(names.take(len(names) - 1),
                                  values.take(len(values) - 1))
# pure-end


def forward_axis_names(names: List[int], values: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(names) == len(values))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Every incoming entry is forwarded as an axis selector: the forwarded
    # axis-name sequence is the WHOLE incoming name sequence (no entry diverted
    # because its name collides with the reserved option name).
    Ensures(ToSeq(Result()) == ToSeq(names))
    # post-conditions-end
    # impl-start
    # Forward the mapping positionally: every entry, including one whose name
    # equals RESERVED_NAME, is kept as an axis selector.
    forwarded = []  # type: List[int]
    i = 0
    while i < len(names):
        # invariants-start
        Invariant(Acc(list_pred(names), 1 / 2))
        Invariant(Acc(list_pred(values), 1 / 2))
        Invariant(len(names) == len(values))
        Invariant(Acc(list_pred(forwarded)))
        Invariant(0 <= i and i <= len(names))
        Invariant(ToSeq(forwarded) == ToSeq(names).take(i))
        Invariant(MustTerminate(len(names) - i + 1))
        # invariants-end
        forwarded.append(names[i])
        i = i + 1
    Assert(ToSeq(names).take(len(names)) == ToSeq(names))
    return forwarded
    # impl-end


def bound_reserved_option(names: List[int], values: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(values), 1 / 2))
    Requires(len(names) == len(values))
    # Label selectors are non-negative ids; the default sentinel (-1) is
    # reserved and never appears as a mapping value.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(values),
                                            values[k] >= 0),
                                    [[values[k]]])))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(values), 1 / 2))
    # The reserved option keeps its default for EVERY input -- a colliding axis
    # (name == RESERVED_NAME) is forwarded as an axis selector, never bound to
    # the reserved option slot.
    Ensures(Result() == DEFAULT_OPTION())
    # post-conditions-end
    # impl-start
    # Positional forwarding: the reserved option is not fed from the mapping.
    option = DEFAULT_OPTION()
    return option
    # impl-end
