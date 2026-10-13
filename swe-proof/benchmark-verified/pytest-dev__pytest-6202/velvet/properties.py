"""properties.py — G-PBT falsification battery for pytest-dev__pytest-6202 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the single ``-- impl-start`` /
``-- impl-end`` region, and — for two cases — the ``prove_correct`` tactic body,
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct joinPath`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against a subject known to satisfy the spec).

DEFENDED SURFACE (one contracted method, ``joinPath``):

  joinPath (parts : List (List Char)) return (out : List Char)
    require  parts.length ≥ 1                       -- domain restriction
    ensures  out = joinDot parts                    <-- LOAD-BEARING

An ordered list of name parts is assembled into a single dotted path by placing
exactly one separator code point between consecutive parts and NOTHING ELSE.
``joinDot`` is the fully-unfolded front-recursive fold of that assembly: the
first part verbatim, then for each later part one separator followed by that
part. There is a single top-level clause over the single input binder ``parts``,
and it bundles four independent guarantees:
  (a) SEPARATION — exactly one separator sits between each pair of adjacent
      parts (n parts ⇒ n−1 separators);
  (b) FIDELITY — every code point of every part survives verbatim, in order,
      with NO post-assembly rewrite of any sub-window;
  (c) ORDER — the parts appear in their given order; and
  (d) TOTALITY — every part contributes, including the last, and including the
      degenerate one-part list at the precondition's own boundary.
The domain is total on ``parts.length ≥ 1``; total correctness is pinned (a
diverging loop may NOT discharge the postcondition vacuously — the loop carries
a ``decreasing`` measure).

GROUNDED, NOT AN ORACLE ECHO. ``joinDot`` is a concrete ``def`` spelled out in
the ``pure`` region as a total front-recursive function of the method's own
argument; the ``axioms`` region declares nothing. There is no opaque answer key
to echo — the cheapest honest impl IS ``return joinDot parts`` — so the
ungrounded-oracle-echo class is N/A and the cheapest positive control is that
direct return. Nothing in this carrier is ``opaque``, so no witness needs to
CONDITION on the carrier: every refutation is stated at literal inputs and no
witness binds a hypothesis (hence none can be `witness-inconsistent`).

WHY EVERY REJECT CASE CARRIES A ``witness_reference``. The frozen impl keeps a
backward ``while`` loop, and under ``loom.semantics.choice "demonic"`` its
fixpoint elaborates through a classical choice term the kernel cannot unfold. So
``decide`` against the FROZEN tester is stuck for every claim regardless of
truth — measured here, verbatim:

    Tactic `decide` failed for proposition
      joinPathTester [['a'], ['.', '[']] = false
    ... reduction got stuck at the `Decidable` instance

A gold-side exit code therefore carries NO information, and reading it as
"the witness discriminates" would attest to a refutation never performed (the
``witness-undecided`` defect: a forged witness asserting the rival is CORRECT
would clear both halves). Every reject case below is instead refuted against
``_REFERENCE`` — the loop-FREE ``return joinDot parts`` impl, which shares the
frozen spec and VERIFIES (checked by the gate before use), and whose tester DOES
reduce. It is shipped as the ``pos-direct`` positive too, so the battery itself
records that loop-freeness is not what any rival is being rejected for.

BINDER / CLAUSE COVERAGE. ``parts`` is the sole binder of the spec predicate.
The five reject witnesses probe FIVE distinct part-lists, varying both the
part-count and the part content, one per independent guarantee (plus a near-miss
split):
  * FIDELITY, window spanning a part BOUNDARY — ``weak-prepatch`` at
    ``[['a','.'],['[']]``;
  * FIDELITY, window INSIDE one part — ``weak-perpart`` (the near-miss) at
    ``[['x'],['.','[','y']]``;
  * SEPARATION — ``weak-nosep`` at ``[['a'],['b']]``;
  * ORDER — ``weak-reverse`` at ``[['a'],['b'],['c']]`` (3 parts);
  * TOTALITY at the precondition boundary — ``weak-droplast`` at ``[['a']]``
    (the ONLY one-part probe: a rival wrong only at ``parts.length = 1`` would
    otherwise verify unnoticed).
Part-counts 1, 2 and 3 all appear, so no length is pinned across the battery,
and no two witnesses share an input point.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling reasons about a
    read-only input held at a fractional heap permission an impl could WRITE.
    Lean and Velvet are referentially transparent: ``parts`` is an immutable
    value, this bundle declares no ``mut`` binder, there is no heap and no
    aliasing — so there is no read-only input to overwrite and no substitute
    probe to build. Not fabricated. The nagini sibling itself records this class
    as N/A.
  * DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

      - a guard-true loop with NO measure           -> exit 1, "Decreasing
        annotations are required in total correctness semantics";
      - a measure that strictly INCREASES
        (``decreasing k`` with ``k := k + 1``)      -> exit 1, goal ``k + 1 < k``;
      - a constant guard ``0 < 1`` with no
        ``done_with`` and ``decreasing (0 : Nat)``,
        returning an unambiguously wrong ``[]``     -> exit 1, goal ``0 < 0``;
      - the same with an explicitly false
        ``done_with 1 < 0``                         -> exit 1, goal ``0 < 0``.

    The third and fourth are the shape an earlier internal finding described as a
    corpus-wide non-decreasing-measure hole: the ``total`` obligation supposedly
    accepting any measure expression without proving it decreases. It does NOT
    reproduce on this bundle: the strict-decrease side condition is emitted and left
    unsolved (``⊢ 0 < 0``), so the wrong answer cannot be laundered through an
    unreachable exit here. The mechanism is in the Loom source, not a per-cell
    accident: ``TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop`` takes
    ``measure : β -> Nat`` and emits the ``measure b' < measure b`` conjunct, and the
    ``set_option`` elaborator itself opens that scope
    (``Loom/MonadAlgebras/WP/Options.lean``, lines 169-186). The class is genuinely
    closed by the frozen spec.

    No reject case is shipped, and the reason is a witness-contract limit that
    was MEASURED, not a proof difficulty: a diverging impl returns no wrong
    VALUE at any concrete input, so a value-level witness has nothing to refute.
    Built both ways — the measure-less rival plus the witness
    ``joinPathTester [['a']] = false`` exits 1 with the decreasing-annotation
    error AND a stuck ``decide``; the increasing-measure rival plus the same
    witness exits 1 on the stuck ``decide`` alone. The gate reads a failing
    RIVAL build as ``witness-unproven`` — an inconclusive outcome that would
    fail the whole battery — so shipping one would replace a true disposition
    with a MALFORMED-TESTS record. Disposition: REJECTED-BY-SPEC, not
    expressible as a witnessed case. The pin is attested POSITIVELY instead:
    every verifying case below closes the decreasing obligation.
  * PARTIAL-DOMAIN — APPLIES and is the main attack surface; see the reject
    lane below.
  * UNGROUNDED-ORACLE ECHO — N/A (see above): the post-image is a total,
    fully-unfolded function of the single input binder.

AXIOM lane: the ``axioms`` region declares no ``axiom`` and the changed operation
is modeled DEEPLY as ``joinDot`` / ``replaceWindow`` (A-references validated ==
the real stdlib callees by G-AX, out of scope for this gate). ``AXIOM_TESTS`` is
dropped; the gate ignores it regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-6202"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl region: the ENTIRE `-- impl-start` .. `-- impl-end` block
# ---- (the descriptive comment + the backward-fold loop). It lies wholly inside
# ---- the one impl region and is unique in Solution.lean; both facts are asserted
# ---- at load by _swap. Each variant re-emits the `-- impl-start` /
# ---- `-- impl-end` markers so the region boundary is preserved exactly. -------
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    -- Build the dotted path by folding the parts from the back, prepending a\n"
    "    -- separator before each part after the first. The result is exactly the\n"
    "    -- separator-join of the parts, with no further transformation applied.\n"
    "    let mut result : List Char := parts[parts.length - 1]!\n"
    "    let mut i := parts.length - 1\n"
    "    while i > 0\n"
    "      invariant 1 ≤ i + 1 ∧ i ≤ parts.length - 1\n"
    "      invariant result = joinDot (parts.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let p := parts[i - 1]!\n"
    "      result := p ++ (sep :: result)\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)
assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- The frozen proof body (the `prove_correct` tactic script), tuned to the
# ---- frozen loop shape. Elided from the consumer spec view; the loop-free cases
# ---- retune the script, keeping the obligation STATEMENT and the
# ---- `prove_correct` header untouched so same_spec still holds. --------------
_GOLD_PROOF = (
    "prove_correct joinPath by\n"
    "  loom_solve\n"
    "  · rw [joinDot_drop_step parts i (by omega) (by omega)]\n"
    "    simp_all\n"
    "  · exact joinDot_drop_last parts (by omega)"
)
assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block.
    `body` is the text BETWEEN the markers; we wrap it back in the exact
    `-- impl-start` / `-- impl-end` markers so the region boundary is intact."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_BASE, _GOLD_IMPL, block)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    block = "    -- impl-start\n" + body.rstrip("\n") + "\n    -- impl-end"
    return _swap(_swap(_BASE, _GOLD_IMPL, block), _GOLD_PROOF, proof)


# ---------------------------------------------------------------------------
# THE WITNESS REFERENCE — the subject every reject witness is refuted against,
# in place of the frozen solution.
#
# WHY: the frozen impl keeps a backward `while` loop; under
# `loom.semantics.choice "demonic"` the loop's fixpoint elaborates through a
# classical choice term the kernel cannot unfold, so `decide` against the frozen
# tester is STUCK for every claim — true or false — and its exit code
# discriminates nothing. Measured directly (frozen-side build of a witness):
#
#     Tactic `decide` failed for proposition
#       joinPathTester [['a'], ['.', '[']] = false
#     because its `Decidable` instance ... did not reduce to `isTrue` or
#     `isFalse`. ... reduction got stuck at the `Decidable` instance
#
# Reading that exit code as a refutation would attest to a check never
# performed. So each reject case names this loop-FREE impl instead: it shares
# the frozen spec, it VERIFIES (the gate re-checks both before using it — an
# impl that failed everything would refute every witness), and its tester DOES
# reduce, so a failure against it is a real `decide` verdict. Verified
# out-of-band: every witness below fails against it with
# "Tactic `decide` proved that the proposition ... is false" and ZERO stuck-
# reduction lines. It is also shipped as `pos-direct`, so the battery records
# that loop-freeness is not what any rival is rejected for.
# ---------------------------------------------------------------------------
_REFERENCE = _impl_proof(
    "    return joinDot parts\n",
    "prove_correct joinPath by\n  loom_solve")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `joinPathTester parts = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete part-list (the tester
# ---- short-circuits to `true` when the `require` clause is false, so every
# ---- witness below uses a non-empty part-list that satisfies `parts.length ≥ 1`).
# ---- Checked in a file whose `prove_correct` block has been stripped, so no
# ---- tactic script can mask the verdict. `List Char` has DecidableEq, so the
# ---- postcondition is decidable and every witness closes by `decide` on literal
# ---- inputs — no `sorry`/`admit`/`native_decide`, and no hypothesis to be
# ---- inconsistent. Each rival is written loop-free so ITS side reduces too.
_TESTER = ("extract_program_for joinPath\n"
           "prove_precondition_decidable_for joinPath\n"
           "prove_postcondition_decidable_for joinPath\n"
           "derive_tester_for joinPath\n\n")


def _witness(point):
    return _TESTER + f"example : joinPathTester {point} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # (1) POSITIVE CONTROL — cheapest honest impl (soundness). Return the
    # grounded pure model `joinDot parts` directly, no loop. This is the
    # separator-join with no further transformation — the correct answer, not a
    # wrong echo (joinDot is a function of the input, not an opaque answer-key).
    # The postcondition `out = joinDot parts` is then definitionally the RHS, so
    # the retuned proof is just `loom_solve`. If a faithful correct impl could
    # NOT verify ⇒ SPEC-TOO-STRONG. This is the SAME source as `_REFERENCE`, so
    # this case is also the battery's own record that the witness subject
    # verifies. Verified out-of-band with a real build (EXIT 0).
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _REFERENCE,
        "rationale": "PASS SOURCE = the single clause `out = joinDot parts`. "
                     "Returning the grounded pure model directly makes the body "
                     "definitionally the postcondition RHS, so `loom_solve` "
                     "closes the byte-identical obligation. `joinDot` is a total "
                     "function of the input binder (not an opaque oracle), so "
                     "this cheapest impl IS the real separator-join — there is no "
                     "wrong echo. A faithful correct impl MUST verify, else the "
                     "postcondition over-constrains it (SPEC-TOO-STRONG). This "
                     "source is also the reject lane's `witness_reference`, so "
                     "the case doubles as the battery's own attestation that the "
                     "witness subject is a VERIFYING impl of this spec — i.e. "
                     "that loop-freeness is not what any rival is rejected for.",
    },

    # =====================================================================
    # (2) POSITIVE CONTROL — structurally different but CORRECT (soundness).
    # Same backward fold as gold with the accumulator renamed (result → acc) and
    # the loop guard rewritten `i ≥ 1` (equivalent to `i > 0`), keeping EVERY
    # gold invariant, the `done_with`/`decreasing` clauses, and the per-step
    # prepend verbatim. It computes the identical assembly on every part-list and
    # adds no new obligation, so the frozen proof (keyed on the preserved loop
    # variable `i` and input `parts`) still closes it unchanged. MUST verify,
    # else SPEC-TOO-STRONG on impl shape. Verified out-of-band (EXIT 0).
    # =====================================================================
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    let mut acc : List Char := parts[parts.length - 1]!\n"
            "    let mut i := parts.length - 1\n"
            "    while i ≥ 1\n"
            "      invariant 1 ≤ i + 1 ∧ i ≤ parts.length - 1\n"
            "      invariant acc = joinDot (parts.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let p := parts[i - 1]!\n"
            "      acc := p ++ (sep :: acc)\n"
            "      i := i - 1\n"
            "    return acc\n"),
        "rationale": "PASS SOURCE = the single clause `out = joinDot parts`. A "
                     "correct reshape with renamed accumulator (result→acc) and "
                     "guard `i ≥ 1` (equivalent to `i > 0`) that keeps the "
                     "backward direction, EVERY gold invariant and the "
                     "decreasing/done_with clauses computes the identical "
                     "assembly and adds no new obligation, so the equality clause "
                     "still discharges under the frozen proof (keyed on the "
                     "preserved loop variable `i` and input `parts`). Also "
                     "exercises the total-correctness pin: the reshaped loop still "
                     "closes the decreasing obligation. Else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # (3) ADMISSIBILITY — the `require parts.length ≥ 1` clause is over a
    # decidable, easily-satisfied predicate, so "a normal input satisfies the
    # precondition" is real but weak; the residual admissibility risk is that the
    # post-image is DEGENERATE at the decisive point (the sub-domain the fix
    # exists for). The impl loop is kept verbatim so the method's own obligation
    # still discharges under the frozen loop proof; an in-region `assert` pins the
    # post-image at that corner — a 2-part list whose second part itself contains
    # the two-code-point window a post-assembly rewrite would collapse —
    # demanding the assembly place ONE separator and PRESERVE that window
    # verbatim (`joinDot [['a'],['.','[']] = ['a','.','.','[']`, NOT collapsed).
    # The assert is live, not decoration: a false claim about the same point (a
    # collapsed window) leaves a type mismatch, verified out-of-band. The proof is
    # retuned only to discharge the extra decidable side goal `loom_solve` leaves.
    # =====================================================================
    {
        "id": "admiss-f2p-corner-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert "
            "(joinDot [['a'], ['.', '[']] = ['a', '.', '.', '[']))\n"
            "    -- Build the dotted path by folding the parts from the back, prepending a\n"
            "    -- separator before each part after the first. The result is exactly the\n"
            "    -- separator-join of the parts, with no further transformation applied.\n"
            "    let mut result : List Char := parts[parts.length - 1]!\n"
            "    let mut i := parts.length - 1\n"
            "    while i > 0\n"
            "      invariant 1 ≤ i + 1 ∧ i ≤ parts.length - 1\n"
            "      invariant result = joinDot (parts.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let p := parts[i - 1]!\n"
            "      result := p ++ (sep :: result)\n"
            "      i := i - 1\n"
            "    return result\n",
            "prove_correct joinPath by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | (rw [joinDot_drop_step parts i (by omega) (by omega)]; simp_all)\n"
            "    | exact joinDot_drop_last parts (by omega)"),
        "rationale": "PASS SOURCE = post-image satisfiable AND non-degenerate at "
                     "the decisive corner. The precondition admits a normal "
                     "multi-part input, and on a part that itself contains the "
                     "two-code-point window `['.','[']` the assembly must place "
                     "ONE separator and keep that window verbatim — "
                     "`joinDot [['a'],['.','[']] = ['a','.','.','[']`, not the "
                     "window collapsed. The in-region assert must discharge (else "
                     "the obligation is degenerate at the interesting point); the "
                     "loop impl is verbatim so the equality clause still "
                     "discharges too. Else PRECOND-TOO-STRONG / SPEC-degenerate.",
    },

    # =====================================================================
    # (3b) ADMISSIBILITY — the METHOD'S OWN OBLIGATION, discharged at the
    # concrete decisive input. The case above pins the pure post-image
    # (`joinDot` at that corner) but never discharges the method's contract
    # there, so on its own it does not rule out the residual
    # PRECOND-TOO-STRONG shape this lane exists for: the obligation being
    # UNSATISFIABLE at exactly the shape the failing test exercises. This case
    # closes that directly. It states the method's Hoare triple at the literal
    # 2-part input whose second part itself carries the two-code-point window a
    # post-assembly rewrite would collapse, and discharges it BY EVALUATION as a
    # `have` (`decide` on the reduced post-image), then closes the frozen
    # obligation verbatim with `loom_solve`. Both halves of admissibility are
    # therefore machine-checked in one case: `hpre` shows the `require` clause
    # actually admits that input, and `hadm` shows the contract is satisfiable
    # there with the window intact.
    #
    # LIVE, not decoration — three real builds:
    #   * as written                                        -> EXIT 0;
    #   * `hadm` restated at the COLLAPSED window
    #     (`['a','.','[']`, the pre-fix corruption)         -> EXIT 1,
    #     "`decide` proved that the proposition ... is false";
    #   * `hadm` restated with the separator also dropped
    #     (`['a','[']`)                                     -> EXIT 1, same shape.
    # So a false claim about this point does NOT close, which is what makes the
    # passing build evidence rather than ceremony.
    #
    # The impl is the loop-free `return joinDot parts` (the same source as
    # pos-direct / `_REFERENCE`) because a `triple` stated over the frozen
    # backward loop cannot be discharged at a literal input at all: measured,
    # the loop's `forIn Lean.Loop.mk` term leaves `failed to synthesize
    # Decidable (wp (do let r <- forIn Lean.Loop.mk ...))`. That is a carrier
    # limit on the loop's reducibility, not a property of the spec, and a
    # verifying loop-free impl of the SAME spec answers the admissibility
    # question just as well — the obligation it discharges is byte-identical.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-f2p-corner",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    return joinDot parts\n",
            "prove_correct joinPath by\n"
            "  -- The `require` clause genuinely ADMITS the decisive input.\n"
            "  have hpre : ([['a'], ['.', '[']] : List (List Char)).length ≥ 1 := by\n"
            "    decide\n"
            "  -- ...and the method's own obligation is SATISFIABLE there, with the\n"
            "  -- two-code-point window preserved verbatim and exactly one separator\n"
            "  -- placed: the contract is not degenerate at the shape that matters.\n"
            "  have hadm : triple True (joinPath [['a'], ['.', '[']])\n"
            "      (fun out => out = ['a', '.', '.', '[']) := by\n"
            "    simp only [joinPath, triple]\n"
            "    intro _\n"
            "    rw [wp_pure]\n"
            "    decide\n"
            "  loom_solve"),
        "rationale": "PASS SOURCE = the `require parts.length ≥ 1` clause AND the "
                     "obligation it guards, both discharged at the concrete "
                     "decisive input. `hpre` evaluates the precondition at that "
                     "literal 2-part list (so the domain restriction does not "
                     "exclude the shape the fix exists for — else "
                     "PRECOND-TOO-STRONG). `hadm` discharges the METHOD'S OWN "
                     "triple there by evaluation, demanding the assembly place "
                     "exactly ONE separator and keep the `['.','[']` window "
                     "verbatim (`['a','.','.','[']`) — so the contract is "
                     "satisfiable at that point and not degenerate on it. The "
                     "frozen obligation is then closed verbatim by `loom_solve`, "
                     "so nothing is weakened to buy the two `have`s. This is the "
                     "half the sibling admissibility case does not reach: that "
                     "one pins the pure post-image `joinDot` at the corner, this "
                     "one pins the CONTRACT at it.",
    },

    # =====================================================================
    # UNIQUENESS rivals (reject) — wrong impls sharing the frozen spec, each
    # loop-free (so its own witness side reduces) with a machine-checked
    # refutation witness SEEN to discriminate: EXIT 0 against the rival, and
    # against `_REFERENCE` a genuine `decide` verdict ("proved that the
    # proposition ... is false", zero stuck-reduction lines) rather than the
    # frozen impl's uninformative stuck build. Each attacks a distinct guarantee
    # of the single clause at a distinct part-list.
    # =====================================================================

    # (4) FIDELITY attack, BOUNDARY window — the literal PRE-PATCH behaviour:
    # assemble the dotted path, then apply the removed post-assembly window
    # rewrite that collapses the two-code-point sequence `['.','[']` into `['[']`.
    # Correct on any part-list whose assembly contains no such window; WRONG
    # whenever one appears — including, decisively, when it is MANUFACTURED by
    # the assembly itself (a part ending in `'.'` followed by a part starting
    # `'['`), which no per-part rewrite can see. Refuted at `[['a','.'],['[']]`,
    # whose assembly `['a','.','.','[']` contains a window this rival collapses.
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return replaceWindow (joinDot parts)"),
        "witness": _witness("[['a', '.'], ['[']]"),
        "witness_reference": _REFERENCE,
        "refinement": "This IS the faithful pre-patch shape: it re-applies the "
                      "exact post-assembly window rewrite the fix DELETES. Its "
                      "real-code counterpart is the base-commit behaviour, which "
                      "the failing test rejects — it asserts the presented path "
                      "keeps the two-code-point window verbatim, but the rewrite "
                      "collapses it, corrupting the path. So a verifying "
                      "weak-prepatch would be a true verify-but-does-not-resolve "
                      "break.",
        "rationale": "REJECT from `out = joinDot parts` (FIDELITY): the impl "
                     "returns `replaceWindow (joinDot parts)`, which differs from "
                     "`joinDot parts` exactly when the assembly contains a "
                     "`['.','[']` window. Refuted at `[['a','.'],['[']]`, where "
                     "the window straddles the part boundary: the assembly is "
                     "`['a','.','.','[']`, the rewrite collapses it to "
                     "`['a','.','[']`, so the postcondition equality fails. This "
                     "point is chosen over an intra-part window precisely because "
                     "it SEPARATES this rival from the weak-perpart near-miss "
                     "below, which AGREES with the spec at this very point "
                     "(re-measured: the same witness built against weak-perpart "
                     "exits 1, `decide` reporting the refutation false). The "
                     "separation is ONE-DIRECTIONAL and only that is claimed: "
                     "this rival is also wrong at weak-perpart's intra-part "
                     "point (re-measured, exit 0), because rewriting the "
                     "finished path collapses an intra-part window too. So this "
                     "point is what isolates THIS rival, and weak-perpart's "
                     "point is what only weak-perpart's own sub-domain reaches.",
    },

    # (5) FIDELITY attack, INTRA-PART window — the NEAR-MISS. Apply the window
    # rewrite to each part BEFORE assembling, instead of to the finished path.
    # It agrees with the spec over strictly MORE of the domain than
    # weak-prepatch: any window manufactured at a part boundary is invisible to
    # it, so it is correct at `[['a','.'],['[']]` (measured). Its own failing
    # sub-domain is a window lying wholly INSIDE one part, so it gets its own
    # discriminating point rather than sharing weak-prepatch's — otherwise its
    # rationale would claim a sub-domain the manifest never demonstrates.
    {
        "id": "weak-perpart",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return joinDot (parts.map replaceWindow)"),
        "witness": _witness("[['x'], ['.', '[', 'y']]"),
        "witness_reference": _REFERENCE,
        "refinement": "A subtler counterpart of the pre-patch behaviour: apply "
                      "the window rewrite per name part before assembly rather "
                      "than to the assembled path. Its faithful real patch still "
                      "fails the failing test, which pins a presented path whose "
                      "window sits INSIDE a single parametrised name part — that "
                      "part is rewritten and the path is corrupted exactly as "
                      "before. So a verifying weak-perpart would be a true "
                      "verify-but-does-not-resolve break.",
        "rationale": "REJECT from `out = joinDot parts` (FIDELITY, intra-part "
                     "sub-domain): the impl assembles rewritten parts, so it "
                     "diverges from `joinDot parts` whenever some part contains a "
                     "`['.','[']` window. Refuted at `[['x'],['.','[','y']]`: the "
                     "post-image demands `['x','.','.','[','y']` but the rival "
                     "returns `['x','.','[','y']`. NEAR-MISS, not a duplicate of "
                     "weak-prepatch: this rival is CORRECT at weak-prepatch's "
                     "boundary point `[['a','.'],['[']]` — re-measured, that "
                     "witness build against THIS rival exits 1 with ``decide`` "
                     "reporting the refutation FALSE, i.e. the tester returns "
                     "true and the postcondition HOLDS there. So this rival's "
                     "own point is not interchangeable with weak-prepatch's, "
                     "and the boundary witness does not catch it. The converse "
                     "does not hold and is not claimed: weak-prepatch also "
                     "violates the spec at THIS intra-part point (re-measured, "
                     "exit 0), because a rewrite of the finished path sees an "
                     "intra-part window too. The asymmetry is the near-miss: "
                     "this rival agrees with the spec on strictly MORE of the "
                     "domain (every boundary-manufactured window), which is "
                     "exactly why it needs its own witness rather than sharing "
                     "weak-prepatch's.",
    },

    # (5b) FIDELITY attack, FIRST-OCCURRENCE ONLY — the STRICTEST near-miss, and
    # the nagini sibling's own `weak-firsthit` re-derived on this carrier rather
    # than folded away. Assemble the dotted path, then collapse only the FIRST
    # two-code-point window in it, copying the remainder verbatim. It agrees with
    # the spec on strictly more of the domain than weak-prepatch (which collapses
    # every window) AND on a sub-domain weak-perpart gets wrong: it is correct at
    # weak-prepatch's boundary point too (measured, EXIT 1 with `decide`
    # reporting the refutation false), because there is only one window there and
    # collapsing it is the only difference either rival makes. Its own failing
    # sub-domain therefore needs a part-list carrying TWO windows, where the
    # first is collapsed and the second survives — a binder value no other case
    # in the battery reaches. Written loop-free so its own witness side reduces;
    # the `find?`-based first-hit scan was tried first and is NOT usable here
    # (Velvet's WP generator cannot process the `match` on the search result:
    # "Failed to parse an assertion without names"), so the scan is expressed as
    # a `filter`/`headD` index lookup instead, which elaborates.
    {
        "id": "weak-firsthit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl_proof(
            "    let s := joinDot parts\n"
            "    let hits := (List.range s.length).filter (fun j =>\n"
            "      s[j]? = some '.' && s[j+1]? = some '[')\n"
            "    let j := hits.headD s.length\n"
            "    return (s.take j) ++ (if j < s.length then '[' :: s.drop (j + 2) else [])\n",
            "prove_correct joinPath by\n  loom_solve"),
        "witness": _witness("[['q', '.', '['], ['.', '[']]"),
        "witness_reference": _REFERENCE,
        "refinement": "The subtlest counterpart of the pre-patch behaviour: "
                      "collapse only the FIRST such window in the assembled "
                      "path, leaving later ones intact. Its faithful real patch "
                      "still fails the failing test, which pins a presented path "
                      "whose window is the first one in it — that window is "
                      "collapsed and the path is corrupted exactly as before. So "
                      "a verifying weak-firsthit would be a true "
                      "verify-but-does-not-resolve break.",
        "rationale": "REJECT from `out = joinDot parts` (FIDELITY, first-hit "
                     "sub-domain): the impl returns the assembly with its first "
                     "`['.','[']` window collapsed, so it diverges from "
                     "`joinDot parts` whenever the assembly contains at least "
                     "one. Refuted at `[['q','.','['],['.','[']]`, whose "
                     "assembly `['q','.','[','.','.','[']` carries TWO windows: "
                     "the rival collapses the first and keeps the second, so its "
                     "result is one code point short of the post-image. STRICTEST "
                     "near-miss in the battery, and measured to be one: it is "
                     "CORRECT at weak-prepatch's boundary point (exit 1, `decide` "
                     "reports the refutation false), so neither weak-prepatch's "
                     "nor weak-perpart's witness catches it, and this two-window "
                     "point is reached by no other case. It is the nagini "
                     "sibling's `weak-firsthit`, landed rather than merged away.",
    },

    # (6) SEPARATION attack — drop the separator entirely: return the bare
    # concatenation of the parts. Coincides with gold only on a single-part list;
    # WRONG for any multi-part input (it omits the separators). Refuted at
    # `[['a'],['b']]`, a 2-part list where the sole separator is dropped — no
    # other rival diverges here (all the others preserve separation), so this
    # witness is distinct, and it moves the binder to separator-free parts.
    {
        "id": "weak-nosep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return parts.flatten"),
        "witness": _witness("[['a'], ['b']]"),
        "witness_reference": _REFERENCE,
        "refinement": "Assembling the parts with NO separator (bare "
                      "concatenation) is a plausible but wrong 'join'. Its "
                      "faithful real patch fails the PASS-line assertions of the "
                      "failing test too: a two-part collected node's path must "
                      "read as the two names separated by one separator, but bare "
                      "concatenation runs them together. A verifying weak-nosep "
                      "would be a verify-but-does-not-resolve break.",
        "rationale": "REJECT from `out = joinDot parts` (SEPARATION): joinDot "
                     "inserts one separator between consecutive parts; the bare "
                     "concatenation omits it, so for any multi-part input the "
                     "result is shorter by (parts.length − 1) separators. Refuted "
                     "at `[['a'],['b']]`: the impl returns `['a','b']` but the "
                     "post-image demands `['a','.','b']`.",
    },

    # (7) ORDER attack — assemble the parts in REVERSE order (still one separator
    # between consecutive parts, so SEPARATION and FIDELITY are intact).
    # Coincides with gold only on a palindromic part-list; WRONG whenever order
    # matters. Refuted at `[['a'],['b'],['c']]`, a 3-part list — a length no
    # other rival probes, so the binder's length axis is varied and no
    # part-count is pinned across the battery.
    {
        "id": "weak-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return joinDot parts.reverse"),
        "witness": _witness("[['a'], ['b'], ['c']]"),
        "witness_reference": _REFERENCE,
        "refinement": "Assembling the parts in the wrong ORDER yields a "
                      "different dotted path for any non-palindromic node. Its "
                      "faithful real patch fails the failing test's PASS-line "
                      "assertions, which pin the exact ordered path of each "
                      "collected node (outer-to-inner). A verifying weak-reverse "
                      "would be a verify-but-does-not-resolve break.",
        "rationale": "REJECT from `out = joinDot parts` (ORDER): the impl "
                     "assembles `parts.reverse`, so on any list whose reversal "
                     "differs from itself the result diverges from `joinDot "
                     "parts`. Refuted at `[['a'],['b'],['c']]`: the impl returns "
                     "`['c','.','b','.','a']` but the post-image demands "
                     "`['a','.','b','.','c']`.",
    },

    # (8) TOTALITY attack at the PRECONDITION BOUNDARY — assemble only the parts
    # before the last one, dropping the final part. This is the rival the rest of
    # the battery would MISS: it is a truncation, so it preserves separation,
    # fidelity and order on everything it does emit, and at the degenerate
    # one-part list `parts.length = 1` — the exact boundary the `require` clause
    # admits — it returns the empty path where the spec demands the part itself.
    # Refuted at `[['a']]`, the battery's ONLY one-part probe: without it, a
    # rival wrong only at the precondition boundary would verify unnoticed and
    # the manifest would never demonstrate that the clause constrains that point.
    {
        "id": "weak-droplast",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("    return joinDot (parts.take (parts.length - 1))"),
        "witness": _witness("[['a']]"),
        "witness_reference": _REFERENCE,
        "refinement": "Dropping the innermost name part is a plausible "
                      "off-by-one in the accumulation bound. Its faithful real "
                      "patch fails the failing test outright: every asserted "
                      "path there ends in the innermost collected name, so a "
                      "truncated path matches none of them — and for a "
                      "single-part node it presents an empty path. A verifying "
                      "weak-droplast would be a verify-but-does-not-resolve "
                      "break.",
        "rationale": "REJECT from `out = joinDot parts` (TOTALITY): the impl "
                     "assembles `parts.take (parts.length − 1)`, omitting the "
                     "final part, so it diverges from `joinDot parts` on EVERY "
                     "admissible input. Refuted at the precondition's own "
                     "boundary `[['a']]` (parts.length = 1), where the post-image "
                     "demands `['a']` but the rival returns `[]`. This is the "
                     "only one-part witness in the battery, so it is what makes "
                     "the manifest demonstrate that the clause constrains the "
                     "degenerate end of the domain rather than only its "
                     "multi-part interior.",
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case          -> here
#   -----------------------------------------------------------------------
#   pos-direct            -> pos-direct                            PORTED
#   pos-reshape           -> pos-reshape                           PORTED
#   admiss-f2p            -> admiss-f2p-corner-nondegenerate       RE-AIMED
#                          + admiss-obligation-satisfiable-at-f2p-corner
#                                                                  PORTED (audit)
#   weak-prepatch         -> weak-prepatch                         PORTED
#   weak-firsthit         -> weak-firsthit                         PORTED (audit)
#                          (+ weak-perpart, kept: a DISTINCT sub-domain)
#   weak-nosep            -> weak-nosep                            PORTED
#   weak-nonterm          -> (none)                     REJECTED-BY-SPEC,
#                                                       UNWITNESSABLE (measured)
#   (frame-mutation)      -> (none)                                VACUOUS
#   + weak-reverse        (added, ORDER-clause coverage)
#   + weak-droplast       (added, TOTALITY + 1-part binder coverage)
#
# 10 velvet cases: 4 verify (2 soundness + 2 admissibility) and 6 reject.
#
# PORTED (pos-direct / pos-reshape): the nagini positives — the cheapest honest
#   impl (`return join_dot(parts)`) and the accumulator-rename/guard-reshape —
#   port directly. `join_dot` is grounded, so the cheapest impl is the real
#   assembly, not a wrong echo. Both verified out-of-band with real builds
#   (EXIT 0).
# RE-AIMED (admissibility): the nagini admiss-f2p asserts the postcondition holds
#   of a 2-part F2P-shaped witness downstream of the gold loop. Here the same
#   idea is expressed as an in-region `assert` pinning the post-image at the
#   decisive corner (a part containing the two-code-point window that a
#   post-assembly rewrite would collapse), demanding the window survive verbatim.
#   The assert is load-bearing: a false (collapsed-window) claim fails to build
#   (verified out-of-band). The precondition-admits-a-normal-input half is
#   subsumed (the F2P witness satisfies `parts.length ≥ 1`).
# PORTED (weak-prepatch / weak-nosep): the nagini partial-domain rivals. The full
#   post-assembly rewrite ports as `return replaceWindow (joinDot parts)` (the
#   pure model of the removed substitution is already present in the frozen pure
#   region as `replaceWindow`); the drop-separator rival ports as
#   `return parts.flatten`.
# PORTED (weak-firsthit): nagini's "collapse only the FIRST occurrence" rival is
#   a NEAR-MISS of weak-prepatch — same clause, strictly more agreement with
#   gold. An earlier port recorded it as inexpressible on this carrier ("would
#   need an index-recursive scan whose witness reduction is awkward") and merged
#   it into weak-perpart. That is FALSE and has been corrected: the first-hit
#   scan expresses cleanly as an index `filter` over `List.range s.length` plus
#   `headD`, which elaborates and is rejected on the postcondition goal, and
#   whose witness reduces under `decide`. It is shipped as its own case with its
#   own two-window point, because it is the STRICTEST near-miss in the family:
#   measured, it is CORRECT at weak-prepatch's boundary point AND at
#   weak-perpart's intra-part point, so only a point bearing TWO collapsible
#   windows separates it from gold. weak-perpart is KEPT alongside it: the two
#   rivals partition the fidelity clause differently (per-part scope vs
#   first-occurrence-only), and each has a point at which the other is correct.
# REJECTED-BY-SPEC, UNWITNESSABLE (weak-nonterm): nagini's reachable-
#   nontermination rival. NOT written off as "referential transparency collapses
#   the class". Re-measured for this audit rather than cited: the velvet corpus
#   is `loom.semantics.termination` = `{'total': 500}` — the `partial` population
#   that makes divergence a spec hole elsewhere is EMPTY, so no cross-bundle
#   statistic is load-bearing here. What was actually built: four diverging
#   routes against this frozen spec, all REJECTED, with the goals the build
#   emitted — an unmeasured `while` (`Decreasing annotations are required in
#   total correctness semantics`), an increasing measure (`⊢ k + 1 < k`), and two
#   unreachable-exit loops carrying a constant measure (`⊢ 0 < 0`, unsolved).
#   That last pair matters: the corpus-level `decreasingGadget` weakness (a
#   recorded measure that is never re-checked at the exit) does NOT reproduce on
#   this bundle — the obligation is emitted and it fails. So the class is closed
#   by the frozen spec, measured on this carrier.
#   No reject case is shipped anyway, and the reason is also measured, not
#   assumed: a diverging rival fails the `decreasing` OBLIGATION rather than the
#   postcondition, so the witness contract cannot be met — the tester extracted
#   from a rival that does not elaborate has nothing to `decide`, and the build
#   returns `witness-unproven` rather than a refutation. A reject case whose
#   witness has never been SEEN to discriminate is exactly what must not ship.
#   The pin is attested positively instead: every verifying case closes the
#   decreasing obligation.
# VACUOUS (frame-mutation): the nagini sibling itself records this class as N/A
#   (`parts` is an immutable mathematical value with no heap permission). On this
#   backend the same holds structurally: referential transparency, no `mut`
#   binder, no heap or aliasing — no read-only input to overwrite and no
#   discriminating witness could exist. Not fabricated.
# ADDED (weak-reverse, weak-droplast): no nagini counterpart. The nagini battery
#   attacks FIDELITY and SEPARATION but leaves ORDER and TOTALITY unattacked, and
#   every nagini witness is a multi-part list. weak-reverse attacks ORDER at a
#   3-part list; weak-droplast attacks TOTALITY at the one-part precondition
#   boundary — the binder value no other witness in either battery probes, and
#   the shape a truncation rival would otherwise slip through.
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py); this
#   bundle declares no `axiom` (the changed op is modeled deeply as
#   `joinDot`/`replaceWindow`, A-references), and the gate ignores AXIOM_TESTS
#   regardless.
#
# CLAUSE / BINDER COVERAGE. Binder `parts` (the sole binder): six distinct
#   witness points — `[['a','.'],['[']]` (2 parts, boundary window),
#   `[['x'],['.','[','y']]` (2 parts, intra-part window),
#   `[['q','.','['],['.','[']]` (2 parts, TWO collapsible windows — one intra-part
#   and one at the boundary, the only point that separates the first-hit rival),
#   `[['a'],['b']]` (2 parts, separator-free), `[['a'],['b'],['c']]` (3 parts) and
#   `[['a']]` (1 part, precondition boundary) — so pts=6 across part-counts 1/2/3
#   and both window-bearing and window-free content, with window MULTIPLICITY
#   varied as well; no binder value is pinned. The single
#   top-level clause `out = joinDot parts` is attacked along all four independent
#   guarantees (fidelity ×3 nested sub-domains — whole-path, per-part,
#   first-occurrence-only — separation, order, totality); the positives defend it
#   directly, at the decisive corner, and as a satisfiable triple at that corner,
#   and every positive exercises the total-correctness pin.
#
# WITNESS SUBJECT. Every reject case names `witness_reference = _REFERENCE`
#   rather than relying on the frozen solution, because the frozen `while` loop
#   under demonic choice makes `decide` STUCK for every claim (see the
#   `_REFERENCE` comment for the verbatim error). Out-of-band, each of the six
#   witnesses was SEEN to discriminate: EXIT 0 against its rival, and against
#   `_REFERENCE` a genuine `decide` verdict ("proved that the proposition ... is
#   false") with ZERO stuck-reduction lines. The substitution is NECESSARY, not
#   evasive, and that was measured both ways: with the witness claim FLIPPED
#   (`= true`), `_REFERENCE` builds EXIT 0 — the exit code tracks the claim, so
#   the discrimination is real — while the same flipped witness against the
#   frozen solution stays EXIT 1 with byte-identical stuck-reduction output,
#   carrying no information either way. `_REFERENCE` itself verifies (EXIT 0) and
#   is shipped as `pos-direct`.
AXIOM_TESTS = []
