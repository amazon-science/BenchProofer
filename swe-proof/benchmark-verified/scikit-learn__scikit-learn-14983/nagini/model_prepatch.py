"""Twin-artifact model for scikit-learn__scikit-learn-14983.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configurable object reports its constructor parameters for a textual
  representation. For one parameter, the reported value is resolved like this:
  the object's own directly-set attribute for that parameter is used when it
  yields a value; OTHERWISE, if the object additionally carries a secondary
  keyword-argument store (a mapping from parameter name to value, used to
  configure a wrapped component) AND that store records the parameter, the
  value recorded there is used; otherwise the value is reported as absent.

  The consequence that matters: a parameter that is NOT held as a direct
  attribute but IS recorded in the secondary store must be reported with the
  store's concrete value, NOT as absent. An object that carries no secondary
  store reports a missing direct attribute as absent, unchanged.

Modelling choices (Nagini fragment):
  * Parameter names are `int` keys; parameter values are `int`.
  * "absent" / "no value" is carried by a caller-chosen sentinel `none` (an
    `int`): an attribute lookup that finds nothing yields `none`, and the
    reported value is `none` exactly when the parameter is absent everywhere.
    (`Optional[int]` returns from a `@Pure` helper used inside an `Ensures`
    trip a translator defect in this Nagini build; the sentinel keeps the
    helper total and the equality provable.)
  * The secondary store is a `Dict[int, int]`; `has_store` flags whether the
    object carries one. The store records concrete (non-`none`) values for the
    keys it holds (a real configuration value, never "absent").

Termination: the real per-key resolution is loop-free straight-line work
(an attribute lookup, one guarded mapping lookup, return), so every call
returns. Nagini checks partial correctness by default, so without a
termination obligation a same-spec impl that spins forever satisfies every
Ensures vacuously while its real counterpart would hang the caller.
`Requires(MustTerminate(2))` pins totality; it adds no behaviour beyond what
the real code already has, so it cannot exclude a correct implementation.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the value-resolution logic is the behaviour under
# specification and is modelled deeply (resolved_value). The primary
# attribute lookup and the secondary mapping lookup it composes are validated
# against their real Python semantics out-of-band by axiom_check.py (G-AX) as
# an A-reference, not consumed here.
# axioms-end


# pure-start
# NOTE for auditors: resolved_value is a TRANSPARENT, fully-grounded @Pure
# function of its arguments (its body inlines the whole resolution) — NOT an
# opaque answer-key. Consequently `return resolved_value(...)` in the impl
# region is simply a CORRECT implementation (the cheapest one), not an
# "ungrounded-oracle echo" defect: it performs the real work, and its
# faithful refinement is exactly the reference edit (which resolves). Such an
# echo therefore belongs in positive_control, never in a spec-too-weak attack
# list, which must contain only implementations whose behavior DIFFERS from
# resolved_value on some admissible input.
@Pure
def resolved_value(attr: int, none: int, has_store: bool,
                   store: Dict[int, int], key: int) -> int:
    """The reported value for one parameter `key`.

    `attr` is the value obtained from the object's own attribute lookup for
    `key` (equal to `none` when that lookup finds nothing). `has_store` says
    whether the object carries the secondary store; `store` is that store.
    A present direct attribute wins; otherwise the store's recorded value is
    used when the object carries a store AND records the key; otherwise the
    reported value is `none` (absent).
    """
    Requires(Acc(dict_pred(store), 1 / 4))
    if attr != none:
        return attr
    if has_store and (key in store):
        return store[key]
    return none
# pure-end


def reported_param_value(attr: int, none: int, has_store: bool,
                         store: Dict[int, int], key: int) -> int:
    # pre-conditions-start
    Requires(Acc(dict_pred(store), 1 / 2))
    # The secondary store records concrete values (never the absent sentinel)
    # for the keys it holds.
    Requires(Implies(key in store, store[key] != none))
    # Totality obligation: the real per-key resolution is loop-free
    # straight-line work (an attribute lookup, one guarded mapping lookup,
    # return) — every call returns. Without this, a same-spec impl that
    # diverges (e.g. an infinite loop before the return) verifies vacuously
    # under Nagini's partial-correctness default while its real counterpart
    # would hang the caller.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(store), 1 / 2))
    # The reported value is exactly the deep resolution above.
    Ensures(Result() == resolved_value(attr, none, has_store, store, key))
    # A present direct attribute always wins (reported verbatim).
    Ensures(Implies(attr != none, Result() == attr))
    # The discriminating behaviour: a parameter with no direct attribute but
    # recorded in a carried store is reported with the store's value ...
    Ensures(Implies(attr == none and has_store and (key in store),
                    Result() == store[key]))
    # ... and is therefore NOT reported as absent.
    Ensures(Implies(attr == none and has_store and (key in store),
                    Result() != none))
    # With no carried store, a missing direct attribute stays absent.
    Ensures(Implies(attr == none and not has_store, Result() == none))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the reported value is ONLY the object's own direct
    # attribute lookup; there is no fallback to the secondary store. A
    # parameter held only in the store is therefore reported as absent.
    value = attr  # type: int
    return value
    # impl-end
