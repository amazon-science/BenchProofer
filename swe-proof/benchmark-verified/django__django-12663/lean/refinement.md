# refinement.md — django__django-12663

Maps every operation in `implementation_outputType` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `outputType` (`Query.output_field`)

Post-patch repo code (`patch.diff`, `query.py:233-238`):
```python
@property
def output_field(self):
    if len(self.select) == 1:
        select = self.select[0]
        return getattr(select, 'target', None) or select.field   # changed lines
    elif len(self.annotation_select) == 1:
        return next(iter(self.annotation_select.values())).output_field
    # implicit `return None`
```

Lean impl (`implementation_outputType`):
```lean
def implementation_outputType
    (selections : List Selection) (annotations : List AnnExpr) : Option FieldId :=
  Id.run do
    if selections.length = 1 then
      let select := selections.headI
      return some (baseOrDeclared select)
    else if annotations.length = 1 then
      return some annotations.headI.outputField
    return none
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `selections : List Selection` (input carrier) | `self.select` — the tuple of selected expressions | **R** | each element ↔ one selected expression, restricted to its two observable candidate type descriptors `base` (`Col.target`, optional) and `declared` (`Expression.field`); list order = tuple order. See mapping.md. |
| 2 | `annotations : List AnnExpr` (input carrier) | `self.annotation_select` — ordered mapping of annotation expressions | **R** | each element ↔ one annotation's `.output_field`; insertion order preserved. |
| 3 | `if selections.length = 1 then …` | `if len(self.select) == 1:` | **I** | identical length guard on the selected-columns carrier. |
| 4 | `let select := selections.headI; return some (baseOrDeclared select)` | `select = self.select[0]; return getattr(select, 'target', None) or select.field` | **I** (deep model of the changed op) | **the fixed operation.** `baseOrDeclared select = select.base.getD select.declared` reproduces `getattr(select, 'target', None) or select.field`: the underlying referenced attribute (`target`) is returned when present, else the declared output type (`field`). Real model-field objects are always truthy, so Python's `or` reduces exactly to `Option.getD` (truthiness note in mapping.md; G-CONF exercises the genuine `or`). This is the heart of the fix — pre-patch returned `select.field` directly. |
| 5 | `else if annotations.length = 1 then return some annotations.headI.outputField` | `elif len(self.annotation_select) == 1: return next(iter(self.annotation_select.values())).output_field` | **R** | the single-annotation branch, unchanged by the patch. `annotations.headI` ↔ `next(iter(...values()))` (the first/only value); `.outputField` ↔ `.output_field`, carried directly as observable data. |
| 6 | `return none` | implicit `return None` when neither branch fires | **R** | `none` ↔ Python `None`; the property falls off the end returning `None`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `output_field` property.

## Callee provenance (no consumed axiom)

- `getattr(select, 'target', None)` and Python `or` — language built-ins. Modeled
  deeply by `Option.getD` (a present, truthy attribute ⇒ used; absent/falsy ⇒
  fall back). Not callees; nothing axiomatized.
- `next(iter(self.annotation_select.values()))` — picks the single annotation
  value; modeled as `annotations.headI`. Unchanged by the patch.
- The single annotation's `.output_field` is itself a property in the repo, but it
  is UNCHANGED by the patch and its value is carried directly as
  `AnnExpr.outputField`; the F2P fix turns solely on the single-column branch, so
  the annotation branch consumes no callee property.

## Soundness check (verify ⟹ correct)

- `problem_spec_outputType` pins the result EXACTLY to a total case split on the
  inputs (full equality to an input-grounded expression) — directive 5 (frame):
  the result is determined by `selections.length`, `annotations.length`, and the
  observable descriptors of the chosen element. No output component is left
  unconstrained, and in the single-column branch the result is pinned to
  `baseOrDeclared` (preferring `base`), never to `declared` alone. No ungrounded
  oracle (directive 8) — the postcondition is dischargeable only by actually
  selecting the right branch and computing `base.getD declared`.
- The prepatch impl reproduces the PRE-FIX choice: in the single-column branch it
  returns `select.declared` (i.e. `select.field`) directly, modeling the buggy
  `return self.select[0].field`. It violates the spec on the discriminating clause
  `selections.length = 1 ∧ base = some t ∧ t ≠ declared`: the spec requires
  `some (baseOrDeclared select) = some t`, but the prepatch yields
  `some declared ≠ some t`. Its carried gold proof cannot close (G-DIFF/G-PANEL):
  `rfl` fails because `pure (some selections.headI.declared)` is not
  definitionally `some (baseOrDeclared selections.headI)`.
- This discriminating case is precisely the FAIL_TO_PASS scenario added by the
  test patch (`test_subquery_filter_by_lazy`): a nested subquery annotation's
  single output column has an underlying referenced attribute (a related-field
  target) that differs from its declared output type. Pre-fix the declared type
  was reported, so the downstream lookup attempted a raw numeric coercion of a
  lazily-evaluated related object and raised `TypeError`; post-fix the underlying
  referenced attribute is reported, enabling the related-field value coercion and
  the query resolves.
- G-CONF confirms the R/I shadow == an in-process replica of the patched
  `output_field` over hand-picked edge cases (single selection with `target`
  present-and-different, present-and-equal, absent, present-but-None; the
  annotation branch; the empty branch; multi-element lists) plus ≥1e5 fuzzed
  inputs.
