# refinement.md — django__django-15467

Maps every operation in `implementation_emptyLabel` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `emptyLabel` (the placeholder-label resolution in `formfield_for_foreignkey`)

The patch (`django/contrib/admin/options.py`, the single-choice/radio branch of
`formfield_for_foreignkey`) changes one assignment:

```python
# pre-patch (base_commit):
kwargs["empty_label"] = _("None") if db_field.blank else None
# post-patch (gold):
kwargs["empty_label"] = (
    kwargs.get("empty_label", _("None")) if db_field.blank else None
)
```

This assignment only executes inside the radio branch:
```python
if "widget" not in kwargs:
    ...
    elif db_field.name in self.radio_fields:
        kwargs["widget"] = widgets.AdminRadioSelect(...)
        kwargs["empty_label"] = (kwargs.get("empty_label", _("None")) if db_field.blank else None)
```
When the radio branch does NOT run, `kwargs["empty_label"]` keeps whatever the
caller passed (or stays absent). The modeled value is the *resolved
`empty_label`* the function forwards into `db_field.formfield(**kwargs)`.

Lean impl (`implementation_emptyLabel`): given `radioBranch` (the radio branch is
the one taken), `blank` (`db_field.blank`), and `provided` (the caller's
`kwargs.get("empty_label")`), it computes the resolved label.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `radioBranch : Bool` | the `"widget" not in kwargs` ∧ `db_field.name in self.radio_fields` guard selecting the radio branch | **R** | the conjunction of the guard conditions that reach the changed assignment is pre-resolved to a single Bool (mapping.md bijection). Identity on the taken/not-taken value. |
| 2 | `blank : Bool` | `db_field.blank` | **R** | the field's optionality flag ↔ a Bool. |
| 3 | `provided : Option String` | `kwargs.get("empty_label")` — the caller-supplied placeholder, possibly absent | **R** | a Python optional string ↔ `Option String` (mapping.md); absence ↔ `none`. |
| 4 | `let mut emptyLabel := provided` | initial state: `kwargs["empty_label"]` is whatever the caller passed (or absent) before the radio branch | **I** | identity initialization — the resolved label starts as the caller's value. |
| 5 | `if radioBranch then emptyLabel := if blank then some (provided.getD noneLabel) else none` | `kwargs["empty_label"] = (kwargs.get("empty_label", _("None")) if db_field.blank else None)` (executed only in the radio branch) | **I** (the changed op, deeply modeled) | **the fixed operation.** Post-patch, in the radio branch over an optional relation, the label is `kwargs.get("empty_label", _("None"))` = the caller's value when present, else the default `_("None")`; this is exactly `some (provided.getD noneLabel)`. For a required relation it is `None` ↔ `none`. Modeled directly (no axiom). The prepatch impl uses `some noneLabel` (discarding `provided`), matching pre-patch. |
| 6 | `return emptyLabel` | the resolved `kwargs["empty_label"]` forwarded into `db_field.formfield(**kwargs)` | **R** | the function returns/forwards the resolved label; we model that resolved value. |

`noneLabel : String := "None"` (`pure` region) models `_("None")`, Django's
translatable default placeholder — an input-independent constant string. It is
modeled directly (not axiomatized): in the test/default locale `_("None")` is the
literal `"None"`, and the fix's behavior (caller value vs. default) does not
depend on the default's concrete text. The R/I leg is mechanically refuted by
G-CONF.

## Soundness check (verify ⟹ correct)

- `problem_spec_emptyLabel` pins the SINGLE output in EVERY case (directive 5 —
  frame: no output left unconstrained; directive 8 — grounded in the inputs, no
  ungrounded oracle):
  - `radioBranch = false` → `result = provided` (caller's value carried through);
  - `radioBranch = true, blank = true` → `result = some (provided.getD noneLabel)`
    (caller's value when present, else default);
  - `radioBranch = true, blank = false` → `result = none`.
- The discriminating clause is the `radioBranch = true, blank = true,
  provided = some s` case: the spec demands `some s` (the caller's own label),
  while the prepatch impl yields `some noneLabel` (the default), discarding the
  caller value. So the carried gold proof's `rfl` for the `true.true` case fails
  to typecheck (G-DIFF / G-PANEL). When `provided = none` both agree on
  `some noneLabel`, and when `blank = false` both agree on `none`.
- This is exactly what
  `test_radio_fields_foreignkey_formfield_overrides_empty_label` exercises: a
  `ModelAdmin` whose `formfield_overrides` supply `empty_label = "Custom empty
  label"` for a radio ForeignKey over an optional (`blank=True`) relation must
  see that custom label survive, not be overwritten by the default.
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  resolution over the exhaustive `radioBranch × blank` cross-product with a wide
  range of `provided` values (present strings, including the default text, and
  absent), plus ≥1e5 fuzzed inputs (0 disagreements).
