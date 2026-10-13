"""Twin-artifact model for django__django-11400.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the row sequence backing a related model's choices is assembled, an
  EXPLICIT ordering is honoured only when one is supplied. The caller hands in
  a possibly-empty ordering specification. When that specification is non-empty,
  the rows are produced in the order it dictates (`reordered(base, ordering)`).
  When it is empty, NO reordering is performed: the rows keep the order of the
  base collection exactly as it arrives -- the base collection's own default
  order is preserved, never discarded.

  The hazard the contract rules out: applying the reorder operation with an
  empty specification is NOT guaranteed to reproduce the base order (an empty
  specification clears any pre-existing order and yields an unspecified
  arrangement). So an implementation may invoke the reorder operation only on
  the branch where the specification is non-empty.

Two related collection-choice builders share this behaviour and are modelled as
two contracted functions (`related_choice_rows`, `reverse_choice_rows`).

Rows are modelled as `List[int]` (opaque row identities); the ordering
specification is modelled as `List[int]` (its emptiness is the only property
the behaviour turns on). The reorder operation over a base collection is the
unchanged queryset callee, axiomatized (`reordered` / `apply_order_by`) and
validated against the real callee out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def reordered(base: PSeq[int], ordering: PSeq[int]) -> PSeq[int]:
    """Pure value of the unchanged queryset reorder callee
    (`QuerySet.order_by(*ordering)`) applied to a base collection.

    The operation is UNINTERPRETED: this contract states NO property of its
    value at all, and a caller may assume none.

      * Nothing ties `reordered(b, [])` to `b`. An empty ordering specification
        clears any pre-existing order, so the arrangement it then yields is
        unspecified.
      * Nothing ties the LENGTH, the membership, or the multiplicity of
        `reordered(b, o)` to `b` either. An ordering specification names
        traversal paths, and a path may cross a to-many association -- the
        operation then repeats base entries, one per associated element -- or a
        mandatory single-valued association, where an entry whose associate is
        absent drops out instead. So the operation is NOT a rearrangement of the
        base collection, and no count, set or multiset relation to `base` holds
        of its result.

    Being uninterpreted is also what GROUNDS the obligation that consumes it:
    the only way to obtain a value equal to `reordered(b, o)` is to invoke the
    operation itself (via `apply_order_by`), so the obligation cannot be
    discharged by reconstructing a value from the arguments.

    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """


@ContractOnly
def apply_order_by(base: List[int], ordering: List[int]) -> List[int]:
    """Effecting form of the reorder callee, returning a fresh row list whose
    value is `reordered(base, ordering)`. Used by the impl on the
    non-empty-ordering branch only. Read-only in its inputs (fractional)."""
    Requires(Acc(list_pred(base), 1 / 4))
    Requires(Acc(list_pred(ordering), 1 / 4))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(base), 1 / 4))
    Ensures(Acc(list_pred(ordering), 1 / 4))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering)))
# axioms-end


# pure-start
# pure-end


def copy_rows(base: List[int]) -> List[int]:
    """A faithful copy of the base collection's rows in their arriving order
    (the result list comprehension that materializes the base queryset)."""
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(MustTerminate(len(base) + 2))
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(base))
    out = []  # type: List[int]
    i = 0
    while i < len(base):
        # invariants-start
        Invariant(Acc(list_pred(base), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(base))
        Invariant(ToSeq(out) == ToSeq(base).take(i))
        Invariant(MustTerminate(len(base) - i + 1))
        # invariants-end
        out.append(base[i])
        Assert(ToSeq(base).take(i + 1) == ToSeq(base).take(i) + PSeq(base[i]))
        i = i + 1
    Assert(ToSeq(base).take(len(base)) == ToSeq(base))
    return out


def related_choice_rows(base: List[int], ordering: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ordering), 1 / 2))
    Requires(MustTerminate(len(base) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ordering), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The data-row sequence backing the choices:
    #  * empty ordering  -> the base order is preserved exactly;
    #  * non-empty order  -> the requested reordering of the base.
    Ensures(Implies(len(ordering) == 0, ToSeq(Result()) == ToSeq(base)))
    Ensures(Implies(len(ordering) > 0,
                    ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
    # post-conditions-end
    # impl-start
    if len(ordering) > 0:
        qs = apply_order_by(base, ordering)  # type: List[int]
        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
        return qs
    res = copy_rows(base)  # type: List[int]
    Assert(ToSeq(res) == ToSeq(base))
    return res
    # impl-end


def reverse_choice_rows(base: List[int], ordering: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(ordering), 1 / 2))
    Requires(MustTerminate(len(base) + 3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(ordering), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(Implies(len(ordering) == 0, ToSeq(Result()) == ToSeq(base)))
    Ensures(Implies(len(ordering) > 0,
                    ToSeq(Result()) == reordered(ToSeq(base), ToSeq(ordering))))
    # post-conditions-end
    # impl-start
    if len(ordering) > 0:
        qs = apply_order_by(base, ordering)  # type: List[int]
        Assert(ToSeq(qs) == reordered(ToSeq(base), ToSeq(ordering)))
        return qs
    res = copy_rows(base)  # type: List[int]
    Assert(ToSeq(res) == ToSeq(base))
    return res
    # impl-end
