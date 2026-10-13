# mapping.md — django__django-11149

## Symbol binding (file:line @ base_commit e245046bb6e8b32360aa48b8a41fb7050f0fc730)

The fix lives in `InlineModelAdmin`'s four permission predicates in
`django/contrib/admin/options.py`. All four share an `if self.opts.auto_created:`
branch (the auto-created m2m "through"/link model case); the `else` defers to
`super().has_<action>_permission(...)`.

| Lean symbol | Python | location |
|---|---|---|
| `implementation_hasAnyPermsForTargetModel` / `problem_spec_hasAnyPermsForTargetModel` / `correct_hasAnyPermsForTargetModel` | `InlineModelAdmin._has_any_perms_for_target_model(self, request, perms)` (new helper introduced by the patch): resolve the target model over `self.opts.fields`, return `any(user.has_perm('%s.%s' % (opts.app_label, get_permission_codename(perm, opts))) for perm in perms)` | `options.py:2114-2128` (post-patch); pre-patch the equivalent target-resolution loop lived inline in `has_view_permission` at `options.py:2155-2169` |
| `implementation_hasAddPermission` / `problem_spec_hasAddPermission` / `correct_hasAddPermission` | `InlineModelAdmin.has_add_permission(self, request, obj)` | `options.py:2113-2120` (pre-patch); post-patch returns `self._has_any_perms_for_target_model(request, ['change'])` |
| `implementation_hasChangePermission` / `problem_spec_hasChangePermission` / `correct_hasChangePermission` | `InlineModelAdmin.has_change_permission(self, request, obj=None)` | `options.py:2122-2129` (pre-patch); post-patch `['change']` |
| `implementation_hasDeletePermission` / `problem_spec_hasDeletePermission` / `correct_hasDeletePermission` | `InlineModelAdmin.has_delete_permission(self, request, obj=None)` | `options.py:2131-2138` (pre-patch); post-patch `['change']` |
| `implementation_hasViewPermission` / `problem_spec_hasViewPermission` / `correct_hasViewPermission` | `InlineModelAdmin.has_view_permission(self, request, obj=None)` | `options.py:2140-2156` (pre-patch); post-patch `['view', 'change']` |

## What the gold patch changes

Pre-patch, the auto_created branch of `has_add`, `has_change`, and
`has_delete` each `return self.has_view_permission(request, obj)`. And
`has_view_permission` (auto_created) returns
`user.has_perm(view_<target>) or user.has_perm(change_<target>)`. So all four
actions accepted the *view* permission alone — a view-only user could mutate the
m2m rows (the bug).

Post-patch, the target-resolution + permission lookup is factored into the new
helper `_has_any_perms_for_target_model(request, perms)`. add/change/delete pass
`['change']` (so they now require the *change* permission); view passes
`['view', 'change']` (its result is UNCHANGED — `view or change`, a pure
refactor). The discriminating change is therefore on add/change/delete only.

## Modeled inputs (abstraction of the decision point)

| Lean | Python reality | meaning |
|---|---|---|
| `autoCreated : Bool` | `self.opts.auto_created` | is the model an auto-created m2m through model? |
| `selfAppLabel : String` | `self.opts.app_label` | the link model's own app label (fallback target) |
| `selfModelName : String` | `self.opts.model_name` | the link model's own model name (fallback target) |
| `parentModelId : String` | identity of `self.parent_model` | tag used by the resolution loop to skip the field pointing back at the parent |
| `fields : List LinkField` | `self.opts.fields` | each field's `(field.remote_field is not None, field.remote_field.model identity, field.remote_field.model._meta.app_label, .model_name)` |
| `userPerms : List String` | the set of permission strings for which `request.user.has_perm(s)` is true | the user's effective permission set; `has_perm(s)` ⇔ `s ∈ userPerms` |
| `superResult : Bool` | `super().has_<action>_permission(...)` | the non-auto_created decision (an opaque external input here; the patch does not touch it) |

## Output

| Lean | Python |
|---|---|
| `result : Bool` | the boolean returned by `has_<action>_permission` |

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `self.opts.auto_created` etc. (bools/strs) | `autoCreated`, `selfAppLabel`, `selfModelName`, `parentModelId` | identity |
| a `Field` with `remote_field` | `LinkField {hasRemote, remoteModelId, remoteAppLabel, remoteModelName}` | `hasRemote = (field.remote_field is not None)`; `remoteModelId` = identity tag of `field.remote_field.model`; app_label/model_name from `field.remote_field.model._meta` |
| `'%s.%s' % (opts.app_label, get_permission_codename(perm, opts))` = `'%s.%s_%s' % (app_label, perm, model_name)` | `permString app model action` = `app ++ "." ++ action ++ "_" ++ model` | identity of the codename format (`get_permission_codename` UNCHANGED, modeled deeply) |
| `request.user.has_perm(s)` | `userPerms.contains s` | the permission lookup ⇔ membership |
| `any(has_perm(...) for perm in perms)` | `actions.any (fun a => userPerms.contains (permString …))` | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** `get_permission_codename(action, opts)` is
  UNCHANGED (`django/contrib/auth/__init__.py:195`, body
  `'%s_%s' % (action, opts.model_name)`); modeled deeply as `permString`, an
  A-reference validated by G-CONF. `request.user.has_perm` is modeled as set
  membership against the `userPerms` input. Target resolution over `opts.fields`
  is modeled deeply (the field loop). `axiom_check.py` is a skip stub.
- **Flag dependency:** the whole decision is guarded by `autoCreated`
  (`self.opts.auto_created`); G-CONF fuzzes both values, and for the
  non-auto_created case checks the `superResult` passthrough.
- The four actions differ ONLY in the action list passed to the helper:
  add/change/delete use `["change"]`, view uses `["view","change"]`. G-CONF
  fuzzes all four actions.

## G-CONF fuzz seed

`SEED = 20240629` (pinned in `conformance_check.py`).
