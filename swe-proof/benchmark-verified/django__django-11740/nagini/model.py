"""Twin-artifact model for django__django-11740.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An altered-field operation is emitted whenever a model field's definition
  changes. The operation carries a list of ordering dependencies that the
  migration planner needs in order to apply the change in a valid order.

  When the field's NEW definition points at another model (it is a relational
  field — it names a target model it must be able to resolve), the emitted
  operation MUST carry the ordering dependencies that make the target model's
  schema available first. Those dependencies are exactly the relational
  dependencies of the new field definition, and there is always at least one
  of them (the dependency on the referenced model itself). When the new field
  definition does NOT point at another model, the operation carries no such
  dependency and its dependency list is empty.

  In other words: the dependency list attached to the altered-field operation
  is the field's relational dependencies when the new definition is relational,
  and empty otherwise. It must NOT be unconditionally empty — an operation that
  changes a plain field into one referencing another model and yet declares no
  dependency on that model cannot be ordered correctly.

The field definition is modelled by a minimal carrier exposing only the touched
property — whether its new definition references another model (``is_relation``).
The relational-dependency computation for a referencing field is an unchanged
helper, axiomatized as a pure decision returning a non-empty dependency
sequence. Dependency tuples are modelled as opaque ``int`` codes; the
specification is carried over ``PSeq[int]`` (the dependency list), for which the
load-bearing observable is which dependencies are present, in particular whether
the list is non-empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class FieldDef:
    def __init__(self, is_relation: bool) -> None:
        # Level 2 leaves room beneath any obligated caller (the modeled function
        # is at 6) so a caller that constructs a FieldDef can hand its
        # unsatisfied obligation down: this body is straight-line, no loop, no
        # call, so it terminates unconditionally.
        Requires(MustTerminate(2))
        Ensures(Acc(self.is_relation, 1 / 2) and self.is_relation == is_relation)  # type: ignore
        self.is_relation = is_relation  # type: bool


# axioms-start
@Pure
@ContractOnly
def fk_dependencies(field: FieldDef) -> PSeq[int]:
    """The unchanged helper that computes the ordering dependencies of a field
    definition that references another model. It always yields at least one
    dependency — the dependency on the referenced model itself is emitted
    unconditionally — so the returned sequence is non-empty. Pure decision over
    the field definition; provenance + executable soundness: mapping.md /
    axiom_check.py.
    """
    Requires(Acc(field.is_relation, 1 / 4))
    Requires(field.is_relation)
    Ensures(len(Result()) > 0)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def altered_field_dependencies(new_field: FieldDef) -> PSeq[int]:
    # pre-conditions-start
    Requires(Acc(new_field.is_relation, 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(new_field.is_relation, 1 / 2))
    # When the new definition references another model, the operation carries
    # exactly that field's relational dependencies — which are non-empty, so
    # the target model is depended upon (NOT an unconditionally empty list).
    Ensures(Implies(new_field.is_relation,
                    Result() == fk_dependencies(new_field) and len(Result()) > 0))
    # When the new definition references no model, the operation carries no
    # ordering dependency.
    Ensures(Implies(not new_field.is_relation, len(Result()) == 0))
    # post-conditions-end
    # impl-start
    dependencies = PSeq()  # type: PSeq[int]
    if new_field.is_relation:
        dependencies = dependencies + fk_dependencies(new_field)
    return dependencies
    # impl-end
