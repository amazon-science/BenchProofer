"""Twin-artifact model for psf__requests-5414.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Before a host label drawn from a locator is accepted, it is screened for a
  leading code point that cannot begin a valid label. A non-empty host whose
  first code point is code point 42 or code point 46 names an empty or otherwise
  ill-formed first label and must be reported as a rejection rather than allowed
  to return normally.

  This screen applies only to a host that is already expressible in the
  restricted (ASCII) form. A host that is NOT in that restricted form is handed
  instead to the unchanged internationalised-label encoder, whose only
  observable datum is whether the host carries an encodable label; that encoder
  reports a rejection (the SAME out-of-band signal) exactly when the label is
  not encodable, and otherwise returns normally. The leading-code-point screen
  is NOT applied to a non-restricted host.

  The behaviour pinned here is therefore, for a non-empty host:

    * restricted (ASCII) host: rejected  iff  the first code point is 42 or
                                              46; returns normally otherwise.
    * non-restricted host:     rejected  iff  the encoder cannot encode the
                                              label; returns normally otherwise.

The host is modelled as a ``List[int]`` of Unicode code points (Nagini bans
``str`` indexing). Whether the host is in the restricted (ASCII) form, and
whether a non-restricted label is encodable, are the two single observable bits
of the unchanged callees (the predicate deciding the restricted form, and the
internationalised-label encoder); the latter is axiomatized as a contract-only
function. The rejection is a user-defined exception class (a builtin exception
in an ``Exsures`` crashes the Nagini translator).

The screen is a bounded, straight-line computation and MUST terminate (a
total-correctness obligation, carried as ``MustTerminate`` in the
precondition). Nagini is a partial-correctness verifier by default, so without
this obligation a non-terminating implementation (e.g. bare self-recursion or
an endless loop) satisfies every ``Ensures``/``Exsures`` vacuously; the real
host screen always answers (returns normally or signals the rejection) before
the surrounding preparation continues.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class InvalidLocator(Exception):
    """The rejection signalled when the host carries an invalid label. A
    user-defined stand-in for the locator error the desired behaviour requires
    (a builtin exception in an ``Exsures`` crashes the Nagini translator;
    mapping.md §2)."""
    pass


# axioms-start
@ContractOnly
def encode_label(encodable: bool) -> None:
    """The unchanged internationalised-label encoder, the callee a non-ASCII
    host is handed to instead of the leading-code-point screen. Its only
    observable datum is ``encodable``: whether the host's label can be encoded.
    It returns normally exactly when the label is encodable and signals a
    rejection (the same out-of-band rejection) exactly when it is not.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    # pre-conditions-start
    # The real encoder is a bounded call that always answers (returns the
    # encoded host or raises; axiom_check.py shows it is total over those two
    # channels). The strictly smaller measure (1 < 2) lets the contracted
    # caller holding MustTerminate(2) invoke it without leaking its own
    # obligation.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal completion is reachable EXACTLY on the encodable case.
    Ensures(encodable is True)
    # Rejection is signalled out of band EXACTLY on the not-encodable case.
    Exsures(InvalidLocator, encodable is False)
    # post-conditions-end
# axioms-end


# pure-start
# NOTE for auditors: the contract below pins the COMPLETE observable relation
# on the modeled domain — for every admissible input it determines whether
# the screen returns normally or signals the rejection, and the @Pure
# predicate here is TRANSPARENT (its body IS the whole membership test), not
# an opaque answer-key. Consequently any same-spec implementation that
# verifies is behaviourally EQUAL to the pinned behaviour on every admissible
# input: a restructured or branch-reordered equivalent (or one that tests the
# pure predicate directly) is a POSITIVE CONTROL, never a spec-too-weak
# counterexample — it belongs in positive_control, not in the attack list. A
# valid weakness attack must DIFFER from the pinned relation on some
# admissible input, and the contract then rejects it.
@Pure
def is_invalid_leading(c: int) -> bool:
    """A single leading code point cannot begin a valid label iff it is
    code point 42 or code point 46."""
    return c == 42 or c == 46
# pure-end


def screen_host(host: List[int], host_is_ascii: bool, encodable: bool) -> None:
    # pre-conditions-start
    # ``host`` is only READ (fractional permission, directive 5). The host is
    # non-empty (a host with no label is decided earlier, out of this slice).
    # ``host_is_ascii`` / ``encodable`` are the abstract world-state data of the
    # two unchanged callees: whether the host is in the restricted (ASCII) form,
    # and (when it is not) whether its label is encodable.
    Requires(Acc(list_pred(host), 1 / 2))
    Requires(len(host) > 0)
    # TERMINATION: the screen must actually ANSWER (return normally or signal
    # the rejection) — it is a bounded, straight-line decision over one host.
    # Nagini is a partial-correctness verifier by default, so without this
    # obligation a non-terminating implementation (bare self-recursion, an
    # endless loop) satisfies every Ensures/Exsures vacuously; the real host
    # screen always answers before the surrounding preparation continues.
    # The measure (2) strictly exceeds the encoder axiom's (1), so the impl
    # may call encode_label but may NOT re-invoke this routine itself — the
    # postcondition cannot be discharged by echoing this routine's own
    # contract.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The host is read-only: returned untouched at the same fractional
    # permission (so the screen cannot have mutated it, directive 5).
    Ensures(Acc(list_pred(host), 1 / 2))
    # Normal completion is reachable EXACTLY in two disjoint cases:
    #   (a) a restricted (ASCII) host whose first code point is neither 42
    #       nor 46;
    #   (b) a non-restricted host whose label is encodable.
    # In particular, a restricted (ASCII) host whose first code point is 46 can
    # NEVER return normally.
    Ensures(len(host) > 0)
    Ensures(Implies(host_is_ascii, len(host) > 0 and not is_invalid_leading(host[0])))
    Ensures(Implies(not host_is_ascii, encodable is True))
    # Rejection is signalled EXACTLY when a restricted (ASCII) host's first code
    # point is 42 or 46, OR a non-restricted host's label is not encodable. The
    # read-only host is re-established on the rejecting path as well.
    Exsures(InvalidLocator,
            Acc(list_pred(host), 1 / 2)
            and len(host) > 0
            and ((host_is_ascii and is_invalid_leading(host[0]))
                 or (not host_is_ascii and encodable is False)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the leading-code-point screen rejects ONLY the
    # wildcard ``*`` (42); a host whose first code point is the label separator
    # ``.`` (46) is NOT rejected and returns normally — exactly the behaviour
    # the fix forbids (an ASCII host beginning with ``.`` must be rejected on
    # equal footing with one beginning with ``*``).
    if not host_is_ascii:
        encode_label(encodable)
    elif host[0] == 42:
        raise InvalidLocator()
    # impl-end
