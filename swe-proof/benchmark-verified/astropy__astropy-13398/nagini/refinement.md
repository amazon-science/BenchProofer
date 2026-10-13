# refinement.md — astropy__astropy-13398

The operation-by-operation correspondence between `model.py`'s implementation
(the `itrs_to_observed`, `observed_to_itrs`, `observed_roundtrip`, `equ_to_rot`,
`rot_to_equ`, and `equ_rot_roundtrip` impl regions, plus the consumed
`orthogonality` / `fwd_*` / `bwd_*` / `prot_orthogonality` / `prot_*` /
`same_frame_noop` / `offset_*` axioms and the `rebased_*` spec helpers) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses this axiom's `Ensures`), **A-reference** (a deep
model validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested round-trip inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## 0. Provenance note — model the GOLD, not the issue's draft

The problem statement embeds a **draft** implementation in which the forward
transform subtracts the observer's ITRS position *inside* the transform
(`topocentric_itrs_repr = itrs_coo.cartesian - observed_frame.location.get_itrs().cartesian`)
and the backward adds it back. The **merged gold** transform does NOT do this:
that observer-position arithmetic lives in the **caller** (the F2P test forms
`itrs_repr = itrs_geo - obsrepr`, and the addition back comes via the round trip /
the `EarthLocation` arithmetic). This document and the spec pin to the gold
transform, never to the draft.

Gold does, however, carry a step of its own that the draft does not, and it must
not be confused with the draft's subtraction: **an anchoring re-reference**. The
gold forward begins by referring the position into the output frame's own
`(obstime, location)` whenever the two frames' anchorings differ
(`itrs_observed_transforms.py:106-110`), and the gold backward ends by referring
the rotated position out of the input frame's own `(obstime, location)` onto the
requested one (`:141-145`). That step is a shift of the position (it routes
through CIRS and alters stellar aberration, as gold's own comments at `:108` and
`:144` say), it is position-dependent, and it vanishes exactly when both
anchorings agree. The spec therefore models each direction as **two** steps in a
definite order, not as a bare rotation; see §A, §B and §D.

## A. Forward transform — `itrs_to_observed`

Verbatim gold (`itrs_observed_transforms.py:105-122`, the whole function; the
refraction branch is scoped out in §D):
```
105  def itrs_to_observed(itrs_coo, observed_frame):
106      if (np.any(itrs_coo.location != observed_frame.location) or
107              np.any(itrs_coo.obstime != observed_frame.obstime)):
108          # This transform will go through the CIRS and alter stellar aberration.
109          itrs_coo = itrs_coo.transform_to(ITRS(obstime=observed_frame.obstime,
110                                                location=observed_frame.location))
112      lon, lat, height = observed_frame.location.to_geodetic('WGS84')
115          crepr = itrs_coo.cartesian.transform(itrs_to_altaz_mat(lon, lat))
121          crepr = itrs_coo.cartesian.transform(itrs_to_hadec_mat(lon))
122      return observed_frame.realize_frame(crepr)
```
Two steps, in this order: **refer** the position to the OUTPUT frame's own
anchoring (`:106-110`), **then rotate** it with the orientation matrix built from
that same OUTPUT frame's own site (`:112` reads `observed_frame.location`, and
`:115`/`:121` feed its `lon`/`lat` to the matrix builder). Nothing requires the
input frame's anchoring to equal the output frame's; when they do agree, `:106`'s
guard is false and the re-reference contributes nothing.

| # | model.py impl op (`itrs_to_observed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | components `vx,vy,vz`; source site `lx,ly,lz` + epoch `esrc`; target site `tx,ty,tz` + epoch `etgt`; `comp` selector | `itrs_coo.cartesian` (.x,.y,.z); `(itrs_coo.obstime, itrs_coo.location)` and `(observed_frame.obstime, observed_frame.location)` | R | exact-real components <-> exact `int`; each site is an integer triple; each obstime is an opaque integer epoch TAG (equal iff the `Time`s are); the centre of the Earth (`EARTH_CENTER`, the `location` default gold adds at `itrs.py:68`) <-> `(0,0,0)` (mapping.md §2). |
| A2 | step 1: `wx = vx + offset_x(vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt)` (== `rebased_x(...)`) | `:106-110` `itrs_coo.transform_to(ITRS(obstime=observed_frame.obstime, location=observed_frame.location))` | A-consumed | the same-kind re-referencing transform is an UNCHANGED callee; `offset_*` is bound to the componentwise change it makes to the position, at the ITRS<->ITRS instance (mapping.md §3.3), depending on the position and BOTH anchorings. Gold's `if` at `:106` takes the branch exactly when the anchorings differ, which is precisely the `same_frame_noop` scoping. |
| A3 | step 2: `fwd_x/fwd_y/fwd_z(wx,wy,wz, tx,ty,tz)` | `:112,115,121` `observed_frame.location.to_geodetic('WGS84')` then `itrs_coo.cartesian.transform(itrs_to_altaz_mat(lon,lat))` (or `itrs_to_hadec_mat(lon)`) | A-consumed | the orthogonal matrix-vector apply is an unchanged callee (`CartesianRepresentation.transform` of the `rotation_matrix` composite); axiomatized as the three components of `M(S) @ v`, indexed by the SITE `S` the matrix is built from. The site argument is `tx,ty,tz` because `:112` reads the OUTPUT frame's own `location`. Applied to the RE-REFERRED position `w`, matching gold, where `:115` reads the `itrs_coo` rebound at `:109`. G-AX checks orthogonality at one site against the real matrices and CONTROLS that a cross-site composition is detectably not the identity (mapping.md §3.1). |

## B. Backward transform — `observed_to_itrs`

Verbatim gold (`itrs_observed_transforms.py:127-145`):
```
127  def observed_to_itrs(observed_coo, itrs_frame):
129      lon, lat, height = observed_coo.location.to_geodetic('WGS84')
137          crepr = crepr.transform(matrix_transpose(itrs_to_altaz_mat(lon, lat)))
139          crepr = observed_coo.cartesian.transform(matrix_transpose(itrs_to_hadec_mat(lon)))
141      itrs_at_obs_time = ITRS(crepr, obstime=observed_coo.obstime,
142                              location=observed_coo.location)
143      # This final transform may be a no-op if the obstimes and locations are the same.
144      # Otherwise, this transform will go through the CIRS and alter stellar aberration.
145      return itrs_at_obs_time.transform_to(itrs_frame)
```
The same two steps in the OPPOSITE order: **rotate** with the transpose of the
matrix built from the INPUT frame's own site (`:129` reads
`observed_coo.location`; `:137`/`:139`), **then refer** the rotated position out
of the input frame's own anchoring (`:141-142`) onto whatever `itrs_frame` carries
(`:145`).

| # | model.py impl op (`observed_to_itrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | step 1: `wx = bwd_x(ox,oy,oz, lx,ly,lz)` | `:129,137,139` `observed_coo.cartesian.transform(matrix_transpose(M(lon,lat)))` | A-consumed | the transpose-action (inverse rotation) is the unchanged `matrix_transpose` + `transform` callees; axiomatized as the three components of `M(S)^T @ v`. The site argument is `lx,ly,lz` because `:129` reads the INPUT frame's own `location` — the opposite end from the forward direction's `:112`. |
| B2 | step 2: `wx + offset_x(wx,wy,wz, lx,ly,lz,esrc, tx,ty,tz,etgt)` (== `rebased_x(bwd_*(o,L), ...)`) | `:141-145` `ITRS(crepr, obstime=observed_coo.obstime, location=observed_coo.location).transform_to(itrs_frame)` | A-consumed / I | same unchanged callee as A2, but applied AFTER the rotation and to the ROTATED position — matching gold's order exactly. The nesting in the postcondition (`rebased_*` OF `bwd_*`) is what pins the order. |

The observer-position arithmetic of the issue's draft (subtract on the way in, add
on the way out) remains a **caller-layer** operation and is not part of either
transform (§0). What IS inside both transforms is the anchoring re-reference above,
and each direction applies it at its own end of the pipeline.

## C. Round-trip identity — `observed_roundtrip` (the tested guarantee)

Gold: the F2P tests `test_itrs_straight_overhead`, `test_cirs_itrs_topo`, and
the **no-pressure** round-trip blocks of
`test_itrs_topo_to_{altaz,hadec}_with_refraction` (the `altaz_frame1` /
`hadec_frame1` frames) require that converting an ITRS position to Observed and
back is the **exact** identity (default `assert_allclose`, e.g.
`assert_allclose(itrs11.x, itrs.x)` and Alt=90° exactly to `1*u.uas`).

The round trip is taken at ONE shared anchoring `(L, e)` — both frames carry the
same site and the same epoch, which is what the tests set up — so each leg's
re-referencing step is an instance of `same_frame_noop` and contributes nothing.

| # | model.py impl op (`observed_roundtrip`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `same_frame_noop(v, L, e)` -> `q = rebased_*(v, L,e, L,e) == v` | `:106`'s guard is FALSE for a same-anchoring pair, so the block at `:107-110` is skipped | A-consumed | the outbound leg's re-reference is between identical anchorings, hence zero (mapping.md §3.3). This is where the `same_frame_noop` axiom, and only it, is consumed. |
| C2 | `ox,oy,oz = fwd_*(q, lx,ly,lz)`, asserted `== itrs_to_observed(k, v, L,e, L,e)` | the forward transform output | I | the round trip composes the two modeled functions exactly as the tests chain `transform_to(AltAz)` / `transform_to(ITRS)`; the site handed to the matrix is the shared one, which is simultaneously "the output frame's" (A3) and "the input frame's" (B1). |
| C3 | `orthogonality(q, lx,ly,lz)` -> `bwd_*(fwd_*(q, L), L) == q` | `M(S)^T (M(S) v) = v` for the orthogonal `M(S)` at ONE site `S` | A-consumed | the inverse-rotation fact, scoped to a single site (mapping.md §3.1). |
| C4 | `same_frame_noop(w, L, e)` -> `rebased_*(w, L,e, L,e) == w`, then `observed_to_itrs(comp, o, L,e, L,e) == v_comp` | `:145`'s final `transform_to(itrs_frame)` is the no-op gold's comment at `:143` describes | A-consumed / I | the return leg's re-reference is likewise between identical anchorings; with C3 recovering `q` and C1 giving `q == v`, the backward conversion returns the original position. |

Two independent things make the round trip the exact identity, and the spec pins
both. First, the **DIRECT** orthogonal-rotation pair (forward `M(S)`, backward
`M(S)^T`, both built from the shared site): `model_prepatch.py` reverts the
forward transform to the pre-patch **indirect** skeleton — there was no direct
ITRS->Observed rotation, so the observer-centred orientation was reached by
routing through an intermediate (geocentric) frame, which inserts an extra frame
rotation (`fwd_*(bwd_*(v))` rather than `fwd_*(v)`) — the viewpoint-dependent
stellar-aberration shift the issue describes ("If the CIRS self-transform breaks
it won't, due to improper treatment of aberration"). That indirect result is not
the direct orthogonal rotation, so it **fails** the frozen postcondition of
`itrs_to_observed`, exactly the spec sensing the missing direct path (G-DIFF).
Second, both legs must re-reference between the anchorings the conversion is
actually given, so that at a shared anchoring the shift is provably zero: a
conversion that re-referred to a CONSTANT site instead would leave a residual even
there, which is the geocentric-vs-topocentric error the issue reports. Both
failure modes are cases in `properties.py`
(`indirect-route-prepatch-forward`, `dropped-rereference-forward`,
`constant-site-forward`) and all are rejected.

## C2. Anchoring-honouring transform pair — `equ_to_rot` / `rot_to_equ` / `equ_rot_roundtrip`

Gold (`intermediate_rotation_transforms.py:147-167,197-217`): the pre-existing
Earth-equatorial <-> Earth-rotating repo transforms (`tete_to_itrs` /
`itrs_to_tete` / `cirs_to_itrs` / `itrs_to_cirs`) are changed so that they refer
the position to the *frame's own anchoring* — its own site AND its own obstime —
instead of forcing the centre of the Earth. Verbatim gold, `cirs_to_itrs`:

```
199    # first get us to a CIRS frame with the right attributes (which is
200    cirs_coo2 = cirs_coo.transform_to(CIRS(obstime=itrs_frame.obstime,
201                                          location=itrs_frame.location))   # was location=EARTH_CENTER
204    pmat = cirs_to_itrs_mat(itrs_frame.obstime)
205    crepr = cirs_coo2.cartesian.transform(pmat)
```

and `itrs_to_cirs`:

```
212    pmat = cirs_to_itrs_mat(itrs_coo.obstime)
213    newrepr = itrs_coo.cartesian.transform(matrix_transpose(pmat))
214    cirs = CIRS(newrepr, obstime=itrs_coo.obstime, location=itrs_coo.location)   # was geocentric
217    return cirs.transform_to(cirs_frame)
```

Read them side by side and three separate facts are visible, all three of which
the model now pins:

1. **The re-referencing step happens, and to which anchoring.** The forward
   direction refers the position to the OUTPUT frame's `(obstime, location)`
   (`:200-201`); the backward direction refers it FROM the INPUT frame's
   `(obstime, location)` (`:214`) to whatever `cirs_frame` carries (`:217`).
2. **The ORDER differs between the two directions.** Forward: refer, then rotate
   (`:200-201` precede `:205`). Backward: rotate, then refer (`:213` precedes
   `:214,217`). The two are not interchangeable, because the re-referencing shift
   is direction- and distance-dependent (stellar aberration), i.e. a function of
   the position it is applied to.
3. **Which EPOCH the rotation uses.** Forward builds `pmat` from
   `itrs_frame.obstime` — the OUTPUT frame's — at `:204`; backward from
   `itrs_coo.obstime` — the INPUT frame's — at `:212`. Both are "the ITRS side's
   obstime", but they are opposite ends of the conversion.

Nothing requires the two frames to share an anchoring. `test_cirs_itrs_topo`
exercises precisely the case where they do NOT (a CIRS frame at `t` and a second
CIRS frame at `t + 6 years`, and it asserts the two results are distinguishable).
So the model gives the pair TWO independent anchorings, `(L, esrc)` and
`(T, etgt)`, and the postconditions name which one each step uses. All four repo
functions (TETE and CIRS, forward and backward) share this one geometry — a
shared skeleton — so the model carries one representative pair (`equ_to_rot` /
`rot_to_equ`).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C2a | components `vx,vy,vz`; source site `lx,ly,lz` + epoch `esrc`; target site `tx,ty,tz` + epoch `etgt`; `comp` selector | `cirs_coo.cartesian` (.x,.y,.z); `(cirs_coo.obstime, cirs_coo.location)` and `(itrs_frame.obstime, itrs_frame.location)` | R | exact-real components <-> exact `int`; each site is an integer triple; each obstime is an opaque integer epoch TAG (equal iff the `Time`s are); the centre of the Earth (`EARTH_CENTER`, exactly `(0,0,0)` km in the repo) <-> `(0,0,0)` (mapping.md §2). |
| C2b | `equ_to_rot` step 1: `wx = vx + offset_x(vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt)` (== `rebased_x(...)`) | `:200-201` `cirs_coo.transform_to(CIRS(obstime=itrs_frame.obstime, location=itrs_frame.location))` | A-consumed | the re-referencing transform is an UNCHANGED callee; `offset_*` is bound to the componentwise change it makes to the position (mapping.md §3.3), depending on the position and BOTH anchorings. The gold change is exactly its two arguments. |
| C2c | `equ_to_rot` step 2: `prot_x(wx,wy,wz, etgt)` | `:204-205` `pmat = cirs_to_itrs_mat(itrs_frame.obstime)`; `cirs_coo2.cartesian.transform(pmat)` | A-consumed | the Earth-orientation matrix-vector apply is an unchanged callee (`cirs_to_itrs_mat`/`tete_to_itrs_mat` via `CartesianRepresentation.transform`); axiomatized as the three components of `P(e) @ v` at the epoch `e`. The epoch argument is `etgt` because `:204` reads the OUTPUT frame's obstime. G-AX checks `prot_orthogonality` at one epoch and CONTROLS that the cross-epoch composition is detectably not the identity. |
| C2d | `rot_to_equ` step 1: `wx = prot_inv_x(ox,oy,oz, esrc)` | `:212-213` `pmat = cirs_to_itrs_mat(itrs_coo.obstime)`; `itrs_coo.cartesian.transform(matrix_transpose(pmat))` | A-consumed | the transpose action is the unchanged `matrix_transpose`+`transform` callee; the epoch argument is `esrc` because `:212` reads the INPUT frame's obstime. |
| C2e | `rot_to_equ` step 2: `wx + offset_x(wx,wy,wz, lx,ly,lz,esrc, tx,ty,tz,etgt)` (== `rebased_x(prot_inv_*(o,esrc), ...)`) | `:214,217` `CIRS(newrepr, obstime=itrs_coo.obstime, location=itrs_coo.location).transform_to(cirs_frame)` | A-consumed / I | same unchanged callee as C2b, but applied AFTER the rotation and to the ROTATED position — matching gold's order exactly. The nesting in the postcondition (`rebased_*` OF `prot_inv_*`) is what pins the order. |
| C2f | `same_frame_noop(v, L, e)` -> `offset_*(v, L,e, L,e) == 0` | the gold comments at `intermediate_rotation_transforms.py:199,213` ("no-op if same obstime and location") and the guard/comment pair at `itrs_observed_transforms.py:106,143` | A-consumed | the ONLY fact the proof consumes about the re-referencing transform, and the weakest one sufficient for either round-trip identity. It covers exactly ONE case: both anchorings identical. G-AX validates it against the real transform, at BOTH instances the model binds the offset to (CIRS<->CIRS and ITRS<->ITRS), and runs the two CONTROLS at each — target site changed alone, target epoch changed alone, each beyond the 1 m detection floor — showing the fact does NOT extend into the differing-anchoring domain the postconditions pin. |
| C2g | `equ_rot_roundtrip` composes the pair at ONE shared anchoring `(L, e)`; consumes `same_frame_noop` twice and `prot_orthogonality` once | CIRS@(L,t) -> ITRS@(L,t) -> CIRS@(L,t) is the identity (`test_cirs_itrs_topo`, the through-ITRS no-refraction agreement of the two refraction tests, and the `_add_merged_transform(ITRS, CIRS, ITRS)` loopback at `:276`) | I / A-consumed | the round-trip composes the two modeled functions exactly as the tests chain `transform_to(ITRS(location=loc, obstime=t))` / `transform_to(cirs)`. This is the sub-case where the offset provably vanishes, so the identity is exact. |

The genuinely-changed operation here is the ANCHORING the transform refers the
position to: gold honours the frame's own site and obstime; the pre-patch forced
the centre of the Earth. The discriminating postconditions are the two that name
BOTH anchorings and the epoch of the rotation:

```
equ_to_rot:  Result() == prot_x(rebased_x(v, L,esrc, T,etgt), ..., etgt)
rot_to_equ:  Result() == rebased_x(prot_inv_x(o,esrc), ..., L,esrc, T,etgt)
```

`model_prepatch.py` reverts all FOUR conversion regions to the pre-patch
anchoring: `equ_to_rot` and `itrs_to_observed` refer the position to the CONSTANT
site `(0,0,0)` (the centre of the Earth), and `rot_to_equ` / `observed_to_itrs`
refer it FROM that constant site. Since `same_frame_noop` gives only
`offset_*(v, L,e, L,e) == 0`, no reverted result is derivable and ALL FOUR
postconditions **fail** (G-DIFF; measured — `Verification failed` with errors at
`model_prepatch.py:327` `itrs_to_observed`, `:388` `observed_to_itrs`, `:505`
`equ_to_rot`, `:560` `rot_to_equ`). This is the
geocentric-vs-topocentric aberration the F2P tests
(`test_itrs_topo_to_{altaz,hadec}_with_refraction`, `test_cirs_itrs_topo`) catch:
with the site dropped to the centre, the through-ITRS observed route disagrees
with the direct route by arc-minutes (G-AX measures ~4e7 m of offset on a
topocentric witness), so the faithful real patch does NOT resolve.

**Why the two anchorings must be separate carriers.** A version of this spec that
gave a pair ONE site triple, used as both the source and the target of the
re-referencing step, would make every `offset_*` call an instance of
`same_frame_noop` — provably zero — and its postconditions would collapse to the
bare rotations (`prot_x(v, e)` / `prot_inv_x(o, e)` for the equatorial pair,
`fwd_x(v, S)` / `bwd_x(o, S)` for the observer-centred one). An implementation
that omitted the re-referencing step entirely would then satisfy them, i.e. the
spec would admit exactly the behaviour the issue reports. `properties.py` cases
`dropped-rereference-equ-to-rot`, `dropped-rereference-rot-to-equ`,
`dropped-rereference-forward` and `dropped-rereference-backward` are those
implementations, and all four are REJECTED (`Postcondition of <fn> might not
hold`); G-MUT independently confirms the offset term is live (the `'+'` -> `'-'`
mutants on the offset lines are killed, 20/20).

**Why the matrix carries the site too.** Both directions of the observer-centred
pair build the orientation matrix from the OBSERVER-CENTRED side's own site —
`:112` reads `observed_frame.location` going forward, `:129` reads
`observed_coo.location` coming back — so "which site the matrix comes from" is a
second, independent observable. A spec whose `fwd_*`/`bwd_*` took only the three
position components would leave it free: an implementation could build the matrix
from the OTHER end's site and still verify, even though at differing anchorings
that is a different position (G-AX measures the cross-site composition
`M(S')^T (M(S) v)` missing `v` by far more than the 1 m floor). `fwd_*`/`bwd_*`
are therefore indexed by the site, the `orthogonality` axiom is scoped to ONE
site, and `properties.py` cases `wrong-matrix-site-forward` /
`wrong-matrix-site-backward` — which swap `T` for `L` in the matrix argument only
— are REJECTED.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The two operations that genuinely
changed are modeled **directly**:

* introducing the DIRECT Earth-fixed <-> observer-centred transform pair (and
  thereby the exact round-trip identity) — modeled by `itrs_to_observed` /
  `observed_to_itrs` / `observed_roundtrip`. Both steps of each direction are
  modeled: the site-indexed orientation-matrix apply with the consumed
  `orthogonality` axiom (A3/B1), and the anchoring re-reference gold performs at
  `:106-110` / `:141-145` with the consumed `same_frame_noop` fact (A2/B2). The
  genuinely-changed data are the two arguments passed to the re-referencing
  transform (`obstime=observed_frame.obstime, location=observed_frame.location`
  and `obstime=observed_coo.obstime, location=observed_coo.location`) plus the
  frame whose `location` the matrix is built from; they are pinned by naming BOTH
  anchorings AND the matrix's site in the postcondition, together with the ORDER
  of the two steps;
* making the Earth-equatorial <-> Earth-rotating transforms honour the frame's
  own anchoring — its own site AND its own obstime — instead of forcing the
  centre of the Earth. Modeled by `equ_to_rot` / `rot_to_equ` /
  `equ_rot_roundtrip` (the epoch-indexed Earth-orientation rotation, the
  position- and anchoring-dependent `offset_*`, and the consumed
  `same_frame_noop` fact about the unchanged re-referencing transform). The
  genuinely-changed data are again the two arguments passed to the re-referencing
  transform (`obstime=itrs_frame.obstime, location=itrs_frame.location` vs
  `location=EARTH_CENTER` / no `location=`); they are pinned by naming BOTH
  anchorings in the postcondition, together with the ORDER of the two steps and
  the EPOCH of the rotation — NOT hidden behind an axiom about the function
  under change.

Both pairs therefore have the SAME two-step shape, differing only in what the
rotation is indexed by (the observer's SITE for the observer-centred pair, since
`:112`/`:129` read a `location`; the EPOCH for the equatorial pair, since
`intermediate_rotation_transforms.py:204`/`:212` read an `obstime`) and in which
end of the conversion each direction reads its arguments from. Neither pair's
postcondition is a bare rotation.

There is **no A-reference deep model** and **no kind-3 step**: every callee used
(`fwd_*`/`bwd_*`, `prot_*`/`prot_inv_*`, `offset_*`) is an UNCHANGED callee
axiomatized at its weakest sufficient contract (orthogonality at one site / at one
epoch, identical-anchoring no-op), never a re-implemented changed operation. The
`rebased_*` helpers live in the `pure` (spec) region and introduce NO assumption:
each is a definition, `rebased_c(v, ...) = v_c + offset_c(v, ...)`. The
refraction helpers
(`add_refraction`/`remove_refraction`) and the specific matrix entries are NOT
modeled: they are precision-level numerics the F2P tolerances absorb, and the
tested *structural* guarantee is the two-step round-trip identity, which
is fully captured above.

**Refraction vs. identity (precise scoping).** Exact round-trip identity is
asserted by the tests only on the **no-pressure** frames (`altaz_frame1` /
`hadec_frame1`): there `assert_allclose(itrs11.{x,y,z}, itrs.{x,y,z})` with the
default (tight) tolerance — the pure `M^T(M v) = v` identity modeled here. The
**refraction** frames (`altaz_frame2`, with pressure) are NOT an exact identity
(refraction is a deliberate, non-orthogonal directional perturbation, relative
error ~1e-3); the tests check only that the refraction path *agrees with the
pre-existing CIRS route* within loose tolerance (`atol=0.1*u.mas`,
`atol=10*u.cm`), never that the refraction round trip equals the input. The
discriminating structural property — exact identity on the no-pressure path — is
the one modeled here.

## E. verify(model) ⇒ resolved

`itrs_to_observed` verifies only if it performs the re-referencing step, from the
INPUT frame's anchoring `(L, esrc)` to the OUTPUT frame's `(T, etgt)`, BEFORE the
rotation, and rotates with the matrix built from the OUTPUT frame's own site `T`
(A2/A3). `observed_to_itrs` verifies only if it rotates with the transpose of the
matrix built from the INPUT frame's own site `L` FIRST and then re-references the
ROTATED position between those same two anchorings (B1/B2). `observed_roundtrip`
verifies only if that pair is the exact identity at a shared anchoring (C).
`equ_to_rot` verifies only if it performs the re-referencing step, from the INPUT
frame's anchoring `(L, esrc)` to the OUTPUT frame's `(T, etgt)`, BEFORE the
rotation, and rotates at the OUTPUT frame's epoch `etgt` (C2b/C2c). `rot_to_equ`
verifies only if it rotates with the transpose at the INPUT frame's epoch `esrc`
FIRST and then re-references the ROTATED position between those same two
anchorings (C2d/C2e). No conversion can be satisfied by dropping the
re-referencing step, by handing it a constant site, by handing it the other
endpoint's anchoring, by building the rotation from the other end's site or epoch,
by swapping the order of the two steps, by reaching the observer-centred
orientation through an indirect route, or by getting it right only on part of the
domain (only for some `comp`, or only where the anchorings agree) — each of those
is a case in `properties.py` and each is rejected by the verifier.
`equ_rot_roundtrip` verifies only if that pair is the exact identity at a shared
anchoring (C2g).

By R (exact-real components <-> int; obstime <-> epoch tag; site <-> integer
triple; the centre of the Earth <-> `(0,0,0)`) and A-consumed (the real
`transform`/`matrix_transpose` of the orthogonal `rotation_matrix` /
`cirs_to_itrs_mat` / `tete_to_itrs_mat` composites satisfy orthogonality at a
fixed site resp. a fixed epoch, and the real re-referencing transform is a no-op
between frames of identical anchoring — all measured by G-AX, with controls
showing neither the site nor the epoch carrier is decorative on either the matrix
or the offset), the verified skeleton equals the gold transforms up to type
refinement and the audited axioms — and the gold patch resolves (G-RESOLVE).
G-CONF closes the loop empirically: the impl shadow, with `fwd_*`/`bwd_*`,
`offset_*` and `prot_*` bound to the real transforms per mapping.md, agrees with
the real patched frame transforms — BOTH conversion pairs, the observer-centred one
driven at AltAz and HADec — on 364500 component inputs across 15 configurations x
4 anchoring pairs (identical / site-differs / epoch-differs / both-differ), 0
disagreements.
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).

## F. Why the observer-centred pair carries anchorings at all

An earlier shape of this spec gave `itrs_to_observed` / `observed_to_itrs` only
the three position components and modeled each direction as a single rotation, on
the reading that gold's `:106-110` and `:141-145` blocks are inert. They are not
inert: they are inert only on the sub-domain where the two frames share an
anchoring. Off that sub-domain the earlier postcondition
`Result() == fwd_x(vx, vy, vz)` was satisfied by an implementation that ignores
the two frames' anchorings entirely and rotates the position as given — i.e. by
the very geocentric reading the issue reports, since a frame whose `location`
defaults to `EARTH_CENTER` (`itrs.py:68`) is then indistinguishable from one
anchored at a real site. Such an implementation verified against that spec and its
faithful transcription into the real repo did NOT resolve: `test_gcrs_altaz_bothroutes`
fails for every one of its five parametrised frames, because dropping the
re-reference makes the direct ITRS->AltAz route disagree with the pre-existing
through-CIRS route.

The shape above closes that by making the previously-unconstrained observables
OBSERVABLE and pinning them, rather than by excluding the offending inputs:

* both frames' anchorings became arguments (`(lx,ly,lz,esrc)` and
  `(tx,ty,tz,etgt)`), free and unconstrained — no precondition requires them to
  agree, so the interesting domain is IN scope, not excluded;
* the postconditions name the re-referencing endpoints, in the order gold applies
  them, nested so the order is not re-derivable (A2/A3, B1/B2);
* `fwd_*`/`bwd_*` gained the site the matrix is built from, and `orthogonality`
  was narrowed to ONE site, so "which end's site the matrix comes from" is pinned
  and no cross-site cancellation is assumable;
* the round trip (C) still holds, and holds for the same reason gold's does —
  both legs' re-references are `same_frame_noop` instances at a shared anchoring.

Every added clause is an equality the gold source makes true at a named line, and
no obligation was weakened: the four `model_prepatch.py` postcondition failures
(one per conversion) and the 27 rejected `properties.py` rivals — against 6
positive controls and 1 admissibility case that must and do verify — are the
record of that.
