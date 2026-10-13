# refinement.md — django__django-12406

Operation-by-operation correspondence between `Solution.lean`'s two impl regions
(`relationBlankFlag` for site B and `blankChoiceOffered` for site A) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. This bundle has
**no A steps** (no axiomatized callees): both modeled functions are CHANGED
functions whose new logic is a pure boolean combination of inputs, modeled
deeply and tagged R/I.

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`,
resolves — G-RESOLVE).

The fix is **two coupled sites**, each its own `method` (plan §3, multi-site).

## A. Site B — `ForeignKey.formfield` forwards the model's blank flag

Gold hunk (`django/db/models/fields/related.py`):
```
         return super().formfield(**{
             'queryset': self.remote_field.model._default_manager.using(using),
             'to_field_name': self.remote_field.field_name,
             **kwargs,
+            'blank': self.blank,
         })
```

| # | Solution.lean impl op (`relationBlankFlag`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `modelAllowsBlank : Bool` | `self.blank` (model field's bool attribute) | R | Python bool ↔ Lean `Bool` (mapping.md §2). |
| A2 | `return modelAllowsBlank` | `'blank': self.blank` added to the kwargs forwarded to `ModelChoiceField` | I | identity forwarding: the value handed to the choice field is exactly the model's `blank` flag. The surrounding `queryset`/`to_field_name`/`**kwargs` entries are unchanged by the patch and irrelevant to the blank decision (they configure other aspects of the field), so they are abstracted away — the ONLY changed dataflow at this site is the forwarded blank flag. |

Pre-patch, this key was absent, so `ModelChoiceField.__init__` received its
default `blank=False` and behaved as though a blank selection were never
permitted. `Solution_prepatch_2.lean` reproduces that (constant `false`) and
**fails** `out = modelAllowsBlank` whenever the model permits blank (G-DIFF).

## B. Site A — `ModelChoiceField.__init__` blank-option decision

Gold hunk (`django/forms/models.py`): the signature gains `blank=False`, and the
empty-label assignment moves after `Field.__init__` and gains the radio clause:
```
-        if required and (initial is not None):
-            self.empty_label = None
-        else:
-            self.empty_label = empty_label
         ...
+        if (
+            (required and initial is not None) or
+            (isinstance(self.widget, RadioSelect) and not blank)
+        ):
+            self.empty_label = None
+        else:
+            self.empty_label = empty_label
```
(plus `from django.forms.widgets import ... RadioSelect ...`.)

The OBSERVABLE this site governs is whether the synthetic blank choice appears
in `field.choices`. `ModelChoiceIterator.__iter__` yields the leading
`("", empty_label)` pair iff `self.empty_label is not None`
(`django/forms/models.py:1149-1150`). So:

    blank option offered  ⇔  empty_label is not None  ⇔  NOT (the assignment to None fires)

`blankChoiceOffered` models that observable boolean directly.

| # | Solution.lean impl op (`blankChoiceOffered`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `required initialPresent widgetIsRadio blank : Bool` | `required` arg; `initial is not None`; `isinstance(self.widget, RadioSelect)`; the `blank` arg | R | each Python truth value ↔ Lean `Bool` (mapping.md §2). `initialPresent` is `initial is not None`; `widgetIsRadio` is the `isinstance(..., RadioSelect)` result. |
| B2 | `required && initialPresent` | `required and initial is not None` | I | identical conjunction (first withholding condition). |
| B3 | `widgetIsRadio && !blank` | `isinstance(self.widget, RadioSelect) and not blank` | I | identical conjunction (second withholding condition — the added rule). |
| B4 | `(B2) \|\| (B3)` then `out = !(…)` | `if (B2) or (B3): empty_label = None else: empty_label = empty_label`, observed as `empty_label is not None` | I + R | the disjunction is the `or` of the two `if` conditions (I); the outer negation is the R bridge `empty_label is not None ↔ blank option offered` (the `if`-branch sets `None` ⇒ no blank option; the `else`-branch keeps a non-`None` label ⇒ blank option). mapping.md §1, §2. |

Discriminating content of the change — the second disjunct
`widgetIsRadio && !blank` — is exactly the rule the pre-patch lacked. The
pre-patch withheld the blank option only on `required && initialPresent`;
`Solution_prepatch.lean` reproduces that (`out = !(required && initialPresent)`)
and **fails** `out = !((required && initialPresent) || (widgetIsRadio && !blank))`
whenever a radio field forbids blank (G-DIFF). This is what the F2P
`test_choices_radio_blank` (radio + `blank=False` ⇒ no leading blank choice;
radio + `blank=True` ⇒ leading blank choice) and
`test_non_blank_foreign_key_with_radio` observe.

## C. The coupling (why two methods, why both prepatches)

The user-visible bug (a non-blank FK rendered with a radio widget still shows a
blank option) needs BOTH sites: site B must forward the model's `blank` so that
site A's new `widgetIsRadio && !blank` rule can fire. The two sites are
independently observable, so there are two failing prepatches (one per site,
G-DIFF):

* `Solution_prepatch.lean` — site A's pre-image (radio rule absent). Fails the
  `blankChoiceOffered` spec.
* `Solution_prepatch_2.lean` — site B's pre-image (flag not forwarded ⇒
  constant `false`). Fails the `relationBlankFlag` spec.

`test_choices_radio_blank` constructs `ModelChoiceField` directly with `blank=`,
so it pins site A in isolation; `test_blank_foreign_key_with_radio` (blank=True,
P2P) and `test_non_blank_foreign_key_with_radio` (blank=False, F2P) go through a
`ModelForm` over a FK, exercising the site-B → site-A coupling.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. Each changed operation — forwarding the blank flag (site
B) and adding the radio withholding rule (site A) — is a pure boolean dataflow,
modeled **deeply** as a closed boolean expression, not hidden behind an axiom
about the function under change. There are no consumed axioms and no
A-references.

## E. verify(Solution) ⇒ resolved

`relationBlankFlag` verifies only if it returns exactly the model's blank
flag (A2); `blankChoiceOffered` verifies only if its result equals
`!((required && initialPresent) || (widgetIsRadio && !blank))` (B2–B4). By R
(the bool bijections and the `empty_label is not None ↔ blank option offered`
bridge) the verified results equal the patched expressions on the real form/
model objects. By G-CONF the R/I transliteration of both decisions agrees with
the patched source behaviour on the fuzzed boolean cube; there are no axioms, so
no G-AX obligations. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The only residual trust point is the type bijection (mapping.md
§2), exercised by G-CONF; there is no axiom trust point.
