# properties.py — PBT falsification battery for scikit-learn__scikit-learn-13779 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region surgery — it edits ONLY the impl region
# (and, where a reshaped impl needs it, the proof body), so the frozen spec
# (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and the `theorem correct_checkWeightSupport` STATEMENT is
# preserved verbatim. No case introduces sorry/admit/native_decide/axiom or any
# new theorem/lemma; every reshaped impl is REPROVEN inside the proof region.
#
# PORT NOTE — carrier NARROWING vs the nagini sibling.
# The nagini battery models the same validation over a carrier of per-slot
# integer STATUS TAGS (`roster : List[int]`, tags 0/1/2) plus a `@ContractOnly`
# boolean probe axiom whose precondition excludes the empty-slot tag. Two
# structural consequences for this port:
#
#   * The tag→behavior indirection is GONE. Here a slot is
#     `(String × Option Bool)`: `none` is an empty slot, `some accepts` a present
#     component carrying its own weight-acceptance flag directly. So nagini's
#     "consulting the probe outside its domain" rejection has no counterpart as a
#     PRECONDITION violation — `Option Bool` makes the empty slot a distinct
#     CONSTRUCTOR rather than an out-of-domain tag value. The same adversarial
#     content survives as a value-level rival (`weak-reject-on-empty-slot`):
#     an impl that treats an empty slot as a rejection is refuted by the
#     postcondition itself, which is strictly stronger evidence than a
#     precondition gap.
#   * The carrier GAINS a component NAME. The frozen spec pins the rejection
#     message, so it pins WHICH component is identified — an axis nagini's
#     integer roster cannot express at all. Attacked here by two rivals with no
#     nagini counterpart (`weak-names-leading-component`,
#     `weak-drops-final-slot`).
#
# The carrier is fully COMPUTABLE (no `opaque` callee, no axiom: the acceptance
# flag is a grounded input), so every rival is refutable at a concrete literal
# roster and no witness needs to condition on the carrier. `Id.run do` +
# `forIn` does not reduce under `decide` alone (the `Decidable` instance gets
# stuck on the unreduced monadic block), so each witness reduces the loop and the
# reference walk together with
# `simp [Id.run, pure, Id.instMonad, validateRoster, errMsg]`.
#
# DEFENDED SURFACE — one obligation, one clause, one input binder:
#   theorem correct_checkWeightSupport :
#     ∀ estimators, problem_spec_checkWeightSupport estimators
#                     (implementation_checkWeightSupport estimators)
#   and problem_spec is the single master clause
#       result = validateRoster estimators
#   which is TOTAL on the carrier: it pins the outcome at every roster, leaving
#   no output component free. Read as independent behavioral axes, that one
#   clause constrains:
#     (C1) an empty slot contributes NOTHING — it neither rejects nor halts the
#          walk;
#     (C2) a present accepting component contributes nothing;
#     (C3) a present non-accepting component REJECTS the roster;
#     (C4) the rejection IDENTIFIES that component by name;
#     (C5) it is the FIRST such component that is identified;
#     (C6) a roster with no non-accepting present component is ACCEPTED;
#     (C7) EVERY slot is visited (no slot is skipped or dropped);
#     (C8) an EXHAUSTED roster is accepted — the base case the walk bottoms out
#          in, observable only at the zero-length roster.
#   Each of C1–C8 is attacked by at least one rival below.
#
# AUDIT NOTE 2 (SECOND independent adversarial re-derivation, a later pass).
# The battery below already carried the two repairs described in AUDIT NOTE 1. A
# fresh audit re-derived every case from scratch and found THREE further defects,
# all of them in prose or coverage rather than in any case's recorded outcome —
# again invisible to the gate, which only re-confirms behavior-as-declared.
#   (3) `weak-names-last-declining`'s `refinement` claimed "every listed test that
#       supplies weights to a roster containing more than one declining component
#       asserts the raised message VERBATIM ... the assertion FAILS and the
#       instance does not resolve". No such listed test exists. Projected onto this
#       carrier, the listed weight-supplying rosters carry declining-component
#       counts 0/0/0/0/1/0 — never more than one — and the rival was built against
#       all five and AGREES with the reference walk on every one (exit 0 both
#       sides). So its faithful patch resolves the instance and the claimed
#       verify-does-not-resolve break is impossible. This is the exact defect class
#       "a `refinement` claiming a near-miss the manifest never demonstrates", and
#       it was introduced by the previous audit's own repair. Fixed by restating
#       the refinement at its true, narrower scope (spec strength on C5, explicitly
#       NOT a resolve break) rather than by dropping the case, since C5 is real
#       modeled behavior.
#   (4) The DIVERGENCE class was recorded as VACUOUS on the grounds that a
#       diverging impl "cannot be written at all" on a total carrier. Measured and
#       false: a `partial def` self-call passes `variant_scope` (`partial` is not a
#       banned assumption token). The class is expressible but not shippable, for a
#       reason that also had to be measured rather than assumed — see the reworked
#       OMITTED entry below. Re-recorded as a KNOWN SPEC HOLE, which is what an
#       expressible-but-unwitnessable class is; "vacuous" would have claimed the
#       battery is complete.
#   (5) Length-0 was an UNPROBED structural point of the sole input binder: the
#       seven ported witnesses use rosters of length 1, 2 and 3 only, so nothing
#       pinned the walk's base case — the `[] => Except.ok ()` arm every accepting
#       outcome bottoms out in. Closed by `weak-rejects-empty-roster`.
# Also re-measured and left alone: attack A (all 11 case statements AND all three
# frozen spec regions byte-identical to Solution.lean); the FORGERY test on all
# seven ported witnesses (see the witness note below); five NEW wrong impls, all
# rejected with discriminating witnesses; and three NEW correct reshapes
# (`find?`-based, `filterMap`-based, `foldr`-based), all of which VERIFY — so the
# spec is neither too weak nor too strong on the axes probed.
#
# AUDIT NOTE 1 (the earlier pass).
# Two defects were found and repaired here; both were invisible to the gate,
# which only re-confirms that each case behaved as DECLARED.
#   (1) C5 was CLAIMED above but never demonstrated. Every reject witness as
#       ported probed a roster with AT MOST ONE non-accepting component (six
#       rosters, `some false` count 1/1/0/1/1/0), and on such a roster "first
#       declining" and "last declining" coincide — so no shipped rival could
#       distinguish them and the C5 line was a coverage claim the manifest did
#       not back. Closed by `weak-names-last-declining` below, refuted at a
#       roster carrying TWO declining components, the shape that separates them.
#   (2) The ADMISSIBILITY lane was recorded as structurally omitted on the
#       grounds that "manufacturing one would need a new example/theorem that
#       `variant_scope` forbids". Re-measured: that is false. `variant_scope`
#       forbids a new `theorem`/`lemma`, but an anonymous `example` inside the
#       impl region is admissible (`variant_problems` returns []) and elaborates
#       (exit 0). Restored as `admiss-f2p-shaped-roster`.
# Also measured and left alone: the three positives are NOT definitionally equal
# to the frozen impl (`example : implS1 = implGold := rfl` and the S2 analogue
# both fail with a type mismatch on `rfl`), so none of them is a trivial restate
# of gold — they are genuine reshapes that the frozen script happens to still
# close, and `pos-structural-recursion` needs and supplies its own induction.
#
# INPUT-BINDER COVERAGE. The spec predicate has exactly ONE input binder,
# `estimators`. It is a LIST, so "varying the binder" means varying its
# structure, and the EIGHT reject witnesses probe eight DISTINCT rosters that
# differ in length (0, 1, 2 and 3 slots), in empty-vs-present slot composition, in
# whether a non-accepting component exists, in the POSITION of the non-accepting
# component (absent / final / interior), and in HOW MANY non-accepting components
# there are (0, 1, and — added by the audit, since C5 is unobservable without it
# — 2). No two rivals share a witness: each is refuted at the roster that
# isolates the axis it mishandles, so no rival's rationale claims a sub-domain
# the manifest never demonstrates.
#
# NEAR-MISS HONESTY. Two of the eight rivals (`weak-names-last-declining` and
# `weak-rejects-empty-roster`) agree with the modeled walk at EVERY roster the
# listed tests reach, so their faithful patches would pass the listed suite. Their
# `refinement` fields say so explicitly and rest on spec STRENGTH over modeled
# behavior instead of on F2P/P2P resolution. That is a weaker claim than the other
# six carry, and it is stated as such rather than dressed up as a resolve break —
# an audit found the first of them asserting a resolve break its own witness
# roster shape proves impossible.
#
# OMITTED nagini cases and why (see `assessment` in the payload too):
#   * FRAME / permission-mutation (`weak-frame-mutation`) is VACUOUS on this
#     backend. Nagini's rival overwrites the half-permission input list so the
#     fold becomes trivially true; Lean is referentially transparent — no
#     aliasing, no fractional permission — so there is no input to overwrite and
#     no counterpart rival to author. Not fabricated.
#   * DIVERGENCE / non-termination is a KNOWN HOLE here, NOT a vacuous class.
#     The port originally recorded it as vacuous on the grounds that
#     "`implementation_*` is a total Lean `def`, so a diverging implementation
#     cannot be written at all". The audit MEASURED that and it is false:
#       partial def implementation_checkWeightSupport
#           (estimators : List (String × Option Bool)) : Except String Unit :=
#         implementation_checkWeightSupport estimators
#     is accepted by `variant_scope` (`variant_problems` returns [] — `partial` is
#     not one of the banned assumption tokens) and the surgery produces a file the
#     verifier accepts as far as the obligation. So the class IS expressible.
#     It is nonetheless NOT SHIPPABLE, for a reason that was also measured rather
#     than assumed: a `partial def` is compiled to an OPAQUE constant with no
#     equation lemmas, so nothing can reduce it, and both halves of the witness
#     contract fail together.
#       - A literal witness cannot even be stated against the rival: the build
#         fails with `Tactic 'unfold' failed to unfold
#         'implementation_checkWeightSupport'` (exit 1 on the RIVAL side), which is
#         `witness-unproven` — the gate would fail the case.
#       - Conditioning on the carrier instead makes it WORSE, not better: the
#         hypothesis-form witness elaborates against the rival AND against the
#         frozen solution (both exit 0), i.e. `witness-vacuous`. It asserts
#         something true of any impl, because the hypothesis it assumes is exactly
#         what it needs to conclude.
#     So the obligation does reject the diverging rival (the frozen proof cannot
#     close over an opaque constant), but no witness can attribute that rejection
#     to the SPEC rather than to the missing equation lemmas — which is precisely
#     the tactic-mismatch confound the witness requirement exists to catch. The
#     honest disposition is therefore a KNOWN SPEC HOLE (the master clause does not
#     constrain a non-reducing impl in any way a witness can exhibit), not a
#     vacuous class: a vacuous class would claim the battery is complete, and it
#     is not. Recorded so the gap is a visible queue entry rather than a silent
#     omission.
#   * The nagini ADMISSIBILITY positive is PORTED, not omitted (audit repair 2).
#     Nagini's version asserts inside the impl region that an F2P-shaped input
#     satisfies the precondition. This obligation has no precondition binder
#     (`∀ estimators, …`), so there is no Requires to establish — but the
#     non-vacuity content survives: the ported case asserts inside the impl
#     region what the modeled walk COMPUTES at an F2P-shaped roster (an empty
#     slot beside an accepting component ⇒ acceptance). An earlier draft of this
#     port recorded the case as inexpressible because `variant_scope` forbids a
#     new theorem; that reason was wrong — the ban is on `theorem`/`lemma`, and
#     an anonymous `example` in the impl region is in scope and elaborates.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job, and this bundle
#     ships no consumed axiom (the acceptance observation enters as a grounded
#     input flag, not as an `opaque` callee — mapping.md records G-AX as a skip).
#
# DROPPED rivals that DO discriminate but cannot ground a refinement argument —
# reported rather than shipped; see `assessment`.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13779"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each lies ENTIRELY inside the region it edits and is unique in
# the frozen file: `_GOLD_IMPL` is the whole impl `def` (impl region), and
# `_GOLD_PROOF` the whole tactic body (proof region). Swapping the whole block
# mechanically guarantees the spec view is untouched.
# ---------------------------------------------------------------------------

_HEAD = """def implementation_checkWeightSupport
    (estimators : List (String × Option Bool)) : Except String Unit"""

_GOLD_IMPL = _HEAD + """ := Id.run do
  for slot in estimators do
    let (name, step) := slot
    match step with
    | none => pure ()
    | some accepts =>
      if accepts then
        pure ()
      else
        return Except.error (errMsg name)
  return Except.ok ()"""

_GOLD_PROOF = """  intro estimators
  unfold problem_spec_checkWeightSupport implementation_checkWeightSupport
  induction estimators with
  | nil => rfl
  | cons a as ih =>
    simp only [List.forIn_cons, Id.run, bind]
    obtain ⟨name, step⟩ := a
    cases step with
    | none => simpa only [validateRoster] using ih
    | some accepts =>
      cases accepts with
      | false => simp only [validateRoster]; rfl
      | true => simpa only [validateRoster] using ih"""

assert _BASE.count(_GOLD_IMPL) == 1, "impl anchor drift"
assert _BASE.count(_GOLD_PROOF) == 1, "proof anchor drift"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally different, behaviorally
# IDENTICAL, each REPROVEN honestly for its own shape.
# ===========================================================================

# S1 — negate the acceptance test and swap the branch arms: `if !accepts then
# reject else continue` instead of `if accepts then continue else reject`. Same
# outcome at every slot. The frozen induction still closes it (the `false`/`true`
# cases just arrive through the mirrored arm), so the proof body is unchanged.
_S1_IMPL = _HEAD + """ := Id.run do
  for slot in estimators do
    let (name, step) := slot
    match step with
    | none => pure ()
    | some accepts =>
      if !accepts then
        return Except.error (errMsg name)
      else
        pure ()
  return Except.ok ()"""

# S2 — collapse the nested `match` + `if` into a SINGLE pattern match that names
# only the rejecting shape, with a catch-all for everything the walk passes over:
# `| some false => reject | _ => continue`. This fuses C1 and C2 into one arm,
# which is the shape a faithful author who noticed both are no-ops would write.
_S2_IMPL = _HEAD + """ := Id.run do
  for slot in estimators do
    let (name, step) := slot
    match step with
    | some false => return Except.error (errMsg name)
    | _ => pure ()
  return Except.ok ()"""

# S3 — abandon the accumulator loop entirely for STRUCTURAL RECURSION over the
# roster, mirroring the reference walk's own shape. The strongest positive
# control available here: it shares no control-flow idiom with the frozen impl
# (no `Id.run`, no `forIn`, no early `return`), so it cannot pass by reusing the
# frozen tactic script — it needs its own induction, supplied below.
_S3_IMPL = _HEAD + """ :=
  match estimators with
  | [] => Except.ok ()
  | (_, none) :: rest => implementation_checkWeightSupport rest
  | (_, some true) :: rest => implementation_checkWeightSupport rest
  | (name, some false) :: _ => Except.error (errMsg name)"""

# S4 (AUDIT REPAIR 2 — restores the dropped nagini admissibility lane) — the
# frozen impl, plus an anonymous `example` in the impl region recording what the
# modeled walk COMPUTES at an F2P-shaped roster. Anonymous `example`s are
# admissible to `variant_scope` (only new `theorem`/`lemma` names are banned) and
# the obligation statement is untouched, so this is a positive that pins the
# behavior at a concrete point rather than restating the master clause.
_S4_IMPL = _GOLD_IMPL + """

/-- Non-vacuity of the modeled behavior at an F2P-shaped roster: one EMPTY slot
alongside a present component that accepts per-sample weights. The walk passes
over the empty slot and ACCEPTS, so the obligation says something substantive at
that shape — and something the walk must actually compute — rather than holding
trivially. -/
example : implementation_checkWeightSupport [("lr", none), ("rf", some true)]
    = Except.ok () := by
  simp [implementation_checkWeightSupport, Id.run, pure, Id.instMonad]"""

_S3_PROOF = """  intro estimators
  induction estimators with
  | nil => rfl
  | cons a as ih =>
    obtain ⟨name, step⟩ := a
    cases step with
    | none =>
      unfold problem_spec_checkWeightSupport at *
      simpa only [implementation_checkWeightSupport, validateRoster] using ih
    | some accepts =>
      cases accepts with
      | false => rfl
      | true =>
        unfold problem_spec_checkWeightSupport at *
        simpa only [implementation_checkWeightSupport, validateRoster] using ih"""


# ===========================================================================
# UNIQUENESS rivals. Each mishandles exactly one behavioral axis of the master
# clause, and is refuted at the roster that isolates that axis.
# ===========================================================================

# R1 (ports nagini `weak-prepatch-probe-on-absent`) — treat an EMPTY slot as a
# rejection naming it, instead of passing over it. This is the discriminating
# divergence the instance is built around, re-expressed on this carrier: nagini
# rejects it via the probe axiom's precondition, whereas here the postcondition
# itself refutes it. Attacks C1.
_R1_IMPL = _swap(_GOLD_IMPL, "| none => pure ()",
                 "| none => return Except.error (errMsg name)")

# R2 (ports nagini `weak-never-raise` / `weak-treat2-as-accept`) — never reject:
# visit every slot and accept unconditionally, so a present non-accepting
# component is passed over like an empty one. Attacks C3.
_R2_IMPL = _HEAD + """ := Id.run do
  for slot in estimators do
    let (_, step) := slot
    match step with
    | none => pure ()
    | some _ => pure ()
  return Except.ok ()"""

# R3 — INVERT the acceptance test: reject on a present ACCEPTING component and
# pass over a non-accepting one. Attacks C2 and C3 jointly (the sense of the
# per-component test), and is refuted on a roster with no non-accepting
# component at all, where every other rival agrees with the reference walk.
_R3_IMPL = _HEAD + """ := Id.run do
  for slot in estimators do
    let (name, step) := slot
    match step with
    | none => pure ()
    | some accepts =>
      if accepts then
        return Except.error (errMsg name)
      else
        pure ()
  return Except.ok ()"""

# R4 — reject at the right TIME but identify the wrong component: the message
# names the roster's LEADING slot rather than the component that actually
# declined. Accept/reject is indistinguishable from the reference walk; only the
# identity carried in the rejection differs. Attacks C4. No nagini counterpart —
# its integer-tag carrier has no component name to get wrong.
_R4_IMPL = _HEAD + """ := Id.run do
  let lead := match estimators with
              | [] => ""
              | (n, _) :: _ => n
  for slot in estimators do
    let (_, step) := slot
    match step with
    | none => pure ()
    | some accepts =>
      if accepts then
        pure ()
      else
        return Except.error (errMsg lead)
  return Except.ok ()"""

# R5 (ports nagini `weak-skip-first` onto the opposite end) — walk every slot but
# the LAST: `estimators.dropLast`. A partial-domain rival, correct on every
# roster whose final slot is not the sole non-accepting component. Attacks C7.
_R5_IMPL = _HEAD + """ := Id.run do
  for slot in estimators.dropLast do
    let (name, step) := slot
    match step with
    | none => pure ()
    | some accepts =>
      if accepts then
        pure ()
      else
        return Except.error (errMsg name)
  return Except.ok ()"""

# R6 (AUDIT REPAIR 1 — closes the undemonstrated C5 claim) — accumulate the
# offender instead of stopping at it, so the rejection names the LAST declining
# component rather than the FIRST. Agrees with the reference walk on WHETHER
# every roster is accepted, and on WHICH component is named for every roster with
# at most one declining component — which is every roster the ported witnesses
# probed. Only a roster with TWO declining components separates it. Attacks C5.
_R6_IMPL = _HEAD + """ := Id.run do
  let mut offender : Option String := none
  for slot in estimators do
    let (name, step) := slot
    match step with
    | none => pure ()
    | some accepts =>
      if accepts then
        pure ()
      else
        offender := some name
  match offender with
  | some name => return Except.error (errMsg name)
  | none => return Except.ok ()"""

# R7 (ports nagini `weak-always-raise`) — complete the walk correctly but reject
# unconditionally at the end, so a roster with nothing to object to is still
# refused (with an empty component name). Attacks C6.
_R7_IMPL = _swap(_GOLD_IMPL, "  return Except.ok ()",
                 '  return Except.error (errMsg "")')

# R8 (AUDIT REPAIR 3 — closes the unprobed base case of the walk) — special-case
# the EMPTY roster to a rejection, and walk any non-empty roster exactly as the
# frozen impl does. The narrowest near-miss in the battery: it agrees with the
# reference walk at every roster with at least one slot, so every other witness in
# this file elaborates against it unchanged, and ONLY the empty roster separates
# it. Attacks the `[]` arm of `validateRoster` — a structural point of the input
# binder that no ported witness reached (the seven ported rosters have lengths
# 1, 2 and 3, never 0), which is why the case is added rather than merged.
_R8_IMPL = _HEAD + """ :=
  match estimators with
  | [] => Except.error (errMsg "")
  | _ => Id.run do
    for slot in estimators do
      let (name, step) := slot
      match step with
      | none => pure ()
      | some accepts =>
        if accepts then
          pure ()
        else
          return Except.error (errMsg name)
    return Except.ok ()"""


# ---------------------------------------------------------------------------
# Witnesses. Each states the spec predicate directly at ONE concrete roster and
# reduces both sides: `Id.run`/`pure`/`Id.instMonad` unfold the monadic loop,
# `validateRoster`/`errMsg` the reference walk and its message. Each was built
# against its rival (must elaborate) and against the frozen solution (must fail);
# every one was SEEN to discriminate, gold failing with `⊢ False` — i.e. the spec
# genuinely holds there. `decide` alone is NOT enough: the `Decidable` instance
# gets stuck on the unreduced `forIn` block.
#
# FORGERY-TESTED (audit note 2). "gold failed with ⊢ False" is only admissible
# evidence if gold's exit code tracks the CLAIM rather than the file, so each
# witness was additionally FLIPPED — the leading `¬` dropped, i.e. asserting the
# frozen impl is CORRECT at that same roster — and rebuilt on both sides. All
# eight witnesses invert cleanly and completely:
#
#     claim as shipped (¬ spec holds):   rival exit 0   gold  exit 1  (⊢ False)
#     claim flipped    (  spec holds):   rival exit 1   gold  exit 0
#                                              (⊢ False)
#
# That 4-way inversion is the strongest available signature: the SAME tactic
# script proves the positive claim on gold and the negative claim on the rival, and
# fails in the mirrored positions, so `simp` is deciding these equations rather
# than getting stuck. `⊢ False` here means the simp set fully evaluated both the
# loop and the reference walk and closed the goal — it is a genuine evaluation, not
# a `witness-undecided` stuck reduction, and no witness in this file could be
# swapped for one asserting gold is wrong without the exit codes changing.
# ---------------------------------------------------------------------------

def _w(roster):
    return ("example : ¬ problem_spec_checkWeightSupport\n"
            "    %s\n"
            "    (implementation_checkWeightSupport\n"
            "      %s) := by\n"
            "  unfold problem_spec_checkWeightSupport "
            "implementation_checkWeightSupport\n"
            "  simp [Id.run, pure, Id.instMonad, validateRoster, errMsg]"
            % (roster, roster))


SPEC_TESTS = [

    # ---- POSITIVE CONTROLS (soundness; must verify) ---------------------
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _S1_IMPL),
        "rationale": (
            "A structurally different but behaviorally IDENTICAL impl: the "
            "per-component test is negated and the branch arms swapped "
            "(`if !accepts then reject else continue`). Every slot yields the "
            "same contribution, so the master clause "
            "`result = validateRoster estimators` still holds pointwise, and the "
            "frozen induction closes it unchanged. Must verify against the "
            "master clause; if a faithful reshape of the per-component test "
            "cannot satisfy it, the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-fused-match-arm",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _S2_IMPL),
        "rationale": (
            "A structurally different but behaviorally IDENTICAL impl that "
            "collapses the nested match-then-test into ONE pattern match naming "
            "only the rejecting shape, with a catch-all for every slot the walk "
            "passes over (`| some false => reject | _ => continue`). This fuses "
            "clauses C1 and C2 — the two no-op contributions — into a single "
            "arm, which is what an author who noticed they coincide would write. "
            "Must verify against the master clause, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-structural-recursion",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _S3_IMPL),
                        _GOLD_PROOF, _S3_PROOF),
        "rationale": (
            "The strongest positive control here: the accumulator loop is "
            "replaced by STRUCTURAL RECURSION over the roster, sharing no "
            "control-flow idiom with the frozen impl (no `Id.run`, no `forIn`, no "
            "early `return`). Because it cannot reuse the frozen tactic script, "
            "it is REPROVEN with its own induction inside the proof region — the "
            "`theorem correct_checkWeightSupport` statement is byte-identical and "
            "nothing is assumed. It verifies for the real reason: the recursion "
            "and the reference walk agree at every slot. A correct impl of a "
            "different SHAPE failing here would be SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "admiss-f2p-shaped-roster",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _S4_IMPL),
        "rationale": (
            "Ports the nagini admissibility lane, which an earlier draft of this "
            "port recorded as inexpressible for a reason the audit measured to be "
            "false. This obligation binds no precondition, so there is no "
            "Requires to establish; the surviving content is NON-VACUITY of the "
            "modeled behavior at a concrete F2P-shaped roster. The impl region "
            "carries an anonymous `example` asserting that at an empty slot "
            "beside an accepting component the walk yields `Except.ok ()` — "
            "acceptance, not rejection. `variant_scope` admits it (only new "
            "`theorem`/`lemma` names are banned; `variant_problems` returns []) "
            "and the obligation statement is byte-identical. If the modeled walk "
            "did NOT accept at that shape the case would fail, so it pins the "
            "outcome at the shape the instance turns on instead of restating the "
            "master clause. Verified: exit 0."
        ),
    },

    # ---- UNIQUENESS (must reject; witness SEEN to discriminate) ---------
    {
        "id": "weak-reject-on-empty-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R1_IMPL),
        "refinement": (
            "Its faithful real patch makes the supplied-weights validation walk "
            "treat a slot the caller has EMPTIED as a component that declines "
            "the weights, refusing the whole roster and naming that empty slot. "
            "The listed failing test supplies weights to a roster in which one "
            "slot has been emptied and the remaining component accepts them: it "
            "expects the walk to pass over the empty slot and the fit to "
            "proceed. With this body the fit is refused instead, so the failing "
            "test does NOT pass and the instance does not resolve. A verifying "
            "rival here would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "Rejected by the master clause via C1 (an empty slot contributes "
            "NOTHING): at `[(\"lr\", none), (\"rf\", some true)]` the reference "
            "walk passes over the empty slot and accepts (`Except.ok ()`), while "
            "the rival rejects naming it. Witness at the empty-slot-then-"
            "accepting roster — the 2-slot shape that isolates C1, since it is "
            "the only probed roster where an empty slot precedes a component the "
            "walk must still reach and the outcome is acceptance."
        ),
        # Elaborates against the rival (error ≠ ok); gold fails with ⊢ False.
        "witness": _w('[("lr", none), ("rf", some true)]'),
    },
    {
        "id": "weak-never-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R2_IMPL),
        "refinement": (
            "Its faithful real patch drops the rejection entirely: the walk "
            "visits every slot and always reports success, so a present "
            "component that cannot consume per-sample weights is admitted and "
            "the weights are silently disregarded (or fail far downstream) "
            "instead of being refused up front. The listed test that supplies "
            "weights to a roster containing such a component asserts the walk "
            "raises with the exact message identifying it; with this body "
            "nothing is raised, so that listed test FAILS and the instance does "
            "not resolve. A verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the master clause via C3 (a present non-accepting "
            "component REJECTS the roster): at "
            "`[(\"lr\", some true), (\"knn\", some false)]` the reference walk "
            "yields `Except.error` naming the second component, while the rival "
            "accepts. Witness at an all-present 2-slot roster whose FINAL slot "
            "declines and which contains NO empty slot — chosen so the "
            "refutation is attributable to C3 alone and not to empty-slot "
            "handling."
        ),
        # Elaborates against the rival (ok ≠ error); gold fails with ⊢ False.
        "witness": _w('[("lr", some true), ("knn", some false)]'),
    },
    {
        "id": "weak-inverted-acceptance-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R3_IMPL),
        "refinement": (
            "Its faithful real patch inverts the sense of the per-component "
            "test, refusing the roster at the first component that DOES accept "
            "per-sample weights and admitting those that do not. Every listed "
            "test that supplies weights uses a roster whose leading component "
            "accepts them, so all of them — including the failing test — are "
            "refused and FAIL. A verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the master clause via C2/C3 (the SENSE of the "
            "per-component test): at the single-slot roster "
            "`[(\"rf\", some true)]` the reference walk accepts, while the rival "
            "rejects naming that component. Witness at a 1-slot all-accepting "
            "roster — the shortest probed roster, and the only one containing "
            "NEITHER an empty slot nor a declining component, so it isolates the "
            "accepting-component arm that every other rival handles correctly."
        ),
        # Elaborates against the rival (error ≠ ok); gold fails with ⊢ False.
        "witness": _w('[("rf", some true)]'),
    },
    {
        "id": "weak-names-leading-component",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R4_IMPL),
        "refinement": (
            "Its faithful real patch refuses the roster at exactly the right "
            "moment but builds the message from the roster's FIRST entry instead "
            "of the component that actually declined, so the caller is told the "
            "wrong component is at fault. The listed test that supplies weights "
            "to a roster containing a declining component asserts the raised "
            "message VERBATIM, naming that component; with this body the message "
            "names the leading entry instead, the assertion FAILS, and the "
            "instance does not resolve. A verify-does-not-resolve break. NOTE "
            "this rival is a NEAR-MISS of the accept/reject axis — it agrees "
            "with the reference walk on WHETHER every roster is accepted, and "
            "differs only in the identity carried in the rejection, so it gets "
            "its own witness rather than sharing one."
        ),
        "rationale": (
            "Rejected by the master clause via C4 (the rejection IDENTIFIES the "
            "declining component): at "
            "`[(\"lr\", none), (\"rf\", some true), (\"knn\", some false)]` both "
            "the reference walk and the rival reject, but the walk names the "
            "third component while the rival names the first. Witness at a "
            "3-slot roster mixing an empty slot, an accepting component and a "
            "declining one — the only probed roster where the declining "
            "component is neither first nor second, which is exactly what makes "
            "the misnaming observable."
        ),
        # Elaborates against the rival (names differ); gold fails with ⊢ False.
        "witness": _w('[("lr", none), ("rf", some true), ("knn", some false)]'),
    },
    {
        "id": "weak-drops-final-slot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R5_IMPL),
        "refinement": (
            "Its faithful real patch walks every slot BUT THE LAST, so the final "
            "entry is never validated. A partial-domain rival: correct on every "
            "roster whose final slot is not the sole declining component, and "
            "silently admitting the roster when it is. The listed test that "
            "supplies weights places the declining component LAST and asserts the "
            "walk raises; with this body that component is never examined, "
            "nothing is raised, the listed test FAILS and the instance does not "
            "resolve. A verify-does-not-resolve break on the final-slot "
            "sub-domain."
        ),
        "rationale": (
            "Rejected by the master clause via C7 (EVERY slot is visited): at "
            "`[(\"rf\", some true), (\"nb\", some true), (\"knn\", some false)]` "
            "the reference walk rejects naming the third component, while the "
            "rival — having dropped it — accepts. Witness at a 3-slot ALL-PRESENT "
            "roster whose only declining component is final: distinct from the "
            "other 3-slot probe (which carries an empty slot) so the two "
            "positional rivals are refuted at genuinely different points, and "
            "chosen because a shorter roster could not separate 'drops the final "
            "slot' from 'never rejects'."
        ),
        # Elaborates against the rival (ok ≠ error); gold fails with ⊢ False.
        "witness": _w('[("rf", some true), ("nb", some true), ("knn", some false)]'),
    },
    {
        "id": "weak-names-last-declining",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R6_IMPL),
        "refinement": (
            "Its faithful real patch does not stop the walk at the component that "
            "declines: it records the offender and keeps going, refusing the "
            "roster at the end while naming the LAST component that declined "
            "rather than the first. HONEST SCOPE OF THIS ARGUMENT — this rival "
            "does NOT break the listed suite, and the case is shipped on the "
            "narrower ground stated next. Every listed roster that supplies "
            "weights carries AT MOST ONE declining component (projected onto this "
            "carrier: the weight-supplying rosters have declining counts "
            "0/0/0/0/1/0), and on such a roster 'first declining' and 'last "
            "declining' coincide — so this body computes the same outcome and the "
            "same message as the modeled walk at every listed roster, and every "
            "listed test PASSES. Measured, not argued: the rival was built against "
            "each of the five projected weight-supplying rosters and agrees with "
            "the reference walk on all five (exit 0 on both sides). So a verifying "
            "rival here would NOT be a verify-does-not-resolve break. What it "
            "would be is a spec that fails to pin the SHORT-CIRCUIT the modeled "
            "region actually performs — the real region stops at the first "
            "declining component rather than surveying the whole roster — which is "
            "behavior inside the modeled surface even though the listed tests "
            "never reach a roster that observes it. The case therefore attests to "
            "spec STRENGTH on clause C5, not to F2P/P2P resolution; it is kept "
            "because C5 is genuine modeled behavior, and it is labelled this way "
            "so no reader mistakes it for a resolve break."
        ),
        "rationale": (
            "Rejected by the master clause via C5 (it is the FIRST declining "
            "component that is identified): at "
            "`[(\"knn\", some false), (\"mlp\", some false)]` the reference walk "
            "stops at the first slot and names it, while the rival walks on and "
            "names the second. Witness at the ONLY probed roster with TWO "
            "declining components — required, because on a roster with at most "
            "one such component 'first' and 'last' coincide and this rival is "
            "indistinguishable from the frozen impl. ADDED BY AUDIT: C5 was "
            "claimed in the clause list above but no shipped rival demonstrated "
            "it, since all six ported witnesses probed rosters with 0 or 1 "
            "declining component."
        ),
        # Rebuilt by the audit: rival exit 0, gold exit 1 with `⊢ False`.
        "witness": _w('[("knn", some false), ("mlp", some false)]'),
    },
    {
        "id": "weak-always-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R7_IMPL),
        "refinement": (
            "Its faithful real patch completes the walk correctly but then "
            "refuses the roster unconditionally, so a configuration with nothing "
            "to object to is rejected anyway (with an empty component name). "
            "EVERY listed test that supplies per-sample weights — including the "
            "failing test, whose roster is accepted once the emptied slot is "
            "passed over — then has its fit refused and FAILS. A "
            "verify-does-not-resolve break."
        ),
        "rationale": (
            "Rejected by the master clause via C6 (a roster with no declining "
            "present component is ACCEPTED): at the single-slot roster "
            "`[(\"lr\", none)]` the reference walk passes over the empty slot and "
            "accepts, while the rival rejects with an empty name. Witness at the "
            "1-slot ALL-EMPTY roster — the only probed roster containing no "
            "present component whatsoever, so the acceptance it demands cannot "
            "be produced by any per-component reasoning and isolates the "
            "walk-completed-successfully outcome."
        ),
        # Elaborates against the rival (error ≠ ok); gold fails with ⊢ False.
        "witness": _w('[("lr", none)]'),
    },
    {
        "id": "weak-rejects-empty-roster",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _R8_IMPL),
        "refinement": (
            "Its faithful real patch special-cases the situation where the "
            "ensemble's roster carries no slots at all, refusing it outright "
            "instead of letting the walk complete with nothing to object to. "
            "HONEST SCOPE, on the same standard applied to the other near-miss in "
            "this file: no listed test supplies per-sample weights to an EMPTY "
            "roster (the listed weight-supplying rosters all carry at least one "
            "slot), so this body computes exactly what the modeled walk computes "
            "at every listed roster and the listed suite PASSES. Measured, not "
            "argued: this rival's module was built and the other seven witnesses in "
            "this file were built against it, all agreeing with the reference walk. "
            "So a verifying rival here would not be a verify-does-not-resolve "
            "break; it would be a spec that leaves the walk's BASE CASE — the "
            "outcome when the roster is exhausted with nothing rejected — "
            "unconstrained. That base case is genuine modeled behavior (it is the "
            "`[] => Except.ok ()` arm of the reference walk, and it is the arm "
            "every accepting outcome ultimately bottoms out in), so the case "
            "attests to spec STRENGTH at the one structural point of the input "
            "binder no other case reaches."
        ),
        "rationale": (
            "Rejected by the master clause at the `[]` arm of `validateRoster`: at "
            "the EMPTY roster `[]` the reference walk yields `Except.ok ()` — the "
            "walk has nothing to examine and therefore nothing to object to — "
            "while the rival rejects with an empty component name. Witness at `[]`, "
            "the ZERO-LENGTH roster, which is the only structural point of the "
            "list binder that the seven ported witnesses never reach (their rosters "
            "have lengths 1, 2 and 3). Deliberately the narrowest rival here: it "
            "agrees with the reference walk at every roster with at least one slot, "
            "so it is refuted at exactly one input and nowhere else, which is what "
            "makes its rejection attributable to the base case alone rather than to "
            "any per-slot reasoning. ADDED BY AUDIT: length-0 was an unprobed "
            "structural point of the sole input binder."
        ),
        # Rebuilt by the audit: witness-vs-rival exit 0, witness-vs-gold exit 1
        # with `⊢ False`, and the flipped-claim forgery INVERTS (gold 0 / rival 1),
        # so gold's exit code tracks the claim rather than the file.
        "witness": _w('[]'),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job, and this bundle ships NO consumed axiom
# to probe. The nagini sibling's two axiom cases target its `@ContractOnly`
# boolean probe; here that observation is modeled as a grounded input flag
# carried in each present slot (`some accepts`), not as an `opaque` callee with a
# contract, so there is no `_prop` for a PBT axiom lane to exercise. mapping.md
# records G-AX as a skip stub for this bundle.
AXIOM_TESTS = []
