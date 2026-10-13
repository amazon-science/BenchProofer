"""Twin-artifact model for django__django-16819.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When two index-management operations on a model are considered for
  combination during migration optimisation, an operation that *adds* a named
  index, immediately considered against an operation that *removes* an index of
  the SAME name, contributes nothing: the pair cancels and the combined result
  is the empty operation list. This is the discriminating behaviour the issue
  asks for — adding an index and then removing the same index is a no-op.

  For every other counterpart operation the add-index operation falls back to
  the generic combination rule shared by all operations: a self-elidable
  operation is replaced by the counterpart alone; otherwise a counterpart that
  is elidable replaces the operation by the operation alone; otherwise the two
  operations cannot be combined.

The combination outcome is modelled as a small tagged code (Nagini has no mixed
list/bool return): 1 = "the pair cancels to nothing", 2 = "replace by the
counterpart alone", 3 = "replace by this operation alone", 0 = "cannot
combine". An operation is modelled as a minimal class carrying only the touched
facets: whether it is an index-removal, its name (a sequence of code points),
and whether it is elidable. The add-index operation carries the name of the
managed index and its own elidable flag.

The generic combination rule is the operation base class's own shared logic and
is modelled deeply (it is the superclass of the function under specification,
not an opaque external callee); there are therefore no axioms.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Operand:
    """A counterpart operation considered for combination. Only the touched
    facets are modelled: whether it removes an index, the name it carries
    (consulted only when it is an index-removal), and its elidable flag."""

    def __init__(self, is_remove_index: bool, name: List[int], elidable: bool) -> None:
        # Three field stores and no loop or call: this constructor obviously
        # terminates. Level 2 < reduce_add_index's 6 leaves room beneath the
        # function under specification, so a caller that itself owes termination
        # may still build the counterpart operation it passes in.
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_remove_index) and self.is_remove_index == is_remove_index)  # type: ignore
        Ensures(Acc(self.name) and self.name is name)                                    # type: ignore
        Ensures(Acc(self.elidable) and self.elidable == elidable)                        # type: ignore
        self.is_remove_index = is_remove_index
        self.name = name
        self.elidable = elidable


# axioms-start
# (no axioms: the generic combination rule is the function-under-specification's
#  own base-class logic and is modelled deeply, not axiomatized)
# axioms-end


# pure-start
@Pure
def names_equal(a: List[int], b: List[int]) -> bool:
    """Whether two index names denote the same string."""
    Requires(Acc(list_pred(a), 1 / 4) and Acc(list_pred(b), 1 / 4))
    return ToSeq(a) == ToSeq(b)


@Pure
def base_combine(self_elidable: bool, op_elidable: bool) -> int:
    """The generic combination rule shared by every operation: a self-elidable
    operation is replaced by the counterpart alone (2); otherwise an elidable
    counterpart replaces the operation by the operation alone (3); otherwise the
    operations cannot be combined (0)."""
    if self_elidable:
        return 2
    if op_elidable:
        return 3
    return 0
# pure-end


def reduce_add_index(index_name: List[int], self_elidable: bool, operation: Operand) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(index_name), 1 / 2))
    Requires(Acc(operation.is_remove_index, 1 / 2))
    Requires(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
    Requires(Acc(operation.elidable, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(index_name), 1 / 2))
    Ensures(Acc(operation.is_remove_index, 1 / 2))
    Ensures(Acc(operation.name, 1 / 2) and Acc(list_pred(operation.name), 1 / 2))
    Ensures(Acc(operation.elidable, 1 / 2))
    # The discriminating guarantee: an index-removal of the same name cancels
    # the add to the empty list (tag 1).
    Ensures(Implies(operation.is_remove_index and names_equal(index_name, operation.name),
                    Result() == 1))
    # Otherwise the outcome is exactly the generic combination rule.
    Ensures(Implies(not (operation.is_remove_index and names_equal(index_name, operation.name)),
                    Result() == base_combine(self_elidable, operation.elidable)))
    # The outcome is always one of the four legal tags.
    Ensures(Result() == 0 or Result() == 1 or Result() == 2 or Result() == 3)
    # post-conditions-end
    # impl-start
    if operation.is_remove_index and names_equal(index_name, operation.name):
        return 1
    if self_elidable:
        return 2
    if operation.elidable:
        return 3
    return 0
    # impl-end
