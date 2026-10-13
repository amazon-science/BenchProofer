"""Twin-artifact model for django__django-15525.

Behaviour under specification (stated as desired behaviour over observables):

  A loader resolves a record's identity by computing the record's natural key
  and looking that key up in a TARGET data store. Computing the natural key of
  the record may itself require dereferencing a related record; that
  dereference is a query whose result store is determined by the record's own
  store association at the moment the key is computed (a record with no
  association queries the ambient default store).

  Desired behaviour: when the loader operates against the target store, the
  record whose natural key is computed is associated with that target store, so
  the dereference performed while computing the key is sent to the target store
  and finds the related record (which resides there). On a non-default target
  store, computing the key of a record left with no store association would
  instead query the ambient default store — where the related record is absent —
  and the dereference would not find it. The specification therefore pins three
  observables of the resolved outcome: the association the record carried when
  its key was computed, the store that key's dereference was sent to, and that
  the dereference succeeds.

  That behaviour is claimed for EVERY target store the loader may operate
  against, the ambient default one included. The record is associated because
  the loader has a target store at all, not because that target happens to be
  some store other than the ambient default: where the two differ the
  association is what keeps the dereference off the ambient default store, and
  where they coincide it is still the association the outcome reports. The
  ambient default store is therefore left free by the specification below, so
  that an association established only where the two stores differ satisfies
  nothing.

  A natural key exists only where the dereference behind it finds the related
  record, so the outcome of resolving a record's identity is modelled as a value
  that can only come into being FROM a record already associated with the store
  the related record lives in. The association is therefore an observable of the
  key computation itself, not a state the outcome can be given afterwards.

  Two of the facts that decide whether a dereference finds anything are facts
  about the DEPLOYMENT the loader runs in, not values the loader picks: which
  store an unrouted query falls back to, and which store the related record
  actually resides in. A loader can neither redirect the ambient fallback nor
  move the related record between stores, so those two facts are handed to the
  loader as one given world and are readable there but not choosable. Every
  dereference the loader performs is therefore judged against the SAME world,
  the one it was handed — which is what makes "a natural key exists only where
  its dereference finds the related record" a claim about every key the loader
  computes rather than only about the one whose outcome it hands back. A loader
  that computes a further key on a record whose association sends that
  dereference to a store without the related record has performed a dereference
  that finds nothing, and the specification below leaves it no world in which to
  claim otherwise.

The model abstracts a "data store" as an integer identifier and a record as a
small object carrying its store association. The natural-key dereference is
modelled deeply as a routed lookup whose success depends on the queried store
matching the store the related record lives in.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# A sentinel store identifier meaning "no association yet" (a fresh instance).
UNROUTED = -1


class ModelInstance:
    """A built record. ``routed`` is the store identifier the record is
    associated with for query routing; ``UNROUTED`` means no association."""

    def __init__(self, routed: int) -> None:
        Requires(True)
        # The constructor performs one field store and no iteration, so it
        # terminates unconditionally. Level 1 sits strictly beneath the level of
        # every method that builds an instance, leaving those callers room to
        # hand their own unsatisfied obligation down to this callee.
        Requires(MustTerminate(1))
        Ensures(Acc(self.routed) and self.routed == routed)  # type: ignore[name-defined]
        self.routed = routed  # type: int


class Deployment:
    """The two routing facts of the deployment a loader runs in, as a single
    given world: ``default_store``, the ambient store an unrouted query falls
    back to, and ``record_store``, the store the related record actually
    resides in.

    Both are facts about the surroundings, not decisions of the loader: nothing
    a loader does redirects the ambient fallback, and nothing it does moves the
    related record from one store to another. So a world is something a loader
    is HANDED and may read; it is never something a loader produces. The
    constructor below is unavailable to any loader — its precondition is
    unsatisfiable — precisely so that the facts a dereference is judged against
    are the ones the surroundings determine, identical at every dereference the
    loader performs, and never a pair of numbers the loader named because they
    made a query it wanted to perform look like it succeeded.
    """

    def __init__(self, default_store: int, record_store: int) -> None:
        # Unsatisfiable by construction: the world is given, never minted. A
        # loader holds a world only because it was handed one.
        Requires(False)
        Requires(MustTerminate(1))
        Ensures(Acc(self.default_store, 1 / 2))  # type: ignore[name-defined]
        Ensures(Acc(self.record_store, 1 / 2))  # type: ignore[name-defined]
        self.default_store = default_store  # type: int
        self.record_store = record_store  # type: int


# axioms-start
# (no axioms consumed: the routed-lookup behaviour is modelled deeply below.)
# axioms-end


# pure-start
@Pure
def query_store(routed: int, default_store: int) -> int:
    """The store a dereference query is routed to: the record's own
    association if it has one, otherwise the ambient default store."""
    if routed == UNROUTED:
        return default_store
    return routed


@Pure
def dereference_succeeds(routed: int, default_store: int, record_store: int) -> bool:
    """A routed dereference of the related record succeeds iff the store the
    query is routed to is the store the related record actually lives in."""
    return query_store(routed, default_store) == record_store
# pure-end


class KeyedRecord:
    """The outcome of resolving one record's identity: its natural key has been
    computed, and this value carries the two observables of that computation —
    ``routed``, the store association the record carried at the moment its key
    was computed, and ``queried_store``, the store the related-record
    dereference behind that key was therefore sent to.

    Producing this value IS computing the natural key, which is why the
    dereference criterion below is a precondition of producing it: a natural key
    exists only where the dereference the computation performs reaches the store
    the related record lives in. A record whose association sends that query
    elsewhere — in particular an unassociated record on a non-default target,
    whose query falls back to the ambient default store — has no natural key at
    all, so there is no outcome for it and none can be produced.

    That criterion is evaluated against the world the loader was handed, so it
    binds EVERY key computation the loader performs and not merely the one whose
    outcome is handed back: the routing facts are the same at each, and a
    computation whose dereference finds nothing under them is one no loader can
    perform at all, whether or not it keeps the result.

    Evaluating ``query_store`` / ``dereference_succeeds`` is a statement about a
    routing state; it is not itself a query against a store. The dereference is
    performed here, and nowhere else in this model.

    Both observables are records of what that one computation did, so they are
    readable but never assignable: a share of each is handed out, enough for any
    consumer to read them and never enough for a later step to restate them.
    What the key computation saw is what the outcome reports.
    """

    def __init__(self, record: ModelInstance, world: Deployment) -> None:
        # The dereference is routed by the record's own association, read here,
        # at this moment. A half permission suffices to read it and is handed
        # back, so the caller keeps its own share and the record is not mutated.
        Requires(Acc(record.routed, 1 / 2))
        # The world's routing facts are read, never written: a quarter share
        # each, handed back untouched.
        Requires(Acc(world.default_store, 1 / 4) and Acc(world.record_store, 1 / 4))
        # A natural key exists only where that routed dereference finds the
        # related record — judged against the given world's facts, not against
        # numbers supplied here.
        Requires(dereference_succeeds(record.routed, world.default_store,
                                      world.record_store))
        # One field read and two field stores, no iteration, so it terminates
        # unconditionally. Level 1 sits strictly beneath the level of every
        # method that resolves a record's identity.
        Requires(MustTerminate(1))
        Ensures(Acc(record.routed, 1 / 2))
        Ensures(Acc(world.default_store, 1 / 4) and Acc(world.record_store, 1 / 4))
        Ensures(Acc(self.routed, 1 / 2) and self.routed == record.routed)  # type: ignore[name-defined]
        Ensures(Acc(self.queried_store, 1 / 2))  # type: ignore[name-defined]
        Ensures(self.queried_store  # type: ignore[name-defined]
                == query_store(record.routed, world.default_store))
        self.routed = record.routed  # type: int
        self.queried_store = query_store(record.routed, world.default_store)  # type: int


def build_with_natural_key(target_store: int, world: Deployment) -> KeyedRecord:
    # pre-conditions-start
    # The loader is handed the deployment's routing facts and may read them; it
    # keeps its share back, so it never alters the world it runs in.
    Requires(Acc(world.default_store, 1 / 2) and Acc(world.record_store, 1 / 2))
    # The related record lives in the target store the loader is loading into
    # (the fixture under load carries the related record in the same store),
    # and the target store is a real store distinct from the unrouted sentinel.
    Requires(target_store != UNROUTED)
    Requires(world.record_store == target_store)
    # The ambient default store is left FREE — it may be any store, the target
    # store itself included. The obligations below are therefore claimed for
    # every target store the loader can operate against, and in particular for
    # the one where a query that falls back to the ambient default store would
    # reach the related record anyway. Nothing here says the target store
    # differs from the ambient default one, because the record's association
    # follows from the loader having a target store at all: it is not a choice
    # an implementation may make only where those two stores happen to differ.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # The world is handed back as it was: reading the routing facts is all a
    # loader ever does to them.
    Ensures(Acc(world.default_store, 1 / 2) and Acc(world.record_store, 1 / 2))
    # The instance used to compute the natural key is associated with the
    # target store, so the natural-key dereference is routed to it...
    # (a share of each observable is granted: it is there to be read, and what
    # the key computation saw is what the outcome reports.)
    Ensures(Acc(Result().routed, 1 / 2))
    Ensures(Result().routed == target_store)
    # ...the dereference behind that key was therefore sent to the target store,
    # and not to the ambient default one...
    Ensures(Acc(Result().queried_store, 1 / 2))
    Ensures(Result().queried_store == target_store)
    # ...and therefore the dereference succeeds (the related record is found),
    # regardless of which store the ambient default would otherwise pick.
    Ensures(dereference_succeeds(Result().routed, world.default_store,
                                 world.record_store))
    # post-conditions-end
    # impl-start
    # Build the instance (fresh: no store association yet) and compute its
    # natural key on it directly, WITHOUT associating it with the target store.
    # The natural-key dereference therefore routes to the ambient default
    # store, where the related record is absent.
    obj = ModelInstance(UNROUTED)
    keyed = KeyedRecord(obj, world)
    return keyed
    # impl-end
