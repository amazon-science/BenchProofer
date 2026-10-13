"""Twin-artifact model for sphinx-doc__sphinx-8035.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an automatic-documentation pass collects the members of an object and
  must decide whether to keep a member that is considered private, the option
  that controls private members can be in one of three states, and the keep
  decision depends on which state it is in:

    (a) the option was NOT supplied -> no private member is kept;
    (b) the option was supplied with NO argument (the "all-private" form)
        -> a private member is kept exactly when it is documentable in the
        usual sense (it has documentation, or undocumented members are being
        kept);
    (c) the option was supplied with an explicit list of names -> a private
        member is kept exactly when its OWN name appears in that list, it is
        otherwise documentable, and it is not an inherited member that is being
        filtered out. A private member whose name is NOT in the list is
        dropped, even though OTHER names are listed.

  The crucial point distinguishing (c) from a coarse on/off control: supplying
  a non-empty list of names does NOT keep every private member; it keeps
  exactly the named ones. An undocumentable private member is never kept in any
  state.

  A second behaviour is the merge of the various ``*-members`` selectors into
  the explicit member list: when the principal member selector is the
  "all-members" form, the merge is a no-op; otherwise each name from each
  supplementary selector that is given as an explicit list (not the all-form)
  is appended to the member list if it is not already present, preserving order
  and avoiding duplicates.

Member names are modelled as ``int`` identity tokens; a list of names is a
``List[int]`` of such tokens (Nagini bans ``str`` indexing). The three option
states are encoded by an explicit ``mode`` tag (0 = absent, 1 = all-form,
2 = explicit list) carrying its list payload, which is the faithful refinement
of the ``None`` / sentinel-object / list trichotomy the real option uses.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms: the keep decision and the merge are pure boolean /
#  sequence logic over the abstract option tag, the name tokens and the
#  documentability flags, spelled out in full. There is no unchanged opaque
#  callee whose contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def documentable(has_doc: bool, undoc_members: bool) -> bool:
    """A member is documentable in the usual sense when it carries
    documentation, or undocumented members are being retained."""
    return has_doc or undoc_members


@Pure
def keep_private(mode: int, names: PSeq[int], membername: int,
                 has_doc: bool, undoc_members: bool,
                 filtered_inherited: bool) -> bool:
    """The keep decision for a member that is considered private, as a pure
    function of the option's three states.

      mode 0 (absent)        -> never kept
      mode 1 (all-form)      -> kept iff documentable
      mode 2 (explicit list) -> kept iff documentable, not a filtered inherited
                                member, and this member's name is in the list

    The inherited-member filter applies only to the explicit-list state; the
    all-form keeps every documentable private member.
    """
    if not documentable(has_doc, undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    return (not filtered_inherited) and (membername in names)
# pure-end


def keep_private_member(mode: int, names: List[int], membername: int,
                        has_doc: bool, undoc_members: bool,
                        filtered_inherited: bool) -> bool:
    # pre-conditions-start
    # ``names`` (the explicit list payload of the option) is read only here:
    # fractional permission, returned unchanged (directive 5). ``mode`` is the
    # option-state tag, 0/1/2 as documented above.
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(0 <= mode and mode <= 2)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    # The decision equals the pure three-state rule.
    Ensures(Result() == keep_private(mode, ToSeq(names), membername,
                                     has_doc, undoc_members, filtered_inherited))
    # An undocumentable member is never kept, in any option state.
    Ensures(Implies(not documentable(has_doc, undoc_members),
                    Result() is False))
    # Absent option: never kept.
    Ensures(Implies(mode == 0, Result() is False))
    # All-form: kept exactly when documentable (the inherited-member filter
    # does not apply to the all-form).
    Ensures(Implies(mode == 1,
                    Result() == documentable(has_doc, undoc_members)))
    # Explicit list: a documentable, non-filtered member is kept iff its OWN
    # name is in the list. This is the discriminating clause: a non-empty list
    # does NOT keep every private member, only the named ones.
    Ensures(Implies(mode == 2 and documentable(has_doc, undoc_members)
                    and not filtered_inherited,
                    Result() == (membername in ToSeq(names))))
    Ensures(Implies(mode == 2 and documentable(has_doc, undoc_members)
                    and not filtered_inherited and not (membername in ToSeq(names)),
                    Result() is False))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy) skeleton: the option is treated as a single on/off
    # control. Any "given" option (the all-form OR a non-empty explicit list)
    # is collapsed to a truthy flag, so a documentable private member is kept
    # whenever the option is given at all -- the member's own name is never
    # consulted, and every private member is kept rather than only the named
    # ones.
    option_given = mode != 0
    return option_given and (has_doc or undoc_members)
    # impl-end


@Pure
def merged_at(orig: PSeq[int], extra: PSeq[int], i: int) -> bool:
    """Membership predicate for the merge result built from ``orig`` by
    appending the as-yet-unseen names of ``extra``: ``i`` indexes ``extra`` and
    the name is appended exactly when it is not already in ``orig`` and not in
    the already-processed prefix of ``extra``."""
    Requires(0 <= i and i < len(extra))
    return (not (extra[i] in orig)) and (not (extra[i] in extra.take(i)))


def merge_selector_names(members_is_all: bool, members: List[int],
                         extra: List[int]) -> List[int]:
    # pre-conditions-start
    # ``members`` is the principal member list being extended; ``members_is_all``
    # is True when the principal selector is the all-members form (so the merge
    # is a no-op). ``extra`` is one supplementary selector given as an explicit
    # list of names. Both lists are read only here (fractional permission).
    Requires(Acc(list_pred(members), 1 / 2))
    Requires(Acc(list_pred(extra), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(members), 1 / 2))
    Ensures(Acc(list_pred(extra), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # All-members form: the merge is a no-op, the member list is unchanged.
    Ensures(Implies(members_is_all, ToSeq(Result()) == ToSeq(members)))
    # Otherwise the result begins with the original member list (order kept) ...
    Ensures(Implies(not members_is_all,
                    ToSeq(Result()).take(len(members)) == ToSeq(members)))
    # ... and every original member is still present.
    Ensures(Implies(not members_is_all,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                   members[k] in ToSeq(Result()))))))
    # ... and every extra name is now present (it was appended if new, or was
    # already there) — the supplementary selector's names are all included.
    Ensures(Implies(not members_is_all,
                    Forall(int, lambda k: (Implies(0 <= k and k < len(extra),
                                                   extra[k] in ToSeq(Result()))))))
    # post-conditions-end
    # impl-start
    if members_is_all:
        result = []  # type: List[int]
        i = 0
        while i < len(members):
            # invariants-start
            Invariant(Acc(list_pred(members), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(members))
            Invariant(ToSeq(result) == ToSeq(members).take(i))
            Invariant(MustTerminate(len(members) - i + 1))
            # invariants-end
            result = result + [members[i]]
            i = i + 1
        Assert(ToSeq(members).take(len(members)) == ToSeq(members))
        return result
    result = []
    i = 0
    while i < len(members):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(members))
        Invariant(ToSeq(result) == ToSeq(members).take(i))
        Invariant(MustTerminate(len(members) - i + 1))
        # invariants-end
        result = result + [members[i]]
        i = i + 1
    Assert(ToSeq(members).take(len(members)) == ToSeq(members))
    Assert(ToSeq(result) == ToSeq(members))
    j = 0
    while j < len(extra):
        # invariants-start
        Invariant(Acc(list_pred(members), 1 / 2))
        Invariant(Acc(list_pred(extra), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(extra))
        Invariant(ToSeq(result).take(len(members)) == ToSeq(members))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(members),
                                                 members[k] in ToSeq(result)))))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                                                 extra[k] in ToSeq(result)))))
        Invariant(MustTerminate(len(extra) - j + 1))
        # invariants-end
        m = extra[j]
        present = m in ToSeq(result)
        if not present:
            result = result + [m]
        Assert(extra[j] in ToSeq(result))
        j = j + 1
    return result
    # impl-end
