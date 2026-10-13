# properties.py — PBT manifest for sympy__sympy-17318 (lean backend).
#
# A PORT of the nagini falsification battery to the Lean-family carrier. NOT a
# Lean module; an adversarial battery the gate parses. Each SPEC_TESTS case is a
# full Solution.lean variant built by region-surgery: ONLY the text inside the
# impl region (and, for the soundness positive, the proof body) is swapped, so
# the frozen spec is provably untouched (same_spec holds) and every rejection is
# attributable to the postcondition/branch decision, never a tampered spec.
#
# Defended surface (read the frozen Solution.lean docstring first). The modeled
# behavior is a SINGLE two-way decision over a list of addends:
#   * When every addend's square is a positive rational (`allSquarePosRat p`),
#     the fast decomposition routine is applicable and its result is returned
#     UNCHANGED: `result = fastDecomp p`.
#   * Otherwise the fast routine is not applicable and the general matcher
#     produces the result: `result = Except.ok (depthMatch p)` — the fast
#     routine's inability is NEVER propagated on this branch.
# Both callees (`fastDecomp`, `depthMatch`) are `opaque`: their VALUE is unpinned,
# so no literal a wrong impl can echo. The clauses are dischargeable ONLY by
# calling the right callee, with the right argument, on the right branch.
#
# Carrier narrowing vs the nagini sibling: the Lean bundle models exactly this
# decision. Cases the nagini battery attached to unmodeled machinery (the
# NoMatch-vs-depth-marker distinction, fractional-permission frames, the numeric
# surd count `k`) have no separate counterpart here and are handled as noted in
# the per-case comments and the submission `assessment`.
#
# AUDIT PASS (independent, verifier-backed). All 21 builds the gate performs were
# re-run and reproduce the recorded outcomes. Three defects were found and fixed:
#   * the sole soundness positive was definitionally equal to the frozen impl (the
#     frozen tactic script closes its impl verbatim), so it could not have detected
#     a spec that pinned the guard's syntactic form; case `1b` adds a positive that
#     is extensionally equal but NOT definitionally so, and that measurably needs a
#     bridging lemma;
#   * the `admissibility` lane was dropped with no stated reason — the port carried
#     none of the three directions' third test. Case `1c` lands it in the shape a
#     total carrier admits (satisfy the obligation by evaluation at an F2P-shaped
#     input, then close the frozen obligation verbatim);
#   * the else clause's grounding in the general matcher was pinned by no rival;
#     case `7` adds one.
# SECOND AUDIT PASS (independent, verifier-backed). All 21 builds the first pass
# claimed were re-run from scratch and every recorded outcome reproduced; the
# spec-region and theorem-statement bytes of all 9 variants were diffed against the
# frozen file and are identical. The first pass's own measured claims were re-checked
# and all four hold: case 1's impl under the frozen tactic script exits 0 (so it IS
# only a definitional reshape, as its rationale admits) and case 1b's exits 1 (so its
# bridging lemma IS load-bearing).
#
# The witness discrimination was re-derived rather than assumed. For each reject case
# a FORGERY asserting the OPPOSITE claim — that the frozen impl is CORRECT at that
# same input, carrying the same reduction plus the final defeq step — was built on
# both sides: it ELABORATES against the frozen solution (exit 0) and FAILS against
# every rival (exit 1), the exact mirror of the real witnesses. So the gold-side exit
# code tracks the CLAIM and is genuine evidence, not a tactic artifact. (An earlier
# flip that omitted the trailing defeq step failed on gold for a tactic reason and
# proved nothing either way — the fair pair is the one that matters.)
#
# One real gap was found and fixed. The shipped guard rival loosens the decision all
# the way to rationality and is refuted at a NEGATIVE square, so a sign flip alone
# catches it; the decision's actual BOUNDARY — strict `0 < q` versus `0 <= q` — was
# probed by nothing. A rival loosening ONLY strictness agrees with gold at every
# input the shipped cases discriminate at and differs on exactly one point, a ZERO
# square. Case 8 lands it with a full discriminating triple (rival 0, gold 1, probe
# 1, forgery inverted).
#
# THIRD AUDIT PASS (independent, verifier-backed) re-ran the opposite-claim control
# with the SHIPPED witness's own tactic prefix, and the `inability-escapes-else`
# witness did not survive it. Its gold build printed
#   unsolved goals ⊢ ¬ pure (Except.ok (depthMatch [{sq := none, tag := 0}]))
#                      = Except.ok (depthMatch [{sq := none, tag := 0}])
# and the same script with the `¬` dropped printed the identical bytes without the
# `¬` (both exit 1, 6.2 s / 6.1 s): the `do` block's `pure` was never peeled, so the
# refutation was never performed and gold's exit code was claim-INDEPENDENT. The
# second pass's forgery missed this because it added a trailing defeq step the
# shipped witness did not carry, which made the CONTROL decisive without making the
# WITNESS decisive. Repaired in place (rival untouched -- it is genuinely wrong):
# the witness now supplies that `pure` lemma itself and reduces the impl to a
# concrete value first, so gold fails at
#   ⊢ Except.ok (depthMatch [{sq := none, tag := 0}]) = Except.error ()
# -- gold's own value exhibited against the claimed one -- while the flipped claim
# VERIFIES on gold (exit 0) and fails on the rival (exit 1). The other six rejects
# fail on gold by TYPE MISMATCH against their carrier hypothesis, a different shape,
# and are untouched.
#
# The frozen spec survived every remaining probe: seven tuned wrong impls (always-fast,
# always-else, any-instead-of-all, branch swap, empty-list special case, wrong argument
# into the matcher, and the zero-square loosening) ALL reject, and four independent
# correct reshapes (match-on-Bool, term-level if, eta-expanded guard, and a decide over
# a Prop-level bounded forall) ALL verify — the last three only after a real bridging
# proof, so the spec pins the decision's value and not its syntactic form in both
# directions.
from pathlib import Path

INSTANCE = "sympy__sympy-17318"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()

# the exact gold impl block (between -- impl-start / -- impl-end); unique in _BASE.
_GOLD_IMPL = (
    "  if allSquarePosRat p then\n"
    "    return fastDecomp p\n"
    "  else\n"
    "    return Except.ok (depthMatch p)\n"
)

# the exact gold proof body (between the theorem statement and -- proof-end);
# tuned to the frozen impl's `if allSquarePosRat p` shape. Unique in _BASE.
_GOLD_PROOF = (
    "  by_cases h : allSquarePosRat p = true\n"
    "  · simp only [Id.run, h, if_true]; rfl\n"
    "  · simp only [Id.run, h]; rfl\n"
)


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: anchor not found: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_body: str) -> str:
    """Build a variant by replacing ONLY the gold impl block (proof left frozen —
    a reshaped impl no longer matches the frozen tactic script, which is exactly
    the reject signal; the discriminating `witness` certifies it rejects for the
    right reason, not merely because `rfl` broke)."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


def _impl_and_proof(new_body: str, new_proof: str) -> str:
    """Build a variant that reshapes the impl AND reproves the (byte-identical)
    obligation — for the soundness positive, which must VERIFY."""
    return _swap(_swap(_BASE, _GOLD_IMPL, new_body), _GOLD_PROOF, new_proof)


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness) — a structurally-different but CORRECT impl.
#    Inverts the branch nesting: the not-applicable branch is handled FIRST
#    (guarded by `!allSquarePosRat p`), the applicable branch in the trailing
#    else. Both clauses are still discharged by the real callees (fast path calls
#    fastDecomp p, else path returns Except.ok (depthMatch p)). The obligation is
#    reproven for the new shape without weakening it. MUST verify, else the spec
#    is SPEC-TOO-STRONG. (Ports nagini `pos-control-reorder`.)
#
#    AUDIT NOTE (measured, not argued): this reshape is only *syntactically*
#    different. Building this impl under the FROZEN tactic script verbatim exits
#    0 — `if !b then x else y` and `if b then y else x` are definitionally equal
#    after `Bool.not`'s iota reduction, so the reshaped proof below is a
#    convenience, not a necessity. That makes this positive a weak soundness
#    control on its own: it cannot distinguish a spec that is too strong from one
#    that merely happens to accept the frozen normal form. Case 1b is the
#    load-bearing positive; it is kept because a cheap definitional reshape is
#    still the right FIRST positive (it isolates branch ORDER from everything
#    else), and dropping it would lose that isolation.
# ---------------------------------------------------------------------------
_POS_IMPL = (
    "  if !allSquarePosRat p then\n"
    "    return Except.ok (depthMatch p)\n"
    "  else\n"
    "    return fastDecomp p\n"
)
_POS_PROOF = (
    "  by_cases h : allSquarePosRat p = true\n"
    "  · simp only [Id.run, h, Bool.not_true]; rfl\n"
    "  · simp only [Bool.not_eq_true] at h\n"
    "    simp only [Id.run, h]; rfl\n"
)

# ---------------------------------------------------------------------------
# 1b. POSITIVE CONTROL, GENUINELY RESHAPED (soundness) — added by audit. Case 1
#    is definitionally equal to the frozen impl (the frozen tactic script closes
#    it verbatim, measured), so it tests only that the spec accepts one normal
#    form. This one recomputes the SAME decision through a different quantifier:
#    `!p.any (fun a => !squarePosRat a)` instead of `p.all squarePosRat`. That is
#    De Morgan over the addend list — extensionally the same predicate, but NOT
#    definitionally equal, so it needs a real bridging lemma
#    (`List.all_eq_not_any_not`) before either clause closes. Confirmed load-bearing:
#    this impl under the FROZEN proof script exits 1, and verifies only with the
#    bridge below. A spec that pinned the guard's SYNTACTIC form rather than its
#    value would reject this => SPEC-TOO-STRONG. MUST verify.
# ---------------------------------------------------------------------------
_POS2_IMPL = (
    "  if !p.any (fun a => !squarePosRat a) then\n"
    "    return fastDecomp p\n"
    "  else\n"
    "    return Except.ok (depthMatch p)\n"
)
_POS2_PROOF = (
    "  have hd : (!p.any (fun a => !squarePosRat a)) = allSquarePosRat p := by\n"
    "    simp [allSquarePosRat, List.all_eq_not_any_not]\n"
    "  by_cases h : allSquarePosRat p = true\n"
    "  · simp only [Id.run, hd, h, if_true]; rfl\n"
    "  · simp only [Id.run, hd, h]; rfl\n"
)

# ---------------------------------------------------------------------------
# 1c. ADMISSIBILITY — added by audit; the lane the port dropped entirely. On a
#    total carrier the frozen obligation carries no precondition, so the analogue
#    of PRECOND-TOO-STRONG is the obligation being UNSATISFIABLE at exactly an
#    F2P-shaped input. This positive discharges it at two concrete points, BY
#    EVALUATION, as `have`s, before closing the frozen obligation verbatim:
#      * the issue-shaped input (a positive-square addend beside a non-positive
#        one), where the decision evaluates to `false` and the else clause must be
#        satisfiable by the general matcher's form;
#      * an all-positive-square input, where it evaluates to `true` and the fast
#        clause must be satisfiable by the fast routine's own result.
#    Both `have`s are then `clear`ed, so the frozen obligation is closed by the
#    frozen script alone — the case adds evidence, it does not weaken anything. If
#    either point were unreachable (a decision no input can drive to that value,
#    or a clause no result can satisfy there) these would fail. MUST verify.
# ---------------------------------------------------------------------------
_P_F2P = "[{sq := some 16, tag := 0}, {sq := some (-1), tag := 1}]"
_P_FAST = "[{sq := some 18, tag := 0}, {sq := some 8, tag := 1}]"
_ADMISS_PROOF = (
    f"  have hElse : allSquarePosRat {_P_F2P} = false := by decide\n"
    f"  have hElseSat : problem_spec_decompose {_P_F2P}\n"
    f"      (Except.ok (depthMatch {_P_F2P})) := by\n"
    f"    unfold problem_spec_decompose\n"
    f"    simp only [hElse, Bool.false_eq_true, if_false]\n"
    f"  have hFast : allSquarePosRat {_P_FAST} = true := by decide\n"
    f"  have hFastSat : problem_spec_decompose {_P_FAST}\n"
    f"      (fastDecomp {_P_FAST}) := by\n"
    f"    unfold problem_spec_decompose\n"
    f"    simp only [hFast, if_true]\n"
    f"  clear hElseSat hFastSat hElse hFast\n"
) + _GOLD_PROOF

# ---------------------------------------------------------------------------
# 2. WEAK GUARD / prepatch bug (uniqueness, reject) — THE fix. Selects the fast
#    routine under the LOOSER decision "every addend square is a rational" (i.e.
#    `a.sq.isSome`), dropping the positivity requirement. On an addend whose
#    square is a NON-positive rational the impl takes the fast branch, but the
#    spec's branch decision (`allSquarePosRat p = false`) requires the else
#    branch `result = Except.ok (depthMatch p)`. Witness at the issue-shaped
#    input (a positive-square addend plus a negative-square one). MUST reject; if
#    it verified the spec would not see the bug the patch fixes => SPEC-TOO-WEAK.
#    (Ports nagini `weak-guard-fastpath`.)
# ---------------------------------------------------------------------------
_WEAK_GUARD = (
    "  if p.all (fun a => a.sq.isSome) then\n"
    "    return fastDecomp p\n"
    "  else\n"
    "    return Except.ok (depthMatch p)\n"
)
_W_WEAK_GUARD = (
    "example (h : fastDecomp [{sq := some 16, tag := 0}, {sq := some (-1), tag := 1}]\n"
    "             ≠ Except.ok (depthMatch [{sq := some 16, tag := 0}, {sq := some (-1), tag := 1}])) :\n"
    "    ¬ problem_spec_decompose [{sq := some 16, tag := 0}, {sq := some (-1), tag := 1}]\n"
    "        (implementation_decompose [{sq := some 16, tag := 0}, {sq := some (-1), tag := 1}]) := by\n"
    "  unfold problem_spec_decompose implementation_decompose\n"
    "  simp only [Id.run,\n"
    "    show allSquarePosRat [{sq := some 16, tag := 0}, {sq := some (-1), tag := 1}] = false from by decide,\n"
    "    show ([{sq := some 16, tag := 0}, {sq := some (-1), tag := 1}] : List Addend).all (fun a => a.sq.isSome) = true from by decide,\n"
    "    if_true, if_false]\n"
    "  exact h\n"
)

# ---------------------------------------------------------------------------
# 3. INABILITY ESCAPES ON THE ELSE BRANCH (uniqueness, reject) — attacks the
#    else-branch clause. On the not-applicable branch it propagates the fast
#    routine's inability (`Except.error ()`) instead of routing to the general
#    matcher. The spec pins `result = Except.ok (depthMatch p)` there, and
#    `Except.error () ≠ Except.ok _` structurally — no assumption about the
#    opaque callees needed. Witness at a not-rational-square input (`sq = none`),
#    exercising a DIFFERENT binder value than the reject cases above. MUST reject.
#    (Lean analogue of nagini's empty-match / partial-domain family: the lean
#    model folds "raise NoMatch" into `Except.error ()` escaping on this branch.)
# ---------------------------------------------------------------------------
_ERR_ELSE = (
    "  if allSquarePosRat p then\n"
    "    return fastDecomp p\n"
    "  else\n"
    "    return Except.error ()\n"
)
# The witness evaluates the impl at the input BEFORE contradicting the clause.
# An earlier version stopped at `simp only [Id.run, <guard>]; simp`, which leaves
# the result wrapped in the `do` block's `pure`: nothing in that simp set peels
# `pure x = x` for `Id`, so the goal stayed `¬ pure <result> = <result>` and the
# gold-side build failed on the unpeeled carrier rather than on the claim. Measured:
# the SAME script with the leading `¬` dropped -- i.e. asserting gold is CORRECT
# here, which it is -- failed with the byte-identical message modulo that `¬`, so
# gold's exit code carried no information about what was claimed. The `pure` lemma
# the frozen proof discharges by `rfl` is now supplied to `simp only`, so `hval`
# reduces the impl to a CONCRETE value: `Except.error ()` for this rival (hval
# closes, and error ≠ ok then refutes the clause), while gold reduces to
# `Except.ok (depthMatch [...])` and the build stops exhibiting gold's own value
# against the claimed one. The opposite claim -- `hval` restated at gold's value,
# same prefix -- now VERIFIES against gold (exit 0) and FAILS against this rival
# (exit 1), so the gold-side failure tracks the claim.
_W_ERR_ELSE = (
    "example :\n"
    "    ¬ problem_spec_decompose [{sq := none, tag := 0}]\n"
    "        (implementation_decompose [{sq := none, tag := 0}]) := by\n"
    "  have hguard : allSquarePosRat [{sq := none, tag := 0}] = false := by decide\n"
    "  have hval : implementation_decompose [{sq := none, tag := 0}]\n"
    "      = (Except.error () : Except Unit NestedForm) := by\n"
    "    simp only [implementation_decompose, Id.run, hguard, Bool.false_eq_true, if_false,\n"
    "      show ∀ x : Except Unit NestedForm, (pure x : Id (Except Unit NestedForm)) = x from\n"
    "        fun _ => rfl]\n"
    "  unfold problem_spec_decompose\n"
    "  rw [hguard, hval]\n"
    "  simp\n"
)

# ---------------------------------------------------------------------------
# 4. FAST BRANCH ROUTED THROUGH THE GENERAL MATCHER (uniqueness, reject) —
#    attacks the fast-path clause. Returns `Except.ok (depthMatch p)` on BOTH
#    branches, so it agrees with gold on the else branch and differs only on the
#    fast branch, where the spec requires `result = fastDecomp p`. Refuted by
#    conditioning on the carrier: whenever fastDecomp differs from routing through
#    depthMatch, the impl's answer differs from the spec's. Witness at a
#    positive-square input. MUST reject. (Ports nagini `depth-marker-on-fastpath`.)
# ---------------------------------------------------------------------------
_DEPTH_ON_FAST = (
    "  if allSquarePosRat p then\n"
    "    return Except.ok (depthMatch p)\n"
    "  else\n"
    "    return Except.ok (depthMatch p)\n"
)
_W_DEPTH_ON_FAST = (
    "example (h : fastDecomp [{sq := some 1, tag := 0}]\n"
    "             ≠ Except.ok (depthMatch [{sq := some 1, tag := 0}])) :\n"
    "    ¬ problem_spec_decompose [{sq := some 1, tag := 0}]\n"
    "        (implementation_decompose [{sq := some 1, tag := 0}]) := by\n"
    "  unfold problem_spec_decompose implementation_decompose\n"
    "  simp only [Id.run, show allSquarePosRat [{sq := some 1, tag := 0}] = true from by decide, if_true]\n"
    "  intro hc\n"
    "  exact h hc.symm\n"
)

# ---------------------------------------------------------------------------
# 5. LITERAL ECHO ON THE FAST BRANCH (uniqueness, reject) — the ungrounded-oracle
#    probe, recast. On the fast branch it returns a hardcoded normal form WITHOUT
#    calling the fast routine. The spec pins `result = fastDecomp p`, an OPAQUE
#    value, so no literal can be proved equal to it. Refuted by conditioning: at
#    an input where the fast routine's result differs from the literal, the impl
#    is wrong. Witness at a positive-square input distinct from case 4's. MUST
#    reject; if it verified the postcondition would be a fabricatable marker =>
#    SPEC-TOO-WEAK. (Ports nagini `echo-literal-fastpath`.)
# ---------------------------------------------------------------------------
_ECHO_LIT = (
    "  if allSquarePosRat p then\n"
    "    return Except.ok { repr := \"\" }\n"
    "  else\n"
    "    return Except.ok (depthMatch p)\n"
)
_W_ECHO_LIT = (
    "example (h : fastDecomp [{sq := some 2, tag := 0}]\n"
    "             ≠ Except.ok { repr := \"\" }) :\n"
    "    ¬ problem_spec_decompose [{sq := some 2, tag := 0}]\n"
    "        (implementation_decompose [{sq := some 2, tag := 0}]) := by\n"
    "  unfold problem_spec_decompose implementation_decompose\n"
    "  simp only [Id.run, show allSquarePosRat [{sq := some 2, tag := 0}] = true from by decide, if_true]\n"
    "  intro hc\n"
    "  exact h hc.symm\n"
)

# ---------------------------------------------------------------------------
# 6. WRONG ARGUMENT INTO THE FAST ROUTINE (uniqueness, reject) — the lean
#    analogue of nagini `wrong-k-into-helper`. The lean fast routine takes the
#    addend list itself (there is no separate surd-count `k`), so the way to
#    mishandle its input is to call it on the WRONG argument. Calls the fast
#    routine on `[]` instead of `p`, still returning its result on the fast
#    branch. The spec pins `result = fastDecomp p`; refuted by conditioning on
#    `fastDecomp p ≠ fastDecomp []`, distinguishable given a concrete non-empty
#    `p`. Witness at a positive-square input distinct from cases 4/5. MUST reject.
# ---------------------------------------------------------------------------
_WRONG_ARG = (
    "  if allSquarePosRat p then\n"
    "    return fastDecomp []\n"
    "  else\n"
    "    return Except.ok (depthMatch p)\n"
)
_W_WRONG_ARG = (
    "example (h : fastDecomp [{sq := some 3, tag := 0}] ≠ fastDecomp []) :\n"
    "    ¬ problem_spec_decompose [{sq := some 3, tag := 0}]\n"
    "        (implementation_decompose [{sq := some 3, tag := 0}]) := by\n"
    "  unfold problem_spec_decompose implementation_decompose\n"
    "  simp only [Id.run, show allSquarePosRat [{sq := some 3, tag := 0}] = true from by decide, if_true]\n"
    "  intro hc\n"
    "  exact h hc.symm\n"
)


# ---------------------------------------------------------------------------
# 7. LITERAL ECHO ON THE ELSE BRANCH (uniqueness, reject) — added by audit. Every
#    shipped rival attacks either the branch DECISION (cases 2, 3) or the fast
#    clause (cases 4, 5, 6); the else clause's own GROUNDING — that the returned
#    form is the general matcher's, applied to `p` — was pinned by no case. Case 3
#    only shows `Except.error () ≠ Except.ok _`, a structural clash that says
#    nothing about WHICH form the ok-branch carries. This rival keeps the decision
#    and the fast clause exactly right and returns a hardcoded form on the else
#    branch. The clause pins `Except.ok (depthMatch p)` with `depthMatch` OPAQUE,
#    so no literal can be proved equal to it. Refuted by conditioning on the
#    matcher's form differing from the literal. MUST reject; if it verified, the
#    else clause would be a fabricatable marker => SPEC-TOO-WEAK.
# ---------------------------------------------------------------------------
_ELSE_LIT = (
    "  if allSquarePosRat p then\n"
    "    return fastDecomp p\n"
    "  else\n"
    "    return Except.ok { repr := \"\" }\n"
)
_W_ELSE_LIT = (
    "example (h : Except.ok (depthMatch [{sq := none, tag := 0}])\n"
    "             ≠ (Except.ok { repr := \"\" } : Except Unit NestedForm)) :\n"
    "    ¬ problem_spec_decompose [{sq := none, tag := 0}]\n"
    "        (implementation_decompose [{sq := none, tag := 0}]) := by\n"
    "  unfold problem_spec_decompose implementation_decompose\n"
    "  simp only [Id.run,\n"
    "    show allSquarePosRat [{sq := none, tag := 0}] = false from by decide,\n"
    "    Bool.false_eq_true, if_false]\n"
    "  intro hc\n"
    "  exact h hc.symm\n"
)


# ---------------------------------------------------------------------------
# 8. NON-STRICT POSITIVITY AT A ZERO SQUARE (uniqueness, reject) — added by the
#    second audit. Case 2 loosens the decision all the way to "the square is
#    rational" and is refuted at a NEGATIVE square; every rival that loosening
#    admits is caught by the sign flip alone. Nothing shipped probed the decision
#    at its actual BOUNDARY: `0 < q` versus `0 <= q`. This rival changes only
#    that — it requires each square to be rational and NON-NEGATIVE — so it
#    agrees with gold on every input the other rivals discriminate at, including
#    case 2's, and differs from gold on exactly one carrier point: an addend whose
#    square is ZERO. There the spec's decision is false (0 is not strictly
#    positive) and the else clause is required, while the rival takes the fast
#    branch. Refuted by conditioning on the fast routine differing from the
#    matcher route (one weak, satisfiable hypothesis). MUST reject; if it verified
#    the decision's strictness would be unpinned and a patch that admitted a
#    zero-square expression to the inapplicable fast routine would pass
#    => SPEC-TOO-WEAK.
# ---------------------------------------------------------------------------
_NONSTRICT = (
    "  if p.all (fun a => match a.sq with\n"
    "                    | some q => decide (0 <= q)\n"
    "                    | none => false) then\n"
    "    return fastDecomp p\n"
    "  else\n"
    "    return Except.ok (depthMatch p)\n"
)
_P_ZERO = "[{sq := some 9, tag := 0}, {sq := some 0, tag := 1}]"
_W_NONSTRICT = (
    f"example (h : fastDecomp {_P_ZERO}\n"
    f"             ≠ Except.ok (depthMatch {_P_ZERO})) :\n"
    f"    ¬ problem_spec_decompose {_P_ZERO}\n"
    f"        (implementation_decompose {_P_ZERO}) := by\n"
    f"  unfold problem_spec_decompose implementation_decompose\n"
    f"  simp only [Id.run,\n"
    f"    show allSquarePosRat {_P_ZERO} = false from by decide,\n"
    f"    show ({_P_ZERO} : List Addend).all (fun a => match a.sq with\n"
    f"        | some q => decide (0 <= q)\n"
    f"        | none => false) = true from by decide,\n"
    f"    if_true, Bool.false_eq_true, if_false]\n"
    f"  exact h\n"
)


SPEC_TESTS = [
    {"id": "pos-control-reorder", "kind": "soundness", "expect": "verify",
     "module": _impl_and_proof(_POS_IMPL, _POS_PROOF),
     "rationale": "structurally-different correct impl (inverted branch nesting: "
                  "the not-applicable branch handled first, the applicable branch "
                  "in the trailing else). Both clauses still discharged by the real "
                  "callees; the obligation is reproven unweakened. Must verify or "
                  "the spec is SPEC-TOO-STRONG. NOTE (audit, measured): this "
                  "reshape is definitionally equal to the frozen impl — the frozen "
                  "tactic script closes it verbatim — so it isolates branch ORDER "
                  "only. `pos-control-demorgan-guard` is the load-bearing positive."},

    {"id": "pos-control-demorgan-guard", "kind": "soundness", "expect": "verify",
     "module": _impl_and_proof(_POS2_IMPL, _POS2_PROOF),
     "rationale": "correct impl that recomputes the SAME decision through the dual "
                  "quantifier (!any of the negation, instead of all), i.e. De Morgan "
                  "over the addend list. Extensionally the same predicate but NOT "
                  "definitionally equal: measured, this impl under the frozen tactic "
                  "script exits 1 and verifies only via the bridging lemma "
                  "List.all_eq_not_any_not. So it tests that the spec pins the "
                  "decision's VALUE and not its syntactic form; if the spec rejected "
                  "it the spec would be SPEC-TOO-STRONG."},

    {"id": "admiss-both-branch-points", "kind": "admissibility", "expect": "verify",
     "module": _impl_and_proof(_GOLD_IMPL, _ADMISS_PROOF),
     "rationale": "ports nagini `admiss-both-branches` to a total carrier, where the "
                  "obligation has no precondition and the analogue of "
                  "PRECOND-TOO-STRONG is the obligation being unsatisfiable at an "
                  "F2P-shaped input. Discharges it BY EVALUATION at two concrete "
                  "points before closing the frozen obligation verbatim: the "
                  "issue-shaped input (a positive-square addend beside a "
                  "non-positive one), where the decision evaluates to false and the "
                  "else clause is satisfied by the general matcher's form; and an "
                  "all-positive-square input, where it evaluates to true and the fast "
                  "clause is satisfied by the fast routine's own result. Both facts "
                  "are cleared before the frozen script runs, so nothing is weakened. "
                  "If either branch point were unreachable, or either clause "
                  "unsatisfiable there, this would fail => PRECOND-TOO-STRONG."},

    {"id": "weak-guard-fastpath", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_WEAK_GUARD),
     "refinement": "this is the prepatch bug the fix removes: the looser decision "
                   "admits an expression with a non-positive rational square to the "
                   "fast routine, which is inapplicable there and lets its inability "
                   "escape — the exact IndexError the FAIL_TO_PASS asserts is gone. "
                   "A faithful patch keeping the looser guard would reproduce that "
                   "crash and not resolve.",
     "rationale": "attacks the branch decision. On an addend with a non-positive "
                  "rational square, allSquarePosRat p = false so the spec requires "
                  "the else clause result = Except.ok (depthMatch p); the impl takes "
                  "the fast branch instead. Witness at the issue-shaped two-addend "
                  "input; conditions only on the fast routine differing from the "
                  "matcher route (one weak, satisfiable hypothesis).",
     "witness": _W_WEAK_GUARD},

    {"id": "inability-escapes-else", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_ERR_ELSE),
     "refinement": "propagating the fast routine's inability on the not-applicable "
                   "branch is precisely the pre-fix behavior: the expression is not "
                   "returned unchanged, so the F2P (expression returned unchanged "
                   "when it cannot be decomposed) does not resolve.",
     "rationale": "attacks the else-branch clause result = Except.ok (depthMatch p). "
                  "Returns Except.error () there; error ≠ ok structurally, so no "
                  "assumption about the opaque callees is needed. Witness at a "
                  "not-rational-square input (sq = none), a distinct binder value "
                  "from the other rejects.",
     "witness": _W_ERR_ELSE},

    {"id": "depth-route-on-fastpath", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_DEPTH_ON_FAST),
     "refinement": "routing an all-positive-rational sum through the general matcher "
                   "instead of the fast routine yields the matcher's normal form, not "
                   "the fast decomposition, so the fast-path P2P splits "
                   "(test_sqrtdenest2/3) fail.",
     "rationale": "attacks the fast-path clause result = fastDecomp p. Returns the "
                  "matcher route on both branches; agrees with gold on the else "
                  "branch, differs only on the fast branch. Refuted by conditioning "
                  "on fastDecomp differing from the matcher route (one satisfiable "
                  "hypothesis). Witness at a positive-square input.",
     "witness": _W_DEPTH_ON_FAST},

    {"id": "echo-literal-fastpath", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_ECHO_LIT),
     "refinement": "returning a hardcoded normal form on the fast branch instead of "
                   "the fast routine's decomposition gives the wrong result for every "
                   "real fast-path sum, failing the fast-path P2P.",
     "rationale": "attacks the fast-path clause with a literal. The clause pins the "
                  "result to the OPAQUE fastDecomp p, which no literal can be proved "
                  "equal to; if it verified the postcondition would be a fabricatable "
                  "marker => SPEC-TOO-WEAK. Refuted by conditioning on fastDecomp "
                  "differing from the literal. Witness at a positive-square input "
                  "distinct from the depth-route case.",
     "witness": _W_ECHO_LIT},

    {"id": "wrong-arg-into-fast", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_WRONG_ARG),
     "refinement": "handing the fast routine the wrong argument builds the "
                   "decomposition of a different expression, so the returned normal "
                   "form does not match the input on the fast path and the P2P fails.",
     "rationale": "lean analogue of the nagini wrong-count rival (the lean fast "
                  "routine takes the addend list, not a separate surd count). Calls "
                  "the fast routine on [] rather than p; the clause pins "
                  "result = fastDecomp p. Refuted by conditioning on "
                  "fastDecomp p ≠ fastDecomp [] for the concrete non-empty p. Witness "
                  "at a positive-square input distinct from the other fast-path cases.",
     "witness": _W_WRONG_ARG},

    {"id": "else-literal-form", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_ELSE_LIT),
     "refinement": "on the not-applicable branch the expression must come back with "
                   "the general matcher's own normal form; substituting a fixed form "
                   "returns a spurious decomposition for every such expression "
                   "instead of the one the matcher computed, so the F2P (the "
                   "expression is returned unchanged when it cannot be decomposed) "
                   "does not resolve.",
     "rationale": "added by audit: the else clause's GROUNDING was pinned by no "
                  "shipped case. The other rejects attack the branch decision or the "
                  "fast clause, and the inability-escapes case only shows "
                  "error ≠ ok — a structural clash that says nothing about which form "
                  "the ok-branch carries. This rival keeps the decision and the fast "
                  "clause exactly right and returns a literal on the else branch, "
                  "where the clause pins Except.ok (depthMatch p) with depthMatch "
                  "OPAQUE. Refuted by conditioning on the matcher's form differing "
                  "from the literal (one weak, satisfiable hypothesis). If it "
                  "verified the else clause would be a fabricatable marker => "
                  "SPEC-TOO-WEAK.",
     "witness": _W_ELSE_LIT},

    {"id": "nonstrict-positivity-zero-square", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_NONSTRICT),
     "refinement": "the decision the fix installs requires each square to be "
                   "strictly positive, not merely non-negative. An expression "
                   "carrying a zero square is not one the fast routine can "
                   "process, so admitting it reproduces the same escaping "
                   "inability the F2P asserts is gone — on an input the other "
                   "near-miss does not reach.",
     "rationale": "added by the second audit: the decision's BOUNDARY was probed "
                  "by no shipped case. The other guard rival loosens all the way "
                  "to rationality and is refuted at a negative square, so the "
                  "sign flip alone catches it; this one loosens ONLY strictness "
                  "(0 < q to 0 <= q), agrees with gold everywhere the other "
                  "rivals discriminate, and differs on exactly one carrier point: "
                  "a ZERO square, where allSquarePosRat is false and the else "
                  "clause is required but the impl takes the fast branch. "
                  "Refuted by conditioning on the fast routine differing from the "
                  "matcher route. If it verified, the strictness of the decision "
                  "would be unpinned => SPEC-TOO-WEAK.",
     "witness": _W_NONSTRICT},
]
