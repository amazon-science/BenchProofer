"""properties.py — G-PBT falsification battery for sympy__sympy-20801 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct equalsOperand`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation. It is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over an inductive right-hand operand,
``Int × Operand → Bool``):

  equalsOperand (selfVal : Int) (o : Operand) return (out : Bool)
    ensures out = floatEq selfVal o          -- THE load-bearing clause

The method decides equality of a finite-precision value ``selfVal`` (its exact
value; the zero value is ``0``) against a right-hand operand classified into
three kinds:

  * ``logical b``  — a logical constant: values of incomparable kind, NEVER
                     equal, unconditionally ``false``;
  * ``numeric m``  — a number: equal exactly when the values are equal
                     (``decide (selfVal = m)``);
  * ``symbolic t`` — any other expression: equal exactly when the value is the
                     zero value AND the expression is falsy
                     (``if selfVal = 0 then !t else false``).

``floatEq`` is a total, fully-unfolded pure function of the method's own inputs
in the ``pure`` region. The ``axioms`` region is EMPTY; there is no opaque answer
key to echo (directive 8 — the post-image is grounded in the actual inputs). The
clause decomposes into independently-attackable structural sub-behaviours, one
per operand kind (with a ``selfVal = 0`` split inside the symbolic kind):

  * LOGICAL   — the logical-constant kind is unconditionally ``false``; the fix
                relocates a leading zero-value short circuit PAST this branch so
                that a zero value against a falsy logical constant is settled by
                THIS branch (false), not by the short circuit (which would report
                equality). This is the F2P discriminator.
  * NUMERIC   — the number kind is the exact value comparison ``selfVal = m``.
  * SYMBOLIC-ZERO    — a zero value against another expression is equal only when
                the expression is falsy (``!t``).
  * SYMBOLIC-NONZERO — a non-zero value against another expression is NEVER equal
                (``false``), i.e. the zero-value short circuit does not fire.

The NUMERIC sub-behaviour splits once more, and the split matters because a rival
can be wrong on one half only: the EQUAL-values half (``selfVal = m``, where the
verdict is ``true``) and the UNEQUAL-values half (``selfVal ≠ m``, where it is
``false``). An INVERTING rival is refuted on the first; only an OVER-PERMISSIVE
one is refuted on the second. Both halves carry a rival.

TWO input binders, both free; the post-image must hold for every value of each:
  * ``selfVal`` — the exact value (the ``selfVal = 0`` split governs both the
                  logical F2P discriminator and the symbolic two-arm split);
  * ``o``       — the operand: its kind (logical/numeric/symbolic), its numeric
                  value ``m``, and its truth field ``b``/``t``.
There is NO precondition (the ``pre-conditions`` region is empty), so every input
is in domain — a witness need not respect any ``require`` clause.

ADVERSARIAL READ of the nagini classes on this carrier (see the footer for the
case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling already records this
    class as not constructible: every input is a pass-by-value primitive with no
    heap permission (``has_readonly_input == False``). Lean/Velvet are
    referentially transparent a fortiori: both inputs are immutable values, the
    method declares no ``mut`` binder, there is no heap and no aliasing. No
    substitute probe is fabricated (per the porting map, this class is
    legitimately dropped rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``floatEq selfVal o`` — a concrete ``def`` over the method's own
    arguments (empty ``axioms`` region; no opaque callee). The only satisfier is
    the grounded classification itself; there is nothing to echo.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. Each rival gets the SHAPE right
    (a Bool per input) and is correct on part of the domain, but diverges on one
    structural sub-behaviour above.
  * DIVERGENCE (non-termination) — the nagini sibling ships a MANDATORY
    ``uniq-diverge-loop`` case (its ``atk_7``). On THIS bundle BOTH forms of the
    class are REJECTED BY THE SPEC, so it is not a portable witnessed reject and
    not a hole either. The measure-LESS form is refused at elaboration (this
    bundle reads ``termination "total"``, which also opens ``TotalCorrectness``),
    and the measure-CARRYING form (the sharper one, which cannot be dismissed as
    merely missing the annotation) is refused on the measure's own descent goal
    (measured on this cell: ``⊢ 0 < 0``). It ships no case only because a rival
    whose module fails to compile admits no elaborating witness. See the
    DIVERGENCE notes in the footer, which record both with builds and retract an
    earlier claim that the annotated form verifies.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is LOOP-FREE (a single ``match``
over the operand kind), so its extracted tester reduces under ``decide``. Each
reject rival is likewise a loop-free expression, so its tester also ``decide``s.
Each reject rival therefore carries a machine-checked refutation ``witness`` — a
Velvet tester statement ``equalsOperandTester selfVal o = false`` at ONE concrete
input, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (the tester
``decide``s to ``false`` — the rival's output violates the postcondition there)
and FAILS against the frozen solution (gold's tester ``decide``s to ``true``, so
``= false`` is refuted), so each rejection is a genuine spec refutation and not
mechanical tactic breakage. There is no precondition, so no witness input is
vacuously excluded.

The gold-side failure is a SEMANTIC refutation in every case, not a stuck
reduction: the error reads ``Tactic `decide` proved that the proposition ... is
false``, i.e. the kernel evaluated the claim and rejected it. Re-measured by the
SECOND independent audit, which rebuilt all 14 witness builds from this manifest
(7 rival, exit 0 each; 7 gold, exit 1 each, every one carrying that same
evaluated-and-rejected signature) and ran the FORGERY pair on all seven: the
flipped claim (``... = true``) against the frozen solution ELABORATES, exit 0,
for every case. So gold's tester really does reduce here and each exit code
TRACKS THE CLAIM rather than reflecting an irreducible term — the two builds, not
the reading of the error text, are what establish that.

The positive control was additionally checked NOT to be definitionally equal to
the frozen impl (``example : gold = reorder := rfl`` FAILS with a type mismatch),
so it is a genuine reshape the tactic must re-close rather than the frozen term
under another spelling. The admissibility assert was checked LIVE by negating its
first conjunct (``floatEq 0 (Operand.logical false) = true``): exit 1,
``unsolved goals``, so a false claim there does not pass.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references;
the whole computation is concrete arithmetic and constructor matching over the
inputs. Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20801"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN `-- impl-start`
# and `-- impl-end` that carries the dispatch (the leading comment lines and the
# markers themselves stay put). Every rival and reshape edits ONLY this block
# (and, for reshapes, the elided `prove_correct` tactic body), so the spec view
# is untouched and same_spec holds by construction.
_IMPL = (
    "    match o with\n"
    "    | .logical _   => pure false\n"
    "    | .numeric m   => pure (decide (selfVal = m))\n"
    "    | .symbolic t  => pure (if selfVal = 0 then !t else false)"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# elided from the spec view); rivals leave it as `loom_solve`, so the wrong impl
# leaves the postcondition goal unsolved and the rival MODULE fails to build —
# which is what expect="reject" requires. The witness, not the module build, is
# what attributes the rejection to the spec.
_PROOF = "prove_correct equalsOperand by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `equalsOperandTester selfVal o = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict; both the rival and the frozen impl are loop-free, so
# ---- both testers reduce under `decide`.
def _witness(call):
    return ("extract_program_for equalsOperand\n"
            "prove_precondition_decidable_for equalsOperand\n"
            "prove_postcondition_decidable_for equalsOperand\n"
            "derive_tester_for equalsOperand\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify, else SPEC-TOO-STRONG. The three match arms are REORDERED
    # (number and other-expression settled before the logical constant), the
    # opposite of the frozen kind order. Observationally identical on every
    # input, so `out = floatEq selfVal o` holds on the whole domain and the
    # frozen proof (`loom_solve`) still closes the byte-identical obligation.
    # Verified out-of-band with a real build.
    # =====================================================================
    {
        "id": "pos-match-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Reordered dispatch: settle the number and other-expression\n"
            "    -- kinds before the logical constant. Observationally identical.\n"
            "    match o with\n"
            "    | .numeric m   => pure (decide (selfVal = m))\n"
            "    | .symbolic t  => pure (if selfVal = 0 then !t else false)\n"
            "    | .logical _   => pure false"),
        "rationale": "structurally different CORRECT impl: the three match arms "
                     "are reordered (number/other-expression before the logical "
                     "constant), the opposite of the frozen order. A `match` is "
                     "total and order-insensitive, so the verdict is identical on "
                     "every input and `out = floatEq selfVal o` holds on the whole "
                     "domain. A faithful reshape MUST verify, else the "
                     "postcondition is SPEC-TOO-STRONG.",
    },
    # =====================================================================
    # ADMISSIBILITY — the nagini sibling's admissibility probe re-establishes
    # that the discriminating F2P-shaped input is admitted and lands on the
    # load-bearing verdict. There is no precondition here (nothing to admit), so
    # the residual admissibility risk is NON-DEGENERACY: that the post-image on
    # the F2P-shaped input is the fix's verdict (a zero value vs a falsy logical
    # constant is NOT equal) AND the symbolic zero arm is genuinely non-constant
    # (equal to a falsy other, unequal to a truthy other) rather than a collapse.
    # Pinned by ONE in-region assert; the impl is kept verbatim so the method's
    # own obligation still discharges. The frozen proof closes the extra assert
    # goal too (`loom_solve` alone). The assert is LIVE (a false claim leaves an
    # unsolved goal — verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- Non-degeneracy at the discriminating F2P-shaped input: the\n"
            "    -- zero value against a falsy logical constant is NOT equal (the\n"
            "    -- fix), and the zero-value/other-expression arm is non-constant\n"
            "    -- (equal to a falsy other, unequal to a truthy other).\n"
            "    assert (with_name_prefix `admiss\n"
            "      (floatEq 0 (Operand.logical false) = false ∧\n"
            "       floatEq 0 (Operand.symbolic false) = true ∧\n"
            "       floatEq 0 (Operand.symbolic true) = false))\n"
            "    match o with\n"
            "    | .logical _   => pure false\n"
            "    | .numeric m   => pure (decide (selfVal = m))\n"
            "    | .symbolic t  => pure (if selfVal = 0 then !t else false)"),
        "rationale": "there is no precondition to admit, so the admissibility "
                     "residual is NON-DEGENERACY: the post-image at the "
                     "F2P-shaped input (zero value vs a falsy logical constant) is "
                     "the fix's verdict `false`, and the zero-value/other arm is "
                     "genuinely non-constant (true for a falsy other, false for a "
                     "truthy other) rather than a constant collapse. The in-region "
                     "assert must discharge (a false claim leaves an unsolved "
                     "goal); the impl is kept verbatim so the method's own "
                     "`ensures` discharges too. Must verify.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is a loop-free
    # expression so its extracted tester `decide`s; the frozen spec is untouched.
    # =====================================================================
    {
        "id": "uniq-prepatch-zero-short-circuit-first",
        "kind": "uniqueness",
        "expect": "reject",
        # THE gold bug: the zero-value short circuit is placed FIRST, before the
        # operand kind is examined, returning the negation of the operand's truth
        # for every kind. For a zero value against a falsy logical constant it
        # returns `not false == true` instead of the constant false. Correct on
        # every other input.
        "module": _impl(
            "    -- Pre-fix order: the zero-value short circuit fires BEFORE the\n"
            "    -- operand kind is examined, negating the operand truth for every\n"
            "    -- kind. On a zero value vs a falsy logical constant it reports\n"
            "    -- equality.\n"
            "    let otherTruth : Bool :=\n"
            "      match o with\n"
            "      | .logical b   => b\n"
            "      | .numeric m   => decide (m ≠ 0)\n"
            "      | .symbolic t  => t\n"
            "    if selfVal = 0 then\n"
            "      pure (!otherTruth)\n"
            "    else\n"
            "      match o with\n"
            "      | .logical _   => pure false\n"
            "      | .numeric m   => pure (decide (selfVal = m))\n"
            "      | .symbolic _  => pure false"),
        "refinement": "this IS the pre-fix behaviour: the zero-value short circuit "
                      "sits at the FRONT of the equality dispatch, before the "
                      "logical-constant branch. The faithful real patch (this "
                      "order) makes a zero value compared with a falsy logical "
                      "constant report equality — exactly the reported bug — so the "
                      "F2P assertion that this comparison is False FAILS and the "
                      "instance is NOT resolved.",
        "rationale": "REJECT from `out = floatEq selfVal o` on the LOGICAL "
                     "sub-behaviour: floatEq pins the logical-constant verdict to "
                     "the constant false, but the relocated short circuit returns "
                     "`!b`, which differs at selfVal=0 and a falsy logical "
                     "constant. Refuted at selfVal=0, o=logical false: gold false, "
                     "rival true. Discrimination comes from selfVal=0 AND the "
                     "logical kind — the F2P discriminator.",
        "witness": _witness("equalsOperandTester 0 (Operand.logical false)"),
    },
    {
        "id": "uniq-logical-echoes-truth",
        "kind": "uniqueness",
        "expect": "reject",
        # The logical-constant branch echoes the operand's truth value instead of
        # the constant false. Wrong whenever the logical constant is truthy.
        # Present branch, wrong value (distinct from the prepatch rival, where the
        # branch is skipped entirely).
        "module": _impl(
            "    match o with\n"
            "    | .logical b   => pure b\n"
            "    | .numeric m   => pure (decide (selfVal = m))\n"
            "    | .symbolic t  => pure (if selfVal = 0 then !t else false)"),
        "refinement": "for a logical constant the gold returns the constant False "
                      "unconditionally. This rival instead returns the constant's "
                      "own truth value. The faithful real patch (return the "
                      "operand's truthiness on the logical branch) makes a value "
                      "spuriously equal to a truthy logical constant, so the "
                      "logical-comparison tests (the F2P and the bool-equality "
                      "P2P tests) diverge from the gold result and it would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = floatEq selfVal o` on the LOGICAL "
                     "sub-behaviour: floatEq pins the logical branch to false, the "
                     "rival returns `b`, differing whenever b is true. Distinct "
                     "from the prepatch rival: here the logical branch is present "
                     "but returns the wrong value rather than being skipped. "
                     "Refuted at selfVal=5, o=logical true: gold false, rival true. "
                     "Discrimination comes from a NON-zero selfVal (so the branch "
                     "is not confounded with the zero short circuit) and a truthy "
                     "logical constant.",
        "witness": _witness("equalsOperandTester 5 (Operand.logical true)"),
    },
    {
        "id": "uniq-numeric-negated",
        "kind": "uniqueness",
        "expect": "reject",
        # The number kind negates the exact value comparison; the logical and
        # symbolic kinds stay correct. A test that never compares against a number
        # would miss it.
        "module": _impl(
            "    match o with\n"
            "    | .logical _   => pure false\n"
            "    | .numeric m   => pure (decide (selfVal ≠ m))\n"
            "    | .symbolic t  => pure (if selfVal = 0 then !t else false)"),
        "refinement": "for a number the gold returns the exact value comparison "
                      "`selfVal = m`. This rival negates ONLY the number kind. The "
                      "faithful real patch (negate the exact value comparison) "
                      "inverts every number-vs-number equality verdict, so the "
                      "value-equality tests (Float == Float / Float == Rational, "
                      "idempotence) FAIL and the instance is NOT resolved. A test "
                      "that never compares against a number would miss this.",
        "rationale": "REJECT from `out = floatEq selfVal o` on the NUMERIC "
                     "sub-behaviour: floatEq is `decide (selfVal = m)`, the rival "
                     "`decide (selfVal ≠ m)`, disagreeing on the whole number kind. "
                     "Refuted at selfVal=3, o=numeric 3: gold true (equal values), "
                     "rival false. Discrimination comes from the numeric kind with "
                     "selfVal = m — the equal-values sub-domain no other rival "
                     "probes.",
        "witness": _witness("equalsOperandTester 3 (Operand.numeric 3)"),
    },
    {
        "id": "uniq-symbolic-zero-drops-negation",
        "kind": "uniqueness",
        "expect": "reject",
        # For a zero value against another expression the gold returns `!t` (equal
        # only when the expression is falsy). This rival returns `t`, inverting the
        # whole zero-value/other verdict. The non-zero arm stays correct.
        "module": _impl(
            "    match o with\n"
            "    | .logical _   => pure false\n"
            "    | .numeric m   => pure (decide (selfVal = m))\n"
            "    | .symbolic t  => pure (if selfVal = 0 then t else false)"),
        "refinement": "for a zero value against another expression the gold "
                      "returns `not other` (equal only to a falsy expression). "
                      "This rival returns `other`, inverting the verdict: the zero "
                      "value becomes equal to a TRUTHY expression and unequal to a "
                      "falsy one. The faithful real patch (`return other` rather "
                      "than `return not other` in the relocated block) breaks the "
                      "zero-comparison behaviour in the opposite direction, so the "
                      "general value-vs-expression equality tests diverge and it "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = floatEq selfVal o` on the SYMBOLIC-ZERO "
                     "sub-behaviour: floatEq returns `!t` when selfVal=0, the rival "
                     "returns `t`, disagreeing on the whole zero-value/other "
                     "domain. Refuted at selfVal=0, o=symbolic true: gold false, "
                     "rival true. Discrimination comes from selfVal=0 with a truthy "
                     "symbolic operand — the zero half of the symbolic split.",
        "witness": _witness("equalsOperandTester 0 (Operand.symbolic true)"),
    },
    {
        "id": "uniq-symbolic-nonzero-drops-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # For another expression the rival drops the selfVal=0 guard and returns
        # `!t` unconditionally. The zero arm stays correct; a NON-zero value
        # against a falsy expression spuriously reports equality.
        "module": _impl(
            "    match o with\n"
            "    | .logical _   => pure false\n"
            "    | .numeric m   => pure (decide (selfVal = m))\n"
            "    | .symbolic t  => pure (!t)"),
        "refinement": "for a NON-zero value against another expression the gold "
                      "falls through to False (the zero-value short circuit does "
                      "not fire). This rival drops the selfVal=0 guard and returns "
                      "`not other` unconditionally, so a non-zero value against a "
                      "falsy expression spuriously reports equality. The faithful "
                      "real patch (remove the `if not self` guard so `return not "
                      "other` runs unconditionally) makes a non-zero value equal "
                      "to a falsy non-number, so the general value-vs-expression "
                      "equality tests diverge and it would NOT resolve.",
        "rationale": "REJECT from `out = floatEq selfVal o` on the "
                     "SYMBOLIC-NONZERO sub-behaviour: floatEq returns false when "
                     "selfVal ≠ 0, the rival returns `!t`, disagreeing whenever the "
                     "expression is falsy. Refuted at selfVal=5, o=symbolic false: "
                     "gold false, rival true. Discrimination comes from a NON-zero "
                     "selfVal with a falsy symbolic operand — the non-zero half of "
                     "the symbolic split, disjoint from the zero-arm rival.",
        "witness": _witness("equalsOperandTester 5 (Operand.symbolic false)"),
    },
    {
        "id": "uniq-always-false-supporting",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheap supporting near-miss: every comparison is unequal. Correct on the
        # logical kind and the symbolic non-zero arm, but WRONG on a number whose
        # value matches and on the symbolic zero arm against a falsy expression.
        "module": _impl(
            "    -- Cheap near-miss: every comparison is unequal.\n"
            "    match o with\n"
            "    | .logical _   => pure false\n"
            "    | .numeric _   => pure false\n"
            "    | .symbolic _  => pure false"),
        "refinement": "cheap supporting near-miss: every comparison is unequal. "
                      "The faithful real patch (make the equality always return "
                      "False) breaks every TRUE equality — a value equal to itself, "
                      "value vs matching number, the idempotence tests — so the "
                      "value-equality P2P tests FAIL and it would NOT resolve. Kept "
                      "as a cheap supporting case, NOT a substitute for the "
                      "reasoned sub-domain rivals above.",
        "rationale": "REJECT from `out = floatEq selfVal o` on the NUMERIC "
                     "sub-behaviour (and the symbolic zero arm): floatEq returns "
                     "true for a number with matching value, the rival always "
                     "false. Refuted at selfVal=2, o=numeric 2: gold true, rival "
                     "false. (Shares the equal-numeric sub-domain with the "
                     "numeric-negated rival but at a distinct input point.)",
        "witness": _witness("equalsOperandTester 2 (Operand.numeric 2)"),
    },
    {
        "id": "uniq-numeric-widened-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # The number kind WIDENS the exact comparison: the value also counts as
        # equal to the number one above it. Both existing numeric rivals
        # (numeric-negated, always-false) are refuted only where selfVal = m, so
        # each of their witnesses AGREES with this impl; the whole
        # selfVal ≠ m half of the number kind — where an over-permissive
        # comparison lives — was unattacked before this case.
        "module": _impl(
            "    -- Widened number comparison: the value counts as equal to the\n"
            "    -- number one above it as well as to its own value, so a\n"
            "    -- NON-matching number spuriously compares equal. Correct on\n"
            "    -- every other input, and correct on the whole equal-value\n"
            "    -- sub-domain the other numeric rivals probe.\n"
            "    match o with\n"
            "    | .logical _   => pure false\n"
            "    | .numeric m   => pure (decide (selfVal = m ∨ selfVal = m + 1))\n"
            "    | .symbolic t  => pure (if selfVal = 0 then !t else false)"),
        "refinement": "for a number the gold returns the EXACT value comparison, "
                      "so distinct values are never equal — the comparison is "
                      "exact by design (a value at one precision is not equal to "
                      "the same value at another). This rival widens the "
                      "comparison to admit an adjacent value. The faithful real "
                      "patch (compare with a tolerance instead of exactly) makes "
                      "distinct numbers spuriously equal, so the exact-comparison "
                      "value-equality tests diverge from the gold result and the "
                      "instance is NOT resolved. Note the direction: this is an "
                      "over-permissive comparison, whereas the numeric-negated "
                      "rival is an inverted one.",
        "rationale": "REJECT from `out = floatEq selfVal o` on the NUMERIC "
                     "sub-behaviour, UNEQUAL-values half: floatEq is "
                     "`decide (selfVal = m)`, which is false whenever the values "
                     "differ; the rival also returns true at selfVal = m + 1. "
                     "Refuted at selfVal=4, o=numeric 3: gold false, rival true. "
                     "Discrimination comes from the numeric kind with selfVal ≠ m "
                     "— the sub-domain NO other rival probes: both other numeric "
                     "rivals are refuted only at selfVal = m (3 and 2), and this "
                     "impl agrees with gold at every one of the other five "
                     "witness points, so it survives every other witness in this "
                     "battery.",
        "witness": _witness("equalsOperandTester 4 (Operand.numeric 3)"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (1 soundness
# positive, 1 admissibility, 8 uniqueness rivals — including a divergence rival)
# plus an EMPTY AXIOM lane. This bundle models the SAME purely-functional core —
# the equality dispatch of a finite-precision value against a classified operand —
# over `Int × Operand → Bool`. The sibling's carrier distinguishes SEVEN `kind`
# values (0 truth-value, 1 irrational const, 2..5 four numeric sub-kinds, 6 other)
# with a numeric-equality input `numeric_eq`; THIS carrier collapses them to THREE
# constructors: `logical` (= sibling kind 0), `numeric` (= sibling kinds 1..5,
# since an irrational constant and every numeric sub-kind are ALL settled by the
# same exact value comparison here — the model does not distinguish them), and
# `symbolic` (= sibling kind 6, with the self_is_zero split carried as `selfVal=0`).
# That collapse is genuine carrier narrowing, not an omission — see below.
#
#   sibling case                        -> here                          disposition
#   ---------------------------------------------------------------------------------
#   pos-control-collapsed-reordered     -> pos-match-reorder             PORTED
#   admiss-f2p-witness                  -> admiss-f2p-nondegenerate      PORTED (re-aimed)
#   uniq-prepatch-zero-short-circuit... -> uniq-prepatch-zero-short-...  PORTED
#   uniq-truthvalue-echoes-numeric      -> uniq-logical-echoes-truth     PORTED (re-expressed)
#   uniq-irrational-echoes-numeric      -> (none)                        DROPPED (carrier narrowing)
#   uniq-float-kind-negated             -> uniq-numeric-negated          PORTED (widened)
#   (no sibling counterpart)            -> uniq-numeric-widened-off-by-one  ADDED (audit)
#   uniq-other-nonzero-drops-guard      -> uniq-symbolic-nonzero-drops-guard  PORTED
#   uniq-other-zero-drops-negation      -> uniq-symbolic-zero-drops-negation  PORTED
#   uniq-diverge-loop                   -> (none)                        REJECTED-BY-SPEC
#                                          (BOTH forms: measure-less refused at
#                                           elaboration, annotated form refused on
#                                           its descent goal, both measured, see
#                                           the DIVERGENCE notes)
#   uniq-always-false-supporting        -> uniq-always-false-supporting  PORTED
#   AXIOM_TESTS ([])                    -> (none)                        DROPPED (G-AX)
#   frame-mutation                      -> (none)                        VACUOUS
#
# PORTED (positive): the sibling collapses/reorders the kind ladder. Here the
#   dispatch is a single total `match`; the reshape REORDERS its three arms
#   (number/other before logical). The frozen `loom_solve` closes the
#   byte-identical obligation (verified out-of-band with a real build).
# PORTED-RE-AIMED (admissibility): the sibling asserts the precondition admits the
#   F2P-shaped input and routes it onto the load-bearing clause. THIS bundle has NO
#   precondition (empty pre-conditions region), so there is nothing to admit; the
#   re-aimed probe instead pins NON-DEGENERACY at the F2P-shaped input (the zero
#   value vs a falsy logical constant is not equal — the fix — and the symbolic
#   zero arm is non-constant). Verified out-of-band; the assert is live.
# PORTED (rivals): the sibling's sub-domain rivals port to the structural
#   sub-behaviours of `out = floatEq selfVal o`:
#     prepatch-zero-first          -> LOGICAL (the F2P discriminator, verbatim
#                                     shape as Solution_prepatch.lean's skeleton);
#     truthvalue-echoes-numeric    -> LOGICAL branch returns the operand truth `b`
#                                     instead of the constant false (re-expressed:
#                                     the sibling leaked `numeric_eq` into kind 0;
#                                     here the logical branch has no numeric_eq
#                                     input, so the faithful wrong value it could
#                                     return is the operand's own truthiness);
#     float-kind-negated           -> NUMERIC negated (WIDENED: the sibling negated
#                                     only one of four numeric sub-kinds because it
#                                     modeled them separately; this carrier has ONE
#                                     numeric kind, so negating it is the faithful
#                                     port. NOTE it does not by itself cover the
#                                     whole numeric domain: an INVERTING rival is
#                                     refuted at selfVal = m, which leaves the
#                                     selfVal ≠ m half to the added widened rival);
#     other-nonzero-drops-guard    -> SYMBOLIC-NONZERO drops the selfVal=0 guard;
#     other-zero-drops-negation    -> SYMBOLIC-ZERO drops the negation;
#     always-false                 -> supporting near-miss.
#   Each carries a machine-checked witness that ELABORATES against the rival and
#   FAILS against gold (two real builds per case).
# DROPPED (uniq-irrational-echoes-numeric): the sibling's kind 1 (an irrational
#   named constant, which the real dispatch settles as unequal WITHOUT consulting
#   any value comparison) has no counterpart here, because the `Operand` carrier
#   has no constructor that reaches it. An irrational constant has NO exact value
#   in the `Int` fragment `numeric m : Int` models — the carrier is the
#   integer-valued-number fragment, where the `Int` proxy is a faithful bijection
#   of the underlying value (mapping.md §2), and an irrational constant is
#   deliberately outside it (mapping.md §2 / conformance_check.py `operands()`
#   bridge no irrational constant, since projecting one onto an `Int` would be
#   lossy). So the sub-domain the sibling's rival attacked is not part of THIS
#   bundle's modeled domain at all, and a rival aimed at it cannot even be stated:
#   there is no `Operand` value denoting an irrational constant to make the impl
#   behave differently on.
#
#   NOTE the correction: this is a MODELED-DOMAIN boundary, not the "same numeric
#   constructor, same comparison" collapse an earlier draft of this footer
#   claimed. Those two reasons are not interchangeable — a collapse would mean the
#   behaviour is still pinned here (by uniq-numeric-negated) merely under another
#   name, whereas a domain boundary means the behaviour is genuinely ABSENT from
#   the spec's reach. The honest accounting is the latter, and its cost is
#   explicit: `floatEq`'s numeric arm claims nothing about an operand with no
#   exact integer value, so no rival in this battery can attest to the
#   irrational-constant early-exit. That is a carrier-fidelity limitation of the
#   frozen spec, recorded here rather than papered over; it is NOT a spec hole in
#   the attack-D sense (no wrong impl of the MODELED domain verifies), and closing
#   it would mean widening the frozen carrier, which is outside this lane.
#   The unchanged-numeric-callee behaviour that IS in the modeled domain stays
#   pinned by uniq-numeric-negated and uniq-numeric-widened-off-by-one, on both
#   halves of the numeric kind.
# DIVERGENCE (uniq-diverge-loop): the sibling's MANDATORY divergence case (its
#   atk_7). CORRECTED BY THE SECOND AUDIT — the previous revision of this footer
#   had the disposition AND its stated cause wrong, in a way that read as a
#   clean-looking known hole and was not.
#
#   What it said: this bundle sets `loom.semantics.termination "partial"`, so a
#   diverging impl verifies vacuously; KNOWN SPEC HOLE, nothing shippable.
#
#   What is true: this bundle's frozen `Solution.lean` line 4 reads
#   `set_option loom.semantics.termination "total"` and its line 7 reads
#   `open TotalCorrectness DemonicChoice`, with no `open PartialCorrectness`
#   anywhere in the file. It does not read "partial" (the corpus moved to total
#   semantics; 0 of 500 velvet bundles read "partial" now). So the cited reason
#   did not describe this artifact, and vacuous satisfaction is the "partial"
#   disposition, not this bundle's. MEASURED, real builds, both shapes:
#     - diverging prefix (`while True do pure ()`) then the frozen body:
#       REJECTED, exit 1, `error: Decreasing annotations are required in total
#       correctness semantics`.
#     - diverging prefix returning the NEGATION of the correct answer
#       (`pure (!(floatEq selfVal o))`): REJECTED, exit 1, same error.
#   So in the sibling's own measure-less shape the spec is STRONG here.
#
#   Why it still ships as no reject case — a witness-contract limit, not a proof
#   difficulty and not (in this shape) a spec weakness. The rejection lands on the
#   method's TERMINATION obligation, so the rival module does not compile at all
#   and no appended witness can elaborate against it. MEASURED: that rival plus
#   That is the shape with NO measure. A rival that CARRIES a measure which
#   does not decrease is refused at the ``prove_correct`` site instead, which
#   the witness file strips, so that module does elaborate; but its post-image
#   is then an unreduced ``forIn Lean.Loop.mk`` term carrying
#   ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
#   kernel will not normalise to a value a concrete-input tester can decide.
#   Both shapes therefore land ``witness-unproven``.
#   the battery's own witness shape exits 1 carrying BOTH the
#   decreasing-annotation error AND a stuck ``Tactic `decide` failed``, which the
#   gate records as `witness-unproven` — an inconclusive outcome that would fail
#   the whole battery. That is the gate behaving correctly: a diverging impl
#   returns no WRONG VALUE at any concrete input, so a value-level witness has
#   nothing to refute. Disposition: REJECTED-BY-SPEC, not expressible as a
#   witnessed case.
#
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``match`` / ``if`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness DemonicChoice``, and the two AGREE. Loom's
#   ``set_option`` elaborator is not a plain option write: it both records the
#   option AND runs ``openScope `TotalCorrectness``
#   (``Loom/MonadAlgebras/WP/Options.lean:169-186``), and Velvet's ``method``
#   macro opens the same namespace (``Velvet/Velvet/Syntax.lean:386``). So line 7
#   is REDUNDANT with line 4, not in conflict with it, and there is no
#   ``open PartialCorrectness`` anywhere in this file for a later line to
#   restore. Both namespaces define ``WPGen.forWithInvariantLoop`` and the
#   difference IS the guarantee -- the ``PartialCorrectness`` version
#   (``Loom/MonadAlgebras/NonDetT/Basic.lean:211``) takes
#   ``measure : β → Option ℕ`` and DISCARDS it, while the ``TotalCorrectness``
#   twin at :544 takes ``measure : β → Nat`` and emits ``measure b' < measure b``
#   as ``decreasing_<n>`` -- which is why the two lines have to move together,
#   and they do here. Under the total scope a postcondition is claimed of ALL runs
#   and not only of terminating ones, so a spliced loop owes that descent
#   obligation.
#   Re-measured on this bundle with real builds:
#     - a ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin``
#       is REJECTED on the measure's own goal (``case «decreasing_1: spin» ...
#       ⊢ spin < spin``);
#     - the same shape with a CONSTANT measure, i.e. ``while 0 < 1`` /
#       ``invariant True`` / ``done_with 1 < 0`` / ``decreasing (0 : Nat)``
#       spliced ahead of the frozen body with every proof reduced to a bare
#       ``loom_solve``, is REJECTED at ``⊢ 0 < 0``;
#     - dropping the clause rather than faking it is refused even earlier, by the
#       elaborator's own check (``Decreasing annotations are required in total
#       correctness semantics``).
#   So divergence neither applies to this impl nor discharges the ``ensures``
#   clauses vacuously if a rival introduces it.
#
#   THIS RETRACTS the claims this block used to carry, that
#   `while True` + `decreasing (some z : Option Nat)` (or `(none : Option Nat)`)
#   returning `!(floatEq selfVal o)` VERIFIES at exit 0, that the decrease check
#   is "switched OFF by the `open`", and that "24 of 500 velvet bundles read total
#   while opening PartialCorrectness". None of the three holds. The Option-typed
#   measure belongs to the PartialCorrectness rule's signature, which this file
#   does not use; re-attempted here, that shape does not even elaborate
#   (`Failed to parse an assertion without names: WPGen`), so it is INCONCLUSIVE
#   as a probe rather than a verifying rival, while the Nat-typed constant measure
#   in the same position IS rejected on `⊢ 0 < 0` as recorded above. The census
#   was keyed on the wrong reading of the `open` line: 496 of 500 velvet bundles
#   carry `open TotalCorrectness`, and no bundle carries a bare
#   `open PartialCorrectness` that survives a later total open.
#
#   Its faithful real patch is an equality that never returns, which hangs every
#   comparison, times out the F2P run, and does NOT resolve, so the class is out
#   of reach of a resolve-based lane too. NOT shippable as a reject case, and the
#   reason is the WITNESS CONTRACT: a reject case needs a witness that ELABORATES
#   against the rival and FAILS against gold, and a diverging rival's module does
#   not compile at all (the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester), so the first half is unreachable for any
#   witness and the gate returns ``witness-unproven`` -> INCONCLUSIVE ->
#   MALFORMED-TESTS, a failing gate rather than a rejection. Nothing is escalated
#   and no edit to the frozen `Solution.lean` is wanted: the total-correctness
#   loop rule is in force and gold satisfies it. Disposition: SPEC-CLOSED and
#   unwitnessable, with the two goals above as evidence.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job; this bundle declares no
#   axioms and no deep-model references (the dispatch is concrete arithmetic and
#   constructor matching), so there is nothing to probe and the gate ignores
#   AXIOM_TESTS regardless.
# VACUOUS (frame-mutation): the sibling already records this class as not
#   constructible (all inputs are pass-by-value primitives; has_readonly_input ==
#   False). This backend is referentially transparent and declares no `mut` binder
#   — every input is an immutable value with no heap footprint — so there is no
#   read-only field to overwrite and no substitute probe. Not fabricated.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses (pts = 7 distinct input points):
#     selfVal — 0, 5, 3, 0, 5, 2, 4: the selfVal=0 split is exercised on BOTH
#               sides (0 for the logical F2P discriminator and the symbolic zero
#               arm; 5 for the logical echo and the symbolic non-zero arm), the
#               equal-value numeric sub-domain (selfVal = m) is probed at 3 and 2,
#               and the UNEQUAL-value numeric sub-domain (selfVal ≠ m) at 4 vs 3.
#     o       — logical false, logical true, numeric 3, symbolic true, symbolic
#               false, numeric 2, numeric 3 (at selfVal 4): every constructor
#               appears; the truth field (b/t) is varied true AND false; the
#               numeric value `m` is both equal to selfVal (3, 2) and DISTINCT
#               from it (m=3 against selfVal=4).
#   Every top-level structural sub-behaviour of `out = floatEq selfVal o` is
#   attacked: LOGICAL (uniq-prepatch, uniq-logical-echoes-truth), NUMERIC on BOTH
#   halves — equal-values (uniq-numeric-negated, uniq-always-false) and
#   unequal-values (uniq-numeric-widened-off-by-one) — SYMBOLIC-ZERO
#   (uniq-symbolic-zero-drops-negation), SYMBOLIC-NONZERO
#   (uniq-symbolic-nonzero-drops-guard). No two rivals share an input tuple.
#
# AUDIT PROBES beyond the shipped cases (second audit; real builds, none is a
#   shipped case, all recorded so the coverage claims rest on measurement).
#
#   SPEC-TOO-WEAK probes (attack D) — seven NEW wrong impls aimed at what the
#   shipped rivals leave unattacked. ALL SEVEN were REJECTED (exit 1, `unsolved
#   goals` on the postcondition), so no spec hole was found in the modeled domain:
#     - numeric arm compares MAGNITUDES (`selfVal.natAbs = m.natAbs`), wrong at
#       selfVal=-3 vs numeric 3 — the negative-value sub-domain no shipped
#       witness point reaches (all seven use selfVal >= 0).       REJECTED.
#     - logical arm leaks the constant's truth ONLY at a zero value
#       (`if selfVal = 0 then b else false`) — a narrower version of the F2P bug
#       that agrees with gold at the logical-echo rival's own witness point.
#                                                                  REJECTED.
#     - symbolic guard INVERTED (`if selfVal ≠ 0 then !t else false`).  REJECTED.
#     - numeric arm makes a zero value match every number.              REJECTED.
#     - symbolic arm ignores the truth field entirely
#       (`decide (selfVal = 0)`), a collapse the non-degeneracy assert is aimed
#       at.                                                             REJECTED.
#     - logical arm returns `!b` (wrong at a FALSY logical constant, the
#       opposite polarity from the shipped logical-echo rival).          REJECTED.
#     - everything `true`, the dual of the always-false near-miss.       REJECTED.
#
#   SPEC-TOO-STRONG probes (attack E) — three NEW correct reshapes, all VERIFY at
#   exit 0 with the frozen `loom_solve` unchanged, so the spec pins VALUE and not
#   code shape:
#     - numeric arm as `if selfVal = m then true else false`, symbolic arm
#       re-associated as `if t then false else decide (selfVal = 0)`.  VERIFIES.
#     - symbolic arm as boolean algebra `(decide (selfVal = 0)) && !t`, no `if`.
#       Also checked NOT definitionally equal to gold (`rfl` fails).    VERIFIES.
#     - whole dispatch computed into a `let`-bound Bool, then `pure r`. VERIFIES.
#
#   Why the unequal-values numeric rival is not redundant (it was ADDED by the
#   independent audit, which measured the gap rather than arguing it): the two
#   pre-existing numeric rivals are both refuted only where selfVal = m, so an
#   impl that is correct on the equal-value half and over-permissive on the other
#   half AGREES with gold at all six original witness points and survived the
#   whole battery. Its witness (selfVal=4, o=numeric 3) is the point that senses
#   the exactness of the comparison in the over-permissive direction, which no
#   inverting rival can reach.
AXIOM_TESTS = []
