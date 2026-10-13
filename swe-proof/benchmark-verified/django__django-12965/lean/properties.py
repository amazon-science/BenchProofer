# properties.py — G-PBT falsification battery for django__django-12965 (lean lane).
# NOT a Lean module: a manifest the gate parses. PORTED from the nagini sibling's
# battery — the adversarial ARGUMENTS are carried over, the mechanics re-expressed
# against this backend's carrier. Each SPEC_TESTS entry is a FULL Solution.lean
# variant built by region surgery: only the impl region (and, where a positive
# reproves a reshaped impl, the proof tactic body) is edited, so the frozen spec
# view is byte-identical and `same_spec` holds by construction, and the
# `theorem correct_*` STATEMENT is preserved verbatim so the obligation survives.
# No new axiom / lemma / sorry / admit / native_decide anywhere.
#
# Every expect="reject" case carries a refutation `witness`: a snippet stating the
# spec predicate at a CONCRETE input, which ELABORATES against the rival and FAILS
# against the frozen solution. That is what makes a rejection attributable to the
# spec rather than to a frozen tactic script that merely stopped matching a
# reshaped impl — the default outcome of reshaping any impl on a tactic-proof
# backend. All 11 witnesses below were built BOTH ways and seen to discriminate.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json)
#
#   implementation_isSingleTableDelete (refs : List Nat) : Bool
#
#   The decision, while compiling a row deletion, of whether the deletion targets
#   exactly ONE table — the condition under which it can be issued as a single
#   direct statement instead of one guarded by a self-referential membership
#   subquery. `refs` is the deletion's recorded table references, carried as their
#   non-negative reference counts in recording order; a reference is ACTIVE when
#   its count is positive.
#
#   ONE obligation, ONE binder, ONE postcondition equation:
#
#     (P) result = (activeCount (includePrimary refs) == 1)
#
#   It is a single equation but it composes FOUR independently attackable
#   ingredients, and the battery attacks each separately:
#
#     (P.a) the primary-presence step runs AT ALL before the count
#           — `includePrimary` is applied, not skipped;
#     (P.b) that step is right in BOTH of its branches, and touches the right
#           reference — no reference recorded yet ⇒ a brand new reference with
#           count one; otherwise the FIRST-recorded reference's count rises by one;
#     (P.c) the counted quantity is the number of references with a POSITIVE
#           count — the activeness threshold and the aggregation (a COUNT of
#           qualifying references, not a total of their counts);
#     (P.d) the comparison is to EXACTLY one — not ≤, not ≠, not a constant.
#
#   The carrier is FULLY TRANSPARENT: `activeCount` and `includePrimary` are total,
#   concrete `def`s over `List Nat` with no `opaque` callee and no answer-key
#   oracle, so `decide` computes the spec at any literal input and every witness
#   below is stated at a literal — no conditioning on the carrier is needed.
#
# ---------------------------------------------------------------------------
# CARRIER NARROWING vs the nagini sibling (why the case set is reshaped, not
# thinned)
#
#   The nagini model contracts TWO functions over a mutable `query` object:
#   `references_single_table(query)` (the changed decision, which WRITES
#   `query.primary_present`) and `delete_uses_subquery(query)` (its UNCHANGED
#   caller, which chooses the direct vs. subquery statement form). This bundle
#   models only the purely functional core: ONE total `Bool`-valued function of
#   the reference counts, with the primary-presence step spelled out as a pure
#   helper rather than as a heap write, and the caller not modeled at all.
#
#   Consequences for the port, case by case:
#
#   * nagini `drop-fix-no-primary-present` — PORTED as `weak-drop-primary-step`.
#     Same argument (read the count without first guaranteeing the primary table
#     is accounted for); here it is expressed by dropping the `includePrimary`
#     application instead of by dropping a field write. This is the reported
#     regression, and it is the same impl the frozen `Solution_prepatch.lean`
#     carries (G-DIFF).
#   * nagini `predicate-inverted` — PORTED as `weak-inverted`.
#   * nagini `partial-domain-rst-le-one` — PORTED as `weak-at-most-two`. Nagini's
#     boundary was `extra_active <= 1` (base table plus one extra join); on this
#     carrier the equivalent boundary is a total active count of ≤ 2, since the
#     primary reference is one of the counted references rather than a separate
#     flag. Same partial-domain argument, same sub-domain.
#   * nagini `always-subquery` / `always-direct` — PORTED as `weak-always-single`
#     / `weak-never-single`. In nagini these attacked the CALLER's two branches;
#     that caller is unmodeled here, but the constant-answer attack transfers
#     directly onto the decision itself and refutes clause (P.d) the same way.
#     Both are kept because they probe opposite sub-domains (the many-active and
#     the single-active case).
#   * nagini `frame-mut-write-extra-active` / `frame-mut-dus-write-extra-active`
#     — VACUOUS on this carrier, NOT dropped for convenience. Nagini's frame
#     clauses freeze a read-only quantity of a mutable object, and the rival
#     overwrites it so the discriminating clause holds vacuously. Lean is
#     referentially transparent: `refs` is an immutable value, there is no
#     aliasable heap location to overwrite, and no permission to hold — so the
#     rival is not expressible and the whole lane does not exist here. Nothing is
#     fabricated in its place. (The nagini frame argument is nevertheless
#     PRESERVED in substance: the spec pins the result to a function of `refs`
#     alone, and `weak-add-fresh-always` / `weak-bump-last-recorded` below attack
#     exactly the "the step touched the wrong reference" failure the frame clause
#     was there to catch.)
#   * nagini `admiss-caller-establishes-predicate-precond` — N/A as written: the
#     frozen obligation is `∀ (refs : List Nat), problem_spec … (implementation …
#     refs)` with NO precondition hypothesis and no modeled caller, so there is no
#     callee precondition a call site could fail to establish and nothing can be
#     PRECOND-TOO-STRONG. The admissibility lane is retargeted (not dropped) to
#     the surviving admissibility question on this carrier — whether the spec
#     still holds the two decision points the modeled behavior turns on — as
#     `admiss-decision-points`.
#   * nagini `partial-domain-dus-direct-on-extra-one` — the caller-side twin of
#     `partial-domain-rst-le-one`. The caller is unmodeled, so there is no second
#     obligation to attack and this case has no counterpart; its argument is
#     already carried by `weak-at-most-two` on the decision itself.
#   * nagini `pos-control-rst-direct-discriminator` — PORTED as
#     `pos-other-discriminator`. Nagini's positive computed the decision through
#     `extra_active == 0` rather than `active_tables == 1`, exploiting that the two
#     coincide once the primary table is accounted for; the same equivalence holds
#     here ("no OTHER recorded reference is active"), so the case transfers
#     directly and is expressible on this carrier.
#   * nagini `pos-control-dus-not-predicate` — the caller-side positive. No
#     counterpart for the same reason. The soundness lane is instead broadened
#     over this carrier's own shapes (see the five positives below).
#   * AXIOM_TESTS — DROPPED. `meta.axioms == []` and there is no `opaque` callee:
#     the primary-presence step is modeled DEEPLY as `includePrimary` and
#     validated == the real callee by the conformance gate. The axiom lane is
#     G-AX's job and this gate ignores it.
#   * DIVERGENCE / NON-TERMINATION lane — the nagini sibling carries no such case,
#     and on lean the class is genuinely VACUOUS: `implementation_*` is a total
#     Lean `def`, so a diverging implementation cannot be written at all. (This is
#     specifically NOT the velvet situation, where under partial termination
#     semantics a non-terminating impl satisfies every clause vacuously and the
#     frozen spec ADMITS the rival — a known spec hole, see
#     the corpus-wide termination-semantics finding. That hole does not exist on this backend.)
#
#   ADDED with no nagini counterpart, because this carrier exposes structure
#   nagini's boolean-flag abstraction collapsed. Nagini reduced the primary table
#   to a single `primary_present : bool` and the rest to a scalar `extra_active`,
#   so it could not express a rival that runs the primary-presence step but
#   applies it to the WRONG reference, nor one that miscounts activeness or
#   aggregates the counts instead of counting them. Those are exactly clauses
#   (P.b) and (P.c), and without them the reference ORDER and the activeness
#   predicate would be pinned by no witness at all:
#     `weak-bump-only-when-recorded`, `weak-add-fresh-always`,
#     `weak-bump-last-recorded`  (clause P.b)
#     `weak-count-all-recorded`, `weak-strongly-active-only`, `weak-sum-counts`
#                                (clause P.c)

from pathlib import Path

INSTANCE = "django__django-12965"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two editable regions, extracted VERBATIM so the manifest breaks loudly if
# the frozen solution ever changes. Each anchor lies entirely inside the region
# it names (impl-start/impl-end, proof-start/proof-end) and is unique in the file.
# The spec view — docstring, `activeCount`, `includePrimary`,
# `problem_spec_isSingleTableDelete` — and the `theorem correct_*` STATEMENT are
# never touched by any case.
# ---------------------------------------------------------------------------

_IMPL_OLD = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  -- Ensure the primary table is present among the recorded references before
  -- counting (adds it / bumps the primary reference count).
  let refs := includePrimary refs
  -- Count the active references (positive reference count) and decide "== 1".
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"

_PROOF_OLD = """\
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
  have helper : ∀ (xs : List Nat) (init : Nat),
      Id.run (forIn xs init (fun c r =>
        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
        else do pure PUnit.unit; pure (ForInStep.yield r)))
        = init + activeCount xs := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a > 0
      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
          List.length_cons]
        omega
      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
          Bool.false_eq_true, if_false]
  show (Id.run (forIn (includePrimary refs) 0 (fun c r =>
        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
        else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
      = (activeCount (includePrimary refs) == 1)
  rw [helper]
  simp"""

assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _v(impl, proof=None):
    """A full Solution.lean variant: new impl body, optionally a new proof body
    (for a positive whose reshaped impl needs a matching tactic script). The
    theorem STATEMENT and the entire spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, impl)
    if proof is not None:
        out = _swap(out, _PROOF_OLD, proof)
    return out


def _wit(args):
    """A refutation witness at one concrete, `decide`-able input: the spec
    predicate is stated directly of the rival's own output there. Elaborates iff
    the rival's answer contradicts the spec at that input; fails on the frozen
    solution, which satisfies the spec everywhere."""
    return f"""\
example : ¬ problem_spec_isSingleTableDelete {args}
    (implementation_isSingleTableDelete {args}) := by
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
  decide"""


# The frozen loop-equals-fold lemma, reused verbatim by the positives that keep
# an accumulator loop. It is an in-proof `have`, not a new top-level lemma, so no
# case adds a declaration beyond the frozen set.
_HELPER = """\
  have helper : ∀ (xs : List Nat) (init : Nat),
      Id.run (forIn xs init (fun c r =>
        if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
        else do pure PUnit.unit; pure (ForInStep.yield r)))
        = init + activeCount xs := by
    intro xs
    induction xs with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a > 0
      · simp only [h, if_true, ih, activeCount, List.filter_cons, decide_true,
          List.length_cons]
        omega
      · simp only [h, if_false, ih, activeCount, List.filter_cons, decide_false,
          Bool.false_eq_true, if_false]"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY, each shipped with
# a proof that actually closes for its own shape. If one fails => SPEC-TOO-STRONG.
# ===========================================================================

# pos-functional: the decision as a single pure expression — no `Id.run do`, no
# accumulator loop, the aggregation delegated to the spec's own helper. The
# corpus-narrowest possible reshape, and the control that shows the spec does not
# secretly demand the imperative encoding.
_POS_FUNCTIONAL = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool :=
  (activeCount (includePrimary refs) == 1)"""
_POS_FUNCTIONAL_PROOF = """\
  intro refs
  rfl"""

# pos-countp: the active references counted by a library count-with-predicate
# instead of by a hand-rolled `let mut` accumulator. Same value, a completely
# different traversal, and a proof that must bridge count-by-predicate to
# count-of-filtered rather than replay the frozen induction.
_POS_COUNTP = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := includePrimary refs
  return refs.countP (fun c => c > 0) == 1"""
_POS_COUNTP_PROOF = """\
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
  simp [Id.run, activeCount, List.countP_eq_length_filter]
  rfl"""

# pos-split-head: the primary-presence step FUSED INTO the count instead of run as
# a separate pass — the two branches are taken apart, and in the recorded-reference
# branch the primary reference is known active a priori, so the accumulator starts
# at one and the loop runs over the tail only. Behaviourally identical, and the
# only positive whose proof must case-split on the binder. This is the shape that
# would break if the spec had accidentally pinned the two-pass STRUCTURE rather
# than the value.
_POS_SPLIT_HEAD = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  match refs with
  | []        => return true
  | _ :: rest =>
    let mut active := 1
    for c in rest do
      if c > 0 then
        active := active + 1
    return active == 1"""
_POS_SPLIT_HEAD_PROOF = """\
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
""" + _HELPER + """
  cases refs with
  | nil => simp [Id.run, includePrimary, activeCount]; rfl
  | cons c rest =>
    show (Id.run (forIn rest 1 (fun c r =>
          if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
          else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
        = (activeCount (includePrimary (c :: rest)) == 1)
    rw [helper]
    simp [includePrimary, activeCount]"""

# pos-set-primary-active: the primary-presence step written as "make the primary
# reference active" (set its count to one) rather than "raise its count by one".
# The two differ as functions on the counts — and the spec's helper spells out the
# raise — yet they are INDISTINGUISHABLE through the decision, because only the
# SIGN of the primary count can reach the result and the raise can never clear it.
# Verifying is the interesting fact: it shows the spec's equation is pinned to the
# decision's VALUE and not to a syntactic echo of the helper it names. Its
# near-miss twin `weak-bump-only-when-recorded` is the rival that changes the same
# step in a way that DOES reach the result — so this pair is what separates
# "reshaped the step" from "broke the step".
_POS_SET_ONE = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := match refs with
    | []        => [1]
    | _ :: rest => 1 :: rest
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1"""
_POS_SET_ONE_PROOF = """\
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
""" + _HELPER + """
  cases refs with
  | nil =>
    show (Id.run (forIn ([1] : List Nat) 0 (fun c r =>
          if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
          else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
        = (activeCount (includePrimary []) == 1)
    rw [helper]
    simp [includePrimary, activeCount]
  | cons c rest =>
    show (Id.run (forIn (1 :: rest) 0 (fun c r =>
          if c > 0 then do pure PUnit.unit; pure (ForInStep.yield (r + 1))
          else do pure PUnit.unit; pure (ForInStep.yield r))) == 1)
        = (activeCount (includePrimary (c :: rest)) == 1)
    rw [helper]
    simp [includePrimary, activeCount, List.filter_cons]"""

# pos-other-discriminator: the PORT of nagini's `pos-control-rst-direct-
# discriminator` (which computed the decision via `extra_active == 0` instead of
# `active_tables == 1`). Same argument on this carrier: after the primary-presence
# step the primary reference is active unconditionally, so "exactly one active
# reference" is equivalent to "no OTHER recorded reference is active" — a
# different discriminator reaching the same decision, with the primary-presence
# step never applied as a list operation at all. Its proof must establish the
# bridging fact `activeCount (includePrimary (c :: rest)) = 1 + activeCount rest`
# rather than replay the frozen induction.
_POS_OTHER_ZERO = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool :=
  match refs with
  | []        => true
  | _ :: rest => (activeCount rest == 0)"""
_POS_OTHER_ZERO_PROOF = """\
  intro refs
  unfold problem_spec_isSingleTableDelete implementation_isSingleTableDelete
  cases refs with
  | nil => simp [includePrimary, activeCount]
  | cons c rest =>
    have h : activeCount (includePrimary (c :: rest)) = 1 + activeCount rest := by
      simp only [includePrimary, activeCount, List.filter_cons, Nat.succ_pos,
        decide_true, if_true, List.length_cons]
      omega
    rw [h]
    show (activeCount rest == 0) = (1 + activeCount rest == 1)
    rcases Nat.eq_zero_or_pos (activeCount rest) with h0 | h0
    · rw [h0]; rfl
    · have a : (activeCount rest == 0) = false := by
        simp only [beq_eq_false_iff_ne, ne_eq]; omega
      have b : (1 + activeCount rest == 1) = false := by
        simp only [beq_eq_false_iff_ne, ne_eq]; omega
      rw [a, b]"""

# admiss-decision-points: the retargeted admissibility control (see the carrier
# note). Nagini's admissibility case asked whether a call site can establish the
# callee's precondition; this obligation has no precondition and no modeled
# caller, so the surviving question is whether the spec still admits — and pins —
# the two decision points the modeled behavior actually turns on: with NO
# reference recorded yet the decision is affirmative, and with a second ACTIVE
# reference recorded alongside the primary one it is negative. Both are asserted
# in-body as `have … := by decide`; the impl body and the frozen proof script are
# otherwise verbatim, so the only thing this case can fail on is a regression at
# those two points.
_ADMISS_SHAPE = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  -- The two decision points the modeled behavior turns on, asserted in-body.
  have _hNone : (activeCount (includePrimary []) == 1) = true := by decide
  have _hTwo : (activeCount (includePrimary [0, 1]) == 1) = false := by decide
  let refs := includePrimary refs
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1"""


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each edits ONLY the
# impl region and ships a witness SEEN to elaborate against it and fail on gold.
# ===========================================================================

# --- clause (P.a): the primary-presence step must run at all -----------------

# weak-drop-primary-step: count the recorded references WITHOUT first guaranteeing
# the primary table is among them. This IS the reported regression, and it is the
# impl the frozen prepatch file carries.
_R_DROPFIX = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1"""

# --- clause (P.b): the step's branches, and WHICH reference it touches -------

# weak-bump-only-when-recorded: run the step, but only in its recorded-reference
# branch — with nothing recorded yet, leave the references untouched instead of
# creating the primary one. A NEAR MISS of gold: agrees everywhere except on the
# no-reference-recorded input, which is precisely the input the change is about.
_R_ONLY_BUMP = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := match refs with
    | []        => []
    | c :: rest => (c + 1) :: rest
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1"""

# weak-add-fresh-always: always ADD a fresh primary reference with count one,
# never recognising that the primary table is already the first recorded
# reference — so with references already recorded the primary table is
# double-counted. The mirror of the previous rival: it gets the empty case right
# and the recorded case wrong.
_R_ADD_FRESH = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := refs ++ [1]
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1"""

# weak-bump-last-recorded: run both branches of the step correctly but apply the
# recorded-reference branch to the LAST-recorded reference instead of the
# first-recorded (primary) one. Correct whenever the target happens to coincide
# or the sign does not move; wrong exactly when the two differ in activeness.
# This is the rival that makes the recording ORDER of `refs` load-bearing — no
# other witness distinguishes a permutation.
_R_BUMP_LAST = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := match refs.reverse with
    | []        => [1]
    | c :: rest => ((c + 1) :: rest).reverse
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active == 1"""

# --- clause (P.c): activeness threshold and aggregation ----------------------

# weak-count-all-recorded: count every recorded reference, active or not — the
# activeness test dropped. Correct whenever every recorded reference is active,
# wrong as soon as one is inactive.
_R_COUNT_ALL = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := includePrimary refs
  let mut active := 0
  for _c in refs do
    active := active + 1
  return active == 1"""

# weak-strongly-active-only: shift the activeness threshold by one — count only
# references referenced MORE THAN once. Same aggregation, same comparison, only
# the per-reference predicate moved; the tightest possible miss on that predicate.
_R_STRONGLY_ACTIVE = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := includePrimary refs
  let mut active := 0
  for c in refs do
    if c > 1 then
      active := active + 1
  return active == 1"""

# weak-sum-counts: total the reference COUNTS instead of counting the references
# that have a positive one. It answers affirmatively only when the total is one,
# i.e. only when the primary reference is the sole reference carrying any count at
# all; so it agrees with gold exactly on the inputs where no OTHER reference is
# active AND the primary reference entered with count zero, and diverges on every
# input whose primary reference was already referenced (verified by exhaustive
# enumeration over lengths 0..6, counts 0..3: the divergence set is exactly the
# inputs with refs[0] > 0 and every later count zero). The aggregation attack; no
# other rival changes what is being accumulated.
_R_SUM_COUNTS = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := includePrimary refs
  let mut active := 0
  for c in refs do
    active := active + c
  return active == 1"""

# --- clause (P.d): the comparison to exactly one -----------------------------

# weak-at-most-two: the port of nagini's boundary rival. Correct at one active
# reference and at three or more, wrong at exactly two — i.e. the primary table
# plus one further active reference. Drops only that boundary sub-domain.
_R_LE_TWO = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := includePrimary refs
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return Nat.ble active 2"""

# weak-inverted: the negated decision — affirmative exactly when the active count
# is NOT one. Disagrees with gold on the whole domain.
_R_INVERTED = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let refs := includePrimary refs
  let mut active := 0
  for c in refs do
    if c > 0 then
      active := active + 1
  return active != 1"""

# weak-never-single: the constant negative answer. Runs the primary-presence step
# (so it is not merely the dropped-step rival) and then ignores the count.
_R_FALSE = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let _refs := includePrimary refs
  return false"""

# weak-always-single: the constant affirmative answer — the opposite constant,
# wrong on the complementary sub-domain.
_R_TRUE = """\
def implementation_isSingleTableDelete (refs : List Nat) : Bool := Id.run do
  let _refs := includePrimary refs
  return true"""


SPEC_TESTS = [
    # ------------------------------------------------------------- POSITIVES
    {
        "id": "pos-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _v(_POS_FUNCTIONAL, _POS_FUNCTIONAL_PROOF),
        "rationale": (
            "structurally-different CORRECT impl: the decision as one pure "
            "expression, with no imperative accumulator at all. Satisfies (P) "
            "definitionally, so the reproof is `rfl` — the theorem STATEMENT is "
            "byte-identical, only the tactic body changes. Shows (P) pins the "
            "decision's VALUE and does not secretly demand the loop encoding. If "
            "it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-countp",
        "kind": "soundness",
        "expect": "verify",
        "module": _v(_POS_COUNTP, _POS_COUNTP_PROOF),
        "rationale": (
            "CORRECT impl that counts the active references with a library "
            "count-with-predicate instead of a hand-rolled accumulator — a "
            "different traversal reaching the same count, so the reproof must "
            "bridge count-by-predicate to count-of-filtered rather than replay "
            "the frozen induction. Defends clause (P.c) from the positive side: "
            "any faithful way of counting the positively-referenced references "
            "must be admitted. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-split-head",
        "kind": "soundness",
        "expect": "verify",
        "module": _v(_POS_SPLIT_HEAD, _POS_SPLIT_HEAD_PROOF),
        "rationale": (
            "CORRECT impl that FUSES the primary-presence step into the count "
            "instead of running it as a separate pass: the branches are taken "
            "apart and, where a reference is already recorded, the primary one is "
            "known active so the accumulator starts at one over the tail. Defends "
            "(P.a)+(P.b) from the positive side — the spec must pin the resulting "
            "decision, not the two-pass STRUCTURE the frozen impl happens to use. "
            "The only positive whose proof case-splits on the binder. If it fails "
            "=> SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-set-primary-active",
        "kind": "soundness",
        "expect": "verify",
        "module": _v(_POS_SET_ONE, _POS_SET_ONE_PROOF),
        "rationale": (
            "CORRECT impl whose primary-presence step makes the primary reference "
            "ACTIVE (count set to one) rather than raising its count by one. The "
            "two differ as functions on the counts, and the spec's helper spells "
            "out the raise, yet they are indistinguishable THROUGH the decision: "
            "only the sign of the primary count can reach the result, and a raise "
            "can never clear it. Verifying is the load-bearing fact — it shows "
            "(P) is pinned to the decision's value and not satisfiable only by a "
            "syntactic echo of the helper the spec names. Paired with its "
            "near-miss twin `weak-bump-only-when-recorded`, which changes the "
            "same step in a way that DOES reach the result. If it fails => "
            "SPEC-TOO-STRONG (the spec would be demanding the echo)."
        ),
    },
    {
        "id": "pos-other-discriminator",
        "kind": "soundness",
        "expect": "verify",
        "module": _v(_POS_OTHER_ZERO, _POS_OTHER_ZERO_PROOF),
        "rationale": (
            "the PORT of nagini's `pos-control-rst-direct-discriminator`, which "
            "computed the decision through the OTHER discriminator (no further "
            "active table) instead of through the count. Here: after the "
            "primary-presence step the primary reference is active "
            "unconditionally, so 'exactly one active reference' is equivalent to "
            "'no other recorded reference is active', and this impl decides that "
            "way — never applying the step as a list operation at all. The spec "
            "must admit the equivalent discriminator, not just the counting one, "
            "so its reproof carries the bridging fact `activeCount (includePrimary "
            "(c :: rest)) = 1 + activeCount rest`. Complements "
            "pos-set-primary-active (which reshapes the step) by reshaping the "
            "DECISION instead. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-decision-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _v(_ADMISS_SHAPE),
        "rationale": (
            "the retargeted admissibility control. Nagini's admissibility case "
            "asked whether a call site can establish the callee's precondition; "
            "this obligation binds no precondition and models no caller, so "
            "nothing here can be PRECOND-TOO-STRONG. The surviving admissibility "
            "question is whether the spec still admits and PINS the two decision "
            "points the modeled behavior turns on — no reference recorded yet "
            "(affirmative) and a second active reference alongside the primary "
            "one (negative) — asserted in-body as `have … := by decide`. Impl "
            "body and frozen proof script are otherwise verbatim, so the only "
            "thing this can fail on is a regression at those two points."
        ),
    },
    # ---------------------------------------- clause (P.a): the step runs at all
    {
        "id": "weak-drop-primary-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_DROPFIX),
        "witness": _wit("[0]"),
        "refinement": (
            "this IS the reported regression: without the primary-presence step "
            "the deletion's own table is unaccounted for at count time, so a "
            "deletion of every row in a table finds no active reference, the "
            "decision comes out negative, and the deletion is issued in the "
            "guarded form with a self-referential membership subquery. Its "
            "faithful real patch is the unpatched code, whose FAIL_TO_PASS test "
            "runs a whole-table deletion and asserts the emitted statement "
            "contains no membership subquery — it finds one. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.a): the primary-presence step is "
            "dropped entirely, so on an input whose only recorded reference is "
            "INACTIVE the active count is 0, not 1, and the rival answers "
            "negatively where the spec demands affirmatively. Witness at [0] — "
            "one recorded-but-inactive reference, which discriminates the dropped "
            "step while keeping the list non-empty (so it is not merely a restatement "
            "of the empty-input case probed by weak-bump-only-when-recorded). "
            "If it verifies => SPEC-TOO-WEAK, and the spec would not see the bug."
        ),
    },
    # ------------------------- clause (P.b): branches, and WHICH reference moves
    {
        "id": "weak-bump-only-when-recorded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_ONLY_BUMP),
        "witness": _wit("[]"),
        "refinement": (
            "a real change that guaranteed the primary table's presence only when "
            "some reference had already been recorded would leave the "
            "no-reference-recorded case — a deletion of every row in a table, "
            "which records nothing — exactly as it was before: decision negative, "
            "guarded subquery form emitted. That is the very case the "
            "FAIL_TO_PASS test exercises, and it still fails. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.b), empty branch: with no reference "
            "recorded the spec requires a brand new primary reference (active "
            "count 1, affirmative) and the rival leaves the collection empty "
            "(count 0, negative). A NEAR MISS — it agrees with gold on every "
            "non-empty input, so it is refuted only at the empty one, and it is "
            "the exact counterpart of the pos-set-primary-active positive (same "
            "step reshaped, but this reshape reaches the result). Witness at []. "
            "If it verifies => SPEC-TOO-WEAK on the empty branch."
        ),
    },
    {
        "id": "weak-add-fresh-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_ADD_FRESH),
        "witness": _wit("[2, 0]"),
        "refinement": (
            "a real change that always recorded a FRESH reference to the primary "
            "table, instead of recognising that the primary table is already the "
            "first-recorded reference when anything has been recorded, would "
            "double-count that table. A deletion restricted through a related "
            "table would then show two active references where one is genuine, "
            "the decision would come out negative, and the deletion would be "
            "issued in the guarded subquery form where the direct form is "
            "correct — the fast-delete PASS_TO_PASS deletion tests count the "
            "emitted statements and would fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.b), recorded branch: the spec raises "
            "the FIRST-recorded reference's count, the rival appends a second "
            "reference instead. The exact mirror of "
            "weak-bump-only-when-recorded — this one gets the empty input right "
            "and the recorded input wrong. Witness at [2, 0]: one active "
            "reference plus an inactive one, where the spec's answer is "
            "affirmative and the rival's appended reference makes it negative. If "
            "it verifies => SPEC-TOO-WEAK on the recorded branch."
        ),
    },
    {
        "id": "weak-bump-last-recorded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_BUMP_LAST),
        "witness": _wit("[1, 0]"),
        "refinement": (
            "a real change that raised the reference count of the LAST-recorded "
            "table rather than the deletion's own primary one would, whenever the "
            "two are different tables, mark the wrong table as referenced: a "
            "deletion joined to a related table would report one active "
            "reference where two are genuinely active (or vice versa) and pick "
            "the wrong statement form — issuing a direct deletion that drops the "
            "join restriction and removes rows the deletion was not supposed to "
            "touch. The fast-delete PASS_TO_PASS deletion tests fail. Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.b): both branches are shaped right but "
            "applied to the wrong reference — the rival that isolates WHICH "
            "reference the step moves. It is one of three cases whose witness "
            "point relies on the recording ORDER of `refs`: re-checked against a "
            "hypothetical permutation-blind spec (one that counts the multiset of "
            "recorded counts), the witnesses of this case, weak-add-fresh-always "
            "and weak-sum-counts stop refuting their rivals, while the other "
            "eight still refute at their own points. It is, however, the only "
            "rival that a bump-the-LAST-recorded-reference spec would ADMIT "
            "outright, so it is the case that pins the target of the step rather "
            "than merely being stated at an order-sensitive input. (The ordering "
            "half of (P.b) is additionally pinned from the positive side: all "
            "four positives are refuted by a permutation-blind spec, e.g. at "
            "[1, 0].) Witness at [1, 0]: an active primary reference and an inactive "
            "second one, where gold answers affirmatively (raising the first "
            "leaves one active) and the rival answers negatively (raising the "
            "last makes two active). If it verifies => SPEC-TOO-WEAK on which "
            "reference the step touches."
        ),
    },
    # ----------------------- clause (P.c): activeness threshold + aggregation
    {
        "id": "weak-count-all-recorded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_COUNT_ALL),
        "witness": _wit("[0, 0]"),
        "refinement": (
            "a real change that counted every recorded table reference rather "
            "than only those actually referenced would, for a deletion that has "
            "recorded a reference it no longer uses, see more tables involved "
            "than are and issue the guarded subquery form where the direct form "
            "is correct. Deletions whose restriction matches nothing, and the "
            "cascading fast-delete paths, are exactly the PASS_TO_PASS cases that "
            "count emitted statements; they fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.c): the activeness test (positive "
            "reference count) is dropped, so an inactive recorded reference is "
            "counted. Witness at [0, 0]: after the primary-presence step the "
            "counts are [1, 0], so exactly one reference is active (spec: "
            "affirmative) but two are recorded (rival: negative). If it verifies "
            "=> SPEC-TOO-WEAK — the spec would not require the reference count to "
            "be consulted at all."
        ),
    },
    {
        "id": "weak-strongly-active-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_STRONGLY_ACTIVE),
        "witness": _wit("[0, 3]"),
        "refinement": (
            "a real change that treated a table as involved only once it had been "
            "referenced MORE THAN once would miss every singly-referenced table. "
            "A deletion joined to a related table referenced exactly once would "
            "report that table as uninvolved, come out affirmative, and be issued "
            "as a direct deletion with the join restriction dropped — removing "
            "rows outside the intended set. The fast-delete PASS_TO_PASS deletion "
            "tests fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.c): the per-reference threshold is "
            "shifted by one while the aggregation and the comparison are left "
            "correct — the TIGHTEST possible miss on the activeness predicate, "
            "distinct from weak-count-all-recorded, which removes the predicate "
            "outright. Witness at [0, 3]: after the step the counts are [1, 3], "
            "so two references are active (spec: negative) but only one is "
            "referenced more than once (rival: affirmative). If it verifies => "
            "SPEC-TOO-WEAK on where the activeness boundary sits."
        ),
    },
    {
        "id": "weak-sum-counts",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_SUM_COUNTS),
        "witness": _wit("[3, 0]"),
        "refinement": (
            "a real change that totalled the reference COUNTS instead of counting "
            "the tables that have a positive one would answer affirmatively only "
            "when the total is one — that is, only for a deletion whose own table "
            "is the single table carrying any reference at all and which had not "
            "already been referenced before the primary-presence step ran. Every "
            "deletion whose own table was ALREADY referenced (the ordinary case "
            "once any restriction has been compiled, since the step then raises "
            "an already-positive count) would report more involvement than there "
            "are tables, come out negative, and be issued in the guarded subquery "
            "form where the direct form is correct; the statement-counting "
            "fast-delete PASS_TO_PASS tests fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.c), aggregation half: the spec counts "
            "how MANY references are active, the rival totals HOW OFTEN they are "
            "referenced. The only rival that changes what is accumulated — every "
            "other one accumulates a count of qualifying references — so without "
            "it the 'a count, not a total' reading of (P.c) is pinned by no "
            "witness. Its agreement region is narrow rather than 'the common "
            "case': it coincides with gold only where the primary reference "
            "entered with count zero and no later reference is active. Witness at "
            "[3, 0]: after the step the counts are [4, 0], so "
            "exactly one reference is active (spec: affirmative) while the total "
            "is 4 (rival: negative). If it verifies => SPEC-TOO-WEAK on the "
            "aggregation."
        ),
    },
    # ------------------------------ clause (P.d): comparison to exactly one
    {
        "id": "weak-at-most-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_LE_TWO),
        "witness": _wit("[1, 1]"),
        "refinement": (
            "ports the nagini boundary rival. A real change answering "
            "affirmatively for two active tables — the deletion's own table plus "
            "one further referenced table — would issue a direct deletion for a "
            "deletion restricted through a single related table, dropping the "
            "join restriction and removing rows outside the intended set. The "
            "fast-delete PASS_TO_PASS deletion tests, which count the emitted "
            "statements for exactly such deletions, fail. Does NOT resolve. "
            "(Nagini stated the boundary as 'at most one EXTRA active table'; "
            "here the primary reference is one of the counted references rather "
            "than a separate flag, so the same boundary reads as a total of at "
            "most two.)"
        ),
        "rationale": (
            "rejected by (P) via clause (P.d): correct at one active reference and "
            "at three or more, wrong at exactly two. PARTIAL-DOMAIN attack — it "
            "drops only the boundary sub-domain, so a spec that pinned the "
            "decision merely as 'few active references' would admit it. Witness at "
            "[1, 1]: after the step the counts are [2, 1], two active references, "
            "where the spec demands a negative answer. If it verifies => "
            "SPEC-TOO-WEAK at the boundary."
        ),
    },
    {
        "id": "weak-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_INVERTED),
        "witness": _wit("[1]"),
        "refinement": (
            "an inverted decision — affirmative exactly when the deletion does "
            "NOT target a single table — would issue the guarded subquery form "
            "for whole-table deletions and the direct form for multi-table ones. "
            "Both are wrong: the FAIL_TO_PASS whole-table test still finds a "
            "membership subquery, and the multi-table fast-delete PASS_TO_PASS "
            "tests get a direct deletion with the restriction dropped. Does NOT "
            "resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.d): the rival returns the negation of "
            "the required decision, so it disagrees with the spec at every input. "
            "Witness at [1] — a single active reference, the affirmative case, "
            "where the rival answers negatively. If it verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "weak-never-single",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_FALSE),
        "witness": _wit("[2]"),
        "refinement": (
            "ports nagini's always-emit-the-subquery rival onto the decision "
            "itself (nagini attacked the caller's branch; that caller is not "
            "modeled here). A real change that answered negatively unconditionally "
            "would emit the guarded self-referential subquery for every deletion, "
            "including a whole-table one — precisely the regression the issue "
            "reports. The FAIL_TO_PASS whole-table test asserts the emitted "
            "statement contains no membership subquery and fails. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.d): the constant negative answer. It "
            "still runs the primary-presence step, so its rejection is "
            "attributable to the comparison and not to a dropped step (that is "
            "weak-drop-primary-step's job). Witness at [2] — one reference already "
            "actively referenced, an affirmative case. If it verifies => "
            "SPEC-TOO-WEAK (the result would be unpinned on the affirmative "
            "sub-domain)."
        ),
    },
    {
        "id": "weak-always-single",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _v(_R_TRUE),
        "witness": _wit("[0, 1]"),
        "refinement": (
            "ports nagini's always-emit-the-direct-form rival onto the decision "
            "itself. A real change answering affirmatively unconditionally would "
            "issue a direct deletion even for a deletion genuinely involving a "
            "second table, dropping the restriction that confines it and removing "
            "rows it was never meant to touch. The multi-table fast-delete "
            "PASS_TO_PASS deletion tests fail. Does NOT resolve."
        ),
        "rationale": (
            "rejected by (P) via clause (P.d): the constant affirmative answer — "
            "the opposite constant to weak-never-single, wrong on the "
            "complementary sub-domain, which is why both are kept. Witness at "
            "[0, 1]: after the step the counts are [1, 1], two active references, "
            "where the spec demands a negative answer. If it verifies => "
            "SPEC-TOO-WEAK (the result would be unpinned on the negative "
            "sub-domain)."
        ),
    },
]

# The axiom lane is dropped: `meta.axioms == []` and there is no `opaque` callee
# in this bundle — the primary-presence step is modeled deeply as a concrete
# helper and validated against the real callee by the conformance gate, so there
# is no assumed contract for an axiom case to probe. That lane is G-AX's job and
# this gate ignores it.
AXIOM_TESTS = []
