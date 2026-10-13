# properties.py — PBT falsification battery for django__django-15525 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each SPEC_TESTS case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, where a reshaped correct impl needs it, the proof body), so the frozen
# spec (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and the `theorem correct_resolveRecord` STATEMENT is preserved
# verbatim. No case introduces sorry/admit/native_decide/axiom or any new
# theorem/lemma.
#
# ---------------------------------------------------------------------------
# PORT NOTE — carrier narrowing vs the nagini sibling.
# ---------------------------------------------------------------------------
# The nagini battery contracts the fix over three pass-by-value `int` store ids,
# pinning a constructed result object's routing field to the target store. This
# Lean bundle models the SAME fix on a purely functional carrier: assembling a
# record's data for processing. `resolveRecord` takes the record `data` (an
# optional pre-known identifier + a descriptive `payload`), a target `store`
# alias, a `hasKey` flag saying whether the model being processed supports
# identifying keys, and the key-derivation step `derive` that model offers; it
# returns the resolved `data`, or a `Failure` if it had to run a derivation that
# was not there to run.
#
# `derive` is a PARTIAL callee and a BINDER of the spec, not a global constant:
# `derivationAvailability data store hasKey derive` says a key comes back under
# `hasKey` FOR THE RECORD ASSEMBLED ON `store`, that nothing comes back when
# `hasKey` is false, and — deliberately — nothing at all about the step on any
# other record. The frozen obligation assumes only that. So `hasKey` is a
# DEFINEDNESS condition for running the derivation, and so is being on the target
# store, rather than either being merely a condition on whether running it is
# useful; that is what clause (C0) below is stated over. The other two callees
# (`lookupByKey`, `coerceId`) are opaque constants — there is no value to
# compute, so the rivals that attack them are refuted by CONDITIONING on the
# carrier (see the witnesses), not by literal evaluation.
#
# DEFENDED SURFACE (what every rival attacks) — the clauses of
# `problem_spec_resolveRecord`:
#   (C0) ∃ res, result = Except.ok res                          [definedness]
#   (C1) result.payload = data.payload                              [frame]
#   (C2) (data.id = none ∧ hasKey = true) → result.id resolves the key
#        RELATIVE TO `store`: the key is the one `derive` yields for the record
#        ASSEMBLED ON `store`, looked up in `store`; found ⇒ some (coerceId
#        raw), not-found ⇒ data.id                          [load-bearing]
#   (C3) ¬(data.id = none ∧ hasKey = true) → result.id = data.id     [frame]
# Clause (C2) is the fix's pin on the STORE dimension: the store on which the key
# is DERIVED and the store in which it is LOOKED UP are both `store`, not the
# default. The prepatch derives the key relative to the default store and fails
# (C2) whenever the target store differs from the default — the multi-database
# bug. Clause (C0) is the fix's pin on the WHERE and ON-WHAT dimensions: because
# the derivation step is undefined off `hasKey` AND undefined off the record
# assembled on `store`, an impl that runs it anywhere else — or on anything else
# — has no key to show and cannot produce a record at all.
#
# ---------------------------------------------------------------------------
# FIFTH AUDIT NOTE — a DISCARDED derivation is not a run of it, and no spec can
# pretend otherwise. The boundary is drawn HERE, mechanically.
# ---------------------------------------------------------------------------
# The audit after the fourth note returned three rivals (`atk_2`, `atk_3`,
# `atk_11`) that VERIFIED and whose materialized diffs did not resolve — the
# hoisting shape again (PASS_TO_PASS 27/53) and the two probe shapes again
# (FAIL_TO_PASS 0/1). This time the finding was NOT a spec weakness, and the
# distinction is worth the space because it is the last one this carrier has to
# offer.
#
# All three of those Lean implementations write the extra derivation as a PURE
# LET whose value is dropped (`let _probe : Except Failure Key := derive obj`,
# and for the hoist `let keyOutcome := derive obj` evaluated above the guard but
# BOUND only inside it). In a pure total language that term is zeta-erased: it
# denotes nothing. Measured, not argued — with the frozen spec regions in scope:
#
#     example : implH = implG := rfl   -- hoist-as-value  (atk_2)
#     example : implP = implG := rfl   -- probe before     (atk_3)
#     example : implQ = implG := rfl   -- probe after      (atk_11)
#
# all three closed (`scripts/lean_verify.sh` exit 0). They ARE gold. No
# specification can accept gold and reject them, so a spec change is not merely
# unnecessary here, it is impossible: any obligation that rejected one would
# reject gold and the bundle would have no correct implementation at all.
#
# Their diffs did not resolve because those diffs are not transcriptions of those
# implementations. Python's call is an EFFECT: `obj.natural_key()` on a record
# whose references do not resolve raises, and the raise escapes whether or not
# the value is used. The faithful transcription of a DISCARDED derivation must
# therefore not let that failure escape — and when it does not, it resolves.
# Measured on fresh harness runs of the two faithful transcriptions:
#   * hoist-as-value (evaluate the step up front, capture the outcome, re-raise
#     it only inside the guard): FAIL_TO_PASS 1/1, PASS_TO_PASS 53/53 — RESOLVED.
#   * probe-with-value-dropped (`try: obj.natural_key() except Exception: pass`
#     before establishing the store): FAIL_TO_PASS 1/1, PASS_TO_PASS 53/53 —
#     RESOLVED.
# So verify ⇒ correct holds on both, and the earlier non-resolving runs measured
# a DIFFERENT program from the one the Lean side denotes.
#
# What this battery adds so the boundary is mechanical rather than a matter of
# reading: the three discarded-value shapes are shipped as POSITIVE controls
# (`pos-control-discarded-hoist`, `-discarded-probe-before`,
# `-discarded-probe-after`) that MUST verify, and each one carries an `_isGold`
# step inside its proof — a `have` that proves, by `rfl` alone, that its
# implementation is the frozen one applied pointwise. Their `←`-BOUND twins
# (`rej-derive-outside-guard`, `rej-probe-before-store`, `rej-probe-after-store`)
# must REJECT. Those six cases are the same six edits, differing only in whether
# the derivation is bound or dropped, and the battery now pins both sides:
# binding the step is what models running it, and dropping it models nothing.
# The spec view says so where the callee is introduced (`KeyDerivation`), and
# refinement.md states the correspondence as a refinement rule.
#
# ---------------------------------------------------------------------------
# FOURTH AUDIT NOTE — availability is STORE-RELATIVE, and why it had to be.
# ---------------------------------------------------------------------------
# The (C0) repair below (third audit note) closed the hoisting rival but left a
# second hole, which the next G-EQ audit walked straight through. `atk_7` and
# `atk_9` both VERIFIED and neither RESOLVED. Their content is
# `rej-probe-before-store` and `rej-probe-after-store`: keep gold's guard, gold's
# store establishment and gold's derivation exactly as they are, and merely run
# the derivation step ONE EXTRA TIME on a record that is still on the default
# store, throwing that result away. Measured on fresh harness runs: PASS_TO_PASS
# 53/53 — nothing unrelated regresses — but FAIL_TO_PASS 0/1, consistently over 3
# attempts. They break the very test the fix exists for, which is the opposite
# failure signature from the hoisting rival and is why the earlier repair did not
# anticipate them.
#
# The reason the spec could not see it: `derivationAvailability` asserted that
# under `hasKey` the step yields a key for EVERY record. That is false of the real
# callee and it was the load-bearing falsehood. `natural_key()` follows the
# record's references against the alias the record carries, so on a record still
# on the default store a reference to a row that lives only in the target store
# does not resolve — it raises. Confirmed directly, outside the harness, on the
# F2P's own model shape: the default-store call raises `Person.DoesNotExist` while
# the target-store call returns the key. So the old hypothesis handed the
# implementation a guarantee the repo does not offer, and an extra derivation off
# the target store became free.
#
# The repair is to assume availability only where the repo provides it: under
# `hasKey`, for the record assembled on `store`, and nowhere else. Clause (C0) is
# unchanged and now does the work in a second dimension — a step run on any other
# record has no key to show, so its failure propagates and no record comes back.
# What it cost, recorded rather than glossed:
#   * gold needed ONE line of proof change (the availability instance is now the
#     target record rather than a ∀ instantiated at it), and the prepatch twin
#     still fails — now for a stronger reason: it derives on the default-store
#     record, about which the hypothesis says nothing, so it fails (C0) as well as
#     (C2).
#   * every witness now proves the store-relative predicate at its own point; the
#     two new ones instantiate a step that is available on the target record and
#     UNAVAILABLE on any other, which is the regression scenario itself rather
#     than a contrivance.
#   * one positive control was ADDED to bound the strengthening:
#     `pos-control-double-derive` runs the step twice on the target record and
#     must verify. Without it, "reject an extra derivation" would be
#     indistinguishable from "reject a second derivation", and the latter would be
#     a syntactic counting rule rather than a property of the operation.
#   * the payload dimension of the new hypothesis is an UNDER-approximation (the
#     repo would resolve a key for other field data on the target store; the spec
#     declines to assume it). That direction only ever makes the obligation
#     harder, and its cost is measured: all five positives and the admissibility
#     instance still discharge it. See mapping.md.
#
# ---------------------------------------------------------------------------
# THIRD AUDIT NOTE — the (C0) repair, and what it cost the battery.
# ---------------------------------------------------------------------------
# A G-EQ audit produced a rival (`atk_10`) that VERIFIED against the previous
# frozen spec and did NOT resolve the instance: measured on a fresh harness run,
# FAIL_TO_PASS 1/1 but PASS_TO_PASS 27/53, with 26 named regressions (fixture
# loading for models that offer no identifying key at all). Its content is
# exactly `rej-derive-outside-guard` below — it hoists the assemble-and-derive
# prelude ABOVE the guard, so the derivation step runs for every record, including
# the models that have no such step. Gold runs it only inside the guard.
#
# The previous spec could not see that, for a structural reason worth recording:
# the derivation step was a TOTAL opaque function of (store, payload), so
# "derived a key here rather than there" had no observable consequence, and the
# postcondition was purely extensional over the returned record. The repair is
# not a syntactic ban on hoisting — it makes the callee's PARTIALITY part of the
# model (`KeyDerivation` returns `Except Failure Key`, `derivationAvailability`
# says where it is defined) and adds clause (C0), the obligation that assembling
# a record always yields a record. Gold discharges (C0) because it reaches the
# derivation only under `hasKey`, where availability guarantees a key; the hoisted
# rival cannot, because at `hasKey = false` availability forces the derivation to
# yield nothing and its result is a `Failure`. Two dodges were closed while
# choosing that shape: a pure `deriveKeyOn (hasKey : Bool)` lets an impl pass a
# literal `true` and hoist anyway, and leaving ANY total derivation in scope lets
# the impl compute the key outside the guard exactly as the rival does. Passing
# `derive` as an argument constrained only by the theorem's hypothesis closes
# both: the impl has no way to obtain a key except through the partial callee and
# no way to forge its availability.
#
# What the repair cost this battery, recorded rather than glossed:
#   * Every case was re-anchored and re-derived against the new carrier; all 18
#     were rebuilt with the real verifier and behaved as declared.
#   * The witnesses got STRONGER, not weaker. `derive` is now a binder, so a
#     witness supplies a concrete derivation step (`fun r => Except.ok [r.store]`
#     — a step that reads the record's store alias, which is the whole point of
#     (C2)) and PROVES `derivationAvailability` at it. So each counterexample
#     point is shown ADMISSIBLE for the frozen obligation, which the previous
#     witnesses could not state at all: they had to condition the store dimension
#     on hypotheses about an opaque `deriveKey`, and every alias was
#     computationally indistinguishable. Now the derive-store rivals are separated
#     by COMPUTATION (`["other"]` vs `["default"]`) and only the `lookupByKey` /
#     `coerceId` dimensions are still conditioned.
#   * The guard corner (data.id = none, hasKey = false) is now refuted by (C0)
#     rather than by (C3): any impl that runs the derivation there produces a
#     `Failure`, so it never reaches a frame violation. That is a strengthening,
#     but it means (C3) is pinned by rej-guard-narrowed and rej-inactive-id-frame
#     rather than by rej-guard-widened — see those cases' rationales.
#
# SECOND AUDIT NOTE (independent re-derivation, earlier pass — retained because
# its two repairs are still in the battery). Every case was rebuilt from scratch
# and behaved as declared; all statements byte-identical to the frozen one; all
# frozen spec regions byte-identical in every variant. The witness lane was
# re-derived with stronger instruments than the first pass used:
#   * For each reject case, GOLD WAS SHOWN TO SATISFY THE SPEC at exactly the
#     witness's own input (`example : problem_spec_resolveRecord <the witness
#     point> ... := correct_resolveRecord _ _ _ _ _`). That is the positive form
#     of the discrimination claim and is stronger than reading gold's error text:
#     gold's build cannot be failing for a syntactic reason at a point where the
#     spec is provably TRUE of it.
#   * The FORGERY test was run both ways (asserting the AGREEMENT claim the
#     witness denies): gold proves it, the rival does not. So every gold-side exit
#     code in this battery tracks the claim.
# Two defects were repaired in that pass and both survive here:
#   (iii) the ADMISSIBILITY lane had been recorded as inexpressible on a reason
#         that does not hold (see the omission list); it is expressible, it
#         builds, and it is case `admiss-f2p-shaped-input`.
#   (iv) the (id/hasKey) guard had FOUR corners and only three were visited; the
#         corner (id = some _, hasKey = true) is attacked by rej-guard-narrowed,
#         the complement of rej-guard-widened.
#
# FIRST AUDIT NOTE (independent re-derivation of this battery). Two defects were
# repaired rather than left implicit:
#   (i) both original positives are DEFINITIONALLY the frozen impl (they reduce to
#       the frozen goal and keep the frozen proof body verbatim), so neither could
#       have witnessed SPEC-TOO-STRONG. Two positives that are not definitionally
#       gold, and therefore carry their own proof bodies, were added.
#  (ii) the battery attacked only part of (C2)/(C1)/(C3): the coercion, the
#       not-found arm, the guard's hasKey conjunct, the inactive-branch payload
#       frame, and partial/miscomputed store association were unprobed. Six rivals
#       were added for those, each with a witness re-derived by hand (holds of the
#       rival, fails SEMANTICALLY on the frozen solution, hypotheses consistent).
#
# INPUT BINDERS of the spec predicate: `data` (its `id` and `payload`), `store`,
# `hasKey`, `derive`. The reject witnesses vary them across distinct points: the
# active-branch rivals hold `data.id = none, hasKey = true` at an available
# derivation and probe several distinct non-default target stores and payloads;
# the inactive-branch rivals hold `data.id = some 5, hasKey = false` at the
# unavailable derivation availability forces there; `rej-guard-widened` is refuted
# at `hasKey = false` WITH `data.id = none` and `rej-guard-narrowed` at
# `data.id = some 5` WITH `hasKey = true`. Those are ALL FOUR corners of the
# (id/hasKey) guard, so each conjunct is pinned by a rival that drops it. The
# derive-store and lookup-store arguments of (C2), both of (C2)'s arms, both frame
# clauses (each on both branches), and (C0) on both guard branches are exercised.
# The `derive` binder itself is varied three ways, one per shape the availability
# hypothesis admits: a step available everywhere (the active-branch witnesses), the
# step availability FORCES at `hasKey = false` (the inactive-branch witnesses), and
# a step available on the TARGET RECORD ONLY and nowhere else (the two probe
# witnesses). Only the third can refute an impl that derives a correct key and
# additionally derives off the target record, which is why it is in the battery.
#
# NOTE on alias variation: the store alias is now computationally observable in
# the derive dimension (`derive` is a binder, and the witnesses instantiate it
# with a step that reads `r.store`), so varying the literal across rivals is real
# coverage there. It is still HYGIENE only in the `lookupByKey` dimension, which
# remains opaque. Alias-SENSITIVITY is a property of an impl, so it is attacked by
# an impl that is alias-sensitive: `rej-alias-guarded` establishes the target
# store for only some aliases and is refuted at one the guard misses.
#
# OMITTED nagini cases and why (see `assessment` too):
#   * `pos-control-via-record-store` (nagini): INEXPRESSIBLE. It reads a SECOND
#     store binder that a precondition pins equal to the target. This carrier has
#     a single `store` binder and no precondition, so there is no second, pinned-
#     equal store to read instead — the case has no analogue rather than a hard
#     proof.
#   * `uniq-skip-assoc-keep-assert` (nagini's supporting near-miss): COLLAPSES on
#     this carrier. Its content is "derive against the wrong store while
#     separately *checking* the right one". A check is a statement, not a value,
#     and Lean is referentially transparent, so the analogue can only be a dead
#     binding in front of the default-store derivation — observationally IDENTICAL
#     to `rej-default-store-derive`, hence a vacuous duplicate rather than a rival.
#     Its live content (a partial / miscomputed store association) is instead
#     carried by `rej-alias-guarded` and `rej-offby-alias`.
#   * FRAME / permission-mutation: VACUOUS on lean — referentially transparent,
#     no aliasing / fractional permission to violate. The analogue here is the
#     frame CLAUSES (C1)/(C3), which ARE attacked by dedicated rivals
#     (payload-mutate, inactive-mutate, inactive-payload).
#   * DIVERGENCE / non-termination: VACUOUS on this bundle, and MEASURED rather
#     than asserted. The frozen solution sets no
#     `set_option loom.semantics.termination`, so there is no partial-semantics
#     escape under which a diverging impl could verify vacuously. Both ways of
#     writing one were built: (a) a plain self-recursive `def` fails ELABORATION
#     of the variant itself (`fail to show termination for
#     implementation_resolveRecord`), so the module never reaches the obligation
#     and — decisively — its WITNESS file does not compile either, meaning no
#     witness can be stated against it and the case is unshippable rather than
#     merely failing; (b) marking it `partial` makes the impl opaque, so
#     `unfold implementation_resolveRecord` fails and the rejection attests to
#     unfoldability, not to the spec. Neither is a refutable rival, so there is
#     nothing to ship in this lane on this carrier.
#   * AXIOM_TESTS: dropped; the axiom lane is G-AX's job. The frozen bundle
#     declares no `_prop` axiom — what the proof consumes about the derivation
#     step is a THEOREM HYPOTHESIS (`derivationAvailability`), discharged by
#     whoever instantiates the obligation, and the two opaque callees appear
#     identically in the spec and the impl. So there is no consumed-axiom
#     over-approximation for this gate to probe.
from pathlib import Path

INSTANCE = "django__django-15525"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — all strictly INSIDE the impl / proof regions of the frozen
# Solution.lean, each unique in the file.
# ---------------------------------------------------------------------------

# The frozen impl's assemble-and-derive prelude (impl region), which sits INSIDE
# the guard.
_GOLD_DERIVE = """    -- assemble the record; establish its target store before deriving the key
    let mut obj : Record := { payload := data.payload, store := defaultStore }
    obj := { obj with store := store }
    let key ← derive obj"""

# The single line that establishes the target store BEFORE deriving the key.
_ESTAB = "    obj := { obj with store := store }\n"

# The frozen impl's lookup/coerce match (impl region).
_GOLD_MATCH = """    match lookupByKey store key with
    | some raw => return { data with id := some (coerceId raw) }
    | none     => return data"""

# The found-case arm alone.
_FOUND = "    | some raw => return { data with id := some (coerceId raw) }"

# The impl's tail: the not-found arm followed by the outer fallthrough return.
_TAIL = """    | none     => return data
  return data"""

# The frozen proof body, verbatim (proof region). A positive whose reshape is not
# definitionally gold must REPROVE, which means swapping this out.
_GOLD_PROOF = """  intro data store hasKey derive havail
  unfold problem_spec_resolveRecord implementation_resolveRecord
  by_cases h : (data.id = none ∧ hasKey = true)
  · rw [if_pos h]
    obtain ⟨key, hk⟩ := havail.1 h.2
    simp only [hk, bind, Except.bind]
    cases hl : lookupByKey store key with
    | none =>
      refine ⟨⟨data, rfl⟩, ?_⟩
      intro res hres
      simp only [pure, Except.pure, Except.ok.injEq] at hres
      subst hres
      refine ⟨rfl, ?_, ?_⟩
      · intro _ key₁ hkey
        simp only [Except.ok.injEq] at hkey
        subst hkey
        rw [hl]
      · intro hc; exact absurd h hc
    | some raw =>
      refine ⟨⟨{ id := some (coerceId raw), payload := data.payload }, rfl⟩, ?_⟩
      intro res hres
      simp only [pure, Except.pure, Except.ok.injEq] at hres
      subst hres
      refine ⟨rfl, ?_, ?_⟩
      · intro _ key₁ hkey
        simp only [Except.ok.injEq] at hkey
        subst hkey
        rw [hl]
      · intro hc; exact absurd h hc
  · rw [if_neg h]
    simp only [bind, Except.bind, pure, Except.pure, Except.ok.injEq]
    refine ⟨⟨data, rfl⟩, ?_⟩
    intro res hres
    subst hres
    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩"""

# The guard line of the impl (impl region).
_GUARD = "  if data.id = none ∧ hasKey = true then\n"

# The frozen proof's `intro` line (proof region), unique in the file. The
# admissibility positive prepends a ground `have` in front of it, so the theorem
# STATEMENT and the spec view are both untouched.
_P_INTRO = "  intro data store hasKey derive havail\n"

# NOTE on the first two positives: their impls reduce (`obj.store` → `store`) to
# exactly the goal the frozen tactic script unfolds to, so they keep the frozen
# proof body byte-identical. That is honest but WEAK as a soundness control: an
# impl that is DEFINITIONALLY the frozen one cannot witness spec-too-strong,
# since it is the same term up to `rfl` and any spec gold satisfies it satisfies
# too. The two positives below (`-option-or`, `-guard-commuted`) are therefore the
# load-bearing ones: neither is definitionally gold (each needs its own proof
# body, which is why they carry proof-region surgery), so they genuinely test
# that the spec admits a correct impl the frozen tactic script does NOT close.


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-different but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-control-direct: assemble the record ALREADY established on the target
# store (construct with `store := store`) instead of building it on the default
# store and reassigning via `let mut`/`with`. Different executable shape — no
# mutable local, no field update — but the SAME observable: the derivation step is
# run on the record assembled on `store`, and it is still run only under the
# guard. Because `obj` reduces to that record in one step, the frozen proof body
# still closes verbatim; the proof is left untouched.
_POS_DIRECT = """    -- assemble the record already established on its target store
    let obj : Record := { payload := data.payload, store := store }
    let key ← derive obj"""

# pos-control-inline: drop the intermediate binding entirely and hand the
# derivation step the target-store record directly. Fewest moving parts; the
# observable is identical. The frozen proof body closes verbatim (the record is
# already in the shape the proof unfolds to).
_POS_INLINE = """    -- derive the key directly from the record assembled on the target store
    let key ← derive { payload := data.payload, store := store }"""

# pos-control-double-derive: run the derivation step on the target-store record
# TWICE and use the second key. Redundant, but CORRECT: every run is on the
# record the obligation's hypothesis speaks about, so each yields a key and the
# key used is still the spec's. This is the control that clause (C0) plus
# store-relative availability forbid running the step on the WRONG RECORD rather
# than running it more than once — the distinction the two probe rivals turn on.
# `obj` reduces to the target record and both runs rewrite with the same
# equation, so the frozen proof body closes verbatim.
_POS_DOUBLE_DERIVE = """    -- assemble the record, establish its target store, and run the derivation
    -- step on it TWICE (redundant, but every run is on the target record)
    let mut obj : Record := { payload := data.payload, store := defaultStore }
    obj := { obj with store := store }
    let _key₀ ← derive obj
    let key ← derive obj"""

# --- the three DISCARDED-VALUE positives (fifth audit note) ----------------
# Each is the same edit as one of the three reject cases it is paired with, with
# the extra derivation written as a dropped VALUE (`let _ := ...`) instead of a
# BOUND effect (`let _ ← ...`). A dropped term is zeta-erased, so each of these
# impls IS the frozen one; the `_isGold` step below proves exactly that by `rfl`,
# inside the proof, so the claim is checked by this gate rather than asserted.

# The `_isGold` step: prepended in front of the frozen proof's `intro` line, it
# states that the case's implementation is pointwise the frozen implementation
# and closes with `rfl` alone. If a case's impl were NOT definitionally gold this
# `have` would fail to elaborate and the case would not verify, so no case can
# claim gold-hood it does not have.
_ISGOLD = """  have _isGold : ∀ (d : Data) (s : Store) (hk : Bool) (dv : KeyDerivation),
      implementation_resolveRecord d s hk dv
        = (do
            if d.id = none ∧ hk = true then
              let mut o : Record := { payload := d.payload, store := defaultStore }
              o := { o with store := s }
              let k ← dv o
              match lookupByKey s k with
              | some raw => return { d with id := some (coerceId raw) }
              | none     => return d
            return d) := fun _ _ _ _ => rfl
"""

# pos-control-discarded-hoist: the twin of rej-derive-outside-guard. Assemble the
# record, establish its store and EVALUATE the derivation step above the guard —
# but bind it only inside the guard, so nothing is run outside. Must verify.
_POS_DISCARD_HOIST = """  -- assemble the record, establish its target store and evaluate the model's
  -- key-derivation step as a VALUE up front; the guard then decides whether to
  -- BIND it. Evaluating a term is not running a step: this impl is the frozen
  -- one (see the proof's `_isGold` step).
  let mut obj : Record := { payload := data.payload, store := defaultStore }
  obj := { obj with store := store }
  let keyOutcome : Except Failure Key := derive obj
  if data.id = none ∧ hasKey = true then
    let key ← keyOutcome
"""

# pos-control-discarded-probe-before: the twin of rej-probe-before-store, with the
# extra derivation's value DROPPED rather than bound. Must verify.
_POS_DISCARD_PROBE_BEFORE = """    -- assemble the record; establish its target store before deriving the key
    let mut obj : Record := { payload := data.payload, store := defaultStore }
    -- ALSO name the derivation step's value on the record while it is still on
    -- the default store, and DROP it (a dropped value is not a run)
    let _probe : Except Failure Key := derive obj
    obj := { obj with store := store }
    let key ← derive obj"""

# pos-control-discarded-probe-after: the twin of rej-probe-after-store, with the
# extra derivation's value DROPPED rather than bound. Must verify.
_POS_DISCARD_PROBE_AFTER = _GOLD_DERIVE + """
    -- ALSO name the derivation step's value on a freshly assembled record that
    -- is back on the default store, and DROP it
    let _probe : Except Failure Key := derive { payload := data.payload, store := defaultStore }"""

# pos-control-option-or: resolve the id FUNCTIONALLY — map the coercion over the
# looked-up option and fall back to the existing id via `Option.or` — instead of
# dispatching on a `match`. Same observable as gold on the active branch (found ⇒
# some (coerceId raw), not-found ⇒ data.id), and the derivation is still run only
# under the guard so (C0) still holds. But it is NOT definitionally gold: the
# frozen `rfl`-shaped arms do not close it, so this positive needs its own proof
# body. That is what makes it a real soundness control.
_POS_OPTION_OR = """    -- resolve the id functionally rather than by matching
    let key ← derive { payload := data.payload, store := store }
    return { data with id := ((lookupByKey store key).map coerceId).or data.id }"""

_POS_OPTION_OR_PROOF = """  intro data store hasKey derive havail
  unfold problem_spec_resolveRecord implementation_resolveRecord
  by_cases h : (data.id = none ∧ hasKey = true)
  · rw [if_pos h]
    obtain ⟨key, hk⟩ := havail.1 h.2
    simp only [hk, bind, Except.bind, pure, Except.pure]
    refine ⟨⟨_, rfl⟩, ?_⟩
    intro res hres
    simp only [Except.ok.injEq] at hres
    subst hres
    refine ⟨rfl, ?_, ?_⟩
    · intro _ key₁ hkey
      simp only [Except.ok.injEq] at hkey
      subst hkey
      cases hl : lookupByKey store key with
      | none => simp [hl]
      | some raw => simp [hl]
    · intro hc; exact absurd h hc
  · rw [if_neg h]
    simp only [bind, Except.bind, pure, Except.pure, Except.ok.injEq]
    refine ⟨⟨data, rfl⟩, ?_⟩
    intro res hres
    subst hres
    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩"""

# pos-control-guard-commuted: test the guard's two conditions in the OTHER order
# (`hasKey = true ∧ data.id = none`). Logically the same condition — so the
# derivation is still run exactly where it is defined — but `∧` is not
# commutative up to `rfl`, so the frozen script's `rw [if_pos h]`/`absurd` steps
# no longer line up and the impl must be reproven: a correct reshape the frozen
# tactic form rejects, which is exactly what a soundness control should be.
_POS_GUARD_COMMUTED = "  if hasKey = true ∧ data.id = none then\n"

_POS_GUARD_COMMUTED_PROOF = """  intro data store hasKey derive havail
  unfold problem_spec_resolveRecord implementation_resolveRecord
  by_cases h : (hasKey = true ∧ data.id = none)
  · rw [if_pos h]
    have h' : data.id = none ∧ hasKey = true := ⟨h.2, h.1⟩
    obtain ⟨key, hk⟩ := havail.1 h.1
    simp only [hk, bind, Except.bind]
    cases hl : lookupByKey store key with
    | none =>
      refine ⟨⟨data, rfl⟩, ?_⟩
      intro res hres
      simp only [pure, Except.pure, Except.ok.injEq] at hres
      subst hres
      refine ⟨rfl, ?_, ?_⟩
      · intro _ key₁ hkey
        simp only [Except.ok.injEq] at hkey
        subst hkey
        rw [hl]
      · intro hc; exact absurd h' hc
    | some raw =>
      refine ⟨⟨{ id := some (coerceId raw), payload := data.payload }, rfl⟩, ?_⟩
      intro res hres
      simp only [pure, Except.pure, Except.ok.injEq] at hres
      subst hres
      refine ⟨rfl, ?_, ?_⟩
      · intro _ key₁ hkey
        simp only [Except.ok.injEq] at hkey
        subst hkey
        rw [hl]
      · intro hc; exact absurd h' hc
  · rw [if_neg h]
    simp only [bind, Except.bind, pure, Except.pure, Except.ok.injEq]
    refine ⟨⟨data, rfl⟩, ?_⟩
    intro res hres
    subst hres
    refine ⟨rfl, ?_, fun _ => rfl⟩
    intro hc
    exact absurd (⟨hc.2, hc.1⟩ : hasKey = true ∧ data.id = none) h"""

# The ADMISSIBILITY ground instance, prepended to the frozen tactic body. It
# discharges the whole predicate at one concrete F2P-shaped point — no identifier
# yet, key support on, a NON-DEFAULT target store alias, and a derivation step
# that is AVAILABLE there (proved, not assumed) — before the general obligation is
# closed verbatim below it.
_GROUND = """  -- ADMISSIBILITY. The obligation must be SATISFIABLE at an F2P-shaped input:
  -- a record with no identifier yet, key support on, a NON-DEFAULT target store
  -- alias, and a derivation step that is available there. `_avail` establishes
  -- that the point is one the obligation actually speaks about (an unavailable
  -- derivation under `hasKey = true` would be excluded by the hypothesis), and
  -- `_ground` discharges all four clauses at it, splitting both arms of the
  -- carrier's lookup. Both are `have`s inside the existing tactic body, so the
  -- theorem STATEMENT and the spec view are untouched.
  have _avail : derivationAvailability { id := none, payload := ["title"] } "other"
      true (fun r => Except.ok [r.store]) :=
    ⟨fun _ => ⟨["other"], rfl⟩, fun hc => absurd hc (by decide)⟩
  have _ground : problem_spec_resolveRecord
      { id := none, payload := ["title"] } "other" true (fun r => Except.ok [r.store])
      (implementation_resolveRecord { id := none, payload := ["title"] } "other" true
        (fun r => Except.ok [r.store])) := by
    cases hl : lookupByKey "other" ["other"] with
    | none =>
      simp [problem_spec_resolveRecord, implementation_resolveRecord, bind,
        Except.bind, pure, Except.pure, hl]
    | some raw =>
      simp [problem_spec_resolveRecord, implementation_resolveRecord, bind,
        Except.bind, pure, Except.pure, hl]
"""


# ===========================================================================
# UNIQUENESS rivals (must reject; else SPEC-TOO-WEAK). Each carries a witness
# proving it violates the spec at a concrete input — checked in a file with the
# frozen obligation removed, so it must ELABORATE against the rival and FAIL on
# the frozen solution.
# ===========================================================================

# rej-default-store-derive: THE prepatch bug. The manifest removes the line that
# establishes the target store (`_ESTAB`), so the key is derived from a record
# still on the DEFAULT store rather than on `store` — attacks (C2)'s derive-store.
# (Built inline in SPEC_TESTS via `_swap(_BASE, _ESTAB, "")`.)

# rej-lookup-default: derive relative to `store` (correct) but LOOK UP the key in
# the DEFAULT store instead of `store`. A distinct half of (C2): the lookup store
# must also be `store`. Attacks (C2)'s lookup-store argument.
_REJ_LOOKUP_DEFAULT = _GOLD_MATCH.replace(
    "match lookupByKey store key", "match lookupByKey defaultStore key")

# rej-ignore-found: derive and look up correctly, but NEVER apply a found id —
# always return the record unchanged in the active branch. Attacks (C2)'s
# found ⇒ some (coerceId raw) obligation.
_REJ_IGNORE_FOUND = """    let _ := lookupByKey store key
    return data"""

# rej-payload-mutate: in the found case, also ALTER the descriptive payload.
# Attacks the frame clause (C1) result.payload = data.payload.
_REJ_PAYLOAD_MUTATE = _FOUND.replace(
    "return { data with id := some (coerceId raw) }",
    "return { data with id := some (coerceId raw), payload := data.payload ++ [\"x\"] }")

# rej-inactive-mutate: on the INACTIVE branch (record already identified, or no
# key support) overwrite the identifier instead of leaving it. Attacks the frame
# clause (C3) result.id = data.id.
_REJ_INACTIVE_MUTATE = """    | none     => return data
  return { data with id := some 0 }"""

# rej-skip-coerce: derive and look up correctly and DO apply the found id, but
# apply the RAW stored id without coercing it to the field's identifier type.
# Attacks the `some (coerceId raw)` half of (C2)'s found arm, which every other
# rival either satisfies or never reaches.
_REJ_SKIP_COERCE = "    | some raw => return { data with id := some raw }"

# rej-notfound-clobber: the not-found arm invents an identifier instead of leaving
# the record's own. Attacks (C2)'s `none ⇒ data.id` arm — the other half of the
# lookup dispatch, which no other rival reaches (they are all refuted on found).
_REJ_NOTFOUND_CLOBBER = _GOLD_MATCH.replace(
    "| none     => return data", "| none     => return { data with id := some 0 }")

# rej-guard-widened: resolve whenever the record has no identifier, IGNORING
# whether the model supports identifying keys. Attacks (C0) at the guard corner
# `data.id = none ∧ hasKey = false`: the derivation step is not defined there, so
# running it yields no key and no record.
_REJ_GUARD_WIDENED = "  if data.id = none then\n"

# rej-guard-narrowed: resolve whenever the model supports identifying keys,
# IGNORING whether the record already carries an identifier — the COMPLEMENT of
# rej-guard-widened, which drops the other conjunct. Attacks (C3) at the corner
# `data.id = some _ ∧ hasKey = true`, where the derivation IS available (so the
# rival produces a record and the refutation is a frame violation, not a
# definedness one).
_REJ_GUARD_NARROWED = "  if hasKey = true then\n"

# rej-derive-outside-guard: hoist the whole assemble-and-derive prelude ABOVE the
# guard, so the derivation step is run for EVERY record and only its RESULT is
# used under the guard. This is the shape of the audit rival that verified against
# the pre-(C0) spec and did not resolve the instance; see the third audit note.
# Attacks (C0).
_REJ_DERIVE_OUTSIDE_GUARD = """  -- assemble the record and derive its identifying key BEFORE testing the
  -- guard, so the derivation step is run for every record
  let mut obj : Record := { payload := data.payload, store := defaultStore }
  obj := { obj with store := store }
  let key ← derive obj
  if data.id = none ∧ hasKey = true then
"""

# rej-alias-guarded: establish the target store on the assembled record for only
# SOME aliases and fall back to the default for the rest — a partial fix whose
# store association is guarded behind a predicate on the alias that does not
# always hold. This is the port's analogue of nagini's partial-domain rivals, and
# the only rival for which the store ALIAS is observably load-bearing (the impl,
# not the witness, distinguishes aliases).
_REJ_ALIAS_GUARDED = (
    "    obj := { obj with store :=\n"
    "      if store = defaultStore ∨ store = \"other\" then store else defaultStore }\n")

# rej-offby-alias: establish a MISCOMPUTED alias derived from the target one
# (perturbed) rather than the target itself, so the key is derived relative to a
# store that exists nowhere. Distinct from rej-default-store-derive: the record IS
# associated, just with the wrong alias, so a patch that "sets the store" but
# computes it wrongly is caught.
_REJ_OFFBY_ALIAS = '    obj := { obj with store := store ++ "!" }\n'

# rej-probe-before-store: keep gold's fixed derivation EXACTLY as it is, and add
# one extra run of the derivation step on the record BEFORE its target store is
# established, discarding its result. Nothing about the key gold uses changes.
# This is the shape of the second audit rival (atk_7).
_REJ_PROBE_BEFORE = """    -- assemble the record; establish its target store before deriving the key
    let mut obj : Record := { payload := data.payload, store := defaultStore }
    -- ALSO run the derivation step once on the record while it is still on the
    -- default store, and throw that result away
    let _probe ← derive obj
    obj := { obj with store := store }
    let key ← derive obj"""

# rej-probe-after-store: the same extra run placed AFTER gold's correct
# derivation, on a freshly assembled record that is back on the default store.
# This is the shape of the third audit rival (atk_9); it is a distinct impl from
# rej-probe-before-store (the correct key is derived first, so an
# order-of-operations reading of the fix is satisfied).
_REJ_PROBE_AFTER = _GOLD_DERIVE + """
    -- ALSO re-run the derivation step on a freshly assembled record that is
    -- back on the default store, and throw that result away
    let _probe ← derive { payload := data.payload, store := defaultStore }"""

# rej-inactive-payload: on the INACTIVE branch, alter the descriptive payload.
# Attacks (C1) OFF the found arm — rej-payload-frame only exercises the frame
# inside the active branch's found case.
_REJ_INACTIVE_PAYLOAD = """    | none     => return data
  return { data with payload := data.payload ++ ["x"] }"""


# ---------------------------------------------------------------------------
# Witnesses.
#
# `derive` is a BINDER of the spec predicate, so every witness instantiates it
# CONCRETELY and PROVES `derivationAvailability` at that instantiation — the first
# conjunct of each witness statement. That matters twice over: the frozen
# obligation only speaks about available derivations, so a refutation at an
# inadmissible one would attribute nothing to the spec; and it makes the store
# dimension of (C2) computational rather than conditioned. The step used for the
# available case is `fun r => Except.ok [r.store]`: it READS the record's store
# alias, which is exactly the dependence (C2) is about, so a rival that assembles
# the record on the wrong store yields a literally different key (`["other"]` vs
# `["default"]`). At `hasKey = false` availability FORCES the step to yield
# nothing, so those witnesses use the failing step and need no hypotheses at all.
#
# `lookupByKey` and `coerceId` are still opaque, so witnesses that attack those
# dimensions CONDITION on them: each binds at most the hypotheses its refutation
# needs, kept jointly satisfiable (they constrain DIFFERENT opaque points, and the
# gate's consistency probe is run over exactly these binders).
# ---------------------------------------------------------------------------
_D_OK = "(fun r => Except.ok [r.store])"
_AVAIL_OK = "⟨fun _ => ⟨_, rfl⟩, fun hc => absurd hc (by decide)⟩"
_D_ERR = "(fun _ => Except.error Failure.keyDerivationUnavailable)"
_AVAIL_ERR = "⟨fun hc => absurd hc (by decide), fun _ _ => rfl⟩"

# The derivation step used by the two OFF-TARGET-RECORD witnesses: available on
# records carrying the target alias and UNAVAILABLE on every other record. That
# is not a contrivance — it is the regression scenario itself (the key follows a
# reference to a record that lives only in the target store, so on any other
# alias there is nothing to resolve), and it is admissible for the frozen
# obligation, which assumes availability ONLY on the record assembled for
# `store`. Both witnesses that use it target store "other".
_D_TARGET_ONLY = ('(fun r => if r.store = "other" then Except.ok [r.store]\n'
                  "      else Except.error Failure.keyDerivationUnavailable)")
_AVAIL_TARGET_ONLY = '⟨fun _ => ⟨["other"], by simp⟩, fun hc => absurd hc (by decide)⟩'

_SIMP = ("simp [problem_spec_resolveRecord, implementation_resolveRecord, bind,\n"
         "    Except.bind, pure, Except.pure")


def _refute(binders, ident, payload, store, has_key, derive, avail, extra=""):
    """`derivationAvailability … ∧ ¬ problem_spec_… ` at one concrete point.

    The first conjunct shows the point is one the frozen obligation speaks about;
    the second is the refutation. Stated positively (rather than as
    `¬ (avail ∧ spec)`, which could be discharged by refuting availability) so
    both halves must genuinely be proven.
    """
    data = f"{{ id := {ident}, payload := {payload} }}"
    head = f"example {binders}:\n" if binders else "example :\n"
    return (
        f"{head}"
        f"    derivationAvailability {data} {store} {has_key} {derive} ∧\n"
        f"    ¬ problem_spec_resolveRecord {data} {store} {has_key} {derive}\n"
        f"        (implementation_resolveRecord {data} {store} {has_key}\n"
        f"          {derive}) := by\n"
        f"  refine ⟨{avail}, ?_⟩\n"
        f"  {_SIMP}{extra}]")


def _witness_ok(binders, store, payload, ident="none", extra=""):
    """A refutation at an AVAILABLE derivation step (`hasKey = true`)."""
    return _refute(binders, ident, payload, store, "true", _D_OK, _AVAIL_OK, extra)


def _witness_target_only(store, payload, ident="none"):
    """A refutation at a derivation step available ONLY on the target record.

    Used by the two OFF-TARGET-RECORD rivals. `hasKey = true`, so the step is
    available where the obligation says it is, and unavailable on every record
    carrying another alias — which is why an impl that runs it on the
    default-store record comes back with no record at all. Needs `defaultStore`
    in the simp set (like `_W_ALIAS_GUARDED`): the rival's off-target record is
    built FROM that constant, so deciding the step's own alias test requires its
    value. Binds no hypotheses — everything here is decided by computation.
    """
    return _refute("", ident, payload, store, "true", _D_TARGET_ONLY,
                   _AVAIL_TARGET_ONLY, extra=", defaultStore")


def _witness_err(store, payload, ident):
    """A refutation at the UNAVAILABLE derivation step `hasKey = false` forces.

    No hypotheses: the failing step is decided by computation, so these witnesses
    bind nothing and the gate runs no consistency probe over them (there is
    nothing to be inconsistent).
    """
    return _refute("", ident, payload, store, "false", _D_ERR, _AVAIL_ERR)


# rej-default-store-derive: the rival assembles the record on `defaultStore`, so
# its derivation yields ["default"]; the spec's is ["other"]. Separate the two
# lookups: the store-relative key is found (some 7), the default-relative one is
# not. Spec then demands id = some (coerceId 7); the rival returns none.
_W_DEFAULT_STORE_DERIVE = _witness_ok(
    '(h1 : lookupByKey "other" ["other"] = some 7)\n'
    '    (h2 : lookupByKey "other" [defaultStore] = none) ',
    '"other"', '["p"]', extra=", h1, h2")

# rej-lookup-default: both sides derive ["replica"]; the rival looks that key up
# in the DEFAULT store. Separate the two lookups of the SAME key: found in
# "replica", not found in the default.
_W_LOOKUP_DEFAULT = _witness_ok(
    '(h1 : lookupByKey "replica" ["replica"] = some 7)\n'
    '    (h2 : lookupByKey defaultStore ["replica"] = none) ',
    '"replica"', '["title", "v2"]', extra=", h1, h2")

# rej-ignore-found: one hypothesis — the store-relative lookup is found. Spec ⇒
# id = some (coerceId 7); the rival returns the record unchanged (id = none).
_W_IGNORE_FOUND = _witness_ok(
    '(h1 : lookupByKey "shard1" ["shard1"] = some 7) ',
    '"shard1"', '["a", "b"]', extra=", h1")

# rej-skip-coerce: two hypotheses at DIFFERENT opaque points — the lookup is
# found with raw id 7, and the coercion is not the identity AT 7. Spec ⇒ id =
# some (coerceId 7); rival ⇒ some 7. Jointly satisfiable: `lookupByKey` and
# `coerceId` are independent opaque constants, so no tactic derives False.
_W_SKIP_COERCE = _witness_ok(
    '(h1 : lookupByKey "other" ["other"] = some 7)\n'
    '    (h2 : (7 : Int) ≠ coerceId 7) ',
    '"other"', '["p"]', extra=", h1, h2")

# rej-notfound-clobber: one hypothesis forcing the NOT-FOUND arm. Spec (C2) then
# demands id = data.id = none; the rival returns some 0.
_W_NOTFOUND_CLOBBER = _witness_ok(
    '(h1 : lookupByKey "other" ["other"] = none) ',
    '"other"', '["p"]', extra=", h1")

# rej-guard-widened: refuted at hasKey = FALSE with id = none — the guard corner
# no other rival visits. The rival enters its widened branch and runs a
# derivation step that is not defined there, so it yields no key and the
# operation comes back with no record at all: (C0) fails. Decided by computation.
_W_GUARD_WIDENED = _witness_err('"other"', '["p"]', "none")

# rej-guard-narrowed: refuted at (id = some 5, hasKey = true), where the
# derivation IS available — so the rival does produce a record and the violation
# is a FRAME one. Spec (C3) demands result.id = data.id = some 5; the rival takes
# its narrowed branch and returns some (coerceId 7). Two hypotheses at
# independent opaque points (the lookup, and the coercion's value at 7 versus the
# record's own identifier), so they are jointly satisfiable.
_W_GUARD_NARROWED = _witness_ok(
    '(h1 : lookupByKey "other" ["other"] = some 7)\n'
    '    (h2 : coerceId 7 ≠ 5) ',
    '"other"', '["p"]', ident="some 5", extra=", h1, h2")

# rej-derive-outside-guard: refuted at (id = some 5, hasKey = false) — a point
# where rej-guard-widened behaves CORRECTLY (its guard is false there too), so
# the two cases are refuted at different points. The rival derives before testing
# the guard at all, so it runs the unavailable step and (C0) fails. Decided by
# computation.
_W_DERIVE_OUTSIDE_GUARD = _witness_err('"other"', '["p"]', "some 5")

# rej-alias-guarded: refuted at an alias the rival's guard MISSES, so it assembles
# the record on the default store. Same separation as the derive-store witness,
# but the discriminating fact lives in the IMPL's alias guard. This is the one
# witness that must unfold `defaultStore`: the rival's own guard COMPARES the
# target alias against it, so deciding that guard requires its value, and h2
# therefore names that value ("default") rather than the constant.
_W_ALIAS_GUARDED = _witness_ok(
    '(h1 : lookupByKey "replica" ["replica"] = some 7)\n'
    '    (h2 : lookupByKey "replica" ["default"] = none) ',
    '"replica"', '["q"]', extra=", defaultStore, h1, h2")

# rej-offby-alias: separate the target-relative key from the perturbed-alias key.
# The second hypothesis names the NORMALIZED literal, which is what the rival's
# impl reduces to.
_W_OFFBY_ALIAS = _witness_ok(
    '(h1 : lookupByKey "other" ["other"] = some 7)\n'
    '    (h2 : lookupByKey "other" ["other!"] = none) ',
    '"other"', '["p"]', extra=", h1, h2")

# rej-payload-mutate: attack the frame conjunct (C1). On the found case the
# rival's payload is data.payload ++ ["x"] ≠ data.payload. One hypothesis forces
# the found arm.
_W_PAYLOAD_MUTATE = _witness_ok(
    '(h1 : lookupByKey "analytics" ["analytics"] = some 7) ',
    '"analytics"', '["k"]', extra=", h1")

# rej-probe-before-store / rej-probe-after-store: refuted at the F2P-shaped point
# (id = none, hasKey = true, target store "other") with a derivation step that is
# available on the target record and unavailable on any other — the regression
# scenario itself. Each rival runs the step once on a default-store record, so it
# comes back with no record and (C0) fails; gold runs it only on the target
# record. Different payloads, so the two are refuted at different points.
_W_PROBE_BEFORE = _witness_target_only('"other"', '["p"]')
_W_PROBE_AFTER = _witness_target_only('"other"', '["nk", "v2"]')

# rej-inactive-payload / rej-inactive-id-frame: decidable literals on the
# inactive branch (id = some 5, hasKey = false, the failing derivation step).
# Neither rival runs the step there, so both produce a record and the violation is
# a frame one: (C1) for the payload, (C3) for the identifier.
_W_INACTIVE_PAYLOAD = _witness_err('"backup"', '["z"]', "some 5")
_W_INACTIVE_MUTATE = _witness_err('"backup"', '["z"]', "some 5")


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROLS (soundness) -----------------------------------
    {
        "id": "pos-control-direct-construct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_DERIVE, _POS_DIRECT),
        "rationale": (
            "Structurally-different CORRECT impl: assemble the record ALREADY "
            "established on the target store (construct with `store := store`) "
            "instead of building it on the default store and reassigning via a "
            "mutable local + field update. The derivation step is still run on "
            "the record assembled on `store`, so clause (C2) holds; it is still "
            "run only under the guard, so (C0) holds; the payload and "
            "inactive-branch frames are untouched. `obj` reduces to that record "
            "in one step so the frozen proof body closes verbatim (proof left "
            "unchanged). CAVEAT on its strength: because it reduces to the frozen "
            "term, this reshape is DEFINITIONALLY gold, so on its own it could "
            "not witness SPEC-TOO-STRONG — it is a cheap smoke test that the "
            "surgery is well-formed. The load-bearing soundness controls are "
            "pos-control-option-or and pos-control-guard-commuted, which are not "
            "definitionally gold and must be reproven."
        ),
    },
    {
        "id": "pos-control-inline-derive",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_DERIVE, _POS_INLINE),
        "rationale": (
            "Structurally-different CORRECT impl with the fewest moving parts: "
            "drop the intermediate binding entirely and hand the derivation step "
            "the target-store record directly. The observable is byte-identical "
            "to gold's, so (C2) holds, the step is still run only under the guard "
            "so (C0) holds, and both frame clauses are trivially preserved. The "
            "frozen proof body closes verbatim. Same CAVEAT as "
            "pos-control-direct-construct: byte-identical observable means "
            "DEFINITIONALLY gold, so this case confirms the surgery is well-formed "
            "rather than probing spec strength; see pos-control-option-or / "
            "-guard-commuted for that."
        ),
    },
    {
        "id": "pos-control-option-or",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_DERIVE + "\n" + _GOLD_MATCH, _POS_OPTION_OR),
            _GOLD_PROOF, _POS_OPTION_OR_PROOF),
        "rationale": (
            "LOAD-BEARING soundness control. Resolves the identifier "
            "FUNCTIONALLY — `((lookupByKey store key).map coerceId).or data.id` — "
            "instead of dispatching on a `match`. Observably identical to gold on "
            "both arms of (C2) (found ⇒ some (coerceId raw); not-found ⇒ falls "
            "back to data.id, which is `none` on this branch), the derivation step "
            "is still run only under the guard so (C0) holds, and both frames are "
            "untouched. Crucially it is NOT definitionally gold: the frozen "
            "script's `rfl` arms do not close it, so the case carries its own "
            "proof body. A correct impl the frozen tactic form rejects but the "
            "SPEC accepts — if it could not verify, the spec would be "
            "SPEC-TOO-STRONG (it would be pinning the frozen syntactic shape "
            "rather than the behavior)."
        ),
    },
    {
        "id": "pos-control-guard-commuted",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GUARD, _POS_GUARD_COMMUTED),
            _GOLD_PROOF, _POS_GUARD_COMMUTED_PROOF),
        "rationale": (
            "LOAD-BEARING soundness control. Tests the two guard conditions in "
            "the OPPOSITE order (`hasKey = true ∧ data.id = none`). The condition "
            "is logically the same — so the derivation step is still run exactly "
            "where availability defines it, and every clause still holds — but "
            "`∧` does not commute up to `rfl`: the frozen script's "
            "`rw [if_pos h]` and `absurd` steps no longer line up, so this must "
            "be reproven (own proof body, with the conjuncts swapped back where "
            "the spec's guard is consulted). Confirms the spec constrains the "
            "guard's MEANING and not the frozen conjunct order; must verify (else "
            "SPEC-TOO-STRONG). It is also the control for (C0) being a behavioral "
            "obligation rather than a syntactic one: (C0) is discharged here by a "
            "guard that is not even written in the frozen order."
        ),
    },

    {
        "id": "pos-control-double-derive",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_DERIVE, _POS_DOUBLE_DERIVE),
        "rationale": (
            "Structurally-different CORRECT impl that runs the derivation step "
            "TWICE on the target-store record and uses the second key. Redundant "
            "but correct: every run is on the record the availability hypothesis "
            "speaks about, so each yields a key, (C0) holds, and the key used is "
            "still the spec's, so (C2) holds. This is the CONTROL FOR THE (C0) "
            "REPAIR NOT BEING A COUNTING RULE: the two probe rivals are rejected "
            "for running the step on the wrong RECORD, not for running it more than "
            "once, and this case is what distinguishes those two readings. It is "
            "definitionally close to gold (both runs rewrite with the same "
            "equation, so the frozen proof body closes verbatim), which is why it "
            "is a cheap control rather than a load-bearing one — the load-bearing "
            "soundness controls remain pos-control-option-or and "
            "pos-control-guard-commuted."
        ),
    },

    {
        "id": "pos-control-discarded-hoist",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GUARD + _GOLD_DERIVE + "\n", _POS_DISCARD_HOIST),
            _P_INTRO, _ISGOLD + _P_INTRO),
        "rationale": (
            "BOUNDARY CONTROL for the (C0) obligation, and the twin of "
            "rej-derive-outside-guard: the same edit, with the hoisted derivation "
            "EVALUATED as a value above the guard and BOUND only inside it. It "
            "must verify, and not because the spec is weak — because it IS gold. "
            "A term whose value is dropped is zeta-erased in a pure total "
            "language, so this impl is the frozen one, and the case PROVES that "
            "here: its proof opens with an `_isGold` step that closes "
            "`implementation_resolveRecord d s hk dv = <the frozen body>` by "
            "`rfl` alone, pointwise. No obligation can reject this and keep gold, "
            "so a G-EQ rival of this shape is not a spec-too-weak finding: it is "
            "an unfaithful transcription, because the real call is an EFFECT that "
            "raises whether or not its value is used. Measured: the FAITHFUL "
            "transcription — evaluate the step up front, capture the outcome, "
            "re-raise it only inside the guard — RESOLVES (FAIL_TO_PASS 1/1, "
            "PASS_TO_PASS 53/53 on a fresh harness run), so verify ⇒ correct "
            "holds on it. What the spec does reject is the BOUND hoist, where the "
            "failure propagates: rej-derive-outside-guard."
        ),
    },
    {
        "id": "pos-control-discarded-probe-before",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_DERIVE, _POS_DISCARD_PROBE_BEFORE),
            _P_INTRO, _ISGOLD + _P_INTRO),
        "rationale": (
            "BOUNDARY CONTROL, twin of rej-probe-before-store: the extra "
            "derivation on the not-yet-established record with its value DROPPED "
            "instead of bound. Must verify, and its `_isGold` proof step shows "
            "why by `rfl` — it is the frozen implementation. Measured: the "
            "faithful transcription of a dropped call (`try: obj.natural_key() "
            "except Exception: pass` before the store is established) RESOLVES — "
            "FAIL_TO_PASS 1/1, PASS_TO_PASS 53/53 on a fresh harness run. The "
            "shape the spec must and does reject is the BOUND one, where the "
            "extra step's failure escapes: rej-probe-before-store. Together the "
            "pair states the refinement rule mechanically — binding the step "
            "models running it, dropping its value models nothing."
        ),
    },
    {
        "id": "pos-control-discarded-probe-after",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _GOLD_DERIVE, _POS_DISCARD_PROBE_AFTER),
            _P_INTRO, _ISGOLD + _P_INTRO),
        "rationale": (
            "BOUNDARY CONTROL, twin of rej-probe-after-store: gold's derivation "
            "followed by a DROPPED evaluation of the step on a freshly assembled "
            "default-store record. Must verify; `_isGold` proves it is the frozen "
            "implementation by `rfl`. Shipped alongside the -probe-before twin "
            "because the two rivals were reported as distinct findings on distinct "
            "audits, and the boundary has to hold for both orders. The BOUND twin "
            "is rejected (rej-probe-after-store); this one cannot be, and a rival "
            "of this shape whose materialized diff lets the dropped call raise is "
            "measuring a program the Lean side does not denote."
        ),
    },

    # --- ADMISSIBILITY (must verify; else the obligation is unsatisfiable at
    # exactly an F2P-shaped input — this carrier's analogue of
    # PRECOND-TOO-STRONG) ---------------------------------------------------
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _GROUND + _P_INTRO),
        "rationale": (
            "ADMISSIBILITY. The frozen obligation's only hypothesis is "
            "`derivationAvailability`, so PRECOND-TOO-STRONG has a literal "
            "analogue here AND the total-carrier one: the hypothesis could be "
            "unsatisfiable, or the four clauses could be jointly unsatisfiable, at "
            "exactly an F2P-shaped input. This case rules out both at one concrete "
            "point — a record with no identifier yet (id = none), key support on "
            "(hasKey = true), a NON-DEFAULT target store alias (the regression "
            "shape), and a derivation step that is AVAILABLE there. `_avail` PROVES "
            "the hypothesis at that step (so the point is one the obligation "
            "actually speaks about, which matters now that (C0) is stated over "
            "availability), and `_ground` discharges the predicate there on its "
            "own, splitting both arms of the carrier's lookup, before the frozen "
            "obligation is closed verbatim. If either could not be established, "
            "the spec would be vacuous or self-contradictory at the very input the "
            "fix is about, and the whole battery's rejections would attest to "
            "nothing. Nothing is assumed: no new declaration, the theorem "
            "STATEMENT is byte-identical, and both instances are `have`s prepended "
            "inside the existing tactic body. Ports nagini's "
            "admiss-f2p-shaped-input, whose content on that carrier was its three "
            "`Requires` clauses."
        ),
    },

    # --- UNIQUENESS: (C0) the derivation step is run only where it is DEFINED
    # (the release-blocking rival) -----------------------------------------
    {
        "id": "rej-derive-outside-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD + _GOLD_DERIVE + "\n",
                        _REJ_DERIVE_OUTSIDE_GUARD),
        "refinement": (
            "Hoist the whole assemble-and-derive prelude ABOVE the guard: build "
            "the record, establish its target store and run the model's "
            "key-derivation step for EVERY record, then consult the guard only to "
            "decide whether to USE the resulting key. Every observable on the "
            "guarded path is identical to gold's, which is why this shape reads as "
            "a harmless refactor. It is not: not every model offers a "
            "key-derivation step, and on one that does not there is nothing to "
            "run. A faithful patch of this shape resolves the F2P and BREAKS the "
            "unrelated fixture-loading paths — measured on a fresh harness run: "
            "FAIL_TO_PASS 1/1, PASS_TO_PASS 27/53, 26 regressions, all of them "
            "loading data for models with no identifying key. It does NOT resolve."
        ),
        "rationale": (
            "Rejected by clause (C0). This is the audit rival that VERIFIED "
            "against the pre-(C0) spec (see the third audit note), so it is the "
            "case that makes the definedness obligation load-bearing rather than "
            "decorative. At `hasKey = false` the availability hypothesis FORCES the "
            "derivation step to yield nothing, so a rival that runs it there "
            "produces no record at all and (C0) fails; gold never reaches the step "
            "off the guard. Witness is refuted at (id = some 5, hasKey = false), a "
            "point where rej-guard-widened — the other (C0) rival — behaves "
            "correctly, and it binds NO hypotheses: the failing step is decided by "
            "computation, so there is nothing for the consistency probe to be "
            "inconsistent about."
        ),
        "witness": _W_DERIVE_OUTSIDE_GUARD,
    },

    # --- UNIQUENESS: (C0) the derivation step is run only on the RECORD it is
    # defined on (the second release-blocking rival) ------------------------
    {
        "id": "rej-probe-before-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_DERIVE, _REJ_PROBE_BEFORE),
        "refinement": (
            "Keep the fix EXACTLY as gold has it — establish the target store on "
            "the assembled record, then derive the key from it — and additionally "
            "run the model's key-derivation step ONCE on the record while it is "
            "still on the default store, discarding that result. The key the "
            "operation uses is unchanged, so this reads as a redundant probe with "
            "no observable. It is not: deriving a key follows the record's "
            "references to other records against the alias the record carries, and "
            "in the regression scenario the referenced record exists ONLY in the "
            "target store — so the extra run resolves nothing and raises, and the "
            "failure escapes the operation. Measured on a fresh harness run of a "
            "faithful patch of this shape (`obj = Model(**data); obj.natural_key(); "
            "obj._state.db = db; natural_key = obj.natural_key()`): PASS_TO_PASS "
            "53/53 but FAIL_TO_PASS 0/1 — the target test itself fails, consistently "
            "over 3 attempts. Mechanism confirmed directly outside the harness: on "
            "the F2P's model shape the default-store call raises "
            "`Person.DoesNotExist` while the target-store call returns the key. It "
            "does NOT resolve."
        ),
        "rationale": (
            "Rejected by clause (C0). This is the audit rival that VERIFIED against "
            "the previous spec (see the fourth audit note), where availability was "
            "asserted for EVERY record under `hasKey` — so an extra run off the "
            "target store was guaranteed to succeed and had no consequence. "
            "Availability is now assumed only ON THE RECORD ASSEMBLED FOR `store`, "
            "which is all gold needs and all the repo guarantees; the witness "
            "instantiates a step that is available exactly there, so this rival's "
            "default-store run yields no key, its failure propagates, and the "
            "operation comes back with no record. Binds no hypotheses (decided by "
            "computation). Distinct from rej-derive-outside-guard, which is refuted "
            "at `hasKey = false`: this rival's guard is gold's, and it is refuted at "
            "an F2P-shaped point INSIDE the guard."
        ),
        "witness": _W_PROBE_BEFORE,
    },
    {
        "id": "rej-probe-after-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_DERIVE, _REJ_PROBE_AFTER),
        "refinement": (
            "The same extra run of the derivation step, placed AFTER gold's correct "
            "one, on a freshly assembled record that is back on the default store "
            "(`Model(**data).natural_key()` again). A distinct impl and a stricter "
            "test of the obligation than rej-probe-before-store: here the fix's "
            "order of operations is fully respected and the correct key has already "
            "been obtained, so nothing about the ORDER is wrong — only the record "
            "the extra run is handed. Measured on a fresh harness run of a faithful "
            "patch of this shape: PASS_TO_PASS 53/53, FAIL_TO_PASS 0/1, consistent "
            "over 3 attempts. It does NOT resolve."
        ),
        "rationale": (
            "Rejected by clause (C0), for the same reason as rej-probe-before-store "
            "and at a different point (a different payload): availability is assumed "
            "only on the record assembled for `store`, so the default-store run "
            "yields no key and the operation returns no record. Keeping BOTH shapes "
            "matters because they falsify different readings of the repair — a "
            "syntactic 'derive last' rule would admit this one, and a syntactic "
            "'derive only once' rule would reject pos-control-double-derive, which "
            "must verify. What (C0) actually forbids is letting the step's failure "
            "escape from a record it is not defined on."
        ),
        "witness": _W_PROBE_AFTER,
    },

    # --- UNIQUENESS: (C2) derive-store dependence (THE bug) ---------------
    {
        "id": "rej-default-store-derive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ESTAB, ""),
        "refinement": (
            "This IS the prepatch behavior: assemble the not-yet-stored record "
            "and derive its identifying key WITHOUT first establishing the target "
            "store on it, so the key is derived from a record still on the DEFAULT "
            "store. On the regression scenario (data loaded into a non-default "
            "store whose related record lives only there) the key's related-record "
            "lookups resolve against the default store, which lacks the row, and "
            "the operation raises — the exact failure in the problem statement. A "
            "faithful patch keeping this omission does NOT resolve the F2P."
        ),
        "rationale": (
            "Rejected by clause (C2): the spec pins the result id to a lookup of "
            "the key the derivation step yields for the record assembled ON "
            "`store`, but this rival hands it a record still on `defaultStore`. "
            "Because the witness instantiates the step with one that READS the "
            "record's alias, the two keys are literally different (`[\"other\"]` "
            "vs `[defaultStore]`) rather than merely assumed different: the "
            "witness holds `data.id = none, hasKey = true` at store \"other\" and "
            "separates the two LOOKUPS (store-relative found ⇒ some 7, "
            "default-relative not found), so the spec demands id = some (coerceId "
            "7) while the rival returns none."
        ),
        "witness": _W_DEFAULT_STORE_DERIVE,
    },

    # --- UNIQUENESS: (C2) lookup-store dependence -------------------------
    {
        "id": "rej-lookup-default-store",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_MATCH, _REJ_LOOKUP_DEFAULT),
        "refinement": (
            "Derive the key correctly against the target store but perform the "
            "existing-record LOOKUP in the default store instead of the target — "
            "modelling a patch that fixed the key derivation yet queried the "
            "wrong store when checking for an existing row. On a non-default "
            "target the default store lacks the row, so no existing id is found "
            "and the record is stored as new rather than deduplicated against the "
            "target — diverging from the behavior the F2P requires; it does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by clause (C2): the spec looks up in `store`, this rival in "
            "`defaultStore`. Witness (store = \"replica\", active branch) separates "
            "the two lookups of the SAME derived key — found in \"replica\" (some "
            "7), not found in the default — so the spec demands id = some "
            "(coerceId 7) while the rival returns none. Distinct from "
            "rej-default-store-derive: this rival derives correctly (its key is "
            "the spec's key) and only the lookup store is wrong, so its h2 "
            "constrains a different opaque point."
        ),
        "witness": _W_LOOKUP_DEFAULT,
    },

    # --- UNIQUENESS: (C2) found ⇒ apply coerced id ------------------------
    {
        "id": "rej-ignore-found-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_MATCH, _REJ_IGNORE_FOUND),
        "refinement": (
            "Derive and look up correctly but DISCARD a found id — always return "
            "the record unchanged on the active branch, as though the "
            "existing-record match were dropped on the floor. A record that "
            "already exists in the target store would be re-inserted as new "
            "instead of being resolved to its stored id; it does NOT resolve the "
            "de-duplication the F2P exercises."
        ),
        "rationale": (
            "Rejected by clause (C2)'s found arm: when the store-relative lookup "
            "returns `some raw` the spec demands id = some (coerceId raw), but "
            "this rival returns `data` (id = none). Witness holds a single "
            "hypothesis (the store-relative lookup is found): it isolates the "
            "found arm's obligation as such, independently of WHICH store the "
            "lookup used. rej-skip-coerce attacks the same arm's coercion, "
            "rej-notfound-clobber the complementary not-found arm."
        ),
        "witness": _W_IGNORE_FOUND,
    },

    # --- UNIQUENESS: (C2) found ⇒ the id is COERCED -----------------------
    {
        "id": "rej-skip-coerce",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FOUND, _REJ_SKIP_COERCE),
        "refinement": (
            "Derive, look up and apply a found identifier correctly, but store the "
            "RAW looked-up value without putting it through the identifier field's "
            "own conversion. Wherever that conversion is not the identity on the "
            "stored representation the record carries an identifier of the wrong "
            "value/type, so the round-tripped data does not match the fixture; it "
            "does NOT resolve."
        ),
        "rationale": (
            "Rejected by clause (C2)'s found arm, specifically its `some (coerceId "
            "raw)` shape: the rival yields `some raw`. The witness binds two "
            "hypotheses at INDEPENDENT opaque points — the lookup is found with raw "
            "= 7, and the conversion is not the identity at 7 — so they are jointly "
            "satisfiable (neither constrains the other). The only rival that pins "
            "the coercion as load-bearing rather than decorative."
        ),
        "witness": _W_SKIP_COERCE,
    },

    # --- UNIQUENESS: (C2) not-found ⇒ the id is LEFT ----------------------
    {
        "id": "rej-notfound-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_MATCH, _REJ_NOTFOUND_CLOBBER),
        "refinement": (
            "Resolve correctly when an existing record IS found, but when none is "
            "found invent an identifier instead of leaving the record's own — "
            "modelling a patch that mishandles the absent-row path. A genuinely new "
            "record would be stored under a fabricated identifier rather than as "
            "new; it does NOT resolve."
        ),
        "rationale": (
            "Rejected by clause (C2)'s NOT-FOUND arm: when the store-relative "
            "lookup returns `none` the spec demands result.id = data.id, but this "
            "rival returns some 0. Witness holds the single hypothesis that the "
            "lookup is not found — the complementary sub-domain of (C2)'s match, "
            "which every other active-branch rival is refuted OFF of (they all "
            "condition on the lookup being found)."
        ),
        "witness": _W_NOTFOUND_CLOBBER,
    },

    # --- UNIQUENESS: (C0) at the guard's hasKey conjunct ------------------
    {
        "id": "rej-guard-widened",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _REJ_GUARD_WIDENED),
        "refinement": (
            "Resolve the identifier whenever the record has no identifier yet, "
            "IGNORING whether the model supports identifying keys at all — "
            "modelling a patch that widened the guard and dropped the key-support "
            "condition. Records of models with no identifying-key support would "
            "have a key-derivation step run on them that they do not offer, so "
            "loading them raises; it does NOT resolve."
        ),
        "rationale": (
            "Rejected by clause (C0) at the guard corner (data.id = none, hasKey = "
            "false), which no other case visits with this impl shape: the "
            "active-branch rivals all set hasKey = true and the inactive-branch "
            "ones all set data.id = some _. The availability hypothesis forces the "
            "derivation step to yield nothing at hasKey = false, so the rival's "
            "widened branch runs a step that is not there and comes back with no "
            "record. Witness binds nothing (decided by computation). NOTE the "
            "refutation moved with the (C0) repair: on the previous spec this same "
            "rival was refuted by the FRAME clause (C3), because a total derivation "
            "let it produce a record and clobber the id. It can no longer reach a "
            "frame violation, so (C3) is pinned instead by rej-guard-narrowed and "
            "rej-inactive-id-frame."
        ),
        "witness": _W_GUARD_WIDENED,
    },

    # --- UNIQUENESS: (C3) the guard's id conjunct (the fourth corner) ------
    {
        "id": "rej-guard-narrowed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GUARD, _REJ_GUARD_NARROWED),
        "refinement": (
            "Resolve the identifier whenever the model supports identifying keys, "
            "IGNORING whether the record already carries one — the complementary "
            "half-guard to rej-guard-widened. A record that arrives with its "
            "identifier already known would have it overwritten by whatever the "
            "key lookup returns, so data that should pass through with its own "
            "identifier is re-pointed at another row; it does NOT resolve."
        ),
        "rationale": (
            "Rejected by the frame clause (C3): at data.id = some 5 with hasKey = "
            "true the guard's conjunction is FALSE, so the spec demands result.id "
            "= data.id = some 5, but the rival takes its narrowed branch and "
            "returns some (coerceId 7). This is the corner where the derivation "
            "step IS available, so the rival does produce a record — which is what "
            "makes this a genuine FRAME refutation rather than a definedness one, "
            "and why it (with rej-inactive-id-frame) is what pins (C3) now that "
            "rej-guard-widened is refuted by (C0). Witness is refuted at exactly "
            "that corner — (id = some _, hasKey = true) — the FOURTH corner of the "
            "(id/hasKey) guard: rej-guard-widened sits at (none, false), the "
            "inactive-branch rivals at (some _, false), and every active-branch "
            "rival at (none, true). Its two hypotheses sit at independent opaque "
            "points (the lookup, and the coercion's value at 7 versus the record's "
            "own identifier), so they are jointly satisfiable."
        ),
        "witness": _W_GUARD_NARROWED,
    },

    # --- UNIQUENESS: (C2) partial-domain over the store alias -------------
    {
        "id": "rej-alias-guarded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ESTAB, _REJ_ALIAS_GUARDED),
        "refinement": (
            "A PARTIAL fix: establish the target store on the assembled record for "
            "only some store aliases and fall back to the default for the rest — "
            "modelling a patch that guarded the store association behind a "
            "predicate on the alias that does not always hold. Correct on the "
            "aliases the guard covers and the original bug on every other, where "
            "the key's related-record lookups resolve against the default store, "
            "which lacks the row. It does NOT resolve for the missed aliases."
        ),
        "rationale": (
            "Rejected by clause (C2) on the sub-domain of aliases the rival's own "
            "guard misses: the spec pins the derivation's record to `store` "
            "UNCONDITIONALLY, so an impl that pins it only sometimes fails wherever "
            "it does not. Witness is refuted at such an alias (\"replica\"), "
            "separating the target-relative key's lookup (found) from the "
            "default-relative one (not found). This is the port's analogue of the "
            "nagini sibling's partial-domain rivals, and the case where the store "
            "alias is load-bearing in the IMPL rather than in the witness's choice "
            "of literal."
        ),
        "witness": _W_ALIAS_GUARDED,
    },

    # --- UNIQUENESS: (C2) the established alias is the TARGET one ---------
    {
        "id": "rej-offby-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _ESTAB, _REJ_OFFBY_ALIAS),
        "refinement": (
            "Establish a MISCOMPUTED alias on the assembled record — one derived "
            "from the target alias but perturbed — rather than the target alias "
            "itself. The record is associated with a store, just not one that "
            "exists, so the key's related-record lookups resolve nowhere and the "
            "operation fails; it does NOT resolve. Distinct from "
            "rej-default-store-derive, which omits the association entirely rather "
            "than performing it wrongly."
        ),
        "rationale": (
            "Rejected by clause (C2): the spec derives from the record assembled on "
            "`store`, this rival from one assembled on a perturbation of it. "
            "Witness separates the two keys' lookups — target-relative found (some "
            "7), perturbed-relative not found — so the spec demands id = some "
            "(coerceId 7) while the rival returns none. Its second hypothesis names "
            "the NORMALIZED alias literal, which is what the rival's impl reduces "
            "to."
        ),
        "witness": _W_OFFBY_ALIAS,
    },

    # --- UNIQUENESS: (C1) payload frame -----------------------------------
    {
        "id": "rej-payload-frame",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FOUND, _REJ_PAYLOAD_MUTATE),
        "refinement": (
            "Resolve the id correctly but ALSO alter the record's descriptive "
            "payload while doing so — modelling a patch that corrupts the "
            "record's field data as a side effect of the lookup. The stored "
            "record would carry mutated descriptive fields; it does NOT resolve "
            "(the round-tripped data no longer matches the fixture)."
        ),
        "rationale": (
            "Rejected by the frame clause (C1) result.payload = data.payload: on "
            "the found case this rival returns payload = data.payload ++ [\"x\"] "
            "≠ data.payload. Witness (single found-lookup hypothesis) derives the "
            "contradiction from the payload conjunct. It exercises (C1) inside the "
            "ACTIVE branch's found case; rej-inactive-payload exercises the same "
            "clause on the inactive branch."
        ),
        "witness": _W_PAYLOAD_MUTATE,
    },

    # --- UNIQUENESS: (C1) payload frame on the INACTIVE branch ------------
    {
        "id": "rej-inactive-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TAIL, _REJ_INACTIVE_PAYLOAD),
        "refinement": (
            "On the branch where nothing should be resolved, alter the record's "
            "descriptive payload anyway — modelling a patch that corrupts field "
            "data on the pass-through path. Records that should be stored unchanged "
            "would carry mutated descriptive fields; it does NOT resolve."
        ),
        "rationale": (
            "Rejected by the frame clause (C1) on the inactive branch: the spec "
            "demands result.payload = data.payload for every record it returns — "
            "(C1) is NOT guarded by the (id/hasKey) condition — while this rival "
            "appends to it when the guard is false. Witness is a decidable literal "
            "(id = some 5, hasKey = false, at the failing derivation step "
            "availability forces there); the rival does not run the step, so it "
            "returns a record and the violation is a frame one rather than (C0). "
            "Together with rej-payload-frame it shows (C1) binds on BOTH branches, "
            "which neither case alone establishes."
        ),
        "witness": _W_INACTIVE_PAYLOAD,
    },

    # --- UNIQUENESS: (C3) inactive-branch id frame ------------------------
    {
        "id": "rej-inactive-id-frame",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _TAIL, _REJ_INACTIVE_MUTATE),
        "refinement": (
            "On the branch where nothing should be resolved (the record already "
            "carries an identifier, or the model has no identifying-key support) "
            "OVERWRITE the identifier instead of leaving it untouched — modelling "
            "a patch that mishandles the already-identified / no-key case and "
            "clobbers a valid pk. It does NOT resolve (records that should pass "
            "through unchanged are corrupted)."
        ),
        "rationale": (
            "Rejected by the frame clause (C3): when ¬(data.id = none ∧ hasKey = "
            "true) the spec demands result.id = data.id, but this rival returns "
            "id = some 0. Witness is a decidable literal: id = some 5, hasKey = "
            "false ⇒ the inactive branch, where the rival yields some 0 ≠ some 5. "
            "The rival does not run the derivation step there, so it returns a "
            "record and this is a genuine frame refutation; with "
            "rej-guard-narrowed it is what pins (C3). It varies the (id/hasKey) "
            "guard binder that every active-branch rival holds fixed; the guard's "
            "two remaining corners are covered by rej-guard-widened (id = none "
            "WITH hasKey = false) and rej-guard-narrowed (id = some _ WITH hasKey "
            "= true), neither of which this case reaches."
        ),
        "witness": _W_INACTIVE_MUTATE,
    },
]


# ===========================================================================
# AXIOM_TESTS — none. The axiom lane is G-AX's job; this bundle declares no
# `_prop` axiom. What the proof consumes about the key-derivation step is a
# THEOREM HYPOTHESIS (`derivationAvailability`), which whoever instantiates the
# obligation must discharge, and the two remaining callees (`lookupByKey`,
# `coerceId`) are opaque signatures the proof reasons about only by
# case-splitting the lookup result, not via any asserted contract. There is no
# consumed-axiom over-approximation for this gate to probe.
# ===========================================================================
AXIOM_TESTS = []
