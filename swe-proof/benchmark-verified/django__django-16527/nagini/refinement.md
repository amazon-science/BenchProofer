# refinement.md — django__django-16527

The operation-by-operation correspondence between `model.py`'s implementation
(the `save_as_new_visible` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed** / **A-reference**), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The save-as-new visibility expression — `submit_row` (`django/contrib/admin/templatetags/admin_modify.py:102-105`)

Gold hunk:
```
             "show_save_as_new": not is_popup
-            and has_change_permission
+            and has_add_permission
             and change
             and save_as,
```

| # | model.py impl op (`save_as_new_visible`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `is_popup, may_add, may_change, editing_existing, save_as_enabled : bool` | the locals `is_popup`, `has_add_permission`, `has_change_permission`, `change`, `save_as` read from `context[...]` (`admin_modify.py:66-73`) | R | each `context[k]` read is the identity on a Python `bool` (mapping.md §2). The model binds them positionally; `may_change` is carried only to keep the spec byte-identical with the prepatch. |
| A2 | `not is_popup` | `not is_popup` | I | identical boolean negation. |
| A3 | `... and may_add ...` | `... and has_add_permission ...` | R+I | same conjunction; `may_add` ↔ `has_add_permission` (R, mapping.md §1). This is the operand the gold patch changed (was `has_change_permission`); the model fixes it to the ADD-permission operand identically. |
| A4 | `... and editing_existing ...` | `... and change ...` | R+I | same conjunction; `editing_existing` ↔ `change` (R). |
| A5 | `... and save_as_enabled` | `... and save_as` | R+I | same conjunction; `save_as_enabled` ↔ `save_as` (R). |
| A6 | `return show_save_as_new` | the value bound to the `"show_save_as_new"` dict key in `ctx.update({...})` | R | the model returns the same boolean the patch stores under `"show_save_as_new"`; the template/F2P test observes exactly that value (`template_context["show_save_as_new"]`). |

The discriminating content of the change — gating on **add** permission rather
than **change** permission — lives in step A3 (`may_add` vs the pre-patch
`may_change`). `model_prepatch.py` reproduces the bug (the impl reads
`may_change`) and **fails** the postcondition
`Result() == (not is_popup and may_add and editing_existing and save_as_enabled)`
on any input where `may_add != may_change` (e.g. the F2P "change_user" who has
change-but-not-add permission: `may_add=False, may_change=True`). This is
exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The one operation that genuinely *changed* — which
permission flag gates the control — is a primitive boolean operand swap, modeled
**directly** as `may_add` in a `bool` conjunction. There is **no consumed axiom**
(no opaque callee is approximated) and **no A-reference deep model standing in
for a callee**: the whole expression is primitive `and`/`not` over booleans.

`axiom_check.py` therefore checks the only nontrivial soundness obligation that
remains — that the modeled boolean formula equals Python's native evaluation of
the gold expression over the entire 2^5 boolean cube (the R-refinement of
mapping.md §2 is exact). It consumes no repo code; the gold expression is pure
boolean logic over the five context flags.

## C. verify(model) ⇒ resolved

`save_as_new_visible` verifies only if its result equals
`not is_popup and may_add and editing_existing and save_as_enabled` (A2-A5).
By R (each `context[k]` is the identity on its `bool`, and the model operands
are the gold operands renamed) the verified expression equals the gold
`not is_popup and has_add_permission and change and save_as` for every context
the F2P test constructs. The F2P test observes `template_context["show_save_as_new"]`
for two viewers:

* a change-but-not-add viewer (`has_add_permission=False`,
  `has_change_permission=True`, `change=True`, `save_as=True`,
  `is_popup=False`) — gold and the verified model both yield `False`; the
  prepatch (and the pre-patch repo) yield `True` and would fail the test;
* an add-and-change viewer (`has_add_permission=True`, …) — gold and the
  verified model yield `True`.

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to the boolean R-refinement — and the gold patch resolves (G-RESOLVE).
The only trust point is refinement fidelity (this document, G-EQ); there are no
axioms (so G-AX reduces to the exhaustive boolean equality of `axiom_check.py`).
