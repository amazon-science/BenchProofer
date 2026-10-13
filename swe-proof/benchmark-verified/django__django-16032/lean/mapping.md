# mapping.md — django__django-16032

`spec_provenance: cold` (derived from problem_statement + gold patch + repo at
`base_commit=0c3981eb5094419fe200eb46c71b5376a2266166`; no prior solution consulted).

## Modeled function

`implementation_prepInLookup` ↔ the column-restriction decision inside
`RelatedIn.get_prep_lookup` for the subquery-RHS (non-direct-value) branch:
`django/db/models/fields/related_lookups.py:75-110` @ base_commit (class
`RelatedIn`, method `get_prep_lookup`, the `elif not getattr(self.rhs,
"has_select_fields", True) and not getattr(self.lhs.field.target_field,
"primary_key", False):` arm, lines 93-110).

The genuinely-changed primitive consumed by that decision is the truth value of
`self.rhs.has_select_fields`, whose definition is what the gold patch rewrites:

- `django/db/models/sql/query.py` — class `Query`:
  - base_commit: `has_select_fields` is a derived `@property` (lines 264-268)
    returning `bool(self.select or self.annotation_select_mask or
    self.extra_select_mask)`.
  - patched: the property is deleted; `has_select_fields = False` becomes a plain
    class attribute (line 198 region), and `set_values` (line 2379 region) sets
    `self.has_select_fields = True`.

So post-patch `has_select_fields` is an explicit flag, true **iff** an explicit
column selection (`values()`/`values_list()` → `set_values`) has been applied;
pre-patch it is true whenever the query happens to carry any selected column,
annotation-select mask, or extra-select mask — which an `annotate()`/`alias()`
queryset does, even though the user never selected columns.

## Lean ↔ Python type bijection (G-CONF / leakage)

| Lean (`SubqueryState` / args)        | Python                                                                 |
|--------------------------------------|------------------------------------------------------------------------|
| `rhs.selectCols : List String`       | `list(self.rhs.values_select)` (the RHS query's current select columns)|
| `rhs.hasAnnotationSelection : Bool`  | `bool(self.rhs.annotation_select_mask)`                                |
| `rhs.hasExtraSelection : Bool`       | `bool(self.rhs.extra_select_mask)`                                     |
| `rhs.explicitValuesApplied : Bool`   | the post-patch `self.rhs.has_select_fields` flag (True iff `set_values`/`values()` ran) |
| `lhsTargetPrimaryKey : Bool`         | `getattr(self.lhs.field.target_field, "primary_key", False)`           |
| `targetField : String`               | the already-resolved single target column name (`self.lhs.field.name` or `…target_field.name`) |
| `result : SubqueryState`             | the RHS query's state (the four components above) after `get_prep_lookup` runs |

`has_select_fields` (post-patch) = `explicitValuesApplied`. The pre-patch rule
`bool(select or annotation_select_mask or extra_select_mask)` =
`!selectCols.isEmpty || hasAnnotationSelection || hasExtraSelection` — this lives
ONLY in the prepatch impl region (the bug).

## Callee provenance

No callee is consumed as an axiom. The restriction `set_values([target_field])`
(post) vs `clear_select_clause(); add_fields([target_field], True)` (pre) both
produce the single-column select `[target_field]`; modeled as the literal
`[targetField]` (R — identical observable result columns when the branch is
entered). `axioms = []`, `deep_model_references = []`; `axiom_check.py` is a skip
stub (G-AX skip).

## Flag dependency

The decision arm is reached only for a non-direct-value RHS that is a subquery
(`not isinstance(self.lhs, MultiColSource)` and `not self.rhs_is_direct_value()`);
those guards are unchanged and outside the modeled decision. G-CONF builds
querysets in the in-subquery configuration.

## G-CONF fuzz seed

`seed = 16032` (pinned in `conformance_check.py`).
