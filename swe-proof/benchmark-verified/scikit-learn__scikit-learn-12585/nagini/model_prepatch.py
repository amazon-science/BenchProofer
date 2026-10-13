"""Twin-artifact model for scikit-learn__scikit-learn-12585.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A generic copy routine reproduces a parameterised object. A candidate is
  classified by three observable, mutually-relevant properties: whether it is a
  plain aggregate (a list/tuple/set), whether it exposes the parameter
  introspection capability used to take it apart and rebuild it, and whether it
  is itself a *class object* rather than an *instance* of one.

  The routine's contract is about which candidates may be taken apart and
  rebuilt and which must be reproduced atomically:

    * A class object is NEVER taken apart and rebuilt, EVEN WHEN it exposes the
      introspection capability (a class exposes that capability as an attribute,
      but it is unusable without an instance to bind to). It is treated as a
      leaf: when the caller permits a fallback copy it is reproduced atomically,
      and an atomic reproduction of a class object yields THE SAME object (a
      class has no internal parameter state to deep-copy, so its reproduction is
      reference-identical to the input). When the caller forbids the fallback,
      such a candidate is refused.

    * Likewise any candidate that does not expose the introspection capability
      is a leaf, with the same permit/forbid behaviour. Such a leaf is also
      reproduced atomically when the fallback is permitted; that atomic
      reproduction need not be reference-identical (an atomic copy of a
      state-bearing leaf — e.g. a value carrier — may yield a distinct object).
      Only the class-object leaf carries the additional identity guarantee.

    * Only a genuine instance — one that exposes the introspection capability
      and is NOT a class object (and is not a plain aggregate) — is taken apart
      and rebuilt, producing a FRESH, distinct object.

  The discriminating guarantee the desired behaviour adds: a class object, when
  the fallback copy is permitted, is reproduced to the SAME object reference
  (identity preserved), instead of being mis-routed into the take-apart/rebuild
  path (which would fail outright on a class and, if it did not, would yield a
  distinct object). The identity guarantee is specific to the class-object leaf;
  a non-class leaf is only required to be reproduced atomically (and refused when
  the fallback is forbidden), not reference-identically.

The candidate is modelled as a minimal class carrying only the three
dispatch-relevant boolean properties. The refusal of an un-copyable leaf when
the fallback is forbidden is a user-defined exception (a builtin exception in an
`Exsures` crashes the Nagini translator; mapping.md §2).

Reproducing a candidate is a bounded dispatch step: it MUST terminate and
actually deliver its result (or its refusal) — a total-correctness obligation,
carried as MustTerminate in the precondition. An implementation that computes
the right value but diverges before returning it (e.g. an infinite loop
inserted into the copy routine) would satisfy every value postcondition only
vacuously and would hang the copy routine's caller forever instead of
delivering the reproduced object.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Candidate:
    def __init__(self, is_aggregate: bool, has_introspect: bool,
                 is_class_object: bool) -> None:
        # Constructing a candidate is a bounded step (three field writes);
        # its measure (1) is strictly below reproduce's (2) so the allocation
        # inside the copy routine discharges the caller's obligation.
        Requires(MustTerminate(1))
        Ensures(Acc(self.is_aggregate, 1 / 2) and  # type: ignore
                self.is_aggregate == is_aggregate)
        Ensures(Acc(self.has_introspect, 1 / 2) and  # type: ignore
                self.has_introspect == has_introspect)
        Ensures(Acc(self.is_class_object, 1 / 2) and  # type: ignore
                self.is_class_object == is_class_object)
        self.is_aggregate = is_aggregate        # type: bool
        self.has_introspect = has_introspect      # type: bool
        self.is_class_object = is_class_object    # type: bool


class NotCloneableError(Exception):
    """Signals that the candidate is a leaf that cannot be reproduced atomically
    because the caller forbade the fallback copy. Stands in for the `TypeError`
    the desired behaviour raises (a builtin exception in an `Exsures` crashes the
    Nagini translator; mapping.md §2)."""
    pass


# axioms-start
# (no axiomatized callees. The only operation this specification observes is the
# routine's own dispatch decision and the identity of what it returns on the
# leaf / non-leaf branches. The take-apart/rebuild machinery that a genuine
# instance delegates to is unchanged and unobserved here beyond the fact that it
# yields a fresh, distinct object — modelled deeply by allocating one.)
# axioms-end


# pure-start
@Pure
def is_leaf(c: Candidate) -> bool:
    """A candidate is a leaf (reproduced atomically, never taken apart) iff it
    does not expose the introspection capability OR it is a class object. The
    class-object disjunct is the discriminating property of the desired
    behaviour: a class exposes the capability as an attribute yet must still be
    treated as a leaf."""
    Requires(Acc(c.has_introspect, 1 / 4) and Acc(c.is_class_object, 1 / 4))
    return (not c.has_introspect) or c.is_class_object
# pure-end


def reproduce(est: Candidate, permit_fallback: bool) -> Candidate:
    # pre-conditions-start
    # `est` is read-only (its classification is observed, never mutated): held
    # at fractional permission so the postcondition cannot be satisfied by
    # overwriting the input.
    Requires(Acc(est.is_aggregate, 1 / 2))
    Requires(Acc(est.has_introspect, 1 / 2))
    Requires(Acc(est.is_class_object, 1 / 2))
    # The reproduced-atomically path is the one the tested behaviour exercises;
    # the aggregate path is a separate concern, excluded here.
    Requires(est.is_aggregate is False)
    # TERMINATION (total correctness): reproducing a candidate is a bounded
    # dispatch — classify, then either refuse, return the same reference, or
    # allocate one fresh object. It must actually DELIVER its result (or its
    # refusal). Without this obligation a diverging implementation (e.g. one
    # that spins forever on the rebuild path before returning the correct
    # fresh object) satisfies every value postcondition vacuously while never
    # handing its caller the reproduced object.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(est.is_aggregate, 1 / 2))
    Ensures(Acc(est.has_introspect, 1 / 2))
    Ensures(Acc(est.is_class_object, 1 / 2))
    # The input is never mutated.
    Ensures(est.is_aggregate == Old(est.is_aggregate))
    Ensures(est.has_introspect == Old(est.has_introspect))
    Ensures(est.is_class_object == Old(est.is_class_object))
    # A leaf reachable normally requires the fallback to be permitted (otherwise
    # the routine refuses — see the Exsures clause).
    Ensures(Implies(is_leaf(est), permit_fallback is True))
    # Discriminating guarantee: a CLASS-OBJECT leaf, with the fallback
    # permitted, is reproduced to the SAME object reference (identity preserved)
    # — a class has no internal parameter state to copy. In particular a class
    # object is NOT taken apart and rebuilt into a distinct object. (A non-class
    # leaf is only reproduced atomically; its atomic copy may be a distinct
    # object, so identity is NOT asserted there.)
    Ensures(Implies(is_leaf(est) and permit_fallback and est.is_class_object,
                    Result() is est))
    # A genuine instance (not a leaf) is taken apart and rebuilt into a FRESH,
    # distinct object — never the input.
    Ensures(Implies(not is_leaf(est), Result() is not est))
    # The routine refuses EXACTLY when a leaf meets a forbidden fallback. The
    # input is left intact (fractional permission returned) on the refusal path.
    Exsures(NotCloneableError, Acc(est.is_aggregate, 1 / 2) and
            Acc(est.has_introspect, 1 / 2) and Acc(est.is_class_object, 1 / 2) and
            is_leaf(est) and permit_fallback is False)
    # post-conditions-end
    # impl-start
    if not est.has_introspect:
        if not permit_fallback:
            raise NotCloneableError()
        # Atomic reproduction of a leaf: a class object (and any object with no
        # internal parameter state) is reproduced reference-identical.
        return est
    # Genuine instance: take apart and rebuild into a fresh, distinct object.
    rebuilt = Candidate(est.is_aggregate, est.has_introspect,
                        est.is_class_object)
    return rebuilt
    # impl-end
