# mapping.md — django__django-12325

Symbol binding, the Lean↔Python type bijection (used by G-CONF and G-AX), callee
provenance, and the pinned G-CONF fuzz seed. Spec provenance: **cold** (derived
only from `problem_statement`, the gold `patch`, and the repo source at
`base_commit = 29c126bb349526b5f1cd78facbe9f25906f18563`).

Repo files under change: `django/db/models/base.py` and
`django/db/models/options.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collectParentLinks (refs : List Ref)` | the `parent_links = {}` collection loop inside `ModelBase.__new__` — `django/db/models/base.py:194-207` | the modeled changed function: build the per-ancestor identity-link selection (`parent_links`) from the class's declared `OneToOneField`s |
| `Ref` | one `OneToOneField` instance scanned at `base.py:202-207` (`field`, `field.remote_field.parent_link`, `field.remote_field.model`) | one declared one-to-one reference |
| `LinkMap` | the `parent_links` dict (`{make_model_tuple(related): field}`) | the per-ancestor identity-link selection |
| `selectRef` / `collectLinks` | the loop body + accumulation (`base.py:202-207`) | the per-reference fold building `parent_links` |

No callee is axiomatized: the change is a pure data-flow over the scanned field
list, modeled DIRECTLY by `selectRef`/`collectLinks` (refinement.md §C). The
unchanged helpers `resolve_relation`/`make_model_tuple` only compute the *key*
(`target`) of each reference; they are not modeled — `target` is an opaque
ancestor identity in the abstraction (a `Nat`), and G-AX validates that the
metaclass's per-target keying agrees with the model's.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the class's declared `OneToOneField`s, in declaration order (`base._meta.local_fields` filtered to `isinstance(field, OneToOneField)`) | `refs : List Ref` | the *i*-th scanned `OneToOneField` ↔ `refs[i]` |
| `field.remote_field.parent_link` (a `bool`) | `Ref.isLink : Bool` | `True ↔ true` |
| `make_model_tuple(resolve_relation(new_class, field.remote_field.model))` — the referenced ancestor's identity key | `Ref.target : Nat` | distinct ancestors ↔ distinct `Nat`s; the F2P domain has one ancestor `Place`, so `target = 0` throughout |
| the field's own identity (its `name`) | `Ref.fid : Nat` | distinct fields ↔ distinct `Nat`s; lets two references to the same ancestor stay distinguishable |
| `parent_links` dict `{key: field}` | `LinkMap = Nat → Option Ref` | `parent_links.get(key)` ↔ `linkMap key`; absent key ↔ `none` |
| `dict[key] = field` (last assignment wins for a repeated key) | `selectRef` overwrite under `f.target` | Python dict last-writer-wins ↔ the `if k = f.target then some f` overwrite |

The patch's single edit — adding `and field.remote_field.parent_link` to the
`isinstance(field, OneToOneField)` guard — is exactly `selectRef`'s
`if f.isLink then … else m` filter: a reference with `isLink = false` is dropped
from the selection.

### 2.1 The downstream observable (unchanged scaffolding, I-tagged)

`parent_links` is consumed immediately after, at `base.py:236-268`, to set
`new_class._meta.parents[base]`: if the ancestor's key is in `parent_links`, that
field is used; otherwise (and not a proxy) an auto-created
`<modelname>_ptr` `OneToOneField(parent_link=True)` is synthesized. This
selection step is **unchanged** by the patch (an **I** op). The end-to-end
observable G-CONF compares is therefore `child._meta.parents[Place].name`:

* selection non-empty for the ancestor → the selected field's `name`;
* selection empty → the synthesized `'<modelname>_ptr'`.

And `_meta.pk.name` (set in `options.py:_prepare`) equals
`_meta.parents[Place].name` for single-ancestor MTI (the first parent link is
promoted to pk), so the parents observable subsumes pk.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

**This bundle has NO consumed axiom and NO deep-model reference.** The behavior
is a data-flow over the scanned field list, modeled directly. G-AX
(`axiom_check.py`) therefore validates the *structural layout facts the direct
model depends on* — the R-bijection's soundness — by executing the REAL Django
metaclass machinery in-container at **base_commit (unpatched)**:

1. **Flag reading is faithful** (`Ref.isLink ↔ field.remote_field.parent_link`):
   a `OneToOneField` declared `parent_link=True` reads `parent_link is True`; a
   plain one reads `parent_link is False`. So the model's `isLink = false` for a
   non-link reference is sound.
2. **Per-ancestor keying is faithful and injective on ancestors**
   (`Ref.target : Nat`, distinct ancestors → distinct `Nat`s): for the fields a
   child declares, `make_model_tuple(resolve_relation(child, f.remote_field
   .model))` (the dict key written under) is equal for two refs iff they target
   the same ancestor, and distinct ancestors get distinct keys.
3. **Scan order is declaration order** (`refs[i] ↔ i-th declared field`): the
   `OneToOneField`s scanned (`base._meta.local_fields` filtered to
   `isinstance(field, OneToOneField)`) appear in declaration order, so the
   left-to-right fold matches the loop's last-writer-wins semantics.

(The *end-to-end* equality of the model's `collectLinks` selection with the
patched metaclass's `parent_links` — and the consequent disappearance of the
`ImproperlyConfigured` raise — is the **patched** observable, validated by
**G-CONF** end-to-end on ≥10⁵ configs and by **G-RESOLVE**; G-AX validates only
the unpatched-invariant layout facts the model is built on, never re-running the
function under spec.)

Imports only `django` (the module under change) + the standard library. Exit 0
iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12325`**. The R/I shadow
it builds transliterates `selectRef`/`collectLinks` + the unchanged
selection/synthesis step (§2.1) to Python over the real `OneToOneField` layout,
and compares `child._meta.parents[Place].name` against the patched metaclass's
real output over the fuzzed field configurations. There are NO A-tagged ops, so
the shadow is pure R/I.
