# properties.py — G-PBT falsification battery for sympy__sympy-22714 (lean lane).
#
# NOT a Lean file: a manifest the G-PBT gate executes. Each SPEC case is a FULL
# Solution.lean variant that shares the FROZEN spec byte-for-byte — only text
# inside `-- impl-start`/`-- impl-end` (and, where a positive honestly reproves,
# inside `-- proof-start`/`-- proof-end`) is edited — so `markers.same_spec`
# holds by construction and the single `theorem correct_imaginaryCheck`
# STATEMENT stays byte-identical. `expect="verify"` passes iff the file
# elaborates with the obligation closed (no sorry/admit/native_decide, no new
# axiom/theorem/lemma); `expect="reject"` passes iff it does NOT verify AND the
# case's refutation `witness` holds of the rival while FAILING on the frozen
# solution.
#
# PORT NOTE. This is a PORT of the nagini sibling's battery
# (`../nagini/properties.py`): the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. The nagini bundle
# abstracts the same decision to three PARALLEL int lists behind fractional read
# permission (`coord_kind` / `coord_verdict` / `coord_extra`, folded by a
# front-recursive `any_triggering`); this bundle carries the three per-coordinate
# observations as FIELDS of one transparent `Coord` record and folds with
# `List.any`. So nagini's three list arguments become three fields of a single
# `List Coord` binder — the same three observations, reachable at a literal
# input, which is what makes every witness below a plain `decide`.
#
# ============================ DEFENDED SURFACE ==============================
#
#   problem_spec_imaginaryCheck (coords : List Coord) (result : Bool) : Prop :=
#     result = coords.any Coord.rejects
#
# ONE modeled behavior, ONE obligation (`theorem correct_imaginaryCheck`, no
# precondition hypothesis: the statement is `∀ (coords : List Coord), …`).
#
# The postcondition is a single top-level equation, but it is layered and each
# layer is independently attackable:
#
#   (L1 the existential)  the verdict is the EXISTENTIAL over the whole list —
#       `List.any`, i.e. true iff AT LEAST ONE coordinate qualifies, and over
#       EVERY element of the list (no element skipped).
#   (L2 the per-element conjunction)  `Coord.rejects c` requires BOTH
#       `c.isNumber` AND `c.imagPartDetZero == some false`: a concrete number,
#       AND an imaginary part whose vanishing is DETERMINED NEGATIVELY.
#   (L3 the three-valued discrimination)  the second conjunct is `== some
#       false` EXACTLY — not `some true` (determined to vanish), not `none`
#       (undetermined), and NOT the record's other, form-level field.
#
# THE BEHAVIOURAL DISCRIMINATOR. `Coord` carries THREE observations, and the
# spec reads exactly TWO of them. `imagPartTruthy` — the surface, form-level
# reading of a coordinate's imaginary part — is the REDUNDANT third fact: the
# spec never mentions it, and the module docstring says so outright ("A surface,
# form-level reading of a coordinate's imaginary part is *not* the criterion").
# The headline rival below keys the decision off that field instead of the
# three-valued determination. That is the whole point of the modeled change, and
# it is the sub-domain where the two fields DISAGREE (a coordinate that reads as
# a non-trivial object on the surface while its imaginary part is still
# determined to vanish) that the F2P behavior lives in.
#
# BINDER STRUCTURE / COVERAGE. The predicate has two binders: `coords` (input)
# and `result` (output). `coords` is the only input binder, but it is not
# atomic — the reject witnesses must, and do, vary each of the three `Coord`
# FIELDS independently as well as the list's LENGTH and the POSITION of the
# qualifying element, because a rival that mishandled only one field (or only a
# non-final position) would otherwise verify unnoticed:
#
#   Counts below are per COORDINATE across the nine coordinates the seven reject
#   witnesses contain (five length-1 witnesses + two length-2), re-derived from
#   the shipped witness text rather than asserted:
#
#   field / dimension        values probed
#   isNumber                 true (7 coords), false (2)
#   imagPartTruthy           true (6), false (3)      <- the redundant field
#   imagPartDetZero          some false (4), some true (4), none (1)
#   list length              1 (5 witnesses), 2 (2 witnesses)
#   qualifying position      first (weak-universal-not-existential),
#                            last (weak-skip-last), sole (three witnesses),
#                            none (three witnesses)
#
# Seven reject witnesses at SEVEN DISTINCT input points. In particular
# `imagPartDetZero` takes all THREE of its inhabited values, which is what
# certifies that the spec's `== some false` is a three-way discrimination and
# not a two-way one.
#
# ============================ LANES THAT DO NOT PORT =========================
#
#   * FRAME / PERMISSION MUTATION — VACUOUS here. The nagini sibling calls this
#     its #1 class and MANDATORY (all three of its list arguments are held at
#     half permission, and two rivals write into them: `rej-frame-extra`,
#     `rej-frame-kind`). Lean is referentially transparent — no aliasing, no
#     fractional permission, and `coords` is an immutable value — so a
#     "store into a read-only input" rival is not expressible at all. Both
#     nagini frame rivals are therefore dropped, and NO substitute is
#     fabricated. See `assessment`.
#
#   * DIVERGENCE / NON-TERMINATION — VACUOUS here, and this was RE-MEASURED with
#     real builds rather than argued. This bundle carries NO
#     `set_option loom.semantics.termination` line at all (it is a plain Lean
#     `def` bundle, not a velvet one), so the "partial" disposition — a
#     non-terminating impl verifying vacuously, i.e. a known spec hole — does not
#     apply: Lean's own elaborator plays the role the "total" setting plays for
#     velvet, and it refuses the impl outright. Three shapes were built:
#       - a self-recursive `def` with no decreasing measure: rejected by the
#         ELABORATOR (`fail to show termination for
#         implementation_imaginaryCheck ... failed to infer structural
#         recursion`), and its witness build fails for the SAME reason, so no
#         witness can attribute the rejection to the spec;
#       - the same body as `partial def`: the impl is then opaque, and a witness
#         at a literal input fails with `Tactic `unfold` failed to unfold
#         `implementation_imaginaryCheck``, so nothing is refutable;
#       - an unbounded `repeat` loop: witness fails on the rival too (`Tactic
#         `decide` failed for proposition ¬(have rest := …; forIn Lean.Loop.mk
#         …)`) — the un-normalised loop term is exactly the gate's
#         `_STUCK_UNIFICATION`/reduction class.
#     So the class is vacuous for a structural reason (the carrier's own
#     termination checker fires before the spec is ever consulted), not written
#     off: there is no diverging impl this spec ADMITS, hence no hole. See
#     `assessment`.
#
#   * ADMISSIBILITY — PORTED, as `admiss-ground-accepts` below. An earlier
#     revision of this manifest recorded this lane as N/A on the ground that the
#     lean obligation carries no precondition hypothesis
#     (`∀ (coords : List Coord), problem_spec … (implementation … coords)`), so
#     nothing could be PRECOND-TOO-STRONG. That reasoning is wrong, and an audit
#     pass measured it wrong: on a TOTAL carrier the analogue of a too-strong
#     precondition is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped input, which a positive that discharges the obligation at that
#     concrete input — by evaluation, as a `have`, before closing the frozen
#     obligation verbatim — tests directly. That case is expressible here and it
#     is shipped. `pos-oracle` does not cover it: it exercises the degenerate
#     empty list only incidentally and never pins WHICH verdict any concrete
#     input produces.
#
#   * PARTIAL-DOMAIN, DROP-**FIRST** (nagini `rej-drop-first`) — DROPPED as
#     not-wrong-in-the-refinement-sense, and this is a real finding rather than
#     a convenience. The rival IS refutable on this carrier, but its faithful
#     real counterpart — narrowing the existential to skip the FIRST coordinate
#     — was measured against the actual harness on this instance and passes
#     BOTH the F2P test and all eleven P2P tests (13/13). So it is not a
#     verify-does-not-imply-resolve break and cannot honestly carry a
#     `refinement`. The equivalent-strength attack whose real patch DOES break
#     the harness is skipping the LAST coordinate, which fails a P2P test; that
#     is shipped instead as `weak-skip-last`. See `assessment`.
#
#   * AXIOM_TESTS — dropped. The axiom lane is G-AX's job and this gate ignores
#     it; there is no consumed axiom here in any case (the changed
#     classification is modeled DEEPLY in the spec, and the three observations
#     are A-references).
from pathlib import Path

INSTANCE = "sympy__sympy-22714"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ANCHORS. Each lies ENTIRELY inside the region it is used to edit (impl region
# for `_TRIG_COND` / `_LOOP` / `_BODY` / `_IMPL_DECL`, proof region for
# `_PROOF`) and each is unique in the frozen file, so the manifest breaks loudly
# if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The per-element decision — the ONLY place the two read observations are
# consulted. Every value-level rival edits exactly this line.
_TRIG_COND = "    if c.isNumber && (c.imagPartDetZero == some false) then\n"

# The traversal header, for the coverage-narrowing rival.
_LOOP = "  for c in coords do\n"

# The whole loop body + fallthrough, for rivals that replace the traversal.
_BODY = (
    "  for c in coords do\n"
    "    if c.isNumber && (c.imagPartDetZero == some false) then\n"
    "      return true\n"
    "  return false\n"
)

# The full impl declaration, for positives that change the impl's SHAPE (not
# just its body) from an imperative loop to a pure fold.
_IMPL_DECL = (
    "def implementation_imaginaryCheck (coords : List Coord) : Bool := Id.run do\n"
    + _BODY
)

# The frozen proof body's FIRST line, for the admissibility positive: it
# prepends a ground `have` ahead of the frozen script and leaves every frozen
# tactic line in place, so the obligation is closed verbatim.
_PROOF_INTRO = "  intro coords\n"

# The frozen proof body (tactic lines only, entirely inside proof-start/-end).
# A positive that reshapes the impl must re-close the SAME obligation honestly;
# swapping on this anchor keeps the `theorem correct_imaginaryCheck` STATEMENT
# byte-identical and touches only the tactic script.
_PROOF = """  intro coords
  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
  induction coords with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.any_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : (a.isNumber && (a.imagPartDetZero == some false)) = true
    · simp only [h, if_true, Bool.true_or]; rfl
    · simp only [Bool.not_eq_true] at h
      rw [h]
      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
"""

for _a in (_TRIG_COND, _LOOP, _BODY, _IMPL_DECL, _PROOF, _PROOF_INTRO):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted: {_a[:60]!r}")


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
#
# Each is a structurally DIFFERENT but behaviourally IDENTICAL implementation,
# re-proved honestly: the obligation statement is byte-identical, no new
# axiom/lemma/theorem is introduced and no `sorry`/`admit`/`native_decide` is
# used. Every one of the three was built and confirmed to elaborate.
# ===========================================================================

# pos-commute: the per-element CONJUNCTION is commuted — the three-valued
# determination is tested first and the concrete-number test second. `&&` is
# commutative on Bool and neither operand can diverge, so the verdict is
# identical at every input; only the executable FORM changes, and it is a form a
# faithful patch could equally take. The frozen script's `by_cases` is stated on
# the gold operand order, so it no longer closes the reshaped branch tree; the
# proof is re-closed by normalising the reshaped conjunction back with an
# explicit `Bool.and_comm` rewrite before the same case split. A genuine
# reproof, not a weakening. If it FAILS => SPEC-TOO-STRONG (the postcondition
# would be over-fit to one operand order).
_POS_COMMUTE = _swap(
    _swap(_BASE, _TRIG_COND,
          "    if (c.imagPartDetZero == some false) && c.isNumber then\n"),
    _PROOF,
    """  intro coords
  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck Coord.rejects
  induction coords with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.any_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [Bool.and_comm a.isNumber (a.imagPartDetZero == some false)]
    by_cases h : ((a.imagPartDetZero == some false) && a.isNumber) = true
    · simp only [h, if_true, Bool.true_or]; rfl
    · simp only [Bool.not_eq_true] at h
      rw [h]
      simp only [Bool.false_or, Bool.false_eq_true, if_false, ih]
""",
)

# pos-fold: replaces the imperative early-return traversal with a pure
# right-fold that ORs the per-element decision across the list. Different
# control flow (no early exit — every element is visited), same value at every
# input, because `||` is short-circuit-irrelevant on a total predicate. The
# `Id.run`/`forIn` machinery disappears from the goal, so the proof is re-closed
# by a two-line induction over `List.foldr_cons` / `List.any_cons`. Must verify.
_POS_FOLD = _swap(
    _swap(_BASE, _IMPL_DECL,
          "def implementation_imaginaryCheck (coords : List Coord) : Bool :=\n"
          "  coords.foldr (fun c acc =>\n"
          "    (c.isNumber && (c.imagPartDetZero == some false)) || acc) false\n"),
    _PROOF,
    "  intro coords\n"
    "  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck"
    " Coord.rejects\n"
    "  induction coords with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.any_cons, List.foldr_cons, ih]\n",
)

# pos-oracle: the cheapest HONEST implementation. The postcondition's right-hand
# side is GROUNDED in the argument — `coords.any Coord.rejects` is a total,
# transparent fold over the input with no opaque callee and no answer key — so
# returning it directly is a fully correct implementation rather than an
# ungrounded-oracle echo, and it is the analogue of nagini's `pos-echo`. This is
# also the control that shows the spec is not echo-vulnerable: there is no WRONG
# constant or oracle to echo (every constant fails the postcondition, as
# `weak-never-rejects` below demonstrates). It additionally exercises the
# degenerate input `[]`, which the nagini `admiss-drain` case was really about.
# Proof collapses to `rfl` after unfolding. Must verify.
_POS_ORACLE = _swap(
    _swap(_BASE, _IMPL_DECL,
          "def implementation_imaginaryCheck (coords : List Coord) : Bool :=\n"
          "  coords.any Coord.rejects\n"),
    _PROOF,
    "  intro coords\n"
    "  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck\n"
    "  rfl\n",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK.
#
# Each shares the frozen spec exactly and edits only the impl region, leaving
# the frozen proof body in place (it will not close for the reshaped impl — but
# a reject case is NOT judged on that build; it is judged on its `witness`,
# which is checked in a file with the obligation removed, so no tactic script
# can interfere).
# ===========================================================================

# L3 / the redundant field. THE headline rival: keys the decision off the
# surface, form-level reading of the imaginary part instead of the three-valued
# determination of its vanishing. This is the pre-change behavior.
_RIV_TRUTHY = _swap(_BASE, _TRIG_COND,
                    "    if c.isNumber && c.imagPartTruthy then\n")

# L3 / polarity. Fires on a determination of ZERO instead of NON-ZERO: inverts
# the discriminating clause.
_RIV_POLARITY = _swap(_BASE, _TRIG_COND,
                      "    if c.isNumber && (c.imagPartDetZero == some true) then\n")

# L3 / the third value. Fires on UNDETERMINED instead of determined-non-zero:
# collapses the three-valued discrimination the other way.
_RIV_UNDET = _swap(_BASE, _TRIG_COND,
                   "    if c.isNumber && (c.imagPartDetZero == none) then\n")

# L2 / the first conjunct. Inverts the concrete-number test, so the decision is
# taken on non-numeric coordinates and skipped on numeric ones.
_RIV_NOTNUM = _swap(_BASE, _TRIG_COND,
                    "    if !c.isNumber && (c.imagPartDetZero == some false) then\n")

# L1 / coverage of the existential. Narrows the traversal so the LAST coordinate
# is never examined. (nagini's drop-FIRST analogue; see the port note — first is
# the one that does not carry a refinement here, last does.)
_RIV_SKIP_LAST = _swap(_BASE, _LOOP, "  for c in coords.dropLast do\n")

# L1 / the quantifier itself. Replaces the EXISTENTIAL with a UNIVERSAL: rejects
# only when EVERY coordinate qualifies.
_RIV_ALL = _swap(
    _BASE, _BODY,
    "  for c in coords do\n"
    "    if !(c.isNumber && (c.imagPartDetZero == some false)) then\n"
    "      return false\n"
    "  return true\n",
)

# L1+L2+L3 / total collapse. Never rejects: the decision is dropped entirely.
_RIV_NEVER = _swap(_BASE, _BODY, "  return false\n")


# ---------------------------------------------------------------------------
# WITNESSES. The carrier is fully TRANSPARENT — `Bool`, `Option Bool`, and a
# three-field record — with no opaque callee anywhere in the spec, so every
# refutation is stated at a CONCRETE literal input and closed by `decide`; no
# conditioning on the carrier is needed and no witness binds a hypothesis (so
# `witness-inconsistent` is structurally out of reach).
#
# Each `_c(...)` below is a real, reachable observation triple. The comment names
# the abstract situation, never a repo symbol.
# ---------------------------------------------------------------------------


def _c(is_number, truthy, det_zero):
    return ("{ isNumber := %s, imagPartTruthy := %s, imagPartDetZero := %s }"
            % (is_number, truthy, det_zero))


# A concrete number that reads as trivial on the surface AND is determined to
# vanish: the ordinary accepted coordinate.
_PLAIN = _c("true", "false", "some true")
# A concrete number that reads as a NON-TRIVIAL object on the surface while its
# imaginary part is STILL determined to vanish. This is the divergence point
# between the two observations, and the situation the reported failure is about:
# it must be ACCEPTED.
_SURFACE_ONLY = _c("true", "true", "some true")
# A concrete number whose imaginary part is UNDETERMINED: must be accepted.
_UNDETERMINED = _c("true", "true", "none")
# A concrete number determined to have a NON-ZERO imaginary part: the one
# situation that must be rejected.
_QUALIFIES = _c("true", "true", "some false")
# A NON-numeric coordinate that nonetheless carries a determined-non-zero
# imaginary part: must be accepted (the concrete-number conjunct blocks it).
_NONNUM_DET = _c("false", "true", "some false")


def _wit(lst, note):
    """`¬ problem_spec … coords (implementation … coords)` at a literal input.

    Elaborates against a rival whose verdict diverges from the spec's there, and
    FAILS on the frozen solution (which satisfies the spec at every input) — so
    it is a real discriminator, not a tautology.
    """
    return (
        "-- %s\n"
        "example : ¬ problem_spec_imaginaryCheck %s\n"
        "    (implementation_imaginaryCheck %s) := by\n"
        "  unfold problem_spec_imaginaryCheck implementation_imaginaryCheck\n"
        "  decide" % (note, lst, lst)
    )


# ===========================================================================
# ADMISSIBILITY — the obligation must be SATISFIABLE at an F2P-shaped input.
#
# The frozen theorem carries no precondition hypothesis, so nagini's
# `admiss-drain` (which asserts the loop drains under its three-equal-length
# precondition) has no binder to attack. The analogue on a TOTAL carrier is the
# obligation being unsatisfiable at exactly an F2P-shaped input, so this case
# discharges the spec predicate at that concrete input BY EVALUATION, as a
# `have`, and then closes the frozen obligation verbatim — every frozen tactic
# line is still there, nothing is assumed, no new declaration, statement
# byte-identical.
#
# The input is the F2P shape: a PAIR of concrete coordinates each of which reads
# as a non-trivial object on the surface while its imaginary part is still
# determined to vanish — the very situation the reported failure is about — so
# the admission is pinned to the ACCEPTING branch that behavior requires.
# Two `have`s, because the second alone would not pin the outcome: the spec ties
# `result` to a term over the same input, so discharging it would read the same
# whichever verdict that input produced. `_accepts` EVALUATES the modeled
# behavior at the input down to the concrete verdict `false` first.
#
# Measured load-bearing, not decorative: the identical block placed on the
# `weak-surface-reading` rival FAILS, with `decide` reporting
# `implementation_imaginaryCheck [ … ] = false is false` — i.e. the `_accepts`
# have is what discriminates the accepting branch.
_ADMISS_LIST = "[%s, %s]" % (_SURFACE_ONLY, _SURFACE_ONLY)
_POS_ADMISS = _swap(
    _BASE, _PROOF_INTRO,
    "  have _accepts : implementation_imaginaryCheck %s = false := by decide\n"
    "  have _ground : problem_spec_imaginaryCheck %s\n"
    "      (implementation_imaginaryCheck %s) := by\n"
    "    unfold problem_spec_imaginaryCheck\n"
    "    rw [_accepts]\n"
    "    decide\n" % (_ADMISS_LIST, _ADMISS_LIST, _ADMISS_LIST)
    + _PROOF_INTRO,
)


SPEC_TESTS = [
    # ------------------------- positive controls -------------------------
    {
        "id": "pos-commute",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_COMMUTE,
        "rationale": (
            "structurally-different CORRECT impl: the per-element conjunction is "
            "COMMUTED (three-valued determination tested first, concrete-number "
            "test second). `&&` is commutative on Bool and neither operand can "
            "diverge, so the verdict is identical at every input; only the "
            "executable form changes. The frozen script's `by_cases` names the "
            "gold operand order, so the proof is honestly re-closed by "
            "normalising with an explicit `Bool.and_comm` rewrite before the same "
            "case split — the `theorem correct_imaginaryCheck` STATEMENT is "
            "byte-identical and no new axiom/lemma/sorry is used. If it FAILS => "
            "SPEC-TOO-STRONG (postcondition over-fit to one operand order). "
            "Ports nagini's `pos-reorder`."
        ),
    },
    {
        "id": "pos-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLD,
        "rationale": (
            "structurally-different CORRECT impl with different CONTROL FLOW: the "
            "imperative early-return traversal is replaced by a pure right-fold "
            "that ORs the per-element decision across the list, so every element "
            "is visited and there is no early exit. Same value at every input "
            "(the per-element predicate is total, so short-circuiting is "
            "unobservable). Re-proved by a two-line induction over "
            "List.foldr_cons / List.any_cons; obligation statement unchanged. "
            "Must verify, else SPEC-TOO-STRONG (a spec that only admits the "
            "early-exit shape would be over-fit to the impl)."
        ),
    },
    {
        "id": "pos-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ORACLE,
        "rationale": (
            "the cheapest HONEST impl: the postcondition's right-hand side is "
            "GROUNDED in the argument (a total transparent fold over the input, "
            "no opaque callee, no answer key), so returning it directly is a "
            "fully correct implementation and NOT an ungrounded-oracle echo — the "
            "lean counterpart of nagini's `pos-echo`. Proof collapses to `rfl`. "
            "Must verify (the postcondition IS this equation), else "
            "SPEC-TOO-STRONG. Also the control showing the spec is not "
            "echo-vulnerable: there is no wrong constant to echo, as "
            "`weak-never-rejects` demonstrates. Exercises the degenerate empty "
            "input incidentally — but it never pins WHICH verdict a concrete "
            "input produces, which is why the admissibility case below is "
            "separate rather than folded into this one."
        ),
    },

    # --------------------------- admissibility ---------------------------
    {
        "id": "admiss-ground-accepts",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISS,
        "rationale": (
            "the obligation is SATISFIABLE at an F2P-shaped input, discharged "
            "there by EVALUATION as a `have` before the frozen obligation is "
            "closed verbatim (every frozen tactic line is retained; statement "
            "byte-identical; no new declaration, axiom, lemma or "
            "sorry/admit/native_decide). The frozen theorem carries no "
            "precondition hypothesis, so nagini's `admiss-drain` has no binder "
            "to attack; the analogue on a TOTAL carrier is the obligation being "
            "UNSATISFIABLE at exactly an F2P-shaped input, which this tests "
            "directly. The input is the F2P shape — a PAIR of concrete "
            "coordinates that each read as a non-trivial object on the surface "
            "while their imaginary parts are still determined to vanish — so the "
            "admission is pinned to the ACCEPTING branch that behavior requires, "
            "not merely to some arbitrary point. Two `have`s because the second "
            "alone would not pin the outcome (the spec ties `result` to a term "
            "over the same input, so it would read the same whichever verdict "
            "that input produced): `_accepts` evaluates the modeled behavior "
            "down to the concrete verdict `false` first. Measured load-bearing "
            "— the identical block placed on the `weak-surface-reading` rival "
            "FAILS, `decide` reporting that "
            "`implementation_imaginaryCheck […] = false` is false. If it FAILS "
            "=> the modeled behavior is unsatisfiable at exactly a normal F2P "
            "input, the total-carrier analogue of PRECOND-TOO-STRONG. Ports "
            "nagini's `admiss-drain`."
        ),
    },

    # ------------------------- uniqueness rivals -------------------------
    {
        "id": "weak-surface-reading",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRUTHY,
        "refinement": (
            "THE headline rival, and the pre-change behavior: it keys the "
            "decision off the SURFACE, form-level reading of a coordinate's "
            "imaginary part instead of the three-valued determination of that "
            "part's vanishing. Its faithful real counterpart is the un-narrowed "
            "guard that consults the surface object's own truth value. Measured "
            "against the actual harness for this instance: that guard FAILS the "
            "F2P test (the reported situation constructs a pair of ordinary "
            "concrete real coordinates in a context where their imaginary parts "
            "stay in un-simplified surface form; the surface reading is "
            "non-trivial while the determination is still `vanishes`, so the "
            "construction is wrongly refused) while passing the eleven P2P "
            "tests — 1 failed, 11 passed. So it does NOT resolve, and a rival "
            "that verified here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition `result = coords.any Coord.rejects`, "
            "whose per-element predicate reads `imagPartDetZero`, NOT "
            "`imagPartTruthy` — the spec never mentions the form-level field at "
            "all. Attacks layer L3 (the three-valued discrimination) via the "
            "REDUNDANT third observation. Discriminating sub-domain: exactly "
            "those coordinates where the two observations DISAGREE. If it "
            "VERIFIES => SPEC-TOO-WEAK (the spec would be blind to the very "
            "distinction it exists to draw). Ports nagini's `rej-extra`."
        ),
        # one concrete number, surface reading non-trivial, determination
        # `vanishes`: spec demands false, rival answers true.
        "witness": _wit("[%s]" % _SURFACE_ONLY,
                        "surface reading and determination disagree: spec "
                        "accepts, rival rejects"),
    },
    {
        "id": "weak-inverted-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_POLARITY,
        "refinement": (
            "inverts the polarity of the discriminating clause: fires when the "
            "imaginary part is determined to VANISH instead of determined "
            "NON-zero. Its faithful real counterpart tests the determination "
            "against the opposite outcome. Measured against the actual harness: "
            "it refuses ordinary all-real constructions and permits genuinely "
            "non-real ones, failing on the FIRST P2P test with the "
            "refusal raised for an ordinary real pair — 1 failed, 0 passed "
            "(collection stops at the first failure). Does NOT resolve. Ports "
            "nagini's `rej-polarity`."
        ),
        "rationale": (
            "REJECTED by the postcondition: `Coord.rejects` pins the second "
            "conjunct to `some false`, so a coordinate whose imaginary part is "
            "determined to vanish must NOT qualify. Attacks layer L3 at the "
            "OPPOSITE value of `imagPartDetZero` from `weak-surface-reading` — a "
            "distinct sub-domain (this rival is refuted on a coordinate whose "
            "surface reading is TRIVIAL, where the headline rival agrees with the "
            "spec), so it needs and gets its own witness point. If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # ordinary accepted coordinate (surface trivial, determined to vanish):
        # spec demands false, rival answers true.
        "witness": _wit("[%s]" % _PLAIN,
                        "ordinary coordinate determined to vanish: spec "
                        "accepts, rival rejects"),
    },
    {
        "id": "weak-undetermined-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNDET,
        "refinement": (
            "collapses the three-valued discrimination the remaining way: fires "
            "when the vanishing of the imaginary part is UNDETERMINED rather "
            "than determined non-zero. Its faithful real counterpart tests the "
            "determination against the undetermined outcome. Measured against "
            "the actual harness: it permits every genuinely non-real coordinate "
            "(the determination there is NEGATIVE, not undetermined), so the "
            "constructions that must be refused are accepted and the FIRST P2P "
            "test fails with a did-not-refuse — 1 failed, 0 passed. Does NOT "
            "resolve. This case has no nagini counterpart: nagini's carrier "
            "encodes the undetermined outcome as a third integer that its fold "
            "simply never triggers on, and no nagini rival keys off it."
        ),
        "rationale": (
            "REJECTED by the postcondition: `== some false` is an exact match on "
            "the DETERMINED-NON-ZERO value, so `none` must NOT qualify. Attacks "
            "layer L3 at the THIRD inhabited value of `imagPartDetZero` — the "
            "case that certifies the spec's test is a three-way discrimination "
            "and not a two-way one. Its own witness point (a coordinate whose "
            "determination is `none`) is one where BOTH other L3 rivals agree "
            "with the spec, so it is not sharing a sub-domain. If it VERIFIES => "
            "SPEC-TOO-WEAK."
        ),
        # concrete number, determination undetermined: spec demands false, rival
        # answers true.
        "witness": _wit("[%s]" % _UNDETERMINED,
                        "undetermined vanishing: spec accepts, rival rejects"),
    },
    {
        "id": "weak-drops-number-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOTNUM,
        "refinement": (
            "inverts the FIRST conjunct: the decision is taken on NON-concrete "
            "coordinates and skipped on concrete ones. Its faithful real "
            "counterpart negates the concreteness test in the guard. Measured "
            "against the actual harness: genuinely non-real CONCRETE coordinates "
            "are then permitted, so the FIRST P2P test fails with a "
            "did-not-refuse — 1 failed, 0 passed. Does NOT resolve. (nagini has "
            "no rival for this conjunct; its `coord_kind` dimension is only ever "
            "attacked jointly with the verdict.)"
        ),
        "rationale": (
            "REJECTED by the postcondition: `Coord.rejects` is the CONJUNCTION "
            "`isNumber && …`, so a non-concrete coordinate can never qualify no "
            "matter what its determination says. Attacks layer L2 (the "
            "per-element conjunction) at the `isNumber` observation — the only "
            "reject case whose witness holds `isNumber := false`, which is what "
            "keeps that field from being a binder every rival pins at one value. "
            "If it VERIFIES => SPEC-TOO-WEAK (the concreteness conjunct would be "
            "hollow)."
        ),
        # non-concrete coordinate carrying a determined-non-zero imaginary part:
        # spec demands false, rival answers true.
        "witness": _wit("[%s]" % _NONNUM_DET,
                        "non-concrete coordinate with determined-non-zero "
                        "imaginary part: spec accepts, rival rejects"),
    },
    {
        "id": "weak-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SKIP_LAST,
        "refinement": (
            "partial-domain: narrows the traversal so the LAST coordinate is "
            "never examined. Its faithful real counterpart restricts the "
            "existential to all but the final coordinate. Measured against the "
            "actual harness: a construction whose only non-real coordinate is "
            "the final one is then wrongly permitted, and the FIRST P2P test "
            "fails with a did-not-refuse — 1 failed, 0 passed. Does NOT resolve. "
            "This is the position-narrowing attack nagini ships as "
            "`rej-drop-first`; the FIRST-coordinate form was measured on this "
            "instance and its real patch passes all 13 harness tests, so it "
            "cannot honestly carry a refinement and the LAST-coordinate form is "
            "shipped in its place (see the header note)."
        ),
        "rationale": (
            "REJECTED by the postcondition `result = coords.any Coord.rejects`, "
            "whose existential ranges over EVERY element: dropping the final "
            "element leaves the verdict of `coords.dropLast`, which differs "
            "whenever the only qualifying coordinate is last. Attacks layer L1 "
            "(coverage of the existential). The ONLY reject case whose witness "
            "has length > 1 with the qualifying element in FINAL position — so "
            "it is what varies the list-length and position dimensions of the "
            "`coords` binder. If it VERIFIES => SPEC-TOO-WEAK (the spec would "
            "not pin which coordinates are examined)."
        ),
        # two coordinates, only the LAST qualifies: spec demands true, rival
        # answers false.
        "witness": _wit("[%s, %s]" % (_c("false", "false", "some true"),
                                      _QUALIFIES),
                        "only the final coordinate qualifies: spec rejects, "
                        "rival accepts"),
    },
    {
        "id": "weak-universal-not-existential",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALL,
        "refinement": (
            "replaces the EXISTENTIAL with a UNIVERSAL: the decision is taken "
            "only when EVERY coordinate qualifies. Its faithful real counterpart "
            "swaps the any-quantifier for an all-quantifier. Measured against "
            "the actual harness: a construction with one non-real and one real "
            "coordinate is then permitted, so the FIRST P2P test fails with a "
            "did-not-refuse — 1 failed, 0 passed. Does NOT resolve. No nagini "
            "counterpart: nagini's fold is fixed by its front-recursive @Pure "
            "helper, so the quantifier itself is not a dimension its rivals can "
            "reshape."
        ),
        "rationale": (
            "REJECTED by the postcondition: `List.any` is the EXISTENTIAL — one "
            "qualifying coordinate suffices — whereas this rival demands all of "
            "them. Attacks layer L1 (the quantifier). Refuted on a MIXED list, a "
            "sub-domain no other rival probes: every other reject witness is "
            "either single-element or has a single qualifying element, so only "
            "this one distinguishes any from all. Note it also answers `true` on "
            "the empty list where the spec demands `false`, so the collapse is "
            "not confined to mixed inputs. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # qualifying coordinate first, ordinary accepted coordinate second: spec
        # demands true, rival answers false.
        "witness": _wit("[%s, %s]" % (_QUALIFIES, _PLAIN),
                        "mixed list: spec rejects, rival accepts"),
    },
    {
        "id": "weak-never-rejects",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NEVER,
        "refinement": (
            "total collapse: the decision is dropped entirely and nothing is "
            "ever refused. Its faithful real counterpart removes the guard. "
            "Measured against the actual harness: every genuinely non-real "
            "construction is then accepted, so the FIRST P2P test fails with a "
            "did-not-refuse — 1 failed, 0 passed. Does NOT resolve: the "
            "constructor must still refuse determined-non-real coordinates, "
            "which is the behavior the narrowing preserves. Ports nagini's "
            "`rej-const-false`."
        ),
        "rationale": (
            "REJECTED by the postcondition: a constant `false` contradicts "
            "`coords.any Coord.rejects` on any list containing a qualifying "
            "coordinate. Attacks all three layers at once (the degenerate "
            "baseline: it is the control proving the spec has ANY value content, "
            "i.e. that `pos-oracle` verifying is not an echo artifact). Refuted "
            "at the minimal qualifying input. If it VERIFIES => SPEC-TOO-WEAK "
            "(the postcondition would place no constraint on the result at all)."
        ),
        # the single qualifying coordinate: spec demands true, rival answers
        # false.
        "witness": _wit("[%s]" % _QUALIFIES,
                        "lone qualifying coordinate: spec rejects, rival "
                        "accepts"),
    },
]


# The axiom lane belongs to G-AX and this gate ignores it. There is no consumed
# axiom and no opaque callee here in any case: the three per-coordinate
# observations are carried as record fields (A-references) and the changed
# classification is modeled DEEPLY in the spec over a transparent carrier.
AXIOM_TESTS = []
