"""Twin-artifact model for astropy__astropy-13398.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Two pairs of DIRECT conversions are specified. Every frame involved is
  ANCHORED: it carries its own observing site and its own epoch, and nothing
  makes the anchoring of the frame a position is held in agree with the anchoring
  of the frame it is wanted in. So each conversion is TWO steps — a RE-REFERENCING
  step that moves the position from the anchoring it is held in to the anchoring
  it is wanted in, and a purely geometric ROTATION.

  FIRST PAIR: an Earth-fixed orientation <-> an observer-centred orientation.
  The rotation here is a constant orthogonal orientation matrix determined by the
  observing site of the OBSERVER-CENTRED frame — the frame that defines the
  observer-centred orientation, whichever end of the conversion it sits at.

  Earth-fixed (site L, epoch e_src) -> observer-centred (site T, epoch e_tgt):
    * FIRST refer the given position to the same-kind Earth-fixed frame anchored
      at the OUTPUT (observer-centred) frame's own site T and epoch e_tgt;
    * THEN apply the orientation matrix FOR THAT OUTPUT frame's own site T to the
      re-referred position.

  observer-centred (site L, epoch e_src) -> Earth-fixed (site T, epoch e_tgt):
    * FIRST apply the TRANSPOSE of the orientation matrix FOR THE INPUT
      (observer-centred) frame's own site L to the given position;
    * THEN refer the rotated position from the input frame's own anchoring
      (site L, epoch e_src) to the output frame's anchoring (site T, epoch
      e_tgt).

  SECOND PAIR: an intermediate Earth-equatorial orientation <-> an Earth-rotating
  orientation. The rotation here is the Earth-orientation rotation, whose value
  depends on an EPOCH.

  Earth-equatorial (site L, epoch e_src) -> Earth-rotating (site T, epoch e_tgt):
    * FIRST refer the given position to the same-kind Earth-equatorial frame
      anchored at the OUTPUT frame's own site T and epoch e_tgt;
    * THEN apply the Earth-orientation rotation FOR THE OUTPUT frame's epoch
      e_tgt to that re-referred position.

  Earth-rotating (site L, epoch e_src) -> Earth-equatorial (site T, epoch e_tgt):
    * FIRST apply the TRANSPOSE of the Earth-orientation rotation FOR THE INPUT
      frame's epoch e_src to the given position;
    * THEN refer the rotated position from the input frame's own anchoring
      (site L, epoch e_src) to the output frame's anchoring (site T, epoch
      e_tgt).

  The anchoring handed to the re-referencing step is the observable the issue is
  about: the position must be referred to the OUTPUT frame's OWN site and epoch,
  taken from the frame the caller asked for, and referred FROM the anchoring the
  input actually carries. Any other choice — a constant site independent of the
  frames, the endpoints interchanged, or omitting the step so the position is
  rotated as it stands — is a different observable behaviour. The same holds of
  the site the orientation matrix is built from, and of the epoch the
  Earth-orientation rotation is taken at: each conversion reads it off ONE named
  end of the conversion, and the two directions read opposite ends.

  When the two frames of a conversion agree in both site and epoch the
  re-referencing step introduces nothing, and only then is that conversion the
  bare rotation. In that same-anchoring case each pair is an EXACT round-trip
  identity — converting a position out and back returns it componentwise —
  precisely because each rotation is orthogonal, so its transpose undoes it. That
  same-anchoring round trip is the guarantee the issue demands. A conversion that
  instead reaches the far orientation by an INDIRECT route — one that does not
  apply the orthogonal rotation to the re-referred position, but introduces a
  further viewpoint-dependent directional shift along the way — does NOT
  reproduce the direct rotation and so does NOT round-trip exactly. When the
  anchorings differ neither pair composes to the identity — which is what makes
  the re-referencing step, and the site and epoch it is given, observable rather
  than decorative.

The position components, the site coordinates and the epoch are modelled as
exact integers (the round-trip identity is the exact algebraic cancellation that
the comparison tolerances absorb; the behaviour is precision-independent — see
refinement.md / mapping.md). The orthogonal rotation matrices and their actions
are unchanged callees (the rotation-matrix machinery and the Cartesian
transform); their forward/backward action is axiomatised, the only property the
proof needs being that the transpose-action inverts the forward action at one and
the same site (respectively at one and the same epoch). The re-referencing step
is an unchanged callee too; the only property the proof needs is that referring a
position between two frames of identical anchoring introduces no offset.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def fwd_x(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """First component of the constant orthogonal orientation matrix M(S) FOR THE
    SITE S = (sx, sy, sz) applied to the vector (x, y, z). The matrix is built
    from the site's own geodetic coordinates, so M(S) and M(S') are unrelated for
    S != S'. Unchanged callee (the rotation-matrix machinery via the Cartesian
    transform); provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def fwd_y(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Second component of M(S) applied to (x, y, z)."""
    Ensures(True)


@Pure
@ContractOnly
def fwd_z(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Third component of M(S) applied to (x, y, z)."""
    Ensures(True)


@Pure
@ContractOnly
def bwd_x(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """First component of the TRANSPOSE of M(S) applied to (x, y, z) (the
    inverse rotation for the site S). Unchanged callee."""
    Ensures(True)


@Pure
@ContractOnly
def bwd_y(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Second component of the transpose of M(S) applied to (x, y, z)."""
    Ensures(True)


@Pure
@ContractOnly
def bwd_z(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> int:
    """Third component of the transpose of M(S) applied to (x, y, z)."""
    Ensures(True)


@ContractOnly
def orthogonality(x: int, y: int, z: int, sx: int, sy: int, sz: int) -> None:
    """The single fact about the unchanged orthogonal orientation matrix the
    round-trip proof consumes: at ONE AND THE SAME site S = (sx, sy, sz),
    applying the transpose-action to the forward-action of any vector returns
    that vector componentwise (the transpose of an orthogonal matrix is its
    inverse). Nothing is claimed across two different sites. Provenance +
    executable soundness: mapping.md / axiom_check.py."""
    Requires(MustTerminate(2))
    Ensures(bwd_x(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == x)
    Ensures(bwd_y(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == y)
    Ensures(bwd_z(fwd_x(x, y, z, sx, sy, sz), fwd_y(x, y, z, sx, sy, sz),
                  fwd_z(x, y, z, sx, sy, sz), sx, sy, sz) == z)


@Pure
@ContractOnly
def prot_x(x: int, y: int, z: int, e: int) -> int:
    """First component of the Earth-orientation rotation P(e) FOR THE EPOCH e
    applied to the vector (x, y, z). This rotation relates an intermediate
    Earth-equatorial orientation to an Earth-rotating orientation; its value
    depends on the epoch e, and P(e) and P(e') are unrelated for e != e'. It is a
    distinct unchanged callee (the epoch-dependent Earth-orientation matrix
    builder and the Cartesian transform). Provenance + executable soundness:
    mapping.md / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def prot_y(x: int, y: int, z: int, e: int) -> int:
    """Second component of the rotation P(e) applied to (x, y, z)."""
    Ensures(True)


@Pure
@ContractOnly
def prot_z(x: int, y: int, z: int, e: int) -> int:
    """Third component of the rotation P(e) applied to (x, y, z)."""
    Ensures(True)


@Pure
@ContractOnly
def prot_inv_x(x: int, y: int, z: int, e: int) -> int:
    """First component of the TRANSPOSE of the rotation P(e) applied to
    (x, y, z) (the inverse rotation at the epoch e). Unchanged callee."""
    Ensures(True)


@Pure
@ContractOnly
def prot_inv_y(x: int, y: int, z: int, e: int) -> int:
    """Second component of the transpose of P(e) applied to (x, y, z)."""
    Ensures(True)


@Pure
@ContractOnly
def prot_inv_z(x: int, y: int, z: int, e: int) -> int:
    """Third component of the transpose of P(e) applied to (x, y, z)."""
    Ensures(True)


@ContractOnly
def prot_orthogonality(x: int, y: int, z: int, e: int) -> None:
    """The single fact about the unchanged Earth-orientation rotation P(e) the
    round-trip proof consumes: at ONE AND THE SAME epoch e, its transpose-action
    inverts its forward-action componentwise (P(e) is orthogonal, so P(e)^T is
    its inverse). Nothing is claimed across two different epochs. Provenance +
    executable soundness: mapping.md / axiom_check.py."""
    Requires(MustTerminate(6))
    Ensures(prot_inv_x(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == x)
    Ensures(prot_inv_y(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == y)
    Ensures(prot_inv_z(prot_x(x, y, z, e), prot_y(x, y, z, e),
                       prot_z(x, y, z, e), e) == z)


@Pure
@ContractOnly
def offset_x(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """First component of the offset that referring the position (vx, vy, vz)
    introduces when that position, held in a frame anchored at site
    L = (lx, ly, lz) at epoch esrc, is referred to the SAME-KIND frame anchored
    at site T = (tx, ty, tz) at epoch etgt. The route taken ties the position to
    the Solar-System barycentre, so the offset is the
    geocentric-versus-topocentric aberration difference together with the change
    of epoch; it therefore depends on the position itself as well as on both
    anchorings. This is an unchanged callee (the re-referencing transform between
    two same-kind frames). Provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def offset_y(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """Second component of the re-referencing offset on (vx, vy, vz) from
    (site L, epoch esrc) to (site T, epoch etgt)."""
    Ensures(True)


@Pure
@ContractOnly
def offset_z(vx: int, vy: int, vz: int,
             lx: int, ly: int, lz: int, esrc: int,
             tx: int, ty: int, tz: int, etgt: int) -> int:
    """Third component of the re-referencing offset on (vx, vy, vz) from
    (site L, epoch esrc) to (site T, epoch etgt)."""
    Ensures(True)


@ContractOnly
def same_frame_noop(vx: int, vy: int, vz: int,
                    lx: int, ly: int, lz: int, e: int) -> None:
    """The single fact about the unchanged re-referencing transform the proof
    consumes: referring a position between two frames of IDENTICAL anchoring —
    the same site L and the same epoch e — introduces no offset. This is the
    weakest fact sufficient for the round-trip proof; the offset is otherwise
    uninterpreted, so nothing follows about referring to any other site or any
    other epoch. Provenance + executable soundness: mapping.md /
    axiom_check.py."""
    Requires(MustTerminate(10))
    Ensures(offset_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
    Ensures(offset_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
    Ensures(offset_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e) == 0)
# axioms-end


# pure-start
@Pure
def rebased_x(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """First component of the position (vx, vy, vz) once it has been REFERRED
    from the frame anchored at (site L = (lx, ly, lz), epoch esrc) to the
    same-kind frame anchored at (site T = (tx, ty, tz), epoch etgt): the given
    component plus the offset that re-referencing introduces."""
    return vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)


@Pure
def rebased_y(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """Second component of the re-referred position."""
    return vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)


@Pure
def rebased_z(vx: int, vy: int, vz: int,
              lx: int, ly: int, lz: int, esrc: int,
              tx: int, ty: int, tz: int, etgt: int) -> int:
    """Third component of the re-referred position."""
    return vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
# pure-end


def itrs_to_observed(comp: int,
                     vx: int, vy: int, vz: int,
                     lx: int, ly: int, lz: int, esrc: int,
                     tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (vx, vy, vz)
    # is an Earth-fixed position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the observer-centred output is wanted
    # in the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(14))
    # pre-conditions-end
    # post-conditions-start
    # The given position is FIRST referred from the anchoring it is held in
    # (site L, epoch esrc) to the OUTPUT (observer-centred) frame's OWN anchoring
    # (site T, epoch etgt) — so the site and the epoch handed to the
    # re-referencing step are exactly the output frame's, and the position it is
    # applied to is exactly the given one. The orthogonal orientation matrix FOR
    # THAT OUTPUT frame's OWN site T is THEN applied to the re-referred position.
    # Each clause names the re-referencing endpoints and the site the matrix is
    # built from, so omitting the re-referencing step, referring to any other site
    # or epoch, reaching the observer-centred orientation by an indirect route, or
    # building the matrix from any other site, is a different value.
    Ensures(Implies(comp == 0, Result() == fwd_x(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    Ensures(Implies(comp == 1, Result() == fwd_y(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    Ensures(Implies(comp == 2, Result() == fwd_z(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        tx, ty, tz)))
    # post-conditions-end
    # impl-start
    # INDIRECT skeleton, and no re-referencing. There is no direct Earth-fixed
    # -> observer-centred rotation: the observer-centred orientation is reached by
    # routing through an intermediate (geocentric) frame, which inserts an extra
    # frame rotation before the orientation matrix is applied -- the matrix is NOT
    # applied to the re-referred position. And the position is rotated AS IT
    # STANDS, i.e. taken to be already referred to the geocentre, rather than
    # referred to the output frame's own site T and epoch etgt first. This is the
    # viewpoint-dependent ("aberration") shift the issue describes; it does not
    # reproduce the direct rotation of the re-referred position, so it cannot
    # satisfy the postcondition.
    ix = bwd_x(vx, vy, vz, tx, ty, tz)
    iy = bwd_y(vx, vy, vz, tx, ty, tz)
    iz = bwd_z(vx, vy, vz, tx, ty, tz)
    if comp == 0:
        return fwd_x(ix, iy, iz, tx, ty, tz)
    if comp == 1:
        return fwd_y(ix, iy, iz, tx, ty, tz)
    return fwd_z(ix, iy, iz, tx, ty, tz)
    # impl-end


def observed_to_itrs(comp: int,
                     ox: int, oy: int, oz: int,
                     lx: int, ly: int, lz: int, esrc: int,
                     tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (ox, oy, oz)
    # is an observer-centred position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-fixed output is wanted in the
    # frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(18))
    # pre-conditions-end
    # post-conditions-start
    # The TRANSPOSE of the orientation matrix FOR THE INPUT (observer-centred)
    # frame's OWN site L is applied to the given position FIRST; the rotated
    # position is THEN referred from the input frame's OWN anchoring (site L,
    # epoch esrc) to the output frame's anchoring (site T, epoch etgt). So the
    # matrix is built from the input frame's own site, the re-referencing step's
    # source anchoring is the input frame's own, its target anchoring is the
    # output frame's own, and the position it acts on is the ROTATED one — the
    # mirror of the forward conversion, in which the re-referencing precedes the
    # rotation and the matrix is built from the OUTPUT frame's site.
    Ensures(Implies(comp == 0, Result() == rebased_x(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 1, Result() == rebased_y(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 2, Result() == rebased_z(
        bwd_x(ox, oy, oz, lx, ly, lz), bwd_y(ox, oy, oz, lx, ly, lz),
        bwd_z(ox, oy, oz, lx, ly, lz),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    # post-conditions-end
    # impl-start
    # Rotate with the transpose of the orientation matrix built from the input
    # frame's own site L, and then RETURN THE ROTATED POSITION AS IT STANDS: the
    # rotated position is left referred to the anchoring the input carried, and is
    # never referred on to the output frame's site T and epoch etgt. Whenever the
    # two anchorings differ this is a different position from the one the output
    # frame asks for, so it cannot satisfy the postcondition.
    if comp == 0:
        return bwd_x(ox, oy, oz, lx, ly, lz)
    if comp == 1:
        return bwd_y(ox, oy, oz, lx, ly, lz)
    return bwd_z(ox, oy, oz, lx, ly, lz)
    # impl-end


def observed_roundtrip(comp: int,
                       vx: int, vy: int, vz: int,
                       lx: int, ly: int, lz: int, e: int) -> int:
    # pre-conditions-start
    # `comp` selects which component (0, 1 or 2) of the round-tripped position
    # to return. An Earth-fixed position (vx, vy, vz) held in a frame anchored at
    # the site L = (lx, ly, lz) at the epoch e, taken to the observer-centred
    # orientation in the frame anchored at the SAME site and the SAME epoch, and
    # back.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(22))
    # pre-conditions-end
    # post-conditions-start
    # Converting an Earth-fixed position to the observer-centred orientation at
    # (site L, epoch e) and back to the Earth-fixed orientation at (site L, epoch
    # e) returns the original position exactly. This is the round-trip identity
    # the issue demands of the direct conversion pair; it holds because the two
    # frames share their anchoring, so the re-referencing step contributes nothing
    # on either leg, and because the orientation matrix for one site is
    # orthogonal.
    Ensures(Implies(comp == 0, Result() == vx))
    Ensures(Implies(comp == 1, Result() == vy))
    Ensures(Implies(comp == 2, Result() == vz))
    # post-conditions-end
    # impl-start
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qx == vx)
    Assert(qy == vy)
    Assert(qz == vz)
    # The observer-centred components are the orientation matrix for the shared
    # site applied to that re-referred position (each equals the corresponding
    # forward-conversion output by that conversion's postcondition).
    ox = fwd_x(qx, qy, qz, lx, ly, lz)
    oy = fwd_y(qx, qy, qz, lx, ly, lz)
    oz = fwd_z(qx, qy, qz, lx, ly, lz)
    r0 = itrs_to_observed(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = itrs_to_observed(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r2 = itrs_to_observed(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r0 == ox)
    Assert(r1 == oy)
    Assert(r2 == oz)
    # RETURN LEG. The transpose-action for that same site undoes the
    # forward-action, recovering the re-referred position and hence the input.
    orthogonality(qx, qy, qz, lx, ly, lz)
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    Assert(wx == vx)
    Assert(wy == vy)
    Assert(wz == vz)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    return observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end


def equ_to_rot(comp: int,
               vx: int, vy: int, vz: int,
               lx: int, ly: int, lz: int, esrc: int,
               tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (vx, vy, vz)
    # is an Earth-equatorial position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-rotating output is wanted in
    # the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(26))
    # pre-conditions-end
    # post-conditions-start
    # The given position is FIRST referred from the anchoring it is held in
    # (site L, epoch esrc) to the OUTPUT frame's OWN anchoring (site T, epoch
    # etgt) — so the site and the epoch handed to the re-referencing step are
    # exactly the output frame's, and the position it is applied to is exactly
    # the given one. The Earth-orientation rotation FOR THE OUTPUT frame's epoch
    # etgt is THEN applied to that re-referred position. Each clause names the
    # re-referencing endpoints and the rotation's epoch, so omitting the
    # re-referencing step, referring to any other site or epoch, or rotating at
    # any other epoch, is a different value.
    Ensures(Implies(comp == 0, Result() == prot_x(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    Ensures(Implies(comp == 1, Result() == prot_y(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    Ensures(Implies(comp == 2, Result() == prot_z(
        rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt),
        rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt), etgt)))
    # post-conditions-end
    # impl-start
    # Refer the position to ONE CONSTANT SITE -- the centre of the Earth, site
    # (0, 0, 0) -- at the output frame's epoch etgt, rather than to the OUTPUT
    # frame's own site T, and then rotate at that epoch. Whenever the output
    # frame's site is not the centre of the Earth this leaves the position
    # referred somewhere other than where the output frame asks for, so the result
    # is not the rotation of the position referred to the output frame's own
    # anchoring, and cannot satisfy the postcondition.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end


def rot_to_equ(comp: int,
               ox: int, oy: int, oz: int,
               lx: int, ly: int, lz: int, esrc: int,
               tx: int, ty: int, tz: int, etgt: int) -> int:
    # pre-conditions-start
    # `comp` selects which output component (0, 1 or 2) to return. (ox, oy, oz)
    # is an Earth-rotating position held in a frame anchored at the site
    # L = (lx, ly, lz) at the epoch esrc; the Earth-equatorial output is wanted
    # in the frame anchored at the site T = (tx, ty, tz) at the epoch etgt. Both
    # anchorings are free: nothing requires them to agree.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(30))
    # pre-conditions-end
    # post-conditions-start
    # The TRANSPOSE of the Earth-orientation rotation FOR THE INPUT frame's
    # epoch esrc is applied to the given position FIRST; the rotated position is
    # THEN referred from the input frame's OWN anchoring (site L, epoch esrc) to
    # the output frame's anchoring (site T, epoch etgt). So the re-referencing
    # step's source anchoring is the input frame's own, its target anchoring is
    # the output frame's own, the position it acts on is the ROTATED one, and the
    # rotation is taken at the INPUT epoch — the mirror of the forward
    # conversion, in which the re-referencing precedes the rotation and the
    # rotation is taken at the OUTPUT epoch.
    Ensures(Implies(comp == 0, Result() == rebased_x(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 1, Result() == rebased_y(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    Ensures(Implies(comp == 2, Result() == rebased_z(
        prot_inv_x(ox, oy, oz, esrc), prot_inv_y(ox, oy, oz, esrc),
        prot_inv_z(ox, oy, oz, esrc),
        lx, ly, lz, esrc, tx, ty, tz, etgt)))
    # post-conditions-end
    # impl-start
    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
    # frame's epoch esrc, then refer the rotated position as if it were held at
    # ONE CONSTANT SITE -- the centre of the Earth, site (0, 0, 0) -- rather than
    # at the input frame's OWN site L. Whenever the input frame's site is not the
    # centre of the Earth this refers the position from somewhere other than where
    # it is actually held, so the result is not the rotated position referred from
    # the input frame's own anchoring, and cannot satisfy the postcondition.
    wx = prot_inv_x(ox, oy, oz, esrc)
    wy = prot_inv_y(ox, oy, oz, esrc)
    wz = prot_inv_z(ox, oy, oz, esrc)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
    # impl-end


def equ_rot_roundtrip(comp: int,
                      vx: int, vy: int, vz: int,
                      lx: int, ly: int, lz: int, e: int) -> int:
    # pre-conditions-start
    # `comp` selects which component (0, 1 or 2) of the round-tripped position to
    # return. An Earth-equatorial position (vx, vy, vz) held in a frame anchored
    # at the site L = (lx, ly, lz) at the epoch e, taken to the Earth-rotating
    # orientation in the frame anchored at the SAME site and the SAME epoch, and
    # back.
    Requires(comp == 0 or comp == 1 or comp == 2)
    Requires(MustTerminate(34))
    # pre-conditions-end
    # post-conditions-start
    # Converting the position to the Earth-rotating orientation at (site L, epoch
    # e) and back to the Earth-equatorial orientation at (site L, epoch e)
    # returns the original position exactly. This is the round-trip identity for
    # the second conversion pair; it holds because the two frames share their
    # anchoring, so the re-referencing step contributes nothing on either leg,
    # and because the Earth-orientation rotation at one epoch is orthogonal.
    Ensures(Implies(comp == 0, Result() == vx))
    Ensures(Implies(comp == 1, Result() == vy))
    Ensures(Implies(comp == 2, Result() == vz))
    # post-conditions-end
    # impl-start
    # OUTBOUND LEG. Both frames carry the same anchoring, so referring between
    # them introduces no offset and the re-referred position is the position
    # itself.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qx == vx)
    Assert(qy == vy)
    Assert(qz == vz)
    # The Earth-rotating components are the rotation, at the shared epoch, of
    # that re-referred position (each equals the corresponding forward-conversion
    # output by that conversion's postcondition).
    ox = prot_x(qx, qy, qz, e)
    oy = prot_y(qx, qy, qz, e)
    oz = prot_z(qx, qy, qz, e)
    r0 = equ_to_rot(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = equ_to_rot(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r2 = equ_to_rot(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r0 == ox)
    Assert(r1 == oy)
    Assert(r2 == oz)
    # RETURN LEG. The inverse rotation at that same epoch undoes the forward
    # rotation, recovering the re-referred position and hence the input.
    prot_orthogonality(qx, qy, qz, e)
    wx = prot_inv_x(ox, oy, oz, e)
    wy = prot_inv_y(ox, oy, oz, e)
    wz = prot_inv_z(ox, oy, oz, e)
    Assert(wx == vx)
    Assert(wy == vy)
    Assert(wz == vz)
    # The return leg refers between the same anchoring as well, so it introduces
    # no offset either.
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    return rot_to_equ(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end
