# refinement.md — operation correspondence (django__django-15280)

Maps every op in `implementation_assignParents` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python loop (in `RelatedManager.get_prefetch_queryset`) is:

```python
for rel_obj in queryset:
    if not self.field.is_cached(rel_obj):
        instance = instances_dict[rel_obj_attr(rel_obj)]
        setattr(rel_obj, self.field.name, instance)
```

Type bijection (mapping.md): a child `rel_obj` ↔ `Child {key, parent}`;
`self.field.is_cached(rel_obj)` ↔ `c.parent.isSome` (equivalently
`¬ c.parent.isNone`); `instances_dict[rel_obj_attr(rel_obj)]` ↔ `lookup c.key`;
`setattr(rel_obj, self.field.name, instance)` ↔ setting `parent := some …`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut acc := []` | the result batch `queryset` accumulated as the loop visits each row | I | concrete empty-output init; iteration preserves order |
| 2 | `for c in children do` | `for rel_obj in queryset:` | I | per-element iteration over the batch, in order |
| 3 | `if c.parent.isNone then …` | `if not self.field.is_cached(rel_obj):` | R | `is_cached(rel_obj)` ↔ "a parent value is already present" ↔ `c.parent.isSome`; the negation ↔ `c.parent.isNone`. The optional slot models the field cache; total/sound in Lean. |
| 4 | `let p := lookup c.key` | `instance = instances_dict[rel_obj_attr(rel_obj)]` | R | dict-keyed-by-related-value lookup ↔ a total `lookup : Int → Int` over the child's key (mapping.md). |
| 5 | `acc := acc ++ [{ c with parent := some p }]` | `setattr(rel_obj, self.field.name, instance)` then keep `rel_obj` | R/I | assigning the looked-up parent into the (previously empty) slot; other components of the child are framed unchanged. |
| 6 | `else acc := acc ++ [c]` (cached branch) | the implicit else of the new `if`: `rel_obj` is appended UNCHANGED, its already-cached parent preserved | I | the new behavior — skip overwriting when a value is already present. This is the bug fix. |
| 7 | `return acc` | the loop terminates; `queryset` is returned | I | identity return of the accumulated batch |

No A-consumed rows (axioms region empty). No A-reference rows: nothing UNCHANGED
is axiomatized — `is_cached`, the dict lookup, and `setattr` are all modeled
directly by the structure's optional slot, the `lookup` argument, and record
update respectively. No changed-inexpressible op.

The discriminating clause is row 6 (paired with row 3's guard): the cached
branch. The prepatch impl drops the `c.parent.isNone` guard and unconditionally
overwrites with `lookup c.key`, so for any child with `parent = some v` where
`v ≠ lookup key`, the prepatch result differs from `children.map (assignOne
lookup)` (which keeps `some v`). Hence its `correct_assignParents` cannot close
against the frozen `problem_spec_assignParents`. That is the G-DIFF signal, and
it is exactly the issue's bug (the inner-prefetch value being overwritten by the
outer object).
