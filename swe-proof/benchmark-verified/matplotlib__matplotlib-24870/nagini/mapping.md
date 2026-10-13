# mapping.md — matplotlib__matplotlib-24870

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6091437be9776139d3672cde28a19cbe6c09dcd5`, states the type
abstraction, and gives the provenance of the one consumed axiom.

Repo files under change:
`lib/matplotlib/contour.py` and `lib/matplotlib/tri/_tricontour.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `choose_default_levels(has_explicit, two_valued, filled, zmin, zmax, mid)` | `ContourSet._process_contour_level_args(self, args)` — `lib/matplotlib/contour.py:1120` (the `self.levels is None` default-selection block, lines 1124-1134) | the modeled changed function: the default contour-level selection |
| `auto_levels(zmin, zmax)` *(axiom — A-consumed)* | the hard-wired-default branch `levels_arg = 7` → `self._autolev(7)` (`contour.py:1126,1131-1132`; `_autolev` at `contour.py:1080`) → `MaxNLocator(N+1).tick_values(zmin, zmax)` trimmed | the unchanged ordinary multi-level automatic selection the routine delegates to for a continuous field; an UNCHANGED callee |
| `mid` (parameter, pinned `mid - zmin == zmax - mid`) | the midpoint `.5` of the two-valued default lists `[.5]` / `[0, .5, 1]` the patch introduces (`contour.py:1126-1131` post-patch) | the single boundary level for a two-valued field |
| `zmin`, `zmax` | `self.zmin`, `self.zmax` set from `z.min()`/`z.max()` in `_contour_args` (`contour.py:1459-1460`; `_tricontour.py:72-73`) | the data extents |
| `two_valued` | `np.issubdtype(z_dtype, bool)` (`contour.py:1127` post-patch) | whether the field is a two-valued (boolean) field |
| `filled` | `self.filled` (`contour.py:725`) | whether the contour is filled |
| `has_explicit` | `len(args) != 0` i.e. `if args:` (`contour.py:1125` post-patch) | whether the caller passed an explicit level list/count |

The pre-patch repo symbol the change generalises (for the refinement audit, not
referenced from the consumer spec view): the unconditional
`if len(args) == 0: levels_arg = 7` default (`contour.py:1125-1126` pre-patch),
which never special-cased a two-valued field. The supporting hunks that thread
the field's dtype to the selection (`_contour_args`/`_check_xyz` signature
changes in both `contour.py` and `_tricontour.py`, and dropping the
`dtype=np.float64` coercion so the boolean dtype survives to the selection) are
plumbing for the one behavioural delta; see refinement.md §B.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the boolean numpy `z` array dtype test `np.issubdtype(z.dtype, bool)` | the boolean flag `two_valued` | a boolean field has exactly two distinct sample values (its min `zmin` and max `zmax`); `two_valued == True` ↔ that dtype test is true. The behaviour depends only on this predicate, not on the array contents. |
| `self.filled` | the boolean flag `filled` | identity |
| `len(args) == 0` (no explicit levels) / `args` truthy | `has_explicit` (the model fixes `not has_explicit`, the branch under spec) | identity on the boolean |
| `self.zmin`, `self.zmax` (numpy float64 scalars; `0.0`, `1.0` for a bool field) | `zmin`, `zmax` : interpreted `float` (`--float-encoding=real`) | the real data extents; for a two-valued bool field `zmin == 0.0`, `zmax == 1.0` |
| the resulting `self.levels` list (`np.asarray(levels_arg, np.float64)`; `[.5]` or `[0, .5, 1]`) | `List[float]` (the `Result()` of `choose_default_levels`) | `np.asarray([...], float64)` of a python list is the identity on the float values the F2P test reads via `.levels.tolist()` |
| the midpoint scalar `.5` | `mid` : `float`, pinned by `mid - zmin == zmax - mid` | the value equidistant from the two extremes; for `[0,1]` this is `0.5`. Pinned by its linear defining equation rather than computed by division — see §2.1 |

### 2.1 Why `mid` is an input pinned by a linear equation (the real-arithmetic wall)

Under `--float-encoding=real` the verifier's real fragment cannot discharge
division/reciprocal facts: even `m == (a+b)/2.0` and `m+m == a+b ⇒ a<m` fail to
verify (measured; the same wall documented for matplotlib-25960). The midpoint
is therefore introduced as a parameter `mid` constrained by the **subtraction-
only** linear equation `mid - zmin == zmax - mid` (mid is equidistant from the
two values). That equation (a) uniquely determines the midpoint, grounding it in
the data extents `zmin`/`zmax` (directive 8 — it is not an oracle), and (b)
together with `zmin < zmax` discharges strict interiority `zmin < mid < zmax`
inside the linear real fragment. In the real code the midpoint is the literal
`.5` of `[.5]` / `[0, .5, 1]`, which is exactly the value equidistant from `0.0`
and `1.0`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `auto_levels` ↔ the default multi-level selection (A-consumed)
**Callee:** the hard-wired-default branch of `_process_contour_level_args`:
`levels_arg = 7` (an `Integral`) ⇒ `self.levels = self._autolev(7)`. `_autolev`
(`contour.py:1080`) builds `ticker.MaxNLocator(N+1, min_n_ticks=1)` and returns
`locator.tick_values(self.zmin, self.zmax)` trimmed to the data range. For any
non-degenerate range (`zmin < zmax`) `MaxNLocator` returns several ticks, so the
default level list has **more than one** level — which is precisely why the
ordinary default is useless for a two-valued field (the contour lines pile up
near the single 0↔1 transition). This unchanged path is the operation the fixed
routine delegates to for a continuous field.

The axiom encodes only the obligation the proof consumes:
`len(auto_levels(zmin, zmax)) > 1` for `zmin < zmax`. It is the **weakest**
contract sufficient for the `not two_valued` postcondition (more than one level),
not the full `MaxNLocator` tick algorithm.

**Soundness check (G-AX):** `axiom_check.py` drives the REAL routine
in-container via `plt.contour(z)` on continuous (float64) 2×2 fields spanning a
range `[zmin, zmax]` (7 boundary ranges incl. `[0,1]` and a very narrow
`[1, 1.0001]`, plus 200 randomized ranges) with no explicit levels, and asserts
`len(cs.levels) > 1` in every case. Exit 0 iff sound. It imports only
matplotlib/numpy — the package the gold patch lives in. (Validated green on host
mpl 3.10.6; the `_autolev`/`MaxNLocator` default path is unchanged across the
3.6 image and 3.10.)

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (shadow, with
`auto_levels` delegated to the real `_autolev(7)` default-count branch)
differentially against the REAL patched selection routine in-container, on
>= 1e5 Requires-satisfying inputs (boundary + end-to-end entry-point drives +
fuzz). **Pinned fuzz seed: 24870** (the instance number).
