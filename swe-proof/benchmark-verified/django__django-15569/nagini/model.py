"""Twin-artifact model for django__django-15569.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A registry component answers "does this name resolve, and to what?". Names
  can be registered at two levels: a local backing store belonging to the
  component itself, and an enclosing registration layer the component falls
  back to. A read resolves a name to the local registration when the name is
  registered locally, and otherwise to whatever the enclosing layer provides
  for that name. For fast reads the answers are memoised in a derived lookup
  view; the view is kept consistent with the two registration layers so that a
  read of any name reflects their current contents.

  Which answers count as "the enclosing layer" is a property of the component
  doing the reading, not of the registration hierarchy at large: different
  components may consult different subsets of it, so ``inherited`` carries the
  fallback answers THIS component's own reads use — i.e. what a read of this
  component reports for a name the component itself does not register. The
  incoming state satisfies the corresponding read-through law, stated as a
  precondition below.

  A registry is read through MANY components, not one. A component's local
  registrations are consulted by its own reads and equally by the reads of every
  other component that falls back to it, and each such reader memoises the
  answers IT reports. One reader's memoised answers are a separate observable
  from another's: they are distinct derived views over a shared registration
  layer, so bringing one of them in line says nothing about the others.
  ``reader_view`` therefore carries the memoised answers of an ARBITRARY reader
  of this registry — any component through which the registry can be read,
  including this one — and ``reader_rest`` carries what that reader's OWN read
  range provides once this component's local store is set aside. Because the
  reader is an arbitrary parameter rather than a chosen one, a claim about it is
  a claim about EVERY reader at once.

  The operation under specification removes the item registered under a name in
  the local store. It must:

    * delete that name's registration from the local backing store, and
    * keep the derived answers consistent — for EVERY reader of the registry,
      not merely for the component through which the removal was requested — so
      that a subsequent read of the removed name no longer reports the local
      registration but reports exactly what that reader's remaining registration
      levels provide for it, which, when they register nothing under that name,
      means the name no longer resolves at all for that reader.

  The behaviour that matters: a removal that updates only the local store but
  leaves memoised answers reporting the old answer for the removed name lets a
  later read answer from an out-of-date view and still report the removed local
  registration. Bringing only the requesting component's own answers back in
  line is not enough, for exactly the same reason one level down: a reader that
  falls back to this component keeps its own memoised answers, so a read through
  THAT reader still reports the removed local registration even though a read
  through the component itself no longer does. After the removal a read of the
  removed name — through the component, or through any other component that
  reaches this component's registrations — must report that reader's remaining
  registration levels' answer for it, while names other than the removed one
  continue to resolve exactly as before for every reader. This is the round trip
  a registry relies on: register-then-remove a name locally leaves no trace of
  the local registration for subsequent reads, whichever component those reads
  go through.

Modelling choices (Nagini fragment):
  * The local backing store, the enclosing registration layer and the derived
    views are each modelled as ``Dict[int, int]`` from a name token to a
    registration state. A distinguished value ``unregistered()`` records "this
    name is not registered at this level / a read does not resolve it"; any
    other value is the identity of the item the name resolves to.
    ``store[name] != unregistered()`` means the name is registered locally;
    ``inherited[name] != unregistered()`` means the enclosing layer this
    component falls back to provides it; ``view[name] != unregistered()`` means
    a read of that name currently resolves. This value-state carrier is used
    because the underlying
    structures evolve only by re-binding a single name (Nagini does not support
    key deletion); a read returning "name absent" is modelled as the view
    reporting ``unregistered()`` for it. Only per-name state is observed, so
    integer identity is the faithful carrier (mapping.md §2).
  * A SECOND reader of the registry is modelled by the same pair of carriers one
    level out: ``reader_view`` is that reader's memoised answers and
    ``reader_rest`` is what its own read range provides with this component's
    local store set aside. The reader is universally quantified by being a
    PARAMETER — the contract must hold for every dictionary pair admitted by the
    precondition, hence for every reader of the registry, so no particular
    reader, depth or distance is singled out. When the reader is this component
    itself the two pairs coincide, which is why ``reader_view`` and
    ``reader_rest`` are not required to be disjoint from ``view`` and
    ``inherited`` (mapping.md §1).
  * The affected name is an integer parameter. No string indexing is used
    (Nagini bans it).
  * The local store and the derived views are genuinely mutated in place, so
    each is held at full permission and its post-state for the affected name is
    stated exactly. What the OTHER registration levels provide is only read, so
    ``inherited`` and ``reader_rest`` are held at half permission. The
    whole-structure frame (no OTHER name's resolution disturbed) is carried by
    the single-name-write skeleton (refinement.md), with a representative
    unrelated name pinned per-key here and the quantified frame stated over all
    three written-or-read views.
  * ``inherited`` is constrained relative to ``store`` and ``view`` by the
    read-through law in the precondition rather than left as a free third
    mapping. That law is what makes ``inherited[name]`` mean "the answer a read
    of THIS component falls back to for that name": without it the parameter
    would be an arbitrary dictionary and the postcondition below would claim a
    resolution no read of this component ever produces. ``reader_view`` and
    ``reader_rest`` are tied to real reads by the corresponding per-reader law:
    a reader either reports this component's local registration for a name
    (it reaches this component and that registration wins its merge) or it
    reports exactly what its own remaining levels provide.

The behaviour is modelled deeply (the store deletion and the derived-view
updates are spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl region.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: keeping the backing store and the derived resolved views consistent
# is the behaviour under specification and is spelled out deeply in the impl
# region. There is no unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def unregistered() -> int:
    # The distinguished registration state meaning "this name is not registered
    # at this level" / "a read of this name does not resolve". Any other value
    # held for a name is the identity of the item it resolves to.
    return 0


@Pure
def other_name() -> int:
    # A representative pre-existing, unrelated registered name. It witnesses
    # that the operation leaves names other than the affected one resolving
    # exactly as before, in the backing store and in every reader's answers.
    return -1
# pure-end


def remove_registration(store: Dict[int, int], view: Dict[int, int],
                        inherited: Dict[int, int],
                        reader_view: Dict[int, int],
                        reader_rest: Dict[int, int], name: int) -> None:
    # pre-conditions-start
    # The store and this component's own view are mutated in place: full
    # permission for each.
    Requires(dict_pred(store))
    Requires(dict_pred(view))
    # The enclosing registration layer is only read: half permission.
    Requires(Acc(dict_pred(inherited), 1 / 2))
    # An ARBITRARY reader of this registry. Its memoised answers are equally the
    # operation's to keep in line, so full permission; what its own remaining
    # registration levels provide is not this operation's to change, so half.
    Requires(dict_pred(reader_view))
    Requires(Acc(dict_pred(reader_rest), 1 / 2))
    Requires(name in store)
    Requires(name in view)
    Requires(name in inherited)
    Requires(name in reader_view)
    Requires(name in reader_rest)
    Requires(other_name() in store)
    Requires(other_name() in view)
    Requires(other_name() in reader_view)
    Requires(other_name() != name)
    # This operation: the name is currently registered in the local store ...
    Requires(store[name] != unregistered())
    # ... and the derived view currently reports it as resolving (a prior read
    # memoised the local registration): the out-of-date answer a view-blind
    # removal would leave behind.
    Requires(view[name] != unregistered())
    # READ-THROUGH LAW on the incoming state, over every name at once. This is
    # what identifies ``inherited`` as the fallback answers THIS component's own
    # reads use, rather than an arbitrary third mapping: a read resolves a
    # locally-registered name to the LOCAL registration, and a name the local
    # store does not register to exactly what the enclosing layer provides for
    # it. Without this the postcondition below would be free to claim a
    # resolution no read of this component can produce.
    Requires(Forall(int, lambda k: (Implies(k in store and k in view and store[k] != unregistered(),
                                            view[k] == store[k]), [[view[k]]])))
    Requires(Forall(int, lambda k: (Implies(k in store and k in view and k in inherited and store[k] == unregistered(),
                                            view[k] == inherited[k]), [[view[k]]])))
    # READ-THROUGH LAW FOR THE ARBITRARY READER, over every name at once. What a
    # reader reports is an answer real reads produce, not a free value: either
    # the reader reaches this component and the local registration is what wins
    # its merge, so it reports the LOCAL registration, or it reports exactly what
    # its own remaining registration levels provide. Readers that do not reach
    # this component at all satisfy the second disjunct everywhere, so they are
    # admitted too. This law leaves ``reader_rest[name]`` free — the local
    # registration it competes with is denied ``unregistered()`` by the
    # precondition above — which is what keeps the per-reader postcondition
    # below discriminating rather than derivable from the incoming carriers.
    Requires(Forall(int, lambda k: (Implies(k in store and k in reader_view and k in reader_rest,
                                            reader_view[k] == store[k] or reader_view[k] == reader_rest[k]),
                                    [[reader_view[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(store))
    Ensures(dict_pred(view))
    Ensures(Acc(dict_pred(inherited), 1 / 2))
    Ensures(dict_pred(reader_view))
    Ensures(Acc(dict_pred(reader_rest), 1 / 2))
    Ensures(name in store and name in view and name in inherited)
    Ensures(name in reader_view and name in reader_rest)
    Ensures(other_name() in store and other_name() in view)
    Ensures(other_name() in reader_view)
    # (1) The name is no longer registered in the local backing store.
    Ensures(store[name] == unregistered())
    # (2) The derived view no longer reports the removed name's LOCAL
    #     registration: a subsequent read of it reflects the remaining
    #     registration levels, i.e. exactly what the enclosing layer THIS
    #     component falls back to provides for that name (``unregistered()``
    #     when it provides nothing, which is what the read-through law in the
    #     precondition ties that value to). This is the clause a view-blind
    #     removal (store-only) violates.
    Ensures(view[name] == inherited[name])
    # (2b) THE SAME OBLIGATION FOR EVERY OTHER READER OF THE REGISTRY. A read of
    #      the removed name through ANY component that reaches this component's
    #      registrations must likewise report exactly what that reader's own
    #      remaining registration levels provide for it — ``unregistered()`` when
    #      they provide nothing, and the surviving level's item when one of them
    #      does. Because the reader is an arbitrary parameter, this is a claim
    #      about all of them at once. A removal that brings only the requesting
    #      component's own answers back in line leaves every reader that reaches
    #      it still reporting the removed local registration: such a removal
    #      satisfies clause (2) and violates this one.
    Ensures(reader_view[name] == reader_rest[name])
    # The representative unrelated name still resolves to its exact item in the
    # store and for every reader: the operation disturbs only the affected
    # name's resolution, and may not repair one name's answers by disturbing
    # another's.
    Ensures(store[other_name()] == Old(store[other_name()]))
    Ensures(view[other_name()] == Old(view[other_name()]))
    Ensures(reader_view[other_name()] == Old(reader_view[other_name()]))
    # Whole-structure frame: EVERY name other than the affected one keeps its
    # exact registration state in the backing store and its exact resolution in
    # every derived view — no other name's membership changes and no other
    # name's bound state changes. (Explicit triggers keep the quantifiers
    # tractable.)
    Ensures(Forall(int, lambda k: (Implies(k != name, (k in store) == Old(k in store)), [[k in store]])))
    Ensures(Forall(int, lambda k: (Implies(k != name and k in store, store[k] == Old(store[k])), [[store[k]]])))
    Ensures(Forall(int, lambda k: (Implies(k != name, (k in view) == Old(k in view)), [[k in view]])))
    Ensures(Forall(int, lambda k: (Implies(k != name and k in view, view[k] == Old(view[k])), [[view[k]]])))
    Ensures(Forall(int, lambda k: (Implies(k != name, (k in reader_view) == Old(k in reader_view)), [[k in reader_view]])))
    Ensures(Forall(int, lambda k: (Implies(k != name and k in reader_view, reader_view[k] == Old(reader_view[k])), [[reader_view[k]]])))
    # post-conditions-end
    # impl-start
    store[name] = unregistered()
    view[name] = inherited[name]
    reader_view[name] = reader_rest[name]
    # impl-end
