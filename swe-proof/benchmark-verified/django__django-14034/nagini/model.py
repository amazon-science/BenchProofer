"""Twin-artifact model for django__django-14034.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the attributes for rendering a bound input are assembled, a single
  guard decides whether the mandatory-input marker applies at all:

    g = widget_marks_mandatory AND field_is_mandatory AND form_marks_mandatory

  where ``widget_marks_mandatory`` is what the field-level widget reports for
  the current initial value, ``field_is_mandatory`` is the field's own
  mandatory flag, and ``form_marks_mandatory`` is the form-level switch.

  If ``g`` is false, the mandatory marker is left entirely unset (neither on
  the aggregate attribute set nor on any constituent input).

  If ``g`` is true, there are two regimes:

    (A) When the field aggregates several constituent inputs whose membership
        is individually optional (the field exposes a per-constituent
        mandatory policy that is switched OFF, and its widget is the
        composite kind), the aggregate marker is NOT applied as a whole.
        Instead each constituent input independently receives the marker iff
        that constituent's own widget reports the marker for the current
        initial value AND that constituent is itself mandatory. A constituent
        that is optional therefore renders without the marker even though the
        aggregate field is mandatory.

    (B) Otherwise the aggregate marker is applied to the whole attribute set
        (and constituent inputs are not individually adjusted).

  The disabled marker is applied to the aggregate attribute set exactly when
  the field is disabled, independently of the above.

The aggregate attribute set is modelled by two tri-state slots
(``required_attr`` / ``disabled_attr``: -1 unset, 0 absent, 1 present). Each
constituent input is a small object carrying its read-only widget marker and
mandatory flag plus a mutable per-constituent marker slot. Booleans carry the
guards directly; no string/HTML modelling is needed because the observable is
exactly which inputs carry the marker.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Constituent:
    """One constituent input paired with its constituent field.

    ``widget_mark`` is what this constituent's widget reports for the current
    initial value (read-only). ``field_required`` is the constituent field's
    own mandatory flag (read-only). ``marker`` is the per-constituent
    mandatory-marker slot that the operation may set (-1 unset, 0 absent,
    1 present)."""

    def __init__(self, widget_mark: bool, field_required: bool) -> None:
        Ensures(Acc(self.widget_mark) and self.widget_mark == widget_mark)  # type: ignore
        Ensures(Acc(self.field_required) and self.field_required == field_required)  # type: ignore
        Ensures(Acc(self.marker) and self.marker == -1)  # type: ignore
        self.widget_mark = widget_mark
        self.field_required = field_required
        self.marker = -1  # type: int


class Result2:
    """The aggregate attribute set produced by the operation: two tri-state
    slots for the mandatory and disabled markers (-1 unset, 0 absent,
    1 present)."""

    def __init__(self) -> None:
        Ensures(Acc(self.required_attr) and self.required_attr == -1)  # type: ignore
        Ensures(Acc(self.disabled_attr) and self.disabled_attr == -1)  # type: ignore
        self.required_attr = -1  # type: int
        self.disabled_attr = -1  # type: int


# axioms-start
# (no unchanged opaque callee is consumed: every operation is a boolean guard
# or a per-constituent assignment modelled directly.)
# axioms-end


# pure-start
@Pure
def constituent_marker(widget_mark: bool, field_required: bool) -> int:
    """The mandatory marker a single constituent input receives when the
    aggregate guard holds and the per-constituent regime is in effect: present
    iff the constituent's widget reports the marker AND the constituent is
    itself mandatory; absent otherwise."""
    if widget_mark and field_required:
        return 1
    return 0
# pure-end


def build_required_attrs(
        out: Result2,
        widget_mark: bool,
        field_required: bool,
        form_marks: bool,
        is_partial_multi: bool,
        field_disabled: bool,
        subs: List[Constituent]) -> None:
    # pre-conditions-start
    Requires(Acc(out.required_attr) and Acc(out.disabled_attr))
    Requires(out.required_attr == -1 and out.disabled_attr == -1)
    # The constituent list spine and the read-only constituent fields
    # (widget_mark, field_required) are held at HALF permission — the operation
    # only READS them; full permission is held on the per-constituent marker
    # slot, the one thing the operation writes (directive 5).
    Requires(Acc(list_pred(subs), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
        Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
        and Acc(subs[k].marker)),
        [[subs[k]]])))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
        subs[k].marker == -1), [[subs[k]]])))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(out.required_attr) and Acc(out.disabled_attr))
    Ensures(Acc(list_pred(subs), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
        Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
        and Acc(subs[k].marker)),
        [[subs[k]]])))
    # disabled marker: present iff the field is disabled, else left unset.
    Ensures(Implies(field_disabled, out.disabled_attr == 1))
    Ensures(Implies(not field_disabled, out.disabled_attr == -1))
    # Regime A: guard holds and per-constituent policy in effect -> aggregate
    # marker NOT applied; each constituent gets its own marker.
    Ensures(Implies((widget_mark and field_required and form_marks) and is_partial_multi,
        out.required_attr == -1))
    Ensures(Implies((widget_mark and field_required and form_marks) and is_partial_multi,
        Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
            subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
            [[subs[k]]]))))
    # Regime B: guard holds, not per-constituent -> aggregate marker applied,
    # constituents untouched.
    Ensures(Implies((widget_mark and field_required and form_marks) and not is_partial_multi,
        out.required_attr == 1))
    Ensures(Implies((widget_mark and field_required and form_marks) and not is_partial_multi,
        Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
            subs[k].marker == -1), [[subs[k]]]))))
    # Guard fails -> no mandatory marker anywhere.
    Ensures(Implies(not (widget_mark and field_required and form_marks),
        out.required_attr == -1))
    Ensures(Implies(not (widget_mark and field_required and form_marks),
        Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
            subs[k].marker == -1), [[subs[k]]]))))
    # post-conditions-end
    # impl-start
    if widget_mark and field_required and form_marks:
        if is_partial_multi:
            i = 0
            while i < len(subs):
                # invariants-start
                Invariant(Acc(list_pred(subs), 1 / 2))
                Invariant(0 <= i and i <= len(subs))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(subs),
                    Acc(subs[k].widget_mark, 1 / 2) and Acc(subs[k].field_required, 1 / 2)
                    and Acc(subs[k].marker)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                    subs[k].marker == constituent_marker(subs[k].widget_mark, subs[k].field_required)),
                    [[subs[k]]])))
                Invariant(Forall(int, lambda k: (Implies(i <= k and k < len(subs),
                    subs[k].marker == -1), [[subs[k]]])))
                Invariant(MustTerminate(len(subs) - i + 1))
                # invariants-end
                sub = subs[i]
                if sub.widget_mark and sub.field_required:
                    sub.marker = 1
                else:
                    sub.marker = 0
                i = i + 1
        else:
            out.required_attr = 1
    if field_disabled:
        out.disabled_attr = 1
    # impl-end
