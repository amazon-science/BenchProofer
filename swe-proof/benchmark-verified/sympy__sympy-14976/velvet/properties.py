"""properties.py — G-PBT falsification battery for sympy__sympy-14976 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct mpfRational`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is judged by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method; no ``require`` clause — the domain is
total in all three arguments):

    mpfRational (qualified : Bool) (p : Int) (q : Int)
        return (out : String × List (String × String))
      ensures out.1 = render qualified p q
      ensures out.2 = mpfImport

with the post-image fully unfolded in the ``pure`` region:

    render qualified p q = mpfName qualified ++ "(" ++ toString p ++ ")/"
                                 ++ mpfName qualified ++ "(" ++ toString q ++ ")"
    mpfName qualified    = if qualified then "mpmath.mpf" else "mpf"
    mpfImport            = [("mpmath", "mpf")]

The two top-level ``ensures`` clauses are a conjunction of SEPARABLE structural
obligations on the rendered quotient and on the recorded import, and each is
attacked below:

  (C-wrap-num) the numerator is wrapped in a call to the backend float
               constructor — the resolved constructor spelling, then ``(``, the
               numerator's decimal text, then ``)``.
  (C-wrap-den) the denominator is wrapped the same way. This together with
               C-wrap-num is the LOAD-BEARING discriminator: the desired
               behaviour wraps BOTH parts, where the unchanged behaviour emitted
               a bare integer ratio with NEITHER wrapped, losing precision.
  (C-quotient) the two wrapped parts are joined by the division operator ``/``,
               in that position — the token that makes the rendering a quotient
               at all rather than a juxtaposition.
  (C-order)    the numerator's part comes FIRST and the denominator's second.
               A transposed rendering denotes the reciprocal.
  (C-ctor)     the constructor spelling is exactly ``mpfName qualified``; a
               truncated or otherwise different spelling names something that
               does not exist in generated code.
  (C-parens)   each part's decimal text is enclosed in parentheses, i.e. the
               constructor is APPLIED rather than merely prefixed.
  (C-sign)     each part's decimal text is that of the ARGUMENT ITSELF, sign
               included, not of its magnitude. A rendering that drops the
               numerator's sign is structurally perfect and denotes the negation
               of the intended value; it is invisible at every non-negative
               input, which is why it gets its own rival and its own negative
               witness point.
  (C-config)   the spelling is the one the AMBIENT NAME-SPELLING CONFIGURATION
               resolves the constructor's dotted name to — the module-qualified
               dotted name when qualified spellings are asked for, the bare final
               component otherwise — and the SAME spelling in both positions. A
               rendering that pins one branch regardless of the configuration
               names something the generated code cannot resolve in the other.
  (C-import)   resolving the constructor's dotted name records the import the
               generated code needs, in BOTH configurations. A rendering that
               records nothing, or records it in only one configuration, or
               records the wrong pair, leaves generated code with no binding for
               the spelling it emits.

C-config and C-import are the two clauses this battery gained when the model
stopped treating the resolver as a single constant: the resolver is
configuration-dependent and it has a recording effect, so a model that ignored
either was strictly stronger (C-config) or strictly weaker (C-import) than the
real callee. Seven rivals below aim at exactly those two clauses, and the
soundness lane gained a control that resolves the spelling by explicit case
analysis rather than through ``mpfName``, so the clause cannot be satisfied only
by naming the model's own function.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``render``, ``mpfName`` and ``mpfImport`` are concrete ``def``s in the ``pure``
region and the ``axioms`` region declares NOTHING (the rendering is modeled
deeply and validated == the real renderer by conformance_check.py /
axiom_check.py, NOT consumed as an axiom). So each rival's violation reduces to a
decidable equality of concrete ``String`` / ``List (String × String)`` values and
a witness at literal inputs discriminates it by ``decide`` — there is no opaque
callee to condition on, hence no witness binds a hypothesis and the
joint-satisfiability question does not arise. There is likewise no answer-key
term an echo could carry that satisfies the ensures yet is behaviourally wrong:
``render`` is a fully-unfolded function of ``qualified``, ``p`` and ``q``, so the
unique satisfier IS the grounded rendering.

ADVERSARIAL READ of the sibling's classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl must still verify, else the spec is
    SPEC-TOO-STRONG (over-fit to one concatenation shape, or to resolving the
    spelling through the model's own helper).
  * ADMISSIBILITY — the method has no ``require`` clause, so the sibling's
    "a normal input satisfies the precondition" probe is degenerate here. Re-aimed
    at the residual risk on a total domain: that the post-image is DEGENERATE at
    the interesting points. ``admiss-grounded`` discharges a LIVE in-region assert
    pinning BOTH configurations' renderings, separating each from the unchanged
    bare-ratio rendering, and pinning the recorded import non-empty.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling's two MANDATORY
    frame-mutation rivals write into read-only digit-carrier inputs held at
    fractional (1/2) permission and must be rejected for INSUFFICIENT PERMISSION.
    Lean and Velvet are referentially transparent: ``qualified``, ``p`` and ``q``
    are immutable values (declared read-only, not ``mut``), there is no heap and
    no aliasing, so there is no read-only input to mutate and no permission
    system to trip. Not fabricated — reported as a vacuous omission in the footer.
    The one mutable thing the real callee touches — the printer's recorded
    imports — is modeled as an OUTPUT component (the recording delta) rather than
    as a ``mut`` binder, for the reason mapping.md §2 gives: the real effect is a
    set insertion, so a list-valued ``mut`` post-state would impose an ORDER the
    real callee does not have and would reject a correct impl that recorded the
    same pair in a different position.
  * UNGROUNDED-ORACLE ECHO — N/A by construction; see CARRIER NOTE. The
    sibling's ``pos-cheapest`` control exists to record that its post-image is
    grounded rather than an opaque answer key; the same fact holds here (empty
    ``axioms`` region), and the honest positive controls that compute the
    rendering directly already discharge it.
  * DIVERGENCE / non-termination: this bundle is ``termination "total"``, so a
    postcondition is claimed of ALL runs and not only of terminating ones, and the
    whole class is CLOSED rather than a hole. Two sub-shapes, both re-measured.
    An annotation-free diverging rival is REJECTED (exit 1, ``Decreasing
    annotations are required in total correctness semantics``). A rival that DOES
    carry a ``decreasing`` clause whose measure increases or stays constant is also
    REJECTED, on the measure's own descent goal (``case decreasing_1: i ...
    |- i + 1 < i``, and ``|- 3 < 3`` for the constant form), so the annotation is
    required to be TRUE and not merely present. An earlier revision of this bullet
    escalated that second shape as a residual spec hole on the strength of exit-0
    builds that do NOT reproduce; it is retracted, and the footer records the
    measurements. The class is unshipped only because a rival that fails to
    elaborate admits no witness at all; see the footer for that contract.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong renderings
    that diverge from the desired behaviour and MUST be rejected, each refuted at
    a DISTINCT concrete input point by a machine-checked witness that FAILS on the
    frozen solution.

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery:
``mpfRationalTester qualified p q = false`` says the extracted program's result
violates the postcondition at that concrete input point, checked in a file whose
``prove_correct`` block has been stripped (no tactic script can mask the verdict).
Both halves of every witness below were checked out of band with
``scripts/lean_verify.sh``: each ELABORATES against its rival (exit 0) and FAILS
against the frozen solution with ``decide proved … is false`` (exit 1).

MEASURED TOOLING LIMIT, and its SCOPE (why the tester-form witness points all
have non-negative ``p`` and ``q``, and why that is NOT a limit on the sign
clause). ``toString`` of a NEGATIVE ``Int`` literal does not reduce in this
workspace: the tester's ``decide`` gets stuck at
``String.Internal.append "-" (toString (Nat.succ 4))``, and ``decide``,
``decide +kernel``, ``rfl`` and ``simp`` with every unfolding lemma tried
(``Int.toString`` / ``Int.instToString`` / ``Int.repr`` /
``String.Internal.append``) all fail on the standalone goal
``toString (-5 : Int) = "-5"`` (``norm_num`` is not a known tactic here). So a
``mpfRationalTester``-form witness — the shape ``_witness`` builds — cannot be
stated at a negative point, and every such point below is non-negative.

  SECOND AUDIT RE-MEASUREMENT, and a RETRACTION. Two earlier revisions of this
  block escalated that reduction failure into a claim about the SIGN CLAUSE:
  first that the sign "cannot be probed", then — conceding that ``native_decide``
  closes the goal but is in ``pbt_witness._WITNESS_BANNED`` (it discharges
  through the ``ofReduceBool`` compiler-trust axiom) — that the sign is
  "unprobeable by any KERNEL-reducible witness, which is the only kind this gate
  admits". That second claim is FALSE and is retracted; ``weak-sign-dropped``
  now ships a kernel-only witness for exactly this clause.

  What the earlier measurements missed is that the stuck reduction is a property
  of the TESTER's ``decide``, not of the carrier. The refutation does not have to
  be decided end to end: stated over ``mpfRationalExec`` — the same
  ``extract_program_for`` projection the tester is derived from — and given the
  two literals' decimal texts as hypotheses, the remaining goal reduces to a
  disequality of two CONCRETE strings in which the surviving numeral is
  ``toString 5``, a POSITIVE literal that ``decide`` closes. Measured, on the
  rival that renders ``|p|`` via ``if p < 0 then -p else p``: the witness
  elaborates against that rival (exit 0) and fails against the frozen solution
  (exit 1), and the frozen-side failure is semantic — ``simp`` PROVES the
  equation for the frozen impl, so the residual goal is ``False`` and ``decide``
  reports "proved that the proposition False is false". The forgery pair
  confirms the exit codes track the claim and not the file: with the ``≠``
  flipped to ``=``, the frozen build SUCCEEDS (exit 0) and the rival build FAILS
  on the concrete string equation (exit 1) — the exact inversion of the witness.
  The hypotheses bind only true equations about ``toString``, so the gate's
  consistency probe cannot derive ``False`` from them (probe exit 1).

  So the sign IS pinned by a shipped rival, and the residual limit is narrow and
  purely syntactic: the ``_witness`` tester form is restricted to non-negative
  points, and a negative point is reached by ``_witness_exec`` instead. The Bool
  binder ``qualified`` has no limit of either kind and is probed at BOTH values.

AXIOM lane: EMPTY. The sibling's ``AXIOM_TESTS`` is already ``[]`` (no consumed
axioms); the constructor-spelling resolver is an A-reference validated by
axiom_check.py (G-AX), now in BOTH configurations and for its recording effect.
The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14976"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct header byte-identical
# (the spec view elides both regions).
#
# NOTE the concatenation expression alone occurs in the frozen `pure` region as
# well, so it is NOT a legal anchor; _IMPL below includes the impl-region comment
# and the `let`/`return` lines, which makes it unique and confines the edit to
# the impl region.
# ---------------------------------------------------------------------------
_IMPL = (
    "    -- Resolve the constructor's name once under the ambient configuration, wrap\n"
    "    -- both parts of the quotient in it, and report the import that resolving\n"
    "    -- recorded.\n"
    "    let m : String := mpfName qualified\n"
    '    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
    "    return (text, mpfImport)"
)
assert _BASE.count(_IMPL) == 1, "mpfRational impl region drifted from expected text"

# The FULL frozen proof body. A positive control or the admissibility case may
# retune it; the tactic body is elided from the spec view, so this is a proof
# reshape, not a spec change. Unique in the file.
_PROOF = "prove_correct mpfRational by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl-region body replaced (frozen
    tactic script kept — used for reject rivals, expected NOT to verify)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """As _impl, but also retunes the elided tactic body (positive controls whose
    reshaped impl needs the associativity of `++` folded back, or a case split on
    the configuration performed)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `mpfRationalTester qualified p q = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input point.
# ---- Checked in a file whose `prove_correct` block has been stripped. Both
# ---- values of the Bool binder are used; every integer point is a non-negative
# ---- literal (see the module docstring's MEASURED TOOLING LIMIT).
def _witness(qualified, p, q):
    b = "true" if qualified else "false"
    return ("extract_program_for mpfRational\n"
            "prove_precondition_decidable_for mpfRational\n"
            "prove_postcondition_decidable_for mpfRational\n"
            "derive_tester_for mpfRational\n\n"
            f"example : mpfRationalTester {b} {p} {q} = false := by\n  decide\n")


# ---- witness preamble, EXEC form. Used where the tester's `decide` cannot
# ---- reduce the point but the extracted program's own value still can, which is
# ---- exactly the negative-integer case (see the docstring's SIGN block). The
# ---- refutation is stated over `mpfRationalExec`, the same `extract_program_for`
# ---- projection the tester is built from, against the post-image `render`
# ---- applies at that point; `DivM.res` is the total-run constructor, so the
# ---- claim is "the extracted program's result at this input is NOT what the
# ---- ensures demands there".
# ----
# ---- The two hypotheses supply only the DECIMAL TEXT of the two literals, which
# ---- is the single step the workspace's `decide` cannot take on a negative
# ---- `Int`. They are satisfiable by construction (each is a true equation about
# ---- `toString`), so the gate's consistency probe cannot derive `False` from
# ---- them, and they are assumptions about the CARRIER shared by both builds
# ---- rather than about either impl — the discrimination still comes from the
# ---- impl, as the forgery pair below records.
def _witness_exec(qualified, p, q, pt, qt):
    b = "true" if qualified else "false"
    ps = f"({p})" if p < 0 else f"{p}"
    qs = f"({q})" if q < 0 else f"{q}"
    return ("extract_program_for mpfRational\n"
            "prove_precondition_decidable_for mpfRational\n"
            "prove_postcondition_decidable_for mpfRational\n"
            "derive_tester_for mpfRational\n\n"
            f'example (hp : toString ({p} : Int) = "{pt}")\n'
            f'    (hq : toString ({q} : Int) = "{qt}") :\n'
            f"    mpfRationalExec {b} {ps} {qs} ≠\n"
            f"      DivM.res (render {b} {ps} {qs}, mpfImport) := by\n"
            "  simp [mpfRationalExec, mpfRational, NonDetT.run, pure, render,\n"
            "    mpfName, hp, hq]\n"
            "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps both `ensures` clauses and only reshapes the
    # executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: return the closed form the post-image names directly, with no
        # intermediate `let` and no re-spelling of the concatenation. Maximally
        # different control/data shape; the frozen `loom_solve` still closes.
        "module": _impl("    return (render qualified p q, mpfImport)"),
        "rationale": "returns the closed form the post-image names directly, so "
                     "both clauses hold definitionally with no local `let` and no "
                     "restatement of the concatenation. A correct impl of a "
                     "maximally different shape must verify, else SPEC-TOO-STRONG "
                     "(the clauses would be over-fit to the literal spelling of "
                     "one concatenation chain rather than to its VALUE).",
    },
    {
        "id": "pos-named-parts",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build each wrapped operand into its OWN named local, then join
        # them with the division operator. Different bracketing of `++` (the two
        # parts are each fully assembled before being joined, where the frozen
        # impl assembles one left-to-right chain), so the proof folds the
        # re-association back — the tactic body is elided from the spec view, so
        # this is a proof reshape, not a spec change. Same resulting String.
        "module": _impl_proof(
            "    let m : String := mpfName qualified\n"
            '    let num : String := m ++ "(" ++ toString p ++ ")"\n'
            '    let den : String := m ++ "(" ++ toString q ++ ")"\n'
            '    return (num ++ "/" ++ den, mpfImport)',
            "prove_correct mpfRational by\n"
            "  loom_solve <;> simp [render, String.append_assoc]"),
        "rationale": "assembles the two wrapped operands into separate named "
                     "locals and joins them with the division operator — a "
                     "DIFFERENT bracketing of `++` than the frozen left-to-right "
                     "chain, yielding the identical String by associativity, so "
                     "`out.1 = render qualified p q` still holds and the proof "
                     "closes once the re-association is folded back. Confirms the "
                     "clause is not over-fit to one bracketing; else "
                     "SPEC-TOO-STRONG. This is the port of the sibling's separate-"
                     "head/tail-locals positive.",
    },
    {
        "id": "pos-two-step",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: accumulate in two steps through an intermediate local that
        # carries the numerator part TOGETHER WITH the division operator, then
        # append the denominator part. A third distinct write shape; the frozen
        # `loom_solve` still closes.
        "module": _impl(
            "    let m : String := mpfName qualified\n"
            '    let head : String := m ++ "(" ++ toString p ++ ")/"\n'
            '    let text : String := head ++ m ++ "(" ++ toString q ++ ")"\n'
            "    return (text, mpfImport)"),
        "rationale": "builds the result in two accumulation steps through an "
                     "intermediate local holding the wrapped numerator together "
                     "with the division operator, then appends the wrapped "
                     "denominator; a third distinct write shape producing the same "
                     "String, so both clauses still discharge. This is the port of "
                     "the sibling's single-expression-concatenation positive (its "
                     "associativity/write-shape variation).",
    },
    {
        "id": "pos-branch-split",
        "kind": "soundness",
        "expect": "verify",
        # ADDED with C-config. Resolves the constructor spelling by an explicit
        # case analysis on the ambient configuration instead of calling the
        # model's own `mpfName`, and spells each branch's constant literally. A
        # correct impl that never mentions `mpfName` must still verify, else the
        # C-config clause would be satisfiable only by naming the model's helper —
        # which is over-fitting to the model rather than to the behaviour, and
        # would also mean the two branch VALUES were never pinned separately.
        "module": _impl_proof(
            "    if qualified then\n"
            '      return ("mpmath.mpf" ++ "(" ++ toString p ++ ")/" ++\n'
            '                "mpmath.mpf" ++ "(" ++ toString q ++ ")", mpfImport)\n'
            "    else\n"
            '      return ("mpf" ++ "(" ++ toString p ++ ")/" ++\n'
            '                "mpf" ++ "(" ++ toString q ++ ")", mpfImport)',
            "prove_correct mpfRational by\n"
            "  loom_solve <;> simp_all [render, mpfName]"),
        "rationale": "PASS SOURCE = the configuration clause pins the two branch "
                     "VALUES, not the model's helper. This impl resolves the "
                     "spelling by case analysis on `qualified` and writes each "
                     "branch's constant out literally, never mentioning `mpfName`; "
                     "it is behaviourally identical to the frozen impl in both "
                     "branches and must verify. If it were rejected the clause "
                     "would be SPEC-TOO-STRONG in the worst way — satisfiable only "
                     "by calling the model's own function — and the reject lane's "
                     "configuration rivals would be attacking a tautology.",
    },
    {
        "id": "pos-import-spelled-out",
        "kind": "soundness",
        "expect": "verify",
        # ADDED with C-import. Reports the recorded import as the literal pair
        # list instead of through the model's `mpfImport` name. Confirms the
        # effect clause is about the VALUE recorded, not about naming the model's
        # constant.
        "module": _impl_proof(
            "    let m : String := mpfName qualified\n"
            '    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
            '    return (text, [("mpmath", "mpf")])',
            "prove_correct mpfRational by\n"
            "  loom_solve <;> rfl"),
        "rationale": "reports the recorded import as the literal (module, name) "
                     "pair rather than through the model's `mpfImport` constant, "
                     "so it must verify; else the effect clause would be "
                     "SPEC-TOO-STRONG, satisfiable only by naming the model's own "
                     "definition rather than by recording the right pair. The "
                     "tactic body — elided from the spec view — gains a `rfl` arm "
                     "to unfold the model's constant on the goal side; a proof "
                     "reshape for a correct impl, not a spec change.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The sibling self-calls on an F2P-shaped input to
    # show its fractional-permission precondition ADMITS it. This bundle carries
    # NO `require` clause (the rendering is total in all three arguments), so that
    # probe is degenerate. Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is DEGENERATE / unsatisfiable at the interesting
    # points. The in-region assert pins the post-image in BOTH configurations AND
    # separates each from the unchanged bare-ratio rendering AND pins the recorded
    # import non-empty; the impl is kept verbatim so the method's own obligation
    # still discharges. The assert is LIVE — verified out of band by flipping a
    # pinned value, which leaves `decide proved … is false` (exit 1) rather than
    # passing silently.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `admiss\n"
            '      (render true 1 2 = "mpmath.mpf(1)/mpmath.mpf(2)" ∧\n'
            '       render false 1 2 = "mpf(1)/mpf(2)" ∧\n'
            '       render true 1 2 ≠ "1/2" ∧\n'
            '       render false 1 2 ≠ "1/2" ∧\n'
            "       mpfImport ≠ ([] : List (String × String))))\n" + _IMPL,
            "prove_correct mpfRational by\n  loom_solve <;> decide"),
        "rationale": "PASS SOURCE = the post-image is satisfiable AND "
                     "NON-DEGENERATE at the F2P-shaped point, in BOTH "
                     "configurations. The live in-region assert pins "
                     "`render true 1 2` and `render false 1 2` to the quotient "
                     "with BOTH parts wrapped in the constructor spelling that "
                     "configuration resolves to, pins each AWAY from the bare "
                     "integer ratio the unchanged behaviour produced, and pins the "
                     "recorded import non-empty — so the obligation genuinely "
                     "demands the wrapped rendering plus the recording, and is not "
                     "vacuously satisfiable in either configuration. The impl is "
                     "kept verbatim so both clauses discharge as well; the proof "
                     "gains a `decide` arm solely to close the ground assert. If "
                     "the assert failed, the obligation would be degenerate "
                     "(SPEC-UNUSABLE at the very points the failing test and the "
                     "reported path observe).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong renderings sharing the frozen
    # spec that MUST be rejected, each with a machine-checked refutation witness
    # at a DISTINCT concrete input point and the refinement argument that its
    # faithful real counterpart would NOT resolve the failing test, or would
    # regress the reported path.
    # =====================================================================
    {
        "id": "weak-bare-ratio",
        "kind": "uniqueness",
        "expect": "reject",
        # THE modeled defect: neither part wrapped — a bare integer quotient. This
        # is the pre-image behaviour and the headline discriminator.
        "module": _impl('    let text : String := toString p ++ "/" ++ toString q\n'
                        "    return (text, mpfImport)"),
        "refinement": "this is the unchanged behaviour itself: with no "
                      "backend-specific handling a rational falls through to the "
                      "generic textual form, a bare integer quotient with NEITHER "
                      "part wrapped in the backend float constructor. Its faithful "
                      "counterpart is the un-patched code, under which the failing "
                      "test — which asserts the quotient of two constructor calls "
                      "— still observes the bare ratio, so it would NOT resolve. "
                      "The bundle's prepatch skeleton is exactly this rendering and "
                      "G-DIFF records that it fails the obligation.",
        "rationale": "REJECT from C-wrap-num AND C-wrap-den jointly: at "
                     "(qualified, 1, 2) the spec demands the quotient of two "
                     "constructor calls but this returns the bare ratio, so "
                     "`out.1 ≠ render qualified p q`. The precise change the spec "
                     "senses; if it verified => SPEC-TOO-WEAK (admits the unchanged "
                     "fall-through and the precision loss the issue reports). "
                     "Refuted at the F2P-shaped point (true, 1, 2).",
        "witness": _witness(True, 1, 2),
    },
    {
        "id": "weak-denominator-unwrapped",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR MISS: numerator wrapped, denominator left bare. Agrees with gold on
        # strictly MORE of the surface than the bare-ratio rival, so it gets its
        # own distinct witness point.
        "module": _impl("    let m : String := mpfName qualified\n"
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString p ++ ")/" ++ toString q\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that wrapped only the numerator would render "
                      "the quotient of one constructor call and a bare integer. The "
                      "failing test pins BOTH parts as constructor calls, so it "
                      "would NOT resolve — and the generated code would still "
                      "divide by a bare integer, reproducing the reduced-precision "
                      "result the issue reports.",
        "rationale": "REJECT from C-wrap-den alone: at (true, 3, 7) the denominator "
                     "must be wrapped and is not, so `out.1 ≠ render qualified p q`. "
                     "This is the closest NEAR MISS to the desired behaviour — it "
                     "satisfies C-wrap-num, C-quotient, C-order, C-ctor, C-parens, "
                     "C-config and C-import on the numerator side, and so agrees "
                     "with the frozen solution over strictly more of the rendering "
                     "than weak-bare-ratio; it therefore carries its OWN witness "
                     "point (true, 3, 7) rather than sharing one, so its sub-domain "
                     "claim is demonstrated. If it verified => SPEC-TOO-WEAK "
                     "(C-wrap-den unpinned).",
        "witness": _witness(True, 3, 7),
    },
    {
        "id": "weak-numerator-unwrapped",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror near miss: denominator wrapped, numerator left bare. Isolates
        # C-wrap-num, which no other surviving rival isolates.
        "module": _impl("    let m : String := mpfName qualified\n"
                        "    let text : String :=\n"
                        '      toString p ++ "/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that wrapped only the denominator would render "
                      "a bare integer divided by a constructor call. The failing "
                      "test pins BOTH parts as constructor calls, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from C-wrap-num alone: at (true, 7, 2) the numerator "
                     "must be wrapped and is not, so `out.1 ≠ render qualified p q`. "
                     "The mirror image of weak-denominator-unwrapped and the only "
                     "rival isolating C-wrap-num, which pins the numerator side "
                     "independently of the denominator side. Refuted at a distinct "
                     "point (true, 7, 2), which also swaps the roles of the two "
                     "magnitudes used by weak-denominator-unwrapped (3, 7) — so "
                     "neither integer binder is held fixed across the pair. If it "
                     "verified => SPEC-TOO-WEAK.",
        "witness": _witness(True, 7, 2),
    },
    {
        "id": "weak-transposed-operands",
        "kind": "uniqueness",
        "expect": "reject",
        # Both parts wrapped, but the operands transposed: the reciprocal.
        # Refutable ONLY where the two integer arguments differ — hence a point
        # with two distinct, both-non-trivial magnitudes.
        "module": _impl("    let m : String := mpfName qualified\n"
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString q ++ ")/" ++ m ++ "(" ++ toString p ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that emitted the denominator first and the "
                      "numerator second would render the RECIPROCAL of the intended "
                      "value. The failing test pins the numerator's part first, and "
                      "the generated code would compute a numerically different "
                      "quantity, so it would NOT resolve.",
        "rationale": "REJECT from C-order: at (true, 2, 9) the spec demands the "
                     "numerator's constructor call first, but this emits the "
                     "denominator's first. This rival wraps BOTH parts, resolves "
                     "the correct constructor spelling in both configurations, uses "
                     "the parentheses and the division operator and records the "
                     "right import, so it is refutable ONLY where the two integer "
                     "arguments differ — it is the sole rival that pins the ORDER "
                     "of the two parts (no wrap-dropping rival senses it). Refuted "
                     "at (true, 2, 9), a point with two distinct magnitudes. If it "
                     "verified => SPEC-TOO-WEAK (C-order unpinned).",
        "witness": _witness(True, 2, 9),
    },
    {
        "id": "weak-truncated-constructor",
        "kind": "uniqueness",
        "expect": "reject",
        # Structure and configuration-awareness entirely correct; the constructor
        # SPELLING is truncated in each branch.
        "module": _impl('    let m : String := if qualified then "mpmath.mp" else "mp"\n'
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that resolved a truncated dotted name would "
                      "render calls to a constructor that does not exist in the "
                      "generated code's namespace, in EITHER configuration. The "
                      "failing test pins the constructor's exact spelling, so it "
                      "would NOT resolve — and the generated function would raise "
                      "at call time rather than merely lose precision.",
        "rationale": "REJECT from C-ctor: at (true, 6, 11) both parts are wrapped, "
                     "in the right order, parenthesised, joined by the division "
                     "operator, the import is recorded and the spelling is resolved "
                     "PER CONFIGURATION — every other clause holds — but the "
                     "spelling is truncated relative to `mpfName qualified` in both "
                     "branches, so `out.1 ≠ render qualified p q`. The only rival "
                     "isolating the constructor SPELLING as opposed to the wrapping "
                     "STRUCTURE or the configuration BRANCH, and a genuine "
                     "value-level near miss. Refuted at a distinct point "
                     "(true, 6, 11), the only witness with a multi-digit "
                     "denominator, so the rendering is probed where the two parts "
                     "have different text lengths. If it verified => SPEC-TOO-WEAK "
                     "(C-ctor unpinned).",
        "witness": _witness(True, 6, 11),
    },
    {
        "id": "weak-no-division-operator",
        "kind": "uniqueness",
        "expect": "reject",
        # Both parts correctly wrapped, but juxtaposed with no division operator.
        "module": _impl("    let m : String := mpfName qualified\n"
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString p ++ ")" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that omitted the division operator would "
                      "juxtapose the two constructor calls rather than form a "
                      "quotient — not the intended value, and not even "
                      "syntactically valid in the generated code. The failing test "
                      "pins the quotient, so it would NOT resolve.",
        "rationale": "REJECT from C-quotient: at (true, 8, 3) both parts are "
                     "correctly wrapped with the right spelling and order, but the "
                     "division operator between them is absent, so "
                     "`out.1 ≠ render qualified p q`. The only rival isolating the "
                     "operator that makes the rendering a quotient. Refuted at a "
                     "distinct point (true, 8, 3). If it verified => SPEC-TOO-WEAK "
                     "(C-quotient unpinned).",
        "witness": _witness(True, 8, 3),
    },
    {
        "id": "weak-constructor-not-applied",
        "kind": "uniqueness",
        "expect": "reject",
        # The constructor spelling is PREFIXED to each part but never APPLIED —
        # the parentheses are gone. Isolates C-parens, which the wrap-dropping
        # rivals conflate with the presence of the spelling.
        "module": _impl("    let m : String := mpfName qualified\n"
                        "    let text : String :=\n"
                        '      m ++ toString p ++ "/" ++ m ++ toString q\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that concatenated the constructor's name onto "
                      "each part without applying it would emit an identifier "
                      "glued to a digit string rather than a call. The failing test "
                      "pins the parenthesised call form, so it would NOT resolve — "
                      "and the generated code would not parse as a constructor "
                      "application at all.",
        "rationale": "REJECT from C-parens: at (true, 12, 5) the constructor "
                     "spelling is present on both parts, resolved per "
                     "configuration, and the division operator and order are "
                     "correct, but neither part is PARENTHESISED, so the "
                     "constructor is never applied and "
                     "`out.1 ≠ render qualified p q`. This is the only rival "
                     "isolating the call syntax from the mere PRESENCE of the "
                     "constructor name — the wrap-dropping rivals remove both at "
                     "once and so cannot distinguish them. Refuted at a distinct "
                     "point (true, 12, 5), the only witness whose numerator text is "
                     "longer than its denominator text. If it verified => "
                     "SPEC-TOO-WEAK (C-parens unpinned).",
        "witness": _witness(True, 12, 5),
    },
    {
        "id": "weak-f2p-point-only",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. Most rivals here are wrong EVERYWHERE, so all of them are
        # already refuted at the F2P-shaped point (true, 1, 2) and none of those
        # tests that the obligation is quantified over the whole domain rather than
        # pinned at the one point the failing test observes. This rival hard-codes
        # the correct rendering at exactly (true, 1, 2) and falls back to the
        # unchanged bare integer ratio everywhere else: it AGREES with the frozen
        # solution at the F2P point (measured — the tester witness at (true, 1, 2)
        # does NOT hold of it, exit 1) and diverges at every other input. So it is
        # refutable only AWAY from that point, and its witness point (true, 5, 4) is
        # one no other rival uses.
        "module": _impl("    let text : String :=\n"
                        "      if qualified = true ∧ p = 1 ∧ q = 2 then\n"
                        '        "mpmath.mpf(1)/mpmath.mpf(2)"\n'
                        '      else toString p ++ "/" ++ toString q\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that special-cased the single rational the "
                      "failing test observes, in the single configuration that test "
                      "constructs, and left every other rational on the unchanged "
                      "fall-through would pass that one assertion while rendering "
                      "every OTHER rational at reduced precision. It is the shape "
                      "that resolves a test without addressing the reported "
                      "behaviour, so although the pinned test would go green the "
                      "issue would not be addressed for any other value — and the "
                      "numeric backend's other call sites, which are what the "
                      "regression tests cover, would still receive bare ratios.",
        "rationale": "REJECT because the obligation is UNIVERSALLY quantified in "
                     "`qualified`, `p` and `q`: both clauses must hold at every "
                     "input, not merely at the one the failing test names. This is "
                     "the only rival that is CORRECT at the F2P-shaped point "
                     "(true, 1, 2) — verified out of band: the tester witness at "
                     "(true, 1, 2) elaborates against the frozen solution and NOT "
                     "against this rival, the mirror image of every other case here "
                     "— so it is the only rival that tests the quantifier rather "
                     "than the clause content. Refuted at (true, 5, 4), a point no "
                     "other witness uses, whose two magnitudes are both multi-unit "
                     "and in the opposite order to (1, 2). If it verified => "
                     "SPEC-TOO-WEAK (the spec would pin only the observed point and "
                     "admit an answer-key special case).",
        "witness": _witness(True, 5, 4),
    },
    {
        "id": "weak-empty-rendering",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheapest possible cheat: render nothing at all. Supporting near miss;
        # also the rival that probes the boundary numerator 0.
        "module": _impl('    let text : String := ""\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that rendered nothing would emit an empty "
                      "fragment for every rational, so the generated code would be "
                      "malformed and the failing test — which pins a specific "
                      "non-empty quotient — would NOT resolve.",
        "rationale": "REJECT from every rendering clause at once: at (true, 0, 1) "
                     "the spec demands the wrapped quotient but this returns the "
                     "empty rendering, so `out.1 ≠ render qualified p q`. The "
                     "cheapest cheat and a supporting control confirming the "
                     "obligation is not satisfiable by returning nothing. Its "
                     "witness point (true, 0, 1) is also the only one exercising "
                     "the boundary numerator 0 and the boundary denominator 1 — the "
                     "pair where the desired rendering's two parts have their "
                     "shortest text — so it varies both integer binders to their "
                     "edge values. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(True, 0, 1),
    },

    # ---- C-config rivals (the configuration clause) ----------------------
    {
        "id": "weak-config-blind-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        # THE defect this model was repaired for. Pins the module-qualified
        # spelling regardless of the ambient configuration: correct wherever
        # qualified spellings are asked for, and a name the generated code cannot
        # resolve everywhere else.
        "module": _impl('    let m : String := "mpmath.mpf"\n'
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that emitted the module-qualified dotted name "
                      "unconditionally is exactly what a spec pinning ONE branch of "
                      "the resolver licenses, and it is what the previous revision "
                      "of this model asserted. Its real behaviour was measured, not "
                      "argued: under the unqualified configuration the generated "
                      "function contains the qualified spelling while the "
                      "namespace it runs in binds only the bare constructor name, "
                      "so calling it raises NameError instead of losing precision. "
                      "The regression test the change ships for the reported path "
                      "fails, so this rival does NOT resolve that path even though "
                      "the F2P unit test — which constructs a printer in the "
                      "default configuration — would still pass. This rival is why "
                      "C-config exists.",
        "rationale": "REJECT from C-config: at (false, 1, 2) the ambient "
                     "configuration resolves the constructor to its bare final "
                     "component, but this rival emits the module-qualified dotted "
                     "name, so `out.1 ≠ render qualified p q`. Every other clause "
                     "holds — both parts wrapped, right order, parentheses, "
                     "division operator, import recorded — so this isolates the "
                     "configuration branch and nothing else. It is the ONLY rival "
                     "that is correct under `qualified = true` and wrong under "
                     "`qualified = false`, which is what makes it the load-bearing "
                     "C-config case: if it verified => SPEC-TOO-WEAK, and the spec "
                     "would be back to asserting one branch of a two-branch callee.",
        "witness": _witness(False, 1, 2),
    },
    {
        "id": "weak-config-blind-bare",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror: pins the bare final component regardless of the ambient
        # configuration. Correct exactly where qualified spellings are NOT asked
        # for, so it is refutable only under `qualified = true`.
        "module": _impl('    let m : String := "mpf"\n'
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that emitted the bare final component "
                      "unconditionally would, under the configuration that asks for "
                      "module-qualified spellings, emit a name that is NOT bound "
                      "there: the failing unit test asserts the module-qualified "
                      "quotient, so it would NOT resolve.",
        "rationale": "REJECT from C-config, in the OPPOSITE direction to "
                     "weak-config-blind-qualified: at (true, 10, 4) the "
                     "configuration resolves the constructor to its module-"
                     "qualified dotted name and this rival emits the bare "
                     "component, so `out.1 ≠ render qualified p q`. Shipping both "
                     "directions is what pins the branch as a FUNCTION of the "
                     "configuration rather than merely making one branch "
                     "reachable — a spec that pinned only the bare branch would "
                     "reject the other rival and admit this one. Refuted at "
                     "(true, 10, 4), a point no other rival uses. If it verified "
                     "=> SPEC-TOO-WEAK.",
        "witness": _witness(True, 10, 4),
    },
    {
        "id": "weak-config-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Configuration-aware but with the branches EXCHANGED: emits the bare
        # component when qualified spellings are asked for and vice versa. Wrong
        # in BOTH configurations, and the rival a spec that merely required "the
        # spelling depends on the configuration" would admit.
        "module": _impl("    let m : String := mpfName (!qualified)\n"
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that read the configuration and then resolved "
                      "the OTHER way round would emit an unbound name in both "
                      "configurations — the bare component where the qualified one "
                      "is required and the qualified one where only the bare "
                      "component is bound. Neither the failing unit test nor the "
                      "reported path would resolve.",
        "rationale": "REJECT from C-config's DIRECTION: at (false, 11, 6) the "
                     "configuration asks for the bare component and this rival "
                     "emits the qualified dotted name (and symmetrically at "
                     "`qualified = true`). It is the rival that shows the clause "
                     "pins WHICH branch goes with which configuration, not merely "
                     "that the spelling varies with it — a spec stating only "
                     "dependence would admit this. Refuted at (false, 11, 6), the "
                     "second of the two points at which the Bool binder takes the "
                     "value `false`. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(False, 11, 6),
    },

    # ---- C-import rivals (the recording effect) --------------------------
    {
        "id": "weak-import-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Rendering perfect; the recording effect dropped entirely. This is the
        # second divergence the previous model had — it modeled the resolver as a
        # pure constant and so had no clause for the import at all.
        "module": _impl("    let m : String := mpfName qualified\n"
                        '    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, ([] : List (String × String)))"),
        "refinement": "a counterpart that resolved the constructor's dotted name "
                      "without recording the import is what a model treating the "
                      "resolver as a pure value licenses. Measured on the real "
                      "repo: the recorded imports are what the code generator turns "
                      "into the import block of the module it emits, so a "
                      "counterpart that records nothing emits a module in which the "
                      "spelling it just wrote is unbound. The rendering assertion of "
                      "the failing unit test would pass, but the generated module "
                      "would not run — which is why the clause is separate from the "
                      "rendering clause and is attacked separately.",
        "rationale": "REJECT from C-import: at (true, 9, 8) `out.2` must be the "
                     "recorded import pair and this rival returns the empty "
                     "recording, so `out.2 ≠ mpfImport`. Every rendering clause "
                     "holds, so this isolates the effect clause exactly. Refuted at "
                     "(true, 9, 8), a point no other rival uses. If it verified => "
                     "SPEC-TOO-WEAK (the effect would be unmodeled, which is the "
                     "state a faithfulness review found).",
        "witness": _witness(True, 9, 8),
    },
    {
        "id": "weak-import-only-when-qualified",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR MISS on the effect clause: records the import only where qualified
        # spellings are asked for. Refutable ONLY under `qualified = false`, so it
        # pins the effect as configuration-INDEPENDENT.
        "module": _impl("    let m : String := mpfName qualified\n"
                        '    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, if qualified then mpfImport else ([] : List (String × String)))"),
        "refinement": "the real resolver records the import BEFORE it consults the "
                      "name-spelling configuration, so the recording happens in both "
                      "configurations — and it is precisely under the unqualified "
                      "configuration that the recording MATTERS, because there the "
                      "emitted spelling is the bare component and the import is the "
                      "only thing that binds it. A counterpart that skipped the "
                      "recording there would emit code naming an unbound "
                      "constructor, so the reported path would not resolve.",
        "rationale": "REJECT from C-import's configuration-INDEPENDENCE: at "
                     "(false, 3, 4) the import must still be recorded and this "
                     "rival records nothing, so `out.2 ≠ mpfImport`. It agrees with "
                     "the frozen solution on every rendering clause AND on the "
                     "effect clause under `qualified = true`, so it is the closest "
                     "near miss on the effect and carries its own witness point. If "
                     "it verified => SPEC-TOO-WEAK (the effect clause would be "
                     "pinned in only one configuration — the same one-branch mistake "
                     "as C-config, one clause over).",
        "witness": _witness(False, 3, 4),
    },
    {
        "id": "weak-import-transposed",
        "kind": "uniqueness",
        "expect": "reject",
        # The recording is present but the pair is transposed: the final component
        # recorded as the module and the module as the name.
        "module": _impl("    let m : String := mpfName qualified\n"
                        '    let text : String := m ++ "(" ++ toString p ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        '    return (text, [("mpf", "mpmath")])'),
        "refinement": "a counterpart that recorded the pair the other way round "
                      "would have the code generator emit an import of the "
                      "qualifying module FROM the constructor — a module that does "
                      "not exist — so the generated module would fail to import at "
                      "all, and the reported path would not resolve.",
        "rationale": "REJECT from C-import's ORDER: at (true, 13, 2) the recorded "
                     "pair must name the qualifying module first and the final "
                     "component second, and this rival transposes them, so "
                     "`out.2 ≠ mpfImport`. It is the only rival that records a "
                     "NON-EMPTY but wrong pair, so it separates 'something is "
                     "recorded' from 'the right thing is recorded' — a distinction "
                     "weak-import-dropped cannot make. Refuted at (true, 13, 2), a "
                     "point no other rival uses. If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(True, 13, 2),
    },

    # ---- C-sign rival (the numerator's sign) -----------------------------
    {
        "id": "weak-sign-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT, and it closes what the previous revision recorded as an
        # unprobeable binder. This rival renders the numerator's MAGNITUDE,
        # discarding its sign, so it agrees with the frozen solution at every
        # non-negative point — i.e. at all 15 points the rest of this battery
        # probes — and diverges only where `p < 0`. Nothing else here senses the
        # sign, so without this case the obligation's dependence on it rests on no
        # rival at all.
        "module": _impl("    let m : String := mpfName qualified\n"
                        "    let ap : Int := if p < 0 then -p else p\n"
                        "    let text : String :=\n"
                        '      m ++ "(" ++ toString ap ++ ")/" ++ m ++ "(" ++ toString q ++ ")"\n'
                        "    return (text, mpfImport)"),
        "refinement": "a counterpart that rendered the numerator's magnitude and "
                      "dropped its sign would emit the NEGATION of the intended "
                      "value for every negative rational — a quotient of the right "
                      "shape, at full precision, naming the right constructor, "
                      "denoting the wrong number. The failing test constructs a "
                      "positive rational, so that assertion would still pass; the "
                      "regression coverage over signed values is what would fail, "
                      "and the reported path would return a sign-flipped result "
                      "rather than a lower-precision one. It is the near miss that "
                      "a rendering-shape review does not catch, because every "
                      "structural clause holds.",
        "rationale": "REJECT from the numerator's SIGN, which `render` carries "
                     "through `toString p` and this rival replaces with "
                     "`toString |p|`: at (true, -5, 2) the spec demands the "
                     "numerator's own decimal text and this emits the magnitude's, "
                     "so `out.1 ≠ render qualified p q`. Every other clause holds "
                     "in both configurations — both parts wrapped, right order, "
                     "parentheses, division operator, spelling resolved per "
                     "configuration, import recorded — and the rival is CORRECT at "
                     "every non-negative point, hence at all 15 points the other "
                     "rivals use, which is what makes it the one case that pins "
                     "this binder. If it verified => SPEC-TOO-WEAK (the sign would "
                     "be unpinned and a sign-flipping rendering admitted).",
        # Stated over the Exec projection rather than the tester: the tester's
        # `decide` gets stuck on a negative `Int` literal (the docstring's SIGN
        # block records the measurement), while the extracted program's value
        # reduces once the two literals' decimal texts are supplied. Measured both
        # ways — rival exit 0, frozen exit 1, and the frozen-side failure is the
        # SEMANTIC one (`simp` closes the equation for the frozen impl, leaving
        # `decide` to refute `False`), not a stuck reduction.
        "witness": _witness_exec(True, -5, 2, "-5", "2"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting, and the FAITHFULNESS REPAIR this battery was
# re-authored for.
#
# The sibling battery ships 13 SPEC cases (3 soundness positives + 1
# admissibility; 9 uniqueness rivals — two of them the mandatory frame-mutation
# pair) and 0 AXIOM_TESTS. The sibling contracts ONE function,
# `render_mpf_ratio(p_digits, q_digits) -> List[int]`, over two READ-ONLY
# digit-carrier lists held at fractional (1/2) heap permission, building the
# rendering per code-point with `out = out + [...]` concatenation chains and
# pinning the result to the @Pure deep model `rendered(p, q)`.
#
# This bundle models the SAME decision — how a rational is rendered for the
# arbitrary-precision numeric backend — but on a VALUE carrier:
# `mpfRational (qualified : Bool) (p q : Int) return (out : String × List (String × String))`
# with `ensures out.1 = render qualified p q` and `ensures out.2 = mpfImport`,
# where `render`, `mpfName` and `mpfImport` are concrete pure `def`s (the
# sibling's per-code-point `List[int]` digit carriers and its @Pure
# `ctor`/`rendered` folds are refined to `Int` arguments, `toString`, and
# `String` `++`, mapping.md §2).
#
# WHY THIS BATTERY MOVED (the repair). The model previously took only `(p, q)`
# and pinned the constructor spelling to the single constant "mpmath.mpf",
# with no clause for the resolver's recording effect. A G-PANEL-2 faithfulness
# review refuted that on the real repo: the resolver is settings-dependent, the
# configuration it depends on is hardcoded to the OTHER branch by the code
# generator the reported issue is about, and the resolver also records an import
# that the old model dropped. The spec was therefore STRONGER than the real
# callee on the rendering (it demanded the qualified spelling unconditionally) and
# WEAKER on the effect (it demanded nothing at all). The model now carries the
# configuration as a Bool binder with a two-branch deep model, and the recording
# delta as a second output component. Both new clauses are attacked here:
# C-config by three rivals (`weak-config-blind-qualified` — the previous model's
# own rendering, `weak-config-blind-bare`, `weak-config-inverted`) and C-import by
# three (`weak-import-dropped` — the previous model's own effect, i.e. none,
# `weak-import-only-when-qualified`, `weak-import-transposed`), and both are
# DEFENDED by new positive controls (`pos-branch-split`, `pos-import-spelled-out`)
# so neither clause can be satisfied merely by naming the model's own helpers.
# Nothing was removed: every case the previous battery shipped is still here, in
# the new signature, with its own witness point.
#
#   sibling case            kind          -> here                          disposition
#   ------------------------------------------------------------------------------------------
#   pos-single-expr         soundness     -> pos-two-step                  PORTED (re-shaped)
#   pos-reorder-build       soundness     -> pos-named-parts               PORTED (re-shaped)
#   pos-cheapest            soundness     -> (none)                        N/A (no opaque oracle)
#   admiss-f2p-shaped       admissibility -> admiss-grounded               PORTED (re-aimed)
#   frame-append-p          uniqueness    -> (none)                        VACUOUS
#   frame-setitem-q         uniqueness    -> (none)                        VACUOUS
#   bare-division           uniqueness    -> weak-bare-ratio               PORTED
#   drop-den-wrap           uniqueness    -> weak-denominator-unwrapped    PORTED
#   drop-num-wrap           uniqueness    -> weak-numerator-unwrapped      PORTED
#   swap-operands           uniqueness    -> weak-transposed-operands      PORTED
#   wrong-ctor-token        uniqueness    -> weak-truncated-constructor    PORTED
#   no-slash                uniqueness    -> weak-no-division-operator     PORTED
#   empty-output            uniqueness    -> weak-empty-rendering          PORTED
#   (no sibling)            soundness     -> pos-closed-form               ADDED (shape cov.)
#   (no sibling)            soundness     -> pos-branch-split              ADDED (C-config def.)
#   (no sibling)            soundness     -> pos-import-spelled-out        ADDED (C-import def.)
#   (no sibling)            uniqueness    -> weak-constructor-not-applied  ADDED (C-parens cov.)
#   (no sibling)            uniqueness    -> weak-f2p-point-only           ADDED BY AUDIT
#                                                                          (quantifier cov.)
#   (no sibling)            uniqueness    -> weak-config-blind-qualified   ADDED BY REPAIR
#   (no sibling)            uniqueness    -> weak-config-blind-bare        ADDED BY REPAIR
#   (no sibling)            uniqueness    -> weak-config-inverted          ADDED BY REPAIR
#   (no sibling)            uniqueness    -> weak-import-dropped           ADDED BY REPAIR
#   (no sibling)            uniqueness    -> weak-import-only-when-qualified ADDED BY REPAIR
#   (no sibling)            uniqueness    -> weak-import-transposed        ADDED BY REPAIR
#   (no sibling)            uniqueness    -> weak-sign-dropped             ADDED BY AUDIT
#                                                                          (sign binder)
#
# 7 uniqueness ported + 9 added (16 total), 2 soundness ported + 3 added (5
# total), 1 admissibility re-aimed, 2 vacuous, 1 N/A — 22 SPEC cases. The sibling
# ships NO divergence case, so nothing was dropped there — and under this
# bundle's "total" semantics BOTH diverging sub-shapes are REJECTED, so the class
# is closed rather than a hole; the witness-side reason no reject case ships for
# it is recorded below.
#
# ADDED BY AUDIT (weak-sign-dropped): no sibling counterpart — the sibling's
#   carrier passes the numerator in as a digit LIST, so its rivals cannot express
#   "same digits, sign discarded" as a separate edit at all, whereas on the `Int`
#   carrier the sign is a distinct property of one argument. This battery
#   previously recorded the sign as unprobeable and shipped no rival for it; that
#   claim was refuted by re-measurement (see the docstring's retraction) and the
#   rival now ships with a kernel-only witness at (true, -5, 2). It is the closest
#   near miss in the battery: it agrees with the frozen solution at all 15 other
#   witness points and every structural clause holds.
#
# PORTED (pos-single-expr -> pos-two-step; pos-reorder-build -> pos-named-parts):
#   both siblings vary the associativity / write shape of a fold-free
#   concatenation. On `String` the same spirit becomes: a two-step accumulation
#   through an intermediate local carrying the numerator part plus the division
#   operator (pos-two-step, frozen proof closes), and the two wrapped operands
#   assembled into separate named locals before being joined (pos-named-parts).
#   The latter genuinely RE-BRACKETS `++`, so `loom_solve` alone leaves
#   `… ++ "(" ++ toString p ++ ")" ++ "/" ++ (…) = render …`; the tactic body —
#   elided from the spec view — gains `simp [render, String.append_assoc]` to fold
#   the re-association back. That is a proof reshape for a genuinely correct impl,
#   not a weakening: the `prove_correct mpfRational` header is byte-identical and
#   nothing is assumed. ADDED pos-closed-form supplies a third, maximally
#   different shape (no local `let` at all).
# ADDED (pos-branch-split): the C-config DEFENCE. It resolves the spelling by an
#   explicit `if qualified then … else …` and writes each branch's constant out
#   literally, so it never mentions `mpfName`. Its tactic body gains
#   `simp [render, mpfName]` to unfold the model's branch on the goal side; that
#   is a proof reshape for a correct impl. Without this control the three C-config
#   rivals would be attacking a clause that might only be satisfiable by calling
#   the model's own helper, which is over-fitting to the model.
# ADDED (pos-import-spelled-out): the C-import DEFENCE, same argument one clause
#   over — it records the literal (module, name) pair instead of naming
#   `mpfImport`; its tactic body gains `rfl` to unfold the model's constant on the
#   goal side.
# N/A (pos-cheapest): the sibling's cheapest-impl control exists to record that
#   its post-image is GROUNDED in the arguments rather than an opaque answer key,
#   so there is no wrong echo to build. The same holds here by construction — the
#   `axioms` region is EMPTY and `render` is a fully-unfolded function of
#   `qualified`, `p` and `q` — and the honest positives above, which compute the
#   rendering directly, already discharge it. No separate signal to add.
# PORTED (admiss-f2p-shaped -> admiss-grounded): the sibling self-calls on the
#   F2P-shaped digit carriers to show its fractional-permission `Requires` admits
#   a normal input. This method has NO `require` clause, so that probe is
#   degenerate; the case is re-aimed at the residual risk on a total domain (a
#   degenerate post-image) via a LIVE in-region assert pinning `render true 1 2`
#   AND `render false 1 2` to the both-parts-wrapped quotient of the spelling that
#   configuration resolves, each away from the bare ratio, plus the recorded
#   import non-empty. Liveness verified out of band by flipping a pinned value:
#   the variant then fails with `decide proved … is false`, so the assert is not
#   decorative.
# PORTED (7 uniqueness rivals): each sibling rival maps to a direct value-carrier
#   counterpart, and each is refuted at its OWN input point rather than sharing
#   one, because the wrap-dropping rivals are genuine NEAR MISSES that agree with
#   the frozen solution over different, strictly larger parts of the domain than
#   the bare-ratio rival does. `weak-truncated-constructor` now truncates the
#   spelling IN EACH BRANCH (`if qualified then "mpmath.mp" else "mp"`), so it
#   isolates C-ctor without also violating C-config — which a single truncated
#   constant would have done, conflating two clauses.
# ADDED BY AUDIT (weak-f2p-point-only): no sibling counterpart, and a gap the
#   original port left open in a direction none of its rivals pointed. Most
#   rivals are wrong at EVERY input, so each is refutable at the F2P-shaped point
#   and the battery never asked whether the obligation binds AWAY from the point
#   the failing test observes. The added rival is correct exactly at (true, 1, 2)
#   — measured: the (true, 1, 2) tester witness fails against it, the only rival
#   here of which that is true — and wrong elsewhere, so it probes the UNIVERSAL
#   QUANTIFIER over the three binders rather than any single clause. It is also
#   the rival closest to the realistic failure mode of a test-driven change.
# ADDED (weak-constructor-not-applied): no sibling counterpart. On the sibling's
#   code-point carrier, dropping the parentheses and dropping the constructor
#   spelling are the same kind of edit to one digit list; on the `String` carrier
#   the constructor's NAME and its APPLICATION are separable, so a rival that
#   prefixes the name without applying it isolates C-parens — a clause no ported
#   rival senses on its own.
# ADDED BY REPAIR (the six C-config / C-import rivals): see WHY THIS BATTERY
#   MOVED above. Two of them are not hypothetical shapes but the PREVIOUS MODEL
#   ITSELF: `weak-config-blind-qualified` is the rendering the old
#   `def mpfName : String := "mpmath.mpf"` mandated, and `weak-import-dropped` is
#   the effect the old model had (none). Both are REJECTED by the spec that now
#   ships, which is the falsification-side statement of the repair: the model did
#   not merely change, it now rejects what it used to require.
#
# VACUOUS (frame-append-p, frame-setitem-q): the sibling's MANDATORY
#   frame-mutation pair writes into the read-only digit carriers (an `append` on
#   the numerator's list, an index assignment on the denominator's) and must be
#   rejected for INSUFFICIENT PERMISSION, since each is held at only 1/2
#   permission. This backend is referentially transparent: `qualified`, `p` and
#   `q` are immutable values, the method declares no `mut` binder, and there is
#   no heap, no aliasing and no permission system. There is no read-only input to
#   overwrite and nothing to trip, so BOTH cases are vacuous. No substitute is
#   fabricated. The real callee's one mutation — the printer's recorded imports —
#   is modeled as an output component rather than a `mut` binder ON PURPOSE
#   (mapping.md §2): the real effect is a SET insertion, so pinning a list-valued
#   `mut` post-state would impose an order the real callee does not have and
#   would reject a correct impl that recorded the same pair in another position.
#   The three C-import rivals attack the clause as it is actually stated.
# DIVERGENCE / NON-TERMINATION: NO SPEC HOLE. The sibling ships no divergence
#   case, so this is not a dropped port, and the class is CLOSED here by the
#   semantics. This slot has been rewritten twice and both earlier versions are
#   RETRACTED IN FULL; what follows is the current re-measurement, on scratch
#   copies, with the bundle itself unmodified.
#
#   The setting, read rather than assumed. Solution.lean line 4 is `set_option
#   loom.semantics.termination "total"` and line 7 is `open TotalCorrectness
#   DemonicChoice`; Solution_prepatch.lean matches. The two lines cannot disagree,
#   because the `set_option` elaborator itself opens the matching scope
#   (Loom/MonadAlgebras/WP/Options.lean, `openScope`, where "total" opens
#   `TotalCorrectness`), and Velvet/Syntax.lean:386 opens the same scope by
#   default. There is no `open PartialCorrectness` in this bundle.
#
#   What total semantics gives. A postcondition is claimed of ALL runs, not only
#   terminating ones, so a diverging impl does NOT satisfy `ensures` vacuously.
#   `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop` takes
#   `measure : β -> Nat` and emits a per-iteration obligation
#   `with_name_prefix `decreasing (measure b' < measure b)`. The
#   `PartialCorrectness` twin takes `measure : β -> Option Nat` and DISCARDS it,
#   which is the behaviour both retracted versions of this note were describing,
#   but that twin is not the one this bundle elaborates under.
#
#   FIRST RETRACTION (already recorded here, restated for the record). An earlier
#   version claimed the bundle was not "total" and reported a `while true do
#   pure ()` body verifying at exit 0. Re-run, that impl is REJECTED, exit 1:
#     error: Decreasing annotations are required in total correctness semantics
#     error: unsolved goals   case «done_1:  ¬ true »
#   So the annotation-free diverging prefix is caught.
#
#   SECOND RETRACTION, and the substantive correction. The version that replaced
#   it conceded the annotation-free sub-class but escalated a NARROWER hole: that
#   `decreasing` is required to be PRESENT but not TRUE, so an increasing or
#   constant measure is accepted and the resulting unreachable exit makes the
#   ensures vacuous. That is FALSE. The measure obligation is discharged like any
#   other goal, and both shapes that note quoted are refused on the measure's own
#   descent goal. Re-measured verbatim, exit 1 each:
#     * `while true` / `invariant True` / `done_with False` / `decreasing i`,
#       body `i := i + 1`  ->  `unsolved goals`, and the residual goal is
#       `case decreasing_1: i ... |- i + 1 < i`;
#     * the constant-measure variant, `decreasing j` with `j` never written
#       (body advances a different counter)  ->  `unsolved goals`, residual goal
#       `case decreasing_1: j ... |- 3 < 3`.
#   The annotation is therefore required to be TRUE, not merely present. The
#   `done_with False` clause buys nothing, because the build never reaches the
#   post-loop value goal: it stops on the descent obligation at the `method`
#   itself. Every downstream claim in the retracted text (the `assert (1 = 2)`
#   control pair surviving after a diverging loop, `done_with` being load-bearing
#   for a vacuity effect, "a defect in the verifier's termination checking") rests
#   on those exit-0 builds and falls with them. There is no escalation here.
#
#   Why no reject case is shipped, which is a WITNESS-side limit and not a spec
#   gap. A reject case needs a witness that ELABORATES against the rival and FAILS
#   against gold, and both diverging shapes defeat the first half, for two
#   DIFFERENT reasons. Measured through the gate's own `_check_witness`:
#     * NO measure: the refusal is raised at the `method` DECLARATION, which the
#       witness file retains (it strips only `prove_correct`), so the module does
#       not compile and even `example : True := trivial` returns
#       `witness-unproven`.
#     * MEASURE PRESENT BUT FALSE: the refusal moves to the `prove_correct` site,
#       which the witness file DOES strip, so the module elaborates and a trivial
#       witness succeeds. A real witness still fails, because the rival keeps a
#       `while` and its post-image is an unreduced `forIn Lean.Loop.mk ...
#       invariantGadget ... decreasingGadget` term the kernel will not normalise;
#       the build ends `unsolved goals` on that term. `witness-unproven` again.
#   A `witness_reference` cannot rescue either shape, since it substitutes the gold
#   subject while the failure is on the rival side. Note also that this
#   cell's frozen impl contains NO loop, so no descent obligation arises for the
#   gold body and the class can only be exercised by splicing a prefix, as above.
#   Spec-side verdict on divergence: REJECT. Recorded here so the absence of a
#   `diverge-*` case reads as the witness contract plus a loop-free impl, not as
#   an unmeasured gap and not as a hole.
#
#   INDEPENDENTLY RE-MEASURED BY AUDIT, on scratch copies, all three shapes
#   spliced as a prefix ahead of the frozen impl. Every number above reproduces:
#     * no measure (`while true do i := i + 1`)         -> variant exit 1
#       ("Decreasing annotations are required in total correctness semantics"),
#       and its witness file exit 1 even for `example : True := trivial`, because
#       the refusal is at the `method` the witness file retains — so the class is
#       genuinely unshippable rather than merely unshipped;
#     * `decreasing i` with body `i := i + 1` (increasing) -> variant exit 1;
#     * `decreasing j` with `j` never written (constant)   -> variant exit 1;
#       for both of these the trivial witness elaborates (exit 0, the refusal
#       having moved to the stripped `prove_correct`) while the real tester
#       witness fails (exit 1), which is exactly the `witness-unproven` shape the
#       note describes.
#   So the annotation is required to be TRUE and not merely present, the two
#   retractions above stand, and the disposition "closed class, no shippable
#   reject case" is confirmed — NOT "known hole" (which would be the correct
#   reading only under `termination "partial"`, and line 4 says "total").
# AXIOM_TESTS: the sibling's list is already EMPTY (no consumed @ContractOnly
#   axioms; its `ctor`/`rendered` are A-references covered by G-AX). Likewise
#   here: the `axioms` region declares nothing and the constructor-spelling
#   resolver is an A-reference validated by axiom_check.py — now in BOTH
#   configurations and for its recording effect, which is what closes the blind
#   spot the faithfulness review named (the old G-AX asserted the default
#   configuration only). The gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE of the 15 reject witnesses over the three input
#   binders of the two ensures clauses. The 15 input points are all DISTINCT:
#     (true, 1, 2)  (true, 3, 7)  (true, 7, 2)  (true, 2, 9)  (true, 6, 11)
#     (true, 8, 3)  (true, 12, 5) (true, 5, 4)  (true, 0, 1)  (false, 1, 2)
#     (true, 10, 4) (false, 11, 6) (true, 9, 8) (false, 3, 4) (true, 13, 2)
#     qualified — takes BOTH values: `true` at 11 points and `false` at 4
#         ((false, 1, 2), (false, 11, 6), (false, 3, 4), and note (false, 1, 2)
#         and (true, 1, 2) are the SAME integer pair at the two configurations,
#         so the Bool binder is varied with everything else held fixed). Three
#         rivals are refutable ONLY at a particular value of this binder
#         (weak-config-blind-qualified and weak-import-only-when-qualified only
#         at `false`, weak-config-blind-bare only at `true`), so the binder is
#         genuinely load-bearing and not decorative.
#     p — takes 13 distinct values: 1, 3, 7, 2, 6, 8, 12, 5, 0, 10, 11, 9, 13.
#         Includes the boundary 0, single- and multi-digit magnitudes, and values
#         both smaller and larger than the paired `q`.
#     q — takes 11 distinct values: 2, 7, 9, 11, 3, 5, 4, 1, 6, 8. Includes the
#         boundary 1, a multi-digit magnitude (11), and values both smaller and
#         larger than the paired `p`. Crucially (3, 7) and (7, 2) exchange the
#         roles of the two magnitudes, so neither integer binder is held at a
#         fixed value nor at a fixed relation to the other across the battery.
#     relative text length of the two parts — probed in both directions:
#         numerator text shorter than denominator's (6, 11), longer (12, 5), and
#         equal (1, 2), so a rival sensitive to the parts' lengths is caught.
#     SIGN of the numerator — PROBED, by `weak-sign-dropped` at (true, -5, 2),
#         which is the 16th reject point and the only negative one. The rival
#         renders `|p|`, so it agrees with the frozen solution at every one of
#         the 15 non-negative points above and diverges only where `p < 0`; no
#         other rival senses the sign at all. Its witness is stated over the
#         `mpfRationalExec` projection rather than the tester, because the
#         tester's `decide` is what gets stuck on a negative literal — see the
#         docstring's retraction. The sign of `q` is left unprobed as a
#         deliberate economy, not a limit: `render` passes both integers through
#         the SAME `toString`, so the numerator rival already pins that the
#         decimal text is taken from the argument itself rather than from its
#         magnitude, and G-CONF (200k fuzzed observations over both
#         configurations, 0 disagreements) plus G-PANEL-2's boundary set cover
#         the denominator's sign over negatives.
#   Every independent clause of the two ensures is attacked by some rival: both
#   wrappings jointly (weak-bare-ratio), the denominator's wrapping alone
#   (weak-denominator-unwrapped), the numerator's alone
#   (weak-numerator-unwrapped), the operand order (weak-transposed-operands), the
#   constructor spelling (weak-truncated-constructor), the division operator
#   (weak-no-division-operator), the parenthesised application
#   (weak-constructor-not-applied), the whole rendering (weak-empty-rendering),
#   the configuration branch in each direction and its direction of association
#   (weak-config-blind-qualified, weak-config-blind-bare, weak-config-inverted),
#   and the recording effect's presence, configuration-independence and content
#   (weak-import-dropped, weak-import-only-when-qualified,
#   weak-import-transposed). Beyond the clauses, the obligation's universal
#   QUANTIFICATION over the three binders is attacked by weak-f2p-point-only, the
#   one rival that is correct at the F2P-shaped point and wrong away from it, and
#   the numerator's SIGN is attacked by weak-sign-dropped, the one rival that
#   agrees with the frozen solution at every other witness point. Both
#   obligations are DEFENDED (5 soundness positives + 1 admissibility) and
#   ATTACKED (16 uniqueness rivals).
#
#   SIGN, third measurement (SUPERSEDES the two notes this line replaced): the
#   sign is now PROBED by a shipped rival with a kernel-only witness, so the
#   earlier "unprobeable" and "unprobeable by any kernel-reducible witness"
#   entries are both retracted. `native_decide` does close the negative
#   `toString` goal but is inadmissible (pbt_witness._WITNESS_BANNED, the
#   `ofReduceBool` compiler-trust axiom) and is NOT what the shipped witness
#   uses: stating the refutation over `mpfRationalExec` with the two literals'
#   decimal texts as hypotheses leaves a goal whose only numeral is positive,
#   which plain `decide` closes. See the module docstring's retraction for the
#   exit codes and the forgery pair.
#
# INDEPENDENT AUDIT PROBES (attacks D and E), all built out of band on scratch
# copies. Recorded because a battery's own case list cannot show what was tried
# AGAINST the spec and failed to break it.
#   NEW WRONG impls, all REJECTED (so no spec hole found): the sign rival now
#   shipped as `weak-sign-dropped`; a duplicated recording (`mpfImport ++
#   mpfImport`); an over-recording (`mpfImport ++ [("math","sqrt")]`); a
#   special-case cheat at one large numerator; a rendering that resolves the
#   spelling per configuration in the numerator's position but inverts it in the
#   denominator's (so the SAME-spelling half of C-config is pinned too); a
#   trailing-space rendering; and a clamp of `q = 0` to `1`.
#   NEW CORRECT reshapes, all VERIFY (so no soundness hole): the spelling built
#   by prefixing (`(if qualified then "mpmath." else "") ++ "mpf"`); a `match`
#   instead of an `if`; the two parts assembled denominator-first; the whole
#   rendering written with `String.append` rather than `++`; and the recording
#   given as a `::` cons. The last three needed a retuned tactic body and NOT a
#   weaker spec — worth recording, because a reshape whose frozen proof does not
#   close is easy to misread as SPEC-TOO-STRONG: `String.append` is definitionally
#   `++` but `simp [String.append_assoc]` does not bridge the two spellings, and
#   `simp only [render, show ∀ a b : String, String.append a b = a ++ b from
#   fun _ _ => rfl, String.append_assoc]` does.
#   ADMISSIBILITY LIVENESS re-confirmed: flipping a value pinned by
#   `admiss-grounded`'s assert (`render true 1 2` to the "…mpf(3)" spelling) makes
#   the variant FAIL with "decide proved … is false", so the assert is load-bearing
#   and the positive is not passing on a vacuous obligation.
#   FRAME-MUTATION vacuity re-confirmed rather than accepted: writing `p := p + 1`
#   into the read-only binder does not merely fail a postcondition, it is refused
#   by the language ("`p` cannot be mutated, only variables declared using
#   `let mut` can be mutated"), so the sibling's permission-based pair has no
#   analogue here and the omission is genuinely vacuous, not a skipped port.
AXIOM_TESTS = []
