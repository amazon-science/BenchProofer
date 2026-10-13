# mapping.md — astropy__astropy-13579

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0df94ff7097961e92fd7812036a24b145bc13ca8`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change:
`astropy/wcs/wcsapi/wrappers/sliced_wcs.py`.

## 0. The behaviour under change (no leakage of the edit)

`SlicedLowLevelWCS` wraps a full N-dimensional WCS and presents a lower-dim
view obtained by fixing (slicing) some pixel axes to integer positions. Its
inverse transform takes world coordinates for the **kept** world dimensions and
must return pixel coordinates for the **kept** pixel dimensions, consistent with
the full WCS.

To call the full WCS inverse transform it must assemble a complete world vector
of length `world_n_dim`: kept world dimensions receive the supplied values; the
**dropped** world dimensions (sliced out) must receive *the world coordinate at
the position of the slice*. When the full WCS couples a dropped world dimension
into a kept pixel dimension (a non-diagonal correlation), the value chosen for a
dropped world slot changes the kept pixel output. The correct fill is the world
coordinate the slice sits at; any constant placeholder breaks the round trip on
coupled axes.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)` | `SlicedLowLevelWCS.world_to_pixel_values` — `astropy/wcs/wcsapi/wrappers/sliced_wcs.py:245`, the `world_arrays_new` assembly loop (lines 247-254) | the modeled changed function (assembly of the full-WCS world vector for the inverse transform) |
| `recovered_pixel(kept, supplied, world_at_slice, world_n_dim, dim)` | the composition `self._wcs.world_to_pixel_values(*world_arrays_new)` then kept-pixel selection (lines 256-269) | spec-level statement of the resulting kept pixel value via the axiomatized full inverse |
| `value_at(kept, supplied, world_at_slice, iworld)` *(pure)* | the per-`iworld` branch body of the assembly loop (lines 249-254): `world_arrays[iworld_curr]` if kept else the dropped fill | the per-index scalar selection (the value placed at full dim `iworld`) |
| `ref_world_vector(kept, supplied, world_at_slice, n)` *(pure)* | the length-`n` prefix of `world_arrays_new` after the loop has processed dims `0..n-1` | the pure reference vector the assembly loop's invariant tracks |
| `full_world_to_pixel(world_vec, dim)` *(axiom — A-consumed)* | `self._wcs.world_to_pixel_values` — the unchanged underlying full-WCS inverse (`BaseLowLevelWCS.world_to_pixel_values`, `astropy/wcs/wcsapi/low_level_api.py:93`) | unchanged community callee the assembled vector is fed to |
| `kept: List[bool]` parameter | `iworld in self._world_keep` (line 250); `self._world_keep` is `np.nonzero(...)`, sliced_wcs.py:149 | per-full-world-dimension flag: true iff dimension `iworld` is kept (the membership test driving the kept/dropped branch, expressed as a boolean vector instead of a membership predicate) |
| `supplied: List[int]` parameter | the dense `world_arrays[iworld_curr]` read via the running counter (line 252) | the supplied world value of each kept dimension, re-indexed by full-world-dimension (refinement.md R1) |
| `world_at_slice: List[int]` parameter | `sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))` (added line 246) | the full world coordinate vector at the slice; produced by the unchanged `_pixel_to_world_values_all` (sliced_wcs.py:212) |

The pre-patch repo behaviour the change removes (for the refinement audit, not
referenced from the consumer spec view): the literal constant `1.` appended for
each dropped world dimension (`world_arrays_new.append(1.)`, sliced_wcs.py:254).
The post-fix behaviour the spec pins: the dropped slot carries
`sliced_out_world_coords[iworld]` (modeled as `world_at_slice[iworld]`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| world / pixel coordinate value (`float`, `np.ndarray` scalar) | `int` | the tested behaviour is **precision-independent**: it depends only on *which scalar* fills a dropped world slot (the slice's world coordinate vs the constant `1.`), and on the full inverse transform being a function of that scalar. Integers represent the value identities and the coupled-affine dependence faithfully; no rounding/tolerance is involved in distinguishing the correct fill from the constant. See refinement.md §A note R0. |
| `world_arrays = tuple(map(np.asanyarray, world_arrays))` then `world_arrays[iworld_curr]` | `supplied: List[int]` indexed by full-world-dimension | `np.asanyarray` and the broadcast are identity on the per-axis scalar value the test reads; order preserved. The repo reads the supplied value via a running kept counter `iworld_curr`; the model re-indexes it to `supplied[iworld]` (refinement.md R1). |
| `world_arrays_new` (a Python list built by the loop) | `List[int]` of length `world_n_dim` | element-for-element; list `append` ↔ list `append`. |
| `sliced_out_world_coords` (length `world_n_dim` sequence) | `world_at_slice: List[int]` | indexed identically by `iworld`. |
| `self._world_keep` (sorted ndarray of ints) | `kept: List[bool]` of length `world_n_dim` | `iworld in self._world_keep` ↔ `kept[iworld]`; the membership predicate over a sorted index set is re-expressed as a per-dimension boolean flag. The running counter `iworld_curr` selects the k-th kept value, captured by the R1 re-indexing of `supplied`. |
| `self._wcs.world_to_pixel_values(*v)[dim]` | `full_world_to_pixel(v, dim)` (axiom) | per-pixel-dimension scalar output of the unchanged full inverse. |

`float` is modeled as `int` (not interpreted floats) because the discriminating
property is the value substituted into the dropped slot, not any floating-point
rounding — recorded as `float_encoding: null` in meta.json.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `full_world_to_pixel` ↔ `self._wcs.world_to_pixel_values` (A-consumed)
**Callee:** the underlying full WCS's inverse transform
(`BaseLowLevelWCS.world_to_pixel_values`, `astropy/wcs/wcsapi/low_level_api.py:93`;
for a FITS WCS this is the wcslib transform). It is **unchanged** by the patch;
the patch only changes *what world vector is fed to it*. The assembled function
under spec calls it but does not modify it, so it is axiomatized.

**What the Nagini axiom actually encodes (the *consumed* property).** The axiom
declaration `full_world_to_pixel` is `@Pure @ContractOnly` with **no `Ensures`**
(its only `Requires` is `dim >= 0`). The single property the Nagini proof
consumes is therefore **determinism (congruence) only**: equal vectors give
equal results, and — crucially — vectors that differ are NOT provably equal.
This is what ties `recovered_pixel`'s result to the EXACT assembled vector, so
that a vector differing in any slot is a different argument. The proof does
**not** consume any round-trip identity, and the model encodes none. This is the
weakest contract sufficient to make the assembled-vector identity discriminating,
not a model of wcslib's math.

**The round-trip identity is validated *executably*, not encoded.** The
correctness condition for the issue — that filling the dropped slots with the
slice's own world coordinates recovers the slice pixel
(`full_world_to_pixel(world_at_slice_vector, dim) == slice_pixel(dim)`), whereas
the constant `1.` does not — is an **executable** property checked by
axiom_check.py against the REAL callee (G-AX), NOT a Nagini-encoded `Ensures`.
The Nagini layer only needs determinism; G-AX supplies the evidence that the
deterministic callee, fed the at-view-filled vector, actually inverts to the
slice pixel on the issue WCS.

**Soundness / round-trip check (G-AX):** `axiom_check.py` constructs the coupled
FITS WCS from the issue (the `COUPLED_WCS_HEADER`), slices it, and runs the REAL
`self._wcs.world_to_pixel_values` to confirm (a) **determinism** (same input ⇒
same output — the property the proof consumes) and (b) the **round-trip identity**
(the executable property): feeding the slice's own world coordinate into the
dropped (spectral) slot recovers pixel 0 in that slot, and the kept spatial pixel
comes back at the expected value — whereas feeding the constant `1.` does not. It
also re-runs the public reproducer asserting `np.allclose(out_pix[0], 0)`
post-fix. stdlib + the repo's own `astropy.wcs`/`numpy` (the very modules the
patch lives in); exit 0 iff sound.

### 3.2 `world_at_slice` provenance ↔ `_pixel_to_world_values_all` (input, A-consumed via §3.1)
`sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))`
(sliced_wcs.py:212-227, unchanged) returns the full WCS world coordinates at
pixel 0 of every kept pixel dimension — i.e. the world coordinate at the slice.
The model receives this as the read-only input `world_at_slice`; its defining
property (that the deterministic callee, evaluated at a vector carrying it in the
dropped slots, recovers the slice pixel) is the **executable** round-trip
property of §3.1, checked by G-AX on the real WCS (it is not a Nagini-encoded
clause).
