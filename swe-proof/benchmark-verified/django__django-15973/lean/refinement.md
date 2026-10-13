# refinement.md — django__django-15973

Maps every operation in `implementation_relationDependencies` to its
`patch.diff` counterpart in `_get_dependencies_for_foreign_key`
(`django/db/migrations/autodetector.py`, lines 1397-1431).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed/unchanged callee validated == real callee,
**I** identical concrete op.

## Patch (post-patch, the dependency-building tail)
```python
# swappable_setting branch sets (dep_app_label, dep_object_name) OR:
dep_app_label, dep_object_name = resolve_relation(
    remote_field_model, app_label, model_name,
)
dependencies = [(dep_app_label, dep_object_name, None, True)]
if getattr(field.remote_field, "through", None):
    through_app_label, through_object_name = resolve_relation(
        field.remote_field.through,   # <-- the fix (was: remote_field_model)
        app_label,
        model_name,
    )
    dependencies.append((through_app_label, through_object_name, None, True))
return dependencies
```
The modeled value is the list of `(app_label, object_name)` heads of
`dependencies` (the `(None, True)` tail is a constant, per mapping.md frame
note).

## Operation correspondence
| # | Lean op (`implementation_relationDependencies`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `firstDep := match swappableSetting with \| some s => ("__setting__", s) \| none => modelRefToPair targetRef scopeApp scopeName` | `if swappable_setting is not None: dep_app_label="__setting__"; dep_object_name=swappable_setting; else: dep_app_label,dep_object_name = resolve_relation(remote_field_model, app_label, model_name)` | R / A-reference | swappable branch is the literal `("__setting__", setting)`; non-swappable resolves the TARGET reference via the deep-modeled `resolve_relation` (A-reference). `Option String` ↔ `getattr(..., None)`. |
| 2 | `let mut deps := [firstDep]` | `dependencies = [(dep_app_label, dep_object_name, None, True)]` | I/R | initialize with the target dependency head (constant `(None, True)` tail projected out, mapping.md). |
| 3 | `match throughRef with \| some thr => … \| none => pure ()` | `if getattr(field.remote_field, "through", None):` | R | through-presence guard; `Option ModelRef` ↔ truthiness+value of `field.remote_field.through`. |
| 4 | `deps := deps ++ [modelRefToPair thr scopeApp scopeName]` | `through_app_label, through_object_name = resolve_relation(field.remote_field.through, app_label, model_name); dependencies.append((through_app_label, through_object_name, None, True))` | R / A-reference | **the fix**: the through dependency resolves the THROUGH reference (`thr`, = `field.remote_field.through`), in the owning model's scope, via `resolve_relation` (A-reference). |
| 5 | `return deps` | `return dependencies` | I | return the dependency list. |

`resolve_relation` is the single A-reference: deep-modeled as `modelRefToPair`,
validated `==` the real callee by G-AX. **No A-consumed row** (no `axiom _prop`
is shipped). Therefore `meta.json axioms = []`,
`deep_model_references = ["resolve_relation"]`.

## The abstract case fold (`opaque lower`)
The object-name normalization inside `resolve_relation` is Python `str.lower`
(full Unicode case fold: `'Ä'.lower() = 'ä'`; `'İ'.lower() = 'i̇'` even changes
length). Lean has no equal concrete fold (`Char.toLower` is ASCII-only,
leaving `'Ä'` unchanged), so approximating it per character would be
unfaithful on non-ASCII names. The model therefore declares
`opaque lower : String → String` in the axioms region and states the contract
relative to it — faithful on EVERY input. The spec's content is the
dependency-construction rule (which reference feeds the resolver for each
dependency, in which scope); the fold is exactly the real helper's
normalization, abstracted. G-AX grounds the binding executably (its replica
interprets `lower` as the real `str.lower` and is checked `==` the real
`resolve_relation`); the correctness proof never unfolds `lower`, so no
`axiom` about it is consumed (`#print axioms` = `[propext]`).

## R/A-reference legs ⇒ gates
The impl region mixes R/I ops with the A-reference `modelRefToPair`. Because the
A-reference is itself an executable replica of `resolve_relation` (no opaque
callee left in the impl), the whole impl is concretely executable, so G-CONF
mechanically differential-tests the impl shadow against `patch.diff` behavior
over ≥10^5 fuzzed inputs (`conf_skip = false`), and G-AX independently validates
`modelRefToPair == resolve_relation` against the real repo callee.

## Prepatch = the real bug
Pre-patch (line 1424) the through dependency is resolved from
`remote_field_model` — the relation's TARGET reference — not from
`field.remote_field.through`. `Solution_prepatch.lean`'s impl reproduces exactly
this: in the through branch it appends `modelRefToPair targetRef scopeApp
scopeName` instead of `modelRefToPair thr scopeApp scopeName`. It therefore
cannot satisfy `problem_spec_relationDependencies` on the discriminating clause
(`throughRef = some thr → result = [firstDep, modelRefToPair thr …]`) whenever
`modelRefToPair thr … ≠ modelRefToPair targetRef …` — precisely when the through
model lives in a different app from the target model. That is the FAIL_TO_PASS
case `test_create_with_through_model_separate_apps`: target `testapp.Publisher`
→ `("testapp","publisher")`, through `contract.Contract` →
`("contract","contract")`; the buggy impl emits `("testapp","publisher")` for
the through dependency, sending the migration dependency to the wrong app. The
carried gold proof fails to typecheck against the buggy impl (G-DIFF).
