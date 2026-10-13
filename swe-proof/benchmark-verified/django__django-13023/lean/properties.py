# properties.py — G-PBT falsification battery for django__django-13023 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT gate
# executes and stamps with a verdict. Each spec case is a FULL Solution.lean
# variant sharing the FROZEN spec exactly (region surgery: only the text strictly
# inside `-- impl-start` / `-- impl-end`, and for a re-proved positive the text
# inside `-- proof-start` / `-- proof-end`, is replaced). The spec view elides
# both regions, so `markers.same_spec` holds by construction and every
# accept/reject is attributable to the postcondition rather than to a tampered
# spec. The `theorem correct_toPython` STATEMENT is byte-identical in every
# variant; no case adds an axiom, a helper lemma, `sorry`, `admit`, or
# `native_decide`.
#
# This battery is a PORT of the nagini sibling's battery (nagini/properties.py).
# The adversarial ARGUMENT is carried over; the mechanics are re-expressed
# against this backend's carrier. See `assessment` in the handoff for the full
# ported/omitted ledger.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean)
# ---------------------------------------------------------------------------
#   implementation_toPython (v : Value) : Outcome
#   Obligation: theorem correct_toPython :
#                 ∀ (v : Value), problem_spec_toPython v (implementation_toPython v)
#
#   There is NO precondition: the obligation quantifies over EVERY `Value` with
#   no hypothesis binder. `Value` is a plain structure of three decidable
#   features (`isNone : Bool`, `isFloat : Bool`, `conv : Option ConvError`), so
#   every input point is a closed literal and every witness below `decide`s.
#
#   The postcondition is a conjunction of four INDEPENDENT top-level clauses,
#   read in precedence order. Each is attacked by at least one rival:
#     (C1) v.isNone = true → result = returned
#          -- the missing value passes straight through.        attacked by: drop-absent-guard,
#                       absent-float-malformed-escapes
#     (C2) v.isNone = false → v.isFloat = true → result = returned
#          -- a floating-point value returns normally.          attacked by: float-branch-rejects
#     (C3) v.isNone = false → v.isFloat = false → v.conv = none →
#          result = returned
#          -- a value that interprets cleanly returns normally. attacked by: clean-conv-rejects
#     (C4) v.isNone = false → v.isFloat = false → v.conv.isSome = true →
#          result = validationError
#          -- EVERY low-level interpretation failure, whatever its kind, is
#             reported as the ONE uniform validation error.
#          attacked by: partial-handler-notanumber-only, partial-handler-drops-unsupported,
#                       cflow-swallow-failure, cflow-propagate-raw
#     (C2>C4) the PRECEDENCE between the clauses: C2 carries no `conv`
#          hypothesis, so a floating-point value returns normally however its
#          interpretation would behave.        attacked by: precedence-conv-before-float
#          -- added by audit: every other rival is wrong on a whole COLUMN of the
#             carrier and so is refutable where one clause acts alone; this is the
#             only case where two clauses are simultaneously applicable and the
#             spec's ordering is what decides.
#     (C1>C2,C4) C1 carries NEITHER an `isFloat` nor a `conv` hypothesis, so a
#          missing value returns normally however the other two features read.
#          attacked by: absent-float-malformed-escapes
#          -- added by the second audit: wrong at exactly ONE of the 16 carrier
#             points, and correct at all seven the other cases witness at, so it
#             shows the spec discriminates at single-point granularity on the
#             missing-value clause rather than only column-wise.
#
#   ADMISSIBILITY lane (admiss-ground-instances): the frozen obligation binds no
#   precondition, but the analogue on a TOTAL carrier is the obligation being
#   UNSATISFIABLE at exactly an F2P/P2P-shaped input. Six ground instances — one
#   per clause, at the input shapes the real tests drive — are discharged BY
#   EVALUATION as `have`s before the frozen obligation is closed verbatim, so a
#   clause unsatisfiable at a normal input fails there and nowhere else. The
#   soundness lane does not subsume this: it quantifies over an ABSTRACT `v` and
#   never computes the spec's verdict at a named input.
#
#   C4 is the load-bearing clause and the one the instance is about: it is
#   universally quantified over the failure kind via `v.conv.isSome`, so it pins
#   EVERY kind of low-level failure, not a majority. `Outcome` carries a third
#   constructor, `propagated`, precisely so that "a low-level failure escapes
#   uncaught" is a DISTINCT observable from "the uniform validation error is
#   reported" — the raise-vs-raise-what discriminator that C4 needs.
#
# ---------------------------------------------------------------------------
# Refinement ground truth (mapping.md / refinement.md / instance.json)
# ---------------------------------------------------------------------------
#   v.isNone   <- the value is the missing value
#   v.isFloat  <- the value is a floating-point number (consulted only when not
#                 the missing value)
#   v.conv     <- how interpreting the value as a decimal behaves: `none` = it
#                 yields a decimal; `some e` = it fails at the low level with a
#                 failure of kind `e`. The three `ConvError` kinds are the three
#                 distinct natures of an unusable value (a value that looks
#                 number-like but is not a well-formed decimal literal; a value
#                 whose type cannot stand for a number at all; a structurally
#                 malformed value). G-CONF derives `v.conv` for a real value by
#                 actually running the conversion, so the bijection is validated.
#   result     <- the observable outcome: a normal return, the uniform
#                 validation error, or a low-level failure escaping uncaught.
#
#   F2P test_invalid_value cleans each of eight unusable values and requires a
#   ValidationError from every one. Those eight span the failure taxonomy: the
#   dict / set / object / complex / byte-string values are the
#   type-cannot-stand-for-a-number kind (`unsupportedType`, and the dict is the
#   exact value the problem statement reports), the empty tuple and empty list
#   are the structurally-malformed kind (`malformedValue`), and the non-numeric
#   string is the not-a-well-formed-literal kind (`notANumber`). So a rival that
#   is correct on a SUBSET of the failure kinds still fails that F2P test on the
#   sub-domain it drops — which is why C4's quantification over the kind, and not
#   merely over "some failure occurred", is what the battery must defend.
#   P2P test_to_python additionally observes that a missing value, a
#   floating-point value and a cleanly-interpreting value all return normally
#   (clauses C1-C3).
#
# The nagini AXIOM_TESTS lane is intentionally NOT ported: the axiom lane is
# G-AX's job and this gate ignores it. (On this bundle it is moot anyway —
# `axioms = []`, the conversion is modeled deeply, and axiom_check.py is a skip
# stub.)
from pathlib import Path

INSTANCE = "django__django-13023"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact frozen impl body — everything strictly inside -- impl-start/-- impl-end.
_GOLD_IMPL = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError"""

# The exact frozen proof body — everything strictly inside -- proof-start/-- proof-end
# BELOW the `theorem correct_toPython` statement. Only the tactic script is ever
# replaced; the statement itself is never touched by any case.
_GOLD_PROOF = """  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · simp only [Id.run, h1, if_true]; rfl
  · intro h2; simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl
  · intro h2 h3
    simp only [Id.run, h1, h2, Bool.false_eq_true, if_false, h3]; rfl
  · intro h2 h3
    cases hcv : v.conv with
    | none => rw [hcv] at h3; simp at h3
    | some e => simp only [Id.run, h1, h2, Bool.false_eq_true, if_false]; rfl"""

# The frozen impl region body INCLUDING the `def` line (the whole text strictly
# inside -- impl-start/-- impl-end). A reshape that drops the `Id.run do` wrapper
# must restate the signature, so it replaces this rather than just the body.
_GOLD_DEF_AND_IMPL = (
    "def implementation_toPython (v : Value) : Outcome := Id.run do\n" + _GOLD_IMPL)

assert _GOLD_IMPL in _BASE, "frozen impl block drifted from Solution.lean"
assert _GOLD_PROOF in _BASE, "frozen proof block drifted from Solution.lean"
assert _GOLD_DEF_AND_IMPL in _BASE, "frozen impl region drifted from Solution.lean"


def _rival(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (frozen proof carried over).

    The carried-over proof will not close against a reshaped impl — that is
    expected and is exactly why every reject case also ships a `witness`, which
    is what actually attributes the rejection to the spec.
    """
    return _swap(_BASE, _GOLD_IMPL, new_impl)


def _positive(new_impl: str, new_proof: str) -> str:
    """Solution.lean with the impl body AND the tactic script replaced.

    The `theorem correct_toPython` statement is outside both anchors, so it stays
    byte-identical: the variant reproves the SAME obligation.
    """
    return _swap(_swap(_BASE, _GOLD_IMPL, new_impl), _GOLD_PROOF, new_proof)


def _ground_positive(ground: str) -> str:
    """Solution.lean with `ground` PREPENDED to the frozen tactic script.

    The frozen impl and the frozen closing script are both carried over verbatim;
    the case adds only `have`s that discharge the spec predicate at concrete
    inputs before the untouched frozen obligation is closed. No new declaration,
    no helper lemma, statement byte-identical — so this is strictly proof-region
    surgery and `markers.same_spec` holds exactly as for every other case.
    """
    return _swap(_BASE, _GOLD_PROOF, ground + _GOLD_PROOF)


def _positive_region(new_region: str, new_proof: str) -> str:
    """Like `_positive`, but replaces the WHOLE impl region body.

    The impl region body is `def implementation_toPython ... := <body>`, so the
    `def` line is inside it and a variant may restate the signature — which is
    what a reshape that drops the `Id.run do` monadic wrapper has to do. Still
    strictly region surgery: the spec view elides the impl region entirely, so
    `markers.same_spec` holds exactly as for the other cases, and the
    `theorem correct_toPython` statement is untouched.
    """
    return _swap(_swap(_BASE, _GOLD_DEF_AND_IMPL, new_region),
                 _GOLD_PROOF, new_proof)


def _witness(is_none: str, is_float: str, conv: str) -> str:
    """`¬ problem_spec_<f> <input> (implementation_<f> <input>)` at a literal point.

    Every feature of the carrier is a closed decidable literal, so the refutation
    needs no hypothesis binder and no conditioning on an opaque term: `decide`
    settles it outright. With no binders there is nothing that could be
    inconsistent, so these witnesses cannot be the `witness-inconsistent`
    forgery — the "counterexample input" is exhibited, not assumed.
    """
    v = f"{{ isNone := {is_none}, isFloat := {is_float}, conv := {conv} }}"
    return f"""example : ¬ problem_spec_toPython
    {v}
    (implementation_toPython
      {v}) := by
  unfold problem_spec_toPython implementation_toPython
  decide"""


# ===========================================================================
# (1) SOUNDNESS — the uniform-handler shape stated as ONE test on "did the
# interpretation fail at all", rather than a match on the failure value. This is
# the closest carrier-level analogue of the nagini sibling's
# pos-control-combined-except: a SINGLE decision covering the whole rejection
# set instead of a per-kind dispatch. Observationally identical; MUST verify.
# ===========================================================================
_POS_ISSOME_TEST_IMPL = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  if v.conv.isSome then
    return Outcome.validationError
  return Outcome.returned"""

_POS_ISSOME_TEST_PROOF = """  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · simp [Id.run, h1] <;> rfl
  · intro h2; simp [Id.run, h1, h2] <;> rfl
  · intro h2 h3; simp [Id.run, h1, h2, h3] <;> rfl
  · intro h2 h3; simp [Id.run, h1, h2, h3] <;> rfl"""

# ===========================================================================
# (2) SOUNDNESS — the two disjoint normal-return fast paths are REORDERED (the
# floating-point test runs before the missing-value test). Ports the nagini
# sibling's pos-control-reorder-fastpaths. Note this is NOT a trivial reshape on
# this carrier: `isFloat` is specified as consulted only when the value is not
# missing, so the reorder is only sound because the missing-value case also
# returns normally — the proof has to case-split on `isFloat` to close C1, which
# the frozen script never does. MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_REORDER_IMPL = """  if v.isFloat then
    return Outcome.returned
  if v.isNone then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError"""

_POS_REORDER_PROOF = """  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · cases hf : v.isFloat with
    | true => simp [Id.run, hf] <;> rfl
    | false => simp [Id.run, hf, h1] <;> rfl
  · intro h2; simp [Id.run, h2] <;> rfl
  · intro h2 h3; simp [Id.run, h1, h2, h3] <;> rfl
  · intro h2 h3
    cases hcv : v.conv with
    | none => rw [hcv] at h3; simp at h3
    | some e => simp [Id.run, h1, h2, hcv] <;> rfl"""

# ===========================================================================
# (3) SOUNDNESS — every low-level failure kind gets its OWN explicit arm, all
# three reporting the same uniform validation error, instead of one wildcard arm.
# The dual of case (1): where (1) collapses the dispatch entirely, this one
# fully expands it. Both must verify, because the contract's whole point is that
# the kinds are treated identically — a spec that could tell a wildcard arm from
# three coincident explicit arms would be pinning the DISPATCH SHAPE rather than
# the behavior. MUST verify.
# ===========================================================================
_POS_EXPLICIT_ARMS_IMPL = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some ConvError.notANumber => return Outcome.validationError
  | some ConvError.unsupportedType => return Outcome.validationError
  | some ConvError.malformedValue => return Outcome.validationError"""

_POS_EXPLICIT_ARMS_PROOF = """  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · simp [Id.run, h1] <;> rfl
  · intro h2; simp [Id.run, h1, h2] <;> rfl
  · intro h2 h3; simp [Id.run, h1, h2, h3] <;> rfl
  · intro h2 h3
    cases hcv : v.conv with
    | none => rw [hcv] at h3; simp at h3
    | some e =>
      cases e <;> simp [Id.run, h1, h2, hcv] <;> rfl"""

# ===========================================================================
# (4) SOUNDNESS — the whole decision restated as a single simultaneous match on
# all three features of the carrier, with the precedence encoded in the arm
# patterns rather than in a sequence of early returns. Structurally the furthest
# from the frozen shape while staying observationally identical. MUST verify.
# ===========================================================================
_POS_SIMULTANEOUS_IMPL = """  match v.isNone, v.isFloat, v.conv with
  | true, _, _ => return Outcome.returned
  | false, true, _ => return Outcome.returned
  | false, false, none => return Outcome.returned
  | false, false, some _ => return Outcome.validationError"""

_POS_SIMULTANEOUS_PROOF = """  intro v
  unfold problem_spec_toPython implementation_toPython
  refine ⟨?_, ?_, ?_, ?_⟩ <;> intro h1
  · simp [Id.run, h1] <;> rfl
  · intro h2; simp [Id.run, h1, h2] <;> rfl
  · intro h2 h3; simp [Id.run, h1, h2, h3] <;> rfl
  · intro h2 h3
    cases hcv : v.conv with
    | none => rw [hcv] at h3; simp at h3
    | some e => simp [Id.run, h1, h2, hcv] <;> rfl"""

# ===========================================================================
# (4b) SOUNDNESS — added by audit. The four positives above all keep the frozen
# impl's `Id.run do` / early-return skeleton, and two of them (cases 1 and 4) are
# reductionally transparent: the FROZEN tactic script closes them verbatim, so
# they impose no new proof burden and cannot distinguish a spec that constrains
# behaviour from one that merely admits anything the frozen script happens to
# close. This positive abandons the monadic skeleton entirely — no `Id.run`, no
# `do`, no early return — and computes the rejection condition as a single
# BOOLEAN expression, so the outcome is decided by `&&`/`Option.isSome` rather
# than by any control flow. Nothing about the frozen impl's shape survives.
#
# Every clause still holds pointwise: the guard `!isNone && !isFloat && conv.isSome`
# is exactly C4's hypothesis conjunction, and its negation covers C1-C3, so the
# reshape is faithful. It is the strongest available evidence that the spec pins
# the input-output relation and not the skeleton. MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================
_POS_BOOLEAN_FORMULA_REGION = """def implementation_toPython (v : Value) : Outcome :=
  if !v.isNone && !v.isFloat && v.conv.isSome then
    Outcome.validationError
  else
    Outcome.returned"""

# Shape-independent script: split the carrier into its 16 points and let `simp`
# reduce whichever shape is present. No step names a frozen-impl construct.
_POS_BOOLEAN_FORMULA_PROOF = """  intro v
  obtain ⟨n, f, c⟩ := v
  cases n <;> cases f <;> cases c <;>
    refine ⟨?_, ?_, ?_, ?_⟩ <;>
    intros <;>
    simp_all [problem_spec_toPython, implementation_toPython, Id.run]"""

# ===========================================================================
# (5) UNIQUENESS — THE pre-patch echo. Only ONE of the three low-level failure
# kinds (the not-a-well-formed-literal kind) is turned into the uniform
# validation error; the other two escape uncaught. This is exactly
# Solution_prepatch.lean's impl. Ports the nagini sibling's
# weak-prepatch-only-malformed. MUST reject via C4 on the two dropped kinds.
# ===========================================================================
_RIVAL_ONLY_NOTANUMBER = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some ConvError.notANumber => return Outcome.validationError
  | some _ => return Outcome.propagated"""

# ===========================================================================
# (6) UNIQUENESS / PARTIAL DOMAIN — the NEAR MISS. Two of the three failure
# kinds are handled; only the type-cannot-stand-for-a-number kind escapes. Ports
# the nagini sibling's partial-domain-kind4-escape, and it is the sharpest rival
# in the battery because it is the one whose sub-domain is a single point: it
# agrees with the frozen solution everywhere except that one kind — which is the
# kind the reported value belongs to. Its witness therefore sits at exactly that
# point (where rival (5) is ALSO wrong, but where rival (5)'s own witness is
# not, keeping the two sub-domain claims separately demonstrated). MUST reject.
# ===========================================================================
_RIVAL_DROPS_UNSUPPORTED = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some ConvError.unsupportedType => return Outcome.propagated
  | some _ => return Outcome.validationError"""

# ===========================================================================
# (7) UNIQUENESS / CONTROL-FLOW EFFECT — SWALLOW every low-level failure and
# return normally instead of reporting it. Ports the nagini sibling's
# cflow-swallow-reject. On this carrier the discriminator is not an undeclared
# exception escape but the `Outcome` value itself: C4 demands
# `validationError` and this impl yields `returned`, so the spec sees
# report-vs-return directly. MUST reject.
# ===========================================================================
_RIVAL_SWALLOW = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.returned"""

# ===========================================================================
# (8) UNIQUENESS / CONTROL-FLOW EFFECT — let EVERY low-level failure escape
# uncaught instead of converting it to the uniform validation error. Ports the
# nagini sibling's cflow-reraise-raw: the literal anti-fix, and the total
# version of rivals (5)/(6). The spec pins the IDENTITY of what is reported
# (`validationError` vs `propagated`), not merely that something went wrong.
# MUST reject.
# ===========================================================================
_RIVAL_PROPAGATE_RAW = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.propagated"""

# ===========================================================================
# (9) UNIQUENESS / clause C1 — drop the missing-value guard entirely, so a
# missing value falls through to be interpreted as a decimal. No nagini
# counterpart (nagini's kind-0 leg is pinned by a value clause the Lean carrier
# abstracts to `returned`); authored here so C1 is attacked and so the `isNone`
# binder is MOVED by some witness rather than held at `false` throughout.
# MUST reject.
# ===========================================================================
_RIVAL_DROP_ABSENT_GUARD = """  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError"""

# ===========================================================================
# (10) UNIQUENESS / clause C2 — report the uniform validation error for a
# floating-point value instead of returning it normally. Attacks C2 and moves
# the `isFloat` binder. MUST reject.
# ===========================================================================
_RIVAL_FLOAT_REJECTS = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.validationError
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError"""

# ===========================================================================
# (11) UNIQUENESS / clause C3 — report the uniform validation error even when
# the value interprets CLEANLY. The over-rejecting mirror of rival (8): where
# (8) reports nothing, this reports everything. Attacks C3, and is the only
# rival whose witness holds `conv` at `none`. MUST reject.
# ===========================================================================
_RIVAL_CLEAN_CONV_REJECTS = """  if v.isNone then
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.validationError
  | some _ => return Outcome.validationError"""

# ===========================================================================
# (12) UNIQUENESS / clause PRECEDENCE (C2 over C4) — the interaction case, added
# by audit. Every rival above is wrong on a whole COLUMN of the carrier, so each
# is refutable at a point where only one clause is in play; none of them tests
# that C2 DOMINATES C4 when both are applicable. This rival is correct on every
# input the rest of the battery witnesses at — including a clean floating-point
# value, where float-branch-rejects is already wrong — and diverges only where a
# floating-point value's interpretation WOULD fail: it consults `conv` before
# honouring the floating-point fast path, so it reports the uniform validation
# error for a value C2 says must return normally.
#
# The spec reads the features in precedence order (`isFloat` is consulted only
# when the value is not missing; `conv` only when it is neither missing nor
# floating-point), so C2 has no `conv` hypothesis at all and pins `returned` for
# EVERY floating-point value regardless of what interpreting it would do. Without
# this case a patch that inspects the value's convertibility before taking the
# floating-point path — the natural way to get the precedence backwards — sails
# through the battery. MUST reject.
# ===========================================================================
_RIVAL_CONV_BEFORE_FLOAT = """  if v.isNone then
    return Outcome.returned
  match v.conv with
  | some _ => return Outcome.validationError
  | none => return Outcome.returned"""

# ===========================================================================
# (13) UNIQUENESS / clause PRECEDENCE (C1 over the rest) — added by the SECOND
# audit. The battery's precedence case (12) tests that C2 dominates C4, and
# drop-absent-guard (9) attacks C1 by removing its guard on a whole COLUMN. What
# neither tests is that C1 dominates where it OVERLAPS C2: C1 carries no
# `isFloat` hypothesis and no `conv` hypothesis, so it pins `returned` for a
# missing value however the other two features read. This rival keeps the
# missing-value guard in place and honours it everywhere the rest of the battery
# looks — it is wrong at EXACTLY ONE of the 16 carrier points, the missing value
# that is also floating-point and whose interpretation would be structurally
# malformed — where it lets the low-level failure escape instead of returning
# normally.
#
# It is the sharpest near-miss in the battery: 15/16 agreement with the frozen
# solution, and correct at all seven points the other twelve cases witness at, so
# nothing else here refutes it. Its purpose is to show the spec discriminates at
# SINGLE-POINT granularity on the missing-value clause specifically, and to move
# the `isFloat` binder to `true` while `isNone` is ALSO `true` — a combination no
# other witness in the battery reaches. MUST reject.
# ===========================================================================
_RIVAL_ABSENT_FLOAT_MALFORMED_ESCAPES = """  if v.isNone then
    if v.isFloat then
      match v.conv with
      | some ConvError.malformedValue => return Outcome.propagated
      | _ => return Outcome.returned
    return Outcome.returned
  if v.isFloat then
    return Outcome.returned
  match v.conv with
  | none => return Outcome.returned
  | some _ => return Outcome.validationError"""

# ===========================================================================
# ADMISSIBILITY — added by the SECOND audit. The battery shipped with NO
# admissibility case, recorded as vacuous because the frozen obligation has no
# precondition binder. That reason is not sufficient: on a TOTAL carrier the
# analogue of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly
# an F2P/P2P-shaped input, which is a distinct failure from either of the other
# two lanes and is tested directly by discharging the spec predicate at those
# concrete inputs BY EVALUATION, as `have`s, before closing the frozen obligation
# verbatim.
#
# It is not implied by the soundness lane. A soundness case proves
# `∀ v, spec v (impl v)` for a reshaped impl — a statement that would still hold
# if some clause were unsatisfiable at a point the impl never reaches, and one
# that is discharged by tactics operating on an ABSTRACT `v` rather than by
# computing the spec's verdict at a named input. These `have`s instead pin the
# CONCRETE outcome the spec assigns at each of the six input shapes the F2P and
# P2P tests actually exercise, so a clause that could not be satisfied at one of
# them would fail here and nowhere else in the battery.
#
# One ground instance per clause, at the input shapes the real tests drive:
#   * the three low-level failure kinds, each of which the F2P invalid-value test
#     supplies (they span the whole failure taxonomy) and each of which must be
#     answerable as the ONE uniform validation error   -> C4, three times;
#   * a value that interprets cleanly                  -> C3;
#   * a floating-point value                           -> C2;
#   * the missing value                                -> C1.
# Nothing is assumed: no new declaration, no helper lemma, the theorem statement
# is byte-identical, and the frozen tactic script closes the obligation
# unchanged below the `have`s. MUST verify.
# ===========================================================================
_ADMISS_GROUND = """  -- Ground instances at F2P/P2P-shaped inputs, each discharged by EVALUATION
  -- (`decide` computes the spec's verdict at the literal input) before the
  -- frozen obligation is closed verbatim below. If any clause were unsatisfiable
  -- at the input shape the real tests drive, the corresponding `have` would fail.
  have _f2p_unsupported : problem_spec_toPython
      { isNone := false, isFloat := false, conv := some ConvError.unsupportedType }
      Outcome.validationError := by
    unfold problem_spec_toPython; decide
  have _f2p_malformed : problem_spec_toPython
      { isNone := false, isFloat := false, conv := some ConvError.malformedValue }
      Outcome.validationError := by
    unfold problem_spec_toPython; decide
  have _f2p_notanumber : problem_spec_toPython
      { isNone := false, isFloat := false, conv := some ConvError.notANumber }
      Outcome.validationError := by
    unfold problem_spec_toPython; decide
  have _p2p_clean : problem_spec_toPython
      { isNone := false, isFloat := false, conv := none }
      Outcome.returned := by
    unfold problem_spec_toPython; decide
  have _p2p_float : problem_spec_toPython
      { isNone := false, isFloat := true, conv := none }
      Outcome.returned := by
    unfold problem_spec_toPython; decide
  have _p2p_absent : problem_spec_toPython
      { isNone := true, isFloat := false, conv := none }
      Outcome.returned := by
    unfold problem_spec_toPython; decide
"""


SPEC_TESTS = [
    # ---------------- soundness / admissibility (expect="verify") ----------
    {
        "id": "pos-uniform-issome-test",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_ISSOME_TEST_IMPL, _POS_ISSOME_TEST_PROOF),
        "rationale": (
            "Structurally-different CORRECT impl: the failure set is decided by a "
            "SINGLE test on whether the interpretation failed at all, rather than "
            "by a per-kind dispatch, and the normal return becomes the fall-through "
            "instead of a match arm. This is the carrier-level analogue of the "
            "nagini sibling's single-handler positive (pos-control-combined-except): "
            "one decision covering the whole rejection set. Every clause C1-C4 is "
            "preserved pointwise, and C4 in particular is discharged from "
            "`v.conv.isSome` directly — the exact hypothesis the clause supplies. "
            "The obligation `theorem correct_toPython` is reproved with an "
            "identical statement. MUST verify, else SPEC-TOO-STRONG: the spec would "
            "be pinning the dispatch shape rather than the behavior."
        ),
    },
    {
        "id": "pos-reorder-normal-fastpaths",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_REORDER_IMPL, _POS_REORDER_PROOF),
        "rationale": (
            "Structurally-different CORRECT impl: the two normal-return fast paths "
            "are reordered so the floating-point test precedes the missing-value "
            "test. Ports the nagini sibling's pos-control-reorder-fastpaths. Both "
            "orders agree on every input because both fast paths produce the same "
            "outcome, but the reorder is NOT a free reshape here — the spec states "
            "`isFloat` as consulted only when the value is not missing, so closing "
            "C1 now needs a case split on `isFloat` that the frozen script never "
            "performs. MUST verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-explicit-arm-per-failure-kind",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_EXPLICIT_ARMS_IMPL, _POS_EXPLICIT_ARMS_PROOF),
        "rationale": (
            "Structurally-different CORRECT impl: each low-level failure kind gets "
            "its OWN explicit arm, all three reporting the same uniform validation "
            "error, where the frozen impl uses one wildcard arm. The exact dual of "
            "pos-uniform-issome-test (which collapses the dispatch instead of "
            "expanding it), and together they bracket the frozen shape from both "
            "sides. Both must verify precisely BECAUSE the contract's content is "
            "that the kinds are indistinguishable to a caller: a spec that could "
            "separate three coincident explicit arms from one wildcard arm would be "
            "over-pinning. The proof must additionally case on the failure kind. "
            "MUST verify (else SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "pos-simultaneous-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(_POS_SIMULTANEOUS_IMPL, _POS_SIMULTANEOUS_PROOF),
        "rationale": (
            "Structurally-different CORRECT impl: the entire decision is restated "
            "as one simultaneous match over all three features of the carrier, with "
            "the precedence encoded in the arm patterns rather than in a sequence "
            "of early returns — no sequential control flow left at all. "
            "MUST verify (else SPEC-TOO-STRONG). NOTE (audit): this reshape is "
            "reductionally TRANSPARENT — the frozen tactic script closes it "
            "verbatim (measured: grafting this impl under the frozen proof "
            "elaborates, exit 0), because Lean's `match` on the three fields and "
            "the frozen chain of `if`s reduce to the same term. So it imposes no "
            "new proof burden and is a weaker positive than its shape suggests; "
            "pos-boolean-formula is the case that actually forces a fresh proof. "
            "Kept because a transparent reshape is still a real (if cheap) "
            "same-spec admissibility check, not because it is the strongest one."
        ),
    },
    {
        "id": "pos-boolean-formula",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive_region(_POS_BOOLEAN_FORMULA_REGION,
                                  _POS_BOOLEAN_FORMULA_PROOF),
        "rationale": (
            "Structurally-different CORRECT impl, added by AUDIT to close a real "
            "gap: the four original positives all keep the frozen `Id.run do` / "
            "early-return skeleton, and two of them are reductionally transparent "
            "(the frozen tactic script closes them verbatim), so none of them "
            "established that the spec is provable against a genuinely different "
            "computation. This impl drops the monad, the `do` block and every "
            "early return, deciding the outcome from ONE boolean expression "
            "(`!isNone && !isFloat && conv.isSome`) — which is precisely C4's "
            "hypothesis conjunction, its negation covering C1-C3, so the reshape "
            "is faithful pointwise. Its proof cannot reuse any frozen step: it "
            "case-splits the carrier and discharges each of the 16 points, and "
            "the frozen script does NOT close it. MUST verify (else "
            "SPEC-TOO-STRONG: the spec would be pinning the skeleton)."
        ),
    },

    # ---------------- admissibility (expect="verify") ----------------------
    {
        "id": "admiss-ground-instances",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ground_positive(_ADMISS_GROUND),
        "rationale": (
            "ADMISSIBILITY, added by the SECOND audit — the battery shipped with "
            "this lane empty, so PRECOND-TOO-STRONG, one of the three directions "
            "this gate exists to test, went untested. The recorded reason (the "
            "frozen obligation binds no precondition) is not sufficient: on a "
            "TOTAL carrier the analogue is the obligation being UNSATISFIABLE at "
            "exactly an F2P/P2P-shaped input, and that is what this case tests "
            "directly. Six ground instances, one per clause at the input shapes "
            "the real tests drive — each of the three low-level failure kinds "
            "(C4, the kinds the invalid-value test supplies, which span the whole "
            "failure taxonomy), a cleanly-interpreting value (C3), a "
            "floating-point value (C2) and the missing value (C1) — are each "
            "discharged BY EVALUATION as a `have`, pinning the CONCRETE outcome "
            "the spec assigns there, before the frozen obligation is closed "
            "verbatim. This is not implied by the soundness lane: a soundness "
            "case proves `∀ v, spec v (impl v)` over an ABSTRACT `v` and would "
            "still hold if a clause were unsatisfiable at a point the impl never "
            "reaches, whereas these `have`s compute the spec's verdict at named "
            "inputs. Nothing is assumed: no new declaration, no helper lemma, "
            "statement byte-identical, frozen impl and closing script carried "
            "over unchanged. MUST verify, else the modeled behaviour is "
            "unsatisfiable at a normal input it must admit."
        ),
    },

    # ---------------- uniqueness (expect="reject") -------------------------
    {
        "id": "partial-handler-notanumber-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_ONLY_NOTANUMBER),
        "witness": _witness("false", "false", "some ConvError.malformedValue"),
        "refinement": (
            "This IS the pre-patch behaviour, and it is byte-for-byte the impl of "
            "Solution_prepatch.lean (documented to fail G-DIFF). Only the "
            "not-a-well-formed-literal failure kind is reported as a validation "
            "error; the type-cannot-stand-for-a-number kind and the "
            "structurally-malformed kind escape uncaught. Its faithful real patch "
            "therefore does NOT resolve: F2P test_invalid_value cleans eight "
            "unusable values and requires a ValidationError from each, but six of "
            "the eight (the dict — the exact value the problem statement reports — "
            "plus the set, object, complex and byte-string values, and the empty "
            "tuple and empty list) belong to the two dropped kinds and would "
            "surface a raw low-level error instead. So if this rival VERIFIED it "
            "would be a true verify-does-not-imply-resolve break, not an artifact."
        ),
        "rationale": (
            "UNIQUENESS against C4, which is quantified over the failure kind via "
            "`v.conv.isSome` and so pins EVERY kind, not a majority. The witness "
            "instantiates C4 at the structurally-malformed kind, where this impl "
            "yields `propagated` while C4 demands `validationError` — `decide` "
            "settles the negation outright. Held at that point the frozen solution "
            "satisfies the spec, so the witness fails on gold: a genuine "
            "discriminator, not a tautology. If this verified, the spec would admit "
            "the pre-patch behaviour => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "partial-handler-drops-unsupported",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_DROPS_UNSUPPORTED),
        "witness": _witness("false", "false", "some ConvError.unsupportedType"),
        "refinement": (
            "The NEAR MISS, and the rival closest to the real defect: TWO of the "
            "three low-level failure kinds are handled and only the "
            "type-cannot-stand-for-a-number kind still escapes. Its faithful real "
            "patch widens the recognized failure set but not far enough, so "
            "test_invalid_value still fails on exactly the sub-domain the problem "
            "statement is about — cleaning the dict (and the set / object / complex "
            "/ byte-string values) surfaces a raw TypeError rather than a "
            "ValidationError. The empty-tuple, empty-list and non-numeric-string "
            "values would pass, which is what makes this rival dangerous: it is "
            "correct on most of the F2P input list and still does not resolve."
        ),
        "rationale": (
            "PARTIAL-DOMAIN uniqueness against C4. Because this rival agrees with "
            "the frozen solution on strictly MORE of the domain than "
            "partial-handler-notanumber-only does, it gets its own witness at the "
            "single point where it is wrong — the type-cannot-stand-for-a-number "
            "kind — rather than sharing one. That point is where the other partial "
            "rival's witness is NOT located, so each rival's claimed sub-domain is "
            "demonstrated separately instead of one witness standing in for both. "
            "C4 demands `validationError` there and this impl yields `propagated`. "
            "A spec pinning only a subset of the failure kinds would be "
            "SPEC-TOO-WEAK; this case is what shows it does not."
        ),
    },
    {
        "id": "cflow-swallow-failure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_SWALLOW),
        "witness": _witness("false", "false", "some ConvError.notANumber"),
        "refinement": (
            "A patch that notices the low-level failure and RETURNS normally "
            "instead of reporting it silently accepts an unusable value. F2P "
            "test_invalid_value asserts a ValidationError is raised for all eight "
            "values and would fail on every one of them, since nothing is raised "
            "at all; it also corrupts every downstream consumer expecting a "
            "decimal. Strictly worse than the pre-patch behaviour, which at least "
            "surfaced something."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT uniqueness against C4. On the nagini carrier this "
            "was a raise-vs-return distinction visible only because the contract "
            "pinned the normal-return domain; on this carrier the distinction is "
            "carried by the `Outcome` value itself, so C4 sees it directly: at the "
            "witnessed point C4 demands `validationError` and this impl yields "
            "`returned`. The witness is placed at the not-a-well-formed-literal "
            "kind — a point where BOTH partial-handler rivals are correct — so it "
            "cannot be confused with their sub-domain claims. This rival and "
            "cflow-propagate-raw share that input legitimately: neither is a near "
            "miss of the other, both are wrong on the ENTIRE failure sub-domain "
            "and for the same reason (C4's demanded outcome is not produced), so "
            "no point discriminates them more sharply than any other."
        ),
    },
    {
        "id": "cflow-propagate-raw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_PROPAGATE_RAW),
        "witness": _witness("false", "false", "some ConvError.notANumber"),
        "refinement": (
            "Dropping the handler entirely is the literal anti-fix: every low-level "
            "failure reaches the caller raw. F2P test_invalid_value fails on all "
            "eight values, each surfacing an assorted low-level error instead of the "
            "ValidationError the test demands — the very situation the problem "
            "statement describes as making the offending field hard to track down. "
            "The total version of the two partial rivals."
        ),
        "rationale": (
            "CONTROL-FLOW-EFFECT uniqueness against C4, pinning the IDENTITY of "
            "what is reported rather than merely that something went wrong: the "
            "carrier's `Outcome` separates `validationError` from `propagated` "
            "precisely so a low-level failure escaping uncaught is a distinct "
            "observable, and C4 requires the former. The witness instantiates it at "
            "the not-a-well-formed-literal kind, where this impl yields "
            "`propagated`. Note this rival is refuted where cflow-swallow-failure "
            "is refuted, but by a DIFFERENT wrong outcome (`propagated` vs "
            "`returned`) — if the spec only forbade one of the two, the other would "
            "verify. If either verified => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "drop-absent-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_DROP_ABSENT_GUARD),
        "witness": _witness("true", "false", "some ConvError.unsupportedType"),
        "refinement": (
            "A patch that omits the missing-value guard sends the missing value on "
            "to be interpreted as a decimal, where it is an unusable value and so "
            "is reported as a validation error. The missing value must instead pass "
            "straight through unchanged: P2P test_to_python and test_get_prep_value "
            "both observe that, and rejecting it would break the entire "
            "null-permitted path (any save of a model whose field is legitimately "
            "unset), so the faithful real patch does not resolve."
        ),
        "rationale": (
            "UNIQUENESS against C1, the clause no nagini case has a counterpart "
            "for on this carrier (nagini pins its absent leg with a value clause "
            "that the Lean model abstracts to `returned`), so this rival is "
            "authored fresh for the port. It is also the ONLY case whose witness "
            "moves the `isNone` binder to `true`: without it every witness would "
            "hold `isNone = false` and a rival mishandling the missing value would "
            "sail through the battery unnoticed. The witness sets `isNone = true` "
            "with a failing interpretation underneath, so C1 demands `returned` "
            "while this impl reaches the failure branch and yields "
            "`validationError`. Gold satisfies C1 there, so the witness fails on "
            "gold."
        ),
    },
    {
        "id": "float-branch-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_FLOAT_REJECTS),
        "witness": _witness("false", "true", "none"),
        "refinement": (
            "A patch reporting a validation error for a floating-point value "
            "rejects input that must convert cleanly. P2P test_to_python converts "
            "several floating-point values and asserts the resulting decimals "
            "(including the rounding behaviour), so it fails outright: the faithful "
            "real patch does not resolve. Over-rejection is as much a defect as "
            "under-rejection, and only the positives would not catch it."
        ),
        "rationale": (
            "UNIQUENESS against C2. The only case whose witness moves the "
            "`isFloat` binder to `true`, so it is what stops `isFloat` from being "
            "held at a single value across the whole battery. C2 demands `returned` "
            "for a non-missing floating-point value and this impl yields "
            "`validationError`; `decide` refutes the conjunction at that literal "
            "point. Held there gold satisfies the spec, so the witness fails on "
            "gold. If it verified, C2 would be unconstraining => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "clean-conv-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_CLEAN_CONV_REJECTS),
        "witness": _witness("false", "false", "none"),
        "refinement": (
            "A patch that reports a validation error even when the value "
            "interprets cleanly rejects every usable value. P2P test_to_python "
            "asserts the decimals produced for a plain integer and a numeric "
            "string, and test_filter_with_strings / test_save_without_float_conversion "
            "depend on clean interpretation too, so the faithful real patch fails "
            "them all and does not resolve. This is the over-rejecting mirror of "
            "cflow-propagate-raw: an implementation can be wrong by widening the "
            "reported-failure set as easily as by narrowing it, and a spec that "
            "only defended one direction would admit the other."
        ),
        "rationale": (
            "UNIQUENESS against C3, and the only case whose witness holds `conv` "
            "at `none` — every other witness sets it to `some _`, so without this "
            "one the clean-interpretation sub-domain would be probed by no rival "
            "at all and C3 would go unattacked. C3 demands `returned` when the "
            "interpretation succeeds and this impl yields `validationError`. Gold "
            "satisfies C3 there, so the witness discriminates."
        ),
    },
    {
        "id": "precedence-conv-before-float",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_CONV_BEFORE_FLOAT),
        "witness": _witness("false", "true", "some ConvError.notANumber"),
        "refinement": (
            "A patch that decides convertibility BEFORE honouring the "
            "floating-point fast path reports a validation error for a "
            "floating-point value that a general-purpose decimal interpretation "
            "cannot parse, even though such a value must convert directly and "
            "return normally. P2P test_to_python converts floating-point values "
            "and asserts the resulting decimals, so the faithful real patch fails "
            "it on exactly that input class while still passing every invalid-value "
            "assertion — a defect no other rival in this battery would catch."
        ),
        "rationale": (
            "PRECEDENCE / CLAUSE-INTERACTION uniqueness, added by AUDIT. Every "
            "other rival is wrong on a whole COLUMN of the carrier and so is "
            "refutable at a point where a single clause is in play; none tests "
            "that C2 DOMINATES C4 where both are applicable. C2 carries no `conv` "
            "hypothesis, so it pins `returned` for EVERY non-missing "
            "floating-point value irrespective of what interpreting it would do — "
            "this rival is the minimal violation of that ordering. It agrees with "
            "the frozen solution at all six points the rest of the battery "
            "witnesses at (including the clean floating-point value where "
            "float-branch-rejects is already wrong), so its own witness is the "
            "only thing that refutes it: `isFloat = true` with a failing "
            "interpretation underneath, where C2 demands `returned` and this impl "
            "yields `validationError`. Gold satisfies C2 there, so the witness "
            "discriminates. Without this case a patch that gets the precedence "
            "backwards verifies => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "absent-float-malformed-escapes",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(_RIVAL_ABSENT_FLOAT_MALFORMED_ESCAPES),
        "witness": _witness("true", "true", "some ConvError.malformedValue"),
        "refinement": (
            "A patch that honours the missing-value guard in general but consults "
            "the value's other features underneath it lets a low-level failure "
            "escape for a missing value, instead of passing it straight through "
            "unchanged. The missing value must return unchanged unconditionally: "
            "P2P test_to_python and test_get_prep_value both observe that, and any "
            "save of a model whose field is legitimately unset would surface a raw "
            "low-level error rather than storing nothing — so the faithful real "
            "patch does not resolve. It is a subtler defect than dropping the "
            "guard outright, because it is correct on every input the rest of the "
            "battery exercises."
        ),
        "rationale": (
            "PRECEDENCE / SINGLE-POINT uniqueness against C1, added by the SECOND "
            "audit. C1 carries NEITHER an `isFloat` nor a `conv` hypothesis, so it "
            "pins `returned` for a missing value however the other two features "
            "read; drop-absent-guard attacks C1 by removing its guard on a whole "
            "COLUMN, and precedence-conv-before-float tests C2 over C4, but "
            "nothing tested C1's dominance where it OVERLAPS the later clauses. "
            "This rival is wrong at EXACTLY ONE of the 16 carrier points "
            "(measured: 15/16 agreement with the frozen solution) and is correct "
            "at all seven points the other twelve cases witness at, so its own "
            "witness is the only thing in the battery that refutes it — which is "
            "what makes it evidence that the spec discriminates at single-point "
            "granularity rather than merely column-wise. It is also the only case "
            "whose witness holds `isNone` and `isFloat` BOTH at `true`, a "
            "combination no other witness reaches. C1 demands `returned` there and "
            "this impl yields `propagated`; `decide` settles the negation at the "
            "literal point, and gold satisfies C1 there so the witness "
            "discriminates. Measured: witness exit 0 against the rival, exit 1 "
            "against the frozen solution with a plain evaluation refutation, and "
            "the flipped-claim forgery inverts both (gold 0, rival 1) — so gold's "
            "exit code tracks the CLAIM, not the shape."
        ),
    },
]
