"""properties.py — G-PBT falsification battery for sympy__sympy-23824 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct restoreLeading`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  restoreLeading (leading : List Int) (tail : List Int) return (out : List Int)
    ensures out = leading ++ tail

  The single load-bearing ``ensures`` clause pins the result to the
  order-preserving concatenation of the two inputs: the leading run, in its
  ORIGINAL left-to-right order, followed by the core term. There is no
  precondition (``require`` ≡ True). ``restoreSeq`` is a total, fully-unfolded
  pure ``def`` (front-recursive concatenation, proven equal to ``++``), so the
  postcondition is grounded in the actual input carrier — nothing opaque to
  echo. The clause has TWO input binders, ``leading`` and ``tail``; a rival that
  mishandled EITHER the leading run's order/completeness or the tail's order
  must be refutable.

ADVERSARIAL READ of the weakness classes:
  * FRAME-MUTATION — VACUOUS on this backend, and demonstrated so rather than
    asserted. The sibling class exists because a read-only input may carry a
    fractional heap permission an impl can overwrite, and such a write must be
    rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: every parameter is an immutable value (this bundle declares no
    ``mut`` binder on an input), there is no heap and no aliasing. Checked
    directly: an impl-region body that assigns to a parameter is not a rival the
    verifier rejects on the SPEC, it is a file that does not compile —
    ``leading := leading ++ [0]`` and ``tail[0] := 0`` are each refused at parse
    time with "`leading`/`tail` cannot be mutated, only variables declared using
    `let mut` can be mutated", which is a syntax verdict carrying no information
    about the postcondition. So the two sibling frame-mutation rivals cannot be
    ported as spec probes at all, and a rejection built on that error would
    attribute nothing to the spec. Not fabricated (per the porting map, dropped
    rather than replaced).
  * PARTIAL-DOMAIN / ORDER — APPLIES, and is the headline SPEC-TOO-WEAK surface.
    The fix is order-only, so the rivals attack every separable component of the
    concatenation: each operand's internal order (the leading run built in
    reverse — the on-carrier image of the prepatch bug — and the core term
    reversed), each operand's completeness (the first leading factor dropped; the
    core term's first factor dropped), and the two operands' relative placement
    (the core term emitted ahead of the leading run). Each agrees with the
    post-image on a sub-domain (0/1-element run or term, all-equal factors, or an
    empty operand) and diverges elsewhere.
  * UNGROUNDED-ORACLE ECHO — N/A. The postcondition is ``out = leading ++ tail``,
    grounded in the two actual inputs (the ``axioms`` region is empty — no opaque
    answer key to echo); the cheapest correct impl simply concatenates, which the
    positive controls cover honestly.
  * DIVERGENCE / NON-TERMINATION — genuinely rejected by the carrier, but NOT
    shippable as a reject case, and the reason is TOOLING rather than the spec.
    This bundle sets ``loom.semantics.termination "total"``, so the verifier
    discharges a termination obligation and a diverging rival is really refused —
    measured with four rivals, all exit 1: the frozen loop with its ``decreasing``
    annotation deleted ("Decreasing annotations are required in total correctness
    semantics"), the frozen loop with ``decreasing i`` kept but ``i`` INCREMENTED
    (a present-but-false measure, leaving the semantic goal ``⊢ i + 1 < i``), and
    two loops that never touch the counter. So this is not the ``partial``
    known-hole disposition, and not a vacuous class either.
    What blocks shipping it is that no witness can be built. A reject case needs a
    witness that ELABORATES against the rival, and the rival's whole defect is a
    loop the kernel cannot reduce — so every claim about its extracted program is
    stuck on the rival side, which is the half that must succeed. Twelve witness
    shapes were built against the diverging rivals and ALL failed there (exit 1):
    ``restoreLeadingExec [1,2] [3] = DivM.div`` by ``simp`` and by ``rfl``; the
    conditioned ``≠ DivM.res out`` form; the negated-postcondition form the five
    shipped rivals use; ``restoreLeadingTester [1,2] [3] = false`` by ``decide``
    and by ``decide +kernel`` (both "did not reduce to `isTrue` or `isFalse`"); a
    ``.run``-projected variant; and the same claim at ``leading = []``, where the
    guard is false at entry — which reduces, but there the rival AGREES with the
    spec, so there is nothing to refute. The gate would record such a case as
    ``witness-unproven``: an inconclusive outcome, i.e. a battery FAILURE, for a
    rival that IS in fact rejected. Recorded here as a known tooling limit rather
    than shipped as a case that would fail the gate, and rather than claimed
    vacuous. (Corpus context: no velvet battery ships a case in this class.)
  * ADMISSIBILITY — re-aimed. The method carries NO ``require`` clause
    (precondition ≡ True), so there is no precondition to be too strong and no
    PRECOND-TOO-STRONG probe to build. The residual admissibility risk on this
    surface is that the post-image is UNSATISFIABLE or DEGENERATE at the
    interesting point; the admissibility case discharges an in-region ``assert``
    pinning the post-image's value at a concrete multi-factor input (a live
    check — a false claim leaves an unsolved goal, verified during authoring),
    with the impl kept verbatim so the method's own obligation still discharges.

WITNESS PLACEMENT, and an honest account of what the two builds do and do not
establish on this carrier.

Each reject rival carries a refutation ``witness`` stated at ONE concrete input
and checked in a file whose ``prove_correct`` has been stripped, so no tactic
script can mask the verdict. The form is a CONDITIONED value-level claim: it
binds the extracted program's result at that input by hypothesis
(``h : restoreLeadingExec <leading> <tail> = DivM.res out``) and concludes
``out ≠ <leading> ++ <tail>`` — the postcondition, negated, at that point. On a
straight-line rival the extracted term reduces, ``h`` collapses to the rival's
actual output, and ``cases h; simp`` closes the goal: a genuine value-level
refutation, and the elaboration-on-rival half.

GOLD CANNOT BE THE SECOND SUBJECT HERE, and the gate knows it. The frozen loop
elaborates through ``Classical.choice`` (measured: ``#print axioms
restoreLeadingExec`` reports ``[propext, Classical.choice, Quot.sound]``), so the
kernel cannot unfold gold's extracted program at all. Gold's build therefore
fails structurally rather than by deciding anything: with a bare ``decide``
witness the error is "did not reduce to `isTrue` or `isFalse`", and with the
conditioned form above it is "Dependent elimination failed", because ``h``'s
right-hand side never reduces to a constructor. Neither message is gold
satisfying the spec, and neither tracks the CLAIM: re-measured for this audit,
the real witness and a flipped-claim forgery (``out = leading ++ tail``, i.e.
gold is CORRECT there) both fail against gold with the byte-identical
``Dependent elimination failed`` headline. So gold's exit code carries no
information about the spec, for any witness on this cell.

THE SUBJECT THE GATE ACTUALLY USES is a verifying positive from this battery,
and that subject DOES discriminate — so discrimination is delegated to the gate
after all, not merely recorded in this docstring. The gate's stuck-reduction
screen fires on gold, falls back to an ``expect="verify"`` case's impl (here
``pos-control-direct-append``, ``return leading ++ tail``, which the kernel DOES
reduce — ``#eval`` prints ``DivM.res [1, 2, 3]``), independently re-checks that
it shares the frozen spec and VERIFIES, and refutes the witness there instead.
An impl the verifier accepts cannot violate its own spec, so a genuine witness
must still fail against it. ``meta.json`` records this per case as
``witness_subject: "a verifying positive from this battery (gold cannot decide)"``
with ``gold_signature: "unsolved goals case refl ⊢ False"`` — the SUBJECT-side
error, which is semantic: after ``cases h`` the residual goal is literally
``⊢ False``, the witness's negated postcondition refuted by the correct output.

Re-measured with real builds for this audit, per reject case, three subjects and
a forgery pair (20 builds):

  * witness vs RIVAL            -> exit 0 (elaborates; the rival provably violates
                                  the clause at that input)
  * witness vs GOLD             -> exit 1, ``Dependent elimination failed``
                                  (stuck; carries no information — screened)
  * witness vs the POSITIVE      -> exit 1, ``unsolved goals / case refl / ⊢ False``
                                  (semantic refutation; this is the attestation)
  * FLIPPED-CLAIM forgery vs
    that same positive           -> exit 0

That last line is what makes the subject's exit code informative rather than
constant: flipping the claim FLIPS the outcome (0 instead of 1), which is exactly
what gold's constant failure could not do. And the agreement-point forgery this
docstring previously reported as unstoppable is now caught: asserting the
reverse-leading rival is CORRECT at ``leading=[7]``, ``tail=[8]`` (a one-element
run, where reversal is the identity) elaborates against the rival (exit 0) AND
against the positive (exit 0), which the gate records as ``witness-vacuous`` — an
inconclusive outcome, i.e. a battery FAILURE, not a pass. Under the older
gold-only check it would have cleared both halves; it no longer does.

Hypothesis satisfiability was checked directly rather than left to the probe: all
five points close ``restoreLeadingExec <leading> <tail> = DivM.res (<leading> ++
<tail>)`` by ``rfl`` against that positive (one file, exit 0), so none of the five
refutations rests on an unreachable input. (The gate's own generated consistency
probe cannot run on this cell — it re-states the binders without the
``extract_program_for`` preamble, so ``restoreLeadingExec`` is unbound there and
the probe fails to elaborate on BOTH subjects, which is the fail-safe direction:
a probe that does not succeed cannot flag the witness inconsistent.)

The five witnesses sit at five DISTINCT input points and vary BOTH binders:
``leading`` ranges over one- and two-element runs and ``tail`` over one- and
two-element core terms, in both combinations. The two-element tail is the
sub-domain on which a reversed or truncated core term is observably wrong, and
the both-operands-two-element point is where placement diverges from
intra-operand order — so the manifest demonstrates the post-image's dependence
on each binder's order, each binder's completeness, and the two binders'
relative placement, rather than its value at a single pinned point. pts=3.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-23824"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE gold loop body (text strictly between
# ---- -- impl-start and -- impl-end). Every straight-line rival and the append
# ---- positive replace it wholesale. Unique in Solution.lean (asserted by _swap).
_IMPL = (
    "    -- impl-start\n"
    "    let mut result : List Int := tail\n"
    "    let mut i := leading.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ leading.length\n"
    "      invariant result = restoreSeq (leading.drop i) tail\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := leading[i - 1]!\n"
    "      result := c :: result\n"
    "      i := i - 1\n"
    "    return result\n"
    "    -- impl-end"
)

# ---- the two loop-body lines that bind `c` then prepend it. The inline-binding
# ---- positive folds `c` into the prepend, leaving `result` definitionally
# ---- identical so the frozen tactic script still closes. Unique in the file.
_INNER = (
    "      let c := leading[i - 1]!\n"
    "      result := c :: result\n"
)

# ---- the frozen proof body (velvet obligation). The append/restoreSeq positives
# ---- reshape the impl to a form `loom_solve` closes alone, so they retune this
# ---- to the plain script. Elided from the consumer spec view. Unique in file.
_PROOF = (
    "prove_correct restoreLeading by\n"
    "  loom_solve\n"
    "  rw [restoreSeq_drop_step leading tail i (by omega) (by omega)]\n"
    "  simp_all"
)


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `restoreLeadingTester leading tail = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for restoreLeading\n"
            "prove_precondition_decidable_for restoreLeading\n"
            "prove_postcondition_decidable_for restoreLeading\n"
            "derive_tester_for restoreLeading\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation statement byte-identical and
    # only reshapes the executable surface + retunes the tactic body.
    # =====================================================================
    {
        "id": "pos-control-direct-append",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: abandon the backward prepend loop entirely and return the
        # order-preserving concatenation directly. `loom_solve` closes the single
        # `out = leading ++ tail` goal on its own, so the tactic body is retuned
        # to the plain script (no drop-step lemma needed).
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return leading ++ tail\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "rationale": "the direct order-preserving concatenation satisfies "
                     "`out = leading ++ tail` definitionally, so a correct "
                     "reshape that abandons the loop must verify; if it failed "
                     "the post-image would be SPEC-TOO-STRONG on the impl's shape.",
    },
    {
        "id": "pos-control-inline-binding",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the per-element `let c := leading[i-1]!` binding into
        # the prepend. The accumulated `result` is DEFINITIONALLY identical, so
        # `loom_solve` leaves the same single loop-body goal and the FROZEN tactic
        # script (drop-step lemma + simp_all) discharges it unchanged.
        "module": _swap(
            _BASE, _INNER,
            "      result := leading[i - 1]! :: result\n"),
        "rationale": "inlining the per-element index binding into the prepend "
                     "leaves the accumulated `result` definitionally identical, "
                     "so both the loop invariant and `out = leading ++ tail` hold "
                     "and the frozen proof closes without change. WEAK BY "
                     "CONSTRUCTION, and recorded as such: because the accumulator "
                     "is definitionally the frozen one, this case can only fail "
                     "if the obligation is sensitive to pure syntax, so it tests "
                     "the elaborator's tolerance of a `let`-free data flow rather "
                     "than the spec's tolerance of a different algorithm. The "
                     "load-bearing soundness evidence is "
                     "`pos-control-forward-accumulate`, which rebuilds the run in "
                     "the opposite direction under a different invariant.",
    },
    {
        "id": "pos-control-forward-accumulate",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the OPPOSITE loop direction. Gold walks the leading run
        # BACKWARD prepending onto an accumulator seeded with `tail`; this walks
        # it FORWARD, appending each factor onto an accumulator seeded empty, and
        # concatenates `tail` once at the end. Different loop bound, different
        # direction, different termination measure (`leading.length - i` rather
        # than `i`), and a different value invariant (`result = leading.take i`
        # rather than `result = restoreSeq (leading.drop i) tail`) — so unlike
        # the two reshapes above it is NOT definitionally the frozen accumulator,
        # and its proof genuinely re-derives the postcondition rather than
        # replaying the frozen drop-step lemma. This is the control that shows
        # the spec is agnostic to the direction in which the run is rebuilt.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    let mut result : List Int := []\n"
            "    let mut i := 0\n"
            "    while i < leading.length\n"
            "      invariant 0 ≤ i ∧ i ≤ leading.length\n"
            "      invariant result = leading.take i\n"
            "      done_with i = leading.length\n"
            "      decreasing leading.length - i\n"
            "    do\n"
            "      result := result ++ [leading[i]!]\n"
            "      i := i + 1\n"
            "    return result ++ tail\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve\n  all_goals simp_all"),
        "rationale": "the forward accumulate-then-append loop rebuilds the same "
                     "order-preserving concatenation by walking the leading run "
                     "in the OPPOSITE direction, under a different value "
                     "invariant (`result = leading.take i`) and a different "
                     "termination measure — so it is not definitionally the "
                     "frozen accumulator and its proof re-derives "
                     "`out = leading ++ tail` instead of replaying the frozen "
                     "drop-step lemma. A faithful correct impl that the spec "
                     "rejected merely for rebuilding the run in the other "
                     "direction would be SPEC-TOO-STRONG on the loop's shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` (precondition ≡ True), so the
    # "a normal input satisfies the precondition" probe is vacuous. Re-aimed at
    # the residual admissibility risk: that the post-image is unsatisfiable or
    # degenerate at the interesting point (a spec no impl can meet reads exactly
    # like one every impl meets). This case discharges an in-region `assert`
    # pinning the post-image's value at a multi-factor input — the leading run
    # restored in ORDER, then the core term. The surrounding impl is kept
    # verbatim so the method's own obligation still discharges; the assert is
    # live (a false claim about the same point leaves an unsolved goal — checked
    # during authoring).
    # =====================================================================
    {
        "id": "admiss-order-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, "    -- impl-start\n",
            "    -- impl-start\n"
            "    assert (with_name_prefix `assert\n"
            "      (restoreSeq [1, 2] [3] = [1, 2, 3]))\n"),
        "rationale": "the post-image is satisfiable AND non-degenerate at a "
                     "multi-factor input: it demands the leading run restored in "
                     "its original order ([1,2]) ahead of the core term ([3]), "
                     "giving [1,2,3] — NOT the reversed [2,1,3]. The in-region "
                     "assert must discharge (else the obligation is unsatisfiable "
                     "/ degenerate); the impl is kept verbatim so the method's "
                     "own `ensures` still discharges. LIVENESS RE-MEASURED (audit): "
                     "the same assert with the reversed value substituted "
                     "(`restoreSeq [1, 2] [3] = [2, 1, 3]`) leaves the unsolved "
                     "goal `⊢ restoreSeq [1, 2] [3] = [2, 1, 3]` under "
                     "`case assert_1` and the file fails (exit 1), so the assert "
                     "is discharged by evaluation and not by a vacuous context. A "
                     "strengthened form conjoining the clause's own vocabulary "
                     "(`[1,2] ++ [3] = [1,2,3] ∧ [1,2] ++ [3] ≠ [2,1,3]`) also "
                     "verifies, and its self-contradictory variant fails.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each is a straight-line
    # impl (so its extracted tester reduces under `decide`) that reshapes only
    # the impl region; the tactic body is retuned to the plain script.
    # =====================================================================
    {
        "id": "weak-reverse-leading",
        "kind": "uniqueness",
        "expect": "reject",
        # Restore the leading run in REVERSE order — the on-carrier image of the
        # prepatch bug (each leading factor front-inserted in turn). Agrees with
        # the post-image only when the leading run has 0/1 element (or all-equal
        # factors); wrong whenever it has two distinct factors.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return leading.reverse ++ tail\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "refinement": "restoring the leading run in reverse is exactly the "
                      "documented defect (the leading uncontracted factors "
                      "prepended in reverse order). On the failing test's "
                      "multi-factor leading run the two factors come back "
                      "transposed, so the simplified product carries the wrong "
                      "factor order — a different tensor expression than the "
                      "expected one. It would NOT resolve.",
        "rationale": "REJECT from `out = leading ++ tail`: the impl computes "
                     "`leading.reverse ++ tail`, which differs from `leading ++ "
                     "tail` whenever the leading run has two distinct factors "
                     "(the load-bearing order clause). Verifying would be "
                     "SPEC-TOO-WEAK on the leading-run order. Refuted at "
                     "`leading=[1,2]`, `tail=[3]` — a two-element run.",
        "witness": _tester(
            "example (out : List Int)\n"
            "    (h : restoreLeadingExec [1, 2] [3] = DivM.res out) :\n"
            "    out ≠ [1, 2] ++ [3] := by\n"
            "  simp [restoreLeadingExec, restoreLeading, NonDetT.run] at h\n"
            "  cases h\n"
            "  simp\n"),
    },
    {
        "id": "weak-drop-first-leading",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the FIRST leading factor. Correct on all of tail and on the rest
        # of the leading run; wrong on every input whose leading run is
        # non-empty (the first-element sub-domain). Distinct from
        # weak-reverse-leading: it changes the run's LENGTH, not just its order.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return leading.drop 1 ++ tail\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "refinement": "dropping the first leading factor loses one gamma matrix "
                      "from the front of the restored term; the simplified "
                      "product is one factor short of the documented result — a "
                      "different (shorter) tensor expression. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = leading ++ tail`: the impl computes "
                     "`leading.drop 1 ++ tail`, which omits the first leading "
                     "factor and so differs whenever the leading run is "
                     "non-empty. Partial-domain (first-element) divergence; "
                     "verifying would be SPEC-TOO-WEAK on the leading-run "
                     "completeness. Refuted at `leading=[5,6]`, `tail=[7]`.",
        "witness": _tester(
            "example (out : List Int)\n"
            "    (h : restoreLeadingExec [5, 6] [7] = DivM.res out) :\n"
            "    out ≠ [5, 6] ++ [7] := by\n"
            "  simp [restoreLeadingExec, restoreLeading, NonDetT.run] at h\n"
            "  cases h\n"
            "  simp\n"),
    },
    {
        "id": "weak-reverse-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # Restore the leading run correctly IN ORDER, but reverse the core term.
        # Correct when the core term has 0/1 element (or all-equal factors);
        # wrong whenever it has two distinct factors. Attacks the SECOND binder
        # (`tail`) — no other rival probes the tail's order — and is refuted at a
        # TWO-element tail, the sub-domain where the reversal is observable.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return leading ++ tail.reverse\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "refinement": "reversing the core term scrambles the factor order WITHIN "
                      "the simplified term; a result term carries an ordered list "
                      "of factor labels, so reordering it produces a different "
                      "tensor expression than the documented one. It would NOT "
                      "resolve.",
        "rationale": "REJECT from `out = leading ++ tail`: the impl computes "
                     "`leading ++ tail.reverse`, which differs whenever the core "
                     "term has two distinct factors. This is the only rival "
                     "attacking the `tail` binder's order; verifying would be "
                     "SPEC-TOO-WEAK on the core-term order. Refuted at "
                     "`leading=[1]`, `tail=[2,3]` — a two-element core term.",
        "witness": _tester(
            "example (out : List Int)\n"
            "    (h : restoreLeadingExec [1] [2, 3] = DivM.res out) :\n"
            "    out ≠ [1] ++ [2, 3] := by\n"
            "  simp [restoreLeadingExec, restoreLeading, NonDetT.run] at h\n"
            "  cases h\n"
            "  simp\n"),
    },
    {
        "id": "weak-swap-operands",
        "kind": "uniqueness",
        "expect": "reject",
        # Put the core term FIRST and the leading run behind it. Both binders are
        # carried whole and in their own internal order — so every rival above
        # leaves this untouched: `weak-reverse-leading` and `weak-reverse-tail`
        # scramble order WITHIN one operand, and `weak-drop-first-leading`
        # changes one operand's length. This one keeps both operands intact and
        # attacks only their RELATIVE PLACEMENT, which is the clause's other half
        # (`leading ++ tail`, not `tail ++ leading`). Correct only when one of the
        # two operands is empty; wrong whenever both are non-empty. Refuted at a
        # point where BOTH operands have two elements, so the reversal cannot be
        # confused with an intra-operand reordering.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return tail ++ leading\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "refinement": "emitting the core term ahead of the leading run puts the "
                      "uncontracted leading factors BEHIND the simplified term's "
                      "factors instead of in front of them. The restored term "
                      "carries the same factor labels in a different order, which "
                      "is a different tensor expression than the documented one "
                      "on any input with both a non-empty leading run and a "
                      "non-empty core term. It would NOT resolve.",
        "rationale": "REJECT from `out = leading ++ tail`: the impl computes "
                     "`tail ++ leading`, which differs whenever BOTH operands are "
                     "non-empty. This is the only rival attacking the two "
                     "binders' relative placement rather than order or "
                     "completeness within one of them; verifying would be "
                     "SPEC-TOO-WEAK on which operand leads. Refuted at "
                     "`leading=[1,2]`, `tail=[3,4]` — both operands two-element, "
                     "so the divergence is placement, not intra-operand order.",
        "witness": _tester(
            "example (out : List Int)\n"
            "    (h : restoreLeadingExec [1, 2] [3, 4] = DivM.res out) :\n"
            "    out ≠ [1, 2] ++ [3, 4] := by\n"
            "  simp [restoreLeadingExec, restoreLeading, NonDetT.run] at h\n"
            "  cases h\n"
            "  simp\n"),
    },
    {
        "id": "weak-drop-first-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the first element of the CORE TERM. The mirror of
        # weak-drop-first-leading on the other binder: `tail`'s COMPLETENESS was
        # the one cell of the binder x weakness grid no rival occupied
        # (`tail` was attacked on order only). Correct on all of the leading run
        # and on the rest of the core term; wrong on every input whose core term
        # is non-empty.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return leading ++ tail.drop 1\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "refinement": "dropping the core term's first factor loses one gamma "
                      "matrix from the simplified term itself; the restored term "
                      "is one factor short of the documented result — a different "
                      "(shorter) tensor expression. It would NOT resolve.",
        "rationale": "REJECT from `out = leading ++ tail`: the impl computes "
                     "`leading ++ tail.drop 1`, which omits the core term's first "
                     "factor and so differs whenever the core term is non-empty. "
                     "Completes the binder x weakness grid — `tail`'s "
                     "COMPLETENESS is otherwise unattacked (the other `tail` "
                     "rival probes its order); verifying would be SPEC-TOO-WEAK "
                     "on the core term's completeness. Refuted at `leading=[4]`, "
                     "`tail=[5,6]`.",
        "witness": _tester(
            "example (out : List Int)\n"
            "    (h : restoreLeadingExec [4] [5, 6] = DivM.res out) :\n"
            "    out ≠ [4] ++ [5, 6] := by\n"
            "  simp [restoreLeadingExec, restoreLeading, NonDetT.run] at h\n"
            "  cases h\n"
            "  simp\n"),
    },
    {
        "id": "weak-shift-values",
        "kind": "uniqueness",
        "expect": "reject",
        # Carry BOTH operands whole, in the right order, in the right relative
        # placement — and corrupt every ELEMENT's value. The five rivals above all
        # permute or delete factors drawn from the two inputs, so each one's output
        # is a sub-multiset of `leading ++ tail`; none of them ever produces a
        # factor label the inputs do not contain. So the clause's requirement that
        # the restored factors be the INPUTS' OWN labels — not merely labels in the
        # right arrangement and count — was unprobed. Correct on no input at all
        # except the empty one, and refuted where both operands are non-empty.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return (leading ++ tail).map (· + 1)\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "refinement": "relabelling every restored factor keeps the term's length "
                      "and arrangement but names DIFFERENT indices throughout, so "
                      "the restored term contracts against different indices than "
                      "the documented result — a different tensor expression on "
                      "every non-empty input. It would NOT resolve.",
        "rationale": "REJECT from `out = leading ++ tail`: the impl computes "
                     "`(leading ++ tail).map (· + 1)`, whose length, operand order "
                     "and operand placement all match the post-image while every "
                     "element differs. This is the only rival attacking the factor "
                     "LABELS rather than their arrangement or count — every other "
                     "rival's output is a sub-multiset of `leading ++ tail`, so "
                     "element identity was unprobed; verifying would be "
                     "SPEC-TOO-WEAK on which factors are restored. Refuted at "
                     "`leading=[2,3]`, `tail=[4]`.",
        "witness": _tester(
            "example (out : List Int)\n"
            "    (h : restoreLeadingExec [2, 3] [4] = DivM.res out) :\n"
            "    out ≠ [2, 3] ++ [4] := by\n"
            "  simp [restoreLeadingExec, restoreLeading, NonDetT.run] at h\n"
            "  cases h\n"
            "  simp\n"),
    },
    {
        "id": "weak-duplicate-tail",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the core term TWICE. The two completeness rivals above both SHORTEN
        # an operand, so the clause was probed for "nothing may be dropped" but not
        # for "nothing may be added": an impl that loses no factor and keeps every
        # operand's order and placement can still be wrong by REPEATING one. Agrees
        # with the post-image exactly when the core term is empty; wrong otherwise.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return leading ++ tail ++ tail\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct restoreLeading by\n  loom_solve"),
        "refinement": "emitting the core term twice duplicates the simplified "
                      "term's factors behind the leading run, giving a longer "
                      "product than the documented result — a different tensor "
                      "expression on any input with a non-empty core term. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = leading ++ tail`: the impl computes "
                     "`leading ++ tail ++ tail`, which drops nothing and reorders "
                     "nothing but repeats the core term, so it differs whenever "
                     "the core term is non-empty. The two completeness rivals both "
                     "SHORTEN an operand, so the clause's upper bound — that "
                     "nothing may be ADDED — is otherwise unprobed; verifying "
                     "would be SPEC-TOO-WEAK on the restored term's length. "
                     "Refuted at `leading=[8]`, `tail=[9,10]`.",
        "witness": _tester(
            "example (out : List Int)\n"
            "    (h : restoreLeadingExec [8] [9, 10] = DivM.res out) :\n"
            "    out ≠ [8] ++ [9, 10] := by\n"
            "  simp [restoreLeadingExec, restoreLeading, NonDetT.run] at h\n"
            "  cases h\n"
            "  simp\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals) plus 0 AXIOM_TESTS (the sibling
# already records the axiom lane as vacuous). This bundle models the same single
# purely-functional core — the method `restoreLeading`, whose net effect is the
# order-preserving concatenation `leading ++ tail`, modeled DEEPLY (not behind an
# opaque callee) — so unlike the opaque-carrier ports the full value surface is
# discriminable via the `derive_tester_for` + `decide` route. Every sibling case
# is accounted for below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-local-reshape               -> pos-control-inline-binding      PORTED
#                                      (+ pos-control-direct-append     ADDED)
#                                      (+ pos-control-forward-accumulate ADDED)
#   admiss-precond                  -> admiss-order-nondegenerate       RE-AIMED
#   frame-mutate-leading-append     -> (none)                          VACUOUS
#   frame-mutate-tail-index         -> (none)                          VACUOUS
#   partial-reverse-leading         -> weak-reverse-leading            PORTED
#   partial-skip-first-leading      -> weak-drop-first-leading         PORTED
#   partial-reverse-tail            -> weak-reverse-tail               PORTED
#                                      (+ weak-swap-operands            ADDED)
#                                      (+ weak-drop-first-tail          ADDED)
#                                      (+ weak-shift-values             ADDED/audit)
#                                      (+ weak-duplicate-tail           ADDED/audit)
#
# 4 ported, 1 re-aimed, 2 vacuous; 2 positive controls and 4 rivals added.
#
# VACUOUS (frame-mutate-leading-append, frame-mutate-tail-index): the sibling's
#   two mandatory frame-mutation rivals write to a read-only input (append to the
#   leading run; in-place index store to the core term) that carries only a
#   fractional heap permission, and are rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: every parameter is an immutable
#   value, this bundle declares no `mut` binder on an input, there is no heap and
#   no aliasing. Demonstrated rather than argued: writing a parameter in the impl
#   region does not produce a rival the verifier rejects on the spec, it produces
#   a file that does not compile. `leading := leading ++ [0]` and `tail[0] := 0`
#   are each refused with "`leading`/`tail` cannot be mutated, only variables
#   declared using `let mut` can be mutated" — a parse-time verdict that says
#   nothing about the postcondition, so a reject case resting on it would
#   attribute nothing to the spec (exactly the failure mode the witness
#   requirement exists to catch). The class is therefore genuinely inexpressible
#   here, not merely hard. No substitute is fabricated (per the porting map, this
#   class is legitimately dropped here, not replaced).
# RE-AIMED (admiss-order-nondegenerate): the sibling's admissibility case asserts
#   the two read-only Requires (Acc(...,1/2)) at entry — a permission fact with no
#   counterpart on a permission-free carrier. The method here carries NO `require`
#   clause (precondition ≡ True), so that probe is vacuous. It is re-aimed at the
#   residual admissibility risk on this surface: that the post-image is
#   unsatisfiable or degenerate at the interesting point. The case discharges an
#   in-region assert pinning the post-image's value at a multi-factor input (the
#   leading run in ORIGINAL order ahead of the core term).
# ADDED (4):
#   pos-control-direct-append — a second correct impl (the concatenation returned
#     directly, abandoning the loop).
#   pos-control-forward-accumulate — a THIRD correct impl that rebuilds the run in
#     the OPPOSITE direction under a different value invariant
#     (`result = leading.take i`) and a different termination measure. The other
#     two positives are definitionally the frozen accumulator or a one-line
#     concatenation, so neither shows the spec admits a different ALGORITHM; this
#     one does, and it is the load-bearing soundness evidence.
#   weak-swap-operands — the rival attacking the two binders' RELATIVE PLACEMENT
#     (`tail ++ leading`). Every ported rival scrambles order within one operand
#     or shortens one operand, so placement — the other half of what `++` pins —
#     was unattacked.
#   weak-drop-first-tail — `tail`'s COMPLETENESS, the one cell of the
#     binder x weakness grid no ported rival occupied (`tail` was probed on order
#     only, `leading` on both).
#   weak-shift-values (audit) — the factor LABELS. All five rivals above permute
#     or delete factors drawn from the inputs, so every one of their outputs is a
#     sub-multiset of `leading ++ tail`; none tests that the restored factors are
#     the inputs' OWN labels rather than merely labels in the right arrangement
#     and count. `(leading ++ tail).map (· + 1)` matches length, operand order and
#     placement while differing in every element.
#   weak-duplicate-tail (audit) — the clause's UPPER bound. Both completeness
#     rivals SHORTEN an operand, so "nothing may be dropped" was probed and
#     "nothing may be ADDED" was not: `leading ++ tail ++ tail` loses no factor and
#     reorders nothing, and is wrong by repetition alone.
#
# BINDER / CLAUSE COVERAGE. The single `ensures` clause `out = leading ++ tail`
#   has two input binders, and the clause pins FIVE separable things: each
#   operand's internal ORDER, each operand's COMPLETENESS, the two operands'
#   relative PLACEMENT, the ELEMENT IDENTITY of what is restored, and the result's
#   LENGTH from above. The grid is now full:
#     leading/order        -> weak-reverse-leading
#     leading/completeness -> weak-drop-first-leading
#     tail/order           -> weak-reverse-tail
#     tail/completeness    -> weak-drop-first-tail
#     placement            -> weak-swap-operands
#     element identity     -> weak-shift-values      (audit)
#     length / no addition -> weak-duplicate-tail    (audit)
#   so neither binder is held fixed and no clause component is unprobed. The
#   clause is defended by three positive controls, one of which (forward
#   accumulate) is not definitionally the frozen impl. The seven witnesses sit at
#   seven DISTINCT input points (`[1,2]`/`[3]`, `[5,6]`/`[7]`, `[1]`/`[2,3]`,
#   `[1,2]`/`[3,4]`, `[4]`/`[5,6]`, `[2,3]`/`[4]`, `[8]`/`[9,10]`), varying
#   `leading` across one- and two-element runs and `tail` across one- and
#   two-element core terms in both combinations: the two-element tail is what makes
#   a reversed or truncated core term observable, and the both-two-element point is
#   what separates placement from intra-operand order. Each was additionally
#   checked to FAIL against a straight-line CORRECT impl — which is also the
#   subject the gate itself uses, gold being undecidable here — so each separates
#   wrong from correct on a carrier that computes, and each was checked to FLIP
#   (exit 0) when its claim is flipped (see WITNESS PLACEMENT above). pts=3.
#
# SPEC STRENGTH, probed beyond the shipped rivals (audit, 19 extra builds; all
#   confirmed the spec, none found a hole):
#   thirteen further WRONG impls were built and all were REJECTED — `[]`,
#   `leading`, `tail`, `leading ++ [0] ++ tail`, `leading.take (len-1) ++ tail`,
#   `leading.drop 1 ++ leading.take 1 ++ tail` (rotation), `(leading ++
#   tail).eraseDups`, `(leading ++ tail).mergeSort`, a zip-interleave, and three
#   input-conditional impls that agree with the post-image on a sub-domain and
#   diverge outside it (`if leading.length ≤ 1 then leading ++ tail else tail ++
#   leading`; `if (leading ++ tail).length = 3 then ... else leading.reverse ++
#   tail`). Each left a semantic residual goal under `ensures_1`, e.g.
#   `⊢ tail ++ leading = leading ++ tail` — the clause itself, unprovable.
#   six further CORRECT reshapes were built and all VERIFIED — `restoreSeq leading
#   tail`, `leading.foldr (fun c acc => c :: acc) tail`, `leading.reverse.reverse
#   ++ tail`, `leading ++ ([] ++ tail)`, `(tail.reverse ++ leading.reverse).reverse`,
#   and a two-phase forward loop that appends `leading` then `tail` under two
#   separate `take`-prefix invariants. So the clause is not sensitive to the shape
#   in which the concatenation is computed.
#
# AXIOM_TESTS: none. The sibling records the axiom lane as vacuous (meta.axioms
#   == []): the modeled operation is pure order-preserving list concatenation
#   modeled deeply in the impl, with no axiomatized callee. There is nothing for
#   G-AX to probe, and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
