# properties.py — G-PBT falsification battery for sympy__sympy-22080 (lean lane).
#
# PORTED from the nagini sibling's battery for this instance: the adversarial
# ARGUMENTS are carried across, the mechanics re-expressed against THIS backend's
# carrier. Each SPEC case is a FULL Solution.lean variant that shares the FROZEN
# spec byte-for-byte — only the impl region, and for two soundness positives the
# proof body, differ — so `markers.same_spec` holds by construction and every
# `theorem correct_renderProduct` keeps a byte-identical STATEMENT. No case adds an
# axiom, a helper lemma, `sorry`, `admit` or `native_decide`.
#
# Every expect="reject" case carries a refutation `witness`: a snippet stating
#   `¬ problem_spec_renderProduct <literals> (implementation_renderProduct <same>)`
# closed by `decide`. It ELABORATES against the rival and FAILS on the frozen
# solution, so the rejection is attributable to the SPEC and not to a tactic script
# that merely stopped matching a reshaped impl. This carrier is fully TRANSPARENT
# (no `opaque` callee, no unconstrained axiom: factor strengths are `Rat`, factor and
# denominator texts are `String`, all supplied as inputs), so no witness needs to
# condition on a hypothesis — all twelve are stated at literal inputs and bind
# nothing, which also means the gate's consistency probe has nothing to probe.
#
# That transparency is what makes every gold-side failure here a PLAIN EVALUATION
# rather than a tactic accident, and it was verified by the forgery experiment on
# ALL TWELVE cases rather than inferred from the error text. Each witness's gold
# build fails with `Tactic 'decide' proved that the proposition ¬(…)`, i.e. the
# kernel evaluated the claim and found the negation false. Flipping the claim (the
# same file with the leading `¬` dropped, so it asserts the frozen solution IS
# correct at that input) INVERTS both exit codes: the flipped claim builds clean
# against the frozen solution (12/12 exit 0) and FAILS against the rival (12/12
# exit 1, `decide` proving the un-negated proposition false). Gold's exit code
# therefore tracks what is claimed, which is the property that distinguishes a
# refutation from a hollow signature.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE — what this spec actually pins.
#
#   problem_spec_renderProduct (sign : String) (prec : Rat) (num : List Factor)
#                              (den : List String) (result : String) : Prop :=
#     result = renderProduct sign prec num den
#
#   ONE top-level equation, but it composes several INDEPENDENT sub-clauses, and a
#   rival can be wrong in exactly one of them while agreeing with the frozen
#   solution everywhere else. Each is attacked separately:
#
#     (C1) BRANCH SELECTION. The dedicated constant comparison level is used exactly
#          when `num.length = 1 ∧ sign = "-"`; otherwise each numerator factor is
#          compared against the product's own binding strength `prec`. BOTH conjuncts
#          are load-bearing and are attacked separately — weak-guard-sign-inverted
#          (the sign half) and weak-guard-length-two (the arity half) — plus
#          weak-general-branch-dropped, which deletes the distinction entirely.
#     (C2) THE DEDICATED LEVEL's VALUE. The spec pins the wrap decision at EVERY
#          factor strength, not merely at the strengths any test happens to exercise.
#          The sharpest attacks move the level a LITTLE: weak-level-just-below sits a
#          half unit under it (agreeing with the frozen solution on every strength
#          outside one narrow band) and weak-level-to-additive drops it to the
#          strength a negated product's own textual form binds at.
#     (C3) THE GENERAL BRANCH's LEVEL. Outside the special case the level IS `prec` —
#          that binder is live, and substituting a constant is wrong
#          (weak-general-level-atom).
#     (C4) THE WRAP PREDICATE. A factor is wrapped iff its strength does not exceed
#          the level. A rival that decides unconditionally in either direction is
#          wrong on one side of the strength domain (weak-never-wrap: wrong for every
#          strength at or below the level; weak-always-wrap: wrong for every strength
#          above it). These two carry the nagini strength-lookup argument onto this
#          carrier — they are wrong precisely because they ignore the strength.
#     (C5) NUMERATOR ASSEMBLY: the factor texts are `*`-joined IN INPUT ORDER
#          (weak-numerator-reversed).
#     (C6) THE SIGN PREFIX, and its position (weak-sign-dropped).
#     (C7) THE DENOMINATOR TAIL: three arms on `den.length` — absent; one
#          already-rendered text after `/` and NOT re-wrapped; the `*`-joined group
#          after `/` and parenthesized. Attacked by weak-den-branches-swapped (each
#          arm gets the other's treatment) and weak-den-dropped (the tail vanishes).
#
#   BINDER COVERAGE. All four input binders vary across the twelve reject witnesses,
#   which sit at twelve DISTINCT input points: `sign` takes both `"-"` (7 cases) and
#   `""` (5); `prec` takes 40, 50 and 60; `num` varies in LENGTH (1 and 2) and in
#   factor STRENGTH (30, 45, 50, 60, 70, 1000 — straddling both the dedicated level
#   and the `prec` values in play); `den` takes length 0, 1 and 2. A binder held fixed
#   by every witness would be a binder no rival was built to abuse.
#
#   REFINEMENT GROUNDING. No `refinement` below is asserted from reading the code.
#   For each rival, its FAITHFUL real patch was applied to this instance's own
#   worktree at `base_commit` (reference patch otherwise applied) and the instance's
#   FAIL_TO_PASS + PASS_TO_PASS names were run; the F2P/P2P breakage quoted per case
#   is measured. Every shipped rival breaks at least one, so were any of them to
#   VERIFY it would be a genuine verify-does-not-imply-resolve break.
#
# ---------------------------------------------------------------------------
# NAGINI CASES THAT DID NOT PORT, AND WHY
#
#   * CARRIER SHAPE. The nagini sibling contracts THREE small functions over an
#     integer-level carrier: a per-operand strength lookup, a wrap predicate over
#     that strength, and a composite boolean tying them together. This bundle models
#     ONE function — the renderer — and takes each factor's strength and rendered text
#     as plain INPUTS. So nagini's two cases attached to the strength LOOKUP have no
#     counterpart: here the strength is an input value, and a variant cannot change an
#     input. Their ARGUMENT survives as weak-never-wrap / weak-always-wrap, which are
#     wrong exactly because they discard the strength they were given.
#   * THE NAGINI COMPOSITE CASE attacked an illustrative third function pinned to a
#     constant. There is no composite here. The observable it stood for — a lone
#     negated factor whose strength does not exceed the dedicated level IS wrapped —
#     is attacked directly and at three different strengths by
#     weak-general-branch-dropped (50), weak-level-to-additive (45) and
#     weak-level-just-below (50 against a level a half unit lower).
#   * FRAME / PERMISSION MUTATION: VACUOUS on lean. Lean is referentially
#     transparent, so a rival that writes back into a read-only input is not
#     expressible. (The nagini sibling records this class N/A on its side too, for the
#     analogous reason: its modeled functions take values and return a value.) The
#     frame obligation instead lives inside the equation — every fragment of the
#     output is pinned — and is attacked structurally by weak-numerator-reversed,
#     weak-sign-dropped, weak-den-branches-swapped and weak-den-dropped.
#   * DIVERGENCE / NON-TERMINATION: VACUOUS on lean, not a spec hole, and MEASURED
#     rather than asserted. This bundle sets no `loom.semantics.termination` option
#     at all (it is vanilla Lean 4 + Mathlib, not the Velvet carrier), so the
#     verifier's totality requirement is Lean's own: every `def` must be shown to
#     terminate. Both expressible spellings of a diverging impl were BUILT to
#     confirm the class is unreachable rather than merely awkward. (a) A plain
#     `def spin (n : Nat) : String := spin (n + 1)` does not elaborate —
#     `fail to show termination for spin / failed to infer structural recursion`
#     — so the variant never reaches the spec at all and its rejection would
#     attest to the elaborator, not to the postcondition. (b) The one spelling
#     that DOES elaborate, `partial def spin`, makes the term opaque to the
#     kernel: a witness at literal inputs against it fails with
#     `Tactic 'decide' failed for proposition ...`, i.e. a stuck reduction, which
#     is precisely the `_STUCK_REDUCTION` shape the gate screens as
#     `witness-undecided`. So no shippable witness exists for this class on this
#     carrier — not because the proof is hard, but because a `partial` term
#     decides nothing. (On velvet, under partial termination semantics, the same
#     class would instead be a KNOWN SPEC HOLE — a non-terminating impl verifies
#     vacuously there. It is not vacuous everywhere.) The nagini sibling ships no
#     divergence case either.
#   * ADMISSIBILITY: PORTED — see `admiss-f2p-shaped-input` below. An earlier draft
#     of this manifest recorded the lane N/A on the ground that the frozen
#     obligation carries NO precondition hypothesis, so PRECOND-TOO-STRONG was
#     said to be unreachable. That reasoning is wrong on a TOTAL carrier and the
#     case is now shipped. The obligation being an unconditional universal does
#     remove the "hypothesis too strong" reading, but the analogue that remains is
#     the obligation being UNSATISFIABLE at exactly an F2P-shaped input — a spec
#     whose equation no implementation can meet at the very point the instance is
#     about would still pass a battery of reshapes and rivals, because every one of
#     those cases only ever compares two impls to each other. Discharging the
#     postcondition AT that concrete input, by evaluation, before closing the
#     frozen obligation verbatim, tests it directly. Nagini's own case defended an
#     integer-range `Requires` this carrier does not have, so what ports is the
#     lane's PURPOSE, not its mechanism.
#   * AXIOM_TESTS: dropped. The axiom lane is G-AX's business and this gate ignores
#     it; there is no `opaque`/`axiom` callee here in any case.
#
#   TWO NAGINI CASES DELIBERATELY OMITTED BECAUSE THEIR REFINEMENT IS FALSE HERE.
#     Two nagini rivals move the dedicated level UPWARD rather than down — one to the
#     strength a power-shaped factor binds at, one making the boundary comparison
#     strict. Both port cleanly as same-spec Lean impls, and both ARE rejected by this
#     spec (I built them and saw discriminating witnesses elaborate). But their
#     `refinement` does not survive measurement: each one's faithful real patch was
#     applied to the worktree and the ENTIRE F2P + P2P set PASSES, so a verifying
#     rival there would not be a verify-does-not-imply-resolve break at all.
#     Measured further, every dedicated level across a wide range above the frozen one
#     resolves, because the instance's test surface constrains the wrap decision only
#     at the two low strengths and the one very high strength it exercises — it never
#     pins a mid-range strength bare. The frozen spec is therefore STRICTER than the
#     test surface in that band. That is a note about the spec, not a defect this gate
#     can find, and it is emphatically not something a reject case may quietly imply,
#     so both are omitted and named in `assessment` instead.
#     An independent audit re-derived both as Lean variants and CONFIRMED the
#     rejection half mechanically: the strength-flip rival (the special branch's
#     comparison made strict, so a lone negated factor at exactly the dedicated
#     level is left bare) and the level-raised-to-power rival both fail to verify
#     (exit 1). Their omission therefore rests only on the refinement claim, which
#     is the right place for it — the spec's extra strictness above the frozen level
#     is a note, not a hole.
#
# ---------------------------------------------------------------------------
# WHAT AN INDEPENDENT AUDIT PROBED AND DID NOT FIND (attacks D and E)
#
#   SPEC-TOO-WEAK probe. Six NEW wrong impls this battery does not contain, aimed
#   at the clauses the shipped rivals leave least attacked, were built against the
#   frozen spec. All six were REJECTED (exit 1), so none is a spec hole:
#     - the special branch's comparison made STRICT (wrong only at a factor of
#       exactly the dedicated strength — a single-point divergence, and nagini's
#       own strict-flip argument);
#     - the dedicated level raised to the power-shaped strength (wrong in the band
#       above the frozen level, the direction no shipped rival takes);
#     - the GENERAL branch's comparison made strict (wrong at a factor of exactly
#       the product's own strength — the general branch's BOUNDARY, where
#       weak-general-level-atom only replaces the level wholesale);
#     - a special arm on the EMPTY numerator list, a `num` shape no shipped witness
#       visits (every witness sits at length 1 or 2);
#     - the multi-entry denominator group joined with the wrong SEPARATOR (the
#       join character, where the two shipped denominator rivals attack the ARM);
#     - the sign emitted as a SUFFIX rather than a prefix (its POSITION, where
#       weak-sign-dropped only removes it).
#   SPEC-TOO-STRONG probe. Four NEW correct reshapes were built; three VERIFY
#   (exit 0), so the spec accepts them and they are not soundness holes: the wrap
#   predicate INLINED at both call sites; the empty-denominator test spelled
#   `den = []` instead of `den.isEmpty`; and the one-entry denominator arm spelled
#   with the same join the many-entry arm uses (equal on a singleton). The fourth,
#   the branch guard as NESTED `if`s instead of a conjunction, also verifies once
#   its proof splits the two guards separately — so it is a proof-effort matter,
#   not a spec rejection. No faithful correct impl was found that this spec
#   refuses.
from pathlib import Path

INSTANCE = "sympy__sympy-22080"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace the unique occurrence of `old`, or raise so drift breaks loudly."""
    if old not in src:
        raise AssertionError(f"anchor drift: {old!r} absent")
    if src.count(old) != 1:
        raise AssertionError(f"anchor not unique ({src.count(old)}x): {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# ANCHORS — every one lies ENTIRELY inside the impl (or proof) region and is
# unique in the file, asserted at import time.
# ---------------------------------------------------------------------------

# The whole frozen impl body.
_IMPL = '''def implementation_renderProduct
    (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String := Id.run do
  let mut numStr : List String := []
  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    return sign ++ body
  else if den.length = 1 then
    return sign ++ body ++ "/" ++ den.headI
  else
    return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"'''
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

# The branch-selection block alone. Distinguished from the pure helper's copy of
# the same shape by the `numStr :=` assignments, which only the impl has.
_SEL = '''  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)'''
assert _BASE.count(_SEL) == 1, "selection anchor drifted"

# The general-branch assignment together with the `*`-join. Again unique via
# `numStr :=`; the pure helper's join line alone is not.
_BODY = '''    numStr := num.map (parenFactor prec)
  let body := String.intercalate "*" numStr'''
assert _BASE.count(_BODY) == 1, "body anchor drifted"

# The three-way denominator tail alone. Unique via the `return`s.
_TAIL = '''  if den.isEmpty then
    return sign ++ body
  else if den.length = 1 then
    return sign ++ body ++ "/" ++ den.headI
  else
    return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"'''
assert _BASE.count(_TAIL) == 1, "tail anchor drifted"

# The frozen proof BODY (statement excluded, so it cannot be touched). Swapped
# only by the positives whose reshaped impl needs an honest reproof of the very
# same obligation.
_PROOF = '''  intro sign prec num den
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [Id.run, numeratorTexts, bind, pure]
  split <;> split <;> rfl'''
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"


# ===========================================================================
# SOUNDNESS POSITIVES — structurally different but CORRECT implementations. Each
# must VERIFY; a rejection means the spec over-constrains the implementation
# (SPEC-TOO-STRONG). None weakens the obligation: the theorem statement is
# byte-identical in all four and no lemma or hypothesis is introduced.
# ===========================================================================

# pos-level-in-local: rather than choosing between two `map`s, what varies is the
# comparison LEVEL — a mutable `Rat` initialised to the product's own strength and
# overwritten with the dedicated constant when the special case applies, then a
# SINGLE `map`. Same value at every input; the frozen proof body still closes it.
_POS_LEVEL_LOCAL = _swap(_BASE, _IMPL, '''def implementation_renderProduct
    (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String := Id.run do
  let mut lvl : Rat := prec
  if num.length = 1 ∧ sign = "-" then
    lvl := negSingleLevel
  let numStr := num.map (parenFactor lvl)
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    return sign ++ body
  else if den.length = 1 then
    return sign ++ body ++ "/" ++ den.headI
  else
    return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"''')

# pos-pure-functional: no `Id.run do`, no `let mut`, no early `return` — the same
# behaviour written as pure `let`-bound `if`-expressions. Reproved honestly inside
# the proof region (after unfolding the numerator helper the impl is definitionally
# the spec's right-hand side); identical theorem statement.
_POS_PURE = _swap(_swap(_BASE, _IMPL, '''def implementation_renderProduct
    (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String :=
  let numStr : List String :=
    if num.length = 1 ∧ sign = "-" then num.map (parenFactor negSingleLevel)
    else num.map (parenFactor prec)
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    sign ++ body
  else if den.length = 1 then
    sign ++ body ++ "/" ++ den.headI
  else
    sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"'''), _PROOF,
    '''  intro sign prec num den
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [numeratorTexts]''')

# pos-guard-commuted: the two conjuncts of the branch test are COMMUTED. Logically
# equivalent, so the value is identical at every input — but `rfl` alone no longer
# closes the goal, which is precisely what makes this a worthwhile positive: it
# separates "the spec accepts an equivalent implementation" from "the frozen tactic
# script happened to match the frozen syntax". Reproved with the frozen script plus
# `and_comm`; the obligation is unchanged.
_POS_GUARD_COMMUTED = _swap(_swap(_BASE, _SEL, '''  if sign = "-" ∧ num.length = 1 then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)'''), _PROOF,
    '''  intro sign prec num den
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [Id.run, numeratorTexts, bind, pure, and_comm]
  split <;> split <;> rfl''')

# admiss-f2p-shaped-input: the obligation is SATISFIABLE at an F2P-shaped input.
# Not a reshape — the impl is the FROZEN one, byte-for-byte; what is added is a
# `have` that discharges the spec predicate at one concrete input BY EVALUATION
# (`decide`), ahead of the frozen tactic body closing the frozen obligation
# verbatim. The input is the shape the instance is about: a lone factor under a
# leading minus, whose binding strength does not exceed the dedicated constant
# level while sitting strictly ABOVE the product's own strength — so the `have`
# drives the special branch AND depends on the dedicated level being the one the
# comparison uses. If the postcondition were unsatisfiable there, this `have`
# could not close, and no reject case in the battery would notice: a rival only
# ever shows two impls DIFFER, never that the spec is meetable at all.
#
# The `have` is INFORMATIVE, not something `decide` would close regardless —
# audited by a two-way control, both built:
#   * the same `have` asserting the spec of the WRONG rendering at that input (the
#     unwrapped text) FAILS, with `decide` reporting the proposition `is false`;
#   * the same `have` asserting the spec of the CORRECT rendering as a bare string
#     LITERAL closes.
# So the step really evaluates the postcondition at this input rather than
# discharging whatever is put in front of it. Nothing is assumed: no new
# declaration, no lemma, no axiom, no `sorry`; the `theorem correct_renderProduct`
# statement stays byte-identical and the frozen four-line body follows the `have`.
_ADMISS_F2P = _swap(_BASE, _PROOF, '''  intro sign prec num den
  have admissible :
      problem_spec_renderProduct "-" 40 [{ strength := 50, text := "x % y" }] []
        (implementation_renderProduct "-" 40
          [{ strength := 50, text := "x % y" }] []) := by
    unfold problem_spec_renderProduct implementation_renderProduct renderProduct
    decide
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [Id.run, numeratorTexts, bind, pure]
  split <;> split <;> rfl''')

# pos-tail-by-match: the three-way denominator tail as a `match` on the SHAPE of
# `den` (`[]` / `[d]` / `_`) instead of two `if`s on `den.isEmpty` and `den.length`.
# Same three arms, same texts; reproved by case-splitting `den`.
_POS_TAIL_MATCH = _swap(_swap(_BASE, _TAIL, '''  match den with
  | [] => return sign ++ body
  | [d] => return sign ++ body ++ "/" ++ d
  | _ => return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"'''),
    _PROOF, '''  intro sign prec num den
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [Id.run, numeratorTexts, bind, pure]
  rcases den with _ | ⟨d, ds⟩
  · split <;> rfl
  · rcases ds with _ | ⟨e, es⟩ <;> split <;> simp''')


# ===========================================================================
# UNIQUENESS RIVALS — wrong implementations under the SAME spec. Each must be
# REJECTED; a verification means the spec admits a wrong program (SPEC-TOO-WEAK).
# Each ships with the witness that made me believe it: I built both halves and saw
# the rival build succeed and the frozen build fail.
# ===========================================================================

# --- (C1) branch selection -------------------------------------------------

# The special case is deleted: every numerator factor, lone-and-negated or not, is
# compared against the product's own binding strength.
_W_BRANCH_DROPPED = _swap(_BASE, _SEL,
                          "  numStr := num.map (parenFactor prec)")
# prec 40 < strength 50 <= dedicated level: the frozen solution wraps, the rival
# does not.
_WIT_BRANCH_DROPPED = '''example : ¬ problem_spec_renderProduct "-" 40
    [{ strength := 50, text := "x % y" }] []
    (implementation_renderProduct "-" 40
      [{ strength := 50, text := "x % y" }] []) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# The sign half of the guard is inverted: the special level is applied to a lone
# factor that is NOT negated, and withheld from one that is.
_W_GUARD_SIGN = _swap(_BASE, _SEL, '''  if num.length = 1 ∧ sign ≠ "-" then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)''')
# Unnegated lone factor, strength 60: the frozen solution compares against
# prec = 60 and wraps; the rival takes the special level 55 and does not.
_WIT_GUARD_SIGN = '''example : ¬ problem_spec_renderProduct "" 60
    [{ strength := 60, text := "p ** q" }] []
    (implementation_renderProduct "" 60
      [{ strength := 60, text := "p ** q" }] []) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# The arity half of the guard is off by one: the special level is applied to a
# negated PAIR of factors and withheld from a negated single one.
_W_GUARD_LEN = _swap(_BASE, _SEL, '''  if num.length = 2 ∧ sign = "-" then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)''')
# Two negated factors of strength 50 at prec 40: the frozen solution takes the
# general branch (50 > 40, neither wrapped), the rival the special one (both).
_WIT_GUARD_LEN = '''example : ¬ problem_spec_renderProduct "-" 40
    [{ strength := 50, text := "a" }, { strength := 50, text := "b" }] []
    (implementation_renderProduct "-" 40
      [{ strength := 50, text := "a" }, { strength := 50, text := "b" }] []) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# --- (C2) the dedicated level's value --------------------------------------

# The dedicated level is dropped to the strength a negated product's own textual
# form binds at — the level the general branch would have used for such a product.
_W_LEVEL_ADD = _swap(_BASE, _SEL, '''  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (parenFactor (40 : Rat))
  else
    numStr := num.map (parenFactor prec)''')
# Strength 45 sits strictly between the rival's level and the frozen one, so the
# frozen solution wraps and the rival does not.
_WIT_LEVEL_ADD = '''example : ¬ problem_spec_renderProduct "-" 60
    [{ strength := 45, text := "a + b" }] ["z"]
    (implementation_renderProduct "-" 60
      [{ strength := 45, text := "a + b" }] ["z"]) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# The sharpest partial-domain attack: the dedicated level is lowered by a HALF
# UNIT. Factor strengths occur in half-unit steps, so this rival agrees with the
# frozen solution on every strength except those in one narrow band — including
# agreeing at the half-unit strength just below, which is the case the frozen
# docstring calls out. It is nagini's "move the cutoff a little, not a lot"
# argument, retargeted at the boundary this carrier actually exposes.
_W_LEVEL_BELOW = _swap(_BASE, _SEL, '''  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (parenFactor (99 / 2 : Rat))
  else
    numStr := num.map (parenFactor prec)''')
# Strength 50 is inside that band: wrapped by the frozen solution, bare here.
# The `have h` step is here only because `decide` cannot reduce the rival's
# non-integral rational literal on its own (its `Rat.instDecidableLe` gets stuck on
# the division); `norm_num` settles that one numeric comparison and `decide` then
# closes the string equality exactly as in the other eleven witnesses. It assumes
# nothing — `h` is a closed arithmetic fact, not a hypothesis about the inputs, so
# the witness still binds nothing and remains a statement at literal inputs.
# That necessity is MEASURED, not assumed: the same witness with the `have h` and
# the `simp only` deleted, leaving a bare `decide`, was built against this rival
# and fails with `Tactic 'decide' failed for proposition ¬(… parenFactor (99 / 2)
# …)`. So the extra step is a reduction aid for one `Rat` comparison, not a
# weakening — and this case's gold-side failure is still a plain evaluation, with
# the flipped claim building clean on the frozen solution and failing on the rival
# like the other eleven.
_WIT_LEVEL_BELOW = '''example : ¬ problem_spec_renderProduct "-" 60
    [{ strength := 50, text := "x % y" }] ["(y*y)"]
    (implementation_renderProduct "-" 60
      [{ strength := 50, text := "x % y" }] ["(y*y)"]) := by
  have h : ¬ ((50 : Rat) ≤ 99 / 2) := by norm_num
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [Id.run, numeratorTexts, parenFactor, List.map_cons, List.map_nil, bind, pure,
    if_neg h]
  decide'''

# --- (C3) the general branch's level ---------------------------------------

# The general branch stops consulting `prec` and compares every factor against the
# maximum atomic strength instead, so it wraps essentially everything.
_W_GENERAL_ATOM = _swap(_BASE, _BODY,
    '''    numStr := num.map (parenFactor (1000 : Rat))
  let body := String.intercalate "*" numStr''')
# strength 60 > prec 50: the frozen solution leaves it bare, the rival wraps it.
_WIT_GENERAL_ATOM = '''example : ¬ problem_spec_renderProduct "" 50
    [{ strength := 60, text := "x**2" }] []
    (implementation_renderProduct "" 50
      [{ strength := 60, text := "x**2" }] []) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# --- (C4) the wrap predicate ------------------------------------------------

# The lone-negated factor is emitted BARE, whatever its strength: the strength
# input is discarded rather than compared.
_W_NEVER_WRAP = _swap(_BASE, _SEL, '''  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (fun f => f.text)
  else
    numStr := num.map (parenFactor prec)''')
# Strength 30 is far below the dedicated level, so the frozen solution wraps.
_WIT_NEVER_WRAP = '''example : ¬ problem_spec_renderProduct "-" 50
    [{ strength := 30, text := "a + b" }] []
    (implementation_renderProduct "-" 50
      [{ strength := 30, text := "a + b" }] []) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# The mirror: the lone-negated factor is ALWAYS wrapped, again ignoring strength.
# Wrong on the other half of the domain, which is why both are needed.
_W_ALWAYS_WRAP = _swap(_BASE, _SEL, '''  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (fun f => "(" ++ f.text ++ ")")
  else
    numStr := num.map (parenFactor prec)''')
# Strength 70 exceeds the dedicated level, so the frozen solution emits it bare.
_WIT_ALWAYS_WRAP = '''example : ¬ problem_spec_renderProduct "-" 40
    [{ strength := 70, text := "f(x)" }] []
    (implementation_renderProduct "-" 40
      [{ strength := 70, text := "f(x)" }] []) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# --- (C5) numerator assembly ------------------------------------------------

# The numerator texts are joined in REVERSE input order. Invisible at length one,
# so only a multi-factor witness can see it.
_W_NUM_REVERSED = _swap(_BASE, _BODY,
    '''    numStr := num.map (parenFactor prec)
  let body := String.intercalate "*" numStr.reverse''')
# Two atomic-strength factors at prec 40: neither is wrapped, so the ONLY
# difference the spec can see is the order.
_WIT_NUM_REVERSED = '''example : ¬ problem_spec_renderProduct "" 40
    [{ strength := 1000, text := "a" }, { strength := 1000, text := "b" }] []
    (implementation_renderProduct "" 40
      [{ strength := 1000, text := "a" }, { strength := 1000, text := "b" }] []) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# --- (C6) the sign prefix ---------------------------------------------------

# The sign is dropped from all three arms of the tail.
_W_SIGN_DROPPED = _swap(_BASE, _TAIL, '''  if den.isEmpty then
    return body
  else if den.length = 1 then
    return body ++ "/" ++ den.headI
  else
    return body ++ "/(" ++ String.intercalate "*" den ++ ")"''')
# A negated atomic factor over a single denominator: the strength is above the
# dedicated level so no wrapping is in play and the sign is the sole difference.
_WIT_SIGN_DROPPED = '''example : ¬ problem_spec_renderProduct "-" 40
    [{ strength := 1000, text := "a" }] ["b"]
    (implementation_renderProduct "-" 40
      [{ strength := 1000, text := "a" }] ["b"]) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# --- (C7) the denominator tail ----------------------------------------------

# The one-entry and many-entry arms are SWAPPED: a single denominator text gets
# group-wrapped (double-wrapping what upstream already rendered) and a multi-entry
# denominator collapses to its first entry, unwrapped.
_W_DEN_SWAPPED = _swap(_BASE, _TAIL, '''  if den.isEmpty then
    return sign ++ body
  else if den.length = 1 then
    return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
  else
    return sign ++ body ++ "/" ++ den.headI''')
# Two denominator entries: the frozen solution emits the parenthesized group, the
# rival silently loses the second entry.
_WIT_DEN_SWAPPED = '''example : ¬ problem_spec_renderProduct "" 40
    [{ strength := 1000, text := "a" }] ["p", "q"]
    (implementation_renderProduct "" 40
      [{ strength := 1000, text := "a" }] ["p", "q"]) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''

# The denominator is dropped entirely: the tail always returns the numerator.
_W_DEN_DROPPED = _swap(_BASE, _TAIL, "  return sign ++ body")
_WIT_DEN_DROPPED = '''example : ¬ problem_spec_renderProduct "" 40
    [{ strength := 1000, text := "a" }] ["b"]
    (implementation_renderProduct "" 40
      [{ strength := 1000, text := "a" }] ["b"]) := by
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  decide'''


SPEC_TESTS = [
    # ---------------- soundness: the obligation must stay provable ----------
    {
        "id": "pos-level-in-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LEVEL_LOCAL,
        "rationale":
            "The impl varies the comparison LEVEL in a mutable local instead of "
            "choosing between two `map` calls, then maps once. Extensionally equal "
            "to the frozen impl at every input, so the spec must still hold. A "
            "rejection would mean the equation is pinned to the frozen control "
            "flow — two `map`s rather than one — which is a shape the spec has no "
            "business dictating (SPEC-TOO-STRONG). The theorem statement is "
            "byte-identical and the frozen tactic body closes it unchanged, so "
            "nothing about the obligation was relaxed to make this pass.",
    },
    {
        "id": "pos-pure-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale":
            "The imperative skeleton is gone: no `Id.run do`, no `let mut`, no "
            "early `return`, just pure `let`-bound `if`-expressions. Same value "
            "everywhere. This is the positive that most directly tests whether the "
            "spec constrains BEHAVIOUR or merely the monadic dress the frozen impl "
            "happens to wear. The proof body is reproved (the impl is now "
            "definitionally the spec's right-hand side once the numerator helper is "
            "unfolded) against a byte-identical statement, with no new lemma, "
            "assumption or axiom — so it is a reproof of the same obligation, not a "
            "weakening of it.",
    },
    {
        "id": "pos-guard-commuted",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_GUARD_COMMUTED,
        "rationale":
            "The two conjuncts of the branch-selection test are commuted. "
            "Logically equivalent, so the output is identical at every input — but "
            "`rfl` no longer closes the goal by computation, which is exactly the "
            "point: this case distinguishes 'the spec admits an equivalent "
            "implementation' from 'the frozen tactic script matched the frozen "
            "syntax'. Discharged by adding `and_comm` to the frozen `simp only` "
            "set, which is a step of ordinary reasoning about the impl, not a "
            "change to what must be shown; the obligation statement is unchanged "
            "and no lemma is introduced.",
    },
    {
        "id": "pos-tail-by-match",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_TAIL_MATCH,
        "rationale":
            "The three-way denominator tail is expressed as a `match` on the SHAPE "
            "of `den` rather than as nested `if`s on `den.isEmpty` and "
            "`den.length`. The three arms and their texts are unchanged, so the "
            "value is identical, and the spec must accept it; a rejection would "
            "mean the tail clause is over-specified to one of two equivalent ways "
            "of discriminating a list's length. Reproved by case-splitting `den` "
            "against the identical statement, adding nothing.",
    },

    # ---------------- admissibility: the obligation is satisfiable ----------
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_F2P,
        "rationale":
            "The frozen obligation is an unconditional universal, so there is no "
            "precondition HYPOTHESIS that could be too strong — but on a total "
            "carrier the analogue of PRECOND-TOO-STRONG is the obligation being "
            "UNSATISFIABLE at exactly an F2P-shaped input, and that is what this "
            "case tests. The impl is the frozen one byte-for-byte; a `have` "
            "discharges `problem_spec_renderProduct` by EVALUATION at one concrete "
            "input — a lone factor under a leading minus whose binding strength "
            "does not exceed the dedicated level while exceeding the product's own "
            "strength, i.e. the point where the special branch and the dedicated "
            "level are both load-bearing — and only then does the frozen tactic "
            "body close the frozen obligation verbatim. No reject case in this "
            "battery can see this property: a rival establishes that two impls "
            "DIFFER, never that the spec is meetable at the input the instance is "
            "about. Audited by a two-way control (both built): the same `have` "
            "asserting the spec of the WRONG rendering at that input fails with "
            "`decide` reporting the proposition `is false`, and the same `have` "
            "asserting the CORRECT rendering as a bare string literal closes — so "
            "the step evaluates the postcondition rather than discharging anything "
            "placed in front of it. The theorem statement is byte-identical and no "
            "declaration, lemma, axiom or `sorry` is introduced.",
    },

    # ---------------- uniqueness: (C1) branch selection --------------------
    {
        "id": "weak-general-branch-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_BRANCH_DROPPED,
        "rationale":
            "Attacks clause C1 by deleting the special case outright: every "
            "numerator factor is compared against the product's own binding "
            "strength, lone-and-negated or not. If the spec verified this, it would "
            "not be pinning the distinguished treatment of a single negated factor "
            "at all — the whole content of the branch selection would be "
            "unconstrained.",
        "refinement":
            "MEASURED, not assumed: the faithful real patch (delete the "
            "special-case arm, keep only the general comparison) was applied to "
            "this instance's worktree at base_commit with the reference patch "
            "otherwise in place, and the instance's FAIL_TO_PASS and PASS_TO_PASS "
            "names were run. ALL THREE FAIL_TO_PASS tests fail. So this rival is "
            "the strongest possible refinement counterexample: if it ever "
            "verified, the artifact would attest to a proof of correctness for a "
            "program that resolves nothing.",
        "witness": _WIT_BRANCH_DROPPED,
    },
    {
        "id": "weak-guard-sign-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_GUARD_SIGN,
        "rationale":
            "Attacks the SIGN half of the C1 conjunction in isolation, leaving the "
            "arity half intact: the dedicated level is applied to a lone factor "
            "that is NOT negated and withheld from one that is. A spec that "
            "verified this would be pinning only that the special case depends on "
            "there being exactly one factor, and saying nothing about which sign "
            "selects it — so the two conjuncts have to be attacked separately, and "
            "this is that attack.",
        "refinement":
            "MEASURED: with the guard's sign comparison inverted in the real "
            "worktree, all three FAIL_TO_PASS tests fail. A verifying rival here "
            "would be a genuine verify-does-not-imply-resolve break.",
        "witness": _WIT_GUARD_SIGN,
    },
    {
        "id": "weak-guard-length-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_GUARD_LEN,
        "rationale":
            "Attacks the ARITY half of the C1 conjunction in isolation, leaving the "
            "sign half intact: the dedicated level is applied to a negated PAIR of "
            "factors and withheld from a negated single one — an off-by-one in the "
            "arity test. Together with weak-guard-sign-inverted this pins both "
            "conjuncts, and with weak-general-branch-dropped it pins that the "
            "distinction exists at all.",
        "refinement":
            "MEASURED: with the arity test changed to two in the real worktree, all "
            "three FAIL_TO_PASS tests fail — the lone-negated-factor rendering the "
            "instance is about is never reached.",
        "witness": _WIT_GUARD_LEN,
    },

    # ---------------- uniqueness: (C2) the dedicated level ------------------
    {
        "id": "weak-level-to-additive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_LEVEL_ADD,
        "rationale":
            "Attacks clause C2 — the VALUE of the dedicated level — by dropping it "
            "to the strength a negated product's own textual form binds at, i.e. "
            "the level the general branch would have used anyway. This is the "
            "subtler cousin of weak-general-branch-dropped: the special branch "
            "still exists and is still selected on the right inputs, it simply "
            "carries the wrong level, so a spec that pinned only the CONTROL FLOW "
            "and not the level would verify it.",
        "refinement":
            "MEASURED: with the dedicated level replaced by the additive strength "
            "in the real worktree, all three FAIL_TO_PASS tests fail. Note that "
            "the direction matters and was checked — lowering the level to this "
            "value breaks the F2P set, whereas several RAISED levels do not, which "
            "is why only the downward rivals are shipped.",
        "witness": _WIT_LEVEL_ADD,
    },
    {
        "id": "weak-level-just-below",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_LEVEL_BELOW,
        "rationale":
            "The sharpest partial-domain attack in the battery, and the direct heir "
            "of the nagini 'move the cutoff by the smallest observable step' case: "
            "the dedicated level is lowered by a HALF UNIT. Factor strengths occur "
            "in half-unit steps, so this rival agrees with the frozen solution on "
            "every strength outside one narrow band — it still wraps the "
            "half-unit-lower strength the frozen docstring calls out, and still "
            "leaves every strength above the level bare. Only a witness placed "
            "inside that band can see it, so this case tests whether the spec pins "
            "the wrap decision POINTWISE across the strength domain or merely on "
            "the coarse regions a test suite would exercise.",
        "refinement":
            "MEASURED: with the level lowered by a half unit in the real worktree, "
            "TWO of the three FAIL_TO_PASS tests fail; the third exercises a factor "
            "whose strength lies outside the affected band, which is precisely why "
            "this rival is the subtle one. Breaking any F2P test settles it: the "
            "faithful patch does not resolve the instance, so a verifying rival "
            "would be a real verify-does-not-imply-resolve break.",
        "witness": _WIT_LEVEL_BELOW,
    },

    # ---------------- uniqueness: (C3) the general branch's level ----------
    {
        "id": "weak-general-level-atom",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_GENERAL_ATOM,
        "rationale":
            "Attacks clause C3 and, with it, the liveness of the `prec` BINDER: the "
            "general branch stops consulting the product's own binding strength and "
            "compares every factor against the maximum atomic strength, wrapping "
            "essentially everything. If the spec verified this, `prec` would be an "
            "input the postcondition never actually reads in the branch that is "
            "supposed to depend on it — the sort of unvaried-binder hole a battery "
            "that only ever attacked the special case would miss entirely.",
        "refinement":
            "MEASURED: with the general branch's comparison level replaced by the "
            "atomic strength in the real worktree, ONE FAIL_TO_PASS test fails and "
            "THREE PASS_TO_PASS tests regress (over-parenthesized output is "
            "compared textually). The faithful patch does not resolve the "
            "instance.",
        "witness": _WIT_GENERAL_ATOM,
    },

    # ---------------- uniqueness: (C4) the wrap predicate ------------------
    {
        "id": "weak-never-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_NEVER_WRAP,
        "rationale":
            "Attacks clause C4 by discarding the factor's STRENGTH in the special "
            "branch and emitting the text bare unconditionally. This is where the "
            "nagini strength-lookup argument lands on this carrier: nagini could "
            "corrupt the lookup because it modeled it as a function, whereas here "
            "the strength is an input, so the corresponding wrong program is one "
            "that ignores the input it was given. Wrong on the whole at-or-below "
            "the-level half of the strength domain.",
        "refinement":
            "MEASURED: with the lone-negated factor emitted unparenthesized in the "
            "real worktree, all three FAIL_TO_PASS tests fail — this is close to "
            "the pre-reference behaviour for the inputs the instance is about.",
        "witness": _WIT_NEVER_WRAP,
    },
    {
        "id": "weak-always-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_ALWAYS_WRAP,
        "rationale":
            "The mirror of weak-never-wrap, and needed for the same reason a "
            "one-sided test is not enough: the strength is again discarded, but now "
            "the factor is ALWAYS wrapped, so the rival is wrong on the strictly "
            "above-the-level half of the domain instead. Between them the two cases "
            "pin that the wrap decision is a comparison rather than a constant, in "
            "either direction; a spec that caught only one would leave the other "
            "half of the predicate unconstrained.",
        "refinement":
            "MEASURED: with the lone-negated factor always parenthesized in the "
            "real worktree, ONE FAIL_TO_PASS test fails and ONE PASS_TO_PASS test "
            "regresses (spuriously wrapped output is compared textually). The "
            "faithful patch does not resolve the instance. Note the asymmetry with "
            "weak-never-wrap, which breaks all three F2P tests: over-wrapping is "
            "much less visible to this test surface than under-wrapping, so it is "
            "the half of the predicate that most needs the spec to pin it.",
        "witness": _WIT_ALWAYS_WRAP,
    },

    # ---------------- uniqueness: (C5)/(C6)/(C7) assembly ------------------
    {
        "id": "weak-numerator-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_NUM_REVERSED,
        "rationale":
            "Attacks clause C5: the numerator texts are `*`-joined in REVERSE input "
            "order. This is the structural/frame attack that replaces nagini's "
            "permission-mutation class, which is vacuous on a referentially "
            "transparent carrier — instead of asking whether an input can be "
            "corrupted in place, it asks whether the ORDER of the inputs is pinned "
            "in the output. Invisible at one factor, so it also exercises the "
            "multi-element shape of the `num` binder.",
        "refinement":
            "MEASURED: with the numerator fragments joined in reverse in the real "
            "worktree, no FAIL_TO_PASS test breaks but THREE PASS_TO_PASS tests "
            "regress (the expected source strings are order-sensitive). That is "
            "enough for the refinement claim — a patch that regresses a "
            "PASS_TO_PASS test does not resolve the instance — and it is worth "
            "recording that this rival's wrongness is invisible to the F2P set "
            "alone, which is exactly why the spec, not the test suite, has to pin "
            "the ordering.",
        "witness": _WIT_NUM_REVERSED,
    },
    {
        "id": "weak-sign-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_SIGN_DROPPED,
        "rationale":
            "Attacks clause C6: the leading sign is dropped from every arm of the "
            "tail. The `sign` binder is read by the branch selection (C1) and again "
            "as an output prefix, and those are separate obligations — a rival can "
            "select the right branch and still not emit the sign. This case pins "
            "the second one.",
        "refinement":
            "MEASURED: with the sign omitted from the assembled text in the real "
            "worktree, ALL THREE FAIL_TO_PASS tests fail and three PASS_TO_PASS "
            "tests regress. The faithful patch does not resolve the instance.",
        "witness": _WIT_SIGN_DROPPED,
    },
    {
        "id": "weak-den-branches-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_DEN_SWAPPED,
        "rationale":
            "Attacks clause C7 by giving each denominator arm the OTHER's "
            "treatment: a single already-rendered denominator text gets group-"
            "wrapped a second time, and a multi-entry denominator collapses to its "
            "first entry with the rest silently lost. The frozen spec's asymmetry "
            "here is deliberate (the single entry arrives fully rendered, so "
            "re-wrapping it is wrong) and this is the rival that tests it. Also "
            "exercises `den` at length two.",
        "refinement":
            "MEASURED: with the two denominator arms swapped in the real worktree, "
            "ONE PASS_TO_PASS test regresses and no FAIL_TO_PASS test breaks. That "
            "still settles the refinement claim — the faithful patch does not "
            "resolve the instance — and it makes this rival one the F2P set alone "
            "cannot see.",
        "witness": _WIT_DEN_SWAPPED,
    },
    {
        "id": "weak-den-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _W_DEN_DROPPED,
        "rationale":
            "Attacks clause C7 at its coarsest: the denominator tail vanishes and "
            "the numerator alone is returned, so the `den` binder is not read at "
            "all. If the spec verified this, the entire denominator half of the "
            "postcondition would be dead weight and the `den` input unconstrained — "
            "the crudest possible unvaried-binder hole, and the baseline the two "
            "finer denominator attacks are measured against.",
        "refinement":
            "MEASURED: with the denominator dropped from the assembled text in the "
            "real worktree, FIVE PASS_TO_PASS tests regress (no FAIL_TO_PASS test "
            "breaks — the instance's own failing tests never exercise a "
            "denominator). The faithful patch does not resolve the instance.",
        "witness": _WIT_DEN_DROPPED,
    },
]
