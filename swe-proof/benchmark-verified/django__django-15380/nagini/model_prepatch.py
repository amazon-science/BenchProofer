"""Twin-artifact model for django__django-15380.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When reconciling the fields of a model across two project states — a prior
  state and a later state — for the purpose of detecting per-field renames,
  the routine processes a field that belongs to the model under its LATER
  identity. The two states index their models by name, but a model may itself
  carry a different name in each state: a name-correspondence map records, for
  a later-state model name, the name the same model had in the prior state.

  Resolving the descriptors needed for one field therefore uses TWO different
  model names that may differ:

    * the model's PRIOR descriptor is taken from the prior-state registry under
      the model's PRIOR name (the correspondence map applied to the later name,
      falling back to the later name when the model kept its name);

    * the model's LATER descriptor is taken from the later-state registry under
      the model's LATER name — the very name under which the field was
      enumerated.

  The consequence that matters: when a model's name differs between the two
  states, the later-state registry contains the model only under its LATER
  name, so its later descriptor MUST be looked up by the later name. Looking it
  up by the prior name would reference an entry the later-state registry does
  not contain. When the two names coincide, both lookups use the same name.

Modelling choices (Nagini fragment):
  * Model names and field names are `int` tokens; a model descriptor is an
    `int` token (a stand-in for the per-model state object whose field is then
    read). The two state registries are `Dict[int, int]` from a model-name
    token to its descriptor token.
  * The name-correspondence map is `Dict[int, int]` from a later-state model
    name to the corresponding prior-state model name; absence means the model
    kept its name.
  * Reading a single named field off a descriptor is not the operation under
    change (the field name is enumerated from that very descriptor), so it is
    not re-modelled here; the behaviour under specification is the selection of
    the correct descriptors from the two registries.

No string indexing is used (Nagini bans it). Dict access is guarded by an
explicit membership test before subscription. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The descriptor-selection logic is the behaviour under
# specification and is modelled deeply (prior_name / the impl). The registry
# lookups it composes are ordinary mapping subscriptions, validated against
# their real Python semantics out-of-band by axiom_check.py (G-AX) as an
# A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def prior_name(correspondence: Dict[int, int], later: int) -> int:
    """The model's name in the prior state: the correspondence map applied to
    the later-state name `later`, falling back to `later` when the model kept
    its name (i.e. `later` is not recorded in the map)."""
    Requires(Acc(dict_pred(correspondence), 1 / 4))
    if later in correspondence:
        return correspondence[later]
    return later
# pure-end


def resolve_field_states(prior_registry: Dict[int, int],
                         later_registry: Dict[int, int],
                         correspondence: Dict[int, int],
                         later: int) -> Tuple[int, int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(prior_registry), 1 / 2))
    Requires(Acc(dict_pred(later_registry), 1 / 2))
    Requires(Acc(dict_pred(correspondence), 1 / 2))
    # The field being processed was enumerated from the later state under the
    # model's later name, so that name is present in the later-state registry.
    Requires(later in later_registry)
    # The model's prior descriptor exists in the prior-state registry under the
    # model's prior name (the correspondence map points only at present names).
    Requires(prior_name(correspondence, later) in prior_registry)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(prior_registry), 1 / 2))
    Ensures(Acc(dict_pred(later_registry), 1 / 2))
    Ensures(Acc(dict_pred(correspondence), 1 / 2))
    # The required keys remain present in their registries (read-only states).
    Ensures(later in later_registry)
    Ensures(prior_name(correspondence, later) in prior_registry)
    # The prior descriptor is the prior-state registry under the prior name.
    Ensures(Result()[0] == prior_registry[prior_name(correspondence, later)])
    # The later descriptor is the later-state registry under the LATER name —
    # the discriminating clause: it is keyed by `later`, never by the prior
    # name. When the model's name differs across states these two names differ;
    # the prior name need not be a key of the later-state registry at all.
    Ensures(Result()[1] == later_registry[later])
    # post-conditions-end
    # impl-start
    old_name = prior_name(correspondence, later)  # type: int
    old_descriptor = prior_registry[old_name]  # type: int
    new_descriptor = later_registry[old_name]  # type: int
    return (old_descriptor, new_descriptor)
    # impl-end
