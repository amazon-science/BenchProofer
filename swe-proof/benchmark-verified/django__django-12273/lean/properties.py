# properties.py — G-PBT falsification battery for django__django-12273 (lean).
#
# NOT a Lean file. A manifest the G-PBT runner parses: each SPEC_TESTS entry is a
# full Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region and — for a soundness positive that legitimately reproves, and for
# the admissibility positive, which prepends ground `have`s and keeps the frozen
# tactic body below them — the proof region differ), so markers.same_spec holds
# by construction and every rejection
# is attributable to the postcondition rather than to a tampered spec. No variant
# introduces an axiom, a helper lemma beyond the frozen set, `sorry`/`admit`, or
# `native_decide`, and every `theorem correct_*` statement is preserved
# byte-identically.
#
# ---------------------------------------------------------------------------
# Defended surface (read from Solution.lean + mapping.md + refinement.md)
# ---------------------------------------------------------------------------
#   implementation_setPrimaryKey
#       (store : String → Option Int) (primaryKeyName : String)
#       (ancestorLinks : List AncestorLink) (value : Option Int)
#       : String → Option Int
#
#   ONE obligation: `theorem correct_setPrimaryKey`, with NO precondition
#   hypothesis — the statement is a bare ∀ over all four binders.
#
#   The single load-bearing postcondition clause is a total functional equality
#   on the resulting attribute map:
#
#       result = setAttr (applyLinks store ancestorLinks value) primaryKeyName value
#
#   It is one equation, but it pins three independent behaviours, each of which a
#   rival can violate on its own, and each of which is probed here:
#
#     (C1) the OWN-key write always takes effect and is applied LAST
#          (the outer `setAttr … primaryKeyName value`);
#     (C2) the CASCADE: `applyLinks` walks the WHOLE ancestor-link list front to
#          back and writes `value` — not a derived value — to the key of every
#          link satisfying `linked ∧ ¬sameAsPrimaryKey`;
#     (C3) the FRAME + the two-part GUARD: `applyLinks` writes NOTHING for a link
#          failing the guard, and `setAttr` leaves every other attribute name at
#          its input value. Because the carrier is a TOTAL map, the frame is not a
#          separate conjunct — it is carried by the equality itself, so any
#          spillover to an unrelated attribute name is refutable by evaluating
#          both sides at that name. That last sentence is DEMONSTRATED, not just
#          asserted: uniq-wipe-frame is refuted at a name no input binder
#          mentions. The guard's exclusion half is additionally probed for WHICH
#          input it reads (uniq-attname-guard), since `sameAsPrimaryKey` and
#          `keyName` are independent binders that a rival can conflate.
#
#   There is no opaque callee, no consumed axiom and no answer-key oracle: the
#   postcondition is grounded entirely in the input binders through the concrete
#   `setAttr` / `applyLinks` folds. So every rival below is refutable at CONCRETE
#   literal inputs by `decide` — no conditioning on the carrier is needed, and
#   consequently no witness binds anything (nothing for the gate's consistency
#   probe to find, and no risk of a `witness-inconsistent` forgery).
#
#   Witness shape. The carrier is a FUNCTION (`String → Option Int`), so the
#   refutation is stated by applying the claimed equality at the one attribute
#   name where the rival and the spec disagree:
#
#       fun h => absurd (congrFun h "<name>") (by decide)
#
#   `congrFun` turns the functional equality into a decidable `Option Int`
#   equation at that name; `decide` then closes it. Verified by hand against both
#   files for every case: elaborates against the rival, fails on the frozen
#   solution.
#
# F2P (model_inheritance_regress.tests.ModelInheritanceTest):
#   test_create_new_instance_with_pk_equals_none
#   test_create_new_instance_with_pk_equals_none_multi_inheritance
#
# ---------------------------------------------------------------------------
# Nagini cases carried over, and the ones deliberately NOT carried
# ---------------------------------------------------------------------------
# Ported (the ARGUMENT re-expressed against this carrier, not the mechanics):
#   nagini partial-prepatch      -> uniq-no-cascade            (C2)
#   nagini partial-drop-first    -> uniq-drop-first-link       (C2)
#   nagini partial-drop-last     -> uniq-drop-last-link        (C2)
#   nagini partial-wrong-value   -> uniq-wrong-cascade-value   (C2)
#   nagini partial-drop-pk       -> uniq-drop-own-key          (C1)
#   nagini partial-invert-guard  -> uniq-invert-guard          (C2 + C3)
#   nagini partial-over-cascade  -> uniq-ignore-absent-link,
#                                   uniq-ignore-coincident-link (C3)
#     — split in two, because this carrier makes the guard's two halves
#       INDEPENDENTLY attackable and a single rival dropping the whole guard
#       would leave each half individually undefended.
#   nagini pos-locals            -> pos-let-hoist              (soundness)
#   plus pos-foldl, a shape with no nagini counterpart: a pure functional fold
#   replacing the mutable accumulator, needing a genuinely re-derived proof.
#
# Added by AUDIT (no nagini counterpart; both were gaps the header above claimed
# and no case demonstrated — see each case's own rationale):
#   uniq-wipe-frame      (C3, frame half: the only refutation stated at an
#                         attribute name outside the input's key chain)
#   uniq-attname-guard   (C3, exclusion half: reads `keyName` vs
#                         `primaryKeyName` instead of the `sameAsPrimaryKey`
#                         input, which U8 cannot distinguish)
#
# Added by a LATER AUDIT pass, correcting a case this manifest previously
# recorded as inexpressible:
#   admiss-ground-key-chain  (nagini admiss-single-inheritance, re-expressed —
#                         the obligation is shown SATISFIABLE, and its ground
#                         outcome pinned by evaluation, at two F2P-shaped inputs)
#
# NOT ported, with reasons (see also `assessment` in the submitted payload):
#   * nagini frame-write-target / frame-write-active — VACUOUS on this backend.
#     They exist because nagini holds those inputs at fractional permission and a
#     rival that WRITES to a read-only input must be rejected for insufficient
#     permission. Lean is referentially transparent: `ancestorLinks` and
#     `primaryKeyName` are immutable values, there is no aliasing and no
#     permission to under-hold, so the illegal write those cases probe cannot be
#     expressed at all. No substitute is fabricated. (The FRAME concern itself is
#     not dropped — it survives as C3 and is attacked by uniq-invert-guard,
#     uniq-ignore-absent-link and uniq-ignore-coincident-link.)
#   * nagini admiss-single-inheritance — PORTED after all, as
#     admiss-ground-key-chain. This entry previously read "VACUOUS: the frozen
#     obligation carries NO precondition hypothesis, so there is nothing for an
#     admissibility probe to establish". That reasoning is REJECTED by a later
#     audit pass and the case is landed. A bare `∀` removes the hypothesis one
#     could weaken; it does not remove the property this lane exists to test. On
#     a total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#     UNSATISFIABLE at exactly an F2P-shaped input — a spec dischargeable only in
#     the abstract, or whose ground instance at the interesting input reduces to
#     something other than the intended behaviour — and a bare `∀` makes that
#     checkable by EVALUATION rather than unreachable. See the case's own
#     rationale for the two ground instances and for the measurement showing the
#     ground-outcome half is load-bearing.
#   * nagini AXIOM_TESTS (ax-sound-set-pk-val, ax-contain-active-targets) —
#     out of scope: the axiom lane is G-AX's job and this gate ignores
#     AXIOM_TESTS. This bundle has no axiom and no deep-model reference anyway
#     (mapping.md/refinement.md: no A-consumed and no A-reference row).
#   * divergence / non-termination — nothing to ship, and the reason is the
#     ELABORATION discipline, not referential transparency: this bundle sets no
#     `partial` semantics option, `implementation_setPrimaryKey` is a total Lean
#     `def` over a `for` loop on a finite list, and a non-terminating rival would
#     not be accepted as a `def` at all. The known spec hole where such a rival
#     verifies VACUOUSLY is the velvet `loom.semantics.termination "partial"`
#     lane, already measured and recorded in the corpus-wide termination-semantics finding; it is
#     cited here rather than re-derived, and is NOT a finding against this cell.
#     The nagini sibling carries no diverge-*/nonterm-* case in any event.

from pathlib import Path

INSTANCE = "django__django-12273"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside the region it edits and is unique in the
# file, so the manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

# impl region: the whole executable body.
_IMPL_BODY = """    String → Option Int := Id.run do
  let mut s := store
  for link in ancestorLinks do
    if link.linked && !link.sameAsPrimaryKey then
      s := setAttr s link.keyName value
  s := setAttr s primaryKeyName value
  return s"""

# impl region: the guarded cascade write (two lines; distinct from the pure
# region's one-line `applyLinks` branch and from the proof's `= true` form).
_GUARD = """    if link.linked && !link.sameAsPrimaryKey then
      s := setAttr s link.keyName value"""

# impl region: the loop header.
_LOOP = "  for link in ancestorLinks do"

# impl region: the accumulator's initialization from the input object.
_INIT = "  let mut s := store"

# impl region: the trailing own-key write plus the return.
_OWNKEY = "  s := setAttr s primaryKeyName value\n  return s"

# proof region: the obligation's `intro` line. The admissibility case prepends
# its ground `have`s here and leaves the frozen tactic body below untouched.
_P_INTRO = "  intro store primaryKeyName ancestorLinks value\n"

for _a in (_IMPL_BODY, _GUARD, _LOOP, _OWNKEY, _INIT, _P_INTRO):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift: {_a!r}")

# proof region: the entire frozen proof (helper + obligation). Only pos-foldl
# touches this, and it re-derives the SAME obligation with a byte-identical
# statement.
_PROOF = """/-- Helper (Route B): the cleaned `forIn` accumulation over the ancestor links,
generalized over the accumulator, equals the front-recursive `applyLinks` fold. -/
theorem forIn_helper (links : List AncestorLink) (init : String → Option Int)
    (value : Option Int) :
    Id.run (forIn links init (fun link r =>
      if (link.linked && !link.sameAsPrimaryKey) = true then
        pure (ForInStep.yield (setAttr r link.keyName value))
      else
        pure (ForInStep.yield r))) = applyLinks init links value := by
  induction links generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, applyLinks] at ih ⊢
    by_cases h : (a.linked && !a.sameAsPrimaryKey) = true
    · simp only [h, if_true, ih]
    · simp only [h, ih]
      simp only [Bool.not_eq_true] at h
      simp only [Bool.false_eq_true, if_false]

theorem correct_setPrimaryKey :
    ∀ (store : String → Option Int) (primaryKeyName : String)
      (ancestorLinks : List AncestorLink) (value : Option Int),
      problem_spec_setPrimaryKey store primaryKeyName ancestorLinks value
        (implementation_setPrimaryKey store primaryKeyName ancestorLinks value) := by
  intro store primaryKeyName ancestorLinks value
  unfold problem_spec_setPrimaryKey implementation_setPrimaryKey
  simp only [Id.run, bind]
  have := forIn_helper ancestorLinks store value
  simp only [Id.run] at this
  rw [this]
  rfl"""

if _BASE.count(_PROOF) != 1:
    raise AssertionError("proof anchor drift")


# ===========================================================================
# SOUNDNESS POSITIVES — structurally different but CORRECT. Must VERIFY, else
# SPEC-TOO-STRONG. Both confirmed to build green (exit 0) with no sorry.
# ===========================================================================

# (S1) Read the guard result and the target attribute name into local bindings
# before the write. Identical data/control flow, so the frozen tactic script
# still closes unchanged — the cheapest possible reshape, and the analogue of the
# nagini sibling's local-variable positive.
POS_LET_HOIST = _swap(
    _BASE,
    _GUARD,
    """    let qualifies := link.linked && !link.sameAsPrimaryKey
    let ancestorKey := link.keyName
    if qualifies then
      s := setAttr s ancestorKey value""",
)

# (S2) A genuinely different SHAPE: drop the mutable accumulator and the `do`
# block entirely, expressing the cascade as a pure `List.foldl` and the own-key
# write as the outermost `setAttr`. The frozen proof does NOT survive this (its
# helper is about `forIn`), so the obligation is re-derived: the helper is
# restated over `List.foldl` and closed by the same accumulator-generalizing
# induction, and `correct_setPrimaryKey` — statement byte-identical — closes by
# `rw [forIn_helper]` alone. This is the case that would catch a spec pinned to
# the frozen impl's syntactic form rather than to its behaviour.
_POS_FOLDL_IMPL = """    String → Option Int :=
  setAttr
    (ancestorLinks.foldl
      (fun s link =>
        if link.linked && !link.sameAsPrimaryKey then setAttr s link.keyName value else s)
      store)
    primaryKeyName value"""

_POS_FOLDL_PROOF = """/-- Helper: the left fold over the ancestor links, generalized over the
accumulator, equals the front-recursive `applyLinks` fold. -/
theorem forIn_helper (links : List AncestorLink) (init : String → Option Int)
    (value : Option Int) :
    links.foldl
      (fun s link =>
        if link.linked && !link.sameAsPrimaryKey then setAttr s link.keyName value else s)
      init = applyLinks init links value := by
  induction links generalizing init with
  | nil => rfl
  | cons a as ih =>
    simp only [List.foldl_cons, applyLinks, ih]

theorem correct_setPrimaryKey :
    ∀ (store : String → Option Int) (primaryKeyName : String)
      (ancestorLinks : List AncestorLink) (value : Option Int),
      problem_spec_setPrimaryKey store primaryKeyName ancestorLinks value
        (implementation_setPrimaryKey store primaryKeyName ancestorLinks value) := by
  intro store primaryKeyName ancestorLinks value
  unfold problem_spec_setPrimaryKey implementation_setPrimaryKey
  rw [forIn_helper]"""

POS_FOLDL = _swap(_swap(_BASE, _IMPL_BODY, _POS_FOLDL_IMPL), _PROOF, _POS_FOLDL_PROOF)


# ===========================================================================
# ADMISSIBILITY — non-vacuity of the obligation at F2P-shaped inputs.
# ===========================================================================
#
# Added by a later AUDIT pass. The earlier header recorded this lane as VACUOUS
# because `correct_setPrimaryKey` carries no precondition hypothesis, so "there
# is no precondition that could be too strong". That reason is wrong, and it is
# the specific reason this lane goes missing across the corpus. On a TOTAL
# carrier the analogue of PRECOND-TOO-STRONG is not a hypothesis one can weaken:
# it is the obligation being UNSATISFIABLE at exactly an F2P-shaped input — a
# spec that quantifies over everything and is dischargeable only in the abstract,
# or one whose ground instance at the interesting input reduces to something
# other than the intended behaviour. A bare `∀` does not make that vacuous; it
# makes it checkable by EVALUATION, which is what this case does.
#
# Two ground instances, both shaped like the F2P scenarios (an object whose own
# primary key is cleared, i.e. `value = none`):
#
#   * `single` — one ancestor link, present and not coincident. The single-parent
#     shape: the own key AND the ancestor key must both end at `none`.
#   * `multi`  — two ancestor links, one already coincident with the own primary
#     key (so excluded by the guard) and one genuinely distinct. The
#     several-inherited-parts shape, where the exclusion half of the guard is
#     live at the same time as the cascade.
#
# Each instance is discharged TWICE, and the pairing is the point:
#
#   `_spec_*` shows `problem_spec_setPrimaryKey` HOLDS at that concrete input,
#   which is the satisfiability claim proper.
#
#   `_obs_*` additionally pins, by `decide`, WHAT the modeled behaviour actually
#   produces there — own key cleared, ancestor key cleared, and an attribute
#   outside the key chain still at its input value. Without it the `_spec_*`
#   `have` would close by `rfl` for ANY impl the spec pins to a term over the
#   same inputs, so it would read identically if the ground input fell into a
#   no-op branch. Measured load-bearing rather than assumed: the `_obs_` half
#   alone, with both `_spec_` haves stripped, builds at exit 0 against the frozen
#   impl and FAILS against three of this battery's own rivals (no-cascade and
#   wipe-frame with `decide` refutations, ignore-coincident on the multi
#   instance).
#
# Nothing is assumed: no new declaration, no assumption token, the
# `correct_setPrimaryKey` statement stays byte-identical, and the frozen tactic
# body is retained unchanged below the prepended `have`s.
_STORE = ('(fun n => if n = "ownPk" then some 5 '
          'else if n = "ancPk" then some 5 else some 99)')
_L_SINGLE = '[{ linked := true, sameAsPrimaryKey := false, keyName := "ancPk" }]'
_L_MULTI = ('[{ linked := true, sameAsPrimaryKey := true, keyName := "ownPk" },\n'
            '       { linked := true, sameAsPrimaryKey := false, keyName := "ancPk" }]')


def _admiss_block(links, tag):
    """Ground satisfiability + ground observable outcome at one F2P-shaped input."""
    return (
        f"""  have _spec_{tag} : problem_spec_setPrimaryKey
      {_STORE} "ownPk"
      {links} none
      (implementation_setPrimaryKey
        {_STORE} "ownPk"
        {links} none) := by rfl
  have _obs_{tag} :
      implementation_setPrimaryKey
          {_STORE} "ownPk"
          {links} none "ownPk" = none
      ∧ implementation_setPrimaryKey
          {_STORE} "ownPk"
          {links} none "ancPk" = none
      ∧ implementation_setPrimaryKey
          {_STORE} "ownPk"
          {links} none "sideAttr" = some 99 := by decide
""")


ADMISS_GROUND = _swap(
    _BASE, _P_INTRO,
    _admiss_block(_L_SINGLE, "single") + _admiss_block(_L_MULTI, "multi")
    + _P_INTRO,
)


# ===========================================================================
# UNIQUENESS RIVALS — each must REJECT, and each ships a witness that has been
# SEEN to hold of the rival and fail on the frozen solution.
# ===========================================================================

# (U1) No cascade at all: write only the own primary-key attribute. This is the
# pre-patch shape (== Solution_prepatch.lean).
UNIQ_NO_CASCADE = _swap(
    _BASE,
    _IMPL_BODY,
    """    String → Option Int := Id.run do
  let mut s := store
  s := setAttr s primaryKeyName value
  return s""",
)
_W_NO_CASCADE = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => some 7) "ownKey"
    [{ linked := true, sameAsPrimaryKey := false, keyName := "ancKey" }] none
    (implementation_setPrimaryKey (fun _ => some 7) "ownKey"
      [{ linked := true, sameAsPrimaryKey := false, keyName := "ancKey" }] none) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "ancKey") (by decide)
"""

# (U2) Skip the FIRST ancestor link.
UNIQ_DROP_FIRST = _swap(_BASE, _LOOP, "  for link in ancestorLinks.tail do")
_W_DROP_FIRST = """example : ¬ problem_spec_setPrimaryKey
    (fun n => if n = "firstAnc" then some 11 else none) "pkOne"
    [{ linked := true, sameAsPrimaryKey := false, keyName := "firstAnc" },
     { linked := true, sameAsPrimaryKey := false, keyName := "secondAnc" }] (some 4)
    (implementation_setPrimaryKey
      (fun n => if n = "firstAnc" then some 11 else none) "pkOne"
      [{ linked := true, sameAsPrimaryKey := false, keyName := "firstAnc" },
       { linked := true, sameAsPrimaryKey := false, keyName := "secondAnc" }] (some 4)) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "firstAnc") (by decide)
"""

# (U3) Skip the LAST ancestor link. Probed at the FINAL link's key, so it does
# not share U2's input: U2 agrees with the spec on the tail and U3 on the head,
# and each witness sits at the name the other rival gets right.
UNIQ_DROP_LAST = _swap(_BASE, _LOOP, "  for link in ancestorLinks.dropLast do")
_W_DROP_LAST = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => some (-3)) "keyOwn"
    [{ linked := true, sameAsPrimaryKey := false, keyName := "nearAnc" },
     { linked := true, sameAsPrimaryKey := false, keyName := "farAnc" }] (some 900)
    (implementation_setPrimaryKey (fun _ => some (-3)) "keyOwn"
      [{ linked := true, sameAsPrimaryKey := false, keyName := "nearAnc" },
       { linked := true, sameAsPrimaryKey := false, keyName := "farAnc" }] (some 900)) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "farAnc") (by decide)
"""

# (U4) Cascade a DERIVED value instead of the assigned one. Reaches every
# qualifying link, in the right order, and writes the own key correctly — the
# nearest miss in the battery, so its witness sits where only the cascaded VALUE
# differs, at a `value` that is `some` (a `none` assignment would make the
# derived value agree with the spec and the rival would look correct).
UNIQ_WRONG_VALUE = _swap(
    _BASE,
    _GUARD,
    """    if link.linked && !link.sameAsPrimaryKey then
      s := setAttr s link.keyName (value.map (· + 1))""",
)
_W_WRONG_VALUE = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => none) "selfKey"
    [{ linked := true, sameAsPrimaryKey := false, keyName := "linkedKey" }] (some 5)
    (implementation_setPrimaryKey (fun _ => none) "selfKey"
      [{ linked := true, sameAsPrimaryKey := false, keyName := "linkedKey" }] (some 5)) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "linkedKey") (by decide)
"""

# (U5) Cascade correctly but omit the own primary-key write. Refuted with an
# EMPTY link list, isolating C1 from C2 entirely.
UNIQ_DROP_OWN_KEY = _swap(_BASE, _OWNKEY, "  return s")
_W_DROP_OWN_KEY = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => some 3) "theOwnKey" [] none
    (implementation_setPrimaryKey (fun _ => some 3) "theOwnKey" [] none) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "theOwnKey") (by decide)
"""

# (U6) Guard polarity flipped: write exactly the links that should be skipped and
# skip exactly the ones that should be written. Refuted at the QUALIFYING link's
# key with a non-qualifying link also present, so the witness demonstrates the
# missed cascade (C2) on an input where the spillover (C3) is live too — the
# sub-domain its rationale claims, and one no other rival's witness occupies.
UNIQ_INVERT_GUARD = _swap(
    _BASE,
    _GUARD,
    """    if !(link.linked && !link.sameAsPrimaryKey) then
      s := setAttr s link.keyName value""",
)
_W_INVERT_GUARD = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => some 9) "ownIdent"
    [{ linked := false, sameAsPrimaryKey := false, keyName := "absentKey" },
     { linked := true, sameAsPrimaryKey := false, keyName := "realAnc" }] none
    (implementation_setPrimaryKey (fun _ => some 9) "ownIdent"
      [{ linked := false, sameAsPrimaryKey := false, keyName := "absentKey" },
       { linked := true, sameAsPrimaryKey := false, keyName := "realAnc" }] none) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "realAnc") (by decide)
"""

# (U7) Drop the PRESENCE half of the guard: an ABSENT link's key is written
# anyway. Correct on every qualifying link, so this is a pure frame break (C3),
# and its witness varies `linked` alone.
UNIQ_IGNORE_ABSENT = _swap(
    _BASE,
    _GUARD,
    """    if !link.sameAsPrimaryKey then
      s := setAttr s link.keyName value""",
)
_W_IGNORE_ABSENT = """example : ¬ problem_spec_setPrimaryKey
    (fun n => if n = "gapKey" then some 61 else some 2) "myPk"
    [{ linked := false, sameAsPrimaryKey := false, keyName := "gapKey" }] (some 17)
    (implementation_setPrimaryKey
      (fun n => if n = "gapKey" then some 61 else some 2) "myPk"
      [{ linked := false, sameAsPrimaryKey := false, keyName := "gapKey" }] (some 17)) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "gapKey") (by decide)
"""

# (U8) Drop the OTHER half of the guard: a link that already coincides with the
# object's own primary-key attribute is written through anyway. Distinct rival
# and distinct sub-domain from U7 — it varies `sameAsPrimaryKey`, which U7's
# witness holds at `false`, so without this case that half of the guard would be
# defended by nothing.
UNIQ_IGNORE_COINCIDENT = _swap(
    _BASE,
    _GUARD,
    """    if link.linked then
      s := setAttr s link.keyName value""",
)
_W_IGNORE_COINCIDENT = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => some 1) "promotedPk"
    [{ linked := true, sameAsPrimaryKey := true, keyName := "coveredKey" }] none
    (implementation_setPrimaryKey (fun _ => some 1) "promotedPk"
      [{ linked := true, sameAsPrimaryKey := true, keyName := "coveredKey" }] none) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "coveredKey") (by decide)
"""

# (U9) Build the result from an EMPTY object rather than from the input one: the
# key chain is written correctly, but every attribute outside it is dropped to
# `none` instead of keeping its previous value.
#
# Added by audit. U1-U8 all state their refutation at a name that their own input
# puts INSIDE the key chain (a link's `keyName`, or `primaryKeyName`), so the C3
# claim that "any spillover to an UNRELATED attribute name is refutable by
# evaluating both sides at that name" was asserted by the header and demonstrated
# by nothing. U7/U8 are near-misses on the guard, not on the frame: each writes an
# extra name that is still one of its own link keys. This rival is the only one
# that breaks the frame at a name no input binder mentions, which is exactly the
# "every attribute that is not part of this key chain keeps its previous value"
# half of the obligation.
UNIQ_WIPE_FRAME = _swap(_BASE, _INIT, "  let mut s : String → Option Int := fun _ => none")
_W_WIPE_FRAME = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => some 42) "pkOnly" [] (some 8)
    (implementation_setPrimaryKey (fun _ => some 42) "pkOnly" [] (some 8)) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "totallyUnrelated") (by decide)
"""

# (U10) Decide the exclusion by comparing the link's ancestor-key NAME against
# the own primary-key attribute name, instead of consulting the link's own
# coincidence flag.
#
# Added by audit. This is the nearest miss in the battery: it agrees with the spec
# on every input where the two happen to move together, and U8 cannot reach it —
# U8 drops the exclusion test outright, so an impl that keeps a test but reads the
# WRONG field passes U8's point. The two are distinct inputs to the modeled
# function (mapping.md binds the flag and the key name to different metadata
# reads), so a rival that conflates them is observably wrong wherever a link is
# flagged as coincident while writing a differently-named ancestor key.
UNIQ_ATTNAME_GUARD = _swap(
    _BASE,
    _GUARD,
    """    if link.linked && link.keyName != primaryKeyName then
      s := setAttr s link.keyName value""",
)
_W_ATTNAME_GUARD = """example : ¬ problem_spec_setPrimaryKey
    (fun _ => some 1) "pkNamed"
    [{ linked := true, sameAsPrimaryKey := true, keyName := "otherName" }] none
    (implementation_setPrimaryKey (fun _ => some 1) "pkNamed"
      [{ linked := true, sameAsPrimaryKey := true, keyName := "otherName" }] none) := by
  unfold problem_spec_setPrimaryKey
  exact fun h => absurd (congrFun h "otherName") (by decide)
"""


SPEC_TESTS = [
    # ------------------------- soundness positives -------------------------
    {
        "id": "pos-let-hoist",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_LET_HOIST,
        "rationale": (
            "Structurally reshaped but observationally identical CORRECT impl: the "
            "guard result and the target attribute name are bound to locals before "
            "the write. Same data and control flow, so the frozen tactic script "
            "still closes the byte-identical `correct_setPrimaryKey` statement "
            "unchanged. Defends the single obligation against SPEC-TOO-STRONG at "
            "the cheapest reshape; the analogue of the nagini sibling's "
            "local-variable positive."
        ),
    },
    {
        "id": "pos-foldl",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_FOLDL,
        "rationale": (
            "A genuinely DIFFERENT SHAPE that is still correct: the mutable "
            "accumulator and the `do` block are gone, the cascade is a pure "
            "`List.foldl` over the ancestor links and the own-key write is the "
            "outermost update. The frozen proof does not survive this, so the "
            "obligation is honestly RE-DERIVED — the helper is restated over "
            "`List.foldl` and closed by the same accumulator-generalizing "
            "induction, then `correct_setPrimaryKey` (statement byte-identical, "
            "tactic body only) closes by rewriting with it. No new lemma beyond "
            "the frozen set, no `sorry`, no weakened obligation. This is the case "
            "that would expose a spec pinned to the frozen impl's syntactic form "
            "rather than to the behaviour it describes."
        ),
    },

    # ---------------------- admissibility (non-vacuity) --------------------
    {
        "id": "admiss-ground-key-chain",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS_GROUND,
        "rationale": (
            "The obligation is an unguarded `∀` over all four binders, so there "
            "is no precondition hypothesis to weaken — but that does NOT make "
            "this lane vacuous, and recording it as vacuous is what this case "
            "corrects. On a total carrier the analogue of PRECOND-TOO-STRONG is "
            "the obligation being UNSATISFIABLE at exactly an F2P-shaped input, "
            "which is tested directly by discharging it at concrete inputs by "
            "EVALUATION before closing the frozen obligation verbatim. Two "
            "ground instances, both shaped like the F2P scenarios (the object's "
            "own primary key being CLEARED, `value = none`): one ancestor link "
            "present and non-coincident (the single-inherited-part shape), and "
            "two links of which one already coincides with the own primary key "
            "and is therefore excluded while the other genuinely cascades (the "
            "several-inherited-parts shape, where the exclusion half of the "
            "guard is live alongside the cascade). Each is discharged twice: "
            "`_spec_*` shows the postcondition HOLDS there, and `_obs_*` pins by "
            "`decide` WHAT the modeled behaviour produces — own key cleared, "
            "ancestor key cleared, an attribute outside the key chain still at "
            "its input value. The second half is what makes the case bite: the "
            "spec pins `result` to a term over the same inputs, so the `_spec_*` "
            "`have` alone would close by `rfl` without ever showing which "
            "outcome that input yields. Measured load-bearing rather than "
            "asserted — the `_obs_*` half alone, with both `_spec_*` haves "
            "stripped, verifies against the frozen impl and FAILS against three "
            "of this battery's own rivals. Must verify; a failure would mean the "
            "modeled behaviour is unsatisfiable at exactly the inputs the "
            "failing tests observe. Nothing is assumed: no new declaration, no "
            "assumption token, `correct_setPrimaryKey`'s statement is "
            "byte-identical and the frozen tactic body is retained unchanged."
        ),
    },

    # ------------------------- uniqueness rivals ---------------------------
    {
        "id": "uniq-no-cascade",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_NO_CASCADE,
        "refinement": (
            "The faithful real patch is the UNCHANGED code: assign only the "
            "object's own primary-key attribute and never reach the ancestor-key "
            "attributes that tie it to its inherited parts. On an object built by "
            "inheritance, clearing the primary key then leaves the ancestor key "
            "still pointing at the original inherited part, so a subsequent save "
            "overwrites that part instead of creating a new one — the exact "
            "reported behaviour. Both F2P tests "
            "(test_create_new_instance_with_pk_equals_none and its "
            "..._multi_inheritance sibling) fail, so it would NOT resolve."
        ),
        "rationale": (
            "Rejected by C2 (the cascade in `applyLinks`): with one present, "
            "non-coincident link the spec requires that link's key to hold "
            "`value`, and this impl leaves it at its input value. Witness "
            "evaluates the claimed functional equality at that key: the rival "
            "yields the stale entry where the spec yields the assigned value. "
            "Binders varied: a uniform-`some` store, a `none` assignment, a "
            "single qualifying link."
        ),
        "witness": _W_NO_CASCADE,
    },
    {
        "id": "uniq-drop-first-link",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_DROP_FIRST,
        "refinement": (
            "A faithful real patch whose traversal of the ancestor links starts "
            "one position in. For an object with a single inherited part — where "
            "the only link IS the first one — the ancestor key is never "
            "reassigned, so clearing the primary key does not clear the key chain "
            "and the save overwrites the original inherited part. "
            "test_create_new_instance_with_pk_equals_none fails; NOT resolve."
        ),
        "rationale": (
            "Rejected by C2 at the HEAD of the link list: `applyLinks` walks the "
            "whole list, this impl walks its tail. Witness probes the first "
            "link's key with two qualifying links present, and is deliberately "
            "NOT the input used for uniq-drop-last-link — this rival is correct "
            "on the tail, that one on the head, so each is refuted at the name "
            "the other gets right. Binders varied: a store that is `some` at "
            "exactly the probed key and `none` elsewhere, a `some` assignment, a "
            "two-element link list."
        ),
        "witness": _W_DROP_FIRST,
    },
    {
        "id": "uniq-drop-last-link",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_DROP_LAST,
        "refinement": (
            "A faithful real patch whose traversal stops one link short. In a "
            "multi-level inheritance chain the deepest ancestor key keeps "
            "pointing at the original inherited part, so clearing the primary key "
            "resets the chain only partially and the save is inconsistent for "
            "that chain. The new-instance F2P test fails on it; NOT resolve."
        ),
        "rationale": (
            "Rejected by C2 at the TAIL of the link list. Witness probes the last "
            "link's key. Binders varied independently of every other case: a "
            "uniform NEGATIVE store value, a large `some` assignment, distinct "
            "attribute names."
        ),
        "witness": _W_DROP_LAST,
    },
    {
        "id": "uniq-wrong-cascade-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_WRONG_VALUE,
        "refinement": (
            "A faithful real patch that writes a DERIVED value to the "
            "ancestor-key attributes rather than the value being assigned. The "
            "ancestor key then disagrees with the object's own primary key, so the "
            "object is not consistently re-keyed and a save writes a row whose "
            "link to its inherited part is wrong — the F2P assertions on the "
            "inherited part's own fields fail. NOT resolve."
        ),
        "rationale": (
            "Rejected by C2's VALUE half specifically: this rival reaches every "
            "qualifying link, in the right order, and writes the own key "
            "correctly, so it is the nearest miss in the battery and needs its own "
            "input rather than sharing one. Its witness therefore sits where only "
            "the cascaded value can differ — a `some` assignment (under a `none` "
            "assignment the derived value coincides with the spec's and this rival "
            "would look correct, which is exactly the sub-domain distinction the "
            "rationale claims). Binders varied: an everywhere-`none` store."
        ),
        "witness": _W_WRONG_VALUE,
    },
    {
        "id": "uniq-drop-own-key",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_DROP_OWN_KEY,
        "refinement": (
            "A faithful real patch that reaches the ancestor keys but drops the "
            "assignment to the object's own primary-key attribute. Clearing the "
            "primary key would then not clear the object's own key at all, leaving "
            "the identity internally inconsistent; both F2P tests assert the own "
            "key was cleared. NOT resolve."
        ),
        "rationale": (
            "Rejected by C1 (the always-applied own-key write). Witness uses an "
            "EMPTY ancestor-link list, which isolates C1 from C2 completely: the "
            "cascade is vacuous there, so the only thing the refutation can be "
            "attributed to is the missing own-key assignment. Binders varied: the "
            "only case in the battery probing the empty link list."
        ),
        "witness": _W_DROP_OWN_KEY,
    },
    {
        "id": "uniq-invert-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_INVERT_GUARD,
        "refinement": (
            "A faithful real patch with the qualifying condition inverted: it "
            "writes exactly the links that must be skipped (absent ones, and ones "
            "already covered by the own-key assignment) and skips exactly the "
            "genuine ones. On an object inheriting from several parts the real "
            "ancestor key is never reassigned while an excluded attribute is "
            "wrongly overwritten, so ..._multi_inheritance fails and unrelated "
            "inheritance behaviour is corrupted. NOT resolve."
        ),
        "rationale": (
            "Rejected by C2 AND C3 at once. The witness is stated at the "
            "QUALIFYING link's key on an input that ALSO carries a "
            "non-qualifying link, so the point it refutes at is inside the "
            "sub-domain the rationale claims — the missed cascade — while the "
            "spillover is live as well. That input is occupied by no other "
            "witness in the battery. Binders varied: a two-element link list "
            "mixing an absent and a present link, a `none` assignment."
        ),
        "witness": _W_INVERT_GUARD,
    },
    {
        "id": "uniq-ignore-absent-link",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_IGNORE_ABSENT,
        "refinement": (
            "A faithful real patch that drops the PRESENCE half of the qualifying "
            "condition and writes through a link that is not actually there. An "
            "attribute outside the key chain is overwritten on every assignment to "
            "the primary key, which corrupts state the fix must leave alone and "
            "breaks the unrelated inheritance behaviour the P2P suite covers. NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by C3 (the frame + the presence half of the guard): the spec "
            "writes NOTHING for a link that is absent, and because the carrier is "
            "a total map the frame is carried by the equality itself, so the "
            "spillover is refutable by evaluating both sides at the spilled-on "
            "name. This rival is correct on every qualifying link, so it is a pure "
            "frame break. Binders varied: `linked` is `false` here — the only "
            "value no other witness's qualifying link takes — with "
            "`sameAsPrimaryKey` held at `false` so the presence half is isolated; "
            "store distinguishes the probed key from the rest."
        ),
        "witness": _W_IGNORE_ABSENT,
    },
    {
        "id": "uniq-ignore-coincident-link",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_IGNORE_COINCIDENT,
        "refinement": (
            "A faithful real patch that drops the OTHER half of the qualifying "
            "condition — the exclusion of a link that already coincides with the "
            "object's own primary-key attribute — and writes through it anyway. "
            "This is precisely the multi-inherited-object breakage reported "
            "against a partial fix: the attribute is re-targeted through itself "
            "and other inheritance tests break. NOT resolve."
        ),
        "rationale": (
            "Rejected by C3 through the SECOND half of the guard, which "
            "uniq-ignore-absent-link cannot reach: that witness holds "
            "`sameAsPrimaryKey` at `false`, and this one is the only case that "
            "moves it to `true`. Without both cases one half of the two-part "
            "condition would be defended by nothing and a rival mishandling only "
            "that half would verify. Binders varied: `linked = true` with "
            "`sameAsPrimaryKey = true`, a uniform store, a `none` assignment."
        ),
        "witness": _W_IGNORE_COINCIDENT,
    },
    {
        "id": "uniq-wipe-frame",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_WIPE_FRAME,
        "refinement": (
            "A faithful real patch that rebuilds the object's attributes from "
            "scratch instead of updating them in place: it re-keys the whole key "
            "chain correctly, but every attribute outside that chain is dropped "
            "rather than carried over. Assigning a primary key would then silently "
            "discard all of the object's other field values, so essentially every "
            "test that reads a non-key attribute after such an assignment breaks — "
            "far beyond the reported behaviour. NOT resolve."
        ),
        "rationale": (
            "Rejected by C3's FRAME half specifically, which no other case "
            "demonstrates: U1-U8 each state their refutation at a name their own "
            "input places INSIDE the key chain (a link's `keyName`, or "
            "`primaryKeyName`), and U7/U8 break only the GUARD — the extra name "
            "they write is still one of their own link keys. This rival is correct "
            "on the entire key chain, so the only thing its rejection can be "
            "attributed to is the pinning of attributes outside it. Its witness "
            "evaluates the claimed equality at an attribute name that appears in NO "
            "input binder, using an EMPTY link list so the cascade is vacuous and "
            "the own-key write is correct: the only surviving difference is the "
            "dropped input value. Binders varied: a uniform `some` store with a "
            "`some` assignment and an empty link list, and the only probe point in "
            "the battery outside the key chain."
        ),
        "witness": _W_WIPE_FRAME,
    },
    {
        "id": "uniq-attname-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": UNIQ_ATTNAME_GUARD,
        "refinement": (
            "A faithful real patch that decides the exclusion by comparing the "
            "ancestor-key attribute NAME the link writes against the object's own "
            "primary-key attribute name, rather than asking whether the link itself "
            "coincides with the own primary key. The two agree on the common shape "
            "and diverge exactly where a link is the own primary key but addresses a "
            "differently-named ancestor key: that key is then re-written when it "
            "must be left alone, which is the multi-inherited-object breakage. "
            "NOT resolve."
        ),
        "rationale": (
            "Rejected by C3's exclusion half, read through the WRONG input. This is "
            "the nearest miss in the battery: it keeps a two-part guard and keeps "
            "the presence half intact, so it is not caught at U7's point, and it "
            "still excludes something, so it is not caught at U8's point either — "
            "U8 drops the exclusion outright, and an impl that merely consults the "
            "wrong field survives that witness. The distinction is load-bearing "
            "because `sameAsPrimaryKey` and `keyName` are INDEPENDENT input "
            "binders here (mapping.md binds them to different metadata reads), so "
            "the spec must be sensitive to which one the exclusion reads. Witness "
            "sits at the one point where they can disagree: a link flagged "
            "coincident whose ancestor-key name differs from the own primary-key "
            "name, where the spec skips the write and this rival performs it. "
            "Binders varied: the only case holding `sameAsPrimaryKey = true` while "
            "the link's `keyName` and `primaryKeyName` are distinct strings."
        ),
        "witness": _W_ATTNAME_GUARD,
    },
]
