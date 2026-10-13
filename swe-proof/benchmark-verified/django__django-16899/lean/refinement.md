# refinement.md — operation correspondence (django__django-16899)

Maps every op in `implementation_checkReadonlyFieldsItem` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The patched Python (`_check_readonly_fields_item`) keeps its branch structure:
four short-circuit acceptances (callable / attr-of-obj / attr-of-model /
declared field), then a single `checks.Error(id="admin.E035")`. The patch
changes ONLY the error-message format string, adding the offending
`field_name`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if isCallable then return []` | `if callable(field_name): return []` | R | `callable(field_name)` outcome ↔ `Bool` (mapping.md). UNCHANGED check; only its result is consumed. |
| 2 | `if hasAttrObj then return []` | `elif hasattr(obj, field_name): return []` | R | `hasattr(obj, field_name)` outcome ↔ `Bool`. UNCHANGED. |
| 3 | `if hasAttrModel then return []` | `elif hasattr(obj.model, field_name): return []` | R | `hasattr(obj.model, field_name)` outcome ↔ `Bool`. UNCHANGED. |
| 4 | `if fieldExists then return []` | `try: obj.model._meta.get_field(field_name) … except FieldDoesNotExist: <error> else: return []` | R | "`get_field` succeeds (no `FieldDoesNotExist`)" outcome ↔ `Bool`. UNCHANGED. The `try/else` empty-return is the `fieldExists = true` acceptance; the `except` path is the error branch. |
| 5 | `return [errorMessage label fieldName obj.className obj.modelLabel]` | `return [checks.Error("The value of '%s' refers to '%s', which is not a callable, an attribute of '%s', or an attribute of '%s'." % (label, field_name, obj.__class__.__name__, obj.model._meta.label), obj=obj.__class__, id="admin.E035")]` | I | the CHANGED op, modeled deeply as the concrete formatted string. `errorMessage` spells out the post-patch `%`-format verbatim (now interpolating `field_name`). `checks.Error(obj=…, id="admin.E035")` is unchanged framing (mapping.md); the modeled payload is the message text. |

No A-consumed rows: the proof discharges the spec by case-splitting the four
booleans; no UNCHANGED callee property is assumed (axioms region empty;
`axiom_check.py` is a skip stub). No A-reference rows: the changed op delegates
to no real callee — it is the format string itself, modeled concretely. No
changed-inexpressible op.

The discriminating clause is row 5: the message text. The prepatch impl uses
`errorMessageBug` (the old text, omitting the `'%s' refers to '%s'` value
citation), so its `correct_checkReadonlyFieldsItem` cannot close against the
frozen `problem_spec_checkReadonlyFieldsItem` (which pins the post-patch
`errorMessage`). That is the G-DIFF signal.
