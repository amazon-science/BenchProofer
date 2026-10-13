# refinement.md — django__django-16938

Operation correspondence between `implementation_m2mPkQuery` (Solution.lean) and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

## Modeled function: the m2m related-pk query builder (`queryset_iterator`)

Pre-patch Python (both sites, byte-identical):
```python
return getattr(obj, field.name).only("pk").iterator()
```
Post-patch (gold):
```python
return getattr(obj, field.name).select_related().only("pk").iterator()
```

The behaviorally relevant part is the query-state construction; `.iterator()` is
a streaming wrapper with no effect on the FieldError condition or the load mask
and is not modeled.

| # | `implementation_m2mPkQuery` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | input `qs : QuerySet` | `getattr(obj, field.name)` — the related manager's base queryset | R | a queryset (Python) ↔ `QuerySet` projected onto `relation`/`selectRel`/`immediate` (see mapping.md type bijection). The frame field `relation` is the related-set identity. |
| 2 | `q := { q with selectRel := SelectRel.unrestricted }` | the inserted `.select_related()` (no args) | R | no-arg `select_related()` sets `query.select_related = True` (non-dict), discarding any restricted field dict. Projected to `selectRel := unrestricted` (the True/False non-dict values collapse; see Leakage note). This is the line the gold patch ADDS — the fix. |
| 3 | `q := { q with immediate := some ["pk"] }` | `.only("pk")` | R | `only("pk")` sets the immediate-load mask to `{pk}` (defers all other fields). Modeled as `immediate := some ["pk"]`. Identical at both pre- and post-patch; carried by both. |
| 4 | `return q` | `.iterator()` then the returned iterator | I | the constructed query is what gets evaluated/iterated; the streaming wrapper is behavior-irrelevant and unmodeled. |

The rejection condition the fix avoids — `select_related_descend` raising
`FieldError` when a field is both deferred (absent from the immediate mask) and
traversed under restricted `select_related` — is modeled DEEPLY as
`raisesFieldError` (the `pure` helper). It is the UNCHANGED callee's behavior, an
**A-reference**, NOT a consumed axiom: the spec's no-conflict clause
(`raisesFieldError result = false`) is discharged structurally from op #2
(`selectRel := unrestricted` makes `raisesFieldError` return `false` by definition,
regardless of the inherited dict). G-CONF differential-tests `raisesFieldError`
and the builder against an independent reconstruction of the patched query state +
`select_related_descend` over ≥10^5 inputs.

No op in `implementation_m2mPkQuery` is changed-inexpressible: the whole behavior
is modeled deeply. There is **no consumed axiom** and **no opaque callee** (the
`axioms` region is empty); `axiom_check.py` is a skip stub (G-AX SKIP). The R/I
legs (rows 1-4) and the A-reference (`raisesFieldError`) are mechanically refuted
by G-CONF.

## Prepatch (G-DIFF)
`Solution_prepatch.lean` drops op #2 (no clearing step), leaving the inherited
`selectRel`. For a `fields [f]` input with `f ∉ mask`, the traversal clause
(`result.selectRel = SelectRel.unrestricted`) is false and `raisesFieldError
result = true`, so `correct_m2mPkQuery` is unclosable — exactly the issue's bug
(`test_serialize_prefetch_related_m2m` / the custom-manager `FieldError`). The
carried gold proof body fails to typecheck on the third and fourth clauses. One
prepatch suffices: both call sites are the same behavior.

## Leakage note (spec clause 3 / the SelectRel projection)
The model deliberately does NOT distinguish the two non-dict
`query.select_related` values: gold's no-arg `.select_related()` produces
`True` while the equally-correct alternative fix `.select_related(None)`
produces `False`, and the True-vs-False distinction is behaviorally
unobservable in the modeled slice (both make `restricted=False`,
byte-identical serialized output, both F2P tests pass). A `SelectRel` with
separate `all`/`none` constructors pinned to `all` would encode the gold
patch's exact API call (disclosed only in hints_text, not the problem
statement). The type therefore projects both non-dict values to a single
`unrestricted` constructor, and clause 3 pins only what the issue observably
demands: the inherited field-restricted configuration must not survive
(`result.selectRel = SelectRel.unrestricted`).

## Multi-site note
The gold patch edits two files (python.py, xml_serializer.py) with the identical
hunk. They are one modeled behavior (mapping.md "Multi-site"); `patch.diff`
carries both hunks (gold verbatim) so the harness resolves across all serializer
formats.
