# refinement.md — django__django-12325

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`collectParentLinks` `do` block and the `selectRef`/`collectLinks` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** / **A-reference** (axiomatized / deep-modeled callee), or **I**
(identical concrete op). EVERY step is R, A, or I; there is no kind-3
(inexpressible-changed-op) step.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative and structural facts by **G-AX** + **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The collection site — `ModelBase.__new__` (`django/db/models/base.py:194-207`)

Gold hunk:
```
  for field in base._meta.local_fields:
-     if isinstance(field, OneToOneField):
+     if isinstance(field, OneToOneField) and field.remote_field.parent_link:
          related = resolve_relation(new_class, field.remote_field.model)
          parent_links[make_model_tuple(related)] = field
```

| # | Solution.lean impl op (`collectParentLinks`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `refs : List Ref` | the sequence of `OneToOneField`s scanned by `for field in base._meta.local_fields` (filtered to `isinstance(field, OneToOneField)`) | R | `OneToOneField` list ↔ `List Ref` (mapping.md §2). G-CONF bridges via the real `_meta.local_fields`. |
| A2 | `selectRef m f = if f.isLink then (set m[f.target] := f) else m` | `if isinstance(field, OneToOneField) and field.remote_field.parent_link: parent_links[key] = field` | R + I | the **added** `and field.remote_field.parent_link` guard ↔ the `if f.isLink then … else m` filter (R: `parent_link` bool ↔ `isLink`); the `parent_links[key] = field` write ↔ the map overwrite under `f.target` (I, last-writer-wins). This is the single behavioral change. |
| A3 | `f.target` (the map key) | `make_model_tuple(resolve_relation(new_class, field.remote_field.model))` | R | the referenced-ancestor key. `resolve_relation`/`make_model_tuple` are unchanged callees that only compute the key; the abstraction treats `target` as an opaque ancestor identity (`Nat`). G-AX checks the metaclass's keying agrees per ancestor. |
| A4 | the `while` fold over `refs`, accumulating `result` | the `for field in …:` loop accumulating `parent_links` | I | concrete loop, transliterated by G-CONF (forward fold ↔ left-to-right scan). |
| A5 | returned `LinkMap` `out` | the populated `parent_links` dict | R | `Nat → Option Ref` ↔ `dict[key]=field` (mapping.md §2). |

The discriminating content of the change — a non-`parent_link` `OneToOneField`
must NOT be selected as the ancestor's identity link — lives in `selectRef`'s
`if f.isLink` guard and is pinned by the postcondition
`∀ k g, out k = some g → g.isLink = true` (ensures_2). The pre-patch skeleton
records every reference unconditionally (omits the `isLink` guard);
`Solution_prepatch.lean` reproduces that and **fails** ensures_2 / the functional
equality `out k = collectLinks refs k` (G-DIFF).

## B. The dead-raise removal — `Options._prepare` (`django/db/models/options.py`)

Gold hunks: the `from … import ImproperlyConfigured` is dropped, and inside
`_prepare`, after promoting the first parent link to the pk, the guard
```
- if not field.remote_field.parent_link:
-     raise ImproperlyConfigured('Add parent_link=True to %s.' % field)
```
is deleted.

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | postcondition `∀ k g, out k = some g → g.isLink = true` (ensures_2) | the deleted `if not field.remote_field.parent_link: raise ImproperlyConfigured(...)` | I (behavior-neutral, justified by the spec) | `_prepare` promotes `field = next(iter(self.parents.values()))`. Every field in `self.parents` (= `parent_links` from site A) now satisfies `parent_link == True`, by **exactly** ensures_2 / A2's filter. So the deleted guard's condition `not field.remote_field.parent_link` is **never** true after the site-A fix — the raise is dead code. Its removal changes no observable behavior; it only stops the spurious error the issue reports. |

No separate failing prepatch for site B: the raise is unreachable once site A
filters to `parent_link` fields, so removing it is behavior-neutral and a prepatch
that kept it (with the site-A fix) would behave identically on the F2P tests. The
*necessity* of the change is that, without site A, the promoted field could be a
non-`parent_link` field and the guard would fire (the issue's
`ImproperlyConfigured`); site A's prepatch already exercises that discriminator
via ensures_2.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R, A, or I. The one operation that genuinely *changed* — the
`parent_link` filter on the collected one-to-one references — is modeled
**directly** (the `selectRef` `if f.isLink` guard + the `collectLinks` fold, A2),
not hidden behind an axiom. There is **no consumed axiom and no deep-model
reference**: `resolve_relation`/`make_model_tuple` are unchanged callees that only
compute the opaque key `target`, not modeled as oracles. G-AX validates the
structural layout facts (the per-ancestor keying and the `parent_link` flag
reading) against the real metaclass.

## D. verify(Solution) ⇒ resolved

`collectParentLinks` verifies only if its output equals the filtered selection
`collectLinks refs` (ensures_3) AND every selected entry is an explicit identity
link (ensures_2, `g.isLink = true`) filed under exactly the ancestor it targets
(ensures_1). By R (`OneToOneField` list ↔ `List Ref`, `parent_link` ↔ `isLink`,
`parent_links` dict ↔ `LinkMap`) and the unchanged downstream selection/synthesis
step (mapping.md §2.1), the verified selection equals the patched metaclass's
`parent_links` on the tested classes; by B1 the ensures_2 guarantee makes the
deleted `ImproperlyConfigured` raise dead, so the options.py hunk is
behavior-neutral. By G-AX the model's keying + flag reading agree with the real
metaclass; by G-CONF the R/I transliteration agrees with `patch.diff`'s
`child._meta.parents` behaviour on ≥10⁵ fuzzed field configurations. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The only trust point
is refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms.
