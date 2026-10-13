# refinement.md — pydata__xarray-7229

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `rebuildAttrs` `do` block plus the deep `rebuiltCoord` / `rebuiltVar` /
`rebuiltGlobal` / `lookupAttrs` models) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (a deep model validated ==
real callee by G-AX), or **I** (identical concrete op). Every step is R, A, or I.
This bundle uses only **R** and **I** legs (no axioms).

Every leg here is **R/I** and is mechanically refuted by **G-CONF**
(`conformance_check.py`, §4.1) against the patched repo; this narrative is
audited by **G-EQ**. There are **no axioms** in this bundle (no A-consumed, no
A-reference), so it ships **no `axiom_check.py`** and **G-AX skips** (gates.py:
"no axiom_check.py (no axioms in bundle)"). Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The metadata-rebuild site — `where(cond, x, y, keep_attrs)`

Gold hunk (the `keep_attrs is True` configuration), summarized:
```
- if keep_attrs is True:
-     keep_attrs = lambda attrs, context: getattr(x, "attrs", {})   # passed into apply_ufunc → applied to EVERY level
- return apply_ufunc(duck_array_ops.where, cond, x, y, …, keep_attrs=keep_attrs)
+ result = apply_ufunc(duck_array_ops.where, cond, x, y, …, keep_attrs=keep_attrs)
+ if keep_attrs is True:
+     if isinstance(y, Dataset) and not isinstance(x, Dataset):   # promotion
+         result.attrs = {}
+         if getattr(x, "name", None) in result.data_vars:
+             result[x.name].attrs = getattr(x, "attrs", {})
+     else:
+         result.attrs = getattr(x, "attrs", {})
+         for v in getattr(result, "data_vars", []):
+             result[v].attrs = getattr(getattr(x, v, None), "attrs", {})
+     for c in getattr(result, "coords", []):
+         result[c].attrs = getattr(getattr(x, c, None), "attrs", {})
+ return result
```

| # | Solution.lean impl op (`rebuildAttrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | inputs `resVars`, `resCoords`, `promote`, `xName`, `xGAttrs`, `xVars`, `xCoords` | the `result` of `apply_ufunc` (its level names + output type) and the second arg `x`'s levels | R | the unchanged `apply_ufunc` callee supplies the result skeleton (names) and the type; `keep_attrs` controls metadata only, so names are identical pre/post-patch (mapping.md §3.1). `Obj`/`Lvl` ↔ object/level bijection (mapping.md §2). |
| A2 | `rebuiltGlobal promote xGAttrs` (`= 0` if promote else `xGAttrs`) → `out.gattrs` | `result.attrs = {}` (promotion) / `result.attrs = getattr(x,"attrs",{})` (else) | R + I | global metadata token; `{}` ↔ `0`, `x.attrs` ↔ `xGAttrs`. Concrete `if` transliterated by G-CONF. |
| A3 | `rebuiltVar promote xName xGAttrs xVars (resVars[i]!)` for every `i`, via the variable `while` loop | the data-var loop `result[v].attrs = getattr(getattr(x,v,None),"attrs",{})` and the promotion `result[x.name].attrs = getattr(x,"attrs",{})` | R + I | per-variable by-name selection (ordinary) / single source-named fill (promotion); `lookupAttrs` ↔ `getattr(getattr(x,v,None),"attrs",{})` (mapping.md §3.2). The fold over `resVars` is concrete (I), transliterated by G-CONF. |
| A4 | `rebuiltCoord xCoords (resCoords[k]!)` for every `k`, via the coordinate `while` loop | the **always-run** coord loop `result[c].attrs = getattr(getattr(x,c,None),"attrs",{})` | R + I | **the discriminating clause.** Coordinate metadata ALWAYS taken by name from x's equally-named coordinate — never from x's global metadata. `lookupAttrs xCoords name` ↔ `getattr(getattr(x,c,None),"attrs",{})`. This is exactly the bug the issue reports (coord attrs overwritten); the spec pins coord metadata to the by-name selection so a global-stamp impl cannot verify. |
| A5 | `return { gattrs, vars := outVars, coords := outCoords }` | `return result` | R | the rebuilt object; `Obj` ↔ result object (mapping.md §2). |

Discriminating content of the change — coordinate levels take their metadata
from x's equally-named **coordinate** (`rebuiltCoord` / `lookupAttrs xCoords`),
not from x's **global** metadata token. The pre-patch threaded a single
`getattr(x,"attrs",{})` callback through `apply_ufunc` that stamped x's global
metadata onto every level, coordinates included; `Solution_prepatch.lean`
reproduces that (`outCoords[k] := ⟨name, xGAttrs⟩`) and **fails**
`out.coords[i]! = rebuiltCoord xCoords (resCoords[i]!)` (G-DIFF). The variable
clause `out.vars[i]! = rebuiltVar …` fails for the same reason (variable
metadata also taken by name), which is the second observable facet of the fix.

## B. No axioms (no A-consumed, no A-reference)

The `axioms` region is empty and the bundle ships **no `axiom_check.py`**.
There are only two callees in scope, and neither is a nontrivial *unchanged*
repo callee that needs abstracting:

- `apply_ufunc` is **unchanged** by the patch and is modeled as the result
  skeleton it returns (the `resVars`/`resCoords`/`promote` inputs, mapping.md
  §3.1) — an **R-input**, not axiomatized about its values, since the patch does
  not change them.
- `getattr(obj, "attrs", {})` is a **Python language builtin** (a total field
  read with a default), transliterated directly as `lookupAttrs` over the level
  arrays — an **I** op, not a repo callee.

The operation the patch *changes* — the per-level by-name metadata rebuild — is
**the behavior under repair itself**, not a stable upstream callee. Its only
real-world embodiment is the *patched* `xr.where`, which is exactly **G-CONF**'s
oracle (G-CONF applies the gold patch; §4.1). It would be unsound to "validate"
it via G-AX, because **G-AX runs the UNPATCHED repo** — there the buggy
`xr.where` stamps x's global metadata onto coordinates, so any patched-behavior
assertion is impossible by construction. Per SPEC_GUIDE §3, a changed op modeled
deeply and checked against the patched oracle is an **R/I leg validated by
G-CONF**, not an A-reference. Hence: no consumed axiom, no A-reference, no dead
axiom, and G-AX skips.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — moving metadata
propagation from a single global-stamp callback to a per-level by-name rebuild —
is modeled **deeply** (steps A2–A4), not hidden behind an axiom about the
function under change. There is no consumed axiom and no `apply_ufunc` oracle in
the postconditions; the result is grounded in the structural inputs
(`resVars`/`resCoords`/`xVars`/`xCoords` by name), per SPEC_GUIDE §0.8.

## D. verify(Solution) ⇒ resolved

`rebuildAttrs` verifies only if every output coordinate level's metadata equals
the by-name selection from x's coordinates (A4) and every variable level's
metadata equals the by-name / promotion selection (A3) and the global metadata
follows `rebuiltGlobal` (A2). By R (`Obj`/`Lvl` ↔ object/level, `{}` ↔ `0`,
`getattr(...,"attrs",{})` ↔ `lookupAttrs`) the verified rebuild equals the gold
patch's post-`apply_ufunc` metadata rebuild on the tested objects; by **G-CONF**
the R/I transliteration agrees with the **patched** `xr.where(..., keep_attrs=
True)` behaviour across the F2P matrix (3 DataArrays, scalar x, scalar y, both
scalar, scalar cond, DataArray+2 Datasets, 2 DataArrays+1 Dataset) plus the
pinned fuzz corpus (100007 inputs, 0 disagreements). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). Trust points are exactly
refinement fidelity (this doc, G-EQ + G-CONF); there are no consumed axioms and
no A-reference, so G-AX skips.
