"""properties.py — G-PBT falsification battery for sympy__sympy-16766 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct renderAccess`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness ELABORATES against the rival and FAILS
against a second subject that satisfies the spec. Here that second subject is a
declared ``witness_reference``, NOT the frozen solution — gold's loop does not
reduce in the kernel, so a witness against it is stuck rather than refuted; see
the CARRIER NOTE for the measured control and the reasoning).

DEFENDED SURFACE (one contracted method over two read-only sequence inputs):

  renderAccess (base : List Char) (indices : List (List Char))
      return (out : List Char)
    ensures out = accessRender base indices

The method assembles the supported rendering of an element access of a
subscriptable carrier: the carrier symbol's already-rendered text, then the
already-rendered subscript fragments joined by the two-character separator ", "
and wrapped in square brackets — and nothing else. The single load-bearing
``ensures`` pins ``out`` to the fully-unfolded pure model:

  ``accessRender base indices = base ++ "[".toList ++ joinComma indices ++ "]".toList``
  ``joinComma [] = []`` ; ``joinComma [x] = x`` ;
  ``joinComma (x :: y :: rest) = x ++ ", ".toList ++ joinComma (y :: rest)``

There is NO opaque answer-key to echo: the ``axioms`` region is empty and
``accessRender`` / ``joinComma`` are fully-unfolded ``def``s over the method's
own two arguments, so the unique satisfier IS the honestly-assembled access
string. The single top-level clause combines several independently-attackable
sub-obligations:

  * CARRIER PREFIX: the result begins with ``base`` (the carrier symbol's text).
  * BRACKETS: the joined subscripts are wrapped in ``[`` / ``]`` specifically.
  * SEPARATOR: consecutive subscript fragments are joined by ", " (the
    two-character comma-space), with no leading or trailing separator.
  * NO SURROUNDING TEXT: nothing precedes the carrier prefix (in particular no
    "unsupported construct" annotation) and nothing follows the closing bracket.
  * ORDER / ELEMENT-WISE: the subscript fragments appear in their given order,
    all of them, none special-cased by position, over the WHOLE input domain
    (every ``indices`` length ≥ 0, and in particular the single-fragment case).

Both input binders are load-bearing: ``base`` supplies the carrier prefix;
``indices`` supplies the fragments, their order, and (through ``joinComma``) the
separator structure.

CARRIER NOTE — THE DECIDABLE BOUNDARY, AND WHY GOLD IS NOT THE SECOND SUBJECT.
The gold impl is a backward ``while`` loop under
``loom.semantics.choice "demonic"``, so it elaborates through ``Classical.choice``
and its extracted ``renderAccessExec`` does NOT reduce in the kernel. A witness
stated against the frozen solution therefore gets STUCK rather than decided:
``decide`` reports the tester instance "did not reduce to `isTrue` or `isFalse`".

That stuck build must NOT be read as the second half of the discriminator, and
an earlier revision of this file described it that way. It is not a refutation:
the failure is byte-identical for a claim and for its NEGATION. Measured, same
input ``base=['q'] indices=[['0']]``, frozen solution as subject:

  * ``renderAccessTester ['q'] [['0']] = false`` (the real witness) -> exit 1,
    "did not reduce to `isTrue` or `isFalse`"
  * ``renderAccessTester ['q'] [['0']] = true``  (the exact OPPOSITE claim, i.e.
    a FORGERY asserting the rival is correct there) -> exit 1, same message
  * ``(1 : Nat) + 1 = 2`` -> exit 0, so the cell is not simply broken

Gold's exit code consequently carries NO information here, which is precisely
the ``witness-undecided`` defect the gate screens for (``gates/pbt.py``
``_STUCK_REDUCTION``).

So each reject case names an explicit ``witness_reference`` instead: the
loop-free ``return accessRender base indices`` impl of this SAME frozen spec,
which the gate independently checks (a) shares the frozen spec and (b) VERIFIES,
before refuting the witness against it. An impl the verifier accepts cannot
violate its own spec, so a genuine "the spec is violated at this input" claim
must fail there — and unlike gold, this subject DECIDES, in both directions:

  * reference, ``… = true``  -> exit 0 (``decide`` computes the correct impl's
    tester to ``true``: it passes its own postcondition at that input)
  * reference, ``… = false`` -> exit 1, "``decide`` proved that the proposition
    ``renderAccessTester ['q'] [['0']] = false`` is false"

Every rival below is a loop-free straight-line closed form whose extracted
program reduces by kernel computation, so ``renderAccessTester base indices``
(from ``derive_tester_for renderAccess``) evaluates to a literal ``Bool`` and
each witness closes by ``decide`` at fully-concrete literal inputs.
Discrimination is by VALUE and is a computed SEMANTIC refutation on both halves:
against the rival ``tester … = false`` elaborates, and against the reference the
same claim is refuted by computation ("proved that the proposition … is false"),
never by a stuck reduction, a missing identifier, a type error or a timeout. The
carrier at every witness is concrete (``List Char`` / ``List (List Char)``
literals of single characters), so no hypothesis is assumed and there is no
joint-satisfiability obligation (``consistency_probe`` is ``None`` for all of
them). Confirmed by real ``scripts/lean_verify.sh`` builds: per reject case, the
witness against the rival (exit 0), against the frozen solution (exit 1, stuck —
recorded here as evidence that gold cannot serve, not as a refutation), and
against the reference (exit 1, computed refutation). Independently re-derived by
the audit, which additionally ran the FORGED (claim-flipped) build on all three
subjects per case: gold stuck in both directions with only the echoed literal
differing (so its exit code is claim-independent), the reference exit 0 on the
forged claim and exit 1 on the real one (so its exit code tracks the claim), and
the rival exit 1 on the forged claim (so it really does violate the
postcondition there). See the WITNESS DISCRIMINATION block in the footer.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Two structurally different but
    behaviourally identical correct impls (return the grounded model
    ``accessRender base indices`` directly with no loop; and the loop with its
    per-step branch ARMS SWAPPED, so the general ``i < indices.length`` case leads
    and the base case moves to the else) must verify, else the spec is
    SPEC-TOO-STRONG on the impl shape. Both reprove: the direct-model form with a
    bare ``loom_solve``, the arm swap with a retuned loop-step script. Only the
    tactic body — elided from the spec view — is retuned, so ``same_spec`` holds.
    Note on what makes a positive load-bearing: an earlier revision used, as the
    second control, a reshape that bound the frozen conditional to a ``let`` local
    before assigning it, and kept the frozen proof verbatim. The proof still
    closing was the warning sign, not the reassurance — the ``let`` is a
    beta-redex the elaborator discharges, so that variant is DEFINITIONALLY EQUAL
    to the frozen impl and cannot witness anything about shape-sensitivity. The
    arm swap changes the emitted branch condition and genuinely needs a reproof.
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame rivals that WRITE through read-only inputs held at fractional
    heap permissions (``Acc(list_pred(name), 1/2)`` and
    ``Acc(list_pred(index_renderings), 1/2)``). Lean and Velvet are referentially
    transparent: ``base`` and ``indices`` are immutable values, this bundle
    declares NO ``mut`` binder for them, and there is no heap and no aliasing — so
    there is no read-only input to overwrite and no permission system to trip. Not
    fabricated (per the porting map, this class is vacuous on a
    referentially-transparent backend). See the footer for the accounting.
  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE SPEC, and re-measured rather
    than argued. Two earlier revisions of this file each got this wrong in a
    different direction: one claimed the ``done_with i = 0`` measure closes the
    hole "structurally" (a statement about the frozen impl, which says nothing
    about what a RIVAL may write), and one claimed this bundle sets
    ``loom.semantics.termination "partial"`` and cited an internal escalation over
    a 401-bundle ``partial`` cohort as a known spec hole. That second claim was
    materially FALSE, twice over: line 4 of the frozen solution reads
    ``set_option loom.semantics.termination "total"``, and there is no ``partial``
    cohort to belong to either, since all 500 velvet bundles set ``"total"`` and
    open ``TotalCorrectness``. Under total-correctness semantics a postcondition is
    claimed of ALL runs rather than only terminating ones, so the verifier demands
    a decreasing measure on every loop and a diverging rival is genuinely rejected.
    Measured here with three real builds: a ``while true`` prefix ahead of an
    otherwise correct body, and an unbounded ``while k ≥ 0`` returning the
    unambiguously wrong ``[]``, both exit 1 at the method header with
    ``error: Decreasing annotations are required in total correctness semantics``;
    and the sharper shape that CARRIES a measure the verifier cannot show
    decreasing (``let mut q : Nat := 1; while q > 0 / invariant 0 ≤ q /
    done_with q = 0 / decreasing q do q := q``) is REJECTED on the measure's OWN
    descent goal, ``case «decreasing_1: q»``, residual ``⊢ q < q``. That third
    build is the decisive one: the refusal is not the annotation linter, so
    supplying an annotation launders nothing. So the class is neither a spec hole
    nor structurally impossible: the spec catches it.
    It is nevertheless NOT SHIPPABLE as a ``reject`` case on this carrier, and the
    reason is the witness contract rather than the spec. That same
    ``Decreasing annotations are required`` error is a MODULE-level elaboration
    failure: it fires in the witness file too (the ``method`` survives there), so
    the witness build against the diverging rival exits 1 and the gate records
    ``witness-unproven`` — an inconclusive outcome — for a rival the spec in fact
    rejects. Measured: the rival's own witness build carries that header error
    plus a non-reducing tester (``decide`` "did not reduce to ``isTrue`` or
    ``isFalse``"), because a method that failed to elaborate extracts no program.
    The nagini sibling carries NO ``diverge-*`` / ``nonterm-*`` / ``weak-diverge``
    case either, so nothing is being dropped from the design document. Recorded as
    "closed by the spec, unshippable as a witnessed reject case", with the exit
    codes above as the demonstration.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a fully-unfolded pure function
    of the two input binders; there is no answer-key term a wrong impl could echo.
    The cheapest correct impl assembles the access string honestly, which the
    positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of the
    domain right yet diverges on one sub-obligation (parentheses for brackets; a
    bare comma for the ", " separator; a leading annotation character; the
    brackets dropped on the single-fragment sub-domain; the carrier prefix
    dropped; the fragment order reversed).

ADMISSIBILITY — PORTED, as ``admiss-f2p-post-image``. The sibling's control
asserts an F2P-shaped input (an ``Indexed`` always carries ≥ 1 subscript)
satisfies its ``Requires(len(index_renderings) >= 1)`` precondition. It is true
that this backend's method has NO ``require`` clause, so the precondition admits
every input trivially — but an earlier revision of this file stopped there and
recorded the whole lane DEGENERATE, which is the wrong disposition. The analogue
of PRECOND-TOO-STRONG on a TOTAL carrier is not "the precondition rejects a
normal input"; it is the OBLIGATION being unsatisfiable, or degenerately
satisfiable, at exactly an F2P-shaped input. That is a live risk a
``verify``-lane case tests directly and no reject case tests at all: the reject
lane shows six rivals FAIL the postcondition, which establishes the post-image is
not satisfied by everything, but it cannot establish that the post-image demanded
at the F2P point is the RIGHT one — six wrong impls all failing is equally
consistent with an obligation nothing can meet there.

So the ported case discharges, by evaluation, an in-region ``assert`` at the
concrete F2P input before closing the frozen obligation verbatim: that
``accessRender ['p'] [['0'], ['1']]`` is exactly ``"p[0, 1]".toList`` AND that it
DIFFERS from the rendering of the same two subscripts transposed. The first
conjunct pins the post-image to the literal F2P string (so the obligation is
satisfiable there, and satisfiable at the right value); the second shows it is
non-degenerate at that point (the model genuinely discriminates the input, rather
than collapsing every input to one image). The assert is LIVE, not decoration —
measured with two false controls that differ only in the claim: spelling the
target ``"p[0,1]"`` (the wrong separator) fails, exit 1, and weakening the second
conjunct from ``≠`` to ``=`` fails, exit 1, while the true claim verifies, exit 0.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` — the components
the rendering is assembled from (the carrier's text and each subscript's rendered
text) are the outputs of UNCHANGED helpers, modeled as the free input carrier,
and the assembly itself is modeled DEEPLY as ``accessRender`` / ``joinComma``.
The nagini file's AXIOM_TESTS drive the real post-patch printer in Docker (G-AX's
job); this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-16766"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the ENTIRE frozen loop body (between and INCLUDING
# ---- the markers). Lies wholly inside the single `-- impl-start`/`-- impl-end`
# ---- region and is unique in Solution.lean (both facts asserted at load by
# ---- the assert below).
_IMPL = """    -- impl-start
    let mut joined : List Char := []
    let mut i := indices.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ indices.length
      invariant joined = joinComma (indices.drop i)
      done_with i = 0
      decreasing i
    do
      let piece := indices[i - 1]!
      joined := if i = indices.length then piece else piece ++ ", ".toList ++ joined
      i := i - 1
    return base ++ "[".toList ++ joined ++ "]".toList
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen loop
# ---- body. A positive control that drops the loop entirely retunes it to a bare
# ---- `loom_solve`; both the impl region and the `prove_correct` body are elided
# ---- from the spec view, so same_spec still holds and the `prove_correct
# ---- renderAccess` obligation survives with an identical header. Unique.
_PROOF = """prove_correct renderAccess by
  loom_solve
  all_goals
    first
      | (rw [joinComma_drop_step indices i (by omega) (by omega)]; simp_all)
      | simp_all [accessRender]"""
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl_block(body):
    return "    -- impl-start\n" + body + "\n    -- impl-end"


def _rewrite_impl(body):
    """Full variant: impl body replaced, spec + frozen proof left intact. For
    rivals (expected NOT to verify) and for positive controls whose frozen proof
    still closes."""
    return _swap(_BASE, _IMPL, _impl_block(body))


# ---- the frozen impl body WITHOUT its markers, for the admissibility case,
# ---- which prepends an in-region `assert` and keeps the rest verbatim so the
# ---- method's own obligation still discharges unchanged.
_IMPL_INNER = _IMPL[len("    -- impl-start\n"):-len("\n    -- impl-end")]


def _assert_then_gold(claim, proof_extra):
    """Frozen impl prefixed by an in-region `assert claim`, frozen proof plus
    `proof_extra` to clear the extra assert goal. Both edited regions are elided
    from the consumer spec view, so `same_spec` holds and the `prove_correct
    renderAccess` header survives byte-identically."""
    body = ("    assert (with_name_prefix `admiss\n      (" + claim + "))\n"
            + _IMPL_INNER)
    return _swap(_swap(_BASE, _IMPL, _impl_block(body)), _PROOF,
                 _PROOF + proof_extra)


# Clears the single extra goal the in-region assert leaves. `decide` evaluates
# the concrete claim; the `simp_all` arm is the frozen fallback for the method's
# own goals, which are unchanged.
_ADMISS_PROOF_EXTRA = ("\n  all_goals first\n    | decide\n"
                       "    | simp_all [accessRender]")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `renderAccessTester base indices = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input. Checked
# ---- in a file whose `prove_correct` block has been stripped, so no tactic
# ---- script can mask the verdict.
def _tester(body):
    return ("extract_program_for renderAccess\n"
            "prove_precondition_decidable_for renderAccess\n"
            "prove_postcondition_decidable_for renderAccess\n"
            "derive_tester_for renderAccess\n\n" + body)


# ---- witness_reference: the second subject every witness is refuted against.
# ---- The frozen impl's `while` loop under `loom.semantics.choice "demonic"`
# ---- elaborates through `Classical.choice`, which the kernel cannot unfold, so
# ---- `decide` against gold is STUCK for every claim and its exit code
# ---- discriminates nothing (see the CARRIER NOTE for the measured
# ---- claim-vs-negation control). This loop-free impl of the SAME frozen spec
# ---- does reduce, so the refutation is computed rather than stuck. The gate
# ---- checks it shares the frozen spec and VERIFIES before trusting it, which is
# ---- what makes it a sound stand-in for gold: an impl the verifier accepts
# ---- cannot violate its own spec. It is the `pos-return-model` positive's
# ---- module, so it is independently required to verify by that case too.
_REFERENCE = _swap(_rewrite_impl("    return accessRender base indices"),
                   _PROOF, "prove_correct renderAccess by\n  loom_solve")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-return-model",
        "kind": "soundness",
        "expect": "verify",
        # Maximally different correct impl: drop the loop entirely and return the
        # grounded pure model `accessRender base indices` directly. `accessRender`
        # is a total function of the two inputs (no opaque answer-key), so this is
        # a correct impl, not an echo. The residual goal is definitional, closed
        # by a bare `loom_solve` (the frozen loop-specific rewrite is not needed
        # and is dropped — the tactic body is elided from the spec view, so
        # same_spec and the obligation header are untouched).
        "module": _REFERENCE,
        "rationale": (
            "the cheapest honest correct impl returns the grounded pure model "
            "`accessRender base indices` directly (no loop at all — maximally "
            "different from the gold backward `while`). The ensures is literally "
            "`out = accessRender base indices`, so it holds on the whole domain "
            "and a bare `loom_solve` discharges the definitional residual. If this "
            "failed the spec would be over-fit to the loop shape "
            "(SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: the "
            "model IS the real assembly work, so returning it is correct, not a "
            "cheat. (Sibling: pos-control-oracle-direct.)"),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # The sibling's positive, ported LITERALLY: the per-step branch arms are
        # swapped so the `i < indices.length` general case comes first and the
        # `i = indices.length` base case moves to the else. This is a genuinely
        # different CONTROL-FLOW shape (the branch condition itself changes), not
        # a renaming: `joinComma_drop_step` is stated for the `i = length`
        # orientation, so the frozen tactic script no longer closes and the case
        # retunes the proof body to case-split on `i = indices.length` and
        # normalise `getElem!` to the `getElem?.getD` form the loop goal is
        # stated in. Retuning the tactic body is admissible — it is elided from
        # the spec view, so same_spec holds and the obligation header is
        # byte-identical.
        #
        # An earlier revision shipped, in this slot, a `let step := …` reshape
        # that merely bound the SAME conditional expression to a local before
        # assigning it. That is definitionally equal to the frozen body (the
        # `let` is a beta-redex the elaborator discharges), which is why it kept
        # the frozen proof verbatim — and a positive whose "different shape" the
        # elaborator erases tests nothing about the spec's shape-sensitivity. It
        # was replaced by the sibling's actual arm swap, which does change the
        # emitted control flow and does require a real reproof.
        "module": _swap(_rewrite_impl(
            "    let mut joined : List Char := []\n"
            "    let mut i := indices.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ indices.length\n"
            "      invariant joined = joinComma (indices.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let piece := indices[i - 1]!\n"
            "      joined := if i < indices.length then piece ++ \", \".toList ++ joined else piece\n"
            "      i := i - 1\n"
            "    return base ++ \"[\".toList ++ joined ++ \"]\".toList"),
            _PROOF,
            "prove_correct renderAccess by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (rw [joinComma_drop_step indices i (by omega) (by omega),\n"
            "         List.getElem!_eq_getElem?_getD]\n"
            "       by_cases hlt : i = indices.length <;> simp_all <;> omega)\n"
            "    | simp_all [accessRender]"),
        "rationale": (
            "structurally-different CORRECT impl, ported literally from the "
            "sibling: the per-step branch ARMS are swapped, so the general "
            "`i < indices.length` case leads and the `i = indices.length` base "
            "case becomes the else. The emitted control flow genuinely differs "
            "(the branch condition changes, so this is not a beta-redex the "
            "elaborator erases), yet the behaviour is identical, so it must "
            "verify — else the spec is over-fit to the frozen impl's branch "
            "orientation => SPEC-TOO-STRONG. It does verify (exit 0) once the "
            "tactic body is retuned to case-split on `i = indices.length`; the "
            "frozen script verbatim fails with `unsolved goals` on the loop "
            "invariant, which is a fact about the SCRIPT (tuned to the frozen "
            "orientation of `joinComma_drop_step`) and NOT about the spec. A "
            "positive is entitled to reprove: the tactic body is elided from the "
            "spec view. (Sibling: pos-control-branch-reorder.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — the PRECOND-TOO-STRONG direction, in its total-carrier
    # form: not "does the precondition admit a normal input" (there is no
    # `require` clause to be too strong) but "is the obligation SATISFIABLE, at
    # the right value, and NON-DEGENERATE at exactly an F2P-shaped input". See
    # the ADMISSIBILITY section of the module docstring.
    # =====================================================================
    {
        "id": "admiss-f2p-post-image",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl kept VERBATIM (so the method's own obligation discharges
        # unchanged) with an in-region `assert` prepended that must be discharged
        # BY EVALUATION at the concrete F2P-shaped input: the two-subscript
        # access renders to exactly the expected literal, and that rendering is
        # distinct from the transposed-subscript rendering.
        "module": _assert_then_gold(
            "accessRender ['p'] [['0'], ['1']] = \"p[0, 1]\".toList\n"
            "        ∧ accessRender ['p'] [['0'], ['1']] "
            "≠ accessRender ['p'] [['1'], ['0']]",
            _ADMISS_PROOF_EXTRA),
        "rationale": (
            "the obligation is SATISFIABLE, at the RIGHT value, and NON-DEGENERATE "
            "at an F2P-shaped input. The in-region assert is discharged by "
            "evaluation at the concrete two-subscript input: the post-image is "
            "exactly the expected `p[0, 1]` literal (first conjunct — satisfiable, "
            "and pinned to the correct value rather than merely to something), and "
            "it DIFFERS from the rendering of the same two subscripts transposed "
            "(second conjunct — the model discriminates its input rather than "
            "collapsing the domain to one image). Must verify, else the obligation "
            "is unsatisfiable or degenerate exactly where the behaviour matters => "
            "PRECOND-TOO-STRONG in its total-carrier form. The reject lane cannot "
            "establish this: six rivals failing the postcondition is equally "
            "consistent with an obligation nothing can meet. The assert is LIVE — "
            "two false controls differing ONLY in the claim both fail (exit 1): "
            "spelling the target `\"p[0,1]\"` with the wrong separator, and "
            "weakening the second conjunct from `≠` to `=`. (Sibling: "
            "admiss-in-domain, whose `Requires(len >= 1)` has no analogue here — "
            "the pre-conditions region is empty — so the probe is re-aimed at the "
            "post-image rather than dropped.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free straight-line closed form with a
    # machine-checked refutation witness at a DISTINCT concrete input and the
    # refinement argument for why its faithful real counterpart would NOT resolve
    # the failing test. Each rival's extracted program reduces by kernel
    # computation, so its witness discriminates by value (see the CARRIER NOTE);
    # the frozen spec and obligation header are untouched.
    # =====================================================================
    {
        "id": "rival-paren-not-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        # The joined fragments are correct; only the wrapping delimiters are
        # parentheses instead of square brackets.
        "module": _rewrite_impl(
            '    return base ++ "(".toList ++ joinComma indices ++ ")".toList'),
        "refinement": (
            "a faithful counterpart that wrapped the joined subscripts in "
            "parentheses instead of square brackets renders the access with the "
            "wrong delimiters (e.g. `p(0, 1)` where the fix demands `p[0, 1]`). "
            "The failing test asserts the exact bracketed rendering, so it FAILS — "
            "it would NOT resolve. Correct on the carrier prefix, the separator, "
            "and the fragment order; the divergence is exactly the delimiter "
            "choice. (Sibling: rival-paren-not-bracket.)"),
        "rationale": (
            "REJECT from the BRACKETS sub-obligation: `accessRender` wraps the "
            "join in `[` / `]`, and this impl wraps it in `(` / `)`, so `out` ≠ "
            "the model whenever the access is rendered. If it verified => "
            "SPEC-TOO-WEAK (the bracket delimiters unpinned). Refuted at "
            "base=['q'], indices=[['0']]: gold resolves `q[0]`, the rival `q(0)`."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : renderAccessTester ['q'] [['0']] = false := by\n  decide\n"),
    },
    {
        "id": "rival-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # The canonical wrong patch: join consecutive fragments with a bare comma
        # (no following space) instead of the two-character ", " separator.
        # `intersperse … |>.flatten` is a loop-free closed form that reduces under
        # `decide`. Diverges only when two-or-more fragments are joined.
        "module": _rewrite_impl(
            '    return base ++ "[".toList ++ (indices.intersperse ",".toList).flatten ++ "]".toList'),
        "refinement": (
            "this is the canonical wrong real patch: join the rendered subscripts "
            "with a bare `,` (no following space) rather than the two-character "
            "`, ` separator. It renders `p[0,1]` where the fix demands `p[0, 1]`, "
            "so the failing test's exact-string assertion FAILS — it would NOT "
            "resolve. Correct on the carrier prefix, the brackets, and any "
            "single-subscript access; the divergence is exactly the separator. "
            "(Sibling: rival-wrong-separator.)"),
        "rationale": (
            "REJECT from the SEPARATOR sub-obligation: `joinComma` places `, ` "
            "(comma-space) between consecutive fragments, and this impl places a "
            "bare `,`, so `out` ≠ the model whenever ≥ 2 subscripts are joined. If "
            "it verified => SPEC-TOO-WEAK (the two-character separator unpinned). "
            "Refuted at base=['p'], indices=[['0'], ['1']]: gold resolves "
            "`p[0, 1]`, the rival `p[0,1]`."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : renderAccessTester ['p'] [['0'], ['1']] = false := by\n  decide\n"),
    },
    {
        "id": "rival-surrounding-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # Prepend a leading annotation character to the assembled access — the
        # shape of the pre-change unsupported-node fallback (which prepends an
        # "unsupported construct" comment). Correct rendering, wrong surrounding
        # text.
        "module": _rewrite_impl(
            '    return "#".toList ++ base ++ "[".toList ++ joinComma indices ++ "]".toList'),
        "refinement": (
            "prepending a leading annotation character is the shape of the "
            "pre-change unsupported-node fallback, which emits an 'unsupported "
            "construct' comment before the code. Any leading content makes the "
            "rendered source differ from the fix's exact output, so the failing "
            "test FAILS — it would NOT resolve; this is precisely the pre-change "
            "state the fix repairs. Correct on the carrier prefix, brackets, "
            "separator and order; the divergence is the surrounding text. "
            "(Sibling: rival-surrounding-prefix.)"),
        "rationale": (
            "REJECT from the NO-SURROUNDING-TEXT sub-obligation: `accessRender` "
            "begins with `base` and nothing precedes it, but this impl prepends "
            "`#`, so `out` ≠ the model for every input. If it verified => "
            "SPEC-TOO-WEAK (a leading annotation admitted). Refuted at base=['p'], "
            "indices=[['5']]: gold resolves `p[5]`, the rival `#p[5]`."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : renderAccessTester ['p'] [['5']] = false := by\n  decide\n"),
    },
    {
        "id": "rival-partial-domain-single-index",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: correct on multi-subscript accesses but drops the
        # brackets on the single-subscript sub-domain. Identical to gold whenever
        # indices.length ≠ 1.
        "module": _rewrite_impl(
            "    return (if indices.length = 1 then base ++ joinComma indices\n"
            '      else base ++ "[".toList ++ joinComma indices ++ "]".toList)'),
        "refinement": (
            "a faithful counterpart that special-cased a single subscript to omit "
            "the brackets renders `p0` for `p[0]` while still rendering multi-index "
            "accesses correctly. It would pass a multi-index assertion but produce "
            "wrong source for any single-subscript access — the postcondition "
            "fixes the bracketed rendering for the WHOLE domain (every "
            "indices.length ≥ 0), so it regresses single-index rendering and does "
            "NOT resolve faithfully. Agrees with gold over the whole multi-index "
            "sub-domain; refuted at the distinguishing single-subscript input. "
            "(Sibling: rival-partial-domain-single-index.)"),
        "rationale": (
            "REJECT from the BRACKETS sub-obligation over the WHOLE domain: "
            "`accessRender` wraps `joinComma indices` in `[` / `]` for every "
            "input, but this impl drops them when exactly one subscript is "
            "present. If it verified => SPEC-TOO-WEAK (the single-subscript "
            "sub-domain unpinned). Refuted at base=['x'], indices=[['7']]: gold "
            "resolves `x[7]`, the rival `x7`."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : renderAccessTester ['x'] [['7']] = false := by\n  decide\n"),
    },
    {
        "id": "rival-drop-carrier-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        # The ONLY rival that abuses the `base` binder: omit the carrier prefix
        # entirely, rendering just the bracketed subscript list. Moves `base` off
        # the value the other witnesses pin it at (it becomes irrelevant to this
        # rival's output), so this is the witness that varies the `base` binder.
        "module": _rewrite_impl(
            '    return "[".toList ++ joinComma indices ++ "]".toList'),
        "refinement": (
            "a counterpart that dropped the carrier symbol's text emits `[0, 1]` "
            "where the fix demands `p[0, 1]` — the access loses the name it is "
            "subscripting. The failing test asserts the full rendering including "
            "the carrier symbol, so it FAILS — it would NOT resolve. Correct on "
            "the brackets, separator and order; the divergence is the missing "
            "carrier prefix. (Added: the sibling's `base` binder is otherwise "
            "unattacked, so without this rival no witness would move it and a "
            "rival mishandling only the carrier would go uncaught.)"),
        "rationale": (
            "REJECT from the CARRIER PREFIX sub-obligation: `accessRender` begins "
            "with `base`, and this impl omits it, so `out` ≠ the model whenever "
            "`base` is non-empty. If it verified => SPEC-TOO-WEAK (the carrier "
            "prefix unpinned — the ONLY rival on which `base` is the deciding "
            "value). Refuted at base=['p'], indices=[['a'], ['b']]: gold resolves "
            "`p[a, b]`, the rival `[a, b]`."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : renderAccessTester ['p'] [['a'], ['b']] = false := by\n  decide\n"),
    },
    {
        "id": "rival-empty-indices-no-brackets",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, at the one sub-domain every other witness misses:
        # `indices = []`. Correct for every non-empty subscript list; drops the
        # brackets entirely when there are no subscripts. The shipped witnesses
        # probe lengths 1 and 2 only, so before this case the length-0 boundary
        # of the ORDER/ELEMENT-WISE-over-the-WHOLE-DOMAIN clause was unpinned.
        "module": _rewrite_impl(
            "    return (if indices.length = 0 then base\n"
            '      else base ++ "[".toList ++ joinComma indices ++ "]".toList)'),
        "refinement": (
            "a faithful counterpart that treated an empty subscript list as "
            "'nothing to render' and returned the bare carrier text would emit `p` "
            "where the model demands `p[]`. It agrees with the fix on every access "
            "that actually carries subscripts — including the multi-subscript "
            "assertion the failing test makes — so it would pass that test while "
            "silently rendering the degenerate case differently from the model the "
            "spec fixes; it is not the fix's behaviour and would NOT resolve "
            "faithfully. Refuted at the distinguishing empty-subscript input. "
            "(Added by the audit: no shipped witness moved `indices` off lengths "
            "{1, 2}, so the length-0 boundary was untested.)"),
        "rationale": (
            "REJECT from the BRACKETS sub-obligation at the length-0 boundary: "
            "`accessRender base [] = base ++ \"[\".toList ++ [] ++ \"]\".toList`, "
            "i.e. the brackets are emitted even with no subscripts (`joinComma [] "
            "= []`), but this impl omits them, so `out` ≠ the model whenever "
            "`indices` is empty. If it verified => SPEC-TOO-WEAK (the empty-"
            "subscript sub-domain unpinned). Refuted at base=['p'], indices=[]: "
            "the model gives `p[]`, the rival `p`."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : renderAccessTester ['p'] [] = false := by\n  decide\n"),
    },
    {
        "id": "rival-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN (order): render the subscripts in REVERSE order. Correct
        # on any single-subscript access or a palindromic fragment list; wrong
        # whenever the order is observable. The only rival attacking the ORDER
        # sub-obligation.
        "module": _rewrite_impl(
            '    return base ++ "[".toList ++ joinComma indices.reverse ++ "]".toList'),
        "refinement": (
            "a counterpart that iterated the subscripts in reverse order renders "
            "`p[1, 0]` for `p[0, 1]`, transposing the access indices. The failing "
            "test asserts the subscripts in source order, so it FAILS — it would "
            "NOT resolve. Correct on any single-subscript access (order "
            "unobservable), so it agrees with gold over that sub-domain and is "
            "refuted at a distinguishing multi-subscript input where the order "
            "differs. (Added: no sibling rival attacks fragment ORDER; without it "
            "the element-wise/positional sub-obligation is untested here.)"),
        "rationale": (
            "REJECT from the ORDER / ELEMENT-WISE sub-obligation: `accessRender` "
            "joins `indices` in their given order, and this impl joins "
            "`indices.reverse`, so `out` ≠ the model whenever reversing changes "
            "the joined string. If it verified => SPEC-TOO-WEAK (fragment order "
            "unpinned). Refuted at base=['p'], indices=[['0'], ['9']]: gold "
            "resolves `p[0, 9]`, the rival `p[9, 0]`."),
        "witness_reference": _REFERENCE,
        "witness": _tester(
            "example : renderAccessTester ['p'] [['0'], ['9']] = false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling ships 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals — two of which are MANDATORY
# frame-mutation rivals; AXIOM_TESTS is empty). The sibling contracts
# `print_indexed(name, index_renderings)` over two `List`/`PSeq` inputs held at
# fractional read-only permissions. This backend models the SAME bracketed,
# comma-separated access assembly DEEPLY and CONCRETELY (`accessRender` /
# `joinComma` over `List Char` / `List (List Char)`), pins it with a single
# element-wise `ensures`, and has NO precondition and NO permission surface. Those
# carrier facts make two sibling classes vacuous/degenerate here.
#
#   nagini case                         kind          -> here                          disposition
#   ------------------------------------------------------------------------------------------------
#   pos-control-oracle-direct           soundness     -> pos-return-model              PORTED
#   pos-control-branch-reorder          soundness     -> pos-branch-reorder            PORTED (literal)
#   admiss-in-domain                    admissibility -> admiss-f2p-post-image         RE-AIMED
#   frame-mut-name-append               uniqueness    -> (none)                        VACUOUS
#   frame-mut-index-append              uniqueness    -> (none)                        VACUOUS
#   rival-wrong-separator               uniqueness    -> rival-wrong-separator         PORTED
#   rival-paren-not-bracket             uniqueness    -> rival-paren-not-bracket       PORTED
#   rival-surrounding-prefix            uniqueness    -> rival-surrounding-prefix      PORTED
#   rival-partial-domain-single-index   uniqueness    -> rival-partial-domain-single-index PORTED
#   (no sibling)                        uniqueness    -> rival-drop-carrier-prefix     ADDED
#   (no sibling)                        uniqueness    -> rival-reverse-order           ADDED
#   (no sibling)                        uniqueness    -> rival-empty-indices-no-brackets ADDED (audit)
#   (no sibling)                        divergence    -> (none)                        CLOSED BY SPEC
#   AXIOM_TESTS                         axiom         -> (none)                        N/A (G-AX)
#
# 4 uniqueness ported + 3 added; 2 soundness ported; 1 admissibility re-aimed;
# 2 frame-mutation vacuous; axiom lane dropped.
# 10 SPEC cases (2 soundness, 1 admissibility, 7 uniqueness).
#
# AUDIT REVISION (independent adversarial audit of the recorded SOUND). The port
# passed the gate, but three of its dispositions did not survive re-derivation and
# are corrected above:
#   1. TERMINATION SEMANTICS MISREAD. The docstring asserted this bundle sets
#      `loom.semantics.termination "partial"` and cited an escalation over a
#      401-bundle `partial` cohort as a known spec hole covering this cell. Line 4
#      of the frozen solution reads `"total"`, as does every velvet bundle's, so no
#      such cohort exists. Re-measured: two diverging rivals are REJECTED at
#      the method header (`Decreasing annotations are required in total
#      correctness semantics`, exit 1 each), and a third that CARRIES a
#      non-decreasing measure is REJECTED on the descent goal itself
#      (`case «decreasing_1: q»`, residual `q < q`), so the spec closes the class
#      in both shapes and not merely by requiring the annotation. The
#      class remains unshippable as a witnessed reject case, but for the witness
#      contract's reason (that error is module-level, so it breaks the witness
#      build too and the gate reads `witness-unproven`) — not because the spec
#      admits divergence. Recorded with both exit codes.
#   2. ADMISSIBILITY LANE DROPPED ON A BAD REASON. "The frozen obligation has no
#      precondition" is true and insufficient: the total-carrier analogue is the
#      obligation being unsatisfiable or degenerate at an F2P-shaped input, which
#      is expressible here and is now `admiss-f2p-post-image` (exit 0, with two
#      claim-only-differing false controls at exit 1 proving the assert is live).
#      It restores the only one of this gate's three directions the battery had
#      omitted entirely.
#   3. A POSITIVE THAT TESTED NOTHING. `pos-local-reshape` bound the frozen
#      conditional to a `let` local before assigning it — definitionally equal to
#      the frozen body, which is why it kept the frozen proof verbatim. A reshape
#      the elaborator erases cannot detect over-fitting. Replaced by the sibling's
#      LITERAL branch-arm swap (`pos-branch-reorder`), which changes the emitted
#      branch condition and required a genuine reproof (exit 0 retuned; exit 1
#      with the frozen script, confirming the reproof is real work).
# One rival was ADDED from the attack-D sweep: `rival-empty-indices-no-brackets`
# pins the `indices = []` sub-domain, the only length boundary no shipped witness
# touched (the six original witnesses probe lengths 1 and 2 only).
#
# PORTED (pos-control-oracle-direct -> pos-return-model): the sibling's cheapest
#   honest impl returns the grounded oracle. On this carrier the maximally-
#   different correct impl drops the loop entirely and returns the grounded model
#   `accessRender base indices`; it doubles as the no-ungrounded-echo control (the
#   model is the real assembly work, not an answer-key). Proof retuned to a bare
#   `loom_solve` (verified to build).
# PORTED, LITERALLY (pos-control-branch-reorder -> pos-branch-reorder): the
#   sibling's positive swaps the per-step branch arms (the `i < n` general case
#   leads, the base case moves to the else). That literal swap IS what ships here.
#   It does break the FROZEN tactic script — `joinComma_drop_step` is stated for
#   the `i = length` orientation, so the frozen proof verbatim fails `unsolved
#   goals` on the loop invariant, exit 1 (measured) — but that is a fact about the
#   SCRIPT, not the spec, and a positive is entitled to reprove: the
#   `prove_correct` body is elided from the spec view, so same_spec and the
#   obligation header are untouched. Retuned to normalise `getElem!` to the
#   `getElem?.getD` form the loop goal is actually stated in and then case-split
#   on `i = indices.length`, it VERIFIES (exit 0). So the spec admits the
#   sibling's shape.
#   An earlier revision shipped a typed-local reshape in this slot instead (bind
#   the per-step conditional to `step`, then assign it) precisely BECAUSE the
#   frozen proof still closed over it — and that is the tell: the `let` is a
#   beta-redex the elaborator discharges, so the variant is definitionally equal
#   to the frozen body and its "different shape" does not survive elaboration. A
#   positive that reduces to the frozen impl cannot detect over-fitting to the
#   frozen impl, so it passed honestly while testing nothing. Replaced.
# PORTED (the four value/branch rivals): rival-wrong-separator (bare `,` for the
#   `, ` separator — the canonical wrong patch and F2P discriminator);
#   rival-paren-not-bracket (parentheses for square brackets);
#   rival-surrounding-prefix (a leading annotation character — the pre-change
#   unsupported-node fallback shape); rival-partial-domain-single-index (drop the
#   brackets on the single-subscript sub-domain, correct on multi-index).
# ADDED (rival-drop-carrier-prefix): omit the carrier symbol's text. It is the ONLY
#   rival on which `base` is the deciding value and the only witness that moves the
#   `base` binder off a value irrelevant to the divergence — without it no witness
#   would exercise the carrier-prefix sub-obligation and a rival mishandling only
#   `base` would go uncaught.
# ADDED (rival-reverse-order): render the subscripts in reverse order. No sibling
#   rival attacks fragment ORDER; without it the element-wise/positional
#   sub-obligation (indices joined in their given order) is untested on this
#   carrier. Correct on single-subscript accesses; refuted at a multi-subscript
#   input where order is observable.
# RE-AIMED (admiss-in-domain -> admiss-f2p-post-image): the sibling asserts an
#   F2P-shaped input (an Indexed always carries ≥ 1 subscript) satisfies its
#   `Requires(len(index_renderings) >= 1)`. This backend's method has NO `require`
#   clause, so that literal probe has no analogue — but an earlier revision
#   concluded the whole LANE was therefore degenerate, and that does not follow.
#   "The frozen obligation has no precondition" is exactly the reason that has
#   been measured wrong across this corpus: on a TOTAL carrier the
#   PRECOND-TOO-STRONG analogue is the obligation being unsatisfiable, or
#   degenerately satisfiable, at exactly an F2P-shaped input. That is expressible
#   here, so the case is re-aimed at the post-image rather than dropped: an
#   in-region `assert`, discharged BY EVALUATION at the concrete two-subscript
#   input, that the rendering is exactly the expected literal AND differs from the
#   transposed-subscript rendering. Verifies, exit 0.
#   The reject lane does NOT already establish this, which is where the earlier
#   reasoning failed: six rivals failing the postcondition shows the post-image is
#   not met by everything, and is equally consistent with an obligation nothing can
#   meet at that point. Only a positive that DISCHARGES the obligation at the
#   concrete input separates those. The assert is live rather than decoration —
#   two controls differing ONLY in the claim (wrong-separator target string; `≠`
#   weakened to `=`) both fail, exit 1.
# VACUOUS (frame-mut-name-append, frame-mut-index-append): the sibling's TWO
#   MANDATORY frame rivals write into read-only inputs held at
#   `Acc(list_pred(name), 1/2)` / `Acc(list_pred(index_renderings), 1/2)`, tripping
#   the insufficient-permission check. This backend is referentially transparent:
#   `base` and `indices` are immutable values, no `mut` binder is declared for
#   them, and there is no heap, no aliasing, and no permission system. There is no
#   read-only input to overwrite and no frame clause to violate, so the class has
#   no carrier analogue. Omitted as a genuine carrier fact, NOT fabricated (porting
#   map: this class is vacuous on a referentially-transparent backend).
# DIVERGENCE / NON-TERMINATION — CLOSED BY THE SPEC (not vacuous, not a hole).
#   The sibling carries NO diverge-*/nonterm-*/weak-diverge case, so nothing is
#   dropped from the design document. Two earlier claims in this file were wrong
#   and are corrected: (a) that the class is "genuinely vacuous" because the frozen
#   loop carries `done_with i = 0` — that describes the FROZEN impl and says
#   nothing about what a rival may write, and a rival can trivially write an
#   unbounded loop; (b) that this bundle is `partial` and the class is therefore a
#   known 401-bundle spec hole. The frozen solution's line 4 is
#   `set_option loom.semantics.termination "total"`, and so is every velvet
#   bundle's, so there is no split and no cohort in which this would be a hole.
#   Re-measured with real builds: a `while true` prefix ahead of an otherwise
#   correct body, and an unbounded `while k ≥ 0` returning the wrong `[]`, are BOTH
#   rejected, exit 1, `error: Decreasing annotations are required in total
#   correctness semantics` at the method header; and a loop that CARRIES a measure
#   the verifier cannot show decreasing (`while q > 0 / invariant 0 <= q /
#   done_with q = 0 / decreasing q`, body `q := q`) is rejected on the measure's own
#   goal, `case «decreasing_1: q»`, residual `q < q`. The spec catches divergence,
#   annotated or not.
#   Still unshippable as a witnessed reject case, for the witness contract rather
#   than the spec: that error is a MODULE-level elaboration failure, so it fires in
#   the witness file too (the `method` survives there), the witness build against
#   the rival exits 1, and the gate records `witness-unproven` — inconclusive — for
#   a rival the spec does in fact reject. Measured: the rival's witness build
#   carries the header error plus a non-reducing tester, because a method that
#   failed to elaborate extracts no program to test.
#
# BINDER / CLAUSE COVERAGE. The single `ensures out = accessRender base indices`
#   binds `out`, `base`, and `indices`; the model combines a CARRIER-PREFIX
#   sub-obligation, a BRACKETS sub-obligation, a SEPARATOR sub-obligation, a
#   NO-SURROUNDING-TEXT sub-obligation, and an ORDER/ELEMENT-WISE sub-obligation.
#   All are attacked:
#     * CARRIER PREFIX: rival-drop-carrier-prefix (the only rival keying on `base`).
#     * BRACKETS: rival-paren-not-bracket (wrong delimiters), and
#       rival-partial-domain-single-index (brackets dropped on the length-1
#       sub-domain) — two distinct sub-domains of the same clause.
#     * SEPARATOR: rival-wrong-separator (bare `,` for `, `).
#     * NO SURROUNDING TEXT: rival-surrounding-prefix (leading `#`).
#     * ORDER / ELEMENT-WISE: rival-reverse-order (fragments transposed).
#     * BRACKETS at the length-0 boundary: rival-empty-indices-no-brackets.
#   The seven reject witnesses probe seven DISTINCT input points (pts=7):
#     * rival-paren-not-bracket            base=['q'] indices=[['0']]
#     * rival-wrong-separator              base=['p'] indices=[['0'], ['1']]
#     * rival-surrounding-prefix           base=['p'] indices=[['5']]
#     * rival-partial-domain-single-index  base=['x'] indices=[['7']]
#     * rival-drop-carrier-prefix          base=['p'] indices=[['a'], ['b']]
#     * rival-reverse-order                base=['p'] indices=[['0'], ['9']]
#     * rival-empty-indices-no-brackets    base=['p'] indices=[]
#   So `base` ranges over {['p'], ['q'], ['x']} (and is the deciding value at
#   drop-carrier-prefix), and `indices` over lengths {0, 1, 2} with varied content;
#   no binder is pinned at a single value across the reject set. The length-0 point
#   was added by the audit: the original six probed lengths {1, 2} only, so the
#   empty-subscript boundary of the BRACKETS clause was unattacked.
# WITNESS DISCRIMINATION (re-derived independently by the audit, 5 real builds per
#   reject case). Each witness ELABORATES against its loop-free rival (exit 0: the
#   extracted program's result provably violates the ensures at the probed input,
#   `renderAccessTester … = false` closing by `decide`), and is REFUTED BY
#   COMPUTATION against the declared `witness_reference` (exit 1, `decide` "proved
#   that the proposition … is false" — 7/7). Against the FROZEN solution all seven
#   instead fail by STUCK REDUCTION (exit 1, "did not reduce to `isTrue` or
#   `isFalse`" — 7/7), which is why gold is not the subject: that failure is not a
#   refutation.
#   FORGERY CONTROL (attack B′), run per case in both directions and the reason the
#   `witness_reference` design is sound rather than merely convenient:
#     * gold, witness `… = false`  -> exit 1, stuck
#     * gold, FORGED `… = true`    -> exit 1, stuck, error text differing only in
#       the literal `false`/`true` it echoes back — so gold's exit code is
#       independent of the claim and carries no information (7/7).
#     * reference, witness `… = false` -> exit 1, COMPUTED refutation (7/7)
#     * reference, FORGED `… = true`   -> exit 0 (7/7): the reference's tester
#       computes to `true` at that input, i.e. it passes its own postcondition
#       there. The reference decides BOTH directions, which is exactly what gold
#       cannot do, and is what makes the refutation track the claim.
#     * rival, FORGED `… = true` -> exit 1, "proved that the proposition … is
#       false" (7/7) — the rival's tester computes to `false`, confirming the
#       rival really does violate the postcondition at that point rather than the
#       witness merely failing to elaborate.
#   The carrier is fully concrete at every witness, so each closes by `decide` with
#   no hypothesis and there is no joint-satisfiability obligation
#   (`consistency_probe` is None for all seven). No
#   `sorry`/`admit`/`native_decide`/`axiom` appears.
#
# AUDIT PROBES (attacks D/E/F; built, not shipped — recorded so the next reader
#   knows which directions were tested and found closed):
#   * SPEC-TOO-WEAK probe — 8 NEW wrong impls beyond the shipped rivals, aimed at
#     the least-probed points: wrong ONLY on the empty-`indices` sub-domain
#     (length 0); a TRAILING separator after the last fragment; the separator
#     spelled " ," instead of ", "; the carrier text moved to a SUFFIX; duplicate
#     fragments silently de-duplicated; the FIRST fragment dropped; the closing
#     bracket omitted; and one wrong ONLY at length ≥ 3 (correct on lengths 0/1/2,
#     so it agrees with every other witness in this battery). ALL 8 were REJECTED
#     by the frozen spec, exit 1 each. No spec hole found in this direction.
#     The empty-`indices` probe was the one whose sub-domain no shipped witness
#     touched, so it was promoted out of the probe set and SHIPPED as
#     `rival-empty-indices-no-brackets` (witness re-derived: rival exit 0,
#     reference exit 1 computed refutation, forged-claim-on-reference exit 0).
#   * SPEC-TOO-STRONG probe — 3 NEW correct impls with different shapes, and the
#     result changed what ships. The sibling's LITERAL branch-arm swap
#     (`if i < indices.length` general case first) VERIFIES, exit 0, once its
#     tactic body is retuned to normalise `getElem!` to the `getElem?.getD` form
#     the loop goal is stated in and case-split on `i = indices.length`; with the
#     FROZEN proof verbatim it fails `unsolved goals` on the loop invariant, exit
#     1. That pair is a tactic-script fact, not a spec fact — and since the spec
#     does admit the shape, the arm swap was promoted into the battery as
#     `pos-branch-reorder`, displacing the definitionally-equal typed-local
#     reshape that previously occupied that slot.
#     The structurally spelled-out closed form (`['[']` / `[']']` literals, no
#     `accessRender` by name) also VERIFIES, exit 0, under the frozen proof.
#     A FORWARD-fold reshape (accumulate over `indices.take i` rather than
#     `indices.drop i`) could NOT be closed and is recorded UNCERTAIN, not as a
#     hole: it needs a `take`-side step lemma that the frozen file does not
#     provide and that a variant may not add (`variant_scope` forbids new
#     top-level lemmas), and the residual goal
#     `(if i = 0 then indices[i]! else joined ++ ", ".toList ++ indices[i]!)
#     = joinComma (List.take (i+1) indices)` is a true statement left unproven for
#     want of that lemma. So this is a limit of what a variant may declare, not
#     evidence the spec rejects forward folds.
#   * FRAME inexpressibility DEMONSTRATED, not asserted: assigning through the
#     read-only input (`base := base ++ "!".toList`) does not reach a permission
#     check at all — it fails to elaborate with "`base` cannot be mutated, only
#     variables declared using `let mut` can be mutated". There is no frame
#     surface on this carrier to attack, which is what makes the sibling's two
#     MANDATORY frame rivals genuinely vacuous here rather than merely omitted.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   `axiom` (the assembly's components are a free input carrier and the assembly
#   is modeled deeply as `accessRender` / `joinComma`), and this gate ignores
#   AXIOM_TESTS regardless.
AXIOM_TESTS = []
