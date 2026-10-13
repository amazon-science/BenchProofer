"""Twin-artifact model for django__django-12325.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a class participates in multi-table inheritance, the framework scans the
  one-to-one relations declared on its bases and records, per related model, the
  single relation that links the child to that parent. That recorded relation is
  later promoted to be the child's primary key. Among several one-to-one
  relations that happen to target the SAME related model, only the relation that
  is explicitly designated as a parent link is eligible to be recorded; an
  ordinary one-to-one relation that merely happens to point at the same related
  model must never be recorded, regardless of the order in which the relations
  were declared. Consequently:

    (1) Every recorded relation is a designated parent link. An ordinary
        one-to-one relation -- even one whose target coincides with a parent --
        is never recorded, so the relation later promoted to primary key is
        always a genuine parent link. (This is what removes the spurious
        configuration error the issue reports.)

    (2) Declaration order is irrelevant. A designated parent link to a given
        related model is recorded whether it is declared before or after an
        ordinary one-to-one relation to that same model; an ordinary relation
        declared after a parent link cannot displace it.

    (3) Every related model that has at least one designated parent link among
        the scanned relations ends up with a recorded relation for it, so a
        legitimate inheritance link is never lost.

    (4) Among several designated parent links to the SAME related model, the
        one scanned LAST is the one recorded (a later designated parent link
        overwrites an earlier one, mirroring the repository's last-writer-wins
        dict recording). The recorded relation is therefore never an earlier
        parent link than any other parent link to that model.

Modelling choices (Nagini fragment):
  * The scanned one-to-one relations are modelled by two parallel lists indexed
    by relation position: ``is_parent_link[i]`` is whether relation ``i`` is a
    designated parent link, and ``related_key[i]`` is the identity token of the
    related model that relation ``i`` targets (the repository derives this token
    from the related model via the unchanged key-derivation callee; mapping.md
    §2). Equal tokens model the same related model.
  * The per-related-model record is a ``Dict[int, int]`` mapping a related-model
    token to the POSITION of the recorded relation. Recording a position rather
    than an opaque object keeps the chosen relation's designation observable,
    so the guarantee "every recorded relation is a parent link" is expressible
    directly on the carrier.

Both input lists are read-only and held at fractional permission; the record is
built fresh and returned at full permission. No string indexing is used (Nagini
bans it). The behaviour is modelled deeply (the eligibility filter and the
per-model recording are spelled out in the impl region); there is no
axiomatised callee. Markers (machine-parsed) delimit the spec/proof/impl
regions.
"""
from typing import Dict, List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the per-related-model recording (with its eligibility filter) is
# the behaviour under specification and is spelled out deeply in the impl
# region. The related-model token is the result of an UNCHANGED key-derivation
# callee, abstracted to the int carrier ``related_key[i]`` (a type refinement,
# mapping.md §2); it is not called inside any contract and so is not an axiom.
# axioms-end


# pure-start
# No pure helpers: the specification is phrased directly over the parallel
# input lists and the result dictionary.
# pure-end


def select_inheritance_links(is_parent_link: List[bool],
                             related_key: List[int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both inputs are read-only; fractional permission (directive 5).
    Requires(Acc(list_pred(is_parent_link), 1 / 2))
    Requires(Acc(list_pred(related_key), 1 / 2))
    # The two lists are parallel: one entry per scanned relation.
    Requires(len(is_parent_link) == len(related_key))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(is_parent_link), 1 / 2))
    Ensures(Acc(list_pred(related_key), 1 / 2))
    Ensures(dict_pred(Result()))
    Ensures(len(is_parent_link) == len(related_key))
    # (1) Every recorded relation is a designated parent link, and the position
    #     it records is a real relation position whose target is that key. An
    #     ordinary one-to-one relation is therefore never recorded -- the
    #     relation promoted to primary key downstream is always a parent link.
    Ensures(Forall(int, lambda k: (Implies(
        k in Result(),
        0 <= Result()[k] and Result()[k] < len(is_parent_link)
        and Result()[k] < len(related_key)
        and is_parent_link[Result()[k]]
        and related_key[Result()[k]] == k),
        [[k in Result()]])))
    # (3)+(4) Every related model that has a designated parent link among the
    #     scanned relations ends up recorded (no legitimate inheritance link is
    #     ever lost, independently of declaration order, clause (2)), and the
    #     recorded position is not earlier than ANY designated parent link
    #     targeting that model. Together with clause (1) the recorded position
    #     is therefore exactly the LAST designated parent-link position for
    #     that related model (last-writer-wins, clause (4)) -- the spec pins
    #     WHICH relation is recorded, not merely that some parent link is.
    Ensures(Forall(int, lambda i: (Implies(
        0 <= i and i < len(is_parent_link) and is_parent_link[i],
        related_key[i] in Result()
        and Result()[related_key[i]] >= i),
        [[is_parent_link[i]]])))
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): every scanned one-to-one relation is recorded, with no
    # eligibility filter, so the last relation written for a given related model
    # wins regardless of whether it is a designated parent link. An ordinary
    # one-to-one relation that targets a parent therefore displaces (or stands in
    # for) the genuine parent link, and the relation later promoted to primary
    # key may not be a parent link at all -- the bug the issue reports.
    result = {}  # type: Dict[int, int]
    i = 0
    while i < len(is_parent_link):
        # invariants-start
        Invariant(Acc(list_pred(is_parent_link), 1 / 2))
        Invariant(Acc(list_pred(related_key), 1 / 2))
        Invariant(dict_pred(result))
        Invariant(len(is_parent_link) == len(related_key))
        Invariant(0 <= i and i <= len(is_parent_link))
        # The strongest honest invariant of the buggy loop: every recorded
        # position is a real prefix position targeting that key -- but NOT
        # necessarily a parent link (the missing filter).
        Invariant(Forall(int, lambda k: (Implies(
            k in result,
            0 <= result[k] and result[k] < i
            and result[k] < len(related_key)
            and related_key[result[k]] == k),
            [[k in result]])))
        # Every relation in the processed prefix has been recorded (parent link
        # or not).
        Invariant(Forall(int, lambda j: (Implies(
            0 <= j and j < i,
            related_key[j] in result),
            [[related_key[j]]])))
        Invariant(MustTerminate(len(is_parent_link) - i + 1))
        # invariants-end
        result[related_key[i]] = i
        i = i + 1
    return result
    # impl-end
