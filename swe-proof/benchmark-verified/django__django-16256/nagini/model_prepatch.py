"""Twin-artifact model for django__django-16256.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A related-set accessor exposes both an immediate and a deferred form of three
  object-producing operations. The immediate forms perform relation-specific
  work: producing (or locating) an object AND, when a NEW object is produced,
  attaching it to the owning instance's related set (so the object becomes a
  member of that set). The three operations are distinguished by what they do
  to an object that is ALREADY present and by the payload the delivered object
  ends up carrying:

    * "produce" always produces a new object, attaches it to the related set,
      and the object carries the payload the caller asked for;
    * "locate-or-produce" hands an already-present object back EXACTLY as it
      stands — the caller's payload is used only when a new object has to be
      produced — and attaches only a newly-produced object;
    * "refresh-or-produce" leaves the object carrying the caller's payload in
      BOTH cases: an already-present object is refreshed with it (that payload
      is what persists and what the caller receives), a new object is produced
      with it and attached.

  The deferred forms exist so a caller may obtain the result without blocking;
  the contract pinned here is that each deferred form delivers EXACTLY the
  result its SAME-named immediate counterpart would, with EXACTLY the same
  effect on the owning instance's related set and on the delivered object's
  payload. Concretely:

    (1) the deferred "produce" form delivers the object the immediate "produce"
        form would, leaves the owning instance's related set extended by that
        produced object (membership), and leaves the object carrying the
        requested payload, just as the immediate form does;

    (2) the deferred "locate-or-produce" form delivers the same object, the
        same produced/located flag and the same payload as its immediate
        counterpart, and reproduces its effects: a produced object is attached
        to the related set and carries the requested payload; an already-present
        object leaves the set unchanged and is delivered with the payload it
        already had, which is also left unchanged;

    (3) the deferred "refresh-or-produce" form behaves like (2) on membership —
        attach a produced object, leave the set unchanged for an already-present
        one — but on payload it differs: in BOTH cases the object ends up
        carrying the requested payload, and that is the payload delivered.

  The two discriminating requirements. (a) MEMBERSHIP: each deferred form must
  reproduce the membership effect of the same-named immediate form; a deferred
  form that delivers the object but does NOT attach a newly-produced object to
  the owning instance's related set violates the contract. (b) PAYLOAD: each
  deferred form must reproduce the payload behaviour of the same-named
  immediate form; a "refresh-or-produce" form that hands an already-present
  object back untouched, and a "locate-or-produce" form that overwrites an
  already-present object's payload with the caller's, both violate the
  contract — even though the two agree on the delivered identity, on the
  produced/located flag and on membership.

The related set is modelled as a `List[int]` of member object identities held
by a minimal accessor object; an object identity is an `int`. The payload of
the object an operation keys on is modelled by one `int` slot on that accessor
(`payload`) — the value currently persisted for that object — and the payload
the caller asks the object to carry is the `int` parameter `requested`. The
immediate forms are modelled deeply (a produced object is attached via a list
append, and the payload slot is written exactly when the operation is defined
to write it), and each deferred form is specified to reproduce its immediate
counterpart's post-state exactly. The produced/located flag, the delivered
object and its delivered payload are carried by a minimal result object.

Termination (total correctness): every modelled operation is bounded,
loop-free straight-line work that must actually ANSWER — deliver the produced
(or located) object to the awaiting caller. Nagini is a partial-correctness
verifier by default, so without an explicit obligation a non-terminating
implementation (e.g. an endless loop before the return) satisfies every
`Ensures` vacuously while a real deferred form that never resolves would hang
every awaiting F2P test. The obligation is carried as `MustTerminate` in each
precondition, with strictly decreasing measures (deferred form 3 -> immediate
form 2 -> result/accessor construction 1) so each routine may invoke its
callees but may NOT re-invoke itself.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class RelatedAccessor:
    """Accessor for an owning instance's related set. Carries only the touched
    fields: ``members``, the identities of the objects currently attached to the
    owning instance (the related set), and ``payload``, the value currently
    persisted for the object the operation keys on."""

    def __init__(self, members: List[int], payload: int) -> None:
        Requires(list_pred(members))
        # Constructing the accessor is bounded straight-line work (measure 1,
        # strictly below every modelled operation, so any of them may build one).
        Requires(MustTerminate(1))
        Ensures(Acc(self.members))  # type: ignore
        Ensures(Acc(self.payload))  # type: ignore
        Ensures(self.members is members)  # type: ignore
        Ensures(self.payload == payload)  # type: ignore
        self.members = members  # type: List[int]
        self.payload = payload  # type: int


class Outcome:
    """Result of a locate-or-produce / refresh-or-produce operation: the object
    identity delivered, whether it was newly produced (``created``), and the
    payload the delivered object carries."""

    def __init__(self, obj: int, created: bool, payload: int) -> None:
        # Building the result carrier is bounded straight-line work (measure 1).
        Requires(MustTerminate(1))
        Ensures(Acc(self.obj))  # type: ignore
        Ensures(Acc(self.created))  # type: ignore
        Ensures(Acc(self.payload))  # type: ignore
        Ensures(self.obj == obj)  # type: ignore
        Ensures(self.created == created)  # type: ignore
        Ensures(self.payload == payload)  # type: ignore
        self.obj = obj  # type: int
        self.created = created  # type: bool
        self.payload = payload  # type: int


# axioms-start
# (no unchanged-callee axioms are consumed: the relation-specific attachment
# and payload work of the immediate forms is modelled DEEPLY below as a list
# append and a payload write, and each deferred form's contract is tied to its
# immediate counterpart's pinned post-state. The thread-offloading machinery
# the deferred forms use to run the immediate form is unobservable at this
# granularity — the only observable fact is that the SAME immediate form runs,
# so the related set and the payload end in the SAME state — and is therefore
# not axiomatised.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required: the membership effect is pinned
# exactly by sequence equality on the related set and the payload effect by
# equality on the payload slot.)
# pure-end


def create(mgr: RelatedAccessor, obj: int, requested: int) -> int:
    # pre-conditions-start
    # The immediate "produce" form genuinely mutates the related set (it
    # attaches the produced object) and the payload slot (the produced object
    # carries the requested payload), so both are held at full permission with
    # their exact post-state pinned below.
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: producing-and-attaching is bounded work that must COMPLETE
    # and deliver the produced object. Under partial-correctness semantics a
    # diverging body satisfies every Ensures vacuously yet never answers; the
    # real immediate form always returns. Measure 2 (> 1) lets it construct
    # the result/accessor carriers; measure 2 (< 3) lets the deferred form
    # invoke it without leaking its own obligation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    # The produced object is delivered.
    Ensures(Result() == obj)
    # ATTACH: the produced object is appended to the owning instance's related
    # set (it becomes a member); nothing else changes.
    Ensures(ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj))
    # PAYLOAD: the produced object carries the payload the caller asked for.
    Ensures(mgr.payload == requested)
    # post-conditions-end
    # impl-start
    mgr.members.append(obj)
    mgr.payload = requested
    return obj
    # impl-end


def acreate(mgr: RelatedAccessor, obj: int, requested: int) -> int:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must actually RESOLVE — run the immediate
    # form to completion and deliver its result to the awaiting caller. Nagini
    # checks partial correctness by default, so without this obligation a
    # same-spec impl that spins forever before returning satisfies every
    # Ensures vacuously while its real counterpart would hang every awaiting
    # F2P test. Measure 3 (> 2) admits the delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    # (1) The deferred form delivers EXACTLY what the immediate "produce" form
    # delivers, and reproduces its effects: the produced object is attached to
    # the owning instance's related set and carries the requested payload.
    Ensures(Result() == obj)
    Ensures(ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj))
    Ensures(mgr.payload == requested)
    # post-conditions-end
    # impl-start
    # PRE-PATCH BUG: the deferred form is not the accessor's own; it runs a bare
    # produce that delivers the object with the requested payload but does NOT
    # attach it to the owning instance's related set. The related set is
    # therefore left unchanged, so the membership clause
    # `ToSeq(mgr.members) == Old(...) + PSeq(obj)` fails.
    mgr.payload = requested
    return obj
    # impl-end


def get_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                  requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: locate-or-produce is bounded work that must COMPLETE and
    # deliver its (object, produced-flag, payload) outcome; the real immediate
    # form always returns. Measure 2: may build the Outcome carrier (1), may be
    # invoked by the deferred form (3).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # `exists` records whether a matching object is already present (located),
    # in which case the related set is left unchanged and the object is handed
    # back exactly as it stands; otherwise a new object is produced, attached,
    # and given the requested payload.
    Ensures(Result().obj == obj)
    # produced flag mirrors whether the object had to be produced.
    Ensures(Result().created == (not exists))
    # LOCATE: an already-present object leaves the related set unchanged.
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    # PRODUCE: a newly-produced object is attached to the related set.
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    # LOCATE / PAYLOAD: the caller's payload is NOT applied to an object that is
    # already present — it keeps, and is delivered with, the payload it has.
    Ensures(Implies(exists, mgr.payload == Old(mgr.payload)))
    Ensures(Implies(exists, Result().payload == Old(mgr.payload)))
    # PRODUCE / PAYLOAD: a newly-produced object carries the requested payload.
    Ensures(Implies(not exists, mgr.payload == requested))
    Ensures(Implies(not exists, Result().payload == requested))
    # post-conditions-end
    # impl-start
    if exists:
        return Outcome(obj, False, mgr.payload)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)
    # impl-end


def aget_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                   requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must RESOLVE (run the immediate form to
    # completion and deliver its outcome to the awaiting caller); a diverging
    # body would satisfy every Ensures vacuously. Measure 3 (> 2) admits the
    # delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # (2) The deferred form delivers EXACTLY the object, produced flag and
    # payload the immediate "locate-or-produce" form would, and reproduces its
    # membership and payload effects.
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    Ensures(Implies(exists, mgr.payload == Old(mgr.payload)))
    Ensures(Implies(exists, Result().payload == Old(mgr.payload)))
    Ensures(Implies(not exists, mgr.payload == requested))
    Ensures(Implies(not exists, Result().payload == requested))
    # post-conditions-end
    # impl-start
    return get_or_create(mgr, obj, exists, requested)
    # impl-end


def update_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                     requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: refresh-or-produce is bounded work that must COMPLETE and
    # deliver its (object, produced-flag, payload) outcome; the real immediate
    # form always returns. Measure 2: may build the Outcome carrier (1), may be
    # invoked by the deferred form (3).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    # REFRESH / PAYLOAD: whether the object was already present or had to be
    # produced, it ends up carrying the payload the caller asked for, and that
    # is the payload delivered. This is what separates refresh-or-produce from
    # locate-or-produce: an already-present object is NOT handed back untouched.
    Ensures(mgr.payload == requested)
    Ensures(Result().payload == requested)
    # post-conditions-end
    # impl-start
    if exists:
        mgr.payload = requested
        return Outcome(obj, False, requested)
    mgr.members.append(obj)
    mgr.payload = requested
    return Outcome(obj, True, requested)
    # impl-end


def aupdate_or_create(mgr: RelatedAccessor, obj: int, exists: bool,
                      requested: int) -> Outcome:
    # pre-conditions-start
    Requires(Acc(mgr.members))
    Requires(Acc(mgr.payload))
    Requires(list_pred(mgr.members))
    # TERMINATION: the deferred form must RESOLVE (run the immediate form to
    # completion and deliver its outcome to the awaiting caller); a diverging
    # body would satisfy every Ensures vacuously. Measure 3 (> 2) admits the
    # delegation to the immediate form.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(mgr.members))
    Ensures(Acc(mgr.payload))
    Ensures(list_pred(mgr.members))
    Ensures(Acc(Result().obj))
    Ensures(Acc(Result().created))
    Ensures(Acc(Result().payload))
    # (3) The deferred form delivers EXACTLY the object, produced flag and
    # payload the immediate "refresh-or-produce" form would, and reproduces its
    # membership and payload effects.
    Ensures(Result().obj == obj)
    Ensures(Result().created == (not exists))
    Ensures(Implies(exists, ToSeq(mgr.members) == Old(ToSeq(mgr.members))))
    Ensures(Implies(not exists,
                    ToSeq(mgr.members) == Old(ToSeq(mgr.members)) + PSeq(obj)))
    Ensures(mgr.payload == requested)
    Ensures(Result().payload == requested)
    # post-conditions-end
    # impl-start
    return update_or_create(mgr, obj, exists, requested)
    # impl-end
