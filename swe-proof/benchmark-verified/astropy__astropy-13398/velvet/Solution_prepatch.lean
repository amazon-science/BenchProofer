import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The constant orthogonal orientation matrix applied to a three-component
   position, returned componentwise (`fwdX`/`fwdY`/`fwdZ` are the three rows of
   `M · v`). `M` is built by the unchanged rotation-matrix machinery and applied
   by the unchanged Cartesian transform; the action is left uninterpreted — the
   only property the round-trip proof needs is that its transpose-action inverts
   it (the `orth_*` facts below). Provenance + executable soundness check:
   mapping.md / axiom_check.py (G-AX). -/
axiom fwdX : Int → Int → Int → Int
axiom fwdY : Int → Int → Int → Int
axiom fwdZ : Int → Int → Int → Int

/- The TRANSPOSE of the same orientation matrix applied to a position
   (`M^T · v`), componentwise — the inverse rotation. Unchanged callee. -/
axiom bwdX : Int → Int → Int → Int
axiom bwdY : Int → Int → Int → Int
axiom bwdZ : Int → Int → Int → Int

/- The single fact about the unchanged orthogonal orientation matrix the proof
   consumes: the transpose-action applied to the forward-action of any position
   returns that position componentwise (the transpose of an orthogonal matrix is
   its inverse). The matrix is otherwise uninterpreted. -/
axiom orth_x : ∀ x y z : Int, bwdX (fwdX x y z) (fwdY x y z) (fwdZ x y z) = x
axiom orth_y : ∀ x y z : Int, bwdY (fwdX x y z) (fwdY x y z) (fwdZ x y z) = y
axiom orth_z : ∀ x y z : Int, bwdZ (fwdX x y z) (fwdY x y z) (fwdZ x y z) = z

/- A second constant orthogonal rotation `P` (relating an Earth-rotating
   orientation to an intermediate Earth-equatorial one) applied to a position,
   componentwise (`P · v`). A distinct unchanged callee (the precession-nutation
   orientation matrix and the Cartesian transform). Provenance + soundness:
   mapping.md / axiom_check.py. -/
axiom protX : Int → Int → Int → Int
axiom protY : Int → Int → Int → Int
axiom protZ : Int → Int → Int → Int

/- The TRANSPOSE of the rotation `P` applied to a position (`P^T · v`),
   componentwise — the inverse rotation. Unchanged callee. -/
axiom protInvX : Int → Int → Int → Int
axiom protInvY : Int → Int → Int → Int
axiom protInvZ : Int → Int → Int → Int

/- The single fact about the second unchanged orthogonal rotation `P` the proof
   consumes: its transpose-action inverts its forward-action componentwise. -/
axiom prot_orth_x : ∀ x y z : Int, protInvX (protX x y z) (protY x y z) (protZ x y z) = x
axiom prot_orth_y : ∀ x y z : Int, protInvY (protX x y z) (protY x y z) (protZ x y z) = y
axiom prot_orth_z : ∀ x y z : Int, protInvZ (protX x y z) (protY x y z) (protZ x y z) = z

/- The viewpoint-dependent directional offset the transform carries when a
   near-Earth position whose frame is anchored at site `L = (lx, ly, lz)` is
   referred to a frame anchored at site `T = (tx, ty, tz)`, along the route that
   ties the position to the Solar-System barycentre — the geocentric-versus-
   topocentric difference, componentwise. An unchanged callee (the re-referencing
   transform between two same-kind frames); otherwise uninterpreted. Provenance +
   soundness: mapping.md / axiom_check.py. -/
axiom offsetX : Int → Int → Int → Int → Int → Int → Int
axiom offsetY : Int → Int → Int → Int → Int → Int → Int
axiom offsetZ : Int → Int → Int → Int → Int → Int → Int

/- The single fact about the unchanged re-referencing transform the proof
   consumes: referring a position whose frame is anchored at a site to a frame
   anchored at the SAME site introduces no offset (it is a no-op). The weakest
   fact sufficient for the agreement proof; the offset is otherwise
   uninterpreted. -/
axiom same_site_x : ∀ lx ly lz : Int, offsetX lx ly lz lx ly lz = 0
axiom same_site_y : ∀ lx ly lz : Int, offsetY lx ly lz lx ly lz = 0
axiom same_site_z : ∀ lx ly lz : Int, offsetZ lx ly lz lx ly lz = 0
-- axioms-end

-- pure-start
-- (no module-level pure helpers required)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Forward conversion of a three-component position from an Earth-rotating
   orientation to an observer-centred orientation. The desired behavior: the
   selected output component is the constant orthogonal orientation matrix
   applied DIRECTLY to the given position (`comp` selects which of the three
   output components to return). Pinning each component to the forward action of
   the input itself — with no intermediate viewpoint shift — forces the direct
   orthogonal rotation. -/
noncomputable section
method itrsToObserved (comp : Int) (vx : Int) (vy : Int) (vz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = fwdX vx vy vz
  ensures comp = 1 → out = fwdY vx vy vz
  ensures comp = 2 → out = fwdZ vx vy vz
  do
    -- impl-start
    -- Pre-image skeleton: there is NO direct route to the observer-centred
    -- orientation. It is reached by first routing through an intermediate frame
    -- (the transpose-action) and only then applying the orientation matrix, so
    -- the matrix is not applied to the given position directly — a
    -- viewpoint-dependent shift is inserted along the way.
    let ix := bwdX vx vy vz
    let iy := bwdY vx vy vz
    let iz := bwdZ vx vy vz
    if comp = 0 then
      return fwdX ix iy iz
    else if comp = 1 then
      return fwdY ix iy iz
    else
      return fwdZ ix iy iz
    -- impl-end
end

prove_correct itrsToObserved by
  loom_solve

/- Backward conversion of a three-component position from an observer-centred
   orientation to an Earth-rotating orientation. The desired behavior: the
   selected output component is the TRANSPOSE action (inverse rotation) applied
   DIRECTLY to the observer-centred input. -/
noncomputable section
method observedToItrs (comp : Int) (ox : Int) (oy : Int) (oz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = bwdX ox oy oz
  ensures comp = 1 → out = bwdY ox oy oz
  ensures comp = 2 → out = bwdZ ox oy oz
  do
    -- impl-start
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz
    -- impl-end
end

prove_correct observedToItrs by
  loom_solve

/- The round-trip identity for the direct conversion pair. The desired behavior:
   converting an Earth-rotating position to the observer-centred orientation and
   back returns the original position exactly (componentwise). This is the exact
   geometric round trip the issue demands of the direct pair; it holds precisely
   because the orientation matrix is orthogonal, so its transpose undoes it. A
   conversion that instead reaches the observer-centred orientation by an
   INDIRECT route — introducing a viewpoint-dependent directional shift rather
   than applying the orthogonal matrix directly — does NOT round-trip exactly. -/
noncomputable section
method observedRoundtrip (comp : Int) (vx : Int) (vy : Int) (vz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = vx
  ensures comp = 1 → out = vy
  ensures comp = 2 → out = vz
  do
    -- impl-start
    -- The observer-centred components are the forward action of the input; the
    -- transpose-action then inverts it, recovering the original position.
    let ox := fwdX vx vy vz
    let oy := fwdY vx vy vz
    let oz := fwdZ vx vy vz
    if comp = 0 then
      return bwdX ox oy oz
    else if comp = 1 then
      return bwdY ox oy oz
    else
      return bwdZ ox oy oz
    -- impl-end
end

prove_correct observedRoundtrip by
  loom_solve <;>
    simp_all [orth_x, orth_y, orth_z]

/- Forward conversion of a three-component position from an Earth-equatorial
   orientation to an Earth-rotating orientation, tied to an observing site `L`.
   The desired behavior: the position is referred to the output frame anchored
   at the SAME site `L = (lx, ly, lz)` it already carries, so referring to it
   introduces no viewpoint offset and the selected component is the rotation `P`
   applied to the given position with NO spurious viewpoint shift. Pinning each
   component to the bare rotation of the input forces the transform to honour the
   frame's own site rather than referring to one single constant site. -/
noncomputable section
method equToRot (comp : Int) (vx : Int) (vy : Int) (vz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = protX vx vy vz
  ensures comp = 1 → out = protY vx vy vz
  ensures comp = 2 → out = protZ vx vy vz
  do
    -- impl-start
    -- Pre-image skeleton: the position is referred to one FIXED site (the centre
    -- of the Earth, the origin (0, 0, 0)) rather than the output frame's own
    -- site L. When the site is not the centre this carries the
    -- geocentric-versus-topocentric viewpoint offset, so the result is the
    -- rotation PLUS that offset, not the bare rotation.
    if comp = 0 then
      return protX vx vy vz + offsetX lx ly lz 0 0 0
    else if comp = 1 then
      return protY vx vy vz + offsetY lx ly lz 0 0 0
    else
      return protZ vx vy vz + offsetZ lx ly lz 0 0 0
    -- impl-end
end

prove_correct equToRot by
  loom_solve <;>
    simp_all [same_site_x, same_site_y, same_site_z]

/- Backward conversion of a three-component position from an Earth-rotating
   orientation to an Earth-equatorial orientation, carrying the observing site
   `L`. The desired behavior: apply the TRANSPOSE of `P` (the inverse rotation)
   to the input and carry the input frame's own site `L` onto the result, so
   referring to the output frame's own (same) site is a no-op; the selected
   component is the inverse rotation of the input with NO spurious viewpoint
   shift. -/
noncomputable section
method rotToEqu (comp : Int) (ox : Int) (oy : Int) (oz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = protInvX ox oy oz
  ensures comp = 1 → out = protInvY ox oy oz
  ensures comp = 2 → out = protInvZ ox oy oz
  do
    -- impl-start
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct rotToEqu by
  loom_solve <;>
    simp_all [same_site_x, same_site_y, same_site_z]

/- The topocentric round-trip identity for the site-honouring conversion pair.
   The desired behavior: converting an Earth-equatorial position to the
   Earth-rotating orientation at site `L` and back returns the original position
   exactly (componentwise). It holds only because both legs honour the site `L`
   (so neither inserts a viewpoint offset) and `P` is orthogonal. A conversion
   that refers the position to one single constant site (the centre of the Earth, the
   origin) rather than the frame's own site introduces a viewpoint-dependent
   offset whenever the site is not the centre, so it does NOT round-trip
   exactly. -/
noncomputable section
method equRotRoundtrip (comp : Int) (vx : Int) (vy : Int) (vz : Int)
    (lx : Int) (ly : Int) (lz : Int) return (out : Int)
  require comp = 0 ∨ comp = 1 ∨ comp = 2
  ensures comp = 0 → out = vx
  ensures comp = 1 → out = vy
  ensures comp = 2 → out = vz
  do
    -- impl-start
    -- The Earth-rotating components are the rotation of the input (the
    -- site-offset of each leg is a no-op at the shared site L); the transpose
    -- rotation then inverts it, recovering the original position.
    let ox := protX vx vy vz
    let oy := protY vx vy vz
    let oz := protZ vx vy vz
    if comp = 0 then
      return protInvX ox oy oz + offsetX lx ly lz lx ly lz
    else if comp = 1 then
      return protInvY ox oy oz + offsetY lx ly lz lx ly lz
    else
      return protInvZ ox oy oz + offsetZ lx ly lz lx ly lz
    -- impl-end
end

prove_correct equRotRoundtrip by
  loom_solve <;>
    simp_all [prot_orth_x, prot_orth_y, prot_orth_z, same_site_x, same_site_y, same_site_z]
