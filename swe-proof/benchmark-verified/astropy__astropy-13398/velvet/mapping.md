# mapping.md — astropy__astropy-13398

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6500928dc0e57be8f06d1162eacc3ba5e2eff692`, states the type
abstraction, and gives the provenance of each axiomatized callee.

Repo files under change (gold patch):
- `astropy/coordinates/builtin_frames/itrs_observed_transforms.py` (NEW file —
  the two direct Earth-fixed ↔ observer-centred conversions + their matrices /
  refraction)
- `astropy/coordinates/builtin_frames/itrs.py` (the Earth-fixed frame gains a
  `location` attribute)
- `astropy/coordinates/builtin_frames/intermediate_rotation_transforms.py` (the
  Earth-equatorial ↔ Earth-rotating conversions gain a `location=` so they
  honour a frame's site instead of forcing the centre of the Earth)
- `astropy/coordinates/builtin_frames/__init__.py` (registers the new module)

## 1. Symbol ↔ repo binding

| `Solution.lean` symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `itrsToObserved comp vx vy vz` | `itrs_to_observed(itrs_coo, observed_frame)` — `itrs_observed_transforms.py:258` (new) | modeled changed function (forward Earth-fixed → observer-centred conversion: a single DIRECT orthogonal-matrix apply on the given cartesian; no internal offset) |
| `observedToItrs comp ox oy oz` | `observed_to_itrs(observed_coo, itrs_frame)` — `itrs_observed_transforms.py:280` (new) | modeled changed function (backward observer-centred → Earth-fixed conversion: a single DIRECT transpose-matrix apply; no internal offset) |
| `observedRoundtrip comp vx vy vz` | composition `observed_to_itrs(itrs_to_observed(...))` exercised by the F2P round-trip tests | modeled composite (the exact round-trip identity the issue + F2P tests demand) |
| `fwdX/fwdY/fwdZ` *(axiom — A-consumed)* | the orthogonal orientation matrix `M` applied via `CartesianRepresentation.transform(M)`, with `M` the ITRS→AltAz / ITRS→HADec orientation composite (`itrs_observed_transforms.py:18,29`) | unchanged callee: the three components of `M · v` |
| `bwdX/bwdY/bwdZ` *(axiom — A-consumed)* | the same orientation matrix transposed, `CartesianRepresentation.transform(matrix_transpose(M))` (`matrix_utilities.matrix_transpose`, `matrix_utilities.py:29`) | unchanged callee: the three components of `Mᵀ · v` |
| `orth_x/orth_y/orth_z` *(axiom — A-consumed)* | the fact `Mᵀ (M v) = v` for the orthogonal `M` built from `rotation_matrix` (`matrix_utilities.py:40`) composed with orthogonal sign-flip diagonals | unchanged callee property: transpose of an orthogonal matrix is its inverse |
| `equToRot comp vx vy vz lx ly lz` | `cirs_to_itrs(cirs_coo, itrs_frame)` / `tete_to_itrs(tete_coo, itrs_frame)` — `intermediate_rotation_transforms.py:197,148` | modeled changed function (forward Earth-equatorial → Earth-rotating conversion that honours the frame's site: refer to `itrs_frame.location` not the centre of the Earth) |
| `rotToEqu comp ox oy oz lx ly lz` | `itrs_to_cirs(itrs_coo, cirs_frame)` / `itrs_to_tete(itrs_coo, tete_frame)` — `intermediate_rotation_transforms.py:212,161` | modeled changed function (backward Earth-rotating → Earth-equatorial conversion that carries the site: `location=itrs_coo.location` not geocentric) |
| `equRotRoundtrip comp vx vy vz lx ly lz` | composition `itrs_to_cirs(cirs_to_itrs(...))` exercised by `test_cirs_itrs_topo` and the through-intermediate no-refraction blocks | modeled composite (the topocentric round-trip identity the F2P tests demand) |
| `protX/protY/protZ` *(axiom — A-consumed)* | the precession-nutation matrix `P = cirs_to_itrs_mat(time)` / `tete_to_itrs_mat(time)` applied via `CartesianRepresentation.transform(P)` (`intermediate_rotation_transforms.py:200,156`) | unchanged callee: the three components of `P · v` |
| `protInvX/protInvY/protInvZ` *(axiom — A-consumed)* | the same precession matrix transposed, `CartesianRepresentation.transform(matrix_transpose(P))` (`intermediate_rotation_transforms.py:163,214`) | unchanged callee: the three components of `Pᵀ · v` |
| `prot_orth_x/prot_orth_y/prot_orth_z` *(axiom — A-consumed)* | the fact `Pᵀ (P v) = v` for the orthogonal precession matrix `P` | unchanged callee property: transpose of an orthogonal matrix is its inverse |
| `offsetX/offsetY/offsetZ` *(axiom — A-consumed)* | the viewpoint offset introduced by the re-referencing conversion `coo.transform_to(<same kind>(location=T))` when the source frame is anchored at site L and the target at site T | unchanged callee: the geocentric-vs-topocentric difference |
| `same_site_x/same_site_y/same_site_z` *(axiom — A-consumed)* | the fact `offset*(L, L) = 0`: re-referring to the SAME site is a no-op (the gold comments: "no-op if same obstime and location") | unchanged callee property: the re-referencing conversion is the identity at a fixed site |

The discriminating data flow the gold introduces (modeled in the impl regions):
- forward applies the orthogonal orientation matrix DIRECTLY to the given
  cartesian (`itrs_observed_transforms.py:268`); in the tested same-site /
  same-time path the early conditional block is a no-op, so there is no internal
  offset;
- backward applies the matrix-transpose DIRECTLY to the observer-centred
  cartesian (`itrs_observed_transforms.py:290`); the final re-reference (`:298`)
  is a no-op for the same site / time, so there is no internal offset added back.

The observer-offset arithmetic (subtract on the way in, add on the way out) is a
**caller-layer** operation, NOT part of either conversion. The problem
statement's draft put the offset *inside* the conversion; gold does not. The
model pins to gold (offset-free).

The pre-patch state (for the refinement audit, NOT referenced from the consumer
spec view): there was **no** direct Earth-fixed ↔ observer-centred conversion.
The path went Earth-fixed → (geocentric) intermediate → observer-centred, and
the intermediate ↔ Earth-rotating conversions forced the centre of the Earth
(`intermediate_rotation_transforms.py:151,201` pre-patch), so the route inserted
the geocentric-vs-topocentric directional shift. That indirect route did not
reproduce the direct orthogonal rotation. `Solution_prepatch.lean` reverts to
that indirect skeleton (the forward applies an extra intermediate-frame rotation
— `fwd (bwd v)` — instead of the direct `fwd v`), so it fails the direct
postcondition `out = fwdX vx vy vz`; and it reverts `equToRot` to refer to the
centre of the Earth (`offset*(L, 0)`), so it fails the offset-free postcondition
`out = protX vx vy vz`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a 3-D Cartesian position (`CartesianRepresentation` with `.x,.y,.z`, real `Quantity` components) | three components `vx, vy, vz` (one selected by `comp ∈ {0,1,2}`) | component `k` of the representation ↔ the `comp = k` value |
| the observer's geocentric Earth-fixed position (real components) | three components `lx, ly, lz` | component `k` ↔ the `comp = k` value |
| each real Cartesian component | exact `Int` | the tested behaviour is the **exact algebraic round-trip identity**; the real implementation reaches it only up to floating-point error, which the F2P tolerances (`atol=0.1*u.mas`, `10*u.cm`, default `assert_allclose`) absorb. The behaviour is precision-INDEPENDENT, so the component is modeled as an exact `Int` (NOT interpreted floats, whose IEEE `==` is non-reflexive on NaN and whose `(a-b)+b` does not cancel — the property would be unstatable). See refinement.md. |
| `crepr.transform(M)` (matrix-vector apply) | `fwdX/fwdY/fwdZ` (axiom) | the three components of `M · v` |
| `crepr.transform(matrix_transpose(M))` | `bwdX/bwdY/bwdZ` (axiom) | the three components of `Mᵀ · v` |
| `crepr.transform(P)` (precession matrix-vector apply) | `protX/protY/protZ` (axiom) | the three components of `P · v` |
| `crepr.transform(matrix_transpose(P))` | `protInvX/protInvY/protInvZ` (axiom) | the three components of `Pᵀ · v` |
| the observing site / frame `location` (`EarthLocation`) | three components `lx, ly, lz` | the site's Earth-fixed position; **the centre of the Earth** is exactly `(0., 0., 0.)` km in the repo, so it maps to `(0,0,0)` |
| the re-referencing conversion `coo.transform_to(<same kind>(location=T))` | additive integer offset `offset*(L, T)` carried after the rotation (equivalent since `P` is linear: `P(v+s) = P v + P s`) | the viewpoint shift inserted when re-referring from site L to site T; **zero** when `T = L` (`same_site_*`) |

`comp` is a pure selector: each modeled function returns the single integer
component the caller requests; the three-component object is recovered by ranging
`comp` over `{0,1,2}`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 The orientation matrix action `fwd*` / `bwd*` and orthogonality
**Callee:** `CartesianRepresentation.transform(M)` applies the 3×3 matrix `M`;
the new code builds `M` from `rotation_matrix(angle, axis)` composed with
sign-flip diagonal matrices:

```python
def itrs_to_altaz_mat(lon, lat):
    minus_x = np.eye(3); minus_x[0][0] = -1.0
    return minus_x @ rotation_matrix(NORTH_POLE - lat, 'y') @ rotation_matrix(lon, 'z')

def itrs_to_hadec_mat(lon):
    minus_y = np.eye(3); minus_y[1][1] = -1.0
    return minus_y @ rotation_matrix(lon, 'z')
```

`rotation_matrix` returns a **unitary rotation matrix** (`matrix_utilities.py:40`
docstring); each sign-flip diagonal is an orthogonal reflection. A product of
orthogonal matrices is orthogonal, so `M` is orthogonal: `Mᵀ M = I`. The backward
conversion applies `matrix_transpose(M)` (`matrix_utilities.py:29`), so
`bwd(fwd(v)) = Mᵀ (M v) = (Mᵀ M) v = v`. This is the **only** fact the proof
consumes about the unchanged matrix machinery, encoded as the `orth_*` axioms
(`bwdX (fwdX v) (fwdY v) (fwdZ v) = v_x`, and y, z), with `fwd*`/`bwd*` otherwise
uninterpreted. The axiom is the **weakest** contract sufficient for the
round-trip proof; it claims no specific matrix entry, sign, or angle.

**Soundness check (G-AX):** `axiom_check.py` builds the real orientation matrices
(`itrs_to_altaz_mat`, `itrs_to_hadec_mat`, `altaz_to_hadec_mat`) from the real
`rotation_matrix` over a grid of longitudes/latitudes (boundary + fuzz), computes
`Mᵀ (M v)` for randomized integer and real vectors `v`, and asserts it equals `v`
to floating-point tolerance — i.e. the orthogonality axiom holds for the actual
unchanged callees. It imports only `numpy` and the repo's `matrix_utilities`.

### 3.2 The precession-rotation action `prot*` / `protInv*` and `prot_orth_*`
**Callee:** `CartesianRepresentation.transform(P)` where `P` is the
precession-nutation matrix `cirs_to_itrs_mat(time)` / `tete_to_itrs_mat(time)`.
These matrices are products of ERFA polar-motion / Earth-rotation / precession
rotations (all orthogonal), so `P` is orthogonal: `Pᵀ P = I`. The backward
conversion applies `matrix_transpose(P)`, so `protInv(prot(v)) = Pᵀ (P v) = v`.
This is the only fact the proof consumes about the precession machinery, encoded
as `prot_orth_*`. These are an UNCHANGED callee: the gold patch does not touch
the matrix builders, only the *site* the surrounding conversion refers to.

**Soundness check (G-AX):** `axiom_check.py` builds the real `cirs_to_itrs_mat` /
`tete_to_itrs_mat` over several obstimes and asserts `Pᵀ P = I` and
`Pᵀ (P v) = v` to floating-point tolerance.

### 3.3 The re-referencing offset `offset*` and `same_site_*`
**Callee:** the re-referencing conversion
`coo.transform_to(<same-kind>(location=T))` between two frames of the same kind
anchored at sites L and T. When `T = L` this is the identity (the gold comments:
"no-op if same obstime and location"); when `T ≠ L` it inserts the
geocentric-vs-topocentric difference. The **only** fact the proof consumes is the
no-op at the same site, encoded as `same_site_*` (`offset*(L, L) = 0`); the offset
is otherwise uninterpreted. The gold change is exactly the SITE argument: the
frame's own location vs the pre-patch centre of the Earth. Because `P` is linear,
the model carries the offset additively *after* the rotation (`P(v+s) = P v +
P s`), which is equivalent and avoids an artificial nesting.

**Soundness check (G-AX):** `axiom_check.py` drives the REAL gold-patched
Earth-equatorial ↔ Earth-rotating conversions over the F2P topocentric sites and
asserts (i) re-referring to the same site has zero residual (`same_site_*` holds
— measured ~0 m), (ii) the topocentric round trip is the identity, and (iii)
forcing the centre of the Earth (the pre-patch target) introduces a detectably
nonzero offset on a topocentric witness, so the pre-patch behaviour is
demonstrably wrong. It imports only `numpy` and the repo `coordinates` package.
