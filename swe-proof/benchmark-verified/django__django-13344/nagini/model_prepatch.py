"""Twin-artifact model for django__django-13344.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class-based request/response handler is configured at construction from a
  single supplied response-producer. Configuration MUST establish three
  observable facts about the constructed handler, for EVERY such handler kind:

    (1) the absence of a supplied producer is reported through the legacy
        configuration-time signal: that signal fires exactly when the supplied
        producer is the absent value, and not otherwise;

    (2) the supplied producer is retained on the handler so the handler can
        later invoke it;

    (3) the handler advertises the *same* asynchronous capability as its
        supplied producer: the handler is recognised as asynchronous exactly
        when the supplied producer is itself asynchronous, and as synchronous
        otherwise. This is what lets a downstream consumer in a chain receive a
        materialised result rather than an unresolved asynchronous placeholder.

  A handler variant that additionally selects a backing store by name must,
  beyond the three facts above, keep its selected store CONSISTENT with the
  selected name: the resolved store is always the store that the currently
  selected name designates, whether that name is the configured default or an
  explicit override supplied at construction. Overriding the name re-resolves
  the store from the new name; leaving it as the default keeps the
  default-resolved store. (This is the observable invariant a constructor of
  such a variant must maintain across the default, explicit-default, and
  explicit-custom construction paths.)

The supplied producer is modelled by an opaque token (``Optional[int]``; the
absent value is ``None``). Whether a given producer is asynchronous is decided
by an unchanged runtime predicate, axiomatized as a pure deterministic callee.
The store-name -> store resolution is likewise an unchanged registry lookup,
axiomatized as a pure deterministic callee. The handler is a minimal class
carrying only the touched fields.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Handler:
    def __init__(self) -> None:
        Requires(MustTerminate(2))
        Ensures(Acc(self.producer) and self.producer is None)  # type: ignore
        Ensures(Acc(self.async_advertised) and self.async_advertised is False)  # type: ignore
        Ensures(Acc(self.absence_signalled) and self.absence_signalled is False)  # type: ignore
        Ensures(Acc(self.store_name) and self.store_name == 0)  # type: ignore
        Ensures(Acc(self.store) and self.store == 0)  # type: ignore
        self.producer = None  # type: Optional[int]
        self.async_advertised = False  # type: bool
        self.absence_signalled = False  # type: bool
        self.store_name = 0  # type: int
        self.store = 0  # type: int


# axioms-start
@Pure
@ContractOnly
def producer_is_async(producer: Optional[int]) -> bool:
    """Unchanged runtime predicate deciding whether a supplied producer is an
    asynchronous producer (the coroutine-function test). Deterministic in the
    producer token; the absent producer is not asynchronous. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Implies(producer is None, Result() is False))


@Pure
@ContractOnly
def resolve_store(store_name: int) -> int:
    """Unchanged registry lookup resolving a store-name token to its store
    token. Deterministic in the name (it is a plain mapping read); two distinct
    names need not resolve to distinct stores, but the same name always
    resolves to the same store. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def configure_handler(handler: Handler, producer: Optional[int]) -> None:
    # pre-conditions-start
    Requires(Acc(handler.producer))
    Requires(Acc(handler.async_advertised))
    Requires(Acc(handler.absence_signalled))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(handler.producer))
    Ensures(Acc(handler.async_advertised))
    Ensures(Acc(handler.absence_signalled))
    # (2) the supplied producer is retained.
    Ensures(handler.producer is producer)
    # (1) the absence signal fires exactly when the producer is the absent value.
    Ensures(handler.absence_signalled == (producer is None))
    # (3) the handler advertises async exactly when the producer is async.
    Ensures(handler.async_advertised == producer_is_async(producer))
    # post-conditions-end
    # impl-start
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    # impl-end


def configure_settings_handler(handler: Handler, producer: Optional[int],
                               default_name: int,
                               override_name: Optional[int]) -> int:
    # pre-conditions-start
    Requires(Acc(handler.producer))
    Requires(Acc(handler.async_advertised))
    Requires(Acc(handler.absence_signalled))
    Requires(Acc(handler.store_name))
    Requires(Acc(handler.store))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(handler.producer))
    Ensures(Acc(handler.async_advertised))
    Ensures(Acc(handler.absence_signalled))
    Ensures(Acc(handler.store_name))
    Ensures(Acc(handler.store))
    # The shared three facts hold for a store-selecting handler too.
    Ensures(handler.producer is producer)
    Ensures(handler.absence_signalled == (producer is None))
    Ensures(handler.async_advertised == producer_is_async(producer))
    # The selected name is the override when one is supplied, else the default.
    Ensures(handler.store_name == (override_name if override_name is not None else default_name))
    # The load-bearing invariant: the resolved store is ALWAYS the store the
    # selected name designates -- on every construction path.
    Ensures(handler.store == resolve_store(handler.store_name))
    # The configured store is reported back to the caller.
    Ensures(Result() == handler.store)
    # post-conditions-end
    # impl-start
    if producer is None:
        handler.absence_signalled = True
    else:
        handler.absence_signalled = False
    handler.producer = producer
    # Defaults established first (as super().__init__ -> base init does):
    handler.store_name = default_name
    handler.store = resolve_store(handler.store_name)
    # An explicit override re-selects the name AND re-resolves the store from it:
    if override_name is not None:
        handler.store_name = override_name
        handler.store = resolve_store(handler.store_name)
    return handler.store
    # impl-end
