# mapping.md — django__django-15916

base_commit: `88e67a54b7ed0210c11523a337b498aadb2f5187`
file under change: `django/forms/models.py`

## Behavior under spec

A model-form class is built by a metaclass. During construction it must decide
**which `formfield_callback` the class uses** to build its form fields. The
fixed behavior: the callback is taken from the class's *options block*
(`Meta.formfield_callback`, resolved through options inheritance); when the
options block declares none, no callback is used. Previously the resolution
ignored the options block and instead consulted a top-level class attribute
(falling back to a base class's options block), which (a) ignored a callback
declared in the class's own options block and (b) could be clobbered by a
`None` default injected by the factory helper.

## Symbol bindings (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_resolveModelFormCallback` | callback-selection inside `ModelFormMetaclass.__new__` | `django/forms/models.py:259-266, 311` |
| `CallbackConfig.metaCallback` | `getattr(opts, "formfield_callback", None)` where `opts = ModelFormOptions(new_class.Meta)` | post-patch `:255`, used `:301` |
| `CallbackConfig.attrsHasCallback` / `attrsCallback` | `attrs.pop("formfield_callback", …)` — key presence and value | pre-patch `:266` |
| `CallbackConfig.baseMetas` | the `for b in bases:` scan reading `b.Meta.formfield_callback` | pre-patch `:260-264` |
| (factory) | `form_class_attrs = {"Meta": Meta}` (was `{… , "formfield_callback": formfield_callback}`) | `modelform_factory` `:639` |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX

| Lean | Python |
|---|---|
| `Callback := Nat` (opaque id; distinct callbacks ⇒ distinct ids) | a `formfield_callback` callable (identity matters, not behavior) |
| `Option Callback` `none` | absence of a callback (`None`) |
| `CallbackConfig.metaCallback` | `getattr(BuiltMetaClass, "formfield_callback", None)` (resolved via the inner-`Meta` MRO) |
| `attrsHasCallback : Bool` | `"formfield_callback" in attrs` (the class body, not the inner `Meta`) |
| `attrsCallback : Option Callback` | `attrs.get("formfield_callback")` when present |
| `baseMetas : List (Option (Option Callback))` | per base in `bases`: `None` = base lacks `Meta`/the attr; `some v` = `b.Meta.formfield_callback = v` (`v` itself may be `None`) |
| result `Option Callback` | the callback passed to `fields_for_model` to build `base_fields` |

## Callee provenance / flags

No unchanged callee property is consumed by the proof. The downstream callee
`fields_for_model` (and `Field.formfield`) is **unchanged** by the patch and is
NOT modeled here: the patch alters only *which callback value is selected*, not
how fields are built from it. There is therefore no `opaque` callee signature
and no consumed/`_prop` axiom. (axiom_check.py is a skip stub.)

## G-CONF fuzz seed

`SBL_CONF_SEED = 15916` (pinned; see conformance_check.py).
