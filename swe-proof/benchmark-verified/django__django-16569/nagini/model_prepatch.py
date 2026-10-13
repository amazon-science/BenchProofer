"""Twin-artifact model for django__django-16569.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A hook augments a single form with two optional auxiliary fields, governed by
  three boolean configuration flags and a per-form position. The position is
  OPTIONAL: a form rendered as a standalone blank template has no position
  (it is absent / ``None``), and the hook must behave gracefully in that case
  rather than failing.

  Two independent decisions are made, each recording only whether the
  corresponding auxiliary field becomes present on the form:

    (1) The ORDERING field is present iff ordering is enabled; its initial
        value is pre-filled ONLY for a form that occupies an initial position
        (one that HAS a position below the initial-form count), and is left
        blank otherwise.

    (2) The DELETION field is present iff deletion is enabled AND either extra
        (non-initial) forms are also allowed a deletion control, OR the form
        occupies one of the initial positions. A form occupies an initial
        position only when it HAS a position at all (a positionless form does
        not) and that position lies below the initial-form count.

  Equivalently, in both decisions the "is this an initial-position form?"
  predicate is FALSE for a positionless form: a present position below the
  initial count, and never for an absent position. The deletion decision must
  honour this just as the ordering decision does, so a positionless form with
  deletion enabled but extra-deletion disabled receives NO deletion field
  (and the hook does not fail).

  (3) A form's fields are an ORDERED collection, and the placement order is
      observable: it is the order in which the form renders its controls. The
      two auxiliary controls have an INVARIANT relative placement — the ordering
      control is placed on the form AHEAD of the deletion control — so a form
      granted both renders its ordering control first and its deletion control
      immediately after. Only the controls that the decisions above make
      present are placed at all, and the hook places nothing else.

The form is modeled as a minimal mutable object exposing the booleans the hook
writes (whether each auxiliary key is present, and whether the ordering key
carries a pre-filled initial value) together with the SEQUENCE of auxiliary
keys it has placed, in placement order (the ordering key is token 1, the
deletion key is token 2). The configuration flags and the initial-form count
are read-only scalars; the position is an ``Optional[int]``.

The hook is a bounded, loop-free prologue over scalars and MUST terminate (a
total-correctness obligation, carried as ``MustTerminate`` in the
precondition). Nagini is a partial-correctness verifier by default, so without
this obligation a non-terminating implementation (e.g. bare self-recursion)
satisfies every ``Ensures`` vacuously; the real hook always returns its
augmented form.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Form:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.has_order_field) and self.has_order_field == False)  # type: ignore
        Ensures(Acc(self.order_field_prefilled) and self.order_field_prefilled == False)  # type: ignore
        Ensures(Acc(self.has_delete_field) and self.has_delete_field == False)  # type: ignore
        Ensures(Acc(self.aux_keys) and self.aux_keys == empty_key_sequence())  # type: ignore
        self.has_order_field = False  # type: bool
        self.order_field_prefilled = False  # type: bool
        self.has_delete_field = False  # type: bool
        self.aux_keys = empty_key_sequence()  # type: PSeq[int]


# axioms-start
# No consumed axioms. The changed operation is pure control flow over scalars
# (a None-guard added to an integer comparison inside a boolean disjunction),
# modeled deeply and exactly. The constructed field/widget objects and the
# initial-form count are unchanged by this behaviour and are abstracted to the
# presence of each auxiliary key plus the order in which the keys are placed;
# their real semantics are validated out-of-band by axiom_check.py (G-AX) as
# A-reference, not consumed here.
# axioms-end


# pure-start
@Pure
def at_initial_position(index: Optional[int], initial_form_count: int) -> bool:
    """Whether a form occupies an initial position: it must HAVE a position
    (a positionless form does not qualify) and that position lies below the
    initial-form count. This is exactly the predicate the ordering decision
    already uses; the deletion decision must honour it identically."""
    return index is not None and index < initial_form_count


@Pure
def empty_key_sequence() -> PSeq[int]:
    """A form that has been granted no auxiliary control at all: the empty
    placement sequence."""
    return PSeq(1).take(0)


@Pure
def placed_keys(has_order_field: bool, has_delete_field: bool) -> PSeq[int]:
    """The auxiliary keys a form carries, in the order they are placed on it.
    The ordering key (token 1) is always placed AHEAD of the deletion key
    (token 2); a control the decisions leave absent contributes nothing, and
    nothing else is ever placed. So a form granted both carries exactly
    ``PSeq(1, 2)`` — never ``PSeq(2, 1)`` — and one granted a single control
    carries just that control's key."""
    return ((PSeq(1) if has_order_field else empty_key_sequence())
            + (PSeq(2) if has_delete_field else empty_key_sequence()))
# pure-end


def configure_optional_fields(
    form: Form,
    can_order: bool,
    can_delete: bool,
    can_delete_extra: bool,
    index: Optional[int],
    initial_form_count: int,
) -> None:
    # pre-conditions-start
    # The form is the only mutated object: full permission to its flags.
    Requires(Acc(form.has_order_field) and Acc(form.order_field_prefilled) and Acc(form.has_delete_field))
    Requires(Acc(form.aux_keys))
    # The hook runs on a freshly built form: neither auxiliary field is present
    # yet and nothing has been placed. The hook only ever ADDS a field; it never
    # removes one.
    Requires(form.has_order_field == False and form.order_field_prefilled == False and form.has_delete_field == False)
    Requires(form.aux_keys == empty_key_sequence())
    # The initial-form count is a non-negative form-count (read-only scalar).
    Requires(initial_form_count >= 0)
    # TERMINATION: the hook must actually ANSWER (return the augmented form) —
    # it is a bounded, loop-free prologue over scalars, so every call
    # completes. Nagini checks partial correctness by default, so without this
    # obligation a non-terminating implementation (e.g. bare self-recursion of
    # this very routine, which discharges every Ensures vacuously) would be
    # accepted despite never delivering an answer. The measure (2) strictly
    # exceeds the Form() constructor's (1), so bounded construction stays
    # admitted but a self-call is rejected (no strictly smaller measure is
    # available).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(form.has_order_field) and Acc(form.order_field_prefilled) and Acc(form.has_delete_field))
    Ensures(Acc(form.aux_keys))
    # (1) The ordering field is present iff ordering is enabled; its initial
    # value is pre-filled only for an initial-position form (and only then).
    Ensures(form.has_order_field == can_order)
    Ensures(form.order_field_prefilled
            == (can_order and at_initial_position(index, initial_form_count)))
    # (2) The deletion field is present iff deletion is enabled AND (extra-form
    # deletion is allowed OR the form occupies an initial position). The
    # initial-position predicate is FALSE for a positionless form, so a
    # positionless form with deletion enabled and extra-deletion disabled
    # receives NO deletion field.
    Ensures(
        form.has_delete_field
        == (can_delete and (can_delete_extra or at_initial_position(index, initial_form_count)))
    )
    # (3) PLACEMENT ORDER. The form carries exactly the auxiliary keys the two
    # decisions grant it, and it carries them in the one placement order the
    # form's rendering exposes: the ordering control ahead of the deletion
    # control. A form granted both therefore renders Order before Delete.
    Ensures(form.aux_keys == placed_keys(form.has_order_field, form.has_delete_field))
    # post-conditions-end
    # impl-start
    if can_order:
        if index is not None and index < initial_form_count:
            form.has_order_field = True
            form.order_field_prefilled = True
            form.aux_keys = form.aux_keys + PSeq(1)
        else:
            form.has_order_field = True
            form.aux_keys = form.aux_keys + PSeq(1)
    if can_delete and (can_delete_extra or index < initial_form_count):
        form.has_delete_field = True
        form.aux_keys = form.aux_keys + PSeq(2)
    # impl-end
