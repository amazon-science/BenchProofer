# mapping.md — astropy__astropy-13579

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0df94ff7097961e92fd7812036a24b145bc13ca8`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo file under change: `astropy/wcs/wcsapi/wrappers/sliced_wcs.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assembleWorldVector (axes, supplied)` | `SlicedLowLevelWCS.world_to_pixel_values` — `sliced_wcs.py:245` (the `world_arrays_new` assembly loop, lines 247–254) | the modeled changed function (the world-vector assembly the patch fixes) |
| `Axis = Bool × Float` | per original-WCS-world-axis pair: `(iworld in self._world_keep, sliced_out_world_coords[iworld])` | one descriptor per original world axis |
| `axes` (`List Axis`) | the sequence over `iworld in range(self._wcs.world_n_dim)` of `(iworld ∈ self._world_keep, sliced_out_world_coords[iworld])` | the per-axis loop domain |
| `supplied` (`List Float`) | `world_arrays` (the caller-supplied values, one per kept world axis, in order) | read-only caller input |
| `.2` of an absent axis (the reference coordinate) | `sliced_out_world_coords[iworld]`, where `sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))` (post-patch line 246) | the value the dropped axis takes at pixel 0 along the kept axes |
| `scatter`, `scatterStep` *(deep model)* | the `world_arrays_new` list built by the `for iworld …` loop (lines 247–254 post-patch) | pure spec: the assembled full-dimensional vector; deep model of the **changed function's own** assembly behavior, NOT a callee |

The callees the loop touches but does **not** change (refinement audit only, not
modeled as axioms — see §3):
`self._pixel_to_world_values_all` (produces `sliced_out_world_coords`, the source
of each `.2`) and `self._wcs.world_to_pixel_values` (the downstream inverse
transform consuming the assembled vector).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to). For
the tested scenario the per-axis world arrays are scalars (0-d / length-1), so a
single `Float` per axis is the faithful carrier.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `world_arrays_new` (the assembled list, one entry per original world axis) | `List Float` | `xs[k]` ↔ `xs[k]!`; `len(xs)` ↔ `xs.length`; append ↔ `++ [·]`; the entry is the scalar world value for axis `k` |
| `world_arrays` (caller-supplied, one per kept world axis) | `supplied : List Float` | i-th supplied value ↔ `supplied[i]!`; consumed left-to-right (`headD`/`tail`) exactly as `world_arrays[iworld_curr]` with `iworld_curr += 1` |
| `iworld ∈ self._world_keep` (membership test, line 250) | `a.1 : Bool` | True iff the original world axis is kept in the slice; precomputed per axis |
| `sliced_out_world_coords[iworld]` (scalar, post-patch line 254) | `a.2 : Float` | the dropped axis's reference world coordinate; one float per axis |
| the constant `1.` (pre-patch line 254) | the literal `1.0` (prepatch only) | the buggy fixed placeholder the fix replaces |
| `np.asanyarray` / `np.broadcast_arrays` (lines 246, 256) | identity (omitted) | for the F2P scalar inputs these are observationally the identity on each axis's scalar value; they do not alter the per-axis content the assembly selects |

Lean `List` indexing is total and sound; the carrier is `List Float` because the
operation is a per-axis scatter of scalar world values.

## 3. Callee provenance — both callees UNCHANGED, NOT axiomatized

The patch changes only the *value used to fill a dropped world axis* inside
`world_to_pixel_values`. Two callees are referenced by the surrounding code and
**neither is changed** by the patch:

### 3.1 `self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))`
Produces `sliced_out_world_coords` — the full-WCS world coordinates at pixel
position 0 along every kept pixel axis. The patch ADDS the *call* (post-patch
line 246) but does not change `_pixel_to_world_values_all` itself
(`sliced_wcs.py:212`, unchanged). Its only role here is to supply, per dropped
axis, the reference coordinate carried as `Axis.2`. It is therefore a read-only
**input** to the modeled assembly, not a consumed axiom and not an A-reference
deep model of a callee: `scatter` deeply models the **changed function's own**
new fill behavior, which selects between `supplied` and the supplied `.2`. (No
axiom; G-AX is a skip.)

### 3.2 `self._wcs.world_to_pixel_values(*world_arrays_new)`
The lower-level inverse transform (line 257). Unchanged by the patch and
**downstream** of the assembly the spec models — the spec stops at the assembled
`world_arrays_new` vector (= `scatter`), which is exactly the data the patch
changes. The downstream transform receives identical assembled input from any
impl satisfying the spec, hence yields identical pixels. Not axiomatized.

There are thus **no axioms** in this bundle (`axiom_check.py` is a skip, mirroring
django__django-14053): the changed behavior is modeled deeply over read-only
inputs and the relevant callees are unchanged.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13579`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `scatter`/`scatterStep` (R/I-tagged ops) to Python and compares
against the **real patched** `world_to_pixel_values`' assembled `world_arrays_new`
(both callees left as the real repo callees — A-tagged-as-input, run for real),
over ≥10⁵ fuzzed (axes-keep-mask, reference-coordinate, supplied-values)
scenarios.
