"""properties.py — G-PBT falsification battery for sympy__sympy-21847 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_selectMonomials`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
contracts TWO byte-identical functions (``keep_comm`` / ``keep_noncomm``) over a
``PSeq[int]`` carrier and pins each against a GROUNDED front-recursive pure fold
(nagini's ``deg_sum``). This Lean bundle models the SAME single purely-functional
core — the per-candidate acceptance filter that keeps a candidate monomial
exactly when its TOTAL degree (the sum of its exponent vector) meets the
threshold — over a ``List (List Nat)`` carrier, and the SAME grounding: the
postcondition relates ``result`` structurally to the inputs
(``result = candidates.filter (fun powers => decide (minDegree ≤ powers.sum))``),
with no opaque answer key to echo. The commutative and non-commutative branches
differ in nagini only by name (mapping.md: "a single Lean model covers both"), so
the two nagini sites collapse to ONE modeled function here; their per-site
duplicates (``keep_comm`` vs ``keep_noncomm``) have no distinct counterpart.

DEFENDED SURFACE (one modeled behavior; ONE top-level postcondition clause).
``problem_spec_selectMonomials minDegree candidates result`` pins EXACTLY:

  * (C0)  ``result = candidates.filter (fun powers => decide (minDegree ≤
    powers.sum))`` — the kept candidates are exactly those whose TOTAL degree
    (``powers.sum``) reaches ``minDegree``, in their original order.

The BEHAVIOURAL DISCRIMINATOR (the fix): the acceptance test is against the SUM
of the per-variable exponents, not the LARGEST single exponent. The pre-fix
behaviour tested the max; on a candidate that spreads its degree across several
variables (e.g. exponent vector [2,1], total degree 3, max 2) the max rule wrongly
drops it while the sum rule keeps it. The ``wrong-max`` rival below IS that
pre-fix behaviour.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``minDegree`` (the
threshold) and ``candidates`` (the list of exponent vectors). Both are
load-bearing and both are varied across the reject witnesses (see the point-spread
block at the bottom): ``minDegree ∈ {1,2,3}`` and ``candidates`` ranges over
single- and two-element lists whose inner exponent vectors have length 1 and 2.
The three reject witnesses probe three DISTINCT input tuples (``pts=3``).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling rejects a rival that
    WRITES into the read-only ``powers`` input while still computing the correct
    sum, on permission grounds (``Acc(list_pred(powers),1/2)``). Lean is
    referentially transparent: ``candidates`` is an immutable value, there is no
    ``mut`` input binder, no aliasing, and no read-only cell to overwrite. The
    class cannot be expressed and no substitute probe is fabricated (porting map:
    vacuous here).

  * UNGROUNDED-ORACLE ECHO — N/A (as in nagini). The postcondition is GROUNDED:
    ``result`` is pinned by ``candidates.filter`` over the actual input carrier
    and the transparent ``powers.sum``. There is no opaque answer key to echo —
    the honest cheapest implementation IS the loop that filters by the total
    degree. In its place the battery carries honest cheapest-implementation
    POSITIVE CONTROLS that must verify.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this carrier, measured. This is
    vanilla Lean 4: termination is discharged when ``implementation_*`` is
    DEFINED, not by the ``correct_*`` obligation. A non-decreasing recursive
    ``def`` does not fail to verify, it fails to ELABORATE (``fail to show
    termination ... no parameters suitable for structural recursion``), so there
    is no shippable same-spec variant; and a ``partial def`` elaborates but is
    opaque to the kernel, so the frozen obligation AND every witness fail
    identically on ``unfold``, leaving nothing that could discriminate. See the
    accounting block at the bottom for the two build results.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: the pre-fix MAX reduction (wrong on any vector
    whose max is below the threshold but whose sum reaches it); dropping the first
    exponent from the total (wrong whenever the first variable carries decisive
    degree); and a strict comparison (wrong exactly at the equality boundary — the
    heart of the F2P case).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate at one CONCRETE,
fully-``decide``-able input (small ``Nat`` literals; the carrier is transparent,
no opaque term to condition on) and closes by ``decide``. Each witness binds
NOTHING in its head (all inputs are ground literals), so there are no hypotheses
whose consistency could be in question. Each was checked with two real ``lake env
lean`` builds to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is the
acceptance test computed the wrong way (max instead of sum, a dropped exponent, or
a strict comparison), so the produced monomial set omits (or over-includes) terms
of exactly the total degree the reported issue is about, and the F2P
``test_monomials`` assertions — which pin the full set of terms whose total degree
reaches the threshold — would mismatch. So the faithful patch would NOT resolve.

AXIOM lane: EMPTY here (as in nagini). The bundle declares no ``opaque`` callee
and consumes no ``axiom`` (the changed reduction is modeled deeply as
``powers.sum``); the axiom lane belongs to G-AX, and the nagini ``AXIOM_TESTS``
(also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-21847"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The two-line acceptance test in the impl loop body: the guard on the total
# degree and the order-preserving append of the kept candidate. Every impl
# reshape lands entirely inside `-- impl-start`/`-- impl-end`. NOTE: the proof
# region also contains `if minDegree ≤ powers.sum then`, but NOT followed by the
# `acc := acc ++ [powers]` append line, so this two-line block is unique to the
# impl.
_GUARD_BLOCK = ("      if minDegree ≤ powers.sum then\n"
                "        acc := acc ++ [powers]")

# The frozen proof's intro line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the theorem
# STATEMENT or the spec view.
_INTRO = "  intro minDegree candidates"

# The frozen final theorem's `unfold` line (proof region), unique in the file.
# The two positive controls each append ONE guard-normalising rewrite after it, so
# the reshaped guard is brought back to the frozen form before the frozen fold
# lemma is applied. Edits land strictly inside `-- proof-start`/`-- proof-end`, so
# the `theorem correct_selectMonomials` STATEMENT and the spec view are untouched.
_UNFOLD = "  unfold problem_spec_selectMonomials implementation_selectMonomials"

# sanity: anchors present exactly once
assert _BASE.count(_GUARD_BLOCK) == 1, "guard-block anchor drift"
assert _BASE.count(_INTRO) == 1, "intro anchor drift"
assert _BASE.count(_UNFOLD) == 1, "unfold anchor drift"


# ---------------------------------------------------------------------------
# witness scaffold. State the spec predicate directly at a concrete, decidable
# input. `decide` reduces both the `Id.run do`/`for` implementation and the
# `List.filter` spec on ground `Nat` literals, so no proof engineering is needed.
# Each witness holds of its rival (the two disagree at this input) and FAILS on
# the frozen solution (there the two agree, so the negation is false).
# ---------------------------------------------------------------------------
def _w(min_degree, candidates):
    return (
        f"example : ¬ problem_spec_selectMonomials {min_degree} {candidates}\n"
        f"    (implementation_selectMonomials {min_degree} {candidates}) := by\n"
        "  unfold problem_spec_selectMonomials implementation_selectMonomials\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_selectMonomials` statement byte-identical.
    #
    # AUDIT REPAIR (both positives replaced). The two positives this battery
    # originally shipped (`pos-let-hoist`: hoist `powers.sum` into a local `s`;
    # `pos-ge-form`: write the guard in the `≥` orientation) were measured to be
    # `rfl`-DEFINITIONALLY EQUAL to the frozen implementation: a standalone
    # `example : @reshape = @implementation_selectMonomials := by rfl` closed for
    # BOTH (two real builds, exit 0). `≥` is notation for the flipped `≤` and a
    # non-dependent `let` is zeta-reduced, so neither reshape presented the
    # elaborator with a different term at all — the frozen tactic script closed
    # them because there was nothing to reshape. A positive that is defeq to the
    # frozen impl exercises no proof obligation the frozen file does not already
    # discharge, so it passed honestly while testing nothing.
    #
    # Both are replaced by reshapes measured NOT defeq to the frozen impl (the
    # same `rfl` probe FAILS: "The left-hand side ... is not definitionally equal
    # to the right-hand side", two real builds, exit 1). Each therefore breaks the
    # frozen tactic script and requires a real extra proof step (verified: the
    # unmodified frozen proof fails on each with `Tactic 'rewrite' failed: Did not
    # find an occurrence of the pattern`, then closes once the guard is normalised
    # to the frozen form). That is what makes them load-bearing SPEC-TOO-STRONG
    # probes: a faithful correct impl the spec could only accept via a genuine
    # re-proof.
    # =====================================================================
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: state the acceptance test as the
        # NEGATION of the strict opposite comparison, `¬ (powers.sum < minDegree)`,
        # instead of `minDegree ≤ powers.sum`. Classically the same predicate but
        # NOT definitionally equal (`Nat.lt` is a distinct decidable relation, and
        # the `¬`/`ite` wrapping changes the `Decidable` instance the loop
        # elaborates through), so the frozen `rw` no longer matches and the proof
        # needs a real `Nat.not_lt` normalisation step first.
        "module": _swap(
            _swap(_BASE, _GUARD_BLOCK,
                  "      if ¬ (powers.sum < minDegree) then\n"
                  "        acc := acc ++ [powers]"),
            _UNFOLD,
            _UNFOLD + "\n  simp only [Nat.not_lt]"),
        "rationale": "correct reshape that states the acceptance test as the "
                     "negation of the strict opposite comparison, "
                     "`¬ (powers.sum < minDegree)` instead of `minDegree ≤ "
                     "powers.sum`. The two accept exactly the same candidates on "
                     "every input, so clause C0 (the filter equality) still holds — "
                     "else SPEC-TOO-STRONG. Unlike the reshapes this case replaced, "
                     "it is NOT definitionally equal to the frozen impl (measured: a "
                     "standalone `rfl` between the two FAILS), so the frozen tactic "
                     "script genuinely breaks on it and the case is reproven rather "
                     "than passed for free: one `simp only [Nat.not_lt]` normalises "
                     "the guard to the frozen form before the frozen fold lemma "
                     "applies. Statement byte-identical, no new axiom/lemma, no "
                     "assumption token. Ports the nagini pos-control-reshape-comm "
                     "positive (there: a local-variable/statement reshape of the "
                     "accumulator loop).",
    },
    {
        "id": "pos-foldl-sum",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: compute the total degree with an
        # explicit left fold, `powers.foldl (· + ·) 0`, instead of `powers.sum`
        # (which is a right fold — `List.sum_eq_foldl` is a real theorem, not
        # `rfl`). Not definitionally equal, so the frozen `rw` fails until the two
        # folds are identified.
        "module": _swap(
            _swap(_BASE, _GUARD_BLOCK,
                  "      if minDegree ≤ powers.foldl (· + ·) 0 then\n"
                  "        acc := acc ++ [powers]"),
            _UNFOLD,
            _UNFOLD + "\n  simp only [← List.sum_eq_foldl]"),
        "rationale": "correct reshape that computes the candidate's TOTAL DEGREE "
                     "with an explicit left fold, `powers.foldl (· + ·) 0`, rather "
                     "than `powers.sum`. It totals the very same exponents, so the "
                     "kept set is identical on every input and C0 holds — else "
                     "SPEC-TOO-STRONG. This is the stronger of the two positives: "
                     "`powers.sum` is a RIGHT fold, so the equality with the left "
                     "fold is a real theorem (`List.sum_eq_foldl`) and not "
                     "definitional (measured: `rfl` between the reshape and the "
                     "frozen impl FAILS). The frozen script therefore does not close "
                     "it for free — one `simp only [← List.sum_eq_foldl]` rewrite "
                     "re-establishes the frozen guard form, after which the frozen "
                     "fold lemma applies. It defends C0 against the reading that the "
                     "spec accidentally pins the particular way the total is "
                     "accumulated rather than its VALUE. Statement byte-identical, no "
                     "new axiom/lemma.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The nagini precondition-admission self-call
    # (a fresh probe [2,1] with min_degree 0) re-expresses here as: discharge the
    # spec predicate by evaluation at a concrete F2P-shaped combination as a
    # `have`, then close the frozen obligation verbatim. Nothing is assumed: no new
    # declaration, statement byte-identical, ground instance is a `have` prepended
    # to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _INTRO,
            "  have _ground : problem_spec_selectMonomials 3 [[3], [2, 1], [1, 1]]\n"
            "      (implementation_selectMonomials 3 [[3], [2, 1], [1, 1]]) := by\n"
            "    unfold problem_spec_selectMonomials implementation_selectMonomials\n"
            "    decide\n"
            + _INTRO),
        "rationale": "the obligation is discharged at a normal F2P-shaped input — "
                     "candidates [[3],[2,1],[1,1]] with minDegree 3, the F2P "
                     "discriminator where the total-degree-3 candidate [2,1] "
                     "(max 2 < 3) MUST be kept and the total-degree-2 candidate "
                     "[1,1] dropped — by evaluation as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behaviour would be unsatisfiable at exactly a normal F2P "
                     "input — the analogue of PRECOND-TOO-STRONG). Nothing is "
                     "assumed: no new declaration, statement byte-identical, ground "
                     "instance is a `have` in the existing tactic body. Ports "
                     "nagini's admiss-comm-selfcall (there: a fresh probe [2,1]).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, and (b) a witness pinning the violation
    # at one concrete input.
    # =====================================================================

    # ---- the pre-fix bug: reduce by the per-variable MAX, not the total degree ----
    {
        "id": "wrong-max",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behaviour: accept on the LARGEST single exponent
        # (`powers.foldr Nat.max 0`) instead of the total degree (`powers.sum`).
        "module": _swap(
            _BASE, _GUARD_BLOCK,
            "      if minDegree ≤ powers.foldr Nat.max 0 then\n"
            "        acc := acc ++ [powers]"),
        "refinement": "this IS the pre-fix bug: the acceptance test compares the "
                      "threshold against the LARGEST single exponent rather than the "
                      "total degree. The faithful real counterpart is the unpatched "
                      "predicate testing the max of the per-variable exponents. On "
                      "the reported case the candidate with exponent vector [2,1] "
                      "(total degree 3, max 2) is wrongly dropped at threshold 3, so "
                      "the produced monomial set omits every term that spreads its "
                      "degree across variables — exactly the defect the issue "
                      "reports. The F2P test_monomials assertions pin those terms as "
                      "present, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0: the spec pins the kept set as "
                     "`candidates.filter (minDegree ≤ powers.sum)` but the rival "
                     "filters on `minDegree ≤ powers.foldr Nat.max 0`; the two "
                     "disagree on any vector whose max is below the threshold but "
                     "whose sum reaches it. Refuted at minDegree=3, "
                     "candidates=[[2,1]] (sum 3 ≥ 3 kept by gold, max 2 < 3 dropped "
                     "by the rival).",
        "witness": _w(3, "[[2, 1]]"),
    },

    # ---- drop the first exponent from the total ----
    {
        "id": "drop-first-exponent",
        "kind": "uniqueness",
        "expect": "reject",
        # Sum only the exponents after the first (`(powers.drop 1).sum`), so the
        # first variable's exponent never counts toward the total degree.
        "module": _swap(
            _BASE, _GUARD_BLOCK,
            "      if minDegree ≤ (powers.drop 1).sum then\n"
            "        acc := acc ++ [powers]"),
        "refinement": "sums only the exponents AFTER the first, so the first "
                      "variable's exponent never contributes to the total degree. "
                      "The faithful real counterpart is an acceptance test over "
                      "`sum(list(powers.values())[1:])`. A candidate whose degree "
                      "sits (partly or wholly) in its first variable is then "
                      "under-counted and wrongly dropped — e.g. a single-variable "
                      "term of degree 3 gets total 0. The F2P test_monomials "
                      "assertions pin such terms as present, so the faithful patch "
                      "would NOT resolve.",
        "rationale": "REJECT from C0: the spec pins the filter on `powers.sum` but "
                     "the rival filters on `(powers.drop 1).sum`, which omits the "
                     "first exponent; the two disagree whenever the first variable "
                     "carries decisive degree. Refuted at minDegree=2, "
                     "candidates=[[2],[1,1]] (gold keeps both — sums 2 and 2 — but "
                     "the rival drops both: drop-first sums are 0 and 1).",
        "witness": _w(2, "[[2], [1, 1]]"),
    },

    # ---- off-by-one: strict comparison drops the exact-equality boundary ----
    {
        "id": "strict-boundary",
        "kind": "uniqueness",
        "expect": "reject",
        # Strict `<` instead of `≤`, so a candidate whose total degree EXACTLY
        # equals the threshold is dropped.
        "module": _swap(
            _BASE, _GUARD_BLOCK,
            "      if minDegree < powers.sum then\n"
            "        acc := acc ++ [powers]"),
        "refinement": "uses a strict comparison, so a candidate whose total degree "
                      "EXACTLY equals the threshold is dropped. This is the heart of "
                      "the reported case: the requested min degree equals the "
                      "requested max degree, and every kept term has total degree "
                      "exactly equal to the threshold — with the strict test the "
                      "produced set is EMPTY. The faithful real counterpart is an "
                      "acceptance test with `>` instead of `>=`. The F2P "
                      "test_monomials assertions pin the exact-equality terms as "
                      "present, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C0: the spec pins the filter on `minDegree ≤ "
                     "powers.sum` but the rival filters on `minDegree < powers.sum`; "
                     "the two disagree exactly when `powers.sum = minDegree` (the "
                     "F2P boundary). Refuted at minDegree=1, candidates=[[1]] (sum 1 "
                     "= 1 kept by gold, dropped by the strict rival).",
        "witness": _w(1, "[[1]]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness rivals — the 6 being 2 frame-mutation,
# 2 wrong-max, 1 partial-first, 1 strict, spread across the comm/noncomm sites)
# plus an EMPTY AXIOM lane. This bundle models the SAME single purely-functional
# core (the total-degree acceptance filter), where the commutative and
# non-commutative sites collapse to ONE Lean model, and re-expresses every
# non-vacuous sibling case.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   pos-control-reshape-comm     -> pos-negated-guard        RE-EXPRESSED
#   (none)                       -> pos-foldl-sum            ADDED (2nd positive)
#   admiss-comm-selfcall         -> admiss-ground            RE-EXPRESSED
#   wrong-max-comm               -> wrong-max                PORTED
#   wrong-max-noncomm            -> (folded into wrong-max)  COLLAPSED (one model)
#   partial-first-comm           -> drop-first-exponent      PORTED
#   strict-boundary-comm         -> strict-boundary          PORTED
#   frame-mut-comm               -> (none)                   VACUOUS (pure carrier)
#   frame-mut-noncomm            -> (none)                   VACUOUS (pure carrier)
#   AXIOM_TESTS (0)              -> (none)                   DROPPED (G-AX)
#
# COLLAPSED (wrong-max-noncomm): mapping.md establishes that the commutative and
#   non-commutative sub-branches differ ONLY in the candidate enumerator
#   (combinations_with_replacement vs product); the per-candidate acceptance loop
#   and its patched predicate are byte-identical, so a SINGLE Lean model covers
#   both. The nagini per-site duplicate (a second copy of the same reduction bug
#   attached to keep_noncomm) has no distinct counterpart on this carrier: it
#   attacks the identical clause of the identical model. Not omitted for
#   difficulty — there is only one modeled function to attack.
# RE-EXPRESSED (pos-negated-guard): the nagini positive reshapes the accumulator
#   loop (reordered framing pins, the per-element read hoisted into a named local
#   `e`). This carrier's loop reads the whole exponent vector's total degree, so
#   the analogous "structurally different but correct" reshape restates the
#   acceptance test as `¬ (powers.sum < minDegree)`. Measured NOT definitionally
#   equal to the frozen impl (a standalone `rfl` between the two FAILS), so the
#   frozen script really does break on it and one `Nat.not_lt` normalisation
#   reproves it. This REPLACES the battery's original `pos-let-hoist`, which an
#   audit measured to be `rfl`-defeq to the frozen impl and therefore vacuous.
# RE-EXPRESSED (admiss-ground): the nagini admissibility case builds a fresh
#   F2P-shaped probe [2,1] and self-calls to witness the precondition is
#   satisfiable. The frozen Lean obligation carries no precondition (∀ minDegree
#   candidates, unconditional), so the honest analogue is to discharge the
#   POSTCONDITION at the smallest F2P-shaped combination (candidates including the
#   discriminator [2,1] at threshold 3) as a `have`, proving the modeled behaviour
#   is satisfiable at a normal input, then close the frozen obligation verbatim.
# ADDED (pos-foldl-sum): a second positive control, and the stronger of the two.
#   The nagini sibling carried a single reshape positive; here a second one totals
#   the exponents with an explicit LEFT fold instead of `powers.sum` (a right
#   fold). Their equality is the theorem `List.sum_eq_foldl`, not `rfl`, so this
#   reshape provably presents the elaborator with a different term and must be
#   re-proven rather than accepted for free. This REPLACES the battery's original
#   `pos-ge-form` (`≥` is mere notation for the flipped `≤`, so that case was
#   `rfl`-defeq to the frozen impl and tested nothing).
# VACUOUS (frame-mut-comm / frame-mut-noncomm): the nagini frame-mutation rivals
#   write into the read-only `powers` input (a VALUE no-op) and are rejected on
#   permission grounds (Acc(...,1/2)). Lean is referentially transparent — no heap
#   permission, no `mut` input binder, no aliasing, no read-only cell to
#   overwrite. The class cannot be expressed; no substitute probe is fabricated.
# DIVERGENCE / NON-TERMINATION: the nagini sibling carries no diverge-*/nonterm-*
#   case, and on this carrier the class is genuinely VACUOUS — demonstrated with
#   two real builds rather than asserted. This bundle is vanilla Lean 4 (no
#   `loom.semantics.termination` option; the frozen file sets no such option), so
#   the termination obligation is discharged by the DEFINITION of
#   `implementation_selectMonomials`, not by the `correct_*` theorem:
#     (a) a non-decreasing recursive `def` does not merely fail to verify, it
#         fails to ELABORATE — `error: fail to show termination for
#         implementation_selectMonomials ... no parameters suitable for structural
#         recursion`. The file is uncompilable, so there is no same-spec variant to
#         ship: nothing distinguishes it from a syntax error.
#     (b) marking it `partial def` does elaborate, but then the impl is opaque to
#         the kernel and BOTH the frozen obligation and any witness fail
#         identically with `Tactic 'unfold' failed to unfold
#         'implementation_selectMonomials'` — i.e. the rejection is a tactic/
#         reducibility artefact and no witness can discriminate, so such a case
#         could only ever be recorded as `witness-undecided`.
#   There is therefore no diverging impl on this carrier that is both expressible
#   and refutable. Not a "known hole": under total semantics a diverging rival is
#   rejected for a real reason, and here it cannot even be written down.
# DROPPED (order/reversal rival, considered and rejected): a rival that reverses
#   the order of the kept candidates was considered but is NOT a legitimate
#   verify-does-not-resolve break here. The real function yields the kept terms
#   through `yield from set(...)`, which discards order downstream; an
#   order-reversing patch would still resolve the F2P. The frozen spec pins order
#   (via `List.filter`) more strictly than the F2P requires, so an order rival
#   would refute the spec at a point where the faithful patch DOES resolve —
#   exactly the false break to avoid. Not shipped.
#
# POINT SPREAD. The three reject witnesses probe three DISTINCT input tuples
# (pts=3):
#   (minDegree, candidates) =
#     (3, [[2, 1]])          wrong-max              C0
#     (2, [[2], [1, 1]])     drop-first-exponent    C0
#     (1, [[1]])             strict-boundary        C0
#   Across them minDegree ∈ {1,2,3}, and candidates ranges over single- and
#   two-element lists whose inner exponent vectors have length 1 and 2, so neither
#   input binder is pinned to a single value. (The spec has ONE top-level clause,
#   C0, the filter equality; all three rivals attack it, each at a distinct point
#   exercising a distinct failure of the total-degree computation.)
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the reduction is modeled deeply as `powers.sum`), so there is nothing to
# probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
