"""properties.py — G-PBT falsification battery for sympy__sympy-17139 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct powerRewriteStep`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method — one rewrite step on a candidate power):

  powerRewriteStep (rv : Expr) (exp : Cexp) (matchesPow : Bool)
      (transformed : Expr) return (out : Expr)
    ensures out = (if matchesPow then
                     (if expIsReal exp then transformed else rv) else rv)  -- (E) master
    ensures (matchesPow ∧ ¬ expIsReal exp) → out = rv          -- (C1) non-comparable guard
    ensures (matchesPow ∧ expIsReal exp)  → out = transformed  -- (C2) real ⇒ rewrite
    ensures ¬ matchesPow → out = rv                            -- (C3) not-targeted ⇒ unchanged

  ``expIsReal exp = (exp.im == 0)``: the exponent is real exactly when it has no
  imaginary component. The load-bearing decision the spec pins is C1: a targeted
  power whose exponent is NOT a real number is returned UNCHANGED (it cannot be
  compared by magnitude, so no rewrite is attempted) rather than being handed to
  the downstream rewrite. That middle clause — the whole content of the modeled
  change — is the discriminator every reject rival is built around.

CARRIER NARROWING — why this port is much thinner than the nagini sibling.

  The nagini model contracts the ENTIRE ``_f`` rewrite step: the magnitude
  dispatch (==1/==2/==4), the parity rule under ``pow=False``, the perfect-power
  rule under ``pow=True``, the order-of-magnitude short-circuits, and the
  non-real guard — via a branch-tag return (0/1/2) and three axiomatized callees
  (``order_lt_zero`` / ``order_gt_max`` / ``is_perfect_power``). This velvet
  bundle models ONLY the guard structure the patch touches: whether the node is a
  targeted power (``matchesPow``, a FREE Bool, the unchanged first guard), whether
  the exponent is real (``expIsReal``, the NEW guard — the actual change), and the
  value the downstream rewrite would produce (``transformed``, a FREE ``Expr``).
  The whole magnitude/parity/perfect-power ladder is folded into the free
  ``transformed`` (mapping.md §1, directive 7: unchanged sub-steps are modeled as
  strictly-weaker free values). So every nagini case attached to that ladder —
  the historical D1 odd/even parity defect, the squared-boundary case, the
  ignore-pow rival, the over-max short-circuit, the perfect-power dispatch — has
  NO counterpart on this carrier: those behaviours are not modeled here at all,
  and fabricating rivals for them would attack a surface this bundle does not
  contract. This is carrier narrowing, not an omission gap (per the porting map:
  most nagini cases attached to an unmodeled behaviour have no counterpart).

THE CARRIER IS FULLY TRANSPARENT. ``Expr`` is an identity-only ``structure`` with
``DecidableEq``, ``Cexp`` is a pair of ``Int`` with ``DecidableEq``, and
``expIsReal`` computes. So a witness reaches the impl through Velvet's own tester
machinery (``extract_program_for powerRewriteStep`` → ``derive_tester_for`` →
``powerRewriteStepTester rv exp matchesPow transformed = false := by decide``):
the extracted program is checked against the method's postcondition at ONE
concrete input, and ``decide`` closes the residual literal. No opaque leaf, no
carrier conditioning, so NO witness binds a hypothesis and there is no
joint-satisfiability obligation. Each reject rival is a straight-line closed form
whose extracted program reduces under ``decide`` to the rival's return, while
gold's nested-guard program reduces to a DIFFERENT value at the same input — so
the same witness ELABORATES against the rival and FAILS (``decide`` proves the
tester is ``true``) against the frozen solution, the discrimination the gate
requires. Both halves (rival exit 0, gold exit ≠ 0) plus the full-rival
non-verification were checked out-of-band with ``scripts/lean_verify.sh`` for
every reject case during authoring.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION (nagini frame-write-value, frame-write-real,
    MANDATORY there) — VACUOUS. Nagini holds ``exp`` at ``Acc(...,1/2)`` and a
    store into ``exp.value`` / ``exp.real`` needs full permission, so an
    in-place-write rival is rejected for INSUFFICIENT PERMISSION. Velvet is
    referentially transparent: ``rv`` / ``exp`` / ``matchesPow`` / ``transformed``
    are immutable values, this bundle declares NO ``mut`` binder over any input,
    and there is no heap and no aliasing — so there is no read-only input to
    overwrite and no permission system to trip. Not fabricated (per the porting
    map, dropped rather than replaced).
  * DIVERGENCE / NON-TERMINATION: the sibling ships no divergence case, and the
    class is CLOSED BY THE SEMANTICS here. It is NOT a spec hole, and two earlier
    revisions of this bullet said otherwise, each on its own false premise. The
    first said this bundle runs under ``termination "partial"``: the frozen
    solution sets ``loom.semantics.termination "total"``, as do all 500 velvet
    bundles, and the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness`` (``Loom/MonadAlgebras/WP/Options.lean:169-186``)
    so the option and the ``open`` cannot drift apart. The second, which is the
    consequential one, said ``"total"`` does NOT close the class because the
    ``decreasing`` annotation is required but never DISCHARGED, so a rival could
    supply a bogus measure and be admitted. Both halves of that were rebuilt
    against the real verifier and NEITHER reproduces:
      - A loop with NO ``decreasing`` clause is rejected, with
        ``error: Decreasing annotations are required in total correctness
        semantics``. This half was always right.
      - A loop that DOES carry an annotation is rejected too, on the descent goal
        itself. The earlier revision named its shape exactly, so it was rebuilt
        exactly: ``let mut k : Nat := 1; while k > 0 invariant k > 0
        done_with k = 0 decreasing k do k := k + 1``, a measure that strictly
        INCREASES every iteration, spliced at the impl anchor with the proof
        reduced to a bare ``loom_solve``. It exits 1 with ``unsolved goals``,
        ``case «decreasing_1: k»``, residual ``⊢ k + 1 < k``. A constant measure
        fares no better: ``decreasing (0 : Nat)`` gives
        ``case «decreasing_1: (0 : Nat)»``, residual ``⊢ 0 < 0``. The earlier
        revision recorded both as exit 0, "reproduced twice"; that measurement is
        withdrawn.
    So a diverging rival does NOT satisfy this spec, in either shape, and nothing
    is escalated. The mechanism is in Loom rather than in a tactic:
    ``TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop``
    (``Loom/MonadAlgebras/NonDetT/Basic.lean:544``) takes ``measure : β -> Nat``
    and emits ``with_name_prefix `decreasing (measure b' < measure b)``, while only
    the ``PartialCorrectness`` twin (same file, :211) takes an ``Option ℕ`` and
    DISCARDS it. Under ``total`` a postcondition is claimed of ALL runs, so the
    measure is both demanded and proven. The class still does not SHIP as a reject
    case, for a mechanical reason and not a spec one: the rejection lands on the
    ``method`` command, so the rival's module does not compile and the witness the
    gate builds from it cannot elaborate, which records ``witness-unproven``, an
    INCONCLUSIVE outcome that forces MALFORMED-TESTS. That is a property of the
    witness contract, not a weakness of the spec and not an underported class.
  * PARTIAL-DOMAIN over the magnitude/parity/perfect-power ladder (nagini
    partial-odd-rewrite, partial-even-unchanged, partial-ignore-pow,
    partial-squared-as-general, over-max-rewrite) — NO COUNTERPART. That whole
    ladder is folded into the free ``transformed`` here (see CARRIER NARROWING),
    so this bundle does not contract any of those sub-cases and there is no clause
    to attack. Dropped as carrier narrowing, not as effort.
  * CONTROL-FLOW / GUARD-PLACEMENT (nagini drop-nonreal-guard,
    guard-after-ordering) — PORTED as the heart of this bundle. The modeled change
    IS the non-real guard, so both the "guard dropped" and the "guard mis-placed"
    rivals collapse onto the SAME modeled defect: a rewrite applied to a targeted
    power with a non-real exponent (C1 violated). Ported as R-drop-nonreal-guard.
    On this carrier the ordering-precondition machinery nagini's guard-after case
    exploited (``order_lt_zero``'s ``Requires(e.real)``) is not modeled — the
    downstream is the free ``transformed`` — so guard-placement is
    behaviourally identical to guard-absence here and the two nagini cases are the
    one rival R-drop-nonreal-guard. Two more rivals (R-ignore-matchesPow,
    R-invert-realness) attack the remaining clauses C3 and C2.
  * SOUNDNESS positive controls (nagini pos-reordered) — PORTED, plus a grounded
    positive materialising the master clause directly.
  * ADMISSIBILITY (nagini admiss-gold) — PORTED as A-admiss-f2p-shaped. ADDED BY
    AUDIT (wave a7). This file previously argued the lane away: "the method
    declares NO ``require`` clause, so there is no precondition to be
    PRECOND-TOO-STRONG and no separate admissibility probe to build". That reason
    is not sufficient. The analogue of PRECOND-TOO-STRONG on a total carrier with
    no ``require`` is the OBLIGATION being unsatisfiable, or degenerate, at
    exactly an F2P-shaped input, which a positive that discharges the obligation
    at that concrete input — by evaluation, as an in-region assert, before closing
    the frozen obligation verbatim — tests directly. It was expressible here and
    is now shipped: A-admiss-f2p-shaped evaluates the guard's separation of the
    two exponent shapes and the master clause's two distinct images at a targeted
    power, then closes the frozen obligation against the byte-identical frozen
    impl. Verified with a real build (exit 0), and the assert is live (a falsified
    conjunct fails the file), so it is not a decorative positive.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries four
axiom-soundness / containment probes over the real ``Expr.__lt__`` / ``__gt__``
/ ``perfect_power`` callees; that is G-AX's job and this bundle has NO consumed
axiom and NO deep-model reference (mapping.md §3: the two unchanged sub-steps are
free values), so there is nothing for G-AX to check and the G-PBT gate ignores
AXIOM_TESTS regardless.

WITNESS PLACEMENT / coverage. The method has FOUR input binders — ``rv``,
``exp``, ``matchesPow``, ``transformed``. The four reject witnesses probe FOUR
distinct input points (pts=4) and vary every binder that drives the dispatch:
  * ``matchesPow`` — true (R-drop-nonreal-guard, R-invert-realness,
    R-nonpositive-im-as-real) and false (R-ignore-matchesPow): both verdicts of
    the first guard.
  * ``expIsReal exp`` (via ``exp.im``) — non-real at a POSITIVE imaginary part
    ``im=1`` (R-drop-nonreal-guard), non-real at a NEGATIVE imaginary part
    ``im=-1`` (R-nonpositive-im-as-real), and real ``im=0``
    (R-ignore-matchesPow, R-invert-realness): both verdicts of the NEW guard, and
    both SIGNS of the non-real verdict. The negative-imaginary point is what
    separates the guard "imaginary component is zero" from the weaker "imaginary
    component is not positive"; it was added by audit a7, which found that every
    previously-shipped witness sat at ``im ≥ 0`` and so left that half of C1's
    domain unprobed.
  * ``rv`` and ``transformed`` — distinct ``Expr`` values in every witness
    (⟨0⟩/⟨1⟩, ⟨2⟩/⟨3⟩, ⟨4⟩/⟨5⟩, ⟨6⟩/⟨7⟩) so ``out = rv`` vs
    ``out = transformed`` is a real observation, never trivially equal.
Clause coverage: C1 (matchesPow ∧ ¬real ⇒ rv) attacked by R-drop-nonreal-guard
at ``im=1`` and by R-nonpositive-im-as-real at ``im=-1``; C2 (matchesPow ∧ real
⇒ transformed) attacked by R-invert-realness; C3 (¬matchesPow ⇒ rv) attacked by
R-ignore-matchesPow; the master clause E is attacked by all four, defended by
both soundness positives, and shown satisfiable-and-non-degenerate at an
F2P-shaped input by A-admiss-f2p-shaped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-17139"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside a region the spec view elides (the impl body
# between -- impl-start / -- impl-end, or the prove_correct tactic body) and is
# unique in Solution.lean; both facts are asserted at load by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct powerRewriteStep
# statement byte-identical.
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (text strictly between -- impl-start
# and -- impl-end). Every variant replaces it wholesale.
_IMPL = (
    "    -- impl-start\n"
    "    -- Guard 1 (unchanged): not a targeted power -> leave it untouched.\n"
    "    if !matchesPow then\n"
    "      return rv\n"
    "    else\n"
    "      -- Guard 2: a non-real exponent is not comparable by magnitude, so the\n"
    "      -- expression is returned unchanged rather than rewritten.\n"
    "      if !expIsReal exp then\n"
    "        return rv\n"
    "      else\n"
    "        -- Real, targeted power: proceed to the downstream rewrite.\n"
    "        return transformed\n"
    "    -- impl-end"
)

assert _IMPL in _BASE, "frozen impl region drifted; update _IMPL"


def _rival(body: str) -> str:
    """Solution.lean whose impl body is a single closed form. The frozen
    prove_correct block is kept as-is (it will fail to close the reshaped impl —
    the intended rejection; the witness, not the tactic failure, is scored)."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _positive(body: str) -> str:
    """A correct-impl positive; the frozen `prove_correct ... loom_solve` closes
    each of these straight-line reshapes, so no proof retune is needed."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


# The frozen proof block, and the same block with one extra tactic to clear the
# additional goal an in-region `assert` leaves. `variant_scope` elides the
# tactic BODY from the spec view (only the `prove_correct <name>` header must
# survive byte-identical), so retuning the body is in scope; the four `ensures`
# clauses and the header are untouched.
_PROVE = "prove_correct powerRewriteStep by\n  loom_solve\n"

assert _PROVE in _BASE, "frozen prove_correct block drifted; update _PROVE"


def _positive_reproved(body: str, proof: str) -> str:
    """A positive that adds an in-region `assert`, which leaves one extra goal
    the frozen one-line `loom_solve` does not clear, so the proof body is
    retuned. Both edited spans lie inside regions the spec view elides."""
    return _swap(_swap(_BASE, _IMPL,
                       "    -- impl-start\n" + body + "\n    -- impl-end"),
                 _PROVE, proof)


# ---- witness preamble + body. The spec is a `method` CONTRACT over a fully
# ---- transparent carrier, so a witness reaches it through Velvet's tester
# ---- machinery: `powerRewriteStepTester rv exp matchesPow transformed = false`
# ---- says the extracted program's result violates the method's postcondition at
# ---- that concrete input. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can mask the verdict. The closed-form rival's
# ---- extracted program reduces under `decide` to the rival's return; gold's
# ---- nested-guard program reduces to a DIFFERENT value at the same input, so the
# ---- same witness FAILS on gold — the required discrimination. No binder, so no
# ---- consistency probe is needed.
def _witness(inp: str) -> str:
    return (
        "extract_program_for powerRewriteStep\n"
        "prove_precondition_decidable_for powerRewriteStep\n"
        "prove_postcondition_decidable_for powerRewriteStep\n"
        "derive_tester_for powerRewriteStep\n\n"
        f"example : powerRewriteStepTester {inp} = false := by decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify (else SPEC-TOO-STRONG). The frozen body tests the
    # guards with NEGATED conditions (`!matchesPow` / `!expIsReal`); this reshape
    # tests the POSITIVE conditions and swaps the branch arms accordingly. The
    # control flow is behaviourally identical on every input, so the frozen
    # `prove_correct powerRewriteStep by loom_solve` still closes with no retune.
    # =====================================================================
    {
        "id": "S-pos-reordered",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(
            "    if matchesPow then\n"
            "      if expIsReal exp then\n"
            "        return transformed\n"
            "      else\n"
            "        return rv\n"
            "    else\n"
            "      return rv"),
        "rationale": "reshapes the two guards to test the POSITIVE conditions "
                     "(matchesPow / expIsReal) with swapped arms instead of the "
                     "frozen negated form; behaviourally identical on every input, "
                     "so E and C1/C2/C3 all hold and the frozen `loom_solve` proof "
                     "closes unchanged. A correct reshape that failed to verify "
                     "would mean the spec is over-fit to the guard POLARITY => "
                     "SPEC-TOO-STRONG. Defends the whole obligation along a "
                     "distinct control-flow shape.",
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness, cheapest honest impl) — MATERIALISE the
    # master clause directly. The postcondition E equates `out` to a pure
    # expression GROUNDED in the inputs (`if matchesPow then (if expIsReal exp
    # then transformed else rv) else rv`), so returning that expression is the
    # correct computation, not an ungrounded-oracle echo. The impl is loop-free
    # and straight-line, so the frozen `loom_solve` proof closes with no retune.
    # MUST verify, else the spec rejects its own grounded model => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "S-pos-grounded",
        "kind": "soundness",
        "expect": "verify",
        "module": _positive(
            "    return (if matchesPow then "
            "(if expIsReal exp then transformed else rv) else rv)"),
        "rationale": "returns the master clause's grounded expression directly; "
                     "since E is grounded in the actual inputs (a total function "
                     "of matchesPow/expIsReal/rv/transformed, not an opaque "
                     "answer-key), materialising it is the honest cheapest correct "
                     "impl. A structurally-different (single-expression) correct "
                     "impl that MUST verify; failing would be SPEC-TOO-STRONG. "
                     "Also shows the spec is not echo-vulnerable — any wrong "
                     "constant would fail E.",
    },

    # =====================================================================
    # ADMISSIBILITY — added by audit (wave a7). The method declares no `require`
    # clause, but "no precondition" is NOT a reason to skip this lane: the
    # analogue on a total carrier is the OBLIGATION being unsatisfiable, or
    # degenerate, at exactly an F2P-shaped input. That is what this case tests
    # directly. The impl is kept BYTE-IDENTICAL to the frozen body (so the
    # method's own four `ensures` still discharge against the real impl) and an
    # in-region `assert` additionally discharges, BY EVALUATION at concrete
    # literals, the two facts the modeled behaviour turns on:
    #   (a) the guard predicate genuinely SEPARATES the two exponent shapes —
    #       `expIsReal ⟨0,1⟩ = false` (a nonzero imaginary component is not real)
    #       and `expIsReal ⟨0,0⟩ = true`; and
    #   (b) the master clause E's image at the F2P-shaped point is NON-DEGENERATE
    #       and lands on the two DISTINCT values — at a targeted power with a
    #       non-real exponent it is `rv`, and at one with a real exponent it is
    #       `transformed`, evaluated over distinct literals ⟨0⟩/⟨1⟩ so the two
    #       outcomes cannot be the same value.
    # Together those say the obligation is satisfiable at the F2P-shaped input
    # AND does not collapse to a constant there. The assert is LIVE: replacing
    # the (a)-clause's expected `⟨0⟩` with `⟨1⟩` leaves the file failing with
    # `Tactic decide proved that the proposition ... is false` (checked with a
    # real build during the audit), so this positive cannot pass on a vacuous
    # assert. If the obligation were unsatisfiable or degenerate at this point
    # => PRECOND-TOO-STRONG / degenerate-postcondition.
    # =====================================================================
    {
        "id": "A-admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _positive_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      (expIsReal ⟨0, 1⟩ = false ∧\n"
            "       expIsReal ⟨0, 0⟩ = true ∧\n"
            "       (if true then (if expIsReal ⟨0, 1⟩ then (⟨1⟩ : Expr) "
            "else (⟨0⟩ : Expr)) else ⟨0⟩) = ⟨0⟩ ∧\n"
            "       (if true then (if expIsReal ⟨0, 0⟩ then (⟨1⟩ : Expr) "
            "else (⟨0⟩ : Expr)) else ⟨0⟩) = ⟨1⟩))\n"
            "    if !matchesPow then\n"
            "      return rv\n"
            "    else\n"
            "      if !expIsReal exp then\n"
            "        return rv\n"
            "      else\n"
            "        return transformed",
            "prove_correct powerRewriteStep by\n"
            "  loom_solve\n"
            "  all_goals decide\n"),
        "rationale": "ADMISSIBILITY on a carrier with no `require`: the analogue "
                     "of PRECOND-TOO-STRONG here is the obligation being "
                     "unsatisfiable or degenerate at an F2P-shaped input, so this "
                     "case discharges it BY EVALUATION at that input before "
                     "closing the frozen obligation verbatim. The assert proves "
                     "the guard predicate separates the two exponent shapes "
                     "(expIsReal ⟨0,1⟩ = false, expIsReal ⟨0,0⟩ = true) AND that "
                     "the master clause's image at a targeted power is `rv` for "
                     "the non-real exponent but `transformed` for the real one, "
                     "over DISTINCT literals — so the postcondition is both "
                     "satisfiable and non-degenerate exactly where the modeled "
                     "behaviour lives. The impl is the frozen body byte-for-byte, "
                     "so the method's own four `ensures` discharge against the "
                     "real implementation too; only the proof body is retuned "
                     "(one `all_goals decide`) to clear the assert's extra goal, "
                     "which the spec view elides.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a closed form with a machine-checked refutation
    # witness at a concrete input and the refinement argument for why its faithful
    # real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- THE DISCRIMINATING RIVAL: drop the non-real guard (the PRE-PATCH bug).
    # ---- A targeted power is ALWAYS handed to the downstream rewrite, even when
    # ---- its exponent is non-real. Violates C1 (matchesPow ∧ ¬real ⇒ rv).
    {
        "id": "R-drop-nonreal-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    if !matchesPow then\n"
            "      return rv\n"
            "    else\n"
            "      return transformed"),
        "refinement": "this IS the pre-change behaviour: a targeted power is "
                      "always rewritten, with no check that its exponent is a real "
                      "number. On a power whose exponent has a nonzero imaginary "
                      "component the faithful real patch attempts the magnitude "
                      "comparison the issue reports as raising an invalid-comparison "
                      "error, so the reported F2P scenario (simplifying such a "
                      "power) still errors instead of returning it unchanged. It "
                      "would NOT resolve, so a verifying rival is a true "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from C1 (matchesPow ∧ ¬expIsReal exp ⇒ out = rv): the "
                     "rival returns `transformed` for a targeted power regardless "
                     "of realness, so on a non-real exponent it returns "
                     "`transformed` while the spec demands `rv`. Refuted at "
                     "matchesPow=true, exp=(re 0, im 1) [non-real], rv=⟨0⟩, "
                     "transformed=⟨1⟩ — distinct values, so the rival's "
                     "`transformed` provably differs from the spec's `rv`. Uses "
                     "matchesPow=true and the ¬real verdict. If it verified ⇒ "
                     "SPEC-TOO-WEAK on the load-bearing non-real guard.",
        "witness": _witness("⟨0⟩ ⟨0, 1⟩ true ⟨1⟩"),
    },

    # ---- CONTROL-FLOW RIVAL: ignore the targeted-power guard entirely and
    # ---- dispatch on realness ALONE. Wrong when the node is NOT a targeted power
    # ---- but has a real exponent: it rewrites where the spec demands unchanged.
    # ---- Violates C3 (¬matchesPow ⇒ rv).
    {
        "id": "R-ignore-matchesPow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    if expIsReal exp then\n"
            "      return transformed\n"
            "    else\n"
            "      return rv"),
        "refinement": "dropping the targeted-power guard rewrites ANY expression "
                      "with a real exponent, including nodes that are not powers of "
                      "the trig function this rewrite targets. A faithful real "
                      "patch that skipped that first guard would rewrite unrelated "
                      "sub-expressions during the bottom-up traversal, corrupting "
                      "the rewrite of every non-targeted node the PASS-TO-PASS trig "
                      "suite pins, so it would NOT resolve.",
        "rationale": "REJECT from C3 (¬matchesPow ⇒ out = rv): the rival never "
                     "consults matchesPow, so on a non-targeted node with a real "
                     "exponent it returns `transformed` while the spec demands "
                     "`rv`. Refuted at matchesPow=false, exp=(re 5, im 0) [real], "
                     "rv=⟨2⟩, transformed=⟨3⟩ — distinct values. Uses "
                     "matchesPow=false (the verdict R-drop-nonreal-guard and "
                     "R-invert-realness never touch). If it verified ⇒ "
                     "SPEC-TOO-WEAK on the unchanged first guard.",
        "witness": _witness("⟨2⟩ ⟨5, 0⟩ false ⟨3⟩"),
    },

    # ---- VALUE/BRANCH RIVAL: invert the realness guard — rewrite a NON-real
    # ---- exponent and leave a REAL one unchanged (the exact opposite of the
    # ---- desired rule). Wrong when the node is a targeted power with a REAL
    # ---- exponent: it returns unchanged where the spec demands the rewrite.
    # ---- Violates C2 (matchesPow ∧ real ⇒ transformed).
    {
        "id": "R-invert-realness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    if !matchesPow then\n"
            "      return rv\n"
            "    else\n"
            "      if expIsReal exp then\n"
            "        return rv\n"
            "      else\n"
            "        return transformed"),
        "refinement": "inverting the realness test rewrites the non-comparable "
                      "(non-real) exponents and leaves the ordinary real-exponent "
                      "powers UNCHANGED. Its faithful real patch would (a) still "
                      "attempt the invalid magnitude comparison on the non-real "
                      "exponent the issue reports, AND (b) stop rewriting every "
                      "real-exponent trig power the FAIL-TO-PASS and PASS-TO-PASS "
                      "rewrite assertions require to be transformed, so it would "
                      "NOT resolve.",
        "rationale": "REJECT from C2 (matchesPow ∧ expIsReal exp ⇒ out = "
                     "transformed): the rival returns `rv` for a targeted power "
                     "with a real exponent, while the spec demands `transformed`. "
                     "Refuted at matchesPow=true, exp=(re 0, im 0) [real], rv=⟨4⟩, "
                     "transformed=⟨5⟩ — distinct values. Uses matchesPow=true and "
                     "the real verdict — the mirror of R-drop-nonreal-guard's "
                     "non-real point, exercising C2 rather than C1. If it verified "
                     "⇒ SPEC-TOO-WEAK on the real-exponent rewrite clause.",
        "witness": _witness("⟨4⟩ ⟨0, 0⟩ true ⟨5⟩"),
    },

    # ---- SHARPEST NEAR-MISS (added by audit, wave a7). Every shipped rival
    # ---- above is refuted at a NON-NEGATIVE imaginary component (im = 0 or
    # ---- im = 1), so none of them tests whether the guard is pinned as
    # ---- "imaginary component is ZERO" rather than the weaker "imaginary
    # ---- component is not positive". This rival reads realness as `exp.im ≤ 0`:
    # ---- it agrees with the frozen impl on EVERY input the rest of the battery
    # ---- probes and diverges only at a strictly negative imaginary component.
    # ---- Violates C1 on the half of the non-real domain the battery left
    # ---- unattacked.
    {
        "id": "R-nonpositive-im-as-real",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    if !matchesPow then\n"
            "      return rv\n"
            "    else\n"
            "      if exp.im ≤ 0 then\n"
            "        return transformed\n"
            "      else\n"
            "        return rv"),
        "refinement": "treating every non-positive imaginary component as real "
                      "keeps the guard for one sign and drops it for the other. "
                      "Its faithful real counterpart still hands a power whose "
                      "exponent has a negative imaginary component to the "
                      "downstream magnitude comparison — the same non-comparable "
                      "ordering the issue reports as raising an invalid-comparison "
                      "error — so simplifying such a power still errors instead of "
                      "returning it unchanged. Half the reported scenario is "
                      "unfixed, so it would NOT resolve.",
        "rationale": "REJECT from C1 (matchesPow ∧ ¬expIsReal exp ⇒ out = rv): "
                     "`expIsReal` is `exp.im == 0`, so an exponent with a "
                     "NEGATIVE imaginary component is not real and must be "
                     "returned unchanged; this rival rewrites it. Refuted at "
                     "matchesPow=true, exp=(re 0, im -1) [non-real], rv=⟨6⟩, "
                     "transformed=⟨7⟩ — distinct values. This is the sharpest "
                     "near-miss available on the carrier: it coincides with the "
                     "frozen impl at every input the other three rivals and both "
                     "positives use, and is separated ONLY at a strictly negative "
                     "imaginary part, a fourth input point (pts=4). It shows C1 is "
                     "pinned pointwise over the whole non-real domain rather than "
                     "on the positive-imaginary half alone. If it verified ⇒ "
                     "SPEC-TOO-WEAK on the sign of the imaginary component.",
        "witness": _witness("⟨6⟩ ⟨0, -1⟩ true ⟨7⟩"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI → VELVET ACCOUNTING. The nagini sibling has 10 SPEC cases (1
# admissibility, 1 soundness, 2 frame-mutation, 6 partial/control-flow rivals)
# plus a 4-case AXIOM lane. This velvet bundle models ONLY the guard structure
# the patch touches — targeted-power? (`matchesPow`, free Bool), real exponent?
# (`expIsReal`, the NEW guard), and the downstream value (`transformed`, free
# Expr) — folding the entire magnitude/parity/perfect-power ladder into the free
# `transformed` (mapping.md §1). So most nagini cases attach to a behaviour this
# bundle does not contract and have NO counterpart.
#
#   nagini case                    -> here                     disposition
#   ---------------------------------------------------------------------------
#   admiss-gold                    -> A-admiss-f2p-shaped        PORTED (added by audit a7)
#   pos-reordered                  -> S-pos-reordered           RE-EXPRESSED
#   (no sibling)                   -> S-pos-grounded            ADDED (grounded materialise)
#   frame-write-value              -> (none)                    VACUOUS
#   frame-write-real               -> (none)                    VACUOUS
#   drop-nonreal-guard             -> R-drop-nonreal-guard      PORTED (the central defect)
#   guard-after-ordering           -> R-drop-nonreal-guard      MERGED (see below)
#   partial-odd-rewrite            -> (none)                    NO COUNTERPART (ladder folded)
#   partial-even-unchanged         -> (none)                    NO COUNTERPART (ladder folded)
#   partial-ignore-pow             -> (none)                    NO COUNTERPART (ladder folded)
#   partial-squared-as-general     -> (none)                    NO COUNTERPART (ladder folded)
#   over-max-rewrite               -> (none)                    NO COUNTERPART (ladder folded)
#   (no sibling)                   -> R-ignore-matchesPow       ADDED (attacks C3)
#   (no sibling)                   -> R-invert-realness         ADDED (attacks C2)
#   (no sibling)                   -> R-nonpositive-im-as-real  ADDED by audit a7
#                                                               (near-miss on C1's
#                                                                negative-im half)
#   AXIOM_TESTS (4)                -> (none)                     DROPPED (G-AX)
#
# 7 velvet cases: 2 soundness positives, 1 admissibility positive, 4 uniqueness
# rivals. Every top-level clause of the modeled postcondition (C1/C2/C3 + master
# E) is attacked by some rival and defended by the positives.
#
# RE-EXPRESSED (pos-reordered -> S-pos-reordered): nagini's reordered-branch
#   soundness positive ports as a correct reshape that tests the two guards in
#   positive-condition form, behaviourally identical, closing under the frozen
#   `loom_solve`. Verified to build. (nagini's admiss-gold is NOT subsumed here —
#   it ports on its own as A-admiss-f2p-shaped; see below.)
# PORTED (admiss-gold -> A-admiss-f2p-shaped): ADDED BY AUDIT a7. The lane was
#   previously argued away on the grounds that the method has no `require`. The
#   total-carrier analogue of PRECOND-TOO-STRONG is the obligation being
#   unsatisfiable or degenerate at an F2P-shaped input, which this case
#   discharges by evaluation at that input (guard separates the two exponent
#   shapes; master clause's two images there are the two DISTINCT values) before
#   closing the frozen obligation against the byte-identical frozen impl. Real
#   build exit 0; the assert is live (falsifying a conjunct fails the file).
# ADDED (S-pos-grounded): materialises the master clause's grounded expression
#   directly (`return if matchesPow then …`). Distinct control-flow shape from
#   S-pos-reordered, also closes under the frozen proof. Verified to build.
# PORTED (drop-nonreal-guard -> R-drop-nonreal-guard): THE central rival — the
#   pre-patch behaviour (targeted power always rewritten, no realness check),
#   attacking C1. The refinement argument carries over: on a non-real exponent
#   the faithful patch attempts the magnitude comparison the issue reports as
#   raising, so it does not resolve. Witness verified to discriminate (rival exit
#   0, gold exit 1).
# MERGED (guard-after-ordering -> R-drop-nonreal-guard): nagini's late-guard rival
#   exploits the ordering axioms' `Requires(e.real)` — machinery NOT modeled here
#   (the downstream is the free `transformed`, with no ordering precondition). On
#   this carrier "guard placed after the ordering" is behaviourally identical to
#   "guard absent", so the two nagini cases are the single modeled defect
#   R-drop-nonreal-guard. Merged, not dropped for effort: there is no distinct
#   observable to attack.
# NO COUNTERPART (partial-odd-rewrite, partial-even-unchanged, partial-ignore-pow,
#   partial-squared-as-general, over-max-rewrite): all five attack the
#   magnitude/parity/perfect-power/order dispatch, which this bundle folds into
#   the free `transformed` (directive 7). Those behaviours are not contracted
#   here, so there is no clause to violate and no rival to build. Carrier
#   narrowing, not an effort gap.
# ADDED (R-ignore-matchesPow, R-invert-realness): the two clauses C3 (¬matchesPow
#   ⇒ rv) and C2 (matchesPow ∧ real ⇒ transformed) that the single nagini
#   guard-defect does not isolate. R-ignore-matchesPow drops the first guard
#   (rewrites a non-targeted node), R-invert-realness inverts the second (leaves a
#   real-exponent targeted power unchanged). Both witnesses verified to
#   discriminate.
# VACUOUS (frame-write-value, frame-write-real): nagini holds `exp` at
#   Acc(...,1/2) and a store into exp.value / exp.real is rejected for
#   insufficient permission. Velvet is referentially transparent, declares no
#   `mut` binder — `rv`/`exp`/`matchesPow`/`transformed` are immutable values with
#   no heap footprint — so there is no read-only input to overwrite and no
#   permission system to trip. No substitute fabricated.
# DIVERGENCE: the sibling carries no divergence case, and the class is CLOSED BY
#   THE SEMANTICS here, NOT a spec hole. Two premises from earlier versions of this
#   note are withdrawn. First, "this bundle runs under `termination \"partial\"`":
#   the frozen solution sets `"total"`, as do all 500 velvet bundles. Second, and
#   this is the one that mattered, "the annotation is accepted without the decrease
#   being PROVEN". Rebuilt at the shape that note named, `while k > 0 /
#   invariant k > 0 / done_with k = 0 / decreasing k` with body `k := k + 1`: it is
#   REJECTED, exit 1, `unsolved goals`, `case «decreasing_1: k»`, residual
#   `k + 1 < k`. A constant measure is rejected the same way
#   (`case «decreasing_1: (0 : Nat)»`, residual `0 < 0`). Omitting `decreasing`
#   remains rejected too (`Decreasing annotations are required in total correctness
#   semantics`). So both shapes fail, the second on the measure's OWN goal rather
#   than on the annotation requirement, and no diverging rival satisfies this spec.
#   Nothing is escalated. The class still cannot SHIP as a reject case, for a
#   witness-contract reason: the rejection fires on the `method` command, so the
#   rival's module never compiles and the witness built from it cannot elaborate,
#   which the gate records as `witness-unproven` (INCONCLUSIVE, forcing
#   MALFORMED-TESTS). See the DIVERGENCE bullet in the module docstring.
# DROPPED (AXIOM_TESTS x4): the axiom lane is G-AX's job. This bundle has no
#   consumed axiom and no deep-model reference (mapping.md §3: the two unchanged
#   sub-steps are free values), and the G-PBT gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Input binders: `rv`, `exp` (field `im` drives
#   `expIsReal`), `matchesPow`, `transformed`. The four reject witnesses probe
#   FOUR distinct input points (pts=4) and vary every dispatch-driving binder:
#     * matchesPow — true (R-drop-nonreal-guard, R-invert-realness,
#       R-nonpositive-im-as-real) and false (R-ignore-matchesPow): both verdicts
#       of the first guard.
#     * expIsReal exp — non-real at im=1 (R-drop-nonreal-guard), non-real at
#       im=-1 (R-nonpositive-im-as-real), and real im=0 (R-ignore-matchesPow,
#       R-invert-realness): both verdicts of the NEW guard, and both SIGNS of the
#       non-real verdict, so the guard is pinned as "im is zero" and not merely
#       "im is not positive".
#     * rv / transformed — distinct Expr values in every witness so `out = rv` vs
#       `out = transformed` is a real observation, never trivially equal.
#   Clause coverage: C1 (matchesPow ∧ ¬real ⇒ rv) by R-drop-nonreal-guard (im=1)
#   and R-nonpositive-im-as-real (im=-1); C2 (matchesPow ∧ real ⇒ transformed) by
#   R-invert-realness; C3 (¬matchesPow ⇒ rv) by R-ignore-matchesPow; master E by
#   all four; both soundness positives defend the whole obligation and
#   A-admiss-f2p-shaped pins it satisfiable and non-degenerate at an F2P-shaped
#   input. No two rivals are refuted at the same input.
# WITNESS DISCRIMINATION (verified during authoring with real builds per reject
#   case): each witness ELABORATES against its closed-form rival (the extracted
#   program reduces to a literal that provably differs from the spec at the probed
#   input) and FAILS against the frozen nested-guard solution (whose extracted
#   program reduces to a different literal there). The carrier is fully
#   transparent, so no witness binds a hypothesis and there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears.
AXIOM_TESTS = []
