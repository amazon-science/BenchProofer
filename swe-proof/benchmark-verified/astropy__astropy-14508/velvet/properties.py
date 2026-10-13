"""properties.py — G-PBT falsification battery for astropy__astropy-14508 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
every ``prove_correct`` obligation survives) and swaps in a candidate impl; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must elaborate against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE (``formatFloatField (value : Float) return (out : List Char)``):
  the decimal-field renderer turns a finite real into a field of at most 20 code
  points spending the MINIMAL number of significant digits. Six ``ensures``
  clauses, in four groups:

    (C1) well-formed / cap        1 ≤ out.length ∧ out.length ≤ 20
    (C2) fits ⇒ exact rendering   (shortestField value).length ≤ 20 →
                                     out = shortestField value
                                   … → parseDec out = value
                                   … → sigCount out = minSig value
    (C3) over-cap, no exponent    …length > 20 → eIndex … ≥ length →
                                     out = (shortestField value).take 20
    (C4) over-cap, exponent @idx  …length > 20 → eIndex … < length →
                                     out = take (20-(len-idx)) ++ drop idx

  THE CARRIER IS AN OPAQUE-AXIOM ORACLE. The whole spec is stated over OPAQUE
  AXIOMS — ``shortestField``, ``parseDec``, ``sigCount``, ``minSig``,
  ``paddedField`` — applied to an OPAQUE ``Float``. There is no executable
  content: ``shortestField value`` never reduces, and its length /
  exponent-index are unknown to the elaborator. That fact governs the WITNESS
  TECHNIQUE, not which clauses can be attacked: every clause here is refutable,
  but a rival's divergence must be stated at a point described by HYPOTHESIS —
  conditioning on the carrier — because no literal float decides the guards.

WITNESS MECHANICS, AND THE TRAP THIS BATTERY WAS REPAIRED FOR.
  The velvet tester path (``extract_program_for`` → ``derive_tester_for`` →
  ``<name>Tester args = false := by decide``) IS DEAD HERE: the tester extracts
  an EXECUTABLE program, but ``formatFloatField`` depends on the opaque axioms
  and has no executable code, and the postcondition's ``Decidable`` instance
  gets stuck on ``parseDec``/``sigCount``. Measured: a wrong rival and gold fail
  the tester build IDENTICALLY, so it discriminates nothing.

  So every witness here speaks DIRECTLY to the method's Hoare triple. The frozen
  file runs under ``loom.semantics.termination "total"`` (line 4) and opens
  ``TotalCorrectness DemonicChoice`` (line 7), so ``triple`` is the TOTAL-
  correctness triple ``prove_correct`` discharges, and ``wp_pure`` reduces the
  weakest precondition of a ``return`` to a fact about the returned value.

  THE TRAP. An earlier draft of this battery built three rivals whose body was an
  UNCONDITIONAL ``return <concrete>``. On such a rival ``formatFloatField``
  unfolds to a bare ``pure``, so ``rw [wp_pure]`` fires and the claim is decided.
  Against GOLD, whose body is a nested ``if`` over opaque guards, ``wp_pure``
  cannot fire AT ALL — the goal still has the shape ``wp (if … then pure … else
  …) post``. Gold's build therefore failed with

      Tactic `rewrite` failed: Did not find an occurrence of the pattern
        wp (pure ?x) ?post

  for EVERY claim, true or false, because the failure is an UNFOLDING failure and
  never reaches the claim. Measured with five forgery builds against the frozen
  solution: the witness's own claim, the claim with ``¬`` DROPPED (asserting gold
  is CORRECT there), the tautology ``0 ≤ out.length`` under a ``¬``, and a
  non-refutation asserting the rival merely SATISFIES ``out.length ≤ 21``, all
  produced the byte-identical first error line — and that last forgery built
  against the rival at exit 0, so the gate would have recorded
  "rejected (witness refutes the rival)" for a witness that refutes nothing.
  Gold's exit code carried no information about the claim, and those three cases
  attested to a tactic mismatch rather than to the spec.

  THE REPAIR, applied to all three. A rival must KEEP gold's branching structure
  and diverge only INSIDE one branch, and its witness must CONDITION on that
  branch's guard so ``if_pos`` / ``if_neg`` selects the branch on BOTH sides.
  Then ``wp_pure`` fires on both, and the closing step
  (``omega``/``exact hne …``) DECIDES the claim on each. Every reject
  case below has been built the four required ways and the flip pair proves the
  gold-side error tracks the claim:

    rival exit 0 · gold exit 1 · consistency probe exit 1 ·
    FLIPPED claim (the ``¬`` dropped, asserting gold IS correct on that branch)
      exit 0 on GOLD and exit 1 on the RIVAL

  That last line is the discrimination the gate cannot see: gold's failure is now
  a refutation of the concrete claim (``omega`` on real length arithmetic, a
  ``Type mismatch`` on a decided length fact, or ``rfl``/``h3`` on a decided
  content equation), not a pattern that never matched.

  AND THE FLIP HAS TO CARRY THE SAME CLOSER, not merely the same prefix. Fixing
  the unfolding is not the same as fixing the DECISION: a witness can reach a
  real conditioned goal on both sides and still close it with a tactic that is
  INERT on gold's half, and then gold's exit code tracks the tactic's reach
  rather than the claim. ``weak-fit-empty`` shipped that way for three audits —
  ``simp at hcon`` on an opaque-axiom application, gold's ``simp` made no
  progress`` reproduced byte-for-byte by the opposite claim — because every flip
  build swapped in the closer the flipped goal needed. Its closer is now
  claim-agnostic text that decides arithmetic on either claim; see the case
  header and the FOURTH AUDIT note in the footer.

  No banned token (sorry/admit/native_decide/axiom/opaque) appears in any
  witness.

FRAME-MUTATION — VACUOUS, not fabricated. Already N/A on nagini (the sole input
  is an interpreted float value, no heap location). Vacuous here for the stronger
  backend reason too: Velvet is referentially transparent and this bundle
  declares no ``mut`` binder, so there is no read-only input to overwrite and no
  substitute probe to build.

UNGROUNDED-ORACLE — N/A as an attack. ``shortestField`` IS the opaque oracle; its
  properties are pinned by the ``axioms`` region and validated executably by
  G-AX. Two honest correct-reshape POSITIVE CONTROLS are carried instead.

DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE SEMANTICS
against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` / ``if`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` (line 4) AND carries
``open TotalCorrectness DemonicChoice`` (line 7), and BOTH lines select the
total scope: the ``set_option`` itself opens ``TotalCorrectness`` (Loom,
``MonadAlgebras/WP/Options.lean``, the ``openScope `TotalCorrectness`` arm) and
line 7 opens it again explicitly. Only the ``PartialCorrectness`` twin of
``WPGen.forWithInvariantLoop`` takes a loop measure and DISCARDS it, which is
why the two lines have to move together and do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation: ``TotalCorrectness.WPGen.
forWithInvariantLoop`` takes the ``measure`` and emits ``⌜measure b' <
measure b⌝`` as a goal the proof must discharge. Re-measured on THIS bundle with
real builds, both shapes a diverging rival can take are rejected at exit 1:
  * a ``while 0 < 1`` prefix with ``done_with 1 < 0`` and a CONSTANT
    ``decreasing (0 : Nat)`` fails on the measure's own goal, ``case
    «decreasing_1: (0 : Nat)» ... ⊢ 0 < 0``;
  * the same loop with ``decreasing k`` over an INCREASING ``k := k + 1`` fails
    the same way, ``case «decreasing_1: k» ... ⊢ k + 1 < k``.
Dropping the clause rather than faking it is refused even earlier, by the
elaborator's own check (``Decreasing annotations are required in total
correctness semantics``). So divergence neither applies to this impl nor
discharges the ``ensures`` clauses vacuously if a rival introduces it, and no
spec hole is escalated from the class.

It is also not shippable as a reject case, and the FIFTH AUDIT corrected the
reason this file gave for that — the old reason was measurably wrong. The old
text said the rival's ``method`` declaration itself fails to compile in the
witness file, so no witness could ELABORATE against it. Re-measured with real
builds: the ``method`` declaration compiles FINE in the stripped witness file
(the ``decreasing`` obligation lives in ``prove_correct``, which
``pbt_witness._strip_prove_correct`` removes, so the rival's module error simply
does not arise there). The real obstacle is one level in, and it is the same
``forIn Lean.Loop.mk`` shape ``pbt.py``'s own ``_STUCK_UNIFICATION`` screen
exists for: with a loop spliced in, ``formatFloatField`` unfolds to a term whose
head is ``forIn Lean.Loop.mk``, no ``rw [if_pos …]`` can reach past it to the
branch, and ``wp_pure`` never fires. Four witness shapes were tried against that
rival — a conditioned C1 claim closed by ``omega``, the same closed by
``simp_all``, a C2 content claim closed by ``absurd``, and one carrying the
``rw [if_pos hle]`` prefix — and ALL FOUR fail on the rival (exit 1), i.e. they
fail the half that must SUCCEED. A ``trace_state`` build prints why: ``hcon``'s
type is the un-normalised ``wp (do let _ ← forIn Lean.Loop.mk 0 fun x r => …;
if (shortestField value).length ≤ 20 then …) …``, with the whole branch structure
sitting under the loop. So this is a WITNESS-SIDE carrier limit — the gate would
record ``witness-unproven`` — and not a gap in the spec, which refuses the rival
at the module level anyway (the two measure shapes above, both exit 1).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries four
axiom-soundness / containment probes over the real stdlib callees; that is
G-AX's job (axiom_check.py / mapping.md) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14508"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body. Every variant below
# ---- replaces exactly this text, so each edit lies wholly inside the one
# ---- -- impl-start .. -- impl-end region and same_spec holds by construction.
_IMPL = (
    "    -- impl-start\n"
    "    let vs := shortestField value\n"
    "    let n := vs.length\n"
    "    if n ≤ 20 then\n"
    "      return vs\n"
    "    else\n"
    "      let idx := eIndex vs\n"
    "      if idx ≥ n then\n"
    "        return vs.take 20\n"
    "      else\n"
    "        return vs.take (20 - (n - idx)) ++ vs.drop idx\n"
    "    -- impl-end"
)

assert _IMPL in _BASE, "frozen impl region drifted; update _IMPL"

# ---- The frozen proof script, replaced WHOLE by the admissibility case. The
# ---- `prove_correct` tactic body is elided by the consumer spec view, so this
# ---- edit keeps same_spec; `variant_scope` still requires the `prove_correct
# ---- formatFloatField` header to survive, which it does.
_PROVE_AT = _BASE.index("prove_correct formatFloatField by")
_HEAD = _BASE[:_PROVE_AT]
_LOOM = "prove_correct formatFloatField by\n  loom_solve\n"
assert _BASE.count(_LOOM) == 1, "frozen proof script drifted"


def _impl(fit, no_exp, exp):
    """A variant body with gold's BRANCHING STRUCTURE and per-branch returns.

    Every rival is built through this, which is what makes its witness
    discriminating: the two guards survive, so a witness that conditions on them
    reduces `wp_pure` on BOTH the rival and gold and the closing step decides the
    claim on each side. A rival that collapses the branches to one unconditional
    `return` instead makes gold's build fail by pattern-not-found for every
    claim — see the docstring's TRAP section.
    """
    return (
        "    -- impl-start\n"
        "    let vs := shortestField value\n"
        "    let n := vs.length\n"
        f"    if n ≤ 20 then\n      return {fit}\n"
        "    else\n"
        "      let idx := eIndex vs\n"
        f"      if idx ≥ n then\n        return {no_exp}\n"
        f"      else\n        return {exp}\n"
        "    -- impl-end"
    )


_GOLD_FIT = "vs"
_GOLD_NOEXP = "vs.take 20"
_GOLD_EXP = "vs.take (20 - (n - idx)) ++ vs.drop idx"

# Spec-side spellings of the two over-cap trims, in the frozen vocabulary.
_TAKE_KEPT = ("(shortestField value).take (20 - ((shortestField value).length"
              " - eIndex (shortestField value)))")
_DROP_SUF = "(shortestField value).drop (eIndex (shortestField value))"


# ---- The `:` that terminates a witness `example` head. A case with no extra
# ---- binders still needs it, so it is spliced in as the default rather than
# ---- living inside each caller's binder text.
_HEAD_END = "    :\n"


# ---- FIT-BRANCH witness. `hle` selects the early-return branch via `if_pos` on
# ---- BOTH sides, so `wp_pure` fires on both and `close` decides the claim.
def _fit_witness(post, close, extra_binders=""):
    return (
        "example (value : Float)\n"
        "    (hle : (shortestField value).length ≤ 20)\n"
        f"{extra_binders or _HEAD_END}"
        "    ¬ (triple True (formatFloatField value)\n"
        f"        (fun out => {post})) := by\n"
        "  simp only [formatFloatField, triple]\n"
        "  intro h\n"
        "  have hcon := h trivial\n"
        "  rw [if_pos hle] at hcon\n"
        "  rw [wp_pure] at hcon\n"
        f"{close}"
    )


# ---- OVER-CAP / NO-EXPONENT witness (the C3 branch). `if_neg` steps past the
# ---- fits guard, `if_pos` selects the marker-absent branch; both fire on gold
# ---- too, so `wp_pure` reduces on each side and the claim is decided.
def _noexp_witness(post, close, extra_binders=""):
    return (
        "example (value : Float)\n"
        "    (h1 : 20 < (shortestField value).length)\n"
        "    (h2 : eIndex (shortestField value) ≥ (shortestField value).length)\n"
        f"{extra_binders or _HEAD_END}"
        "    ¬ (triple True (formatFloatField value)\n"
        f"        (fun out => {post})) := by\n"
        "  simp only [formatFloatField, triple]\n"
        "  intro h\n"
        "  have hcon := h trivial\n"
        "  rw [if_neg (by omega), if_pos (by omega)] at hcon\n"
        "  rw [wp_pure] at hcon\n"
        f"{close}"
    )


# ---- OVER-CAP / EXPONENT-PRESENT witness (the C4 branch). Both `if_neg`s fire
# ---- on gold as well, so the closing step is a real decision on each side.
def _exp_witness(post, close, extra_binders=""):
    return (
        "example (value : Float)\n"
        "    (h1 : 20 < (shortestField value).length)\n"
        "    (h2 : eIndex (shortestField value) < (shortestField value).length)\n"
        f"{extra_binders or _HEAD_END}"
        "    ¬ (triple True (formatFloatField value)\n"
        f"        (fun out => {post})) := by\n"
        "  simp only [formatFloatField, triple]\n"
        "  intro h\n"
        "  have hcon := h trivial\n"
        "  rw [if_neg (by omega), if_neg (by omega)] at hcon\n"
        "  rw [wp_pure] at hcon\n"
        f"{close}"
    )


# ---- GUARD-DISAGREEMENT witness (added by the third audit). Every other witness
# ---- here selects the SAME branch on both sides, because every other rival keeps
# ---- gold's guards and varies only a returned expression. A rival that moves the
# ---- fits GUARD instead needs the opposite technique: the two impls take
# ---- DIFFERENT branches in the window where the guards disagree, so no single
# ---- `rw` chain fires on both. The `first` combinator supplies the branch
# ---- selection per side — `if_pos` on the rival (whose looser guard holds in the
# ---- window) and `if_neg`/`if_pos` on gold (whose guard does not) — after which
# ---- `wp_pure` reduces on each and `omega` decides the length claim on each. That
# ---- the alternatives are tried in order costs nothing: whichever fires leaves the
# ---- SAME goal shape, and the closing arithmetic is what separates the sides.
def _guard_window_witness(post, close):
    return (
        "example (value : Float)\n"
        "    (h1 : 20 < (shortestField value).length)\n"
        "    (hb : (shortestField value).length ≤ 21)\n"
        "    (h2 : eIndex (shortestField value) ≥ (shortestField value).length)\n"
        f"{_HEAD_END}"
        "    ¬ (triple True (formatFloatField value)\n"
        f"        (fun out => {post})) := by\n"
        "  simp only [formatFloatField, triple]\n"
        "  intro h\n"
        "  have hcon := h trivial\n"
        "  first\n"
        "  | rw [if_pos (by omega)] at hcon\n"
        "  | rw [if_neg (by omega), if_pos (by omega)] at hcon\n"
        "  rw [wp_pure] at hcon\n"
        f"{close}"
    )


# The C4 clause, written out as a postcondition (guards restated so the witness
# can feed them in and get the content equation).
_C4_POST = (
    "\n          20 < (shortestField value).length →\n"
    "          eIndex (shortestField value) < (shortestField value).length →\n"
    f"          out = {_TAKE_KEPT} ++ {_DROP_SUF}"
)
# The C3 clause likewise.
_C3_POST = (
    "\n          20 < (shortestField value).length →\n"
    "          eIndex (shortestField value) ≥ (shortestField value).length →\n"
    "          out = (shortestField value).take 20"
)


# ---- ADMISSIBILITY proof prelude. Discharges the WHOLE six-clause post-image at
# ---- an F2P-shaped point (a value whose exact rendering FITS the cap) BEFORE
# ---- closing the frozen obligation, then `clear`s it so the frozen bullet
# ---- script runs against a byte-identical goal state.
# ----
# ---- AUDIT REPAIR. The `have` is stated for ALL `v` in the fits sub-domain, but
# ---- THIRD-AUDIT REPAIR. The previous version closed with
# ----     have at_f2p := f2p_admissible (0.009125 : Float)
# ---- and its prose claimed that instantiation was "the step that makes the named
# ---- point the checked point", "measured load-bearing". Both claims are false,
# ---- and the second was measured wrong. `f2p_admissible` is a ∀-statement whose
# ---- body is an IMPLICATION guarded by `(shortestField v).length ≤ 20`, so
# ---- applying it to a float is a bare application of a ∀ to a term of type
# ---- `Float`: it type-checks for ANY float and DISCHARGES NOTHING, because the
# ---- guard is never supplied. Demonstrated with three builds against the frozen
# ---- spec: the case still verifies (exit 0) with `0.009125` replaced by
# ---- `0.00012345678901234567` (a value whose real rendering is 22 code points, so
# ---- the named sub-domain is the WRONG one), by `0.0`, and even by `value`
# ---- itself. An instantiation that survives replacement by a point where the
# ---- claim's own guard is false carries no information about any point. And the
# ---- guard genuinely cannot be discharged at a literal on this carrier — adding
# ----     have guard_at_f2p : (shortestField (0.009125 : Float)).length ≤ 20
# ---- fails (exit 1, `rfl failed: (shortestField 9125e-6).length is not
# ---- definitionally equal to 20`), which is the honest carrier fact the old
# ---- version's prose talked around.
# ----
# ---- So the concrete-float framing is DROPPED rather than patched: on an opaque
# ---- oracle no literal names a point. What replaces it is the thing the lane
# ---- actually exists to test, stated over the sub-domain where satisfiability is
# ---- a REAL question. The old case exhibited the post-image only on the FITS
# ---- sub-domain, where all four non-trivial conjuncts are either `rfl` or a bare
# ---- axiom and the two over-cap conjuncts are vacuous by `absurd` — nothing there
# ---- can be contradictory. The over-cap-with-marker sub-domain is different: the
# ---- field C4 DEMANDS (significand trimmed, whole suffix kept) must also be shown
# ---- to satisfy C1's cap, and that reconciliation needs the short-suffix fact. If
# ---- it failed, no impl could be admitted at exactly the input the
# ---- scientific-notation regression drives. Both sub-domains are now exhibited.
# ---- Measured load-bearing by FALSIFIED CONTROLS, one per sub-domain: asserting
# ---- the fits image meets a cap of 19 fails (exit 1, `Application type mismatch`
# ---- on `hfit`), and asserting the over-cap image meets a cap of 19 fails (exit 1,
# ---- `omega could not prove the goal` over the real length atoms). The shipped
# ---- version, with 20 in both places, verifies (exit 0).
_ADMISS_SCRIPT = """prove_correct formatFloatField by
  -- ADMISSIBILITY. On a total carrier the analogue of PRECOND-TOO-STRONG is the
  -- obligation being UNSATISFIABLE at an F2P-shaped input, so before closing the
  -- frozen obligation exhibit the six-clause post-image SATISFIED on each of the
  -- two sub-domains the regression tests drive. No literal float is named: the
  -- carrier is an opaque oracle, so `shortestField <lit>` does not reduce and an
  -- instantiation at a literal would discharge nothing (it is a ∀ applied to a
  -- term, with the sub-domain guard left unsupplied). Each sub-domain is instead
  -- described by HYPOTHESIS, which is what makes the claim checkable here.
  --
  -- (i) the FITS sub-domain: a value whose exact rendering is within the cap.
  -- Every conjunct comes from the axiom lane's own facts and the two over-cap
  -- conjuncts are vacuous, which is the content of the claim on this half.
  have fits_admissible : ∀ v : Float, (shortestField v).length ≤ 20 →
      (1 ≤ (shortestField v).length ∧ (shortestField v).length ≤ 20)
      ∧ ((shortestField v).length ≤ 20 → shortestField v = shortestField v)
      ∧ ((shortestField v).length ≤ 20 → parseDec (shortestField v) = v)
      ∧ ((shortestField v).length ≤ 20 → sigCount (shortestField v) = minSig v)
      ∧ ((shortestField v).length > 20 → eIndex (shortestField v) ≥ (shortestField v).length →
            shortestField v = (shortestField v).take 20)
      ∧ ((shortestField v).length > 20 → eIndex (shortestField v) < (shortestField v).length →
            shortestField v = (shortestField v).take
                (20 - ((shortestField v).length - eIndex (shortestField v)))
              ++ (shortestField v).drop (eIndex (shortestField v))) := by
    intro v hfit
    exact ⟨⟨shortestField_nonempty v, hfit⟩, fun _ => rfl,
           fun _ => shortestField_roundtrip v, fun _ => shortestField_minimal v,
           fun hgt _ => absurd hfit (by omega), fun hgt _ => absurd hfit (by omega)⟩
  -- (ii) the OVER-CAP sub-domain WITH an exponent marker — the scientific-notation
  -- path a P2P test drives. This is the only sub-domain where satisfiability is a
  -- real question: the field C4 DEMANDS must ALSO meet C1's cap, so the two
  -- clauses have to be reconciled through the short-suffix fact rather than each
  -- discharged on its own. If this `have` failed, the six clauses would be jointly
  -- unsatisfiable exactly where the over-cap regression lands and no impl could be
  -- admitted there.
  have overcap_admissible : ∀ v : Float, 20 < (shortestField v).length →
      eIndex (shortestField v) < (shortestField v).length →
      ∀ w : List Char, w = (shortestField v).take
              (20 - ((shortestField v).length - eIndex (shortestField v)))
            ++ (shortestField v).drop (eIndex (shortestField v)) →
      (1 ≤ w.length ∧ w.length ≤ 20)
      ∧ ((shortestField v).length ≤ 20 → w = shortestField v)
      ∧ ((shortestField v).length ≤ 20 → parseDec w = v)
      ∧ ((shortestField v).length ≤ 20 → sigCount w = minSig v)
      ∧ ((shortestField v).length > 20 → eIndex (shortestField v) ≥ (shortestField v).length →
            w = (shortestField v).take 20)
      ∧ ((shortestField v).length > 20 → eIndex (shortestField v) < (shortestField v).length →
            w = (shortestField v).take
                (20 - ((shortestField v).length - eIndex (shortestField v)))
              ++ (shortestField v).drop (eIndex (shortestField v))) := by
    intro v hgt hlt w hw
    have hsuf := shortestField_suffix_short v (eIndex (shortestField v)) hlt
      (eIndex_eq_E (shortestField v) hlt)
    refine ⟨⟨?_, ?_⟩, fun hfit => absurd hfit (by omega),
            fun hfit => absurd hfit (by omega), fun hfit => absurd hfit (by omega),
            fun _ hge => absurd hlt (by omega), fun _ _ => hw⟩
    · rw [hw, List.length_append, List.length_take, List.length_drop]; omega
    · rw [hw, List.length_append, List.length_take, List.length_drop]; omega
  clear fits_admissible overcap_admissible
  loom_solve
"""

# ---- Order-independent closer for the reshape positives. The frozen script's
# ---- positional bullets are tuned to the frozen impl's goal ORDER, which a
# ---- reshape changes; this discharges each obligation by SHAPE instead, so the
# ---- positive tests the spec rather than the bullet layout.
_RESHAPE_SCRIPT = """prove_correct formatFloatField by
  loom_solve
  all_goals (
    first
    | (intro _; exact shortestField_minimal value)
    | (intro _; exact shortestField_roundtrip value)
    | exact ⟨shortestField_nonempty value, by omega⟩
    | (-- over-cap with no marker: eIndex = length, so the trim degenerates
       intro hgt hge
       have hle := eIndex_le (shortestField value)
       have hidx : eIndex (shortestField value) = (shortestField value).length := by omega
       rw [hidx]; simp)
    | (-- the cap on an over-cap branch, from the short-suffix axiom
       have hle := eIndex_le (shortestField value)
       rcases Nat.lt_or_ge (eIndex (shortestField value)) (shortestField value).length with hlt | hge
       · have hE := eIndex_eq_E (shortestField value) hlt
         have hsuf := shortestField_suffix_short value (eIndex (shortestField value)) hlt hE
         rw [List.length_append, List.length_take, List.length_drop]; omega
       · have hidx : eIndex (shortestField value) = (shortestField value).length := by omega
         rw [hidx, List.length_append, List.length_take, List.length_drop]
         have := shortestField_nonempty value
         simp
         omega)
    | (intro _ _; rfl)
  )
"""


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT impl
    # that MUST verify, else SPEC-TOO-STRONG. Ports nagini pos-control-hoist-decl.
    # =====================================================================
    {
        "id": "pos-control-hoist-decl",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: hoist `let idx := eIndex vs` ABOVE the `n ≤ 20` early return.
        # Statement order across the branch changes, but every computed value is
        # unchanged (idx is used only on the over-cap branch), so the frozen
        # bullet-script still discharges each obligation.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    let vs := shortestField value\n"
            "    let n := vs.length\n"
            "    let idx := eIndex vs\n"
            "    if n ≤ 20 then\n"
            "      return vs\n"
            "    else\n"
            "      if idx ≥ n then\n"
            "        return vs.take 20\n"
            "      else\n"
            "        return vs.take (20 - (n - idx)) ++ vs.drop idx\n"
            "    -- impl-end",
        ),
        "rationale": "a structurally-different but correct reshape — the "
                     "exponent-index binding is hoisted above the fits early "
                     "return, computed values unchanged — must satisfy every "
                     "clause; else SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # POSITIVE CONTROL (soundness) — ADDED by audit. A far stronger reshape than
    # the hoist: the two over-cap branches are UNIFIED into one return. This is
    # correct but NOT definitionally equal to the frozen impl — when the marker
    # is absent, `eIndex vs = n` (by `eIndex_le` plus the guard) and the trim
    # `take (20-(n-n)) ++ drop n` must be shown to collapse to `take 20`, which
    # needs a real argument the frozen bullet script does not contain. So the
    # obligation is REPROVEN for the new shape, not restated. If the spec
    # rejected this it would be SPEC-TOO-STRONG on the branch-structure axis.
    # Measured: verifies (exit 0).
    # =====================================================================
    {
        "id": "pos-control-unify-overcap",
        "kind": "soundness",
        "expect": "verify",
        "module": (_HEAD.replace(
            _IMPL,
            "    -- impl-start\n"
            "    let vs := shortestField value\n"
            "    let n := vs.length\n"
            "    if n ≤ 20 then\n"
            "      return vs\n"
            "    else\n"
            "      let idx := eIndex vs\n"
            "      return vs.take (20 - (n - idx)) ++ vs.drop idx\n"
            "    -- impl-end", 1) + _RESHAPE_SCRIPT),
        "rationale": "a correct reshape that UNIFIES the two over-cap branches: "
                     "with the marker absent the index equals the length, so the "
                     "significand-trim collapses to the first-20 prefix. Not "
                     "definitionally the frozen impl — the collapse is a real "
                     "step, so every clause is reproven for the new shape rather "
                     "than restated. Must verify; else SPEC-TOO-STRONG (the spec "
                     "would be pinning a branch LAYOUT rather than the field).",
    },
    # =====================================================================
    # ADMISSIBILITY — REBUILT by the first audit (the original case was
    # `module = _BASE`, the frozen file verbatim, a tautology), then REPAIRED
    # AGAIN by the third: the rebuilt version's "instantiated at the concrete
    # headline float" step discharged nothing and its "measured load-bearing"
    # claim was measured wrong. See the `_ADMISS_SCRIPT` comment for the three
    # builds that establish this. Now exhibits the six-clause post-image on BOTH
    # sub-domains, each described by hypothesis rather than by a literal, with a
    # falsified control per sub-domain proving each half load-bearing.
    # Measured: verifies (exit 0); cap-19 control on the fits image exit 1;
    # cap-19 control on the over-cap image exit 1.
    # =====================================================================
    {
        "id": "admiss-f2p-postimage-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _LOOM, _ADMISS_SCRIPT),
        "rationale": "the input carries no `require`, so 'a normal input is "
                     "admitted' is vacuous; the residual admissibility risk on a "
                     "total carrier is the post-image being UNSATISFIABLE at an "
                     "F2P-shaped input. This case exhibits all six clauses "
                     "SATISFIED on each of the two sub-domains the regression "
                     "tests drive — the fits sub-domain, and the over-cap "
                     "sub-domain WITH an exponent marker where C4's demanded "
                     "content and C1's cap must be RECONCILED through the "
                     "short-suffix fact rather than discharged separately — as "
                     "checked `have`s, before closing the frozen obligation. "
                     "Unlike a bare re-run of the frozen file this FAILS if the "
                     "conjunction is contradictory on either half, which a "
                     "falsified cap control per sub-domain confirms. No literal "
                     "float is named: on an opaque oracle a literal reduces to "
                     "nothing, so a point is named by hypothesis or not at all. "
                     "Else PRECOND/SPEC-UNSATISFIABLE.",
    },
    # =====================================================================
    # UNIQUENESS (C1 upper cap, over-cap NO-EXPONENT branch) — REPAIRED by audit.
    # Replaces `weak-overlong-cap`, whose rival returned an unconditional
    # 21-char list: gold's build then failed by `wp_pure` pattern-not-found for
    # EVERY claim (proved with four forgeries), so it discriminated nothing.
    # This rival keeps gold's branch structure and over-keeps ONE char on the
    # marker-absent branch, so the conditioned witness reduces on both sides and
    # `omega` decides a real length fact.
    # Measured: rival 0, gold 1, probe 1; FLIP (claim gold's cap holds there)
    # gold 0, rival 1.
    # =====================================================================
    {
        "id": "weak-noexp-take21",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _impl("vs", "vs.take 21", _GOLD_EXP)),
        "refinement": "a renderer that emits a 21-character field on the "
                      "marker-absent over-cap branch produces a value field the "
                      "fixed-width record cannot hold — the cap is the whole "
                      "reason the field is trimmed — so the length-bound "
                      "regression it guards would NOT resolve.",
        "rationale": "REJECT from C1 `out.length ≤ 20`: on the over-cap branch "
                     "with no exponent marker the rival keeps 21 characters, one "
                     "past the cap, and the length arithmetic is independent of "
                     "any oracle VALUE. Against gold that branch keeps exactly "
                     "20, so the closing `omega` fails ON THE DECIDED FACT. If it "
                     "verified ⇒ SPEC-TOO-WEAK (the cap unenforced on C3's "
                     "branch). Conditioned witness: rival 0, gold 1, probe 1, and "
                     "the flipped claim verifies on gold and fails on the rival.",
        "witness": _noexp_witness(
            "out.length ≤ 20",
            "  simp only [List.length_take] at hcon\n  omega\n"),
    },
    # =====================================================================
    # UNIQUENESS (C1 upper cap, the UNTRIMMED ECHO) — ADDED by the second audit.
    # The port recorded nagini's `weak-echo-untrimmed` as RE-AIMED into
    # `weak-noexp-take21`, but re-aiming is not porting: nagini's rival never
    # trims AT ALL (it returns the exact rendering whatever its length), whereas
    # take21 trims to a wrong width. Those are different defects — one omits the
    # cap enforcement, the other miscomputes it — and only the second was
    # carried, so the "NO nagini uniqueness rival is dropped" line was true of
    # the id and false of the behaviour. The faithful echo IS expressible here:
    # keep gold's branch structure and echo `vs` on the marker-absent over-cap
    # branch, where `h1 : 20 < length` makes the cap violation immediate.
    #
    # ITS CLOSER WAS REPAIRED BY THE FIFTH AUDIT, for exactly the reason the
    # fourth audit repaired `weak-fit-empty`: the branch conditioning fixed the
    # UNFOLDING and left the DECISION hollow, and the earlier audits' recorded
    # "FLIP gold 0" was measured with a flip that also swapped the CLOSER, so it
    # never tested the closer that shipped. The shipped closer was a bare
    # `omega`, and gold's `hcon` is then `(List.take 20 (shortestField value)).length
    # ≤ 20` — a term `omega` does NOT evaluate, so it enters the constraint set as
    # a FREE atom (the recorded signature names it, `c := ↑(List.take 20
    # (shortestField value)).length`, constrained only by `0 ≤ c ≤ 20`, i.e. by the
    # claim's own bound and nothing about `List.take`). With `c` free, omega
    # reports the set satisfiable no matter WHAT the claim says about it.
    # Established with real builds against the frozen solution, all carrying the
    # SHIPPED bare-`omega` closer:
    #   * the witness's own claim `out.length ≤ 20`   -> gold 1
    #   * the FLIPPED claim `out.length = 21` (asserting gold IS over the cap
    #     there, which is FALSE of gold)               -> gold 1, and its first
    #     error line is BYTE-IDENTICAL to the shipped one minus the `0 ≤ c ≤ 20`
    #     row — the same tactic, the same atoms, the same verdict;
    #   * the NON-REFUTATION `out.length ≤ 0`, which claims the cap is violated
    #     NOWHERE and is satisfied by no impl at all -> RIVAL exit 0 and gold
    #     exit 1, i.e. it clears BOTH halves of the gate's discrimination check.
    # That last build is the proof of hollowness: the gate would have recorded
    # `rejected (witness refutes the rival)` for it. `≤ 0` is refutable on the
    # rival only because `h1 : 20 < length` contradicts it directly — which is a
    # fact about the GUARD, not about the returned field, so the rival's exit 0
    # was carried by the hypothesis rather than by the impl's defect.
    #
    # REPAIRED by giving the closer the one rewrite that makes gold's atom a real
    # length: `simp only [List.length_take]` turns `(List.take 20 vs).length` into
    # `min 20 vs.length`, which `omega` DOES decide. The text is claim-agnostic
    # (a rewrite of the impl's own returned term, mentioning no claim), so the
    # flip and the non-refutation can carry it byte-for-byte — and under it the
    # exits INVERT with the claim on both impls. Measured this audit:
    #   rival 0 · gold 1 · probe 1
    #   FLIPPED claim `out.length = 21`, SAME prefix AND SAME closer:
    #     gold 0, rival 1 — gold's cap is now DECIDED, not left free;
    #   NON-REFUTATION `out.length ≤ 21` with the same closer:
    #     rival 1 AND gold 1 — the forgery no longer clears the rival half, so
    #     the rival's exit 0 is carried by the CLAIM and not by the guard;
    #   `out.length ≤ 0` and `out.length ≤ 19` with the same closer:
    #     both sides exit 0, i.e. both are honestly refuted everywhere, which is
    #     the opposite of the old closer's silent pass.
    # The rival is unchanged: the untrimmed echo is genuinely wrong and the
    # repaired witness refutes it at exit 0.
    # =====================================================================
    {
        "id": "weak-echo-untrimmed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _impl(_GOLD_FIT, "vs", _GOLD_EXP)),
        "refinement": "a renderer that never trims emits the exact rendering at "
                      "whatever length it happens to have, so an over-long value "
                      "produces a field the fixed-width record cannot hold — the "
                      "cap is the entire reason the field is trimmed, and the "
                      "length-bound regression would NOT resolve.",
        "rationale": "REJECT from C1 `out.length ≤ 20`: on the marker-absent "
                     "over-cap branch the rival returns the untrimmed rendering, "
                     "whose length the branch guard states is strictly greater "
                     "than 20. Distinct from weak-noexp-take21, which trims to a "
                     "WRONG width (21): this one omits trimming entirely, the "
                     "defect nagini's own echo rival carried. Against gold the "
                     "branch trims to exactly 20, so the closing `omega` fails on "
                     "the decided length fact — decided because the closer first "
                     "rewrites gold's `(take 20 …).length` to `min 20 …`, which "
                     "`omega` evaluates; without that rewrite the term is a FREE "
                     "atom and gold's exit code tracks nothing (see the case "
                     "header for the three builds that measured it). If it "
                     "verified ⇒ SPEC-TOO-WEAK (the cap unenforced on C3's "
                     "branch). rival 0, gold 1, probe 1; the flipped claim "
                     "carrying the SAME closer verifies on gold (0) and fails on "
                     "the rival (1), and a non-refutation carrying the same closer "
                     "fails on BOTH (1/1).",
        "witness": _noexp_witness(
            "out.length ≤ 20",
            # Claim-agnostic: it rewrites the impl's own returned term, naming no
            # claim, so the flip and the non-refutation carry it byte-for-byte.
            # Load-bearing on the GOLD side — `omega` does not evaluate
            # `(List.take 20 vs).length`, so without this line gold's constraint
            # set holds that length as a free atom and is satisfiable for every
            # claim about it. Under `try` because the RIVAL's `hcon` carries no
            # `List.take` at all (it returns the untrimmed field), so an
            # unguarded rewrite fails there with `simp made no progress` and
            # breaks the half that must succeed — measured, rival exit 1. `try`
            # keeps the one text valid on both sides, which is what makes the
            # flip comparison a comparison of CLAIMS.
            "  try simp only [List.length_take] at hcon\n  omega\n"),
    },
    # =====================================================================
    # UNIQUENESS (C1 lower cap, FIT branch) — REPAIRED by audit. Replaces
    # `weak-empty-cap`, whose rival returned an unconditional `[]` and whose gold
    # build failed by the same claim-independent pattern-not-found. Here the
    # empty field is returned only on the FIT branch, and the witness conditions
    # on the fits guard so `if_pos` fires on gold too.
    #
    # ITS CLOSER WAS REPAIRED A SECOND TIME (fourth audit), because the branch
    # conditioning fixed the UNFOLDING and left the DECISION hollow. The rival
    # and gold both reached a real conditioned goal — `hcon : 1 ≤ [].length` and
    # `hcon : 1 ≤ (shortestField value).length`, printed by `trace_state` on each
    # side — but the closing step was `simp at hcon`, and on gold that is a
    # rewriter looking at an OPAQUE-AXIOM application with nothing to rewrite.
    # Gold's error was ``simp` made no progress`, and the OPPOSITE-CLAIM CONTROL
    # settles what that byte string is worth: the same statement with the `¬`
    # dropped (claiming gold IS non-empty there), carrying the SAME prefix and the
    # SAME closer, fails on gold with the byte-identical error. Gold's exit code
    # did not depend on the claim, so the recorded refutation was never performed
    # — even though the claim is TRUE of gold, which a sibling closing that same
    # goal by `exact shortestField_nonempty value` proves at exit 0. That flip is
    # what the earlier audits recorded as "FLIP gold 0", but it swaps the CLOSER
    # as well as the claim, so it never tested the closer that shipped.
    # REPAIRED by making the closer decide arithmetic instead of rewriting: bring
    # the renderer's non-emptiness axiom in as a linear fact, spell out the one
    # ground length `omega` does not evaluate (measured: `¬ (1 ≤ ([] : List
    # Char).length)` is NOT closed by `omega`, which reports `a := ↑[].length` as
    # a free atom), and let `omega` decide. The closer is then CLAIM-AGNOSTIC
    # TEXT, so the opposite claim can carry it byte-for-byte.
    # Measured (this audit, 14 probe builds, none a no_verdict, ~3s each):
    #   rival 0 · gold 1 · probe 1
    #   gold's signature is now `omega could not prove the goal: a possible
    #   counterexample may satisfy the constraints 1 ≤ a ≤ 20 where
    #   a := ↑(shortestField value).length` — omega reached the spec instance at
    #   gold's OWN returned field and reported the constraint set SATISFIABLE,
    #   i.e. there is no violation to refute on that branch;
    #   OPPOSITE CLAIM, same prefix AND same closer: gold 0, rival 1 — the exit
    #   code now inverts with the claim on both impls;
    #   NON-REFUTATION forgery (`¬ (… 0 ≤ out.length)`, satisfied by every impl)
    #   with the same closer: rival 1 AND gold 1 with the SAME bytes. `hcon` is
    #   then trivial on both sides, so this is also the check that the closer's
    #   own context (`hax`, `hnil`, `hle`) is CONSISTENT and closes nothing by
    #   itself — the rival's exit 0 is carried by the claim, not by the script;
    #   `hnil` is load-bearing rather than decorative: `omega` does not evaluate
    #   `[].length`, so with that line dropped the RIVAL build fails (exit 1).
    # =====================================================================
    {
        "id": "weak-fit-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _impl("([] : List Char)", _GOLD_NOEXP, _GOLD_EXP)),
        "refinement": "a renderer that can emit an empty field writes no digits "
                      "for the value, so the record carries a blank where a "
                      "number is required and the representation regression would "
                      "NOT resolve.",
        "rationale": "REJECT from C1 `1 ≤ out.length`: on the fits branch the "
                     "rival returns the empty field, length 0, below the floor. "
                     "Refuted on the OTHER half of the cap clause from "
                     "weak-noexp-take21 and on a DIFFERENT branch, so both halves "
                     "of C1 are defended on disjoint sub-domains. Against gold "
                     "the branch returns the exact rendering, whose length the "
                     "renderer axiom bounds BELOW by 1, so the closing `omega` "
                     "reports the constraint set `1 ≤ a ≤ 20` over gold's real "
                     "length atom as SATISFIABLE — the floor holds there and "
                     "there is nothing to refute. If it verified ⇒ "
                     "SPEC-TOO-WEAK. Conditioned witness: rival 0, gold 1, "
                     "probe 1; and the OPPOSITE claim carrying the SAME prefix "
                     "and the SAME closer verifies on gold (0) and fails on the "
                     "rival (1), so gold's exit code tracks the claim rather "
                     "than the rewriter's reach.",
        "witness": _fit_witness(
            "1 ≤ out.length",
            # Claim-agnostic closer: the axiom as a linear fact, the one ground
            # length omega does not evaluate, then a decision. The same three
            # lines close the OPPOSITE claim against gold, which is what makes
            # gold's failure here claim-dependent rather than rewriter-inert.
            "  have hax : 1 ≤ (shortestField value).length :=\n"
            "    shortestField_nonempty value\n"
            "  have hnil : ([] : List Char).length = 0 := List.length_nil\n"
            "  omega\n"),
    },
    # =====================================================================
    # UNIQUENESS (C2, the HEADLINE minimality/exact-rendering clause) — REPAIRED
    # by audit. The pre-patch renderer echo. The previous version returned
    # `paddedField value` unconditionally, so gold failed by pattern-not-found
    # for every claim; here the echo sits on the FIT branch and the witness
    # conditions on the fits guard, so `if_pos` fires on gold and `wp_pure`
    # reduces to gold's own `shortestField value` — which `hne` genuinely cannot
    # refute. That is the discrimination.
    # Measured: rival 0, gold 1, probe 1; FLIP (claim gold's fit branch IS the
    # exact rendering, closed by `rfl`) gold 0, rival 1.
    # =====================================================================
    {
        "id": "weak-padded-renderer",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _impl("paddedField value", _GOLD_NOEXP, _GOLD_EXP)),
        "refinement": "the fixed-precision renderer spends more significant "
                      "digits than the number needs (16 where 4 suffice), "
                      "producing a longer field that forces the trailing comment "
                      "to be truncated — the exact regression the headline F2P "
                      "test forbids. A faithful patch keeping that renderer would "
                      "NOT resolve.",
        "rationale": "REJECT from C2 `(shortestField value).length ≤ 20 → out = "
                     "shortestField value`: on the fits branch the rival returns "
                     "the fixed-precision rendering, so under the fits guard the "
                     "clause reduces to an equality of the two renderings, "
                     "refuted by the separation hypothesis. Against gold the same "
                     "reduction yields `shortestField value = shortestField "
                     "value`, which `hne` cannot close — the flip build confirms "
                     "gold's side is DECIDED (it closes by `rfl`). Both binders "
                     "are about opaque terms and jointly satisfiable — this IS "
                     "the discriminator the axiom lane validates. If it verified "
                     "⇒ SPEC-TOO-WEAK (the minimality discriminator missing). "
                     "rival 0, gold 1, probe 1, flip gold 0 / rival 1.",
        "witness": _fit_witness(
            "(shortestField value).length ≤ 20 → out = shortestField value",
            "  exact hne (hcon hle)\n",
            "    (hne : paddedField value ≠ shortestField value) :\n"),
    },
    # =====================================================================
    # UNIQUENESS (C4, over-cap exponent CONTENT) — the first-20 truncation that
    # DROPS the exponent. Ports nagini weak-trunc-first20-drops-exponent.
    # AUDITED AND KEPT AS SHIPPED: this case was already genuine. Its gold-side
    # failure is an `Application type mismatch` whose two printed types differ
    # exactly in the CLAIM, and the flip test settles it — asserting gold IS
    # correct on C4 builds on gold (exit 0) and fails on the rival with
    # `rfl failed: take 20 … is not definitionally equal to …` (exit 1).
    # =====================================================================
    {
        "id": "weak-trunc-drop-exponent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _impl(_GOLD_FIT, _GOLD_NOEXP, "vs.take 20")),
        "refinement": "truncating a scientific-notation value to its first 20 "
                      "characters drops the trailing exponent, yielding a "
                      "different number (a value ≈ -4.6737…E+32 loses its E+32), "
                      "so the over-cap scientific-notation tests would NOT "
                      "resolve.",
        "rationale": "REJECT from C4 (over-cap, exponent present): the spec "
                     "requires `take (20-(len-idx)) ++ drop idx` (significand "
                     "shortened, whole exponent kept) but the rival returns "
                     "`take 20` (exponent dropped). Both are length 20, so the "
                     "witness conditions on the two branch guards and on the "
                     "content separation of the two trims. Against gold the "
                     "branch returns the spec RHS, so the clause holds and `h3` "
                     "cannot close it. Satisfies C3 — a genuine partial-domain "
                     "break. If it verified ⇒ SPEC-TOO-WEAK. rival 0, gold 1, "
                     "probe 1, flip gold 0 / rival 1.",
        "witness": _exp_witness(
            _C4_POST, "  exact h3 (hcon h1 h2)\n",
            f"    (h3 : (shortestField value).take 20 ≠ {_TAKE_KEPT}"
            f" ++ {_DROP_SUF}) :\n"),
    },
    # =====================================================================
    # UNIQUENESS (C1 upper cap, over-cap EXPONENT branch) — the significand
    # over-keep. Ports nagini weak-offbyone-keep-plus1.
    #
    # ITS CLOSER WAS REPAIRED BY THE FIFTH AUDIT. The rival was always genuine;
    # the WITNESS was not, and for the third instance of the one defect this
    # battery keeps re-growing: a closer that reaches a real conditioned goal on
    # both sides and then decides it on only one. The shipped closer normalised
    # the length algebra and called `omega`, and gold's `hcon` after that rewrite
    # is `min (20 - (len - idx)) len + (len - idx) ≤ 20`, whose truth needs the
    # SHORT-SUFFIX axiom (`len - idx ≤ 5`, hence `20 - (len - idx) ≤ len`). The
    # closer never introduced it, so on gold's side `omega` was reasoning without
    # the one fact that decides the goal.
    #
    # The earlier audits recorded "flip gold 0 / rival 1" for this case, but that
    # flip was closed "from the short-suffix axiom" — i.e. the flip's closer was
    # EQUIPPED with a `have` the shipped closer does not carry, so it measured a
    # different script. Re-measured this audit with the SHIPPED closer held fixed
    # on both sides:
    #   * the witness's own claim `out.length ≤ 20`  -> gold 1
    #   * the FLIPPED claim `out.length = 21`        -> gold 1 as well, and
    #     `20 < out.length` -> gold 1, and the non-refutation `out.length ≤ 21`
    #     -> gold 1. Four different claims, one exit code: gold's failure said
    #     only "this closer cannot decide anything here".
    #   * `out.length ≤ 19`, which is FALSE of gold and of the rival -> both
    #     sides exit 0, so the script's reach, not the claim, was doing the work.
    #
    # REPAIRED by putting the missing axiom instance INTO the closer, before the
    # arithmetic. It is claim-agnostic text — two `have`s over the witness's own
    # branch hypothesis `h2`, mentioning no claim — so the flip carries it
    # byte-for-byte, and under it the exits invert. Measured this audit:
    #   rival 0 · gold 1 · probe 1
    #   FLIPPED claim `out.length = 21`, SAME prefix AND SAME closer:
    #     gold 0, rival 1;
    #   NON-REFUTATION `out.length ≤ 21` with the same closer: gold 1, rival 1.
    # Gold's failure is now `omega` over a constraint set that CONTAINS the
    # suffix bound, i.e. a decision on gold's own field length.
    # =====================================================================
    {
        "id": "weak-overcap-keep-plus1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _impl(_GOLD_FIT, _GOLD_NOEXP,
                              "vs.take (21 - (n - idx)) ++ vs.drop idx")),
        "refinement": "a renderer that keeps one extra significand character on "
                      "the over-cap exponent branch emits a 21-character field, "
                      "one past the fixed-width cap — the record cannot hold it, "
                      "so the length-bound regression it guards would NOT resolve.",
        "rationale": "REJECT from C1 `out.length ≤ 20`: on the over-cap exponent "
                     "branch the kept significand prefix plus the whole exponent "
                     "suffix is (21-(n-idx))+(n-idx) = 21 characters, one over the "
                     "cap, independently of any oracle value. Same cap half as "
                     "weak-noexp-take21 but on the branch WITH an exponent. "
                     "Against gold the branch has length exactly 20, so the "
                     "closing `omega` fails on the decided arithmetic — decided "
                     "because the closer FIRST brings in the short-suffix axiom at "
                     "the witness's own branch point; without it gold's goal needs "
                     "a fact the closer never had and its exit code tracked the "
                     "script's reach rather than the claim (see the case header for "
                     "the four builds that measured it). If it verified ⇒ "
                     "SPEC-TOO-WEAK. rival 0, gold 1, probe 1; the flipped claim "
                     "carrying the SAME closer verifies on gold (0) and fails on "
                     "the rival (1), and a non-refutation carrying it fails on "
                     "BOTH (1/1).",
        "witness": _exp_witness(
            "out.length ≤ 20",
            # Claim-agnostic: two axiom instances at the witness's own branch
            # hypothesis `h2`, naming no claim, so the flip carries them
            # byte-for-byte. Load-bearing on the GOLD side — gold's normalised
            # goal is `min (20 - (len - idx)) len + (len - idx) ≤ 20`, which is
            # decidable only once `len - idx ≤ 5` is in the context.
            "  have hE := eIndex_eq_E (shortestField value) h2\n"
            "  have hsuf := shortestField_suffix_short value"
            " (eIndex (shortestField value)) h2 hE\n"
            "  simp only [List.length_append, List.length_take,"
            " List.length_drop] at hcon\n  omega\n"),
    },
    # =====================================================================
    # UNIQUENESS (C3 CONTENT) — ADDED by audit. The shipped battery's footer
    # claimed C3's content was "defended structurally by weak-overcap-keep-plus1
    # sharing the over-cap machinery" and that a dedicated C3 content rival was
    # "built and seen to discriminate but omitted as redundant". Neither holds:
    # weak-overcap-keep-plus1 attacks C1's LENGTH on the OTHER branch and no
    # case pinned C3's CONTENT at all, so a rival that trims the marker-absent
    # over-cap branch to the LAST 20 characters (length 20, so C1 holds; C2 and
    # C4 untouched) was unattacked. Built here; it is correctly rejected.
    # Measured: rival 0, gold 1, probe 1; FLIP gold 0, rival 1.
    # =====================================================================
    {
        "id": "weak-noexp-last20",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _impl(_GOLD_FIT, "vs.drop (n - 20)", _GOLD_EXP)),
        "refinement": "keeping the LAST 20 characters of an over-long field with "
                      "no exponent marker discards the leading digits and the "
                      "sign, so the field denotes a completely different number "
                      "while still filling the fixed width — the representation "
                      "regression would NOT resolve, and a length-only cap check "
                      "would never notice.",
        "rationale": "REJECT from C3 (over-cap, no exponent marker): the spec "
                     "requires the FIRST 20 characters of the exact rendering, "
                     "the rival returns the LAST 20. Both have length 20, so C1 "
                     "cannot separate them and the witness conditions on the two "
                     "branch guards plus the content separation `h3`. This is the "
                     "clause NO shipped case reached: the battery attacked C1 on "
                     "both branches, C2 on the fit branch and C4's content, but "
                     "left C3's content unpinned. Against gold the branch returns "
                     "the spec RHS so `h3` cannot close it (the flip build closes "
                     "gold by `rfl`). If it verified ⇒ SPEC-TOO-WEAK. rival 0, "
                     "gold 1, probe 1, flip gold 0 / rival 1.",
        "witness": _noexp_witness(
            _C3_POST, "  exact h3 (hcon h1 h2)\n",
            "    (h3 : (shortestField value).drop ((shortestField value).length - 20)\n"
            "            ≠ (shortestField value).take 20) :\n"),
    },
    # =====================================================================
    # UNIQUENESS (C4 CONTENT, near-miss) — ADDED by audit. A far tighter miss
    # than weak-trunc-drop-exponent: the exponent suffix IS kept, but starting
    # one character late (`drop (idx+1)`), so the marker itself is swallowed and
    # the field reads as a bare digit run appended to the significand. Aimed at
    # the boundary the nagini battery never probed, since its two C4 rivals were
    # a whole-suffix drop and a length break.
    # Measured: rival 0, gold 1, probe 1; FLIP gold 0, rival 1.
    # =====================================================================
    {
        "id": "weak-exp-drop-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _impl(_GOLD_FIT, _GOLD_NOEXP,
                              "vs.take (20 - (n - idx)) ++ vs.drop (idx + 1)")),
        "refinement": "keeping the exponent's DIGITS but dropping the marker "
                      "character itself splices the exponent onto the significand "
                      "as ordinary digits, so the field denotes a wildly "
                      "different number while keeping both the cap and the "
                      "exponent-preserving shape — the scientific-notation "
                      "over-cap tests would NOT resolve.",
        "rationale": "REJECT from C4: the spec pins the suffix as `drop idx` "
                     "(from the marker inclusive); the rival takes `drop (idx+1)` "
                     "and loses the marker. A one-character near-miss on the "
                     "clause's index arithmetic, which the whole-suffix-drop "
                     "rival cannot reach — it also makes the field one character "
                     "SHORTER, so it still satisfies C1 and only C4's content "
                     "separates it. Against gold the branch returns the spec RHS, "
                     "so `h3` cannot close it. If it verified ⇒ SPEC-TOO-WEAK "
                     "(the suffix boundary unpinned). rival 0, gold 1, probe 1, "
                     "flip gold 0 / rival 1.",
        "witness": _exp_witness(
            _C4_POST, "  exact h3 (hcon h1 h2)\n",
            f"    (h3 : {_TAKE_KEPT} ++ (shortestField value).drop"
            " (eIndex (shortestField value) + 1)\n"
            f"            ≠ {_TAKE_KEPT} ++ {_DROP_SUF}) :\n"),
    },
    # =====================================================================
    # UNIQUENESS (C2, the SIGN of the rendered number) — ADDED by the fifth audit.
    # This is nagini's `weak-dropsign-at-zero`, the ONE nagini uniqueness rival
    # this port never carried. It was absent from the case list AND from the
    # accounting table below, while that table's summary line asserted "NO nagini
    # uniqueness rival is dropped" — an omission recorded nowhere, which is worse
    # than one recorded with a reason, because nothing in the artifact prompted
    # anybody to check whether it was expressible. It is.
    #
    # The nagini original normalises the sign away at a zero value, reachable there
    # because that model carries the sign as a separate flag. This carrier has no
    # such flag: the sole input is the `Float` itself, so the analogue is a rival
    # that renders a SIGN-NORMALISED value, `shortestField (value + 0.0)`. On this
    # carrier `+ 0.0` is the identity on every float EXCEPT negative zero, which it
    # maps to positive zero — so the rival agrees with gold everywhere but at one
    # input, where it emits the unsigned field and the number's sign is lost from
    # the record. A genuinely wrong impl on a one-point sub-domain, and the
    # narrowest partial-domain break in this battery.
    # Measured: module exit 1 (the frozen script's own `shortestField_minimal
    # value` no longer types against the normalised carrier), witness rival 0,
    # gold 1, probe 1; FLIP (claim gold's fit branch IS the sign-normalised
    # rendering) gold 0, rival 1. Gold's failure is an `Application type mismatch`
    # whose two printed types differ exactly in the claim —
    # `shortestField value = shortestField value` against
    # `shortestField (value + 0.0) = shortestField value` — so the reduction
    # happened and the claim is what it could not close.
    # =====================================================================
    {
        "id": "weak-dropsign-normalized",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _impl("shortestField (value + 0.0)",
                              _GOLD_NOEXP, _GOLD_EXP)),
        "refinement": "a renderer that normalises the sign away emits the "
                      "unsigned field for a negative zero, so the record carries "
                      "a number whose sign has been silently dropped — the "
                      "renderer's contract is to reproduce the number exactly, "
                      "sign included, so the representation regression would NOT "
                      "resolve at that value.",
        "rationale": "REJECT from C2 `(shortestField value).length ≤ 20 → out = "
                     "shortestField value`: on the fits branch the rival renders "
                     "the sign-normalised value rather than the value, so under "
                     "the fits guard the clause reduces to an equality of the two "
                     "renderings, refuted by the separation hypothesis. Ports "
                     "nagini's `weak-dropsign-at-zero`, the one nagini uniqueness "
                     "rival this port had dropped, re-aimed onto the only carrier "
                     "where the distinction survives: there is no sign flag here, "
                     "so the normalisation is expressed on the VALUE. Distinct "
                     "from weak-padded-renderer, which breaks the same clause by "
                     "spending too many digits on EVERY input; this one agrees "
                     "with gold at every float but one, which is why no length or "
                     "digit-count clause can see it. Against gold the same "
                     "reduction yields `shortestField value = shortestField "
                     "value`, which `hne` cannot close, and the flip build "
                     "confirms gold's side is DECIDED (it closes there). If it "
                     "verified ⇒ SPEC-TOO-WEAK (the rendered number's sign "
                     "unpinned). rival 0, gold 1, probe 1, flip gold 0 / rival 1.",
        "witness": _fit_witness(
            "(shortestField value).length ≤ 20 → out = shortestField value",
            "  exact hne (hcon hle)\n",
            "    (hne : shortestField (value + 0.0) ≠ shortestField value) :\n"),
    },
    # =====================================================================
    # UNIQUENESS (C1 upper cap, the TRIM THRESHOLD) — ADDED by the third audit,
    # on an axis nothing in the battery reached. Every other rival here keeps
    # gold's two guards byte-identical and varies a RETURNED EXPRESSION; the
    # coverage reporter counts that as one binder varying and says `ok`, but the
    # variation is all on one axis. This rival is the mirror image: every returned
    # expression is byte-identical to gold's and only the fits GUARD moves, from
    # `n ≤ 20` to `n ≤ 21`. So the trim THRESHOLD — which length starts trimming
    # at, as opposed to what the trim computes — was unpinned by every shipped
    # case, and a spec that fixed only the trim expressions while leaving the
    # threshold free would have passed the whole battery.
    #
    # It is a genuinely wrong impl, not a reshape: at length exactly 21 it takes
    # the fits branch and echoes the whole 21-character field, one past the cap.
    # (The mirror direction, `n ≤ 19`, is CORRECT — at length exactly 20 both
    # over-cap branches degenerate to the identity on the field — and the audit
    # proved it against the frozen spec as an attack-E probe, so this axis carries
    # a hole in one direction only.)
    #
    # The witness needs the guard-disagreement technique, since the two impls take
    # DIFFERENT branches in the window 20 < length ≤ 21; see
    # `_guard_window_witness`. Measured: rival 0, gold 1, probe 1; FLIP (claim the
    # cap HOLDS in that window) gold 0, rival 1. Gold's failure is `omega could not
    # prove the goal` over the real length atoms, and a type-REVEAL build separates
    # the sides concretely — `hcon` is `(List.take 20 …).length ≤ 20` on gold
    # versus `(shortestField value).length ≤ 20` on the rival, neither reduced to
    # `True`, so no gold-side obligation was silently proven away.
    # =====================================================================
    {
        "id": "weak-guard-threshold-off",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL,
                        _IMPL.replace("if n ≤ 20 then", "if n ≤ 21 then")),
        "refinement": "a renderer that starts trimming one character too late "
                      "emits a 21-character field for any value whose exact "
                      "rendering is exactly 21 long — the fixed-width record "
                      "cannot hold it, so the length-bound regression the cap "
                      "guards would NOT resolve, even though every trim this "
                      "renderer does compute is correct.",
        "rationale": "REJECT from C1 `out.length ≤ 20`: the rival's trim "
                      "expressions are byte-identical to the frozen ones and only "
                      "the threshold moves, so in the window where the guards "
                      "disagree it echoes the exact rendering at length 21, one "
                      "past the cap. Distinct in KIND from every other rival here, "
                      "which fixes the threshold and breaks a trim: this fixes "
                      "the trims and breaks the threshold, so it is the case that "
                      "shows the spec pins WHEN to trim and not merely WHAT the "
                      "trim computes. If it verified ⇒ SPEC-TOO-WEAK (the trim "
                      "threshold unpinned). rival 0, gold 1, probe 1, flip gold 0 "
                      "/ rival 1.",
        "witness": _guard_window_witness(
            "out.length ≤ 20",
            "  try simp only [List.length_take] at hcon\n  omega\n"),
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING (revised by the audit).
#
#   nagini case                        -> here
#   -----------------------------------------------------------------------
#   pos-control-hoist-decl             -> pos-control-hoist-decl        PORTED
#   admiss-gold-total                  -> admiss-f2p-postimage-satisfiable
#                                                                       REBUILT
#   weak-echo-untrimmed                -> weak-echo-untrimmed           PORTED
#                                         (+ weak-noexp-take21          RE-AIMED)
#   weak-padded-renderer               -> weak-padded-renderer          PORTED
#   weak-trunc-first20-drops-exponent  -> weak-trunc-drop-exponent      PORTED
#   weak-offbyone-keep-plus1           -> weak-overcap-keep-plus1       RE-AIMED
#   weak-dropsign-at-zero              -> weak-dropsign-normalized      RE-AIMED
#                                         (fifth audit; before it, this rival was
#                                          carried NOWHERE and this table wrongly
#                                          asserted no uniqueness rival was dropped)
#   (no sibling)                       -> weak-fit-empty                ADDED
#   (no sibling)                       -> pos-control-unify-overcap     ADDED
#   (no sibling)                       -> weak-noexp-last20             ADDED
#   (no sibling)                       -> weak-exp-drop-marker          ADDED
#   (no sibling)                       -> weak-guard-threshold-off      ADDED
#
# 4 ported, 2 re-aimed, 1 rebuilt (twice), 6 added = 13 cases (2 soundness,
# 1 admissibility, 10 uniqueness). As of the FIFTH audit no nagini uniqueness
# rival is dropped — before it, one WAS: `weak-dropsign-at-zero` appeared neither
# in the case list nor in this table, while this very paragraph asserted that none
# was dropped. It is now carried as `weak-dropsign-normalized` (see that case's
# header for the six builds); the earlier claim was false and is withdrawn.
# The echo also ships as itself alongside the re-aimed take21, so every nagini
# rival's own defect is carried rather than substituted for a neighbouring one.
#
# FIFTH AUDIT (independent re-derivation; 88 builds, none a no_verdict, ~4s each).
# Every one of the 12 shipped cases was rebuilt from the real verifier and every
# recorded outcome and `gold_signature` reproduced byte-for-byte. Attack A:
# `spec_view` identical to the frozen file for all 12, `variant_problems` empty,
# and every case's diff confined to the impl region or the `prove_correct` body —
# checked by diffing each `module` against the frozen file, not by trusting the
# gate's own scope check.
#
# TWO CASES FAILED THE STRICT FLIP CONTROL and were repaired: see the two case
# headers, and the corrected paragraph above about why the "signature is an
# `omega`, therefore a decision" reasoning does not hold. In both the RIVAL was
# genuinely wrong and was left untouched; only the closer changed, and in both
# the repaired closer is claim-agnostic text so the flip carries it verbatim.
#
# The generalisable lesson, since this is the third consecutive audit to repair
# one instance of it: a conditioned witness has TWO independent failure modes and
# fixing the first does not touch the second. Branch conditioning fixes the
# UNFOLDING (both sides reach a real goal about their own returned field); it says
# nothing about the DECISION (the closer actually settling that goal on each
# side). A closer decides only if, for every atom the claim constrains, it has
# either rewritten that atom to something the arithmetic evaluates or supplied the
# axiom that bounds it. `weak-fit-empty` failed this with `simp` on an opaque
# application (fourth audit), `weak-echo-untrimmed` with `omega` on an
# un-rewritten `List.take` length, `weak-overcap-keep-plus1` with `omega` missing
# the short-suffix bound. All three signatures LOOKED like decisions; the only
# test that separates them is holding the closer fixed and flipping the claim.
#
# ALSO CORRECTED, both prose defects rather than case defects:
#   * The DIVERGENCE paragraph's stated reason for the class being unshippable
#     was measurably false (it said the rival's `method` declaration does not
#     compile in the witness file; it compiles fine, since the `decreasing`
#     obligation lives in the stripped `prove_correct`). The real obstacle was
#     re-derived with five builds and is the `forIn Lean.Loop.mk` shape
#     `pbt.py`'s own screen names; the paragraph now says that, with the four
#     witness shapes that fail on the RIVAL and the `trace_state` term.
#   * The claim that the other seven reject cases "pass the strict control by
#     construction" is withdrawn as false; five of them do, and this audit ran
#     each one rather than reasoning about its signature.
#
# ATTACK D re-run by the fifth audit, five NEW wrong impls beyond every shipped
# and previously-probed one, all REJECTED (exit 1), so no spec hole:
#   * the fit branch space-PADDED out to the cap (`vs ++ replicate (20-n) ' '`) —
#     length legal, C2 content broken by trailing blanks rather than by digits;
#   * the two over-cap RETURNS SWAPPED between the branches — each branch returns
#     the OTHER branch's correct trim, so both C3 and C4 break while every
#     expression in the impl is one the frozen impl also contains;
#   * the marker-absent branch emptied via `vs.take 0` (C1 lower + C3 content, and
#     spelled as a trim rather than as a literal `[]`);
#   * the marker-present branch keeping only the first 4 characters of the
#     exponent suffix (`(vs.drop idx).take 4`) — a near-miss that keeps the marker
#     and shortens the suffix, the mirror of `weak-exp-drop-marker`;
#   * the marker-detection GUARD off by one (`idx + 1 ≥ n`) — the second guard
#     axis, after `weak-guard-threshold-off` covered the first.
# ATTACK E re-run, one NEW correct reshape, PROVEN (exit 0):
#   * the fit branch returning `vs.take n`, i.e. the field trimmed to its own
#     length. Equal to `vs` only through `List.take_length`, which is not
#     definitional and which the frozen bullet script does not contain — measured:
#     with the by-shape closer alone it FAILS (exit 1, `introN failed` on three
#     goals whose `out` is still `List.take (shortestField value).length …`), and
#     it closes at exit 0 once the closer rewrites `List.take_length` per goal. So
#     the spec admits it and no faithful correct impl is refused. Left as a probe:
#     `pos-control-unify-overcap` already carries the positive lane's reshape
#     burden.
# ATTACK F (omissions) found ONE nagini uniqueness rival carried nowhere and
# recorded nowhere: `weak-dropsign-at-zero`. It was not marked inexpressible — it
# was simply absent, with the accounting table asserting the opposite. It IS
# expressible on this carrier, and is now shipped as `weak-dropsign-normalized`
# (rival 0, gold 1, probe 1, flip gold 0 / rival 1; gold's error prints the two
# renderer applications side by side and they differ exactly in the claim). The
# lesson: an accounting table is not evidence, and this one was checked against
# the sibling's case list for the first time by this audit.
#
# The two ADMISSIBILITY falsified controls were re-run independently and both
# still fail (cap 19 on the fits image: exit 1; cap 19 on the over-cap image:
# exit 1), so both halves of that case remain load-bearing.
#
# FOURTH AUDIT (one case; 14 probe builds, none a no_verdict). Scope: whether each
# reject case's GOLD-side failure depends on what the witness CLAIMS. The test is
# the opposite-claim control done STRICTLY — the `¬` dropped and the SAME tactic
# prefix AND the SAME closing step retained — because a flip that also swaps the
# closer measures the new closer, not the shipped one, and that is how the three
# earlier audits' "FLIP gold 0" lines passed a hollow closer through.
#
# One case failed the strict control: `weak-fit-empty`. Its gold-side signature
# was ``simp` made no progress`, and the negated claim carrying the same script
# produced that error byte-for-byte, so gold's exit code carried no information
# about the claim: `simp at hcon` was facing `1 ≤ (shortestField value).length`,
# an application of an `axiom`-declared callee that the rewriter has no rule for,
# and it would have reported the same thing for a TRUE claim, a FALSE claim, or a
# tautology. Repaired in place (see the case's own header for the closer, the
# byte strings and the four builds): the closer now hands `omega` the renderer's
# non-emptiness axiom plus the one ground length omega does not evaluate, and it
# DECIDES — gold prints the satisfiable constraint set over its own length atom,
# and the opposite claim carrying the identical closer verifies on gold at exit 0
# while failing on the rival at exit 1. No rival was changed: the empty-field
# rival is genuinely wrong, and it is refuted at exit 0 by the repaired witness.
#
# The other seven reject cases were declared to "pass the strict control by
# construction" and were not re-opened, on the reasoning that an `omega could not
# prove the goal` signature is a decision on gold's own values. THE FIFTH AUDIT
# FOUND THAT REASONING FALSE FOR TWO OF THEM, and the false step is worth naming
# because it is the same step three audits in a row took: an `omega` signature is
# a decision only if every atom the claim is about is one omega EVALUATES. When
# the claim's subject enters omega's constraint set as a FREE atom — because the
# closer never rewrote it to arithmetic (`weak-echo-untrimmed`: `(List.take 20
# …).length`) or never supplied the axiom that bounds it
# (`weak-overcap-keep-plus1`: the short-suffix fact) — the set is satisfiable for
# EVERY claim about that atom, exactly as `simp` made no progress was for every
# claim in the fourth audit's case. Reading the signature's tactic name is not
# the test; holding the closer FIXED and flipping only the claim is. Both were
# repaired in place (see each case's header for the builds) and neither rival was
# touched: both are genuinely wrong impls, refuted at exit 0 by the repaired
# witnesses. That leaves five reject cases whose strict control this audit ran
# and confirmed: four `Application type mismatch` cases, whose type-REVEAL builds
# print a DISTINCT concrete type per side and never `True`, and
# `weak-guard-threshold-off`, whose flip inverts under its shipped closer.
#
# THIRD AUDIT (independent re-derivation; 60 builds). Every one of the 11 shipped
# cases was rebuilt from the real verifier and every recorded outcome and
# `gold_signature` reproduced byte-for-byte. Attack A: `spec_view` identical to
# the frozen file for all 11, the six `ensures` lines and both headers
# byte-identical, `variant_problems` empty, and every case's diff confined to the
# impl region or the `prove_correct` body. Attack B' was re-run independently on
# all EIGHT reject cases (none has a plain-evaluation signature, so all eight
# required it): each flip pair inverts both exits (gold 0, rival 1), and a
# type-REVEAL build on each side prints a distinct concrete type for `hcon` —
# never `True` — so no gold-side obligation is silently proven away. A
# non-refutation forgery (`¬ (0 ≤ out.length)`, false of every impl) was also
# built on both sides of weak-fit-empty and fails IDENTICALLY on each, confirming
# the conditioned-witness technique is what carries the information rather than
# the `¬`.
#
# WHAT THE THIRD AUDIT CHANGED.
#
# (c) The ADMISSIBILITY case was repaired a SECOND time. The second audit had
#     replaced its universally-quantified `have` with an INSTANTIATION at a
#     concrete float and recorded that step as "measured load-bearing". It is
#     not: the lemma's body is an implication guarded by the fits condition, so
#     applying it to a float discharges nothing, and the case still verifies with
#     the float replaced by one whose real rendering is 22 code points (the WRONG
#     sub-domain), by `0.0`, or by `value` itself. The guard cannot be discharged
#     at a literal here at all — on an opaque oracle `shortestField <lit>` does
#     not reduce, measured as `rfl failed: (shortestField 9125e-6).length is not
#     definitionally equal to 20`. The concrete-float framing is therefore DROPPED
#     rather than patched, and the case now exhibits the post-image on the
#     over-cap-with-marker sub-domain as well — the one place in this spec where
#     satisfiability is a real question, since C4's demanded content must be
#     reconciled with C1's cap through the short-suffix fact. A falsified cap
#     control per sub-domain (19 instead of 20) fails on each half, which is what
#     makes both halves load-bearing rather than decorative.
#
# (d) `weak-guard-threshold-off` was ADDED, closing a whole AXIS the battery
#     missed. All eight prior rivals keep gold's two guards byte-identical and
#     vary a returned expression, so the trim THRESHOLD — which length starts
#     trimming at — was pinned by nothing, and a spec fixing only the trim
#     expressions would have passed the entire battery. The coverage reporter said
#     `ok` throughout, which is exactly the advisory-only limit the instructions
#     warn about: one binder varying across eight spellings of one axis.
#
# SECOND AUDIT (independent re-derivation). All 10 shipped cases were rebuilt
# from the real verifier; every recorded outcome and every `gold_signature`
# reproduced byte-for-byte. Attack B' (forgery) was run on all seven reject
# cases — none of their signatures is a plain evaluation, so all seven required
# it — and in every case the flipped claim inverts BOTH exits (gold 0, rival 1),
# so gold's exit code tracks the claim rather than a tactic mismatch. The four
# signatures that are application/type mismatches were additionally settled by a
# type-REVEAL build (`exact (hcon : Nat)`) on each side: `hcon`'s real type
# differs exactly in the impl's returned field —
#   fit-empty         gold `1 ≤ (shortestField value).length` / rival `1 ≤ [].length`
#   noexp-take21      gold `(take 20 …).length ≤ 20`          / rival `(take 21 …).length ≤ 20`
#   overcap-keep-plus1 gold `(take (20-…) ++ drop …).length ≤ 20` / rival `(take (21-…) ++ …)`
#   padded-renderer   gold `shortestField v = shortestField v` / rival `paddedField v = shortestField v`
# — none reduced to `True`, i.e. no gold-side obligation was silently proven
# away. The docstring's TRAP narrative was also re-derived rather than trusted:
# an unconditional-return rival with an unconditioned witness reproduces the
# claimed hollowness, including the non-refutation `out.length ≤ 21` clearing
# both halves of the gate's check (rival 0, gold 1). The narrative is accurate.
#
# WHAT THE SECOND AUDIT CHANGED.
#
# (a) The ADMISSIBILITY case's prose named a concrete point ("the headline
#     regression value renders in 8 code points") that its `have` never reached:
#     the lemma was universally quantified over the fits sub-domain, and on an
#     opaque carrier a ∀-statement exhibits satisfiability at no named input at
#     all. That is a rationale claiming a sub-domain the manifest did not
#     demonstrate. Repaired by INSTANTIATING the lemma at that concrete float
#     before the `clear`. Measured load-bearing: the instantiated case verifies
#     (exit 0) and a variant whose instantiation is falsified (`2 ≤ length` drawn
#     from the same projection) fails (exit 1).
#
# (b) `weak-echo-untrimmed` was recorded RE-AIMED but its defect — never trimming
#     at all — was not carried by the case it was re-aimed into, which trims to a
#     wrong width instead. Landed as its own case above with the four required
#     builds. The accounting line is corrected accordingly.
#
# Nothing else was changed: the other nine cases each earn their outcome on
# rebuilt evidence.
#
# WHAT THE AUDIT CHANGED, AND WHY.
#
# Three shipped reject cases (`weak-overlong-cap`, `weak-empty-cap`, and the
# earlier `weak-padded-renderer`) were HOLLOW. Each used a rival whose impl
# region was collapsed to a single unconditional `return <concrete>`. On such a
# rival `formatFloatField` unfolds to a bare `pure`, so the witness's
# `rw [wp_pure]` fires; against GOLD, whose body is a nested `if` over opaque
# guards, that rewrite cannot fire at all. Gold's build therefore failed with
# `Did not find an occurrence of the pattern wp (pure ?x) ?post` — an UNFOLDING
# failure that never reaches the claim.
#
# Established with real builds, not by reading the error:
#   * the witness's own claim              -> gold exit 1, that error
#   * the claim with `¬` DROPPED (gold IS correct there) -> gold exit 1, SAME
#     first error line, byte for byte
#   * `¬ (… 0 ≤ out.length)`, false of every impl        -> gold exit 1, same
#   * a NON-refutation asserting the rival merely SATISFIES `out.length ≤ 21`
#     -> RIVAL exit 0, gold exit 1, same error
# The last one is the proof of hollowness: it claims nothing is wrong anywhere,
# yet it clears both halves of the gate's discrimination check, so the gate would
# have recorded `rejected (witness refutes the rival)` for it. Gold's exit code
# carried no information about the claim on any of the three cases.
#
# The repair, applied to all three: keep gold's BRANCH STRUCTURE in the rival and
# diverge only inside one branch, then have the witness condition on that
# branch's guard so `if_pos`/`if_neg` selects the branch on BOTH sides. `wp_pure`
# then fires on both and the closing step decides the claim on each. Verified by
# a FLIP build per case — the same statement with `¬` dropped now VERIFIES
# against gold (exit 0) and FAILS against the rival (exit 1), so gold's exit code
# tracks the claim.
#
# The other two shipped reject cases were already genuine and are kept verbatim.
# `weak-trunc-drop-exponent` fails on gold with an `Application type mismatch`
# whose two printed types differ exactly in the claim; `weak-overcap-keep-plus1`
# fails with `omega` over the real length atoms. Both were confirmed by the same
# flip test (gold 0 / rival 1), so both are refutations and not tactic
# mismatches.
#
# `admiss-gold-total` was `module = _BASE`: the frozen file verbatim, which the
# gate had already built. It could not fail for any spec reason, so it attested
# to nothing. Rebuilt as a real probe of the direction this lane exists to test —
# the post-image's SATISFIABILITY at an F2P-shaped input, discharged by
# evaluation as a `have` before the frozen obligation is closed verbatim.
#
# Two footer claims were FALSE and are withdrawn. (a) "C3's content is defended
# structurally by weak-overcap-keep-plus1 sharing the over-cap machinery" — that
# case attacks C1's LENGTH on the exponent branch and says nothing about C3's
# content; the gap is now closed by `weak-noexp-last20`. (b) "a dedicated C3
# content rival was built and seen to discriminate but omitted as redundant" —
# nothing in the artifact demonstrates that, so the claim is dropped rather than
# repeated.
#
# CLAUSE COVERAGE, as demonstrated rather than asserted.
#   C1 upper: weak-echo-untrimmed (no trim at all, marker-absent branch),
#             weak-noexp-take21 (trimmed to the wrong width, same branch),
#             weak-overcap-keep-plus1 (marker-present branch)
#   C1 lower: weak-fit-empty (fit branch)
#   C2:       weak-padded-renderer (fit branch content; its round-trip and
#             sig-count siblings demand the same `out = shortestField value`
#             content on that branch, so they fall with it)
#   C3:       weak-noexp-last20 (content, at equal length)
#   C4:       weak-trunc-drop-exponent (whole suffix dropped),
#             weak-exp-drop-marker (suffix kept but the marker swallowed — a
#             one-character near-miss on the index arithmetic)
#   THRESHOLD: weak-guard-threshold-off (added by the third audit). The eight
#             rivals above pin WHAT each branch returns; this one pins WHEN the
#             trim starts, by keeping every trim expression byte-identical and
#             moving only the fits guard. Without it the trim threshold was
#             unpinned by the whole battery.
#   All three branches of the impl are attacked, and the fit / over-cap-no-marker
#   / over-cap-with-marker sub-domains each carry at least one rival whose
#   witness was confirmed by a flip build. Both AXES are attacked too — the
#   returned expressions and the guards — which is the distinction the coverage
#   reporter's single "binder varies" count cannot see.
#
# SPEC PROBES RUN BY THE AUDIT, no hole found.
#   D (SPEC-TOO-WEAK): three NEW wrong impls beyond the ported set —
#     last-20 trim (C3 content), exponent-marker swallow (C4 near-miss), and a
#     reversed exact rendering on the fit branch. All three were REJECTED by the
#     frozen spec; the first two are shipped above as cases.
#   E (SPEC-TOO-STRONG): two NEW correct reshapes — the over-cap branches
#     unified, and the fits guard inverted to `20 < n`. BOTH were proven against
#     the frozen spec (exit 0), so no faithful correct impl is refused. The
#     unified one is shipped above as `pos-control-unify-overcap`.
#
# SPEC PROBES RUN BY THE SECOND AUDIT, no hole found. Eight NEW impls beyond the
# shipped set, all built against the frozen spec:
#   D (SPEC-TOO-WEAK), five wrong impls, all REJECTED (exit 1) —
#     * the untrimmed echo on the marker-absent branch (now shipped as a case);
#     * the fit branch reversed (`vs.reverse`), the footer's claimed third probe,
#       re-derived rather than taken on trust;
#     * the marker-absent branch trimmed to 19 (a C3 content break that KEEPS
#       C1, so only content can separate it);
#     * the marker-present branch under-keeping one significand character
#       (`19 - (n - idx)`), the mirror of the shipped over-keep;
#     * the marker-present branch with its two halves SWAPPED (`drop idx ++
#       take …`) — identical length, so C1 cannot see it and only C4's content
#       rejects it;
#     * empty returns on each over-cap branch, and the padded renderer trimmed to
#       20 on the fit branch (a subtler minimality break than the bare echo).
#     None verified, so no probe reached a clause the spec leaves unpinned.
#   E (SPEC-TOO-STRONG), two more correct reshapes, BOTH proven (exit 0) —
#     * the fit branch returning `vs.take 20`, equal to `vs` only UNDER the
#       guard, so the collapse is a real step (`List.take_of_length_le`);
#     * the whole body as ONE `return` of a nested `if`, which changes the wp
#       shape rather than the branch layout and needs the guards re-split inside
#       the proof.
#     Neither is definitionally the frozen impl and both were closed, so the spec
#     pins the FIELD and not the impl's shape. Both are left as probes rather
#     than shipped: `pos-control-unify-overcap` already carries the
#     branch-structure axis and each of these needs its own bespoke closer.
#
# SPEC PROBES RUN BY THE THIRD AUDIT, no hole found. Seven NEW impls beyond the
# shipped set, all built against the frozen spec:
#   D (SPEC-TOO-WEAK), six wrong impls, all REJECTED (exit 1) —
#     * the fits GUARD moved one past the cap (`n ≤ 21`) with every trim kept
#       byte-identical — the threshold axis nothing else attacked, now shipped as
#       `weak-guard-threshold-off`;
#     * the guard keyed on the WRONG quantity entirely (`eIndex vs ≤ 20` rather
#       than the length), so the branch choice ignores how long the field is;
#     * the marker-present branch appending the exponent suffix TWICE;
#     * the marker-absent branch replaced by a fixed 20-character filler run —
#       length exactly 20, so C1 cannot see it and only C3's content rejects it;
#     * the fit branch dropping one leading character (`vs.drop 1`) — still
#       non-empty and under the cap, so only C2's content separates it;
#     * the marker-present branch taking its significand from the WRONG end.
#     None verified, so no probe reached a clause the spec leaves unpinned.
#   E (SPEC-TOO-STRONG), one more correct reshape, PROVEN (exit 0) —
#     * the fits guard TIGHTENED to `n ≤ 19`. This is the mirror of the shipped
#       threshold rival and it is genuinely CORRECT, which is the interesting part:
#       at length exactly 20 the marker-absent branch's `take 20` is the identity
#       (`List.take_of_length_le`) and the marker-present branch's
#       `take (20-(n-idx)) ++ drop idx` collapses to `take idx ++ drop idx`, i.e.
#       `List.take_append_drop`. Neither collapse is definitional and the frozen
#       bullet script fails on it, so it needed a by-shape closer carrying both
#       steps; it then closed at exit 0, and the SAME closer also closes the frozen
#       guard, so nothing guard-specific is smuggled in. Conclusion: the threshold
#       axis carries a genuine asymmetry — trimming too LATE is refused (C1) and
#       trimming EARLIER than needed is admitted, because it changes no field.
#       Left as a probe: `pos-control-unify-overcap` already carries the positive
#       lane's reshape burden and this one needs its own closer.
#
# FRAME-MUTATION: N/A on nagini (float value, no heap) and VACUOUS here (velvet
#   is referentially transparent, no `mut` binder). No substitute fabricated.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py); the G-PBT
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
