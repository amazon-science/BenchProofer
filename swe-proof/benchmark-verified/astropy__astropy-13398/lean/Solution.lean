import Mathlib
-- imports-end
open scoped Matrix

/-!
Direct conversions between an Earth-fixed Cartesian frame and the two
observer-centred frames (an azimuth/altitude frame and an hour-angle/declination
frame), plus the inverse conversions.

The behaviour modelled here, per observation:
  * a position is always recorded against some (site, epoch) pair; when that pair
    differs from the pair the other side of the conversion uses, the position is
    carried across by an indirect route whose value depends on BOTH pairs, not on
    either one alone;
  * the observing site is described by three geodetic angles/length obtained from
    a standard ellipsoidal inversion of its Earth-fixed Cartesian position;
  * the position vector is rotated into the observer frame by a product of
    elementary rotations (about the vertical, then the local meridian, with a
    handedness flip);
  * when the site carries a non-trivial atmosphere, an explicit closed-form
    refraction correction is applied in the altitude/azimuth frame, and — for the
    hour-angle frame — a further constant rotation maps the corrected vector
    across;
  * the inverse conversion undoes those steps and then always carries the
    reconstructed Earth-fixed position to the requested output (site, epoch).

Numeric quantities are modelled as `Float`, the same binary floating-point
carrier the library computes in, so the equalities stated below are equalities of
that machine computation rather than of an idealised exact-real re-derivation.
The choice is deliberate: over an exact-real carrier the postconditions would
also admit rewrites that are provable identities there and catastrophic at
working precision — cancelling a huge added constant, or shifting a
trigonometric argument by whole turns — so an exact-real reading of these
equations would not pin the computation at all.

The elementary trigonometric functions, the ellipsoidal inversion, the site
comparison, the empirical refraction coefficients, the norm/unit-direction
split, the scalar-times-vector product, the spherical⇄Cartesian primitives and
the indirect carry are unchanged library routines exposed here only by signature
(`opaque`). Everything the behaviour *composes* — the rotation-matrix
construction, the matrix and matrix/vector products, the branch structure, the
guard that decides whether a carry is needed, and the refraction arithmetic — is
spelled out.
-/

-- axioms-start
-- An opaque carrier for an observing site, and the unchanged library routines
-- the conversions CALL but do not change. Signatures only; the proof agent adds
-- any `_prop` contract it actually consumes.

/-- An observing site on the Earth. -/
opaque Location : Type

/-- Ellipsoidal inversion of an Earth-fixed Cartesian site position into geodetic
longitude, latitude and height. The two angles come back in the angular unit the
inversion natively reports, which is NOT radians. Unchanged library routine. -/
opaque geodetic : Location → Float × Float × Float

/-- The library's own element-wise comparison of two sites: `true` exactly when
the two are not recorded as the same site. Unchanged library predicate. -/
opaque siteDiffers : Location → Location → Bool

/-- The two empirical bending parameters the atmosphere contributes, as a function
of pressure, temperature, relative humidity and observing wavelength. The
equations below determine how they are consumed; this comment does not restate
them. Unchanged library routine. -/
opaque bendCoefs : Float → Float → Float → Float → Float × Float

/-- Norm-and-direction split of a 3-vector at working precision: its length
together with the unit vector along it. Unchanged library primitive. -/
opaque normSplit : (Fin 3 → Float) → Float × (Fin 3 → Float)

/-- Scalar times 3-vector at working precision. Unchanged library primitive. -/
opaque scaleVec : Float → (Fin 3 → Float) → (Fin 3 → Float)

/-- Cartesian → spherical primitive returning `(azimuth, elevation)` of a unit
vector. Unchanged library routine. -/
opaque cartToSph : (Fin 3 → Float) → Float × Float

/-- Spherical → Cartesian primitive: unit vector from `(azimuth, elevation)`.
Unchanged library routine. -/
opaque sphToCart : Float → Float → (Fin 3 → Float)

/-- The indirect Earth-fixed carry: re-express a position recorded against a
SOURCE (site, epoch) pair as a position recorded against a TARGET (site, epoch)
pair. It is the identity when the two pairs agree and otherwise routes through an
inertial frame, which also shifts stellar aberration; its value is therefore a
function of both pairs together. Unchanged transform pipeline, modelled opaquely:
it is not part of the direct geometry specified here.

Argument order: vector, source site, source epoch, target site, target epoch. -/
opaque carryTo : (Fin 3 → Float) → Location → Float → Location → Float →
    (Fin 3 → Float)
-- axioms-end

-- pure-start
/-- A 3×3 matrix of working-precision numbers. -/
abbrev Mat3 := Matrix (Fin 3) (Fin 3) Float

/-- A 3-vector of working-precision numbers. -/
abbrev Vec3 := Fin 3 → Float

/-- Floor applied to the sine of the elevation before it is used as a divisor, so
that the atmospheric correction stays finite as the direction approaches the
horizontal. -/
def sinAltFloor : Float := 0.05

/-- Floor applied to the cosine of the elevation before it is used as a divisor,
for the same reason, as the direction approaches the vertical. -/
def cosAltFloor : Float := 1e-6

/-- Angular distance of the pole from the equator, expressed in the angular unit
the ellipsoidal inversion reports. -/
def poleAngle : Float := 90.0

/-- Conversion factor from that reported angular unit to the radians the
elementary rotations consume. -/
def angToRad : Float := 0.017453292519943295

/-- `true` exactly when two epoch tags are not the same tag. -/
def epochDiffers (t₁ t₂ : Float) : Bool := !(t₁ == t₂)

/-- Matrix product at working precision: every entry is the row-by-column sum,
accumulated in index order. -/
def mmul (A B : Mat3) : Mat3 :=
  fun i j => A i 0 * B 0 j + A i 1 * B 1 j + A i 2 * B 2 j

/-- Matrix times vector at working precision, accumulated in index order. -/
def mvmul (A : Mat3) (v : Vec3) : Vec3 :=
  fun i => A i 0 * v 0 + A i 1 * v 1 + A i 2 * v 2

/-- Elementary right-handed rotation about the third axis by `θ` radians. -/
def rotZ (θ : Float) : Mat3 :=
  !![ Float.cos θ,  Float.sin θ, 0;
     -Float.sin θ,  Float.cos θ, 0;
      0,            0,           1]

/-- Elementary right-handed rotation about the second axis by `θ` radians. -/
def rotY (θ : Float) : Mat3 :=
  !![ Float.cos θ, 0, -Float.sin θ;
      0,           1,  0;
      Float.sin θ, 0,  Float.cos θ]

/-- Diagonal `diag(-1, 1, 1)` — flips the first axis (left-handed az/alt frame). -/
def flipX : Mat3 := !![(-1 : Float),0,0; 0,1,0; 0,0,1]

/-- Diagonal `diag(1, -1, 1)` — flips the second axis (left-handed HA/Dec frame). -/
def flipY : Mat3 := !![(1 : Float),0,0; 0,-1,0; 0,0,1]

/-- Diagonal `diag(-1, -1, 1)` — 180° about the vertical. -/
def flipXY : Mat3 := !![(-1 : Float),0,0; 0,-1,0; 0,0,1]

/-- Earth-fixed → azimuth/altitude rotation: flip the first axis, rotate by the
site's colatitude about the local meridian, then rotate by its longitude; both
angles are converted from the reported unit into radians first. -/
def altazMat (lon lat : Float) : Mat3 :=
  mmul (mmul flipX (rotY ((poleAngle - lat) * angToRad))) (rotZ (lon * angToRad))

/-- Earth-fixed → hour-angle/declination rotation: flip the second axis, then
rotate by the site's longitude. -/
def hadecMat (lon : Float) : Mat3 :=
  mmul flipY (rotZ (lon * angToRad))

/-- Azimuth/altitude → hour-angle/declination rotation. -/
def poleTiltMat (lat : Float) : Mat3 :=
  mmul flipXY (rotY ((poleAngle - lat) * angToRad))

/-- The apparent direction of a vector given in the altitude/azimuth frame, i.e.
the direction as seen through an atmosphere with bending parameters `coefA` and
`coefB`. The vector is split into length and unit direction, the direction's
elevation is raised by the modelled offset (applied as a small rotation of the
unit direction rather than through the spherical primitives), and the ORIGINAL
length is restored after the bent direction is renormalised. The offset itself is
the value the equation below assigns it; that equation is the definition of
record and this comment does not restate it. -/
def toApparent (p : Vec3) (coefA coefB : Float) : Vec3 :=
  let ns := normSplit p
  let norm := ns.1
  let uv := ns.2
  let sel := max (uv 2) sinAltFloor
  let cel := max (Float.sqrt (uv 0 * uv 0 + uv 1 * uv 1)) cosAltFloor
  let tanz := cel / sel
  let w := coefB * (tanz * tanz)
  let deltaEl := (coefA + w) * tanz / (1.0 + (coefA + 3.0 * w) / (sel * sel))
  let cosdel := 1.0 - 0.5 * (deltaEl * deltaEl)
  let fct := cosdel - deltaEl * sel / cel
  let bent : Vec3 := fun i =>
    if i = 0 then uv 0 * fct
    else if i = 1 then uv 1 * fct
    else cosdel * uv 2 + deltaEl * cel
  scaleVec norm (normSplit bent).2

/-- The geometric direction underlying an apparent altitude/azimuth vector: the
inverse of the above, lowering the elevation by the modelled offset through the
spherical primitives and restoring the original length. The offset is NOT the
same expression as in the forward direction, and the floor below is applied to
one of the two trigonometric quantities only; both differences are visible in the
equations and are deliberate. -/
def toGeometric (p : Vec3) (coefA coefB : Float) : Vec3 :=
  let ns := normSplit p
  let norm := ns.1
  let uv := ns.2
  let sel := max (uv 2) sinAltFloor
  let cel := Float.sqrt (uv 0 * uv 0 + uv 1 * uv 1)
  let tanz := cel / sel
  let deltaEl := (coefA + coefB * (tanz * tanz)) * tanz
  let azel := cartToSph uv
  scaleVec norm (sphToCart azel.1 (azel.2 - deltaEl))
-- pure-end

/-! An observing frame: its site, whether it is the azimuth/altitude flavour
(else hour-angle/declination), its atmospheric parameters, and its epoch tag. -/
structure ObsFrame where
  location : Location
  isAltAz : Bool
  pressure : Float
  temperature : Float
  relHumidity : Float
  obswl : Float
  epoch : Float

-- post-conditions-start
/-- The Earth-fixed → observer-frame conversion. The input position is recorded
against `srcLoc` at `srcEpoch`; whenever that pair differs from the observing
frame's own site and epoch the position is first carried across by the indirect
route, whose value depends on both pairs. The (possibly carried) position is then
rotated into the observer frame, with refraction applied iff the site has a real
atmosphere and a further constant rotation iff the frame is the hour-angle
flavour. -/
def problem_spec_itrs_to_observed
    (v : Vec3) (srcLoc : Location) (srcEpoch : Float) (f : ObsFrame)
    (result : Vec3) : Prop :=
  let src :=
    if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
      carryTo v srcLoc srcEpoch f.location f.epoch
    else v
  let g := geodetic f.location
  let lon := g.1
  let lat := g.2.1
  if f.isAltAz = true ∨ f.pressure > 0 then
    let aa := mvmul (altazMat lon lat) src
    if f.pressure > 0 then
      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
      let ref := toApparent aa rc.1 rc.2
      result = (if f.isAltAz = false then mvmul (poleTiltMat lat) ref else ref)
    else
      result = aa
  else
    result = mvmul (hadecMat lon) src
-- post-conditions-end

-- impl-start
def implementation_itrs_to_observed
    (v : Vec3) (srcLoc : Location) (srcEpoch : Float) (f : ObsFrame) : Vec3 :=
    Id.run do
  let mut src := v
  if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
    src := carryTo v srcLoc srcEpoch f.location f.epoch
  let g := geodetic f.location
  let lon := g.1
  let lat := g.2.1
  let mut crepr : Vec3 := src
  if f.isAltAz = true ∨ f.pressure > 0 then
    crepr := mvmul (altazMat lon lat) src
    if f.pressure > 0 then
      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
      crepr := toApparent crepr rc.1 rc.2
      if f.isAltAz = false then
        crepr := mvmul (poleTiltMat lat) crepr
  else
    crepr := mvmul (hadecMat lon) src
  return crepr
-- impl-end

-- proof-start
theorem correct_itrs_to_observed :
    ∀ (v : Vec3) (srcLoc : Location) (srcEpoch : Float) (f : ObsFrame),
      problem_spec_itrs_to_observed v srcLoc srcEpoch f
        (implementation_itrs_to_observed v srcLoc srcEpoch f) := by
  intro v srcLoc srcEpoch f
  unfold implementation_itrs_to_observed problem_spec_itrs_to_observed
  simp only [Id.run, bind, pure]
  split_ifs <;> rfl
-- proof-end

-- post-conditions-start
/-- The observer-frame → Earth-fixed conversion (inverse of the above). The
observed vector is de-refracted (when the site has a real atmosphere; for the
hour-angle flavour, after first rotating it into the azimuth/altitude frame) and
rotated back by the transposed rotation, giving a position recorded against the
observing site at the observing epoch. That position is then ALWAYS carried to
the requested output pair `(tgtLoc, tgtEpoch)` by the indirect route: the
identity exactly when the pairs agree, and otherwise a value depending on both
pairs. -/
def problem_spec_observed_to_itrs
    (v : Vec3) (f : ObsFrame) (tgtLoc : Location) (tgtEpoch : Float)
    (result : Vec3) : Prop :=
  let g := geodetic f.location
  let lon := g.1
  let lat := g.2.1
  let earthFixed :=
    if f.isAltAz = true ∨ f.pressure > 0 then
      let c0 := v
      let c1 :=
        if f.pressure > 0 then
          let c0' :=
            if f.isAltAz = false then mvmul ((poleTiltMat lat)ᵀ) c0 else c0
          let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
          toGeometric c0' rc.1 rc.2
        else c0
      mvmul ((altazMat lon lat)ᵀ) c1
    else
      mvmul ((hadecMat lon)ᵀ) v
  result = carryTo earthFixed f.location f.epoch tgtLoc tgtEpoch
-- post-conditions-end

-- impl-start
def implementation_observed_to_itrs
    (v : Vec3) (f : ObsFrame) (tgtLoc : Location) (tgtEpoch : Float) : Vec3 :=
    Id.run do
  let g := geodetic f.location
  let lon := g.1
  let lat := g.2.1
  let mut crepr : Vec3 := v
  if f.isAltAz = true ∨ f.pressure > 0 then
    if f.pressure > 0 then
      if f.isAltAz = false then
        crepr := mvmul ((poleTiltMat lat)ᵀ) crepr
      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
      crepr := toGeometric crepr rc.1 rc.2
    crepr := mvmul ((altazMat lon lat)ᵀ) crepr
  else
    crepr := mvmul ((hadecMat lon)ᵀ) v
  return carryTo crepr f.location f.epoch tgtLoc tgtEpoch
-- impl-end

-- proof-start
theorem correct_observed_to_itrs :
    ∀ (v : Vec3) (f : ObsFrame) (tgtLoc : Location) (tgtEpoch : Float),
      problem_spec_observed_to_itrs v f tgtLoc tgtEpoch
        (implementation_observed_to_itrs v f tgtLoc tgtEpoch) := by
  intro v f tgtLoc tgtEpoch
  unfold implementation_observed_to_itrs problem_spec_observed_to_itrs
  simp only [Id.run, bind, pure]
  split_ifs <;> rfl
-- proof-end
