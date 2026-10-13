"""properties.py — G-PBT falsification battery for astropy__astropy-14369 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation. It is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a single ``Nat`` binder):

  reduceDivisionChain (n)   ensures out = expVec n
                            ensures out.length = n

``expVec n`` is the length-``n`` exponent vector whose element ``k`` is
``chainPower k`` — the closed form ``+1`` at the leading position ``0`` and
``-1`` at every later position, modelled DEEPLY in the ``pure`` region (there is
no opaque oracle to echo; the ``axioms`` region is empty). The method has NO
``require`` clause, so the admitted domain is total: every ``n : Nat`` is in
scope. ``n`` is the sole free input, standing for the number of operand
positions of a left-grouped chain; the post-images must hold for EVERY value it
takes, which is what makes the partial-domain rivals below refutable at a
concrete point.

The load-bearing clause is the value equation ``out = expVec n``, which pins
EVERY position to its closed-form exponent independently; the second clause
pins the total count. The rivals attack, in turn: the leading position (which
must be ``+1``), the interior/trailing positions (which must be ``-1``), the
alternating-parity mis-reading that agrees with the closed form only at the
first two positions, and the length.

ADVERSARIAL READ of the classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    an input may carry a fractional heap permission an impl can overwrite. Lean
    and Velvet are referentially transparent: ``n`` is an immutable value (the
    method declares no ``mut`` parameter), there is no heap and no aliasing, so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated — reported as N/A in the footer.
  * UNGROUNDED-ORACLE ECHO — N/A. ``expVec`` is a total, fully unfolded function
    of the method's own argument (a concrete ``def`` in the ``pure`` region,
    empty ``axioms`` region), so there is no opaque answer-key an impl could
    echo without doing the work. The positive controls are honest
    cheapest-reshape variants (``pos-*``) instead.
  * PARTIAL-DOMAIN / VALUE — the main class here. Each rival is right on part of
    the position domain and diverges on a sub-domain: the leading position, the
    trailing position, or the even interior positions.

WITNESS MECHANICS. The frozen impl is a ``while`` loop, whose extracted program
does NOT reduce under kernel ``decide`` (it compiles to ``forIn``/well-founded
recursion). Every rival below is therefore written LOOP-FREE, so its extracted
program reduces and ``<name>Tester n = false`` decides. This is also exactly
what makes each witness a discriminator: the same ``decide`` FAILS to reduce
against the frozen loop-based solution, so half 2 (fails on gold) holds by
construction while half 1 (elaborates against the rival) is a genuine
counterexample. Each witness reaches the method contract through Velvet's own
tester machinery (``extract_program_for`` / ``derive_tester_for``); it is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict.

WITNESS PLACEMENT. The single binder ``n`` is moved across the reject witnesses
— ``n = 1`` (the head/length boundary), ``n = 2`` (the trailing operand), and
``n = 3`` (the first even interior position) — so the battery probes three
distinct input points rather than pinning ``n``. Each rival is refuted at the
smallest ``n`` that exposes its specific divergence.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the changed
behaviour is modelled deeply, and its soundness against the real callee is a
G-AX concern checked by axiom_check.py). The gate ignores ``AXIOM_TESTS``.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14369"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body, verbatim (between -- impl-start and -- impl-end).
# ---- Full-replacement rivals swap THIS for a loop-free body; the fragment lies
# ---- wholly inside the impl region and is unique (both asserted at load). ----
_GOLD_IMPL = (
    "    let mut result : List Int := []\n"
    "    let mut i := n\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ n\n"
    "      -- `result` holds the exponents of operand positions i .. n-1.\n"
    "      invariant result = expVecFrom i (n - i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      -- The accumulated left group `result` is extended on the FRONT by the\n"
    "      -- operand at position i-1: a leading position (i-1 = 0) carries +1, every\n"
    "      -- later position carries -1.\n"
    "      result := chainPower (i - 1) :: result\n"
    "      i := i - 1\n"
    "    return result"
)
assert _GOLD_IMPL in _BASE, "gold impl region drifted from Solution.lean"

# ---- the loop-body step line, for the in-loop reshape positive ----
_LOOP_STEP = "      result := chainPower (i - 1) :: result\n"

# ---- the accumulator-init line, for prepending an admissibility assert ----
_RESULT_INIT = "    let mut result : List Int := []\n"

# ---- the frozen proof block (a tactic body is elided from the consumer spec
# ---- view, so a positive control may retune it without touching the spec or
# ---- dropping the obligation). Unique in the file. ----
_PROVE = (
    "prove_correct reduceDivisionChain by\n"
    "  loom_solve\n"
    "  · rw [invariant_2, ← expVecFrom_drop_step n i (by omega) (by omega)]\n"
    "  · injection i_2 with hi1 hr1\n"
    "    subst hr1\n"
    "    rw [invariant_2]; simp only [expVec, done_1, Nat.sub_zero]\n"
)
assert _PROVE in _BASE, "frozen proof block drifted from Solution.lean"


def _module(body):
    """Full-replacement variant: swap the whole loop body for `body`, keeping
    the frozen proof (which then fails to elaborate against a reshaped impl —
    the rejection)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness preamble: reach the method contract through Velvet's tester. ----
def _tester():
    m = "reduceDivisionChain"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n")


def _witness(n):
    return _tester() + (
        f"example : reduceDivisionChainTester {n} = false := by\n  decide\n")


# ---- positive-control impls (loop-free / reshaped, MUST verify) ----
# Closed-form: return the modelled vector directly. Structurally different from
# the backward accumulator loop, still correct on every n. Retune the proof to
# the one-liner the reshaped impl needs.
_POS_DIRECT_BODY = "    let out : List Int := expVec n\n    return out"
_POS_DIRECT_PROVE = "prove_correct reduceDivisionChain by\n  loom_solve\n"

# In-loop reshape: inline the closed form as an explicit branch in the loop
# body instead of calling the pure helper. Same value flow; the proof folds the
# branch back to the helper before the drop-step rewrite.
_POS_INLINE_STEP = (
    "      result := (if i - 1 = 0 then (1 : Int) else -1) :: result\n")
_POS_INLINE_PROVE = (
    "prove_correct reduceDivisionChain by\n"
    "  loom_solve\n"
    "  · show (if i - 1 = 0 then (1:Int) else -1) :: result = _\n"
    "    rw [invariant_2, ← chainPower, "
    "← expVecFrom_drop_step n i (by omega) (by omega)]\n"
    "  · injection i_2 with hi1 hr1\n"
    "    subst hr1\n"
    "    rw [invariant_2]; simp only [expVec, done_1, Nat.sub_zero]\n"
)

# Admissibility: keep the frozen impl verbatim and discharge, at entry, a live
# assertion that the post-image is satisfiable AND non-degenerate at an
# F2P-shaped point (a three-operand chain -> [+1,-1,-1], length 3). The extra
# proof bullet discharges the assert; the rest of the frozen proof is unchanged
# so the two ensures clauses still discharge for the frozen impl.
_ADMISS_INIT = (
    "    assert (with_name_prefix `assert\n"
    "      (expVec 3 = [1, -1, -1] ∧ (expVec 3).length = 3))\n"
    "    let mut result : List Int := []\n")
_ADMISS_PROVE = (
    "prove_correct reduceDivisionChain by\n"
    "  loom_solve\n"
    "  · decide\n"
    "  · rw [invariant_2, ← expVecFrom_drop_step n i (by omega) (by omega)]\n"
    "  · injection i_2 with hi1 hr1\n"
    "    subst hr1\n"
    "    rw [invariant_2]; simp only [expVec, done_1, Nat.sub_zero]\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-closed-form-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_module(_POS_DIRECT_BODY), _PROVE, _POS_DIRECT_PROVE),
        "rationale": "a loop-free impl that produces the exponent vector "
                     "directly is observationally `expVec n` on every n and "
                     "trivially has length n, so both ensures clauses "
                     "discharge; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-inline-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the loop body: inline the per-position closed form as an
        # explicit branch instead of the pure helper. Same accumulator loop,
        # same value flow; the proof folds the branch back before the drop step.
        "module": _swap(_swap(_BASE, _LOOP_STEP, _POS_INLINE_STEP),
                        _PROVE, _POS_INLINE_PROVE),
        "rationale": "inlining the +1/-1 branch in the loop body computes the "
                     "same head-vs-rest exponent as the pure helper, so "
                     "`out = expVec n` still holds pointwise and the proof "
                     "closes with the branch folded back to the helper; must "
                     "verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause, so no precondition
    # could exclude an F2P-shaped input; the usual "a normal input satisfies
    # the precondition" probe is vacuous. Re-aimed at the residual risk on a
    # total domain: that the post-image is UNSATISFIABLE / degenerate at the
    # interesting point. The case discharges a live in-region assert that the
    # exponent vector at a three-operand chain is exactly [+1,-1,-1] with
    # length 3; the impl is kept verbatim so both ensures clauses still
    # discharge too. (RE-AIMED from nagini's precondition-admits probe.)
    # =====================================================================
    {
        "id": "admiss-expvec-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _RESULT_INIT, _ADMISS_INIT),
                        _PROVE, _ADMISS_PROVE),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped point: at three operand positions it demands "
                     "exactly [+1,-1,-1] of length 3 (leading +1, the rest -1). "
                     "The in-region assert must discharge (else the obligation "
                     "would be unsatisfiable / PRECOND-TOO-STRONG); the impl is "
                     "kept verbatim so the two ensures clauses discharge as "
                     "well.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong loop-free impls sharing the
    # frozen spec that MUST be rejected, each with a machine-checked
    # refutation witness at a concrete n and the argument that its faithful
    # real counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "weak-all-minus-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Emits -1 at EVERY position, dropping the leading-position special
        # case. Agrees with the closed form on every non-leading position;
        # wrong exactly at position 0. Refuted at n=1 (the head/single-operand
        # boundary), the smallest chain that exposes it.
        "module": _module(
            "    let out : List Int := List.replicate n (-1)\n    return out"),
        "refinement": "a counterpart that gives the leading operand exponent -1 "
                      "mis-reads a single-operand chain and flips the head of "
                      "every longer chain, so the failing grammar tests that pin "
                      "the leading unit to +1 still observe the wrong sign and "
                      "still fail. It would NOT resolve.",
        "rationale": "REJECT from `out = expVec n`: at position 0 the post-image "
                     "demands +1 (`chainPower 0 = 1`) and the impl yields -1. "
                     "Refuted at n=1, the head/length boundary no other rival "
                     "probes for this reason.",
        "witness": _witness(1),
    },
    {
        "id": "weak-alternating-parity",
        "kind": "uniqueness",
        "expect": "reject",
        # Reads the exponent as (-1)**k: +1 at even positions, -1 at odd. Agrees
        # with the closed form only at positions 0 and 1 and diverges at every
        # even position >= 2. Refuted at n=3, whose position 2 must be -1 but is
        # given +1.
        "module": _module(
            "    let out : List Int := (List.range n).map "
            "(fun k => if k % 2 = 0 then (1:Int) else -1)\n    return out"),
        "refinement": "a counterpart that alternates the operand sign by parity "
                      "gives interior even positions +1, so a three-operand "
                      "chain is read with its trailing operand's sign flipped — "
                      "exactly the jumbled ordering the failing tests reject. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = expVec n`: the post-image demands -1 at "
                     "every position >= 1, but parity gives +1 at the first even "
                     "interior position. Refuted at n=3 (position 2 = +1 where "
                     "-1 is required).",
        "witness": _witness(3),
    },
    {
        "id": "weak-trailing-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: correct at the leading position AND on every interior
        # position, but the TRAILING position of a length>=2 chain is mis-signed
        # +1. The sharpest value rival — it agrees with the closed form
        # everywhere except the last position. Refuted at n=2, the smallest
        # chain with a distinct trailing operand.
        "module": _module(
            "    let out : List Int := (List.range n).map "
            "(fun k => if k = 0 then (1:Int) else if k + 1 = n then (1:Int) "
            "else -1)\n    return out"),
        "refinement": "a counterpart that leaves the trailing operand at +1 "
                      "reads a chain's last unit with the wrong sign, so the "
                      "failing tests that pin the trailing exponent to -1 still "
                      "fail. It would NOT resolve.",
        "rationale": "REJECT from `out = expVec n`: at position n-1 the "
                     "post-image demands -1 (for n>=2) and the impl yields +1. "
                     "Refuted at n=2, the trailing-operand sub-domain the other "
                     "value rivals leave correct — so this near-miss carries its "
                     "own separating input.",
        "witness": _witness(2),
    },
    {
        "id": "weak-length-extra",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the OTHER top-level clause: the values are correct but the
        # vector carries one extra element, so `out.length = n` fails (and the
        # value clause with it). Refuted at n=1.
        "module": _module(
            "    let out : List Int := expVec n ++ [1]\n    return out"),
        "refinement": "a counterpart that emits one exponent too many produces a "
                      "composite with an extra operand factor, so the failing "
                      "tests comparing the parsed unit against the intended one "
                      "still fail on the surplus factor. It would NOT resolve.",
        "rationale": "REJECT from `out.length = n` (and from `out = expVec n`): "
                     "the impl returns a vector of length n+1 where the "
                     "post-image demands exactly n. This is the rival that "
                     "attacks the length clause specifically. Refuted at n=1.",
        "witness": _witness(1),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals). The sibling contracts a
# list-valued `reduce_division_chain(units)` over a `List[int]` carrier under
# fractional-permission framing; this bundle contracts the SAME behaviour as
# `reduceDivisionChain(n)` over a `Nat` operand count -> `List Int` exponent
# vector, with no heap and no `mut`. The exponent-vector argument is preserved
# in every ported case; only the carrier and the permission machinery change.
#
#   sibling case                  -> here
#   ---------------------------------------------------------------------
#   pos-control-forward-fold      -> pos-inline-closed-form (+ pos-closed-form-
#                                    direct)                             PORTED
#   admissibility-f2p-shaped      -> admiss-expvec-nondegenerate         RE-AIMED
#   frame-mutation-write-units    -> (none)                              VACUOUS
#   prepatch-alternating-parity   -> weak-alternating-parity            PORTED
#   partial-domain-last-operand   -> weak-trailing-operand              PORTED
#   all-minus-one-head-flip       -> weak-all-minus-one                 PORTED
#
# 4 ported (one sibling positive split into two reshape positives), 1 re-aimed,
# 1 vacuous = 6.
#
# PORTED (positives): the sibling ships ONE structurally-different correct impl
#   (a forward-append fold vs the gold backward-prepend fold). A forward-append
#   fold is portable but needs a fresh append-preservation lemma whose `lake`
#   cost buys nothing over cheaper reshapes. It is carried by TWO honest
#   cheapest-reshape positives instead: pos-closed-form-direct (produce the
#   vector directly) and pos-inline-closed-form (inline the +1/-1 branch in the
#   frozen accumulator loop). Both are correct on every n and both verify; the
#   structural-difference intent (a different-shaped impl still satisfies the
#   spec) is preserved.
# PORTED (rivals): the three value rivals port directly — the parity rival IS
#   the differential the issue reports, the last-operand rival is the trailing-
#   boundary near-miss, and the all-minus-one rival is the leading-boundary
#   near-miss. Each is re-expressed loop-free over the Nat carrier so its tester
#   reduces under `decide`; each is refuted at the smallest n exposing it.
# ADDED (1, no sibling counterpart): weak-length-extra. The velvet spec has a
#   SECOND top-level clause `out.length = n` the sibling folds into its single
#   Forall; this rival attacks that clause specifically (values right, one
#   surplus element), so both independent clauses of the postcondition are
#   attacked.
# RE-AIMED (admissibility): the sibling's case establishes that a normal
#   F2P-shaped input satisfies the precondition (len>=1, the read permission).
#   This method has NO `require` clause, so nothing could exclude a normal input
#   and that probe is vacuous. It is re-aimed at the residual admissibility risk
#   on a total domain: that the post-image is UNSATISFIABLE / degenerate at the
#   interesting point. The case discharges a live in-region assert that the
#   exponent vector at a three-operand chain is exactly [+1,-1,-1] of length 3.
# VACUOUS (frame-mutation): the sibling writes back to the half-permission
#   `units` to prove the read-only frame holds. This backend is referentially
#   transparent and the method declares NO `mut` binder, so there is no
#   read-only input to overwrite and no substitute probe to build. Not
#   fabricated.
#
# WITNESS DISTINCTNESS. The sole binder n is moved across the reject witnesses:
#   n=1 (weak-all-minus-one, weak-length-extra), n=2 (weak-trailing-operand),
#   n=3 (weak-alternating-parity) — three distinct input points. n=1 is shared
#   by two rivals that fail there for DIFFERENT reasons and against DIFFERENT
#   clauses (a flipped head value vs a surplus element / wrong length), so they
#   are distinct predicates, not one attack written twice. Each near-miss
#   (trailing / leading) is refuted on the sub-domain that separates it from the
#   blunter value rivals, so its sub-domain claim is machine-checked.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the changed behaviour is
# modelled deeply (no `axiom` in the bundle) and its soundness against the real
# callee lives in axiom_check.py.
AXIOM_TESTS = []
