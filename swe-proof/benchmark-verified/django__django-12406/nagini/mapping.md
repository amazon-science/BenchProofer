# mapping.md — django__django-12406

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 335c9c94acf263901fb023404408880245b0c4b4`, states the type
abstraction, and gives the provenance of the A-reference deep models (checked by
axiom_check.py / G-AX). There are **no consumed `@ContractOnly` axioms**.

Repo files under change:
`django/forms/models.py` and `django/db/models/fields/related.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `configure_placeholder(field, placeholder_label, required, initial_present, is_radio, blank)` | the `empty_label` decision block in `ModelChoiceField.__init__` — `django/forms/models.py:1184-1191` | the modeled changed function (site 1): decides whether the leading blank placeholder choice is offered |
| `ChoiceFieldState.placeholder` (`Optional[int]`) | `ModelChoiceField.empty_label` — set at `django/forms/models.py:1189,1191` | the carrier whose `None`/present state the choice iterator reads |
| `placeholder_offered(required, initial_present, is_radio, blank)` *(deep model — A-reference)* | the boolean condition `(required and initial is not None) or (isinstance(self.widget, RadioSelect) and not blank)` (negated) — post-patch `django/forms/models.py:1192-1196` | pure spec of the suppression decision; validated `== real ModelChoiceField.choices` blank-presence by axiom_check.py |
| `derived_field_emptiness_flag(model_blank)` | the `'blank': self.blank` kwarg added in `ForeignKey.formfield` — `django/db/models/fields/related.py:973-983` | the modeled changed function (site 2): forwards the data layer's emptiness-permission flag to the derived field |

Observable bridge (not referenced from the consumer spec view): the choice
iterator `ModelChoiceIterator.__iter__` (`django/forms/models.py:1148-1150`)
yields the blank-keyed entry `("", self.field.empty_label)` as the FIRST choice
**iff `self.field.empty_label is not None`**. So "placeholder offered" ⇔
"`empty_label is not None`" ⇔ "the choice sequence begins with a blank-keyed
entry". This is exactly what F2P `test_choices_radio_blank` asserts (the list is
`[('', '---------')] + choices` iff `blank`).

The pre-patch repo state the change replaces (for the refinement audit, not in
the consumer spec view):
- `ModelChoiceField.__init__` computed `empty_label` from `required and
  (initial is not None)` ALONE, **before** calling `Field.__init__`
  (`django/forms/models.py:1188-1191`), with no `blank` parameter.
- `ForeignKey.formfield` assembled the form-field kwargs WITHOUT `'blank'`
  (`django/db/models/fields/related.py:978-983`), so `ModelChoiceField` fell
  back to its `blank=False` default.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.empty_label` — `None` (no blank choice) or the label string (blank choice offered) | `ChoiceFieldState.placeholder : Optional[int]` | `None ↔ None`; any present label string ↔ a present `int` code. The tested behaviour observes only PRESENT-vs-ABSENT (does the choice sequence start with a blank entry), so the label's concrete content is irrelevant and carried by an arbitrary present `int`. |
| `empty_label="---------"` argument (the candidate label) | `placeholder_label : int` | the supplied candidate label; carried by an arbitrary present `int`. The `Implies(...placeholder == placeholder_label)` post pins that, when offered, the SUPPLIED label is the one carried (not replaced). |
| `required : bool` | `required : bool` | identical |
| `initial is not None` | `initial_present : bool` | the tested decision depends only on whether `initial` is present, not its value (`initial is not None`). |
| `isinstance(self.widget, RadioSelect)` (after `Field.__init__` normalises the widget) | `is_radio : bool` | the presentation classification computed by the unchanged base initialiser; an A-reference (§3). |
| `blank : bool` (the new `__init__` kwarg / `self.blank` of the FK) | `blank : bool` / `model_blank : bool` | identical boolean |

`Field.__init__`'s widget normalisation (instantiate a widget class, deep-copy a
widget instance) is the reason the patch moves the `empty_label` decision to
**after** `Field.__init__`: `isinstance(self.widget, RadioSelect)` is only
well-defined once `self.widget` is set. This control-flow reorder is captured
by `configure_placeholder` taking `is_radio` as an already-computed input
(refinement.md step C1).

## 3. A-reference deep models (checked by G-AX / axiom_check.py)

There are no consumed axioms. Two deep models are validated against the real
library behaviour out-of-band.

### 3.1 `placeholder_offered` ↔ real `ModelChoiceField` choice sequence
**Callee:** `django.forms.ModelChoiceField` + `ModelChoiceIterator`
(`django/forms/models.py`). The suppression decision is modeled deeply by the
`@Pure` predicate `placeholder_offered`. axiom_check.py builds a REAL
`ModelChoiceField` for every combination of
`required × initial_present × widget ∈ {default, RadioSelect class, RadioSelect
instance, Select instance} × blank` (32 cases) and asserts

  `list(field.choices)[0][0] == ""  ==  placeholder_offered(required,
  initial_present, is_radio, blank)`

— i.e. the OBSERVABLE blank-placeholder presence equals the deep model, with no
double-mask proxy (the equality is checked at the choice-sequence level, the
exact level F2P `test_choices_radio_blank` observes). `is_radio` is taken from
the widget kind passed in, matching the real `isinstance(self.widget,
RadioSelect)` after `Field.__init__` normalisation (verified by including both
the `RadioSelect` class and a `RadioSelect()` instance, mirroring
`test_choices_radio_blank`'s `[forms.RadioSelect, forms.RadioSelect()]`).

### 3.2 `derived_field_emptiness_flag` ↔ real `ForeignKey.formfield` forwarding
**Callee:** `django.db.models.ForeignKey.formfield`
(`django/db/models/fields/related.py`). The forwarding is the identity
`Result() == model_blank`. axiom_check.py builds a real `ForeignKey(blank=B)`,
asserts `fk.blank == B`, and asserts the observable consequence — a non-required
radio `ModelChoiceField` built with that `blank` offers the placeholder iff `B`
is True (`placeholder_offered(False, False, True, B)`). This is exactly the
behaviour the gold's `'blank': self.blank` addition produces, and it drives
F2P `test_blank_foreign_key_with_radio` (blank ⇒ placeholder) /
`test_non_blank_foreign_key_with_radio` (not blank ⇒ no placeholder).

**Soundness check (G-AX):** `axiom_check.py` imports only Django (the library
the gold patch edits) + stdlib, configures minimal settings (no app registry,
no DB query — in-memory stub querysets), and exits 0 iff every observation
matches the model. Run against the PATCHED Django it passes (32 + 2 cases);
run against the PRE-PATCH Django it raises (the `blank` kwarg does not exist),
confirming the check is discriminating, not a tautology.
