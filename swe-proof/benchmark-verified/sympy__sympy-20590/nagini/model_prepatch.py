"""Twin-artifact model for sympy__sympy-20590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An instance of the core expression type must carry NO open per-instance
  namespace, so that binding an attribute name that the type did not pre-declare
  is rejected rather than silently stored.

  Whether an instance carries such an open namespace is decided entirely by the
  chain of types it is built from (its method-resolution order, excluding the
  universal root, which never contributes a namespace). The rule is the one the
  runtime applies:

    * an instance carries an open namespace iff AT LEAST ONE type in that chain
      leaves its instance layout open (does not pin a closed set of attribute
      slots);
    * equivalently, an instance carries NO open namespace iff EVERY type in the
      chain pins a closed layout.

  The behaviour pinned here is the consequence for attribute binding:

    * if the instance carries no open namespace (every type in the chain pins a
      closed layout) then binding an undeclared attribute name is REFUSED — the
      runtime signals the caller with an attribute error and stores nothing;
    * otherwise the open namespace absorbs the binding and it succeeds.

  In particular, for the core expression type's own chain — in which EVERY type
  is required to pin a closed layout — an instance must carry no open namespace,
  so binding an undeclared attribute must be refused.

The inheritance chain is modelled as a `PSeq[bool]`: one flag per type (root
excluded), True iff that type pins a closed layout. The closed-layout predicate
folds front-recursively so a single unfold is available per chain step. The
attribute error is a user-defined exception class (a builtin exception in an
`Exsures` crashes the Nagini translator; mapping.md). No callee is axiomatized:
the layout/namespace rule is modelled deeply.

TERMINATION. Every modelled operation is a bounded, loop-free decision the real
runtime always completes (attribute binding either stores or raises; reading a
class's slot declaration is immediate). Nagini verifies partial correctness
only, so each function carries a `MustTerminate` obligation: without it a
diverging body (an infinite loop before the return) would satisfy every
postcondition vacuously — in particular `Ensures(False)` — yet never deliver
its result, which does not resolve the F2P.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class AttributeBindingRefused(Exception):
    """Signals that binding an undeclared attribute name was refused because the
    instance carries no open namespace. Stands in for the `AttributeError` the
    runtime raises (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees: the layout/namespace rule and the chain assembly are
# modelled deeply. The only operation this specification observes is whether the
# instance carries an open namespace, which is a pure function of the layout
# flags of the types in its chain — spelled out below — and the attribute-
# binding decision that follows from it.)
# axioms-end


# pure-start
@Pure
def all_closed_layout(chain: PSeq[bool]) -> bool:
    """True iff EVERY type in the chain pins a closed instance layout. Front-
    recursive over the chain so one unfold is available per step: the head must
    pin a closed layout and so must the tail."""
    if len(chain) == 0:
        return True
    return chain[0] and all_closed_layout(chain.drop(1))


@Pure
def instance_admits_namespace(chain: PSeq[bool]) -> bool:
    """True iff an instance built from this chain carries an open per-instance
    namespace: that happens iff at least one type leaves its layout open, i.e.
    iff NOT every type pins a closed layout."""
    return not all_closed_layout(chain)
# pure-end


def bind_undeclared_attribute(chain: PSeq[bool]) -> bool:
    # pre-conditions-start
    # `chain` is the instance's type chain (root excluded), one closed-layout
    # flag per type. A pure value sequence: no heap permission needed. The
    # attribute name being bound is one the types did not pre-declare (the
    # observed case).
    # TERMINATION: the runtime's attribute-binding step is a bounded, loop-free
    # decision — it either stores the binding or raises; it never diverges.
    # Nagini verifies partial correctness only, so without this obligation an
    # implementation that loops forever would satisfy the postconditions
    # vacuously. The smallest measure (1) lets every caller holding a strictly
    # larger obligation invoke this step without leaking its own obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Binding succeeds (returns True, recording the binding in the namespace)
    # ONLY when the instance carries an open namespace, i.e. some type leaves its
    # layout open.
    Ensures(instance_admits_namespace(chain))
    Ensures(Result() is True)
    # Binding is REFUSED with the attribute error on EXACTLY the no-namespace
    # case: every type in the chain pins a closed layout.
    Exsures(AttributeBindingRefused, all_closed_layout(chain))
    # post-conditions-end
    # impl-start
    if all_closed_layout(chain):
        raise AttributeBindingRefused()
    return True
    # impl-end


def trait_pins_closed_layout() -> bool:
    # pre-conditions-start
    # TERMINATION: reading a class-level slot declaration is immediate — the
    # flag must actually be DELIVERED (total correctness), not merely never
    # contradicted by a diverging body. Measure 2 sits strictly between the
    # binding step's (1) and the observation functions' (3), so both call
    # directions discharge their obligations without leaking.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # Every type contributing to the core expression type's chain pins a closed
    # instance layout (declares no open namespace of its own), so that combining
    # it with the other types does not re-open the layout of the types that use
    # it. This is the per-type flag the chain-level rule below quantifies over.
    Ensures(Result() is True)
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: this contributing type leaves its instance layout OPEN
    # (it declares no closed slot layout of its own).
    return False
    # impl-end


def core_expression_instance_admits_namespace() -> bool:
    # pre-conditions-start
    # TERMINATION: the observation (does a fresh instance carry a __dict__?) is
    # a bounded query the real interpreter always completes; the F2P test's
    # `assert not hasattr(b1, '__dict__')` only passes if it RETURNS. Under
    # partial correctness a diverging body satisfies Ensures(Result() is False)
    # vacuously; this obligation rejects any such implementation.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The core expression type's instances carry NO open per-instance namespace:
    # every type in their chain pins a closed layout.
    Ensures(Result() is False)
    # post-conditions-end
    # impl-start
    # The chain of the core expression type (root excluded): the type itself and
    # its other contributing types pin closed layouts; the remaining contributing
    # type pins a closed layout iff trait_pins_closed_layout() says so.
    trait = trait_pins_closed_layout()
    chain = PSeq(True, True, trait)  # type: PSeq[bool]
    return instance_admits_namespace(chain)
    # impl-end


def core_expression_bind_undeclared_attribute() -> bool:
    # pre-conditions-start
    # TERMINATION: the F2P test's `with raises(AttributeError): b1.x = 1` only
    # passes if the binding attempt COMPLETES by raising — an implementation
    # that hangs forever never raises and does not resolve. Under partial
    # correctness a diverging body satisfies Ensures(False) vacuously (no
    # normal exit is ever reached); this obligation forces the refusal to
    # actually be delivered.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # Binding an undeclared attribute on a core-expression instance is refused
    # with the attribute error: it never returns normally (no namespace exists).
    Ensures(False)
    Exsures(AttributeBindingRefused, True)
    # post-conditions-end
    # impl-start
    trait = trait_pins_closed_layout()
    chain = PSeq(True, True, trait)  # type: PSeq[bool]
    return bind_undeclared_attribute(chain)
    # impl-end
