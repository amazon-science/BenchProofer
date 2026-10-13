# refinement.md — django__django-16032

Maps every op in `implementation_prepInLookup` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom · **A-reference**
deep model validated == real callee (G-AX) · **I** identical concrete op.

The modeled function is the single-column-narrowing decision in
`RelatedIn.get_prep_lookup` (`related_lookups.py`), whose pivot is the value of
`self.rhs.has_select_fields`. The gold patch changes `has_select_fields` from a
derived property to an explicit flag (`query.py`); the observable consequence is
exactly the branch condition modeled here.

The function returns the UPDATED subquery state (the real `get_prep_lookup`
mutates `self.rhs` in place), so every state component is pinned.

| # | `implementation_prepInLookup` op | `patch.diff` counterpart | tag |
|---|----------------------------------|--------------------------|-----|
| 1 | `!rhs.explicitValuesApplied` | `not getattr(self.rhs, "has_select_fields", True)` where post-patch `has_select_fields` is the explicit flag set only by `set_values` (`query.py`: class attr `has_select_fields = False`; `set_values` sets it `True`; derived property deleted) | R |
| 2 | `&& !lhsTargetPrimaryKey` | `and not getattr(self.lhs.field.target_field, "primary_key", False)` | R / I |
| 3 | `return restrictTo rhs [targetField]` (selectCols=[t], masks cleared, flag set) | `self.rhs.set_values([target_field])` — narrows to the single target column, which clears the select fields and the annotation/extra masks (via `clear_select_fields` + `set_annotation_mask`/`set_extra_mask` inside `set_values`) and sets `has_select_fields = True` | R |
| 4 | `return rhs` (else) | branch not entered: the subquery is left entirely unchanged (no `set_values` call) | I |
| 5 | `targetField` (the resolved single column name) | `target_field = self.lhs.field.name` / `self.lhs.field.target_field.name` (the unchanged name-resolution preceding the call) | R / I |

Notes:
- Op 3 (`restrictTo`) models the post-patch `set_values([t])`: the observable
  state change is `selectCols = [targetField]`, the annotation/extra masks
  cleared, and the explicit-selection flag set. The pre-patch two-step
  `clear_select_clause(); add_fields([t], True)` produced the same single-column
  selection but did NOT make the (then-derived) `has_select_fields` true; both
  collapse to the same modeled narrowing because the modeled decision is keyed on
  the explicit flag (op 1), which is precisely what the gold patch introduces.
- No A-consumed or A-reference rows: nothing is axiomatized. `axioms = []`,
  `deep_model_references = []`; `axiom_check.py` is a skip stub.
- All R/I content ⇒ `conf_skip = false`; `conformance_check.py` differential-tests
  the R/I shadow against the real post-patch decision over ≥10⁵ fuzzed inputs.

## Prepatch (the bug)

`Solution_prepatch.lean` replaces op 1's `!rhs.explicitValuesApplied` with the
pre-patch derived rule `!(!selectCols.isEmpty || hasAnnotationSelection ||
hasExtraSelection)` = `not bool(select or annotation_select_mask or
extra_select_mask)`. On an annotated/aliased subquery
(`hasAnnotationSelection = true`, `explicitValuesApplied = false`) the prepatch
sees it as "already selected" and does NOT narrow → returns `rhs` unchanged,
while the spec (the narrowing branch fires, since `explicitValuesApplied = false`
and `lhsTargetPrimaryKey = false`) forces `selectCols = [targetField]`. That is
exactly the F2P bug (`sub-select returns N columns - expected 1`).

Concrete discriminator (verified by `rfl`): for
`rhs = { selectCols := ["id","ann"], hasAnnotationSelection := true,
hasExtraSelection := false, explicitValuesApplied := false }`,
`lhsTargetPrimaryKey = false`, `targetField = "id"`:
post-patch result `.selectCols = ["id"]` (satisfies the spec); prepatch result
`.selectCols = ["id","ann"]` (violates the spec's `= ["id"]`). The carried `sorry`
proof cannot close against the prepatch impl ⇒ G-DIFF.
