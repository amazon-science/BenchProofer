"""Twin-artifact model for django__django-15499.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A model-creation step may be followed, during optimisation, by a step that
  alters one facet of that same model. When the follow-up step targets the very
  model just created (the two steps name the same model), the optimiser folds
  the pair into a single creation step that already carries the altered facet —
  there is no remaining need for a separate alter step.

  Two such facets are pinned here, each with its OWN folding rule:

    * a step that alters the model's declarative *option set* folds in by
      carrying the altered option set forward while every other facet (the
      collection of *managers*, the field list, the inheritance bases) is taken
      unchanged from the creation step;

    * a step that alters the model's collection of *managers* folds in
      SYMMETRICALLY: the resulting creation step carries the altered manager
      collection forward, while every other facet (the option set, the field
      list, the inheritance bases) is taken unchanged from the creation step.

  Name handling is two-sided and load-bearing. A created model carries BOTH a
  *display name* (the name as declared, case preserved) and a *lower-cased
  comparison key* derived from it; the follow-up step targets a model via the
  lower-cased key only. Whether the two steps name the same model is decided by
  comparing the follow-up step's key with the creation step's key — but the
  folded creation step keeps the creation step's DISPLAY name verbatim (case
  preserved), never the lower-cased key. When the follow-up step's key does NOT
  match the creation step's key, no folding occurs by these rules and the pair
  is left for later passes.

  MODELED SLICE: only the two facet-altering follow-up kinds above are within
  this model's domain. Every other follow-up step kind is dispatched to its own
  reduction rule elsewhere in the optimiser (each with its own folding
  behaviour) and is deliberately OUTSIDE the modeled slice — this model states
  nothing about those kinds.

Each model facet is modelled by an integer token (two facet values are the
"same" iff their tokens are equal); the created model is a minimal object
exposing only the touched facets (display name, lower-cased name key, field
list, option set, bases, manager collection). The display name and the
lower-cased key are DISTINCT tokens in general (they are different string
values whenever the declared name contains an upper-case letter). The incoming
follow-up step is modelled by an integer KIND tag (one of the two modeled
kinds, per the domain restriction above) plus the lower-cased name key it
targets and the facet token it would install. The optimiser outcome is
`Optional[CreateModel]`: a folded single creation step when the pair collapses,
otherwise the null token (the pair is not folded by these rules).

No callee is axiomatized: the folding is pure structural selection over the
two steps' own fields, modelled deeply. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# Follow-up step KIND tags (a stable integer per distinct MODELED step kind;
# the precondition restricts the domain to exactly these two — any other step
# kind has its own reduction rule and is outside the modeled slice):
#   0 — alters the model's option set
#   1 — alters the model's manager collection
KIND_ALTER_OPTIONS = 0
KIND_ALTER_MANAGERS = 1


class CreateModel:
    """A model-creation step exposing only the touched facets, each an integer
    token: `name` (the display name, case preserved), `name_lower` (the
    lower-cased comparison key derived from the display name), `fields` (field
    list), `options` (option set), `bases` (inheritance bases), `managers`
    (manager collection)."""

    def __init__(self, name: int, name_lower: int, fields: int, options: int,
                 bases: int, managers: int) -> None:
        # Termination: the constructor is straight-line (six field writes, no
        # loop, no call), so it terminates at the LOWEST level. Level 1 leaves
        # room beneath every obligated caller (reduce_create at 6): a caller's
        # level must be strictly greater than its callee's.
        Requires(MustTerminate(1))
        Ensures(Acc(self.name) and self.name == name)
        Ensures(Acc(self.name_lower) and self.name_lower == name_lower)
        Ensures(Acc(self.fields) and self.fields == fields)
        Ensures(Acc(self.options) and self.options == options)
        Ensures(Acc(self.bases) and self.bases == bases)
        Ensures(Acc(self.managers) and self.managers == managers)
        self.name = name  # type: int
        self.name_lower = name_lower  # type: int
        self.fields = fields  # type: int
        self.options = options  # type: int
        self.bases = bases  # type: int
        self.managers = managers  # type: int


# axioms-start
# axioms-end


# pure-start
# (no module-level pure helpers required: the folding decision is stated inline
# over the integer facet tokens and the step KIND tag.)
# pure-end


def reduce_create(model: CreateModel, op_kind: int, op_name: int,
                  op_options: int, op_managers: int) -> Optional[CreateModel]:
    # pre-conditions-start
    # The creation step is read-only (folding never mutates the input step):
    # fractional permission, required AND ensured (directive 5).
    Requires(Acc(model.name, 1 / 2))
    Requires(Acc(model.name_lower, 1 / 2))
    Requires(Acc(model.fields, 1 / 2))
    Requires(Acc(model.options, 1 / 2))
    Requires(Acc(model.bases, 1 / 2))
    Requires(Acc(model.managers, 1 / 2))
    # Domain restriction: only the two modeled facet-altering step kinds are
    # in-domain; the model states nothing about any other follow-up step kind.
    Requires(op_kind == KIND_ALTER_OPTIONS or op_kind == KIND_ALTER_MANAGERS)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(model.name, 1 / 2))
    Ensures(Acc(model.name_lower, 1 / 2))
    Ensures(Acc(model.fields, 1 / 2))
    Ensures(Acc(model.options, 1 / 2))
    Ensures(Acc(model.bases, 1 / 2))
    Ensures(Acc(model.managers, 1 / 2))
    # Folding happens EXACTLY when the follow-up step's lower-cased name key
    # matches the creation step's lower-cased key (both in-domain kinds fold on
    # a key match). Otherwise these rules leave the pair unfolded (null token).
    Ensures(Implies(Result() is not None, op_name == model.name_lower))
    Ensures(Implies(op_name == model.name_lower, Result() is not None))
    # A folded step is a creation step that keeps the original model's DISPLAY
    # name verbatim (case preserved) — NOT the lower-cased comparison key —
    # and the same derived lower-cased key.
    Ensures(Implies(Result() is not None, Acc(Result().name)))
    Ensures(Implies(Result() is not None, Acc(Result().name_lower)))
    Ensures(Implies(Result() is not None, Acc(Result().fields)))
    Ensures(Implies(Result() is not None, Acc(Result().options)))
    Ensures(Implies(Result() is not None, Acc(Result().bases)))
    Ensures(Implies(Result() is not None, Acc(Result().managers)))
    Ensures(Implies(Result() is not None, Result().name == model.name))
    Ensures(Implies(Result() is not None, Result().name_lower == model.name_lower))
    # The field list and the inheritance bases are ALWAYS carried unchanged from
    # the creation step (neither facet-altering kind touches them).
    Ensures(Implies(Result() is not None, Result().fields == model.fields))
    Ensures(Implies(Result() is not None, Result().bases == model.bases))
    # Option-alter folding: the altered option set is carried forward; the
    # manager collection is taken unchanged from the creation step.
    Ensures(Implies(Result() is not None and op_kind == KIND_ALTER_OPTIONS,
                    Result().options == op_options
                    and Result().managers == model.managers))
    # Manager-alter folding (symmetric): the altered manager collection is
    # carried forward; the option set is taken unchanged from the creation step.
    Ensures(Implies(Result() is not None and op_kind == KIND_ALTER_MANAGERS,
                    Result().managers == op_managers
                    and Result().options == model.options))
    # post-conditions-end
    # impl-start
    if op_kind == KIND_ALTER_OPTIONS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           op_options, model.bases, model.managers)
    elif op_kind == KIND_ALTER_MANAGERS and op_name == model.name_lower:
        return CreateModel(model.name, model.name_lower, model.fields,
                           model.options, model.bases, op_managers)
    return None
    # impl-end
