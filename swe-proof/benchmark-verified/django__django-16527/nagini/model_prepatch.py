"""Twin-artifact model for django__django-16527.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the row of save/delete controls for an editable object is assembled, one
  of the controls offers to persist the current object as a brand-new object
  (a "save as new" action). Because that action creates a NEW stored object, it
  must be offered ONLY to a viewer who is permitted to add objects of this kind
  — possessing permission merely to alter the existing object is insufficient.

  Concretely, the "save as new" control is offered exactly when ALL of the
  following hold:

    * the page is not being shown in a stripped-down popup presentation,
    * the viewer holds the permission to ADD objects of this kind,
    * the page is editing an already-existing object (not creating one), and
    * the surrounding configuration enables the save-as-new affordance.

  In every other case the control is withheld. In particular, a viewer who may
  only change the existing object — but may not add — is NOT offered the
  control.

All of the inputs are independent booleans drawn from the rendering context
(the permission flags, the popup flag, the object-exists flag, and the
configuration flag). The control's visibility is itself a boolean. No callee is
axiomatized: the visibility is pure boolean logic over the context, modelled
deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms: the control's visibility is pure boolean logic over the
# rendering context. Every input is a context boolean read directly; nothing is
# an unchanged opaque callee whose contract the proof would need.
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def save_as_new_visible(
    is_popup: bool,
    may_add: bool,
    may_change: bool,
    editing_existing: bool,
    save_as_enabled: bool,
) -> bool:
    # pre-conditions-start
    # All inputs are plain booleans; nothing is mutated.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The control is offered exactly when the page is not a popup, the viewer
    # may ADD, the page edits an existing object, and the affordance is enabled.
    # The permission to merely change is NOT part of the gating condition.
    Ensures(
        Result()
        == (not is_popup and may_add and editing_existing and save_as_enabled)
    )
    # post-conditions-end
    # impl-start
    show_save_as_new = (
        not is_popup and may_change and editing_existing and save_as_enabled
    )
    return show_save_as_new
    # impl-end
