# properties.py — PBT falsification battery for astropy__astropy-13398.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside a # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec actually protects — see model.py /
# refinement.md / mapping.md). Six modeled functions, six impl regions. BOTH
# conversion pairs are ANCHORED: every frame involved carries its own observing
# site and its own epoch, and nothing requires the anchoring a position is held
# in to agree with the anchoring it is wanted in. So each directional conversion
# is TWO steps — a RE-REFERENCING step between the two anchorings and a ROTATION
# — and the two anchorings are SEPARATE carriers: source (site L = (lx,ly,lz),
# epoch esrc) and target (site T = (tx,ty,tz), epoch etgt).
#
# (A) The DIRECT Earth-fixed <-> observer-centred pair. Its rotation is the
#     constant orthogonal orientation matrix M(S), SITE-INDEXED: it is built from
#     the geodetic coordinates of the OBSERVER-CENTRED frame's own site,
#     whichever end of the conversion that frame sits at.
#
#   itrs_to_observed(comp, vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt) -> int
#     Requires comp == 0 or 1 or 2                   <-- plain int selector
#     Ensures Implies(comp==k, Result() == fwd_{k}(
#                 rebased_x(v, L,esrc, T,etgt),
#                 rebased_y(v, L,esrc, T,etgt),
#                 rebased_z(v, L,esrc, T,etgt), tx,ty,tz))
#       <-- RE-REFERENCE FIRST to the OUTPUT (observer-centred) frame's own
#           anchoring, THEN apply the orientation matrix built from THAT frame's
#           own site T. Pins (i) that the re-referencing step happens at all,
#           (ii) both of its endpoints, (iii) the site the matrix is built from,
#           and (iv) the order of the two steps.
#
#   observed_to_itrs(comp, ox,oy,oz, lx,ly,lz,esrc, tx,ty,tz,etgt) -> int
#     Ensures Implies(comp==k, Result() == rebased_{k}(
#                 bwd_x(o, lx,ly,lz), bwd_y(o, lx,ly,lz), bwd_z(o, lx,ly,lz),
#                 L,esrc, T,etgt))
#       <-- MIRROR ORDER: rotate FIRST with the TRANSPOSE of the matrix built
#           from the INPUT (observer-centred) frame's own site L, THEN re-refer
#           the ROTATED position from the input frame's own anchoring to the
#           output frame's. Pins the order, the rotated argument, and the site
#           each end takes its matrix from.
#
#   observed_roundtrip(comp, vx,vy,vz, lx,ly,lz, e) -> int
#     Ensures Implies(comp==k, Result() == v_{k})   <-- EXACT IDENTITY, in the
#           special case where the two frames share ONE anchoring (site L,
#           epoch e) — the round trip the issue demands.
#
# (B) The Earth-equatorial <-> Earth-rotating pair. Its rotation is the
#     Earth-orientation rotation P(e), EPOCH-INDEXED.
#
#   equ_to_rot(comp, vx,vy,vz, lx,ly,lz,esrc, tx,ty,tz,etgt) -> int
#     Ensures Implies(comp==k, Result() == prot_{k}(
#                 rebased_x(v, L,esrc, T,etgt),
#                 rebased_y(v, L,esrc, T,etgt),
#                 rebased_z(v, L,esrc, T,etgt), etgt))
#       <-- RE-REFERENCE FIRST to the OUTPUT frame's own anchoring, THEN rotate
#           at the OUTPUT frame's epoch. Pins (i) that the re-referencing step
#           happens at all, (ii) both of its endpoints, and (iii) the epoch of
#           the rotation.
#
#   rot_to_equ(comp, ox,oy,oz, lx,ly,lz,esrc, tx,ty,tz,etgt) -> int
#     Ensures Implies(comp==k, Result() == rebased_{k}(
#                 prot_inv_x(o, esrc), prot_inv_y(o, esrc), prot_inv_z(o, esrc),
#                 L,esrc, T,etgt))
#       <-- MIRROR ORDER: rotate FIRST with the transpose at the INPUT frame's
#           epoch, THEN re-reference the ROTATED position from the input frame's
#           own anchoring to the output frame's. Pins the order, the rotated
#           argument, and the epoch each step uses.
#
#   equ_rot_roundtrip(comp, vx,vy,vz, lx,ly,lz, e) -> int
#     Ensures Implies(comp==k, Result() == v_{k})   <-- EXACT IDENTITY, in the
#           special case where the two frames share ONE anchoring (site L,
#           epoch e) — the topocentric round trip the issue demands.
#
#   `rebased_c(v, L,esrc, T,etgt) = v_c + offset_c(v, L,esrc, T,etgt)` is a
#   `pure`-region (hence spec, hence attack-immutable) helper: the position once
#   REFERRED from the source anchoring to the target anchoring.
#
# KEY ARCHITECTURE OF THE SPEC (why the attacks land where they do):
#   * fwd_x/y/z(x,y,z,sx,sy,sz), bwd_x/y/z(x,y,z,sx,sy,sz) are @Pure
#     @ContractOnly with Ensures(True): TOTALLY UNINTERPRETED, and SITE-INDEXED
#     (M(S) and M(S') are unrelated for S != S'). The ONE fact the proof gets is
#     the `orthogonality(x,y,z,sx,sy,sz)` @ContractOnly axiom: bwd_*(fwd_*(v,S),S)
#     == v componentwise, AT ONE AND THE SAME site S. Nothing is claimed across
#     sites, so a rival that builds the matrix from the other end's site has no
#     fact to lean on. G-AX / axiom_check.py validate that against the REAL
#     rotation_matrix/matrix_transpose composites AND run the cross-site control.
#   * prot_x/y/z(x,y,z,e), prot_inv_x/y/z(x,y,z,e) are uninterpreted too, and
#     EPOCH-INDEXED: P(e) and P(e') are unrelated for e != e'. The ONE fact is
#     `prot_orthogonality(x,y,z,e)` — the transpose inverts the forward action
#     AT ONE AND THE SAME epoch. Nothing is claimed across epochs, so a rival
#     that rotates at the other epoch has no fact to lean on. G-AX validates
#     both the axiom and its epoch-sensitivity (a cross-epoch composition is
#     detectably not the identity).
#   * offset_x/y/z(v, L,esrc, T,etgt) is uninterpreted and depends on the
#     POSITION and on BOTH anchorings. The ONE fact is `same_frame_noop`:
#     offset_*(v, L,e, L,e) == 0 — the single instance where the two anchorings
#     are IDENTICAL. So the offset is provably absent only there; on every
#     differing anchoring it is an opaque nonzero quantity, and an impl that
#     omits the re-referencing step, or hands it a constant site, or hands it
#     the wrong epoch, or interchanges its endpoints, cannot match the pinned
#     value. G-AX validates that fact against the real re-referencing transform
#     AND runs the two controls (target site changed alone, target epoch changed
#     alone) that show the axiom does not extend beyond the
#     identical-anchoring instance.
#   * Every load-bearing postcondition pins Result() to a function OF THE
#     ARGUMENTS (fwd_* of the REBASED input at the named site; rebased_* of the
#     ROTATED input between the named anchorings; prot_* of the REBASED input at
#     the named epoch). So the oracle is GROUNDED in the inputs, NOT an opaque
#     answer-key a wrong impl could echo: the four `dropped-rereference-*` cases
#     below are exactly the echo attempt — each reuses the postcondition's own
#     uninterpreted oracle but on the un-rebased / un-rotated argument — and all
#     four are rejected.
#   * The round-trip postconditions do NOT by themselves force either pair
#     (`return vx` satisfies them), and the round trips only ever exercise the
#     IDENTICAL-anchoring case where the offset vanishes. So the uniqueness
#     attacks target the four directional conversions, where the discriminating
#     clauses live.
#
# NO read-only heap inputs: every parameter is a plain `int` (no Acc(...,1/2)).
# So the FRAME-MUTATION class is N/A (nothing to over-write for insufficient
# permission). Justified in 'assessment'. has_readonly_input = False.
from pathlib import Path

INSTANCE = "astropy__astropy-13398"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Verbatim gold impl bodies (each is the text between a # impl-start / # impl-end
# pair in model.py). Editing only inside one of these keeps spec_view — hence
# same_spec — byte-identical. Each block is UNIQUE in _BASE (different
# identifiers / different leading comment), so _swap targets it unambiguously.
# ---------------------------------------------------------------------------

# --- itrs_to_observed (anchoring-honouring forward) gold impl ---
_FWD_GOLD = """    # impl-start
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the orientation matrix
    # built from that same output frame's own site T.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# --- observed_to_itrs (anchoring-honouring backward) gold impl ---
_BWD_GOLD = """    # impl-start
    # Rotate with the transpose of the orientation matrix built from the INPUT
    # frame's own site L, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# --- observed_roundtrip (direct round-trip) gold impl ---
_RT_GOLD = """    # impl-start
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
    # impl-end"""

# --- equ_to_rot (anchoring-honouring forward) gold impl ---
_C2I_GOLD = """    # impl-start
    # Refer the position to the OUTPUT frame's own anchoring (site T, epoch
    # etgt), then rotate the re-referred position with the Earth-orientation
    # rotation for that same epoch etgt.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end"""

# --- rot_to_equ (anchoring-honouring backward) gold impl ---
_I2C_GOLD = """    # impl-start
    # Rotate with the transpose of the Earth-orientation rotation for the INPUT
    # frame's epoch esrc, then refer the rotated position from the input frame's
    # own anchoring to the output frame's anchoring.
    wx = prot_inv_x(ox, oy, oz, esrc)
    wy = prot_inv_y(ox, oy, oz, esrc)
    wz = prot_inv_z(ox, oy, oz, esrc)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# --- equ_rot_roundtrip (topocentric round-trip) gold impl ---
_ERQ_GOLD = """    # impl-start
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
    # impl-end"""

assert _FWD_GOLD in _BASE, "anchor drift: forward gold impl not found verbatim"
assert _BWD_GOLD in _BASE, "anchor drift: backward gold impl not found verbatim"
assert _RT_GOLD in _BASE, "anchor drift: round-trip gold impl not found verbatim"
assert _C2I_GOLD in _BASE, "anchor drift: equ_to_rot gold impl not found verbatim"
assert _I2C_GOLD in _BASE, "anchor drift: rot_to_equ gold impl not found verbatim"
assert _ERQ_GOLD in _BASE, "anchor drift: equ_rot_roundtrip gold impl not found"


# === (1) POSITIVE CONTROL — direct round-trip, structurally different, CORRECT
# Reorder the executable shape of observed_roundtrip: every proof step RETAINED
# (both same_frame_noop instances, the orthogonality instance at the shared site,
# and all the framing asserts) but the local bindings and asserts written in
# reverse component order. Same observable behaviour; the gold proof still
# discharges. If a faithful correct impl could NOT verify => SPEC-TOO-STRONG.
_RT_POS = """    # impl-start
    # Reverse component order throughout; every proof obligation retained.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qz == vz)
    Assert(qy == vy)
    Assert(qx == vx)
    oz = fwd_z(qx, qy, qz, lx, ly, lz)
    oy = fwd_y(qx, qy, qz, lx, ly, lz)
    ox = fwd_x(qx, qy, qz, lx, ly, lz)
    r2 = itrs_to_observed(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = itrs_to_observed(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r0 = itrs_to_observed(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r2 == oz)
    Assert(r1 == oy)
    Assert(r0 == ox)
    orthogonality(qx, qy, qz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    Assert(wz == vz)
    Assert(wy == vy)
    Assert(wx == vx)
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    return observed_to_itrs(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end"""

# === (2) POSITIVE CONTROL — direct backward, reordered + respelled (CORRECT) ====
# observed_to_itrs with the comp branches reordered and the re-referred result
# spelled through the `pure` helpers rebased_* instead of the inline
# `w_c + offset_c(...)` sum. Same order of operations (rotate with the matrix for
# the INPUT frame's own site, then refer from the input anchoring to the output
# anchoring) and the same value on every input. Must verify, else the spec would
# be pinning the SPELLING of the impl => SPEC-TOO-STRONG.
_BWD_POS = """    # impl-start
    # Reordered branches; the re-referred result spelled through the pure
    # helpers. Same matrix site, same re-referencing endpoints, same order.
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    if comp == 2:
        return rebased_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return rebased_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return rebased_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# === (3) ADMISSIBILITY — the precondition admits a normal F2P-shaped input ====
# Cannot add a top-level caller (that would leave the impl region and break
# same_spec). Instead, in-region in itrs_to_observed: re-derive the precondition
# consequence (comp is one of 0/1/2) and confirm a normal (non-raising) return is
# reachable for an in-domain input. If the Requires were vacuous / over-strong
# the impl could not both use the fact and return => PRECOND-TOO-STRONG.
_FWD_ADMISS = """    # impl-start
    # admissibility: the precondition (comp in {0,1,2}) is usable and a normal
    # (non-raising) return is reachable for an in-domain input.
    Assert(comp == 0 or comp == 1 or comp == 2)   # from Requires; usable
    wx = rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    Assert(comp == 2)                              # the only remaining case
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# === (4) POSITIVE CONTROL — direct forward reordered + respelled (CORRECT) =====
# itrs_to_observed with reverse-ordered local bindings, reordered comp branches,
# and the re-referred position spelled through the pure helpers. Identical value
# on every input: both endpoints of the re-referencing step, the site the matrix
# is built from, and the order of the two steps are unchanged. Must verify, else
# SPEC-TOO-STRONG on the most heavily pinned conversion in the bundle.
_FWD_POS = """    # impl-start
    # Reverse-ordered bindings, reordered branches, and the re-referred position
    # spelled through the pure helpers. Same anchorings, same matrix site.
    wz = rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wx = rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 2:
        return fwd_z(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_x(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# === (5) INDIRECT-ROUTE — direct forward reaches the frame indirectly (reject) =
# THE pre-change discriminator for pair (A). This is model_prepatch.py's forward
# impl: it does NOT apply the orientation matrix to the RE-REFERRED position; it
# first applies the transpose-action (routing through an intermediate geocentric
# frame) and then the forward action to the position AS GIVEN — fwd_*(bwd_*(v))
# instead of fwd_*(rebased(v)). That is the viewpoint-dependent
# stellar-aberration shift the issue describes. fwd_* / bwd_* are uninterpreted
# (Ensures(True)) so fwd_x(bwd_x(v),...) is NOT provably the pinned value.
_FWD_INDIRECT = """    # impl-start
    # INDIRECT route AND no re-referencing: apply the transpose-action first (an
    # extra intermediate-frame rotation), THEN the forward action, to the position
    # AS GIVEN — fwd_*(bwd_*(v)) rather than the direct rotation of the re-referred
    # position. This is the aberration-altering indirect path.
    ix = bwd_x(vx, vy, vz, tx, ty, tz)
    iy = bwd_y(vx, vy, vz, tx, ty, tz)
    iz = bwd_z(vx, vy, vz, tx, ty, tz)
    if comp == 0:
        return fwd_x(ix, iy, iz, tx, ty, tz)
    if comp == 1:
        return fwd_y(ix, iy, iz, tx, ty, tz)
    return fwd_z(ix, iy, iz, tx, ty, tz)
    # impl-end"""

# === (6) PARTIAL-DOMAIN — direct forward wrong on the LAST component (reject) ==
# Correct on comp 0 and comp 1, but for comp==2 returns fwd_y (the comp==1
# component) instead of fwd_z. The postcondition pins Implies(comp==2,
# Result()==fwd_z(rebased(v), T)); fwd_y and fwd_z are independent uninterpreted
# oracles, so the clause fails on the comp==2 sub-domain.
_FWD_PARTIAL = """    # impl-start
    wx = rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    # Emits the comp==1 component for comp==2.
    return fwd_y(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# === (7) WRONG-DIRECTION — direct backward applies M, not M^T (reject) =========
# observed_to_itrs is supposed to apply the TRANSPOSE action (inverse rotation)
# to the given position. This rival instead applies the FORWARD action
# fwd_*(o, L) (the matrix M rather than its transpose M^T). fwd_* and bwd_* are
# independent uninterpreted oracles (no contract relates fwd_x(o,S) to
# bwd_x(o,S)), so the pinned value cannot be proved.
_BWD_WRONGDIR = """    # impl-start
    # Applies the forward action (M) instead of the transpose (M^T), so it does
    # not invert the forward rotation and breaks the round trip.
    wx = fwd_x(ox, oy, oz, lx, ly, lz)
    wy = fwd_y(ox, oy, oz, lx, ly, lz)
    wz = fwd_z(ox, oy, oz, lx, ly, lz)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# === (8) PARTIAL-DOMAIN — direct round-trip ignores comp (reject) ==============
# observed_roundtrip must return the comp-th ORIGINAL component (Result()==v_comp
# exactly). This rival returns vx for every comp. Correct on comp==0, but on
# comp==1 the postcondition requires Result()==vy and on comp==2 Result()==vz;
# vx, vy, vz are independent free ints, so the clause fails on comp in {1,2}.
# (Keeps every proof obligation so the only behavioural change is the returned
# component — making the rejection attributable to the value, not a dropped
# proof step.)
_RT_IGNORECOMP = """    # impl-start
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qx == vx)
    Assert(qy == vy)
    Assert(qz == vz)
    ox = fwd_x(qx, qy, qz, lx, ly, lz)
    oy = fwd_y(qx, qy, qz, lx, ly, lz)
    oz = fwd_z(qx, qy, qz, lx, ly, lz)
    orthogonality(qx, qy, qz, lx, ly, lz)
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    Assert(wx == vx)
    Assert(wy == vy)
    Assert(wz == vz)
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    # Ignores comp, always recovers the FIRST component.
    return observed_to_itrs(0, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end"""

# === (9) DROPPED RE-REFERENCE — direct forward omits the step (reject) =========
# The over-approximation / oracle-echo attempt on the forward leg of pair (A):
# the impl reuses the postcondition's OWN uninterpreted oracle fwd_* at the OWN
# site T, but applies it to the position AS GIVEN — the re-referencing step is
# gone. This is the shape a spec whose forward postcondition carried NO anchoring
# would admit; it verifies against such a spec and does not resolve the instance
# (measured: 4/4 FAIL_TO_PASS pass but 5 of 68 PASS_TO_PASS fail, all five
# test_gcrs_altaz_bothroutes[testframe0..4]).
_FWD_DROPREF = """    # impl-start
    # Rotates the position as it stands: the re-referencing step to the OUTPUT
    # (observer-centred) frame's own anchoring is omitted, so a position held at
    # one site and epoch is treated as if it were already held at the output
    # frame's.
    if comp == 0:
        return fwd_x(vx, vy, vz, tx, ty, tz)
    if comp == 1:
        return fwd_y(vx, vy, vz, tx, ty, tz)
    return fwd_z(vx, vy, vz, tx, ty, tz)
    # impl-end"""

# === (10) DROPPED RE-REFERENCE — direct backward omits the step (reject) =======
# The same over-approximation on the backward leg of pair (A): return the rotated
# position un-referred, so the result is left anchored where the input was
# instead of where the output frame is. The echo control that matters most for
# this half: it returns exactly the postcondition's inner oracle bwd_*(o, L) and
# no more.
_BWD_DROPREF = """    # impl-start
    # Returns the rotated position un-referred: the step that brings it from the
    # input frame's anchoring to the output frame's is omitted.
    if comp == 0:
        return bwd_x(ox, oy, oz, lx, ly, lz)
    if comp == 1:
        return bwd_y(ox, oy, oz, lx, ly, lz)
    return bwd_z(ox, oy, oz, lx, ly, lz)
    # impl-end"""

# === (11) CONSTANT SITE — direct forward refers to the centre (reject) =========
# The re-referencing step is given ONE CONSTANT target site (0, 0, 0) — the
# centre of the Earth — rather than the output frame's own site T.
# same_frame_noop gives ONLY offset_*(v, L,e, L,e) == 0, never anything about
# offset_*(v, L,esrc, 0,0,0, etgt), so the pinned value cannot be established.
_FWD_CONSTSITE = """    # impl-start
    # Refers the position to ONE CONSTANT SITE (the centre of the Earth) at the
    # output epoch instead of to the OUTPUT frame's own site T.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# === (12) WRONG MATRIX SITE — direct forward builds M from the INPUT site ======
# Both steps are present with the right endpoints; only the site the ORIENTATION
# MATRIX is built from is taken from the wrong end of the conversion (the input
# frame's L instead of the observer-centred output frame's T). fwd_* is
# SITE-INDEXED and orthogonality relates one site only to itself, so nothing
# equates fwd_x(w, L) with fwd_x(w, T) for free sites.
_FWD_WRONGMATSITE = """    # impl-start
    wx = rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # Builds the orientation matrix from the INPUT frame's site instead of the
    # observer-centred OUTPUT frame's own site.
    if comp == 0:
        return fwd_x(wx, wy, wz, lx, ly, lz)
    if comp == 1:
        return fwd_y(wx, wy, wz, lx, ly, lz)
    return fwd_z(wx, wy, wz, lx, ly, lz)
    # impl-end"""

# === (13) WRONG MATRIX SITE — direct backward builds M^T from the OUTPUT site ==
# The mirror of (12) on the other leg: the transpose is built from the
# Earth-fixed OUTPUT frame's site T instead of the observer-centred INPUT frame's
# own site L. The two directions read OPPOSITE ends for the matrix, and this
# rival reads the same end as the forward one does.
_BWD_WRONGMATSITE = """    # impl-start
    # Builds the transpose from the OUTPUT frame's site instead of the
    # observer-centred INPUT frame's own site.
    wx = bwd_x(ox, oy, oz, tx, ty, tz)
    wy = bwd_y(ox, oy, oz, tx, ty, tz)
    wz = bwd_z(ox, oy, oz, tx, ty, tz)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# === (14) ORDER SWAP — direct forward rotates BEFORE referring (reject) ========
# The two conversions of pair (A) use OPPOSITE orders (forward: refer then
# rotate; backward: rotate then refer). This rival applies the forward leg in the
# backward leg's order. Both steps are present with the right endpoints and the
# right matrix site, so nothing but the order differs; the postcondition names
# the RE-REFERRED position as the argument of the matrix, and fwd_* of the
# un-referred position is unrelated to it.
_FWD_ORDERSWAP = """    # impl-start
    # Rotates FIRST and refers SECOND — the backward leg's order, applied to the
    # forward leg.
    wx = fwd_x(vx, vy, vz, tx, ty, tz)
    wy = fwd_y(vx, vy, vz, tx, ty, tz)
    wz = fwd_z(vx, vy, vz, tx, ty, tz)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# === (15) PARTIAL-DOMAIN GUARD — direct forward refers only where it is a no-op
# The narrowing attack on pair (A): honour the output frame's anchoring ONLY on
# the sub-domain where doing so is provably free (the two anchorings identical),
# and skip the step everywhere else. This is precisely the shape a spec that
# pinned only the tested same-anchoring round trip would admit. The postcondition
# pins the value on the WHOLE domain, so the else-branch — the interesting
# domain, where the two frames differ — cannot be discharged.
_FWD_GUARD = """    # impl-start
    # Only performs the re-referencing when the two anchorings coincide, i.e.
    # exactly when it changes nothing; skips it whenever they differ.
    if lx == tx and ly == ty and lz == tz and esrc == etgt:
        wx = rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
        wy = rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
        wz = rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    else:
        wx = vx
        wy = vy
        wz = vz
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# === (16) ENDPOINT SWAP — direct backward interchanges the anchorings (reject) =
# Both steps present, the matrix site right, the order right — but the
# re-referencing step is told the position is held at the OUTPUT frame's
# anchoring and wanted at the INPUT frame's, i.e. its two endpoints are
# interchanged. offset_* is uninterpreted in both endpoints and same_frame_noop
# covers only the case where they coincide.
_BWD_ENDPOINTSWAP = """    # impl-start
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    # Refers the rotated position FROM the output frame's anchoring TO the input
    # frame's — the two endpoints interchanged.
    if comp == 0:
        return wx + offset_x(wx, wy, wz, tx, ty, tz, etgt, lx, ly, lz, esrc)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, tx, ty, tz, etgt, lx, ly, lz, esrc)
    return wz + offset_z(wx, wy, wz, tx, ty, tz, etgt, lx, ly, lz, esrc)
    # impl-end"""

# === (16b) OVER-APPROXIMATION — offset sampled at the ROTATED position (reject) =
# Every step, endpoint, matrix site and the ORDER are gold; the only change is
# WHICH position the re-referencing shift is evaluated at. It is sampled at the
# already-rotated (observer-centred) vector and then added to the unrotated one.
# That is the position-independence over-approximation: it is sound only if the
# shift does not depend on the position it is applied to, which stellar
# aberration does.
_FWD_SAMPLEROT = """    # impl-start
    # Samples the re-referencing shift at the ROTATED position, then adds it to
    # the unrotated one before rotating.
    ax = fwd_x(vx, vy, vz, tx, ty, tz)
    ay = fwd_y(vx, vy, vz, tx, ty, tz)
    az = fwd_z(vx, vy, vz, tx, ty, tz)
    wx = vx + offset_x(ax, ay, az, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(ax, ay, az, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(ax, ay, az, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# === (16c) ORACLE ECHO — the no-op axiom invoked outside its scope (reject) =====
# Invokes same_frame_noop at two LEGAL instances (the source anchoring with
# itself, the target anchoring with itself) and then returns the bare rotation,
# as if those instances had established that the source-to-target offset also
# vanishes. Nothing in either instance mentions the cross-anchoring offset.
_FWD_AXIOMECHO = """    # impl-start
    # Two in-scope instances of the no-op axiom, then the bare rotation.
    same_frame_noop(vx, vy, vz, lx, ly, lz, esrc)
    same_frame_noop(vx, vy, vz, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(vx, vy, vz, tx, ty, tz)
    if comp == 1:
        return fwd_y(vx, vy, vz, tx, ty, tz)
    return fwd_z(vx, vy, vz, tx, ty, tz)
    # impl-end"""

# === (16d) CROSS-PAIR SUBSTITUTION — the other pair's rotation (reject) =========
# Keeps the re-referencing step verbatim but rotates with the epoch-indexed
# Earth-orientation matrix of the OTHER conversion pair instead of the
# site-indexed observer-orientation matrix. The two pairs share one offset
# family, so this is the freedom that sharing leaves.
_FWD_CROSSPAIR = """    # impl-start
    # Correct re-referencing, then the OTHER pair's epoch-indexed rotation.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end"""

# === (16e) PARTIAL-DOMAIN GUARD on the SITES ONLY — forward (reject) ============
# Wider than the same-anchoring sub-domain the other guard rival narrows to:
# this one re-references whenever the SITES differ but treats an epoch-only
# difference as needing nothing. The postcondition is universally quantified
# over both epoch carriers, so the shortcut branch must still hold.
_FWD_SITEGUARD = """    # impl-start
    # Skips the re-referencing whenever the two SITES agree, whatever the epochs.
    if lx == tx and ly == ty and lz == tz:
        if comp == 0:
            return fwd_x(vx, vy, vz, tx, ty, tz)
        if comp == 1:
            return fwd_y(vx, vy, vz, tx, ty, tz)
        return fwd_z(vx, vy, vz, tx, ty, tz)
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return fwd_x(wx, wy, wz, tx, ty, tz)
    if comp == 1:
        return fwd_y(wx, wy, wz, tx, ty, tz)
    return fwd_z(wx, wy, wz, tx, ty, tz)
    # impl-end"""

# === (16f) BOUNDARY TOKEN SWAP, SITES ONLY — backward (reject) ==================
# A single token pair moved: the re-referencing step's source SITE becomes T and
# its target SITE becomes L, while both EPOCHS keep their correct places. Finer
# than interchanging the whole anchorings, so it is not covered by that rival.
_BWD_SITESWAP = """    # impl-start
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    # Site endpoints exchanged; epoch endpoints left in their gold places.
    if comp == 0:
        return wx + offset_x(wx, wy, wz, tx, ty, tz, esrc, lx, ly, lz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, tx, ty, tz, esrc, lx, ly, lz, etgt)
    return wz + offset_z(wx, wy, wz, tx, ty, tz, esrc, lx, ly, lz, etgt)
    # impl-end"""

# === (16g) COMPONENT PERMUTATION inside the offset argument — backward (reject) =
# The returned component and every anchoring token are gold; only the position
# handed to the re-referencing step has its first two components exchanged.
_BWD_PERMARG = """    # impl-start
    wx = bwd_x(ox, oy, oz, lx, ly, lz)
    wy = bwd_y(ox, oy, oz, lx, ly, lz)
    wz = bwd_z(ox, oy, oz, lx, ly, lz)
    # The offset is sampled at a permuted copy of the rotated position.
    if comp == 0:
        return wx + offset_x(wy, wx, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wy, wx, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wy, wx, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# === (17) POSITIVE CONTROL — equ_to_rot reordered + respelled (CORRECT) =========
# equ_to_rot with the comp branches reordered, the three local bindings computed
# in reverse order, and the re-referred position spelled through the `pure`
# helpers rebased_* instead of the inline `v_c + offset_c(...)` sum. Identical
# value on every input; both endpoints of the re-referencing step and the epoch
# of the rotation are unchanged. Must verify, else SPEC-TOO-STRONG (the spec
# would be pinning the spelling of the impl rather than its observable value).
_C2I_POS = """    # impl-start
    # Reverse-ordered bindings, reordered branches, and the re-referred position
    # spelled through the pure helpers. Same anchorings, same rotation epoch.
    wz = rebased_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = rebased_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wx = rebased_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 2:
        return prot_z(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_x(wx, wy, wz, etgt)
    # impl-end"""

# === (18) POSITIVE CONTROL — rot_to_equ reordered + respelled (CORRECT) =========
# rot_to_equ with the comp branches reordered and the re-referred result spelled
# through the pure helpers. Same order of operations (rotate at the INPUT epoch,
# then re-reference from the input anchoring to the output anchoring) and the
# same value on every input. Must verify, else SPEC-TOO-STRONG.
_I2C_POS = """    # impl-start
    # Reordered branches; the re-referred result spelled through the pure
    # helpers. Same rotation epoch, same re-referencing endpoints.
    wx = prot_inv_x(ox, oy, oz, esrc)
    wy = prot_inv_y(ox, oy, oz, esrc)
    wz = prot_inv_z(ox, oy, oz, esrc)
    if comp == 2:
        return rebased_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return rebased_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return rebased_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# === (19) POSITIVE CONTROL — topocentric round-trip proof reordered (CORRECT) ==
# equ_rot_roundtrip with every proof step RETAINED (both same_frame_noop
# instances, the prot_orthogonality instance, and all the framing asserts) but
# the local bindings and asserts written in reverse component order. Same
# observable behaviour; the gold proof still discharges. Must verify, else
# SPEC-TOO-STRONG on the round-trip identity.
_ERQ_POS = """    # impl-start
    # Reverse component order throughout; every proof obligation retained.
    same_frame_noop(vx, vy, vz, lx, ly, lz, e)
    qz = rebased_z(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qy = rebased_y(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    qx = rebased_x(vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(qz == vz)
    Assert(qy == vy)
    Assert(qx == vx)
    oz = prot_z(qx, qy, qz, e)
    oy = prot_y(qx, qy, qz, e)
    ox = prot_x(qx, qy, qz, e)
    r2 = equ_to_rot(2, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r1 = equ_to_rot(1, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    r0 = equ_to_rot(0, vx, vy, vz, lx, ly, lz, e, lx, ly, lz, e)
    Assert(r2 == oz)
    Assert(r1 == oy)
    Assert(r0 == ox)
    prot_orthogonality(qx, qy, qz, e)
    wz = prot_inv_z(ox, oy, oz, e)
    wy = prot_inv_y(ox, oy, oz, e)
    wx = prot_inv_x(ox, oy, oz, e)
    Assert(wz == vz)
    Assert(wy == vy)
    Assert(wx == vx)
    same_frame_noop(wx, wy, wz, lx, ly, lz, e)
    Assert(rebased_z(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vz)
    Assert(rebased_y(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vy)
    Assert(rebased_x(wx, wy, wz, lx, ly, lz, e, lx, ly, lz, e) == vx)
    return rot_to_equ(comp, ox, oy, oz, lx, ly, lz, e, lx, ly, lz, e)
    # impl-end"""

# === (20) DROPPED RE-REFERENCE — equ_to_rot omits the step entirely (reject) ===
# The over-approximation / oracle-echo attempt in one: the impl reuses the
# postcondition's OWN uninterpreted oracle prot_* at the OWN epoch etgt, but
# applies it to the position AS GIVEN — the re-referencing step is gone. If the
# postcondition were an ungrounded answer-key this would verify. It cannot:
# rebased_c(v, L,esrc, T,etgt) = v_c + offset_c(...) and offset_* is only
# provably 0 when the two anchorings are IDENTICAL (same_frame_noop), which is
# not derivable for free L,esrc,T,etgt.
_C2I_DROPREF = """    # impl-start
    # Rotates the position as it stands: the re-referencing step to the OUTPUT
    # frame's own anchoring is omitted, so a position held at one site and epoch
    # is treated as if it were already held at the output frame's.
    if comp == 0:
        return prot_x(vx, vy, vz, etgt)
    if comp == 1:
        return prot_y(vx, vy, vz, etgt)
    return prot_z(vx, vy, vz, etgt)
    # impl-end"""

# === (21) CONSTANT SITE — equ_to_rot refers to the centre of the Earth (reject)
# This IS model_prepatch.py's equ_to_rot impl: the re-referencing step is given
# ONE CONSTANT target site (0, 0, 0) rather than the output frame's own site T.
# same_frame_noop gives ONLY offset_*(v, L,e, L,e) == 0, never anything about
# offset_*(v, L,esrc, 0,0,0,etgt), so the pinned value cannot be established.
_C2I_CONSTSITE = """    # impl-start
    # Refers the position to ONE CONSTANT SITE (the centre of the Earth) at the
    # output epoch instead of to the OUTPUT frame's own site T.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, 0, 0, 0, etgt)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end"""

# === (22) BOUNDARY TOKEN SWAP — equ_to_rot rotates at the INPUT epoch (reject) =
# A one-token change: the re-referencing step is exactly right, but the rotation
# is taken at the INPUT frame's epoch esrc rather than the OUTPUT frame's epoch
# etgt. P(e) is epoch-indexed and prot_orthogonality relates only one epoch to
# itself, so prot_x(w, esrc) is not provably prot_x(w, etgt).
_C2I_SRCEPOCH = """    # impl-start
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # Rotates at the INPUT frame's epoch instead of the OUTPUT frame's.
    if comp == 0:
        return prot_x(wx, wy, wz, esrc)
    if comp == 1:
        return prot_y(wx, wy, wz, esrc)
    return prot_z(wx, wy, wz, esrc)
    # impl-end"""

# === (23) BOUNDARY TOKEN SWAP — equ_to_rot re-refers to the INPUT epoch (reject)
# The mirror one-token change on the other carrier: the re-referencing step is
# given the output frame's SITE but the INPUT frame's EPOCH, so the position is
# brought to the right place at the wrong time. offset_* depends on both
# endpoints and nothing equates offset_*(v, L,esrc, T,esrc) with
# offset_*(v, L,esrc, T,etgt).
_C2I_SRCEPOCHREF = """    # impl-start
    # Refers the position to the output frame's SITE but at the INPUT frame's
    # EPOCH.
    wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
    wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
    wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, esrc)
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end"""

# === (24) PARTIAL-DOMAIN GUARD — equ_to_rot re-refers only when it is a no-op ==
# The narrowing attack: honour the output frame's anchoring ONLY on the
# sub-domain where doing so is provably free (the two anchorings identical), and
# skip the step everywhere else. This is precisely the shape a spec that pinned
# only the tested topocentric round trip would admit. The postcondition pins the
# value on the WHOLE domain, so the else-branch — the interesting domain, where
# the two frames differ — cannot be discharged.
_C2I_GUARD = """    # impl-start
    # Only performs the re-referencing when the two anchorings coincide, i.e.
    # exactly when it changes nothing; skips it whenever they differ.
    if lx == tx and ly == ty and lz == tz and esrc == etgt:
        wx = vx + offset_x(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
        wy = vy + offset_y(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
        wz = vz + offset_z(vx, vy, vz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    else:
        wx = vx
        wy = vy
        wz = vz
    if comp == 0:
        return prot_x(wx, wy, wz, etgt)
    if comp == 1:
        return prot_y(wx, wy, wz, etgt)
    return prot_z(wx, wy, wz, etgt)
    # impl-end"""

# === (25) WRONG-DIRECTION — rot_to_equ applies P, not P^T (reject) =============
# rot_to_equ must apply the TRANSPOSE rotation at the input epoch. This rival
# applies the FORWARD rotation prot_*(o, esrc). prot_* and prot_inv_* are
# independent uninterpreted oracles (prot_orthogonality relates
# prot_inv(prot(v,e),e) to v, never prot(o,e) to prot_inv(o,e)), so the pinned
# value cannot be proved.
_I2C_WRONGDIR = """    # impl-start
    # Applies the forward rotation P instead of its transpose P^T, so it does not
    # invert the forward rotation and breaks the topocentric round trip.
    wx = prot_x(ox, oy, oz, esrc)
    wy = prot_y(ox, oy, oz, esrc)
    wz = prot_z(ox, oy, oz, esrc)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    # impl-end"""

# === (26) DROPPED RE-REFERENCE — rot_to_equ omits the step entirely (reject) ===
# The echo attempt on the backward leg: reuse the postcondition's own oracle
# prot_inv_* at the right epoch but return it un-referred, so the result is left
# anchored where the input was instead of where the output frame is.
_I2C_DROPREF = """    # impl-start
    # Returns the rotated position un-referred: the step that brings it from the
    # input frame's anchoring to the output frame's is omitted.
    if comp == 0:
        return prot_inv_x(ox, oy, oz, esrc)
    if comp == 1:
        return prot_inv_y(ox, oy, oz, esrc)
    return prot_inv_z(ox, oy, oz, esrc)
    # impl-end"""

# === (27) ORDER SWAP — rot_to_equ re-refers BEFORE rotating (reject) ===========
# The freedom the repair leaves is the ORDER of the two steps, and the two
# conversions use OPPOSITE orders (forward: refer then rotate; backward: rotate
# then refer). This rival applies the backward leg in the forward leg's order —
# refer the Earth-rotating input first, then rotate. Both steps are present with
# the right endpoints and the right epoch, so nothing but the order differs; the
# postcondition names the rotated position as the argument of the re-referencing
# step, and offset_* of the un-rotated position is unrelated to it.
_I2C_ORDERSWAP = """    # impl-start
    # Refers the position FIRST and rotates SECOND — the forward leg's order,
    # applied to the backward leg.
    wx = ox + offset_x(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wy = oy + offset_y(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    wz = oz + offset_z(ox, oy, oz, lx, ly, lz, esrc, tx, ty, tz, etgt)
    if comp == 0:
        return prot_inv_x(wx, wy, wz, esrc)
    if comp == 1:
        return prot_inv_y(wx, wy, wz, esrc)
    return prot_inv_z(wx, wy, wz, esrc)
    # impl-end"""

# === (28) CONSTANT SOURCE SITE — rot_to_equ refers FROM the centre (reject) ====
# This IS model_prepatch.py's rot_to_equ impl: the re-referencing step is told
# the position is held at ONE CONSTANT site (0, 0, 0) rather than at the input
# frame's own site L, so it is referred from the wrong place.
_I2C_CONSTSRC = """    # impl-start
    # Refers the rotated position as if it were held at ONE CONSTANT SITE (the
    # centre of the Earth) instead of at the INPUT frame's own site L.
    wx = prot_inv_x(ox, oy, oz, esrc)
    wy = prot_inv_y(ox, oy, oz, esrc)
    wz = prot_inv_z(ox, oy, oz, esrc)
    if comp == 0:
        return wx + offset_x(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
    if comp == 1:
        return wy + offset_y(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
    return wz + offset_z(wx, wy, wz, 0, 0, 0, esrc, tx, ty, tz, etgt)
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-control-roundtrip-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _RT_GOLD, _RT_POS),
        "rationale": "Structurally different but correct: observed_roundtrip with "
                     "every proof step RETAINED (both same_frame_noop instances, "
                     "the orthogonality instance at the shared site, and all the "
                     "framing asserts) but the local bindings and asserts written "
                     "in reverse component order. Same behaviour; the gold proof "
                     "still discharges. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-forward-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_POS),
        "rationale": "itrs_to_observed with reverse-ordered local bindings, "
                     "reordered comp branches, and the re-referred position "
                     "spelled through the pure helpers rebased_* instead of the "
                     "inline `v_c + offset_c(...)` sum. Identical value on every "
                     "input: both endpoints of the re-referencing step, the site "
                     "the orientation matrix is built from, and the order of the "
                     "two steps are unchanged. Must verify, else the spec would be "
                     "pinning the SPELLING of the impl rather than its observable "
                     "value => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-backward-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_POS),
        "rationale": "observed_to_itrs with the comp branches reordered and the "
                     "re-referred result spelled through the pure helpers. Same "
                     "matrix site, same re-referencing endpoints, same order "
                     "(rotate then refer), same value on every input. A correct "
                     "re-shaping must verify, else SPEC-TOO-STRONG on the backward "
                     "conversion.",
    },
    {
        "id": "admissibility-forward-indomain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_ADMISS),
        "rationale": "In-region in itrs_to_observed: re-derives the precondition "
                     "(comp in {0,1,2}) as a usable fact and narrows to comp==2 on "
                     "the fall-through, reaching a normal (non-raising) return for "
                     "an F2P-shaped in-domain input. If the Requires were vacuous "
                     "or over-strong this could not both use the fact and return "
                     "=> PRECOND-TOO-STRONG.",
    },
    {
        "id": "pos-control-equ-to-rot-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _C2I_GOLD, _C2I_POS),
        "rationale": "equ_to_rot with reverse-ordered local bindings, reordered "
                     "comp branches, and the re-referred position spelled through "
                     "the pure helpers rebased_* instead of the inline "
                     "`v_c + offset_c(...)` sum. Identical value on every input: "
                     "both endpoints of the re-referencing step and the epoch of "
                     "the rotation are unchanged. Must verify, else the spec would "
                     "be pinning the SPELLING of the impl rather than its "
                     "observable value => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-rot-to-equ-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _I2C_GOLD, _I2C_POS),
        "rationale": "rot_to_equ with the comp branches reordered and the "
                     "re-referred result spelled through the pure helpers. Same "
                     "order of operations (rotate at the INPUT epoch, then refer "
                     "from the input anchoring to the output anchoring) and the "
                     "same value on every input. Must verify, else "
                     "SPEC-TOO-STRONG on the backward conversion.",
    },
    {
        "id": "pos-control-equ-rot-roundtrip-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _ERQ_GOLD, _ERQ_POS),
        "rationale": "equ_rot_roundtrip with every proof step RETAINED (both "
                     "same_frame_noop instances, the prot_orthogonality instance, "
                     "and all the framing asserts) but the bindings and asserts "
                     "written in reverse component order. Same observable "
                     "behaviour; the gold proof still discharges. Must verify, "
                     "else SPEC-TOO-STRONG on the round-trip identity.",
    },
    {
        "id": "dropped-rereference-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_DROPREF),
        "refinement": "A faithful real edit whose Earth-fixed -> observer-centred "
                      "conversion applies the orientation matrix to the position as "
                      "it stands, omitting the step that first brings the position "
                      "to the output frame's own site and obstime, alters the "
                      "stellar aberration whenever the two frames differ. Measured "
                      "on the real repo: this shape passes all 4 FAIL_TO_PASS tests "
                      "but fails 5 of the 68 PASS_TO_PASS tests, all five of "
                      "test_gcrs_altaz_bothroutes[testframe0..4], which compare the "
                      "direct route against the through-ITRS route between frames "
                      "whose obstimes/locations do not coincide. So the refined edit "
                      "does NOT resolve.",
        "rationale": "The over-approximation AND the oracle-echo attempt at once: "
                     "it reuses the postcondition's own uninterpreted oracle fwd_* "
                     "at the pinned site T, but applies it to the position AS "
                     "GIVEN. The postcondition pins Result() == "
                     "fwd_x(rebased_x(v,L,esrc,T,etgt), ..., T), and rebased_c "
                     "unfolds to v_c + offset_c(...). offset_* is uninterpreted; "
                     "the ONLY fact is same_frame_noop, which gives offset_* == 0 "
                     "solely when the two anchorings are IDENTICAL. For free "
                     "L,esrc,T,etgt that is not derivable, so fwd_x(v, T) is not "
                     "provably fwd_x(rebased(v), T). Source: itrs_to_observed's "
                     "refer-then-rotate postcondition.",
    },
    {
        "id": "dropped-rereference-backward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_DROPREF),
        "refinement": "The same omission on the backward leg: a faithful real edit "
                      "that returns the rotated position without the final step "
                      "that refers it from the observer-centred frame's own "
                      "anchoring to the Earth-fixed frame the caller asked for "
                      "leaves the result anchored at the input's site and obstime. "
                      "test_gcrs_altaz_bothroutes compares the two routes between "
                      "frames whose anchorings differ and fails, so the refined edit "
                      "does NOT resolve.",
        "rationale": "The echo attempt on the backward leg of pair (A): it returns "
                     "exactly the postcondition's inner oracle bwd_*(o, L) and no "
                     "more. The postcondition pins Result() == "
                     "rebased_c(bwd_x(o,L), bwd_y(o,L), bwd_z(o,L), L,esrc, T,etgt) "
                     "= bwd_c(o,L) + offset_c(...), and offset_* is provably 0 only "
                     "for identical anchorings (same_frame_noop), which does not "
                     "hold for free L,esrc,T,etgt. Source: observed_to_itrs's "
                     "re-referencing clause.",
    },
    {
        "id": "indirect-route-prepatch-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_INDIRECT),
        "refinement": "This IS the pre-change behaviour (model_prepatch.py): the "
                      "forward conversion reaches the observer-centred orientation "
                      "INDIRECTLY (route ITRS -> intermediate (geocentric) frame -> "
                      "Observed), inserting an extra frame rotation so it computes "
                      "fwd_*(bwd_*(v)) rather than applying the orientation matrix "
                      "to the RE-REFERRED position. That is the geocentric-vs-"
                      "topocentric stellar-aberration shift the issue describes; the "
                      "F2P tests (test_itrs_straight_overhead, test_cirs_itrs_topo, "
                      "the no-pressure refraction round-trip blocks) assert the "
                      "EXACT round-trip identity (Alt=90 to 1*u.uas, default "
                      "assert_allclose on itrs.{x,y,z}) which this indirect route "
                      "breaks — so the faithful real edit does NOT resolve.",
        "rationale": "fwd_* / bwd_* are uninterpreted (@Pure @ContractOnly, "
                     "Ensures(True)); the ONLY relating fact is orthogonality "
                     "(bwd_*(fwd_*(v,S),S)==v at one site), which gives nothing "
                     "about fwd_x(bwd_x(v,T),bwd_y(v,T),bwd_z(v,T),T). So the "
                     "load-bearing forward postcondition cannot be established. "
                     "Source: itrs_to_observed's postcondition (this is exactly the "
                     "G-DIFF clause).",
    },
    {
        "id": "partial-domain-forward-comp2",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_PARTIAL),
        "refinement": "A faithful real edit correct on the first two output "
                      "components but emitting the y-component for the z slot would "
                      "produce a mismatched third Cartesian coordinate; the F2P "
                      "tests compare ALL THREE of itrs.{x,y,z} (assert_allclose on "
                      "each), so the round trip's z-component mismatch makes the "
                      "test FAIL — the refined edit does NOT resolve.",
        "rationale": "The postcondition pins Implies(comp==2, "
                     "Result()==fwd_z(rebased(v), T)). fwd_y and fwd_z are "
                     "independent uninterpreted oracles (no contract equates them), "
                     "so returning fwd_y on comp==2 cannot satisfy the comp==2 "
                     "clause. Source: the per-component forward postcondition (the "
                     "comp==2 sub-domain).",
    },
    {
        "id": "wrong-direction-backward-uses-M",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_WRONGDIR),
        "refinement": "A faithful real edit whose backward conversion applies the "
                      "orientation matrix M itself (not its transpose M^T) does NOT "
                      "invert the forward rotation: observed_to_itrs(itrs_to_observed"
                      "(v)) = M(M v) != v in general, so the round trip is not the "
                      "identity and test_itrs_straight_overhead / test_cirs_itrs_topo "
                      "(exact assert_allclose back to the input ITRS xyz) FAIL — the "
                      "refined edit does NOT resolve.",
        "rationale": "The backward postcondition pins the argument of the "
                     "re-referencing step to bwd_*(o, L) (the M(L)^T action). fwd_* "
                     "and bwd_* are independent uninterpreted oracles — "
                     "orthogonality only relates bwd(fwd(v,S),S) to v, never "
                     "fwd(o,S) to bwd(o,S) — so the rival's value is not provably "
                     "the pinned one. Source: observed_to_itrs's transpose-action "
                     "postcondition.",
    },
    {
        "id": "wrong-matrix-site-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_WRONGMATSITE),
        "refinement": "The real forward conversion builds the orientation matrix "
                      "from the OBSERVER-CENTRED frame's own site "
                      "(observed_frame.location.to_geodetic('WGS84'), "
                      "itrs_observed_transforms.py:112), and its mirror builds it "
                      "from observed_coo.location (:129) — both read the "
                      "observer-centred end. A faithful real edit that built the "
                      "matrix from the OTHER end's location would rotate into an "
                      "orientation defined by the wrong observatory: the horizon "
                      "would be tilted by the angle between the two sites, so "
                      "test_itrs_straight_overhead's Alt=90 assertion (to 1*u.uas) "
                      "and every through-ITRS comparison FAIL — the refined edit "
                      "does NOT resolve.",
        "rationale": "Both re-referencing endpoints are right and the order is "
                     "right; only the site the matrix is built from is taken from "
                     "the wrong end. fwd_* is SITE-INDEXED and orthogonality relates "
                     "one site only to itself, so no fact equates fwd_x(w, L) with "
                     "fwd_x(w, T) for free sites. Source: the site arguments of "
                     "fwd_* in itrs_to_observed's postcondition. (G-AX measures the "
                     "cross-site composition as detectably not the identity, so the "
                     "site carrier is observable, not decorative.)",
    },
    {
        "id": "wrong-matrix-site-backward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_WRONGMATSITE),
        "refinement": "The mirror of the previous case: the real backward "
                      "conversion takes the site from observed_coo.location "
                      "(itrs_observed_transforms.py:129) — the observer-centred "
                      "INPUT — whereas this rival takes it from the Earth-fixed "
                      "output frame. The two directions genuinely read OPPOSITE ends "
                      "of the conversion for the matrix, so a real edit that read "
                      "the same end in both would un-rotate with a matrix built for "
                      "a different observatory and break every ITRS<->Observed round "
                      "trip — the refined edit does NOT resolve.",
        "rationale": "bwd_* is SITE-INDEXED; nothing equates bwd_x(o, T) with "
                     "bwd_x(o, L) for free sites, and orthogonality is single-site. "
                     "Source: the site arguments of bwd_* in observed_to_itrs's "
                     "postcondition.",
    },
    {
        "id": "order-swap-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_ORDERSWAP),
        "refinement": "The two conversions of the pair genuinely use OPPOSITE "
                      "orders: the forward one refers the position "
                      "(itrs_observed_transforms.py:106-110) and THEN applies the "
                      "matrix (:115/:121); the backward one applies the transpose "
                      "(:137/:139) and THEN refers (:141-145). A faithful real edit "
                      "that used the backward order on the forward leg would apply "
                      "the aberration re-referencing to an already-rotated "
                      "(observer-centred) vector, i.e. in the wrong frame; the "
                      "direct and through-ITRS routes then disagree and "
                      "test_gcrs_altaz_bothroutes fails — the refined edit does NOT "
                      "resolve.",
        "rationale": "This attacks the freedom the postcondition shape leaves: "
                     "WHICH position each step acts on. Both steps are present, "
                     "with the right endpoints and the right matrix site; only the "
                     "order differs. The postcondition names the RE-REFERRED "
                     "position as the argument of fwd_*, and offset_* of the "
                     "ROTATED position is an unrelated uninterpreted value, so the "
                     "pinned equality cannot be established. Source: the nesting in "
                     "itrs_to_observed's postcondition (fwd_* OF rebased_*).",
    },
    {
        "id": "partial-domain-guard-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_GUARD),
        "refinement": "A faithful real edit that performs the re-referencing ONLY "
                      "when the two frames already agree in site and obstime — i.e. "
                      "exactly when it changes nothing — is observationally "
                      "identical to omitting it. It passes every "
                      "matching-anchoring assertion (all four F2P tests use one "
                      "location and one obstime) and still fails "
                      "test_gcrs_altaz_bothroutes, which compares routes between "
                      "frames whose anchorings differ. So the refined edit does NOT "
                      "resolve — and this is exactly the shape a spec that pinned "
                      "only the tested same-anchoring round trip would admit.",
        "rationale": "The narrowing attack on pair (A): it satisfies the "
                     "postcondition on the sub-domain where offset_* is provably 0 "
                     "(same_frame_noop) and drops the step on the complement. The "
                     "postcondition is universally quantified over the free "
                     "anchoring carriers, so the else-branch must still equal fwd_* "
                     "of the REBASED position, which is not derivable when the "
                     "anchorings differ. Source: itrs_to_observed's postcondition "
                     "holding on the WHOLE domain, not only where the re-referencing "
                     "is a no-op.",
    },
    {
        "id": "endpoint-swap-backward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_ENDPOINTSWAP),
        "refinement": "A faithful real edit that built the intermediate frame from "
                      "the OUTPUT frame's anchoring and transformed it to the INPUT "
                      "frame's — instead of gold's ITRS(crepr, "
                      "obstime=observed_coo.obstime, location=observed_coo.location) "
                      ".transform_to(itrs_frame) at "
                      "itrs_observed_transforms.py:141-145 — would apply the "
                      "aberration difference with the opposite sign and land at the "
                      "wrong frame; every differing-anchoring comparison "
                      "(test_gcrs_altaz_bothroutes) fails, so the refined edit does "
                      "NOT resolve.",
        "rationale": "Both steps present, the matrix site right, the order right; "
                     "only the two endpoints of the re-referencing step are "
                     "interchanged. offset_* is uninterpreted in BOTH endpoints and "
                     "same_frame_noop covers only the instance where they coincide, "
                     "so nothing equates offset_*(w, T,etgt, L,esrc) with "
                     "offset_*(w, L,esrc, T,etgt). Source: the argument ORDER of the "
                     "anchorings in observed_to_itrs's postcondition.",
    },
    {
        "id": "offset-sampled-at-rotated-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_SAMPLEROT),
        "refinement": "A faithful real edit that computed the aberration "
                      "difference for the OBSERVER-CENTRED (already rotated) vector "
                      "and applied it to the Earth-fixed one would be sampling the "
                      "shift in the wrong frame. Stellar aberration depends on the "
                      "direction and distance of the position it acts on, so the "
                      "two samples differ; the direct ITRS->AltAz route then "
                      "disagrees with the through-CIRS route and "
                      "test_gcrs_altaz_bothroutes fails — the refined edit does NOT "
                      "resolve.",
        "rationale": "The over-approximation attack: it is sound only if offset_* "
                     "is independent of its position argument. offset_* is "
                     "uninterpreted, so nothing equates offset_*(fwd_*(v,T), ...) "
                     "with offset_*(v, ...); every step, endpoint, matrix site and "
                     "the order are otherwise gold. Source: the position argument "
                     "of rebased_* inside itrs_to_observed's postcondition is the "
                     "GIVEN (vx,vy,vz), matching itrs_observed_transforms.py:109, "
                     "where the re-reference acts on itrs_coo before :115 rotates "
                     "it.",
    },
    {
        "id": "axiom-echo-out-of-scope-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_AXIOMECHO),
        "refinement": "A faithful real edit that checked each frame against ITSELF "
                      "— rather than the input frame against the output frame, as "
                      "gold's guard at itrs_observed_transforms.py:106-107 does — "
                      "would find both checks trivially satisfied and skip the "
                      "re-reference on every input, including the "
                      "differing-anchoring ones. That is behaviourally the dropped "
                      "step, so test_gcrs_altaz_bothroutes fails and the refined "
                      "edit does NOT resolve.",
        "rationale": "The oracle-echo attack: it invokes two LEGAL instances of "
                     "same_frame_noop (each anchoring against itself) and returns "
                     "the bare rotation as though they had established that the "
                     "SOURCE-to-TARGET offset also vanishes. Each instance mentions "
                     "only offset_*(v, L,esrc, L,esrc) resp. offset_*(v, T,etgt, "
                     "T,etgt); neither constrains offset_*(v, L,esrc, T,etgt), so "
                     "the pinned equality is not derivable. Source: the scope of "
                     "same_frame_noop's Ensures — one anchoring, used on both sides.",
    },
    {
        "id": "cross-pair-rotation-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_CROSSPAIR),
        "refinement": "A faithful real edit that rotated with the "
                      "Earth-orientation matrix cirs_to_itrs_mat(obstime) instead of "
                      "the observer-orientation matrix built from the site's "
                      "geodetic lon/lat (itrs_observed_transforms.py:112,115) would "
                      "produce an equatorial, not an horizon, orientation: Alt/Az "
                      "would be wrong by the observatory's colatitude. "
                      "test_itrs_straight_overhead, which asserts Alt = 90 deg for a "
                      "position directly above the site, fails — the refined edit "
                      "does NOT resolve.",
        "rationale": "This attacks the freedom left by binding ONE offset family to "
                     "both conversion pairs: it keeps the re-referencing step "
                     "verbatim and substitutes the other pair's rotation. prot_* is "
                     "epoch-indexed and fwd_* site-indexed; both are uninterpreted "
                     "and no axiom relates them, so prot_x(w, etgt) cannot be shown "
                     "equal to fwd_x(w, tx,ty,tz). Source: the rotation named in "
                     "itrs_to_observed's postcondition is fwd_*, carrying a SITE.",
    },
    {
        "id": "site-only-guard-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_SITEGUARD),
        "refinement": "A faithful real edit whose guard tested only "
                      "itrs_coo.location != observed_frame.location — dropping the "
                      "obstime half of gold's condition at "
                      "itrs_observed_transforms.py:106-107 — would skip the "
                      "re-reference for one observatory observed at two different "
                      "times. The Earth has rotated and the aberration differs "
                      "between the two epochs, so the direct and through-CIRS routes "
                      "disagree there and test_gcrs_altaz_bothroutes fails; the "
                      "refined edit does NOT resolve.",
        "rationale": "A partial-domain narrowing STRICTLY WIDER than the "
                     "same-anchoring one: the shortcut branch covers every "
                     "epoch-only difference, where offset_* is NOT provably zero "
                     "(same_frame_noop needs both carriers equal). The "
                     "postcondition is universally quantified over esrc and etgt, "
                     "so that branch must still equal fwd_* of the rebased "
                     "position. Source: itrs_to_observed's postcondition names "
                     "esrc and etgt as independent arguments of rebased_*.",
    },
    {
        "id": "site-endpoint-swap-backward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_SITESWAP),
        "refinement": "A faithful real edit that built the intermediate frame with "
                      "location=itrs_frame.location while keeping "
                      "obstime=observed_coo.obstime — i.e. half of gold's "
                      "itrs_observed_transforms.py:141-142 — would refer the "
                      "rotated position out of an observatory it was never held at. "
                      "The aberration difference is then applied with the wrong site "
                      "on both ends and test_gcrs_altaz_bothroutes fails, so the "
                      "refined edit does NOT resolve.",
        "rationale": "A single token pair moved, finer than interchanging the whole "
                     "anchorings: the SITE endpoints are exchanged and both EPOCH "
                     "endpoints left in place. offset_* is uninterpreted in each of "
                     "its four anchoring slots and same_frame_noop covers only the "
                     "case where the two anchorings coincide entirely, so nothing "
                     "equates offset_*(w, T,esrc, L,etgt) with offset_*(w, L,esrc, "
                     "T,etgt). Source: the site arguments of rebased_* in "
                     "observed_to_itrs's postcondition.",
    },
    {
        "id": "permuted-offset-argument-backward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_PERMARG),
        "refinement": "A faithful real edit that handed the re-referencing step a "
                      "position with two Cartesian components transposed would ask "
                      "for the aberration difference of a DIFFERENT direction on the "
                      "sky. Off the diagonal x == y that is a different vector, so "
                      "the recovered ITRS position is wrong and every "
                      "differing-anchoring comparison fails — the refined edit does "
                      "NOT resolve.",
        "rationale": "Attacks the freedom in WHICH vector the offset is sampled at, "
                     "at component granularity: the returned component and all four "
                     "anchoring slots are gold. offset_* is uninterpreted in its "
                     "position arguments, so offset_x(wy, wx, wz, ...) is an "
                     "unrelated value to offset_x(wx, wy, wz, ...). Source: the "
                     "argument ORDER of the bwd_* triple inside rebased_* in "
                     "observed_to_itrs's postcondition.",
    },
    {
        "id": "partial-domain-roundtrip-ignore-comp",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RT_GOLD, _RT_IGNORECOMP),
        "refinement": "A faithful real edit that always recovers the first "
                      "Cartesian component for every requested component would "
                      "collapse the round-tripped position to (vx,vx,vx); the F2P "
                      "tests assert_allclose on each of itrs.{x,y,z} back to the "
                      "ORIGINAL (vx,vy,vz), so the y and z comparisons FAIL — the "
                      "refined edit does NOT resolve.",
        "rationale": "observed_roundtrip's postcondition pins Implies(comp==1, "
                     "Result()==vy) and Implies(comp==2, Result()==vz). Returning "
                     "observed_to_itrs(0,...) == vx (by orthogonality + "
                     "same_frame_noop) on every comp satisfies comp==0 but vx, vy, "
                     "vz are independent free ints, so the comp in {1,2} clauses "
                     "fail. Source: the round-trip identity postcondition "
                     "(per-component).",
    },
    {
        "id": "dropped-rereference-equ-to-rot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C2I_GOLD, _C2I_DROPREF),
        "refinement": "A faithful real edit whose Earth-equatorial -> "
                      "Earth-rotating conversion rotates the position as it stands, "
                      "omitting the step that brings it to the output frame's own "
                      "site and epoch, leaves a topocentric position referred to "
                      "the input frame's anchoring. test_cirs_itrs_topo transforms "
                      "CIRS at one obstime through ITRS and back into a CIRS frame "
                      "at a DIFFERENT obstime and asserts the result is NOT the "
                      "input, while the same-obstime route IS — an omitted "
                      "re-referencing step makes the two routes agree, so the "
                      "assertion fails; test_gcrs_altaz_bothroutes and "
                      "test_teme_loopback compare the direct and through-ITRS "
                      "routes and fail likewise. Measured: the reproduction of this "
                      "shape fails FAIL_TO_PASS test_cirs_itrs_topo and 7 "
                      "PASS_TO_PASS tests. So the refined edit does NOT resolve.",
        "rationale": "This is the over-approximation AND the oracle-echo attempt at "
                     "once: it reuses the postcondition's own uninterpreted oracle "
                     "prot_* at the pinned epoch etgt, but applies it to the "
                     "position AS GIVEN. The postcondition pins Result() == "
                     "prot_x(rebased_x(v,L,esrc,T,etgt), ...), and rebased_c "
                     "unfolds to v_c + offset_c(...). offset_* is uninterpreted; "
                     "the ONLY fact is same_frame_noop, which gives offset_* == 0 "
                     "solely when the two anchorings are IDENTICAL. For free "
                     "L,esrc,T,etgt that is not derivable, so prot_x(v, etgt) is "
                     "not provably prot_x(rebased(v), etgt). Source: equ_to_rot's "
                     "re-reference-then-rotate postcondition.",
    },
    {
        "id": "constant-site-prepatch-equ-to-rot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C2I_GOLD, _C2I_CONSTSITE),
        "refinement": "This IS the pre-change behaviour (model_prepatch.py): the "
                      "Earth-equatorial <-> Earth-rotating conversion refers the "
                      "position to the centre of the Earth "
                      "(location=EARTH_CENTER) rather than to the output frame's "
                      "own site, so a topocentric position carries the "
                      "geocentric-vs-topocentric stellar-aberration offset. The F2P "
                      "tests (test_itrs_topo_to_altaz_with_refraction, "
                      "test_itrs_topo_to_hadec_with_refraction, test_cirs_itrs_topo) "
                      "compare the through-ITRS route against the direct route and "
                      "FAIL when this offset is present (G-AX measures a "
                      "detectably nonzero constant-centre offset on every "
                      "topocentric witness) — so the faithful real edit does NOT "
                      "resolve.",
        "rationale": "offset_* is uninterpreted; the ONLY relating fact is "
                     "same_frame_noop (offset_*(v,L,e,L,e)==0), which gives nothing "
                     "about offset_*(v,L,esrc,0,0,0,etgt). So the result is not "
                     "provably prot_x of the position referred to the OUTPUT "
                     "frame's own site T. Source: equ_to_rot's postcondition, which "
                     "names T (and etgt) as the re-referencing target — exactly the "
                     "G-DIFF clause for this modeled change.",
    },
    {
        "id": "constant-site-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_CONSTSITE),
        "refinement": "The same constant-site error on pair (A): a faithful real "
                      "edit whose forward conversion builds its intermediate "
                      "Earth-fixed frame with the default centre-of-the-Earth "
                      "location instead of observed_frame.location "
                      "(itrs_observed_transforms.py:109-110) refers a topocentric "
                      "position to the geocentre, picking up the "
                      "geocentric-vs-topocentric aberration difference; the "
                      "through-ITRS and direct routes then disagree and "
                      "test_gcrs_altaz_bothroutes fails, so the refined edit does "
                      "NOT resolve.",
        "rationale": "same_frame_noop gives ONLY offset_*(v,L,e,L,e)==0, never "
                     "anything about offset_*(v,L,esrc,0,0,0,etgt), so the result is "
                     "not provably fwd_* of the position referred to the OUTPUT "
                     "frame's own site T. Source: itrs_to_observed's postcondition, "
                     "which names T (and etgt) as the re-referencing target.",
    },
    {
        "id": "input-epoch-rotation-equ-to-rot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C2I_GOLD, _C2I_SRCEPOCH),
        "refinement": "A faithful real edit that builds the Earth-orientation "
                      "matrix from the INPUT frame's obstime rather than the output "
                      "frame's rotates the Earth to the wrong sidereal angle "
                      "whenever the two obstimes differ (six years apart in "
                      "test_cirs_itrs_topo, which asserts the two routes are "
                      "distinguishable and the matching-obstime route is the "
                      "identity); the ITRS<->ITRS loopback that goes through this "
                      "conversion then fails, so the refined edit does NOT resolve.",
        "rationale": "One-token change (etgt -> esrc in the rotation). prot_* is "
                     "EPOCH-INDEXED and prot_orthogonality relates one epoch only "
                     "to itself, so no fact equates prot_x(w, esrc) with "
                     "prot_x(w, etgt) for free epochs. Source: the epoch argument "
                     "of the rotation in equ_to_rot's postcondition. (G-AX measures "
                     "the cross-epoch composition as detectably not the identity, "
                     "so the epoch carrier is observable, not decorative.)",
    },
    {
        "id": "input-epoch-rereference-equ-to-rot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C2I_GOLD, _C2I_SRCEPOCHREF),
        "refinement": "A faithful real edit that refers the position to the output "
                      "frame's SITE but at the INPUT frame's EPOCH brings it to the "
                      "right place at the wrong time: the two Earth-equatorial "
                      "frames' axes differ by the precession between the epochs, so "
                      "the through-ITRS route no longer agrees with the direct route "
                      "and test_cirs_itrs_topo / test_gcrs_altaz_bothroutes fail — "
                      "the refined edit does NOT resolve.",
        "rationale": "The mirror one-token change, on the other carrier. offset_* "
                     "depends on BOTH anchorings and is uninterpreted; nothing "
                     "equates offset_*(v,L,esrc,T,esrc) with "
                     "offset_*(v,L,esrc,T,etgt) for free epochs. Source: the target "
                     "EPOCH argument of the re-referencing step in equ_to_rot's "
                     "postcondition.",
    },
    {
        "id": "partial-domain-guard-equ-to-rot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _C2I_GOLD, _C2I_GUARD),
        "refinement": "A faithful real edit that performs the re-referencing ONLY "
                      "when the two frames already agree in site and epoch — i.e. "
                      "exactly when it changes nothing — is observationally "
                      "identical to omitting the step. It passes the "
                      "matching-anchoring assertions (the ITRS<->Observed tests, "
                      "which all use one location and one obstime) but fails "
                      "test_cirs_itrs_topo, whose second leg targets a CIRS frame "
                      "at a DIFFERENT obstime and asserts the result differs from "
                      "the input; with the step skipped the two routes coincide. So "
                      "the refined edit does NOT resolve.",
        "rationale": "The narrowing attack: it satisfies the postcondition on the "
                     "sub-domain where offset_* is provably 0 (same_frame_noop) and "
                     "drops the step on the complement. The postcondition is "
                     "universally quantified over the free anchoring carriers, so "
                     "the else-branch must still equal prot_* of the REBASED "
                     "position, which is not derivable when the anchorings differ. "
                     "Source: equ_to_rot's postcondition holding on the WHOLE "
                     "domain, not only where the re-referencing is a no-op. This is "
                     "the case that would verify against a spec that pinned only "
                     "the tested topocentric round trip.",
    },
    {
        "id": "wrong-direction-rot-to-equ-uses-P",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I2C_GOLD, _I2C_WRONGDIR),
        "refinement": "A faithful real edit whose backward Earth-rotating -> "
                      "Earth-equatorial conversion applies the Earth-orientation "
                      "matrix P itself (not its transpose P^T) does NOT invert the "
                      "forward rotation: rot_to_equ(equ_to_rot(v)) = P(P v) != v in "
                      "general, so the topocentric round trip (test_cirs_itrs_topo) "
                      "is not the identity and the test FAILS — the refined edit "
                      "does NOT resolve.",
        "rationale": "The backward postcondition pins the argument of the "
                     "re-referencing step to prot_inv_*(o, esrc). prot_* and "
                     "prot_inv_* are independent uninterpreted oracles — "
                     "prot_orthogonality relates prot_inv(prot(v,e),e) to v, never "
                     "prot(o,e) to prot_inv(o,e) — so the rival's value is not "
                     "provably the pinned one. Source: rot_to_equ's "
                     "transpose-rotation postcondition.",
    },
    {
        "id": "dropped-rereference-rot-to-equ",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I2C_GOLD, _I2C_DROPREF),
        "refinement": "A faithful real edit that returns the rotated position "
                      "without referring it from the input frame's anchoring to the "
                      "output frame's leaves the result anchored where the input "
                      "was. That is the second half of the same defect the issue "
                      "reports: the ITRS<->ITRS loopback goes through this "
                      "conversion, so test_cirs_itrs_topo's differing-obstime leg "
                      "and test_teme_loopback / test_gcrs_altaz_bothroutes fail — "
                      "the refined edit does NOT resolve.",
        "rationale": "The oracle-echo attempt on the backward leg: it returns "
                     "exactly the postcondition's inner oracle prot_inv_*(o,esrc) "
                     "and no more. The postcondition pins Result() == "
                     "rebased_c(prot_inv(o,esrc), L,esrc, T,etgt) = "
                     "prot_inv_c(o,esrc) + offset_c(...), and offset_* is provably "
                     "0 only for identical anchorings (same_frame_noop), which does "
                     "not hold for free L,esrc,T,etgt. Source: rot_to_equ's "
                     "re-referencing clause.",
    },
    {
        "id": "order-swap-rot-to-equ",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I2C_GOLD, _I2C_ORDERSWAP),
        "refinement": "The two conversions genuinely use OPPOSITE orders: the "
                      "forward one refers the position and then rotates at the "
                      "output epoch; the backward one rotates at the input epoch "
                      "and then refers. A faithful real edit that used the forward "
                      "order on the backward leg would re-reference an "
                      "Earth-rotating (body-fixed) position as though it were an "
                      "Earth-equatorial one, applying the aberration difference in "
                      "the wrong frame; the through-ITRS and direct routes then "
                      "disagree and test_cirs_itrs_topo / "
                      "test_gcrs_altaz_bothroutes fail — the refined edit does NOT "
                      "resolve.",
        "rationale": "This attacks the freedom the postcondition shape leaves: "
                     "WHICH position the re-referencing step acts on. Both steps "
                     "are present, with the right endpoints and the right epoch; "
                     "only the order differs. The postcondition names the ROTATED "
                     "position as the re-referencing argument, and offset_* of the "
                     "un-rotated input is an unrelated uninterpreted value, so the "
                     "pinned equality cannot be established. Source: the nesting in "
                     "rot_to_equ's postcondition (rebased_* OF prot_inv_*).",
    },
    {
        "id": "constant-source-site-prepatch-rot-to-equ",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I2C_GOLD, _I2C_CONSTSRC),
        "refinement": "This IS the pre-change behaviour (model_prepatch.py) on the "
                      "backward leg: the intermediate frame it builds carries the "
                      "default centre-of-the-Earth site instead of the input "
                      "frame's own, so the position is referred FROM the wrong "
                      "place and picks up the geocentric-vs-topocentric offset. "
                      "test_cirs_itrs_topo and the ITRS<->Observed round trips fail "
                      "— so the faithful real edit does NOT resolve.",
        "rationale": "offset_* is uninterpreted and same_frame_noop covers only "
                     "identical anchorings, so nothing equates "
                     "offset_*(w,0,0,0,esrc,T,etgt) with "
                     "offset_*(w,L,esrc,T,etgt) when L is not the centre. Source: "
                     "rot_to_equ's postcondition, which names L (and esrc) as the "
                     "re-referencing SOURCE — the G-DIFF clause for this modeled "
                     "change.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE — the orthogonality A-consumed axiom (site-indexed).
#
# The bundle carries axiom_check.py (the G-AX real-callee check). To make this
# battery's axiom lane self-standing rather than merely point at G-AX, the probe
# below re-derives the SAME soundness obligation in-container from the UNCHANGED
# callees the gold patch actually calls (rotation_matrix, matrix_transpose) and
# asserts the orthogonality axiom bwd_*(fwd_*(v,S),S) == v (i.e. M(S)^T(M(S) v)
# == v) on a boundary+fuzz grid of (lon,lat) and vectors — AND runs the CROSS-SITE
# control showing M(S')^T(M(S) v) misses v detectably, so the site carrier on
# fwd_*/bwd_* is observable and a site-free axiom would be unsound. It CALLS the
# real routines (never scrapes source), opens nothing on disk, imports only the
# real library, and exits 0 iff every observation satisfies the axiom.
#
# CONTAINMENT note: the model passes only finite integer triples to fwd_*/bwd_*/
# orthogonality (Requires nothing beyond `int`), and every finite real vector is
# in the matrix-action domain — so every caller-reachable input is covered; this
# is a soundness probe (the containment side is trivially satisfied and folded
# into the same sweep, which includes integer vectors).
# ---------------------------------------------------------------------------

_ORTHO_PROBE = r'''
import sys
import numpy as np
from astropy import units as u
from astropy.coordinates.matrix_utilities import rotation_matrix, matrix_transpose

NORTH_POLE = 90.0 * u.deg


def itrs_to_altaz_mat(lon, lat):
    minus_x = np.eye(3)
    minus_x[0][0] = -1.0
    return minus_x @ rotation_matrix(NORTH_POLE - lat, 'y') @ rotation_matrix(lon, 'z')


def itrs_to_hadec_mat(lon):
    minus_y = np.eye(3)
    minus_y[1][1] = -1.0
    return minus_y @ rotation_matrix(lon, 'z')


def altaz_to_hadec_mat(lat):
    z180 = np.eye(3)
    z180[0][0] = -1.0
    z180[1][1] = -1.0
    return z180 @ rotation_matrix(NORTH_POLE - lat, 'y')


def check_orthogonal(M, vectors, label):
    MT = matrix_transpose(M)
    prod = MT @ M
    if not np.allclose(prod, np.eye(3), atol=1e-12):
        print("VIOLATION %s: M^T M != I: %r" % (label, prod))
        return 1
    bad = 0
    for v in vectors:
        v = np.asarray(v, dtype=float)
        fwd = M @ v
        back = MT @ fwd
        scale = max(1.0, float(np.max(np.abs(v))))
        if not np.allclose(back, v, atol=1e-9 * scale, rtol=1e-12):
            print("VIOLATION %s: M^T(M v)=%r v=%r" % (label, back, v))
            bad += 1
    return bad


def cross_site_control():
    """CONTROL: the SITE carrier on fwd_*/bwd_* is observable. Applying the
    transpose built for a DIFFERENT site does not recover v, so the axiom's
    single-site scope is exactly right (a site-free version would be UNSOUND)."""
    v = np.array([6378137.0, 1234567.0, -2345678.0])
    pairs = [((0.0, 0.0), (77.0, -12.0)), ((-1.0, 52.0), (123.0, -33.0)),
             ((10.0, 80.0), (-179.9, -89.0)), ((45.0, 23.5), (-70.7, -30.2))]
    bad = 0
    n = 0
    for (lon_a, lat_a), (lon_b, lat_b) in pairs:
        Ma = itrs_to_altaz_mat(lon_a * u.deg, lat_a * u.deg)
        Mb = itrs_to_altaz_mat(lon_b * u.deg, lat_b * u.deg)
        mixed = matrix_transpose(Mb) @ (Ma @ v)
        resid = float(np.max(np.abs(mixed - v)))
        if resid <= 1.0:
            print("CONTROL FAILED cross-site (%g,%g)/(%g,%g): residual %g m "
                  "(the site carrier would be decorative)"
                  % (lon_a, lat_a, lon_b, lat_b, resid))
            bad += 1
        Ha = itrs_to_hadec_mat(lon_a * u.deg)
        Hb = itrs_to_hadec_mat(lon_b * u.deg)
        mixed = matrix_transpose(Hb) @ (Ha @ v)
        resid = float(np.max(np.abs(mixed - v)))
        if resid <= 1.0:
            print("CONTROL FAILED cross-site hadec lon %g/%g: residual %g m"
                  % (lon_a, lon_b, resid))
            bad += 1
        n += 2
    return bad, n


def main():
    rng = np.random.RandomState(13398)
    lons = [0.0, 90.0, 180.0, 270.0, 360.0, -1.0, -123.456, 45.0, 359.999]
    lats = [0.0, 90.0, -90.0, 52.0, -52.0, 89.999, -89.999, 23.5]
    lons += list(rng.uniform(-360.0, 360.0, size=30))
    lats += list(rng.uniform(-90.0, 90.0, size=30))
    # integer vectors (the model's exact-int carrier) + boundary + real fuzz
    vectors = [
        [1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0], [1, 1, 1],
        [-3, 7, -11], [1000000, -2000000, 3000000], [123, 456, 789],
    ]
    vectors += [list(rng.randint(-100000, 100000, size=3)) for _ in range(40)]
    vectors += [list(rng.uniform(-1e4, 1e4, size=3)) for _ in range(40)]
    bad = 0
    checks = 0
    for lon in lons:
        for lat in lats:
            lonq = lon * u.deg
            latq = lat * u.deg
            bad += check_orthogonal(itrs_to_altaz_mat(lonq, latq), vectors,
                                    "ITRS->AltAz lon=%g lat=%g" % (lon, lat))
            bad += check_orthogonal(itrs_to_hadec_mat(lonq), vectors,
                                    "ITRS->HADec lon=%g" % lon)
            bad += check_orthogonal(altaz_to_hadec_mat(latq), vectors,
                                    "AltAz->HADec lat=%g" % lat)
            checks += 3
    ctl_bad, ctl_n = cross_site_control()
    bad += ctl_bad
    if bad:
        print("orthogonality axiom VIOLATED or CONTROL FAILED: %d" % bad)
        sys.exit(1)
    print("orthogonality axiom OK over %d (lon,lat) configs x %d vectors, "
          "+%d cross-site controls" % (checks, len(vectors), ctl_n))
    sys.exit(0)


main()
'''


# AXIOM LANE — the prot_orthogonality + same_frame_noop A-consumed axioms.
#
# Validates the two facts the anchoring-honouring round-trip proofs consume, AND
# the controls that show each is exactly as weak as model.py states it:
#   (a) prot_orthogonality: P(e)^T(P(e) v) == v for the REAL Earth-orientation
#       matrices P(e) (cirs_to_itrs_mat / tete_to_itrs_mat), the unchanged
#       callees, AT ONE EPOCH — plus a CONTROL that the CROSS-epoch composition
#       is detectably not the identity, so the epoch carrier on prot_* is
#       observable and a quantified cross-epoch axiom would be unsound;
#   (b) same_frame_noop: offset(v, L,e, L,e) == 0 for the REAL same-kind
#       re-referencing transform — plus two CONTROLS, changing the target SITE
#       alone and the target EPOCH alone, each of which produces a detectably
#       nonzero offset, so neither carrier is decorative and the axiom does not
#       extend past the identical-anchoring instance.
# Imports only the repo package; calls the real routines; exits 0 iff all hold.
_PROT_FRAME_PROBE = r'''
import sys
import numpy as np
from astropy import units as u
from astropy.time import Time
from astropy.coordinates.matrix_utilities import matrix_transpose
from astropy.coordinates.builtin_frames.intermediate_rotation_transforms import (
    cirs_to_itrs_mat, tete_to_itrs_mat)
from astropy.coordinates import (EarthLocation, ICRS, CIRS, ITRS,
                                CartesianRepresentation)
from astropy.coordinates.angle_utilities import golden_spiral_grid

EPOCHS = ["J2000", "J2006", "J2010", "B1950", "2022-06-24T15:22:11"]


def check_prot():
    rng = np.random.RandomState(13398)
    vectors = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0], [1, 1, 1],
               [-3, 7, -11], [1000000, -2000000, 3000000]]
    vectors += [list(rng.randint(-100000, 100000, size=3)) for _ in range(30)]
    bad = 0
    n = 0
    for tname in EPOCHS:
        t = Time(tname)
        for matfn, label in [(cirs_to_itrs_mat, "CIRS<->ITRS"),
                             (tete_to_itrs_mat, "TETE<->ITRS")]:
            P = matfn(t)
            PT = matrix_transpose(P)
            if not np.allclose(PT @ P, np.eye(3), atol=1e-10):
                print("VIOLATION %s %s: P^T P != I" % (label, tname)); bad += 1
            for v in vectors:
                v = np.asarray(v, dtype=float)
                back = PT @ (P @ v)
                scale = max(1.0, float(np.max(np.abs(v))))
                if not np.allclose(back, v, atol=1e-9 * scale, rtol=1e-12):
                    print("VIOLATION %s %s: P^T(P v) != v" % (label, tname)); bad += 1
            n += 1
    # CONTROL: the epoch carrier is observable, so the single-epoch scope of the
    # axiom is exactly right (a cross-epoch version would be UNSOUND).
    v = np.array([6378137.0, 1234567.0, -2345678.0])
    ctl = 0
    for matfn, label in [(cirs_to_itrs_mat, "CIRS<->ITRS"),
                         (tete_to_itrs_mat, "TETE<->ITRS")]:
        for a, b in zip(EPOCHS, EPOCHS[1:]):
            mixed = matrix_transpose(matfn(Time(b))) @ (matfn(Time(a)) @ v)
            resid = float(np.max(np.abs(mixed - v)))
            if resid <= 1.0:
                print("CONTROL FAILED %s: cross-epoch %s/%s residual %g m "
                      "(epoch carrier would be decorative)" % (label, a, b, resid))
                bad += 1
            ctl += 1
    return bad, n, ctl


def offset(vec_m, loc_src, t_src, loc_tgt, t_tgt):
    rep = CartesianRepresentation(vec_m[0] * u.m, vec_m[1] * u.m, vec_m[2] * u.m)
    src = CIRS(rep, obstime=t_src, location=loc_src)
    tgt = src.transform_to(CIRS(obstime=t_tgt, location=loc_tgt))
    return (tgt.cartesian.get_xyz() - rep.get_xyz()).to_value(u.m)


def itrs_offset(vec_m, loc_src, t_src, loc_tgt, t_tgt):
    """The same re-referencing offset for the ITRS<->ITRS instance the direct
    Earth-fixed <-> observer-centred pair performs."""
    rep = CartesianRepresentation(vec_m[0] * u.m, vec_m[1] * u.m, vec_m[2] * u.m)
    src = ITRS(rep, obstime=t_src, location=loc_src)
    tgt = src.transform_to(ITRS(obstime=t_tgt, location=loc_tgt))
    return (tgt.cartesian.get_xyz() - rep.get_xyz()).to_value(u.m)


def check_frame():
    sites = [(0.0, 0.0, 0.0), (-1.0, 52.0, 10000.0), (-1.0, 52.0, 0.0),
             (123.0, -33.0, 500.0), (10.0, 80.0, 2000.0)]
    other = EarthLocation(lon=77.0 * u.deg, lat=-12.0 * u.deg, height=1500.0 * u.m)
    e = Time("J2000")
    e2 = Time("J2006")
    usph = golden_spiral_grid(50)
    dist = np.linspace(1.0, 1000.0, len(usph)) * u.au
    icrs = ICRS(ra=usph.lon, dec=usph.lat, distance=dist)
    bad = 0
    for lon, lat, height in sites:
        loc = EarthLocation(lon=lon * u.deg, lat=lat * u.deg, height=height * u.m)
        cirs_topo = icrs.transform_to(CIRS(obstime=e, location=loc))
        vec = cirs_topo.cartesian.get_xyz().to_value(u.m)
        noop = float(np.max(np.abs(offset(vec, loc, e, loc, e))))
        if noop > 1e-3:
            print("VIOLATION same_frame_noop lon=%g: %g m" % (lon, noop)); bad += 1
        site_ctl = float(np.max(np.abs(offset(vec, loc, e, other, e))))
        if site_ctl <= 1.0:
            print("CONTROL FAILED site carrier lon=%g: %g m" % (lon, site_ctl))
            bad += 1
        epoch_ctl = float(np.max(np.abs(offset(vec, loc, e, loc, e2))))
        if epoch_ctl <= 1.0:
            print("CONTROL FAILED epoch carrier lon=%g: %g m" % (lon, epoch_ctl))
            bad += 1
        itrs_topo = cirs_topo.transform_to(ITRS(obstime=e, location=loc))
        itrs_vec = itrs_topo.cartesian.get_xyz().to_value(u.m)
        # The ITRS<->ITRS instance: the axiom holds at identical anchoring, and
        # each carrier moves the position detectably on its own.
        i_noop = float(np.max(np.abs(itrs_offset(itrs_vec, loc, e, loc, e))))
        if i_noop > 1e-3:
            print("VIOLATION same_frame_noop (ITRS) lon=%g: %g m" % (lon, i_noop))
            bad += 1
        i_site = float(np.max(np.abs(itrs_offset(itrs_vec, loc, e, other, e))))
        if i_site <= 1.0:
            print("CONTROL FAILED ITRS site carrier lon=%g: %g m" % (lon, i_site))
            bad += 1
        i_epoch = float(np.max(np.abs(itrs_offset(itrs_vec, loc, e, loc, e2))))
        if i_epoch <= 1.0:
            print("CONTROL FAILED ITRS epoch carrier lon=%g: %g m" % (lon, i_epoch))
            bad += 1
        cirs_back = itrs_topo.transform_to(CIRS(obstime=e, location=loc))
        rt = float(np.max(np.abs((cirs_back.cartesian.xyz
                                  - cirs_topo.cartesian.xyz).to_value())))
        if rt > 1e-9:
            print("VIOLATION topo-roundtrip lon=%g: %g" % (lon, rt)); bad += 1
        itrs_geo = cirs_topo.transform_to(ITRS(obstime=e))
        forced = float(np.max(np.abs((itrs_topo.x - itrs_geo.x).to_value(u.m))))
        if not (lon == 0.0 and lat == 0.0 and height == 0.0) and forced <= 1.0:
            print("CONTROL FAILED constant-centre not detectable lon=%g: %g m"
                  % (lon, forced)); bad += 1
    return bad, len(sites)


def main():
    bad_p, np_, ctl = check_prot()
    bad_s, ns = check_frame()
    if bad_p or bad_s:
        print("prot_orthogonality / same_frame_noop VIOLATED or CONTROL FAILED")
        sys.exit(1)
    print("prot_orthogonality OK over %d configs (+%d cross-epoch controls); "
          "same_frame_noop OK over %d sites for the CIRS<->CIRS and the "
          "ITRS<->ITRS instance (+site/epoch/constant-centre controls on each)"
          % (np_, ctl, ns))
    sys.exit(0)


main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-orthogonality-soundness",
        "axiom": "orthogonality",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _ORTHO_PROBE,
        "rationale": "The ONLY fact the ITRS<->Observed round-trip proof consumes "
                     "about the unchanged orientation-matrix machinery is "
                     "bwd_*(fwd_*(v,S),S) == v (M(S)^T(M(S) v) == v) AT ONE SITE. "
                     "This probe builds the REAL ITRS->AltAz / ITRS->HADec / "
                     "AltAz->HADec matrices from the unchanged callees "
                     "rotation_matrix / matrix_transpose (the ones the gold patch "
                     "calls) over a boundary+fuzz (lon,lat) grid and asserts "
                     "M^T M == I and M^T(M v) == v on integer + real vectors, then "
                     "runs the CROSS-SITE control showing M(S')^T(M(S) v) misses v "
                     "by a detectable margin — so the site carrier is observable "
                     "and a site-free axiom would be UNSOUND. If the real callee "
                     "violated either, AXIOM-UNSOUND. Mirrors axiom_check.py / "
                     "G-AX, executed self-contained.",
    },
    {
        "id": "ax-prot-frame-soundness",
        "axiom": "prot_orthogonality + same_frame_noop",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROT_FRAME_PROBE,
        "rationale": "The facts the anchoring-honouring round-trip proofs consume, "
                     "with the controls that keep them as weak as model.py states. "
                     "prot_orthogonality: P(e)^T(P(e) v) == v for the REAL matrices "
                     "cirs_to_itrs_mat / tete_to_itrs_mat AT ONE epoch, plus a "
                     "CONTROL that the cross-epoch composition is detectably not "
                     "the identity (so the epoch carrier is observable and a "
                     "quantified cross-epoch axiom would be unsound). "
                     "same_frame_noop: the real same-kind re-referencing transform "
                     "introduces zero offset between frames of IDENTICAL anchoring "
                     "— checked for BOTH instances the model uses it at, "
                     "CIRS<->CIRS (the Earth-equatorial pair) and ITRS<->ITRS (the "
                     "direct observer-centred pair) — plus CONTROLS on each that "
                     "changing the target site alone, and the target epoch alone, "
                     "move the position detectably, so the axiom does not extend "
                     "into the differing-anchoring domain the postconditions pin. "
                     "Also confirms the topocentric round trip is the identity and "
                     "that referring to the centre of the Earth instead of the "
                     "frame's own site is detectably different. If any failed, "
                     "AXIOM-UNSOUND. Mirrors axiom_check.py / G-AX.",
    },
]
