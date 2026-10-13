# refinement.md — django__django-12193

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`computeContextAttrs` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The mapping-assembly site — `CheckboxInput.get_context` (`django/forms/widgets.py:524–529`)

Gold hunk:
```
     def get_context(self, name, value, attrs):
         if self.check_test(value):
-            if attrs is None:
-                attrs = {}
-            attrs['checked'] = True
+            attrs = {**(attrs or {}), 'checked': True}
         return super().get_context(name, value, attrs)
```

| # | Solution.lean impl op (`computeContextAttrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `attrs : List (String × Bool)` (the caller's attribute mapping) | the `attrs` parameter of `get_context` | R | caller-owned attribute `dict` → its touched-key-space association list with `Bool` values; the `'checked'` key ↔ the `"checked"` association (mapping.md §2). G-CONF bridges via the real `attrs` dict and the produced context's widget attrs. |
| A2 | param `checked : Bool` | `self.check_test(value)` (the `if` guard) | R | the affirmative observation → `Bool`; `checked = true` ↔ `bool(self.check_test(value))` (default `boolean_check`). G-CONF computes the same `boolean_check` to bridge it (mapping.md §3). |
| A3 | `let effective := if checked then withChecked attrs else attrs` | `if self.check_test(value): attrs = {**(attrs or {}), 'checked': True}` | I | identical guarded data flow: when the control is affirmative the onward mapping is the caller's mapping with the `"checked"` entry installed true (`withChecked` = the dict-spread `{**attrs, 'checked': True}`, mapping.md §2); otherwise it is the caller's mapping itself. The dict-spread builds a SEPARATE value — modeled as binding a fresh `effective` from `attrs` rather than writing `attrs`. |
| A4 | (the `if attrs is None: attrs = {}` normalization, removed by the patch) | the deleted `if attrs is None:` lines | I (absorbed) | the model carries `attrs` as a concrete mapping; `None ⇒ {}` ↔ the empty list `[]`. The patch folds this normalization into the spread `(attrs or {})`, which is value-preserving for the touched key space — `withChecked [] = [("checked", true)]` equals `{**{}, 'checked': True}`. No separate branch is observable, so it is not a distinct impl op. |
| A5 | `return effective` | the `attrs` value passed to `super().get_context(name, value, attrs)` | R | the onward mapping whose entries drive this rendering's widget context; `effective : List (String × Bool)` ↔ the `attrs` argument reaching the base method (read back by G-CONF from `ctx['widget']['attrs']`, base widget attrs empty ⇒ merge is identity on the touched keys). |
| A6 | `ensures attrs = attrsOld` (the caller's mapping returned unchanged) | the **effect of rebinding** `attrs = {**(attrs or {}), 'checked': True}` instead of `attrs['checked'] = True`: the spread builds a new dict, so the caller's `dict` object is never written and survives the call exactly as it was | I (frame) | the whole point of the gold one-liner. Pre-patch, `attrs['checked'] = True` mutated the caller's shared `dict` in place, leaking the flag into every later rendering that reused it; post-patch the spread leaves the caller's `dict` intact. Directive-5 frame: pinned to the entry value `attrsOld`. |

Discriminating content of the change — the **caller's attribute mapping must
survive the operation unchanged** so a later element rendered from the same
mapping is not forced affirmative — lives in `ensures attrs = attrsOld` (model)
⇔ the rebinding to a fresh dict that diverts the `'checked'` write away from the
caller's shared object (real). The pre-patch code mutates the caller's mapping
directly; `Solution_prepatch.lean` reproduces that (impl is
`attrs := if checked then withChecked attrs else attrs; return attrs`, writing
the carrier) and **fails** the frame clause on exactly the affirmative case — the
unsolved goal is
`(if checked = true then withChecked attrsOld else attrsOld) = attrsOld`, i.e.
the affirmative flag leaking back into the caller's mapping (G-DIFF).

## B. The `mut`-frame discipline (directive 5)

This bundle IS a directive-5 instance: the bug is an unframed write to a
caller-owned, read-only-by-contract attribute mapping.

- `attrs` is declared `mut` (the long-standing code reaches for the caller's
  mapping as the thing to augment), but its post-state is pinned **exactly to its
  entry value**: `ensures attrs = attrsOld`. This closes the Lean analogue of the
  full-permission hole — an impl that wrote the `"checked"` flag back onto `attrs`
  (the pre-patch bug) violates the frame. The onward mapping is delivered through
  the SEPARATE return carrier `effective`, never by mutating the caller's input.
- `checked` is NOT `mut`: the operation reads the affirmative observation and
  never alters it (directive 5 — a read-only input must not be `mut`).
- `effective`'s post-state is pinned exactly by `ensures effective = if checked
  then withChecked attrsOld else attrsOld` — note it is computed against
  `attrsOld`, the caller's entry mapping, so the spec ties the onward mapping to
  the mapping observed BEFORE any write, leaving no room for an impl to observe a
  self-inflicted mutation.

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom** and **no A-reference deep
model of a foreign callee**: the changed operation reads one affirmative
observation and the caller's mapping and produces the onward mapping, calling
nothing whose contract the proof must consume (mapping.md §3). `self.check_test`
is taken as the read-only input `checked` (and G-CONF re-computes it on the
Python side); the dict-spread `{**attrs, 'checked': True}` is modeled directly as
`withChecked` (an **I** leg); `super().get_context` is downstream of the boundary
and unchanged. Hence the `axioms` region is empty, `deep_model_references` is
empty, and G-AX is skipped. The one operation that genuinely *changed* —
rebinding to a fresh dict so the caller's mapping is left intact — is modeled
**directly** as the separate-value + frame discipline (A3 + A6), an **I** leg
transliterated by G-CONF.

## D. verify(Solution) ⇒ resolved

`computeContextAttrs` verifies only if (A6) `attrs = attrsOld` — the caller's
mapping is returned exactly as received — and (A3/A5) `effective = if checked
then withChecked attrsOld else attrsOld` — the onward mapping carries the
`"checked"` flag exactly when the control is affirmative, computed against the
caller's entry mapping. By R (caller `dict` ↔ touched-key `List (String × Bool)`,
`check_test` truth ↔ `checked : Bool`, the `attrs` reaching the base method ↔
`effective`) the verified method equals the patched block's effect on the tested
inputs; by G-CONF the R/I transliteration of the separate-value + frame
discipline agrees with `patch.diff`'s real behaviour (real `CheckboxInput`, real
caller-owned `attrs` dict, real onward context attrs) on ≥10⁵ inputs, including
the F2P case `attrs={'checked': False}` + affirmative `value`. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The only trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (G-AX
skipped).
