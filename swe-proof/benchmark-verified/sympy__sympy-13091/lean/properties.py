# properties.py — PBT falsification battery for sympy__sympy-13091 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region surgery — it edits ONLY the impl region
# (and, where a reshaped impl needs it, the matching proof body), so the frozen
# spec (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and both `theorem correct_richEq` / `theorem correct_richNe`
# STATEMENTS are preserved verbatim. No case introduces sorry / admit /
# native_decide / axiom, nor any new theorem or lemma.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts a three-valued equality reply as an INTEGER code
# (a sentinel constant standing for "no opinion") plus a boolean inequality over
# that code. This Lean bundle models the SAME two behaviors on a total functional
# carrier: the value's own opinion is `Option Bool` (`none` = abstention, `some b`
# = a definite verdict), and the operand classification is spread over five
# independent boolean observations rather than nagini's two. So nagini's single
# `sympifiable` flag splits here into `interpretable` / `sameKind`, a `sameObj`
# identity binder appears, and an `identityOnly` FAMILY binder appears — which
# means the port ATTACKS MORE of the classifier than the nagini sibling could,
# not less.
#
# DEFENDED SURFACE (what every rival attacks):
#   `problem_spec_richEq …  : result = richEqRef sameObj identityOnly
#                                       interpretable sameKind contentEq
#                                       otherVerdict`
#     the resolved equality OPERATOR. Load-bearing consequences: a kind that
#     decides by bare object identity always has a DEFINITE opinion; for every
#     other kind the value's own opinion is an ABSTENTION exactly when the
#     operand cannot be interpreted (and only then); a definite own opinion is
#     taken directly; an abstention defers to the operand's reflected opinion;
#     and two abstentions fall back to identity — `false` for distinct objects.
#   `problem_spec_richNe … : result = richNeRef …`
#     the inequality operator = negation of the FULLY RESOLVED equality operator,
#     NOT of the value's own (possibly abstaining) opinion. The two diverge
#     exactly when the own opinion abstains, which is the sub-domain the second
#     modeled behavior exists to fix.
#
# Input binders of the two spec predicates: sameObj, identityOnly, interpretable,
# sameKind, contentEq, otherVerdict. The 23 reject witnesses probe FIFTEEN
# distinct input points (23 counting the obligation they are asserted on: 15 on
# the equality obligation, 8 on the inequality one) and move every one of the six
# binders: sameObj is held TRUE at one point and FALSE elsewhere; identityOnly is
# held TRUE at three points and FALSE elsewhere; interpretable, sameKind and
# contentEq each take both settings; and otherVerdict takes all THREE of its
# inhabited shapes (`some true`, `some false`, `none`). No binder is pinned across
# the battery, so a rival mishandling only one of them cannot slip past. FOUR of
# those points pair a DEFINITE own opinion with a definite reflected opinion,
# which is what makes the resolution's dispatch ORDER observable at all; they
# carry six of the witnesses (four on the equality obligation and two on the
# inequality one), so the ordering is probed on BOTH modeled behaviors rather
# than only the first.
#
# (Every count in this header is machine-checked against the witness set, not
# asserted: an earlier revision claimed SEVEN points and "two" definite/definite
# pairs, and both numbers had gone stale as rivals were added. A stale count is
# not cosmetic here — the no-binder-is-pinned argument is what licenses the
# claim that a rival mishandling a single binder cannot slip past.)
#
# Coverage is measured by EXHAUSTION rather than argued. The two obligations are
# total functions of six decidable inputs, so the input space is exactly 96
# points (2^5 boolean classifiers x 3 inhabited shapes of the reflected
# opinion). Each rival's divergence set — the points where its impl disagrees
# with the frozen reference — is enumerated by the verifier itself, and every
# rival's own witness point is checked to lie inside its own divergence set.
# Divergence-set sizes range from 1 to 84 of 96, no two rivals have the SAME
# divergence set, and no rival is definitionally equal to the frozen impl on this
# carrier, so every rejection is attributable to an observable disagreement
# rather than to a tactic mismatch.
#
# Weakness classes attacked, carried over from the nagini sibling:
#   * partial-domain — the un-interpretable-operand sub-domain, the input that
#     fails first in the two gated tests (rej-abstain-to-negative,
#     rej-abstain-to-positive);
#   * value-double-mask — collapse every branch to one constant
#     (rej-constant-negative), or drop a whole dimension of the decision
#     (rej-ne-drops-reflected);
#   * control-flow-effect — treat a non-boolean abstention as if it were a
#     boolean and negate it (rej-ne-negates-own-opinion), or invert which
#     opinion WINS when both are definite, on the equality obligation
#     (rej-reflected-priority) and on the inequality obligation
#     (rej-ne-reflected-priority);
#   * over-abstention — abstain on a branch the spec pins to a DEFINITE verdict,
#     handing the decision to the operand: on the KIND branch
#     (rej-wrong-kind-abstains), on the deeper CONTENT branch
#     (rej-content-false-abstains, which diverges from the reference at exactly
#     one of the 96 input points), and on the FAMILY branch, where a kind that
#     decides by bare object identity is made to abstain
#     (rej-identity-only-abstains, and rej-ne-identity-only-abstains on the other
#     obligation). This is the ONLY-IF half of the abstention clause, which the
#     rivals ported from nagini left unattacked;
#   * family-conflation — treat the two real families of equality test as one.
#     The identity-only family is made to answer a definite POSITIVE for any
#     operand (rej-identity-only-positive), and the family observation is DELETED
#     from the cascade altogether (rej-identity-only-ignored), which is exactly
#     the shape the spec had before the observable was added. These two are what
#     make the family observation load-bearing rather than decorative: measured,
#     the divergence sets of all four family rivals contain NO witness point that
#     predates the refinement, so before they were landed nothing in the battery
#     refuted a rival that ignored the family;
#   * per-branch value corruption on each of the DECIDED branches
#     (rej-wrong-kind-positive, rej-content-ignored, rej-content-inverted) and on
#     the both-abstain identity fallback, which is attacked three ways: collapsed
#     to a constant positive on the equality obligation
#     (rej-identity-fallback-positive), made to READ each of the two classifier
#     observations the spec discards there — content
#     (rej-identity-fallback-reads-content) and kind
#     (rej-identity-fallback-reads-kind) — and, on the inequality obligation,
#     both inverted to a constant (rej-ne-fallback-polarity) and made to read
#     the content observation (rej-ne-fallback-reads-content). The last four were
#     added by audit: the constant-collapse rival attacks the arm only where it
#     is reached at all, so a rival correct wherever the discarded observation is
#     FALSE, and a rival corrupting the arm on the OTHER obligation, were each
#     refuted by no witness in the battery. Every one of the four was
#     machine-checked to have a divergence set DISJOINT from every witness point
#     that predated it, which is what makes them additions rather than
#     restatements.
# Both pre-patch behaviors carried by this bundle are reproduced inside the impl
# region as rivals (rej-abstain-to-negative, rej-ne-negates-own-opinion).
#
# SPEC-STRENGTH PROBES an independent audit ran against the frozen spec, recorded
# because a negative result is evidence and is otherwise unrecoverable:
#   * three further WRONG impls beyond the shipped rivals — the both-abstain arm
#     reading the KIND observation, the same leak on the inequality obligation,
#     and the classifier cascade reordered so the KIND test precedes the
#     INTERPRETABLE one — were each REJECTED (no SPEC-TOO-WEAK hole). The first
#     two were refuted by no shipped witness, so they were landed as
#     rej-identity-fallback-reads-kind and rej-ne-fallback-reads-content; the
#     cascade-reorder rival is already refuted by rej-abstain-to-negative's
#     witness point, so it would have been a restatement and was not landed.
#   * a fourth WRONG impl, probed when the FAMILY observation was added: the
#     family test demoted BELOW the interpretable test (`if sameObj … else if
#     !interpretable then none else if identityOnly then some false …`). Measured,
#     its divergence set is a strict subset of rej-identity-only-abstains' and
#     CONTAINS that rival's witness point, so it is refuted by a shipped witness
#     and would have been a restatement; not landed.
#   * four further CORRECT reshapes — the equality resolved by flat guarded
#     returns with the reflected consultation inlined as a `match` expression,
#     the equality resolved through `Option.getD` chaining, the inequality
#     resolved by a `match` on the equality impl's Bool rather than by `!`, and
#     the family test HOISTED above the identity test (`if identityOnly then some
#     sameObj else …`, which is extensionally the frozen cascade) — each VERIFIED
#     against the frozen obligations (no SPEC-TOO-STRONG hole). The last one is
#     shipped as pos-eq-family-first, because it is the reshape that shows the
#     new family clause constrains the RESULT rather than the branch ORDER.
#
# OMITTED nagini cases and why (repeated in the payload `assessment`):
#   * FRAME / permission-mutation rivals: VACUOUS on this backend. Lean is
#     referentially transparent — there is no aliasing and no fractional
#     permission to violate — so there is no counterpart rival to author, and
#     fabricating a substitute would attest to a check that does not exist.
#   * DIVERGENCE / non-termination rivals (nagini's rej-eq-diverge,
#     rej-ne-diverge, which lean on a termination-measure obligation): no rival
#     ships, and the reason is a TOOLING limit on the witness, not a property of
#     the spec. Measured two ways during this audit. (a) A recursive equality
#     impl that self-loops on the un-interpretable branch with NO decreasing
#     measure, left as a total `def`, IS rejected — and rejected by a genuine
#     termination obligation ("fail to show termination for
#     implementation_richEq / failed to infer structural recursion"), which is
#     exactly the disposition the total setting calls for. But the rival's own
#     file does not compile, so a witness built against it cannot elaborate
#     either (measured: the witness build fails with that same termination
#     error, which the gate would record as `witness-unproven` — an inconclusive
#     outcome, i.e. a MALFORMED battery, not a rejection). (b) Adding `partial`
#     lets the DECLARATION elaborate, but the impl then has no equation lemmas,
#     so both the frozen tactic script and any witness stall on the same error
#     ("Tactic `unfold` failed to unfold `implementation_richEq`") rather than on
#     the claim — a proof/tactic gap that attributes nothing to the spec, and one
#     that would make the WITNESS build fail too (recorded `witness-unproven`,
#     i.e. inconclusive). Re-measured during this audit, both halves: the total
#     `def` fails "fail to show termination for implementation_richEq" on the
#     rival AND on the witness built against it; the `partial def` fails the
#     unfold on the rival AND on the witness. Neither half yields the
#     rival-succeeds / gold-fails pair a shippable reject case needs.
#     Re-measured a THIRD time by an independent audit that rebuilt both shapes
#     from scratch (a self-recursive equality impl with no decreasing measure on
#     the un-interpretable branch): the total `def` variant exits 1 with "fail to
#     show termination for implementation_richEq" and its witness exits 1 with
#     that SAME termination error; the `partial def` variant exits 1 and its
#     witness exits 1, both with "Tactic `unfold` failed to unfold
#     `implementation_richEq`". The witness half fails in each shape, so the case
#     would be recorded `witness-unproven` (inconclusive => MALFORMED battery)
#     rather than `rejected`. Independently confirmed as a witness TOOLING limit
#     — neither a spec hole nor a vacuous class.
#     Since a lean `def` is total by elaboration, the termination obligation here
#     is discharged by the ELABORATOR rather than by a proof the spec can be
#     refuted against, so this class has no shippable witness on this carrier.
#     Note this bundle carries NO `set_option loom.semantics.termination` line —
#     that option is a velvet construct (0 of the lean Solution.lean files in the
#     corpus set it), so the total-vs-partial disposition here is decided by Lean
#     totality rather than by a bundle setting. On velvet under partial semantics
#     the same class is a known and already-recorded spec hole (the corpus-wide
#     termination-semantics finding), not a new finding.
#   * ADMISSIBILITY: a counterpart IS shipped — adm-resolution-satisfiable. An
#     earlier note here argued none was needed because both obligations are
#     unconditional `∀` statements with no precondition hypothesis, so no
#     precondition could be too strong. That reason is wrong for this lane: on a
#     total carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#     UNSATISFIABLE at a normally-shaped input, which a positive that discharges
#     the obligation at that concrete input — by evaluation, as a `have`, before
#     closing the frozen obligation verbatim — tests directly. The three points
#     grounded are the ones the modeled behaviors turn on (abstention defers to a
#     definite reflected opinion; both-abstain falls back to identity; and the
#     identity-only family answers a definite negative even when the operand
#     claims equality). The symmetry consequence nagini's admiss-ne-symmetry
#     pinned is ALSO attacked directly, by rej-ne-drops-reflected, so the two
#     lanes are complementary rather than redundant.
#   * AXIOM_TESTS: dropped — the axiom lane is G-AX's job, and this bundle ships
#     no consumed axiom (the operand's reflected opinion is a free input, not a
#     callee contract).
from pathlib import Path

INSTANCE = "sympy__sympy-13091"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — every one lies strictly INSIDE the impl or proof region of
# the frozen Solution.lean and is unique in the file.
#
# NOTE: the classifier cascade text alone is NOT unique — the pure region states
# the same cascade. Each anchor below therefore carries enough surrounding impl
# context (the `let selfVerdict : Option Bool :=` binder, the `match … return`
# arms) to pin it to the impl region; `_swap` asserts that uniqueness.
# ---------------------------------------------------------------------------

# The frozen equality impl (whole impl-region body of the first function).
_EQ_IMPL = """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  match selfVerdict with
  | some b => return b
  | none =>
    match otherVerdict with
    | some b => return b
    | none => return false"""

# Just the classifier cascade of the equality impl, disambiguated from the pure
# region by the `let selfVerdict` binder above it and the `match selfVerdict`
# below it.
_EQ_CASCADE = """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  match selfVerdict"""

# The frozen inequality impl (whole impl-region body of the second function).
_NE_IMPL = """  let eqResult := implementation_richEq sameObj identityOnly interpretable sameKind
    contentEq otherVerdict
  return !eqResult"""

# The two frozen proof bodies. Only the soundness positives touch these, and
# only because a reshaped impl needs a proof that closes for the NEW shape.
_EQ_PROOF = """  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
  simp only [Id.run]
  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
    cases otherVerdict <;> rfl"""

_NE_PROOF = """  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
    selfEqVerdict
  simp only [Id.run]
  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
    cases otherVerdict <;> rfl"""


def _cascade(interp_arm, kind_arm, content_arm, family_arm="some false"):
    """The equality impl's classifier cascade with chosen branch values.

    `family_arm` defaults to the frozen `some false`, so every pre-existing rival
    call site keeps meaning exactly what it meant before the family observation
    was added to the carrier."""
    return (
        "  let selfVerdict : Option Bool :=\n"
        "    if sameObj then some true\n"
        f"    else if identityOnly then {family_arm}\n"
        f"    else if !interpretable then {interp_arm}\n"
        f"    else if !sameKind then {kind_arm}\n"
        f"    else {content_arm}\n"
        "  match selfVerdict")


# ---------------------------------------------------------------------------
# WITNESS BUILDERS
#
# Both spec predicates are total functions of six decidable inputs, so the
# refutation can be stated at CONCRETE literals and closed by `decide` — no
# opaque term to condition on, hence no hypothesis binders and nothing that
# could be jointly unsatisfiable. Each `example` asserts that the spec predicate
# does NOT hold of the variant's own output at one point: it elaborates against
# the rival (which is wrong there) and fails against the frozen solution (which
# satisfies the spec everywhere).
#
# `identityOnly` is a trailing KEYWORD argument defaulting to "false": the
# family observation was added to the carrier after most of these rivals, and a
# default keeps every pre-existing witness point literally unchanged (a rival
# about the classify-then-compare family is probed on that family) instead of
# silently renumbering nineteen positional call sites.
# ---------------------------------------------------------------------------

def _w_eq(sameObj, interpretable, sameKind, contentEq, otherVerdict,
          identityOnly="false"):
    args = (f"{sameObj} {identityOnly} {interpretable} {sameKind} {contentEq}"
            f" {otherVerdict}")
    return (
        f"example : ¬ problem_spec_richEq {args}\n"
        f"    (implementation_richEq {args}) := by\n"
        "  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq"
        " selfEqVerdict\n"
        "  decide")


def _w_ne(sameObj, interpretable, sameKind, contentEq, otherVerdict,
          identityOnly="false"):
    args = (f"{sameObj} {identityOnly} {interpretable} {sameKind} {contentEq}"
            f" {otherVerdict}")
    return (
        f"example : ¬ problem_spec_richNe {args}\n"
        f"    (implementation_richNe {args}) := by\n"
        "  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef"
        " resolveEq selfEqVerdict\n"
        "  decide")


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls.
# Each reproves its own obligation inside the proof region; the theorem
# STATEMENT is untouched.
# ---------------------------------------------------------------------------

# pos-eq-early-return: drops the intermediate `Option Bool` local entirely and
# answers with EARLY RETURNS in the decided cases, falling through to the
# reflected-opinion consultation only when the operand cannot be interpreted.
# Same mapping, different control shape (no explicit abstention value is ever
# constructed — the abstention becomes control flow).
_POS_EQ_IMPL = """  if sameObj then
    return true
  if identityOnly then
    return false
  if interpretable then
    if sameKind then
      return contentEq
    else
      return false
  match otherVerdict with
  | some b => return b
  | none => return false"""

_POS_EQ_PROOF = """  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
  simp only [Id.run]
  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
    cases otherVerdict <;> rfl"""

# pos-eq-oracle-echo: the cheapest honest impl — return the pure-region resolved
# operator directly. This is NOT an ungrounded-oracle echo: `richEqRef` is a
# fully unfolded total function of the six inputs (it computes the classifier
# and the resolution itself, with no opaque callee), so echoing it does the work
# rather than reading an answer key. Carried over from the nagini sibling's
# pos-eq-echo, whose oracle was grounded for the same reason.
_POS_ECHO_IMPL = ("  return richEqRef sameObj identityOnly interpretable sameKind"
                  " contentEq otherVerdict")

_POS_ECHO_PROOF = """  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
  unfold problem_spec_richEq implementation_richEq
  rfl"""

# pos-eq-family-first: HOISTS the family observation above the identity one —
# `if identityOnly then some sameObj else <the rest of the frozen cascade>`. A
# kind that decides by bare object identity answers precisely the identity
# observation, so this is extensionally the frozen cascade with the first two
# tests exchanged. It is the reshape that shows the family clause constrains the
# RESULT and not the branch ORDER: if the spec had been written so that only the
# frozen ordering could satisfy it, this correct impl would fail and the spec
# would be SPEC-TOO-STRONG on the observable that was just added.
_POS_FAMILY_FIRST_IMPL = """  let selfVerdict : Option Bool :=
    if identityOnly then some sameObj
    else if sameObj then some true
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  match selfVerdict with
  | some b => return b
  | none =>
    match otherVerdict with
    | some b => return b
    | none => return false"""

# pos-ne-inlined: the inequality impl stops calling the equality impl and
# INLINES the whole resolution into a local, negating that. Same resolved-
# operator semantics, different call/local structure — the port of nagini's
# pos-ne-reshape.
_POS_NE_IMPL = """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  let resolved : Bool :=
    match selfVerdict with
    | some b => b
    | none => match otherVerdict with
      | some b => b
      | none => false
  return !resolved"""

_POS_NE_PROOF = """  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
    selfEqVerdict
  simp only [Id.run]
  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
    cases otherVerdict <;> rfl"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY — the obligation is SATISFIABLE at the concrete inputs that
# characterise the modeled sub-domain, discharged by evaluation as a `have`
# BEFORE the frozen obligation is closed verbatim.
#
# On a total carrier there is no precondition to be too strong, so the analogue
# of PRECOND-TOO-STRONG is the obligation being unsatisfiable at exactly a
# normally-shaped input — which is what these `have`s test directly. If the
# reference resolution were internally inconsistent at the point where the
# abstention defers to the operand, at the point where both sides abstain and
# the operator falls back to identity, or at the point where a kind that decides
# by bare object identity must overrule an operand that claims equality,
# `decide` could not close these and the case would fail while every uniqueness
# rival still passed. All three points are ones the modeled behaviors turn on, so
# these are the ground instances that matter rather than arbitrary ones.
# ---------------------------------------------------------------------------

_ADM_EQ = """  -- Ground the equality obligation at the sub-domain's own inputs: an operand
  -- the value cannot interpret whose reflected opinion is a definite positive
  -- (the abstention must DEFER, not decide) ...
  have _defer : problem_spec_richEq false false false false false (some true)
      (implementation_richEq false false false false false (some true)) := by
    unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
    decide
  -- ... at the both-abstain point, where the operator falls back to object
  -- identity and must answer `false` for two distinct objects ...
  have _fallback : problem_spec_richEq false false false false false none
      (implementation_richEq false false false false false none) := by
    unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
    decide
  -- ... and at the family point, where a kind deciding by bare object identity
  -- must answer a definite `false` for a non-identical operand even though the
  -- operand itself claims equality (no abstention, hence no deferral).
  have _family : problem_spec_richEq false true false false false (some true)
      (implementation_richEq false true false false false (some true)) := by
    unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
    decide
"""

_ADM_NE = """  -- The same three points on the inequality obligation, where the resolved
  -- equality is negated: deferring to a definite reflected positive must yield
  -- `false`, the both-abstain identity fallback must yield `true`, and the
  -- identity-only family's definite negative must yield `true`.
  have _defer : problem_spec_richNe false false false false false (some true)
      (implementation_richNe false false false false false (some true)) := by
    unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
      selfEqVerdict
    decide
  have _fallback : problem_spec_richNe false false false false false none
      (implementation_richNe false false false false false none) := by
    unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
      selfEqVerdict
    decide
  have _family : problem_spec_richNe false true false false false (some true)
      (implementation_richNe false true false false false (some true)) := by
    unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
      selfEqVerdict
    decide
"""


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — each keeps the frozen spec and the frozen proof scripts,
# and each is refuted by a witness that has been SEEN to discriminate.
# ---------------------------------------------------------------------------

# The un-interpretable branch commits to a definite NEGATIVE instead of
# abstaining: the operand's reflected opinion is then never consulted.
_REJ_ABSTAIN_NEG = _swap(_BASE, _EQ_CASCADE,
                         _cascade("some false", "some false", "some contentEq"))

# The un-interpretable branch commits to a definite POSITIVE — the opposite
# wrong sentinel, equally blind to the reflected opinion.
_REJ_ABSTAIN_POS = _swap(_BASE, _EQ_CASCADE,
                         _cascade("some true", "some false", "some contentEq"))

# Collapse the entire decision to a constant negative.
_REJ_CONST_NEG = _swap(_BASE, _EQ_IMPL, "  return false")

# The wrong-kind branch claims a definite POSITIVE: an operand that CAN be
# interpreted but is of an incomparable kind is reported equal.
_REJ_WRONG_KIND_POS = _swap(_BASE, _EQ_CASCADE,
                            _cascade("none", "some true", "some contentEq"))

# The content comparison is ignored: a same-kind operand is always reported
# equal regardless of whether its content coincides.
_REJ_CONTENT_IGNORED = _swap(_BASE, _EQ_CASCADE,
                             _cascade("none", "some false", "some true"))

# The content comparison is INVERTED on the same-kind branch.
_REJ_CONTENT_INVERTED = _swap(_BASE, _EQ_CASCADE,
                              _cascade("none", "some false", "some (!contentEq)"))

# OVER-ABSTENTION: the wrong-kind branch ABSTAINS instead of committing to a
# definite negative, so an interpretable-but-incomparable operand's own verdict
# is wrongly deferred to the operand. Added by audit: every pre-existing rival
# either kept this branch definite-negative or corrupted its VALUE, so the
# clause "abstention happens exactly when the operand is un-interpretable, and
# ONLY then" had no rival attacking its ONLY-then half.
_REJ_WRONG_KIND_ABSTAINS = _swap(_BASE, _EQ_CASCADE,
                                 _cascade("none", "none", "some contentEq"))

# DISPATCH ORDER INVERTED: the operand's reflected opinion is consulted FIRST
# and the value's own opinion only when the operand abstains. Added by audit:
# every pre-existing rival preserved left-first resolution, so the ordering
# half of the resolution rule (own opinion takes precedence when DEFINITE) was
# unattacked — a rival that merely swaps the two consultations would have
# verified against a spec that only pinned "consult both".
_REJ_REFLECTED_PRIORITY = _swap(_BASE, _EQ_IMPL, """  match otherVerdict with
  | some b => return b
  | none =>
    if sameObj then return true
    else if identityOnly then return false
    else if !interpretable then return false
    else if !sameKind then return false
    else return contentEq""")

# The identity fallback is wrong: when BOTH sides abstain the operator reports
# equal instead of falling back to identity for distinct objects.
_REJ_IDENTITY_POS = _swap(_BASE, _EQ_IMPL,
                          _EQ_IMPL.replace("    | none => return false",
                                           "    | none => return true"))

# FAMILY CONFLATION, over-abstention flavour: a kind that decides by bare object
# identity is made to ABSTAIN for a non-identical operand instead of answering a
# definite negative, so the operand's reflected opinion decides a comparison the
# real method settles by itself. Added when the family observation was added to
# the carrier: measured, this rival's divergence set (8 of the 96 points)
# contains NO witness point that predates the refinement, so nothing in the
# battery refuted it before.
_REJ_IDONLY_ABSTAINS = _swap(_BASE, _EQ_CASCADE,
                             _cascade("none", "some false", "some contentEq",
                                      family_arm="none"))

# FAMILY CONFLATION, value flavour: the identity-only family reports EQUAL for
# every operand, i.e. its bare identity test is replaced by a constant positive.
_REJ_IDONLY_POSITIVE = _swap(_BASE, _EQ_CASCADE,
                             _cascade("none", "some false", "some contentEq",
                                      family_arm="some true"))

# FAMILY CONFLATION, deletion flavour: the family observation is DROPPED from
# the cascade entirely, so a kind that decides by bare object identity is run
# through the interpret / kind / content path meant for the other family. This
# is exactly the impl shape the bundle carried BEFORE the family observation was
# added, which is what makes the observable load-bearing rather than decorative:
# if no witness refuted this rival, the observable could be deleted from the
# spec with nothing noticing. Measured, its divergence set (7 of 96 points) is
# reached by no pre-refinement witness, and it is DISTINCT from
# rej-identity-only-abstains — each diverges at points where the other agrees
# with the reference — so its own witness holds the family observation TRUE
# together with a fully comparable, content-coinciding operand, the shape where
# the deleted clause changes the answer and the abstaining rival does not.
_REJ_IDONLY_IGNORED = _swap(_BASE, _EQ_CASCADE, """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  match selfVerdict""")

# Inequality negates the value's OWN opinion, coercing an abstention as though
# it were a definite positive — so an abstention yields a definite negative and
# the reflected consultation is dropped.
_REJ_NE_NEG_OWN = _swap(_BASE, _NE_IMPL, """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  let ownAnswer := match selfVerdict with
    | some b => b
    | none => true
  return !ownAnswer""")

# Inequality drops the reflected consultation the other way: a definite own
# opinion is negated correctly, but an abstention short-circuits to a definite
# "unequal" without ever consulting the operand.
_REJ_NE_DROPS_REFLECTED = _swap(_BASE, _NE_IMPL, """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  return match selfVerdict with
    | some b => !b
    | none => true""")

# Inequality forgets to NEGATE on the decided-own-opinion branch (it is correct
# on the abstention branch), so on a decided operand it reports the equality
# answer verbatim.
_REJ_NE_UNNEGATED = _swap(_BASE, _NE_IMPL, """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  match selfVerdict with
  | some b => return b
  | none =>
    match otherVerdict with
    | some b => return !b
    | none => return true""")

# Inequality drops the identity observation from its classification: the value
# compared against itself is no longer short-circuited to a definite positive.
_REJ_NE_NO_IDENTITY = _swap(_BASE, _NE_IMPL, """  let selfVerdict : Option Bool :=
    if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  let resolved : Bool :=
    match selfVerdict with
    | some b => b
    | none => match otherVerdict with
      | some b => b
      | none => false
  return !resolved""")

# DISPATCH ORDER INVERTED ON THE INEQUALITY SIDE: the inequality stops
# delegating and resolves the equality itself, but consults the operand's
# reflected opinion FIRST. Added by audit: the ordering half of the resolution
# rule was attacked only on the EQUALITY obligation, so a rival that inverted
# the priority inside the inequality's own resolution — where the negation makes
# the error present differently — had no witness anywhere in the battery.
_REJ_NE_REFLECTED_PRIORITY = _swap(_BASE, _NE_IMPL, """  let resolved : Bool :=
    match otherVerdict with
    | some b => b
    | none =>
      if sameObj then true
      else if identityOnly then false
      else if !interpretable then false
      else if !sameKind then false
      else contentEq
  return !resolved""")

# OVER-ABSTENTION ON THE CONTENT BRANCH: a same-kind operand whose content does
# NOT coincide gets an abstention instead of the definite negative the spec
# pins, so that decision is handed to the operand. Added by audit: the only-if
# half of the abstention clause was attacked on the KIND branch alone
# (rej-wrong-kind-abstains), leaving the deepest branch of the cascade — the one
# that actually compares content — with no over-abstention rival. This is the
# battery's narrowest rival: it diverges from the reference at exactly ONE of
# the 96 points, so it is refuted only by a witness that pairs a content
# mismatch with a definite reflected opinion.
_REJ_CONTENT_FALSE_ABSTAINS = _swap(
    _BASE, _EQ_CASCADE,
    _cascade("none", "some false", "if contentEq then some true else none"))

# BOTH-ABSTAIN FALLBACK READS AN OBSERVATION IT MUST IGNORE: when neither side
# has an opinion the operator is pinned to object identity — `false` for two
# distinct objects — but this rival answers with the CONTENT observation
# instead. Added by audit: rej-identity-fallback-positive corrupts the same arm
# to a CONSTANT positive, so every one of its divergence points sits at
# contentEq irrelevant; a rival that makes the arm DEPEND on a classifier
# observation the spec has already discarded there diverges only where the
# content coincides, and no witness in the battery held contentEq TRUE together
# with an abstaining own opinion. Machine-checked: this rival's two divergence
# points are disjoint from every pre-existing witness point.
_REJ_IDENTITY_READS_CONTENT = _swap(
    _BASE, _EQ_IMPL,
    _EQ_IMPL.replace("    | none => return false",
                     "    | none => return contentEq"))

# BOTH-ABSTAIN FALLBACK READS THE *KIND* OBSERVATION: same arm, a different
# discarded observation. Added by a second audit: the two pre-existing fallback
# rivals corrupt the arm to a constant (rej-identity-fallback-positive) or make
# it read `contentEq` (rej-identity-fallback-reads-content), so a rival reading
# `sameKind` there diverges only where sameKind is TRUE while the operand is
# un-interpretable — a shape NO witness in the battery held, since every
# sameKind=true witness also held interpretable=true. Machine-checked: this
# rival's divergence set (2 of 96 points) is disjoint from all pre-existing
# witness points, so it was refuted by nothing.
_REJ_IDENTITY_READS_KIND = _swap(
    _BASE, _EQ_IMPL,
    _EQ_IMPL.replace("    | none => return false",
                     "    | none => return sameKind"))

# THE SAME LEAK ON THE INEQUALITY OBLIGATION: the inequality stops delegating,
# resolves for itself, and makes the both-abstain arm read the CONTENT
# observation the spec discards there. Added by the same audit: the
# content-reading fallback was attacked only on the equality obligation, and
# rej-ne-fallback-polarity inverts that arm to a CONSTANT, so it diverges
# wherever the arm is reached while this rival is correct wherever the content
# does not coincide — neither refutes the other. Machine-checked: its 2
# divergence points are disjoint from all other witness points.
_REJ_NE_FALLBACK_READS_CONTENT = _swap(_BASE, _NE_IMPL, """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  let resolved : Bool :=
    match selfVerdict with
    | some b => b
    | none => match otherVerdict with
      | some b => b
      | none => contentEq
  return !resolved""")

# THE SAME ARM ON THE INEQUALITY OBLIGATION, resolved in-line: the inequality
# stops delegating and resolves the equality itself, but inverts the polarity of
# the both-abstain identity fallback (`true` where the spec pins `false`), so it
# reports two mutually-unintelligible operands as NOT unequal. Added by audit:
# the identity-fallback arm was attacked only on the EQUALITY obligation
# (rej-identity-fallback-positive), and every inequality rival either reaches
# that arm correctly or does not reach it at all — so this inversion was
# refuted by no witness anywhere in the battery.
_REJ_NE_FALLBACK_POLARITY = _swap(_BASE, _NE_IMPL, """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  let resolved : Bool :=
    match selfVerdict with
    | some b => b
    | none => match otherVerdict with
      | some b => b
      | none => true
  return !resolved""")

# FAMILY CONFLATION ON THE INEQUALITY OBLIGATION: the inequality stops
# delegating, resolves the equality itself, and makes the identity-only family
# ABSTAIN rather than answer its definite negative. Added with the family
# observation: the family clause was otherwise attacked on the EQUALITY
# obligation only, and every inequality rival in the battery keeps the family
# arm definite, so this was refuted by no inequality witness. Measured: 8
# divergence points, none of them a pre-refinement witness point.
_REJ_NE_IDONLY_ABSTAINS = _swap(_BASE, _NE_IMPL, """  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then none
    else if !interpretable then none
    else if !sameKind then some false
    else some contentEq
  let resolved : Bool :=
    match selfVerdict with
    | some b => b
    | none => match otherVerdict with
      | some b => b
      | none => false
  return !resolved""")


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # ------------------------- POSITIVE CONTROLS -------------------------
    {
        "id": "pos-eq-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _EQ_IMPL, _POS_EQ_IMPL),
                        _EQ_PROOF, _POS_EQ_PROOF),
        "rationale": (
            "A structurally-different but CORRECT equality impl: the "
            "intermediate three-valued local is removed and the decided cases "
            "answer by EARLY RETURN, so the abstention is expressed as control "
            "flow (falling through to the reflected-opinion consultation) rather "
            "than as a constructed value. Same input-output mapping, different "
            "shape. No loop, so no induction is needed; the reproved script "
            "reduces the `do` block and case-splits the five boolean binders and "
            "the reflected-opinion shape. It must satisfy `result = richEqRef …`; "
            "if a faithful correct reshape cannot, the spec is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-eq-oracle-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _EQ_IMPL, _POS_ECHO_IMPL),
                        _EQ_PROOF, _POS_ECHO_PROOF),
        "rationale": (
            "The cheapest honest impl: return the pure-region resolved operator "
            "directly. This is a legitimate positive, not an ungrounded-oracle "
            "echo — the pure helper is a fully unfolded total function of the "
            "six inputs, computing the classifier and the resolution itself "
            "with no opaque callee, so echoing it performs the work rather than "
            "reading an answer key. Ported from the nagini sibling's echo "
            "positive, which was admissible for the same reason. Must verify "
            "against `result = richEqRef …`."
        ),
    },
    {
        "id": "pos-eq-family-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _EQ_IMPL, _POS_FAMILY_FIRST_IMPL),
                        _EQ_PROOF, _POS_EQ_PROOF),
        "rationale": (
            "A CORRECT reshape of the observable this bundle's refinement added: "
            "the family test is hoisted ABOVE the identity test and answers "
            "`some sameObj` there, which is extensionally the frozen cascade "
            "(a kind that decides by bare object identity answers precisely the "
            "identity observation, so the two orderings agree at every one of "
            "the 96 input points — machine-checked). It must verify: if the "
            "family clause had been stated in a way that only the frozen branch "
            "ORDER could satisfy, this impl would fail and the newly added "
            "observable would be SPEC-TOO-STRONG. Shipped because the family "
            "observable is new and an over-strong new clause is the specific "
            "failure mode a refinement risks."
        ),
    },
    {
        "id": "pos-ne-inlined",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _NE_IMPL, _POS_NE_IMPL),
                        _NE_PROOF, _POS_NE_PROOF),
        "rationale": (
            "A structurally-different but CORRECT inequality impl: it stops "
            "delegating to the equality impl and INLINES the whole resolution "
            "into a local before negating. Same resolved-operator semantics, "
            "different call and local structure — the port of the nagini "
            "sibling's reshape positive. Must verify against "
            "`result = richNeRef …` else SPEC-TOO-STRONG."
        ),
    },

    # -------------------------- ADMISSIBILITY ---------------------------
    {
        "id": "adm-resolution-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _EQ_PROOF, _ADM_EQ + _EQ_PROOF),
                        _NE_PROOF, _ADM_NE + _NE_PROOF),
        "rationale": (
            "Both obligations are discharged at the CONCRETE inputs that "
            "characterise the modeled sub-domain — an un-interpretable operand "
            "with a definite reflected positive (the abstention must defer), the "
            "both-abstain point (the operator must fall back to identity), and "
            "the identity-only family facing an operand that claims equality "
            "(the family must answer a definite negative and NOT defer) — by "
            "evaluation, as `have`s, before the frozen obligation is closed "
            "verbatim. On this total carrier no binder has a precondition, so "
            "PRECOND-TOO-STRONG cannot arise as an unsatisfiable guard; its "
            "analogue is the obligation being unsatisfiable at exactly a "
            "normally-shaped input, which is what these ground instances test. "
            "They are not decoration: if the reference resolution were "
            "inconsistent at any of the three points, `decide` could not close "
            "them and this case would fail while every uniqueness rival still "
            "passed, because a rival's witness only ever asserts the spec is "
            "VIOLATED somewhere and never that it is SATISFIABLE anywhere. "
            "Nothing is assumed — no new declaration, both theorem statements "
            "byte-identical, the ground instances are `have`s inside the "
            "existing tactic bodies. Ports the nagini sibling's "
            "admiss-ne-symmetry, whose in-impl Assert pinned the same "
            "incomparable-equal-peer consequence."
        ),
    },

    # ----------------------- UNIQUENESS / REJECT ------------------------
    {
        "id": "rej-abstain-to-negative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_ABSTAIN_NEG,
        "refinement": (
            "This is the first of the two behaviors this bundle exists to fix, "
            "reproduced inside the impl region: when the operand cannot be "
            "interpreted, the value commits to a definite negative instead of "
            "declining to opine. Its faithful real patch is simply the UNFIXED "
            "code — the value asserts inequality without ever giving the operand "
            "a chance to answer, so an operand that considers itself equal to the "
            "value is contradicted and the relation becomes asymmetric. That is "
            "exactly the asymmetry the two gated tests assert against (they "
            "compare in BOTH directions and require agreement), so a faithful "
            "patch would NOT resolve them. A verifying rival here would therefore "
            "be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …`: the reference resolution takes "
            "the own opinion only when it is DEFINITE and otherwise defers to "
            "`otherVerdict`, so on an un-interpretable operand whose reflected "
            "opinion is a definite positive the spec demands `true` while this "
            "rival returns `false`. Witness at "
            "(sameObj=false, identityOnly=false, interpretable=false, "
            "otherVerdict=some true) — the point where the dropped consultation "
            "is observable. [partial-domain: diverges only on the "
            "un-interpretable sub-domain, 4 of the 96 points.]"
        ),
        "witness": _w_eq("false", "false", "false", "false", "(some true)"),
    },
    {
        "id": "rej-abstain-to-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_ABSTAIN_POS,
        "refinement": (
            "The opposite wrong sentinel on the same branch: an operand that "
            "cannot be interpreted is declared EQUAL. Its faithful real patch "
            "makes the value claim equality with arbitrary foreign operands, so "
            "the gated tests' requirement that an unrelated operand compare "
            "UNEQUAL in both directions fails outright. Does NOT resolve. Note "
            "this is a genuinely different rival from the definite-negative one, "
            "not a restatement: it is refuted at a different reflected opinion, "
            "and it would pass a battery that only ever probed a positive "
            "reflected opinion."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` on an un-interpretable operand "
            "whose reflected opinion is a definite NEGATIVE: the spec defers to "
            "that negative and demands `false`, this rival returns `true`. "
            "Witness holds otherVerdict at `some false`, the setting that "
            "distinguishes it from rej-abstain-to-negative (which is correct "
            "there). [partial-domain on the un-interpretable sub-domain.]"
        ),
        "witness": _w_eq("false", "false", "false", "false", "(some false)"),
    },
    {
        "id": "rej-constant-negative",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_CONST_NEG,
        "refinement": (
            "Collapses the whole decision to a constant negative. Its faithful "
            "real patch makes the equality operator report `false` for every "
            "operand — including the value compared against itself and against "
            "an operand whose content coincides — so the gated tests' "
            "reflexivity and equal-operand assertions fail immediately. Does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at the IDENTITY point: the spec's "
            "first observation is that the operand is literally the same object, "
            "which forces `true`. Witness is the battery's only EQUALITY point "
            "holding sameObj=true, so it is what discriminates this binder on "
            "this obligation — without it a rival mishandling only the identity "
            "observation would verify here (rej-ne-ignores-identity carries the "
            "matching point on the inequality obligation). "
            "[value-double-mask: every branch collapsed to one value.]"
        ),
        "witness": _w_eq("true", "false", "false", "false", "none"),
    },
    {
        "id": "rej-wrong-kind-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_WRONG_KIND_POS,
        "refinement": (
            "Corrupts a DECIDED branch that the abstention rivals leave alone: "
            "an operand that CAN be interpreted but is of an incomparable kind "
            "is reported equal. Its faithful real patch makes the value claim "
            "equality with any interpretable operand of the wrong kind, which "
            "the gated equality test asserts against directly (it requires such "
            "an operand to compare unequal). Does NOT resolve. This rival is "
            "invisible to any witness that holds the interpretable observation "
            "false, which is why it carries its own point."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=true, sameKind=false): the spec's fourth observation "
            "forces a definite `false` there, this rival returns `true`. Witness "
            "moves the `interpretable` binder to TRUE — a setting the abstention "
            "rivals never reach. [per-branch value corruption on the "
            "wrong-kind arm.]"
        ),
        "witness": _w_eq("false", "true", "false", "false", "none"),
    },
    {
        "id": "rej-content-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_CONTENT_IGNORED,
        "refinement": (
            "Drops the content comparison: a same-kind operand is reported equal "
            "whatever its content. Its faithful real patch makes two distinct "
            "values of the same kind compare equal, which the gated equality "
            "test forbids (it walks a family of same-kind values and requires "
            "each pair to agree exactly when the pair is the same one). Does NOT "
            "resolve. It is a NEAR-MISS of the inverted-content rival below — it "
            "agrees with the reference wherever the content DOES coincide — so "
            "it is refuted at the content-differs point, not the shared one."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=true, sameKind=true, contentEq=false): the spec "
            "forces the content verdict, this rival returns `true`. Witness "
            "holds sameKind TRUE with contentEq FALSE and the reflected opinion "
            "ABSENT — the only point of that shape (rej-content-false-abstains "
            "pairs the same content mismatch with a DEFINITE reflected opinion, "
            "where this rival is refuted too but the narrower rival is not). "
            "[value-double-mask: one dimension of the decision dropped.]"
        ),
        "witness": _w_eq("false", "true", "true", "false", "none"),
    },
    {
        "id": "rej-content-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_CONTENT_INVERTED,
        "refinement": (
            "Inverts the content comparison on the same-kind branch. Its "
            "faithful real patch reports coinciding content as unequal and "
            "differing content as equal, so the gated equality test's "
            "same-kind family assertions fail in both directions. Does NOT "
            "resolve. Distinguished from rej-content-ignored by the "
            "content-COINCIDES point, where that rival is correct and this one "
            "is not — which is why it gets its own witness rather than sharing."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=true, sameKind=true, contentEq=true): the spec "
            "demands `true`, this rival returns `false`. Witness holds "
            "contentEq TRUE with an abstaining reflected opinion — the setting "
            "that separates this rival from rej-content-ignored, which is "
            "correct wherever the content DOES coincide. (contentEq is also "
            "held TRUE by the two witnesses for rej-ne-unnegated-decided and "
            "rej-reflected-priority; this is the point that discriminates it on "
            "the equality obligation with the reflected opinion absent.) "
            "[per-branch value corruption on the content arm.]"
        ),
        "witness": _w_eq("false", "true", "true", "true", "none"),
    },
    {
        "id": "rej-wrong-kind-abstains",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_WRONG_KIND_ABSTAINS,
        "refinement": (
            "Over-abstains: an operand that CAN be interpreted but is of an "
            "incomparable kind gets an abstention rather than a definite "
            "negative, so the value hands that operand the decision instead of "
            "making it. Its faithful real patch lets an interpretable "
            "wrong-kind operand that considers itself equal to the value force "
            "the pair to compare EQUAL, which the gated equality test forbids "
            "(it requires such an operand to compare unequal in both "
            "directions). Does NOT resolve. This is the DUAL of "
            "rej-wrong-kind-positive: that rival corrupts the branch's VALUE "
            "while keeping it definite; this one corrupts its DEFINITENESS "
            "while committing to no value, so neither rival's witness refutes "
            "the other."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=true, sameKind=false, otherVerdict=some true): the "
            "spec's fourth observation forces a definite `false` there and "
            "forbids consulting the reflected opinion at all, whereas this "
            "rival abstains and adopts the reflected positive, answering "
            "`true`. It attacks the ONLY-IF half of the abstention clause on "
            "the KIND branch — that an abstention arises exactly when the "
            "operand is un-interpretable, and not on any other branch of the "
            "classify-then-compare family. Witness is the battery's only "
            "EQUALITY point pairing an INTERPRETABLE operand of the WRONG KIND "
            "(interpretable=true, sameKind=false) with a definite reflected "
            "opinion, which is the only setting where a wrongly-abstaining kind "
            "branch is observable at all (rej-ne-reflected-priority uses the "
            "same input point on the INEQUALITY obligation, where this rival's "
            "error is not what is being probed). Measured: 2 divergence points "
            "of 96. [partial-domain on the interpretable-but-wrong-kind "
            "sub-domain.]"
        ),
        "witness": _w_eq("false", "true", "false", "false", "(some true)"),
    },
    {
        "id": "rej-reflected-priority",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_REFLECTED_PRIORITY,
        "refinement": (
            "Inverts the resolution ORDER: the operand's reflected opinion is "
            "consulted first and the value's own opinion only if the operand "
            "abstains. Its faithful real patch lets any operand override the "
            "value's own content comparison, so two same-kind operands with "
            "coinciding content compare UNEQUAL whenever the operand happens "
            "to disagree — the gated equality test's same-kind family "
            "assertions fail. Does NOT resolve. Note this rival consults BOTH "
            "opinions and abstains nowhere, so it survives every rival above: "
            "each of those attacks WHICH value a branch yields or WHETHER it "
            "abstains, none attacks which opinion WINS when both are definite."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=true, sameKind=true, contentEq=true, "
            "otherVerdict=some false): the reference takes the value's own "
            "DEFINITE positive and ignores the reflected opinion entirely, so "
            "the spec demands `true`; this rival gives the operand priority and "
            "returns `false`. Witness is the battery's only EQUALITY point "
            "pairing a definite own POSITIVE with a definite reflected "
            "NEGATIVE — the polarity clash that makes which-opinion-wins "
            "observable (rej-wrong-kind-abstains also pairs a definite own "
            "opinion with a conflicting definite reflected one, but at own "
            "NEGATIVE / reflected POSITIVE, where this rival is correct). "
            "[control-flow: the dispatch-priority half of the resolution rule.]"
        ),
        "witness": _w_eq("false", "true", "true", "true", "(some false)"),
    },
    {
        "id": "rej-identity-fallback-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_IDENTITY_POS,
        "refinement": (
            "Corrupts the last arm of the resolution: when BOTH sides abstain "
            "the operator reports equal instead of falling back to object "
            "identity. Its faithful real patch makes two mutually-unintelligible "
            "operands compare EQUAL, which is precisely the case the gated tests "
            "pin to unequal (an operand that has no opinion about the value at "
            "all must compare unequal in both directions). Does NOT resolve — "
            "and note this rival gets the ABSTENTION itself right, so it is a "
            "strictly finer attack than the abstain-sentinel rivals: it survives "
            "any battery that only checks whether the abstention is produced."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=false, otherVerdict=none): the reference's final "
            "fallback is identity, `false` for distinct objects, whereas this "
            "rival returns `true`. Witness holds otherVerdict at `none` — the "
            "third inhabited shape of that binder — together with an abstaining "
            "own opinion and every classifier observation FALSE, which is what "
            "separates it from the two sibling fallback rivals: those diverge "
            "only where a discarded observation is TRUE, so their witnesses do "
            "not refute this constant-positive arm at this point. [per-branch "
            "corruption on the identity fallback.]"
        ),
        "witness": _w_eq("false", "false", "false", "false", "none"),
    },
    {
        "id": "rej-identity-only-abstains",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_IDONLY_ABSTAINS,
        "refinement": (
            "Over-abstains on the FAMILY branch: a kind that decides equality by "
            "bare object identity is made to ABSTAIN for a non-identical operand "
            "instead of answering the definite negative its test computes. Its "
            "faithful real patch turns those methods into `return NotImplemented` "
            "for every operand that is not the singleton itself, so any foreign "
            "operand that considers itself equal to the value forces the pair to "
            "compare EQUAL — the value's own bare identity test is overridden by "
            "the very operand it was supposed to reject. The gated tests pin such "
            "an operand to unequal in both directions, so it does NOT resolve. "
            "This branch is one the real patch deliberately leaves untouched, "
            "which is exactly why the spec must pin it: a rival free to abstain "
            "here would be claiming the patch changed a method it never touched."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(identityOnly=true, sameObj=false, otherVerdict=some true): the "
            "spec's second observation forces a definite `false` there and "
            "forbids consulting the reflected opinion, whereas this rival "
            "abstains and adopts the reflected positive, answering `true`. "
            "Witness is the battery's only EQUALITY point pairing "
            "identityOnly=true with a definite reflected positive, the only "
            "shape where a wrongly-abstaining family branch is observable. "
            "Measured: 8 divergence points of 96, and NONE of them is a witness "
            "point that predates the family observable — so before this rival "
            "was landed nothing in the battery refuted it. [over-abstention on "
            "the family branch.]"
        ),
        "witness": _w_eq("false", "false", "false", "false", "(some true)",
                         identityOnly="true"),
    },
    {
        "id": "rej-identity-only-positive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_IDONLY_POSITIVE,
        "refinement": (
            "Corrupts the family branch's VALUE: a kind that decides by bare "
            "object identity reports EQUAL for every operand. Its faithful real "
            "patch replaces those bare identity tests with `return True`, so the "
            "value compares equal to arbitrary unrelated operands and the gated "
            "tests' unequal-in-both-directions assertions fail outright. Does "
            "NOT resolve. It is the DUAL of rej-identity-only-abstains — that "
            "rival corrupts the branch's DEFINITENESS while committing to no "
            "value, this one keeps it definite and corrupts the value — so "
            "neither witness refutes the other: measured, this rival is correct "
            "at every point where the reflected opinion is a definite positive, "
            "which is precisely where that rival is refuted."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(identityOnly=true, sameObj=false, otherVerdict=none): the spec "
            "forces `false` for a non-identical operand, this rival returns "
            "`true`. Witness holds the family observation TRUE with the "
            "reflected opinion ABSENT, which no other point in the battery "
            "does. Measured: 24 divergence points of 96, none of them a "
            "pre-refinement witness point. [per-branch value corruption on the "
            "family branch.]"
        ),
        "witness": _w_eq("false", "false", "false", "false", "none",
                         identityOnly="true"),
    },
    {
        "id": "rej-identity-only-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_IDONLY_IGNORED,
        "refinement": (
            "DELETES the family observation from the cascade, running a kind "
            "that decides by bare object identity through the interpret / kind / "
            "content path meant for the other family. Its faithful real patch "
            "rewrites those three bare identity tests into the classify-then-"
            "compare shape, which changes two things the gated tests see: an "
            "operand the value cannot interpret now abstains (so the operand "
            "decides), and an operand that sympifies to a value with coinciding "
            "content is reported EQUAL even though the real method answers "
            "`other is <singleton>` and would say no. Does NOT resolve. This "
            "rival is the reason the family observable exists: it is exactly the "
            "impl shape this bundle carried BEFORE the refinement, so if no "
            "witness refuted it the observable could be deleted from the spec "
            "with nothing noticing, and the spec would be asserting a total "
            "function over observables that do not determine the answer."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(identityOnly=true, interpretable=true, sameKind=true, "
            "contentEq=true): the spec's second observation forces a definite "
            "`false` for a non-identical operand no matter how well its content "
            "matches, whereas this rival falls through to the content arm and "
            "returns `true`. Witness is the battery's only point pairing the "
            "family observation with a fully comparable, content-coinciding "
            "operand — the shape where the DELETED clause changes the answer "
            "while rej-identity-only-abstains happens to be correct (measured: "
            "that rival agrees with the reference at this point, so its witness "
            "does not stand in for this one). Measured: 7 divergence points of "
            "96, none of them a pre-refinement witness point. "
            "[family-conflation: the observable removed altogether.]"
        ),
        "witness": _w_eq("false", "true", "true", "true", "none",
                         identityOnly="true"),
    },
    {
        "id": "rej-ne-negates-own-opinion",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_NEG_OWN,
        "refinement": (
            "This is the second of the two behaviors this bundle exists to fix, "
            "reproduced inside the impl region: inequality negates the value's "
            "OWN opinion, coercing an abstention as though it were a definite "
            "positive, so an abstention yields a definite `false` and the "
            "reflected consultation is skipped. Its faithful real patch is the "
            "UNFIXED code, and on an operand the value cannot interpret and that "
            "does not consider itself equal it reports the two as NOT unequal "
            "where the fixed behavior reports unequal — the exact assertion the "
            "gated tests make about an unrelated operand. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at "
            "(interpretable=false, otherVerdict=some false): the resolved "
            "equality operator defers to that definite negative, so inequality "
            "must be `true`, whereas this rival coerces the abstention to a "
            "positive and answers `false`. [control-flow-effect: a non-boolean "
            "abstention treated as a boolean — the coercion the value "
            "abstraction exists to catch.]"
        ),
        "witness": _w_ne("false", "false", "false", "false", "(some false)"),
    },
    {
        "id": "rej-ne-drops-reflected",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_DROPS_REFLECTED,
        "refinement": (
            "Drops the reflected consultation the other way round: a definite "
            "own opinion is negated correctly, but an abstention "
            "short-circuits to a definite 'unequal' without consulting the "
            "operand. Its faithful real patch makes the value assert inequality "
            "against an operand that considers itself equal to the value, so the "
            "gated tests' both-directions agreement for such an operand fails. "
            "Does NOT resolve. It is NOT the same rival as the own-opinion "
            "negation above — the two answer differently whenever the reflected "
            "opinion is a definite negative — so it carries its own witness at "
            "the reflected-POSITIVE point, where that rival happens to be right."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at "
            "(interpretable=false, otherVerdict=some true): the resolved "
            "equality operator adopts the reflected positive, so inequality must "
            "be `false`, whereas this rival returns `true`. This is the "
            "consequence nagini's admissibility case merely ASSERTED; here it is "
            "attacked. [value-double-mask: the reflected dimension dropped.]"
        ),
        "witness": _w_ne("false", "false", "false", "false", "(some true)"),
    },
    {
        "id": "rej-ne-unnegated-decided",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_UNNEGATED,
        "refinement": (
            "Attacks the DECIDED half of the inequality behavior, which the two "
            "abstention-flavored inequality rivals leave untouched: the negation "
            "is dropped when the value's own opinion is definite, so a decided "
            "operand's inequality answer is the equality answer verbatim. Its "
            "faithful real patch makes the value report equal operands as "
            "unequal and unequal ones as equal whenever it can interpret them at "
            "all, so the gated tests' same-kind family assertions — which check "
            "equality and inequality agree as complements over a whole family of "
            "values — fail. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at "
            "(interpretable=true, sameKind=true, contentEq=true): the resolved "
            "equality operator is `true` there, so inequality must be `false`, "
            "whereas this rival returns `true`. Witness moves interpretable, "
            "sameKind and contentEq to TRUE for the inequality obligation — the "
            "decided sub-domain that no other inequality rival reaches, and the "
            "gap that the abstention-only rivals would leave open. Measured: the "
            "battery's widest rival at 84 divergence points of 96. "
            "[per-branch corruption on the decided arm of the inequality.]"
        ),
        "witness": _w_ne("false", "true", "true", "true", "none"),
    },
    {
        "id": "rej-ne-ignores-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_NO_IDENTITY,
        "refinement": (
            "Drops the identity observation from the inequality's own "
            "classification, so the value compared against ITSELF is no longer "
            "short-circuited to a definite positive and instead falls through to "
            "the family / interpret / kind / content path. Its faithful real "
            "patch makes a value report itself as unequal to itself whenever it "
            "cannot interpret itself by the ordinary route, breaking the "
            "reflexivity the gated equality test asserts over its family of "
            "values. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at the IDENTITY point "
            "(sameObj=true, everything else false/absent): the spec's first "
            "observation forces the resolved equality to `true` and hence "
            "inequality to `false`, whereas this rival abstains, falls back to "
            "identity-for-distinct-objects and answers `true`. Witness is the "
            "only inequality point holding sameObj TRUE, so it is what "
            "discriminates that binder on this obligation. [partial-domain on "
            "the identity sub-domain.]"
        ),
        "witness": _w_ne("true", "false", "false", "false", "none"),
    },
    {
        "id": "rej-ne-reflected-priority",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_REFLECTED_PRIORITY,
        "refinement": (
            "Inverts the resolution ORDER inside the INEQUALITY's own "
            "resolution: it stops delegating to the equality impl, resolves for "
            "itself, and consults the operand's reflected opinion first. Its "
            "faithful real patch lets any operand with an opinion override the "
            "value's own classification on the `!=` operator specifically, so a "
            "wrong-kind operand that considers itself equal makes the pair "
            "compare NOT-unequal while `==` still reports unequal — the two "
            "operators then contradict each other, which the gated tests forbid "
            "(they assert `==` and `!=` are complements). Does NOT resolve. "
            "Added by audit: rej-reflected-priority attacks the ordering on the "
            "EQUALITY obligation only, and every inequality rival in the "
            "battery preserves left-first resolution, so this inversion was "
            "reachable by no existing witness on the obligation where the "
            "negation makes it present differently."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at "
            "(interpretable=true, sameKind=false, otherVerdict=some true): the "
            "reference takes the value's own DEFINITE negative, so the resolved "
            "equality is `false` and inequality must be `true`; this rival "
            "adopts the reflected positive first and answers `false`. Witness is "
            "the battery's only INEQUALITY point pairing a definite own opinion "
            "of the classify-then-compare family with a conflicting definite "
            "reflected one, which is where the dispatch order is observable on "
            "this obligation. [control-flow: dispatch priority, inequality "
            "side.]"
        ),
        "witness": _w_ne("false", "true", "false", "false", "(some true)"),
    },
    {
        "id": "rej-content-false-abstains",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_CONTENT_FALSE_ABSTAINS,
        "refinement": (
            "Over-abstains on the DEEPEST branch of the cascade: a same-kind "
            "operand whose content does NOT coincide gets an abstention instead "
            "of the definite negative the spec pins, so the value hands the "
            "operand a decision it had already made correctly. Its faithful real "
            "patch lets an operand of the value's OWN kind that disagrees about "
            "content force the pair to compare equal, which the gated equality "
            "test forbids directly (it walks a family of same-kind values and "
            "requires distinct members to compare unequal in both directions). "
            "Does NOT resolve. Added by audit: rej-wrong-kind-abstains attacks "
            "the only-if half of the abstention clause on the KIND branch, and "
            "nothing attacked it on the CONTENT branch, where the operand is "
            "fully comparable and the value has no excuse to abstain."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=true, sameKind=true, contentEq=false, "
            "otherVerdict=some true): the spec's fifth observation forces a "
            "definite `false` there and forbids consulting the reflected "
            "opinion, whereas this rival abstains and adopts the reflected "
            "positive, answering `true`. This is the battery's NARROWEST rival "
            "— measured, it agrees with the reference at 95 of the 96 input "
            "points, so it is refuted only by a witness pairing a content "
            "MISMATCH with a DEFINITE reflected opinion, and this witness is "
            "the battery's only point of that shape: the other rival reaching "
            "the content arm with contentEq=false (rej-content-ignored) holds "
            "otherVerdict at `none`, where this rival's abstention falls through "
            "to the identity fallback and coincidentally answers correctly. "
            "[partial-domain: the same-kind-content-differs sub-domain.]"
        ),
        "witness": _w_eq("false", "true", "true", "false", "(some true)"),
    },
    {
        "id": "rej-identity-fallback-reads-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_IDENTITY_READS_CONTENT,
        "refinement": (
            "Corrupts the both-abstain arm by making it DEPEND on an "
            "observation the spec has already discarded there: when neither "
            "side has an opinion the operator must fall back to object "
            "identity, but this rival answers with the content comparison. Its "
            "faithful real patch makes two mutually-unintelligible operands "
            "compare EQUAL whenever the value's own content check happened to "
            "coincide — an operand that cannot be interpreted at all is "
            "reported equal on the strength of a comparison that was never "
            "performed against it — which the gated tests forbid (an operand "
            "with no opinion about the value must compare unequal in both "
            "directions). Does NOT resolve. Added by audit: it is the DUAL of "
            "rej-identity-fallback-positive, which collapses this arm to a "
            "CONSTANT positive and so diverges wherever the arm is reached at "
            "all; this rival is correct wherever the content does not coincide, "
            "so that rival's witness does not refute it, and no pre-existing "
            "witness paired contentEq TRUE with an abstaining own opinion."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=false, contentEq=true, otherVerdict=none): the "
            "reference's final fallback is identity, `false` for distinct "
            "objects, and it consults NO classifier observation there, whereas "
            "this rival returns the content verdict `true`. Witness is the "
            "battery's only point pairing contentEq TRUE with an abstaining own "
            "opinion AND an absent reflected opinion — the only shape where a "
            "fallback that reads the content observation is observable at all "
            "(the other contentEq-TRUE equality points hold interpretable TRUE, "
            "where this rival's own opinion is definite and the arm is never "
            "reached). Measured: 2 divergence points of 96. [per-branch "
            "corruption on the identity fallback: the arm reads a discarded "
            "observation rather than taking a wrong constant.]"
        ),
        "witness": _w_eq("false", "false", "false", "true", "none"),
    },
    {
        "id": "rej-ne-fallback-polarity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_FALLBACK_POLARITY,
        "refinement": (
            "Inverts the polarity of the both-abstain identity fallback inside "
            "the INEQUALITY's own resolution: it stops delegating to the "
            "equality impl, resolves for itself, and treats two abstentions as "
            "'equal' rather than falling back to identity. Its faithful real "
            "patch makes the `!=` operator report two mutually-unintelligible "
            "operands as NOT unequal while `==` still reports them unequal, so "
            "the two operators contradict each other — which the gated tests "
            "forbid (they assert `==` and `!=` are complements, and they pin an "
            "operand with no opinion about the value to unequal in both "
            "directions). Does NOT resolve. Added by audit: the identity "
            "fallback arm was attacked only on the EQUALITY obligation, and "
            "every inequality rival in the battery either reaches that arm "
            "correctly (rej-ne-reflected-priority, rej-ne-ignores-identity) or "
            "corrupts a DIFFERENT arm, so this inversion was refuted by no "
            "witness in the battery."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at "
            "(interpretable=false, otherVerdict=none): the resolved equality "
            "operator falls back to identity and is `false` for distinct "
            "objects, so inequality must be `true`; this rival resolves the "
            "both-abstain case to `true` and answers `false`. Witness is the "
            "battery's only INEQUALITY point at the both-abstain fallback — the "
            "only sub-domain where this rival diverges, since it is correct "
            "wherever either side has a definite opinion. It is not the "
            "equality-side rival restated: that one is refuted only on the "
            "richEq obligation, where this rival is a byte-identical delegate "
            "of the frozen equality impl and therefore correct. "
            "[per-branch corruption on the identity fallback, inequality side.]"
        ),
        "witness": _w_ne("false", "false", "false", "false", "none"),
    },
    {
        "id": "rej-identity-fallback-reads-kind",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_IDENTITY_READS_KIND,
        "refinement": (
            "Corrupts the both-abstain arm by making it read a DIFFERENT "
            "discarded observation than its sibling does: when neither side has "
            "an opinion the operator is pinned to object identity, but this "
            "rival answers with the KIND observation. Its faithful real patch "
            "reports two mutually-unintelligible operands as EQUAL whenever the "
            "value's kind check happened to succeed — an operand the value "
            "cannot interpret at all is declared equal on the strength of a "
            "kind agreement that was never established against it — which the "
            "gated tests forbid (an operand with no opinion about the value "
            "must compare unequal in both directions). Does NOT resolve. Added "
            "by a second audit: rej-identity-fallback-positive collapses this "
            "arm to a constant and rej-identity-fallback-reads-content makes it "
            "read the CONTENT observation, and neither refutes a rival reading "
            "the KIND one, because every pre-existing sameKind=TRUE witness also "
            "held interpretable=TRUE, where this arm is never reached."
        ),
        "rationale": (
            "Rejected by `result = richEqRef …` at "
            "(interpretable=false, sameKind=true, otherVerdict=none): the "
            "reference's final fallback is identity, `false` for distinct "
            "objects, and it consults NO classifier observation there, whereas "
            "this rival returns the kind verdict `true`. Witness is the only "
            "point in the battery pairing sameKind TRUE with an "
            "UN-INTERPRETABLE operand and an absent reflected opinion — the "
            "only shape where a fallback reading the kind observation is "
            "observable at all. Machine-checked: this rival diverges from the "
            "reference at 2 of the 96 input points and both are disjoint from "
            "every other witness point in the battery. [per-branch corruption "
            "on the identity fallback: the arm reads the kind observation the "
            "spec has already discarded.]"
        ),
        "witness": _w_eq("false", "false", "true", "false", "none"),
    },
    {
        "id": "rej-ne-fallback-reads-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_FALLBACK_READS_CONTENT,
        "refinement": (
            "The content-reading fallback on the INEQUALITY obligation: the "
            "inequality stops delegating, resolves the equality itself, and "
            "makes the both-abstain arm answer with the CONTENT observation "
            "instead of falling back to identity. Its faithful real patch makes "
            "the `!=` operator report two mutually-unintelligible operands as "
            "NOT unequal whenever the value's own content check coincided, "
            "while `==` still reports them unequal — the two operators then "
            "contradict each other, which the gated tests forbid (they assert "
            "`==` and `!=` are complements and pin an operand with no opinion "
            "about the value to unequal in both directions). Does NOT resolve. "
            "Added by a second audit: the content-reading fallback was attacked "
            "only on the EQUALITY obligation, and rej-ne-fallback-polarity "
            "inverts this arm to a CONSTANT so it diverges wherever the arm is "
            "reached at all, while this rival is correct wherever the content "
            "does not coincide — so neither rival's witness refutes the other."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at "
            "(interpretable=false, contentEq=true, otherVerdict=none): the "
            "resolved equality operator falls back to identity and is `false` "
            "for distinct objects, so inequality must be `true`; this rival "
            "reads the content observation, resolves to `true` and answers "
            "`false`. Witness is the battery's only INEQUALITY point pairing "
            "contentEq TRUE with an abstaining own opinion AND an absent "
            "reflected opinion. Machine-checked: 2 divergence points of 96, "
            "both disjoint from every other witness point. [per-branch "
            "corruption on the identity fallback, inequality side: the arm "
            "reads a discarded observation rather than taking a wrong "
            "constant.]"
        ),
        "witness": _w_ne("false", "false", "false", "true", "none"),
    },
    {
        "id": "rej-ne-identity-only-abstains",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _REJ_NE_IDONLY_ABSTAINS,
        "refinement": (
            "The family branch corrupted on the INEQUALITY obligation: the "
            "inequality stops delegating, resolves the equality itself, and "
            "makes a kind that decides by bare object identity ABSTAIN instead "
            "of answering its definite negative. Its faithful real patch makes "
            "`!=` report the pair as NOT unequal whenever a foreign operand "
            "claims equality, while `==` still reports unequal, so the two "
            "operators contradict each other on operands whose comparison the "
            "real patch never touched. Does NOT resolve. Added with the family "
            "observable: the family clause was otherwise attacked on the "
            "EQUALITY obligation only, and every inequality rival in the "
            "battery keeps the family arm definite, so measured this rival is "
            "refuted by NO inequality witness that predates it."
        ),
        "rationale": (
            "Rejected by `result = richNeRef …` at "
            "(identityOnly=true, sameObj=false, otherVerdict=some true): the "
            "reference takes the family's definite negative, so the resolved "
            "equality is `false` and inequality must be `true`; this rival "
            "abstains, adopts the reflected positive and answers `false`. "
            "Witness is the battery's only INEQUALITY point holding "
            "identityOnly TRUE. Measured: 8 divergence points of 96, none of "
            "them a pre-refinement witness point. [over-abstention on the "
            "family branch, inequality side.]"
        ),
        "witness": _w_ne("false", "false", "false", "false", "(some true)",
                         identityOnly="true"),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom.
# Both modeled behaviors are stated deeply over total functions of the six
# observable inputs; the operand's reflected opinion is a free input supplied by
# the caller (arbitrary external code), not a library routine with a contract, so
# there is nothing for an axiom probe to check.
AXIOM_TESTS = []
