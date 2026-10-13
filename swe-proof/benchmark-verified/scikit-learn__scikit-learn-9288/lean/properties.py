# properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-9288 (lean).
#
# NOT a Lean module: a manifest of adversarially-reasoned SPEC_TESTS the gate
# (scripts/pbt_gate.py) parses and stamps a verdict onto. Each case is a full
# Solution.lean variant built by region surgery — only the impl region (and, for
# soundness positives, the proof body) is edited, so the frozen spec is
# byte-identical and `same_spec` holds by construction; the `theorem correct_*`
# STATEMENT is preserved verbatim. Every reject case additionally carries a Lean
# `witness` that discriminates the rival from the frozen solution at a concrete
# (conditioned) input.
#
# ---------------------------------------------------------------- PORT NOTE
# This is a PORT of the nagini sibling battery, re-expressed against THIS
# bundle's carrier. The nagini bundle modeled the up-front advancing draw vector
# (a front-recursive `seed_vector` fold): its rivals perturbed how that vector
# ADVANCES (constant / shift / last-element / length). This Lean bundle models a
# DIFFERENT slice of the same fix — the deterministic best-of-N SELECTION over a
# supplied list of per-attempt configuration values (argmin of cost, earliest on
# ties). The selection carrier has no `seed_vector` fold, so the nagini advance-
# perturbation rivals have no 1:1 counterpart; this is carrier narrowing, not an
# omission. What DOES port is the adversarial STANCE: attack every independent
# clause of the postcondition, and — since the per-attempt routine is opaque —
# condition each refutation on the carrier rather than computing it. See
# `assessment` in the submission for the full ported/omitted ledger.
#
# AUDIT CORRECTION to the ledger above. The blanket claim that the nagini rivals
# have "no 1:1 counterpart" was too broad, and it silently dropped two lanes that
# ARE expressible here. (i) The length-shortfall near-miss ports as a DEFECT rather
# than as a length claim: this carrier returns one outcome, so "the final attempt is
# never performed" surfaces as a result drawn from no supplied attempt at all —
# carried as `atk-skip-last`. (ii) The admissibility lane was dropped entirely with
# no reason recorded; it is expressible, and is now carried as
# `admiss-fshaped-repeat-count`. What is genuinely NOT portable is the per-position
# advance perturbation (constant / shift / last-element), which needs a returned
# VECTOR whose entries can disagree one position at a time; the selection returns a
# single outcome, so those three collapse onto the frame clause C1 that
# `atk-position-driven` and `atk-skip-last` already attack. Separately, the original
# battery attacked only the COST projection of C1; its DATA half is now covered by
# `atk-data-component`.
#
# ---------------------------------------------------------------- DEFENDED SURFACE
# One modeled obligation: `correct_bestTrial`. Input binder: `trials : List Int`
# (the supplied list of independent configuration values). The per-attempt
# routine `runTrial : Int -> Outcome` is `opaque`: it has no computable value, so
# every refutation is stated at a point described by HYPOTHESIS on `runTrial`
# (conditioning on the carrier) rather than at a literal it could compute.
#
# AUDIT NOTE (independent re-derivation). `opaque runTrial` blocks only the VALUE
# of an attempt, not the SELECTION around it: the selection loop still reduces, so
# a witness may compute `implementation_bestTrial` down to a `runTrial` term and
# then discriminate by hypothesis on that term alone.
#
# SECOND-AUDIT CORRECTION, and it is load-bearing rather than cosmetic. A previous
# revision of this note claimed all three reduction controls "elaborate by
# `simp [implementation_bestTrial]`". Re-measured: only the SINGLETON one does.
#   * `implementation_bestTrial [7] = runTrial 7`  by `simp [implementation_bestTrial]`
#     -> exit 0. Real: a one-element list has no comparison to decide.
#   * `(runTrial 1).cost < (runTrial 0).cost => implementation_bestTrial [0,1] =
#     runTrial 1`  by `simp [implementation_bestTrial]` -> exit 1, `unsolved goals`
#     with the `if (runTrial 1).cost < (runTrial 0).cost then .. else ..` STILL
#     UNREDUCED in the goal. Same for the equal-cost form.
# The reason is that on a two-or-more-element list the fold's normal form contains
# an `if` on an opaque-valued `Int` comparison, and `simp` cannot discharge that
# branch unless the deciding fact is PASSED TO IT. Handing it over fixes it:
#   * `simp [implementation_bestTrial, h]` (h the strict `<`) -> exit 0;
#   * `simp [implementation_bestTrial, hle, hnlt]` (both orientations of the tie)
#     -> exit 0.
# This matters because two witnesses below used to state their refutation THROUGH
# that unreduced term, so their gold-side failure was the stuck `if`, not the
# claim. Both now pass the deciding fact to `simp` and pin the impl with an
# explicit `have hres : implementation_bestTrial [0,1] = ...` BEFORE touching the
# spec, so the gold-side error is a concrete equation between two `runTrial` terms.
# See the per-case notes on `atk-never-update` and `atk-last-tie` for the measured
# forgery pair that establishes the difference.
#
# That reduction (with the deciding fact supplied) is what makes every gold-side
# witness failure below a SEMANTIC refutation rather than a stuck reduction, and it
# is why the two lanes the port note called "no 1:1 counterpart" were in fact
# landable here; both are now carried (see `atk-data-component` and
# `atk-skip-last`).
# Lean is referentially transparent, so the nagini FRAME-MUTATION lane is genuinely
# VACUOUS here (see `assessment`): there is no heap to overwrite. On DIVERGENCE:
# `implementation_bestTrial` is a total `def` whose only recursion is a `for .. in`
# over a finite `List Int`, and the frozen file sets no
# `loom.semantics.termination` option at all (checked: no `set_option` line in
# Solution.lean), so there is no partial-semantics escape hatch to exploit and no
# diverging rival to construct — the class is vacuous by the carrier's totality,
# not waved off as a known hole.
#
# SECOND-AUDIT attack-D probes that did NOT become cases, recorded so the next
# reader knows the spec was pushed here and held (neither is a spec hole):
#   * SPLIT FRAME — take the winner's cost but the FIRST attempt's data
#     (`data := (runTrial trials.headI).data`). Sharper than `atk-data-component`
#     because the data is a genuine attempt's data rather than `[]`, so a spec that
#     merely required "data comes from SOME attempt" would admit it. REJECTED,
#     exit 1 (`Tactic 'rfl' failed`, the frame equality does not hold). Not shipped
#     only because `atk-data-component` already isolates the same C1 data half and
#     a second case there buys no new clause coverage.
#   * ARGMAX — reverse the comparison to `if b.cost < o.cost`, keeping the WORST
#     attempt. REJECTED, exit 1. Subsumed by `atk-never-update` on clause C2.
#
# Load-bearing postcondition clauses (three independent conjuncts an attacker
# must each defeat), all quantified over the single binder `trials`:
#   (C1) result = runTrial (trials.get i)   — the FRAME clause: the whole result
#        (cost AND produced data) comes from running attempt `i` of the SUPPLIED
#        list. A rival that drives attempts by anything other than the supplied
#        values violates C1.
#   (C2) forall j, result.cost <= (runTrial (trials.get j)).cost — GLOBAL MINIMUM.
#        A rival that fails to keep the best-so-far violates C2.
#   (C3) forall j < i, result.cost < (runTrial (trials.get j)).cost — the EARLIEST
#        minimum tie-break (strict `<`, so among equal-cost attempts the FIRST is
#        kept). A rival that keeps a LATER tie violates C3.
#
# ---------------------------------------------------------------- THE REAL CHANGE
# The fix makes the single-thread selection consume exactly the same precomputed
# per-attempt value list the distributed strategy consumes, so the kept result no
# longer depends on how the work is distributed. The regression test asserts the
# two strategies agree. Each reject rival's `refinement` argues why its faithful
# real patch would still make the two strategies select over DIFFERENT effective
# per-attempt values (or a different tie-break / a non-minimum), so the kept
# result would again diverge and the regression assertion would still fail — a
# verifying rival would therefore be a true verify-does-not-imply-resolve break.
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-9288"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ------------------------------------------------------------------ anchors
# The frozen impl body (surgery anchor). Editing only inside it keeps the spec
# and the `theorem correct_bestTrial` statement byte-identical.
_GOLD_IMPL = (
    "def implementation_bestTrial (trials : List Int) : Outcome := Id.run do\n"
    "  let mut best : Option Outcome := none\n"
    "  for t in trials do\n"
    "    let o := runTrial t\n"
    "    match best with\n"
    "    | none   => best := some o\n"
    "    | some b => if o.cost < b.cost then best := some o\n"
    "  return best.getD default")

assert _GOLD_IMPL in _BASE, "gold impl block drifted from Solution.lean"

# The `some b` arm of the loop body, isolated (used by two rivals + one positive).
_STEP_ARM = "    | some b => if o.cost < b.cost then best := some o"
assert _BASE.count(_STEP_ARM) == 1

# The strict-`<` comparison inside the running-best update.
_STRICT_CMP = "if o.cost < b.cost then best := some o"
assert _BASE.count(_STRICT_CMP) == 1

# The return line (surgery anchor for the frame/data-component rival).
_GOLD_RET = "  return best.getD default"
assert _BASE.count(_GOLD_RET) == 1

# The loop header alone (surgery anchor for the dropped-attempt rival).
_FOR_LINE = "  for t in trials do\n"
assert _BASE.count(_FOR_LINE) == 1

# End of the proof region (anchor for the admissibility positive, which appends a
# consumer of the frozen obligation without touching its statement).
_PROOF_END = "\n-- proof-end"
assert _BASE.count(_PROOF_END) == 1

# The `some b` arm of the fold-equality INDUCTION step (as opposed to the
# `suffices` normal form above). A reshape that reorders the comparison's operands
# changes both, so a correct-reshape positive must re-state this one too.
_IND_SOME_ARM = """    | some b =>
      by_cases hc : (runTrial h).cost < b.cost
      · simp only [pure_bind, step, hc, if_true]; rw [ih]
      · simp only [pure_bind, step, hc, if_false]; rw [ih]"""
assert _BASE.count(_IND_SOME_ARM) == 1

# The `some b` arm INSIDE the `suffices` normal form in `impl_eq_foldl` — the one
# proof line an if-then-else reshape of the loop body must be re-stated over.
_SUFFICES_ARM = (
    "        | some b => if (runTrial t).cost < b.cost then pure "
    "(ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) "
    "= List.foldl step init trials by")
assert _BASE.count(_SUFFICES_ARM) == 1


# ------------------------------------------------------------------ POSITIVES
# (soundness) LOCAL-VARIABLE RESHAPE. Alpha-rename the accumulator, the loop
# variable, the drawn-outcome local and the matched champion. draw/order are
# unchanged, so the fold and every proof obligation are definitionally identical;
# the frozen proof closes verbatim. Verified with a real build.
_POS_RENAME = _swap(
    _BASE, _GOLD_IMPL,
    "def implementation_bestTrial (trials : List Int) : Outcome := Id.run do\n"
    "  let mut acc : Option Outcome := none\n"
    "  for s in trials do\n"
    "    let cand := runTrial s\n"
    "    match acc with\n"
    "    | none      => acc := some cand\n"
    "    | some champ => if cand.cost < champ.cost then acc := some cand\n"
    "  return acc.getD default")

# (soundness) STRUCTURALLY-DIFFERENT accumulator shape: rewrite the running-best
# update from a one-sided `if ... then best := some o` into a total functional
# assignment `best := if ... then some o else some b` (explicit else branch). The
# selection is observably identical, but the loop body's normal form changes, so
# this needs a genuine (small) proof adaptation: the `impl_eq_foldl` `suffices`
# normal form is re-stated over the if-then-else arm. Everything else in the
# proof is unchanged. Verified with a real build; if it did not close it would
# signal SPEC-TOO-STRONG.
_POS_ITE = _swap(
    _swap(_BASE, _STEP_ARM,
          "    | some b => best := if o.cost < b.cost then some o else some b"),
    _SUFFICES_ARM,
    "        | some b => pure (ForInStep.yield (if (runTrial t).cost < b.cost "
    "then some (runTrial t) else some b)))) = List.foldl step init trials by")

# (soundness, ADDED BY AUDIT — attack E, SPEC-TOO-STRONG probe) FLIPPED-COMPARISON
# reshape. The two previous positives both keep the frozen `o.cost < b.cost`
# orientation, so neither tests whether the spec accepts a faithful impl that
# spells the SAME tie-break with the opposite operator: `best := if b.cost <= o.cost
# then some b else some o` retains the champion on a tie (via `<=` on the reversed
# operands) exactly as the frozen strict `<` does on the forward ones. Selection is
# observably identical, but this is NOT definitionally equal to the frozen form —
# `Int` `<`/`<=` on swapped operands do not reduce to each other, so the proof needs
# a genuine adaptation in TWO places (the `suffices` normal form and the induction
# step's `some b` arm, where `if_pos`/`if_neg` must be discharged from
# `not_le.mpr` / `not_lt.mp`). Measured: the naive one-place edit does NOT close
# (`unsolved goals` in both `by_cases` branches), and the two-place version does.
# A faithful correct impl the spec rejected here would be SPEC-TOO-STRONG.
_POS_FLIPPED = _swap(
    _swap(
        _swap(_BASE, _STEP_ARM,
              "    | some b => best := if b.cost ≤ o.cost then some b else some o"),
        _SUFFICES_ARM,
        "        | some b => pure (ForInStep.yield (if b.cost ≤ (runTrial t).cost "
        "then some b else some (runTrial t))))) = List.foldl step init trials by"),
    _IND_SOME_ARM,
    """    | some b =>
      by_cases hc : (runTrial h).cost < b.cost
      · simp only [pure_bind, step, if_pos hc, if_neg (not_le.mpr hc)]; rw [ih]
      · simp only [pure_bind, step, if_neg hc, if_pos (not_lt.mp hc)]; rw [ih]""")

# (soundness, ADDED BY SECOND AUDIT — attack E, SPEC-TOO-STRONG probe) DROP THE
# IMPERATIVE LOOP ENTIRELY. All three positives above keep the frozen `Id.run do` /
# `for .. in` / `let mut` skeleton and edit inside it, so none of them tests whether
# the spec accepts a faithful impl written in a DIFFERENT EXECUTION STYLE. This one
# replaces the whole imperative body with a pure `List.foldl` over an inline
# accumulator function — no monad, no mutable local, no `for`. Observably identical
# selection, but the impl is no longer a `forIn` term at all, so the frozen
# `impl_eq_foldl` proof (whose `suffices` block is entirely about normalising
# `forIn`) becomes inapplicable and must be REPLACED, not adapted: the new proof
# shows the inline function equals `step` by `funext` + `cases`, then rewrites. The
# rest of the frozen proof (FoldInv and everything downstream) is reused verbatim,
# which is the point — it demonstrates the spec's obligation is about the SELECTION,
# not about the loop syntax. Measured: exit 0. Also measured, and worth recording so
# nobody "simplifies" it later: the tempting one-liner `:= rfl` for `impl_eq_foldl`
# does NOT close (exit 1), so this is a real reprove and not a definitional freebie.
_POS_PURE_FOLDL = _swap(
    _swap(_BASE, _GOLD_IMPL,
          "def implementation_bestTrial (trials : List Int) : Outcome :=\n"
          "  (trials.foldl (fun b t =>\n"
          "      match b with\n"
          "      | none   => some (runTrial t)\n"
          "      | some o => if (runTrial t).cost < o.cost then some (runTrial t) "
          "else some o)\n"
          "    none).getD default"),
    _BASE[_BASE.index("theorem impl_eq_foldl"):
          _BASE.index("theorem FoldInv_init")].rstrip() + "\n",
    """theorem impl_eq_foldl (trials : List Int) :
    implementation_bestTrial trials = (trials.foldl step none).getD default := by
  have hf : (fun b t =>
      match b with
      | none   => some (runTrial t)
      | some o => if (runTrial t).cost < o.cost then some (runTrial t) else some o) = step := by
    funext b t
    cases b <;> rfl
  simp only [implementation_bestTrial, hf]
""")

# ------------------------------------------------------------------ ADMISSIBILITY
# (ADDED BY AUDIT — the nagini `admiss-nonneg-count` lane, re-derived here.) The
# frozen obligation is guarded by `trials ≠ []`, and that guard is genuinely
# LOAD-BEARING rather than a convenient narrowing: at `trials = []` the
# postcondition is UNSATISFIABLE for every candidate result, since it opens with
# `∃ i : Fin trials.length` and `Fin 0` is empty (verified independently:
# `∀ o, ¬ problem_spec_bestTrial [] o` elaborates). So the guard cannot be dropped,
# and what admissibility must instead show is that it still admits a NORMAL
# F2P-shaped input. This case consumes the frozen obligation at a ten-attempt list
# with duplicate costs (the usual repeat count), forcing the hypothesis to be
# discharged at a real input and the spec to be delivered THERE. It adds a
# consumer, not a new theorem, and leaves the obligation's statement untouched.
# If this could not verify, PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE, _PROOF_END,
    """
/-- Admissibility: the obligation's hypothesis admits a normal, F2P-shaped input
(ten independent attempts, the usual repeat count), and the obligation delivers
the spec THERE — so the precondition is not vacuously narrow. -/
example : problem_spec_bestTrial [5, 2, 9, 2, 7, 1, 8, 1, 4, 6]
    (implementation_bestTrial [5, 2, 9, 2, 7, 1, 8, 1, 4, 6]) :=
  correct_bestTrial _ (by simp)

-- proof-end""")


# ------------------------------------------------------------------ REJECT rivals
# (C1) POSITION-DRIVEN — the pre-patch bug. Each attempt is driven by its LOOP
# POSITION instead of the corresponding supplied value, so the returned outcome
# is not `runTrial (trials.get i)` for any index of the supplied list. This is
# the Solution_prepatch shape (the n-jobs-dependent bug).
_ATK_POSITION = _swap(
    _BASE,
    "  for t in trials do\n"
    "    let o := runTrial t\n",
    "  for p in [0:trials.length] do\n"
    "    let o := runTrial (Int.ofNat p)\n")

# (C2) NEVER-UPDATE — keep the FIRST attempt's outcome regardless of cost (the
# running best is never replaced). The result is `runTrial (trials.head)`, which
# need not be the global minimum.
_ATK_NOUPDATE = _swap(
    _BASE, _STEP_ARM, "    | some _ => best := best")

# (C3) LAST-TIE — use `<=` instead of strict `<`, so among equal-cost attempts
# the LAST one is kept rather than the earliest. Violates the tie-break clause
# only; correct on strictly-ordered inputs.
_ATK_LASTTIE = _swap(
    _BASE, _STRICT_CMP, "if o.cost ≤ b.cost then best := some o")

# (C1, DATA COMPONENT — ADDED BY AUDIT, attack D.) The three original rivals all
# attack the COST projection: position-driven perturbs which attempt is run,
# never-update and last-tie perturb which cost wins. None of them attacks the
# other half of the frame clause — that the result's PRODUCED DATA comes from the
# same attempt as its cost. This rival selects the correct attempt and reports its
# cost faithfully, then discards the data it produced. It satisfies C2 and C3 (the
# cost is the true global minimum, attained earliest) and is wrong on C1 ALONE, so
# it is the sharpest available probe of the "whole outcome returned verbatim"
# clause: a spec that pinned only the cost would admit it.
_ATK_DATA = _swap(
    _BASE, _GOLD_RET,
    "  return { cost := (best.getD default).cost, data := [] }")

# (C1, NO-SOURCE-ATTEMPT — ADDED BY AUDIT; the nagini `atk-length-shortfall`
# analogue re-derived on this carrier.) Nagini's near-miss dropped the final entry
# of a RETURNED VECTOR, violating a length clause. This carrier returns ONE outcome,
# not a vector, so there is no length to shorten — but the same defect (the last
# attempt is never performed) is expressible and lands harder here: dropping the
# final attempt of a singleton list means NO attempt is run at all, so the result
# is the `default` Outcome, which is the outcome of no supplied attempt whatsoever.
# That refutes the frame clause C1 outright. Correct whenever the minimum is not
# uniquely attained at the last position, so a fuzzer whose lists always put the
# winner early would miss it — the partial-domain hole in the length lane.
_ATK_SKIPLAST = _swap(
    _BASE, _FOR_LINE, "  for t in trials.dropLast do\n")


SPEC_TESTS = [
    {
        "id": "pos-localvar-rename",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RENAME,
        "rationale": "structurally-different CORRECT impl: alpha-rename of the "
                     "accumulator / loop variable / outcome local / matched "
                     "champion. The fold and every proof obligation are "
                     "definitionally identical, so the frozen proof closes "
                     "verbatim; if it did not, SPEC-TOO-STRONG. Defends all three "
                     "clauses (C1/C2/C3) — the earliest global-minimum outcome.",
    },
    {
        "id": "pos-ite-accumulator",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ITE,
        "rationale": "structurally-different CORRECT impl: the running-best update "
                     "is rewritten from a one-sided `if ... then best := some o` "
                     "into a total functional assignment "
                     "`best := if ... then some o else some b`. Observably "
                     "identical selection, but the loop-body normal form changes, "
                     "so the proof's `suffices` normal form is re-stated over the "
                     "if-then-else arm (the `theorem correct_bestTrial` statement "
                     "is untouched). Must verify (soundness); a rejection would be "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-flipped-comparison",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FLIPPED,
        "rationale": "ADDED BY AUDIT (attack E, SPEC-TOO-STRONG probe). The other "
                     "two positives both keep the frozen comparison's ORIENTATION, "
                     "so neither tests whether the spec accepts a faithful impl "
                     "that spells the same tie-break the other way round: "
                     "`if b.cost <= o.cost then some b else some o` keeps the "
                     "champion on a tie exactly as the frozen strict `<` does. "
                     "Observably identical selection, and NOT definitionally equal "
                     "(`<`/`<=` on swapped Int operands do not reduce to one "
                     "another), so the proof is adapted in two places — the "
                     "`suffices` normal form AND the induction step's `some b` arm. "
                     "Measured: the one-place edit leaves `unsolved goals` in both "
                     "`by_cases` branches; the two-place version closes. A "
                     "rejection here would be SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-pure-foldl",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE_FOLDL,
        "rationale": "ADDED BY SECOND AUDIT (attack E, SPEC-TOO-STRONG probe). The "
                     "other three positives all keep the frozen `Id.run do` / "
                     "`for .. in` / `let mut` skeleton and edit inside it, so none "
                     "tests whether the spec accepts a faithful impl in a different "
                     "EXECUTION STYLE. This drops the imperative loop entirely for a "
                     "pure `List.foldl` over an inline accumulator — no monad, no "
                     "mutable local, no `for`. Selection is observably identical, but "
                     "the impl is no longer a `forIn` term, so the frozen "
                     "`impl_eq_foldl` proof (wholly about normalising `forIn`) is "
                     "inapplicable and is REPLACED by a `funext`/`cases` argument "
                     "that the inline function equals `step`; FoldInv and everything "
                     "downstream is reused verbatim, showing the obligation is about "
                     "the SELECTION and not the loop syntax. Measured exit 0 — and "
                     "the tempting `:= rfl` one-liner does NOT close (exit 1), so "
                     "this is a real reprove, not a definitional freebie. A "
                     "rejection here would be SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fshaped-repeat-count",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "ADDED BY AUDIT: the nagini admissibility lane, re-derived. "
                     "The obligation is guarded by `trials != []`, and that guard "
                     "is load-bearing rather than a convenient narrowing — at "
                     "`trials = []` the postcondition opens with "
                     "`exists i : Fin trials.length` over an EMPTY `Fin 0`, so it "
                     "is unsatisfiable for every result (verified separately: "
                     "`forall o, not problem_spec_bestTrial [] o` elaborates). So "
                     "admissibility must instead show the guard still admits a "
                     "NORMAL input: this consumes the frozen obligation at a "
                     "ten-attempt list with duplicate costs (the usual repeat "
                     "count), discharging the hypothesis at a real input and "
                     "delivering the spec there. If it could not verify, "
                     "PRECOND-TOO-STRONG.",
    },
    {
        "id": "atk-position-driven",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_POSITION,
        "refinement": "This is the pre-patch behavior: the single-thread strategy "
                      "drives each attempt by its POSITION rather than by the "
                      "corresponding supplied configuration value, so the two "
                      "strategies select over completely different effective "
                      "per-attempt values. A faithful real patch with this seeding "
                      "would make the single-thread and distributed strategies "
                      "explore different attempts, so the kept result diverges "
                      "between the two — the regression assertion "
                      "(both strategies agree) fails: NOT resolved.",
        "rationale": "rejects on (C1): the result is `runTrial (Int.ofNat p)` for "
                     "a loop position `p`, which for a singleton list `[7]` is "
                     "`runTrial 0`, not `runTrial (trials.get i) = runTrial 7`. "
                     "The frame clause `result = runTrial (trials.get i)` is "
                     "therefore unsatisfiable whenever the position and the "
                     "supplied value give distinct outcomes.",
        # Conditioned on the carrier: runTrial is opaque, so we assume only that
        # position 0 and the supplied value 7 give distinct outcomes — exactly the
        # sub-domain where the position-driven rival is wrong. Elaborates against
        # the rival (result = runTrial 0 ≠ runTrial 7 = the only frame candidate);
        # fails on gold (whose result IS runTrial 7). Single hypothesis, trivially
        # consistent.
        "witness": (
            "example (h : runTrial 0 ≠ runTrial 7) :\n"
            "    ¬ problem_spec_bestTrial [7] (implementation_bestTrial [7]) := by\n"
            "  unfold problem_spec_bestTrial\n"
            "  rintro ⟨i, hEq, _, _⟩\n"
            "  fin_cases i\n"
            "  simp [implementation_bestTrial] at hEq\n"
            "  exact h hEq"),
    },
    {
        "id": "atk-never-update",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_NOUPDATE,
        "refinement": "Keeping the first attempt's outcome regardless of cost is "
                      "the analogue of a selection that never compares against the "
                      "running best. A faithful real patch that returned the first "
                      "attempt rather than the lowest-cost one would keep a "
                      "non-minimal result, so on any input where a later attempt "
                      "is strictly better the single-thread strategy would keep a "
                      "different (worse) result than the distributed argmin "
                      "strategy — the regression assertion fails: NOT resolved.",
        "rationale": "rejects on (C2): the result is fixed to the first attempt's "
                     "outcome, so its cost is not <= every attempt's cost. For "
                     "`[0, 1]` with attempt 1 strictly cheaper than attempt 0, the "
                     "global-minimum clause `result.cost <= (runTrial "
                     "(trials.get 1)).cost` is violated.",
        # runTrial opaque; assume only that attempt 1 is strictly cheaper than
        # attempt 0. The rival returns runTrial 0, whose cost exceeds attempt 1's,
        # refuting the minimum clause. Fails on gold (which returns the cheaper
        # attempt 1). Single hypothesis, consistent.
        #
        # REPAIRED BY SECOND AUDIT (attack B'). The previous witness folded the
        # reduction into the refutation (`simp [implementation_bestTrial, List.get]
        # at hk` then `omega`). On gold that left the selection's `if` UNREDUCED —
        # gold's recorded failure was `omega could not prove the goal` over a
        # `match ... (if (runTrial 1).cost < (runTrial 0).cost then ..)` term, i.e.
        # omega was defeated by a term it could not see into, NOT by the claim.
        # Measured forgery pair on the OLD witness: claiming the OPPOSITE of what
        # the witness claims (`implementation_bestTrial [0,1] = runTrial 1`, which
        # is TRUE of gold) ALSO failed on gold, exit 1, same unreduced `if`. So
        # gold's exit code carried no information about the claim.
        # The repair pins the impl FIRST, passing the deciding fact to `simp`
        # (`simp [implementation_bestTrial, h]`, measured exit 0 on gold), and only
        # then contradicts the minimum clause. Now the two sides genuinely differ:
        #   rival exit 0; gold exit 1 with `unsolved goals ... ⊢ runTrial 1 =
        #   runTrial 0` — a concrete equation between two opaque outcomes, refuted
        #   because gold's result IS the cheaper attempt 1;
        #   and the flipped-claim partner (`= runTrial 1`) now SUCCEEDS on gold at
        #   exit 0. The exit code tracks the claim, which is the whole requirement.
        "witness": (
            "example (h : (runTrial 1).cost < (runTrial 0).cost) :\n"
            "    ¬ problem_spec_bestTrial [0, 1] (implementation_bestTrial [0, 1]) := by\n"
            "  have hres : implementation_bestTrial [0, 1] = runTrial 0 := by\n"
            "    simp [implementation_bestTrial, h]\n"
            "  rw [hres]\n"
            "  unfold problem_spec_bestTrial\n"
            "  rintro ⟨i, hEq, hmin, _⟩\n"
            "  have hk := hmin ⟨1, by simp⟩\n"
            "  simp [List.get] at hk\n"
            "  omega"),
    },
    {
        "id": "atk-last-tie",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_LASTTIE,
        "refinement": "Using a non-strict comparison keeps the LAST attempt among "
                      "equal-cost ties instead of the earliest. A faithful real "
                      "patch with this tie-break would disagree with the "
                      "distributed strategy's first-occurrence argmin whenever two "
                      "attempts tie for the minimum cost but produce different "
                      "data, so the two strategies keep different results on a tie "
                      "— the regression assertion fails: NOT resolved. (Correct on "
                      "strictly-ordered inputs, so a fuzzer that never produces a "
                      "cost tie would miss it — the partial-domain hole.)",
        "rationale": "rejects on (C3): on a cost tie the rival keeps the LATER "
                     "attempt, so for `[0, 1]` with equal costs but distinct "
                     "outcomes the result is `runTrial 1`, and the earliest-"
                     "minimum clause `forall j < i, result.cost < ...` cannot hold "
                     "at witness index 1 (attempt 0 is earlier with equal, not "
                     "strictly greater, cost).",
        # Two hypotheses about DIFFERENT observables of the same opaque terms:
        # equal COST (forces the rival to keep the later tie) and distinct OUTCOME
        # (so the choice is observable). Jointly satisfiable — an outcome may share
        # a cost while differing in its data — so the consistency probe fails, as
        # required. Elaborates against the rival (result = runTrial 1, and attempt
        # 0 is an earlier equal-cost attempt); fails on gold (which keeps attempt 0).
        #
        # REPAIRED BY SECOND AUDIT (attack B'). The `have hres` was already here,
        # but it was proven by `simp [implementation_bestTrial, hle]` — and `hle`
        # (`(runTrial 1).cost ≤ (runTrial 0).cost`) is the WRONG orientation to
        # decide the frozen impl's `if (runTrial 1).cost < (runTrial 0).cost`. So on
        # gold that `simp` left the `if` unreduced (the recorded `gold_signature` is
        # exactly that stuck term, and the build log flags `hle` as an UNUSED simp
        # argument — the tell). Measured forgery pair on the OLD witness: flipping
        # the claim to `= runTrial 0`, which is TRUE of gold, ALSO failed on gold at
        # exit 1 with the byte-same stuck `if`. Gold's exit code was therefore
        # independent of the claim, so the case attributed nothing to the spec.
        # The repair adds `hnlt : ¬ (runTrial 1).cost < (runTrial 0).cost` — the
        # negation in exactly the impl's orientation, which on a cost TIE is what
        # makes gold keep the earlier attempt — and passes both facts to `simp`
        # (measured exit 0 on gold for the true claim `= runTrial 0`).
        # Now: rival exit 0; gold exit 1 with `unsolved goals ... ⊢ runTrial 0 =
        # runTrial 1`, a concrete equation refuted by `hd`; and the flipped-claim
        # partner SUCCEEDS on gold at exit 0. The exit code tracks the claim.
        "witness": (
            "example (hc : (runTrial 0).cost = (runTrial 1).cost) "
            "(hd : runTrial 0 ≠ runTrial 1) :\n"
            "    ¬ problem_spec_bestTrial [0, 1] (implementation_bestTrial [0, 1]) := by\n"
            "  have hle : (runTrial 1).cost ≤ (runTrial 0).cost := by omega\n"
            "  have hnlt : ¬ (runTrial 1).cost < (runTrial 0).cost := by omega\n"
            "  have hres : implementation_bestTrial [0, 1] = runTrial 1 := by\n"
            "    simp [implementation_bestTrial, hle, hnlt]\n"
            "  rw [hres]\n"
            "  unfold problem_spec_bestTrial\n"
            "  rintro ⟨i, hEq, _, hbefore⟩\n"
            "  fin_cases i\n"
            "  · simp at hEq; exact hd hEq.symm\n"
            "  · have hb := hbefore ⟨0, by simp⟩ (by simp)\n"
            "    simp [List.get] at hb\n"
            "    omega"),
    },
    {
        "id": "atk-data-component",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_DATA,
        "refinement": "The three original rivals all perturb the COST projection "
                      "(which attempt runs, or which cost wins). This one selects "
                      "the right attempt and reports its cost faithfully, then "
                      "returns that cost with the produced data discarded. A "
                      "faithful real patch that kept the winning attempt's ranking "
                      "quantity but not the data that attempt produced would have "
                      "the single-thread strategy return different produced data "
                      "than the distributed strategy on the very same selection, so "
                      "the regression assertion (both strategies agree) still "
                      "fails: NOT resolved. It is the only rival here that is "
                      "correct on BOTH cost clauses, so the spec's frame strength "
                      "is the only thing that can reject it.",
        "rationale": "rejects on (C1) at its DATA half: the frame clause pins the "
                     "WHOLE result to one attempt, `result = runTrial "
                     "(trials.get i)`, not merely `result.cost`. For `[7]` the "
                     "rival returns an outcome whose `data` is `[]` while the only "
                     "frame candidate `runTrial 7` may have non-empty data, so the "
                     "equality is unsatisfiable. C2 and C3 are both SATISFIED by "
                     "this rival, which is what isolates the clause.",
        # runTrial opaque; assume only that attempt 7 produced some data. The
        # refutation is taken on the `data` projection of the frame equality
        # (congrArg Outcome.data), which is exactly the component the rival drops.
        # Rebuilt during the audit: holds of the rival (exit 0), fails on gold
        # (exit 1) with a SEMANTIC mismatch — gold reduces the frame equality to
        # `(runTrial 7).data = []` and the hypothesis refutes it, not an unknown
        # name or a stuck term. Single hypothesis, trivially consistent.
        "witness": (
            "example (h : (runTrial 7).data ≠ []) :\n"
            "    ¬ problem_spec_bestTrial [7] (implementation_bestTrial [7]) := by\n"
            "  rintro ⟨i, hEq, _, _⟩\n"
            "  fin_cases i\n"
            "  apply h\n"
            "  have hd := congrArg Outcome.data hEq\n"
            "  simp only [implementation_bestTrial, List.get] at hd\n"
            "  simpa using hd.symm"),
    },
    {
        "id": "atk-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _ATK_SKIPLAST,
        "refinement": "The nagini length-shortfall near-miss, re-derived on this "
                      "carrier: there the dropped final entry shortened a returned "
                      "VECTOR, here the selection returns one outcome, so the same "
                      "defect (the final attempt is never performed) shows up as a "
                      "result drawn from no attempt at all. A faithful real patch "
                      "that ran one fewer attempt than the supplied values would "
                      "have the two strategies not even explore the same set of "
                      "attempts, so the kept result can differ and the regression "
                      "assertion fails: NOT resolved. (Correct whenever the "
                      "minimum is not uniquely attained at the last position, so a "
                      "fuzzer whose winner is always early would miss it.)",
        "rationale": "rejects on (C1): with the last attempt dropped, a singleton "
                     "list runs NO attempt, so the running best stays `none` and "
                     "the result is the `default` Outcome — the outcome of no "
                     "supplied attempt. For `[7]` the frame clause's only "
                     "candidate is `runTrial 7`, so `result = runTrial "
                     "(trials.get i)` is unsatisfiable whenever `default` and "
                     "`runTrial 7` differ.",
        # runTrial opaque, so `default` cannot be computed apart from it: assume
        # only that the fallback and attempt 7's outcome differ — exactly the
        # sub-domain where returning a result from no attempt is observable.
        # Rebuilt during the audit: holds of the rival (exit 0), fails on gold
        # (exit 1) with a semantic mismatch (gold reduces its result to
        # `runTrial 7`, so the claimed `default = runTrial 7` is refuted).
        # Single hypothesis, trivially consistent.
        "witness": (
            "example (h : (default : Outcome) ≠ runTrial 7) :\n"
            "    ¬ problem_spec_bestTrial [7] (implementation_bestTrial [7]) := by\n"
            "  rintro ⟨i, hEq, _, _⟩\n"
            "  fin_cases i\n"
            "  simp [implementation_bestTrial] at hEq\n"
            "  exact h hEq"),
    },
]
