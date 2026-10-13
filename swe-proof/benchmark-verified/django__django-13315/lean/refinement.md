# refinement.md — django__django-13315

Maps every operation in `implementation_applyChoiceLimit` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `applyChoiceLimit` (`apply_limit_choices_to_to_formfield`)

Post-patch repo code (`patch.diff`):
```python
def apply_limit_choices_to_to_formfield(formfield):
    from django.db.models import Exists, OuterRef, Q
    if hasattr(formfield, 'queryset') and hasattr(formfield, 'get_limit_choices_to'):
        limit_choices_to = formfield.get_limit_choices_to()
        if limit_choices_to:
            complex_filter = limit_choices_to
            if not isinstance(complex_filter, Q):
                complex_filter = Q(**limit_choices_to)
            complex_filter &= Q(pk=OuterRef('pk'))
            # Use Exists() to avoid potential duplicates.
            formfield.queryset = formfield.queryset.filter(
                Exists(formfield.queryset.model._base_manager.filter(complex_filter)),
            )
```

Lean impl (`implementation_applyChoiceLimit`):
```lean
def implementation_applyChoiceLimit
    (applicable constraintActive : Bool) (base : List Candidate) : List Candidate :=
  Id.run do
    let mut queryset := base
    if applicable then
      if constraintActive then
        queryset := queryset.filter qualifies
    return queryset
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `base : List Candidate`, each with `matchRows : Nat` | `formfield.queryset`, with each candidate's constraint-join multiplicity | **R** | each list element ↔ one candidate object; `matchRows` ↔ how many related rows the constraint matches for it (mapping.md bijection). Modeling the queryset as the multiset of candidates with their per-candidate match count is exact for the choice-set behavior. |
| 2 | `applicable : Bool` gate | `hasattr(formfield, 'queryset') and hasattr(formfield, 'get_limit_choices_to')` | **R** | the attribute-pair guard; truthiness ↔ `applicable`. When false, the queryset is untouched (`return queryset` with `queryset = base`). |
| 3 | `if applicable then …` | `if hasattr(...) and hasattr(...):` | **I** | structural guard. |
| 4 | `constraintActive : Bool` gate | `limit_choices_to = formfield.get_limit_choices_to(); if limit_choices_to:` | **R** | the constraint-present guard; truthiness ↔ `constraintActive`. When false, queryset untouched. |
| 5 | `if constraintActive then …` | `if limit_choices_to:` | **I** | structural guard. The fetch + truthiness of `limit_choices_to` is captured by the `constraintActive` input. |
| 6 | `queryset := queryset.filter qualifies` (with `qualifies c := c.matchRows != 0`) | `complex_filter = Q(...) & Q(pk=OuterRef('pk')); formfield.queryset = formfield.queryset.filter(Exists(model._base_manager.filter(complex_filter)))` | **I** (deep model of the changed op) | **the fixed operation.** `filter(Exists(subquery))` keeps each candidate iff at least one related row satisfies the constraint — exactly once, independent of the join multiplicity. `List.filter qualifies` keeps each candidate iff `matchRows != 0`, i.e. iff ≥1 related row matches, once. The constraint-construction lines (`Q(**dict)` normalization, `& Q(pk=OuterRef('pk'))`) build the SAME matching predicate; they affect WHICH candidates match (folded into `matchRows`/`qualifies`), not the at-most-once membership, so they are abstracted by the `Candidate` model. |
| 7 | `return queryset` | mutation of `formfield.queryset` (or leaving it unchanged) | **I** | the function returns by assigning `formfield.queryset`; we model it as returning the new row-list. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the patched `filter(Exists(...))` membership behavior.

## Soundness check (verify ⟹ correct)

- `problem_spec_applyChoiceLimit applicable constraintActive base result :=
  result = (if applicable && constraintActive then base.filter qualifies else
  base)` pins the result EXACTLY (full list equality to an input-grounded
  expression) — directive 5 (frame): the output is fully determined by the two
  gate booleans and the per-candidate match counts. No output component is left
  unconstrained; no ungrounded oracle (directive 8) — the postcondition is
  dischargeable only by computing the actual filter over the input candidates.
- The prepatch impl (`flatMap (fun c => List.replicate c.matchRows c)` when the
  constraint applies) reproduces the join's per-related-row multiplicity: it
  lists a candidate `matchRows` times. It violates the spec on the discriminating
  clause `applicable=true, constraintActive=true, base=[c]` with `c.matchRows ≥
  2` — a candidate matching the constraint through several related rows — where
  it returns `[c, c, …]` (length `matchRows`) but the spec requires `[c]`. Its
  carried gold proof cannot close (G-DIFF/G-PANEL); the failing case is the
  `true.true` branch with a duplicate-producing candidate.
- This discriminating case is precisely what the FAIL_TO_PASS test
  (`test_limit_choices_to_no_duplicates`) exercises: a `limit_choices_to` Q
  object spanning a multi-valued relation (`jokes__funny`, `jokes_today__funny`)
  where a `Character` is related to several matching jokes, so the pre-patch join
  renders it multiple times; the test asserts the form field's queryset contains
  each character exactly once.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  `filter(Exists(...))` membership over hand-picked edge cases (including
  `matchRows ≥ 2`) plus ≥1e5 fuzzed candidate lists.
