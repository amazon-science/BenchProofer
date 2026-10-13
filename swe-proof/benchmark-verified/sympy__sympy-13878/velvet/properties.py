"""properties.py — G-PBT falsification battery for sympy__sympy-13878 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text strictly inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct arcsinCdfBuild`` tactic
body, is changed — both regions the consumer spec view elides, so
``markers.same_spec`` holds by construction and the ``prove_correct
arcsinCdfBuild`` header survives). It is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE — one contracted method over a finite symbolic-expression
carrier (the ``Expr`` inductive in the frozen ``pure`` region):

  arcsinCdfBuild (a : Expr) (b : Expr) (x : Expr) return (out : Expr)
    ensures out = arcsinExprCdf a b x          -- THE load-bearing clause (Q1)

The method builds the closed-form cumulative distribution object of a
two-parameter, bounded-support continuous distribution from its lower endpoint
``a``, its upper endpoint ``b``, and the evaluation point ``x``. There is NO
``require`` clause: every operand triple is in-domain.

``arcsinExprCdf a b x`` is a total, fully-unfolded pure ``def`` over the
method's own three arguments (the ``axioms`` region is EMPTY — nothing opaque,
no answer key to echo, directive 8 satisfied: every node of the target object
is a concrete constructor applied to ``a``, ``b``, ``x``, the rational
constants, or the circle constant). Q1 is therefore an *operand-by-operand
structural pin*, and it decomposes into six independently-attackable
sub-behaviours, each of which some rival below violates:

  * SHAPE      — the result is a three-clause case split, not the generic
                 definite-integral object produced when no closed form is
                 available;
  * OFFSET     — the middle clause's numerator is the evaluation point's
                 displacement from the LOWER endpoint, in that operand order;
  * WIDTH      — its denominator is the support width, from the lower endpoint
                 to the UPPER one, in that operand order;
  * SCALE      — the middle clause is the doubled inverse-sine of the square
                 root of that ratio, over the circle constant (both the literal
                 factor and the two function applications, in that nesting);
  * GUARDS     — the first guard is STRICT and compares the evaluation point
                 against the lower endpoint in that operand order; the second is
                 NON-STRICT against the upper endpoint; the third is the
                 always-true guard;
  * TAILS      — the value below the support is the rational zero and the value
                 above it is the rational one, in that order;
  * ORDER      — the three clauses occupy their intended SLOTS: the vanishing
                 tail is tried first, the closed form second, the saturated tail
                 last. A case split's clauses are tried in sequence, so a rival
                 holding every value and every guard fixed and permuting only
                 the slots is a distinct defect from any of the above.

``arcsinExprCdf`` pins each of these seven independently, and every one is
attacked by some rival below — including the third guard and the clause
ordering, which an earlier revision of this battery DECLARED as covered while
shipping no rival against either. Both gaps are now closed by
``weak-final-guard-conditional`` and ``weak-clause-order-permuted``.

THREE input binders, all free and all three genuinely load-bearing: ``a`` and
``b`` (the two endpoints — they fix the offset, the width and both guards) and
``x`` (the evaluation point — it appears in the offset and in both guards).
Because ``arcsinExprCdf`` mentions every one of them, a rival that mishandles
any single binder is refutable, and the fourteen reject witnesses below vary all
three across fourteen DISTINCT operand triples.

CARRIER GRANULARITY — a real limit of this model, recorded rather than papered
over. The carrier distinguishes ``Expr.one`` from ``Expr.natLit 1`` and
``Expr.zero`` from ``Expr.natLit 0`` as separate constructors, and Q1's
structural pin therefore rejects an impl that spells a tail with the literal
node instead of the rational one. On the library side those two spellings
denote the SAME object (the small-integer constructor returns the rational
unit/zero singleton for the values 1 and 0), so such an impl is in fact
faithful and the spec is strictly finer than the behaviour it models. This is a
narrowness in the CARRIER, not a rival: it can only ever cause the spec to
reject something correct, never to accept something wrong, so it cannot mint a
false pass for any case here. It is recorded because a reader comparing an
``Expr.natLit 1`` reshape against this battery should know the rejection is a
modeling artefact, not a spec violation.

WITNESS MECHANICS ON THIS BUNDLE. The spec is a ``method`` CONTRACT, not a bare
predicate, so each witness reaches Q1 through Velvet's own tester machinery:
``arcsinCdfBuildTester a b x = false`` says the extracted program's output
violates the postcondition at that concrete operand triple. The frozen impl is
LOOP-FREE (a single ``let`` plus a constructor application) and the carrier is a
``DecidableEq`` inductive with no opaque node, so every tester reduces under
``decide`` at literal operands — the fully-transparent case, so NO conditioning
on the carrier is needed anywhere in this battery and no witness binds a
hypothesis (hence no consistency probe is even reachable). Each witness is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh`` for all fourteen rivals: every witness ELABORATES
against its rival (its tester ``decide``s to ``false``) and FAILS against the
frozen solution (gold's tester ``decide``s to ``true``, so ``= false`` is
refuted), so each rejection is a genuine spec refutation and not the frozen
``loom_solve`` failing to re-close a reshaped obligation. Every reject MODULE
keeps the frozen proof VERBATIM; the two positives and the admissibility case
retune only the elided tactic body.

GOLD'S EXIT CODE CARRIES INFORMATION ABOUT THE CLAIM — established by the
flipped-claim experiment, not by reading the error and judging it "semantic".
For every reject case a second file was built differing from the witness ONLY in
what it asserts (``= false`` replaced by ``= true``, i.e. the claim that gold is
CORRECT at that triple). All fourteen flipped claims build against the frozen
solution with exit 0, while all fourteen witnesses fail there with exit 1 and

    error: Tactic `decide` proved that the proposition
      arcsinCdfBuildTester <a> <b> <x> = false
    is false

— a CONCRETE evaluated equation naming the very operands the case claims to
discriminate at, and an error that flips with the claim. So gold's failure is a
performed refutation and not a stuck reduction, a missing identifier, a type
mismatch or a timeout: the two exit codes bracket the claim, which is the only
evidence that distinguishes a real discriminator from a hollow one. No case here
relies on a signature that needs interpreting.

ADVERSARIAL READ of the sibling battery's classes on this carrier (see the
footer for the case-by-case accounting):

  * FRAME / PERMISSION-MUTATION — VACUOUS, and the sibling already records it as
    vacuous on its own backend too (its two inputs are pass-by-value scalars
    carrying no heap permission, so there is no read-only input to overwrite).
    Velvet is referentially transparent a fortiori: all three operands are
    immutable ``Expr`` VALUES, the method declares no ``mut`` binder, and there
    is no heap and no aliasing. No substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records for its own
    fully-unfolded pure oracle. Q1 pins ``out`` to ``arcsinExprCdf a b x``, a
    transparent ``def`` over the method's own arguments with an EMPTY axioms
    region. The unique satisfier is the grounded construction itself, so the
    positive controls below are cheapest faithful reshapes, not wrong echoes.
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * PRECONDITION / DOMAIN rivals — the sibling's precondition-violating rival
    has no counterpart: this method has NO ``require`` clause and the sibling's
    second contracted function is not modeled here (carrier narrowing).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13878"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` (the comment lines included: they live inside the elided
# impl region). Unique in the file, asserted at load, so every edit below keeps
# same_spec by construction and leaves the `prove_correct` header intact.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- Build the three-clause closed form directly from the operands `a`, `b`,\n"
    "    -- `x`. The middle clause is the inverse-sine expression on the support.\n"
    "    let onSupport : Expr :=\n"
    "      Expr.div\n"
    "        (Expr.mul (Expr.natLit 2)\n"
    "          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))\n"
    "        Expr.pi\n"
    "    return Expr.piecewise3\n"
    "      Expr.zero (Expr.lt x a)\n"
    "      onSupport (Expr.le x b)\n"
    "      Expr.one Expr.top"
)
assert _BASE.count(_IMPL) == 1, "arcsinCdfBuild impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); every rival leaves it as-is, so the wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct arcsinCdfBuild by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct arcsinCdfBuild body drifted"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the elided tactic body retuned (correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. Velvet's tester machinery is the only route to a
# ---- `method` contract's postcondition: `arcsinCdfBuildTester a b x = false`
# ---- says the extracted program's output violates Q1 at that operand triple.
# ---- There is no `require` clause, so no triple is vacuously excluded (a
# ---- precondition-false input would short-circuit the tester to `true`). Both
# ---- gold and every rival are loop-free over a DecidableEq carrier with no
# ---- opaque node, so both testers reduce under `decide` at literal operands.
def _witness(a, b, x):
    return ("extract_program_for arcsinCdfBuild\n"
            "prove_precondition_decidable_for arcsinCdfBuild\n"
            "prove_postcondition_decidable_for arcsinCdfBuild\n"
            "derive_tester_for arcsinCdfBuild\n\n"
            f"example : arcsinCdfBuildTester {a} {b} {x} = false := by\n"
            "  decide\n")


# ---- rival-body template. Every rival keeps the SHAPE of the target object (a
# ---- three-clause case split whose middle clause is a scaled inverse-sine over
# ---- the circle constant) and perturbs exactly ONE sub-behaviour, so each is a
# ---- genuine partial-domain attack on one clause of Q1 rather than a blanket
# ---- wrong impl. `_SHAPE_RIVAL` (the pre-change shape) is the sole exception.
def _clauses(comment, numer, denom, mult, g1, g2, g3, v1, v3,
             inner="asin_sqrt", order="v1_mid_v3"):
    ratio = f"(Expr.div {numer} {denom})"
    body = {"asin_sqrt": f"Expr.asin (Expr.sqrt {ratio})",
            "sqrt_asin": f"Expr.sqrt (Expr.asin {ratio})",
            "asin_only": f"Expr.asin {ratio}"}[inner]
    # `order` selects WHICH clause slot each value occupies. The gold ordering
    # is (below-support, on-support, above-support); `mid_last` moves the
    # inverse-sine clause into the final slot and the saturated tail into the
    # middle, keeping all three values and all three guards intact.
    clauses = {
        "v1_mid_v3": (f"      {v1} {g1}\n"
                      f"      onSupport {g2}\n"
                      f"      {v3} {g3}"),
        "mid_last": (f"      {v1} {g1}\n"
                     f"      {v3} {g2}\n"
                     f"      onSupport {g3}"),
    }[order]
    return (f"{comment}\n"
            f"    let onSupport : Expr :=\n"
            f"      Expr.div (Expr.mul {mult} ({body})) Expr.pi\n"
            f"    return Expr.piecewise3\n"
            f"{clauses}")


_GOLD_ARGS = dict(numer="(Expr.sub x a)", denom="(Expr.sub b a)",
                  mult="(Expr.natLit 2)", g1="(Expr.lt x a)",
                  g2="(Expr.le x b)", g3="Expr.top", v1="Expr.zero",
                  v3="Expr.one")


def _rival(comment, **overrides):
    return _clauses(comment, **{**_GOLD_ARGS, **overrides})


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both are straight-line constructor
    # applications (no loop, no fold), so no induction lemma is needed and both
    # were confirmed to verify EXIT 0 with a real build. The sibling ships three
    # reshape positives against its two contracted functions; this bundle models
    # ONE function, so its reshape ARGUMENT is carried by these two.
    # =====================================================================
    {
        "id": "pos-model-direct",
        "kind": "soundness",
        "expect": "verify",
        # Produce the pure model value itself instead of spelling the tree out
        # inline. Observationally identical on every operand triple. The frozen
        # `loom_solve` still closes the byte-identical obligation (the body is
        # definitionally Q1's right-hand side), so the proof is untouched.
        "module": _impl(
            "    -- Produce the closed-form case split as the pure model value\n"
            "    -- itself rather than spelling its constructors out inline.\n"
            "    return arcsinExprCdf a b x"),
        "rationale": "PASS SOURCE = Q1 (out = arcsinExprCdf a b x). Returning the "
                     "pure model value directly is observationally identical to "
                     "the frozen inline construction on every operand triple, so "
                     "Q1 holds on the whole domain. A faithful, structurally "
                     "different reshape MUST verify; if it cannot, the "
                     "postcondition over-constrains the executable shape rather "
                     "than the value (SPEC-TOO-STRONG — it would reject its own "
                     "model's output). Frozen proof kept verbatim.",
    },
    {
        "id": "pos-subnode-lets",
        "kind": "soundness",
        "expect": "verify",
        # Maximal let-splitting: bind the displacement, the support width, their
        # ratio, the inverse-sine term and both order guards in separate typed
        # locals, then assemble. Same value, a very different executable shape
        # (six binds instead of one). Frozen proof still closes.
        "module": _impl(
            "    -- Assemble the case split from separately-bound sub-nodes: the\n"
            "    -- displacement of the evaluation point from the lower endpoint,\n"
            "    -- the width of the support, their ratio, the inverse-sine term,\n"
            "    -- and the two order guards.\n"
            "    let offset : Expr := Expr.sub x a\n"
            "    let width : Expr := Expr.sub b a\n"
            "    let ratio : Expr := Expr.div offset width\n"
            "    let angle : Expr := Expr.asin (Expr.sqrt ratio)\n"
            "    let onSupport : Expr := Expr.div (Expr.mul (Expr.natLit 2) angle) Expr.pi\n"
            "    let belowGuard : Expr := Expr.lt x a\n"
            "    let supportGuard : Expr := Expr.le x b\n"
            "    return Expr.piecewise3 Expr.zero belowGuard onSupport supportGuard\n"
            "      Expr.one Expr.top"),
        "rationale": "PASS SOURCE = Q1. A let-reshape that binds every sub-node "
                     "(displacement, width, ratio, inverse-sine term, both "
                     "guards) in its own typed local and assembles them last: the "
                     "same value by a markedly different executable staging. Must "
                     "verify, else SPEC-TOO-STRONG on the staging rather than the "
                     "value. Frozen proof kept verbatim.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling's admissibility probe asserts, INSIDE the impl
    # region (elided from the spec view, so same_spec holds), that a legitimate
    # F2P-shaped input is admitted and the obligation is satisfiable there. This
    # method has NO `require` clause, so the "is the input admitted" half is
    # trivially true; the residual admissibility risk on this carrier is
    # DEGENERACY, and that is what the probe pins at a concrete F2P-shaped triple
    # (three distinct operands): the target object really is the operand-carrying
    # three-clause split, and it is neither a constant nor the generic
    # definite-integral object. The impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned only to clear the extra
    # decidable `assert` goal. The assert is LIVE — a false claim leaves an
    # unsolved goal (confirmed during authoring). Verified EXIT 0.
    # =====================================================================
    {
        "id": "admiss-f2p-operands",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    -- Admissibility at an F2P-shaped operand triple (three DISTINCT\n"
            "    -- operands): the contract's target object is satisfiable there and\n"
            "    -- NON-DEGENERATE — it carries the operands through both guards and\n"
            "    -- the middle clause, rather than collapsing to a constant or to the\n"
            "    -- generic definite-integral object obtained when no closed form is\n"
            "    -- available.\n"
            "    assert (with_name_prefix `admiss\n"
            "      (arcsinExprCdf (Expr.natLit 1) (Expr.natLit 2) (Expr.natLit 3)\n"
            "         = Expr.piecewise3\n"
            "             Expr.zero (Expr.lt (Expr.natLit 3) (Expr.natLit 1))\n"
            "             (Expr.div\n"
            "               (Expr.mul (Expr.natLit 2)\n"
            "                 (Expr.asin (Expr.sqrt (Expr.div\n"
            "                   (Expr.sub (Expr.natLit 3) (Expr.natLit 1))\n"
            "                   (Expr.sub (Expr.natLit 2) (Expr.natLit 1))))))\n"
            "               Expr.pi) (Expr.le (Expr.natLit 3) (Expr.natLit 2))\n"
            "             Expr.one Expr.top\n"
            "       ∧ arcsinExprCdf (Expr.natLit 1) (Expr.natLit 2) (Expr.natLit 3) ≠ Expr.zero\n"
            "       ∧ arcsinExprCdf (Expr.natLit 1) (Expr.natLit 2) (Expr.natLit 3)\n"
            "           ≠ Expr.integralFallback (Expr.natLit 3) (Expr.natLit 3)))\n"
            + _IMPL,
            "prove_correct arcsinCdfBuild by\n  loom_solve\n  all_goals decide"),
        "rationale": "the method has no `require` clause, so every operand triple "
                     "is admitted and the sibling's 'is this input in-domain' "
                     "question is trivially yes; the residual admissibility risk "
                     "here is DEGENERACY of the obligation. The in-region assert "
                     "pins, at an F2P-shaped triple of three DISTINCT operands, "
                     "that Q1's target object is exactly the operand-carrying "
                     "three-clause split — and is neither the rational zero (a "
                     "constant collapse) nor the generic definite-integral object. "
                     "It is a live decidable claim (a false one leaves an unsolved "
                     "goal); the impl is otherwise gold, so Q1 discharges too. If "
                     "this cannot verify ⇒ PRECOND-TOO-STRONG / a vacuous "
                     "obligation on a legitimate input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at its OWN
    # concrete operand triple and a refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Every rival keeps the frozen
    # proof verbatim. Fourteen distinct witness points; all three binders vary.
    # =====================================================================
    {
        "id": "weak-prechange-integral",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change shape: leave the cumulative distribution as the generic
        # definite-integral object instead of building the closed form. Attacks
        # the SHAPE sub-behaviour; this is the G-DIFF discriminator.
        "module": _impl(
            "    -- Leave the cumulative distribution as the generic\n"
            "    -- definite-integral object obtained by the default route instead\n"
            "    -- of building the closed-form case split.\n"
            "    return Expr.integralFallback x x"),
        "refinement": "this is the PRE-CHANGE behaviour the differential gate "
                      "flags: with no closed form supplied for this distribution, "
                      "the cumulative function is obtained by the default "
                      "definite-integration route and comes back as an "
                      "unevaluated, non-convergent integral object — exactly what "
                      "the issue reports as unusable. The sole failing test "
                      "asserts the cumulative distribution equals the closed-form "
                      "case split under STRUCTURAL object equality, and an "
                      "integral object is not structurally equal to a case split, "
                      "so the assertion fails. Its faithful real counterpart (no "
                      "closed form supplied at all) is precisely the state that "
                      "does NOT resolve.",
        "rationale": "REJECT from Q1 (out = arcsinExprCdf a b x) via the SHAPE "
                     "sub-behaviour: the target object is a three-clause case "
                     "split, the rival returns a different constructor entirely, "
                     "so the two are unequal at EVERY operand triple. If it "
                     "verifies ⇒ SPEC-TOO-WEAK (the spec would not sense the "
                     "pre-change state at all). Refuted at (1, 2, 3).",
        "witness": _witness("(Expr.natLit 1)", "(Expr.natLit 2)", "(Expr.natLit 3)"),
    },
    {
        "id": "weak-offset-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # OFFSET: measure the displacement from the evaluation point to the lower
        # endpoint instead of the other way round. Everything else is gold.
        "module": _impl(_rival(
            "    -- The middle clause's numerator measures the displacement from the\n"
            "    -- evaluation point to the lower endpoint, in that operand order.",
            numer="(Expr.sub a x)")),
        "refinement": "a real counterpart with the subtraction operands reversed "
                      "in the numerator would build a case split whose middle "
                      "clause negates the displacement from the lower endpoint — "
                      "the wrong cumulative value on the whole support (and, for "
                      "real endpoints, the inverse sine of the square root of a "
                      "negative ratio). The failing test compares the cumulative "
                      "distribution to the expected object under STRUCTURAL "
                      "equality, and a reversed subtraction is a different tree, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from Q1 via the OFFSET sub-behaviour: the target "
                     "object's numerator is the displacement of the evaluation "
                     "point from the lower endpoint in that operand order; the "
                     "rival swaps the two operands, so the trees differ whenever "
                     "the evaluation point and the lower endpoint are distinct. "
                     "Correct on every triple where they coincide, so a genuine "
                     "partial-domain attack. Refuted at (3, 4, 5).",
        "witness": _witness("(Expr.natLit 3)", "(Expr.natLit 4)", "(Expr.natLit 5)"),
    },
    {
        "id": "weak-width-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        # WIDTH: measure the support width from the upper endpoint down to the
        # lower one instead of upward. Attacks the OTHER subtraction, so it is a
        # near-miss that weak-offset-reversed does not subsume — hence its own
        # witness point, which moves BOTH endpoints.
        "module": _impl(_rival(
            "    -- The middle clause's denominator measures the width of the support\n"
            "    -- downward, from the upper endpoint to the lower one.",
            denom="(Expr.sub a b)")),
        "refinement": "a real counterpart with the subtraction operands reversed "
                      "in the DENOMINATOR would normalise the displacement by the "
                      "negated support width, so the cumulative value on the "
                      "support has the wrong sign under the square root while the "
                      "guards and both tails stay right. The failing test's "
                      "structural comparison distinguishes the two subtraction "
                      "orders, so it would NOT resolve.",
        "rationale": "REJECT from Q1 via the WIDTH sub-behaviour: the denominator "
                     "runs from the lower endpoint to the upper one in that "
                     "operand order; the rival reverses it, so the trees differ "
                     "whenever the two endpoints are distinct. A near-miss the "
                     "offset rival does not subsume — it perturbs the OTHER "
                     "subtraction — so it carries its own point, (6, 7, 8), which "
                     "moves both endpoints as well as the evaluation point.",
        "witness": _witness("(Expr.natLit 6)", "(Expr.natLit 7)", "(Expr.natLit 8)"),
    },
    {
        "id": "weak-scale-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # SCALE (literal factor): the middle clause is scaled by the rational
        # unit instead of the doubling literal. Everything else is gold.
        "module": _impl(_rival(
            "    -- The middle clause is scaled by the rational unit instead of the\n"
            "    -- doubling literal.",
            mult="Expr.one")),
        "refinement": "a real counterpart that omitted the doubling factor would "
                      "produce a cumulative distribution reaching only half its "
                      "final value at the top of the support — not a cumulative "
                      "distribution at all, and not the object the failing test "
                      "asserts. The structural comparison also distinguishes the "
                      "two literals directly, so it would NOT resolve.",
        "rationale": "REJECT from Q1 via the SCALE sub-behaviour: the target "
                     "object multiplies the inverse-sine term by the exact "
                     "doubling literal, the rival by the rational unit, so the "
                     "middle clauses differ at EVERY operand triple. Refuted at "
                     "(0, 9, 1) — a point that pins the lower endpoint to the "
                     "rational ZERO rather than an integer literal, exercising a "
                     "constant-valued endpoint no other witness uses.",
        "witness": _witness("Expr.zero", "(Expr.natLit 9)", "(Expr.natLit 1)"),
    },
    {
        "id": "weak-function-nesting-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # SCALE (nesting): apply the square root OUTSIDE the inverse sine instead
        # of inside it. Both functions are still present and the ratio is still
        # right — only the composition order is wrong.
        "module": _impl(_rival(
            "    -- The square root is applied OUTSIDE the inverse sine rather than\n"
            "    -- to its argument.",
            inner="sqrt_asin")),
        "refinement": "a real counterpart that composed the two functions in the "
                      "opposite order would take the inverse sine of the raw ratio "
                      "and the square root of that angle — a different function of "
                      "the operands, wrong throughout the interior of the support. "
                      "The failing test's structural comparison distinguishes the "
                      "two nestings, so it would NOT resolve. This attacks the "
                      "composition ORDER while keeping both function applications "
                      "and the ratio intact, which the dropped-root rival does not "
                      "cover.",
        "rationale": "REJECT from Q1 via the SCALE sub-behaviour's function "
                     "NESTING: the target object takes the inverse sine OF the "
                     "square root of the ratio; the rival inverts the composition, "
                     "so the middle clauses differ at every triple. Refuted at "
                     "(18, 19, 20).",
        "witness": _witness("(Expr.natLit 18)", "(Expr.natLit 19)", "(Expr.natLit 20)"),
    },
    {
        "id": "weak-root-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # SCALE (missing application): drop the square root entirely and take the
        # inverse sine of the bare ratio.
        "module": _impl(_rival(
            "    -- The square root is omitted: the inverse sine is applied to the\n"
            "    -- bare ratio.",
            inner="asin_only")),
        "refinement": "a real counterpart that omitted the square root would apply "
                      "the inverse sine to the bare normalised displacement, "
                      "giving the wrong cumulative value everywhere strictly "
                      "inside the support (the two agree only at the endpoints of "
                      "the unit interval). The failing test asserts the object "
                      "with the root present, so it would NOT resolve.",
        "rationale": "REJECT from Q1 via the SCALE sub-behaviour's missing function "
                     "APPLICATION: the target object's inverse-sine argument is "
                     "the square root of the ratio, the rival's is the ratio "
                     "itself, so the middle clauses differ at every triple. A "
                     "distinct defect from the nesting swap (a node deleted rather "
                     "than reordered), hence its own point (21, 22, 23).",
        "witness": _witness("(Expr.natLit 21)", "(Expr.natLit 22)", "(Expr.natLit 23)"),
    },
    {
        "id": "weak-lower-guard-nonstrict",
        "kind": "uniqueness",
        "expect": "reject",
        # GUARDS (strictness, first guard): the first guard is non-strict, so the
        # lower endpoint itself falls into the below-support clause.
        "module": _impl(_rival(
            "    -- The first guard is NON-STRICT, so the lower endpoint itself falls\n"
            "    -- into the below-support clause.",
            g1="(Expr.le x a)")),
        "refinement": "a real counterpart that made the first order relation "
                      "non-strict would assign the below-support value at the "
                      "lower endpoint itself, where the cumulative distribution "
                      "should already take its closed-form value — an off-by-one "
                      "boundary defect at the bottom of the support. The failing "
                      "test compares the whole object structurally, and the two "
                      "order relations are different constructors, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from Q1 via the GUARDS sub-behaviour: the target "
                     "object's first guard is the STRICT order relation, the "
                     "rival's the non-strict one — different constructors, so the "
                     "trees differ at every triple. Attacks guard STRICTNESS at "
                     "the lower boundary. Refuted at (11, 12, 13).",
        "witness": _witness("(Expr.natLit 11)", "(Expr.natLit 12)", "(Expr.natLit 13)"),
    },
    {
        "id": "weak-upper-guard-strict",
        "kind": "uniqueness",
        "expect": "reject",
        # GUARDS (strictness, second guard): the second guard is strict, so the
        # upper endpoint falls through to the above-support clause. The mirror of
        # the previous rival, on the OTHER guard.
        "module": _impl(_rival(
            "    -- The second guard is STRICT, so the upper endpoint falls through to\n"
            "    -- the above-support clause.",
            g2="(Expr.lt x b)")),
        "refinement": "a real counterpart that made the second order relation "
                      "strict would fall through to the above-support value at the "
                      "upper endpoint itself, where the closed form should still "
                      "apply — the mirror off-by-one at the top of the support. "
                      "The structural comparison distinguishes the two order "
                      "relations, so it would NOT resolve.",
        "rationale": "REJECT from Q1 via the GUARDS sub-behaviour on the SECOND "
                     "guard, which the lower-guard rival leaves correct: the "
                     "target object's second guard is NON-STRICT, the rival's is "
                     "strict. Refuted at (14, 15, π) — a point whose evaluation "
                     "point is the circle constant rather than an integer literal, "
                     "a carrier node no other witness places in that binder.",
        "witness": _witness("(Expr.natLit 14)", "(Expr.natLit 15)", "Expr.pi"),
    },
    {
        "id": "weak-lower-guard-flipped",
        "kind": "uniqueness",
        "expect": "reject",
        # GUARDS (operand order): the first guard compares the lower endpoint
        # against the evaluation point instead of the other way round. Same
        # relation, operands swapped — a different defect from the strictness
        # rivals.
        "module": _impl(_rival(
            "    -- The first guard compares the lower endpoint against the evaluation\n"
            "    -- point rather than the other way round.",
            g1="(Expr.lt a x)")),
        "refinement": "a real counterpart that swapped the first guard's operands "
                      "would select the below-support value exactly ON the support "
                      "and the closed form below it — the case split inverted at "
                      "the bottom boundary, so the cumulative distribution is "
                      "wrong on essentially the whole domain. The failing test's "
                      "structural comparison distinguishes the two operand orders, "
                      "so it would NOT resolve.",
        "rationale": "REJECT from Q1 via the GUARDS sub-behaviour's OPERAND ORDER: "
                     "the target object's first guard places the evaluation point "
                     "on the left, the rival swaps it. Same relation, so this is "
                     "not subsumed by either strictness rival; it needs its own "
                     "point, (24, 25, 26).",
        "witness": _witness("(Expr.natLit 24)", "(Expr.natLit 25)", "(Expr.natLit 26)"),
    },
    {
        "id": "weak-tails-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # TAILS: exchange the below-support and above-support values, so the
        # cumulative distribution runs backwards at both ends. Middle clause and
        # all three guards are gold.
        "module": _impl(_rival(
            "    -- The below-support and above-support values are exchanged.",
            v1="Expr.one", v3="Expr.zero")),
        "refinement": "a real counterpart that exchanged the two tail values would "
                      "return the saturated value below the support and the "
                      "vanishing value above it — a cumulative distribution "
                      "running backwards at both ends, while the closed form on "
                      "the support and every guard stay correct. The failing test "
                      "asserts the whole object, including both tails, so it would "
                      "NOT resolve.",
        "rationale": "REJECT from Q1 via the TAILS sub-behaviour: the target "
                     "object's first clause value is the rational zero and its "
                     "last the rational one; the rival exchanges them, so the "
                     "trees differ at every triple. Attacks the two clause VALUES "
                     "no other rival touches (every other rival leaves both tails "
                     "gold). Refuted at (16, 1, 17) — a point placing the rational "
                     "unit in the upper-endpoint binder.",
        "witness": _witness("(Expr.natLit 16)", "Expr.one", "(Expr.natLit 17)"),
    },
    {
        "id": "weak-final-guard-conditional",
        "kind": "uniqueness",
        "expect": "reject",
        # GUARDS (the THIRD guard). Every other rival leaves the final guard
        # gold, so the battery declared a GUARDS sub-behaviour covering "the
        # third is the always-true guard" and then never attacked that
        # conjunct. This rival replaces it with a real order relation, so the
        # case split has no catch-all clause at all.
        "module": _impl(_rival(
            "    -- The FINAL guard is a real order relation rather than the\n"
            "    -- always-true catch-all, so the case split has no exhaustive\n"
            "    -- last clause.",
            g3="(Expr.le x b)")),
        "refinement": "a real counterpart whose last clause carried an order "
                      "relation instead of the always-true guard would build a "
                      "case split that is not exhaustive: above the upper "
                      "endpoint every clause's condition is false, so the "
                      "cumulative distribution has no value there at all "
                      "instead of the saturated one. The failing test compares "
                      "the whole object structurally, including each clause's "
                      "condition, and the always-true guard is a different node "
                      "from an order relation, so it would NOT resolve.",
        "rationale": "REJECT from Q1 via the GUARDS sub-behaviour's THIRD "
                     "conjunct — the one every other rival leaves gold: the "
                     "target object's final guard is the always-true node, the "
                     "rival's is the non-strict order relation, so the trees "
                     "differ at every operand triple. Without this case the "
                     "battery asserted a sub-behaviour it never probed. Refuted "
                     "at (30, 31, 32).",
        "witness": _witness("(Expr.natLit 30)", "(Expr.natLit 31)",
                            "(Expr.natLit 32)"),
    },
    {
        "id": "weak-clause-order-permuted",
        "kind": "uniqueness",
        "expect": "reject",
        # STRUCTURE (clause ORDER): keep all three values, all three guards and
        # the whole middle expression, and only permute WHICH SLOT each value
        # occupies. No existing rival perturbs ordering — every one of the
        # twelve changes a value, a guard or a sub-node in place — so a rival
        # that merely mis-sequences correct clauses was unattacked. Ordering is
        # load-bearing for a case split, whose clauses are tried in order.
        "module": _impl(_rival(
            "    -- The clauses are mis-sequenced: the saturated tail is tried\n"
            "    -- before the closed form, which lands in the final slot. Every\n"
            "    -- value and every guard is otherwise the intended one.",
            order="mid_last")),
        "refinement": "a real counterpart that emitted the clauses in this "
                      "order would be evaluated top-down, so on the support the "
                      "saturated value would be selected before the closed form "
                      "was ever reached — the closed form becomes dead code and "
                      "the cumulative distribution saturates immediately above "
                      "the lower endpoint. The failing test asserts the case "
                      "split's clauses in their intended sequence, and a "
                      "permuted sequence is a different tree, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from Q1 on clause ORDER, a structural dimension no "
                     "other rival touches: all three clause values and all "
                     "three guards are exactly gold's, and only the slots they "
                     "occupy are permuted, so this is not subsumed by any "
                     "value, guard or sub-node rival. A case split's clauses are "
                     "tried in order, so ordering is load-bearing. Refuted at "
                     "(33, 34, 35).",
        "witness": _witness("(Expr.natLit 33)", "(Expr.natLit 34)",
                            "(Expr.natLit 35)"),
    },
    {
        "id": "weak-upper-endpoint-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # BINDER: never consult the upper endpoint at all — take the support width
        # and the second guard from the evaluation point, so `b` does not appear in
        # the result. Pins that the `b` binder is load-bearing.
        "module": _impl(
            "    -- The support width and the second guard are taken from the\n"
            "    -- evaluation point, so the upper endpoint never enters the result.\n"
            "    let onSupport : Expr :=\n"
            "      Expr.div\n"
            "        (Expr.mul (Expr.natLit 2)\n"
            "          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub x a)))))\n"
            "        Expr.pi\n"
            "    return Expr.piecewise3\n"
            "      Expr.zero (Expr.lt x a)\n"
            "      onSupport (Expr.le x x)\n"
            "      Expr.one Expr.top"),
        "refinement": "a real counterpart that never consulted the distribution's "
                      "upper endpoint would normalise the displacement by itself "
                      "and test the support membership against the evaluation "
                      "point, producing a cumulative distribution independent of "
                      "where the support ends — the same object for every upper "
                      "endpoint. The failing test asserts an object in which the "
                      "upper endpoint appears in both the width and the second "
                      "guard, so it would NOT resolve.",
        "rationale": "REJECT from Q1 on the ``b`` BINDER: `arcsinExprCdf` mentions "
                     "the upper endpoint in both the support width and the second "
                     "guard, and the rival's output mentions it nowhere, so the "
                     "trees differ whenever the upper endpoint is not the "
                     "evaluation point. This is the rival a battery that varied "
                     "only the other two binders would miss. Refuted at (0, 7, 1) "
                     "— the only witness whose lower endpoint and evaluation point "
                     "are both rational constants, isolating the upper endpoint.",
        "witness": _witness("Expr.zero", "(Expr.natLit 7)", "Expr.one"),
    },
    {
        "id": "weak-lower-endpoint-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        # BINDER: never consult the lower endpoint — treat it as the rational zero
        # in the displacement, the width and the first guard. The mirror of the
        # previous rival, pinning that the `a` binder is load-bearing.
        "module": _impl(
            "    -- The displacement, the support width and the first guard are taken\n"
            "    -- as if the lower endpoint were the rational zero, so the actual\n"
            "    -- lower endpoint never enters the result.\n"
            "    let onSupport : Expr :=\n"
            "      Expr.div\n"
            "        (Expr.mul (Expr.natLit 2)\n"
            "          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x Expr.zero)\n"
            "            (Expr.sub b Expr.zero)))))\n"
            "        Expr.pi\n"
            "    return Expr.piecewise3\n"
            "      Expr.zero (Expr.lt x Expr.zero)\n"
            "      onSupport (Expr.le x b)\n"
            "      Expr.one Expr.top"),
        "refinement": "a real counterpart that hard-coded the lower endpoint to "
                      "the rational zero would be correct only for the "
                      "default-parameter instance of this distribution and wrong "
                      "for every shifted support — the displacement, the width and "
                      "the below-support guard would all ignore where the support "
                      "actually begins. The failing test instantiates the "
                      "distribution with SYMBOLIC endpoints and asserts an object "
                      "in which the lower endpoint appears, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from Q1 on the ``a`` BINDER: `arcsinExprCdf` mentions "
                     "the lower endpoint in the displacement, the width and the "
                     "first guard, and the rival replaces all three occurrences "
                     "with the rational zero, so the trees differ whenever the "
                     "lower endpoint is not that constant. Mirror of the "
                     "upper-endpoint rival; correct on the whole sub-domain where "
                     "the lower endpoint IS zero, so a true partial-domain attack. "
                     "Refuted at (5, π, 1−0) — the only witness whose evaluation "
                     "point is a COMPOUND node, exercising the binder at a "
                     "non-atomic operand.",
        "witness": _witness("(Expr.natLit 5)", "Expr.pi",
                            "(Expr.sub Expr.one Expr.zero)"),
    },
]


# ===========================================================================
# SIBLING -> VELVET ACCOUNTING. The sibling battery has 11 SPEC cases (3
# soundness positives, 1 admissibility, 7 uniqueness rivals) plus 2 AXIOM_TESTS.
#
# CARRIER NARROWING. The sibling contracts TWO functions over an integer TAG
# carrier: a dispatch taking a family tag and a query-mode flag and returning a
# small code, plus the closed-form supplier it calls under a precondition. This
# bundle models only the purely functional core the change actually adds — the
# CONSTRUCTION of the closed-form object — as one method over a symbolic
# expression carrier, with no precondition and one postcondition clause Q1.
# The dispatch (which branch is taken for which family and query mode) is
# UNCHANGED code here and is not modeled at all, so every sibling case whose
# rival perturbs the DISPATCH has no counterpart. Conversely the object's
# internal structure — invisible on the sibling's tag carrier, where the whole
# closed form is a single opaque code — is what this bundle can attack, and the
# rivals below are aimed there. Case count is NOT parity and should not be:
# 14 rivals against the sibling's 7 is the same adversarial argument re-aimed at
# the surface this bundle models.
#
#   sibling case                 -> here                             disposition
#   ---------------------------------------------------------------------------
#   pos-control-guard-reorder    -> pos-model-direct                 PORTED
#   pos-control-local-reshape    -> pos-subnode-lets                 PORTED
#   pos-control-cff-local        -> (folded into the two above)      MERGED
#   admiss-f2p-arcsin-default    -> admiss-f2p-operands              PORTED (re-aimed)
#   uniq-prepatch-integral       -> weak-prechange-integral          PORTED
#   uniq-cff-returns-integral    -> weak-prechange-integral          MERGED
#   uniq-always-arcsin           -> (none)                           NOT MODELED
#   uniq-ignore-default          -> (none)                           NOT MODELED
#   uniq-other-gets-closedform   -> (none)                           NOT MODELED
#   uniq-nonterm-loop            -> (none)                           REJECTED, UNSHIPPABLE
#   uniq-nonterm-recursion       -> (none)                           REJECTED, UNSHIPPABLE
#   (no sibling counterpart)     -> weak-offset-reversed             ADDED
#   (no sibling counterpart)     -> weak-width-reversed              ADDED
#   (no sibling counterpart)     -> weak-scale-dropped               ADDED
#   (no sibling counterpart)     -> weak-function-nesting-swapped    ADDED
#   (no sibling counterpart)     -> weak-root-dropped                ADDED
#   (no sibling counterpart)     -> weak-lower-guard-nonstrict       ADDED
#   (no sibling counterpart)     -> weak-upper-guard-strict          ADDED
#   (no sibling counterpart)     -> weak-lower-guard-flipped         ADDED
#   (no sibling counterpart)     -> weak-tails-swapped               ADDED
#   (no sibling counterpart)     -> weak-upper-endpoint-ignored      ADDED
#   (no sibling counterpart)     -> weak-lower-endpoint-ignored      ADDED
#   (no sibling counterpart)     -> weak-final-guard-conditional     ADDED (audit)
#   (no sibling counterpart)     -> weak-clause-order-permuted       ADDED (audit)
#   AXIOM_TESTS (2)              -> (none)                           OUT OF LANE
#
# ADDED (audit). The last two rivals were landed by the audit pass, which found
#   the battery DECLARING two sub-behaviours it never probed: the third guard
#   (every original rival left the always-true node gold) and the clause ORDER
#   (every original rival changed a value, a guard or a sub-node in place, so a
#   rival holding all nine of those fixed and permuting only the slots was
#   unattacked). Both were confirmed rejected with real builds, each with a
#   witness that elaborates on its rival (exit 0), fails on gold (exit 1) with an
#   evaluated `arcsinCdfBuildTester <a> <b> <x> = false ... is false`, and whose
#   flipped claim builds clean on gold (exit 0).
#
# MERGED. The sibling's third positive reshapes its SECOND contracted function,
#   which is not modeled here, so its "a faithful reshape of the closed-form
#   supplier must verify" argument is carried by the two positives above, which
#   reshape the one modeled construction. Its uniq-cff-returns-integral rival
#   corrupts that same second function so the integral fallback reaches the
#   dispatch; on this carrier the only way to express "the closed form is not
#   supplied" is to return the definite-integral object, which IS
#   weak-prechange-integral. Not dropped — collapsed onto the same rival because
#   the two really do fail at the same input for the same reason.
#
# NOT MODELED (3 sibling rivals). uniq-always-arcsin, uniq-ignore-default and
#   uniq-other-gets-closedform all perturb the DISPATCH: which families and which
#   query modes get the closed form rather than the integral fallback. That
#   dispatch is UNCHANGED code, has no counterpart in this bundle's model (there
#   is no family tag and no query-mode binder in `arcsinCdfBuild`'s signature),
#   and the third of them is rejected on the sibling by a PRECONDITION this
#   method does not have. Fabricating a family/query binder to host them would
#   model a behaviour this bundle does not contract. Legitimately omitted by
#   carrier narrowing, not for difficulty.
#
# REJECTED BUT UNSHIPPABLE (the divergence lane, 2 sibling rivals). This bundle
#   sets `loom.semantics.termination "total"`, under which a postcondition is
#   claimed of ALL runs rather than only terminating ones, so every loop owes a
#   strictly decreasing measure and a diverging rival is REJECTED. (An earlier
#   version of this entry placed the bundle in a `total` cohort against a
#   `partial` one where such a rival satisfies every `ensures` vacuously,
#   citing an internal findings doc. That census is withdrawn: all 500 velvet
#   bundles set "total", and the `set_option` elaborator itself runs
#   `openScope `TotalCorrectness`
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so the option and the `open`
#   cannot disagree.) Confirmed with a real build: a variant that loops without a
#   decreasing measure before returning the correct object is rejected with
#   `error: Decreasing annotations are required in total correctness semantics`.
#   So the spec DOES close this class and there is no hole to report.
#   It is nonetheless not shippable as an expect="reject" case, and the reason is
#   MEASURED rather than argued — "no witness can be built" is the claim that has
#   most often been wrong elsewhere, so it was tested directly. The witness
#   contract requires a snippet that ELABORATES against the rival. Against the
#   diverging rival a TRIVIAL, spec-independent witness
#
#       example : (1 : Nat) + 1 = 2 := by decide
#
#   fails (exit 1) with
#       error: Decreasing annotations are required in total correctness semantics
#   reported at the METHOD's own line, i.e. the linter rejects the file before any
#   appended witness is elaborated at all. The SAME trivial witness builds clean
#   (exit 0) against the frozen solution and against a rival that keeps a
#   TERMINATING `while` loop with a `decreasing` clause — so the blocker is
#   specifically the missing measure, not loops, not the carrier, and not the
#   witness's own content. No witness whatsoever can clear the rival half, which
#   is what makes the class unshippable rather than merely hard: the gate would
#   record `witness-unproven` (inconclusive, forcing MALFORMED-TESTS) for a rival
#   the spec genuinely refutes, turning a real strength into a gate error. Class
#   closed by the `total` setting, mechanically verified; omitted for a protocol
#   limitation on a rival that produces no value, not for difficulty and not for
#   a gap in the spec.
#
#   A loop-bearing rival is separately NOT witnessable by `decide` on this
#   carrier even when it terminates: measured on a terminating-loop rival with a
#   WRONG output, the tester witness fails on the rival with `did not reduce to
#   isTrue or isFalse`, and `decide +kernel` and `simp`-first variants fail the
#   same way. So the reject lane here is necessarily loop-free, which is what
#   every shipped rival is. Recorded so a later port does not mistake the
#   loop-free shape for an unexamined choice.
#
# OUT OF LANE (AXIOM_TESTS). The sibling's 2 axiom probes re-run its deep-model
#   grounding against the real library. This gate ignores AXIOM_TESTS; here that
#   grounding is G-CONF's job (`conformance_check.py`, recorded pass over 100002
#   configurations) and this bundle's `axioms` region is empty besides.
#
# VACUOUS (frame / permission-mutation). The sibling records this class as
#   already vacuous on its own backend (both its inputs are pass-by-value scalars
#   with no heap permission, so there is no read-only input to overwrite). It is
#   vacuous here a fortiori: Velvet is referentially transparent, all three
#   operands are immutable `Expr` values, and the method declares no `mut`
#   binder. No substitute probe is fabricated.
#
# WITNESS DISTINCTNESS — 14 rivals, 14 DISTINCT operand triples, pts=14. All
# three binders are varied, and each is additionally exercised at a carrier node
# that is not an integer literal, so no binder is silently pinned to one shape:
#
#   rival                          (a, b, x)                    binder stressed
#   ---------------------------------------------------------------------------
#   weak-prechange-integral        (1, 2, 3)                    shape (all three)
#   weak-offset-reversed           (3, 4, 5)                    a vs x order
#   weak-width-reversed            (6, 7, 8)                    a vs b order
#   weak-scale-dropped             (0, 9, 1)                    a = rational zero
#   weak-function-nesting-swapped  (18, 19, 20)                 middle-clause nesting
#   weak-root-dropped              (21, 22, 23)                 middle-clause node
#   weak-lower-guard-nonstrict     (11, 12, 13)                 first-guard relation
#   weak-upper-guard-strict        (14, 15, π)                  x = circle constant
#   weak-lower-guard-flipped       (24, 25, 26)                 first-guard operands
#   weak-tails-swapped             (16, 1, 17)                  b = rational unit
#   weak-upper-endpoint-ignored    (0, 7, 1)                    b alone (a, x constants)
#   weak-lower-endpoint-ignored    (5, π, 1−0)                  a alone; x compound
#   weak-final-guard-conditional   (30, 31, 32)                 third-guard node
#   weak-clause-order-permuted     (33, 34, 35)                 clause slots
#
# No witness binds a hypothesis: the carrier is fully transparent (a DecidableEq
# inductive, empty axioms region), so every refutation is stated at literal
# operands and reduces under `decide`. Conditioning on the carrier — and the
# joint-satisfiability question it raises — does not arise on this bundle.
#
# COVERAGE. The single obligation (`prove_correct arcsinCdfBuild`) is DEFENDED by
# two soundness positives plus the admissibility case, and ATTACKED by fourteen
# rivals. Its single top-level clause Q1 is not decomposable into independent
# conjuncts syntactically — it is one equation between expression trees — so
# coverage is measured against the seven structural sub-behaviours that equation
# pins, and each is attacked: SHAPE (weak-prechange-integral), OFFSET
# (weak-offset-reversed, weak-lower-endpoint-ignored), WIDTH
# (weak-width-reversed, weak-upper-endpoint-ignored), SCALE (weak-scale-dropped,
# weak-function-nesting-swapped, weak-root-dropped), GUARDS
# (weak-lower-guard-nonstrict, weak-upper-guard-strict,
# weak-lower-guard-flipped, weak-final-guard-conditional — the last covering the
# third guard, which the first three leave gold), TAILS (weak-tails-swapped) and
# ORDER (weak-clause-order-permuted). There is no precondition to defend. Every
# witness was confirmed out-of-band to elaborate against its rival and fail on
# the frozen solution.
#
# SPEC-TOO-WEAK PROBES that FAILED to find a hole (audit pass; recorded because a
# probe that found nothing is evidence about the spec, and re-running it is the
# only way to learn that otherwise). Four further wrong impls were built and all
# four were REJECTED, so none is a spec hole: the final guard replaced by an
# order relation; the clause slots permuted; the middle clause's division
# INVERTED (circle constant over the doubled inverse-sine term); and the scaling
# literal given the wrong VALUE (the small-integer node 3 rather than 2, i.e. a
# same-constructor different-payload attack that no shipped rival makes). The
# first two were good enough to ship and are now cases above; the latter two are
# subsumed by SCALE rivals already present and were not added, having produced no
# new information. No correct reshape was found that the spec rejects for a
# reason other than the carrier-granularity limit recorded in the module
# docstring, and that limit can only reject a faithful impl, never accept a wrong
# one.
AXIOM_TESTS = []
