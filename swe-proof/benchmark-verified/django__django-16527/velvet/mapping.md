# mapping.md — django__django-16527

Binds `Solution.lean` symbols to the repo at
`base_commit = bd366ca2aeffa869b7dbc0b0aa01caea75e6dc31`.

Repo file under change:
`django/contrib/admin/templatetags/admin_modify.py` (function `submit_row`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `showSaveAsNew (isPopup hasAddPermission hasChangePermission change saveAs : Bool)` | the `"show_save_as_new"` entry built inside `submit_row` — `django/contrib/admin/templatetags/admin_modify.py:100-103` | the modeled boolean flag |
| `isPopup` | local `is_popup = context["is_popup"]` | request is a popup |
| `hasAddPermission` | local `has_add_permission = context["has_add_permission"]` | viewer may ADD objects |
| `hasChangePermission` | local `has_change_permission = context["has_change_permission"]` | viewer may CHANGE (edit) objects |
| `change` | local `change = context["change"]` | page is the edit view of an existing object |
| `saveAs` | local `save_as = context["save_as"]` | this admin opts into duplicate-as-new |
| `result` | the dict value stored at key `"show_save_as_new"` | the flag exposed to the template |

No callee is axiomatized: the flag is a pure boolean conjunction of the four
inputs, modeled deeply.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `is_popup` : Python truthy/falsey bool | `Bool` | `True ↔ true`, `False ↔ false` |
| `has_add_permission` : bool | `Bool` | as above |
| `has_change_permission` : bool | `Bool` | as above |
| `change` : bool | `Bool` | as above |
| `save_as` : bool | `Bool` | as above |
| `"show_save_as_new"` : bool | `Bool` (result) | exact |
| `not x` | `!x` | logical negation |
| `x and y` | `x && y` | short-circuit conjunction (no side effects here; equivalent to `&&`) |

`hasChangePermission` is observed BUT NOT used in the postcondition: it exists
so the prepatch (which gated on the edit permission) is expressible against the
identical spec and FAILS whenever `hasAddPermission ≠ hasChangePermission`.

## 3. Callee provenance

None (no axioms). The whole behavior is a boolean conjunction, modeled deeply
as `!isPopup && hasAddPermission && change && saveAs`.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **16527**. The R/I shadow is the modeled
boolean formula `(not is_popup) and has_add_permission and change and save_as`;
the oracle is the patched source line, transliterated verbatim (see
`conformance_check.py` docstring for why the real `submit_row` context is not
built in-container). Both are exercised over all 2^5 = 32 input combinations
plus seeded fuzz.
