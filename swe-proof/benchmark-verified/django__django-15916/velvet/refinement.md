# refinement.md — django__django-15916

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `selectFieldCallback` `do` block) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — A-consumed /
A-reference), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The selection site — `ModelFormMetaclass.__new__` (`django/forms/models.py:259`)

The gold patch changes which callback the metaclass passes to `fields_for_model`.

Pre-patch (`django/forms/models.py:260-266`, deleted by the patch):
```python
base_formfield_callback = None
for b in bases:
    if hasattr(b, "Meta") and hasattr(b.Meta, "formfield_callback"):
        base_formfield_callback = b.Meta.formfield_callback
        break
formfield_callback = attrs.pop("formfield_callback", base_formfield_callback)
...
fields = fields_for_model(..., formfield_callback, ...)        # :301 pre-patch
```
Post-patch: `ModelFormOptions.__init__` captures
`self.formfield_callback = getattr(options, "formfield_callback", None)`
(`:256` new line) and the metaclass passes `opts.formfield_callback` (`:301`).

`attrs.pop("formfield_callback", base_formfield_callback)` returns the class-body
attribute when the `formfield_callback` key is present in `attrs` — **even when
its value is `None`** — and otherwise `base_formfield_callback` (the first base
form's `Meta.formfield_callback`). So pre-patch the selected callback is
"class-body value if the key is present, else the base-scan value":
`declaredCallback.getD inheritedCallback`. Post-patch it is the form's own
`Meta`-resolved callback `opts.formfield_callback`: `configCallback`.

| # | Solution.lean impl op (`selectFieldCallback`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `configCallback : Option Nat` | `opts.formfield_callback` (post-patch `fields_for_model` arg, `:301`) | R | the form's own `Meta`-resolved callback ↔ `configCallback` (mapping.md §2): a callback ↔ `some n`, none ↔ `none`. |
| A2 | parameter `declaredCallback : Option (Option Nat)` | `attrs["formfield_callback"]` + its presence (the `attrs.pop` operand, pre-patch `:266`) | R | key absent ↔ `none`; key present with a callback ↔ `some (some n)`; key present with `None` ↔ `some none` (mapping.md §2). Used only by the prepatch skeleton. |
| A3 | parameter `inheritedCallback : Option Nat` | `base_formfield_callback` (pre-patch base-scan, `:260-264`) | R | first base form's `Meta.formfield_callback` ↔ `inheritedCallback` (mapping.md §2). Used only by the prepatch skeleton. |
| A4 | `return configCallback` | post-patch: pass `opts.formfield_callback` to `fields_for_model` | R + I | the post-patch selection is exactly "the form's own `Meta`-resolved callback"; modeled concretely as returning `configCallback`. The two `modelform_factory` hunks are the same selection (mapping.md §1): post-patch the factory's manufactured `Meta.formfield_callback` is read, so the now-dead class-body attr is dropped from `form_class_attrs` — behaviour-neutral given A4. |
| A5 | `out : Option Nat` returned | the callback `fields_for_model` builds fields with | R | observed via the produced field widget class (mapping.md §2); the F2P tests compare `type(field.widget)`. |

The selection is the changed operation; it is modeled **concretely** (`return
configCallback`), so every step is R/I — there is no callee whose contract the
proof consumes (mapping.md §3: zero axioms).

Discriminating content of the change — when the form's own `Meta` resolves to a
callback but the class body either names nothing (so the metaclass would fall to
the base-scan) or names an explicit `None` (so `pop` shadows the base-scan), the
result must still be the form's own `Meta` callback, not the base-scan / `none`.
This lives in clause `ensures out = configCallback` (model) ⇔ passing
`opts.formfield_callback` to `fields_for_model` (real). The pre-patch selected
`declaredCallback.getD inheritedCallback`; `Solution_prepatch.lean` reproduces
that and **fails** that exact clause (G-DIFF) — the goal left unsolved is
`⊢ declaredCallback.getD inheritedCallback = configCallback`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — which of the
three callback sources is selected — is modeled **concretely** (the body
`return configCallback`), not hidden behind an axiom. There are no consumed
axioms and no deep-model references; G-AX has nothing to check (it skips). The
callback sources (`opts.formfield_callback`, the class-body attr, the base-scan)
are the observation functions of the input bijection (mapping.md §2), not axioms.

## C. verify(Solution) ⇒ resolved

`selectFieldCallback` verifies only if its output is the form's own
`Meta`-resolved callback (`configCallback`), regardless of the class-body
attribute or the base offering (A4). By R (`opts.formfield_callback ↔
configCallback`, the source ↔ tag bijection, mapping.md §2) the verified
selection equals the callback the post-patch metaclass passes to
`fields_for_model` on the tested configurations; by G-CONF the R/I
transliteration of the selection agrees with `patch.diff`'s behaviour on ≥10⁵
configurations (the real patched `ModelFormMetaclass` is driven and the
actually-used callback is read off the produced widget class, bridged via
mapping.md §2). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms to trust (G-AX skip).
