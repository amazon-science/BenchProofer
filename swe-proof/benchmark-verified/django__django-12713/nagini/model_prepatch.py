"""Twin-artifact model for django__django-12713.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A configuration step assembles a mapping of keyword options that build a form
  field for a multi-valued relation. Those options may already carry an explicit
  presentation component supplied by the caller. The step also has a default
  presentation component it would otherwise pick, chosen from the relation's
  name by a priority order among three name-membership tests: the primary test
  has highest priority, then the secondary, then the tertiary; if the name
  satisfies none of them no default is chosen.

  The single behaviour pinned here is the precedence between the caller's
  explicit component and the name-derived default:

  (1) When the options already carry an explicit presentation component, that
      component is left exactly as the caller supplied it -- no name-derived
      default is allowed to replace it -- regardless of which (if any) of the
      three name-membership tests the relation satisfies.

  (2) When the options do NOT carry an explicit presentation component, the
      name-derived default is established, selected by that priority order: the
      primary default if the name satisfies the primary test; else the secondary
      default if it satisfies the secondary test; else the tertiary default if
      it satisfies the tertiary test; else no component is established (the
      options still carry none).

  The consequence that matters: a caller who supplies an explicit presentation
  component keeps it even when the relation's name would otherwise select one of
  the three name-derived defaults. This mirrors the sibling configuration step
  for single-valued relations, which already honours a caller-supplied
  component.

Modelling choices (Nagini fragment):
  * The keyword options are a ``Dict[int, int]`` from an option-name token to a
    component-identity token; only membership of the presentation-component key
    and its value are observed, so integer identity is the faithful carrier
    (mapping.md §2). The presentation-component key is the module-level constant
    ``key_component()``.
  * Each of the three name-membership tests is a ``bool`` parameter (the result
    of testing the relation's name against the corresponding configured set);
    booleans need no permission. The three name-derived component identities are
    the module-level constants ``default_primary()`` / ``default_secondary()`` /
    ``default_tertiary()``.
  * Whether the options already carry the presentation component AT ENTRY is
    captured as a ``bool`` parameter ``component_present`` pinned by a
    precondition to the entry membership of ``key_component()``. This makes the
    default-selection guarantee gate on a genuine pre-state fact about the input
    rather than on a membership query against the (mutated-in-place) options,
    which would let an implementation discharge the guarantee vacuously by
    adding the key itself.

The options mapping is genuinely mutated in place, so it is held at FULL
permission and its exact post-state is stated (the pre-state membership/value of
each key is captured with ``Old`` and the entry presence of the presentation
component is captured by ``component_present``). No string indexing is used (Nagini bans it).
The whole behaviour is modelled deeply (the precedence guard and the priority
chain are spelled out in the impl region); there is no axiomatised callee.
Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the precedence guard and the name-derived default selection are the
# behaviour under specification and are spelled out deeply in the impl region.
# There is no unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def key_component() -> int:
    # The option-name token for the presentation component.
    return 0


@Pure
def default_primary() -> int:
    # Component identity selected by the highest-priority name-membership test.
    return 1


@Pure
def default_secondary() -> int:
    # Component identity selected by the second-priority name-membership test.
    return 2


@Pure
def default_tertiary() -> int:
    # Component identity selected by the third-priority name-membership test.
    return 3
# pure-end


def select_component(options: Dict[int, int],
                     component_present: bool,
                     test_primary: bool,
                     test_secondary: bool,
                     test_tertiary: bool) -> None:
    # pre-conditions-start
    # The options mapping is genuinely mutated, so FULL permission is required.
    Requires(Acc(dict_pred(options)))
    # ``component_present`` captures, AT ENTRY, whether the options already carry
    # the presentation component. It is a pre-state fact about the input -- bound
    # before any mutation -- so the default-selection guarantee below can be
    # gated on the genuine entry membership rather than on a membership query
    # that an implementation could perturb by adding the key itself.
    Requires(component_present == (key_component() in options))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(options)))
    # (1) Every option present on entry is preserved exactly -- still present on
    #     exit with the same value. This is the precedence guarantee: a
    #     caller-supplied presentation component (the presentation key being
    #     present on entry) is left exactly as supplied, so no name-derived
    #     default replaces it, whatever the three membership tests say. The step
    #     touches only the presentation component, and only by ADDING it.
    Ensures(Forall(int, lambda k: (Implies(Old(k in options),
                                           (k in options) and options[k] == Old(options[k])))))
    # (2) When the options do NOT already carry the presentation component (i.e.
    #     it was absent at entry, ``not component_present``), the name-derived
    #     default is established by the priority order primary > secondary >
    #     tertiary; if no test matches, no component is established (the options
    #     still carry none). The antecedent is the captured ENTRY fact
    #     ``not component_present``, not a membership query on the (possibly
    #     mutated) options, so each implication has teeth: an implementation must
    #     store the priority-correct default, and only it.
    Ensures(Implies(not component_present and test_primary,
                    key_component() in options
                    and options[key_component()] == default_primary()))
    Ensures(Implies(not component_present and not test_primary and test_secondary,
                    key_component() in options
                    and options[key_component()] == default_secondary()))
    Ensures(Implies(not component_present and not test_primary
                    and not test_secondary and test_tertiary,
                    key_component() in options
                    and options[key_component()] == default_tertiary()))
    Ensures(Implies(not component_present and not test_primary
                    and not test_secondary and not test_tertiary,
                    not (key_component() in options)))
    # No option key other than the presentation component is added: any key
    # present on exit other than the presentation key must have been present on
    # entry. Stated forward (the entry-membership query is the consequent, not a
    # negated antecedent on a possibly-added key) so it constrains body-added
    # keys: an implementation that stores any spurious extra option cannot
    # verify.
    Ensures(Forall(int, lambda k: (Implies((k in options) and k != key_component(),
                                           Old(k in options)))))
    # post-conditions-end
    # impl-start
    if test_primary:
        options[key_component()] = default_primary()
    elif test_secondary:
        options[key_component()] = default_secondary()
    elif test_tertiary:
        options[key_component()] = default_tertiary()
    # impl-end
