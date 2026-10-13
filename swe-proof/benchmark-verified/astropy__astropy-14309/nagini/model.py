"""Twin-artifact model for astropy__astropy-14309.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A format-detection predicate decides whether some input designates a file of
  a particular kind. Its inputs are, in priority order:

    1. an optional open data stream; when present, the verdict is whether the
       stream's leading bytes equal a constant signature;
    2. otherwise an optional path name; when present, the verdict is whether the
       path name ends with one of a predetermined set of recognised suffixes;
    3. otherwise a verdict drawn from the first of the remaining trailing
       positional arguments (whether that object is one of a predetermined set
       of accepted object kinds).

  The required guarantee on case (2): when a path name is present, the predicate
  yields a definite boolean verdict computed SOLELY from that path name — TRUE
  exactly when the path name carries a recognised suffix and FALSE otherwise —
  and in particular it does NOT, in the FALSE case, go on to consult the
  trailing positional arguments. Consulting them would index the trailing
  argument tuple, which is out of range (and would fault) when no trailing
  argument was supplied. So for a present path name the predicate is a total
  function of the path name alone and is well-defined even with no trailing
  arguments.

The result is modelled as a small integer code (TRUE / FALSE, plus a distinct
FAULT sentinel that marks "the predicate indexed an absent trailing argument").
The runtime classification facts (a stream being present, a byte comparison, a
suffix test, an object-kind test, the count of trailing arguments) are modelled
as booleans / a non-negative int (Nagini cannot run the underlying isinstance /
byte / string probes). No library callee is consumed inside a postcondition, so
the axioms region is empty (see mapping.md §3). `axiom_check.py` validates the
decision against the real predicate (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (none — the modelled delta is a pure control-flow decision over boolean
# classification bits and an argument count; no opaque library callee is
# consumed inside an Ensures. See mapping.md §3.)
# axioms-end


# pure-start
@Pure
def R_TRUE() -> int:
    # definite TRUE verdict
    return 1


@Pure
def R_FALSE() -> int:
    # definite FALSE verdict
    return 0


@Pure
def R_FAULT() -> int:
    # the predicate indexed an absent trailing argument (out-of-range fault):
    # a non-boolean outcome that a correct predicate must NEVER produce when a
    # path name is present.
    return -1


@Pure
def decided(stream_present: bool, sig_matches: bool,
            path_present: bool, path_recognised: bool,
            n_trailing: int, first_trailing_accepted: bool) -> int:
    """The verdict the predicate must produce for the given classification
    facts. This is the desired behaviour spelled out as a total function of the
    facts (the specification the impl must meet).

    Priority: a present stream decides by signature; otherwise a present path
    name decides SOLELY by its suffix (TRUE iff recognised, FALSE otherwise —
    never consulting trailing arguments); otherwise the first trailing argument
    decides (and only here is an absent trailing argument indexed -> FAULT)."""
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()
# pure-end


def is_recognised_input(stream_present: bool, sig_matches: bool,
                        path_present: bool, path_recognised: bool,
                        n_trailing: int, first_trailing_accepted: bool) -> int:
    # pre-conditions-start
    # The count of trailing positional arguments is non-negative; the
    # "first trailing argument is accepted" fact is meaningful only when there
    # is at least one trailing argument (else it is not consulted).
    Requires(n_trailing >= 0)
    Requires(Implies(first_trailing_accepted, n_trailing >= 1))
    # Total correctness: the predicate must actually ANSWER (deliver a verdict
    # to its caller), not merely be partially correct. Without this obligation
    # a diverging body (e.g. unbounded self-recursion) would satisfy every
    # postcondition vacuously yet never produce the verdict; the real predicate
    # is a straight-line cascade that always returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The verdict is exactly the desired classification-driven decision.
    Ensures(Result() == decided(stream_present, sig_matches, path_present,
                                 path_recognised, n_trailing,
                                 first_trailing_accepted))
    # When a path name is present, the verdict is a definite boolean computed
    # SOLELY from the path name: TRUE iff the suffix is recognised, FALSE
    # otherwise — and it is NEVER the out-of-range FAULT, regardless of how
    # many trailing arguments were (or were not) supplied. This is the
    # discriminating clause the spec pins.
    Ensures(Implies(not stream_present and path_present and path_recognised,
                    Result() == R_TRUE()))
    Ensures(Implies(not stream_present and path_present and not path_recognised,
                    Result() == R_FALSE()))
    Ensures(Implies(not stream_present and path_present,
                    Result() != R_FAULT()))
    # post-conditions-end
    # impl-start
    # Faithful skeleton of the priority cascade. The path-name branch RETURNS
    # the suffix verdict directly (TRUE or FALSE), so it never falls through to
    # index the trailing-argument tuple.
    if stream_present:
        if sig_matches:
            return R_TRUE()
        return R_FALSE()
    if path_present:
        if path_recognised:
            return R_TRUE()
        return R_FALSE()
    # Only reached when neither a stream nor a path name is present: the first
    # trailing argument decides; indexing it when there is none is the fault.
    if n_trailing == 0:
        return R_FAULT()
    if first_trailing_accepted:
        return R_TRUE()
    return R_FALSE()
    # impl-end
