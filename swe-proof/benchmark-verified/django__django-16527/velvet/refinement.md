# refinement.md — django__django-16527

Correspondence between `Solution.lean`'s `showSaveAsNew` impl and `patch.diff`
(the gold patch swaps `has_change_permission` → `has_add_permission` in the
`"show_save_as_new"` conjunction). `patch.diff` is the gold verbatim (applies at
base_commit, resolves — G-RESOLVE).

## A. The corrected flag — `submit_row`'s `"show_save_as_new"`

Gold hunk:
```
             "show_save_as_new": not is_popup
-            and has_change_permission
+            and has_add_permission
             and change
             and save_as,
```

| # | Solution.lean impl op (`showSaveAsNew`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `isPopup hasAddPermission hasChangePermission change saveAs : Bool` | locals `is_popup`, `has_add_permission`, `has_change_permission`, `change`, `save_as` (all bool) | R | Python bool ↔ Lean `Bool` (mapping.md §2). `hasChangePermission` carried but unused in the post-image, so the prepatch is expressible. |
| A2 | `!isPopup` | `not is_popup` | I | identical: logical negation. |
| A3 | `&& hasAddPermission` | `and has_add_permission` | I | identical: the fix uses the ADD permission. |
| A4 | `&& change` | `and change` | I | identical conjunct. |
| A5 | `&& saveAs` | `and save_as` | I | identical conjunct. |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. The op is a pure
boolean conjunction over the inputs, modeled deeply and tagged **R/I**.

## B. verify(Solution) ⇒ resolved

`showSaveAsNew` verifies only if
`result = (!isPopup && hasAddPermission && change && saveAs)` (A2–A5). By R (the
bool bijection) the verified result equals the patched
`not is_popup and has_add_permission and change and save_as` on the real
context. The F2P test
(`test_submit_row_save_as_new_add_permission_required`) asserts the flag is
`False` for a viewer who holds only the CHANGE permission and `True` once the
viewer also holds the ADD permission — exactly what the spec pins (the result is
gated on `hasAddPermission`, independent of `hasChangePermission`).

The prepatch impl computes `!isPopup && hasChangePermission && change && saveAs`
against the byte-identical spec, leaving the unsolved goal
`(… && hasChangePermission && …) = (… && hasAddPermission && …)`, which fails
whenever `hasAddPermission ≠ hasChangePermission` (G-DIFF) — the discriminating
clause is precisely the add-vs-change permission swap.

G-CONF differential-tests the R/I shadow (the modeled formula) against the
patched source line over all 32 input combinations plus fuzz. No trust points
beyond the type bijection (mapping.md §2): there are no axioms.
