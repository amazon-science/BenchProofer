# refinement.md — django__django-13109

Maps every operation in `implementation_validateReference` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `validateReference` (`ForeignKey.validate`)

Post-patch repo code (`patch.diff` applied):
```python
def validate(self, value, model_instance):
    if self.remote_field.parent_link:
        return
    super().validate(value, model_instance)
    if value is None:
        return
    using = router.db_for_read(self.remote_field.model, instance=model_instance)
    qs = self.remote_field.model._base_manager.using(using).filter(
        **{self.remote_field.field_name: value}
    )
    qs = qs.complex_filter(self.get_limit_choices_to())
    if not qs.exists():
        raise exceptions.ValidationError(self.error_messages['invalid'], code='invalid', ...)
```

Lean impl (`implementation_validateReference`):
```lean
def implementation_validateReference
    (parentLink : Bool) (value : Option Nat) (rows : List Row) : Bool :=
  Id.run do
    if parentLink then
      return true
    match value with
    | none => return true
    | some v =>
      let mut qs := rows
      qs := qs.filter (fun r => r.key == v)
      qs := qs.filter (fun r => r.limitOk)
      return !qs.isEmpty
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `parentLink : Bool`; `if parentLink then return true` | `if self.remote_field.parent_link: return` | **R** | the parent-link early exit; `parent_link` truthiness ↔ `parentLink`. Returning with no error ↔ `return true`. |
| 2 | (none) | `super().validate(value, model_instance)` | **R (abstracted)** | the required/blank check is an unchanged callee orthogonal to the manager-selection fix. The modeled verdict is the FK-existence outcome conditioned on reaching the existence check; this op neither changes nor is consumed by the spec, so it is abstracted out (mapping.md). |
| 3 | `match value with \| none => return true` | `if value is None: return` | **R** | `Option Nat`: `none` ↔ `None`. Null reference ↔ `return true` (sound outright). |
| 4 | `let mut qs := rows` | `qs = self.remote_field.model._base_manager.using(using).filter(...)` — base collection = `_base_manager` (the UNFILTERED stored collection) | **I** (deep model of the changed op) | **the fixed operation.** `_base_manager` exposes every stored row regardless of the model's default presentation filter; the model is the full `rows` list (each row's `defaultVisible` flag is IGNORED). The pre-patch code (`_default_manager`) instead exposes only `rows.filter (·.defaultVisible)`; that one-token swap IS the fix, modeled as the choice of base collection. `router.db_for_read`/`.using(using)` select a read replica and do not change which rows exist; abstracted (mapping.md). |
| 5 | `qs := qs.filter (fun r => r.key == v)` | `.filter(**{self.remote_field.field_name: value})` | **I** | keep rows whose referenced-field value equals `value`. `key` ↔ that field's value (mapping.md). |
| 6 | `qs := qs.filter (fun r => r.limitOk)` | `qs = qs.complex_filter(self.get_limit_choices_to())` | **I** (deep model) | apply the standing choice constraint; `limitOk` ↔ whether the row satisfies `get_limit_choices_to()`. Unchanged across the patch; folded into the per-row observable. |
| 7 | `return !qs.isEmpty` | `if not qs.exists(): raise ValidationError(...)` (else no error) | **R** | `qs.exists()` ↔ `!qs.isEmpty`; raising ↔ `false`, no error ↔ `true`. The verdict `Bool` models pass/raise (mapping.md). |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `_base_manager` existence check.

## Soundness check (verify ⟹ correct)

- `problem_spec_validateReference parentLink value rows result := result =
  (if parentLink then true else match value with | none => true | some v =>
  existsValid v rows)`, where `existsValid v rows := rows.any (fun r => r.key == v
  && r.limitOk)`, pins the verdict EXACTLY (full Bool equality to an
  input-grounded expression) — directive 5 (frame): the output is fully
  determined by `parentLink`, `value`, and the per-row `key`/`limitOk`
  observables of the UNDERLYING collection. No output component is left
  unconstrained; no ungrounded oracle (directive 8) — the postcondition is
  dischargeable only by scanning the actual `rows`. Critically, the spec quant
  over the FULL `rows` (`existsValid v rows`), NOT over `rows.filter
  (·.defaultVisible)`, so any impl that drops hidden-but-stored rows fails it.
- The prepatch impl (`let mut qs := rows.filter (fun r => r.defaultVisible)`
  before the key/limit filters) is the real bug: it scans only the
  default-presentation view. It violates the spec on the discriminating clause
  `parentLink=false, value=some v, rows=[{key:=v, defaultVisible:=false,
  limitOk:=true}]` — a genuinely-stored, eligible, but default-hidden target —
  where it returns `false` (reference unsound) but the spec requires `true`. Its
  carried gold proof cannot close (G-DIFF/G-PANEL).
- This discriminating case is precisely what the FAIL_TO_PASS tests exercise:
  `test_FK_validates_using_base_manager` creates an `archived=True` author
  (hidden by the default manager's `archived=False` filter, present in the base
  table) and asserts `full_clean()` raises no error;
  `test_validate_foreign_key_to_model_with_overridden_manager` does the same via
  a form whose FK queryset is `_base_manager.all()`. PASS_TO_PASS keeps the
  ordinary failure path (`test_wrong_FK_value_raises_error`,
  `test_limited_FK_raises_error`): a value with no matching eligible row still
  yields `false`, which both impl and spec honor.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  `_base_manager` existence check over hand-picked edge cases (including
  `defaultVisible == False` rows) plus ≥1e5 fuzzed inputs.
