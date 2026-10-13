# refinement.md — django__django-12754

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`movedBaseFields` `do` block plus the deep `movedFold`/`isMoved` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed site — `generate_created_models` (`autodetector.py:563-578`)

Gold hunk (added inside `for base in model_state.bases:` when the base is a
`"app.Model"` string):
```python
+ old_base_model_state = self.from_state.models.get((base_app_label, base_name))
+ new_base_model_state = self.to_state.models.get((base_app_label, base_name))
+ if old_base_model_state and new_base_model_state:
+     removed_base_fields = set(old_base_model_state.fields).difference(
+         new_base_model_state.fields,
+     ).intersection(model_state.fields)
+     for removed_base_field in removed_base_fields:
+         dependencies.append((base_app_label, base_name, removed_base_field, False))
```

| # | Solution.lean impl op (`movedBaseFields`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `oldBaseFields : Option (List Int)` | `old_base_model_state = self.from_state.models.get((base_app_label, base_name))`, observed via `.fields` | R | a present base state ↔ `some (field-name set)`, absent (`.get` falsy) ↔ `none` (mapping.md §2). G-CONF bridges by reading the real `ModelState.fields`. |
| A2 | param `newBaseFields : Option (List Int)` | `new_base_model_state = self.to_state.models.get((base_app_label, base_name))`, observed via `.fields` | R | same bijection as A1. |
| A3 | param `derivedFields : List Int` | `model_state.fields` of the created model | R | field names ↔ distinct `Int`s; the `.fields` key set ↔ a `List Int` (mapping.md §2). |
| A4 | `match oldBase, newBase with | some _, some _ => … | _,_ => false` (in `isMoved`) | `if old_base_model_state and new_base_model_state:` short-circuit | I | the both-present guard is the `Option×Option` match; either `none` ⇒ no field qualifies (`movedFold_none_left/right`), exactly the Python falsy short-circuit. |
| A5 | `decide (n ∈ ob) && decide (n ∉ nb)` per field, folded by `movedFold` | `set(old).difference(new).intersection(model_state.fields)` | I | the set computation is transliterated element-wise: a derived field qualifies iff it was in the old base set and not in the new base set. The `.intersection(model_state.fields)` is the restriction to `derivedFields` (the carrier `movedFold` folds over). Concrete membership ops, refuted by G-CONF over ≥10³ real autodetector passes. |
| A6 | `result` is the list of qualifying names; observed as a SET | `for removed_base_field in removed_base_fields: dependencies.append((base_app_label, base_name, removed_base_field, False))` | R + I | the result names ARE the `removed_base_field`s appended as removal deps; `base_app_label`/`base_name`/`False` are constants (R-identity, mapping.md §2). G-CONF compares the field-name set the create depends on. |

Discriminating content of the change — a derived field that was just removed from
the base **must** become a removal dependency so the field removal is sequenced
BEFORE the create. The pre-patch computed no such dependency (the whole block was
absent), so `movedBaseFields` would return `[]` for every input;
`Solution_prepatch.lean` reproduces that (the loop emits `[]` per element) and
**fails** the `out = movedFold oldBaseFields newBaseFields derivedFields` clause
(G-DIFF) — precisely the missing ordering that produced the `FieldError`.

## B. No axioms

There is no site B. The computation consults no unchanged library callee whose
contract the proof must assume: `set.difference`/`set.intersection` are Python
built-ins, transliterated directly as the `isMoved` membership predicate (an
**I** op). Hence no consumed axiom and no deep-model reference; `axiom_check.py`
is absent and G-AX is `skip`. (Same shape as django__django-11163.)

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — computing the
set of moved-down base fields and turning each into a create-ordering dependency
— is modeled **deeply** and concretely (the spelled-out `isMoved`/`movedFold`
fold and the verified backward `while` loop), not hidden behind an axiom about
the function under change. There is no consumed axiom at all.

## D. verify(Solution) ⇒ resolved

`movedBaseFields` verifies only if its output equals, element-for-element, the
`(old_base \ new_base) ∩ derived` set computation (A4–A6) — including the
both-present guard (A4) and the empty result when either base side is absent. By
R (the field-name ↔ `Int` bijection, the `ModelState` ↔ `Option (List Int)`
abstraction, the constant dependency-tuple fields) the verified routine equals
the gold patch's `removed_base_fields` computation on the tested project states;
by G-CONF the R/I transliteration agrees with the field-removal dependencies the
real patched `generate_created_models` appends over ≥10³ real autodetector
passes (seed=12754). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms (no G-AX trust point).
