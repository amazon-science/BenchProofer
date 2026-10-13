"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9711 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct anyRequirementUnmet`` header survives) and swaps
in a candidate implementation; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates — the witness must elaborate against the rival and FAIL against
the subject the gate refutes it on).

DEFENDED SURFACE (one contracted method over a finite list of loaded software
components, each carrying a minimum-version requirement). The single obligation
is

    anyRequirementUnmet (reqs : List Requirement)
        require reqs.all reqWellFormed = true
        ensures raised = anyUnmet reqs

with ``anyUnmet`` the disjunction, element by element, of the per-component test
``unmet``:

    unmet r = if !r.isPresent then false
              else if !r.isKnown then true
              else <numeric component-wise order> r.required r.present

i.e. a single component is UNMET iff it is present and either its available
version is indeterminate, or its available version is strictly below the
demanded minimum under the *numeric component-wise* ordering (``verGt``). The
LOAD-BEARING content is that ordering: components are compared as release
NUMBERS, most-significant component first, each read as a base-10 numeral, with
the shorter zero-extended — so a demanded ``0.6`` is met by an available
``0.10`` (because ``6 < 10`` numerically) where a purely textual order would
disagree. That is the discriminator the issue names, and it is attacked from
four independent directions below (textual order, leading-component-only,
strict-instead-of-at-least, and no zero-extension).

The sole input binder is ``reqs : List Requirement``; each element carries four
fields — ``required`` (demanded minimum, ``List Char``), ``present`` (available
version, meaningful only when present & known), ``isPresent`` (whether the
component is loaded at all), and ``isKnown`` (whether its available version is
determinate) — plus the list's own LENGTH and traversal. Every one is varied by
the reject witnesses.

CARRIER NOTE (decisive for the reject lane). Every carrier here is TRANSPARENT:
``verGt`` / ``relGt`` / ``unmet`` / ``anyUnmet`` are concrete ``def``s in the
``pure`` region (the ``axioms`` region declares NOTHING — the numeric comparator
is modeled deeply, validated ``== packaging.version.Version`` by axiom_check.py
as an A-reference, not consumed as an axiom). So each rival's violation is a
ground equality of concrete values, refutable at a literal input with no
conditioning on the carrier: no witness here binds a hypothesis, so none can be
``witness-inconsistent``. The method ALSO carries a real ``require`` clause, so
the admissibility class is not vacuous either.

REDUCTION NOTE (measured on this carrier; the previous revision of this battery
died here). Two distinct reduction walls sit between a witness and its verdict,
and they need different tools:

  1. ``relGt`` is WELL-FOUNDED recursion. ``decide`` reduces the ``Decidable``
     instance rather than computing the value, and it gets stuck on ``relGt``
     for every input — measured, ``example : relGt [9] [10] = false := by
     decide`` fails with ``did not reduce to isTrue or isFalse``, and so does
     ``decide +kernel``. But ``simp [relGt]`` closes exactly that goal. So the
     numeric order must be UNFOLDED by ``simp``, never decided.
  2. The tester's own result sits under ``NonDetT.run`` applied to the method's
     denotation. ``simp`` on the ``pure`` defs alone leaves
     ``match NonDetT.run (pure false) with …`` unreduced; adding ``NonDetT.run``
     and ``pure`` to the ``simp`` set peels it.

So every witness closes with ``simp [<tester>, <exec>, <method>, NonDetT.run,
pure, <pure defs>] <;> decide``: ``simp`` unfolds the whole chain to a ground
Boolean and ``decide`` finishes any residual literal comparison (needed only by
the textual-order rival, whose ``List Char`` ``<`` is a decidable instance simp
leaves alone). Verified out of band for all eight rivals: ``simp`` reduces the
claim all the way to ``False`` on the reference subject, so each failure there
is a real refutation and not a stuck reduction.

WITNESS SUBJECT — why every reject case carries a ``witness_reference``. The
FROZEN impl keeps a ``while`` loop, and under ``loom.semantics.choice
"demonic"`` that loop's fixpoint elaborates through ``Classical.choice``, which
the kernel cannot unfold. Measured on all eight witnesses below: against the
frozen solution every one fails with

    Reduction got stuck at the `Decidable` instance … did not reduce to
    `isTrue` or `isFalse`

— the identical error a TRUE claim about that impl produces, so the frozen
side's exit code carries no information and would attest to a refutation never
performed (``witness-undecided``; that is precisely how the previous revision of
this battery was recorded MALFORMED-TESTS on three cases). Each reject case
therefore names ``witness_reference = _LOOPFREE``: the loop collapsed to the
closed form the post-image names, which shares the frozen spec and VERIFIES
(so it cannot violate its own spec, and a genuine witness must fail on it) and
which DOES reduce. ``_LOOPFREE`` is also shipped as the ``pos-closed-form``
positive, so the battery itself records that loop-freeness is not what any rival
is rejected for. Confirmed out of band with ``scripts/lean_verify.sh``: the
reference verifies (exit 0), every witness elaborates against its rival (exit
0), and every witness fails against the reference by DECIDING the claim false
(``decide proved that the proposition False is false``), never by stuck
reduction.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating loop collapsed to the closed
    form the post-image names; the per-element test bound to a local) must still
    verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries a ``require`` clause, so the domain is not
    total; the residual risk on this transparent carrier is that the post-image
    is UNSATISFIABLE / DEGENERATE at the interesting point (a spec no impl can
    meet reads like one every impl meets). ``admiss-grounded`` discharges an
    in-region assert pinning BOTH directions of the per-element decision at the
    boundary the failing test pins — a component whose demanded minimum EXCEEDS
    its available version is unmet, and one whose minimum is BELOW its available
    version is met — establishing the numeric order is not constant. The
    surrounding impl is kept verbatim so the method's own obligation still
    discharges; both probed inputs satisfy the ``require`` clause, so the
    precondition is shown inhabited on a normal input.
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on the sibling
    because a read-only heap input may carry a fractional permission an impl
    overwrites. Lean and Velvet are referentially transparent: ``reqs`` is an
    immutable value (declared read-only, not ``mut``), there is no heap and no
    aliasing, so there is no read-only input to mutate and no permission system
    to trip. Not fabricated — reported as a vacuous omission in the footer.
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
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``anyUnmet reqs``, computed entirely from the method's own
    argument by concrete ``def``s (the ``axioms`` region is empty; no opaque
    answer key). There is no value an echo could carry that satisfies the ensures
    yet is behaviourally wrong — the unique satisfier IS the grounded decision.
    The honest controls are the cheapest faithful impls that compute it.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Eight wrong
    impls that diverge from the desired behaviour on some sub-domain and MUST be
    rejected, each refuted at a concrete input by a machine-checked witness.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the numeric
version comparator is an A-reference validated by axiom_check.py (G-AX's job),
not a consumed contract. The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9711"
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
# these keeps markers.same_spec True and the prove_correct header intact (the
# spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the requirement list. Reject rivals replace this with a loop-free closed form.
_IMPL = """    let mut acc : Bool := false
    let mut i := reqs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ reqs.length
      invariant acc = anyUnmet (reqs.drop i)
      done_with i = 0
      decreasing i
    do
      let r := reqs[i - 1]!
      acc := unmet r || acc
      i := i - 1
    return acc"""
assert _BASE.count(_IMPL) == 1, "anyRequirementUnmet impl region drifted from expected text"

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let r := reqs[i - 1]!
      acc := unmet r || acc
      i := i - 1"""
assert _BASE.count(_LOOP_BODY) == 1, "loop body drifted from expected text"

# The FULL frozen proof body (everything after `prove_correct ... by`). The
# tactic body is elided from the spec view, so retuning it is a proof reshape,
# not a spec change.
_PROOF = """prove_correct anyRequirementUnmet by
  loom_solve
  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the loop-bearing impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---------------------------------------------------------------------------
# THE WITNESS SUBJECT. The frozen impl's `while` loop elaborates through
# Classical.choice under demonic choice, so `decide` against it is stuck for
# EVERY claim and its exit code discriminates nothing (witness-undecided). This
# loop-free impl computes the same disjunction directly, shares the frozen spec,
# and VERIFIES — so it cannot violate its own spec and a genuine witness must
# still fail on it — and unlike gold it REDUCES. Every reject case below names
# it as `witness_reference`, and it also ships as the `pos-closed-form` positive
# so the battery records that loop-freeness is not what any rival is rejected
# for. The gate verifies it once for the whole battery.
# ---------------------------------------------------------------------------
_LOOPFREE = _impl_reproved(
    "    return (anyUnmet reqs)",
    "prove_correct anyRequirementUnmet by\n  loom_solve")


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `anyRequirementUnmetTester args = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
_TESTER = (
    "extract_program_for anyRequirementUnmet\n"
    "prove_precondition_decidable_for anyRequirementUnmet\n"
    "prove_postcondition_decidable_for anyRequirementUnmet\n"
    "derive_tester_for anyRequirementUnmet\n\n"
)

# The two reduction walls, in one tactic (see REDUCTION NOTE in the docstring):
# `simp` on the pure defs unfolds the well-founded numeric order `relGt` (which
# `decide` and `decide +kernel` both get STUCK on), and `NonDetT.run`/`pure`
# peel the tester's monadic wrapper around the extracted program. `decide`
# finishes any residual literal comparison — needed only where a rival compares
# raw `List Char` values, whose `<` is a decidable instance simp leaves alone.
_PURE_DEFS = ("anyUnmet, unmet, verGt, relGt, splitDots, parseComp, digitVal, "
              "compOk, numericVer, reqWellFormed")
_WITNESS_TAC = (
    "  simp [anyRequirementUnmetTester, anyRequirementUnmetExec, "
    "anyRequirementUnmet, NonDetT.run, pure, " + _PURE_DEFS + "]\n"
    "  <;> decide"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n{_WITNESS_TAC}\n"


# A Requirement literal for readable witnesses. `ver` is a Python str; each char
# becomes a Lean Char literal so the tester reduces (String.toList does not).
def _req(required, present, is_present, is_known):
    def _cl(s):
        return "[" + ", ".join(f"'{c}'" for c in s) + "]"
    return ("{ required := " + _cl(required) + ", present := " + _cl(present) +
            ", isPresent := " + ("true" if is_present else "false") +
            ", isKnown := " + ("true" if is_known else "false") + " }")


def _reqs(*rs):
    return "[" + ", ".join(rs) + "]"


def _tester(*rs):
    return _witness("anyRequirementUnmetTester " + _reqs(*rs))


# Every reject rival replaces the loop with a loop-free per-element scan, so its
# own extracted program reduces at a literal input. Only the per-element test
# differs between them.
def _scan(per_element):
    return _impl("    return (reqs.any (fun r =>\n" + per_element + "))")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures raised = anyUnmet reqs`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same disjunction; the loop-specific proof is
        # retuned to a bare `loom_solve` since the impl now matches the post-image
        # syntactically. This is ALSO the `witness_reference` every reject case
        # below is refuted against, so shipping it here is what records that
        # loop-freeness is not the ground of any rejection.
        "module": _LOOPFREE,
        "rationale": "a loop-free impl that returns the disjunction directly must "
                     "satisfy `raised = anyUnmet reqs`; a correct reshape of the "
                     "modeled behaviour verifying is exactly what SPEC-TOO-STRONG "
                     "would deny. Exercises the obligation from a maximally "
                     "different (loop-free) control-flow shape, and doubles as the "
                     "witness subject for the reject lane — the gate independently "
                     "re-checks that it shares the frozen spec and verifies before "
                     "refuting any witness against it.",
    },
    {
        "id": "pos-letbind",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the per-component test to a local `u` inside the loop
        # instead of using the expression directly. Same value flow; the loop and
        # the front-recursive invariant are unchanged, so the frozen proof still
        # closes untouched.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let r := reqs[i - 1]!\n"
            "      let u : Bool := unmet r\n"
            "      acc := u || acc\n"
            "      i := i - 1"),
        "rationale": "binding the per-component test to a local before combining "
                     "it computes the same disjunction element-for-element, with "
                     "the loop and invariant unchanged, so the frozen proof closes "
                     "and `raised = anyUnmet reqs` still holds; a correct reshape "
                     "must verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries a `require` clause, so the domain is
    # not total; the residual risk is that the post-image is DEGENERATE at the
    # interesting point. This case discharges an in-region assert establishing
    # that the numeric order really does demand `unmet` when the demanded
    # minimum EXCEEDS the available version, and `met` when it is BELOW it — the
    # two directions of the per-element decision, at the boundary the failing
    # test pins. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; both probed inputs satisfy the `require`
    # clause. The proof alternation tries the loop step FIRST (measured: putting
    # the assert branch first leaves the loop-step goal unsolved).
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (anyUnmet [{ required := ['3','.','1','1'], present := ['3','.','1','0'], isPresent := true, isKnown := true }] = true ∧\n"
            "       anyUnmet [{ required := ['3','.','9'], present := ['3','.','1','0'], isPresent := true, isKnown := true }] = false))\n"
            + _IMPL,
            "prove_correct anyRequirementUnmet by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | (rw [anyUnmet_drop_step reqs i (by omega) (by omega)]; simp_all)\n"
            "    | (simp [anyUnmet, unmet, verGt, relGt, splitDots, parseComp, digitVal])"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "boundary the failing test pins: it demands the component be "
                     "UNMET when its demanded minimum exceeds its available version "
                     "(min above loaded) and MET when the minimum is below it (min "
                     "below loaded) — so the numeric order is not constant and the "
                     "obligation is not degenerate. The in-region assert must "
                     "discharge (else PRECOND-TOO-STRONG / a degenerate "
                     "post-image); the impl is kept verbatim so "
                     "`raised = anyUnmet reqs` still verifies. Both probed inputs "
                     "meet the `require` clause, so the precondition is inhabited on "
                     "a normal input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Four attack the numeric
    # ordering from independent directions; three attack the per-element
    # branch structure; one attacks the whole-list traversal.
    # =====================================================================
    {
        "id": "weak-textual-order",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image bug: compare the demanded and available versions
        # LEXICOGRAPHICALLY (raw List Char order) instead of numerically. Correct
        # whenever the textual and numeric orders agree; diverges exactly where a
        # multi-digit component makes them disagree.
        "module": _scan(
            "      if !r.isPresent then false\n"
            "      else if !r.isKnown then true\n"
            "      else decide (r.required > r.present)"),
        "refinement": "this is the literal pre-image: comparing versions as text "
                      "reports a demanded minimum of 3.9 as UNMET by an available "
                      "3.10 (because '9' > '1' textually) though numerically 9 < 10 "
                      "means the requirement is met — exactly the false 'not new "
                      "enough' failure the issue reports for any component past 9. "
                      "The failing test's fulfilled block demands 3.9-against-3.10 "
                      "be accepted with no error raised; a counterpart keeping the "
                      "textual comparison raises there, so it would NOT resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: at a present & known "
                     "component whose demanded minimum 3.9 is below its available "
                     "3.10 NUMERICALLY, the post-image demands `false` (met) while "
                     "the textual rival reports `true` (unmet). Refuted at the "
                     "multi-digit point where textual and numeric orders disagree — "
                     "the exact discriminator, and the exact input the failing "
                     "test's fulfilled block uses.",
        "witness": _tester(_req("3.9", "3.10", True, True)),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-leading-segment",
        "kind": "uniqueness",
        "expect": "reject",
        # A 'major version only' shortcut: compare only the leading dotted
        # component, ignoring the rest. Correct whenever the leading components
        # differ; diverges when they are equal and a later component settles it.
        "module": _scan(
            "      if !r.isPresent then false\n"
            "      else if !r.isKnown then true\n"
            "      else decide (((splitDots r.required).map parseComp).headD 0 >\n"
            "                   ((splitDots r.present).map parseComp).headD 0)"),
        "refinement": "a counterpart that compared only the leading (major) release "
                      "component would accept any available version with the same "
                      "major number regardless of the minor — e.g. a demanded 3.11 "
                      "against an available 3.10 (both major 3) would be judged met. "
                      "The failing test's not-fulfilled block requires a demanded "
                      "3.11 against an available 3.10 to raise; a leading-component "
                      "shortcut raises nothing, so it would NOT resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: at demanded 3.11 vs "
                     "available 3.10 the numeric order is strictly greater (the "
                     "minimum exceeds the loaded version at the SECOND component), "
                     "so the post-image demands `true` (unmet); the leading-only "
                     "rival sees equal majors (3 == 3) and reports `false`. Refuted "
                     "at the second-component boundary the failing test pins.",
        "witness": _tester(_req("3.11", "3.10", True, True)),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-strict-instead-of-at-least",
        "kind": "uniqueness",
        "expect": "reject",
        # The sibling's direction-swap rival, ported: demand the available
        # version be STRICTLY GREATER than the minimum rather than AT LEAST it.
        # Correct on every strictly-below and strictly-above input; diverges
        # exactly at EQUALITY, where a component that exactly meets its minimum
        # is wrongly reported unmet.
        "module": _scan(
            "      if !r.isPresent then false\n"
            "      else if !r.isKnown then true\n"
            "      else !verGt r.present r.required"),
        "refinement": "a counterpart demanding the available version be STRICTLY "
                      "above the configured minimum would reject a component that "
                      "meets its minimum EXACTLY — the overwhelmingly common "
                      "configuration, since a minimum is normally pinned at a "
                      "release that is actually installed. It reintroduces the "
                      "issue's 'not new enough' abort for an adequate version (now "
                      "on the equal-version sub-domain instead of the multi-digit "
                      "one), so it would NOT resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: the per-element test is "
                     "AT-LEAST (unmet iff the minimum is strictly greater than the "
                     "available version), so at demanded 1.0 against available 1.0 "
                     "the post-image demands `false` (met); the strict rival, "
                     "requiring the available version to exceed the minimum, reports "
                     "`true`. Refuted at the EQUALITY point — the only sub-domain "
                     "where at-least and strictly-greater differ, and one no other "
                     "rival here probes.",
        "witness": _tester(_req("1.0", "1.0", True, True)),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-no-zero-extension",
        "kind": "uniqueness",
        "expect": "reject",
        # Compare the parsed component lists with the plain list order instead of
        # the ZERO-EXTENDED numeric order: a shorter list is judged below a
        # longer one that agrees on the shared prefix. Correct on every pair of
        # equal-length version strings; diverges exactly where the two versions
        # have different component COUNTS but equal numeric value.
        "module": _scan(
            "      if !r.isPresent then false\n"
            "      else if !r.isKnown then true\n"
            "      else decide (((splitDots r.present).map parseComp) <\n"
            "                   ((splitDots r.required).map parseComp))"),
        "refinement": "a counterpart that dropped the zero-extension would treat a "
                      "trailing-zero component as significant, so an available "
                      "version written with fewer components than the configured "
                      "minimum is judged below it even when the two denote the SAME "
                      "release. That aborts the build for a component that exactly "
                      "meets its minimum — the same false 'not new enough' failure "
                      "the issue reports, on the differing-component-count "
                      "sub-domain — and the issue's own scenario pins a minimum and "
                      "a loaded version written with different component counts, so "
                      "it would NOT resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: the numeric order "
                     "zero-extends the shorter component list, so a demanded 0.10.0 "
                     "and an available 0.10 denote the same release and the "
                     "post-image demands `false` (met); the un-extended list order "
                     "judges the shorter available list strictly below and reports "
                     "`true`. Refuted at the differing-component-COUNT point — the "
                     "zero-extension clause of the ordering, which the "
                     "leading-component and textual rivals both leave untested, and "
                     "the only witness here where the two version strings have "
                     "different lengths.",
        "witness": _tester(_req("0.10.0", "0.10", True, True)),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-ignore-indeterminate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the indeterminate-version clause: a present component whose
        # available version is indeterminate is treated as MET instead of unmet.
        # Correct on every determinate component; diverges on the indeterminate
        # sub-domain.
        "module": _scan(
            "      if !r.isPresent then false\n"
            "      else if !r.isKnown then false\n"
            "      else verGt r.required r.present"),
        "refinement": "a counterpart that dropped the indeterminate-version guard "
                      "would treat a loaded component whose version cannot be "
                      "determined as satisfying the minimum and let the build "
                      "proceed; the desired behaviour requires an indeterminate "
                      "available version to be reported unmet (the build must "
                      "abort). A counterpart missing the guard leaves an "
                      "indeterminate component unreported, so it would NOT resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: on the "
                     "present-but-indeterminate sub-domain (`isPresent` true, "
                     "`isKnown` false) `unmet` is `true`, so the post-image demands "
                     "`true`; the rival reports `false`. Refuted at an "
                     "indeterminate-version component — the branch that moves "
                     "`isKnown` to false while the version-order rivals hold it "
                     "true, and one the numeric order is never consulted for.",
        "witness": _tester(_req("2.1", "2.1", True, False)),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-absent-imposes-obligation",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the absent-component clause: an ABSENT component (not loaded at
        # all) is subjected to the version test instead of imposing no obligation.
        "module": _scan(
            "      if !r.isKnown then true\n"
            "      else verGt r.required r.present"),
        "refinement": "a counterpart that dropped the absent-component guard would "
                      "fail the build for a component that is not loaded at all — "
                      "but an absent component is warned-and-skipped, never a hard "
                      "failure. It would report a build error where the desired "
                      "behaviour imposes no version obligation, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: on the absent "
                     "sub-domain (`isPresent` false) `unmet` is `false` (no "
                     "obligation), so the post-image demands `false`; the rival, "
                     "having dropped the `isPresent` guard, reaches the "
                     "indeterminate branch and reports `true`. Refuted at an "
                     "absent component — the only single-element reject moving "
                     "`isPresent` to false.",
        "witness": _tester(_req("5", "4", False, False)),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-never-report",
        "kind": "uniqueness",
        "expect": "reject",
        # Never report any requirement unmet: always returns false, ignoring the
        # decision entirely. Correct on every all-met input; diverges on any
        # input with an unmet component.
        "module": _impl("    return false"),
        "refinement": "always reporting all requirements met is what a counterpart "
                      "that deleted the failure branch entirely would do — it never "
                      "aborts the build for a too-old component. It fails the "
                      "not-fulfilled block of the failing test, which asserts a "
                      "build error IS raised for a loaded component below its "
                      "configured minimum, so it would NOT resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: at a present & known "
                     "component whose demanded minimum 4.0 exceeds its available "
                     "3.9 numerically, `anyUnmet` is `true`, so the post-image "
                     "demands `true`; the rival returns `false`. Verifying would be "
                     "SPEC-TOO-WEAK (the report obligation is unpinned). Refuted at "
                     "a DIFFERING-LEADING-component point rather than at the "
                     "3.11/3.10 point weak-leading-segment uses: this rival is wrong "
                     "on the whole unmet sub-domain, so its witness belongs at an "
                     "input where the near-miss leading-component rival is RIGHT "
                     "(confirmed out of band: the leading-only rival is NOT refuted "
                     "here). Sharing a point would let this rival's rationale borrow "
                     "a sub-domain the near-miss already covers.",
        "witness": _tester(_req("4.0", "3.9", True, True)),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult only the FIRST component instead of the whole list — a
        # traversal clause the list carrier introduces (the single-component
        # sibling has no list to abuse). Every per-component decision it makes is
        # right; it just stops after the first. Refuted only on a list of length
        # >= 2 whose first component is met and a later one is unmet.
        "module": _impl(
            "    return (match reqs with\n"
            "      | [] => false\n"
            "      | r :: _ => unmet r)"),
        "refinement": "a counterpart that checked only the first configured "
                      "requirement would let the build proceed whenever the first "
                      "component happens to be satisfied, even if a LATER loaded "
                      "component is below its minimum; the check must abort if ANY "
                      "requirement is unmet. It would leave a genuinely too-old "
                      "later component unreported, so it would NOT resolve.",
        "rationale": "REJECT from `raised = anyUnmet reqs`: `anyUnmet` is the "
                     "disjunction over ALL components, so at a two-element list "
                     "whose first component is met (demanded 0.6 against available "
                     "0.10 — the issue's own scenario, met numerically) and whose "
                     "second is unmet (demanded 3.11 against available 3.10) the "
                     "post-image demands `true`; the first-only rival returns the "
                     "first component's `false`. Refuted at a length-2 list — the "
                     "only reject varying `reqs.length` beyond one, closing the "
                     "traversal clause the list carrier introduces, and the only "
                     "witness probing the issue's 0.6/0.10 pair.",
        "witness": _tester(_req("0.6", "0.10", True, True),
                           _req("3.11", "3.10", True, True)),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 5 uniqueness — one of which is the
# mandatory frame-mutation rival) plus 1 AXIOM_TESTS entry. The sibling
# contracts one function, `verify_requirement`, over TWO parallel READ-ONLY
# release-segment lists carrying fractional heap permissions, with a
# normal-return / raise control-flow split. This bundle contracts one method,
# `anyRequirementUnmet`, over a LIST of `Requirement` records with the numeric
# order modeled deeply and no axioms; the raise-vs-return split is abstracted to
# the returned Bool (raise <=> true). The two surfaces model the SAME decision
# (a requirement is unmet iff the loaded version is indeterminate or numerically
# below the minimum), so the value surface carries across intact; the permission
# surface does not exist here, and the list carrier ADDS a traversal clause.
#
#   sibling case                       kind          -> here                            disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-combined-guard         soundness     -> pos-closed-form / pos-letbind   PORTED (split)
#   admissibility-fulfilled-path       admissibility -> admiss-grounded                 RE-AIMED
#   frame-mutation-reqversion          uniqueness    -> (none)                          VACUOUS
#   prepatch-textual-strict-greater    uniqueness    -> weak-textual-order +            PORTED (split)
#                                                       weak-strict-instead-of-at-least
#   partial-domain-ignore-ext-known    uniqueness    -> weak-ignore-indeterminate       PORTED
#   control-flow-always-return         uniqueness    -> weak-never-report               PORTED
#   partial-domain-leading-segment     uniqueness    -> weak-leading-segment            PORTED
#   (no sibling)                       uniqueness    -> weak-no-zero-extension          ADDED (clause cov.)
#   (no sibling)                       uniqueness    -> weak-absent-imposes-obligation  ADDED (binder cov.)
#   (no sibling)                       uniqueness    -> weak-first-only                 ADDED (list carrier)
#   ax-version-gt-soundness            axiom         -> (none)                          G-AX
#
# ALL 4 of the sibling's non-permission uniqueness rivals ported (one split into
# two, since this carrier expresses both halves of the sibling's surrogate
# separately); its 1 soundness positive split into two shapes; its 1
# admissibility re-aimed; its 1 permission rival vacuous; 3 rivals added.
# Nothing was dropped for being hard to prove.
#
# PORTED-SPLIT (prepatch-textual-strict-greater -> weak-textual-order +
#   weak-strict-instead-of-at-least): the sibling models the pre-image bug as the
#   WRONG comparison DIRECTION (strictly-greater vs at-least) over its @Pure
#   ordering, explicitly calling that a "surrogate" because its ordering is not
#   spelled out from the characters. This bundle models the comparator DEEPLY, so
#   BOTH defects the sibling's one rival conflates are expressible separately and
#   are refuted at DIFFERENT points: the faithful textual order (refuted on the
#   multi-digit 3.9/3.10 point, the headline discriminator) and the
#   strict-instead-of-at-least direction swap (refuted at EQUALITY, 1.0/1.0 — the
#   only sub-domain where the two orders differ). Splitting is what keeps each
#   rival's rationale honest: a single witness could not demonstrate both
#   sub-domains, and the equality point is one no other rival here probes.
# PORTED (partial-domain-ignore-ext-known -> weak-ignore-indeterminate): the
#   sibling drops the unknown-version guard so an unknown loaded version returns
#   normally; here the indeterminate-version clause of `unmet` is dropped, so a
#   present-but-indeterminate component is judged met. Refuted at `isKnown`=false.
# PORTED (control-flow-always-return -> weak-never-report): the sibling's rival
#   never raises (always returns True on the value side); the raise-vs-return
#   split is abstracted to the Bool here, so "never raise" becomes "always return
#   false (all met)". Refuted on the numeric-unmet sub-domain.
# PORTED (partial-domain-leading-segment -> weak-leading-segment): direct port of
#   the 'major version only' shortcut, refuted at the 3.11/3.10 second-component
#   boundary.
# PORTED-SPLIT (pos-control-combined-guard): the sibling's one positive control
#   collapses the two-step fulfilled flag into a single guard. Here the frozen
#   impl is a backward accumulating LOOP, so the reshape spirit is split across
#   two shapes: pos-closed-form (collapse the loop to the closed form the
#   post-image names — a maximally different control-flow shape, which also
#   serves as the reject lane's witness subject) and pos-letbind (bind the
#   per-element test to a local, loop and invariant unchanged).
# RE-AIMED (admissibility-fulfilled-path): the sibling asserts the two half-
#   permissions are usable and a normal return is reachable on the fulfilled
#   branch. This backend has no permission surface; the `require` clause is met
#   by both probed inputs (so the precondition-inhabited spirit survives), and the
#   sharper residual risk on this transparent carrier — a degenerate post-image —
#   is attacked by an in-region assert pinning BOTH directions of the numeric
#   order (min-above-loaded unmet; min-below-loaded met).
# VACUOUS (frame-mutation-reqversion): the sibling's MANDATORY frame-mutation
#   rival keeps the gold body then writes into a read-only input granted only at
#   half permission, and must be rejected for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent: `reqs` is an immutable value, the method
#   declares no `mut` binder, there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the class is
#   vacuous. No substitute is fabricated.
# ADDED (weak-no-zero-extension): the sibling's ordering treats a missing
#   trailing segment as zero, but no sibling rival attacks that clause — its
#   rivals all compare same-length segment lists. Here the zero-extension is an
#   independent clause of `relGt` (the shorter component list is padded, so
#   0.10.0 and 0.10 denote the same release), so it gets its own rival. Sole
#   witness whose two version strings have different component COUNTS.
# ADDED (weak-absent-imposes-obligation): the sibling's two inputs are always
#   present release lists, so it has no analogue for the absent-component clause.
#   Here `isPresent` — an absent component imposes no obligation — is a separable
#   structural clause, so it gets its own binder-coverage rival: the only
#   single-element reject moving `isPresent` to false.
# ADDED (weak-first-only): the list carrier introduces a traversal clause the
#   single-target sibling has no analogue for. `anyUnmet` is the disjunction over
#   ALL components; a rival that consults only the first is refutable only on a
#   length >= 2 list (met first, unmet later). Sole reject varying reqs.length.
# AXIOM_TESTS (1, ax-version-gt-soundness): dropped. The axiom lane is G-AX's job
#   (axiom_check.py validates the deep ordering model against the real numeric
#   comparator); the comparator is an A-reference here with no consumed axiom, and
#   this gate ignores AXIOM_TESTS regardless.
#
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
#
# BINDER / CLAUSE COVERAGE of the 8 reject witnesses over the one input binder
#   `reqs : List Requirement` (elements carry required/present/isPresent/isKnown)
#   of the sole ensures. 8 DISTINCT input points, NO TWO RIVALS SHARING ONE —
#   deliberately, because two of these rivals are near-misses of each other and a
#   shared point would let the weaker one's rationale borrow the stronger one's
#   sub-domain:
#     required / present — 3.9 vs 3.10 (numeric-vs-textual disagreement),
#                          3.11 vs 3.10 (SECOND-component boundary: leading
#                          components equal, so only the minor settles it),
#                          4.0 vs 3.9 (LEADING-component boundary, where the
#                          leading-only rival is correct and only the
#                          report obligation itself is at stake),
#                          1.0 vs 1.0 (EQUALITY — at-least vs strictly-greater),
#                          0.10.0 vs 0.10 (differing component COUNT —
#                          zero-extension), 2.1 vs 2.1, 5 vs 4,
#                          0.6 vs 0.10 (the issue's own scenario, met): the
#                          version content is varied across every independent
#                          sub-domain of the ordering — multi-digit, leading
#                          component, minor component, equality, component count.
#     isPresent          — true (textual, leading-segment, strict, no-zero-ext,
#                          ignore-indeterminate, never-report, first-only's
#                          both elements) AND false (absent-imposes-obligation):
#                          both.
#     isKnown            — true (textual, leading-segment, strict, no-zero-ext,
#                          never-report, first-only) AND false
#                          (ignore-indeterminate, absent-imposes-obligation):
#                          both.
#     reqs.length        — 1 (seven rivals) AND 2 (first-only): varied, so the
#                          traversal clause the list carrier introduces is
#                          attacked.
#   Every independent top-level clause of the post-image is attacked: the numeric
#   ordering from four directions (textual-order / leading-segment / strict /
#   no-zero-extension), the report obligation itself (never-report), the
#   indeterminate-version clause (ignore-indeterminate), the absent-component
#   clause (absent-imposes-obligation), and the whole-list traversal (first-only).
AXIOM_TESTS = []
