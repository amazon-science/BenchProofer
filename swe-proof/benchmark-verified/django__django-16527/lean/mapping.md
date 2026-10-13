# mapping.md — symbol binding & type bijection (django__django-16527)

## Modeled function
- **Lean** `implementation_buttonFlags : ButtonInput → ButtonFlags`
- **Python** `submit_row(context)` —
  `django/contrib/admin/templatetags/admin_modify.py:61-112 @ base_commit`
  (`bd366ca2aeffa869b7dbc0b0aa01caea75e6dc31`).

`submit_row` is an admin template tag that, given a context of booleans, computes
the set of button-visibility flags shown on a change form. It reads a fixed set
of boolean inputs from `context`, computes three intermediate predicates
(`can_save`, `can_save_and_add_another`, `can_save_and_continue`,
`can_change`), and returns a context updated with seven derived boolean flags.
The function is a pure boolean computation: every output is a fixed boolean
formula over the inputs.

The observable behavior demanded by the F2P test
(`test_submit_row_save_as_new_add_permission_required`) is the value of the
`show_save_as_new` flag. A user with the change permission but NOT the add
permission (on a change view, with `save_as` enabled) must get
`show_save_as_new = False`; a user holding the add permission gets `True`.

## Type bijection (used by G-CONF + G-AX)
All inputs and outputs are Python booleans ↔ Lean `Bool`. `context.get(k, True)`
reads (`show_save`, `show_save_and_add_another`, `show_save_and_continue`,
`show_delete`) are modeled as the boolean actually present in the context (the
`True` default is a dict-access detail orthogonal to the boolean logic; the F2P
context supplies these keys).

| Python (context key / local) | Lean field (`ButtonInput`) | notes |
|---|---|---|
| `context["add"]` | `add` | on an add form |
| `context["change"]` | `change` | on a change form |
| `context["is_popup"]` | `isPopup` | popup mode |
| `context["save_as"]` | `saveAs` | "save as new" enabled for this admin |
| `context.get("show_save", True)` | `showSave` | |
| `context.get("show_save_and_add_another", True)` | `showSaveAndAddAnother` | |
| `context.get("show_save_and_continue", True)` | `showSaveAndContinue` | |
| `context["has_add_permission"]` | `hasAddPermission` | |
| `context["has_change_permission"]` | `hasChangePermission` | |
| `context["has_view_permission"]` | `hasViewPermission` | |
| `context["has_editable_inline_admin_formsets"]` | `hasEditableInlineAdminFormsets` | |
| `context["has_delete_permission"]` | `hasDeletePermission` | |
| `context.get("show_delete", True)` | `showDelete` | |

| Python output dict key | Lean field (`ButtonFlags`) | formula |
|---|---|---|
| `can_change` | `canChange` | `has_change_permission or has_editable_inline_admin_formsets` |
| `show_delete_link` | `showDeleteLink` | `not is_popup and has_delete_permission and change and show_delete` |
| `show_save_as_new` | `showSaveAsNew` | **post-patch**: `not is_popup and has_add_permission and change and save_as` |
| `show_save_and_add_another` | `showSaveAndAddAnother` | `can_save_and_add_another` |
| `show_save_and_continue` | `showSaveAndContinue` | `can_save_and_continue` |
| `show_save` | `showSave` | `show_save and can_save` |
| `show_close` | `showClose` | `not (show_save and can_save)` |

Intermediate predicates (modeled as a `pure` helper `canSave` plus inline `let`s
in the impl):
- `can_save = (has_change_permission and change) or (has_add_permission and add) or has_editable_inline_admin_formsets`
- `can_save_and_add_another = has_add_permission and not is_popup and (not save_as or add) and can_save and show_save_and_add_another`
- `can_save_and_continue = not is_popup and can_save and has_view_permission and show_save_and_continue`

## Callee provenance
`submit_row` calls only `dict.get` (default reads) and `Context(...).update(...)`
(container plumbing). No UNCHANGED domain callee carries semantics the proof must
assume: the entire computation is concrete boolean algebra reproduced as I/R ops.
Therefore the `axioms` region is empty and there is no `opaque` callee. G-AX is a
skip stub.

## Scope note
`submit_row` returns a `Context` object (the input context copied, then
`.update`d with the seven derived keys). The unchanged passed-through context
entries are container plumbing irrelevant to the fix and are not modeled; the
modeled output `ButtonFlags` carries exactly the seven flags the function sets,
each pinned to its input formula (frame discipline). The single behavioral change
is the `show_save_as_new` gate (`has_change_permission` → `has_add_permission`).

## Flag dependency
None beyond the booleans themselves. G-CONF fuzzes all 13 boolean inputs.

## G-CONF fuzz seed
Pinned seed: **16527**. ≥10^5 fuzzed inputs over all boolean input tuples
(exhaustive enumeration of the 2^13 combinations is included, then random fill).
