# mapping.md — astropy__astropy-13579

## Symbol binding (file:line @ base_commit 0df94ff709)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_assemble` / `problem_spec_assemble` / `correct_assemble` | the loop that rebuilds the full-length world-coordinate vector `world_arrays_new` inside `SlicedLowLevelWCS.world_to_pixel_values`, before the underlying inverse transform | `astropy/wcs/wcsapi/wrappers/sliced_wcs.py:245-261` @ base_commit (edited lines: the new `sliced_out_world_coords = …` at hunk 1 and the `else:` branch value at file line 254/256) |
| `slicedOut.getD iworld 0` (the omitted-axis fill) | `sliced_out_world_coords[iworld]` (post-patch; pre-patch: the constant `1.`) | gold patch, `sliced_wcs.py:256` (pre-patch line 254: `world_arrays_new.append(1.)`) |
| `inputs.getD c 0` (the kept-axis value) | `world_arrays[iworld_curr]` | `sliced_wcs.py:255` (unchanged) |
| `worldKeep` | `self._world_keep` (sorted indices of retained underlying world axes) | `sliced_wcs.py:149-150` |
| `worldNDim` | `self._wcs.world_n_dim` (underlying world dimension count) | `sliced_wcs.py:249` |

The modeled function is `SlicedLowLevelWCS.world_to_pixel_values`. The reduced
(sliced) view exposes only the world axes in `self._world_keep`; to invert back
to pixels in the underlying WCS the method must first rebuild a full-length world
vector (`world_arrays_new`, length `self._wcs.world_n_dim`). The loop walks the
underlying world axes in order:

```python
sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))  # POST-PATCH (new)
...
iworld_curr = -1
for iworld in range(self._wcs.world_n_dim):
    if iworld in self._world_keep:
        iworld_curr += 1
        world_arrays_new.append(world_arrays[iworld_curr])   # supplied value, kept axis
    else:
        world_arrays_new.append(sliced_out_world_coords[iworld])   # POST-PATCH (was `1.`)
```

`world_arrays_new` is then `np.broadcast_arrays`'d and fed to the underlying
`self._wcs.world_to_pixel_values`. The PRE-PATCH code filled every omitted axis
with the constant `1.`, so when the underlying WCS *couples* a dropped axis to a
kept one (non-diagonal PC matrix), the wrong omitted-axis world value corrupts
the inverse transform for the kept pixel — the reported bug. The fix fills each
omitted axis with the world coordinate the slice was actually taken at (pixel 0
of the slice, i.e. `_pixel_to_world_values_all(0,…)`), so the inverse transform
recovers the correct kept pixel.

## Modeled scope

The bundle models the **vector reassembly loop** — the only edited control flow.
Two things it touches are taken as inputs, not recomputed:

- `slicedOut` — the reference world vector `sliced_out_world_coords`, produced by
  the unchanged `_pixel_to_world_values_all` callee. It is the upstream quantity
  the fix *consumes*; the reassembly itself does no arithmetic on it, it only
  positionally places its entries. Modeled as an **A-reference** input
  (validated == the real callee's role by G-CONF, which captures the real loop's
  output rather than re-deriving the transform).
- The downstream `self._wcs.world_to_pixel_values` inverse transform and the
  trailing per-pixel `start` offset — unchanged, out of model scope.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `self._wcs.world_n_dim` (int) | `worldNDim : Nat` | underlying world axis count |
| `self._world_keep` (sorted ndarray of ints) | `worldKeep : List Nat` | retained underlying world-axis indices, ascending |
| supplied `world_arrays` (len `world_n_dim` of the slice = `len(world_keep)`) | `inputs : List Int` | per-kept-axis supplied values; positional. The loop only *places* values (no arithmetic), so integer sentinels model float coordinates faithfully |
| `sliced_out_world_coords` (len `world_n_dim`, floats) | `slicedOut : List Int` | per-underlying-axis reference values; positional, indexed by `iworld` |
| `world_arrays_new` (len `world_n_dim`) | `result : List Int` | the reassembled full-length vector; entry `i` ↦ `result.getD i 0` |

## Callee provenance + flag dependencies

- No callee axiom is consumed. The changed op (filling omitted axes with the
  reference value instead of the constant `1.`) is modeled DEEPLY (positional
  placement in `implementation_assemble`); validated against the real loop by
  G-CONF as an A-reference. `axiom_check.py` is a skip stub.
- `_pixel_to_world_values_all` (unchanged) produces `slicedOut`; it is taken as
  an input to the modeled loop, so no axiom is needed. G-CONF reads it from the
  real object at runtime to construct the expected reassembly.
- No flag dependency: the loop runs unconditionally on every
  `world_to_pixel_values` call.

## G-CONF fuzz seed

`SEED = 20240629` (pinned in `conformance_check.py`).
