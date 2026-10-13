"""Twin-artifact model for django__django-13158.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relational query object may be a *compound* query: it carries a sequence of
  constituent queries (the operands of a set operation such as union /
  intersection / difference). The rows such a compound query yields are
  produced ENTIRELY from its constituents — a constituent that is marked as
  matching-nothing contributes nothing, and when every constituent matches
  nothing the compound matches nothing.

  Two operations interact:

  (1) Forcing a query to match nothing must make the WHOLE query match
      nothing. For a compound query that means not only its own outer
      condition but EVERY constituent matches nothing as well; if any
      constituent still matches something, the compound keeps yielding those
      rows and the query that is supposed to match nothing still returns
      results.

  (2) Copying a query yields a copy whose observable contents equal the
      source's at the moment of the copy, and the copy is wholly its own:
      changing the copy never changes the source, and changing the source
      never changes the copy.

  The composite "produce a copy that matches nothing" operation copies first,
  then forces the copy to match nothing: the returned copy matches nothing at
  every level, while the source query and all of its constituents are left
  exactly as they were before the copy was taken.

A query is modelled as a minimal object exposing only the two touched aspects:
a boolean `where_empty` (whether its own outer condition already forces the
empty result) and `child_empty: List[bool]` (the matching-nothing flag of each
constituent query — the only constituent property the compound result reads).
`List[int]`/`PSeq` sequence reasoning carries the constituent specification;
Nagini bans richer object graphs, and a constituent is observed only through
its matching-nothing flag.

No callee is axiomatized: the change is pure object/structure logic, modelled
deeply.

Termination (total correctness): every modelled operation is a bounded
computation over one query object (a flag write/read plus one pass over the
finite constituent sequence) that must actually ANSWER — deliver its result or
complete its marking. Nagini is a partial-correctness verifier by default, so
without an explicit obligation a non-terminating implementation (e.g. bare
self-recursion, or an endless loop before returning) satisfies every `Ensures`
vacuously; the real operations always complete. The obligation is carried as
`MustTerminate` in each precondition, with strictly decreasing measures so a
routine may invoke the smaller helpers but may NOT re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# axioms-end


# pure-start
@Pure
def all_marked(flags: PSeq[bool]) -> bool:
    """True iff every constituent flag is set, i.e. the compound query matches
    nothing as a whole. Front-recursive so a single unfold is available per
    constituent."""
    if len(flags) == 0:
        return True
    return flags[0] and all_marked(flags.drop(1))
# pure-end


def lemma_all_marked(s: PSeq[bool]) -> None:
    """Ghost lemma: an elementwise 'every flag set' fact discharges the
    front-recursive `all_marked` predicate (one unfold per constituent)."""
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(s), s[k] == True))))
    # Ghost recursion over the finite sequence: one unfold per constituent,
    # strictly decreasing measure (the tail is one shorter), bounded below.
    Requires(MustTerminate(len(s) + 1))
    Ensures(all_marked(s))
    if len(s) == 0:
        return
    Assert(s[0] == True)
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(s.drop(1)),
                                          s.drop(1)[k] == s[k + 1]))))
    lemma_all_marked(s.drop(1))


class Query:
    def __init__(self) -> None:
        # A fresh minimal query is a bounded construction (one flag write and
        # one empty-sequence creation, itself a single builtin step).
        Requires(MustTerminate(2))
        Ensures(Acc(self.where_empty) and self.where_empty == False)
        Ensures(Acc(self.child_empty) and Acc(list_pred(self.child_empty)))
        Ensures(len(self.child_empty) == 0)
        self.where_empty = False  # type: bool
        self.child_empty = []  # type: List[bool]


def matches_nothing(q: Query) -> bool:
    # pre-conditions-start
    Requires(Acc(q.where_empty, 1 / 2))
    # TERMINATION: reading the matching-nothing observable is a single bounded
    # step that must actually ANSWER; without the obligation a diverging
    # implementation satisfies the value postcondition vacuously and never
    # delivers the flag to the compound-result reader.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.where_empty, 1 / 2))
    Ensures(Result() == q.where_empty)
    # post-conditions-end
    # impl-start
    return q.where_empty
    # impl-end


def mark_matching_nothing(q: Query) -> None:
    # pre-conditions-start
    Requires(Acc(q.where_empty))
    Requires(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
    # TERMINATION: marking is one flag write plus one pass over the FINITE
    # constituent sequence — it must complete (the real operation always
    # returns to its caller). Without the obligation an implementation that
    # loops forever instead of marking satisfies every Ensures vacuously.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # the query's own outer condition is forced to match nothing ...
    Ensures(Acc(q.where_empty) and q.where_empty == True)
    Ensures(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
    Ensures(len(q.child_empty) == Old(len(q.child_empty)))
    # ... AND every constituent is marked as matching nothing.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(q.child_empty),
                                           q.child_empty[k] == True))))
    # post-conditions-end
    # impl-start
    q.where_empty = True
    i = 0
    while i < len(q.child_empty):
        # invariants-start
        Invariant(Acc(q.where_empty) and q.where_empty == True)
        Invariant(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
        Invariant(0 <= i and i <= len(q.child_empty))
        Invariant(len(q.child_empty) == Old(len(q.child_empty)))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 q.child_empty[k] == True))))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len - i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(q.child_empty) - i + 1))
        # invariants-end
        q.child_empty[i] = True
        i = i + 1
    # impl-end


def duplicate(q: Query) -> Query:
    # pre-conditions-start
    Requires(Acc(q.where_empty, 1 / 2))
    Requires(Acc(q.child_empty, 1 / 2) and Acc(list_pred(q.child_empty), 1 / 2))
    # TERMINATION: copying is one pass over the FINITE constituent sequence —
    # it must complete and actually DELIVER the independent copy. Without the
    # obligation a diverging implementation satisfies every Ensures vacuously
    # and never produces the copy the composite operation empties. The measure
    # (3) strictly exceeds the fresh-object construction's (2), so the impl
    # may build the copy but may NOT re-invoke this routine itself.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # the source is read-only (returned at the same fractional permission) ...
    Ensures(Acc(q.where_empty, 1 / 2))
    Ensures(Acc(q.child_empty, 1 / 2) and Acc(list_pred(q.child_empty), 1 / 2))
    # ... the copy is a fully-owned, INDEPENDENT object whose constituent
    # sequence is a fresh copy with the same flags (mutating it cannot reach
    # the source, since the copy owns its own constituent sequence).
    Ensures(Acc(Result().where_empty) and Result().where_empty == q.where_empty)
    Ensures(Acc(Result().child_empty) and Acc(list_pred(Result().child_empty)))
    Ensures(len(Result().child_empty) == len(q.child_empty))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(q.child_empty),
                                           Result().child_empty[k] == q.child_empty[k]))))
    # post-conditions-end
    # impl-start
    obj = Query()
    obj.where_empty = q.where_empty
    i = 0
    while i < len(q.child_empty):
        # invariants-start
        Invariant(Acc(q.where_empty, 1 / 2))
        Invariant(Acc(q.child_empty, 1 / 2) and Acc(list_pred(q.child_empty), 1 / 2))
        Invariant(Acc(obj.where_empty) and obj.where_empty == q.where_empty)
        Invariant(Acc(obj.child_empty) and Acc(list_pred(obj.child_empty)))
        Invariant(0 <= i and i <= len(q.child_empty))
        Invariant(len(obj.child_empty) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                 obj.child_empty[k] == q.child_empty[k]))))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len - i, discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(q.child_empty) - i + 1))
        # invariants-end
        obj.child_empty.append(q.child_empty[i])
        i = i + 1
    return obj
    # impl-end


def none(q: Query) -> Query:
    # pre-conditions-start
    Requires(Acc(q.where_empty))
    Requires(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
    # TERMINATION: the composite must actually RETURN its matching-nothing
    # copy (the F2P observable is the returned value). The measure
    # len(child_empty) + 4 strictly exceeds the constituent operations'
    # constant measures and the ghost lemma's len + 1, so the impl may call
    # duplicate / mark_matching_nothing / lemma_all_marked but may NOT
    # re-invoke this routine itself (no strictly smaller measure exists) —
    # the postcondition cannot be discharged vacuously by self-recursion or
    # an endless loop.
    Requires(MustTerminate(len(q.child_empty) + 4))
    # pre-conditions-end
    # post-conditions-start
    # the source query is left exactly as it was: same outer condition, same
    # constituents, untouched.
    Ensures(Acc(q.where_empty) and q.where_empty == Old(q.where_empty))
    Ensures(Acc(q.child_empty) and Acc(list_pred(q.child_empty)))
    Ensures(len(q.child_empty) == Old(len(q.child_empty)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(q.child_empty),
                                           q.child_empty[k] == Old(q.child_empty[k])))))
    # the returned copy matches nothing at every level: its own outer condition
    # and every one of its constituents.
    Ensures(Acc(Result().where_empty) and Result().where_empty == True)
    Ensures(Acc(Result().child_empty) and Acc(list_pred(Result().child_empty)))
    Ensures(len(Result().child_empty) == Old(len(q.child_empty)))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(Result().child_empty),
                                           Result().child_empty[k] == True))))
    # ... hence the compound copy matches nothing as a whole.
    Ensures(all_marked(ToSeq(Result().child_empty)))
    # post-conditions-end
    # impl-start
    c = duplicate(q)
    mark_matching_nothing(c)
    lemma_all_marked(ToSeq(c.child_empty))
    return c
    # impl-end
