# mapping.md — django__django-15916

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 88e67a54b7ed0210c11523a337b498aadb2f5187`, states the type
abstraction, and gives the provenance of the (single) deep-model reference.

Repo file under change: `django/forms/models.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `declared_form_callback(meta_own, meta_inherited)` | `ModelFormMetaclass.__new__` selecting the per-field builder passed to `fields_for_model` for a **directly-declared** model form — `django/forms/models.py:258-336` (selection at `:311`, builder stored on options at `ModelFormOptions.__init__`, `:245-255`) | modeled changed behaviour: which builder drives field construction for a directly-declared `ModelForm` |
| `factory_form_callback(passed, base_meta_own, base_meta_inherited)` | `modelform_factory(...)` building the produced form + its `ModelFormMetaclass.__new__` selection — `django/forms/models.py:563-648` (Meta build at `:629-634`, class attrs at `:639`) composed with the metaclass selection at `:311` | modeled changed behaviour: which builder drives field construction for a **factory-produced** form (and any subclass of it) |
| `resolve_attr(own, inherited)` *(deep model — A-reference)* | Python attribute resolution `getattr(meta, "formfield_callback", None)` over a `Meta` `type` whose bases supply the inherited value (`ModelFormOptions.__init__` reads it post-fix; `Meta` MRO supplies inheritance) | pure spec: ordinary attribute lookup with default; validated `== real Python getattr/MRO` by axiom_check.py (G-AX), NOT consumed as an axiom |

Pre-patch repo symbols the change removes/relocates (for the refinement audit,
NOT referenced from the consumer spec view):

- `ModelFormMetaclass.__new__`'s local `base_formfield_callback` loop over
  `bases` and `attrs.pop("formfield_callback", base_formfield_callback)`
  (`django/forms/models.py:260-266`, deleted by the fix), and the use of that
  local at `:311` (replaced by `opts.formfield_callback`).
- `modelform_factory`'s `form_class_attrs = {"Meta": Meta, "formfield_callback":
  formfield_callback}` (`:639`, the `formfield_callback` entry removed).
- The fix ADDS `self.formfield_callback = getattr(options, "formfield_callback",
  None)` to `ModelFormOptions.__init__` (`:255`+), making the builder a
  first-class option resolvable from the form's own options object.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a builder callable (the `formfield_callback`) or `None` | `int` identity code: `0` ↔ `None`/absent; any positive value ↔ a specific callable identity | observationally the tests only distinguish *which* builder ran (it determines the widget type, e.g. `Textarea` vs the model default); callable identity ↔ a distinct positive code; `None`/"no builder" ↔ `0`. axiom_check.py realises the bijection with distinct stand-in callables. |
| an inner `Meta`/options object's `formfield_callback` attribute, resolved through `Meta`'s base classes | a pair `(own, inherited)`: `own` = builder declared directly on this options object (`0` if not), `inherited` = builder reachable from its parent options object | `getattr(meta, "formfield_callback", None)` ↔ `resolve_attr(own, inherited)`; setting it directly ↔ `own != 0`; inheriting it ↔ `own == 0 and inherited != 0` |
| `staticmethod(...)` wrapper applied by the factory | identity on builder identity | `staticmethod` only changes descriptor binding, not *which* callable is selected; the tests observe the produced widget, unaffected by the wrapper |
| the metaclass loop + `fields_for_model` actually invoking the builder per field | the single selected builder identity | every field is built by the one selected builder; the tests assert each field's widget, i.e. the selected builder identity, so the per-field fold collapses to "which builder was selected" |

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `resolve_attr` deep model ↔ real Python attribute resolution
**Reference:** CPython's attribute lookup `getattr(obj, name, default)` over a
`type` and its MRO. The changed selection is modelled **deeply** by the `@Pure`
`resolve_attr` (own shadows inherited; absence yields the default) in the
`pure` region; there is **no `@ContractOnly` axiom** the proof consumes.

The deep model is validated equal to the genuine resolution out-of-band by
`axiom_check.py` (G-AX), which executes the real object model:

- `ModelFormOptions.__init__` (post-fix) reads
  `getattr(options, "formfield_callback", None)` where `options` is the form's
  inner `Meta` `type`; `Meta` inheritance supplies the `inherited` value
  (the produced `Meta` in `modelform_factory` is `type("Meta", (form.Meta,),
  attrs)`, so a base form's `Meta.formfield_callback` is reachable).
- The factory sets `Meta.formfield_callback = staticmethod(formfield_callback)`
  **only when truthy** (`:633-634`) and, post-fix, injects NO overriding
  `formfield_callback` class attribute on the produced form (`:639` change).
  So when the factory is given no builder, the produced options object still
  resolves the base form's builder — exactly `resolve_attr(0, base)`.

axiom_check.py asserts `resolve_attr` (and the two modeled functions composing
it) agree with the real resolution on the two FAIL_TO_PASS scenarios and 20000
randomized presence/absence configurations at each level (40002 resolutions
total, 0 mismatch). It also asserts the further-subclass case
(`InheritedForm(NewForm)`) resolves to the same builder as its parent — the
`test_custom_callback_from_base_form_meta` subclass assertion.

**Flag/configuration dependence:** none. The behaviour is independent of field
contents; `resolve_attr` captures pure attribute resolution. The only
observable is *which* builder identity is selected, which determines the widget
type the F2P tests compare. stdlib-only (the check needs no Django import; it
reproduces the exact `type()`/`getattr`/`staticmethod` resolution the patch
uses).
