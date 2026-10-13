# refinement.md — astropy__astropy-13579

The operation-by-operation correspondence between `model.py`'s implementation
(the `assemble_inverse_world` loop, the pure reference `ref_world_vector`, and
the live `full_world_to_pixel` axiom consumed in `recovered_pixel`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`Ensures`, **A-reference** where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The single edited hunk — `SlicedLowLevelWCS.world_to_pixel_values`
(`astropy/wcs/wcsapi/wrappers/sliced_wcs.py:245`)

Gold hunk (two adjacent edits, one behaviour):
```
+ sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))
  ...
  for iworld in range(self._wcs.world_n_dim):
      if iworld in self._world_keep:
          iworld_curr += 1
          world_arrays_new.append(world_arrays[iworld_curr])
      else:
-         world_arrays_new.append(1.)
+         world_arrays_new.append(sliced_out_world_coords[iworld])
```

The fixed behaviour: the world vector handed to the underlying full inverse fills
every DROPPED world dimension with the world coordinate at the position of the
slice (`sliced_out_world_coords[iworld]`) instead of the constant `1.`.

## R0 — value carrier: `float` ↔ `int`
The repo's coordinate values are `float`/`np.ndarray` scalars; the model uses
`int`. The distinguishing behaviour is **precision-independent**: the bug is the
substitution of a *different scalar* (the constant `1.` vs the dropped axis's
at-view world coordinate), and the downstream transform being a *function of*
that scalar. No floating-point rounding or tolerance participates in
distinguishing the correct fill from the constant (axiom_check.py confirms the
two fills give numerically far-apart pixels: ~0 vs ~1.8e11 on the issue WCS).
Hence `int` faithfully carries the value identities; recorded
`float_encoding: null`. (R — carrier refinement.)

## The correspondence table

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `kept: List[bool]`, `supplied: List[int]`, `world_at_slice: List[int]`, `world_n_dim` | the loop's `self._world_keep` membership, `world_arrays[iworld_curr]`, `sliced_out_world_coords`, `self._wcs.world_n_dim` | R | The model indexes the kept/dropped status (`kept[iw]`) and the supplied per-dimension world value (`supplied[iw]`) by FULL-world-dimension index `iw`; the repo stores supplied values densely and reads `world_arrays[iworld_curr]` via a running counter `iworld_curr`. The bijection is order-preserving: `supplied[self._world_keep[k]] == world_arrays[k]` and `kept[iw] == (iw in self._world_keep)`. The running-counter mechanics are **unchanged** by the patch (R1, re-indexing). `world_at_slice[iw]` ↔ `sliced_out_world_coords[iw]`. |
| 2 | `for iworld in range(world_n_dim)` | `for iworld in range(self._wcs.world_n_dim)` | I | identical loop over the full world dimensions. |
| 3 | `if kept[iworld]: world_arrays_new.append(supplied[iworld])` | `if iworld in self._world_keep: iworld_curr += 1; world_arrays_new.append(world_arrays[iworld_curr])` | R | kept branch: the value placed at full dim `iworld` is the supplied world value for that dimension. Under the R1 re-indexing these are the same scalar; the patch does not touch this branch. |
| 4 | `else: world_arrays_new.append(world_at_slice[iworld])` | `else: world_arrays_new.append(sliced_out_world_coords[iworld])` | I (post-fix) | **the edit.** The dropped slot is filled with the at-view world coordinate. The model's `else` branch IS this assignment (modulo R0 value carrier). The pre-patch `1.` is reproduced in `model_prepatch.py` (`v = 1`) and fails the spec. |
| 5 | `world_at_slice` is an input with the meaning "at-view world coordinate of every full dimension" | `sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))` | A-consumed (input provenance, mapping.md §3.2) | `_pixel_to_world_values_all` is **unchanged**; the patch only *adds a call* to it. Its result is the world coordinate at pixel 0 of every kept pixel dimension — the at-view coordinate. Modeled as the read-only input `world_at_slice`. Its defining property — that the deterministic callee, fed a vector carrying it in the dropped slots, recovers the slice pixel — is **not** a Nagini-encoded clause; it is an **executable** property G-AX checks on the real WCS (axiom_check.py step 2). |
| 6 | `full_world_to_pixel(ToSeq(world_arrays_new), dim)` in `recovered_pixel` | `self._wcs.world_to_pixel_values(*world_arrays_new)` then kept-pixel selection `pixel[ip for ip in self._pixel_keep]` | A-consumed | the underlying full inverse is the **unchanged** callee the assembled vector is fed to. The model declaration `full_world_to_pixel` is `@Pure @ContractOnly` with **no `Ensures`**, so the proof consumes only its **determinism** (equal vectors → equal results; differing vectors NOT provably equal): because it is opaque, `recovered_pixel`'s result is tied to the EXACT assembled vector — the bug's constant-filled vector is a different argument, so the correct kept pixel is provably reached only when the dropped slots carry the at-view coordinate. The round-trip identity itself is validated executably by G-AX (the real `world_to_pixel_values`), not encoded in Nagini. |
| 7 | `np.broadcast_arrays`, `np.asanyarray`, the post-call `pixel_arrays[ipixel] -= start` shift, and the kept-pixel `tuple(...)` selection | same in the repo | R / I | broadcasting and `asanyarray` are identity on the per-axis scalar value the test reads (R, omitted from the model). The constant pixel-start shift and kept-pixel selection are **unchanged** by the patch and do not affect *which* world value fills the dropped slot — the only behaviour under change — so they are outside the modeled core (the model returns the assembled vector and the recovered kept pixel before/at the transform). |

## The discriminating clause and the prepatch
The behavioural delta lives entirely in step 4: dropped slot = at-view world
coordinate (fix) vs `1.` (bug). The model pins it three ways, all failing in
`model_prepatch.py` (which sets `v = 1`):

- `assemble_inverse_world` postcondition
  `ToSeq(Result()) == ref_world_vector(...)` and the dropped-slot clause
  `ToSeq(Result())[iw] == world_at_slice[iw]` for `not kept[iw]`;
- the loop invariant `ToSeq(world_arrays_new) == ref_world_vector(..., iworld)`
  (this is the clause the prepatch fails on — the assembled vector no longer
  equals the reference once a dropped slot carries `1`);
- `recovered_pixel`'s postcondition
  `Result() == full_world_to_pixel(ref_world_vector(...), dim)`: the recovered
  kept pixel is the full inverse at the reference (at-view-filled) vector; a
  constant-filled vector is a different argument to the opaque transform.

Because `world_at_slice[iw]` is generally `!= 1` (on the issue WCS the dropped
spectral coordinate is `1.05e-10`, not `1.`), the prepatch cannot satisfy the
spec. G-DIFF: one failing prepatch, the single independently-fixed behaviour.

## No kind-3 (unexpressible-changed-op) steps
Every step is R, I, or A-consumed. The one operation that genuinely *changed* —
the dropped-slot fill — is modeled **directly** (step 4, an `I` assignment under
the R0 value carrier), not hidden behind an axiom. The only consumed axiom,
`full_world_to_pixel` (step 6, A-consumed), covers the **unchanged** underlying
full inverse the assembled vector is fed to; the patch does not alter it. There
is no A-reference deep-model in this bundle (the changed operation is a single
scalar substitution, expressed concretely, not a re-implemented library
function).

## verify(model) ⇒ resolved
`assemble_inverse_world` verifies only if every dropped slot carries the at-view
world coordinate (step 4) and `recovered_pixel` only if the recovered kept pixel
is the full inverse at that exact vector (step 6). By R (the order-preserving
re-indexing R1, the value carrier R0, and the broadcasting/selection identities)
the verified assembly equals the gold patch's `world_arrays_new` on the tested
inputs; by the A-consumed `full_world_to_pixel` axiom (the Nagini proof consumes
its determinism; G-AX supplies the executable evidence that the real
`world_to_pixel_values`, fed the at-view fill, recovers the slice pixel) the
recovered kept pixel is correct. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement and the audited callee
— and the gold patch resolves (G-RESOLVE). The trust points are
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
