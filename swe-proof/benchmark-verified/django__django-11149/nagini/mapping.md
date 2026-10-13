# mapping.md — django__django-11149

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e245046bb6e8b32360aa48b8a41fb7050f0fc730`, states the type
abstraction, and gives the provenance of the unchanged callees the model
refines (no `@ContractOnly` axiom is consumed — see §3).

Repo file under change: `django/contrib/admin/options.py`
(class `InlineModelAdmin`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `inline_create_decision(held, inspect_code, modify_code)` | `InlineModelAdmin.has_add_permission` — `django/contrib/admin/options.py:2114` (auto_created branch) | modeled changed function: create decision for an auto-created link table |
| `inline_modify_decision(held, inspect_code, modify_code)` | `InlineModelAdmin.has_change_permission` — `django/contrib/admin/options.py:2123` (auto_created branch) | modeled changed function: modify decision |
| `inline_remove_decision(held, inspect_code, modify_code)` | `InlineModelAdmin.has_delete_permission` — `django/contrib/admin/options.py:2132` (auto_created branch) | modeled changed function: remove decision |
| `inline_inspect_decision(held, inspect_code, modify_code)` | `InlineModelAdmin.has_view_permission` — `django/contrib/admin/options.py:2141` (auto_created branch) | modeled function: inspect decision (behaviour unchanged by the patch; present so the spec pins the relationship the other three are derived against) |
| `target_decision(held, required)` | `InlineModelAdmin._has_any_perms_for_target_model` — new method introduced by the patch (`options.py:2114` post-patch) | the shared helper: "does the actor hold ANY of the required codes for the target record"; under spec (not an axiom), called by the four decisions |
| `holds_any(held, required)` | `any(request.user.has_perm(...) for perm in perms)` inside `_has_any_perms_for_target_model` | pure spec: the existential over the required-code list of per-code membership |

The four `has_*_permission` methods, in the `self.opts.auto_created` branch,
each return a boolean derived from the permissions the actor holds on the
*target* model of the auto-created many-to-many through table. The patch
factors the common "any of these perms on the target" computation into
`_has_any_perms_for_target_model(request, perms)` and changes which `perms`
each decision requests:

- post-patch: add → `['change']`, change → `['change']`, delete → `['change']`,
  view → `['view', 'change']`.
- pre-patch (the bug): add/change/delete each returned `has_view_permission(...)`,
  i.e. used the view rule `['view','change']`; only view itself was already
  correct.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the set of permission strings the actor holds for the target model, queried via `request.user.has_perm('<app_label>.<codename>')` | `held: PSet[int]` of held permission *codes* | each distinct permission string ↔ a distinct `int` code; `request.user.has_perm(p)` is TRUE ↔ `code(p) in held`. The actor's permission grant is read-only here, so `held` carries fractional permission `Acc(set_pred(held), 1/2)` (required AND ensured). |
| `get_permission_codename('view', opts)` → `'view_<model>'`; full string `'<app_label>.view_<model>'` | `inspect_code: int` | the target's inspect permission string ↔ a fixed int code |
| `get_permission_codename('change', opts)` → `'change_<model>'`; full string `'<app_label>.change_<model>'` | `modify_code: int` | the target's modify permission string ↔ a fixed int code, with `inspect_code != modify_code` (the two codename strings differ — `'view_…'` vs `'change_…'`) |
| the `perms` list argument (`['change']` / `['view','change']`) → the codename strings built from it | `required: PSeq[int]` | the requested action list refined to the corresponding code list: `['change']` ↔ `PSeq(modify_code)`; `['view','change']` ↔ `PSeq(inspect_code, modify_code)` |
| `any(self.request.user.has_perm(...) for perm in perms)` | `holds_any(held, required)` = `Exists j: 0<=j<len(required) and required[j] in held` | `any` over the requested list ↔ the existential of membership over `required` |
| each `has_*_permission(...)` return value (bool) | the `bool` result of the corresponding model function | identity |
| each decision call returns in finite time (a bounded scan over a finite requested list) | `Requires(MustTerminate(...))` on every modeled function, discharged in `target_decision`'s loop by the decreasing measure `len(required) - i` | total-correctness obligation: a modeled decision must actually be delivered, not merely be correct if it returns |

The `self.opts.auto_created` guard, the `request` object, the iteration over
`opts.fields` that *locates* the target model, and the `super().has_*` else
branch are not part of the modeled behaviour: the F2P tests exercise exactly the
`auto_created` branch on the target model, and the change is solely in which
required codes each decision queries. The locating loop is unchanged between
pre- and post-patch (the patch moves it verbatim into the new helper), so it is
not a modeled operation; the modeled state is the resulting target permission
codes (`inspect_code`, `modify_code`) and the actor's held codes (`held`).

## 3. Callee provenance (no consumed axiom)

There is **no `@ContractOnly` axiom** in this bundle: every operation the changed
code performs is expressible in Nagini's fragment and is modeled deeply.

- `request.user.has_perm('<app_label>.<codename>')` — an unchanged callee
  (`django/contrib/auth/models.py:412`, `_user_has_perm`). It returns TRUE iff
  the actor holds that permission string. Refined (kind R) to set membership
  `code in held`; not axiomatized.
- `get_permission_codename(action, opts)` — an unchanged callee
  (`django/contrib/auth/__init__.py:195`): `return '%s_%s' % (action, opts.model_name)`.
  It maps each distinct action to a distinct codename string for a fixed target
  model. Refined (kind R) to the fixed distinct int codes `inspect_code` /
  `modify_code`; not axiomatized.
- `any(...)` — the Python builtin, refined (kind R / deep model) to the
  existential `holds_any`; not axiomatized.

Because nothing is axiomatized, `axiom_check.py` carries no axiom Ensures to
fuzz; it instead validates the two refinement facts the bundle relies on as a
sanity oracle (G-AX has nothing to reject): (a) `get_permission_codename` yields
distinct strings for `'view'` vs `'change'` (so `inspect_code != modify_code` is
faithful), and (b) `any` over a code list equals the existential of membership
(the deep model of the helper). See `axiom_check.py`.
