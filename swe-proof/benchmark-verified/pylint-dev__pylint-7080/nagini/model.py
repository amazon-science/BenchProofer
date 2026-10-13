"""Twin-artifact model for pylint-dev__pylint-7080.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A candidate path is screened against a set of exclusion rules to decide
  whether it should be skipped. Two independent families of rules apply:

    (1) rules keyed on the final path component (the trailing name), and

    (2) rules keyed on the whole path: such a rule names a directory prefix,
        and a candidate is excluded when the path lies under that prefix.

  A candidate arrives at the screen in whatever form the enumeration that
  produced it emitted, which need not be the form a rule is written against. A
  family-(2) rule is therefore keyed on a SETTLED FORM of the candidate -- the
  value one deterministic map of the candidate yields -- rather than on the
  argument as it arrived.

Paths are modelled as ``List[int]`` of Unicode code points (Nagini bans ``str``
indexing); the specification is carried over ``PSeq[int]`` via ``ToSeq``. The
settling map is DECLARED here and carries NO value-claim: this specification
pins only WHICH value the whole-path family is keyed on, and states nothing
about how that value relates to the argument it is computed from -- so,
formally, no expression over the argument can stand in for it. The whole-path
prefix test is the structural sequence-prefix relation. The trailing-name rules
(family 1) are summarised by one declared predicate of the candidate: the
family's decision for a candidate is pinned to that predicate's value at that
candidate, and nothing is claimed about how the rules arrive at it -- which of
the candidate's components they consult, or in what form. Provenance and
executable soundness for both declared symbols: mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def route_of(path: PSeq[int]) -> PSeq[int]:
    """The settled form of the given candidate: the value the declared map
    yields for it. DECLARED, not defined -- this model states nothing about
    which arguments it changes or how, and treats it as an arbitrary
    deterministic function of its argument. The whole-path family below is keyed
    on this value rather than on the argument as it arrived.
    Provenance + executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def trailing_name_excluded(candidate: PSeq[int]) -> bool:
    """The trailing-name decision the screen reaches for the candidate it is
    given: whether the final-component exclusion rules (final-component
    membership and final-component patterns) fire when the screen is run on that
    candidate. DECLARED, not defined -- this model claims only that the decision
    is a deterministic function of that candidate, and says nothing about which
    of the candidate's components the rules consult or in what form, so no
    expression over the argument can stand in for it. Decided independently of
    the whole-path rules. Provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
# axioms-end


# pure-start
@Pure
def has_prefix(s: PSeq[int], p: PSeq[int]) -> bool:
    """Structural sequence-prefix relation: ``s`` begins with the whole of
    ``p``. This is the anchored whole-path prefix test (a form lies under the
    directory named by ``p``)."""
    return len(p) <= len(s) and s.take(len(p)) == p


@Pure
def excluded_candidate(candidate: PSeq[int], pattern: PSeq[int]) -> bool:
    """The screen's decision for a candidate: a trailing-name rule fires for
    that candidate, or its settled form lies under the anchored whole-path
    directory prefix."""
    return (trailing_name_excluded(candidate)
            or has_prefix(route_of(candidate), pattern))
# pure-end


def is_path_excluded(element: List[int], pattern: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(element), 1 / 2))
    Requires(Acc(list_pred(pattern), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(element), 1 / 2))
    Ensures(Acc(list_pred(pattern), 1 / 2))
    # The screen's decision for the candidate: excluded iff a trailing-name
    # rule fires for it OR its SETTLED FORM -- the value the declared map
    # yields -- lies under the anchored whole-path prefix, which is not the same
    # as the argument as it arrived lying under it.
    Ensures(Result() == excluded_candidate(ToSeq(element), ToSeq(pattern)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
