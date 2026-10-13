# mapping.md — django__django-15916

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 88e67a54b7ed0210c11523a337b498aadb2f5187`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectFieldCallback (configCallback) (declaredCallback) (inheritedCallback)` | `ModelFormMetaclass.__new__` — `django/forms/models.py:259` (the callback-resolution it performs before calling `fields_for_model`) | the modeled changed function: choose which field-building callback a model form is built with |
| `configCallback : Option Nat` | `opts.formfield_callback` post-patch — `ModelFormOptions.formfield_callback`, read off the form's own `Meta` (`django/forms/models.py:256` new attr; consumed at `:301`) | the callback the form's OWN `Meta` resolves to (its `Meta.formfield_callback`, taken directly when set on that `Meta`, otherwise inherited through the `Meta` MRO) |
| `declaredCallback : Option (Option Nat)` | the class-body attribute `attrs["formfield_callback"]` — the pre-patch `attrs.pop("formfield_callback", …)` operand (`django/forms/models.py:266`, deleted by the patch) | what, if anything, is named directly on the form class body. Outer `Option` = key presence in `attrs`; inner = the named value (`some none` = the key is present with value `None`, e.g. set explicitly by `modelform_factory`) |
| `inheritedCallback : Option Nat` | `base_formfield_callback` — the first base form's `Meta.formfield_callback` found by the pre-patch base-scan (`django/forms/models.py:260-264`, deleted by the patch) | the callback a parent form offers as a default |
| `out : Option Nat` | the `formfield_callback` value actually passed to `fields_for_model` (`django/forms/models.py:301` post-patch `opts.formfield_callback`) | result: the callback the form's fields are built with |

The function under change is a metaclass `__new__`: from the new form class it
derives three callback sources and selects one to pass to `fields_for_model`.
Per the §2 bijection, those three sources are presented to the Lean model as the
three `Option`/`Option (Option …)` inputs; the model performs the *selection*
(the changed logic). This is the same shape as the exemplar django__django-14792
(a `tzinfo` presented as its two observable labels, the model performing the
`or`-selection): the observations form the input bijection (R-refinement), they
are **not** consumed axioms about a callee.

### The two pre-patch sources collapse, post-patch
The pre-patch metaclass computed `formfield_callback =
attrs.pop("formfield_callback", base_formfield_callback)` — i.e.
`declaredCallback.getD inheritedCallback` (the class-body value if the key is
present, **even when that value is `None`**; otherwise the base-scan value). The
patch deletes both the base-scan and the `attrs.pop`, captures the callback on
`ModelFormOptions` from the form's own `Meta`, and passes `opts.formfield_callback`
— i.e. `configCallback`. The two `modelform_factory` hunks (`opts.formfield_callback`
at the `fields_for_model` call, and dropping `"formfield_callback"` from
`form_class_attrs`) are the *same* selection viewed from the factory: post-patch
the factory's manufactured `Meta.formfield_callback` is what the metaclass reads,
so the now-unused class-body attr is removed. No independent second behavior.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the real repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

A *callback* is an opaque Python callable. Two callbacks are observationally
distinguished only by the form field they build; the model abstracts each
callable to an integer **tag** and "no callback" to `none`. G-CONF realizes tag
`n` as a callback producing a uniquely-classed widget, so the tag is recoverable
from `Form.base_fields[name].widget.__class__`.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a field-building callback (a callable), or "none" | `Option Nat` | a distinct callable ↔ `some n` (tag `n`); no callback ↔ `none` |
| `opts.formfield_callback` (the form's own `Meta`-resolved callback) | `configCallback : Option Nat` | the callback the form's `Meta` resolves to ↔ `some n` / absent ↔ `none` |
| `attrs.get("formfield_callback")` together with the key's presence in `attrs` | `declaredCallback : Option (Option Nat)` | key absent ↔ `none`; key present with value a callback ↔ `some (some n)`; key present with value `None` ↔ `some none` |
| `base_formfield_callback` (first base form's `Meta.formfield_callback`) | `inheritedCallback : Option Nat` | a callback ↔ `some n`; none found ↔ `none` |
| `pop(key, default)` semantics of `attrs.pop("formfield_callback", base)` | `declaredCallback.getD inheritedCallback` | returns the declared value when the key is present (even `None`); else `default` |
| the callback passed to `fields_for_model` | `out : Option Nat` | observed via the produced widget class on `base_fields[name]` |

The carrier `Nat` is used only as an identity tag for callbacks; no arithmetic is
performed. The single property the selection inspects is *which source* supplies
the callback — content of the callbacks is opaque.

## 3. Callee provenance

**No consumed axioms; no deep-model references.** The three callback sources are
*not* axiomatized: the proof relies on no property of any callee beyond "these are
the three callback values the metaclass has in hand," which is precisely the input
bijection (§2, R-refinement). They are the observation functions that present the
form's configuration to the model, exactly as `tz.tzname(None)` / `str(tz)`
present a `tzinfo` in django__django-14792 (a zero-axiom bundle).

Consequently `meta.json` carries `axioms: []`, `deep_model_references: []`,
there is **no `axiom_check.py`**, and **G-AX skips** (no axioms to check). The
selection logic is the entire changed behavior and is fully transliterable
(R/I), so `conf_skip = false` and G-CONF is the meaningful differential gate.

### 3.1 Why `opts.formfield_callback` is the discriminator (provenance of the corpus)
The behavior change observed by the two F2P tests:

| configuration | pre-patch callback | post-patch (`opts.formfield_callback`) | F2P test |
|---|---|---|---|
| own `Meta.formfield_callback = cb`; nothing on class body; no base form | base-scan/`pop` ⇒ `none` (not consulted) | own `Meta` ⇒ `cb` | `test_custom_callback_in_meta` |
| base form's `Meta.formfield_callback = cb`; subclass made by `modelform_factory` (which sets class-body `formfield_callback=None` explicitly) | `attrs.pop("formfield_callback", base) = None` (key present with `None`) ⇒ `none` | own `Meta` inherits `cb` via the `Meta` MRO ⇒ `cb` | `test_custom_callback_from_base_form_meta` |

Both rows are discriminating: pre-patch the form's own `Meta` callback is ignored
(the first because the metaclass never reads `Meta`; the second because the
explicit class-body `None` shadows the base-scan via `pop`), so the produced
field widget is the model default, whereas post-patch it is the custom widget.
`Solution_prepatch.lean` reproduces the pre-patch selection
(`declaredCallback.getD inheritedCallback`) and **fails** `out = configCallback`.
G-CONF includes both rows plus the full 4-source combination matrix.

`test_inherit_after_custom_callback` and `test_custom_callback` (PASS_TO_PASS)
pass the callback through `modelform_factory`'s `formfield_callback=` argument,
which post-patch routes through the manufactured `Meta.formfield_callback`
(`Meta.formfield_callback = staticmethod(formfield_callback)`), i.e. still
`configCallback`; G-CONF's `base_meta_cb` source covers this.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15916`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the
`selectFieldCallback` selection (`out = configCallback`) to Python and bridges
each configuration via the §2 observations: it builds a genuine `ModelForm`
subclass through the real (patched) metaclass for every combination of the three
callback sources and reads the actually-used callback off the produced widget
class. There are no A-tagged callees to leave as the real callee.
