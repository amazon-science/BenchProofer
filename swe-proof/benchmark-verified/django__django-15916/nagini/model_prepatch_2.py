"""Twin-artifact model for django__django-15916.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a model-backed form class is constructed, the per-field builder that
  turns each model field into a form field is selected from the form's own
  options/configuration object. The selection follows ordinary attribute
  resolution on that options object:

    - if the options object declares its own builder, that builder is used;
    - otherwise the builder inherited from the options object's parent (the
      base form's options) is used;
    - otherwise no custom builder is used (the model's default applies).

  This rule holds uniformly for two construction paths:

    (1) a class declared directly with a model-backed options object that
        carries a builder; and
    (2) a class produced by the run-time factory from a base form whose
        options object carries a builder (with no builder passed to the
        factory) -- and likewise for any further subclass of that produced
        class.

  In every case the builder that ends up driving field construction is the one
  resolvable from the options object, never silently replaced by "no builder".

Identities (callbacks / builders, options objects) are modelled as small
integer codes: 0 denotes "absent / no builder"; any positive value denotes a
specific builder identity. An options object is modelled as a pair (own
builder, inherited builder) capturing attribute resolution through its parent.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: this behaviour is a pure attribute-resolution / data-flow change,
# modelled deeply over integer identity codes; no unchanged opaque callee is
# consumed inside a contract.)
# axioms-end


# pure-start
@Pure
def resolve_attr(own: int, inherited: int) -> int:
    """Ordinary attribute resolution on an options object: an attribute set
    directly on the object (own != 0) shadows the one inherited from its
    parent (inherited); when the object sets nothing of its own (own == 0) the
    inherited value is seen. 0 denotes "attribute absent" on either level."""
    if own != 0:
        return own
    return inherited
# pure-end


def declared_form_callback(meta_own: int, meta_inherited: int) -> int:
    # The builder selected for a form class declared directly from a
    # model-backed options object carrying (meta_own, meta_inherited).
    # pre-conditions-start
    Requires(meta_own >= 0)
    Requires(meta_inherited >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The selected builder is exactly the one resolvable from the options
    # object: own shadows inherited; absence of both yields "no builder".
    Ensures(Result() == resolve_attr(meta_own, meta_inherited))
    Ensures(Implies(meta_own != 0, Result() == meta_own))
    Ensures(Implies(meta_own == 0, Result() == meta_inherited))
    # A builder declared on the options object is never lost.
    Ensures(Implies(meta_own != 0, Result() != 0))
    # post-conditions-end
    # impl-start
    # The options object stores its resolved builder; the constructor reads it
    # straight from there to drive field construction.
    stored = resolve_attr(meta_own, meta_inherited)
    return stored
    # impl-end


def factory_form_callback(
    passed: int, base_meta_own: int, base_meta_inherited: int
) -> int:
    # The builder selected for a form class produced by the run-time factory:
    #   `passed`            -- builder handed to the factory (0 == none given);
    #   base_meta_own/...   -- the base form's options-object builder, which the
    #                          produced options object inherits.
    # pre-conditions-start
    Requires(passed >= 0)
    Requires(base_meta_own >= 0)
    Requires(base_meta_inherited >= 0)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The produced options object's own builder is the one passed to the
    # factory (when one was passed); otherwise it inherits the base options
    # object's resolved builder. The constructor then selects via the same
    # attribute-resolution rule -- so a builder reachable through the base
    # form's options is preserved when the factory is given none.
    Ensures(Result() == resolve_attr(passed, resolve_attr(base_meta_own, base_meta_inherited)))
    Ensures(Implies(passed != 0, Result() == passed))
    Ensures(
        Implies(
            passed == 0,
            Result() == resolve_attr(base_meta_own, base_meta_inherited),
        )
    )
    # When the factory is given no builder but the base options carry one, the
    # produced class still drives field construction with that builder.
    Ensures(Implies(passed == 0 and base_meta_own != 0, Result() == base_meta_own))
    Ensures(
        Implies(
            passed == 0 and base_meta_own == 0 and base_meta_inherited != 0,
            Result() == base_meta_inherited,
        )
    )
    # post-conditions-end
    # impl-start
    # PRE-PATCH: the factory injected the passed builder as a class-level
    # attribute UNCONDITIONALLY -- including the "no builder" value (0) when
    # nothing was passed. The constructor read that class-level attribute in
    # preference to anything reachable from the options object, so the base
    # form's options builder was overridden by 0 whenever the factory was given
    # none. Model that override: the injected (possibly 0) value always wins.
    attrs_level = passed            # injected unconditionally (0 when none)
    stored = attrs_level
    return stored
    # impl-end
