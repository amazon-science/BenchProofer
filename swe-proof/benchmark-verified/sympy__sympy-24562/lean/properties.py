# properties.py — G-PBT falsification battery for sympy__sympy-24562 (lean lane).
#
# This is a PORT of the nagini sibling battery, re-expressed against this
# backend's carrier. It is NOT a Lean module; it is a record of adversarial
# spec cases the G-PBT runner executes and stamps with a recorded verdict.
#
# Defended surface (read from Solution.lean / mapping.md):
#   The single modeled obligation combines two pieces into one product:
#     problem_spec_denominatorProduct (pDen) (qdigits) (result) :=
#         result = pDen * decval qdigits
#   with the obligation `theorem correct_denominatorProduct` quantified over
#   the two INPUT BINDERS:
#     * pDen    : Nat, a positive whole-number factor (precondition 1 ≤ pDen);
#     * qdigits : List Nat, a second operand written as a decimal digit string,
#                 most-significant first (precondition: every entry < 10).
#   `decval` reads the digit list into the integer it denotes (a left fold
#   `acc*10 + d`). The load-bearing clause is the single product equation: the
#   result must be the factor multiplied by the VALUE the digit string denotes,
#   with no dependence on how that value was written.
#
# Carrier narrowing vs nagini: the nagini sibling contracted a two-component
# (numerator, denominator) result plus a fractional-permission frame over a
# read-only list. This bundle models only the purely functional denominator
# PRODUCT — a single clause over the two binders above. See `assessment` in the
# submitted payload for exactly which nagini cases have counterparts here and
# which are vacuous on a referentially-transparent carrier.
#
# Audited independently after the port, in two passes.
#
# First pass — two defects found and repaired, both recorded at their cases
# below: the `partial-domain-factor` rival was extensionally the SAME function as
# the `drop-factor` rival (a duplicate whose prose claimed a sub-domain it did
# not have), and the zero-valued-operand clause — which the defended surface
# calls load-bearing — had no rival attacking it.
#
# Second pass (independent auditor, did not write the port) — every reject case's
# witness was rebuilt by hand against BOTH the rival and the frozen solution, and
# each gold-side failure was confirmed a semantic refutation rather than a
# missing identifier, a type error, or a stuck reduction: gold fails with
# `Tactic 'decide' proved that the proposition ... is false`, and the FORGERY
# control (the same witness with the `¬` dropped, i.e. claiming the frozen impl
# is correct at that input) BUILDS against gold and FAILS against every rival —
# so each gold-side exit code tracks the claim rather than the file. Two further
# gaps were found by fresh attacks and are repaired here: the digit ORDER was
# unprobed (see R6, whose rival is rejected and whose witness discriminates), and
# the battery carried no admissibility case at all (see P3, which verifies).
# A stronger correct reshape was also landed as a second positive (P2). Probes
# that found no defect: an impl wrong only where the digit precondition is
# violated cannot be proven, an impl branching on the excluded pDen = 0 verifies
# but only by agreeing with the clause everywhere in the domain, and the spec was
# machine-checked FUNCTIONAL (any two results satisfying it are equal), which is
# why no wrong impl can satisfy it — SPEC-TOO-WEAK is unreachable by
# construction here.
#
# Region-surgery (_swap on _BASE) edits ONLY inside the # impl-start/# impl-end
# region (and, for the soundness positive, the proof body between
# -- proof-start / -- proof-end). The spec predicate, the pure helper, the
# theorem STATEMENT, and the precondition binders are never touched, so
# same_spec holds by construction and every rejection is attributable to the
# postcondition rather than a tampered spec.
from pathlib import Path

INSTANCE = "sympy__sympy-24562"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl body (exactly the text strictly inside # impl-start/# impl-end).
# Every rival is a _swap of this block; the markers, signature, spec, pure
# helper, precondition, and theorem statement are never touched -> same_spec
# holds by construction. NOTE the em-dash on the penultimate comment line — it
# must match Solution.lean byte-for-byte or _swap raises "drift".
# ---------------------------------------------------------------------------
_GOLD_IMPL = """  -- a FRESH integer accumulator for the combined denominator, started at 1 so
  -- that every contribution is combined numerically
  let mut denAcc : Nat := 1
  -- fold in the whole-number factor contributed by the first operand
  denAcc := denAcc * pDen
  -- the second operand is supplied as a decimal digit string: read it into the
  -- integer it denotes
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  -- fold the operand's integer value into the same accumulator — including a
  -- zero value, which zeroes the combined result
  denAcc := denAcc * c
  return denAcc"""


# The gold proof body (strictly inside -- proof-start/-- proof-end, after the
# forIn_decval helper). Only the soundness positive rewrites this; the reject
# cases keep it verbatim so their rejection comes from the spec, not a tampered
# proof. The witness (see below) is what actually attributes each rejection.
_GOLD_PROOF = """  intro pDen qdigits _ _
  unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
  have hb : Id.run (forIn qdigits 0 (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) 0 := forIn_decval qdigits 0
  simp only [Id.run, bind, pure] at hb ⊢
  rw [hb, Nat.one_mul]"""


# ===========================================================================
# (R1) DROPS THE FACTOR — reads the operand value but never folds in pDen.
# Ports nagini case (4) "denominator drops p_den": out = value, ignoring the
# whole-number factor. Attacks the product clause via the `pDen` binder.
# ===========================================================================
_r_drop_factor = _swap(
    _BASE,
    _GOLD_IMPL,
    """  -- WRONG: reads the operand value but never folds in the whole-number factor
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  return c""",
)

# ===========================================================================
# (R2) REPEAT-THEN-READ — the headline defect. Combines the factor by
# duplicating the operand's WRITTEN digit string that many times and then
# reading the longer string, rather than multiplying the value it denotes.
# Ports nagini's central non-homomorphic bug (its aux-value repeat-then-read
# discriminator). Attacks the product clause: the result depends on how the
# operand was WRITTEN, not on its value.
# ===========================================================================
_r_repeat = _swap(
    _BASE,
    _GOLD_IMPL,
    """  -- WRONG: combine the factor by repeating the operand's written digit string
  -- rather than multiplying the value it denotes
  let digits : List Nat := (List.replicate pDen qdigits).flatten
  let mut c : Nat := 0
  for d in digits do
    c := c * 10 + d
  return c""",
)

# ===========================================================================
# (R3) DROPS THE OPERAND VALUE — returns the factor alone, treating the operand
# as though it denoted 1. Ports nagini case (3) "denominator uses the wrong
# quantity in place of the read value": the read value never reaches the
# product. Attacks the product clause via the `qdigits` binder.
# ===========================================================================
_r_drop_operand = _swap(
    _BASE,
    _GOLD_IMPL,
    """  -- WRONG: returns the whole-number factor but never folds in the operand value
  let mut denAcc : Nat := 1
  denAcc := denAcc * pDen
  return denAcc""",
)

# ===========================================================================
# (R4) PARTIAL DOMAIN on the operand LENGTH — correct for a single-digit operand,
# dropping the factor once the operand is written with more than one digit.
# Ports nagini case (2) "partial-domain": a near-miss that is genuinely right on
# a sub-domain, which an under-widened spec would admit; the frozen spec pins the
# product for operands of EVERY length. Attacks the product clause via the
# `qdigits` binder at a length the near-miss mishandles.
#
# AUDIT NOTE — this rival was REPLACED. It previously gated on `pDen == 1`
# (returning `pDen * c` there and `c` otherwise), which is extensionally the
# SAME FUNCTION as the (R1) drop-factor rival above: on the pDen = 1 branch
# `pDen * c` reduces to `c`, so both rivals return `decval qdigits` at every
# input. Machine-checked with a closed `funext` proof of
# `implDropFactor = implPartial` (exit 0), so the case was a duplicate of (R1)
# rather than the distinct near-miss its prose claimed, and its "sub-domain the
# near-miss claims to handle" did not exist. The replacement below is a real
# near-miss: it is CORRECT on the single-digit sub-domain (checked:
# `implNewPartial 3 [7] = 3 * 7` by decide) and wrong beyond it (checked:
# `implNewPartial 3 [1,2] ≠ 3 * 12` by decide), and it differs from (R1) at
# (2, [5]) (checked: `implNewPartial 2 [5] ≠ implDropFactor 2 [5]` by decide).
# ===========================================================================
_r_partial = _swap(
    _BASE,
    _GOLD_IMPL,
    """  -- read the operand value
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  -- WRONG: folds in the whole-number factor only when the operand is written
  -- with a single digit; for a longer operand the contribution is dropped
  if qdigits.length <= 1 then
    return pDen * c
  else
    return c""",
)

# ===========================================================================
# (R5) ZERO-VALUED OPERAND SKIPPED — agrees with the frozen impl on every
# operand of nonzero value, but treats a zero-valued operand as contributing
# nothing instead of zeroing the product. This attacks the one clause the
# defended surface calls out explicitly and that no other rival here reaches:
# the product is TOTAL over the domain, so a zero-valued operand zeroes it. An
# impl of this shape would agree with the frozen one on every nonzero operand
# and diverge only where the downstream zero handling is fed, which is exactly
# the slack the product equation is there to remove.
#
# AUDIT NOTE — this case is NEW (added by the audit). The ported battery left
# the zero-valued-operand clause unattacked: all four of its rivals were refuted
# at operands of nonzero value, so nothing in it demonstrated that the spec
# pins the zeroing behaviour its own prose calls load-bearing.
# ===========================================================================
_r_skip_zero = _swap(
    _BASE,
    _GOLD_IMPL,
    """  -- a fresh accumulator, then the whole-number factor
  let mut denAcc : Nat := 1
  denAcc := denAcc * pDen
  -- read the operand value
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  -- WRONG: a zero-valued operand is SKIPPED rather than folded in, so the
  -- combined result is left un-zeroed instead of becoming 0
  if c == 0 then
    return denAcc
  denAcc := denAcc * c
  return denAcc""",
)

# ===========================================================================
# (R6) POSITIONAL ORDER REVERSED — folds the digit list from the least
# significant end instead of the most significant, so the accumulator reads the
# operand's positional notation backwards. Every other rival here attacks WHICH
# quantities enter the product (the factor, the operand value, a length branch,
# the zero case); none attacks how the digit sequence is READ, i.e. the
# positional-weight structure of `decval` itself. This rival agrees with the
# frozen impl on every palindromic operand (a single digit included), which is
# exactly the sub-grid the other four witnesses live on, and diverges as soon as
# the operand's digits are not symmetric.
#
# AUDIT NOTE — this case is NEW (added by the audit). The ported battery left
# the positional read unprobed: with all five prior witnesses at operands that
# are single-digit or palindromic in value terms, nothing in it demonstrated
# that the spec pins the digits' ORDER, which is the one property that makes the
# `List Nat` carrier (rather than a plain `Nat`) load-bearing at all. Machine-
# checked as a genuine rival before landing: the variant is rejected, and its
# witness holds of the rival (exit 0) while gold refutes it by evaluation
# (exit 1, `Tactic 'decide' proved that the proposition ... is false`).
# ===========================================================================
_r_reverse_order = _swap(
    _BASE,
    _GOLD_IMPL,
    """  -- a fresh accumulator, then the whole-number factor
  let mut denAcc : Nat := 1
  denAcc := denAcc * pDen
  -- WRONG: reads the operand's positional notation from the least significant
  -- end, so the digits' positional weights are assigned in reverse order
  let mut c : Nat := 0
  for d in qdigits.reverse do
    c := c * 10 + d
  denAcc := denAcc * c
  return denAcc""",
)

# ===========================================================================
# (P1) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
# Shape change: read the operand value FIRST, seed the accumulator with it, then
# fold in the factor with the multiplication commuted (value*factor instead of
# factor*value). Computes the identical product and must verify. The proof
# closes with the same Route-B loop-equals-fold helper, swapping the final
# `Nat.one_mul` for `Nat.mul_comm` to match the commuted arithmetic — no new
# lemma, no induction. Ports nagini case (5) "positive control reorder". If a
# faithful correct impl of this shape cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_pos = _swap(
    _swap(
        _BASE,
        _GOLD_IMPL,
        """  -- read the decimal operand into the integer it denotes FIRST
  let mut c : Nat := 0
  for d in qdigits do
    c := c * 10 + d
  -- then combine the whole-number factor with that value
  let mut denAcc : Nat := c
  denAcc := denAcc * pDen
  return denAcc""",
    ),
    _GOLD_PROOF,
    """  intro pDen qdigits _ _
  unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
  have hb : Id.run (forIn qdigits 0 (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + d)))) =
      qdigits.foldl (fun acc d => acc * 10 + d) 0 := forIn_decval qdigits 0
  simp only [Id.run, bind, pure] at hb ⊢
  rw [hb, Nat.mul_comm]""",
)

# ===========================================================================
# (P2) POSITIVE CONTROL (soundness) — a DEEPER correct reshape: the factor is
# distributed INTO the positional read rather than applied after it. A single
# accumulator starts at 0 and each step does `acc * 10 + pDen * d`, so the
# factor is folded into every digit's contribution as the operand is read and no
# separate value local ever exists. This computes the identical product by
# distributivity, but it shares neither of the frozen impl's two locals nor its
# fold shape, so its proof cannot reuse the frozen `forIn_decval` helper — it
# carries its own generalized induction (stated as a `have` inside the proof
# body, so no new top-level theorem appears).
#
# AUDIT NOTE — this case is NEW (added by the audit). The ported battery's only
# positive was a statement reorder plus `Nat.mul_comm`: its impl is
# definitionally near the frozen one and its proof is the frozen proof with one
# lemma name changed, so it exercised almost no SPEC-TOO-STRONG risk. This one
# is a shape the frozen proof script genuinely does not close, which is what a
# soundness control is for. Machine-checked as VERIFYING before landing (exit 0).
# ===========================================================================
_pos_distribute = _swap(
    _swap(
        _BASE,
        _GOLD_IMPL,
        """  -- scale each digit's contribution by the whole-number factor as the
  -- decimal operand is read, so the factor is distributed into the positional
  -- read instead of being applied to the finished value
  let mut denAcc : Nat := 0
  for d in qdigits do
    denAcc := denAcc * 10 + pDen * d
  return denAcc""",
    ),
    _GOLD_PROOF,
    """  intro pDen qdigits _ _
  unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
  have key : ∀ (ds : List Nat) (init : Nat),
      Id.run (forIn ds (pDen * init) (fun d r => do
        pure PUnit.unit
        pure (ForInStep.yield (r * 10 + pDen * d)))) =
      pDen * ds.foldl (fun acc d => acc * 10 + d) init := by
    intro ds
    induction ds with
    | nil => intro init; rfl
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [List.foldl_cons]
      have hmul : pDen * init * 10 + pDen * a = pDen * (init * 10 + a) := by ring
      rw [hmul]
      exact ih (init * 10 + a)
  have h0 := key qdigits 0
  simp only [Nat.mul_zero, Id.run, bind, pure] at h0 ⊢
  exact h0""",
)

# ===========================================================================
# (P3) ADMISSIBILITY — non-vacuity of the obligation at the F2P-shaped inputs.
# The frozen obligation carries two preconditions (1 ≤ pDen, every digit < 10),
# but on this total carrier the thing worth testing is not whether a binder can
# be attacked: it is whether the obligation is SATISFIABLE at exactly the inputs
# the failing tests observe. A precondition that excluded them, or a clause
# unsatisfiable there, would make the whole obligation vacuous at the only points
# that matter — the total-carrier analogue of PRECOND-TOO-STRONG.
#
# This case tests that directly. Before closing the frozen obligation verbatim it
# discharges `problem_spec_denominatorProduct` BY EVALUATION (`decide`) at two
# concrete F2P-shaped points, each with its preconditions established by
# evaluation too:
#   * the headline shape — factor 2 with a three-digit operand '1','0','0'
#     (the multi-digit operand family the reported behaviour turns on); and
#   * the zero-valued operand — factor 2 with operand '0', the point the
#     defended surface calls load-bearing, where the product must be 0.
# Both `have`s are proven, not assumed: no new declaration, no assumption token,
# the theorem statement byte-identical, and the frozen tactic body retained
# unchanged as the closing step. A failure of either `have` would mean the
# modeled clause is unsatisfiable at an F2P-shaped input.
#
# AUDIT NOTE — this case is NEW (added by the audit). The port carried no
# `kind="admissibility"` case at all, while the nagini sibling carries
# `admiss-f2p-shaped`; dropping it silently removed one of the three directions
# this gate exists to test. The lane is NOT vacuous here (the reason "the frozen
# obligation has no precondition" does not even apply — it has two), and the
# positive was machine-checked as VERIFYING before landing (exit 0).
# ===========================================================================
_admiss = _swap(
    _BASE,
    _GOLD_PROOF,
    """  have hf2p : problem_spec_denominatorProduct 2 [1, 0, 0]
      (implementation_denominatorProduct 2 [1, 0, 0]) := by
    unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
    decide
  have hpre_f2p : 1 ≤ 2 ∧ ∀ d ∈ [1, 0, 0], d < 10 := by decide
  have hzero : problem_spec_denominatorProduct 2 [0]
      (implementation_denominatorProduct 2 [0]) := by
    unfold problem_spec_denominatorProduct implementation_denominatorProduct decval
    decide
  have hpre_zero : 1 ≤ 2 ∧ ∀ d ∈ [0], d < 10 := by decide
"""
    + _GOLD_PROOF,
)


# Witness template: state the spec predicate directly at a concrete input and
# refute it by `decide`. The runner checks it in a file with the frozen proof
# obligations removed; it must ELABORATE against the rival (rival violates the
# spec here) and FAIL against the frozen solution (real discriminator, not a
# tautology). Every witness below was built both ways and seen to discriminate.
def _witness(pDen, qdigits):
    return (
        f"example : ¬ problem_spec_denominatorProduct {pDen} {qdigits}\n"
        f"    (implementation_denominatorProduct {pDen} {qdigits}) := by\n"
        "  unfold problem_spec_denominatorProduct implementation_denominatorProduct decval\n"
        "  decide\n"
    )


SPEC_TESTS = [
    {
        "id": "drop-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_drop_factor,
        "rationale": (
            "Rejection from the sole product clause result = pDen * decval "
            "qdigits: returning decval qdigits alone is not pDen * decval "
            "qdigits whenever the factor pDen ≠ 1. Attacks the `pDen` binder."
        ),
        "refinement": (
            "A faithful real correspondent that drops the factor from the "
            "combined denominator loses the first operand's contribution "
            "entirely. On a fractional first operand (factor 2) the combined "
            "value would be the operand value instead of twice it, so the "
            "constructed quantity is half the intended one and the F2P "
            "equality asserting the combined value fails. It does NOT resolve."
        ),
        "witness": _witness(2, [5]),
    },
    {
        "id": "repeat-then-read",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_repeat,
        "rationale": (
            "Rejection from the product clause result = pDen * decval qdigits: "
            "reading a digit string repeated pDen times denotes, in general, a "
            "value far larger than pDen * decval qdigits (concatenation is not "
            "value multiplication), so the equation cannot hold. Attacks the "
            "product clause's dependence on the VALUE of `qdigits`, not its "
            "written form."
        ),
        "refinement": (
            "This is exactly the reported defect: combining the factor by "
            "repeating the operand's written form rather than multiplying its "
            "value. For factor 2 and operand written as three digits '1','0','0' "
            "the repeated string reads to 100100 rather than 2*100=200, so the "
            "constructed quantity is off by orders of magnitude and the headline "
            "F2P equality fails. A faithful patch of this shape does NOT resolve."
        ),
        "witness": _witness(2, [1, 0, 0]),
    },
    {
        "id": "drop-operand-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_drop_operand,
        "rationale": (
            "Rejection from the product clause result = pDen * decval qdigits: "
            "returning pDen alone is not pDen * decval qdigits whenever the "
            "operand value decval qdigits ≠ 1. Attacks the `qdigits` binder."
        ),
        "refinement": (
            "A faithful real correspondent that never folds the operand value "
            "into the product treats every operand as though it denoted 1, so "
            "the combined quantity ignores the second operand entirely. For "
            "factor 3 and operand '4' it yields 3 instead of 3*4=12, so the F2P "
            "equality over the combined value fails. It does NOT resolve."
        ),
        "witness": _witness(3, [4]),
    },
    {
        "id": "partial-domain-factor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_partial,
        "rationale": (
            "Rejection from the product clause result = pDen * decval qdigits "
            "on the multi-digit branch, where the impl returns decval qdigits "
            "(dropping the factor). Attacks the `qdigits` binder at a LENGTH "
            "the near-miss mishandles: the rival is genuinely CORRECT on the "
            "single-digit sub-domain and wrong beyond it, so the rejection "
            "comes from the spec pinning the product at every operand length "
            "rather than from the rival being wrong everywhere."
        ),
        "refinement": (
            "This is the narrow-spec counterexample shape: an impl correct on a "
            "real sub-domain (a single-digit operand — where a spec exercised "
            "only on short operands would admit it) but dropping the factor as "
            "soon as the operand is written with more digits. For factor 3 and "
            "operand '12' it yields 12 instead of 3*12=36, while for factor 3 "
            "and operand '7' it yields the correct 21. So it does NOT resolve, "
            "and it fails only on the longer-operand inputs — including the "
            "issue's own multi-digit operand. Its witness sits at a two-digit "
            "operand precisely to demonstrate that the sub-domain the near-miss "
            "claims to handle does not extend there; the single-digit agreement "
            "is what distinguishes it from drop-factor, which is wrong at every "
            "input."
        ),
        "witness": _witness(3, [1, 2]),
    },
    {
        "id": "skip-zero-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_skip_zero,
        "rationale": (
            "Rejection from the product clause result = pDen * decval qdigits at "
            "a ZERO-VALUED operand: the impl returns pDen where the clause "
            "demands pDen * 0 = 0. Attacks the totality of the product — the "
            "clause holds with no exception carved out for a zero-valued "
            "operand — which is the one part of the defended surface no other "
            "rival in this battery reaches, since every other witness sits at "
            "an operand of nonzero value."
        ),
        "refinement": (
            "A faithful real correspondent that skipped a zero-valued operand "
            "instead of folding it in agrees with the frozen behaviour on every "
            "operand of nonzero value, so it would look correct across most of "
            "the grid. For factor 2 and operand '0' it yields 2 instead of "
            "2*0=0, so the combined quantity is a nonzero one where the "
            "modeled behaviour produces zero, and the downstream handling that "
            "consumes a zero combined denominator is never reached. It does NOT "
            "resolve."
        ),
        "witness": _witness(2, [0]),
    },
    {
        "id": "reversed-positional-read",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _r_reverse_order,
        "rationale": (
            "Rejection from the product clause result = pDen * decval qdigits: "
            "decval reads the digit list most-significant-first, so folding it "
            "from the other end assigns the positional weights in reverse and "
            "denotes a different integer whenever the digit sequence is not "
            "symmetric. Attacks the `qdigits` binder along the one axis no other "
            "rival here touches — the ORDER of the digits, i.e. the positional "
            "structure of decval itself, which is what makes the digit-sequence "
            "carrier load-bearing rather than a plain value."
        ),
        "refinement": (
            "A faithful real correspondent that read the decimal operand from "
            "the wrong end would agree with the modeled behaviour on every "
            "operand whose digits are symmetric — a single-digit operand "
            "included — and so would look correct on a short-operand grid. For "
            "factor 2 and the operand written '1','0','0' it reads the operand "
            "as 1 rather than 100, giving 2 instead of 2*100=200, so the "
            "constructed quantity is wrong by two orders of magnitude at exactly "
            "the multi-digit operand family the reported behaviour turns on. It "
            "does NOT resolve."
        ),
        "witness": _witness(2, [1, 0, 0]),
    },
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos,
        "rationale": (
            "A structurally-different but CORRECT impl: read the operand value "
            "first, seed the accumulator with it, then fold in the factor with "
            "the multiplication commuted (value * factor). It computes the "
            "identical pDen * decval qdigits product and must verify. The proof "
            "reuses the same loop-equals-fold helper and closes with Nat.mul_comm "
            "in place of Nat.one_mul — no new lemma, no induction. If it cannot "
            "verify, the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-distributed-read",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_distribute,
        "rationale": (
            "A CORRECT impl whose shape is genuinely far from the frozen one: a "
            "single accumulator started at 0, with the whole-number factor "
            "distributed INTO the positional read (`acc * 10 + pDen * d` per "
            "digit) instead of applied to a finished operand value. Equal to "
            "pDen * decval qdigits by distributivity, so it must verify. Unlike "
            "the reorder positive above it shares neither of the frozen impl's "
            "locals nor its fold shape, so the frozen loop-equals-fold helper "
            "does not apply and the proof carries its own generalized induction "
            "as a `have` in the proof body — no new top-level declaration. This "
            "is the real SPEC-TOO-STRONG probe: if the product clause admits "
            "only impls that compute the operand value as a separate step, it is "
            "pinning an implementation shape rather than the behaviour."
        ),
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "Non-vacuity of the obligation at the inputs the failing tests "
            "observe. On this total carrier the analogue of PRECOND-TOO-STRONG "
            "is the obligation being unsatisfiable at an F2P-shaped input, so "
            "this case discharges problem_spec_denominatorProduct BY EVALUATION "
            "(`decide`) at two concrete such points — factor 2 with the "
            "multi-digit operand '1','0','0', and factor 2 with the zero-valued "
            "operand '0' — together with each point's preconditions (1 ≤ pDen "
            "and every digit < 10, both by evaluation), as `have`s, before "
            "closing the frozen obligation verbatim. So the clause is shown "
            "SATISFIABLE at the very inputs that matter, and the two "
            "preconditions are shown to ADMIT them rather than exclude them. "
            "Must verify; a failure of any `have` would mean the modeled clause "
            "or its precondition rules out an F2P-shaped input. Nothing is "
            "assumed: no new declaration, no assumption token, the theorem "
            "statement byte-identical, the frozen tactic body retained as the "
            "closing step."
        ),
    },
]
