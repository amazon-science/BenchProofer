# refinement.md — django__django-15916

Maps every operation in `implementation_resolveModelFormCallback` to its
`patch.diff` counterpart. The modeled value is the `formfield_callback` that the
metaclass selects and hands to the field builder when constructing a model-form
class (`ModelFormMetaclass.__new__` in `django/forms/models.py`).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed op validated == real callee, **I** identical
concrete op.

## Patch (post-patch callback selection)

```python
# ModelFormOptions.__init__ now stores the options-block callback:
self.formfield_callback = getattr(options, "formfield_callback", None)

# ModelFormMetaclass.__new__ now feeds opts.formfield_callback to fields_for_model
# (was a `formfield_callback` local resolved from attrs.pop + base scan):
fields = fields_for_model(opts.model, opts.fields, opts.exclude, opts.widgets,
                          opts.formfield_callback, ...)
```
i.e. the selected callback is exactly `opts.formfield_callback`, the callback in
the constructed class's own options block (`metaCallback`). The factory change
(`form_class_attrs = {"Meta": Meta}`) removes the injected top-level
`formfield_callback=None`, which is what previously clobbered an inherited Meta
callback — so it too is subsumed by "the result is the options-block callback".

## Operation correspondence

| # | Lean op (`implementation_resolveModelFormCallback`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut selected := metaCallback` | `opts.formfield_callback` (= `getattr(Meta, "formfield_callback", None)`) passed to `fields_for_model` | R | `opts.formfield_callback` ↔ `metaCallback : Option Callback`; a callable ↔ `some id`, absence ↔ `none`. Type bijection in mapping.md. |
| 2 | `return selected` | the callback value `fields_for_model` receives | I | return the selected callback. |

Inputs `directHasCallback` / `directCallback` (the pre-patch `attrs.pop(
"formfield_callback", …)`) and `baseMetaCallback` (the pre-patch `for b in bases`
scan) are **deliberately framed out**: the post-patch selection reads none of
them. The spec pins `result = metaCallback`, so any impl that consulted those
inputs would violate it — that is the discriminating clause.

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of
an unchanged callee). Therefore `meta.json axioms = []`,
`deep_model_references = []`, and `axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF

The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug

Pre-patch, the metaclass resolved the callback as
`attrs.pop("formfield_callback", base_formfield_callback)` where
`base_formfield_callback` is the first base's `Meta.formfield_callback` — i.e.
a direct top-level class attribute when present, otherwise the first base form's
options-block callback, **ignoring the class's own options block entirely**. The
prepatch impl (`selected := baseMetaCallback.getD none; if directHasCallback then
selected := directCallback`) is exactly this resolution. It cannot satisfy
`problem_spec_resolveModelFormCallback` (`result = metaCallback`) whenever the
own-options-block callback differs from what the legacy resolution yields — the
two F2P cases:

* `test_custom_callback_in_meta`: a class declaring `Meta.formfield_callback =
  callback` with no top-level attribute and no relevant base ⇒ `metaCallback =
  some cb` but the legacy resolution yields `none` (the factory-injected `None`
  / empty base scan). Spec demands `some cb`; prepatch returns `none`.
* `test_custom_callback_from_base_form_meta`: `modelform_factory(form=BaseForm)`
  builds a class whose options block inherits `BaseForm.Meta.formfield_callback`;
  the factory previously injected `formfield_callback=None` at top level,
  clobbering it ⇒ legacy result `none`, spec demands `some cb`.

The carried gold proof (`rfl`) fails to typecheck against the buggy impl
(G-DIFF), as confirmed by `lean_verify` exit 1.
