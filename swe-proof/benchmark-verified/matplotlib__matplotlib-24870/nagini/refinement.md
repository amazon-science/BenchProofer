# refinement.md — matplotlib__matplotlib-24870

The operation-by-operation correspondence between `model.py`'s implementation
(the `choose_default_levels` impl region and the consumed `auto_levels` axiom)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` — checked — and is the real correctness oracle, G-RESOLVE).

## A. The behavioural delta — default level selection (`_process_contour_level_args`)

Gold hunk (`lib/matplotlib/contour.py`, the `self.levels is None` block):
```
-            if len(args) == 0:
-                levels_arg = 7  # Default, hard-wired.
-            else:
+            if args:
                 levels_arg = args[0]
+            elif np.issubdtype(z_dtype, bool):
+                if self.filled:
+                    levels_arg = [0, .5, 1]
+                else:
+                    levels_arg = [.5]
+            else:
+                levels_arg = 7  # Default, hard-wired.
```
then `self.levels = np.asarray(levels_arg, np.float64)` (for the list cases);
for a line contour the subsequent interior filter `(levels > zmin) & (levels <
zmax)` keeps the level only if it is strictly inside the range.

| # | model.py impl op (`choose_default_levels`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `has_explicit: bool`; spec fixes `not has_explicit` | `if args:` … `else` (the no-explicit-levels branch) | R/I | the model specifies the `levels is None` ∧ no-explicit-args branch, the one the F2P test exercises and the patch changes; the boolean refines `len(args) == 0`. |
| A2 | parameter `two_valued: bool` | `np.issubdtype(z_dtype, bool)` | R | a boolean numpy field has exactly two distinct sample values; `two_valued` is that dtype predicate (mapping.md §2). The behaviour depends only on this predicate. |
| A3 | parameter `filled: bool` | `self.filled` | I | identical boolean. |
| A4 | line + two-valued: `result = [mid]` | `levels_arg = [.5]` then `np.asarray(..., float64)` | R | `mid` is the value equidistant from `zmin`/`zmax` (pinned `mid - zmin == zmax - mid`); for the bool range `[0,1]` it is `.5`. The single-element list ↔ `[.5]`. The model's `zmin < mid < zmax` postcondition captures that the level survives the line-contour interior filter — witnessed by the real `plt.contour(bool).levels == [.5]` (axiom_check / mapping §2). |
| A5 | filled + two-valued: `result = [zmin, mid, zmax]` | `levels_arg = [0, .5, 1]` then `np.asarray(..., float64)` | R | for the bool range `zmin=0, mid=.5, zmax=1`, so `[zmin, mid, zmax]` ↔ `[0, .5, 1]`. The model's `len >= 2` ∧ strict ordering postcondition captures that this is a valid filled spec (filled requires ≥2 levels) — witnessed by the real `plt.contourf(bool).levels == [0, .5, 1]`. |
| A6 | not two-valued: `result = list(auto_levels(zmin, zmax))` | `levels_arg = 7` ⇒ `self._autolev(7)` | A-consumed | the ordinary multi-level default for a continuous field is the UNCHANGED delegate `_autolev`/`MaxNLocator`; the proof consumes only `len(auto_levels) > 1` (the `not two_valued` postcondition), scoped to a WELL-RESOLVED range (the axiom/caller `Requires`: span clears `1e-6` absolute and `1e-9` of each extent's magnitude). The scoping is sound and necessary — the real `MaxNLocator` selection collapses to a single tick at an unresolvable range (measured in-container: `(1e-300,2e-300) -> [1e-300]`), which the unscoped axiom would have over-claimed. G-AX confirms the real default yields >1 level on every well-resolved input and the collapse witnesses are guard-excluded (mapping §3.1, axiom_check.py, RC=0 in the 3.6 image). This branch is unchanged by the patch (the `7` default is preserved for non-bool fields); the well-resolved range covers the tested `[0,1]` bool range with enormous margin, so the discrimination (A1-A5) is untouched. |

The discriminating content of the change — a two-valued field defaults to a
SINGLE boundary level (line) / the THREE bracketing levels (filled) instead of
the ordinary multi-level selection — lives in the `two_valued` branches (model)
⇔ the new `elif np.issubdtype(z_dtype, bool)` block (real). `model_prepatch.py`
reproduces the pre-patch behaviour (the two-valued case is never special-cased;
the default is always the multi-level `auto_levels`) and **fails** the
postcondition `Implies(two_valued and not filled, len(Result()) == 1)` — exactly
the spec sensing the change (G-DIFF). That is the precise behaviour
`test_bool_autolevel` observes (`plt.contour(bool).levels == [.5]`, not the ~8
piled-up default levels).

## B. Supporting plumbing hunks (type/threading — R/I, no behavioural delta)

The remaining gold hunks thread the field's dtype to the selection and stop
coercing `z` to float64 so the boolean dtype survives:

```
# contour.py _contour_args:
-            z = ma.asarray(args[0], dtype=np.float64)        # nargs <= 2
+            z, *args = args
+            z = ma.asarray(z)
-            x, y, z = self._check_xyz(args[:3], kwargs)      # nargs <= 4
+            x, y, z_orig, *args = args
+            x, y, z = self._check_xyz(x, y, z_orig, kwargs)
-        self._process_contour_level_args(args)
+        self._process_contour_level_args(args, z.dtype)
# contour.py _check_xyz: signature unpack; z = ma.asarray(z)  (drop float64 cast)
# tri/_tricontour.py _contour_args: z, *args = args; z = np.ma.asarray(z);
#   self._process_contour_level_args(args, z.dtype)
```

| # | role | tag | justification |
|---|---|---|---|
| B1 | pass `z.dtype` into `_process_contour_level_args` | R | provides the `two_valued` predicate (A2) to the selection; pure data threading, no new behaviour of its own. |
| B2 | drop `dtype=np.float64` from `ma.asarray(z)` / `_check_xyz` | R | preserves the boolean dtype so the `np.issubdtype(z_dtype, bool)` test (A2) can fire; for continuous fields the dtype already was float-like, so `np.asarray(...)`/`np.float64` downstream (`_autolev`, the level cast) is unchanged. Argument-unpacking refactors (`z, *args = args`) are behaviour-preserving rewrites of the previous slicing (`args[0]`, `args[1:]`, `args[:3]`, `args[3:]`). |

These hunks carry no independently-observable behavioural change — they exist to
deliver the dtype to site A. Hence there is **one** behavioural delta and **one**
failing `model_prepatch` (site A), per G-DIFF's "one variant per
independently-fixed behaviour". The tricontour call site is the SAME modeled
selection function `_process_contour_level_args` (TriContourSet inherits
ContourSet); the model's single `choose_default_levels` covers both the
`contour`/`contourf` and `tricontour`/`tricontourf` call sites (the F2P test
checks all four — `[.5]` for both line forms, `[0, .5, 1]` for both filled forms).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— the two-valued default level selection — is modeled **directly** (the
`two_valued` branches producing the single midpoint level / the three bracketing
levels), not hidden behind an axiom about the function under change. The only
consumed axiom, `auto_levels` (**A-consumed**, A6), covers the UNCHANGED
continuous-field default the new code still delegates to for non-bool fields;
the patch does not touch it.

## D. verify(model) ⇒ resolved

`choose_default_levels` verifies only if, for a two-valued field, it returns a
single level equal to the midpoint and strictly inside the range (line, A4) or
the three bracketing levels with the strictly-interior midpoint (filled, A5),
and for a continuous field the unchanged multi-level default (A6). By R (the
boolean/dtype refinements, the `np.asarray(list, float64)` identity on the float
values, `mid` ↔ `.5`) the verified selection equals the gold patch's
`levels_arg` selection on the tested inputs; by G-AX the real continuous-field
default meets the `auto_levels` axiom (A-consumed). The midpoint's strict
interiority is exactly what makes the line level survive the interior filter, so
`self.levels.tolist() == [.5]` (line) and `== [0, .5, 1]` (filled) — the F2P
`test_bool_autolevel` assertions, witnessed against real matplotlib (mapping
§3.1, the host run). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the one audited callee — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
