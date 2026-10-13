"""Twin-artifact model for django__django-16938.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A related collection is serialized by reference: only the primary key of each
  member is needed, so the member collection is fetched in a primary-key-only
  projection. The collection is obtained from its owning record's default
  accessor, and that accessor may itself carry, as a baked-in default, a request
  to eagerly co-select one or more *adjacent* related records (a so-called
  "follow these links" default attached by a custom accessor). The accessor may
  equally carry a baked-in projection of its own, given either as the codes to
  keep or as the codes to leave out.

  Fetching such a collection in a primary-key-only projection is only well-formed
  when NO adjacent record is simultaneously (a) requested for eager co-selection
  AND (b) dropped by the projection. A baked-in eager-co-selection request that
  names an adjacent record which the projection drops is exactly that ill-formed
  combination, and evaluating it is an error.

  The desired behaviour is therefore: the reference fetch the serializer builds
  must be well-formed for EVERY owning collection, including one whose accessor
  bakes in such an eager-co-selection request. The built fetch leaves no adjacent
  record both requested and dropped, so its evaluation never errors -- whatever
  the accessor baked in -- and no *specific* set of adjacent records is requested
  of it any more. That reset is wholesale rather than selective: the built fetch
  falls back on the unrestricted default and NAMES NO adjacent-record code at
  all, so the specific codes the accessor had baked in are DISCARDED rather than
  carried along, narrowed or reshuffled. Whether an adjacent record still gets
  co-selected is then decided by the unrestricted default alone, from the
  adjacent record's own shape, and no longer by any named request -- which is why
  no named request can conflict with the projection.

  Its projection is the by-reference one: it narrows to the single primary-key
  code, so the codes the projection itself lists carry no superfluous code
  besides the primary key, EXCEPT that narrowing to a code the accessor's own
  projection had already put on its leave-out list cancels the restriction
  outright and the projection then imposes no limit at all. (This is a statement
  about the projection's own list of codes; it does not claim anything about
  columns a co-selected adjacent record contributes to the fetch on top of it.)

  The members the build addresses are the same members the owning collection's
  accessor addresses: the build inherits the owning record's membership filter
  unchanged and neither widens nor narrows nor fabricates it, so it is directed
  at exactly the same collection membership. (This is a statement about which
  members the fetch is DIRECTED AT -- the membership it selects on -- not a
  promise about how many records evaluating it ultimately returns, which the
  co-selection performed by the unrestricted default may further restrict.)

A collection-fetch specification carries only the touched facets of its query
state: whether a *specific* set of adjacent records is requested for eager
co-selection (the "restricted" flag), the specifically requested adjacent-record
field codes (``requested``, a ``PSet[int]``), the primary keys of the members the
fetch addresses (``members``, a ``PSet[int]``), and the projection, held the way
the query state itself holds it -- a set of explicitly listed field codes
(``listed``) together with a flag saying whether that list is the codes to leave
OUT rather than the codes to keep (``excluding``). An empty list means the
projection imposes no restriction, so every code is loaded. The ill-formedness
predicate and the two query operations are modelled deeply over those facets;
the field accessor is the unchanged callee.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Fetch:
    """A collection-fetch query state, carrying only the touched facets.

    * ``restricted`` -- True iff a *specific* set of adjacent records is
      requested for eager co-selection (the request is a concrete named set
      rather than the unrestricted default). Only when this holds can the
      ill-formed combination arise.
    * ``requested`` -- the set of adjacent-record field codes named for eager
      co-selection (meaningful only when ``restricted``).
    * ``members`` -- the primary keys of the collection members the fetch
      addresses.
    * ``listed`` -- the field codes the projection explicitly lists. Empty means
      the projection imposes no restriction (every code is loaded).
    * ``excluding`` -- True iff ``listed`` is the set of codes to leave OUT
      (rather than the set of codes to keep).
    """

    def __init__(self, restricted: bool, requested: PSet[int], members: PSet[int],
                 listed: PSet[int], excluding: bool) -> None:
        # Terminates: five straight-line field assignments, no loop and no
        # obligated call. Level 2 sits strictly below every caller's level
        # (clear_specific_request 6, only_pk 10, build_pk_iterator 14), so a
        # caller constructing a Fetch does not leak its own obligation.
        Requires(MustTerminate(2))
        Ensures(Acc(self.restricted) and self.restricted == restricted)   # type: ignore
        Ensures(Acc(self.requested) and self.requested is requested)      # type: ignore
        Ensures(Acc(self.members) and self.members is members)            # type: ignore
        Ensures(Acc(self.listed) and self.listed is listed)               # type: ignore
        Ensures(Acc(self.excluding) and self.excluding == excluding)      # type: ignore
        self.restricted = restricted
        self.requested = requested
        self.members = members
        self.listed = listed
        self.excluding = excluding


# axioms-start
# (No axiomatized callees: the two query operations the build composes
# -- one that leaves no *specific* eager-co-selection request standing, and one
# that narrows the projection to a single field code -- are unchanged operations
# modelled DEEPLY as state transitions over the touched facets (R-refinements,
# see refinement.md); the ill-formedness predicate is the deep model of the
# unchanged descend check the fetch performs at evaluation. The accessor that
# yields the base collection is refined to its base-state argument. No
# @ContractOnly contract is consumed by the proof.)
# axioms-end


# pure-start
@Pure
def dropped(listed: PSet[int], excluding: bool, pk: int, f: int) -> bool:
    """The projection drops field code ``f``. The primary-key code is never
    dropped (a by-reference projection always carries it), and an empty list
    imposes no restriction, so nothing is dropped. Otherwise a listed code is
    dropped exactly when the list is a leave-out list, and an unlisted code is
    dropped exactly when the list is a keep list."""
    return f != pk and len(listed) > 0 and (
        f in listed if excluding else not (f in listed))


@Pure
def ill_formed(restricted: bool, requested: PSet[int], listed: PSet[int],
               excluding: bool, pk: int) -> bool:
    """The fetch is ill-formed (its evaluation errors) exactly when a *specific*
    set of adjacent records is requested for eager co-selection AND the
    projection restricts what is loaded AND at least one requested adjacent
    record is dropped by it. When no specific set is requested (unrestricted
    default), or the projection imposes no restriction, the combination cannot
    arise, so the fetch is well-formed."""
    return restricted and len(listed) > 0 and Exists(
        int, lambda f: f in requested and dropped(listed, excluding, pk, f))
# pure-end


def clear_specific_request(q: Fetch) -> Fetch:
    # pre-conditions-start
    Requires(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
             and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
             and Acc(q.excluding, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
            and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
            and Acc(q.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # No *specific* set of adjacent records is requested any more (the request
    # becomes the unrestricted default, which names no adjacent-record code at
    # all). The addressed members and the projection are carried through
    # unchanged.
    Ensures(Result().restricted == False)
    Ensures(len(Result().requested) == 0)
    Ensures(Result().members is q.members)
    Ensures(Result().listed is q.listed)
    Ensures(Result().excluding == q.excluding)
    # post-conditions-end
    # impl-start
    return Fetch(False, q.requested - q.requested, q.members, q.listed,
                 q.excluding)
    # impl-end


def only_pk(q: Fetch, pk: int) -> Fetch:
    # pre-conditions-start
    Requires(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
             and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
             and Acc(q.excluding, 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(q.restricted, 1 / 2) and Acc(q.requested, 1 / 2)
            and Acc(q.members, 1 / 2) and Acc(q.listed, 1 / 2)
            and Acc(q.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # Narrowing the projection to the single primary-key code. The narrowed
    # projection is a keep list, and the eager-co-selection request and the
    # addressed members are unchanged. The list becomes exactly {pk} -- EXCEPT
    # when the incoming projection was a leave-out list that already carried the
    # primary-key code: the codes to keep are then the named one minus what is
    # already left out, which is nothing, and an empty list imposes no
    # restriction at all.
    Ensures(Result().restricted == q.restricted)
    Ensures(Result().requested is q.requested)
    Ensures(Result().members is q.members)
    Ensures(Result().excluding == False)
    Ensures(Implies(q.excluding and pk in q.listed, len(Result().listed) == 0))
    Ensures(Implies(not (q.excluding and pk in q.listed),
                    Result().listed == PSet(pk)))
    # post-conditions-end
    # impl-start
    if q.excluding and pk in q.listed:
        return Fetch(q.restricted, q.requested, q.members,
                     PSet(pk) - PSet(pk), False)
    return Fetch(q.restricted, q.requested, q.members, PSet(pk), False)
    # impl-end


def build_pk_iterator(base: Fetch, pk: int) -> Fetch:
    # pre-conditions-start
    # The base collection comes from the owning record's accessor; it may carry
    # ANY baked-in eager-co-selection request (restricted or not, naming any
    # adjacent-record fields) and ANY baked-in projection (a keep list or a
    # leave-out list over any codes). The build must be well-formed for all of
    # them.
    Requires(Acc(base.restricted, 1 / 2) and Acc(base.requested, 1 / 2)
             and Acc(base.members, 1 / 2) and Acc(base.listed, 1 / 2)
             and Acc(base.excluding, 1 / 2))
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(base.restricted, 1 / 2) and Acc(base.requested, 1 / 2)
            and Acc(base.members, 1 / 2) and Acc(base.listed, 1 / 2)
            and Acc(base.excluding, 1 / 2))
    Ensures(Acc(Result().restricted) and Acc(Result().requested)
            and Acc(Result().members) and Acc(Result().listed)
            and Acc(Result().excluding))
    # The discriminating guarantee: the reference fetch the serializer builds is
    # WELL-FORMED for EVERY base collection -- including one whose accessor baked
    # in an eager-co-selection request naming an adjacent record that a
    # primary-key-only projection drops. No adjacent record is left both
    # requested and dropped.
    Ensures(not ill_formed(Result().restricted, Result().requested,
                           Result().listed, Result().excluding, pk))
    # It is unrestricted outright: no *specific* set of adjacent records is
    # requested of the built fetch at all, whatever the accessor baked in.
    Ensures(Result().restricted == False)
    # ... and that reset DISCARDS the specifically named adjacent-record codes
    # rather than carrying, narrowing or reshuffling them: the built fetch names
    # NO adjacent-record code whatsoever, for EVERY accessor default. Together
    # with the clause above this leaves the eager-co-selection request at the
    # unrestricted default in both of its facets, so no named request survives
    # that any projection could contradict.
    Ensures(len(Result().requested) == 0)
    # Faithfulness of the projection: it is a keep list, and it is the
    # by-reference one -- exactly the single primary-key code, no superfluous
    # code -- unless the accessor's own projection had already put the
    # primary-key code on its leave-out list, in which case narrowing leaves an
    # empty list, which imposes no restriction.
    Ensures(Result().excluding == False)
    Ensures(Implies(base.excluding and pk in base.listed,
                    len(Result().listed) == 0))
    Ensures(Implies(not (base.excluding and pk in base.listed),
                    Result().listed == PSet(pk)))
    # Grounding: the build addresses the SAME members as the owning collection's
    # accessor yields (the build references the input, it does not fabricate or
    # discard the underlying record set).
    Ensures(Result().members == base.members)
    # post-conditions-end
    # impl-start
    cleared = clear_specific_request(base)  # type: Fetch
    narrowed = only_pk(cleared, pk)         # type: Fetch
    return narrowed
    # impl-end
