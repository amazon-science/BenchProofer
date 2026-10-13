# refinement.md — django__django-16950

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`prepareParentKey` `do` block and the `shouldClearKey` decision in the `pure`
region) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The decision site — `add_fields` (`django/forms/models.py:1173-1181`)

Gold hunk:
```
             else:
                 to_field = self.instance._meta.pk
-            if to_field.has_default():
+
+            if to_field.has_default() and (
+                # Don't ignore a parent's auto-generated key if it's not the
+                # parent model's pk and form data is provided.
+                to_field.attname == self.fk.remote_field.model._meta.pk.name
+                or not form.data
+            ):
                 setattr(self.instance, to_field.attname, None)
```

The enclosing `if self.instance._state.adding:` (line 1175) is unchanged; it
guards the whole block, so it is part of the discard condition (`creatingNew`).

| # | Solution.lean impl op (`prepareParentKey`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `mut inst : ParentObject`, field `keyValue : Option Nat` | `self.instance`, attribute `self.instance.<to_field.attname>` | R | only the touched attribute is modeled; present↔`some`, cleared↔`none` (mapping.md §2). G-CONF bridges. |
| A2 | input `creatingNew : Bool` | `self.instance._state.adding` (line 1175 guard) | R | bool↔bool (mapping.md §2). |
| A3 | input `keyHasDefault : Bool` | `to_field.has_default()` (line 1180/1182) | R | bool↔bool; `to_field` resolution (lines 1176-1179) is unchanged and upstream (mapping.md §1). |
| A4 | input `keyIsPrimaryKey : Bool` | `to_field.attname == self.fk.remote_field.model._meta.pk.name` (line 1183, added disjunct 1) | R | string-equality predicate ↔ bool (mapping.md §2). |
| A5 | input `noDataSubmitted : Bool` | `not form.data` (line 1184, added disjunct 2) | R | Python truthiness of the submitted data ↔ bool (mapping.md §2). |
| A6 | `shouldClearKey = creatingNew && keyHasDefault && (keyIsPrimaryKey \|\| noDataSubmitted)` | the full guard: `_state.adding` ∧ `has_default()` ∧ (`attname == pk.name` ∨ `not form.data`) | I | identical boolean structure: `and`↔`&&`, `or`↔`\|\|`. The single behavioural change — adding the `(keyIsPrimaryKey \|\| noDataSubmitted)` factor — is modeled concretely here, not behind an axiom. |
| A7 | `if shouldClearKey … then inst := { inst with keyValue := none } else return` | `setattr(self.instance, to_field.attname, None)` under the guard (else: no-op) | I | the guarded clear: when the decision holds, the attribute becomes `None`/`none`; otherwise the instance is untouched. The directive-5 frame (`inst.keyValue = instOld.keyValue` on the else branch) pins that no other clearing is admitted. |

Discriminating content of the change — when the FK target is an ALTERNATE key
(`keyIsPrimaryKey = false`) and field data WAS submitted (`noDataSubmitted =
false`), with `creatingNew = keyHasDefault = true` — the new guard yields
`shouldClearKey = false`, so the value is PRESERVED. The pre-patch guard
(`creatingNew && keyHasDefault`, no extra factor) cleared it. `Solution_prepatch.lean`
reproduces the pre-patch guard and **fails** the directive-5 frame postcondition
`shouldClearKey = false → inst.keyValue = instOld.keyValue` at exactly that
input (G-DIFF). This is the bug the F2P test
`test_inlineformset_factory_nulls_default_pks_alternate_key_relation_data`
observes: `assertEqual(formset.forms[0].instance.parent_id, formset.instance.uuid)`
(the alternate key must be kept, not nulled).

## B. No consumed axioms, no A-reference

There is no unchanged imperative/pure callee whose contract the proof consumes,
and no changed op modeled deeply against a real callee. The `to_field` resolution
(lines 1176-1179) is unchanged and upstream of the decision; its result feeds the
R-refined boolean inputs `keyHasDefault` / `keyIsPrimaryKey`, so it is not a
callee the modeled decision relies on internally. Hence no `axiom_check.py`
(meta.json `G-AX.status = "skip"`), matching the no-axiom boolean-band exemplar
django__django-12276.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — adding the
`(keyIsPrimaryKey || noDataSubmitted)` factor to the discard guard — is modeled
**concretely** by `shouldClearKey` (step A6, an I op), not hidden behind an axiom
about the function under change. There is no consumed contract.

## D. verify(Solution) ⇒ resolved

`prepareParentKey` verifies only if (i) when `shouldClearKey` holds the attribute
is cleared (`inst.keyValue = none`), and (ii) when it does NOT hold the attribute
is preserved exactly (`inst.keyValue = instOld.keyValue`, the directive-5 frame).
By the R refinements (`ParentObject`↔`self.instance` touched-field, four
bool↔bool observations) and the I identity of `shouldClearKey` to the patched
guard, a verified `prepareParentKey` equals the patched `add_fields` decision
block on the tested inputs; by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on the full `2^4` cube + ≥10⁵ fuzzed inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The only trust point
is refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (G-AX skip).
