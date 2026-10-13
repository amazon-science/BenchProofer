# refinement.md — django__django-12774

Maps every operation in `implementation_inBulk` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op). Every step is R, A, or I.

## Modeled function: `inBulk` (the field-name guard of `QuerySet.in_bulk`)

Post-patch repo code (`patch.diff`), the guard that the fix rewrites:
```python
opts = self.model._meta
unique_fields = [
    constraint.fields[0]
    for constraint in opts.total_unique_constraints
    if len(constraint.fields) == 1
]
if (
    field_name != 'pk' and
    not opts.get_field(field_name).unique and
    field_name not in unique_fields
):
    raise ValueError("in_bulk()'s field_name must be a unique field but %r isn't." % field_name)
```
where `total_unique_constraints` (`options.py:831-841`) is
`[c for c in self.constraints if isinstance(c, UniqueConstraint) and c.condition is None]`.

Lean impl (`implementation_inBulk`): a decision returning `Except String Unit`
with the same guard structure.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `fieldName : String` | the `field_name` argument | **I** | identical string value (ASCII field labels). |
| 2 | `fld : FieldInfo` (field `unique : Bool`) | `opts.get_field(field_name)`, read only via `.unique` | **R** | `get_field` is an UNCHANGED callee, not the fixed op; its sole observable here is `.unique`, supplied as the model input `fld.unique`. On the `field_name == "pk"` branch the real code short-circuits before calling `get_field`, matched by the guard's first conjunct. |
| 3 | `cs : List UniqueConstraint` (`fields : List String`, `isPartial : Bool`) | `opts.constraints` projected to its `UniqueConstraint` members | **R** | `isinstance(constraint, UniqueConstraint)` (the filter inside `total_unique_constraints`) is the R projection defining the input list; `constraint.fields` ↔ `c.fields`, `constraint.condition is not None` ↔ `c.isPartial`. |
| 4 | `singleFieldUniqueConstraintFields cs = (cs.filter (fun c => !c.isPartial && c.fields.length == 1)).map (fun c => c.fields.headD "")` | `unique_fields = [c.fields[0] for c in opts.total_unique_constraints if len(c.fields) == 1]`, with `total_unique_constraints` = the `condition is None` filter | **I** (changed op, deeply modeled) | the `condition is None` filter ↔ `!c.isPartial`; `len(c.fields) == 1` ↔ `c.fields.length == 1`; `c.fields[0]` ↔ `c.fields.headD ""` (safe head — only reached when length == 1, so the `""` default is never observed). |
| 5 | `if fieldName != "pk" && !fld.unique && !(uniqueFields.contains fieldName) then return Except.error fieldName` | `if field_name != 'pk' and not get_field(field_name).unique and field_name not in unique_fields: raise ValueError(... % field_name)` | **I** (the fixed operation) | **the fix.** The patch ADDS the third conjunct `field_name not in unique_fields`; the Lean guard's `!(uniqueFields.contains fieldName)` is exactly that added clause. The pre-patch guard is only the first two conjuncts (the prepatch impl). `raise ValueError(... % field_name)` ↔ `Except.error fieldName` (the offending name stands in for the formatted message that embeds it). |
| 6 | `return Except.ok ()` | the guard is not taken; `in_bulk` proceeds to build the result dict (unchanged, downstream) | **R** | "guard passed, method proceeds" modeled as `Except.ok ()`; the unchanged dict-construction tail is not modeled (it is not part of the raise/proceed decision the fix alters). |
| 7 | `Id.run do … return …` (`Except String Unit`) | the method either raises or returns a dict | **R** | outcome modeled as `Except String Unit`: `.error` for the raise, `.ok ()` for proceed. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch guard decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_inBulk` pins the result for BOTH exhaustive, mutually-exclusive
  cases via the predicate `fieldNameAcceptable`, which is stated STRUCTURALLY over
  the inputs (`fieldName = "pk" ∨ fld.unique ∨ ∃ c ∈ cs, ¬c.isPartial ∧ c.fields =
  [fieldName]`) and does NOT reuse the impl's executable helper — so a verifying
  impl cannot "echo" the impl's own decision (directive 4 spec-strength; directive
  8 — every output grounded in the inputs, no ungrounded oracle; directive 5 — no
  output left unconstrained). The impl computes the equivalent decision through
  `singleFieldUniqueConstraintFields` + a membership test; the proof bridges the
  two with the `contains_iff` lemma (`(singleFieldUniqueConstraintFields cs).contains
  fieldName ↔ ∃ c ∈ cs, ¬c.isPartial ∧ c.fields = [fieldName]`).
- The discriminating route is the third disjunct: when `fieldName ≠ "pk"`, the
  field is not itself unique, but `fieldName` IS the sole field of an
  unconditional unique constraint, then `fieldNameAcceptable` holds and the spec
  demands `Except.ok ()`. The prepatch impl ignores `cs` entirely, so it returns
  `Except.error fieldName` on that case — disagreeing with the spec. Hence the
  carried gold proof fails to typecheck against the prepatch impl
  (G-DIFF/G-PANEL).
- This is exactly what `test_in_bulk_meta_constraint` exercises: a `Season` model
  with `UniqueConstraint(fields=['year'])` and no `unique=True` on `year`;
  post-patch `in_bulk(field_name='year')` proceeds, pre-patch it raised.
  `test_in_bulk_non_unique_meta_constaint` confirms the rejection still fires for
  a partial single-field constraint (`condition=Q(...)`) and a multi-field
  constraint (both modeled: `isPartial = true` and `fields.length ≠ 1`).
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch guard
  decision, over a representative exhaustive edge set (field name incl. "pk" ×
  field.unique × 0..1 constraint, each unconditional/partial spanning 1 or 2
  fields) plus ≥1e5 fuzzed points with 0..3 constraints (0 disagreements).
