"""Twin-artifact model for sphinx-doc__sphinx-8595.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When automatic documentation is asked to expand the full membership of a
  module, the module's optional explicit export list governs which members are
  retained. The two cases are distinguished by whether the export list is
  ABSENT versus merely EMPTY:

    (1) The export list is ABSENT (the module declares none). Then membership
        is implicit: the routine reports that every discovered member is a
        candidate (the implicit-membership flag is true) and leaves the
        discovered members untouched, marking none of them as excluded.

    (2) The export list is PRESENT — INCLUDING when it is the empty list. Then
        membership is explicit: the routine reports that membership is NOT
        implicit (the flag is false) and, for each discovered member, marks the
        member as excluded exactly when its name is NOT one of the listed
        export names. In particular, a present-but-empty export list excludes
        EVERY discovered member and retains none.

  The discovered members are always returned in full; their per-member
  exclusion flags carry which ones survive. The export list and the member
  names are read-only. The routine always ANSWERS: selecting against a finite
  member set and a finite export list is a bounded scan, so termination is a
  correctness obligation (carried as MustTerminate in the precondition).

Type abstraction (refinement.md / mapping.md): the optional export list
`Optional[Sequence[str]]` is carried by `(all_present: bool, all_names:
List[int])` — `all_present` is whether the list is declared (`None` ↦ False),
`all_names` the export name identifiers (empty when undeclared or declared
empty). The discovered members are two index-aligned carriers: a read-only
`List[int]` of member name identifiers and a mutable `List[bool]` of the
per-member exclusion flags, the latter cleared on entry (a freshly discovered
member is not excluded until proven so). String names are abstracted to integer
identifiers (equal ints == equal names). Membership and the per-member
exclusion vector are carried by a front-recursive pure sequence theory.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The membership test and the absent-vs-empty distinction
# are pure structural logic, modelled deeply (`contains` / `exclusion_flags`).
# The discovery of the module member set is upstream of the modelled function
# and is not consumed here.
# axioms-end


# pure-start
@Pure
def contains(names: PSeq[int], v: int) -> bool:
    """True iff the export-name identifier `v` occurs in the export-name
    sequence `names`. Front-recursive so a single unfold is available per
    loop step. On the empty sequence it is uniformly false."""
    if len(names) == 0:
        return False
    return names[0] == v or contains(names.drop(1), v)


@Pure
def exclusion_flags(member_names: PSeq[int], all_names: PSeq[int]) -> PSeq[bool]:
    """The per-member exclusion vector against a PRESENT export list: member k
    is excluded (True) exactly when its name is not in `all_names`. Front-
    recursive, index-aligned with `member_names`. For an empty `all_names`
    every entry is True (nothing is exported)."""
    if len(member_names) == 0:
        return PSeq(False).take(0)
    return (PSeq(not contains(all_names, member_names[0])) +
            exclusion_flags(member_names.drop(1), all_names))
# pure-end


def select_module_members(member_names: List[int],
                          excluded: List[bool],
                          all_present: bool,
                          all_names: List[int]) -> bool:
    # pre-conditions-start
    # The export name list is read-only: fractional permission, required AND
    # ensured. (`all_names` is empty when the export list is undeclared.)
    Requires(Acc(list_pred(all_names), 1 / 2))
    # The discovered member names are read-only.
    Requires(Acc(list_pred(member_names), 1 / 2))
    # The per-member exclusion flags are written in place: full permission,
    # index-aligned with the member names, and cleared on entry (the default
    # state of a freshly discovered member).
    Requires(Acc(list_pred(excluded)))
    Requires(len(excluded) == len(member_names))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(excluded),
                                             ToSeq(excluded)[k] == False),
                                     [[ToSeq(excluded)[k]]])))
    # TERMINATION: the real routine scans the finite discovered-member set
    # against the finite export list and always returns. Nagini is a
    # partial-correctness verifier by default, so without this obligation a
    # non-terminating implementation (e.g. a loop that never advances its
    # index) satisfies every Ensures vacuously; the real selection always
    # answers.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(all_names), 1 / 2))
    Ensures(Acc(list_pred(member_names), 1 / 2))
    Ensures(Acc(list_pred(excluded)))
    # The full member set is preserved (length unchanged).
    Ensures(len(excluded) == len(member_names))
    # (1) ABSENT export list: implicit membership signalled, nothing excluded.
    Ensures(Implies(not all_present, Result() == True))
    Ensures(Implies(not all_present,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(excluded),
                                                   ToSeq(excluded)[k] == False),
                                           [[ToSeq(excluded)[k]]]))))
    # (2) PRESENT export list (incl. empty): explicit membership signalled, and
    # each member is excluded exactly when its name is not an export name. For a
    # present-but-empty list `exclusion_flags` is uniformly True.
    Ensures(Implies(all_present, Result() == False))
    Ensures(Implies(all_present,
                    ToSeq(excluded) == exclusion_flags(ToSeq(member_names),
                                                       ToSeq(all_names))))
    # post-conditions-end
    # impl-start
    if (not all_present) or len(all_names) == 0:
        # PRE-PATCH (buggy): a present-but-empty export list is conflated with
        # an absent one, so an empty export list wrongly takes the implicit-
        # membership branch and excludes nothing.
        return True
    else:
        seq = ToSeq(all_names)
        i = len(excluded)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(all_names), 1 / 2))
            Invariant(Acc(list_pred(member_names), 1 / 2))
            Invariant(Acc(list_pred(excluded)))
            Invariant(len(excluded) == len(member_names))
            Invariant(seq == ToSeq(all_names))
            Invariant(0 <= i and i <= len(excluded))
            Invariant(ToSeq(excluded).drop(i) ==
                      exclusion_flags(ToSeq(member_names).drop(i), seq))
            # The loop consumes the termination obligation: `i` is the
            # strictly decreasing, bounded-below measure.
            Invariant(MustTerminate(i))
            # invariants-end
            c = member_names[i - 1]
            Assert(ToSeq(member_names).drop(i - 1)[0] == c)
            Assert(ToSeq(member_names).drop(i - 1).drop(1) ==
                   ToSeq(member_names).drop(i))
            if not contains(seq, c):
                excluded[i - 1] = True
            else:
                excluded[i - 1] = False
            Assert(ToSeq(excluded)[i - 1] == (not contains(seq, c)))
            Assert(ToSeq(excluded).drop(i - 1)[0] == ToSeq(excluded)[i - 1])
            Assert(ToSeq(excluded).drop(i - 1).drop(1) == ToSeq(excluded).drop(i))
            i = i - 1
        return False
    # impl-end
