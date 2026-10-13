# refinement.md — django__django-11790

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`configureFieldLimit` `do` block and the `resolveLimit` pure model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement;
state the bijection), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
section 4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The length-configuration block — `AuthenticationForm.__init__` (`django/contrib/auth/forms.py:193-196`)

Gold hunk:
```
- self.fields['username'].max_length = self.username_field.max_length or 254
+ username_max_length = self.username_field.max_length or 254
+ self.fields['username'].max_length = username_max_length
+ self.fields['username'].widget.attrs['maxlength'] = username_max_length
```

| # | Solution.lean impl op (`configureFieldLimit`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `modelLimit : Option Nat` | `self.username_field.max_length` (read at `forms.py:193-194`) | R | `int`/`None` ↔ `Option Nat` (mapping.md section 2). The read is of an unchanged accessor; supplied as a free input. |
| A2 | `let limit := match modelLimit with \| some n => if n = 0 then 254 else n \| none => 254` (≡ `resolveLimit modelLimit`) | `username_max_length = self.username_field.max_length or 254` | R + I | the `x or 254` Python truthiness selection (`None`→254, `0`→254, positive `n`→`n`) transliterated; identical control flow, refined by the `Option Nat` bijection. G-CONF runs the real `or` against `resolveLimit`. |
| A3 | `result := { field with maxLength := some limit }` | `self.fields['username'].max_length = username_max_length` | R + I | assign the derived limit to the field's enforced-limit facet. `BoundedField.maxLength` ↔ `field.max_length` (mapping.md section 2). |
| A4 | `result := { result with widgetMaxLength := some limit }` | `self.fields['username'].widget.attrs['maxlength'] = username_max_length` | R + I | assign the SAME derived limit to the rendered-control facet. `BoundedField.widgetMaxLength` ↔ `widget.attrs['maxlength']`. **This is the line the regression dropped**; the post-state pins it via the second `ensures`. |
| A5 | `field` is read-only (not `mut`); only `result`'s two length facets change | the patch overwrites `max_length` and inserts `maxlength`; no other field attribute is touched | R (frame) | directive 5: `field` is not `mut`; the result is a fresh value differing from `field` in exactly the two length facets (`BoundedField` carries only those). Other attributes (label, unrelated widget attrs) are out of frame and unchanged. |

Discriminating content of the change — the rendered-control limit
(`widget.attrs['maxlength']`) must be set to the same derived limit — lives in
the second postcondition `result.widgetMaxLength = some (resolveLimit
modelLimit)`. The pre-patch set only `max_length` and never touched the widget
attribute; `Solution_prepatch.lean` reproduces that (sets `maxLength` only) and
**fails** the `widgetMaxLength` clause (G-DIFF). This is the exact F2P
assertion added by the test patch:
`form.fields['username'].widget.attrs.get('maxlength') == <limit>`.

## B. No axioms, no A-references

There is no `axiom` and no deep-model A-reference. The only value the routine
consumes from outside (`self.username_field.max_length`) is read by an unchanged
accessor the patch does not modify; it is taken as the free input `modelLimit`,
not axiomatized. `axiom_check.py` (G-AX) is `status=skip` accordingly
(mapping.md section 3). The soundness of that input read and the `x or 254`
selection is covered by G-CONF (real assignment block) + G-RESOLVE.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — additionally
recording the derived limit on the rendered control — is modeled **directly** by
the `widgetMaxLength` assignment (A4) and pinned by the second postcondition,
not hidden behind an axiom. There is no consumed axiom about the function under
change, and no inexpressible op.

## D. verify(Solution) ⇒ resolved

`configureFieldLimit` verifies only if BOTH the enforced-limit facet (A3) and
the rendered-control facet (A4) equal `some (resolveLimit modelLimit)`. By R
(`Option Nat ↔ int|None`, the `resolveLimit ↔ x or 254` bijection, the two
facet ↔ attribute bindings) the verified routine equals the gold assignment
block on the configured-limit domain; by G-CONF the R/I transliteration agrees
with `patch.diff`'s behaviour on ≥10⁵ inputs; G-AX is vacuous (no callee
contract). Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
The sole trust point is refinement fidelity (this doc, G-EQ + G-CONF); there is
no axiom-soundness trust point for this bundle.
