# refinement.md — astropy__astropy-13398

Operation correspondence between the Lean `implementation_*` skeletons and the
gold `patch.diff` (the new module `itrs_observed_transforms.py`). Tags:
**R** type refinement, **A-consumed** proof uses an axiom's property,
**A-reference** deep model validated == real callee (G-AX), **I** identical op.

## The atmospheric-correction facet is a recorded relaxed leak

The graded delta of this cell IS the atmospheric-correction branch: the diff of
the `impl` regions of `Solution_prepatch.lean` against `Solution.lean` is exactly
that branch in both legs, so a spec silent about it cannot make the pre-patch
implementation fail (G-DIFF). The public `problem_statement` disclaims the facet
("I have yet to add refraction, but I can do so if it is deemed important to do
so") and contains none of its vocabulary. That mismatch, the reason no abstract
stand-in works, and the measurements behind both claims are in
`RELAXED_LEAKAGE.md`; `meta.json relaxed_leakage = true` and G-LEAK records
`relaxed`. In short: the carrier must be `Float` (§ below), a `Float` equality
postcondition is bit-exact, and eliding any single piece of the correction makes
the spec unfaithful on inputs reachable through the public API — measured, with a
bit-exact control, in that file.

## Numeric carrier: `Float`, and what that means for the R legs

The numeric carrier is Lean's `Float`, i.e. **the same IEEE-754 binary64 the
library computes in**. The bridge is therefore an identity, not an idealisation:
`Float.cos`, `Float.sin`, `Float.sqrt`, `+ - * /`, `max` and the decimal literals
all denote the very binary64 operations `numpy`/`libm` perform on the same bit
patterns. Consequently:

- **The R legs carry NO approximation gap and no error-bound obligation, because
  there is nothing to approximate**: a `Float` R leg is exact-by-construction
  whenever the model performs the *same operations in the same order* as the
  patch. The obligation the `Float` carrier does impose is the *ordering*
  obligation: `mmul`/`mvmul` fix an explicit index-order accumulation, and the
  refraction bodies fix an explicit parenthesisation, so a model that reassociates
  is a defect even though it would be a theorem over ℝ. G-CONF is what discharges
  this: it re-plays the model's arithmetic against the real callees at ≥1e5 fuzzed
  inputs and admits only the residual attributable to numpy's freedom to
  reassociate a `@` product and to the `d * d` versus `d ** 2` spelling
  (`atol = 1e-12` on the matrices, `rtol = 1e-13, atol = 1e-12` on the refraction
  legs). Nothing larger is tolerated anywhere.
- **The carrier choice is load-bearing for the strength of the postconditions,
  not just for their fidelity.** Over an exact-real carrier the two obligations
  below would admit rewrites that are *provable identities there* and catastrophic
  at working precision: replacing `x` by `(x + 1e300) - 1e300` (a theorem over ℝ
  by `add_sub_cancel_right`, and total annihilation of every input below ~1e284 in
  binary64), or shifting a rotation argument by 10⁹ whole turns (a theorem over ℝ
  by periodicity of `cos`/`sin`, and pure noise once the argument exceeds the
  precision of the angle). Because such a rewrite is *definitionally equal as a
  function* to the gold body over ℝ, and `correct_*` is a predicate on the
  implementation's VALUE alone, **no postcondition over ℝ can separate them** —
  the carrier is the only place the distinction can live. Over `Float` neither
  rewrite is an identity, `rfl` no longer closes the rewritten proof, and both
  are rejected. This is the reason the spec is stated over `Float`, and
  `properties.py` pins both shapes as rejected rivals.
- **What the `Float` carrier costs, stated explicitly rather than left to be
  discovered.** Because the kernel can prove almost nothing about `Float`
  arithmetic, a same-spec implementation whose value is *equal at binary64* but
  not *provably* equal is rejected. Measured against the retained attack corpus
  re-expressed on this spec, exactly one attack is in that position: the one
  that re-associates the rotation product to `flipX * (rotY * rotZ)` (indexed
  `atk_9` in the retained corpus this cell carries — the two audit passes number
  their attack files differently, so shapes, not indices, are what is being
  claimed here). Re-associating a signed-permutation factor with two rotations
  is bit-exact at binary64 (max difference 0.0 over 20000 seeded draws), so that
  code is value-identical — and yet `rfl` cannot close it and the spec rejects
  it. No resolve verdict is claimed for it: the one time it was submitted the
  run ended in an image-pull failure, so its patch has never been measured
  either way. That is a limit on what is PROVABLE, not a claim about the
  behaviour: the postcondition still pins exactly the value the patched function
  computes, which the bundled reproduction measures bit-identically at 21
  configurations, and G-CONF re-plays the model's own accumulation order against
  the real callees at 1e5 draws. It is also the deliberate price of closing the
  SPEC-TOO-WEAK hole — the same inability to reason about `Float` is what rejects
  `atk_11` and `atk_13`, whose superficially similar rewrites are NOT
  value-preserving (one annihilates an Earth-scale input to exactly zero, the
  other displaces the answer by 0.75 m). The alternative was measured: over an
  exact-real carrier `atk_11` VERIFIES and its patch fails 3 of 4 F2P tests.
  The carrier is not blanket-strict either: `atk_8`, which triple-transposes the
  inverse rotation, STILL verifies here, because transposition is definitional
  and eta-reduces, so value-identical rewrites are admitted whenever the kernel
  can see the identity. Full re-run of the corpus against this spec: gold exit 0;
  `atk_8` exit 0 (a correct echo, whose patch resolves); `atk_1`–`atk_7`,
  `atk_9`–`atk_13` exit 1, i.e. every attack that was rejected before is still
  rejected and both attacks that broke the previous spec are now rejected.

Type bijection (full detail in mapping.md):
- Python `CartesianRepresentation` xyz ↔ Lean `Vec3 = Fin 3 → Float`.
- numpy `(3,3)` float64 rotation matrix ↔ Lean `Mat3 = Matrix (Fin 3) (Fin 3) Float`.
- `crepr.transform(M)` (= `erfa.rxp(M, xyz)`, left-multiply the matrix onto the
  column vector) ↔ `mvmul M v`. **R** (index-order accumulation fixed).
- `A @ B` ↔ `mmul A B`. **R** (index-order accumulation fixed).
- `matrix_transpose(M)` ↔ `Mᵀ`. **R**.
- Python `float` angles/lengths ↔ Lean `Float`. **R**, identity bridge (both
  binary64); see above.
- `to_geodetic('WGS84')`'s reported angles are in **degrees**, so the model
  applies `angToRad` and uses `poleAngle = 90.0` where the patch relies on
  `NORTH_POLE = 90.0*u.deg` and lets `rotation_matrix` do the conversion. **R**.

## `itrs_to_observed`  ↔  `implementation_itrs_to_observed`

| Lean impl op | patch.diff op | tag |
|---|---|---|
| `if siteDiffers srcLoc f.location \|\| epochDiffers srcEpoch f.epoch then src := carryTo v srcLoc srcEpoch f.location f.epoch` | the leading `if (np.any(itrs_coo.location != observed_frame.location) or np.any(itrs_coo.obstime != observed_frame.obstime)): itrs_coo = itrs_coo.transform_to(ITRS(obstime=observed_frame.obstime, location=observed_frame.location))` | A-reference (`siteDiffers`, `carryTo`) / I (guard shape) |
| `let (lon,lat,_) := geodetic f.location` | `lon, lat, height = observed_frame.location.to_geodetic('WGS84')` | A-reference |
| `if f.isAltAz = true ∨ f.pressure>0 then crepr := mvmul (altazMat lon lat) src` | `if isinstance(observed_frame, AltAz) or (observed_frame.pressure>0.0): crepr = itrs_coo.cartesian.transform(itrs_to_altaz_mat(lon,lat))` | R (mvmul) / I (branch) |
| `altazMat lon lat = mmul (mmul flipX (rotY ((poleAngle-lat)*angToRad))) (rotZ (lon*angToRad))` | `itrs_to_altaz_mat`: `minus_x @ rotation_matrix(NORTH_POLE-lat,'y') @ rotation_matrix(lon,'z')` — note `@` is left-associative, so the model's nesting is the patch's nesting (deep-modelled, NOT axiomatised) | R |
| `if f.pressure>0 then crepr := toApparent crepr rc.1 rc.2` | `if observed_frame.pressure>0.0: crepr = add_refraction(crepr, observed_frame)` | R / I (branch) |
| `let rc := bendCoefs p t h wl` | `coefA, coefB = erfa.refco(pressure, temperature, humidity, obswl)` (empirical fit, unchanged external) | A-reference |
| `toApparent` body: `normSplit`, `sel = max (uv 2) sinAltFloor`, `cel = max (√(uv0²+uv1²)) cosAltFloor`, `w = coefB*tanz²`, `Δel = (A+w)·tanz/(1+(A+3w)/sel²)`, `cosdel = 1-0.5Δel²`, `fct = cosdel - Δel·sel/cel`, bend, then `scaleVec norm (normSplit bent).2` | the `add_refraction` arithmetic verbatim, including that the SECOND `erfa.pn`'s norm is discarded and the FIRST norm is the one `erfa.sxp` restores (deep-modelled) | R |
| `normSplit` / `scaleVec` | `erfa.pn` / `erfa.sxp` | A-reference |
| `if f.isAltAz = false then crepr := mvmul (poleTiltMat lat) crepr` | `if isinstance(observed_frame, HADec): crepr = crepr.transform(altaz_to_hadec_mat(lat))` | R / I (branch) |
| `poleTiltMat lat = mmul flipXY (rotY ((poleAngle-lat)*angToRad))` | `altaz_to_hadec_mat`: `z180 @ rotation_matrix(NORTH_POLE-lat,'y')` (deep-modelled) | R |
| `else crepr := mvmul (hadecMat lon) src` | `else: crepr = itrs_coo.cartesian.transform(itrs_to_hadec_mat(lon))` | R / I (branch) |
| `hadecMat lon = mmul flipY (rotZ (lon*angToRad))` | `itrs_to_hadec_mat`: `minus_y @ rotation_matrix(lon,'z')` (deep-modelled) | R |
| `return crepr` (`realize_frame` is the carrier wrap) | `return observed_frame.realize_frame(crepr)` | I |

## `observed_to_itrs`  ↔  `implementation_observed_to_itrs`

| Lean impl op | patch.diff op | tag |
|---|---|---|
| `let (lon,lat,_) := geodetic f.location` | `lon,lat,height = observed_coo.location.to_geodetic('WGS84')` | A-reference |
| `if f.isAltAz = true ∨ f.pressure>0 then …` | `if isinstance(observed_coo, AltAz) or (observed_coo.pressure>0.0):` | I (branch) |
| `if f.pressure>0 then …` | `if observed_coo.pressure>0.0:` | I (branch) |
| `if f.isAltAz=false then crepr := mvmul ((poleTiltMat lat)ᵀ) crepr` | `if isinstance(observed_coo, HADec): crepr = crepr.transform(matrix_transpose(altaz_to_hadec_mat(lat)))` | R / I |
| `crepr := toGeometric crepr rc.1 rc.2` | `crepr = remove_refraction(crepr, observed_coo)` | R |
| `toGeometric` body: `normSplit`, `sel = max (uv 2) sinAltFloor`, `cel = √(uv0²+uv1²)` — **no `cosAltFloor` guard on this leg**, `Δel = (A + B·tanz²)·tanz`, `cartToSph`, `sphToCart az (el-Δel)`, `scaleVec norm` | the `remove_refraction` arithmetic verbatim (deep-modelled) | R |
| `crepr := mvmul ((altazMat lon lat)ᵀ) crepr` | `crepr = crepr.transform(matrix_transpose(itrs_to_altaz_mat(lon,lat)))` | R |
| `else crepr := mvmul ((hadecMat lon)ᵀ) v` | `else: crepr = observed_coo.cartesian.transform(matrix_transpose(itrs_to_hadec_mat(lon)))` | R |
| `return carryTo crepr f.location f.epoch tgtLoc tgtEpoch` (UNCONDITIONAL, and with the TARGET pair explicit) | `itrs_at_obs_time = ITRS(crepr, obstime=observed_coo.obstime, location=observed_coo.location); return itrs_at_obs_time.transform_to(itrs_frame)` — the trailing transform is NOT guarded, and `itrs_frame` supplies a target site and a target epoch that are in general different from the observed pair | A-reference |

## Notes

- No changed op is axiomatised. The new direct geometry — the three rotation
  matrices, the matrix and matrix/vector products, the branch structure, the guard
  that decides whether the forward carry happens, and BOTH refraction closed forms
  — is spelled out (deep model). Only genuinely-unchanged external routines the
  new code *calls* are `opaque`: the WGS84 inversion, `erfa.refco`, `erfa.pn`,
  `erfa.sxp`, `erfa.c2s`/`s2c`, the site comparison, and the indirect ITRS↔ITRS
  carry. Those are the **A-reference** rows.
- A-reference callees are G-AX-probed against the real routines; no A-consumed
  (oracle) axiom is shipped — both proofs close by `split_ifs <;> rfl`, so the
  result is *produced by* the modelled branch, never echoed from an answer key
  (SPEC_GUIDE §0.8).
- **`carryTo` depends on BOTH endpoint pairs.** This is the one refinement rule
  that is easy to get wrong and it is stated here precisely, because the earlier
  3-argument reading (`carry v srcLoc srcEpoch`, i.e. "re-express this vector at
  its own site/epoch") over-constrained the inverse conversion: it forced
  `observed_to_itrs` to return a value determined by the observed frame alone,
  whereas the real function's answer depends on the requested output frame. Rule:
  a carry is a map between two (site, epoch) pairs; it is the identity exactly
  when the pairs agree and otherwise routes through an inertial frame, so its
  result is a function of the ordered pair-of-pairs. Every faithful
  materialisation must therefore pass the target site and target epoch, and in
  `observed_to_itrs` the carry is applied unconditionally, because the target pair
  is the caller's `itrs_frame` and there is no guard in front of it. The bundled
  reproduction measures the composed model against the real module at three
  distinct target sites and two target epochs (bit-identical), and G-AX probes the
  identity-when-equal and depends-on-the-target claims directly.
