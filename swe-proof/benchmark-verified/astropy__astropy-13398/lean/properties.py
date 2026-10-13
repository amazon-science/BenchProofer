# properties.py — G-PBT falsification battery for astropy__astropy-13398 (lean).
#
# NOT a Lean module; a record of adversarial cases the G-PBT runner executes and
# stamps a verdict on. Every case is a FULL Solution.lean variant that shares the
# FROZEN spec: edits live only inside an `-- impl-start` / `-- impl-end` region
# (which the spec view elides, so `same_spec` holds by construction) and, for the
# soundness/admissibility positives, inside `-- proof-start` / `-- proof-end`.
# Every `theorem correct_<name>` keeps a byte-identical STATEMENT; no case adds
# an `axiom`, a helper declaration, `sorry`, `admit`, or `native_decide`.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (what this spec actually protects)
# ---------------------------------------------------------------------------
# The bundle models TWO obligations — the Earth-fixed → observer-frame
# conversion and its inverse:
#
#   problem_spec_itrs_to_observed v srcLoc srcEpoch f result
#     * src   = if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch
#                 then carryTo v srcLoc srcEpoch f.location f.epoch
#                 else v                                            <-- CLAUSE
#     * lon,lat = the first two components of the site's geodetic triple <-- BINDER
#     * OUTER branch on (f.isAltAz = true ∨ f.pressure > 0)          <-- CLAUSE
#         then: aa = mvmul (altazMat lon lat) src
#               INNER branch on f.pressure > 0                       <-- CLAUSE
#                 then: ref = toApparent aa (bendCoefs …).1 (bendCoefs …).2
#                       result = if f.isAltAz = false
#                                then mvmul (poleTiltMat lat) ref  <-- CLAUSE
#                                else ref
#                 else: result = aa
#         else: result = mvmul (hadecMat lon) src
#
#   problem_spec_observed_to_itrs v f tgtLoc tgtEpoch result
#     * mirror image: de-refract (for the hour-angle flavour, AFTER first
#       rotating into the azimuth/altitude frame), rotate back by the TRANSPOSED
#       rotation, and then ALWAYS carry the reconstruction from the observed
#       (site, epoch) pair to the requested `(tgtLoc, tgtEpoch)` pair.
#
# KEY ARCHITECTURE OF THE SPEC (why the attacks land where they do):
#
#   * THE CARRIER IS `Float`, i.e. binary64, the very arithmetic the library
#     performs. This is load-bearing for the STRENGTH of the postconditions and
#     not only for their fidelity, and two of the rivals below exist to show it.
#     Over an exact-real carrier the two obligations admit rewrites that are
#     PROVABLE IDENTITIES there and catastrophic at working precision:
#     replacing `x` by `(x + 1e300) - 1e300` (a theorem over ℝ by
#     `add_sub_cancel_right`; total annihilation of every input below ~1e284 in
#     binary64), and shifting a rotation argument by 10⁹ whole turns (a theorem
#     over ℝ by periodicity; pure noise once the argument dwarfs the precision of
#     the angle). Such a rewrite is definitionally equal AS A FUNCTION to the gold
#     body over ℝ, and `correct_*` is a predicate on the implementation's VALUE
#     alone, so NO postcondition over ℝ can separate them — the carrier is the
#     only place the distinction can live. `Float` has no group structure and no
#     periodicity lemmas, so over it neither rewrite is an identity and both are
#     rejected: see `forward-cancels-huge-offset` and
#     `forward-shifts-rotation-by-whole-turns`.
#
#   * NOTHING ABOUT `Float` IS KERNEL-DECIDABLE. `Float.lt`, `Float.le`,
#     `Float.beq`, `Float.cos`, `Float.sin` and `Float.sqrt` are all external
#     primitives, so `decide`/`norm_num` cannot settle even `(1.0 : Float) < 2.0`,
#     let alone reduce a rotation at a concrete angle. Machine-checked while
#     porting this battery: `(0.0:Float) ≠ 1.0`, `¬((0.0:Float) > 0)`,
#     `(1.0:Float) < 2.0` and the `Float.toBits` route all FAIL under
#     `decide`/`simp`/`norm_num`. CONSEQUENCE: unlike the ℝ-carrier battery this
#     replaces, no witness here can be stated at literal inputs. EVERY witness
#     conditions on binders — one per branch it needs to steer, plus exactly one
#     numeric/structural disagreement hypothesis — which is the technique
#     `pbt_witness.consistency_probe` explicitly sanctions ("A witness may have to
#     CONDITION on the carrier instead of computing it … sound as long as the
#     hypotheses can jointly HOLD").
#
#   * SO SATISFIABILITY OF THE BINDERS IS THE THING TO AUDIT FIRST, and this
#     battery is built to make it cheap to audit. Two classes of binder appear:
#       - BRANCH binders (`f.isAltAz = true`, `¬ (f.pressure > 0)`,
#         `siteDiffers srcLoc f.location = true`, `epochDiffers … = false`).
#         Every one of these is a claim about an external primitive or a `Bool`
#         field, jointly satisfiable by construction — an azimuth/altitude frame
#         at zero pressure whose input is recorded against a different site is a
#         perfectly ordinary configuration, and it is exactly the configuration
#         the F2P tests drive.
#       - the DISAGREEMENT binder `hd`. In EVERY case below `hd` is rooted in an
#         `opaque` callee — `carryTo`, `geodetic`, `normSplit` (inside
#         `toApparent`/`toGeometric`), or `Float.cos`/`Float.sin` inside
#         the rotations — so no arithmetic the tactics can perform contradicts it.
#         That is a deliberate design change from the ℝ-carrier battery, whose
#         three refraction witnesses conditioned on TRANSPARENT arithmetic and one
#         of which shipped an UNSATISFIABLE binder (`0 ≠ 0`) that passed the
#         gate's own probe: the norm/unit split and the scalar-vector product are
#         now `normSplit`/`scaleVec`, unchanged library primitives modelled by
#         signature, so a refraction hypothesis is rooted in an uninterpreted
#         callee too and that whole failure mode is closed at the source rather
#         than patched witness by witness.
#     Each binder set was additionally checked against a probe STRICTLY STRONGER
#     than the gate's own `omega`/`simp_all`/`decide` one, namely
#     `example <the binders> : False := by first | simp_all [<defs>] |
#     (simp [<defs>] at *; omega) | omega | decide | norm_num [<defs>] at *`
#     with `<defs>` = `toApparent, toGeometric, mvmul, mmul, altazMat,
#     hadecMat, poleTiltMat, rotY, rotZ, flipX, flipY, flipXY, sinAltFloor,
#     cosAltFloor, epochDiffers, angToRad, poleAngle`, i.e. with the refraction and
#     rotation arithmetic actually unfolded rather than left behind a `def`.
#     Measured on all 15 reject cases: `False` is derivable from NONE of them
#     (15/15 builds fail), so no witness here proves its refutation from a
#     contradiction. And where an `hd` involves only the TRANSPARENT geometry, its
#     satisfiability is not argued for at all but ASSERTED AT IMPORT TIME, by
#     replaying the rival's and the spec's arithmetic in float64 at the F2P site
#     (see the assertions below `_mv`). Those assertions run every time the gate
#     loads this battery.
#
#   * Everything the behaviour COMPOSES is transparent: the three rotation
#     matrices are spelled out from elementary rotations and axis flips, the
#     matrix and matrix/vector products are explicit index-order sums, and the
#     branch structure is explicit. So the attackable content is (a) WHICH branch
#     fires on which input, (b) WHICH matrix is applied and in which orientation,
#     (c) WHICH geodetic slot feeds which angle, (d) WHETHER the refraction
#     correction is applied, (e) WHETHER the indirect carry happens, (f) BETWEEN
#     WHICH TWO (site, epoch) PAIRS it happens, and (g) whether the arithmetic is
#     the arithmetic the machine performs.
#
# Every reject witness below was BUILT twice by hand before shipping: it
# elaborates against its rival and FAILS against the frozen solution. A rival
# whose witness could not be seen to discriminate is not shipped. That pair of
# builds is necessary and NOT sufficient — a witness resting on contradictory
# binders passes both halves — which is why the third build (deriving `False`
# from the binders alone, with the arithmetic actually unfolded) is recorded
# above and is the one an auditor should re-run first.
#
# Audit note on WHY the gold-side failure is a refutation and not a syntactic
# accident. On this carrier the gold-side build fails because the witness's
# final `simp` cannot close `¬ (A = A)`: the frozen spec's equation at the
# witness's point is CLOSED by reflexivity, so the negation reduces to `False`
# and no hypothesis discharges it. That is the semantic refutation, not a tactic
# gap. Established by the flipped-claim forgery experiment: drop the `¬` and
# re-run both builds. Measured on the 14 cases that use the shared cascade, the
# exit codes INVERT exactly — the flipped claim elaborates on GOLD (14/14 exit 0)
# and fails on every RIVAL (14/14 exit 1) — so gold's exit tracks WHAT IS CLAIMED
# and therefore carries information about the claim rather than about the
# script's shape. The 15th case (`forward-zeroes-third-component`) is the one with
# a bespoke script: its first step strips the negation with `intro`, so the
# flipped script has nothing to introduce and fails to elaborate on both sides.
# That is a script-shape artefact of the forgery experiment and NOT a signal about
# that case, whose own four builds discriminate normally.
#
# THE TWO HOLES THIS BATTERY WAS REBUILT TO CLOSE (both were live findings):
#   1. SPEC-TOO-WEAK. A retained attack replaced the rotated argument by
#      `(x + 1e300) - 1e300` and VERIFIED against the ℝ-carrier spec while its
#      patch failed 3 of 4 F2P tests and 5 of 68 P2P tests. Closed by moving the
#      carrier to `Float`; pinned here by `forward-cancels-huge-offset` and its
#      whole-turn sibling.
#   2. SPEC-TOO-STRONG. The ℝ-carrier spec modelled the indirect carry as a
#      3-argument map of the SOURCE (site, epoch) pair only, so the inverse
#      obligation demanded a result determined by the observed frame alone, while
#      the real function's answer depends on the REQUESTED OUTPUT frame (measured:
#      the same observed position resolves to three different Earth-fixed vectors
#      for three different target sites, 5.5e6 m apart). Closed by giving
#      `carryTo` both endpoint pairs and making the trailing carry unconditional;
#      pinned here from both sides — `inverse-carries-to-the-source-pair` and
#      `forward-carries-to-the-source-pair` reject the old reading, and
#      `pos-inverse-result-tracks-the-target-pair` PROVES the repaired obligation
#      genuinely constrains the target pair (a statement that is unprovable under
#      the old shape, so the positive is a regression pin and not decoration).
#
# The FRAME-MUTATION class of the nagini sibling is VACUOUS here: Lean is
# referentially transparent, so there is no aliasing and no fractional permission
# to under-provision. Likewise the DIVERGENCE class: every `implementation_*` is
# a total Lean `def`, so a non-terminating rival cannot be written at all.
# Neither is a spec hole; both are carrier facts.
from pathlib import Path

INSTANCE = "astropy__astropy-13398"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()



# ---------------------------------------------------------------------------
# Machine-checked satisfiability of the ARITHMETIC binder families, in the very
# carrier the spec is stated over. Each `hd` below is a claim about binary64
# values, so where it involves only the transparent geometry it is CHECKED here
# rather than argued for in prose. Pure `math`, no third-party import, so this
# cannot break the battery on a host that lacks the instance's environment. The
# remaining `hd`s are rooted in `carryTo` and in the refraction primitives, which
# need the real library: those are measured by the bundled reproduction (three
# target sites, two target epochs) and probed by G-AX.
# ---------------------------------------------------------------------------
import math as _m


def _rot_z(t):
    c, s = _m.cos(t), _m.sin(t)
    return ((c, s, 0.0), (-s, c, 0.0), (0.0, 0.0, 1.0))


def _rot_y(t):
    c, s = _m.cos(t), _m.sin(t)
    return ((c, 0.0, -s), (0.0, 1.0, 0.0), (s, 0.0, c))


def _mm(A, B):
    return tuple(tuple(A[i][0] * B[0][j] + A[i][1] * B[1][j] + A[i][2] * B[2][j]
                       for j in range(3)) for i in range(3))


def _mv(A, v):
    return tuple(A[i][0] * v[0] + A[i][1] * v[1] + A[i][2] * v[2]
                 for i in range(3))


_FLIPX = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
_FLIPY = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))
_A2R = 0.017453292519943295
_POLE = 90.0
_LON_D, _LAT_D, _HGT_M = -155.5, 19.8, 4200.0    # the F2P observing site
_V = (1.0e6, 2.0e6, 3.0e6)                       # an Earth-scale position, metres

_ALTAZ = _mm(_mm(_FLIPX, _rot_y((_POLE - _LAT_D) * _A2R)), _rot_z(_LON_D * _A2R))
_ALTAZ_T = tuple(tuple(_ALTAZ[j][i] for j in range(3)) for i in range(3))
_HADEC = _mm(_FLIPY, _rot_z(_LON_D * _A2R))
_WRONGSLOT = _mm(_mm(_FLIPX, _rot_y((_POLE - _HGT_M) * _A2R)),
                 _rot_z(_LON_D * _A2R))
_TURNSHIFT = _mm(_mm(_FLIPX, _rot_y((_POLE - _LAT_D) * _A2R)),
                 _rot_z(_LON_D * _A2R + 1.0e9 * (2.0 * 3.141592653589793)))

# `forward-guard-ignores-observer-flavour` / `inverse-guard-...`: the two flavour
# rotations disagree, so the branch the guard picks is observable.
assert _mv(_HADEC, _V) != _mv(_ALTAZ, _V)
# `forward-reads-wrong-site-slot`: a height in metres is not a latitude in degrees.
assert _mv(_WRONGSLOT, _V) != _mv(_ALTAZ, _V)
# `forward-zeroes-third-component`: the discarded component is nonzero anyway.
assert _mv(_ALTAZ, _V)[2] != 0.0
# `forward-cancels-huge-offset`: at binary64 the cancellation ANNIHILATES an
# Earth-scale input exactly, so the binder holds in the strongest possible way --
# and this is the arithmetic fact no exact-real carrier can see.
assert all((x + 1e300) - 1e300 == 0.0 for x in _V)
assert _mv(_ALTAZ, tuple((x + 1e300) - 1e300 for x in _V)) != _mv(_ALTAZ, _V)
# `forward-shifts-rotation-by-whole-turns`: an identity over the reals; at
# binary64 it displaces the rotated position by ~0.75 m at this site, i.e. ~0.04
# arcsecond of direction, four orders of magnitude past the 1-microarcsecond
# tolerance the F2P tests assert.
assert max(abs(a - b) for a, b in
           zip(_mv(_TURNSHIFT, _V), _mv(_ALTAZ, _V))) > 1.0e-2
# `inverse-applies-rotation-not-transpose`: the rotation is not symmetric, so
# applying it untransposed is a different linear map.
assert _mv(_ALTAZ_T, _V) != _mv(_ALTAZ, _V)
assert _mv(_HADEC, _V) != _mv(_ALTAZ_T, _V)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Verbatim gold impl bodies and proof bodies. Each block lies ENTIRELY inside
# one region and is UNIQUE in _BASE, so `_swap` targets it unambiguously and the
# manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

# --- forward conversion: gold impl body (inside the first impl region) ---
_FWD_GOLD = """  let mut src := v
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
  return crepr"""

# --- inverse conversion: gold impl body (inside the second impl region) ---
_BWD_GOLD = """  let g := geodetic f.location
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
  return carryTo crepr f.location f.epoch tgtLoc tgtEpoch"""

# --- forward conversion: gold tactic body (inside the first proof region) ---
_FWD_PROOF_GOLD = """  intro v srcLoc srcEpoch f
  unfold implementation_itrs_to_observed problem_spec_itrs_to_observed
  simp only [Id.run, bind, pure]
  split_ifs <;> rfl"""

# --- inverse conversion: gold tactic body (inside the second proof region) ---
_BWD_PROOF_GOLD = """  intro v f tgtLoc tgtEpoch
  unfold implementation_observed_to_itrs problem_spec_observed_to_itrs
  simp only [Id.run, bind, pure]
  split_ifs <;> rfl"""

assert _BASE.count(_FWD_GOLD) == 1, "anchor drift: forward impl body"
assert _BASE.count(_BWD_GOLD) == 1, "anchor drift: inverse impl body"
assert _BASE.count(_FWD_PROOF_GOLD) == 1, "anchor drift: forward proof body"
assert _BASE.count(_BWD_PROOF_GOLD) == 1, "anchor drift: inverse proof body"


# ---------------------------------------------------------------------------
# The witness tactic cascade, shared by every reject case.
#
# Step 1 unfolds both sides; step 2 discharges the `Id.run` wrapper. Step 3
# resolves the branch conditions from the case's BRANCH binders and closes the
# goal with the DISAGREEMENT binder `hd` in either orientation. Three fallbacks
# because `Float`'s comparisons are external primitives, so which normal form
# `simp` reaches for a guard is not something to guess at; all three routes end
# at the same place, `hd` applied to the equation the spec demands.
# ---------------------------------------------------------------------------
_CASCADE_FWD = """  unfold problem_spec_itrs_to_observed implementation_itrs_to_observed
  simp only [Id.run, bind, pure]
  first
  | simp [{binders}, hd, Ne.symm hd]
  | (simp only [{binders}, Bool.true_or, Bool.or_true, Bool.false_or,
       Bool.or_false, Bool.false_eq_true, if_true, if_false, ite_true, ite_false,
       true_or, or_true, false_or, or_false]
     intro h
     first | exact hd h | exact hd h.symm)
  | (intro h; first | exact hd h | exact hd h.symm)"""

_CASCADE_BWD = _CASCADE_FWD.replace(
    "problem_spec_itrs_to_observed implementation_itrs_to_observed",
    "problem_spec_observed_to_itrs implementation_observed_to_itrs")


def _w_fwd(binders, hd, extra=""):
    """A forward-leg reject witness: BRANCH binders + one `hd`, then the cascade."""
    names = ", ".join(b.split()[0].lstrip("(") for b in binders)
    return ("\nexample (v : Vec3) (srcLoc : Location) (srcEpoch : Float)\n"
            "    (f : ObsFrame)\n"
            + "".join(f"    {b}\n" for b in binders)
            + f"    (hd : {hd}) :\n"
            "    ¬ problem_spec_itrs_to_observed v srcLoc srcEpoch f\n"
            "        (implementation_itrs_to_observed v srcLoc srcEpoch f) := by\n"
            + (extra if extra else _CASCADE_FWD.format(binders=names)) + "\n")


def _w_bwd(binders, hd, extra=""):
    """An inverse-leg reject witness: BRANCH binders + one `hd`, then the cascade."""
    names = ", ".join(b.split()[0].lstrip("(") for b in binders)
    return ("\nexample (v : Vec3) (f : ObsFrame) (tgtLoc : Location)\n"
            "    (tgtEpoch : Float)\n"
            + "".join(f"    {b}\n" for b in binders)
            + f"    (hd : {hd}) :\n"
            "    ¬ problem_spec_observed_to_itrs v f tgtLoc tgtEpoch\n"
            "        (implementation_observed_to_itrs v f tgtLoc tgtEpoch) := by\n"
            + (extra if extra else _CASCADE_BWD.format(binders=names)) + "\n")


# Shorthands for the spec's own sub-terms, written exactly as they appear after
# the `let`s are inlined, so `hd` matches the goal without further rewriting.
_LON = "(geodetic f.location).1"
_LAT = "(geodetic f.location).2.1"
_HGT = "(geodetic f.location).2.2"
_RC1 = "(bendCoefs f.pressure f.temperature f.relHumidity f.obswl).1"
_RC2 = "(bendCoefs f.pressure f.temperature f.relHumidity f.obswl).2"
_AA = f"mvmul (altazMat {_LON} {_LAT}) v"
_AAT = f"mvmul ((altazMat {_LON} {_LAT})ᵀ) v"
_HD = f"mvmul (hadecMat {_LON}) v"
_HDT = f"mvmul ((hadecMat {_LON})ᵀ) v"
_CARRY_FWD = "carryTo v srcLoc srcEpoch f.location f.epoch"
_TO_TGT = "f.location f.epoch tgtLoc tgtEpoch"


# ===========================================================================
# (1) SOUNDNESS POSITIVE — forward conversion, expression-shaped but CORRECT
# ===========================================================================
# Replace the accumulator (`let mut crepr` + successive assignments) with a
# nested expression carrying an EARLY RETURN out of each arm, and collapse the
# `let mut src` + guarded assignment into a single conditional binding. Same
# value on every input, same branch structure, same matrices in the same
# orientations — only the executable shape differs. The frozen tactic script
# (`split_ifs <;> rfl`) still discharges it unchanged, so no proof edit is
# needed. If a faithful correct re-shaping could NOT verify => SPEC-TOO-STRONG.
_FWD_POS = """  let src :=
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
      let bent := toApparent aa rc.1 rc.2
      if f.isAltAz = false then
        return mvmul (poleTiltMat lat) bent
      else
        return bent
    else
      return aa
  else
    return mvmul (hadecMat lon) src"""


# ===========================================================================
# (2) SOUNDNESS POSITIVE — inverse conversion, commuted guard + reproved
# ===========================================================================
# Two independent correct re-shapings at once: the outer disjunct is COMMUTED
# (`pressure > 0 ∨ isAltAz = true`) and the accumulator is replaced by a single
# `let earthFixed := …` expression. Disjunction is commutative, so the value is
# unchanged on every input. The commuted guard is NOT syntactically `rfl`-equal
# to the spec's, so the frozen tactic body no longer closes and the case
# REPROVES honestly inside the proof region, keeping the
# `theorem correct_observed_to_itrs` statement byte-identical. Must verify, else
# SPEC-TOO-STRONG on the inverse conversion.
_BWD_POS = """  let g := geodetic f.location
  let lon := g.1
  let lat := g.2.1
  let earthFixed : Vec3 :=
    if f.pressure > 0 ∨ f.isAltAz = true then
      let c1 :=
        if f.pressure > 0 then
          let c0 := if f.isAltAz = false then mvmul ((poleTiltMat lat)ᵀ) v else v
          let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
          toGeometric c0 rc.1 rc.2
        else v
      mvmul ((altazMat lon lat)ᵀ) c1
    else
      mvmul ((hadecMat lon)ᵀ) v
  return carryTo earthFixed f.location f.epoch tgtLoc tgtEpoch"""

_BWD_PROOF_POS = """  intro v f tgtLoc tgtEpoch
  unfold implementation_observed_to_itrs problem_spec_observed_to_itrs
  simp only [Id.run, bind, pure]
  split_ifs <;> first | rfl | (exfalso; tauto) | simp_all | tauto"""


# ===========================================================================
# (3) ADMISSIBILITY — the forward obligation's DEEPEST arm is satisfiable, by a
#     value named INDEPENDENTLY of the implementation
# ===========================================================================
# On a total carrier there is no precondition hypothesis to be over-strong (both
# frozen obligations are unconditional universals), so the analogue of
# PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE on a sub-domain it
# must admit. This case tests that directly on the deepest arm of the cascade —
# input recorded against a DIFFERENT site (so the carry fires), azimuth/altitude
# flavour, real atmosphere, no cross-rotation — which is the arm that carries the
# refraction sub-term and the carry at once, i.e. where an unsatisfiable
# obligation would surface first.
#
# The satisfying value is SPELLED OUT rather than taken from the implementation.
# That is what makes the step informative: it asserts that the arm's equation is
# exactly `result = toApparent (mvmul (altazMat lon lat) (carry …)) A B`, so
# a spec whose deepest arm demanded anything else would fail here even though it
# would still be trivially satisfiable by its own implementation. Control: the
# same `have` with a constant zero vector in place of that expression does NOT
# close.
#
# Nothing is assumed: no new declaration, no axiom, no `sorry`; the
# `theorem correct_itrs_to_observed` statement stays byte-identical and the
# frozen four-line tactic body follows the `have` verbatim.
_FWD_PROOF_ADMISS = """  have admissible :
      ∀ (w : Vec3) (L : Location) (t : Float) (g : ObsFrame),
        g.isAltAz = true → g.pressure > 0 → siteDiffers L g.location = true →
        problem_spec_itrs_to_observed w L t g
          (toApparent
            (mvmul (altazMat (geodetic g.location).1 (geodetic g.location).2.1)
              (carryTo w L t g.location g.epoch))
            (bendCoefs g.pressure g.temperature g.relHumidity g.obswl).1
            (bendCoefs g.pressure g.temperature g.relHumidity g.obswl).2) := by
    intro w L t g h1 h2 h3
    unfold problem_spec_itrs_to_observed
    first
    | simp [h1, h2, h3]
    | (simp only [h1, h2, h3, Bool.true_or, if_true, ite_true, true_or,
         Bool.true_eq_false, if_false, ite_false]
       rfl)
  intro v srcLoc srcEpoch f
  unfold implementation_itrs_to_observed problem_spec_itrs_to_observed
  simp only [Id.run, bind, pure]
  split_ifs <;> rfl"""


# ===========================================================================
# (4) SOUNDNESS POSITIVE — the inverse obligation TRACKS THE TARGET PAIR
# ===========================================================================
# The faithfulness pin for the repaired refinement rule. The statement proved
# here is: if ONE result satisfies the inverse obligation at target pair
# `(L₁,t₁)` and ANOTHER satisfies it at `(L₂,t₂)`, and the two results are
# equal, then the two carries agree. Equivalently: the obligation's demanded
# value is a function OF THE TARGET PAIR, so a result cannot satisfy it for two
# targets whose carries differ.
#
# That is exactly the property the previous (3-argument, source-pair-only)
# reading of the carry LACKED, and lacking it is what made the spec reject the
# real function: measured against the patched library, one observed AltAz
# position at a Hawaii site resolves to Earth-fixed vectors 5.5e6 m apart for
# target frames at the geocentre, at the same site, and at a South-African site,
# and to a completely different vector again one hour later. Under the old shape
# the inverse postcondition never mentioned the target, so a single result
# satisfied it for ALL targets and this `have` would not close. It closes here.
#
# Stated over the FULL `earthFixed` expression rather than under branch
# hypotheses, so it holds on every arm at once and needs no `Float` comparison
# to be decided. Frozen tactic body follows verbatim; statement byte-identical.
# NOT VACUOUS, by control: replace the conclusion's second target pair by a
# THIRD pair `(L₃,t₃)` that no hypothesis mentions and the `have` no longer
# closes (measured: build fails), so what it proves is specifically that the
# obligation pins the target pairs its hypotheses name.
_BWD_EF = """(if g.isAltAz = true ∨ g.pressure > 0 then
              mvmul ((altazMat (geodetic g.location).1 (geodetic g.location).2.1)ᵀ)
                (if g.pressure > 0 then
                    toGeometric
                      (if g.isAltAz = false then
                          mvmul ((poleTiltMat (geodetic g.location).2.1)ᵀ) w
                        else w)
                      (bendCoefs g.pressure g.temperature g.relHumidity g.obswl).1
                      (bendCoefs g.pressure g.temperature g.relHumidity g.obswl).2
                  else w)
            else mvmul ((hadecMat (geodetic g.location).1)ᵀ) w)"""

_BWD_PROOF_TARGET = """  have target_pair_observable :
      ∀ (w r₁ r₂ : Vec3) (g : ObsFrame) (L₁ L₂ : Location) (t₁ t₂ : Float),
        problem_spec_observed_to_itrs w g L₁ t₁ r₁ →
        problem_spec_observed_to_itrs w g L₂ t₂ r₂ →
        r₁ = r₂ →
        carryTo
            """ + _BWD_EF + """
            g.location g.epoch L₁ t₁
          = carryTo
            """ + _BWD_EF + """
            g.location g.epoch L₂ t₂ := by
    intro w r₁ r₂ g L₁ L₂ t₁ t₂ h₁ h₂ hr
    simp only [problem_spec_observed_to_itrs] at h₁ h₂
    rw [← h₁, ← h₂]
    exact hr
  intro v f tgtLoc tgtEpoch
  unfold implementation_observed_to_itrs problem_spec_observed_to_itrs
  simp only [Id.run, bind, pure]
  split_ifs <;> rfl"""


# ===========================================================================
# (5) UNIQUENESS — forward outer guard drops the observer-flavour disjunct
# ===========================================================================
_FWD_NOFLAVOUR = """  let mut src := v
  if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then
    src := carryTo v srcLoc srcEpoch f.location f.epoch
  let g := geodetic f.location
  let lon := g.1
  let lat := g.2.1
  let mut crepr : Vec3 := src
  if f.pressure > 0 then
    crepr := mvmul (altazMat lon lat) src
    let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl
    crepr := toApparent crepr rc.1 rc.2
    if f.isAltAz = false then
      crepr := mvmul (poleTiltMat lat) crepr
  else
    crepr := mvmul (hadecMat lon) src
  return crepr"""

_W_FWD_NOFLAVOUR = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = false)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    f"{_HD} ≠ {_AA}")


# ===========================================================================
# (6) UNIQUENESS — forward never performs the indirect carry
# ===========================================================================
_FWD_NOCARRY = _FWD_GOLD.replace(
    "  let mut src := v\n"
    "  if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then\n"
    "    src := carryTo v srcLoc srcEpoch f.location f.epoch\n",
    "  let src := v\n")

_W_FWD_NOCARRY = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = true)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    f"{_AA} ≠ mvmul (altazMat {_LON} {_LAT}) ({_CARRY_FWD})")


# ===========================================================================
# (6b) UNIQUENESS — forward carry guard keys on the SITE only, ignoring the epoch
# ===========================================================================
_FWD_GUARDNOEPOCH = _FWD_GOLD.replace(
    "  if siteDiffers srcLoc f.location || epochDiffers srcEpoch f.epoch then\n",
    "  if siteDiffers srcLoc f.location then\n")

_W_FWD_GUARDNOEPOCH = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = true)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    f"{_AA} ≠ mvmul (altazMat {_LON} {_LAT}) ({_CARRY_FWD})")


# ===========================================================================
# (7) UNIQUENESS — forward carries to the SOURCE pair instead of the frame's
# ===========================================================================
_FWD_CARRYSRC = _FWD_GOLD.replace(
    "    src := carryTo v srcLoc srcEpoch f.location f.epoch\n",
    "    src := carryTo v srcLoc srcEpoch srcLoc srcEpoch\n")

_W_FWD_CARRYSRC = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = true)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    f"mvmul (altazMat {_LON} {_LAT}) (carryTo v srcLoc srcEpoch srcLoc srcEpoch)"
    f" ≠ mvmul (altazMat {_LON} {_LAT}) ({_CARRY_FWD})")


# ===========================================================================
# (8) UNIQUENESS — forward reads the wrong slot of the site's geodetic triple
# ===========================================================================
_FWD_WRONGSLOT = _FWD_GOLD.replace("  let lat := g.2.1\n", "  let lat := g.2.2\n")

_W_FWD_WRONGSLOT = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = false)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    f"mvmul (altazMat {_LON} {_HGT}) v ≠ {_AA}")


# ===========================================================================
# (9) UNIQUENESS — forward applies the cross-rotation for BOTH flavours
# ===========================================================================
_FWD_ALWAYSCROSS = _FWD_GOLD.replace(
    "      if f.isAltAz = false then\n"
    "        crepr := mvmul (poleTiltMat lat) crepr\n",
    "      crepr := mvmul (poleTiltMat lat) crepr\n")

_REF = f"toApparent ({_AA}) {_RC1} {_RC2}"

_W_FWD_ALWAYSCROSS = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = false)",
     "(ha : f.isAltAz = true)",
     "(hp : f.pressure > 0)"],
    f"mvmul (poleTiltMat {_LAT}) ({_REF}) ≠ {_REF}")


# ===========================================================================
# (10) UNIQUENESS — forward never applies the refraction correction
# ===========================================================================
_FWD_NOREFRACT = _FWD_GOLD.replace(
    "      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl\n"
    "      crepr := toApparent crepr rc.1 rc.2\n"
    "      if f.isAltAz = false then\n",
    "      if f.isAltAz = false then\n")

_W_FWD_NOREFRACT = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = false)",
     "(ha : f.isAltAz = true)",
     "(hp : f.pressure > 0)"],
    f"{_AA} ≠ {_REF}")


# ===========================================================================
# (11) UNIQUENESS — forward gets two components right and zeroes the third
# ===========================================================================
_FWD_DROPCOMP = _FWD_GOLD.replace(
    "  return crepr",
    "  return (fun i => if i = 2 then 0 else crepr i)")

# Read off ONE component, so the case is a partial-domain refutation rather than
# a restatement of the whole-vector ones.
_W_FWD_DROPCOMP = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = false)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    f"({_AA}) 2 ≠ 0",
    extra="""  unfold problem_spec_itrs_to_observed implementation_itrs_to_observed
  simp only [Id.run, bind, pure]
  simp only [hc, he, ha, hp, Bool.or_self, Bool.false_or, Bool.or_false,
    Bool.false_eq_true, if_true, if_false, ite_true, ite_false, true_or]
  intro h
  have h2 := congrFun h 2
  first
  | exact hd (by simpa using h2.symm)
  | exact hd (by simpa using h2)
  | (simp only [if_pos] at h2; exact hd h2.symm)""")


# ===========================================================================
# (12) UNIQUENESS — forward cancels a huge added constant before rotating
#      (the retained SPEC-TOO-WEAK attack)
# ===========================================================================
_FWD_CANCEL = _FWD_GOLD.replace(
    "    crepr := mvmul (altazMat lon lat) src\n",
    "    crepr := mvmul (altazMat lon lat) (fun i => (src i + 1e300) - 1e300)\n")

_W_FWD_CANCEL = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = false)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    f"mvmul (altazMat {_LON} {_LAT}) (fun i => (v i + 1e300) - 1e300) ≠ {_AA}")


# ===========================================================================
# (13) UNIQUENESS — forward shifts the rotation argument by whole turns
# ===========================================================================
_FWD_TURNSHIFT = _FWD_GOLD.replace(
    "    crepr := mvmul (altazMat lon lat) src\n",
    "    crepr := mvmul (mmul (mmul flipX (rotY ((poleAngle - lat) * angToRad)))"
    " (rotZ (lon * angToRad + 1000000000.0 * (2.0 * 3.141592653589793)))) src\n")

_W_FWD_TURNSHIFT = _w_fwd(
    ["(hc : siteDiffers srcLoc f.location = false)",
     "(he : epochDiffers srcEpoch f.epoch = false)",
     "(ha : f.isAltAz = true)",
     "(hp : ¬ (f.pressure > 0))"],
    "mvmul (mmul (mmul flipX (rotY ((poleAngle - " + _LAT + ") * angToRad)))"
    " (rotZ (" + _LON + " * angToRad + 1000000000.0 * (2.0 * 3.141592653589793))))"
    f" v ≠ {_AA}")


# ===========================================================================
# (14) UNIQUENESS — inverse applies the rotation itself, not its transpose
# ===========================================================================
_BWD_NOTRANSPOSE = _BWD_GOLD.replace(
    "    crepr := mvmul ((altazMat lon lat)ᵀ) crepr\n",
    "    crepr := mvmul (altazMat lon lat) crepr\n")

_W_BWD_NOTRANSPOSE = _w_bwd(
    ["(ha : f.isAltAz = true)", "(hp : ¬ (f.pressure > 0))"],
    f"carryTo ({_AA}) {_TO_TGT} ≠ carryTo ({_AAT}) {_TO_TGT}")


# ===========================================================================
# (15) UNIQUENESS — inverse outer guard drops the observer-flavour disjunct
# ===========================================================================
_BWD_NOFLAVOUR = _BWD_GOLD.replace(
    "  if f.isAltAz = true ∨ f.pressure > 0 then\n",
    "  if f.pressure > 0 then\n")

_W_BWD_NOFLAVOUR = _w_bwd(
    ["(ha : f.isAltAz = true)", "(hp : ¬ (f.pressure > 0))"],
    f"carryTo ({_HDT}) {_TO_TGT} ≠ carryTo ({_AAT}) {_TO_TGT}")


# ===========================================================================
# (16) UNIQUENESS — inverse never performs the trailing carry
# ===========================================================================
_BWD_NOCARRY = _BWD_GOLD.replace(
    "  return carryTo crepr f.location f.epoch tgtLoc tgtEpoch",
    "  return crepr")

_W_BWD_NOCARRY = _w_bwd(
    ["(ha : f.isAltAz = true)", "(hp : ¬ (f.pressure > 0))"],
    f"{_AAT} ≠ carryTo ({_AAT}) {_TO_TGT}")


# ===========================================================================
# (17) UNIQUENESS — inverse carries to the SOURCE pair, not the requested one
#      (the retained SPEC-TOO-STRONG finding, from the other side)
# ===========================================================================
_BWD_CARRYSRC = _BWD_GOLD.replace(
    "  return carryTo crepr f.location f.epoch tgtLoc tgtEpoch",
    "  return carryTo crepr f.location f.epoch f.location f.epoch")

_W_BWD_CARRYSRC = _w_bwd(
    ["(ha : f.isAltAz = true)", "(hp : ¬ (f.pressure > 0))"],
    f"carryTo ({_AAT}) f.location f.epoch f.location f.epoch"
    f" ≠ carryTo ({_AAT}) {_TO_TGT}")


# ===========================================================================
# (18) UNIQUENESS — inverse never removes the refraction correction
# ===========================================================================
_BWD_NODEREFRACT = _BWD_GOLD.replace(
    "      let rc := bendCoefs f.pressure f.temperature f.relHumidity f.obswl\n"
    "      crepr := toGeometric crepr rc.1 rc.2\n",
    "")

_W_BWD_NODEREFRACT = _w_bwd(
    ["(ha : f.isAltAz = true)", "(hp : f.pressure > 0)"],
    f"carryTo ({_AAT}) {_TO_TGT}"
    f" ≠ carryTo (mvmul ((altazMat {_LON} {_LAT})ᵀ)"
    f" (toGeometric v {_RC1} {_RC2})) {_TO_TGT}")


# Sanity: every rival really is a textual change to its anchor.
for _name, _old, _new in (
        ("fwd-noflavour", _FWD_GOLD, _FWD_NOFLAVOUR),
        ("fwd-nocarry", _FWD_GOLD, _FWD_NOCARRY),
        ("fwd-guardnoepoch", _FWD_GOLD, _FWD_GUARDNOEPOCH),
        ("fwd-carrysrc", _FWD_GOLD, _FWD_CARRYSRC),
        ("fwd-wrongslot", _FWD_GOLD, _FWD_WRONGSLOT),
        ("fwd-alwayscross", _FWD_GOLD, _FWD_ALWAYSCROSS),
        ("fwd-norefract", _FWD_GOLD, _FWD_NOREFRACT),
        ("fwd-dropcomp", _FWD_GOLD, _FWD_DROPCOMP),
        ("fwd-cancel", _FWD_GOLD, _FWD_CANCEL),
        ("fwd-turnshift", _FWD_GOLD, _FWD_TURNSHIFT),
        ("fwd-pos", _FWD_GOLD, _FWD_POS),
        ("bwd-notranspose", _BWD_GOLD, _BWD_NOTRANSPOSE),
        ("bwd-noflavour", _BWD_GOLD, _BWD_NOFLAVOUR),
        ("bwd-nocarry", _BWD_GOLD, _BWD_NOCARRY),
        ("bwd-carrysrc", _BWD_GOLD, _BWD_CARRYSRC),
        ("bwd-noderefract", _BWD_GOLD, _BWD_NODEREFRACT),
        ("bwd-pos", _BWD_GOLD, _BWD_POS),
        ("fwd-proof-admiss", _FWD_PROOF_GOLD, _FWD_PROOF_ADMISS),
        ("bwd-proof-target", _BWD_PROOF_GOLD, _BWD_PROOF_TARGET)):
    if _old == _new:
        raise AssertionError(f"variant {_name} is a no-op (anchor drift)")


def _bwd_pos_module():
    m = _swap(_BASE, _BWD_GOLD, _BWD_POS)
    return _swap(m, _BWD_PROOF_GOLD, _BWD_PROOF_POS)


SPEC_TESTS = [
    # ---------------- soundness positives ----------------
    {
        "id": "pos-forward-expression-shaped",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_POS),
        "rationale": "Structurally different but CORRECT re-shaping of the "
                     "Earth-fixed -> observer-frame conversion: the accumulator "
                     "and its successive assignments are replaced by a nested "
                     "expression with an early return out of each arm, and the "
                     "guarded carry assignment is collapsed into a single "
                     "conditional binding. Every branch condition, every matrix "
                     "and every matrix orientation is unchanged, so the value "
                     "agrees with the frozen impl on every input and each arm "
                     "still matches its postcondition arm syntactically — the "
                     "frozen tactic script discharges it unedited. A faithful "
                     "correct re-shaping that could NOT verify would mean "
                     "SPEC-TOO-STRONG on the forward obligation.",
    },
    {
        "id": "pos-inverse-commuted-guard-reproved",
        "kind": "soundness",
        "expect": "verify",
        "module": _bwd_pos_module(),
        "rationale": "Structurally different but CORRECT re-shaping of the "
                     "inverse conversion, combining two independent changes: the "
                     "outer guard's disjunction is COMMUTED, and the accumulator "
                     "is replaced by one bound expression. Disjunction is "
                     "commutative so the value is unchanged on every input, but "
                     "the commuted guard is no longer syntactically reflexive "
                     "against the postcondition's, so this case REPROVES honestly "
                     "inside the proof region with the "
                     "`theorem correct_observed_to_itrs` statement "
                     "byte-identical — no new lemma, no weakened obligation. This "
                     "is the case that shows the spec admits a genuinely "
                     "re-derived proof and not merely a syntactic clone of the "
                     "frozen impl; if it could not verify, SPEC-TOO-STRONG on the "
                     "inverse obligation.",
    },
    {
        "id": "pos-inverse-result-tracks-the-target-pair",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _BWD_PROOF_GOLD, _BWD_PROOF_TARGET),
        "rationale": "THE FAITHFULNESS PIN for the repaired refinement rule, and "
                     "a regression pin against the SPEC-TOO-STRONG finding this "
                     "bundle was rebuilt to close. It PROVES, inside the proof "
                     "region and before the frozen tactic body runs verbatim, "
                     "that the inverse obligation's demanded value is a function "
                     "OF THE REQUESTED TARGET PAIR: if one result satisfies the "
                     "obligation at target `(L1,t1)` and another satisfies it at "
                     "`(L2,t2)` and the two results are equal, then the two "
                     "carries agree. Under the previous 3-argument reading of the "
                     "carry — where the inverse postcondition mentioned only the "
                     "OBSERVED site and epoch — a single result satisfied the "
                     "obligation for EVERY target and this statement was "
                     "unprovable; that is precisely why the old spec rejected the "
                     "real function, whose answer for one observed AltAz position "
                     "at a Hawaii site differs by 5.5e6 m between a geocentric "
                     "target frame and a co-located one, and differs again "
                     "entirely at a target epoch one hour later (measured against "
                     "the patch-applied library, deterministic across "
                     "repetitions). The statement is written over the FULL "
                     "earthFixed expression rather than under branch hypotheses, "
                     "so it holds on all three arms at once and needs no `Float` "
                     "comparison to be decided. Statement of the frozen theorem "
                     "byte-identical; no new declaration, no axiom, no `sorry`. "
                     "Not vacuous, by control: conclude about a THIRD target pair "
                     "that no hypothesis mentions and the `have` no longer closes "
                     "(measured), so what it establishes is specifically that the "
                     "obligation pins the target pairs its hypotheses name. If "
                     "this could not verify, the spec would once again be unable "
                     "to express the behaviour the library actually has.",
    },

    # ---------------- admissibility ----------------
    {
        "id": "admiss-forward-deepest-arm-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _FWD_PROOF_GOLD, _FWD_PROOF_ADMISS),
        "rationale": "The PRECOND-TOO-STRONG lane. Both frozen obligations are "
                     "unconditional universals, so there is no precondition "
                     "hypothesis to be over-strong; on a total carrier the "
                     "analogue is the obligation being UNSATISFIABLE on a "
                     "sub-domain it must admit, and this case tests that on the "
                     "DEEPEST arm of the forward cascade — input recorded against "
                     "a different site so the indirect carry fires, "
                     "azimuth/altitude flavour, real atmosphere, cross-rotation "
                     "not taken. That arm carries the refraction sub-term and the "
                     "carry at once, so an unsatisfiable obligation surfaces there "
                     "first. Crucially the satisfying value is SPELLED OUT, "
                     "independently of the implementation: the `have` asserts that "
                     "the arm's equation is exactly `result = toApparent "
                     "(mvmul (altazMat lon lat) (carry ...)) A B`, so a spec "
                     "whose deepest arm demanded anything else would fail here "
                     "even though it would remain trivially satisfiable by its own "
                     "implementation. That is what makes the step informative "
                     "rather than a tautology, and it is checked by control: the "
                     "same `have` with a constant zero vector in place of that "
                     "expression does NOT close. Nothing is assumed — no new "
                     "declaration, no axiom, no `sorry` — and the frozen tactic "
                     "body follows verbatim. Note the branch conditions are passed "
                     "as HYPOTHESES rather than instantiated at literals because "
                     "`Float`'s comparisons are external primitives that no "
                     "kernel-level tactic can decide.",
    },

    # ---------------- uniqueness rivals: forward obligation ----------------
    {
        "id": "forward-guard-ignores-observer-flavour",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_NOFLAVOUR),
        "refinement": "A faithful real patch whose outer dispatch keyed only on "
                      "the site having a real atmosphere would send an "
                      "azimuth/altitude output frame with no atmosphere down the "
                      "hour-angle arm, rotating the position by the wrong matrix "
                      "and so reporting a completely different pair of observed "
                      "angles. The F2P tests exercise exactly that configuration: "
                      "test_itrs_straight_overhead transforms into an "
                      "atmosphere-free azimuth/altitude frame and asserts the "
                      "altitude is a quarter turn to 1 microarcsecond, and "
                      "test_itrs_topo_to_altaz_with_refraction's no-atmosphere leg "
                      "compares the same frame against the established route to "
                      "0.1 milliarcsecond. Both compare against the "
                      "azimuth/altitude answer, so the hour-angle matrix's output "
                      "fails them outright — the refined patch does NOT resolve.",
        "rationale": "Attacks the OUTER branch clause of the forward "
                     "postcondition, whose condition is the disjunction of the "
                     "observer flavour and the atmosphere test. Dropping the "
                     "flavour disjunct changes which arm fires precisely when the "
                     "frame is the azimuth/altitude flavour and the pressure is "
                     "not positive, so the result is pinned to the hour-angle "
                     "rotation where the spec pins it to the azimuth/altitude one. "
                     "Witness binders: the two carry-guard bits are set to `false` "
                     "so the carry does not fire, the flavour bit to `true` and "
                     "the atmosphere test to negative, which is the sub-domain "
                     "where the two arms disagree; the disagreement binder is that "
                     "the two rotations applied to the same vector differ, which "
                     "is rooted in `geodetic` and in `Float.cos`/`Float.sin` and "
                     "so cannot be contradicted by any arithmetic the tactics "
                     "perform. Satisfiable in the obvious way — the two matrices "
                     "differ at essentially every site.",
        "witness": _W_FWD_NOFLAVOUR,
    },
    {
        "id": "forward-omits-the-indirect-carry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_NOCARRY),
        "refinement": "A faithful real patch that rotated the raw input instead "
                      "of first bringing it across to the output frame's site and "
                      "epoch would apply the observer rotation to a position "
                      "referred to a different viewpoint and time. That is the "
                      "geocentric-versus-topocentric discrepancy the issue is "
                      "about: test_cirs_itrs_topo drives the transform at two "
                      "different epochs and asserts that the matching-epoch route "
                      "round-trips exactly while the mismatched-epoch one does NOT "
                      "agree, so it pins the behaviour on both sides of this "
                      "branch and a rival that never carries collapses the two "
                      "cases together — the refined patch does NOT resolve.",
        "rationale": "Attacks the `src` sub-term of the forward postcondition: "
                     "the spec pins the rotated argument to the CARRIED position "
                     "whenever the input's site or epoch differs from the frame's, "
                     "and this rival always rotates the raw input. `carryTo` is an "
                     "unchanged library pipeline modelled by signature, so the "
                     "witness CONDITIONS on it rather than computing it — one "
                     "disagreement binder about one uninterpreted term, on the "
                     "sub-domain where the carried and raw vectors differ. The "
                     "branch binder sets the site-comparison bit to `true`, which "
                     "is what makes the carry fire; that is exactly the "
                     "configuration the F2P tests use (an ITRS position recorded "
                     "at the geocentre transformed into a frame at a real site).",
        "witness": _W_FWD_NOCARRY,
    },
    {
        "id": "forward-guard-ignores-the-epoch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_GUARDNOEPOCH),
        "refinement": "A faithful real patch whose pre-transform guard compared "
                      "only the SITES would skip the carry whenever a position "
                      "recorded at the observing site is handed to a frame at the "
                      "same site but a DIFFERENT epoch, so it would rotate a "
                      "position referred to the wrong instant and lose the Earth's "
                      "rotation between the two. test_cirs_itrs_topo is built "
                      "around exactly that distinction: it holds the site fixed "
                      "and drives two epochs, asserting that the matching-epoch "
                      "route round-trips exactly AND that the mismatched-epoch "
                      "route does NOT agree. A site-only guard makes the two "
                      "epochs behave identically, so it cannot satisfy both "
                      "assertions — the refined patch does NOT resolve.",
        "rationale": "Attacks the SECOND DISJUNCT of the forward carry guard, "
                     "which `forward-omits-the-indirect-carry` cannot reach: that "
                     "rival never carries at all, and its witness fires on the "
                     "site half of the guard, so a spec that tracked only the site "
                     "would still reject it. This case fires with the sites AGREEING "
                     "and only the epochs differing, so it is the only case in the "
                     "battery that establishes the epoch comparison is load-bearing. "
                     "Same disagreement binder shape as its sibling (the carried and "
                     "raw vectors differ, rooted in the uninterpreted carry), "
                     "different branch binders — which is the point.",
        "witness": _W_FWD_GUARDNOEPOCH,
    },
    {
        "id": "forward-carries-to-the-source-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_CARRYSRC),
        "refinement": "A faithful real patch that performed the indirect "
                      "pre-transform but targeted the position's OWN site and "
                      "epoch rather than the observing frame's would leave the "
                      "position exactly where it was — the carry would be a no-op "
                      "— so it degenerates into the previous defect while looking "
                      "like it does the work. Any two-endpoint carry that ignores "
                      "the requested endpoint also fails test_cirs_itrs_topo, "
                      "which asserts that the matching-epoch route round-trips "
                      "exactly AND that the mismatched-epoch route does not agree; "
                      "a rival that always carries to the source pair treats both "
                      "epochs identically. The refined patch does NOT resolve.",
        "rationale": "Attacks WHICH TWO ENDPOINTS the forward carry runs between, "
                     "a clause the previous battery could not express at all "
                     "because the earlier spec modelled the carry as a "
                     "3-argument map of the source pair alone. That reading is "
                     "the SPEC-TOO-STRONG defect this bundle was rebuilt to "
                     "close, so pinning it from the rival side matters: a spec "
                     "that admitted this rival would be back to constraining the "
                     "carry by its source only. `carryTo` is modelled by "
                     "signature, so the witness conditions on it; the "
                     "disagreement binder says the carry to the source pair and "
                     "the carry to the frame's pair differ, which is exactly the "
                     "claim G-AX probes against the real routine (the carry is the "
                     "identity when the pairs agree and depends on the target "
                     "otherwise). Satisfiable: the measured library moves the "
                     "vector by 5.5e6 m between two such targets.",
        "witness": _W_FWD_CARRYSRC,
    },
    {
        "id": "forward-reads-wrong-site-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_WRONGSLOT),
        "refinement": "A faithful real patch that fed the site's height into the "
                      "meridian rotation in place of its second geodetic angle "
                      "would build the observer rotation from a length rather than "
                      "an angle, so every observed direction it reports is rotated "
                      "by an essentially arbitrary amount. "
                      "test_itrs_straight_overhead pins the altitude of an "
                      "overhead object to a quarter turn within 1 microarcsecond "
                      "at a site 10 km up, and its hour-angle leg pins the "
                      "declination to the site's own latitude — both fail as soon "
                      "as the wrong quantity drives the rotation, so the refined "
                      "patch does NOT resolve.",
        "rationale": "Attacks the `lat` sub-term shared by the forward "
                     "postcondition's azimuth/altitude rotation and its "
                     "cross-rotation: the spec pins it to the SECOND component of "
                     "the site's geodetic triple, this rival reads the THIRD. This "
                     "is the only rival that moves the geodetic triple's third "
                     "slot, so it is what separates the two angle binders from the "
                     "length. The disagreement binder is rooted in `geodetic`, an "
                     "unchanged library inversion modelled by signature, so it "
                     "cannot be contradicted; satisfiable because a site's height "
                     "in metres and its latitude in degrees are unrelated numbers "
                     "(the F2P sites sit at 4200 m and 10 km).",
        "witness": _W_FWD_WRONGSLOT,
    },
    {
        "id": "forward-cross-rotates-both-flavours",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_ALWAYSCROSS),
        "refinement": "A faithful real patch that applied the further constant "
                      "rotation to both observer flavours would rotate an "
                      "azimuth/altitude result that must not be rotated, reporting "
                      "the hour-angle frame's axes for an azimuth/altitude request "
                      "whenever the site has a real atmosphere. That is exactly "
                      "the configuration test_itrs_topo_to_altaz_with_refraction "
                      "exercises: it builds an azimuth/altitude frame at 1000 hPa "
                      "and 50% humidity and asserts both reported angles match the "
                      "established route to 0.1 milliarcsecond, then round-trips "
                      "back and asserts all three Cartesian components. A spurious "
                      "extra rotation breaks both — the refined patch does NOT "
                      "resolve.",
        "rationale": "Attacks the INNERMOST clause of the forward postcondition, "
                     "which applies the constant cross-rotation iff the frame is "
                     "NOT the azimuth/altitude flavour. This rival drops that "
                     "guard, so on the atmosphere-bearing azimuth/altitude "
                     "sub-domain the spec pins the result to the refracted vector "
                     "itself while the rival returns it rotated. It is one of the "
                     "two cases that reach the positive side of the atmosphere "
                     "binder on the forward leg. The disagreement binder is rooted "
                     "in `toApparent`, whose body opens with the unchanged "
                     "norm/unit-split primitive and closes with the unchanged "
                     "scalar-vector product — both modelled by signature — so "
                     "unlike the previous battery's refraction witnesses it rests "
                     "on an uninterpreted term and no arithmetic can contradict "
                     "it. (That is the structural fix for the unsatisfiable `0 "
                     "!= 0` binder the previous port shipped here.)",
        "witness": _W_FWD_ALWAYSCROSS,
    },
    {
        "id": "forward-never-applies-refraction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_NOREFRACT),
        "refinement": "A faithful real patch that took the atmosphere arm but "
                      "returned the unbent vector would report the geometric "
                      "direction where the observed one is asked for, i.e. it "
                      "would behave as though every site were airless. "
                      "test_itrs_topo_to_altaz_with_refraction builds an "
                      "azimuth/altitude frame at 1000 hPa and 50% humidity and "
                      "requires both reported angles to match the established "
                      "route to 0.1 milliarcsecond, while separately requiring the "
                      "atmosphere-free frame to match its own airless reference — "
                      "so an impl that returns the airless answer for both cannot "
                      "satisfy the pair, and its hour-angle twin fails likewise. "
                      "The refined patch does NOT resolve.",
        "rationale": "Attacks the refraction sub-term of the forward "
                     "postcondition's atmosphere arm, which pins the result to "
                     "`toApparent` applied to the rotated vector before any "
                     "cross-rotation, i.e. WHETHER the correction is applied at "
                     "all rather than merely which flavour gets the extra "
                     "rotation. The disagreement binder says the rotated vector "
                     "and its bent image differ; it is rooted in the unchanged "
                     "norm/unit-split and scalar-vector primitives that "
                     "`toApparent` calls, so no arithmetic contradicts it, and "
                     "it is satisfiable at any above-horizon direction with a real "
                     "atmosphere (the correction is tens of arcseconds at 1000 hPa "
                     "and grows without bound towards the horizon, which is why "
                     "the model carries a horizon guard at all).",
        "witness": _W_FWD_NOREFRACT,
    },
    {
        "id": "forward-zeroes-third-component",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_DROPCOMP),
        "refinement": "A faithful real patch that assembled the observed position "
                      "from only two of its three Cartesian components, leaving "
                      "the last one zero, would report a direction lying in a "
                      "coordinate plane no matter where the object actually is — "
                      "the reported elevation would be pinned to the horizon for "
                      "every input. test_itrs_straight_overhead requires the "
                      "altitude of an overhead object to be a quarter turn within "
                      "1 microarcsecond, which is exactly the configuration whose "
                      "answer is carried by the component this rival discards, and "
                      "its hour-angle leg pins the declination to the site's "
                      "latitude in the same way. Both round-trip assertions in "
                      "test_itrs_topo_to_altaz_with_refraction compare all three "
                      "Cartesian components against the original, so a zeroed "
                      "component fails them outright — the refined patch does NOT "
                      "resolve.",
        "rationale": "Attacks the POINTWISE force of both forward postcondition "
                     "arms: the spec is an equation between two `Vec3` functions, "
                     "so it constrains every component, and this rival satisfies "
                     "it in components 0 and 1 while returning zero for component "
                     "2. It covers the PARTIAL-DOMAIN class the nagini sibling "
                     "carries (there the selector was an explicit argument; here "
                     "the three components play that role). Every other rival in "
                     "the battery is wrong in a whole-vector way — a wrong matrix, "
                     "a wrong argument, a missing stage — so nothing else "
                     "establishes that a defect confined to ONE component is "
                     "caught. The witness reads the refutation off component 2 "
                     "SPECIFICALLY, which is what makes it a partial-domain "
                     "witness rather than a restatement of the whole-vector ones; "
                     "its disagreement binder says that component of the rotated "
                     "vector is nonzero, which is rooted in `geodetic` and the "
                     "elementary trigonometric primitives and holds at every site "
                     "except a measure-zero set.",
        "witness": _W_FWD_DROPCOMP,
    },
    {
        "id": "forward-cancels-huge-offset",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_CANCEL),
        "refinement": "This is a RETAINED ATTACK that VERIFIED against the "
                      "previous exact-real spec while its patch failed 3 of the 4 "
                      "F2P tests (test_itrs_topo_to_altaz_with_refraction, "
                      "test_itrs_topo_to_hadec_with_refraction, "
                      "test_itrs_straight_overhead) and 5 of 68 P2P tests "
                      "(test_gcrs_altaz_bothroutes and two more) — a direct "
                      "violation of `verify => correct`. A faithful real patch that "
                      "added 1e300 to each component of the position and then "
                      "subtracted it again before rotating destroys every input: "
                      "at binary64 precision `(x + 1e300) - 1e300` is exactly zero "
                      "for every |x| below about 1e284, so an Earth-scale position "
                      "in metres is annihilated and the transform returns the "
                      "origin. Every F2P assertion about a reported angle or a "
                      "Cartesian component fails. The refined patch does NOT "
                      "resolve.",
        "rationale": "THE case this bundle was rebuilt around, and the reason the "
                     "carrier is `Float`. Over an exact-real carrier this rival's "
                     "implementation is provably equal AS A FUNCTION to the frozen "
                     "one (`add_sub_cancel_right`), and `correct_*` is a predicate "
                     "on the implementation's VALUE only, so NO postcondition over "
                     "the reals — however detailed — can separate them; the "
                     "previous spec's failure here was not a missing clause but a "
                     "carrier that cannot express the distinction. `Float` has no "
                     "additive group structure and no cancellation lemma, so "
                     "`(x + 1e300) - 1e300` is not a normal form of `x`, the "
                     "frozen `rfl` no longer closes the rewritten proof, and the "
                     "rival is rejected. The witness's disagreement binder says "
                     "the rotation of the cancelled vector differs from the "
                     "rotation of the original; nothing in Mathlib can rewrite it "
                     "away on this carrier (checked: the consistency probe does "
                     "not derive `False`), and it is satisfiable in the strongest "
                     "possible sense — it holds at every input of Earth-like "
                     "magnitude, where the cancelled vector is exactly zero.",
        "witness": _W_FWD_CANCEL,
    },
    {
        "id": "forward-shifts-rotation-by-whole-turns",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FWD_GOLD, _FWD_TURNSHIFT),
        "refinement": "The second retained attack of the same family: a faithful "
                      "real patch that added a billion whole turns to the "
                      "longitude before building the rotation about the vertical. "
                      "Mathematically the identity; at binary64 precision the "
                      "argument is about 6.3e9 radians, whose ulp is roughly 2e-6 "
                      "radian, so the computed sine and cosine miss the intended "
                      "ones by around 2e-7. Measured in float64 at the F2P site "
                      "(and asserted at import time below): that displaces the "
                      "rotated position by 0.75 m, i.e. about 0.04 arcsecond of "
                      "direction — four orders of magnitude past the "
                      "1-microarcsecond tolerance test_itrs_straight_overhead "
                      "asserts, and past the 0.1-milliarcsecond tolerances of both "
                      "refraction tests. The refined patch does NOT resolve.",
        "rationale": "The companion to the cancellation rival, attacking the "
                     "ARGUMENT of the rotation rather than the vector: over the "
                     "reals it is an identity by periodicity of the elementary "
                     "trigonometric functions, so again no exact-real "
                     "postcondition could reject it, while `Float.cos`/`Float.sin` "
                     "are external primitives with no periodicity lemma and the "
                     "shifted matrix is simply a different term. Shipping both "
                     "members of the family matters because they exploit DIFFERENT "
                     "real-carrier identities — additive cancellation and "
                     "periodicity — so a carrier or a clause that closed one "
                     "without closing the other would still be weak. The "
                     "disagreement binder is the corresponding matrix/vector "
                     "inequality, rooted in the trigonometric primitives and hence "
                     "uncontradictable inside Lean; its satisfiability is not left "
                     "to prose, it is ASSERTED at import time by replaying the "
                     "shifted and unshifted rotations in float64 at the F2P site, "
                     "where they differ by 0.75 m.",
        "witness": _W_FWD_TURNSHIFT,
    },

    # ---------------- uniqueness rivals: inverse obligation ----------------
    {
        "id": "inverse-applies-rotation-not-transpose",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_NOTRANSPOSE),
        "refinement": "A faithful real patch whose inverse conversion applied the "
                      "observer rotation itself rather than its transpose would "
                      "not undo the forward rotation: composing the two applies "
                      "the rotation twice instead of returning the original "
                      "position, so the round trip is not the identity. "
                      "test_itrs_topo_to_altaz_with_refraction and its hour-angle "
                      "twin both round-trip back to the Earth-fixed frame and "
                      "assert all three Cartesian components against the original, "
                      "and test_cirs_itrs_topo asserts an exact round trip of both "
                      "spherical coordinates — all fail under a doubled rotation, "
                      "so the refined patch does NOT resolve.",
        "rationale": "Attacks the load-bearing ORIENTATION of the inverse "
                     "postcondition, which pins the reconstruction to the "
                     "TRANSPOSED azimuth/altitude rotation applied to the observed "
                     "vector. The rotation is not symmetric, so applying it "
                     "untransposed is a different linear map. The disagreement "
                     "binder is stated at the outermost term — the carry of the "
                     "two candidate reconstructions — because the trailing carry "
                     "is unconditional on this leg, so the refutation has to live "
                     "outside it; `carryTo` is modelled by signature and the "
                     "binder therefore cannot be contradicted. Satisfiable "
                     "because the carry is injective in practice (it is the "
                     "identity when the endpoints agree) and the two "
                     "reconstructions differ at essentially every site.",
        "witness": _W_BWD_NOTRANSPOSE,
    },
    {
        "id": "inverse-guard-ignores-observer-flavour",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_NOFLAVOUR),
        "refinement": "The mirror of the forward guard defect on the inverse leg: "
                      "a faithful real patch keying the outer dispatch only on the "
                      "atmosphere would rotate an atmosphere-free azimuth/altitude "
                      "vector back by the hour-angle matrix's transpose, "
                      "reconstructing a different Earth-fixed position. "
                      "test_itrs_topo_to_altaz_with_refraction's round trip goes "
                      "back from an atmosphere-free azimuth/altitude frame and "
                      "asserts all three Cartesian components against the "
                      "original, so the wrong inverse matrix fails it — the "
                      "refined patch does NOT resolve. Note this is a DIFFERENT "
                      "real defect from the forward-side twin: the two legs are "
                      "independently editable and a patch could get one right and "
                      "the other wrong, which is why both are attacked.",
        "rationale": "Attacks the OUTER branch clause of the inverse "
                     "postcondition. Dropping the flavour disjunct changes which "
                     "arm fires exactly when the frame is the azimuth/altitude "
                     "flavour with non-positive pressure, so the reconstruction is "
                     "pinned to the hour-angle rotation's transpose where the spec "
                     "pins it to the azimuth/altitude one's. Disagreement binder "
                     "at the outermost carry, for the same reason as the transpose "
                     "rival, and rooted in the same uninterpreted callee.",
        "witness": _W_BWD_NOFLAVOUR,
    },
    {
        "id": "inverse-omits-the-trailing-carry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_NOCARRY),
        "refinement": "A faithful real patch returning the reconstructed position "
                      "without bringing it to the requested output frame would "
                      "hand back a position referred to the OBSERVING site and "
                      "epoch rather than the caller's. test_cirs_itrs_topo asserts "
                      "that the matching-epoch route round-trips exactly AND that "
                      "the mismatched-epoch route does not agree, which pins the "
                      "carry on both sides; a rival that never applies it cannot "
                      "satisfy both assertions at once — the refined patch does "
                      "NOT resolve.",
        "rationale": "Attacks the outermost clause of the inverse postcondition, "
                     "which pins the result to the carry of the reconstruction and "
                     "does so UNCONDITIONALLY — there is no guard in front of the "
                     "trailing transform in the real function, and modelling one "
                     "there is half of what made the previous spec too strong. "
                     "This rival is what discriminates the presence of the carry "
                     "at all; its sibling below discriminates its ENDPOINTS. "
                     "Disagreement binder: the reconstruction and its carry "
                     "differ, rooted in the uninterpreted carry. Satisfiable "
                     "whenever the requested pair differs from the observed one, "
                     "which is the normal case (the F2P tests request a geocentric "
                     "ITRS frame from an observation at a real site).",
        "witness": _W_BWD_NOCARRY,
    },
    {
        "id": "inverse-carries-to-the-source-pair",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_CARRYSRC),
        "refinement": "A faithful real patch that ended its inverse conversion by "
                      "carrying the reconstruction to the OBSERVED site and epoch "
                      "— i.e. to where it already was — instead of to the "
                      "requested output frame would return a position referred to "
                      "the wrong frame, differing from the correct answer by the "
                      "whole geocentric-versus-topocentric offset plus the "
                      "aberration difference. Measured against the patch-applied "
                      "library: one observed AltAz position at a Hawaii site "
                      "resolves to Earth-fixed vectors 5.5e6 m apart for a "
                      "geocentric target frame and a co-located one. "
                      "test_cirs_itrs_topo's exact round trip and both Cartesian "
                      "round-trip assertions fail. The refined patch does NOT "
                      "resolve.",
        "rationale": "THE regression pin for the SPEC-TOO-STRONG finding, from "
                     "the rival side. The previous spec modelled the trailing "
                     "carry as a 3-argument map of the OBSERVED pair alone, which "
                     "is exactly this rival's behaviour — so the previous spec did "
                     "not merely fail to reject it, the previous spec DEMANDED it, "
                     "and that is why it rejected the real function. Rejecting it "
                     "here is what shows the repair went in the right direction "
                     "rather than merely loosening the obligation: the spec now "
                     "pins the carry's TARGET endpoints as well as its source, and "
                     "`pos-inverse-result-tracks-the-target-pair` proves the same "
                     "fact from the positive side. Disagreement binder: the carry "
                     "to the observed pair and the carry to the requested pair "
                     "differ — precisely the claim G-AX probes against the real "
                     "pipeline, and the claim the bundled reproduction measures at "
                     "three target sites and two target epochs.",
        "witness": _W_BWD_CARRYSRC,
    },
    {
        "id": "inverse-never-removes-refraction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _BWD_GOLD, _BWD_NODEREFRACT),
        "refinement": "The mirror of the forward refraction defect on the inverse "
                      "leg: a faithful real patch that rotated the still-bent "
                      "observed vector back would hand the caller an Earth-fixed "
                      "position that retains a correction the inverse is supposed "
                      "to undo, so going out to an atmosphere-bearing frame and "
                      "back would not return the original position. "
                      "test_itrs_topo_to_altaz_with_refraction returns from the "
                      "atmosphere-bearing frame and then requires the re-derived "
                      "airless angles to agree with the independently computed "
                      "ones to 0.1 milliarcsecond, and its hour-angle twin does "
                      "the same — both fail when the correction is never removed. "
                      "The refined patch does NOT resolve. Note this is a "
                      "DIFFERENT real defect from the forward-side twin: the two "
                      "legs are independently editable.",
        "rationale": "Attacks the de-refraction sub-term of the inverse "
                     "postcondition's atmosphere arm, and is the only case that "
                     "reaches the positive side of the atmosphere binder on this "
                     "leg. `toGeometric` is spelled out, but its body opens "
                     "with the unchanged norm/unit-split primitive and closes with "
                     "the unchanged spherical and scalar-vector primitives — all "
                     "modelled by signature — so the disagreement binder is rooted "
                     "in uninterpreted callees and no arithmetic can contradict "
                     "it. That is a deliberate improvement on the previous "
                     "battery, whose refraction witnesses conditioned on fully "
                     "transparent arithmetic and one of which was found to rest on "
                     "a contradiction.",
        "witness": _W_BWD_NODEREFRACT,
    },
]
