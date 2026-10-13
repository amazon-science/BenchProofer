# properties.py — PBT falsification battery for astropy__astropy-13977 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, where a reshaped impl needs it, the proof body), so the frozen spec
# (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and the `theorem correct_dispatchOp` STATEMENT is preserved
# verbatim. No case introduces `sorry`/`admit`/`native_decide`/`axiom` or any
# new theorem/lemma.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts a TRI-STATE integer dispatcher (0 = ordinary
# result, 2 = surface the failure, 1 = abstain) over a read-only List[int] held
# at a half fractional permission. This Lean bundle models the SAME dispatch
# decision but on a purely functional carrier:
#   * the "evaluation outcome" is an `Outcome` (completes-with-value | fails);
#   * each operand is abstracted to a single Bool "defers to default handling";
#   * the result is a 3-way `Result` (value r | unhandled | surfacedError).
# The spec is the input->output relation
#     completes r                          -> value r
#     fails & every operand defers          -> surfacedError
#     fails & some operand does NOT defer    -> unhandled
# so the three nagini outcome codes map to the three `Result` constructors, and
# `all_recognised(io_kinds)` maps to `operands.all (·.defersToDefault)`.
#
# DEFENDED SURFACE (the clauses every rival is built to attack):
#   C1  the completed-evaluation branch hands the value back unchanged;
#   C2  a failure with EVERY operand deferring surfaces the error;
#   C3  a failure with SOME non-deferring operand yields the "unhandled"
#       sentinel so that operand may be tried instead.
# Input binders of the spec predicate: the evaluation outcome (`completes`
# carries a value; `fails`) and the operand list. The list is varied over: empty
# (in the C1 witness only, where the `completes` branch never inspects it), a
# single deferring operand, a single non-deferring operand — so BOTH values of an
# operand's defer flag are exercised — and, since the audit, a MIXED two-operand
# list [defers, does-not-defer]. That last point is the only one at which the
# spec's list quantifier is actually pinned: on a singleton list `all` and `any`
# over the defer flag coincide, so a battery decided entirely by singletons
# leaves the quantifier itself unprobed.
#
# The discriminating F2P behaviour: a recoverable failure WITH a non-deferring
# (custom-handler) operand present must yield the "unhandled" sentinel (C3), not
# surface the error — that is what lets the other operand's reflected handler
# run. The mirror clause C2 (an all-deferring failure surfaces the error) is
# exercised by the single-deferring-operand witness.
#
# OMITTED nagini cases and why (see `assessment` in the payload too):
#   * the FRAME-MUTATION rival (nagini rejects a write to the half-permission
#     input list) is VACUOUS on this backend: Lean is referentially transparent,
#     there is no aliasing or fractional permission to violate, so there is no
#     counterpart rival to author.
#   * the ADMISSIBILITY / precondition-well-formedness positive DOES have a
#     counterpart and is now carried (`admiss-obligation-at-f2p-input`). The
#     earlier reading — "`correct_dispatchOp` is an unconditional
#     `∀ inner operands`, so there is no precondition to prove usable" — was
#     wrong about what this lane tests on a total carrier: the analogue of
#     PRECOND-TOO-STRONG here is the obligation being UNSATISFIABLE at an
#     F2P-shaped input, which a positive that discharges the obligation at that
#     concrete input (by evaluation, as a `have`, before closing the frozen
#     obligation verbatim) tests directly.
#   * AXIOM_TESTS are dropped: the axiom lane is G-AX's job and this bundle
#     ships no consumed axiom.
from pathlib import Path

INSTANCE = "astropy__astropy-13977"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (all strictly INSIDE the impl / proof regions).
# ---------------------------------------------------------------------------

# The completed-evaluation branch of the impl (C1).
_COMPLETES_BRANCH = (
    "  | Outcome.completes r =>\n"
    "      -- The evaluation completed: hand its value back unchanged.\n"
    "      return Result.value r\n"
)

# The failure-branch decision of the impl (surface vs unhandled).
_FAIL_DECISION = (
    "      if allDefer then\n"
    "        return Result.surfacedError\n"
    "      else\n"
    "        return Result.unhandled\n"
)

# The whole mutable fold + decision of the failure branch (for the structural
# soundness positive that rewrites it as a single functional expression).
_FAIL_BODY = (
    "      let mut allDefer := true\n"
    "      for o in operands do\n"
    "        allDefer := allDefer && o.defersToDefault\n"
    "      if allDefer then\n"
    "        return Result.surfacedError\n"
    "      else\n"
    "        return Result.unhandled\n"
)

# The per-operand fold header (back-to-front analogue: scan choice).
_FOLD_HEADER = (
    "      for o in operands do\n"
    "        allDefer := allDefer && o.defersToDefault\n"
)

# The head of the frozen proof body (anchor for the admissibility positive: the
# concrete-input `have`s are inserted BEFORE the frozen obligation's `intro`, so
# every frozen proof step that follows stays byte-identical).
_PROOF_INTRO = "  intro inner operands\n"

# The frozen failure-branch proof body (reused when a positive keeps the loop).
_FAIL_PROOF = (
    "  | fails =>\n"
    "    simp only [Id.run, bind, pure]\n"
    "    have hall : (forIn operands true (fun (o:Operand) r => "
    "ForInStep.yield (r && o.defersToDefault)) : Id Bool)\n"
    "        = operands.all (·.defersToDefault) := by rw [helper]; simp\n"
    "    rw [hall]\n"
)


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness): branch reorder --------------------
    # A correct impl that only REORDERS the failure-branch decision (test the
    # negated "some operand does not defer" guard first, yield the sentinel;
    # else surface the error). The mutable fold and every other line are
    # byte-identical, so this is observationally equal to gold. The proof keeps
    # the frozen fold lemma and closes the reordered `if` by a case split. Must
    # verify; if a faithful correct reshape cannot, the spec is TOO STRONG.
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _FAIL_DECISION,
                "      if !allDefer then\n"
                "        return Result.unhandled\n"
                "      else\n"
                "        return Result.surfacedError\n",
            ),
            "    rw [hall]\n",
            "    rw [hall]\n"
            "    by_cases h : operands.all (·.defersToDefault) <;> simp [h]\n",
        ),
        "rationale": "reordering only the failure-branch decision (same fold, "
                     "same values) yields an observationally identical impl; it "
                     "must verify against C2/C3, else the spec is too strong. "
                     "Exercises the `fails` outcome binder on the verify lane.",
    },

    # --- POSITIVE CONTROL (soundness): functional fold -------------------
    # A structurally DIFFERENT correct impl: the mutable `let mut ... for ...`
    # fold is replaced by the single functional expression
    # `operands.all (·.defersToDefault)` — the exact predicate the spec names.
    # The completed-evaluation branch is untouched. The proof discharges by a
    # direct case split (no fold lemma needed). Different shape, same behaviour;
    # must verify. This is the soundness counterpart the nagini reorder positive
    # attests, re-expressed for a carrier where the fold can be inlined.
    {
        "id": "pos-control-functional-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _FAIL_BODY,
                "      if operands.all (·.defersToDefault) then\n"
                "        return Result.surfacedError\n"
                "      else\n"
                "        return Result.unhandled\n",
            ),
            _FAIL_PROOF,
            "  | fails =>\n"
            "    by_cases h : operands.all (·.defersToDefault) <;> "
            "simp only [Id.run, h, if_true] <;> rfl\n",
        ),
        "rationale": "a correct impl whose failure decision is the functional "
                     "`operands.all (·.defersToDefault)` rather than an "
                     "accumulator fold must still verify against C2/C3; a "
                     "structurally distinct positive, else the spec is too "
                     "strong.",
    },

    # --- ADMISSIBILITY: the obligation is satisfiable AT an F2P-shaped input --
    # AUDIT ADDITION. On a total carrier the frozen obligation carries no
    # precondition hypothesis, so PRECOND-TOO-STRONG cannot arrive as "the
    # Requires is contradictory". Its analogue is the obligation being
    # UNSATISFIABLE at exactly an F2P-shaped input: a spec whose clauses
    # over-constrain the failure branch would have no result value at the
    # discriminating input, and the frozen `∀`-obligation would then be closable
    # only vacuously. This positive discharges the obligation BY EVALUATION at
    # two concrete F2P-shaped inputs before closing the frozen obligation:
    #   * a MIXED operand list [defers, does-not-defer] on a failure — the C3
    #     input the discriminating behaviour turns on;
    #   * an ALL-deferring two-operand list on a failure — the C2 mirror.
    # Both `have`s are inserted ahead of the frozen `intro`, so every frozen
    # proof step after them is byte-identical and the case is a pure ADDITION of
    # proof obligations. Verified informative, not vacuous: the identical shape
    # asserting the obligation at a FALSE point (claiming `surfacedError` on the
    # mixed list) fails to elaborate with `unsolved goals ⊢ False`, so these
    # `have`s are decided by evaluation rather than closed by any tactic.
    {
        "id": "admiss-obligation-at-f2p-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_INTRO,
            "  have hMixed : problem_spec_dispatchOp "
            "(Outcome.fails : Outcome Nat) [⟨true⟩, ⟨false⟩]\n"
            "      (implementation_dispatchOp (Outcome.fails : Outcome Nat) "
            "[⟨true⟩, ⟨false⟩]) := by\n"
            "    unfold problem_spec_dispatchOp implementation_dispatchOp\n"
            "    simp\n"
            "  have hAllDefer : problem_spec_dispatchOp "
            "(Outcome.fails : Outcome Nat) [⟨true⟩, ⟨true⟩]\n"
            "      (implementation_dispatchOp (Outcome.fails : Outcome Nat) "
            "[⟨true⟩, ⟨true⟩]) := by\n"
            "    unfold problem_spec_dispatchOp implementation_dispatchOp\n"
            "    simp\n"
            + _PROOF_INTRO,
        ),
        "rationale": "the obligation must be DISCHARGEABLE at the F2P-shaped "
                     "inputs, not merely provable in the abstract: a failure "
                     "with a mixed operand list (C3, the discriminating input) "
                     "and a failure with an all-deferring list (C2). Both "
                     "discharge by evaluation; if the spec's failure-branch "
                     "clauses over-constrained the result at either point, no "
                     "result value would satisfy them there and this would fail "
                     "=> PRECOND-TOO-STRONG. Exercises a TWO-operand list, the "
                     "only length at which C2 and C3 differ by one flag.",
    },

    # --- UNIQUENESS: flip the completed-evaluation outcome (attacks C1) ---
    # On a completed evaluation the rival yields the "unhandled" sentinel
    # instead of handing back the value. Directly violates C1
    # (completes r -> value r). Nagini analogue: returning code 1 (abstain) on
    # a successful protected evaluation.
    {
        "id": "uniqueness-completes-returns-unhandled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _COMPLETES_BRANCH,
            "  | Outcome.completes r =>\n"
            "      -- WRONG: abstain even though the evaluation completed.\n"
            "      return Result.unhandled\n",
        ),
        "refinement": "a real patch that reported the \"unhandled\" sentinel "
                      "when the protected body SUCCEEDED would abstain on every "
                      "ordinary successful call, yielding the reflected/other "
                      "operand's result or a type error instead of the computed "
                      "value — it would regress the large body of passing "
                      "success-path cases and therefore NOT resolve.",
        "rationale": "violates C1 (a completed evaluation hands its value back "
                     "unchanged); exercises the `completes` outcome binder.",
        # Holds of the rival (unhandled != value 0), fails on gold (value 0 = value 0).
        "witness": (
            "example : ¬ problem_spec_dispatchOp\n"
            "    (Outcome.completes (0 : Nat)) []\n"
            "    (implementation_dispatchOp (Outcome.completes (0 : Nat)) []) := by\n"
            "  unfold problem_spec_dispatchOp implementation_dispatchOp\n"
            "  simp"
        ),
    },

    # --- UNIQUENESS: always abstain on failure (attacks C2) --------------
    # On a failure the rival ALWAYS yields the "unhandled" sentinel, dropping
    # the surface path. Correct whenever some operand does not defer, but on an
    # ALL-deferring failure (including the empty operand list) gold surfaces the
    # error and the rival abstains. Violates C2. Nagini analogue: return code 1
    # unconditionally on a recoverable failure.
    {
        "id": "uniqueness-always-abstain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FAIL_DECISION,
            "      let _ := allDefer\n"
            "      return Result.unhandled\n",
        ),
        "refinement": "a real handler that reported the \"unhandled\" sentinel "
                      "for EVERY caught failure (never re-raising) would swallow "
                      "genuine errors when all operands defer to the default "
                      "handling: the runtime, seeing the sentinel from both "
                      "sides, raises a generic error rather than the original "
                      "one the all-deferring F2P orderings assert — so it would "
                      "NOT resolve.",
        "rationale": "violates C2 (an all-deferring failure surfaces the error); "
                     "first fails on the single-deferring-operand input, "
                     "exercising the operand defer flag at `true`.",
        # Holds of the rival (unhandled != surfacedError), fails on gold.
        "witness": (
            "example : ¬ problem_spec_dispatchOp\n"
            "    (Outcome.fails : Outcome Nat) [⟨true⟩]\n"
            "    (implementation_dispatchOp (Outcome.fails : Outcome Nat) [⟨true⟩]) := by\n"
            "  unfold problem_spec_dispatchOp implementation_dispatchOp\n"
            "  simp"
        ),
    },

    # --- UNIQUENESS: skip the first operand (attacks C3) -----------------
    # The fold scans `operands.tail`, so the operand at the head is never
    # inspected. A single non-deferring operand at the head is missed => the
    # running flag stays "all defer" => the rival surfaces the error where gold
    # yields the "unhandled" sentinel. Violates C3. Nagini analogue: the loop
    # that skips index 0 and misses a custom handler sitting there.
    {
        "id": "uniqueness-skip-first-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _FOLD_HEADER,
            "      for o in operands.tail do\n"
            "        allDefer := allDefer && o.defersToDefault\n",
        ),
        "refinement": "a real handler that never classified the first operand "
                      "would, when the sole non-deferring operand is the head "
                      "(the custom-handler-first F2P orderings), surface the "
                      "original error instead of the sentinel — the reflected "
                      "handler never runs, so the asserted behaviour is wrong "
                      "and it does NOT resolve.",
        "rationale": "violates C3 (a failure with a non-deferring operand yields "
                     "the sentinel) when that operand is at the head; exercises "
                     "the operand defer flag at `false`.",
        # Holds of the rival (surfacedError != unhandled), fails on gold.
        "witness": (
            "example : ¬ problem_spec_dispatchOp\n"
            "    (Outcome.fails : Outcome Nat) [⟨false⟩]\n"
            "    (implementation_dispatchOp (Outcome.fails : Outcome Nat) [⟨false⟩]) := by\n"
            "  unfold problem_spec_dispatchOp implementation_dispatchOp\n"
            "  simp"
        ),
    },

    # --- UNIQUENESS: quantifier swap, `any` for `all` (attacks C2 AND C3) ----
    # AUDIT ADDITION. Every pre-existing rival is decided by a SINGLETON operand
    # list, so the spec's quantifier over the operand list was probed only where
    # `all` and `any` agree (on a one-element list they are equal, and on `[]`
    # they differ but the pre-existing witnesses never use a mixed list). This
    # rival surfaces the error when SOME operand defers rather than when EVERY
    # one does. It is observably wrong on any MIXED list: at
    # [defers, does-not-defer] gold yields the sentinel (C3) and the rival
    # surfaces the error; on the empty list it is wrong in the other direction
    # (gold surfaces, `any [] = false` abstains), so it violates C2 and C3 both.
    # Aimed at the least-probed part of the surface: the list quantifier itself.
    {
        "id": "uniqueness-any-for-all-quantifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _swap(
                _BASE, _FAIL_BODY,
                "      if operands.any (·.defersToDefault) then\n"
                "        return Result.surfacedError\n"
                "      else\n"
                "        return Result.unhandled\n",
            ),
            _FAIL_PROOF,
            "  | fails =>\n"
            "    simp only [Id.run, bind, pure]\n",
        ),
        "refinement": "a real handler that surfaced the original error as soon as "
                      "SOME operand defers to the default handling — rather than "
                      "requiring that they ALL do — would, on the mixed operand "
                      "orderings where one operand supplies its own handler "
                      "alongside a deferring one (the load-bearing F2P shape), "
                      "surface the error instead of the sentinel, so the other "
                      "operand's handler never runs; and on an empty operand "
                      "collection it would abstain where the error must be "
                      "surfaced. Wrong in both directions => does NOT resolve.",
        "rationale": "violates C3 (a failure with a non-deferring operand yields "
                     "the sentinel) at the MIXED list [⟨true⟩, ⟨false⟩], and C2 "
                     "at the empty list; exercises the operand-list quantifier at "
                     "a length where `all` and `any` actually differ, which no "
                     "singleton-list witness can do.",
        # Holds of the rival (surfacedError != unhandled at the mixed list),
        # fails on gold (unhandled = unhandled).
        "witness": (
            "example : ¬ problem_spec_dispatchOp\n"
            "    (Outcome.fails : Outcome Nat) [⟨true⟩, ⟨false⟩]\n"
            "    (implementation_dispatchOp (Outcome.fails : Outcome Nat) "
            "[⟨true⟩, ⟨false⟩]) := by\n"
            "  unfold problem_spec_dispatchOp implementation_dispatchOp\n"
            "  simp"
        ),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job and this bundle ships no consumed axiom
# (the evaluation outcome and each operand's defer status are the modeled
# inputs; the proof never reasons about how they are produced).
AXIOM_TESTS = []
