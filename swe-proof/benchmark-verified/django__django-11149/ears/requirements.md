# Requirements: Admin inline permissions for auto-created ManyToMany through models

## Introduction

Django's admin renders related objects as *inlines*. When an inline is built for
the implicit ("auto-created") through model of a `ManyToManyField`, that through
model has no permissions of its own, so the four authorization decisions on the
inline — add, change, delete, and view — must be derived from the permissions
the acting user holds on the *target* model that the many-to-many relationship
points to.

This behavior lives in `InlineModelAdmin` in
`django/contrib/admin/options.py`, specifically the `self.opts.auto_created`
branches of `has_add_permission`, `has_change_permission`,
`has_delete_permission`, and `has_view_permission`. Those methods build a
permission string of the form `'<app_label>.<codename>'` (codenames produced by
`django.contrib.auth.get_permission_codename`) for the located target model and
test it with `request.user.has_perm(...)`.

The defect: a user granted only the *view* permission on the target model was
nevertheless allowed to add, change, and delete rows in the many-to-many inline,
because those three decisions reused the view decision. The goal is to make the
add/change/delete decisions require an editing (change) permission on the target
model, so a view-only user gets a genuinely read-only inline, while leaving the
view decision (and all non-auto-created inline behavior) intact.

Throughout this document, "target model" means the model that the auto-created
through model points to (the far side of the many-to-many relation, not the
parent model of the inline), and "the target's view/change permission" means the
permission whose codename is produced by `get_permission_codename('view'|'change',
target_opts)` under the target model's app label.

## Requirement 1: Editing an auto-created M2M inline requires the target's change permission

**User story:** As a site administrator, I want add, change, and delete on a
many-to-many inline to require change access on the related model, so that a
user with only view access cannot alter the relationship.

**Acceptance criteria**

1. WHEN `has_add_permission` is invoked on an `InlineModelAdmin` whose model is
   an auto-created many-to-many through model, THEN the method SHALL return
   `True` if and only if the requesting user holds the target model's change
   permission.
2. WHEN `has_change_permission` is invoked on such an inline, THEN the method
   SHALL return `True` if and only if the requesting user holds the target
   model's change permission.
3. WHEN `has_delete_permission` is invoked on such an inline, THEN the method
   SHALL return `True` if and only if the requesting user holds the target
   model's change permission.
4. IF the requesting user holds the target model's view permission but does not
   hold its change permission, THEN each of `has_add_permission`,
   `has_change_permission`, and `has_delete_permission` on such an inline SHALL
   return `False`.
5. The system SHALL determine the change permission from the target model of the
   auto-created relationship — the related model reached through the through
   model's fields, not the inline's parent model — using the target model's app
   label and change codename.

## Requirement 2: Viewing an auto-created M2M inline requires view or change on the target

**User story:** As a site administrator, I want a user with view access to the
related model to be able to see (but not edit) the many-to-many inline, so that
read-only visibility is preserved.

**Acceptance criteria**

1. WHEN `has_view_permission` is invoked on an `InlineModelAdmin` whose model is
   an auto-created many-to-many through model, THEN the method SHALL return
   `True` if the requesting user holds the target model's view permission.
2. WHEN `has_view_permission` is invoked on such an inline, THEN the method SHALL
   return `True` if the requesting user holds the target model's change
   permission (change implies view).
3. IF the requesting user holds neither the target model's view permission nor
   its change permission, THEN `has_view_permission` on such an inline SHALL
   return `False`.
4. The system SHALL preserve the existing outcome of the view decision for every
   combination of held target permissions: the view decision SHALL remain
   permissive exactly when view-or-change is held, unchanged by this fix.

## Requirement 3: Non-auto-created inlines and foreign-key inline permissions are unchanged

**User story:** As a maintainer, I want ordinary (non-through) inlines to keep
their existing permission behavior, so that this fix does not regress other
inline types.

**Acceptance criteria**

1. IF the inline's model is not an auto-created through model, THEN each of
   `has_add_permission`, `has_change_permission`, `has_delete_permission`, and
   `has_view_permission` SHALL defer to the standard `ModelAdmin` permission
   logic (the superclass implementation) exactly as before.
2. The system SHALL keep the add/change/delete/view decisions for foreign-key
   (non-auto-created) inlines dependent solely on the user's permissions for the
   inline's own model, unaffected by this change.
3. WHEN a user has the add permission but not the change permission on a
   foreign-key inline's model, THEN the add decision SHALL be `True` and the
   change decision SHALL follow the standard per-model permission rules, exactly
   as prior to this change.

## Requirement 4: Consistency of the derived decisions

**User story:** As a maintainer, I want the four decisions to be derived
uniformly from held target permissions, so the behavior is predictable.

**Acceptance criteria**

1. WHILE evaluating any of the four permission decisions for an auto-created
   through-model inline, the system SHALL base the result only on whether the
   requesting user holds one or more of a decision-specific set of permissions on
   the target model: {change} for add, change, and delete; {view, change} for
   view.
2. The system SHALL treat holding any one of the required permissions for a
   decision as sufficient for that decision to return `True`.
3. WHEN the requesting user holds the target model's change permission, THEN all
   four decisions (add, change, delete, view) on such an inline SHALL return
   `True`.
