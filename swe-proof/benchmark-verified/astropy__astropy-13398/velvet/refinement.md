# refinement.md — astropy__astropy-13398

Operation-by-operation correspondence between `Solution.lean`'s `method` impl
regions (`itrsToObserved`, `observedToItrs`, `observedRoundtrip`, `equToRot`,
`rotToEqu`, `equRotRoundtrip`, plus the consumed `orth_*` / `fwd*` / `bwd*` /
`prot_orth_*` / `prot*` / `same_site_*` / `offset*` axioms) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed**
(the proof uses this axiom's stated fact), **A-reference** (a deep model
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested round-trip inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`, the real
correctness oracle, G-RESOLVE).

## 0. Provenance — model the GOLD, not the issue's draft

The problem statement embeds a **draft** in which the forward conversion
subtracts the observer's Earth-fixed position *inside* the transform and the
backward adds it back. The **merged gold** conversions do NOT do this: in the
tested same-site / same-time path the early conditional block is a no-op, the
forward conversion is a single orthogonal-matrix apply on the cartesian *as
given*, and the backward is a single transpose-matrix apply. The observer-offset
arithmetic lives in the **caller** (the failing tests form the observer-relative
position themselves and recover it via the round trip), NOT inside the
conversion. This document pins to the gold conversions (offset-free, pure
orthogonal rotation).

## A. Forward conversion — `itrsToObserved`

Gold: in the tested same-site / same-time path the early conditional is a no-op
and the observer-centred cartesian is the orthogonal orientation matrix applied
DIRECTLY to the input cartesian (`crepr = cartesian.transform(M)` with `M` the
orientation matrix). No offset is subtracted inside the conversion; it is a pure
orthogonal rotation.

| # | `Solution.lean` impl op (`itrsToObserved`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | components `vx,vy,vz`; `comp` selector | `cartesian` (`.x,.y,.z`) | R | exact-real components ↔ exact `Int`; component `k` ↔ `comp = k` (mapping.md §2). |
| A2 | `fwdX/fwdY/fwdZ vx vy vz` | `cartesian.transform(M)` (the orientation matrix apply) | A-consumed | the orthogonal matrix-vector apply is an unchanged callee (the Cartesian transform of the rotation-matrix composite); axiomatised as the three components of `M · v`, applied to the position AS GIVEN. G-AX checks orthogonality against the real matrices (mapping.md §3.1). |

## B. Backward conversion — `observedToItrs`

Gold: apply the transpose of the orientation matrix directly to the
observer-centred cartesian; the final re-reference is a no-op for the same site /
time, so no offset is added back inside the conversion.

| # | impl op (`observedToItrs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `bwdX/bwdY/bwdZ ox oy oz` | `cartesian.transform(transpose(M))` | A-consumed | the transpose-action (inverse rotation) is the unchanged transpose + transform callee; axiomatised as the three components of `Mᵀ · v`, applied AS GIVEN (mapping.md §3.1). |

The observer-offset arithmetic (subtract on the way in, add on the way out) is a
**caller-layer** operation in gold, NOT part of either conversion. The
conversions themselves are the two pure orthogonal rotations above.

## C. Round-trip identity — `observedRoundtrip` (the tested guarantee)

Gold: the failing-then-passing tests require that converting an Earth-fixed
position to the observer-centred orientation and back is the **exact** identity
(tight `assert_allclose`).

| # | impl op (`observedRoundtrip`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `ox,oy,oz = fwd* vx vy vz` (the forward output, each = the corresponding `itrsToObserved` component by its postcondition) | the forward conversion output | I | the round trip composes the two modeled conversions exactly as the tests chain the two `transform_to` calls. |
| C2 | `bwd* (fwd* v) = v` via `orth_*` | `Mᵀ (M v) = v` for the orthogonal `M` | A-consumed | the inverse-rotation fact (mapping.md §3.1). |
| C3 | `observedToItrs` recovers `v` componentwise | the backward conversion recovers the original Earth-fixed position | I | the orthogonality A-consumed fact (C2) supplies `bwd(fwd(v)) = v` directly; no offset arithmetic is involved. |

The discriminating content — the **DIRECT** orthogonal-rotation pair (forward
`M`, backward `Mᵀ`) — is what makes the round trip the exact identity.
`Solution_prepatch.lean` reverts the forward conversion to the pre-patch
**indirect** skeleton: there is no direct Earth-fixed → observer-centred
rotation, so the observer-centred orientation is reached by routing through an
intermediate frame, which inserts an extra frame rotation (`fwd (bwd v)` rather
than `fwd v`) — the viewpoint-dependent directional shift the issue describes.
That indirect result is not the direct orthogonal rotation, so it **fails** the
frozen postcondition `out = fwdX vx vy vz` of `itrsToObserved` (G-DIFF) — exactly
the spec sensing the missing direct path.

## C2. Site-honouring conversion pair — `equToRot` / `rotToEqu` / `equRotRoundtrip`

Gold: the pre-existing Earth-equatorial ↔ Earth-rotating conversions are changed
so they refer the position to the *frame's own site* instead of forcing one fixed
site (the centre of the Earth). In the tested topocentric case both the input and
output frame are anchored at the SAME site L, so the re-reference is a no-op and
the conversion reduces to the bare rotation `P · v` (forward) / `Pᵀ · v`
(backward). All four real conversions (two flavours, forward and backward) share
this one geometry, so the model carries one representative pair.

| # | impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C2a | components `vx,vy,vz`; site `lx,ly,lz`; `comp` selector | `cartesian` (`.x,.y,.z`); `frame.location` | R | exact-real components ↔ exact `Int`; the observing site is the integer triple `(lx,ly,lz)`; the centre of the Earth is exactly `(0,0,0)` km in the repo ↔ `(0,0,0)` (mapping.md §2). |
| C2b | `protX/protY/protZ vx vy vz` | `cartesian.transform(P)` (precession rotation) | A-consumed | the precession-nutation matrix-vector apply is an unchanged callee; axiomatised as the three components of `P · v`. G-AX checks `prot_orthogonality` (`Pᵀ(P v) = v`) against the real matrices (mapping.md §3.2). |
| C2c | `+ offset* lx ly lz lx ly lz`, reduced to 0 by `same_site_*` | re-reference with the SAME site = no-op | A-consumed | the re-referencing conversion is an unchanged callee; the ONLY fact consumed is that re-referring to the SAME site introduces no offset (`offset*(L,L) = 0`). Because `P` is linear, applying the offset before or after the rotation is equivalent; the model carries the offset additively after the rotation. G-AX validates this against the real conversions (same-site offset == 0; force-centre offset detectably nonzero) (mapping.md §3.3). |
| C2d | `rotToEqu`: `protInv* ox oy oz` + same-site offset | `cartesian.transform(transpose(P))` then re-reference carrying the input frame's site | A-consumed | the transpose precession action is the unchanged transpose + transform callee; carrying the input frame's site makes the final re-reference a no-op (C2c). |
| C2e | `equRotRoundtrip` composes the pair; `prot_orth_*` gives `Pᵀ(P v) = v` | the topocentric round trip is the identity | I / A-consumed | the round trip composes the two modeled conversions exactly as the tests chain the two `transform_to` calls. |

The genuinely-changed datum is the SITE the conversion refers to: gold honours
the frame's own site; the pre-patch forced one fixed site. The discriminating
postcondition is the OFFSET-FREE one (`out = protX vx vy vz` — the bare rotation,
no viewpoint shift). `Solution_prepatch.lean` reverts `equToRot` to refer to the
centre of the Earth (`offset*(L, 0)` instead of `offset*(L, L)`); since
`same_site_*` gives only `offset*(L,L) = 0`, the result carries a spurious
viewpoint offset whenever `L ≠ 0` and the offset-free postcondition **fails**
(G-DIFF). This is the geocentric-vs-topocentric difference the failing tests
catch: with the site dropped to the centre, the through-intermediate route
disagrees with the direct route by arc-minutes (G-AX measures a large offset on a
topocentric witness), so the faithful real patch does NOT resolve without the
change.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The two operations that genuinely
changed are modeled **directly**:

* introducing the DIRECT orthogonal-rotation conversion pair (and thereby the
  exact round-trip identity) — modeled by `itrsToObserved` / `observedToItrs` /
  `observedRoundtrip` (the forward/backward matrix applies and the consumed
  `orth_*` facts);
* making the Earth-equatorial ↔ Earth-rotating conversions honour the frame's
  own site instead of forcing one fixed site — modeled by `equToRot` / `rotToEqu`
  / `equRotRoundtrip` (the precession rotation and the consumed `same_site_*`
  fact). The genuinely-changed datum is the SITE passed to the re-referencing
  conversion (the frame's own location vs the centre of the Earth); it is pinned
  by the offset-free forward/backward postcondition, NOT hidden behind an axiom
  about the function under change.

There is **no A-reference deep model** and **no kind-3 step**: every callee used
(`fwd*`/`bwd*`, `prot*`/`protInv*`, `offset*`) is an UNCHANGED callee axiomatised
at its weakest sufficient contract (orthogonality / same-site no-op), never a
re-implemented changed operation. The refraction helpers and the specific matrix
entries are NOT modeled: they are precision-level numerics the test tolerances
absorb, and the tested *structural* guarantee is the direct-rotation round-trip
identity, fully captured above.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The real conversions are straight-line matrix applies that
always terminate and return, and the F2P tests observe their return values, so
total correctness is the faithful semantics. Partial correctness would admit a
same-spec implementation that diverges (an infinite loop vacuously satisfies
every `ensures`) — a wrong impl the tests would fail — so it would leave the
spec too weak.

**Refraction vs. identity (scoping).** Exact round-trip identity is asserted by
the tests only on the **no-pressure** frames (tight tolerance — the pure
`Mᵀ(M v) = v` identity modeled here). The refraction frames (with pressure) are
NOT an exact identity (refraction is a deliberate non-orthogonal perturbation);
the tests check only that the refraction path *agrees with the pre-existing
intermediate route* within loose tolerance, never that the refraction round trip
equals the input. The discriminating structural property — exact identity on the
no-pressure path — is the one modeled here.

## E. verify(Solution) ⇒ resolved

`itrsToObserved` / `observedToItrs` verify only if they apply the orientation
matrix (resp. its transpose) DIRECTLY to the given position (A2/B1);
`observedRoundtrip` verifies only if that direct pair is the exact identity (C).
`equToRot` / `rotToEqu` verify only if they refer the position to the frame's OWN
site (so the offset is the no-op `offset*(L,L)` and the result is the bare
precession rotation, C2); `equRotRoundtrip` verifies only if that pair is the
exact topocentric identity. By R (exact-real components ↔ `Int`; the centre of the
Earth ↔ `(0,0,0)`) and A-consumed (the real transform / transpose of the
orthogonal orientation / precession composites satisfy orthogonality, and the
real re-referencing conversion is a no-op at the same site, G-AX), the verified
skeleton equals the gold conversions up to type refinement and the audited axioms
— and the gold patch resolves (G-RESOLVE). The trust points are axiom soundness
(G-AX: the orthogonality of the real orientation / precession matrices and the
same-site no-op of the real re-referencing conversion) and refinement fidelity
(this document, G-EQ).
