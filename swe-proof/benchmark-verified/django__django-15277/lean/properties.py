# properties.py — G-PBT falsification battery for django__django-15277 (lean lane).
#
# NOT a Lean module: a manifest of adversarial cases the gate elaborates against
# the FROZEN spec. Ported from the nagini sibling's properties.py, re-expressed
# against this backend's carrier. Every case is a complete Solution.lean that
# differs from the frozen file ONLY inside the impl region (and, where a reshaped
# impl needs it, the proof tactic body); the `theorem correct_*` STATEMENT and the
# whole spec view are byte-identical, so markers.same_spec holds by construction
# and any rejection is attributable to the postcondition rather than to a tampered
# spec.
#
# ---------------------------------------------------------------------------
# Defended surface (read from Solution.lean)
# ---------------------------------------------------------------------------
#   implementation_buildFieldValidators
#     (maxLength : Option Int) (base : List Validator) : List Validator
#
#   problem_spec_buildFieldValidators maxLength base result :=
#     result = base ++ (match maxLength with
#                       | none   => []
#                       | some n => [Validator.lengthBound (some n)])
#
# ONE obligation, ONE top-level clause — but that clause is a FULL list equality,
# so it is load-bearing in four independent ways, and a rival can miss any one of
# them while satisfying the other three:
#   (K1) PRESENCE  — a length-bound validator is appended when, and only when, a
#        maximum length is declared (`some n` appends one, `none` appends none).
#   (K2) CARRIED BOUND — the appended validator carries the DECLARED bound
#        `some n`, not a different value and not an absent bound.
#   (K3) PREFIX PRESERVED — the incoming validators survive unchanged; the result
#        is `base ++ …`, so nothing may be dropped or replaced.
#   (K4) ORDER — the appended validator goes at the END; `base` is a PREFIX.
# The battery attacks all four (K1: weak-never-attaches, weak-attaches-always,
# and weak-guard-on-incoming-list; K2: weak-bound-off-by-one, weak-bound-absent;
# K3: weak-clobbers-incoming; K4: weak-prepends). A fifth thing the clause pins,
# added by the audit because no original rival probed it: PRESENCE is independent
# of `base` — whether the validator is appended is decided by `maxLength` alone
# (weak-guard-on-incoming-list). Both input binders are varied across the reject
# witnesses: `maxLength` over {none, some 2, some 4, some 5, some 7, some 9} and
# `base` over {[], [basic 3], [basic 7], [basic 1, basic 2]} — seven probe points.
#
# What that variation does and does NOT buy (MEASURED). Two earlier revisions of
# this header over-claimed here, so the matrix below is stated as measured rather
# than as designed. It was obtained by evaluating the decidable spec predicate for
# GOLD plus all SEVEN rivals at all SEVEN witness points in ONE `#eval` matrix
# (exit 0); gold holds at all seven, which is the sanity leg. Points are
#   p0=(none,[])              p1=(some 5,[])          p2=(some 7,[])
#   p3=(some 4,[])            p4=(some 5,[basic 3])
#   p5=(some 9,[basic 1,basic 2])                     p6=(some 2,[basic 7])
#
#     rival                     its own witness point      refuted at
#     weak-attaches-always      p0                         {p0}
#     weak-never-attaches       p1                         {p1..p6}
#     weak-bound-off-by-one     p2                         {p1..p6}
#     weak-bound-absent         p3                         {p1..p6}
#     weak-clobbers-incoming    p4                         {p4,p5,p6}
#     weak-prepends             p5                         {p4,p5,p6}
#     weak-guard-on-incoming-list p6                       {p4,p5,p6}
#
# So the seven points are NOT seven independent discriminations. Two groups share
# a refutation set EXACTLY: {never-attaches, bound-off-by-one, bound-absent} are
# refuted at every declared-maximum point, and {clobbers, prepends,
# guard-on-incoming-list} are refuted at exactly the three non-empty-`base`
# points. Any one declared-maximum point would refute the first three; any one
# non-empty-`base` point would refute the last three. The distinct constants
# (2/4/5/7/9) are therefore cosmetic — several spellings of the same probe.
#
# In particular — and this corrects the claim under which
# weak-guard-on-incoming-list was originally added — that rival is NOT refuted
# "at an input no other rival reaches". Its refutation set is byte-identical to
# clobbers' and prepends', so its witness point p6 buys no new probe point, and
# p4/p5 would each refute it. What it does add is a distinct DEPENDENCY SHAPE
# (see its rationale): it is the only rival whose append PRESENCE is keyed on
# `base`, so a spec that pinned only "some validator is appended when a maximum
# is declared, and the prefix survives" would still have to be checked against
# it separately. That is a real clause-coverage contribution; it is not a
# probe-point contribution, and the two must not be conflated.
#
# The one genuinely independent axis is `maxLength = none` vs `some _`:
# weak-attaches-always is refuted ONLY at p0 and by nothing else in the battery,
# and every other rival is refuted only away from p0. That is the real content of
# K1's biconditional here, and it IS covered from both sides. The `base = []` vs
# non-empty axis is the second real axis (it is what separates K3/K4 from K1/K2),
# and it too is covered. Two meaningful axes; the rivals beyond those two axes are
# pairwise distinguishable by the WRONG VALUE they produce rather than by their
# witness point. That is still a sound battery — each rival is genuinely wrong and
# genuinely caught — but the honest statement is "the battery covers both
# meaningful axes and seven distinct wrong behaviors", not "seven independent
# probe points".
#
# ---------------------------------------------------------------------------
# Carrier narrowing vs the nagini sibling
# ---------------------------------------------------------------------------
# The nagini model contracted THREE functions and threaded an exception through
# them: `compare_length(value_length, limit)` (raising when the limit is absent),
# `build_char_validators(max_length)` (the list assembly), and
# `clean_charfield(max_length, value_length)` (assemble-then-run, whose absent
# absent raise-clause is what made the dropped guard unprovable). This bundle
# models only the
# purely functional core — the LIST ASSEMBLY, nagini's middle function — so the
# port narrows to that one surface. Consequences, case by case:
#
#   * nagini `pos-build-conditional-return` -> PORTED as pos-branch-and-return.
#   * nagini `pos-compare-reordered`, `pos-clean-early-return` -> NOT PORTED.
#     Both reshape functions this carrier does not model (the raising comparison
#     and the assemble-then-run wrapper). There is no counterpart obligation to
#     defend, so a "port" would have to invent one.
#   * nagini `weak-build-always-empty`      -> PORTED as weak-never-attaches (K1).
#   * nagini `weak-build-limit-plus-one`    -> PORTED as weak-bound-off-by-one (K2).
#   * nagini `weak-clean-drop-none-guard`   -> PORTED as weak-attaches-always (K1).
#     This is the marquee: the pre-patch shape, the change actually under test.
#     Nagini rejected it INDIRECTLY, via the wrapper having no raise-clause at all
#     (running an
#     inoperable validator could not be proved non-raising). This carrier has no
#     exception to thread, so the same rival is rejected DIRECTLY instead: the
#     list it builds carries a length-bound validator with an absent bound at a
#     point where the spec demands the incoming list unchanged. Same rival, same
#     defect, refuted through the clause rather than through the raise.
#   * nagini `weak-compare-ge`, `weak-compare-const-true` -> NOT PORTED. Both
#     attack the numeric comparison `value_length > limit` inside the raising
#     comparison function. This carrier models the validator's CONSTRUCTION (its
#     presence in the list and the bound it carries), never its later invocation,
#     so `value_length` is not a binder here and there is no comparison to skew.
#     Dropped for absence of a counterpart, NOT for proof difficulty.
#   * nagini `weak-clean-always-false` -> NOT PORTED. (Added by the audit: this
#     nagini case was missing from the ledger entirely, neither ported nor
#     recorded as dropped. Its disposition is the same as the two comparison
#     rivals above and the reason is the same, so nothing ships for it — but an
#     unaccounted-for sibling case is exactly the kind of silent omission this
#     ledger exists to prevent, so it is written down.) The rival makes the
#     assemble-then-run wrapper report 'fits' unconditionally, which is a defect
#     in the wrapper's RESULT — `clean_charfield`'s boolean verdict, computed by
#     invoking the assembled validator. This carrier has no wrapper and no
#     verdict: the modeled function returns the validator LIST, and the list is
#     assembled identically whether or not anything later runs it. There is no
#     counterpart obligation, so a "port" would have to invent the invocation
#     surface. Dropped for absence of a counterpart, NOT for proof difficulty.
#   * nagini `admiss-clean-selfexercise`    -> PORTED as adm-ground-at-f2p-shape.
#     A previous revision recorded this case as VACUOUS here, on the ground that
#     the frozen obligation is an unconditional
#     `∀ (maxLength : Option Int) (base : List Validator)` with no precondition
#     hypothesis, so "there is no precondition that could be too strong". That
#     reason is REJECTED by this audit, and it is the exact reason the audit brief
#     names as measured-wrong. The analogue of PRECOND-TOO-STRONG on a total
#     carrier is not a `Requires` that rejects a good input — it is the modeled
#     OBLIGATION being unsatisfiable at exactly an F2P-shaped input, which can
#     happen through a mis-modeled carrier, a spec that is contradictory at a
#     concrete point, or an impl that does not reduce there. A positive that
#     discharges the obligation AT that concrete input, by evaluation, as a `have`,
#     before closing the frozen obligation verbatim, tests that directly and is
#     not implied by any other case in this battery: the two `pos-*` cases quantify
#     over all inputs and prove nothing about any particular one, and every reject
#     case establishes the NEGATION of the spec at its point.
#     Demonstrated expressible, not argued: four independent tactic spellings of
#     the ground instance were built by the audit and ALL FOUR verified (exit 0) —
#     `rfl`, `decide`, `simp [implementation…, Id.run, bind, pure]`, and
#     `simp [implementation…, Id.run]; rfl`. The lane was landed with the frozen
#     proof body untouched after the `have`s. See adm-ground-at-f2p-shape below.
#
# Two rivals have NO nagini counterpart and are added because this carrier has an
# attack surface nagini's did not: nagini's `build_char_validators` returned a
# FRESH list (its post pinned only length and element 0), whereas this spec pins
# the result as `base ++ …` — so the INCOMING list is part of the contract. K3 and
# K4 are that new surface: weak-clobbers-incoming and weak-prepends. Without them
# the `base` binder would be held at `[]` by every witness, and a rival that
# mishandled only the pre-existing validators would verify unnoticed.
#
# ---------------------------------------------------------------------------
# Why no shipped rival can be a spec hole here (STRUCTURAL, proved)
# ---------------------------------------------------------------------------
# Two facts about the frozen postcondition were PROVED in one build (exit 0),
# alongside the frozen obligation and with the statement untouched:
#   (i)  it is FUNCTIONAL — `problem_spec m b r1 → problem_spec m b r2 → r1 = r2`;
#   (ii) its satisfying set is EXACTLY the frozen impl's graph —
#        `problem_spec m b r ↔ r = implementation m b`.
# Together these say the spec admits an impl iff that impl agrees with the frozen
# one at every input. So no wrong impl can ever verify (attack D is unwinnable by
# construction, not merely unwon), and every faithful impl is admitted, so attack
# E can only fail for proof-EFFORT reasons rather than for spec-strength reasons.
# That is why the rivals below are worth reading as clause-coverage probes: their
# job is to demonstrate the spec's clauses are each load-bearing, not to search
# for a hole that the characterization above rules out.
#
# Probed anyway, by the audit, since a proof of (i)+(ii) is only as good as the
# statement it is about. Five NEW wrong impls the battery did not contain, each
# built under a deliberately GENEROUS proof body (`first | simp […] | simp_all […]
# | (simp […]; omega) | (simp […]; ring_nf) | decide | rfl`) so a rejection cannot
# be blamed on a tactic gap — all five REJECTED (exit 1), with residual goals that
# name the defect rather than a tactic failure:
#   prefix order scrambled (`base.reverse ++ …`)      -> `⊢ base.reverse = base`
#   wrong bound at the single point n = 0             -> `⊢ n = 0 → 1 = n`
#   bound clamped at zero, wrong only for n < 0       -> `⊢ 0 ≤ n`
#   incoming prefix duplicated (`base ++ base ++ …`)  -> `⊢ base = []`
#   a non-length-bound validator appended             -> `⊢ False`
# The third is the carrier trap worth naming: the clamp agrees with the frozen
# impl on every non-negative declared bound and diverges only at a negative one,
# and the spec still catches it — the `Option Int` carrier does NOT collapse the
# negative sub-domain, so `Int`-vs-`Nat` truncation is not hiding a distinction.
# And four NEW correct reshapes, all VERIFIED (exit 0): a `dite` on `isSome` with
# `Option.get`, `maxLength.toList.map`, `Option.elim`, and one deliberately far
# from the frozen proof (`(lengthBound (some n) :: base.reverse).reverse` on one
# arm and a `foldr` rebuild of the prefix on the other, needing `induction base`
# rather than rfl-style reduction). No SPEC-TOO-STRONG on any of those axes.
#
# ---------------------------------------------------------------------------
# Vacuous / dropped classes — stated, not silently omitted
# ---------------------------------------------------------------------------
#   * FRAME / PERMISSION-MUTATION lane — VACUOUS on lean. The nagini sibling
#     already records this class as inapplicable (every input an immutable scalar,
#     no fractional-permission heap parameter). Lean is referentially transparent:
#     there is no aliasable read-only input an impl could overwrite. Nothing to
#     port. NOTE this is NOT the same as saying the incoming list is unguarded —
#     the analogue of the frame obligation here is K3/K4 (the spec pins `base` as
#     a prefix), and that IS attacked, by weak-clobbers-incoming and
#     weak-prepends.
#   * DIVERGENCE / NON-TERMINATION lane — VACUOUS on lean, and for the carrier
#     reason rather than the spec reason. `implementation_buildFieldValidators` is
#     a total Lean `def`, so a diverging implementation cannot be written at all
#     and there is no rival to ship. MEASURED by the audit rather than asserted:
#     the frozen bundle sets no `loom.semantics.termination` option (it is vanilla
#     Lean 4 + Mathlib, not velvet), and a rival rewriting the impl as
#     `partial def … := implementation_buildFieldValidators maxLength base` does
#     not yield a shippable reject case — it fails with
#     `Tactic 'unfold' failed to unfold 'implementation_buildFieldValidators'`,
#     an error about the tactic's inability to see through an opaque `partial`
#     body rather than about the spec, and a witness against it fails the same way
#     (both exit 1). So there is no witness that could attribute such a rejection
#     to the postcondition: the case would be a false discriminator of exactly the
#     kind the witness requirement exists to exclude. Nothing ships. This is the
#     LEAN disposition specifically:
#     on velvet under `set_option loom.semantics.termination "partial"` the same
#     class is a KNOWN SPEC HOLE, not vacuous — a non-terminating impl satisfies
#     every `ensures` vacuously and verifies while its faithful patch hangs the
#     test (the corpus-wide termination-semantics finding). The nagini sibling carries no such case
#     here either way.
#   * AXIOM lane — DROPPED. `meta.axioms == []`; there is no `opaque` callee on
#     this path (the validator's construction is the operation governed here, so
#     it is modeled structurally rather than axiomatized). The axiom lane is
#     G-AX's job and this gate ignores it. AXIOM_TESTS = [].
#
# ---------------------------------------------------------------------------
# A measured correction to the nagini sibling's `refinement` prose — READ THIS
# ---------------------------------------------------------------------------
# The nagini file asserts, for four of its six rivals, that a faithful real patch
# would "break max-length enforcement P2P tests" and so would not resolve. That
# claim was re-measured for THIS instance by building the real tree at
# base_commit, applying the instance's own test_patch, and running the whole
# `expressions` test app once per rival patch. It does not hold:
#
#   * The 158 PASS_TO_PASS tests are ALL in one test module, and not one of them
#     invokes field validation — no `.clean()`, no `.full_clean()`, no
#     `.run_validators()`, no length enforcement anywhere in the file. Model
#     writes do not run validators, so a wrong validator is invisible to every
#     one of them.
#   * The FAIL_TO_PASS assertion is a "does not raise" smoke test, and it probes
#     ONLY the no-declared-maximum path. It never asserts which validators are
#     present, and never asserts that an over-long value is refused.
#
# Measured outcome per rival patch (whole `expressions` app, 168 tests):
#   unconditional attach (the pre-patch shape) -> FAILS the F2P; does NOT resolve.
#   never attach / off-by-one bound / clobber the list / prepend -> ALL PASS; each
#   WOULD resolve.
#
# So the refinement field below reports, per rival, what was actually measured
# rather than the inherited claim. The honest reading of the four
# "would-still-resolve" rivals: they are SPEC-STRENGTH probes, not
# verify-does-not-imply-resolve candidates. The frozen spec is strictly stronger
# than this instance's test set — it pins the whole list where the tests check
# only that one path does not blow up. That is the safe direction for a
# `verify ⟹ correct` bundle (over-strictness cannot admit a wrong impl), and it is
# why those rivals are still worth shipping: each is genuinely WRONG behavior,
# each is caught by the spec, and the spec catching what the test set misses is
# the property a falsification battery should be measuring. Where a rival's real
# patch IS caught by some other Django suite, that is named — as evidence the
# behavior is wrong, explicitly NOT as an F2P/P2P claim.

from pathlib import Path

INSTANCE = "django__django-15277"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- Frozen editable regions, extracted verbatim so the manifest breaks loudly
# --- on drift. These two strings are the ONLY parts a variant may touch: the
# --- impl-region body, and the proof TACTIC body (everything after the theorem
# --- statement's `:= by`). Both anchors lie entirely inside their region and are
# --- unique in the file.

_IMPL_OLD = """\
def implementation_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) : List Validator := Id.run do
  let mut validators := base
  if maxLength.isSome then
    validators := validators ++ [Validator.lengthBound maxLength]
  return validators"""

_PROOF_OLD = """\
  intro maxLength base
  unfold implementation_buildFieldValidators problem_spec_buildFieldValidators
  cases maxLength with
  | none => simp [Id.run, bind, pure]
  | some n => simp [Id.run, bind, pure]"""

assert _BASE.count(_IMPL_OLD) == 1, "impl region drifted from expected text"
assert _BASE.count(_PROOF_OLD) == 1, "proof region drifted from expected text"


def _impl(new_impl, new_proof=None):
    """A full Solution.lean variant: new impl body, optionally a new proof tactic
    body. The theorem STATEMENT and the entire spec view are untouched."""
    out = _swap(_BASE, _IMPL_OLD, new_impl)
    if new_proof is not None:
        out = _swap(out, _PROOF_OLD, new_proof)
    return out


def _head(rest):
    return ("def implementation_buildFieldValidators\n"
            "    (maxLength : Option Int) (base : List Validator) : "
            "List Validator := Id.run do\n" + rest)


def _witness(max_length, base):
    """A refutation witness: the spec predicate FAILS of the rival's own output at
    one concrete input. Checked in a file whose proof obligations have been
    stripped, so no tactic script can interfere. Both halves were run by hand
    (scripts/lean_verify.sh) for every case below: elaborates against the rival,
    FAILS against the frozen solution. Binds nothing, so its hypotheses cannot be
    inconsistent — the carrier is fully transparent here (a concrete `Option Int`
    and a concrete `List Validator`, `Validator` deriving DecidableEq), so every
    refutation is stated at literal inputs and closed by `decide`. No conditioning
    on an opaque term is needed anywhere in this battery."""
    return (f"example : ¬ problem_spec_buildFieldValidators {max_length} {base}\n"
            f"    (implementation_buildFieldValidators {max_length} {base}) := by\n"
            f"  unfold problem_spec_buildFieldValidators "
            f"implementation_buildFieldValidators\n"
            f"  decide")


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY.
# Structurally different but behaviourally identical impls, each shipped with a
# proof that actually closes for the new shape. The theorem statement is
# byte-identical; only the tactic body may move. No new lemma, no new axiom, no
# sorry/admit/native_decide. Both were built and confirmed to close.
# ---------------------------------------------------------------------------

_POS_BRANCH = _head("""\
  match maxLength with
  | none   => return base
  | some n => return base ++ [Validator.lengthBound (some n)]""")

_POS_PURE = """\
def implementation_buildFieldValidators
    (maxLength : Option Int) (base : List Validator) : List Validator :=
  match maxLength with
  | none   => base
  | some n => base ++ [Validator.lengthBound (some n)]"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY. The impl is the FROZEN one and the obligation statement is the
# frozen one; the only change is two `have`s PREPENDED to the frozen tactic body,
# each discharging the obligation at one concrete F2P-shaped input by evaluating
# the impl there. Nothing is assumed (no new declaration, no sorry/axiom, no new
# theorem) and the frozen `intro …; unfold …; cases …` closes the obligation
# verbatim afterwards, so this can only fail if the obligation is genuinely
# unsatisfiable at one of those two points.
#
# The two points are chosen to be the F2P's shape and its complement:
#   (none, [])                  — a string-valued field with NO declared maximum
#                                 carrying no prior validators. This is the shape
#                                 the F2P assertion actually exercises, and the
#                                 point at which the spec demands NOTHING be
#                                 appended.
#   (some 10, [basic 1])        — a declared maximum on a field that already
#                                 carries a validator: the append must happen AND
#                                 the incoming validator must survive as a prefix.
# Together they ground both arms of the match at literal inputs, which is what
# makes this a satisfiability probe rather than a restatement of the pos cases.
_ADM_GROUND = """\
  have _ground_no_declared_max :
      problem_spec_buildFieldValidators none []
        (implementation_buildFieldValidators none []) := by
    have himpl : implementation_buildFieldValidators none [] = [] := by
      simp [implementation_buildFieldValidators, Id.run, bind, pure]
    rw [himpl]
    unfold problem_spec_buildFieldValidators
    decide
  have _ground_declared_max_over_existing :
      problem_spec_buildFieldValidators (some 10) [Validator.basic 1]
        (implementation_buildFieldValidators (some 10) [Validator.basic 1]) := by
    have himpl : implementation_buildFieldValidators (some 10) [Validator.basic 1]
        = [Validator.basic 1, Validator.lengthBound (some 10)] := by
      simp [implementation_buildFieldValidators, Id.run, bind, pure]
    rw [himpl]
    unfold problem_spec_buildFieldValidators
    decide
"""


# ---------------------------------------------------------------------------
# UNIQUENESS — same-spec WRONG impls that MUST be rejected.
# If any VERIFIES => SPEC-TOO-WEAK. Each carries a witness seen to discriminate.
# ---------------------------------------------------------------------------

# K1, the marquee: attach unconditionally, so an undeclared maximum still gets a
# length-bound validator — one carrying an absent, unusable bound.
_WEAK_ATTACH_ALWAYS = _head("""\
  let mut validators := base
  validators := validators ++ [Validator.lengthBound maxLength]
  return validators""")

# K1 mirrored: never attach at all, so a DECLARED maximum goes unenforced.
_WEAK_NEVER_ATTACH = _head("""\
  let mut validators := base
  return validators""")

# K2: attach under the correct guard, but carry a bound one above the declared one.
_WEAK_BOUND_OFF_BY_ONE = _head("""\
  let mut validators := base
  match maxLength with
  | none   => pure ()
  | some n => validators := validators ++ [Validator.lengthBound (some (n + 1))]
  return validators""")

# K2 at the other extreme: attach under the correct guard, but carry NO bound.
_WEAK_BOUND_ABSENT = _head("""\
  let mut validators := base
  if maxLength.isSome then
    validators := validators ++ [Validator.lengthBound none]
  return validators""")

# K3: replace the list rather than extend it, discarding the incoming validators.
_WEAK_CLOBBERS = _head("""\
  let mut validators := base
  match maxLength with
  | none   => pure ()
  | some n => validators := [Validator.lengthBound (some n)]
  return validators""")

# K4: right element, right count, wrong END — placed first instead of last.
_WEAK_PREPENDS = _head("""\
  let mut validators := base
  match maxLength with
  | none   => pure ()
  | some n => validators := [Validator.lengthBound (some n)] ++ validators
  return validators""")

# K1xK3 INTERACTION (added by the audit). Every rival above gets the SHAPE of the
# dependency right: whether the length-bound validator is appended is decided by
# `maxLength` alone. This one makes PRESENCE depend on the OTHER binder — it
# attaches only when the incoming list happens to be empty. The spec forbids that
# (`base ++ …` appends unconditionally on `base`), and no existing rival probes
# it: clobbers drops the prefix but always appends, prepends misplaces but always
# appends, and the K1/K2 rivals all hold `base` at `[]`, where this rival is
# CORRECT. Built by the audit: rival rejected (exit 1), witness holds of the rival
# (exit 0) and is refuted on gold by `decide` (exit 1, semantic).
_WEAK_GUARD_ON_BASE = _head("""\
  let mut validators := base
  match maxLength, base with
  | some n, [] => validators := validators ++ [Validator.lengthBound (some n)]
  | _, _       => pure ()
  return validators""")


SPEC_TESTS = [

    # ===================== SOUNDNESS (positive controls) =====================

    {
        "id": "pos-branch-and-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_BRANCH),
        "rationale": (
            "Ports nagini's pos-build-conditional-return. Correct, structurally "
            "different: branch on the optional maximum and RETURN the finished "
            "list in each arm, instead of seeding a mutable list and appending "
            "under a guard. No mutate-then-return, and the `isSome` test is "
            "replaced by a `match` that binds `n` directly — so the appended "
            "validator is built from the bound `n` rather than from the whole "
            "option. Satisfies K1-K4 on both arms. Verified with the frozen proof "
            "body: both arms reduce definitionally, so `cases maxLength <;> simp` "
            "still closes and no new lemma is needed. If a faithful correct impl "
            "in this shape could NOT verify => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_PURE),
        "rationale": (
            "Second positive control, and the one that probes a different axis: "
            "the same assembly written as a PURE functional `def` — no `Id.run`, "
            "no `do`, no `let mut`, no early return. Confirms the obligation does "
            "not secretly depend on the imperative encoding it happens to be "
            "written in, i.e. that `problem_spec` constrains the VALUE returned "
            "and not the monadic shape that produced it. Verified with the frozen "
            "proof body (the `simp [Id.run, bind, pure]` closes a goal that no "
            "longer has an `Id.run` in it). Must verify (else SPEC-TOO-STRONG)."
        ),
    },

    # ======================== ADMISSIBILITY (PRECOND-TOO-STRONG) =============

    {
        "id": "adm-ground-at-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_IMPL_OLD, _ADM_GROUND + _PROOF_OLD),
        "rationale": (
            "ADDED BY THE AUDIT; the port had recorded this lane as vacuous. The "
            "obligation is discharged at two concrete F2P-shaped inputs by "
            "EVALUATION, each as a `have` in the tactic body, before the frozen "
            "obligation is closed verbatim by the unchanged frozen script. The impl "
            "is the frozen impl and the theorem statement is byte-identical, so the "
            "only thing this case can fail on is the obligation being unsatisfiable "
            "at one of those points — which is the analogue of PRECOND-TOO-STRONG "
            "on a total carrier, where there is no `Requires` to be too strong but "
            "a spec can still be contradictory, mis-carried, or non-reducing at a "
            "concrete input. Point 1 is (none, []): a string-valued field declaring "
            "NO maximum and carrying no prior validators — the shape the F2P "
            "assertion exercises, and the point where the spec demands nothing be "
            "appended. Point 2 is (some 10, [basic 1]): a declared maximum on a "
            "field that already carries a validator, so the append must occur AND "
            "the incoming validator must survive as a prefix. Both arms of the "
            "match are thereby grounded at literal inputs, which no other case in "
            "this battery does: the two `pos-*` cases quantify universally and "
            "assert nothing about any particular input, and every reject case "
            "proves the spec's NEGATION at its point. Must verify (else the modeled "
            "behavior is unsatisfiable at exactly a normal input). Ports nagini's "
            "admiss-clean-selfexercise, whose ground instance was likewise a "
            "concrete call whose post was then asserted. Landed only after the "
            "ground instance was demonstrated buildable four independent ways "
            "(`rfl`, `decide`, `simp [… Id.run, bind, pure]`, `simp [… Id.run]; "
            "rfl`), all exit 0 — so the lane is expressible here, and its earlier "
            "'no precondition, therefore vacuous' disposition was wrong."
        ),
    },

    # ========================= UNIQUENESS / completeness =====================

    {
        "id": "weak-attaches-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ATTACH_ALWAYS),
        "witness": _witness("none", "[]"),
        "refinement": (
            "THE MARQUEE — this is the behavior actually under test, and the ONE "
            "rival in this battery whose faithful real patch was MEASURED not to "
            "resolve. The corresponding real change is to attach the length-bound "
            "validator with no guard at all, which is exactly the pre-change code. "
            "Measured by building the tree at base_commit, applying the instance's "
            "own test_patch and running the whole test app: the FAIL_TO_PASS "
            "assertion ERRORS, because the path it probes constructs a "
            "string-valued field with NO declared maximum length, and cleaning a "
            "value against a length-bound validator holding an absent bound raises "
            "a type error rather than a validation error, so it is not swallowed. "
            "Graded with the harness's own log parser and resolution functions, not "
            "a hand-rolled reading of the output: verdict resolved=False. (No "
            "failure COUNT is quoted here on purpose — the erroring test's line "
            "collapses with the next one in the verbose log, so the run shows one "
            "error while the graded report attributes two F2P misses. The verdict "
            "is unaffected.) Does NOT resolve — so if this rival ever VERIFIED it "
            "would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "Rejected by K1 (PRESENCE) at maxLength = none: the spec appends "
            "NOTHING when no maximum is declared, while the rival appends "
            "`Validator.lengthBound none` — the inoperable validator, the one "
            "carrying no usable bound. Witness at (none, []), the minimal point "
            "that isolates the missing guard: `base` is empty, so the refutation "
            "cannot be coming from the prefix clauses K3/K4, and no bound is "
            "declared, so it cannot be coming from K2. Note the sub-domain: this "
            "rival is CORRECT on every `some n` input, which is why its witness "
            "must sit at `none` and why it is complementary to "
            "weak-bound-absent below rather than a duplicate of it. Nagini "
            "rejected this same rival indirectly, through its wrapper's absent "
            "raise-clause; here it is refuted directly through the clause. If it "
            "verifies => SPEC-TOO-WEAK on the guard, and the bundle would be "
            "blind to the very change it exists to certify."
        ),
    },
    {
        "id": "weak-never-attaches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NEVER_ATTACH),
        "witness": _witness("(some 5)", "[]"),
        "refinement": (
            "Ports nagini's weak-build-always-empty. The corresponding real change "
            "drops the attachment entirely, so a field that DOES declare a maximum "
            "length silently stops enforcing it. MEASURED, correcting the nagini "
            "sibling's claim: this patch PASSES all 168 tests in this instance's "
            "test app, F2P included, and WOULD resolve. It is therefore a "
            "spec-strength probe, not a verify-does-not-imply-resolve candidate — "
            "the frozen spec refuses it even though this instance's tests cannot "
            "see it. That the behavior is genuinely wrong (not a benign refactor) "
            "was confirmed by direct semantic probe: a field declaring a maximum "
            "ACCEPTS an over-long value under this patch, where the real code "
            "refuses it. Suites outside this instance's test set do detect it, but "
            "no specific suite or count is asserted here — two independent "
            "measurement runs disagreed on exactly which out-of-set tests fail, "
            "and only the in-set result above bears on the resolve claim."
        ),
        "rationale": (
            "Rejected by K1 (PRESENCE) in the mirror direction from "
            "weak-attaches-always: at maxLength = some 5 the spec demands exactly "
            "one appended `Validator.lengthBound (some 5)` and the rival appends "
            "nothing. Witness at (some 5, []) — a DECLARED maximum, which is the "
            "half of K1's biconditional that weak-attaches-always leaves untested. "
            "Shipping both is what makes 'exactly when, and only when' a measured "
            "claim rather than a one-sided one: each rival satisfies the half the "
            "other violates. Empty `base` again isolates K1 from K3/K4. If it "
            "verifies => SPEC-TOO-WEAK on the presence half."
        ),
    },
    {
        "id": "weak-bound-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_BOUND_OFF_BY_ONE),
        "witness": _witness("(some 7)", "[]"),
        "refinement": (
            "Ports nagini's weak-build-limit-plus-one. The corresponding real "
            "change attaches the validator with a bound one greater than the "
            "declared maximum, admitting values one longer than allowed. "
            "MEASURED, correcting the nagini sibling's claim: this patch PASSES "
            "all 168 tests here and WOULD resolve — the F2P probes only the "
            "no-declared-maximum path, where this rival and the real code agree "
            "exactly, and no test in the set enforces a length. A spec-strength "
            "probe. Confirmed genuinely wrong by direct semantic probe: a value one "
            "longer than the declared maximum is ACCEPTED where the real code "
            "refuses it. Out-of-set suites do detect it; no specific suite is "
            "asserted here (see weak-never-attaches on why no such count is cited)."
        ),
        "rationale": (
            "Rejected by K2 (CARRIED BOUND): the rival gets PRESENCE right — one "
            "validator appended exactly when a maximum is declared, at the correct "
            "end of the correct prefix — and misses only the VALUE it carries "
            "(`some 8` where the spec demands `some 7`). It therefore satisfies "
            "K1, K3 and K4 in full, and is refutable ONLY through K2, which is "
            "what makes it the case that shows the carried bound is pinned to the "
            "declared value rather than merely to 'some bound'. This is the "
            "NEAREST possible miss on that axis — one above, not an arbitrary "
            "constant — so a spec that pinned the bound only loosely would still "
            "catch a far-away value while letting this through. Witness at "
            "(some 7, []). AUDIT CORRECTION: an earlier revision claimed the "
            "point 'differs from weak-never-attaches' (some 5) so the two are not "
            "refuted at a shared input'. That is false and was measured false — "
            "this rival is refuted at EVERY declared-maximum point in the "
            "battery, (some 5, []) included, and weak-never-attaches is likewise "
            "refuted at (some 7, []). The two witnesses are interchangeable; the "
            "differing constant buys nothing. What distinguishes this case from "
            "weak-never-attaches is not its witness POINT but the CLAUSE it "
            "violates: never-attaches omits the element (K1), this one supplies "
            "the element with the wrong payload (K2). Both are worth shipping for "
            "that reason, not for probe-point diversity. If it verifies => "
            "SPEC-TOO-WEAK on the bound value."
        ),
    },
    {
        "id": "weak-bound-absent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_BOUND_ABSENT),
        "witness": _witness("(some 4)", "[]"),
        "refinement": (
            "No direct nagini counterpart; it is the exact COMPLEMENT of the "
            "marquee and exists to pin down which half of the biconditional each "
            "rival breaks. The corresponding real change keeps the guard but "
            "constructs the validator with an absent bound instead of the declared "
            "one. MEASURED: the F2P probes only the no-declared-maximum path, "
            "where this rival's guard correctly suppresses the attachment, so the "
            "F2P passes and this WOULD resolve. A spec-strength probe. Genuinely "
            "wrong all the same: a field that DOES declare a maximum ends up "
            "holding precisely the inoperable validator this change exists to "
            "avoid, so cleaning any value against such a field raises a type error."
        ),
        "rationale": (
            "Rejected by K2 (CARRIED BOUND) on the opposite sub-domain from "
            "weak-attaches-always, which is the point of shipping both. The two "
            "rivals build the SAME wrong element, `Validator.lengthBound none`, "
            "but at disjoint inputs: weak-attaches-always emits it when NO maximum "
            "is declared (and is correct whenever one is), this one emits it when "
            "a maximum IS declared (and is correct when none is). Neither witness "
            "would refute the other rival, so they cannot share a point: this one "
            "sits at (some 4, []) against the marquee's (none, []). Together they "
            "show the guard and the carried bound are pinned INDEPENDENTLY — a "
            "spec that only checked 'the list has the right length' would admit "
            "both. If it verifies => SPEC-TOO-WEAK on the carried bound."
        ),
    },
    {
        "id": "weak-clobbers-incoming",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_CLOBBERS),
        "witness": _witness("(some 5)", "[Validator.basic 3]"),
        "refinement": (
            "No nagini counterpart — this attacks a clause nagini's carrier did "
            "not have. Nagini's assembly returned a FRESH list and its post "
            "constrained only the length and element 0, so the incoming validators "
            "were not part of its contract; here the spec pins the result as "
            "`base ++ …`, making them part of it. The corresponding real change "
            "REPLACES the field's validator list with a one-element list instead "
            "of extending it, discarding every validator the field already "
            "carried. MEASURED: PASSES all 168 tests here and WOULD resolve — no "
            "test in this instance's set inspects the validator list or exercises "
            "a field carrying other validators. A spec-strength probe. "
            "Confirmed genuinely wrong by direct semantic probe: field types whose "
            "validation comes from their own default validators lose it entirely. "
            "Note the sub-domain precisely, because it is narrow and it is what the "
            "witness has to hit: this rival AGREES with the real code whenever the "
            "incoming list is empty, which is the common case for a plainly-declared "
            "string field. It diverges only for a field that already carries "
            "validators — from its own type's defaults or supplied explicitly. That "
            "is why its witness holds a NON-EMPTY incoming list, and why no probe "
            "at the empty list could have caught it. Out-of-set suites do detect it; "
            "no specific suite or count is asserted here (see weak-never-attaches "
            "on why no such count is cited)."
        ),
        "rationale": (
            "Rejected by K3 (PREFIX PRESERVED) — the clause the frame directive "
            "maps onto for this carrier. The rival's appended element is entirely "
            "CORRECT (`Validator.lengthBound (some 5)`, present exactly when a "
            "maximum is declared) so it satisfies K1, K2 and K4; it is refutable "
            "only through the prefix. This is the FIRST witness to move `base` off "
            "the empty list: at (some 5, [Validator.basic 3]) the spec demands "
            "`[basic 3, lengthBound (some 5)]` and the rival yields "
            "`[lengthBound (some 5)]`. Without this case every witness would hold "
            "`base = []`, where clobbering and extending are indistinguishable — "
            "so a rival that dropped the pre-existing validators would verify and "
            "the battery would never notice. That is exactly the held-binder gap "
            "this manifest is required to close."
        ),
    },
    {
        "id": "weak-prepends",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPENDS),
        "witness": _witness("(some 9)", "[Validator.basic 1, Validator.basic 2]"),
        "refinement": (
            "No nagini counterpart (same reason as weak-clobbers-incoming: the "
            "incoming list was not in nagini's contract). The corresponding real "
            "change inserts the length-bound validator at the FRONT of the "
            "field's validator list rather than appending it. MEASURED: PASSES all "
            "168 tests here and WOULD resolve. It is also the "
            "WEAKEST-OBSERVABILITY rival in the battery: the change is visible "
            "only in the ORDER in which validation problems are reported, never in "
            "whether a value is accepted or refused, so a value-level probe cannot "
            "separate it from the real code at all. Two independent measurement "
            "runs disagreed on whether ANY out-of-set Django suite detects it, so "
            "no such claim is made here. That makes it a pure spec-strength probe, "
            "and the clearest case in this battery of the frozen spec being "
            "strictly stronger than the available test evidence: the ordering it "
            "pins is real behavior that no test in the instance's set observes."
        ),
        "rationale": (
            "Rejected by K4 (ORDER), and by K4 alone. The rival produces exactly "
            "the right MULTISET of validators — every incoming one, plus one "
            "correctly-bounded length validator, appearing exactly when a maximum "
            "is declared — so it satisfies K1, K2, and even K3's 'nothing is "
            "dropped' reading. Only the POSITION is wrong. That makes it the "
            "case which distinguishes `result = base ++ [v]` from the weaker "
            "'result is a permutation of base with v added': a spec written with "
            "set/multiset semantics would admit this rival, and this witness is "
            "the evidence that the frozen one does not. Witness at "
            "(some 9, [Validator.basic 1, Validator.basic 2]) — TWO incoming "
            "validators, because with a single-element `base` a prepend is only "
            "detectable against a one-element prefix, and a longer, non-symmetric "
            "prefix makes the order claim unambiguous. This is also the third "
            "distinct value of `base` in the battery. If it verifies => "
            "SPEC-TOO-WEAK on ordering."
        ),
    },
    {
        "id": "weak-guard-on-incoming-list",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_GUARD_ON_BASE),
        "witness": _witness("(some 2)", "[Validator.basic 7]"),
        "refinement": (
            "No nagini counterpart, and no counterpart among the rivals above "
            "either — ADDED BY THE AUDIT to close a gap the battery left open. "
            "The corresponding real change gates the attachment on the field's "
            "existing validator list being empty as well as on a maximum being "
            "declared, so a field that already carries validators silently stops "
            "enforcing its declared maximum. No resolve claim is asserted for it: "
            "the in-set F2P probes only the no-declared-maximum path, where this "
            "rival agrees with the real code exactly, so this is a spec-strength "
            "probe like the others, and unlike the marquee it was NOT separately "
            "measured against the real tree by this audit. Genuinely wrong on the "
            "carrier's own terms all the same: the spec appends unconditionally on "
            "`base`, and this rival makes the append conditional on it."
        ),
        "rationale": (
            "Rejected by K1 (PRESENCE), and it is here for the DEPENDENCY SHAPE it "
            "gets wrong, NOT for a probe point no other rival reaches. Every other "
            "rival decides presence by `maxLength` alone, which is the shape the "
            "spec demands; this one alone couples presence to the second binder, "
            "appending only when the incoming list happens to be empty. "
            "AUDIT CORRECTION (measured): the claim under which this case was "
            "originally added — that it is refuted 'at an input NO other rival "
            "reaches', outside every existing refutation set — is FALSE. A "
            "seven-rival x seven-point `#eval` matrix of the decidable spec "
            "predicate (exit 0, reproduced in the header) shows its refutation set "
            "is {p4,p5,p6}, byte-identical to weak-clobbers-incoming's and "
            "weak-prepends'. Its witness point (some 2, [basic 7]) is therefore "
            "interchangeable with theirs and buys no new probe point. What it does "
            "buy is clause coverage: a spec pinning only 'the prefix survives and "
            "some correctly-bounded validator is appended when a maximum is "
            "declared' would admit an impl whose append is gated on `base`, and no "
            "other rival forces that to be checked. Its witness must still sit at "
            "a declared maximum AND a non-empty incoming list: at `base = []` this "
            "rival is exactly gold, and at `maxLength = none` it is also exactly "
            "gold. Verified "
            "by build: the rival does not verify, the witness elaborates against "
            "it, and against the frozen solution `decide` proves the negated spec "
            "claim FALSE — a semantic refutation, not a name or reduction error. "
            "If it verifies => SPEC-TOO-WEAK on presence's independence from "
            "`base`."
        ),
    },
]


# No @ContractOnly-style callee axioms and no `opaque` callee on this path
# (meta.axioms == []): the validator's construction is the operation governed by
# this spec, so it is modeled structurally rather than axiomatized. Nothing for
# the axiom lane to execute; the A-references are validated out of band by
# axiom_check.py / G-AX, not consumed by this proof.
AXIOM_TESTS = []
