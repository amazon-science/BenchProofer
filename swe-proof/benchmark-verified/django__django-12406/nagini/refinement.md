# refinement.md — django__django-12406

The operation-by-operation correspondence between `model.py`'s implementation
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model validated `==` the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). EVERY step is one of these — there is no
kind-3 (changed-but-inexpressible) step. The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This patch fixes **two independently-observable behaviours**, each its own
modeled function with its own failing prepatch (G-DIFF):

- **Site 1** — `ModelChoiceField.__init__` placeholder decision ⇔
  `configure_placeholder` / `placeholder_offered`; prepatch `model_prepatch_1.py`.
- **Site 2** — `ForeignKey.formfield` forwarding of `blank` ⇔
  `derived_field_emptiness_flag`; prepatch `model_prepatch_2.py`.

## A. Site 1 — the placeholder decision (`django/forms/models.py`)

Gold hunk (`ModelChoiceField.__init__`): the `empty_label` decision is moved to
**after** `Field.__init__` and gains a second suppression clause; a new
`blank=False` keyword is added.

```
-        if required and (initial is not None):
-            self.empty_label = None
-        else:
-            self.empty_label = empty_label
-
         # Call Field instead of ChoiceField __init__() ...
         Field.__init__( self, required=required, ... )
+        if (
+            (required and initial is not None) or
+            (isinstance(self.widget, RadioSelect) and not blank)
+        ):
+            self.empty_label = None
+        else:
+            self.empty_label = empty_label
```

| # | model.py impl op (`configure_placeholder`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `field: ChoiceFieldState`, attribute `field.placeholder: Optional[int]` | `self` and `self.empty_label` | R | `empty_label` (`None` ↔ no blank choice; label string ↔ blank choice offered) ↔ `placeholder: Optional[int]` (mapping.md §2). |
| A2 | `required: bool`, `initial_present: bool` | `required`, `initial is not None` | R | identical boolean and the `is not None` presence test (mapping.md §2). |
| A3 | `is_radio: bool` | `isinstance(self.widget, RadioSelect)` | A-reference | the widget classification is computed by the unchanged base initialiser `Field.__init__` (it normalises a widget class/instance into the widget instance). It is modeled as an already-computed boolean input; G-AX (axiom_check.py §3.1) validates that the real `ModelChoiceField` blank-presence matches `placeholder_offered` for both a `RadioSelect` class and a `RadioSelect()` instance, exactly mirroring the real `isinstance(self.widget, RadioSelect)` after normalisation. |
| A4 | `blank: bool` | the new `blank` keyword | I | identical boolean parameter. |
| A5 | `if (required and initial_present) or (is_radio and not blank): field.placeholder = None else field.placeholder = placeholder_label` | the gold `if ((required and initial is not None) or (isinstance(self.widget, RadioSelect) and not blank)): self.empty_label = None else: self.empty_label = empty_label` | I (under A1-A4 R/A) | the SAME control flow and the SAME boolean decision, op-for-op. |

The discriminating content — the SECOND suppression clause `(is_radio and not
blank)` — lives in the postcondition `field.placeholder is not None iff
placeholder_offered(...)`. `model_prepatch_1.py` reverts `configure_placeholder`
to the pre-patch single-clause decision (`required and initial_present` only)
and **fails** this postcondition on inputs `is_radio and not blank` (a radio
field with no permitted empty value: the spec demands suppression, the buggy
impl offers the placeholder). That is the spec sensing site 1's change (G-DIFF).

## B. Site 2 — forwarding the emptiness flag (`django/db/models/fields/related.py`)

Gold hunk (`ForeignKey.formfield`):

```
         return super().formfield(**{
             ...
             **kwargs,
+            'blank': self.blank,
         })
```

| # | model.py impl op (`derived_field_emptiness_flag`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `model_blank: bool` | `self.blank` (the FK's model-field blank attribute) | R | identical boolean (mapping.md §2). |
| B2 | `return model_blank` | adding `'blank': self.blank` to the form-field kwargs dict | I | the value forwarded to the derived `ModelChoiceField` is exactly the model field's `blank`, unchanged. The dict-merge is the identity transport of that value; G-AX (axiom_check.py §3.2) confirms a real `ForeignKey(blank=B)` records `fk.blank == B` and that the derived radio field's placeholder is decided by that forwarded `B`. |

`model_prepatch_2.py` reverts `derived_field_emptiness_flag` to the pre-patch
behaviour (`return False`: the kwarg was absent, so `ModelChoiceField` fell back
to its `blank=False` default) and **fails** the postcondition `Result() ==
model_blank` when `model_blank` is True. That is the spec sensing site 2's
change (G-DIFF). This is the behaviour F2P `test_blank_foreign_key_with_radio`
(blank=True ⇒ placeholder present) and `test_non_blank_foreign_key_with_radio`
(blank=False ⇒ placeholder absent) observe.

## C. Control-flow reorder (the hard subtlety) — no kind-3

The gold MOVES the `empty_label` decision from before `Field.__init__` to after
it. This is necessary because the new clause reads `self.widget`, which only
exists once `Field.__init__` has normalised it. The reorder is captured
faithfully: `configure_placeholder` receives `is_radio` as an **already-computed
input** (step A3), reflecting that the classification is available only post-
`Field.__init__`. No operation in the model is a changed operation Nagini cannot
express: the decision is pure boolean logic (modeled deeply, A5/B2 = I) and the
single library-dependent fact (the widget classification) is an A-reference
validated by G-AX, not an unjustified hand-wave.

## D. verify(model) ⇒ resolved

`configure_placeholder` verifies only if `field.placeholder` ends present iff
`placeholder_offered(required, initial_present, is_radio, blank)` (A5), i.e.
the field offers the blank placeholder under exactly the post-patch condition;
`derived_field_emptiness_flag` verifies only if it returns `model_blank` (B2),
i.e. the FK forwards its `blank`. By R (Optional-label ↔ `empty_label`, boolean
identities) and the A-reference G-AX results (the real `ModelChoiceField`
choice sequence and the real `ForeignKey.blank` match the deep models), a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited library facts — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: A-reference soundness (G-AX)
and refinement fidelity (this document, G-EQ); there are no consumed axioms.
