"""Twin-artifact model for django__django-15368.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A batch update assembles, for one column, an ordered list of per-object
  assignments. For each object an attribute value is taken; the value must then
  be classified into one of two assignment forms:

    * a value that is *resolvable* — it knows how to turn itself into a column
      reference / sub-expression — must be carried into the assignment AS IT IS,
      so the database resolves it (e.g. to another column);

    * a value that is NOT resolvable — a plain Python datum — must instead be
      wrapped as a literal bound parameter before it is carried in.

  The classification must be by the *capability* of carrying a value into a
  resolvable form, NOT by membership in any one concrete family of resolvable
  values. In particular a resolvable value that does not belong to that one
  concrete family (it merely has the resolving capability) must still be carried
  through unwrapped, exactly like a member of the family — never silently turned
  into a literal, which would store the value's text instead of resolving it.

  The observable result is, in object order, one boolean per assignment:
  True iff that value was wrapped as a literal. A value must be wrapped iff it
  is NOT resolvable; every resolvable value, whether or not it is in the
  concrete family, must be left unwrapped (False).

Each candidate value is described by two booleans: `in_family` (it is a member
of the one concrete resolvable family) and `resolvable` (it carries the
resolving capability). Family membership entails the capability — every member
of the family is resolvable — but NOT conversely: a value can be resolvable
without being in that family. That entailment is the type-hierarchy fact stated
as a precondition (`in_family[i] ==> resolvable[i]`); the converse failure is
the discriminating case. The per-assignment result is a `List[bool]`, with the
specification carried over `PSeq[bool]`.

No callee is axiomatized: the classification is pure, local logic modelled
deeply by the front-recursive fold `wrap_flags` and the verified loop below.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms. The behaviour under specification — a value is wrapped as
# a literal iff it is NOT resolvable, regardless of concrete family — is modelled
# DEEPLY by the pure `wrap_flags` fold below and the verified loop, not behind a
# @ContractOnly. The type-hierarchy fact "family membership entails the resolving
# capability" is stated as an input precondition and audited against the real
# class hierarchy by axiom_check.py / G-AX, NOT consumed as an axiom.)
# axioms-end


# pure-start
@Pure
def empty_flags() -> PSeq[bool]:
    return PSeq(True).take(0)


@Pure
def wrap_flags(resolvable: PSeq[bool]) -> PSeq[bool]:
    """Per-assignment wrap flags for a sequence of resolvable-capability bits,
    in order. A value is wrapped as a literal (True) iff it is NOT resolvable;
    every resolvable value is left unwrapped (False). Front-recursive so a single
    unfold is available to the loop per step."""
    if len(resolvable) == 0:
        return empty_flags()
    return PSeq(not resolvable[0]) + wrap_flags(resolvable.drop(1))
# pure-end


def build_wrap_flags(in_family: List[bool], resolvable: List[bool]) -> List[bool]:
    # pre-conditions-start
    Requires(Acc(list_pred(in_family), 1 / 2))
    Requires(Acc(list_pred(resolvable), 1 / 2))
    # the two descriptions are aligned, one entry per object
    Requires(len(in_family) == len(resolvable))
    # type-hierarchy fact: family membership entails the resolving capability
    Requires(Forall(int, lambda i:
        (Implies(0 <= i and i < len(in_family),
                 Implies(in_family[i], resolvable[i])),
         [[in_family[i]], [resolvable[i]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(in_family), 1 / 2))
    Ensures(Acc(list_pred(resolvable), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Each value is wrapped as a literal iff it is NOT resolvable — the
    # capability decides, never the concrete family.
    Ensures(ToSeq(Result()) == wrap_flags(ToSeq(resolvable)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[bool]
    i = len(resolvable)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(in_family), 1 / 2))
        Invariant(Acc(list_pred(resolvable), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(in_family) == len(resolvable))
        Invariant(Forall(int, lambda k:
            (Implies(0 <= k and k < len(in_family),
                     Implies(in_family[k], resolvable[k])),
             [[in_family[k]], [resolvable[k]]])))
        Invariant(0 <= i and i <= len(resolvable))
        Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        attr_in_family = in_family[i - 1]
        Assert(ToSeq(resolvable).drop(i - 1)[0] == resolvable[i - 1])
        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
        if not attr_in_family:
            result = [True] + result
        else:
            result = [False] + result
        i = i - 1
    return result
    # impl-end
