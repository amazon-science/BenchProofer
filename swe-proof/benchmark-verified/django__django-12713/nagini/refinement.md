# refinement.md — django__django-12713

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_component` impl region) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, proof uses the axiom's `Ensures`, and **A-reference**, a deep
model validated == the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The widget-selection block — `formfield_for_manytomany` (`django/contrib/admin/options.py:252`)

Gold hunk (the entire autocomplete/raw_id/filter block becomes wrapped in a
presence guard):
```
-        autocomplete_fields = self.get_autocomplete_fields(request)
-        if db_field.name in autocomplete_fields:
-            kwargs['widget'] = AutocompleteSelectMultiple(db_field.remote_field, self.admin_site, using=db)
-        elif db_field.name in self.raw_id_fields:
-            kwargs['widget'] = widgets.ManyToManyRawIdWidget(db_field.remote_field, self.admin_site, using=db)
-        elif db_field.name in [*self.filter_vertical, *self.filter_horizontal]:
-            kwargs['widget'] = widgets.FilteredSelectMultiple(
-                db_field.verbose_name,
-                db_field.name in self.filter_vertical
-            )
-
+        if 'widget' not in kwargs:
+            autocomplete_fields = self.get_autocomplete_fields(request)
+            if db_field.name in autocomplete_fields:
+                kwargs['widget'] = AutocompleteSelectMultiple(...)
+            elif db_field.name in self.raw_id_fields:
+                kwargs['widget'] = widgets.ManyToManyRawIdWidget(...)
+            elif db_field.name in [*self.filter_vertical, *self.filter_horizontal]:
+                kwargs['widget'] = widgets.FilteredSelectMultiple(...)
```
(The constructor calls are only reformatted across lines; their arguments are
unchanged. The single semantic change is the added `if 'widget' not in kwargs:`
guard.)

| # | model.py impl op (`select_component`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `options: Dict[int, int]`, mutated in place | the `**kwargs` dict of `formfield_for_manytomany`, mutated in place | R | `str`-keyed kwargs ↔ `Dict[int, int]`; `'widget'` ↔ `key_component()`; widget objects ↔ int identity codes (mapping.md §2). Full permission (genuinely mutated). |
| A1' | parameter `component_present: bool`, pinned by `Requires(component_present == (key_component() in options))` | (no runtime op) the value of `'widget' in kwargs` evaluated AT ENTRY, before the guarded block runs | R | a spec-only capture of the ENTRY membership of the presentation key. It is NOT an operation the gold patch performs at run time; it is the pre-state fact `'widget' in kwargs` snapshotted at function entry so the default-selection postcondition can be gated on the genuine entry state rather than on a membership query against the mutated dict (which Nagini evaluates post-mutation for an added key, rendering the gate vacuous). The impl's live guard `if not (key_component() in options)` is logically equal to `not component_present` at entry, so this introduces no behavioural divergence from the patch. |
| A2 | `if not (key_component() in options):` | `if 'widget' not in kwargs:` | R + I | the dict membership test `'widget' in kwargs` ↔ `key_component() in options` (R on the key carrier; the `in` primitive itself is identical, A-reference-checked). This is the one operation the fix ADDS. |
| A3 | `if test_primary:` | `if db_field.name in autocomplete_fields:` (with `autocomplete_fields = self.get_autocomplete_fields(request)`) | R | the `str`-set membership test ↔ the boolean `test_primary` (mapping.md §2); the `get_autocomplete_fields` call only produces the set the name is tested against and is unchanged by the patch. |
| A4 | `options[key_component()] = default_primary()` | `kwargs['widget'] = AutocompleteSelectMultiple(db_field.remote_field, self.admin_site, using=db)` | R | dict assignment under the refined key; the constructed widget ↔ its identity code `default_primary()` (mapping.md §2). The `[]=` primitive is identical (A-reference-checked). |
| A5 | `elif test_secondary: options[key_component()] = default_secondary()` | `elif db_field.name in self.raw_id_fields: kwargs['widget'] = widgets.ManyToManyRawIdWidget(...)` | R | as A3/A4 for the second-priority branch. |
| A6 | `elif test_tertiary: options[key_component()] = default_tertiary()` | `elif db_field.name in [*self.filter_vertical, *self.filter_horizontal]: kwargs['widget'] = widgets.FilteredSelectMultiple(...)` | R | as A3/A4 for the third-priority branch; the combined filter set ↔ the single boolean `test_tertiary` (mapping.md §2). |

The discriminating content of the change — the caller-supplied component
surviving the selection block — lives in the added guard A2. The pre-patch had
no guard, so the priority chain ran unconditionally and overwrote any
caller-supplied `kwargs['widget']`. `model_prepatch.py` reproduces exactly that
(it drops the `if not (key_component() in options):` guard) and **fails** the
preservation postcondition
`Forall k. Old(k in options) ⟹ options[k] == Old(options[k])`, which is precisely
the spec sensing the change (G-DIFF).

## B. The deep model ↔ the real Python primitives (A-reference)

The operations the patch *composes* — `'widget' in kwargs` and
`kwargs['widget'] = …` — are Python language primitives, not library callees.
They are modeled **deeply** (spelled out in the `impl` region over a
`Dict[int, int]`), not behind any consumed axiom.

| # | model.py construct | real operation | tag | justification |
|---|---|---|---|---|
| B1 | the guard + priority chain over `Dict[int,int]` (the whole impl region) | the gold patch's guard + chain over the real `**kwargs` dict | A-reference | there is NO consumed `@ContractOnly` axiom. The deep model is validated == the real primitives out-of-band by `axiom_check.py` (G-AX): it runs the gold patch's exact control flow over a real `dict` and asserts every observation meets `model.py`'s frozen postconditions (mapping.md §3). |

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the presence guard wrapping the selection block — is modeled
**deeply** (the spelled-out `if not (key_component() in options): …` over a
`Dict[int, int]`, validated against the real `dict` primitives by G-AX), not
hidden behind an axiom about the function under change. There is **no consumed
axiom** in this bundle (no `@ContractOnly`): the changed code calls no opaque
library callee whose contract the proof would need; the widget constructors and
name-set membership tests it does call are unchanged and abstracted as opaque
identities/booleans whose internals are irrelevant to the precedence behavior.

## D. verify(model) ⇒ resolved

`select_component` verifies only if (1) it preserves every entry key's value —
in particular a caller-supplied presentation component is never overwritten by a
name-derived default — and (2) when (and only when) no caller component is
present *at entry* (`not component_present`) it establishes the priority-ordered
default with the priority-correct identity, and only it. Clause (2) is gated on
the captured ENTRY fact `not component_present` (pinned equal to the entry value
of `key_component() in options`), not on an `Old`-membership query against the
mutated dict — so each priority implication has teeth: an implementation that
swaps the priority order, stores the wrong default identity, or fails to
establish the default cannot verify (a structurally-different but correct impl
still does; the priority-violating witnesses do not). By R (str↔int key carrier,
widget-object↔identity-code, str-set-membership↔bool) the verified block equals
the gold patch's wrapped selection block on the tested inputs; by G-AX the deep
model equals the real `dict` membership/assignment primitives (A-reference, B1).
The F2P test (`test_formfield_overrides_m2m_filter_widget`) supplies a
`CheckboxSelectMultiple` via `formfield_overrides` (so `'widget' in kwargs` on
entry, i.e. `key_component() in options`) with `filter_vertical = ['members']`
(so the tertiary test fires); the verified preservation clause forces the
caller's component to survive, exactly as the gold patch does and the pre-patch
did not. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and the G-AX-validated deep model — and the
gold patch resolves (G-RESOLVE). The single trust point is the one of
PLAN §1.1: refinement fidelity (this document, G-EQ); axiom soundness is vacuous
here (no consumed axiom) and the deep-model A-reference is discharged by G-AX.
