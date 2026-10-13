"""Twin-artifact model for django__django-15268.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The optimization layer decides, for a constraint-altering schema operation,
  whether it is safe to commute that operation past a neighbouring operation
  while collapsing a redundant pair (so two passes over a constraint become
  one). The decision is exposed as a "may commute through the neighbour"
  predicate, and the desired behaviour is:

    (1) A constraint-altering operation may commute through any neighbour that
        does NOT touch the same model.

    (2) IN ADDITION, a constraint-altering operation may commute through a
        neighbour that DOES touch the same model, provided the neighbour is
        itself a constraint-altering operation of a DIFFERENT constraint
        family (e.g. a uniqueness alteration commutes through an index
        alteration on the same model, and vice versa). Same-family neighbours
        on the same model are NOT commutable through under this rule.

  Consequently, given the four-step sequence on a single model

      [ clear-uniqueness, clear-index, set-uniqueness, set-index ]

  the set-uniqueness step may commute past the in-between clear-index step
  (different family, same model) and the set-index step may commute past the
  in-between set-uniqueness step, so each redundant clear/set pair collapses to
  the single surviving set step: the sequence reduces to

      [ set-uniqueness, set-index ].

An operation is modelled as a minimal object carrying only the two touched
attributes: a family tag (`kind`) and the identifier of the model it acts on
(`model_id`). `kind >= 0` marks a constraint-altering operation whose value is
its constraint family (0 and 1 are the two families); `kind < 0` marks any
other operation. The "touches model m" relation is modelled as
`model_id == m` for these model-scoped operations (the unchanged neighbour
predicate). The collapse decision drives the surrounding optimization loop.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

# Family tags.
FAMILY_UNIQUE = 0   # a uniqueness-constraint alteration
FAMILY_INDEX = 1    # an index-constraint alteration
# kind < 0 marks any operation that is NOT a constraint-altering operation.


# axioms-start
# (no axiomatized callees: every operation in the modelled decision is an
#  expressible integer/boolean computation, modelled deeply below.)
# axioms-end


# pure-start
@Pure
def is_constraint_alteration(kind: int) -> bool:
    """True iff the operation is a constraint-altering operation (a member of
    one of the constraint families); other operations carry a negative tag."""
    return kind >= 0


@Pure
def touches_model(op_model: int, name: int) -> bool:
    """The unchanged neighbour predicate: a model-scoped operation touches the
    model named `name` exactly when it acts on that model."""
    return op_model == name


@Pure
def base_commutes_through(self_model: int, other_kind: int,
                          other_model: int) -> bool:
    """The base rule: a model-scoped operation may commute through a neighbour
    that does not touch its model (clause 1). Independent of the family tags."""
    return not touches_model(other_model, self_model)


@Pure
def alter_commutes_through(self_kind: int, self_model: int,
                           other_kind: int, other_model: int) -> bool:
    """The constraint-altering operation's commute rule (clauses 1 + 2): the
    base rule, OR the neighbour is a constraint-altering operation of a
    different family."""
    return (
        base_commutes_through(self_model, other_kind, other_model) or
        (is_constraint_alteration(other_kind) and other_kind != self_kind)
    )
# pure-end


class Operation:
    """A schema operation: its family tag and the model it acts on. Only the
    two attributes the commute decision reads are modelled."""

    def __init__(self, kind: int, model_id: int) -> None:
        # pre-conditions-start
        Requires(True)
        Requires(MustTerminate(2))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.kind) and Acc(self.model_id))
        Ensures(self.kind == kind and self.model_id == model_id)
        # post-conditions-end
        # impl-start
        self.kind = kind          # type: int
        self.model_id = model_id  # type: int
        # impl-end


def commutes_through(self_op: Operation, other: Operation) -> bool:
    # pre-conditions-start
    Requires(Acc(self_op.kind, 1 / 2) and Acc(self_op.model_id, 1 / 2))
    Requires(Acc(other.kind, 1 / 2) and Acc(other.model_id, 1 / 2))
    # the modelled operation is a constraint-altering operation.
    Requires(is_constraint_alteration(self_op.kind))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self_op.kind, 1 / 2) and Acc(self_op.model_id, 1 / 2))
    Ensures(Acc(other.kind, 1 / 2) and Acc(other.model_id, 1 / 2))
    # The decision is exactly the constraint-altering commute rule: base rule
    # OR a different-family constraint-altering neighbour (clauses 1 + 2).
    Ensures(Result() == alter_commutes_through(
        self_op.kind, self_op.model_id, other.kind, other.model_id))
    # Pinned consequences of the rule:
    #  - may commute through any neighbour not touching this model (clause 1).
    Ensures(Implies(not touches_model(other.model_id, self_op.model_id),
                    Result()))
    #  - may commute through a same-model neighbour of a DIFFERENT family
    #    (clause 2).
    Ensures(Implies(is_constraint_alteration(other.kind) and
                    other.kind != self_op.kind, Result()))
    #  - may NOT commute through a same-model neighbour of the SAME family.
    Ensures(Implies(touches_model(other.model_id, self_op.model_id) and
                    other.kind == self_op.kind, not Result()))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: only the base rule -- a constraint-altering operation
    # may commute through a neighbour solely when that neighbour does not touch
    # this model. There is no different-family allowance.
    return not touches_model(other.model_id, self_op.model_id)
    # impl-end


def pair_collapses_through(first: Operation, between: Operation,
                           second: Operation) -> bool:
    # pre-conditions-start
    Requires(Acc(first.kind, 1 / 2) and Acc(first.model_id, 1 / 2))
    Requires(Acc(between.kind, 1 / 2) and Acc(between.model_id, 1 / 2))
    Requires(Acc(second.kind, 1 / 2) and Acc(second.model_id, 1 / 2))
    # `first` and `second` are a same-family pair on the same model (a redundant
    # clear/set pair); the in-between step is a constraint-altering operation.
    Requires(is_constraint_alteration(first.kind))
    Requires(is_constraint_alteration(between.kind))
    Requires(is_constraint_alteration(second.kind))
    Requires(first.kind == second.kind)
    Requires(first.model_id == second.model_id)
    Requires(between.model_id == first.model_id)
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(first.kind, 1 / 2) and Acc(first.model_id, 1 / 2))
    Ensures(Acc(between.kind, 1 / 2) and Acc(between.model_id, 1 / 2))
    Ensures(Acc(second.kind, 1 / 2) and Acc(second.model_id, 1 / 2))
    # The redundant pair collapses iff the in-between step may be commuted
    # through, i.e. the in-between step itself can commute past `second`.
    Ensures(Result() == alter_commutes_through(
        between.kind, between.model_id, second.kind, second.model_id))
    # The collapse succeeds exactly when the in-between step is of a DIFFERENT
    # family from the pair (the four-step sequence then reduces to two).
    Ensures(Result() == (between.kind != first.kind))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: the in-between step's commute decision against
    # `second` uses only the base rule (no different-family allowance), so a
    # same-model in-between step never commutes through and the pair does not
    # collapse.
    res = not touches_model(second.model_id, between.model_id)
    return res
    # impl-end
