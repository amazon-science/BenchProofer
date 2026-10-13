# properties.py — PBT manifest for pydata__xarray-4356 (lean bundle).
#
# NOT a Lean module; a record of adversarially-reasoned falsification cases.
# The G-PBT gate parses SPEC_TESTS, writes each `module` to a temp Solution.lean
# variant, runs the Lean verifier + variant_scope.variant_problems against the
# frozen Solution.lean, and (for every expect="reject" case) checks the attached
# `witness` in a file with the proof obligations stripped. We only ever replace
# text strictly inside the impl region and the proof region (the two regions the
# spec view elides), so markers.same_spec holds by construction for every case.
#
# This is a PORT of the nagini sibling battery, re-expressed against this
# backend's carrier. The nagini surface contracts a single boolean helper
# `flag_too_few(sizes, missing, required_minimum) -> bool` over a half-permission
# read-only `sizes`; here the modeled core is `enforceMinCount`, mapping a list
# of output cells to their post-threshold values through the SAME per-cell
# decision, returning an `Except String (List Float)` so the error branch is a
# first-class observable.
#
# DEFENDED SURFACE (reasoned from this bundle's own frozen spec):
#   implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
#       (minCount : Nat) (fillValue : Float) : Except String (List Float)
#   For each output cell (value, missing), the number of entries reduced into it
#   is `axisSizes.prod`; the cell keeps its value when `prod - missing ≥ minCount`
#   and is replaced by `fillValue` otherwise. Reducing over several axes at once
#   is admitted directly (no error), and the per-cell total is the product over
#   ALL reduced-axis sizes, not a single axis.
#
#   POSTCONDITION (problem_spec_enforceMinCount), two independent top-level
#   clauses:
#     (C0) result = Except.ok out          — completes without error; the multi-
#          axis request is NOT rejected. (Directly modeled here via `Except`; on
#          the nagini carrier this was implicit in admitting len(sizes) >= 2.)
#     (C1) ∀ i, out[i]? = (cells[i]?).map (fun cell =>
#            if (axisSizes.prod : Int) - (cell.2 : Int) < (minCount : Int)
#              then fillValue else cell.1)
#          — position-by-position: length pinned, each output element the fill
#          sentinel iff `prod − missing < minCount` (STRICT), else the cell's own
#          value. This clause carries three sub-facts a rival can attack
#          independently: the count is the WHOLE-BLOCK product, the comparison is
#          STRICT `<`, and the kept value is the cell's own `cell.1` (not fill).
#
#   INPUT BINDERS of the spec predicate: axisSizes, cells, minCount, fillValue.
#   The reject witnesses vary axisSizes ([2,3] / [1,1,3] / [2,2]), cells (empty /
#   one-cell with missing ∈ {0,1,2,3}), minCount (1 / 3), and rely on fillValue ≠
#   the cell value as the discriminator (a Float-order fact stated by hypothesis,
#   since Float is not `decide`-able — CONFIRMED by the audit: `decide`, `simp`,
#   `rfl` and `norm_num` each fail to close `(2.0 : Float) ≠ (1.0 : Float)`, so
#   the hypothesis form is forced, not a convenience).
#
#   THE REAL BUG: the pre-fix count was a single reduced-axis size (equivalently
#   `axisSizes.headD 1`), guarded so that any multi-axis request raised outright.
#   The fix makes the count the product over all reduced axes and drops the
#   guard. The F2P reduces over three axes with minCount=3; pre-fix it raised
#   (C0 violated).
#
#   AUDIT CORRECTION — what the F2P does and does NOT separate. This was measured
#   against the real reduction, and the original manifest overstated it. The F2P
#   reduces over EVERY axis of its array, so its result is a single cell whose
#   block total is the whole carrier size; that shape is computed by a path which
#   does not consult the per-axis count at all. Consequences, all measured:
#     * The guard is what the F2P actually senses: keeping it while fixing the
#       count leaves all 8 F2P cases failing. This is the `reject-error-on-multi-
#       axis` rival, and its refinement claim holds as written.
#     * The COUNT and the BOUNDARY are NOT sensed by the F2P. Faithful patches
#       that drop the guard but keep a single-axis count, or a first-two-axes
#       product, or a `≤` boundary, each pass all 8 F2P cases and all 604 P2P
#       cases. Those three rivals are still genuinely WRONG — they diverge from
#       the reference on a PARTIAL multi-axis reduction (some axes reduced, some
#       surviving), which is inside the modeled domain and is the issue's own
#       request — but their rejection is attributable to the SPEC's clauses, not
#       to the F2P assertion. Each refinement field below now says so and carries
#       the concrete diverging input instead of the F2P claim.
#   This is a property of the shipped test, not a defect in the frozen spec: the
#   spec is STRONGER than the F2P on the modeled domain, which is the direction
#   the guarantee needs (verify ⟹ correct). It is recorded here so no later
#   reader mistakes "the F2P separates this" for a measured fact.
#
# PORT NOTES — nagini cases with NO counterpart on this carrier. Both omissions
# were RE-DERIVED independently by the audit and both hold; the evidence each
# rests on is recorded here rather than asserted.
#   * FRAME-MUTATION (nagini case 1, `sizes[0] = sizes[0]` under Acc(...,1/2)):
#     VACUOUS here. Lean is referentially transparent — there is no aliasing and
#     no fractional permission, so "write to a read-only input" is not
#     expressible and cannot be attacked. Concretely, `axisSizes : List Nat` is
#     an immutable value: the carrier offers no store operation to smuggle in, so
#     there is no rival to write. What the nagini permission system bought — the
#     frame guarantee that the inputs are not disturbed — this carrier gives for
#     free by construction, and the spec's own framing job (pinning the output at
#     every index to the input carrier) is what C1 already does. Omitted by
#     carrier collapse, not difficulty.
#   * ADMISSIBILITY (nagini case 6, F2P-shaped self-call discharging Requires):
#     NOT omitted — LANDED, as `admiss-f2p-three-axes` below. A second audit
#     found the previous note here wrong on the reason and wrong on the
#     disposition. It argued the lane was vacuous because the frozen obligation
#     carries no precondition hypotheses, so there is "no Requires to admit";
#     that is not the analogue on a total carrier. The analogue is the obligation
#     being UNSATISFIABLE at exactly an F2P-shaped input, which no amount of
#     "∀ with no hypotheses" rules out: a `problem_spec` whose two clauses could
#     not both hold at a concrete legitimate input would still quantify
#     vacuously-freely and still be a PRECOND-TOO-STRONG defect. The way to test
#     it is to DISCHARGE the obligation at that concrete input by evaluation,
#     as a `have`, before closing the frozen obligation verbatim — which is what
#     the landed case does, and which the audit measured as a real build
#     (exit 0), not an argument.
#
# AUDIT ADDITIONS. An independent audit rebuilt every witness (each elaborates
# against its rival and fails on the frozen solution for a SEMANTIC reason — the
# concrete `.ok [...]` value the rival computes is not the one the frozen impl
# computes, or the frozen impl's `.ok` refutes the rival's `.error`), then probed
# for holes the battery left open:
#   * SPEC-TOO-WEAK probe (new wrong impls, none of which verified): a `Nat`-
#     truncating subtraction instead of the signed one; a total taken as the SUM
#     of the axis sizes instead of the product; dropping the last cell; appending
#     a spurious trailing cell; ignoring minCount entirely; reversing the output
#     positions; and discarding every cell. The last of these had no counterpart
#     in the battery and is now shipped as `reject-always-fill`; the rest are
#     already covered by C1 as written. No wrong impl verified, so no spec hole.
#   * SPEC-TOO-STRONG probe (new correct reshapes, all of which verified): the
#     per-cell map expressed as a `foldr`; as a reverse-map-reverse round trip;
#     as a structurally recursive helper; and with the block total computed by
#     `List.foldl` rather than `List.prod`. The spec admits every faithful correct
#     shape tried, including one that reshapes the PRODUCT itself, so C1 pins the
#     decision rather than a syntactic rendering of it.
#   * The frozen postcondition was additionally shown to be EXACT, not merely
#     necessary: `problem_spec_enforceMinCount ... r` is provably equivalent to
#     `r = Except.ok (cells.map ...)`, so C0 and C1 together determine the result
#     uniquely and leave no output component unconstrained. (Re-derived as a real
#     build by the THIRD audit — see below — since this was recorded here as a
#     claim without a recorded exit code.)
#   * AXIOM_TESTS (A-reference soundness/containment for the product oracle):
#     DROPPED. The axiom lane is G-AX's job; this gate ignores AXIOM_TESTS. Here
#     the count is modeled DEEPLY as `axisSizes.prod` with no consumed callee
#     axiom (the axioms region is empty), so there is nothing for this lane.
#
# THIRD AUDIT — the FORGERY test, and three sub-facts that were unattacked.
# Every claim below is an exit code from a real `lean_verify.sh` build, not an
# argument.
#   * FORGERY TEST (mandatory, since four gold-side signatures are `rfl` type
#     mismatches rather than plain evaluations, and a type mismatch is exactly
#     the shape that has read as "semantic" while carrying no information). For
#     each of the five shipped reject cases, a second gold-side file was built
#     differing from the witness ONLY in what it CLAIMS: the spec asserted to
#     HOLD at the same input (the `¬` dropped), with the value the frozen impl
#     actually computes. All five flipped claims BUILD on gold (exit 0) where the
#     witness FAILS (exit 1), and the same flipped claim fails on each rival
#     (exit 1) while the rival's own computed value builds there (exit 0). So
#     gold's exit code tracks the claim in both directions, on every case: the
#     `rfl` mismatch is a real refutation — gold computes `.ok [2.0]` where the
#     rival computes `.ok [1.0]` — and not a hollow tactic gap. The C0 case's
#     gold-side failure is `unsolved goals ⊢ False`, a plain evaluation, and its
#     flip also builds.
#   * THE POSITIVES ARE NOT NEUTERED, re-measured directly: each positive's impl
#     was rebuilt with the FROZEN proof script kept. Both FAIL (`pos-functional-
#     map`: `No goals to be solved`; `pos-reassociated-signed-compare`: the
#     bridge-lemma `rewrite` finds no occurrence), so neither positive inherits
#     the frozen proof and each really reproves the obligation. The reassociated
#     impl was additionally shown NOT definitionally equal to the frozen one (a
#     closing `rfl` between the two bodies fails to typecheck), so its `omega`
#     step does real work.
#   * THE ADMISSIBILITY GROUND `have` IS LOAD-BEARING: the same case with the
#     evaluated value changed to a wrong one (the discarded cell claimed to keep
#     3.0 instead of the sentinel) FAILS to build, so the `have` is genuinely
#     checked and the case is not a no-op wrapper around the frozen file.
#   * THREE SUB-FACTS WERE UNATTACKED, and each is now a shipped rival with a
#     rebuilt, forgery-tested witness (rival 0 / gold 1 / flip-on-gold 0):
#       - `reject-constant-sentinel`: what a DISCARDED cell receives. Every prior
#         witness discriminates on the CELL VALUE; none on `fillValue`, so a
#         rival ignoring the sentinel binder passed unexamined.
#       - `reject-head-missing-for-all`: C1's POSITIONAL grounding. Every prior
#         rival errs uniformly across cells, so all of them are refuted at a
#         ONE-cell input and none needs a second cell to exist; a rival deciding
#         every cell from cells[0] agrees with the spec on every single-cell
#         input and so was invisible to all five prior input points. This is the
#         first witness here to instantiate C1 at a NONZERO index.
#       - `reject-drop-last-cell`: C1's LENGTH pin. No shipped rival changed the
#         output length, so that pin rested on argument alone.
#   * SPEC-TOO-WEAK probe, this round (none verified, so no spec hole): a total
#     taken as the SUM of the axis sizes; a constant-0.0 discard value; the
#     head-cell missing count for every cell; a truncated output; and a reversed
#     output. A `Nat`-truncating subtraction was also written and refuted, but is
#     deliberately NOT shipped: it diverges from the frozen decision only when
#     missing > total, which the modeled domain reaches but the real reduction
#     never does (a per-cell missing count cannot exceed its own block), so it
#     would be a rival that is wrong only off the faithful domain.
#   * SPEC-TOO-STRONG probe, this round (all verified): the per-cell decision
#     with the condition NEGATED and the two branches swapped; a
#     reverse-map-reverse round trip; and the block total accumulated by an
#     explicit `List.foldl` instead of `List.prod`. The spec admits each, so C1
#     pins the decision and not a rendering of it.
#   * EXACTNESS re-derived as a real build, not a claim: `problem_spec_
#     enforceMinCount a c m f r ↔ r = Except.ok (c.map ...)` was PROVEN (exit 0),
#     so C0 and C1 together determine the result uniquely and leave no output
#     component unconstrained.
#   * The Float-undecidability justification for the hypothesis form was
#     re-measured rather than trusted: `(2.0 : Float) ≠ (1.0 : Float)` is closed
#     by NONE of `decide` (fails to synthesize a `Decidable` instance), `simp`,
#     or `norm_num` (both `unsolved goals`). The hypothesis form is forced.
#
# SECOND AUDIT — the gold-side failures re-established by FORGERY, not by
# reading them. The four value-branch witnesses fail on the frozen solution with
# `Type mismatch: rfl ... but is expected to have type implementation_... =
# Except.ok [1.0]`, which is an admissible refutation only if that exit code
# TRACKS THE CLAIM. Measured, three builds per case:
#   * Flip the claimed output to gold's own value (`.ok [1.0]` -> `.ok [2.0]`,
#     everything else byte-identical) and build the full witness on gold: it
#     fails DIFFERENTLY — `Invalid field 'symm': the environment does not
#     contain 'True.symm'; hgold has type True`. `simp` reduced the instantiated
#     clause to `True`, i.e. it PROVED the per-cell equation for the frozen impl
#     at that input. Same flipped witness against the rival fails at the
#     `hcompute` step instead, since the rival does not compute `.ok [2.0]`.
#   * Reveal the hypothesis type (replace the closing `exact h hgold.symm` with a
#     deliberate `exact (hgold : Nat)`): against the RIVAL, `hgold has type
#     1.0 = 2.0` — a concrete false Float equation, so the refutation is real and
#     the only thing left to discharge is the stated distinctness hypothesis.
#     Against GOLD the build never reaches that step. The `True` / `1.0 = 2.0`
#     pair is the genuine refutation, so none of the four is hollow.
#   * The bare computation on each side: `implementation_... = .ok [2.0]` (gold's
#     value) elaborates by `rfl` on the frozen solution and fails on every rival
#     with `Tactic 'rfl' failed: ... is not definitionally equal to Except.ok
#     [2.0]`. So each rival is observably DIFFERENT from the frozen impl at its
#     witness's input, on this carrier — not merely reshaped (attack C).
#   * The C0 witness's gold-side failure is a plain evaluation (`unsolved goals
#     ⊢ False`), and dropping its `¬` makes gold's build SUCCEED (exit 0) while
#     the rival still fails — claim-sensitive in the strongest possible way.
#   * Non-vacuity of the two soundness positives, re-measured: restoring the
#     FROZEN proof script over each reshaped impl FAILS (`No goals to be solved`
#     for the functional-map reshape, and for the reassociated compare `rewrite
#     failed: did not find an occurrence of the pattern forIn ...`). Both
#     positives therefore reprove the obligation rather than inherit it.
#   * The forced-hypothesis claim above was re-measured tactic by tactic:
#     `(2.0 : Float) ≠ (1.0 : Float)` is closed by NONE of `decide`, `simp`,
#     `rfl`, `norm_num`, or even `native_decide` (no `Decidable`/`Bool`
#     instance), so stating the distinctness as a hypothesis is forced by the
#     carrier, not chosen for convenience.
#   * SPEC-TOO-WEAK, re-probed with new wrong impls not in the battery: swapping
#     the missing count and minCount in the comparison; appending a spurious
#     trailing cell; reversing the output order; a total off by one. None
#     verified. This is settled structurally rather than case-by-case by the
#     EXACTNESS theorem above (re-verified, exit 0): the postcondition is
#     equivalent to `r = Except.ok (cells.map ...)`, so ANY impl whose output
#     differs from that map at any index is rejected and no wrong impl can
#     verify. There is no spec hole to find in this direction.
#   * SPEC-TOO-STRONG, re-probed with three further correct reshapes, all of
#     which VERIFIED (exit 0): a reverse-map-reverse round trip, the block total
#     via `List.foldl (· * ·) 1` instead of `List.prod`, and the per-cell map as
#     a `foldr` that conses. No faithful correct shape was rejected.
from pathlib import Path

INSTANCE = "pydata__xarray-4356"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()

# The exact frozen impl-region body (the whole `def implementation_...`). Every
# variant replaces this block, so the spec regions stay byte-identical.
_IMPL = """def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
  let total : Int := (axisSizes.prod : Int)
  let mut out : List Float := []
  for cell in cells do
    out := out ++ [reducedCellValue total minCount fillValue cell]
  return .ok out"""

# The frozen `theorem correct_...` block (statement + tactic body), VERBATIM.
# Soundness positives replace this whole block with a proof that closes for the
# reshaped impl, keeping the theorem STATEMENT byte-identical (variant_scope
# rule 2). Reject rivals keep it as-is — the frozen script no longer closes
# against a reshaped impl, which is exactly why each reject case carries a
# witness rather than relying on "did not verify".
_PROOF = """theorem correct_enforceMinCount :
    ∀ (axisSizes : List Nat) (cells : List (Float × Nat))
      (minCount : Nat) (fillValue : Float),
      problem_spec_enforceMinCount axisSizes cells minCount fillValue
        (implementation_enforceMinCount axisSizes cells minCount fillValue) := by
  intro axisSizes cells minCount fillValue
  refine ⟨cells.map (reducedCellValue (axisSizes.prod : Int) minCount fillValue), ?_, ?_⟩
  · -- the loop builds exactly the per-cell map; bridge the desugared body to the helper
    unfold implementation_enforceMinCount
    simp only [Id.run, bind]
    rw [enforceMinCount_forIn (reducedCellValue (axisSizes.prod : Int) minCount fillValue) cells []]
    rfl
  · -- each index matches: `getElem?` commutes with `map`, and the mapped function
    -- is definitionally `reducedCellValue`'s `if`
    intro i
    rw [List.getElem?_map]
    rfl"""


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(body: str) -> str:
    """Replace ONLY the impl-region def (frozen proof kept)."""
    return _swap(_BASE, _IMPL, body)


def _impl_proof(body: str, proof: str) -> str:
    """Replace the impl-region def AND the proof-region theorem block."""
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, proof)


# The frozen proof's opening `intro`. The admissibility positive prepends a
# ground `have` here: the impl region stays byte-identical to the frozen one and
# the theorem STATEMENT is untouched, so the only thing added is a discharged
# instance of the obligation at a concrete input, closed by evaluation.
_INTRO = "  intro axisSizes cells minCount fillValue\n"


def _ground(have: str) -> str:
    """Prepend a ground `have` to the frozen proof body (impl kept frozen)."""
    return _swap(_BASE, _INTRO, have + _INTRO)


# --------------------------------------------------------------------------
# Reject witnesses. Each states the spec predicate is violated at ONE concrete
# input; it must ELABORATE against the rival and FAIL against the frozen
# solution. The per-cell `if` is over `Int` (decidable), but the two branch
# results are `Float` (fillValue vs the cell's value), which the kernel cannot
# compare (Float equality reduces only under `native_decide`, which is banned).
# So the value-branch rivals fix concrete Float LITERALS for the cell value and
# the fill and state their distinctness `2.0 ≠ 1.0` as a HYPOTHESIS, discharging
# the contradiction from it. The hypothesis is jointly satisfiable (it is in
# fact true, just not kernel-decidable), so the consistency probe the gate runs
# cannot derive False. Keeping the spec arguments as literals (not bound
# variables) also lets the coverage tool read which input point each witness
# probes, so the four rivals register as four distinct points.
# --------------------------------------------------------------------------

# C0 attack: the multi-axis request must complete with `.ok`. `cells = []` makes
# the whole thing decidable — the rival returns `.error`, so no `out` with
# `result = .ok out` exists; gold returns `.ok []`, so the negation fails on gold.
_W_ERROR = """example : ¬ problem_spec_enforceMinCount [2, 3] [] 1 (0.0 : Float)
    (implementation_enforceMinCount [2, 3] [] 1 (0.0 : Float)) := by
  unfold problem_spec_enforceMinCount implementation_enforceMinCount
  simp"""

# C1 attack (product = whole block): axisSizes = [2, 3] (prod 6), one cell value
# 2.0 with missing 3, minCount 1, fill 1.0. Gold present = 6 − 3 = 3 ≥ 1 → keeps
# 2.0. A rival that counts only the first axis size uses 2 − 3 = −1 < 1 → fills
# 1.0. With 2.0 ≠ 1.0 the outputs differ, so gold (out[0] = 2.0) refutes the
# rival's `.ok [1.0]`.
_W_FIRST_AXIS = """example (h : (2.0 : Float) ≠ (1.0 : Float)) :
    ¬ problem_spec_enforceMinCount [2, 3] [(2.0, 3)] 1 1.0
      (implementation_enforceMinCount [2, 3] [(2.0, 3)] 1 1.0) := by
  rintro ⟨out, hok, hall⟩
  have hcompute : implementation_enforceMinCount [2, 3] [(2.0, 3)] 1 1.0 = .ok [1.0] := rfl
  rw [hcompute, Except.ok.injEq] at hok
  subst hok
  have hgold := hall 0
  simp only [List.getElem?_cons_zero, Option.map_some, List.prod_cons,
    List.prod_nil] at hgold
  norm_num [reducedCellValue] at hgold
  exact h hgold.symm"""

# C1 attack (product = ALL axes, not a leading prefix): axisSizes = [1, 1, 3]
# (prod 3), one cell value 2.0 with missing 2, minCount 1, fill 1.0. Gold present
# = 3 − 2 = 1 ≥ 1 → keeps 2.0. A rival that products only the first two axes uses
# 1·1 = 1, then 1 − 2 = −1 < 1 → fills 1.0. Distinguishes at a THREE-axis shape
# (the F2P arity), so a first-two-axes rival that agrees with gold on the one-
# and two-axis cases is refuted here.
_W_FIRST_TWO = """example (h : (2.0 : Float) ≠ (1.0 : Float)) :
    ¬ problem_spec_enforceMinCount [1, 1, 3] [(2.0, 2)] 1 1.0
      (implementation_enforceMinCount [1, 1, 3] [(2.0, 2)] 1 1.0) := by
  rintro ⟨out, hok, hall⟩
  have hcompute : implementation_enforceMinCount [1, 1, 3] [(2.0, 2)] 1 1.0 = .ok [1.0] := rfl
  rw [hcompute, Except.ok.injEq] at hok
  subst hok
  have hgold := hall 0
  simp only [List.getElem?_cons_zero, Option.map_some, List.prod_cons,
    List.prod_nil] at hgold
  norm_num [reducedCellValue] at hgold
  exact h hgold.symm"""

# C1 attack (STRICT boundary): axisSizes = [2, 2] (prod 4), one cell value 2.0
# with missing 1, minCount 3, fill 1.0. Gold present = 4 − 1 = 3, and 3 < 3 is
# FALSE → keeps 2.0. A rival using `≤` flips exactly this boundary → fills 1.0.
# Refuted at the present == minCount point with 2.0 ≠ 1.0.
_W_BOUNDARY = """example (h : (2.0 : Float) ≠ (1.0 : Float)) :
    ¬ problem_spec_enforceMinCount [2, 2] [(2.0, 1)] 3 1.0
      (implementation_enforceMinCount [2, 2] [(2.0, 1)] 3 1.0) := by
  rintro ⟨out, hok, hall⟩
  have hcompute : implementation_enforceMinCount [2, 2] [(2.0, 1)] 3 1.0 = .ok [1.0] := rfl
  rw [hcompute, Except.ok.injEq] at hok
  subst hok
  have hgold := hall 0
  simp only [List.getElem?_cons_zero, Option.map_some, List.prod_cons,
    List.prod_nil] at hgold
  norm_num [reducedCellValue] at hgold
  exact h hgold.symm"""

# C1 attack (the KEPT VALUE is the cell's own `cell.1`, never the sentinel).
# Added by the audit: the three witnesses above all refute a rival that FILLS
# where gold KEEPS, so each of them pins "do not fill here". None of them pins
# the other direction — that when a cell IS kept, what survives is the cell's
# own computed value rather than the sentinel. A rival that unconditionally
# writes the sentinel therefore went unattacked. axisSizes = [2, 3] (prod 6),
# one cell value 2.0 with missing 0, minCount 1: gold present = 6 ≥ 1 → keeps
# 2.0, and an always-fill rival emits 1.0.
_W_ALWAYS_FILL = """example (h : (2.0 : Float) ≠ (1.0 : Float)) :
    ¬ problem_spec_enforceMinCount [2, 3] [(2.0, 0)] 1 1.0
      (implementation_enforceMinCount [2, 3] [(2.0, 0)] 1 1.0) := by
  rintro ⟨out, hok, hall⟩
  have hcompute : implementation_enforceMinCount [2, 3] [(2.0, 0)] 1 1.0 = .ok [1.0] := rfl
  rw [hcompute, Except.ok.injEq] at hok
  subst hok
  have hgold := hall 0
  simp only [List.getElem?_cons_zero, Option.map_some, List.prod_cons,
    List.prod_nil] at hgold
  norm_num [reducedCellValue] at hgold
  exact h hgold.symm"""

# C1 attack (the DISCARD value is the SUPPLIED sentinel, not some constant).
# Added by the THIRD audit. `reject-always-fill` pins what a KEPT cell keeps;
# nothing pinned what a DISCARDED cell receives. C1 says the discarded position
# holds `fillValue` — the sentinel the caller supplied — and a rival that writes
# a hardcoded 0.0 there satisfies "discard exactly the right cells" while
# ignoring the sentinel binder entirely. axisSizes = [2, 3] (prod 6), cell value
# 2.0 with missing 5, minCount 3: present = 6 − 5 = 1 < 3, so the cell IS
# discarded and must become the supplied 1.0; the rival emits 0.0. This is the
# only case in the battery whose discriminating hypothesis is about fillValue
# rather than about the cell value, so it is also the only one that would fail
# if `fillValue` were dropped from C1's right-hand side.
_W_CONST_SENTINEL = """example (h : (1.0 : Float) ≠ (0.0 : Float)) :
    ¬ problem_spec_enforceMinCount [2, 3] [(2.0, 5)] 3 1.0
      (implementation_enforceMinCount [2, 3] [(2.0, 5)] 3 1.0) := by
  rintro ⟨out, hok, hall⟩
  have hcompute : implementation_enforceMinCount [2, 3] [(2.0, 5)] 3 1.0 = .ok [0.0] := rfl
  rw [hcompute, Except.ok.injEq] at hok
  subst hok
  have hgold := hall 0
  simp only [List.getElem?_cons_zero, Option.map_some, List.prod_cons,
    List.prod_nil] at hgold
  norm_num at hgold
  exact h hgold.symm"""

# C1 attack (each cell is decided by ITS OWN missing count). Added by the THIRD
# audit. Every rival above varies the TOTAL, the BOUNDARY, or the branch VALUE —
# all of which are per-cell-uniform errors, so each is refuted at a ONE-cell
# input and none of them ever needs a second cell to exist. That leaves C1's
# positional grounding (`out[i]?` is decided by `cells[i]?`, index for index)
# untested: a rival that decides every cell by the FIRST cell's missing count
# uses the right total, the right strict boundary, and the right two branch
# values, and agrees with the spec on every single-cell input. axisSizes =
# [2, 3] (prod 6), cells [(2.0, 0), (3.0, 6)], minCount 1: the spec keeps cell 0
# (6 − 0 = 6 ≥ 1 → 2.0) and discards cell 1 (6 − 6 = 0 < 1 → 1.0); the rival
# reads cell 0's missing count (0) for BOTH, so it keeps cell 1 as 3.0. Refuted
# at index 1 — the first witness in this battery to instantiate C1 at a nonzero
# index.
_W_HEAD_MISSING = """example (h : (3.0 : Float) ≠ (1.0 : Float)) :
    ¬ problem_spec_enforceMinCount [2, 3] [(2.0, 0), (3.0, 6)] 1 1.0
      (implementation_enforceMinCount [2, 3] [(2.0, 0), (3.0, 6)] 1 1.0) := by
  rintro ⟨out, hok, hall⟩
  have hcompute : implementation_enforceMinCount [2, 3] [(2.0, 0), (3.0, 6)] 1 1.0
      = .ok [2.0, 3.0] := rfl
  rw [hcompute, Except.ok.injEq] at hok
  subst hok
  have hgold := hall 1
  simp only [List.getElem?_cons_succ, List.getElem?_cons_zero, Option.map_some,
    List.prod_cons, List.prod_nil] at hgold
  norm_num at hgold
  exact h hgold"""

# C1 attack (the output has ONE ENTRY PER INPUT CELL). Added by the THIRD audit.
# C1 is stated as an equality of `Option`s at every index `i`, which pins the
# LENGTH as well as the values: at `i` past the end of `cells` the right-hand
# side is `none`, so a longer output is refuted, and at `i` inside `cells` the
# right-hand side is `some _`, so a shorter one is. No shipped rival changes the
# output length, so this pin was carried entirely by argument. This rival drops
# the last cell; at the one-cell input [(2.0, 0)] it returns the empty list,
# where the spec demands `some 2.0` at index 0. Needs no Float hypothesis at all
# — `none = some _` is refuted by `simp` outright — so it is also the battery's
# second fully-decidable witness alongside the C0 one.
_W_DROP_LAST = """example : ¬ problem_spec_enforceMinCount [2, 3] [(2.0, 0)] 1 (1.0 : Float)
      (implementation_enforceMinCount [2, 3] [(2.0, 0)] 1 (1.0 : Float)) := by
  rintro ⟨out, hok, hall⟩
  have hcompute : implementation_enforceMinCount [2, 3] [(2.0, 0)] 1 (1.0 : Float)
      = .ok [] := rfl
  rw [hcompute, Except.ok.injEq] at hok
  subst hok
  have hgold := hall 0
  simp at hgold"""


SPEC_TESTS = [
    # -------------------------------------------------------------------------
    # SOUNDNESS positive — structurally different but CORRECT: the imperative
    # accumulation loop is replaced by a single functional `List.map`, and the
    # proof closes directly (the desugaring bridge lemma is unnecessary, so the
    # map goal is `rfl`). Same spec, same theorem STATEMENT, honest proof. MUST
    # verify — else the postcondition is unsatisfiable by a genuinely correct
    # impl (SPEC-TOO-STRONG).
    # -------------------------------------------------------------------------
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) :=\n"
            "  let total : Int := (axisSizes.prod : Int)\n"
            "  .ok (cells.map (reducedCellValue total minCount fillValue))",
            "theorem correct_enforceMinCount :\n"
            "    ∀ (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "      (minCount : Nat) (fillValue : Float),\n"
            "      problem_spec_enforceMinCount axisSizes cells minCount fillValue\n"
            "        (implementation_enforceMinCount axisSizes cells minCount fillValue) := by\n"
            "  intro axisSizes cells minCount fillValue\n"
            "  refine ⟨cells.map (reducedCellValue (axisSizes.prod : Int) minCount fillValue), ?_, ?_⟩\n"
            "  · unfold implementation_enforceMinCount\n"
            "    rfl\n"
            "  · intro i\n"
            "    rw [List.getElem?_map]\n"
            "    rfl",
        ),
        "rationale": "a structurally-different but correct impl (functional List.map "
                     "instead of the accumulate-in-a-loop shape) satisfies both spec "
                     "clauses C0 (.ok) and C1 (per-cell decision) and is reproved "
                     "honestly with the theorem statement byte-identical. If it cannot "
                     "verify, the postcondition rejects a correct implementation "
                     "(SPEC-TOO-STRONG). The reshape is not cosmetic and the positive is "
                     "not neutered: the audit confirmed the FROZEN proof script does not "
                     "close against this impl (the loop-desugaring bridge step it rewrites "
                     "with has no `forIn` left to match, so the tactic block errors), so "
                     "the case genuinely reproves the obligation for a new impl shape "
                     "rather than inheriting the frozen proof.",
    },
    # -------------------------------------------------------------------------
    # SOUNDNESS positive — keeps the imperative accumulate loop but inlines the
    # per-cell decision with the comparison reassociated to the ORIGINAL signed
    # form `(prod − missing − minCount) < 0` instead of `prod − missing <
    # minCount`. Value-preserving over Int (the proof shows the two `if`
    # conditions coincide by `omega`), so it MUST verify. Guards the strict-`<`
    # sub-fact of C1 from the correct side: the honest re-expression of the
    # boundary is admissible.
    # -------------------------------------------------------------------------
    {
        "id": "pos-reassociated-signed-compare",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let total : Int := (axisSizes.prod : Int)\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells do\n"
            "    let keep := if total - (cell.2 : Int) - (minCount : Int) < 0 then fillValue else cell.1\n"
            "    out := out ++ [keep]\n"
            "  return .ok out",
            "theorem correct_enforceMinCount :\n"
            "    ∀ (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "      (minCount : Nat) (fillValue : Float),\n"
            "      problem_spec_enforceMinCount axisSizes cells minCount fillValue\n"
            "        (implementation_enforceMinCount axisSizes cells minCount fillValue) := by\n"
            "  intro axisSizes cells minCount fillValue\n"
            "  have hfun : (fun cell : Float × Nat => if (axisSizes.prod : Int) - (cell.2 : Int) - (minCount : Int) < 0 then fillValue else cell.1)\n"
            "      = (fun cell : Float × Nat => if (axisSizes.prod : Int) - (cell.2 : Int) < (minCount : Int) then fillValue else cell.1) := by\n"
            "    funext cell\n"
            "    by_cases h : (axisSizes.prod : Int) - (cell.2 : Int) < (minCount : Int)\n"
            "    · have h2 : (axisSizes.prod : Int) - (cell.2 : Int) - (minCount : Int) < 0 := by omega\n"
            "      rw [if_pos h, if_pos h2]\n"
            "    · have h2 : ¬ ((axisSizes.prod : Int) - (cell.2 : Int) - (minCount : Int) < 0) := by omega\n"
            "      rw [if_neg h, if_neg h2]\n"
            "  refine ⟨cells.map (fun cell => if (axisSizes.prod : Int) - (cell.2 : Int) - (minCount : Int) < 0 then fillValue else cell.1), ?_, ?_⟩\n"
            "  · unfold implementation_enforceMinCount\n"
            "    simp only [Id.run, bind]\n"
            "    rw [enforceMinCount_forIn _ cells []]\n"
            "    rfl\n"
            "  · intro i\n"
            "    rw [List.getElem?_map, hfun]",
        ),
        "rationale": "an equivalent arithmetic form of the per-cell test (the original "
                     "signed `(prod − missing − minCount) < 0`) is value-preserving over "
                     "Int and must still satisfy C1; the proof shows the two branch "
                     "conditions coincide via omega. A rejection here would mean the "
                     "spec pins one particular syntactic rendering of the boundary rather "
                     "than the decision (SPEC-TOO-STRONG). Confirmed non-vacuous by the "
                     "audit: the impl is NOT definitionally equal to the frozen one (its "
                     "`if` scrutinee is a different Int proposition, so no closing `rfl` "
                     "identifies them), and the FROZEN proof script does NOT close against "
                     "it — the reassociated per-cell body no longer matches the bridge "
                     "lemma that script rewrites with, so the `omega` step is doing real "
                     "work rather than restating the obligation.",
    },
    # -------------------------------------------------------------------------
    # ADMISSIBILITY positive — LANDED BY THE SECOND AUDIT (ports nagini's
    # `admiss-f2p-three-axes`; the first port dropped the whole lane as "no
    # precondition to admit", which is not the analogue on a total carrier).
    #
    # What this tests that the two soundness positives do not: those reshape the
    # IMPL and re-prove the ∀-obligation, so they would still pass if the
    # obligation happened to be unsatisfiable at some particular legitimate
    # input — a ∀ over a spec that no impl output can meet at that point is
    # still closable only if the spec's clauses are jointly satisfiable there,
    # and nothing above ever CHECKS a concrete point. This case does: it
    # discharges `problem_spec_enforceMinCount` at the F2P-shaped input by
    # EVALUATION (`rfl` computes the impl's `.ok [...]`, then each index is
    # matched), as a `have`, and only then closes the frozen obligation verbatim.
    # If the modeled behavior were unsatisfiable at exactly a normal F2P input,
    # this is the case that fails — the analogue of PRECOND-TOO-STRONG.
    #
    # The input is the F2P shape: THREE reduced axes (sizes [4,3,2], whole-block
    # product 24) and minCount 3, with TWO cells chosen to exercise BOTH branches
    # of the per-cell decision at that one input — (2.0, 5) is kept (24−5=19 ≥ 3)
    # and (3.0, 22) is discarded (24−22=2 < 3, so it becomes the sentinel 1.0).
    # A one-branch ground instance would leave the other branch's satisfiability
    # at the F2P shape untested.
    #
    # Nothing is assumed: the impl region is byte-identical to the frozen one,
    # the theorem STATEMENT is byte-identical, no new declaration or axiom, and
    # the ground instance is a `have` inside the existing tactic body.
    # -------------------------------------------------------------------------
    {
        "id": "admiss-f2p-three-axes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ground(
            "  have _ground : problem_spec_enforceMinCount [4, 3, 2]\n"
            "      [((2.0 : Float), 5), ((3.0 : Float), 22)] 3 (1.0 : Float)\n"
            "      (implementation_enforceMinCount [4, 3, 2]\n"
            "        [((2.0 : Float), 5), ((3.0 : Float), 22)] 3 (1.0 : Float)) := by\n"
            "    have hval : implementation_enforceMinCount [4, 3, 2]\n"
            "        [((2.0 : Float), 5), ((3.0 : Float), 22)] 3 (1.0 : Float)\n"
            "        = Except.ok [(2.0 : Float), (1.0 : Float)] := rfl\n"
            "    refine ⟨[(2.0 : Float), (1.0 : Float)], hval, ?_⟩\n"
            "    intro i\n"
            "    match i with\n"
            "    | 0 => rfl\n"
            "    | 1 => rfl\n"
            "    | (n + 2) => rfl\n"
        ),
        "rationale": "the obligation is DISCHARGED at an F2P-shaped input — three "
                     "reduced axes of sizes [4,3,2] (whole-block product 24) with "
                     "minCount 3, and two cells straddling the threshold so both "
                     "branches of the per-cell decision are evaluated at that one "
                     "input: (2.0, 5) is kept (24−5 = 19 ≥ 3) and (3.0, 22) is "
                     "replaced by the sentinel (24−22 = 2 < 3). Closed by evaluation "
                     "as a `have` (the impl's `.ok [2.0, 1.0]` is computed by `rfl` and "
                     "every index is then matched, including the out-of-range tail), "
                     "and only then is the frozen obligation closed verbatim. MUST "
                     "verify: a failure would mean the modeled behavior is "
                     "unsatisfiable at exactly a legitimate F2P-shaped input, which is "
                     "the total-carrier analogue of PRECOND-TOO-STRONG — the direction "
                     "neither the soundness positives (which reshape the impl and "
                     "re-prove the ∀) nor the uniqueness rivals (which attack spec "
                     "STRENGTH) can detect. Nothing is assumed: impl region "
                     "byte-identical to the frozen one, theorem statement "
                     "byte-identical, no new declaration. Ports nagini's "
                     "admiss-f2p-three-axes, whose Requires-discharging self-call has "
                     "this as its analogue here.",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — C0 attack. Reintroduce an error return for the
    # multi-axis (axisSizes.length > 1) request. Violates C0 (result = .ok out):
    # for a multi-axis input the rival yields `.error`, so no `out` with
    # `result = .ok out` exists. The frozen proof no longer closes (impl
    # reshaped), and the witness pins the violation at [2,3] with no cells.
    # -------------------------------------------------------------------------
    {
        "id": "reject-error-on-multi-axis",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  if axisSizes.length > 1 then\n"
            "    return .error \"reduction over more than one dimension is unavailable\"\n"
            "  let total : Int := (axisSizes.prod : Int)\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells do\n"
            "    out := out ++ [reducedCellValue total minCount fillValue cell]\n"
            "  return .ok out"
        ),
        "witness": _W_ERROR,
        "refinement": "a faithful real patch that keeps the multi-dimension guard leaves "
                     "the reduction-over-several-axes request raising an error instead of "
                     "producing a thresholded result. The F2P reduces over three axes at "
                     "once and asserts the outcome equals the all-axes reference; a raised "
                     "error produces no value, so the comparison never runs. Does NOT "
                     "resolve.",
        "rationale": "violates C0 (result = Except.ok out): on any multi-axis input the "
                     "rival returns `.error`, so no `out` satisfies the existential. A "
                     "verify here is SPEC-TOO-WEAK — the completes-without-error clause "
                     "would be unenforced. Witness: axisSizes=[2,3], cells=[] "
                     "(fully decidable, no Float branch).",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — C1 attack, the real pre-fix count. Count only the FIRST
    # reduced-axis size (axisSizes.headD 1) rather than the whole-block product.
    # Coincides with the product when there is a single axis; UNDERCOUNTS for ≥2
    # axes with a non-unit later size. Witness: axisSizes=[2,3], cell missing 3,
    # minCount 1 — gold keeps `v` (6−3=3≥1), rival fills `f` (2−3<1).
    # -------------------------------------------------------------------------
    {
        "id": "reject-first-axis-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let total : Int := (axisSizes.headD 1 : Int)\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells do\n"
            "    out := out ++ [reducedCellValue total minCount fillValue cell]\n"
            "  return .ok out"
        ),
        "witness": _W_FIRST_AXIS,
        "refinement": "MEASURED, and the F2P alone does NOT separate this rival — see the "
                     "audit note at the bottom of this file. The F2P reduces over ALL of "
                     "the array's axes, so the per-cell block total there is the whole "
                     "carrier size and is computed by a path that does not consult the "
                     "per-axis count at all; every cell-count variant agrees on that "
                     "shape. The count is separated one step off the F2P, on a PARTIAL "
                     "multi-axis reduction (some axes reduced, some surviving), which the "
                     "modeled domain covers and which the issue's own request "
                     "(reduce over a proper subset of several axes, thresholded per "
                     "surviving cell) is. There the block total is the product of the "
                     "reduced-axis sizes and a first-axis count undercounts it, "
                     "invalidating cells the all-axes rule keeps. Measured against the "
                     "real reduction at axisSizes=[4,3] with 4 of the 12 entries reducing "
                     "into a cell missing and minCount=3: the reference keeps the cell "
                     "(12−4=8 ≥ 3) and a first-axis count fills it (4−4=0 < 3). So the "
                     "rival is observably WRONG on the modeled domain and the spec must "
                     "reject it; but its rejection is attributable to the SPEC's "
                     "whole-block clause, not to the F2P's own assertion.",
        "rationale": "violates C1 on every input where axisSizes.prod ≠ the first axis "
                     "size (≥2 axes, a later size >1): the kept/filled decision uses the "
                     "wrong total. A verify here is SPEC-TOO-WEAK — the whole-block "
                     "product count would be unenforced. Witness: axisSizes=[2,3], "
                     "cell missing 3, minCount 1 (v ≠ f).",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — C1 attack, subtler partial-domain miss. Product of only
    # the FIRST TWO reduced axes (drops axis 3+). Correct for ≤2 axes; undercounts
    # for ≥3 axes with a non-unit third+ size — exactly the F2P arity. Witness:
    # axisSizes=[1,1,3], cell missing 2, minCount 1 — gold keeps `v` (3−2=1≥1),
    # rival fills `f` (1·1−2<1). Probes that C1 pins the WHOLE product, not a
    # leading prefix of axes; distinct input point from reject-first-axis-only.
    # -------------------------------------------------------------------------
    {
        "id": "reject-first-two-axes-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let total : Int := (match axisSizes with | a :: b :: _ => a * b | _ => axisSizes.prod : Int)\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells do\n"
            "    out := out ++ [reducedCellValue total minCount fillValue cell]\n"
            "  return .ok out"
        ),
        "witness": _W_FIRST_TWO,
        "refinement": "MEASURED, and as with the first-axis rival the F2P alone does NOT "
                     "separate this one (see the audit note at the bottom of this file): "
                     "the F2P reduces over ALL axes, where the block total is the whole "
                     "carrier size and no per-axis product is consulted. The prefix-vs-"
                     "whole-product distinction is separated on a PARTIAL multi-axis "
                     "reduction over THREE OR MORE reduced axes with a surviving axis — "
                     "inside the modeled domain. Measured against the real reduction with "
                     "three reduced axes of sizes [2,2,3] (whole product 12) and 9 of "
                     "those 12 entries missing at a cell with minCount=3: the reference "
                     "keeps the cell (12−9=3, and 3 < 3 is false) while a first-two-axes "
                     "product fills it (2·2−9 < 3). Observably WRONG on the modeled "
                     "domain, so the spec must reject it; the rejection is attributable "
                     "to C1's whole-product clause rather than to the F2P assertion.",
        "rationale": "violates C1 on the length ≥3 sub-domain (where the whole product ≠ "
                     "the product of the first two axes). A verify here is SPEC-TOO-WEAK "
                     "— C1 would pin only a prefix of the reduced axes. Witness stated at "
                     "a three-axis shape [1,1,3], cell missing 2, minCount 1 (a DISTINCT "
                     "input point from the first-axis rival, since that rival agrees with "
                     "gold on this near-miss's domain).",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — C1 attack, strict-boundary near-miss. Use `≤ 0` instead
    # of `< 0`, flipping the exactly-minCount position. Right block product;
    # wrong only at present == minCount. Witness: axisSizes=[2,2] (prod 4), cell
    # missing 1, minCount 3 — present = 3, gold keeps `v` (3<3 false), rival fills
    # `f` (3≤3 true). Confirms C1 pins the STRICT boundary.
    # -------------------------------------------------------------------------
    {
        "id": "reject-boundary-le",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let total : Int := (axisSizes.prod : Int)\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells do\n"
            "    let keep := if total - (cell.2 : Int) - (minCount : Int) ≤ 0 then fillValue else cell.1\n"
            "    out := out ++ [keep]\n"
            "  return .ok out"
        ),
        "witness": _W_BOUNDARY,
        "refinement": "MEASURED. The correct test keeps a cell iff present ≥ minCount "
                     "(strictly: fill iff `prod − missing − minCount < 0`); a `≤` patch "
                     "also fills the cell where present == minCount exactly. The F2P does "
                     "NOT separate this rival either (see the audit note at the bottom of "
                     "this file): it compares two reductions that BOTH go through the "
                     "threshold, so a boundary shifted the same way on both sides cancels "
                     "and the comparison still holds. The boundary is separated by any "
                     "single thresholded reduction whose cell has present == minCount "
                     "exactly — a point the modeled domain covers and the spec's C1 pins. "
                     "Measured against the real reduction with reduced-axis sizes [2,2,3] "
                     "(total 12), 9 missing at a cell and minCount=3: present is exactly "
                     "3, the reference KEEPS the cell and a `≤` patch replaces it with the "
                     "fill sentinel. Observably WRONG on the modeled domain, so the spec "
                     "must reject it; attributable to C1's strict boundary, not the F2P.",
        "rationale": "violates C1 at the present == minCount boundary: C1 demands strict "
                     "`<`, the rival uses `≤`. A verify here is SPEC-TOO-WEAK — the strict "
                     "boundary would be unenforced. Witness: axisSizes=[2,2], cell missing "
                     "1, minCount 3 → present 3 (v ≠ f). Distinct minCount and input "
                     "point from the other rivals.",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — ADDED BY THE AUDIT. C1 attack on the sub-fact none of
    # the four rivals above touches: what a KEPT cell keeps. All four existing
    # witnesses refute a rival that fills where the reference keeps, so each pins
    # only "do not discard here". A rival that unconditionally writes the fill
    # sentinel — discarding EVERY cell regardless of how many entries were
    # present — was passing the battery unexamined. Witness: axisSizes=[2,3]
    # (prod 6), cell (2.0, 0) fully present, minCount 1 → the reference keeps
    # 2.0 while the rival emits the sentinel 1.0.
    # -------------------------------------------------------------------------
    {
        "id": "reject-always-fill",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let mut out : List Float := []\n"
            "  for _cell in cells do\n"
            "    out := out ++ [fillValue]\n"
            "  return .ok out"
        ),
        "witness": _W_ALWAYS_FILL,
        "refinement": "MEASURED, and unlike the count/boundary rivals this one is "
                     "separated by the shipped tests directly. A faithful real patch that "
                     "invalidates every output cell unconditionally — never letting a cell "
                     "keep its own reduced value — discards cells that have far more than "
                     "the required minimum present. Applied to the real reduction and run "
                     "against the shipped suite, this breaks 20 of the currently-passing "
                     "single-axis threshold tests (the reference keeps their cells; the "
                     "rival returns the sentinel) while the multi-axis tests still pass. "
                     "Does NOT resolve.",
        "rationale": "violates C1's kept-value sub-fact: C1 requires out[i] to be the "
                     "cell's own `cell.1` whenever `prod − missing ≥ minCount`, and this "
                     "rival returns `fillValue` there. A verify here is SPEC-TOO-WEAK — "
                     "the spec would pin only WHEN a cell is discarded and never WHAT a "
                     "surviving cell holds, so an impl could erase every value and still "
                     "satisfy it. Witness: axisSizes=[2,3], cell (2.0, 0) fully present, "
                     "minCount 1 → present 6 ≥ 1, so the cell must keep 2.0 (v ≠ f).",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — ADDED BY THE THIRD AUDIT. C1 attack on the DISCARD
    # value. `reject-always-fill` pins what a KEPT cell keeps; nothing pinned
    # what a DISCARDED cell receives, so a rival that discards exactly the right
    # cells but writes a hardcoded 0.0 into them — ignoring the supplied
    # sentinel binder altogether — was passing the battery unexamined. This is
    # the only case whose discriminating hypothesis is about `fillValue` rather
    # than about the cell value, so it is the only one that would fail if
    # `fillValue` were dropped from C1's right-hand side.
    # -------------------------------------------------------------------------
    {
        "id": "reject-constant-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let total : Int := (axisSizes.prod : Int)\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells do\n"
            "    out := out ++ [if total - (cell.2 : Int) < (minCount : Int) then (0.0 : Float) else cell.1]\n"
            "  return .ok out"
        ),
        "witness": _W_CONST_SENTINEL,
        "refinement": "a faithful real patch that invalidates the right cells but writes a "
                     "hardcoded zero into them, instead of the promoted fill sentinel the "
                     "surrounding code selects for the result's dtype, marks an "
                     "under-supported cell as a genuine zero rather than as missing. The "
                     "threshold decision is identical, so every test that only checks WHICH "
                     "cells were invalidated still passes; what breaks is the value read "
                     "back at an invalidated cell. Measured against the real reduction with "
                     "reduced-axis sizes [2,3] (total 6), 5 of the 6 entries missing at a "
                     "cell and minCount=3: present is 1 < 3, so the reference yields the "
                     "missing sentinel there and this rival yields 0.0 — a difference the "
                     "reference's own all-dims comparison path also reports, since that "
                     "path selects the same promoted sentinel. Observably WRONG on the "
                     "modeled domain. Does NOT resolve.",
        "rationale": "violates C1's discard-value sub-fact: C1 requires out[i] to be "
                     "`fillValue` — the SUPPLIED sentinel — whenever `prod − missing < "
                     "minCount`, and this rival returns a constant 0.0 there. A verify "
                     "here is SPEC-TOO-WEAK: the spec would pin WHICH cells are discarded "
                     "and WHAT a surviving cell holds, but leave the discarded cell's "
                     "value free, so an impl could ignore the fillValue binder entirely. "
                     "Witness: axisSizes=[2,3], cell (2.0, 5), minCount 3 → present 1 < 3, "
                     "so the cell must be discarded to the supplied 1.0, not to 0.0 "
                     "(f ≠ 0). The hypothesis is about fillValue, not the cell value — a "
                     "discriminator no other case in this battery uses.",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — ADDED BY THE THIRD AUDIT. C1 attack on POSITIONAL
    # GROUNDING. Every other rival errs uniformly across cells (wrong total,
    # wrong boundary, wrong branch value), so each is refuted at a ONE-cell input
    # and none ever needs a second cell to exist. That left "cell i is decided by
    # cells[i], index for index" untested. This rival decides every cell by the
    # FIRST cell's missing count: right total, right strict boundary, right two
    # branch values, and it agrees with the spec on EVERY single-cell input — so
    # no existing witness's input point can see it.
    # -------------------------------------------------------------------------
    {
        "id": "reject-head-missing-for-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let total : Int := (axisSizes.prod : Int)\n"
            "  let m0 : Nat := (cells.headD ((0.0 : Float), 0)).2\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells do\n"
            "    out := out ++ [if total - (m0 : Int) < (minCount : Int) then fillValue else cell.1]\n"
            "  return .ok out"
        ),
        "witness": _W_HEAD_MISSING,
        "refinement": "a faithful real patch that reads the per-cell missing count at one "
                     "fixed position and reuses it for the whole output — rather than "
                     "letting the reduced missing-count array vary per cell — thresholds "
                     "every cell as though it had the first cell's support. On a partial "
                     "multi-axis reduction the surviving axes give several output cells "
                     "with genuinely different missing counts, so cells that should be "
                     "discarded survive and vice versa. Measured against the real "
                     "reduction with reduced-axis sizes [2,3] (total 6), minCount=1, and "
                     "two output cells whose missing counts are 0 and 6: the reference "
                     "keeps the first (6−0 ≥ 1) and discards the second (6−6 = 0 < 1), "
                     "while this rival keeps BOTH because it reads the first cell's count "
                     "for the second. Observably WRONG on the modeled domain, and inside "
                     "the issue's own request. Does NOT resolve.",
        "rationale": "violates C1's positional grounding: C1 equates out[i]? with "
                     "(cells[i]?).map f index for index, and this rival decides index i "
                     "from cells[0] instead of cells[i]. A verify here is SPEC-TOO-WEAK — "
                     "C1 would constrain only that SOME single cell's data drives every "
                     "output position, so an impl could smear one cell's support across "
                     "the whole array. Witness: axisSizes=[2,3], cells [(2.0,0),(3.0,6)], "
                     "minCount 1, refuted at INDEX 1 — the only case here that "
                     "instantiates C1 at a nonzero index, and the only input point with "
                     "more than one cell, since this rival agrees with the frozen impl on "
                     "every single-cell input.",
    },
    # -------------------------------------------------------------------------
    # UNIQUENESS reject — ADDED BY THE THIRD AUDIT. C1 attack on the LENGTH pin.
    # C1 is an `Option` equality at EVERY index, so it pins the output length as
    # well as the values: past the end of `cells` the right-hand side is `none`,
    # and inside `cells` it is `some _`. No shipped rival changed the output
    # length, so that pin rested on argument alone. Needs no Float hypothesis —
    # `none = some _` is refuted outright — making it the battery's second fully
    # decidable witness alongside the C0 one.
    # -------------------------------------------------------------------------
    {
        "id": "reject-drop-last-cell",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))\n"
            "    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do\n"
            "  let total : Int := (axisSizes.prod : Int)\n"
            "  let mut out : List Float := []\n"
            "  for cell in cells.dropLast do\n"
            "    out := out ++ [reducedCellValue total minCount fillValue cell]\n"
            "  return .ok out"
        ),
        "witness": _W_DROP_LAST,
        "refinement": "a faithful real patch that emits one fewer output cell than the "
                     "reduction produced returns a differently-shaped array: the "
                     "thresholding pass is supposed to overwrite cells in place and "
                     "preserve the reduced result's shape exactly. Every downstream "
                     "consumer that aligns the thresholded result against the reduction's "
                     "own coordinates then mismatches, and a shape comparison against the "
                     "all-dims reference fails outright rather than comparing values. "
                     "Measured against the real reduction at reduced-axis sizes [2,3] with "
                     "a single fully-present output cell and minCount=1: the reference "
                     "returns that one cell holding its computed value, this rival returns "
                     "an empty result. Observably WRONG on the modeled domain. Does NOT "
                     "resolve.",
        "rationale": "violates C1's length pin: C1 equates out[i]? with (cells[i]?).map f "
                     "at EVERY index, so at an index inside `cells` the right-hand side is "
                     "`some _` and a truncated output supplies `none`. A verify here is "
                     "SPEC-TOO-WEAK — C1 would pin the values only where the output "
                     "happens to reach, leaving an impl free to return a shorter (or "
                     "empty) array. Witness: axisSizes=[2,3], cells [(2.0,0)], minCount 1, "
                     "refuted at index 0 where the rival's output is exhausted. Fully "
                     "decidable — `none = some _` needs no Float hypothesis, so this is "
                     "the only value-clause witness here that binds nothing at all.",
    },
]
