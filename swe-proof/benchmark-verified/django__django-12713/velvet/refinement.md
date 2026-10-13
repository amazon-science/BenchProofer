# refinement.md — django__django-12713

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveWidget` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — A-consumed /
A-reference), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no A-tagged ops** (no
consumed axioms, no deep-model references): the changed behaviour is the
precedence of a caller-supplied widget over a field-computed default, modeled as
a closed `Option`-precedence function of two free inputs; the unchanged
selection chain that produces the default is abstracted to the free input
`computedDefault` (R), not a callee with a contract to consume.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The widget-precedence site — `formfield_for_manytomany` (`django/contrib/admin/options.py:242`)

Gold hunk (the behavioural core):
```
-        autocomplete_fields = self.get_autocomplete_fields(request)
-        if db_field.name in autocomplete_fields:
-            kwargs['widget'] = AutocompleteSelectMultiple(db_field.remote_field, self.admin_site, using=db)
-        elif db_field.name in self.raw_id_fields:
-            kwargs['widget'] = widgets.ManyToManyRawIdWidget(db_field.remote_field, self.admin_site, using=db)
-        elif db_field.name in [*self.filter_vertical, *self.filter_horizontal]:
-            kwargs['widget'] = widgets.FilteredSelectMultiple(...)
+        if 'widget' not in kwargs:
+            autocomplete_fields = self.get_autocomplete_fields(request)
+            if db_field.name in autocomplete_fields:
+                kwargs['widget'] = AutocompleteSelectMultiple(...)
+            elif db_field.name in self.raw_id_fields:
+                kwargs['widget'] = widgets.ManyToManyRawIdWidget(...)
+            elif db_field.name in [*self.filter_vertical, *self.filter_horizontal]:
+                kwargs['widget'] = widgets.FilteredSelectMultiple(...)
```

| # | Solution.lean impl op (`resolveWidget`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `provided : Option Widget` | `kwargs.get('widget')`; present iff `'widget' in kwargs` | R | widget-or-absent ↔ `Option Widget` (mapping.md §2). The guard `'widget' not in kwargs` ↔ `provided.isNone`. G-CONF bridges via the `kwargs` dict membership. |
| A2 | param `computedDefault : Option Widget` | the widget the UNCHANGED `if/elif/elif` selection chain (autocomplete / raw_id / filter) would assign; `none` when no branch fires | R | the chain is unchanged by the patch and only computes WHICH default applies; its net assignment ↔ `computedDefault` (mapping.md §2, §3). The membership tests + widget constructors are folded into this free input (the django__django-11095 ORACLE-choice precedent). |
| A3 | `let mut widget := provided` then `if widget.isNone then widget := computedDefault` (= `if provided.isNone then computedDefault else provided`) | the added `if 'widget' not in kwargs:` guard wrapping the chain: the chain (which sets `kwargs['widget'] := computedDefault`) runs only when no widget was supplied; otherwise `kwargs['widget']` keeps the caller's value | I (deep model of the added guard) | the guard is spelled out: run the default-assignment only when `provided.isNone`, else keep `provided`. NOT a consumed axiom — G-CONF validates against the patched control flow. The resolved widget is `kwargs['widget']` after the guarded chain. |

The post-condition pins this exactly:
`out = (if provided.isNone then computedDefault else provided)`. No
implementation that overwrites a caller-supplied widget with the computed
default (the pre-patch bug the issue reports — "does not work when I set widget
param"), or that drops the default when the caller supplied none, can satisfy
it. The discriminating case — `provided = some w`, `computedDefault = some d`,
`w ≠ d` — is exactly the F2P scenario (`formfield_overrides` supplies
`CheckboxSelectMultiple`; the `filter_vertical` field's unchanged chain would
otherwise pick `FilteredSelectMultiple`); the spec requires `out = some w`
(caller wins). `Solution_prepatch.lean` reproduces the unconditional chain
(`if computedDefault.isSome then widget := computedDefault`) and **fails**
`out = (if provided.isNone then computedDefault else provided)` precisely there
(G-DIFF).

## B. No second behavioural site

The change is a single guarded block in one function. The queryset handling
(`if 'queryset' not in kwargs:`) and the help-text wrapping below it are
identical pre- and post-patch and are widget-irrelevant, so they are neither
modeled nor a separate prepatch. (The sibling `formfield_for_foreignkey`, which
already had this `if 'widget' not in kwargs:` guard, is the reference the issue
cites; it is unchanged by this patch and not modeled.)

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operation that genuinely *changed* — gating the
default-widget assignment on the caller not having supplied a widget — is
modeled **deeply** (the `Option`-precedence `if provided.isNone then …`), not
behind an axiom about the function under change. There is **no axiomatized
callee** and **no deep-model reference** (`meta.json axioms = []`,
`deep_model_references = []`; G-AX skipped): the widget constructors and the
field-membership tests are unchanged and abstracted to the free input
`computedDefault` (an R refinement, A2), not pre-existing callees with contracts
to consume.

## D. verify(Solution) ⇒ resolved

`resolveWidget` verifies only if its output is
`if provided.isNone then computedDefault else provided` (A3): the caller's widget
exactly when supplied, the computed default otherwise. By R (`kwargs.get('widget')`
↔ `provided`; the unchanged chain's net assignment ↔ `computedDefault`; the
`'widget' not in kwargs` guard ↔ `provided.isNone`) the verified method equals
the patched `formfield_for_manytomany`'s widget choice on every configuration.
By G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour on ≥10⁵
inputs (and diverges from the pre-patch unconditional overwrite, confirming
discrimination on the F2P case). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The sole trust point is refinement fidelity (this doc +
G-CONF); there is no axiom-soundness trust point (no axioms).
