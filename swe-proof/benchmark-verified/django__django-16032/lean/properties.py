"""properties.py — PBT falsification manifest for django__django-16032 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Every case edits ONLY the implementation region
(and, for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and each rejection is
attributable to the postcondition rather than to a tampered spec.

DEFENDED SURFACE
----------------
This bundle models ONE obligation:

    implementation_prepInLookup
        (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String)
      : SubqueryState

pinned by `problem_spec_prepInLookup`, a two-armed conditional whose GUARD is
itself a load-bearing part of the spec:

    if (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) then
      result.selectCols = [targetField]
        ∧ result.hasAnnotationSelection = false
        ∧ result.hasExtraSelection = false
        ∧ result.explicitValuesApplied = true
    else
      result = rhs

The carrier is FULLY TRANSPARENT: `SubqueryState` is a four-field structure
deriving `DecidableEq`, and no callee is opaque. So every rival is refutable by
`decide` at a concrete input and no witness needs to condition on the carrier
(hence no witness below binds a hypothesis, and there is nothing that could be
inconsistent).

There are FIVE independent things a rival can get wrong, and each is attacked:

  * THE GUARD'S FIRST HALF — narrowing is decided by `explicitValuesApplied`
    ALONE, never by whether the subquery merely happens to carry a current
    selection or a selection mask. This is the behaviour at the heart of the
    report: a subquery that carries derived selections but was never given an
    explicit column selection MUST still be narrowed. Attacked by
    `w1-guard-derives-from-masks`, `w2-guard-reads-current-selection`,
    `w3-guard-adds-extra-mask-conjunct`.
  * THE GUARD'S SECOND HALF — narrowing is suppressed when the comparison's
    target column is the primary key. Attacked by `w5-overfires-on-pk-target`.
  * THE NARROWED SELECTION'S IDENTITY — exactly the single `targetField`.
    Attacked by `w9-narrows-to-fixed-column`.
  * THE CLEARING CONJUNCTS — both derived-selection components are cleared by
    the narrowing, and the result is MARKED as explicitly selected. Attacked by
    `w6-keeps-annotation-selection`, `w7-keeps-extra-selection`,
    `w4-narrows-without-marking`.
  * THE LEAVE-UNCHANGED ARM — `result = rhs`, a whole-structure equality, so it
    is the frame obligation as well: any component the rival touches on that arm
    breaks it. Attacked by `w8-touches-untouched-arm` (a boolean component) and
    `w10-drops-selection-on-untouched-arm` (the list-valued component). Two
    rivals, not one, because a rival only witnesses the component it touches and
    every other else-arm witness holds `selectCols` at `[]`, where clearing it is
    a no-op.

BINDER COVERAGE. Each of the six spec binders is moved by some reject witness
while the others are held: `selectCols` ([] / ["title"] / ["title", "isbn"]),
`hasAnnotationSelection` (both values), `hasExtraSelection` (both values),
`explicitValuesApplied` (both values — `w2`, `w8` and `w10` probe the `true`
side), `lhsTargetPrimaryKey` (both values — `w5` probes `true`), and
`targetField` (five distinct names). A binder every witness held at one value
would be a binder no rival was built to abuse. The variation is also required to
be MEANINGFUL rather than two spellings of one point: `w10` exists because the
`selectCols` values that the else-arm witnesses used were all `[]`, at which the
frame at that component is not observable.

WHY NO RIVAL CAN VERIFY, ONCE AND FOR ALL. Beyond the case-by-case rivals, the
spec is FUNCTIONAL on this carrier: it pins the result uniquely in both arms, so
any two results satisfying it at the same input are equal, and hence every
verifying impl agrees with the frozen one at every input. That was machine-checked
during audit (a `∀ rhs pk tf r1 r2, spec … r1 → spec … r2 → r1 = r2` theorem
elaborating against the frozen file, exit 0), which is the structural reason the
SPEC-TOO-WEAK lane cannot be open here: a rival verifies only if it is
extensionally gold. The rivals below therefore probe the battery's own
discrimination, not the residual risk of a spec hole.

An independent audit pass re-derived that theorem (exit 0) and then probed it
empirically anyway, with eight NEW wrong impls the battery does not contain, each
aimed where the shipped rivals do not reach: a disjunctive guard, appending the
target column instead of replacing the selection, never narrowing at all, always
narrowing, narrowing to the EMPTY selection, marking the leave-unchanged arm,
a four-conjunct guard strictly stronger than w3's, and narrowing to the target
column duplicated. All eight were rejected by the frozen obligation and all eight
were refuted by their own witness at a concrete input (rival exit 0, gold exit 1).
The same pass wrote four NEW correct reshapes — guard operands commuted, a `match`
on the two booleans instead of an `if`, a `let`-bound record returned, and the
guard as `!(a || b)` — and all four VERIFY, so the spec is not too strong about
the decision's spelling either.

PORTING NOTES (which nagini cases ported, which are omitted and why)
--------------------------------------------------------------------
The nagini sibling contracts THREE functions over a mutable query twin
(`project_columns`, `attach_auxiliary_expressions`, `prepare_in_rhs`); this
bundle models only the purely functional decision that corresponds to nagini's
`prepare_in_rhs`. The other two are not separate obligations here — the
restriction is a pure helper inside the spec view, and the auxiliary-expression
attachment is not modeled at all. So carrier narrowing, not thinning, accounts
for the difference in shape; the case count is HIGHER than nagini's because the
one surviving obligation has more independently-attackable structure.

  * `weak-aux-recouples-flag` (nagini's primary rival) ->
    `w1-guard-derives-from-masks`. Nagini attacked it through the second
    function's "flag unchanged" clause; here the same wrong rule appears where
    it is actually consumed, in this obligation's guard. Same argument, moved to
    the carrier that models it.
  * `weak-rhs-narrow-without-flag` -> `w4-narrows-without-marking`.
  * `weak-rhs-overfires-on-pk-target` -> `w5-overfires-on-pk-target`.
  * `faith-aux-preserved-in-project` -> SPLIT into
    `w6-keeps-annotation-selection` and `w7-keeps-extra-selection`. Nagini's
    twin collapsed both derived-selection components into one boolean; this
    carrier keeps them apart, so the single nagini rival becomes two, each with
    its own witness at its own component.
  * `weak-rhs-wrong-column` -> `w9-narrows-to-fixed-column`.
  * `frame-cols-in-aux` -> OMITTED as written (it attacks the unmodeled
    auxiliary-expression attachment), but the value-frame CLASS it defends is
    not lost: it reappears against this obligation's `result = rhs` arm, which is
    a whole-structure equality and so frames all four components at once. Nagini's
    case attacked the SELECT-columns component specifically, and that is
    `w10-drops-selection-on-untouched-arm`; `w8-touches-untouched-arm` attacks the
    same arm at a boolean component. Both are needed — the clause frames four
    components but a rival only witnesses the one it touches.
  * `pos-project-reorder-no-reset` and `pos-rhs-inline-projection` ->
    `pos-inline-restriction` (inlines the restriction's record literal instead
    of calling the pure helper — nagini's "same effect, different call
    structure" argument) and `pos-degenerate-guard-swap` (the guard in its
    de Morgan dual with the two branches exchanged — nagini's
    "order-independent, no incidental statement order is pinned" argument).
    Both proofs were re-closed for the new impl shape; neither weakens the
    obligation. Re-measured during audit: restoring the FROZEN proof script over
    either positive's impl fails to elaborate (`pos-degenerate-guard-swap`:
    `Application type mismatch` on the `rfl`s plus an unsolved else-arm goal;
    `pos-inline-restriction`: `unfold` cannot unfold `restrictTo`, there being no
    such call left), so each reshape genuinely defeats the frozen tactics and its
    proof had to be re-derived rather than restated.
  * `admiss-rhs-narrow-reachable` -> PORTED as `admiss-narrowing-reachable`.
    The port originally dropped it, reasoning that the lean obligation is
    `∀ rhs lhsTargetPrimaryKey targetField, problem_spec …` with NO precondition
    hypothesis, so there is no precondition to be too strong. That reason is
    WRONG, and an audit pass replaced it: on a total carrier the analogue of
    PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input, which a positive that discharges the obligation at that
    concrete input — by evaluation, before closing the frozen obligation
    verbatim — tests directly. "Some reject witness fires that arm" is not a
    substitute: a witness proves the spec is VIOLATED there by a rival, which
    says nothing about the frozen behaviour being admissible there. See the case
    for the two `have`s and the measurement that the second is load-bearing.
  * Nagini's fractional-permission frame-mutation class is VACUOUS here: Lean is
    referentially transparent, so there is no aliasing or permission level to
    abuse. The frame discipline that does exist is a VALUE frame and is attacked
    by `w8` (see above); no substitute for the permission class was fabricated.
  * The divergence / non-termination class is genuinely VACUOUS on this backend
    (not a known spec hole as it is on velvet under partial termination
    semantics — cf. the corpus-wide termination-semantics finding): `implementation_prepInLookup`
    is a total Lean `def`, so a diverging implementation cannot be written at
    all. The nagini sibling carries no `diverge-*` / `nonterm-*` case either.
  * `AXIOM_TESTS` dropped: this bundle consumes no axiom (`axioms = []`), and
    the axiom lane is G-AX's job — this gate ignores it.

WITNESSES. Every reject case carries a `witness`: a Lean `example` negating the
spec predicate at one concrete input, checked in a file with the frozen
obligation removed so no tactic script can interfere. Each was built BOTH ways
with scripts/lean_verify.sh — exit 0 against the rival, exit 1 against the
frozen solution, where the gold-side failure is in every case `decide` reporting
that it proved the spec DOES hold there (a real discriminator, not an unknown
name or a parse error).

Re-derived independently during a later audit, all twenty builds: every witness
elaborates against its rival (exit 0) and fails on the frozen solution (exit 1).
The gold-side exit code was additionally shown to CARRY INFORMATION ABOUT THE
CLAIM rather than to be a standing property of the carrier, by the forgery test —
for each of the ten, a second file differing from the witness ONLY in dropping the
`¬` (so it asserts the frozen behaviour IS correct at that input, the opposite of
a refutation) was built on both sides. The exit codes invert cleanly, ten for ten:
forged-on-gold exits 0 and forged-on-rival exits 1, the mirror image of the real
witness. So no witness here rests on a stuck reduction, a missing instance or a
tactic mismatch; each gold-side `decide` genuinely evaluated the claim and found
it false, and a forged witness would have been caught rather than recorded.

A witness must be specific to the rival it accompanies, which is a stronger
requirement than the gate's two builds enforce: a rival's witness that also holds
of a DIFFERENT rival in the battery discriminates against gold but not against the
wrong rule it names. `w2`'s witness was re-placed for exactly this reason (it
elaborated against `w1`), so where two rivals are near-misses the witness sits at
an input on which one is correct and the other is not.

One mechanical note for future edits, since it cost a build round here and is
not about the spec: a multiline `return { rhs with f := v, … }` inside an
`Id.run do` block does not parse (`unexpected identifier; expected '}'`). The
rivals that reshape the record update therefore wrap it in parentheses, which
parses and changes nothing semantically.
"""
from pathlib import Path

INSTANCE = "django__django-16032"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring, asserting the
    anchor exists and is unique so silent drift (Solution.lean edited) fails
    loudly instead of producing a variant that tests nothing."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors — each lies strictly INSIDE the impl region and is unique
# across the whole file (enforced by _swap's count guard).
# ---------------------------------------------------------------------------

# The impl-region guard line. Unique: the spec's own conditional is spelled
# `if (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) then` (parenthesized).
_GUARD = "  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then"

# The narrowing return.
_NARROW = "    return restrictTo rhs [targetField]"

# The narrowing return together with the leave-unchanged return, so a rival can
# edit the SECOND arm without disturbing the first.
_BOTH_ARMS = "    return restrictTo rhs [targetField]\n  return rhs"

# The whole impl body, for the positive controls that reshape it wholesale.
_GOLD_IMPL = (
    "def implementation_prepInLookup\n"
    "    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)\n"
    "    (targetField : String) : SubqueryState := Id.run do\n"
    "  if !rhs.explicitValuesApplied && !lhsTargetPrimaryKey then\n"
    "    return restrictTo rhs [targetField]\n"
    "  return rhs"
)

_PROOF_HEAD = "-- proof-start"
_PROOF_TAIL = "-- proof-end"


def _swap_proof(src: str, new_proof_body: str) -> str:
    """Replace everything strictly between the proof markers. The
    `theorem correct_prepInLookup` STATEMENT is re-emitted byte-identically
    inside `new_proof_body` (see `_THM_STMT`); only the tactic body changes,
    which is exactly what variant_scope permits."""
    s = src.index(_PROOF_HEAD)
    e = src.index(_PROOF_TAIL)
    return src[: s + len(_PROOF_HEAD)] + "\n" + new_proof_body + "\n" + src[e:]


# The obligation statement, re-emitted verbatim by every positive so the
# proof obligation survives byte-identically.
_THM_STMT = (
    "theorem correct_prepInLookup :\n"
    "    ∀ (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool) (targetField : String),\n"
    "      problem_spec_prepInLookup rhs lhsTargetPrimaryKey targetField\n"
    "        (implementation_prepInLookup rhs lhsTargetPrimaryKey targetField) := by"
)
if _THM_STMT not in _BASE:
    raise AssertionError("drift: theorem statement no longer matches the frozen file")


# ===========================================================================
# ADMISSIBILITY — expect "verify"
# ===========================================================================

# The obligation carries no precondition binder (it is a bare `∀` over a total
# carrier), so there is no Requires clause to probe the way nagini's twin does.
# The analogue on this carrier is the obligation being UNSATISFIABLE at exactly
# an F2P-shaped input, and that is what this case tests: it discharges the spec
# predicate at one concrete such input BY EVALUATION, as a `have` prepended to
# the frozen tactic body, and then closes the frozen obligation verbatim.
#
# The input is the F2P shape: a subquery that acquired BOTH derived-selection
# components without ever being given an explicit column selection, compared
# against a non-primary-key target. That is the point where the narrowing arm
# must fire and the whole battery's reject lane is aimed.
#
# TWO `have`s, because the first alone would be weak. `_ground` says the spec
# holds of the modeled behaviour at that input — but the spec pins `result` to a
# term over the same inputs, so it would read identically if the input landed in
# the leave-unchanged arm and nothing was narrowed at all. `_narrowed` EVALUATES
# the behaviour at that input down to the concrete four-component state, which
# pins the admission to the narrowing arm specifically: exactly the single target
# column selected, both derived components cleared, the result marked. Measured
# load-bearing rather than asserted — placing the same two `have`s over a WRONG
# impl (one that narrows to a constant column) FAILS to elaborate, `decide`
# reporting it proved the negation of both claims.
_ADM_HAVES = (
    "  have _ground : problem_spec_prepInLookup\n"
    "      { selectCols := [], hasAnnotationSelection := true,\n"
    "        hasExtraSelection := true, explicitValuesApplied := false }\n"
    "      false \"author_id\"\n"
    "      (implementation_prepInLookup\n"
    "        { selectCols := [], hasAnnotationSelection := true,\n"
    "          hasExtraSelection := true, explicitValuesApplied := false }\n"
    "        false \"author_id\") := by\n"
    "    unfold problem_spec_prepInLookup implementation_prepInLookup\n"
    "    decide\n"
    "  have _narrowed : implementation_prepInLookup\n"
    "      { selectCols := [], hasAnnotationSelection := true,\n"
    "        hasExtraSelection := true, explicitValuesApplied := false }\n"
    "      false \"author_id\"\n"
    "      = { selectCols := [\"author_id\"], hasAnnotationSelection := false,\n"
    "          hasExtraSelection := false, explicitValuesApplied := true } := by\n"
    "    unfold implementation_prepInLookup\n"
    "    decide\n"
)

# Prepended INSIDE the existing tactic body (right after the frozen statement's
# `:= by`), so the impl region, the theorem statement and the frozen tactic
# script all survive byte-identically and nothing is assumed: no new
# declaration, no axiom, no assumption token.
_ADM = _swap(
    _BASE,
    "        (implementation_prepInLookup rhs lhsTargetPrimaryKey targetField) := by\n",
    "        (implementation_prepInLookup rhs lhsTargetPrimaryKey targetField) := by\n"
    + _ADM_HAVES,
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-degenerate-guard-swap) A structurally different CORRECT impl: no
# imperative do-block at all, the guard written in its de Morgan dual, and the
# two arms EXCHANGED so the leave-unchanged case is tested first. Same function,
# different shape and different branch order. Proof re-closed by splitting on
# the two boolean components rather than on the conjunction.
_POS_SWAP = _swap_proof(
    _swap(
        _BASE, _GOLD_IMPL,
        "def implementation_prepInLookup\n"
        "    (rhs : SubqueryState) (lhsTargetPrimaryKey : Bool)\n"
        "    (targetField : String) : SubqueryState :=\n"
        "  if rhs.explicitValuesApplied || lhsTargetPrimaryKey then rhs\n"
        "  else restrictTo rhs [targetField]",
    ),
    _THM_STMT + "\n"
    "  intro rhs lhsTargetPrimaryKey targetField\n"
    "  unfold problem_spec_prepInLookup implementation_prepInLookup restrictTo\n"
    "  by_cases h : rhs.explicitValuesApplied = true\n"
    "  · simp [h]\n"
    "  · by_cases h2 : lhsTargetPrimaryKey = true\n"
    "    · simp [h, h2]\n"
    "    · simp [h, h2]\n",
)

# (pos-inline-restriction) A second correct impl that keeps the imperative shape
# but INLINES the restriction's record literal instead of calling the pure
# helper — the same observable result reached without the helper call, which is
# nagini's "the spec must pin the behaviour, not a particular call structure"
# positive. The proof no longer unfolds the helper (there is none to unfold);
# the four conjuncts close by `rfl` off the literal.
_POS_INLINE = _swap_proof(
    _swap(
        _BASE, _NARROW,
        "    return ({ selectCols := [targetField],\n"
        "              hasAnnotationSelection := false,\n"
        "              hasExtraSelection := false,\n"
        "              explicitValuesApplied := true })",
    ),
    _THM_STMT + "\n"
    "  intro rhs lhsTargetPrimaryKey targetField\n"
    "  unfold problem_spec_prepInLookup implementation_prepInLookup\n"
    "  by_cases h : (!rhs.explicitValuesApplied && !lhsTargetPrimaryKey) = true\n"
    "  · simp only [Id.run, h, if_true]\n"
    "    exact ⟨rfl, rfl, rfl, rfl⟩\n"
    "  · simp only [Bool.not_eq_true] at h\n"
    "    simp only [Id.run, h, Bool.false_eq_true, if_false, bind, pure]\n",
)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (w1) Decide narrowing from whether the subquery merely CARRIES any current
# selection or derived-selection component, instead of from whether an explicit
# column selection was applied. Agrees with gold on every subquery that carries
# nothing derived; wrong exactly on the reported sub-domain.
_RIVAL_W1 = _swap(
    _BASE, _GUARD,
    "  let looksSelected := !rhs.selectCols.isEmpty\n"
    "    || rhs.hasAnnotationSelection || rhs.hasExtraSelection\n"
    "  if !looksSelected && !lhsTargetPrimaryKey then",
)

# (w2) Consult only whether the current selection is non-empty. A NEAR-MISS of
# w1: it too fails in both directions, but at DIFFERENT points, so its witness is
# placed where w1 is correct and it is not (see _WIT_W2).
_RIVAL_W2 = _swap(
    _BASE, _GUARD,
    "  if rhs.selectCols.isEmpty && !lhsTargetPrimaryKey then",
)

# (w3) Keep the correct first half of the guard but ADD a conjunct requiring the
# extra-selection component to be absent. Agrees with gold everywhere except a
# subquery carrying that one component, which it then wrongly leaves alone.
_RIVAL_W3 = _swap(
    _BASE, _GUARD,
    "  if !rhs.explicitValuesApplied && !rhs.hasExtraSelection && !lhsTargetPrimaryKey then",
)

# (w4) Narrow and clear both derived-selection components, but never MARK the
# result as explicitly selected.
_RIVAL_W4 = _swap(
    _BASE, _NARROW,
    "    return ({ rhs with selectCols := [targetField],\n"
    "                       hasAnnotationSelection := false,\n"
    "                       hasExtraSelection := false })",
)

# (w5) Drop the primary-key half of the guard: narrow even when the comparison's
# target column is the primary key, which the spec requires be left alone.
_RIVAL_W5 = _swap(_BASE, _GUARD, "  if !rhs.explicitValuesApplied then")

# (w6) Narrow correctly but PRESERVE the annotation-selection component.
_RIVAL_W6 = _swap(
    _BASE, _NARROW,
    "    return ({ rhs with selectCols := [targetField],\n"
    "                       hasExtraSelection := false,\n"
    "                       explicitValuesApplied := true })",
)

# (w7) Narrow correctly but PRESERVE the extra-selection component.
_RIVAL_W7 = _swap(
    _BASE, _NARROW,
    "    return ({ rhs with selectCols := [targetField],\n"
    "                       hasAnnotationSelection := false,\n"
    "                       explicitValuesApplied := true })",
)

# (w8) VALUE FRAME: on the leave-unchanged arm, clear one component instead of
# returning the subquery untouched. Correct on the whole narrowing arm.
_RIVAL_W8 = _swap(
    _BASE, _BOTH_ARMS,
    "    return restrictTo rhs [targetField]\n"
    "  return ({ rhs with hasAnnotationSelection := false })",
)

# (w9) Narrow with the full correct effect but to a FIXED column name rather
# than the comparison's target column.
_RIVAL_W9 = _swap(_BASE, _NARROW, '    return restrictTo rhs ["id"]')

# (w10) VALUE FRAME at the `selectCols` component: on the leave-unchanged arm,
# discard the subquery's current column selection instead of returning it
# untouched. Correct on the whole narrowing arm. This is the component nagini's
# frame case defended directly; w8 attacks the same arm at a different component,
# and neither subsumes the other (each is correct where the other is wrong).
_RIVAL_W10 = _swap(
    _BASE, _BOTH_ARMS,
    "    return restrictTo rhs [targetField]\n"
    "  return ({ rhs with selectCols := [] })",
)


# --- witnesses (checked with the frozen obligation removed) -----------------
# The carrier is transparent, so each states the refutation at literal inputs
# and closes with `decide`; none binds a hypothesis, so none can be
# inconsistent. All were built both ways (rival exit 0, gold exit 1).

def _wit(cols: str, ann: str, ext: str, exp: str, pk: str, tf: str) -> str:
    state = (f"{{ selectCols := {cols}, hasAnnotationSelection := {ann},\n"
             f"      hasExtraSelection := {ext}, explicitValuesApplied := {exp} }}")
    inner = state.replace("\n      ", "\n        ")
    return (
        "example : ¬ problem_spec_prepInLookup\n"
        f"    {state}\n    {pk} {tf}\n"
        "    (implementation_prepInLookup\n"
        f"      {inner}\n      {pk} {tf}) := by\n"
        "  unfold problem_spec_prepInLookup implementation_prepInLookup\n"
        "  decide"
    )


# Carries a derived annotation-selection but no explicit selection => gold
# narrows; w1 reads the component as "already selected" and leaves it alone.
_WIT_W1 = _wit("[]", "true", "false", "false", "false", '"author_id"')
# Explicitly selected, with an EMPTY selection list but a derived
# annotation-selection present => gold leaves it unchanged; w2 reads the empty
# list and narrows anyway.
#
# The annotation component is load-bearing, not decoration. Dropping it (the
# plainer state selectCols=[], all masks clear, explicitValuesApplied=true) also
# refutes w2 and also fails on gold, so it passes the gate — but at THAT input w1
# narrows too, so the witness holds of w1 as well and attributes nothing to what
# separates the two rivals. Re-measured both ways with real builds: the plainer
# witness elaborates against w1 (exit 0), this one does not (exit 1, `decide`
# proving w1 satisfies the spec there). Keep the mask set.
_WIT_W2 = _wit("[]", "true", "false", "true", "false", '"publisher_id"')
# Carries only the extra-selection component => gold narrows; w3's extra guard
# conjunct suppresses it.
_WIT_W3 = _wit("[]", "false", "true", "false", "false", '"isbn"')
# Plain unselected subquery => gold marks the result explicitly selected; w4
# leaves the mark off.
_WIT_W4 = _wit("[]", "false", "false", "false", "false", '"author_id"')
# Target column IS the primary key => gold leaves the subquery unchanged; w5
# narrows it. The only witness that moves lhsTargetPrimaryKey.
_WIT_W5 = _wit("[]", "false", "false", "false", "true", '"pk"')
# Carries an annotation-selection => gold clears it; w6 keeps it.
_WIT_W6 = _wit("[]", "true", "false", "false", "false", '"book_id"')
# Carries an extra-selection (and a non-empty current selection, so this witness
# also moves selectCols) => gold clears it; w7 keeps it.
_WIT_W7 = _wit('["title"]', "false", "true", "false", "false", '"isbn"')
# Explicitly selected AND carrying an annotation-selection => gold returns it
# untouched; w8 clears the annotation component on that arm.
_WIT_W8 = _wit("[]", "true", "false", "true", "false", '"author_id"')
# Plain unselected subquery with a target column that is not the fixed name =>
# gold selects the target column; w9 selects its constant.
_WIT_W9 = _wit("[]", "false", "false", "false", "false", '"author_id"')
# Explicitly selected AND carrying a non-empty current selection => gold returns
# it untouched; w10 discards the selection on that arm. The ONLY witness in the
# battery that takes the leave-unchanged arm with a NON-EMPTY selectCols, which is
# what makes the else-arm frame observable at that component at all: every other
# else-arm witness (w2, w5, w8) holds selectCols at [], where clearing it is a
# no-op and this rival is indistinguishable from gold.
_WIT_W10 = _wit('["title", "isbn"]', "false", "false", "true", "false",
                '"author_id"')


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-degenerate-guard-swap",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SWAP,
        "rationale": (
            "a structurally different CORRECT impl: a pure functional expression "
            "(no imperative do-block), the guard written in its de Morgan dual, "
            "and the two arms EXCHANGED so the leave-unchanged case is tested "
            "first. The spec's conditional is agnostic to how the decision is "
            "spelled and to which arm is written first, so this must verify; the "
            "proof was re-closed by splitting on the two boolean components "
            "separately instead of on their conjunction. If it fails, the spec is "
            "pinned to an incidental branch order / guard spelling rather than to "
            "the behaviour => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-inline-restriction",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": (
            "a second correct impl that keeps the imperative shape but INLINES "
            "the narrowed subquery's record literal instead of reaching the same "
            "value through the pure restriction helper — nagini's "
            "pos-rhs-inline-projection argument on this carrier. The four "
            "postcondition conjuncts hold of the literal by `rfl`, so this must "
            "verify. If it fails, the spec forces a particular CALL structure "
            "rather than the observable result => SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY) ----
    {
        "id": "admiss-narrowing-reachable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM,
        "rationale": (
            "the obligation must be SATISFIABLE at an F2P-shaped input, not only "
            "in the abstract. Ports nagini's admiss-rhs-narrow-reachable: the "
            "frozen obligation is a bare `∀` over a total carrier, so there is no "
            "precondition binder to attack, and the analogue of "
            "PRECOND-TOO-STRONG here is the obligation being unsatisfiable at "
            "exactly the input the F2P exercises. Two `have`s prepended to the "
            "frozen tactic body discharge it at one concrete such input — a "
            "subquery carrying BOTH derived-selection components with no explicit "
            "column selection, compared against a non-primary-key target — the "
            "first by deciding the spec predicate there, the second by EVALUATING "
            "the modeled behaviour down to the concrete narrowed state. The second "
            "is what pins the admission to the NARROWING arm: the spec pins "
            "`result` to a term over the same inputs, so the first `have` alone "
            "would read identically had the input landed in the leave-unchanged "
            "arm. Then the frozen obligation is closed verbatim. Must verify — if "
            "it does not, the modeled behaviour is unsatisfiable at precisely the "
            "input the change is about. Nothing is assumed: the impl region, the "
            "theorem statement and the frozen script are byte-identical, and no "
            "declaration, axiom or assumption token is introduced. Measured "
            "load-bearing: the same two `have`s over a rival that narrows to a "
            "constant column FAIL to elaborate."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "w1-guard-derives-from-masks",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W1,
        "witness": _WIT_W1,
        "refinement": (
            "its faithful real patch decides the narrowing from whether the "
            "subquery happens to carry any current selection or derived-selection "
            "component, rather than from whether an explicit column selection was "
            "applied. (It is wrong in both directions, not merely an "
            "over-suppression: on a subquery that carries nothing at all but WAS "
            "explicitly selected it also narrows where the spec's else-arm "
            "requires the subquery be left alone. The witness below is placed on "
            "the over-suppression direction, which is the reported one.) "
            "A subquery that acquired derived selections without the "
            "user ever selecting columns then reports itself as already selected, "
            "the narrowing is skipped, and the comparison is issued against a "
            "subquery returning many columns instead of one — precisely the "
            "column-count mismatch error in the report. Both F2P tests would "
            "still FAIL, so a verifying rival here is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "attacks the FIRST HALF OF THE GUARD, which the spec grounds solely "
            "in the `explicitValuesApplied` binder. Witness at a subquery with "
            "hasAnnotationSelection=true, explicitValuesApplied=false: the spec's "
            "narrowing arm fires (so gold selects [targetField] and clears both "
            "components) while the rival takes the leave-unchanged path. Built "
            "both ways (rival exit 0; gold exit 1, `decide` proving the spec does "
            "hold there)."
        ),
    },
    {
        "id": "w2-guard-reads-current-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W2,
        "witness": _WIT_W2,
        "refinement": (
            "its faithful real patch decides the narrowing by inspecting whether "
            "the subquery's current column selection is non-empty. That is wrong "
            "in BOTH directions: it skips narrowing for a subquery carrying "
            "derived selections (the reported failure), and it re-narrows a "
            "subquery whose columns WERE deliberately chosen but whose selection "
            "list is empty, discarding a user's explicit choice. The F2P "
            "annotation/alias subquery tests fail on the first direction and the "
            "explicit-selection suites regress on the second, so it would NOT "
            "resolve."
        ),
        "rationale": (
            "a NEAR-MISS of w1: both consult the wrong thing, but they disagree "
            "on the sub-domain where a derived-selection component is present "
            "WITHOUT a current column selection, so this case is refuted at an "
            "input that DISTINGUISHES them rather than at one they both fail. "
            "Witness at explicitValuesApplied=true, hasAnnotationSelection=true, "
            "selectCols=[]: the spec's else-arm demands `result = rhs`, this rival "
            "reads the empty selection list and narrows anyway, while w1 reads the "
            "annotation component and correctly leaves the subquery alone. Built "
            "three ways (rival 0; gold 1; and against w1 exit 1, `decide` proving "
            "w1 satisfies the spec at this input — so the witness is specific to "
            "what this rival gets wrong)."
        ),
    },
    {
        "id": "w3-guard-adds-extra-mask-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W3,
        "witness": _WIT_W3,
        "refinement": (
            "its faithful real patch keeps the correct explicit-selection test "
            "but additionally suppresses the narrowing whenever the subquery "
            "carries an extra-selection component. A subquery carrying that one "
            "component and no explicit selection is then left un-narrowed and the "
            "comparison again sees more columns than it expects, so the "
            "corresponding F2P test still fails -> NOT resolved. A strictly "
            "weaker over-suppression than w1, which is why it needs its own "
            "witness."
        ),
        "rationale": (
            "attacks the guard's first half from the over-SUPPRESSION side: the "
            "spec makes narrowing depend on `explicitValuesApplied` and "
            "`lhsTargetPrimaryKey` ONLY, so no additional component may gate it. "
            "Witness at hasExtraSelection=true with everything else clear — the "
            "one point where this rival and gold disagree, and the only witness "
            "besides w7 that moves `hasExtraSelection`. Built both ways (rival 0, "
            "gold 1)."
        ),
    },
    {
        "id": "w4-narrows-without-marking",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W4,
        "witness": _WIT_W4,
        "refinement": (
            "this is the pre-patch narrowing route: it does set the subquery's "
            "columns to the single target column and clears the derived "
            "components, but never records that an explicit column selection now "
            "applies. The subquery is therefore not recognised downstream as "
            "explicitly selected, and the related-membership behaviour the change "
            "is supposed to fix regresses -> NOT resolved."
        ),
        "rationale": (
            "attacks the fourth conjunct of the narrowing arm, "
            "`result.explicitValuesApplied = true`. Witness at a plain unselected "
            "subquery with a non-primary-key target: gold marks the result, the "
            "rival leaves the mark off while getting all three other conjuncts "
            "right, so only that conjunct fails. Built both ways (rival 0, "
            "gold 1)."
        ),
    },
    {
        "id": "w5-overfires-on-pk-target",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W5,
        "witness": _WIT_W5,
        "refinement": (
            "drops the primary-key half of the guard. Its faithful real patch "
            "narrows the subquery of a membership comparison whose target column "
            "IS the primary key — a case the unchanged code must leave alone — "
            "so it rewrites the emitted SQL on a sub-domain the large "
            "related-lookup P2P suite exercises -> NOT resolved. Correct on the "
            "entire non-primary-key sub-domain, which is why it is a genuine "
            "partial-domain rival rather than a mechanical break."
        ),
        "rationale": (
            "attacks the SECOND HALF OF THE GUARD, i.e. the `lhsTargetPrimaryKey` "
            "binder — the ONLY rival that moves it, so without this case a rival "
            "mishandling only the primary-key sub-domain would verify unnoticed. "
            "Witness at lhsTargetPrimaryKey=true with explicitValuesApplied=false: "
            "the spec's else-arm demands `result = rhs`, and the rival narrows. "
            "Built both ways (rival 0, gold 1)."
        ),
    },
    {
        "id": "w6-keeps-annotation-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W6,
        "witness": _WIT_W6,
        "refinement": (
            "its faithful real patch narrows the subquery's columns but leaves the "
            "annotation-selection component in place, so the narrowed subquery "
            "returns the target column PLUS the carried annotations. The "
            "comparison expects exactly one column and again sees several, so the "
            "F2P annotation/alias subquery test still fails -> NOT resolved."
        ),
        "rationale": (
            "attacks the second conjunct of the narrowing arm, "
            "`result.hasAnnotationSelection = false`. Witness at a subquery "
            "carrying an annotation-selection and no explicit selection: gold "
            "clears it, the rival preserves it while satisfying the other three "
            "conjuncts. Built both ways (rival 0, gold 1)."
        ),
    },
    {
        "id": "w7-keeps-extra-selection",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W7,
        "witness": _WIT_W7,
        "refinement": (
            "the same failure as w6 on the OTHER derived-selection component: the "
            "narrowed subquery keeps its extra selections and so returns more "
            "than the one column the comparison expects -> the F2P test still "
            "fails -> NOT resolved. Nagini's twin collapsed both components into "
            "a single boolean, so its one faithfulness rival becomes two here; "
            "each is correct where the other is wrong, so they cannot share a "
            "witness."
        ),
        "rationale": (
            "attacks the third conjunct of the narrowing arm, "
            "`result.hasExtraSelection = false`. Witness at a subquery carrying "
            "an extra-selection AND a non-empty current selection (so this "
            "witness also moves the `selectCols` binder): gold clears the "
            "component, the rival preserves it. Built both ways (rival 0, "
            "gold 1)."
        ),
    },
    {
        "id": "w8-touches-untouched-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W8,
        "witness": _WIT_W8,
        "refinement": (
            "its faithful real patch mutates a subquery it was supposed to leave "
            "entirely alone, discarding a derived-selection component from every "
            "membership comparison that takes the no-narrowing path. Querysets "
            "that legitimately carry those selections into a membership "
            "comparison would silently lose them, changing the returned rows for "
            "the P2P suites that combine an explicit column selection with "
            "annotations -> NOT resolved."
        ),
        "rationale": (
            "attacks the LEAVE-UNCHANGED ARM, `result = rhs`. Because that clause "
            "is a whole-structure equality it is also the VALUE-FRAME obligation "
            "for all four components at once, which is how nagini's frame class "
            "survives the move to a referentially transparent carrier (there is "
            "no permission level to abuse here, but the untouched components are "
            "observable in the result). Witness at an explicitly-selected "
            "subquery carrying an annotation-selection: gold returns it "
            "identically, the rival clears one component. Built both ways "
            "(rival 0, gold 1). Note that this case pins the else-arm frame at ONE "
            "component only — a whole-structure equality is what the CLAUSE says, "
            "but a single rival can only witness the component it touches, so the "
            "`selectCols` component needs its own rival (w10)."
        ),
    },
    {
        "id": "w9-narrows-to-fixed-column",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W9,
        "witness": _WIT_W9,
        "refinement": (
            "its faithful real patch narrows the subquery to a hard-coded column "
            "name instead of the column the comparison actually targets. The "
            "comparison then matches the wrong column, so the membership result "
            "set is wrong for every target other than that one name — the F2P "
            "related-membership test returns wrong rows -> NOT resolved."
        ),
        "rationale": (
            "attacks the first conjunct of the narrowing arm, "
            "`result.selectCols = [targetField]`, whose right-hand side is "
            "grounded in the `targetField` binder — so a constant fails at every "
            "target but its own. Witness at a plain unselected subquery whose "
            "target differs from the rival's constant. Built both ways (rival 0, "
            "gold 1)."
        ),
    },
    {
        "id": "w10-drops-selection-on-untouched-arm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_W10,
        "witness": _WIT_W10,
        "refinement": (
            "its faithful real patch discards the column selection of a subquery "
            "it was supposed to leave entirely alone: every membership comparison "
            "that takes the no-narrowing path — which is precisely the path taken "
            "when the columns WERE deliberately chosen — comes back having lost "
            "that choice, so the comparison is issued against a subquery selecting "
            "nothing rather than the chosen column. The explicit-selection "
            "membership suites return wrong rows -> NOT resolved. Correct on the "
            "entire narrowing arm, so it is a genuine partial-domain rival."
        ),
        "rationale": (
            "attacks the LEAVE-UNCHANGED ARM at the `selectCols` component, which "
            "w8 cannot reach: w8 clears a boolean and is witnessed at "
            "selectCols=[], where discarding the selection is a no-op. The clause "
            "`result = rhs` is a whole-structure equality, so it frames all four "
            "components, but a rival only witnesses the one it touches — this case "
            "supplies the value-frame rival for the list-valued component, and is "
            "the only witness in the battery that takes the else-arm with a "
            "NON-EMPTY selection. Built both ways (rival exit 0; gold exit 1, "
            "`decide` proving the spec does hold there)."
        ),
    },
]
