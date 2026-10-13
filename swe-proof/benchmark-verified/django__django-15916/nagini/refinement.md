# refinement.md — django__django-15916

The operation-by-operation correspondence between `model.py`'s implementation
(the `declared_form_callback` / `factory_form_callback` impl regions and the
deep `resolve_attr` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** when
the proof uses the axiom's `Ensures`, **A-reference** when a deep model is
validated == the real callee/semantics by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change (three coupled hunks, `django/forms/models.py`)

```
# (h1) ModelFormOptions.__init__  -- make the builder a first-class option:
+ self.formfield_callback = getattr(options, "formfield_callback", None)

# (h2) ModelFormMetaclass.__new__ -- drop the bases/attrs lookup, read it
#      from the options object instead:
- base_formfield_callback = None
- for b in bases:
-     if hasattr(b, "Meta") and hasattr(b.Meta, "formfield_callback"):
-         base_formfield_callback = b.Meta.formfield_callback
-         break
- formfield_callback = attrs.pop("formfield_callback", base_formfield_callback)
  ...
-     formfield_callback,            # passed to fields_for_model
+     opts.formfield_callback,

# (h3) modelform_factory -- stop injecting an overriding class attribute:
- form_class_attrs = {"Meta": Meta, "formfield_callback": formfield_callback}
+ form_class_attrs = {"Meta": Meta}
```

The single observable behaviour both FAIL_TO_PASS tests pin: *which builder
drives `fields_for_model`* (it determines each field's widget type —
`Textarea` for the custom callback, the model default otherwise).

## A. The directly-declared site — `declared_form_callback` (h1 + h2)

| # | model.py impl op (`declared_form_callback`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `meta_own, meta_inherited: int` | the form's inner `Meta`/options object `formfield_callback` (own) + the value reachable through `Meta`'s bases (inherited) | R | builder callable / `None` ↔ int identity code (`0` == none); `Meta`-attribute-with-inheritance ↔ `(own, inherited)` pair (mapping.md §2). |
| A2 | `stored = resolve_attr(meta_own, meta_inherited)` | `opts.formfield_callback`, where `opts = ModelFormOptions(getattr(new_class, "Meta", None))` and the option is `getattr(options, "formfield_callback", None)` (h1) read at `:311` (h2) | A-reference + I | the selection is modelled **deeply**: `resolve_attr` IS `getattr(meta, "formfield_callback", None)` over `Meta`'s MRO (own shadows inherited, default when absent). No consumed axiom — the deep model is validated == real Python resolution by axiom_check.py / G-AX (mapping.md §3.1). The `return stored` driving field construction is identical control flow. |

The discriminating content: a builder declared on the form's **own** `Meta`
(`meta_own != 0`) is now selected (`Result() == meta_own`). Pre-patch (h2),
the metaclass read `attrs.pop("formfield_callback", base_formfield_callback)` —
the class-level attribute (absent when the builder is only in `Meta`) falling
back to a **base form class's** `Meta`, never the current class's own `Meta`.
`model_prepatch.py` reproduces that (`attrs_level = 0`; fall back to
`meta_inherited`, dropping `meta_own`) and **fails** the postcondition
`Result() == resolve_attr(meta_own, meta_inherited)` on the `meta_own != 0,
meta_inherited == 0` witness — exactly `test_custom_callback_in_meta` (G-DIFF).

## B. The factory site — `factory_form_callback` (h2 + h3)

| # | model.py impl op (`factory_form_callback`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | params `passed, base_meta_own, base_meta_inherited: int` | `formfield_callback` arg of `modelform_factory` + the base `form.Meta`'s builder (own + its parent) | R | same int / `(own, inherited)` refinement as A1 (mapping.md §2). |
| B2 | `produced_inherited = resolve_attr(base_meta_own, base_meta_inherited)` | the produced `Meta = type("Meta", (form.Meta,), attrs)` inheriting the base form's `Meta.formfield_callback` | A-reference + I | `Meta` is built inheriting `form.Meta`, so the base builder is reachable; modelled by `resolve_attr` over the base pair (mapping.md §3.1). |
| B3 | `produced_own = passed` (0 when none) | `if formfield_callback: Meta.formfield_callback = staticmethod(formfield_callback)` (`:633-634`, set **only when truthy**) | I + R | the passed builder becomes the produced `Meta`'s own attribute exactly when truthy; `staticmethod` is identity on builder identity (mapping.md §2). When `passed == 0` (none given) the produced `Meta` sets nothing of its own → inherits. |
| B4 | `stored = resolve_attr(produced_own, produced_inherited)` | `opts.formfield_callback` read by the metaclass (h2) for the produced class; **no** overriding `form_class_attrs["formfield_callback"]` (h3) | A-reference + I | post-fix the produced form carries no class-level `formfield_callback` to override the options read, so the metaclass selects the resolved options builder. `resolve_attr(passed, base)` IS that resolution (validated by G-AX). |

The discriminating content: when the factory is given **no** builder
(`passed == 0`) but the base form's `Meta` carries one (`base_meta_own != 0`),
the produced class (and any subclass) still selects that builder
(`Result() == base_meta_own`). Pre-patch (h3) put
`form_class_attrs["formfield_callback"] = formfield_callback` (= `None` here),
which the pre-patch metaclass `attrs.pop("formfield_callback", ...)` (h2) read
and used, overriding the base `Meta` builder with `None`. `model_prepatch_2.py`
reproduces that (`stored = passed`, the injected possibly-`0` value always
wins) and **fails** `Result() == resolve_attr(passed, resolve_attr(...))` on
the `passed == 0, base_meta_own != 0` witness — exactly
`test_custom_callback_from_base_form_meta` (G-DIFF). axiom_check.py also
exercises the further-subclass (`InheritedForm`) resolution.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — selecting the builder via the form's own options-object attribute
resolution rather than a `bases`/`attrs` lookup — is modelled **deeply**
(`resolve_attr`, the spelled-out own-shadows-inherited lookup consumed in both
modeled functions, an **A-reference**), not hidden behind an axiom about the
function under change. There is **no consumed `@ContractOnly` axiom**: no
unchanged opaque callee is relied on inside a contract. `resolve_attr` appears
only as the **A-reference** that G-AX validates against the real Python
`getattr`/MRO resolution the patch performs.

## D. verify(model) ⇒ resolved

`declared_form_callback` / `factory_form_callback` verify only if the selected
builder equals the options-resolved builder — `meta_own` when declared on the
form's own options (A), and the base form's builder when the factory is given
none (B). By R (builder ↔ int identity; `Meta`-attribute-with-inheritance ↔
`(own, inherited)`; `staticmethod`/per-field-fold identities) the verified
selection equals the gold patch's `opts.formfield_callback` on the tested
inputs; by G-AX the deep model `resolve_attr` equals the real Python attribute
resolution (A-reference) on the two F2P scenarios + 40002 fuzz resolutions.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited language-semantics reference — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: deep-model/axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
