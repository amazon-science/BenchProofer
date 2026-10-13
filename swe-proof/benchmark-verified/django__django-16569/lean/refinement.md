# refinement.md — django__django-16569

Maps every operation in `implementation_addFields` to its `patch.diff`
counterpart in `BaseFormSet.add_fields` (django/forms/formsets.py:472, deletion
branch :493-499). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** op left as the real repo callee in G-CONF, **I** identical
concrete op.

## Patch (post-patch deletion branch)
```python
if self.can_delete and (
    self.can_delete_extra or (index is not None and index < initial_form_count)
):
    form.fields[DELETION_FIELD_NAME] = BooleanField(
        label=_("Delete"), required=False, widget=self.get_deletion_widget(),
    )
```

The single changed token is the `index is not None and` guard inserted in front
of the `index < initial_form_count` comparison. Everything else (the
`can_delete` / `can_delete_extra` short-circuit, the field-construction body) is
unchanged.

## Modeling decision
The observable behavior of the deletion branch is: does `add_fields` complete and
attach the deletion field, or does it raise? We model the outcome as
`Option Bool`:
- `none` ↔ `add_fields` raised (the `TypeError` from `None < int`);
- `some b` ↔ it completed, with `b = (DELETION_FIELD_NAME in form.fields)`.

The decision is a pure boolean over `(can_delete, can_delete_extra, index,
initial_form_count)`. `index` is `Option Nat` (`none ↔ None`). The within-prefix
test `withinInitial` returns `false` for a positionless item (`none`) and
`decide (i < ifc)` for a positioned one — exactly the patched guard `index is not
None and index < initial_form_count`. The field-construction side effect is
abstracted to the boolean "was the field attached"; the proof/spec do not model
`BooleanField`/`get_deletion_widget` (unchanged, untouched by the fix).

## Operation correspondence
| # | Lean op (`implementation_addFields`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut addControl := false` | the deletion field is absent unless the guard fires | I | default outcome: no deletion field |
| 2 | `if canDelete then …` | `if self.can_delete and (…)` outer conjunct | I | `can_delete : bool ↔ canDelete : Bool`; short-circuits the whole branch |
| 3 | `if canDeleteExtra then addControl := true` | `self.can_delete_extra or (…)` first disjunct | I | `can_delete_extra : bool ↔ canDeleteExtra : Bool`; attaches the field for any item |
| 4 | `match index with \| some i => if i < ifc then addControl := true \| none => pure ()` | `(index is not None and index < initial_form_count)` second disjunct | R | `index : (int\|None) ↔ Option Nat`; positionless (`None`/`none`) ⇒ guard false (no crash, field omitted); positioned ⇒ `i < ifc`. This is the FIXED token. |
| 5 | `return some addControl` | branch completes; field present iff guard fired | I | total outcome (`some _`) — never raises. |

## R/I legs ⇒ G-CONF
Op 4 (the optional-position guard, R) is the modeled change; ops 1,2,3,5 (I) are
the unchanged boolean framing. `conf_skip = false`: the impl region is genuine
R/I content. `conformance_check.py` builds the boolean shadow (the full deletion
decision) and differential-tests it against the REAL patched
`BaseFormSet.add_fields` — driving a live formset, calling `add_fields(form,
index)` with `index ∈ {None} ∪ [0..n]`, and observing both whether it raised and
whether `DELETION_FIELD_NAME` landed in `form.fields` — over ≥10^5 fuzzed inputs.

## No A-consumed / A-reference row
The deletion decision calls no unchanged callee that needs a property: it is pure
boolean logic plus a comparison. The field-construction side effect is abstracted
away (not axiomatized, not modeled). So `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## F2P alignment
`test_disable_delete_extra_formset_forms` builds a formset with `can_delete=True,
can_delete_extra=False` and asserts `"DELETE" not in formset.empty_form.fields`.
`empty_form` calls `add_fields(form, None)` (positionless). Pre-patch, the deletion
branch evaluates `None < initial_form_count` and raises `TypeError` — modeled as
the prepatch impl returning `none`, which violates the spec's TOTAL `result =
some _` clause (the discriminating clause). The fixed impl returns `some false`
(field omitted for the positionless item), satisfying the spec. `patch.diff` (gold
verbatim) makes the harness resolve.
