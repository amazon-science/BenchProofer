# Requirements: "Save as new" admin button requires add permission

## Introduction

The Django admin change form renders a row of action buttons via the
`submit_row` context function in
`django/contrib/admin/templatetags/admin_modify.py`. This function reads a set
of boolean inputs from the template context (permission flags, form-mode flags,
and per-button display toggles) and derives the visibility flags used by the
`submit_line.html` template.

One of these derived flags, `show_save_as_new`, controls the "Save as new"
button. Choosing "Save as new" creates a brand-new object from the current
form, so it is an *add* operation. Historically the flag was gated on the
change permission only, which let a user without add permission trigger an add
operation. The goal is to make `show_save_as_new` correctly depend on the
**add** permission, while leaving every other derived button flag unchanged.

The affected function is `submit_row(context)`. The behavioral contract is a
pure boolean computation over the input flags; the introduction below names the
input flags as they appear in the context: `add`, `change`, `is_popup`,
`save_as`, `show_save`, `show_save_and_add_another`, `show_save_and_continue`,
`has_add_permission`, `has_change_permission`, `has_view_permission`,
`has_editable_inline_admin_formsets`, `has_delete_permission`, and
`show_delete`.

## Requirement 1: "Save as new" visibility gated on add permission

**User story:** As a site administrator, I want the "Save as new" button to
appear only for users who may add objects, so that a user without add
permission cannot use it to create a new object.

**Acceptance criteria**

1. WHEN `submit_row` derives the button flags, THEN the system SHALL set
   `show_save_as_new` to true if and only if all of the following hold together:
   the request is not a popup (`is_popup` is false), the user has the add
   permission (`has_add_permission` is true), the form is in change mode
   (`change` is true), and save-as is enabled (`save_as` is true).
2. IF the user lacks the add permission (`has_add_permission` is false), THEN
   the system SHALL set `show_save_as_new` to false, regardless of whether the
   user has the change permission.
3. WHEN the user has the add permission and the form is in change mode with
   save-as enabled and the request is not a popup, THEN the system SHALL set
   `show_save_as_new` to true even if the change permission is separately
   toggled, i.e. `show_save_as_new` SHALL NOT depend on `has_change_permission`.
4. IF the request is a popup (`is_popup` is true), THEN the system SHALL set
   `show_save_as_new` to false.
5. IF the form is not in change mode (`change` is false) OR save-as is disabled
   (`save_as` is false), THEN the system SHALL set `show_save_as_new` to false.

## Requirement 2: Other derived button flags remain unchanged

**User story:** As a maintainer, I want the remaining button-visibility flags
to keep their existing behavior, so that only "Save as new" is affected by this
change.

**Acceptance criteria**

1. The system SHALL compute a "can save" condition that is true when either the
   user has change permission and the form is in change mode, or the user has
   add permission and the form is in add mode, or there are editable inline
   admin formsets (`has_editable_inline_admin_formsets` is true).
2. WHEN `submit_row` derives the button flags, THEN the system SHALL set
   `show_save` to true if and only if `show_save` (input) is true and the
   "can save" condition holds.
3. WHEN `submit_row` derives the button flags, THEN the system SHALL set
   `show_close` to the logical negation of the `show_save` output flag defined
   in criterion 2.
4. WHEN `submit_row` derives the button flags, THEN the system SHALL set
   `show_save_and_add_another` to true if and only if the user has add
   permission, the request is not a popup, either save-as is disabled or the
   form is in add mode, the "can save" condition holds, and the input
   `show_save_and_add_another` is true.
5. WHEN `submit_row` derives the button flags, THEN the system SHALL set
   `show_save_and_continue` to true if and only if the request is not a popup,
   the "can save" condition holds, the user has view permission, and the input
   `show_save_and_continue` is true.
6. WHEN `submit_row` derives the button flags, THEN the system SHALL set
   `can_change` to true if and only if the user has change permission or there
   are editable inline admin formsets.
7. WHEN `submit_row` derives the button flags, THEN the system SHALL set
   `show_delete_link` to true if and only if the request is not a popup, the
   user has delete permission, the form is in change mode, and `show_delete`
   (defaulting to true when absent) is true.
8. The system SHALL preserve the whole incoming context when returning the
   derived flags, updating it with the computed flags rather than replacing it,
   so that all keys present in the input context remain available to the
   template.

## Requirement 3: Default handling of optional display toggles

**User story:** As a template author, I want optional display toggles to default
sensibly, so that omitting them does not hide always-available buttons.

**Acceptance criteria**

1. IF `show_save` is absent from the context, THEN the system SHALL treat it as
   true.
2. IF `show_save_and_add_another` is absent from the context, THEN the system
   SHALL treat it as true.
3. IF `show_save_and_continue` is absent from the context, THEN the system SHALL
   treat it as true.
4. IF `show_delete` is absent from the context, THEN the system SHALL treat it
   as true.
