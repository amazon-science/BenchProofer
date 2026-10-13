"""Twin-artifact model for django__django-12406.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A model-backed single-choice field offers a leading blank placeholder
      choice exactly when an unfilled selection is a meaningful option. The
      placeholder is suppressed in two situations and offered otherwise:

        * it is suppressed when the field is mandatory AND already carries a
          pre-filled value (an empty selection would contradict the pre-fill);

        * it is ALSO suppressed when the field is rendered with a presentation
          whose unselected state is itself a visible choice (a one-of radio
          presentation) AND an empty selection is not a permitted value for
          the underlying data — because then the placeholder would masquerade
          as a genuine selectable value.

      In every other case the placeholder is offered. Whether the placeholder
      is offered is observable as: the field's choice sequence begins with a
      blank-keyed entry iff the placeholder is offered.

  (2) When such a field is derived for a related-object reference, the
      permission-to-leave-empty flag that the data layer records for that
      reference is forwarded to the field unchanged, so situation (1)'s second
      clause is decided by the data layer's own emptiness permission, not by a
      hard-coded default.

The placeholder label is modelled as an ``Optional[int]`` carrier: ``None``
means "no placeholder choice" and a present integer code means "placeholder
choice offered" (its concrete content is irrelevant to the tested behaviour).
The presentation classification (is the unselected state a visible choice) and
the emptiness-permission flag are booleans. No library callee is consumed as an
axiom: the decision is pure boolean/structure logic, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The placeholder-suppression decision and the
# permission-flag forwarding are pure boolean logic, modelled deeply. The base
# initialiser that normalises the presentation object (so its classification is
# well-defined) is an unchanged callee whose only observed effect here — that
# the presentation classification is available afterwards — is validated
# out-of-band by axiom_check.py (G-AX) as an A-reference, not consumed.
# axioms-end


# pure-start
@Pure
def placeholder_offered(required: bool, initial_present: bool,
                        is_radio: bool, blank: bool) -> bool:
    """The blank placeholder choice is offered iff NEITHER suppression
    situation holds: not (mandatory with a pre-filled value) AND not (a radio
    presentation whose empty state is not a permitted value)."""
    return not ((required and initial_present) or (is_radio and not blank))
# pure-end


class ChoiceFieldState:
    def __init__(self) -> None:
        Ensures(Acc(self.placeholder))  # type: ignore
        Ensures(self.placeholder is None)  # type: ignore
        self.placeholder = None  # type: Optional[int]


def configure_placeholder(field: ChoiceFieldState, placeholder_label: int,
                          required: bool, initial_present: bool,
                          is_radio: bool, blank: bool) -> None:
    # pre-conditions-start
    # The field object is genuinely mutated (its placeholder label is set), so
    # it carries full permission. The classification/permission inputs are
    # plain booleans (already-computed by the unchanged base initialiser).
    Requires(Acc(field.placeholder))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(field.placeholder))
    # The placeholder is OFFERED iff neither suppression situation holds; when
    # offered the field carries a present label, otherwise it carries none.
    Ensures(field.placeholder is not None
            if placeholder_offered(required, initial_present, is_radio, blank)
            else field.placeholder is None)
    # When offered, the carried label is exactly the supplied candidate label
    # (the placeholder is not replaced by some unrelated value).
    Ensures(Implies(placeholder_offered(required, initial_present, is_radio, blank),
                    field.placeholder is not None
                    and field.placeholder == placeholder_label))
    # post-conditions-end
    # impl-start
    if (required and initial_present) or (is_radio and not blank):
        field.placeholder = None
    else:
        field.placeholder = placeholder_label
    # impl-end


def derived_field_emptiness_flag(model_blank: bool) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    # The emptiness-permission flag forwarded to the derived field is exactly
    # the data layer's recorded flag for the reference (forwarded unchanged).
    Ensures(Result() == model_blank)
    # post-conditions-end
    # impl-start
    # PRE-PATCH (buggy): the data layer's recorded emptiness-permission flag is
    # NOT forwarded; the derived field falls back to the hard-coded default of
    # not permitting an empty value, regardless of what the data layer records.
    return False
    # impl-end
