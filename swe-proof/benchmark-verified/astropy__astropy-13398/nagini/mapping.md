# mapping.md — astropy__astropy-13398

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6500928dc0e57be8f06d1162eacc3ba5e2eff692`, states the type
abstraction, and gives the provenance of each axiomatized callee.

Repo files under change (gold patch):
- `astropy/coordinates/builtin_frames/itrs_observed_transforms.py` (NEW file —
  the two direct ITRS<->Observed transforms + their matrices/refraction)
- `astropy/coordinates/builtin_frames/itrs.py` (ITRS gains a `location`
  `EarthLocationAttribute`)
- `astropy/coordinates/builtin_frames/intermediate_rotation_transforms.py`
  (TETE/CIRS<->ITRS transforms gain `location=` so they honour an ITRS frame's
  location instead of forcing `EARTH_CENTER`)
- `astropy/coordinates/builtin_frames/__init__.py` (registers the new module)

## 1. Symbol <-> repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `itrs_to_observed(comp, vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt)` | `itrs_to_observed(itrs_coo, observed_frame)` — `itrs_observed_transforms.py:105` (new) | modeled changed function (forward Earth-fixed -> observer-centred conversion, TWO steps: refer the position to the OUTPUT (observer-centred) frame's own anchoring — `:106-110`, `itrs_coo.transform_to(ITRS(obstime=observed_frame.obstime, location=observed_frame.location))` — and THEN apply the orthogonal orientation matrix built from THAT frame's OWN site, `:112` `lon, lat, height = observed_frame.location.to_geodetic('WGS84')` then `:115`/`:121` `itrs_coo.cartesian.transform(itrs_to_altaz_mat(lon, lat))` / `itrs_to_hadec_mat(lon)`) |
| `observed_to_itrs(comp, ox,oy,oz, lx,ly,lz,esrc, tx,ty,tz,etgt)` | `observed_to_itrs(observed_coo, itrs_frame)` — `itrs_observed_transforms.py:127` (new) | modeled changed function (backward observer-centred -> Earth-fixed conversion, TWO steps in the MIRROR ORDER: apply the transpose of the orientation matrix built from the INPUT (observer-centred) frame's OWN site — `:129` `lon, lat, height = observed_coo.location.to_geodetic('WGS84')` then `:137`/`:139` `transform(matrix_transpose(itrs_to_altaz_mat(lon, lat)))` — and THEN refer the ROTATED position from the input frame's own anchoring to the output frame's, `:141-142` `ITRS(crepr, obstime=observed_coo.obstime, location=observed_coo.location)` then `:145` `.transform_to(itrs_frame)`) |
| `observed_roundtrip(comp, vx,vy,vz, lx,ly,lz, e)` | composition `observed_to_itrs(itrs_to_observed(...))` exercised by the F2P round-trip tests | modeled composite (the exact round-trip identity the issue + F2P tests demand: SAME site, SAME obstime on both frames) |
| `fwd_x/fwd_y/fwd_z(x,y,z,sx,sy,sz)` *(axiom — A-consumed)* | the orthogonal orientation matrix `M(S)` FOR THE SITE `S`, applied via `CartesianRepresentation.transform(M)`, with `M` = `itrs_to_altaz_mat(lon,lat)` / `itrs_to_hadec_mat(lon)` (`itrs_observed_transforms.py:18,29`) built from `S.to_geodetic('WGS84')` | unchanged callee: the three components of `M(S) @ v` |
| `bwd_x/bwd_y/bwd_z(x,y,z,sx,sy,sz)` *(axiom — A-consumed)* | the same site's orientation matrix transposed, `CartesianRepresentation.transform(matrix_transpose(M))` (`matrix_utilities.matrix_transpose`, `matrix_utilities.py:29`) | unchanged callee: the three components of `M(S)^T @ v` |
| `orthogonality(x,y,z,sx,sy,sz)` *(axiom — A-consumed)* | the mathematical fact `M(S)^T @ (M(S) @ v) == v` for the orthogonal `M(S)` built from `rotation_matrix` (`matrix_utilities.py:40`) and orthogonal sign-flip diagonals — AT ONE AND THE SAME site `S`; nothing is claimed across sites | unchanged callee property: transpose of an orthogonal matrix is its inverse |
| `equ_to_rot(comp, vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt)` | `cirs_to_itrs(cirs_coo, itrs_frame)` / `tete_to_itrs(tete_coo, itrs_frame)` — `intermediate_rotation_transforms.py:197,147` | modeled changed function (forward Earth-equatorial -> Earth-rotating conversion: refer the position to the OUTPUT frame's own anchoring — `intermediate_rotation_transforms.py:200-201`, `CIRS(obstime=itrs_frame.obstime, location=itrs_frame.location)`, gold, vs. the base's `location=EARTH_CENTER` — and THEN rotate with the matrix for the OUTPUT frame's epoch, `:204` `pmat = cirs_to_itrs_mat(itrs_frame.obstime)`) |
| `rot_to_equ(comp, ox,oy,oz, lx,ly,lz,esrc, tx,ty,tz,etgt)` | `itrs_to_cirs(itrs_coo, cirs_frame)` / `itrs_to_tete(itrs_coo, tete_frame)` — `intermediate_rotation_transforms.py:209,159` | modeled changed function (backward Earth-rotating -> Earth-equatorial conversion, MIRROR ORDER: rotate with the transpose for the INPUT frame's epoch — `:212` `pmat = cirs_to_itrs_mat(itrs_coo.obstime)` — and THEN refer the rotated position from the input frame's own anchoring to the output frame's, `:214` `CIRS(newrepr, obstime=itrs_coo.obstime, location=itrs_coo.location)` then `:217` `.transform_to(cirs_frame)`; the base built that intermediate frame with no `location=`, i.e. the default centre) |
| `equ_rot_roundtrip(comp, vx,vy,vz, lx,ly,lz, e)` | composition `itrs_to_cirs(cirs_to_itrs(...))` (and the `_add_merged_transform(ITRS, CIRS, ITRS)` loopback, `:276`) exercised by `test_cirs_itrs_topo` and the through-ITRS no-refraction blocks | modeled composite (the topocentric round-trip identity the F2P tests demand: SAME site, SAME obstime on both frames) |
| `prot_x/prot_y/prot_z(x,y,z,e)` *(axiom — A-consumed)* | the Earth-orientation matrix `pmat = cirs_to_itrs_mat(e)` / `tete_to_itrs_mat(e)` FOR THE EPOCH `e`, applied via `CartesianRepresentation.transform(pmat)` (`intermediate_rotation_transforms.py:204,152`) | unchanged callee: the three components of `P(e) @ v` |
| `prot_inv_x/prot_inv_y/prot_inv_z(x,y,z,e)` *(axiom — A-consumed)* | the same matrix for the epoch `e` transposed, `CartesianRepresentation.transform(matrix_transpose(pmat))` (`intermediate_rotation_transforms.py:213,166`) | unchanged callee: the three components of `P(e)^T @ v` |
| `prot_orthogonality(x,y,z,e)` *(axiom — A-consumed)* | the fact `P(e)^T @ (P(e) @ v) == v` for the orthogonal `P(e)` — AT ONE AND THE SAME epoch `e`; nothing is claimed across epochs | unchanged callee property: transpose of an orthogonal matrix is its inverse |
| `offset_x/offset_y/offset_z(vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt)` *(axiom — A-consumed)* | the componentwise change the re-referencing transform `coo.transform_to(<same kind>(obstime=etgt, location=T))` makes to the position `v` when `coo` is that same kind of frame anchored at site L at epoch `esrc`: `CIRS(v, obstime=esrc, location=L).transform_to(CIRS(obstime=etgt, location=T)).cartesian - v` (the SSB-tied route) | unchanged callee: the re-referencing shift (the geocentric-vs-topocentric aberration difference plus the epoch's precession/aberration difference). Depends on the POSITION and on BOTH anchorings |
| `same_frame_noop(vx,vy,vz, lx,ly,lz, e)` *(axiom — A-consumed)* | the fact `offset_*(v, L,e, L,e) == 0`: referring between two frames of IDENTICAL anchoring is a no-op (the gold comments at `:199,213`: "no-op if same obstime and location") | unchanged callee property: the re-referencing transform is the identity between frames with the same site AND the same obstime — and ONLY there (G-AX runs the two controls) |
| `rebased_x/rebased_y/rebased_z(vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt)` *(`pure` region — spec)* | the position after that re-referencing: `<same kind>(v, obstime=esrc, location=L).transform_to(<same kind>(obstime=etgt, location=T)).cartesian` | `v_c + offset_c(...)`; a naming convenience, no new assumption |

The discriminating data flow the gold introduces (modeled in the impl regions).
BOTH conversion pairs are two-step and anchoring-honouring, and the two
directions of each pair use OPPOSITE orders:
- the direct pair's forward conversion FIRST refers the position to the OUTPUT
  (observer-centred) frame's own anchoring (`itrs_observed_transforms.py:106-110`:
  `if np.any(itrs_coo.location != observed_frame.location) or
  np.any(itrs_coo.obstime != observed_frame.obstime): itrs_coo =
  itrs_coo.transform_to(ITRS(obstime=observed_frame.obstime,
  location=observed_frame.location))`) and THEN applies the orientation matrix
  built from THAT frame's own site (`:112` `observed_frame.location.to_geodetic
  ('WGS84')`, `:115`/`:121` the `transform(...)` call);
- the direct pair's backward conversion FIRST applies the transpose of the matrix
  built from the INPUT (observer-centred) frame's own site (`:129`
  `observed_coo.location.to_geodetic('WGS84')`, `:137`/`:139`) and THEN refers the
  ROTATED position from the input frame's own anchoring to the output frame's
  (`:141-142` `ITRS(crepr, obstime=observed_coo.obstime,
  location=observed_coo.location)`, `:145` `.transform_to(itrs_frame)`).

So the two ends of the direct pair read OPPOSITE ends of the conversion for the
orientation matrix — always the observer-centred frame's own site, which is the
output in one direction and the input in the other — and both re-referencing
steps have named, non-interchangeable endpoints. All four facts are pinned:
that the re-referencing happens, both of its endpoints, the site the matrix is
built from, and the order of the two steps.

The observer-offset arithmetic (subtract on the way in, add on the way out) is a
**caller-layer** operation, NOT part of either transform: the F2P test
`test_itrs_straight_overhead` forms `itrs_repr = itrs_geo - obsrepr` itself, and
the addition back is the `EarthLocation` / ITRS-frame arithmetic. The problem
statement's draft put that observer offset *inside* the transform; gold does not,
and the model does not model it. (This is a DIFFERENT quantity from the
anchoring re-referencing above, which gold does perform inside both transforms.)

Two anchoring carriers per pair, all observable. Every frame involved carries its
own site and its own obstime (`itrs.py:68` gold adds `location =
EarthLocationAttribute(default=EARTH_CENTER)` to ITRS; `cirs.py:36`, `altaz.py`
and `hadec.py` already had one). Nothing makes the two agree, so the model gives
each pair two independent anchorings — source `(L, esrc)` and target `(T, etgt)`
— and the postconditions name which one each step uses:
- `itrs_to_observed` refers the position to `(T, etgt)` FIRST, then rotates with
  `M(T)` (gold `:106-110` then `:112,115,121`);
- `observed_to_itrs` rotates with `M(L)^T` FIRST, then refers from `(L, esrc)` to
  `(T, etgt)` (gold `:129,137,139` then `:141-142,145`);
- `equ_to_rot` refers the position to `(T, etgt)` FIRST, then rotates at `etgt`
  (gold `intermediate_rotation_transforms.py:200-201` then `:204`);
- `rot_to_equ` rotates at `esrc` FIRST, then refers from `(L, esrc)` to
  `(T, etgt)` (gold `:212` then `:214,217`).
The order genuinely differs between the two directions of each pair, and the
site/epoch each step uses genuinely differs; all of it is pinned. Each round-trip
composite is the special case `L == T`, `esrc == etgt` — the one the F2P tests
exercise — where the offset provably vanishes.

The pre-patch state (for the refinement audit, NOT referenced from the consumer
spec view): there was **no** direct ITRS<->Observed transform. The path went
ITRS -> (geocentric) CIRS -> Observed, and the CIRS<->ITRS transforms forced
`location=EARTH_CENTER` (`intermediate_rotation_transforms.py:151,201` pre-patch),
so the route inserted the geocentric-vs-topocentric stellar-aberration shift
(the test comment: "If the CIRS self-transform breaks it won't, due to improper
treatment of aberration"). That indirect, aberration-altering route did not
reproduce the direct orthogonal rotation, and it had no anchoring re-referencing
of its own. `model_prepatch.py` reverts to that skeleton in all FOUR impl
regions, so it fails four postconditions:
- `itrs_to_observed` applies an extra intermediate-frame rotation —
  `fwd_*(bwd_*(v))` — instead of applying the matrix to the RE-REFERRED
  position, and performs no re-referencing at all;
- `observed_to_itrs` returns the rotated position un-referred, instead of
  referring it from the input frame's anchoring to the output frame's;
- `equ_to_rot` refers the position to the CONSTANT site `(0,0,0)` (the centre of
  the Earth) instead of the output frame's own site `T`;
- `rot_to_equ` refers the rotated position FROM the constant site `(0,0,0)`
  instead of from the input frame's own site `L`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a 3-D Cartesian position (`CartesianRepresentation` with `.x,.y,.z`, real `Quantity` components) | three components `vx, vy, vz` (one selected by `comp` in {0,1,2}) | component `k` of the representation <-> the `comp == k` value |
| the observer's geocentric ITRS position (`observed_frame.location.get_itrs().cartesian`, real components) | three components `lx, ly, lz` | component `k` <-> the `comp == k` value |
| each real Cartesian component | exact `int` | the tested behaviour is the **exact algebraic round-trip identity**; the real implementation reaches it only up to floating-point error, which the F2P tolerances (`atol=0.1*u.mas`, `10*u.cm`, default `assert_allclose`) absorb. The behaviour is precision-INDEPENDENT, so per SPEC_GUIDE §2 the component is modeled as an exact `int` (NOT interpreted floats, whose IEEE `==` is non-reflexive on NaN and whose `(a-b)+b` does not cancel — the property would be unstatable). See refinement.md. |
| vector subtraction `itrs_coo.cartesian - location.get_itrs().cartesian` | integer `-` componentwise (`vx - lx`, ...) | exact |
| vector addition `topocentric + location.get_itrs().cartesian` | integer `+` componentwise (`... + lx`) | exact |
| `crepr.transform(M)` (matrix-vector apply), `M` built from the observing site `S` | `fwd_x/fwd_y/fwd_z(x,y,z,sx,sy,sz)` (axiom) | the three components of `M(S) @ v`, with `(sx,sy,sz)` the site carrier |
| `crepr.transform(matrix_transpose(M))` | `bwd_x/bwd_y/bwd_z(x,y,z,sx,sy,sz)` (axiom) | the three components of `M(S)^T @ v` |
| `crepr.transform(cirs_to_itrs_mat(t))` (Earth-orientation matrix apply) | `prot_x/prot_y/prot_z(x,y,z,e)` (axiom) | the three components of `P(e) @ v`, with `e` the epoch carrier |
| `crepr.transform(matrix_transpose(cirs_to_itrs_mat(t)))` | `prot_inv_x/prot_inv_y/prot_inv_z(x,y,z,e)` (axiom) | the three components of `P(e)^T @ v` |
| the observing site / frame `location` (`EarthLocation`) | three components `lx, ly, lz` (source site L) and `tx, ty, tz` (target site T) | the site's ITRS position; **the centre of the Earth** (`EARTH_CENTER`) is exactly `(0., 0., 0.)` km in the repo (`utils.EARTH_CENTER`), so it maps to `(0,0,0)` |
| a frame's `obstime` (`Time`) | one `int` epoch TAG (`esrc`, `etgt`, `e`) | an opaque identity token, not a date: the model needs only "same epoch or not", since `prot_*`/`offset_*` are uninterpreted per epoch. Two tags are equal iff the two `Time`s are. `conformance_check.py` realises the tags with a fixed tag -> `Time` table |
| the re-referencing transform `coo.transform_to(<same kind>(obstime=etgt, location=T))` | additive integer offset `offset_*(v, L,esrc, T,etgt)` applied to the position at the point in the pipeline where the real code does the `transform_to` | the shift inserted when referring the position `v` from the frame anchored at `(L, esrc)` to the frame anchored at `(T, etgt)`; **zero** when the two anchorings are IDENTICAL (`same_frame_noop`), and (measured by G-AX) detectably nonzero when either the site or the epoch differs |

`comp` is a pure selector: each modeled function returns the single integer
component the caller requests; the three-component object is recovered by
ranging `comp` over {0,1,2}.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 The orientation matrix action `fwd_*` / `bwd_*` and orthogonality
**Callee:** `CartesianRepresentation.transform(M)` applies the 3x3 matrix `M`;
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
docstring: "A unitary rotation matrix"; it is built from `sin`/`cos` of the
angle, the standard SO(3) generator). Each `minus_x`/`minus_y` is an orthogonal
reflection (`diag(-1,1,1)` / `diag(1,-1,1)`). A product of orthogonal matrices
is orthogonal, so `M` is orthogonal: `M^T M = I`. The backward transform applies
`matrix_transpose(M)` (`matrix_utilities.py:29`, `.swapaxes(-2,-1)`), so
`bwd(fwd(v)) = M^T (M v) = (M^T M) v = v`. This is the **only** fact the proof
consumes about the unchanged matrix machinery, encoded as the `orthogonality`
axiom

  `bwd_x(fwd_x(v,S),fwd_y(v,S),fwd_z(v,S),S) == v_x` (and y, z),

with `fwd_*`/`bwd_*` otherwise uninterpreted (the proof never needs their
explicit entries — only that the transpose-action inverts the forward-action).
The axiom is the **weakest** contract sufficient for the round-trip proof; it
does not over-claim any specific matrix entry, sign, or angle.

**Scope: one site.** `fwd_*`, `bwd_*` and `orthogonality` all carry the SITE the
matrix is built from, and the axiom relates the forward and transpose actions
only **at the same `S`**. Nothing is claimed about `M(S')^T (M(S) v)` for
`S' != S` — because nothing true could be: the two observatories' horizons differ
by the angle between them. That single-site scope is what makes a rival that
builds the matrix from the wrong end of the conversion unprovable rather than
merely inelegant. The site carrier is load-bearing because gold builds the matrix
from the OBSERVER-CENTRED frame's own site at whichever end that frame sits:
`observed_frame.location` forward (`itrs_observed_transforms.py:112`) and
`observed_coo.location` backward (`:129`).

**Soundness check (G-AX):** `axiom_check.py` builds the real orientation
matrices (`itrs_to_altaz_mat`, `itrs_to_hadec_mat`) from the real
`rotation_matrix` over a grid of longitudes/latitudes (boundary + fuzz),
computes `M^T (M v)` for randomized integer and real vectors `v`, and asserts it
equals `v` to floating-point tolerance — i.e. the orthogonality axiom holds for
the actual unchanged callees. It then runs the site CONTROL: the CROSS-SITE
composition `M(S')^T (M(S) v)` misses `v` by a detectably large margin on a
topocentric witness, so the site carrier is observable and a site-free axiom
would be UNSOUND. It imports only `numpy` and the repo's `matrix_utilities` (the
unchanged module the new code calls); nothing from the changed transforms.

### 3.2 The Earth-orientation rotation `prot_*` / `prot_inv_*` and `prot_orthogonality`
**Callee:** `CartesianRepresentation.transform(pmat)` where `pmat` is the
Earth-orientation matrix `cirs_to_itrs_mat(time)` / `tete_to_itrs_mat(time)`.
These matrices are products of ERFA polar-motion / Earth-rotation / precession
rotations (all orthogonal), so `pmat` is orthogonal: `pmat^T pmat = I`. The
backward transform applies `matrix_transpose(pmat)`, so
`prot_inv(prot(v, e), e) = P(e)^T (P(e) v) = v`. This is the only fact the proof
consumes about that machinery, encoded as `prot_orthogonality`. These are an
UNCHANGED callee: the gold patch does not touch the matrix builders, only the
*anchoring* the surrounding transform refers the position to.

**Scope: one epoch.** `prot_*` and `prot_inv_*` carry an EPOCH argument `e`, and
the axiom relates the forward and transpose actions only **at the same `e`**.
Nothing is claimed about `P(e')^T (P(e) v)` for `e' != e` — because nothing true
could be: the Earth rotates. That single-epoch scope is what makes a rival that
builds the matrix from the wrong frame's obstime unprovable rather than merely
inelegant.

**Soundness check (G-AX):** `axiom_check.py` builds the real `cirs_to_itrs_mat`
/ `tete_to_itrs_mat` over five obstimes and asserts `pmat^T pmat == I` and
`pmat^T (pmat v) == v` to floating-point tolerance. It then runs the epoch
CONTROL: the cross-epoch composition `P(e')^T (P(e) v)` misses `v` by a
detectably large margin on a topocentric witness, so the epoch carrier is
observable and a quantified cross-epoch axiom would be UNSOUND. (Measured: 8
cross-epoch controls, all beyond the 1 m detection floor.)

### 3.3 The re-referencing offset `offset_*` and `same_frame_noop`
**Callee:** the re-referencing transform
`coo.transform_to(<same-kind>(obstime=etgt, location=T))` between two frames of
the same kind, where `coo` is anchored at site `L` at epoch `esrc`. The model
uses ONE offset family for both conversion pairs, and "the same kind" is the kind
the conversion under test re-references between: **CIRS->CIRS** for the
Earth-equatorial pair (gold `intermediate_rotation_transforms.py:200-201, :214`)
and **ITRS->ITRS** for the direct Earth-fixed <-> observer-centred pair (gold
`itrs_observed_transforms.py:109-110` forward and `:141-145` backward). G-AX
validates the axiom and both controls at BOTH instances; G-CONF binds the shadow
to the matching one for each conversion. The model binds

    offset_*(v, L, esrc, T, etgt)
        = CIRS(v, obstime=esrc, location=L)
            .transform_to(CIRS(obstime=etgt, location=T)).cartesian - v

componentwise. Note it depends on the POSITION `v` as well as both anchorings —
stellar aberration is direction- and distance-dependent, so an offset modeled as
position-independent would be unsound (and would leave the model unable to
distinguish `rot_to_equ`'s order from `equ_to_rot`'s).

When BOTH anchorings agree this is the identity — the gold comments say so
explicitly at `intermediate_rotation_transforms.py:199,213` ("no-op if same
obstime and location") and gold's `itrs_observed_transforms.py:106` guards the
forward re-reference with exactly that test (`if observed_frame.location !=
itrs_coo.location or observed_frame.obstime != itrs_coo.obstime`), taking the
branch only when the anchorings differ; when the site differs it inserts the
geocentric-vs-topocentric aberration difference, and when the epoch differs it
inserts that epoch's own precession/aberration difference. The **only** fact the
proof consumes is the no-op at the identical anchoring, encoded as
`same_frame_noop` (`offset_*(v, L, e, L, e) == 0`); the offset is otherwise
uninterpreted. The gold change is exactly those two arguments:
`obstime=itrs_frame.obstime, location=itrs_frame.location` (honour the OUTPUT
frame's anchoring — `intermediate_rotation_transforms.py:200-201`) and
`obstime=itrs_coo.obstime, location=itrs_coo.location` (honour the INPUT frame's
— `:214`), vs. the base's `location=EARTH_CENTER` / absent `location=`. The
observer-centred pair carries the same two arguments on its own two sides:
`ITRS(obstime=observed_frame.obstime, location=observed_frame.location)` (honour
the OUTPUT frame's — `itrs_observed_transforms.py:108-110`) and
`ITRS(crepr, obstime=observed_coo.obstime, location=observed_coo.location)` then
`.transform_to(itrs_frame)` (honour the INPUT frame's, then land on the requested
one — `:141-145`). Both rest on gold's new `location = EarthLocationAttribute(
default=EARTH_CENTER)` frame attribute on `ITRS` (`itrs.py:68`), which is what
makes an ITRS frame carry a site at all.

The model applies the offset additively at the point in the pipeline where the
real code performs the `transform_to`: BEFORE the rotation in `equ_to_rot`
(matching gold's `intermediate_rotation_transforms.py:200-201` then `:204`) and
AFTER it in `rot_to_equ` (matching `:212` then `:214,217`); BEFORE the rotation in
`itrs_to_observed` (matching gold's `itrs_observed_transforms.py:106-110` then
`:112,115,121`) and AFTER it in `observed_to_itrs` (matching `:129,137,139` then
`:141-142,145`). The two orders are NOT interchangeable — the offset is
position-dependent, so `P(v + s(v)) != P(v) + s(P(v))` in general — which is why
the order-swap rivals in `properties.py` (one per pair) are rejected rather than
accepted as equivalent spellings.

**Soundness check (G-AX):** `axiom_check.py` drives the REAL gold-patched
same-kind re-referencing transform over the F2P topocentric sites and asserts, at
**each of the two instances the model binds the offset to** — CIRS->CIRS for the
Earth-equatorial pair and ITRS->ITRS for the observer-centred pair, the latter on
a witness produced by the real `CIRS@(L,e) -> ITRS@(L,e)` transform — (i) the
axiom: referring between two frames of IDENTICAL anchoring has zero residual
(`same_frame_noop` holds, worst residual reported in the gate summary and asserted
under 1e-3 m), (ii) CONTROL, changing the target SITE alone moves the position by
more than the 1 m detection floor, (iii) CONTROL, changing the target EPOCH alone
likewise — so neither carrier is decorative at either instance, and the axiom does
not extend past the identical-anchoring case it is stated for. It further asserts
(iv) the topocentric round-trips CIRS@(L,e) -> ITRS@(L,e) -> CIRS@(L,e) and
ITRS@(L,e) -> ITRS@(L,e) are the identity (the behaviour the issue demands), and
(v) referring to the centre of the Earth instead of the frame's own site is a
detectably different position on every off-centre witness, so a conversion that
used a constant site would be observably wrong. It imports only `numpy` and the
repo `coordinates` package.
