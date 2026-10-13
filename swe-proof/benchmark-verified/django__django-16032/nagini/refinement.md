# refinement.md — django__django-16032

The operation-by-operation correspondence between `model.py`'s implementation
(the three contracted functions `project_columns`, `attach_auxiliary_expressions`,
`prepare_in_rhs` over the minimal `Query` twin) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses an axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
`axiom_check.py` / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are **no consumed axioms**; the
three operations are modelled deeply, and the underlying real-Django primitives
are A-reference observations validated by G-AX.

## A. The flag-establishing site — `set_values` (`query.py:2383`)

Gold hunks (`query.py`):
```
  class Query(BaseExpression):
      ...
+     has_select_fields = False                 # new class attribute, default False
      ...
-     @property
-     def has_select_fields(self):              # the removed dynamic property
-         return bool(self.select or self.annotation_select_mask or self.extra_select_mask)
  def set_values(self, fields):
      self.select_related = False
      self.clear_deferred_loading()
      self.clear_select_fields()
+     self.has_select_fields = True             # set the flag on projection
```

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `q: Query` (twin with `restricted_to_explicit_columns`, `selected_columns`, `aux_expr_materialized`) | the real `Query` object | R | rich object ↔ minimal twin of the three touched fields (mapping.md §1,§2). |
| A2 | `project_columns`: `q.selected_columns = []` then `q.selected_columns = [column]` | `set_values`'s `clear_select_fields()` then the field machinery setting the SELECT to `fields` | R + A-reference | clearing then setting the selected columns ↔ list reset then single-element assignment (`select`/`values_select` ↔ `List[int]`, mapping.md §2). The real composite (`clear_select_fields` + field setup) is validated == "selected output is exactly `[col]`" by G-AX (mapping.md §3.1). |
| A3 | `project_columns`: `q.restricted_to_explicit_columns = True` | `set_values`'s new line `self.has_select_fields = True` | I | identical concrete assignment of the boolean flag (`has_select_fields` ↔ `restricted_to_explicit_columns`, mapping.md §2). **This is the query.py fix.** |
| A4 | `project_columns`: `q.aux_expr_materialized = False` | `set_values`'s field partitioning + `set_annotation_mask(annotation_names)` — for ordinary column names `annotation_names == []`, so `annotation_select_mask` becomes `set()` | R + A-reference | the projection re-derives the annotation mask for the chosen columns; empty mask ↔ `aux_expr_materialized is False` (mapping.md §2). Validated on the real gold-patched tree by G-AX: after `set_values(['code'])` on an annotate+alias query, `annotation_select_mask == set()` (mapping.md §3.1). This clearing frame was previously mis-modelled as preservation — the G-PANEL-2 UNFAITHFUL finding — and is now faithful. |

## B. The auxiliary-expression site — `add_annotation` via annotate/alias (`query.py:1109`)

The gold patch removes the dynamic `has_select_fields` **property** (above) and
replaces it with a class attribute the annotation machinery never touches. The
observable effect at this site: attaching annotations/aliases materializes the
annotation mask but no longer flips `has_select_fields`.

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `attach_auxiliary_expressions`: `q.aux_expr_materialized = True` | `add_annotation(select=True)` (`append_annotation_mask`) then `add_annotation(select=False)` (`set_annotation_mask(...difference...)`) — reached via `.annotate()` then `.alias()` | R + A-reference | materializing the annotation tracking structure ↔ setting the materialized flag (`annotation_select_mask` non-empty ↔ `aux_expr_materialized is True`, mapping.md §2). G-AX validates that real annotate+alias materializes a non-empty mask (§3.2). |
| B2 | `attach_auxiliary_expressions`: `restricted_to_explicit_columns` left unchanged (no write) | post-patch `has_select_fields` is a class attribute neither `add_annotation` path writes | I | identical: the annotation machinery does not assign the flag. **This is the behavioural content of removing the derived property** — the flag is decoupled from the mask. The postcondition `restricted_to_explicit_columns == Old(...)` pins it; the pre-patch property (which derived `True` from a non-empty mask) violates it (G-DIFF, `model_prepatch.py`). |

## C. The rhs-narrowing site — `RelatedIn.get_prep_lookup` (`related_lookups.py:93-108`)

Gold hunk:
```
  elif not getattr(self.rhs, "has_select_fields", True) and not getattr(
      self.lhs.field.target_field, "primary_key", False
  ):
-     self.rhs.clear_select_clause()
      ... target_field = ...
-     self.rhs.add_fields([target_field], True)
+     self.rhs.set_values([target_field])
```

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `prepare_in_rhs`: guard `if (not q.restricted_to_explicit_columns) and (not target_is_unique_key)` | `elif not getattr(self.rhs, "has_select_fields", True) and not getattr(...target_field..., "primary_key", False)` | R + I | same boolean guard: `has_select_fields` False ↔ `not restricted_to_explicit_columns`; `target_field.primary_key` ↔ `target_is_unique_key` (mapping.md §2). The `getattr(..., True)` default is irrelevant — the rhs here is a `Query`, which always has the attribute. |
| C2 | `prepare_in_rhs`: `project_columns(q, target_column)` (calls operation A, under spec) | `self.rhs.set_values([target_field])` | R + A-reference | identical call to the projection operation A (modelled under its own spec, NOT an axiom): it narrows the rhs to the single target column, sets the flag True, and clears the rhs's annotation mask (operation A4). **This is the related_lookups.py fix:** the old `clear_select_clause()` + `add_fields([...], True)` set the selected columns but, post-patch, would NOT set the new `has_select_fields` attribute. G-AX validates the real narrowing ends with `has_select_fields True`, one column, and an empty `annotation_select_mask` (§3.3). |

The pre-patch `related_lookups.py` (clear + `add_fields`) is reproduced by
`model_prepatch_2.py`: it sets `selected_columns = [target_column]` but does NOT
set the flag, so the postcondition that narrowing establishes
`restricted_to_explicit_columns is True` **fails** — exactly the spec sensing
that the new narrowing must go through `set_values` (G-DIFF).

## D. No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R, I, or A-reference. There is **no consumed `@ContractOnly`
axiom**: the three changed operations are modelled **deeply** (spelled-out state
updates over the minimal twin). The real Django primitives they correspond to
(`set_values`, `add_annotation`/annotate+alias, the `RelatedIn` narrowing) are
**A-reference** observations validated == the real callees by `axiom_check.py`
(G-AX), not consumed in the proof. `prepare_in_rhs` calls `project_columns`
**under its own spec** (the caller uses the callee's contract — §3 of
SPEC_GUIDE: changed functions that call each other use the callee's spec, not an
axiom).

## E. verify(model) ⇒ resolved

The two independently-fixed behaviours each have a failing prepatch:
- **query.py** (`model_prepatch.py`): the derived property — `add_annotation`
  flipping `has_select_fields` True when the annotation mask materializes —
  fails `attach_auxiliary_expressions`'s postcondition
  `restricted_to_explicit_columns == Old(...)`. This is the reported bug: with
  annotate **and** alias, the old property wrongly reported `has_select_fields`,
  so the `__in` rhs was not narrowed (`sub-select returns N columns - expected 1`).
- **related_lookups.py** (`model_prepatch_2.py`): narrowing via
  clear-select + add-fields (not `set_values`) fails `prepare_in_rhs`'s
  postcondition that narrowing establishes `restricted_to_explicit_columns is
  True`. This is the second fixed behaviour (the hint's `ToFieldTests` failures):
  with the new flag-based heuristic, narrowing must go through `set_values` so
  the rhs is recognised as explicitly projected.

By R (Query ↔ twin, column refs ↔ `List[int]`, mask presence ↔ count `> 0`),
the verified operations equal the gold patch's `set_values` /
`add_annotation` / `RelatedIn.get_prep_lookup` on the tested inputs; by G-AX the
deep model matches the real callees (A-reference). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
audited observations — and the gold patch resolves (G-RESOLVE). The trust points
are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
