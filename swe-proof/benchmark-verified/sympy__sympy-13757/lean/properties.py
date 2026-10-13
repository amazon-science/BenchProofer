# properties.py — PBT falsification battery for sympy__sympy-13757 (lean).
#
# NOT a Lean module: a record of adversarially-reasoned cases the G-PBT runner
# executes and stamps with a recorded verdict. Each spec case is a full
# Solution.lean variant built by region-surgery — it edits ONLY the impl region
# (and, where a reshaped impl needs it, the proof body), so the frozen spec
# (axioms / pure / post-conditions) stays byte-identical, same_spec holds by
# construction, and the `theorem correct_polyMul` STATEMENT is preserved
# verbatim. No case introduces `sorry`/`admit`/`native_decide`/`axiom` or any
# new theorem/lemma.
#
# PORT NOTE — carrier narrowing vs the nagini sibling.
# The nagini battery contracts FIVE functions of a numeric-precedence dispatch:
# `default_priority()`, `polynomial_priority()`, a `resolved_by_right(self_prio,
# other_prio, has_handler)` predicate, a `product_is_evaluated(...)` that takes
# the two operand priorities / evaluates flags / has-handler as by-value inputs,
# and the end-to-end `generic_times_polynomial()`. This Lean bundle models only
# the purely functional CORE — the single observable
#     implementation_polyMul (side : Side) (coercible : Bool) : MulResult
# with the two operand precedences hardcoded INSIDE the impl (`exprPriority = 10`,
# `polyPriority = 10.001`) exactly as the real class data are. The spec is the
# input->output relation
#     problem_spec_polyMul side coercible result :=
#         result = (if coercible then evaluated else symbolic)
# so the nagini dispatch inputs (`self_priority`, `other_priority`,
# `other_has_handler`) are NOT reachable binders here — they are constants folded
# into the impl. What the Lean spec exposes that nagini folded away is the
# `coercible` axis: whether the plain factor converts into a polynomial over the
# operand's generators (the `Poly(e,*gens)` guard).
#
# DEFENDED SURFACE (the clauses every rival is built to attack):
#   C-eval  a CONVERTIBLE factor (`coercible = true`) makes the product carried
#           out (`evaluated`) for EITHER operand order;
#   C-symb  a NON-convertible factor (`coercible = false`) leaves the product a
#           plain symbolic expression (`symbolic`) for EITHER operand order.
# The discriminating F2P behaviour (`test_issue_13079`) lives on the polyRight
# leg: a convertible `expr * poly` must be `evaluated`, which the precedence
# dispatch only produces when the polynomial advertises STRICTLY greater
# precedence — the datum the patch introduces. The mirror is exercised on both
# legs and both coercibility values by the reject witnesses below.
#
# Input binders of the spec predicate and how the reject witnesses vary them:
#   * `side`      — polyRight (R1, R2, R4) AND polyLeft (R3, R5);
#   * `coercible` — true (R1, R2, R5) AND false (R3, R4).
# Four distinct witness input points: (polyRight,true), (polyRight,false),
# (polyLeft,true), (polyLeft,false) — i.e. the spec's ENTIRE input domain
# (`Side × Bool` has exactly four inhabitants), each refuted at a literal point.
# The admissibility positive grounds two of those four points by evaluation.
#
# OMITTED nagini cases and why (see `assessment` in the payload too):
#   * `admiss-f2p-shaped-self-call`: PORTED as `admiss-ground-f2p-both-legs`
#     below. The original port dropped it on the ground that `correct_polyMul` is
#     an unconditional `∀ side coercible` with no precondition hypothesis, so
#     there is "no precondition to prove admissible". That reason is wrong: on a
#     TOTAL carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#     UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
#     discharges the spec predicate at that concrete input — by evaluation, as a
#     `have`, before closing the frozen obligation verbatim — tests directly.
#     Landed on audit.
#   * `reject-product-always-other` / `reject-product-relaxed-ge-on-tie`: these
#     nagini rivals abuse a variable-priority TIE / no-handler input of
#     `product_is_evaluated`. On this carrier the two operand precedences are
#     hardcoded constants (`10` vs `10.001`), so no tie or no-handler input is
#     REACHABLE: `>` and `>=` agree on the only priority pair, and "always
#     delegate right" agrees with gold on the reachable polyRight domain. The
#     rivals are not wrong on this carrier — dropped, not weakened. (The
#     coercibility residue of "always delegate right" — ignore convertibility on
#     the delegating leg — IS wrong and is ported as R4.)
#   * FRAME / PERMISSION-mutation rivals: VACUOUS. Lean is referentially
#     transparent; there is no aliasing or fractional permission to violate.
#   * DIVERGENCE / non-termination rivals: VACUOUS on lean. `implementation_polyMul`
#     is a total Lean `def`; a diverging implementation cannot be written.
#   * AXIOM_TESTS: dropped — the axiom lane is G-AX's job and this bundle ships
#     no consumed axiom (the dispatch is modeled deeply; `coercible` is an input).
from pathlib import Path

INSTANCE = "sympy__sympy-13757"

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

# The polynomial operand's advertised precedence (impl region). The strictly
# greater value is what routes a convertible `expr * poly` to `evaluated`.
_POLY_PRIORITY = "  let polyPriority : Rat := 10.001        -- a polynomial object"

# The frozen proof step that discharges the precedence guard.
_POLY_PROOF = "rw [if_pos (by norm_num : (10.001 : Rat) > 10)]"

# The polyLeft branch (the product routine runs directly, no dispatch).
_PL_BRANCH = (
    "  | Side.polyLeft =>\n"
    "    -- The polynomial's own multiplication routine runs directly: it coerces the\n"
    "    -- expression into a polynomial when convertible and multiplies; otherwise\n"
    "    -- it falls back to the plain symbolic product of expressions.\n"
    "    if coercible then\n"
    "      return MulResult.evaluated\n"
    "    else\n"
    "      return MulResult.symbolic"
)

# The polyRight branch (precedence dispatch, then coerce-or-fallback).
_PR_BRANCH = (
    "  | Side.polyRight =>\n"
    "    -- The precedence dispatch hands the product to the operand advertising the\n"
    "    -- strictly greater precedence; only then does the polynomial's reflected\n"
    "    -- multiplication run (coerce when convertible, else fall back symbolic).\n"
    "    if polyPriority > exprPriority then\n"
    "      if coercible then\n"
    "        return MulResult.evaluated\n"
    "      else\n"
    "        return MulResult.symbolic\n"
    "    else\n"
    "      -- No delegation: the unevaluated symbolic product is returned.\n"
    "      return MulResult.symbolic"
)

# The first line of the frozen proof body: the anchor an admissibility ground
# instance is prepended to (as a `have`, before the frozen tactic script runs
# verbatim).
_PROOF_INTRO = "  intro side coercible"

# The inner coerce-or-fallback of the polyRight branch (after delegation).
_PR_INNER = (
    "    if polyPriority > exprPriority then\n"
    "      if coercible then\n"
    "        return MulResult.evaluated\n"
    "      else\n"
    "        return MulResult.symbolic\n"
    "    else"
)


# ===========================================================================
# SPEC_TESTS
# ===========================================================================
SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness): branch reorder --------------------
    # A correct impl that only REORDERS the polyRight dispatch: test the
    # negated precedence guard first (fall through to symbolic), else the
    # coerce-or-fallback. Observationally identical to gold. The proof swaps the
    # frozen `if_pos` for the matching `if_neg` on the negated guard and closes
    # by the same case split. Must verify; if a faithful correct reshape cannot,
    # the spec is TOO STRONG.
    {
        "id": "pos-control-polyright-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _PR_BRANCH,
                "  | Side.polyRight =>\n"
                "    -- The precedence dispatch hands the product to the operand advertising the\n"
                "    -- strictly greater precedence; only then does the polynomial's reflected\n"
                "    -- multiplication run (coerce when convertible, else fall back symbolic).\n"
                "    if !(polyPriority > exprPriority) then\n"
                "      -- No delegation: the unevaluated symbolic product is returned.\n"
                "      return MulResult.symbolic\n"
                "    else\n"
                "      if coercible then\n"
                "        return MulResult.evaluated\n"
                "      else\n"
                "        return MulResult.symbolic",
            ),
            _POLY_PROOF,
            "rw [if_neg (by norm_num : ¬ (!((10.001 : Rat) > 10)) = true)]",
        ),
        "rationale": "reordering only the polyRight dispatch (test the negated "
                     "guard first, same values) yields an observationally "
                     "identical impl; it must verify against C-eval/C-symb, else "
                     "the spec is too strong. Exercises the polyRight `side` "
                     "binder on the verify lane.",
    },

    # --- POSITIVE CONTROL (soundness): different in-spec priority value ---
    # A correct impl of the dispatch using a DIFFERENT strictly-greater
    # precedence (10.5 instead of 10.001). Any value strictly above the plain
    # expression's precedence routes a convertible `expr * poly` to `evaluated`,
    # and its faithful real patch (`Poly._op_priority = 10.5`) also resolves.
    # Documents that the spec's latitude above the default is correct, not a
    # defect (else SPEC-TOO-STRONG: over-pinning the exact 10.001). The proof
    # re-derives the guard with `norm_num` at the new value.
    {
        "id": "pos-control-priority-different-valid-value",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _POLY_PRIORITY,
                "  let polyPriority : Rat := 10.5          -- a polynomial object",
            ),
            _POLY_PROOF,
            "rw [if_pos (by norm_num : (10.5 : Rat) > 10)]",
        ),
        "rationale": "the outcome only requires the polynomial's precedence be "
                     "strictly greater than the plain expression's; any such "
                     "value (here 10.5) is correct and its faithful real patch "
                     "resolves. Must verify, else the spec over-pins one literal.",
    },

    # --- ADMISSIBILITY: the obligation is SATISFIABLE at F2P-shaped input --
    # On a total carrier there is no precondition to admit, so the analogue of
    # PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly a
    # normal, F2P-shaped input. This case discharges the spec predicate at the
    # two concrete input points the F2P products occupy — (polyRight, true), the
    # discriminating leg, and (polyLeft, false), the non-convertible fallback —
    # BY EVALUATION, as a `have`, and only then closes the frozen obligation
    # verbatim. Nothing is assumed: no new declaration, no new axiom, statement
    # byte-identical, the ground instance is a `have` prepended to the existing
    # tactic body which then runs unchanged. Must verify; if the spec could not
    # be satisfied at a normal input the whole battery would be vacuous.
    {
        "id": "admiss-ground-f2p-both-legs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_INTRO,
            "  have _ground : problem_spec_polyMul Side.polyRight true\n"
            "      (implementation_polyMul Side.polyRight true)\n"
            "      ∧ problem_spec_polyMul Side.polyLeft false\n"
            "        (implementation_polyMul Side.polyLeft false) := by\n"
            "    constructor\n"
            "    · unfold problem_spec_polyMul implementation_polyMul\n"
            "      simp only [Id.run]\n"
            "      rw [if_pos (by norm_num : (10.001 : Rat) > 10)]\n"
            "      decide\n"
            "    · unfold problem_spec_polyMul implementation_polyMul\n"
            "      decide\n"
            + _PROOF_INTRO,
        ),
        "rationale": "the obligation is discharged BY EVALUATION at the two "
                     "concrete F2P-shaped input points — (polyRight, true), the "
                     "discriminating convertible `expr * poly` leg, and "
                     "(polyLeft, false), the non-convertible fallback — as a "
                     "`have`, after which the frozen obligation is closed "
                     "verbatim. Verifies, else the modeled behaviour would be "
                     "unsatisfiable at exactly a normal input (the total-carrier "
                     "analogue of PRECOND-TOO-STRONG). Ports nagini's "
                     "`admiss-f2p-shaped-self-call`. Note the `norm_num` step is "
                     "load-bearing on the polyRight leg: `Rat.instDecidableLt` "
                     "does not reduce, so `decide` alone is STUCK on the "
                     "precedence guard rather than deciding it.",
    },

    # --- UNIQUENESS: the pre-patch tie (attacks C-eval on polyRight) ------
    # The polynomial advertises the SAME precedence as the plain expression
    # (the value it inherits pre-patch). The polyRight dispatch never delegates,
    # so a CONVERTIBLE `expr * poly` stays `symbolic` where gold makes it
    # `evaluated`. This is exactly the reported bug locus.
    {
        "id": "reject-priority-equals-default-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _POLY_PRIORITY,
            "  let polyPriority : Rat := 10            -- a polynomial object",
        ),
        "refinement": "this is the PRE-PATCH state: the polynomial inherits the "
                      "plain expression's precedence, so on a tie the dispatch "
                      "prefers the LEFT (generic) operand and `expr * poly` stays "
                      "an inert symbolic product even when convertible — exactly "
                      "the F2P assertion `x*Poly(x) == Poly(x**2,...)` that FAILS "
                      "pre-patch. The faithful real patch does NOT resolve.",
        "rationale": "violates C-eval (a convertible factor is `evaluated`) on the "
                     "polyRight leg; the spec's discriminating clause, so this "
                     "rejection is mandatory for verify=>resolve. Point "
                     "(polyRight, true).",
        # Rival returns symbolic (guard false); gold returns evaluated.
        #
        # NOTE on the tactic shape. A bare `decide` here is NOT a usable witness
        # on this carrier: the precedence comparison is a `Rat` order, and
        # `Rat.instDecidableLt` does not reduce, so against the FROZEN impl
        # `decide` gets stuck ("did not reduce to `isTrue` or `isFalse`") for
        # EVERY claim rather than refuting this one. That failure carries no
        # information — the gold-side exit code would attest to a refutation
        # never performed. `norm_num` discharges the rational guard first, which
        # collapses the impl to a constructor literal; only then is `decide` a
        # real decision.
        #
        # Both halves re-measured with real builds on audit. The shipped witness:
        # rival exit 0; gold exit 1 with `decide` PROVING `¬pure evaluated =
        # evaluated` false — an evaluation, not a stuck reduction. The bare-`decide`
        # variant of this same witness, built for contrast: gold exit 1 with
        # `Rat.instDecidableLt ... did not reduce to isTrue or isFalse`, i.e. the
        # stuck shape the gate screens as hollow. And the FORGERY (this witness with
        # the `¬` dropped, so it claims gold is CORRECT here) inverts as it must:
        # gold exit 0, rival exit 1 (`decide` proves `pure symbolic = evaluated`
        # false). The gold-side exit code therefore tracks the claim.
        "witness": (
            "example : ¬ problem_spec_polyMul Side.polyRight true\n"
            "    (implementation_polyMul Side.polyRight true) := by\n"
            "  unfold problem_spec_polyMul implementation_polyMul\n"
            "  simp only [Id.run]\n"
            "  norm_num\n"
            "  decide"
        ),
    },

    # --- UNIQUENESS: precedence strictly below default (attacks C-eval) ---
    # A different wrong constant: the polynomial advertises a precedence BELOW
    # the plain expression's. The dispatch still refuses to delegate, so a
    # convertible `expr * poly` stays `symbolic`. Fails at the same input as the
    # tie rival, for the same reason (guard false), but from a distinct impl
    # text — the second nagini below-default rival.
    {
        "id": "reject-priority-below-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _POLY_PRIORITY,
            "  let polyPriority : Rat := 9              -- a polynomial object",
        ),
        "refinement": "a precedence below the plain expression's makes the "
                      "dispatch prefer the GENERIC operand, so `expr * poly` stays "
                      "an inert symbolic product and the F2P assertion FAILS. The "
                      "faithful real patch (a lower `_op_priority`) does NOT "
                      "resolve.",
        "rationale": "violates C-eval on the polyRight leg (guard false again). "
                     "Distinct rival text from the tie case; point "
                     "(polyRight, true).",
        # Same tactic shape as the tie rival, and for the same reason: the `Rat`
        # precedence guard must be discharged by `norm_num` before `decide` can
        # decide anything against the frozen impl (a bare `decide` is stuck
        # there for every claim, so it would discriminate nothing).
        "witness": (
            "example : ¬ problem_spec_polyMul Side.polyRight true\n"
            "    (implementation_polyMul Side.polyRight true) := by\n"
            "  unfold problem_spec_polyMul implementation_polyMul\n"
            "  simp only [Id.run]\n"
            "  norm_num\n"
            "  decide"
        ),
    },

    # --- UNIQUENESS: polyLeft ignores convertibility (attacks C-symb) -----
    # On the polyLeft leg the rival always carries the product out, dropping the
    # convertibility guard. A NON-convertible factor should stay `symbolic`
    # (the coercion falls back), but the rival reports `evaluated`. Violates
    # C-symb on polyLeft. Exercises the `coercible=false` binder value.
    {
        "id": "reject-polyleft-ignores-coercibility",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _PL_BRANCH,
            "  | Side.polyLeft =>\n"
            "    -- WRONG: always carry the product out, ignoring convertibility.\n"
            "    return MulResult.evaluated",
        ),
        "refinement": "a real multiplication routine that produced a polynomial "
                      "value for a NON-convertible factor would return a Poly "
                      "where the coercion must fall back to a plain expression "
                      "(e.g. `Poly(x)*sin(x)`): it contradicts the observed "
                      "fallback behaviour the F2P and its neighbours assert, so it "
                      "does NOT resolve.",
        "rationale": "violates C-symb (a non-convertible factor is `symbolic`) on "
                     "the polyLeft leg; exercises `side=polyLeft`, "
                     "`coercible=false`. Point (polyLeft, false).",
        # Rival returns evaluated; gold returns symbolic.
        "witness": (
            "example : ¬ problem_spec_polyMul Side.polyLeft false\n"
            "    (implementation_polyMul Side.polyLeft false) := by\n"
            "  unfold problem_spec_polyMul implementation_polyMul\n"
            "  decide"
        ),
    },

    # --- UNIQUENESS: polyRight ignores convertibility (attacks C-symb) ----
    # On the polyRight leg, AFTER the dispatch delegates, the rival carries the
    # product out regardless of convertibility. A non-convertible factor should
    # fall back to `symbolic`, but the rival reports `evaluated`. Violates
    # C-symb on the delegating leg — this is the coercibility residue of
    # nagini's "always delegate right" rival. The witness must first discharge
    # the (kept) precedence guard before `decide`.
    {
        "id": "reject-polyright-ignores-coercibility",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _PR_INNER,
            "    if polyPriority > exprPriority then\n"
            "      -- WRONG: carry out the product regardless of convertibility.\n"
            "      return MulResult.evaluated\n"
            "    else",
        ),
        "refinement": "a reflected multiplication that produced a polynomial for a "
                      "NON-convertible factor would evaluate `expr * poly` where "
                      "the real `__rmul__` falls back to a plain expression "
                      "(`sin(x)*Poly(x)` stays symbolic): it contradicts the "
                      "observed fallback and does NOT resolve.",
        "rationale": "violates C-symb on the polyRight (delegating) leg; exercises "
                     "`side=polyRight`, `coercible=false`. Point (polyRight, "
                     "false).",
        # Rival: guard true (norm_num), then evaluated; gold: symbolic.
        "witness": (
            "example : ¬ problem_spec_polyMul Side.polyRight false\n"
            "    (implementation_polyMul Side.polyRight false) := by\n"
            "  unfold problem_spec_polyMul implementation_polyMul\n"
            "  simp only [Id.run]\n"
            "  rw [if_pos (by norm_num : (10.001 : Rat) > 10)]\n"
            "  decide"
        ),
    },

    # --- UNIQUENESS: polyLeft never carries the product out (attacks C-eval)
    # On the polyLeft leg the rival always returns `symbolic`, dropping the
    # convertibility guard the other way: a CONVERTIBLE factor should be
    # `evaluated` (e.g. `Poly(x)*x`), but the rival reports `symbolic`. Violates
    # C-eval on polyLeft. Exercises the `coercible=true` binder value on the
    # polyLeft leg (the fifth F2P product `Poly(x)*S(-2)` is a polyLeft-coercible
    # case).
    {
        "id": "reject-polyleft-never-evaluates",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _PL_BRANCH,
            "  | Side.polyLeft =>\n"
            "    -- WRONG: never carry out the product, even when convertible.\n"
            "    return MulResult.symbolic",
        ),
        "refinement": "a routine that never carried out the product on the "
                      "polyLeft leg would leave `Poly(x)*x` symbolic where the "
                      "F2P asserts an evaluated polynomial — it regresses the "
                      "polyLeft F2P orderings and does NOT resolve.",
        "rationale": "violates C-eval (a convertible factor is `evaluated`) on the "
                     "polyLeft leg; exercises `side=polyLeft`, `coercible=true`. "
                     "Point (polyLeft, true).",
        # Rival returns symbolic; gold returns evaluated.
        "witness": (
            "example : ¬ problem_spec_polyMul Side.polyLeft true\n"
            "    (implementation_polyMul Side.polyLeft true) := by\n"
            "  unfold problem_spec_polyMul implementation_polyMul\n"
            "  decide"
        ),
    },
]


# ===========================================================================
# AXIOM_TESTS
# ===========================================================================
# Dropped: the axiom lane is G-AX's job. This bundle ships no consumed axiom —
# the precedence dispatch is modeled DEEPLY in the impl and `coercible` is a
# spec input, so the proof reasons over concrete rationals, not a callee
# contract.
AXIOM_TESTS = []
