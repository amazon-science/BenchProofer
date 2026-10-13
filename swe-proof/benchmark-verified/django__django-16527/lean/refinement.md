# refinement.md — operation correspondence (django__django-16527)

Maps every op in `implementation_buttonFlags` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The patched Python (`submit_row`, `admin_modify.py:61-112`) reads a fixed set of
boolean context values and computes seven derived button-visibility flags via
fixed boolean formulas. The fix changes one gate: the `show_save_as_new` flag is
gated on `has_add_permission` instead of `has_change_permission`. Every op is a
concrete boolean computation reproduced exactly (R for the str-key→struct-field
input reads, I for the boolean algebra). No callee semantics are abstracted.

| # | Lean impl op | patch.diff / source counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `ButtonInput` fields read from `i` | the 13 `context["…"]` / `context.get("…", True)` reads (lines 65-75, 98, 100) | R | Python `dict[str]→bool` reads ↔ `ButtonInput` field projections; bijection in mapping.md. `.get(k, True)` default modeled as the present boolean (F2P context supplies the keys). |
| 2 | `canSaveV := (hasChangePermission && change) \|\| (hasAddPermission && add) \|\| hasEditableInlineAdminFormsets` | `can_save = (has_change_permission and change) or (has_add_permission and add) or has_editable_inline_admin_formsets` (76-80) | I | identical boolean formula |
| 3 | `canSaveAndAddAnother := hasAddPermission && !isPopup && (!saveAs \|\| add) && canSaveV && showSaveAndAddAnother` | `can_save_and_add_another = …` (81-87) | I | identical boolean formula (unchanged by fix) |
| 4 | `canSaveAndContinue := !isPopup && canSaveV && hasViewPermission && showSaveAndContinue` | `can_save_and_continue = …` (88-90) | I | identical boolean formula |
| 5 | `canChange := hasChangePermission \|\| hasEditableInlineAdminFormsets` | `can_change = has_change_permission or has_editable_inline_admin_formsets` (91) | I | identical |
| 6 | `showDeleteLink := !isPopup && hasDeletePermission && change && showDelete` | `"show_delete_link": …` (96-100) | I | identical |
| 7 | `showSaveAsNew := !isPopup && hasAddPermission && change && saveAs` | `"show_save_as_new": not is_popup and has_add_permission and change and save_as` (102-105, **patched line 103**) | I | the **changed op**: the gate is `has_add_permission` (post-patch). Reproduced concretely; NOT axiomatized. |
| 8 | `showSaveAndAddAnother := canSaveAndAddAnother` | `"show_save_and_add_another": can_save_and_add_another` (106) | I | passthrough |
| 9 | `showSaveAndContinue := canSaveAndContinue` | `"show_save_and_continue": can_save_and_continue` (107) | I | passthrough |
| 10 | `showSave := showSave && canSaveV` | `"show_save": show_save and can_save` (108) | I | identical |
| 11 | `showClose := !(showSave && canSaveV)` | `"show_close": not (show_save and can_save)` (109) | I | identical |
| 12 | `return { … }` (ButtonFlags) | `ctx.update({…}); return ctx` (93-112) | R | the seven derived keys ↔ `ButtonFlags` fields; the copied-context passthrough entries are container plumbing out of model scope (mapping.md) |

No A-consumed rows: the proof discharges the boolean formulas directly; no
UNCHANGED callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: every callee (`dict.get`, `Context.update`) is container
plumbing reproduced concretely or out of scope, not abstracted behind a model.
No changed-inexpressible op.

The discriminating clause is row 7: post-patch `showSaveAsNew` is gated on
`hasAddPermission`. The prepatch impl gates it on `hasChangePermission`, so on any
input with `!isPopup && change && saveAs && hasChangePermission &&
!hasAddPermission` the prepatch produces `showSaveAsNew = true` while the frozen
`problem_spec_buttonFlags` demands `false`. Hence the prepatch
`correct_buttonFlags` cannot close — the G-DIFF signal. This is exactly the F2P
test's `change_user` scenario.
