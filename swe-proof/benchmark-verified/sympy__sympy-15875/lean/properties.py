"""properties.py — G-PBT falsification battery for sympy__sympy-15875 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's ``witness`` holds of the rival while
FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models one function ``add_is_zero(classes, sub_is_zero)`` with a
fractional-permission ``classes`` input; this Lean bundle models the SAME single
purely-functional core as ``zeroStatus(terms, realSumZero)`` — a total function
from the per-summand category list and the three-valued real-anchor fact to the
three-valued verdict. The nagini rivals are re-expressed against the frozen
Lean spec; each nagini case's disposition (ported, or principally omitted) is in
the module ``assessment`` at the foot of this file.

DEFENDED SURFACE (one modeled behavior). The postcondition pins ``result``
equal to a single GROUNDED computation ``zeroVerdict terms realSumZero`` over the
two inputs, so it is a CASE PARTITION of the input domain with these independent
top-level clauses, selected by the inputs:

  * any undecidable/unclassifiable term present  -> undetermined (``none``);
  * every term a real-zero  -> definitely zero (``some true``);
  * no definitely-nonzero real anchor, or every term such an anchor  ->
    undetermined (``none``) — this is the CHANGED clause (the fix adds the
    "no anchor" half of this disjunct);
  * with an anchor and the anchor sub-sum itself zero: the imaginary content
    decides — no imaginary/imaginary-or-zero -> zero; a pure imaginary and no
    imaginary-or-zero -> nonzero; otherwise undetermined;
  * with an anchor and the anchor sub-sum nonzero  -> definitely nonzero;
  * with an anchor and the anchor sub-sum undetermined  -> undetermined.

The BEHAVIOURAL DISCRIMINATOR (the fix): a sum with NO definitely-nonzero real
term but some imaginary content must stay UNDETERMINED. The pre-fix routine
tested only the "every term is a nonzero anchor" half and so returned a definite
(wrong) nonzero verdict for the reported witness (two imaginary summands whose
real anchor sub-sum is empty, hence zero); the partial-domain rival below IS that
pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini frame-mutation rival (a
    store into the read-only input list) has no expressible instance here and no
    substitute is fabricated. (nagini case 1.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs (the category list and
    the three-valued anchor fact), fully computed by the impl's loop. There is
    NO opaque answer key an implementation could echo — every clause pins the
    verdict to a concrete three-valued constant on the category profile, so the
    only way to satisfy the spec is to compute that constant. In its place the
    battery carries an honest cheapest-implementation POSITIVE CONTROL.

    AUDIT NOTE (soundness positive rebuilt). Because the postcondition is the
    single equation ``result = zeroVerdict terms realSumZero``, the impl
    ``:= zeroVerdict terms realSumZero`` is the spec's own right-hand side, so
    it is DEFINITIONALLY the pinned value and its obligation closes by bare
    ``rfl`` with no reasoning about the modeled behavior at all. Such a positive
    verifies honestly but demonstrates nothing about whether the spec admits a
    genuinely reshaped correct impl — a SPEC-TOO-STRONG probe that cannot fail.
    The soundness positive below is therefore a reshape that is NOT defeq to the
    spec RHS: it computes the same verdict from the four aggregate folds with a
    reordered dispatch, and its obligation needs a real case analysis (bare
    ``rfl`` on it FAILS: ``realSumZero is not definitionally equal to
    implementation_zeroStatus terms realSumZero``, measured). The spec-echo impl
    is kept as a second, cheaper positive so both ends are covered.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject lane. Each rival is
    correct on part of the domain and diverges where one clause bites; the
    witnesses probe distinct input points so no clause is defended at a fixed
    binder value.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl (the frozen proof is tuned to the frozen form), so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet stating the spec predicate directly at one concrete input
and refuting it. The whole carrier is TRANSPARENT and DECIDABLE (no ``opaque``
callee — the recursive real-anchor zero-test enters as the plain input
``realSumZero``), so every witness is a literal-input ``decide`` and needs no
conditioning; each was checked to ELABORATE against its rival and to FAIL on the
frozen solution, so it discriminates rather than asserting a tautology.

BINDER / POINT SPREAD. The spec predicate has two input binders, ``terms`` and
``realSumZero``. The reject witnesses move both: ``realSumZero`` takes all three
values (``some true`` at the imaginary/anchor clauses, ``some false`` at the
anchor-nonzero clause, ``none`` at the anchor-undetermined and structural
clauses); ``terms`` ranges over category profiles of length two, three and four
mixing every relevant constructor (``realZero``, ``realNonzero``, ``imaginary``,
``imagOrZero``, ``realUnknown``, ``indeterminate``). The reject witnesses probe
pairwise-distinct inputs, and no two rivals share a point — re-checked by
enumeration over the eleven shipped reject witnesses, all eleven
(terms, realSumZero) pairs distinct.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class. A rival whose
    body is a bare self-call under `partial def` stays inside the variant scope
    (no new axiom, no `sorry`, statement byte-identical) and DOES fail to verify,
    so the outcome the gate would record is the right one. But it fails for a
    reason no witness can convert into a refutation of the spec: the impl name is
    irreducible, so a literal-input `decide` on it does not evaluate
    (measured: `Tactic 'decide' failed … because its 'Decidable' instance
    instDecidableNot`, and the same error appears for a DIFFERENT input, so the
    exit code carries nothing about the claim). Conditioning the witness on the
    impl's value instead (`example (h : implementation_zeroStatus … = some false)
    : ¬ problem_spec_zeroStatus …`) is worse, not better: measured, that snippet
    elaborates against BOTH the diverging rival AND the frozen solution (exit 0
    on each), because the hypothesis is unsatisfiable of the frozen impl and the
    rewrite closes the goal regardless — a forgery the gate's own consistency
    probe cannot refute here (`simp_all made no progress`, exit 1, i.e. recorded
    consistent). So the class is recorded as a HOLE in what this spec can pin,
    not shipped as a case: no admissible witness discriminates, and a case whose
    rejection attests to irreducibility rather than to the spec is exactly the
    hollow pass this battery exists to avoid.

AUDIT ADDITIONS (rivals landed against clauses the port left unattacked). Three
leaves of the partition were defended by no rival and are now covered, each with
a witness rebuilt against both subjects:
  * the ``nz == terms.length`` HALF of the undetermined disjunct (the port's
    ``weak-drop-no-anchor`` deletes only the other, ``nz == 0``, half, so an impl
    keeping just ``nz == 0`` was unattacked);
  * the ``indeterminate`` constructor of the outer unclassified guard (the port's
    ``weak-unclassified-not-short-circuit`` moves only ``realUnknown``);
  * the ``im && imOrZ -> none`` leaf of the anchor-zero imaginary dispatch (a
    profile carrying BOTH imaginary classes at once, which no ported witness
    reaches).

SECOND-AUDIT ADDITION (one further leaf, found by enumeration rather than by
reading). Enumerating the nine top-level leaves against all ten then-shipped
rivals over every category profile of length <= 4 and all three anchor-fact
values showed exactly ONE leaf that no rival differed from the frozen verdict
anywhere inside and that no witness pinned: the anchor-zero CANCELLATION leaf
(anchor sub-sum zero, neither imaginary class present, verdict definite zero).
``weak-cancel-leaf-underdecide`` closes it. Every leaf of the partition is now
pinned by at least one witness at a point where gold and the rival disagree.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the real-anchor zero-test is supplied as an input, not axiomatized).
The nagini ``AXIOM_TESTS`` (the deep-model soundness/containment probes) belong
to G-AX, not this gate; they are dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15875"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positives that
# re-prove / add a ground `have`, the proof region), so same_spec is preserved.

# The whole impl region (soundness positive replaces the imperative loop with an
# equivalent functional body and re-proves).
_IMPL_REGION = _BASE[_BASE.index("-- impl-start"):
                     _BASE.index("-- impl-end") + len("-- impl-end")]

# The whole proof region (soundness positive replaces it with the matching `rfl`
# proof for the functional impl; obligation STATEMENT kept byte-identical).
_PROOF_REGION = _BASE[_BASE.index("-- proof-start"):
                      _BASE.index("-- proof-end") + len("-- proof-end")]

# The frozen proof's opening lines (admissibility prepends a ground `have`).
_PROOF_HEAD = ("  intro terms realSumZero\n"
               "  unfold problem_spec_zeroStatus\n"
               "  by_cases h : terms.any isUnclassified = true")

# Impl-region decision-tail landmarks (each carries no loop-invariant duty).
_I_ZN = "  if z == terms.length then\n    return some true"
_I_NZ0 = "  if nz == 0 || nz == terms.length then\n    return none"
_I_IOZ = "      if !imOrZ && !im then\n        return some true"
_I_IM3BLOCK = ("      if !imOrZ && !im then\n        return some true\n"
               "      if im && !imOrZ then\n        return some false\n")
_I_SOMEFALSE = "  | some false => return some false"
_I_SUBNONE = "  | none => pure ()"
_I_REALUNK = "    | .realUnknown => return none"
_I_INDET = "    | .indeterminate => return none"
_I_IMNOTIOZ = "      if im && !imOrZ then\n        return some false"

# The frozen obligation STATEMENT, reused verbatim by every case that reproves
# (so `variant_scope`'s byte-identical-statement rule holds by construction).
_STMT = """theorem correct_zeroStatus :
    ∀ (terms : List Summand) (realSumZero : Option Bool),
      problem_spec_zeroStatus terms realSumZero
        (implementation_zeroStatus terms realSumZero) := by"""
if _STMT not in _BASE:
    raise AssertionError("drift: frozen obligation statement not found")


# ---- soundness positive (PRIMARY): a reshape that is NOT defeq to the spec ----
# Loop-free like the echo below, but it does NOT return the spec's right-hand
# side: it recomputes the verdict from the four aggregate folds with the
# `realSumZero` dispatch REORDERED (the `some false` / `none` leaves pulled
# ahead of the `some true` imaginary cascade, and that cascade flattened from
# `!imOrZ && !im` / `im && !imOrZ` into nested single-flag guards). Every leaf
# returns the same three-valued constant as the frozen impl on the same profile,
# but the term is not the spec's, so bare `rfl` does NOT close it (measured:
# `realSumZero is not definitionally equal to implementation_zeroStatus terms
# realSumZero`) and the obligation must be re-established by case analysis. That
# is what makes it a real SPEC-TOO-STRONG probe rather than a tautology.
_POS_RESHAPE_IMPL = """-- impl-start
def implementation_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) : Option Bool :=
  if terms.any isUnclassified then none
  else if terms.countP isRealZero == terms.length then some true
  else if terms.countP isRealNonzero == 0
          || terms.countP isRealNonzero == terms.length then none
  else
    match realSumZero with
    | some false => some false
    | none => none
    | some true =>
        if terms.any isImagOrZero then none
        else if terms.any isImag then some false
        else some true
-- impl-end"""

_POS_RESHAPE_PROOF = """-- proof-start
""" + _STMT + """
  intro terms realSumZero
  unfold problem_spec_zeroStatus implementation_zeroStatus zeroVerdict
  by_cases h : terms.any isUnclassified = true
  · simp only [h, if_true]
  · have h' : terms.any isUnclassified = false := by simpa using h
    simp only [h', Bool.false_eq_true, if_false]
    by_cases hz : (terms.countP isRealZero == terms.length) = true
    · simp only [hz, if_true]
    · simp only [hz, Bool.false_eq_true, if_false]
      by_cases hnz : (terms.countP isRealNonzero == 0
                        || terms.countP isRealNonzero == terms.length) = true
      · simp only [hnz, if_true]
      · simp only [hnz, Bool.false_eq_true, if_false]
        rcases realSumZero with _ | b
        · rfl
        · cases b
          · rfl
          · cases hio : terms.any isImagOrZero <;>
              cases hi : terms.any isImag <;> simp [hio, hi]
-- proof-end"""

_POS_RESHAPE = _swap(_swap(_BASE, _IMPL_REGION, _POS_RESHAPE_IMPL),
                     _PROOF_REGION, _POS_RESHAPE_PROOF)

# ---- soundness positive (SECONDARY): the cheapest correct impl -----------
# The spec's own right-hand side. Honest and it must verify, but note it is
# DEFINITIONALLY the pinned value, so its `rfl` proof exercises no reasoning
# about the modeled behavior; it is retained as the cheapest-impl end of the
# range, not as the load-bearing SPEC-TOO-STRONG probe (see the AUDIT NOTE in
# the module docstring).
_POS_IMPL = """-- impl-start
def implementation_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) : Option Bool :=
  zeroVerdict terms realSumZero
-- impl-end"""

_POS_PROOF = """-- proof-start
""" + _STMT + """
  intro terms realSumZero
  rfl
-- proof-end"""

_POS_CONTROL = _swap(_swap(_BASE, _IMPL_REGION, _POS_IMPL), _PROOF_REGION, _POS_PROOF)

# ---- admissibility: discharge the obligation at a ground F2P-shaped input ----
# SECOND-AUDIT NOTE. The point was moved. The previous version discharged the
# obligation at an all-real-zero profile, which is the `z == n` leaf — a normal
# input, but NOT the profile the reporting input has, so the case's own claim to
# be "F2P-shaped" was prose the manifest did not demonstrate. The point below is
# the reporting profile itself (the no-anchor / imaginary-content profile whose
# verdict must stay undetermined), which is exactly where the pre-fix behavior
# answered definitely and where PRECOND-TOO-STRONG would bite if the modeled
# behavior were unsatisfiable there. Measured: the `have` closes by `decide` and
# the file verifies (exit 0).
_ADMISS_HAVE = (
    "  have _ground : problem_spec_zeroStatus [Summand.imaginary, Summand.imaginary] (some true)\n"
    "      (implementation_zeroStatus [Summand.imaginary, Summand.imaginary] (some true)) := by\n"
    "    unfold problem_spec_zeroStatus; decide\n"
)
_ADMISS = _swap(_BASE, _PROOF_HEAD, _ADMISS_HAVE + _PROOF_HEAD)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS
    # =====================================================================
    # Ports nagini case (5) pos-control-tail-reshape. The nagini positive kept
    # the imperative tail but flattened the sub-dispatch into an equivalent
    # cascade. Here the structurally-different-but-CORRECT impl drops the
    # imperative loop entirely and returns the grounded spec computation
    # directly; the obligation STATEMENT is byte-identical and re-proved by
    # `rfl` (no helper lemma, no axiom, no assumption token).
    # PRIMARY soundness positive (added by audit): a reshape that is NOT
    # definitionally the spec's right-hand side, so its obligation is genuinely
    # re-established rather than closed by conversion. See the AUDIT NOTE in the
    # docstring for why the echo below cannot serve as this probe.
    {
        "id": "pos-control-aggregate-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_RESHAPE,
        "rationale": "a structurally-different but CORRECT implementation that is "
                     "NOT definitionally the value the spec pins: it drops the "
                     "imperative accumulator loop and recomputes the verdict from "
                     "the four aggregate folds with the anchor dispatch reordered "
                     "(definite-nonzero and undetermined leaves pulled ahead of the "
                     "anchor-zero imaginary cascade, and that cascade flattened into "
                     "nested single-flag guards). Bare `rfl` does NOT close it, so "
                     "the obligation is re-established by case analysis over the "
                     "unclassified guard, the all-zero guard, the anchor-count guard "
                     "and the three-valued anchor fact; every leaf agrees with the "
                     "frozen verdict. The theorem STATEMENT is byte-identical; only "
                     "the impl body and the tactic body differ. If it fails to verify "
                     "the postcondition is over-fit to the exact imperative spelling "
                     "=> SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-functional-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CONTROL,
        "rationale": "a structurally-different but CORRECT implementation: instead "
                     "of the imperative accumulator loop it returns the grounded "
                     "verdict computation directly, which is definitionally the "
                     "result the spec pins, so `result = zeroVerdict …` holds on "
                     "every input and the re-proof is `rfl`. The theorem STATEMENT "
                     "is byte-identical; only the impl body and the tactic body "
                     "differ. If it fails to verify the postcondition is over-fit "
                     "to the exact imperative spelling => SPEC-TOO-STRONG.",
    },
    # Ports nagini case (6) admiss-self-call. The frozen `correct_zeroStatus`
    # carries no precondition hypothesis (the modeled behavior is total, `∀`
    # unguarded), so there is no precondition binder to attack; the honest
    # analogue is to discharge the spec predicate by evaluation at a ground
    # F2P-shaped input alongside the frozen obligation, confirming the modeled
    # behavior is SATISFIABLE (non-vacuous) there.
    {
        "id": "admiss-ground-allzero-instance",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "the obligation is discharged at the ground REPORTING-SHAPED "
                     "input — the no-anchor profile carrying only imaginary content, "
                     "whose verdict must stay undetermined, i.e. exactly the point "
                     "the CHANGED clause governs — by `decide` inside a `have`, then "
                     "the frozen obligation is closed verbatim. That point is chosen "
                     "over a bland all-real-zero sum because it is where the modeled "
                     "behavior would be unsatisfiable if the partition were "
                     "over-constrained. Verifies unless the modeled behavior is "
                     "unsatisfiable at exactly a normal reporting input (the "
                     "analogue of PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, the "
                     "ground instance is a `have` inside the existing tactic body.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals (each with a discriminating witness)
    # =====================================================================

    # ---- the fix itself (ports nagini (3a) partial-domain-drop-nz0) ----
    {
        "id": "weak-drop-no-anchor",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: test only "every term is a nonzero anchor", dropping
        # the "no anchor at all" half of the undetermined guard.
        "module": _swap(_BASE, _I_NZ0,
                        "  if nz == terms.length then\n    return none"),
        "refinement": "this IS the pre-fix behavior (the fix ADDS the no-anchor "
                      "half of the undetermined disjunct). With no definitely-"
                      "nonzero real term the anchor sub-sum is empty, hence zero, "
                      "so control falls into the anchor-zero dispatch and — on the "
                      "reported witness (two imaginary summands, so a pure imaginary "
                      "present and no imaginary-or-zero) — returns the WRONG "
                      "definite-nonzero verdict where the true answer is "
                      "undetermined. The F2P test asserts the reported complex sum "
                      "is undetermined, so the faithful real patch (the unpatched "
                      "guard line) does NOT resolve — it is exactly the bug fixed.",
        "rationale": "REJECT from the CHANGED clause: with no definitely-nonzero "
                     "real anchor (and not all-zero) the spec pins the verdict to "
                     "`none`, and the rival returns a definite verdict. Binder "
                     "spread: terms = two imaginary, realSumZero = some true.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.imaginary, Summand.imaginary] (some true)\n"
            "    (implementation_zeroStatus [Summand.imaginary, Summand.imaginary] (some true)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- ports nagini (3b) partial-domain-subnone-false ----
    {
        "id": "weak-anchor-undetermined-false",
        "kind": "uniqueness",
        "expect": "reject",
        # In the active region, when the real-anchor fact is undetermined, return
        # a definite nonzero verdict instead of undetermined.
        "module": _swap(_BASE, _I_SUBNONE, "  | none => return some false"),
        "refinement": "a faithful real patch that treated an UNDECIDED real-anchor "
                      "sub-sum as provably nonzero would fabricate a definite "
                      "is_zero=False the assumption engine cannot justify — wrong "
                      "on any sum whose real anchor has undetermined zero-ness — "
                      "corrupting the three-valued contract the P2P assumption "
                      "tests depend on. Faithful but non-resolving.",
        "rationale": "REJECT from the anchor-undetermined clause: active region "
                     "with realSumZero = none pins the verdict to `none`; the rival "
                     "returns `some false`. Binder spread: terms = one nonzero "
                     "anchor + one real-zero, realSumZero = none.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realNonzero, Summand.realZero] none\n"
            "    (implementation_zeroStatus [Summand.realNonzero, Summand.realZero] none) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- ports nagini (3c) partial-domain-ioz-true ----
    {
        "id": "weak-ignore-imag-or-zero-true",
        "kind": "uniqueness",
        "expect": "reject",
        # In the anchor-zero branch, drop the imaginary-or-zero guard: declare the
        # sum zero whenever no pure imaginary is present, ignoring an
        # imaginary-or-zero term.
        "module": _swap(_BASE, _I_IOZ, "      if !im then\n        return some true"),
        "refinement": "a faithful real patch that ignored the imaginary-or-zero "
                      "class and declared the sum zero whenever the real part "
                      "vanishes would return is_zero=True for a sum carrying a term "
                      "that is imaginary-or-zero (zero-ness undetermined) — claiming "
                      "a possibly-nonzero expression is zero, a soundness break in "
                      "the assumption engine. Faithful but non-resolving.",
        "rationale": "REJECT from the anchor-zero imaginary-content clause: with an "
                     "anchor sub-sum zero and an imaginary-or-zero term present the "
                     "spec pins the verdict to `none`; the rival returns `some "
                     "true`. Binder spread: terms include an imagOrZero term, "
                     "realSumZero = some true.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realNonzero, Summand.realZero, Summand.imagOrZero] (some true)\n"
            "    (implementation_zeroStatus [Summand.realNonzero, Summand.realZero, Summand.imagOrZero] (some true)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- ports nagini (3d) partial-domain-im3-none ----
    {
        "id": "weak-imag-underdecide-none",
        "kind": "uniqueness",
        "expect": "reject",
        # In the anchor-zero branch, drop the pure-imaginary nonzero conclusion so
        # it falls through to undetermined instead of definite nonzero.
        "module": _swap(_BASE, _I_IM3BLOCK,
                        "      if !imOrZ && !im then\n        return some true\n"),
        "refinement": "a faithful real patch that failed to conclude nonzero when "
                      "the real part is zero and a pure-imaginary term remains "
                      "would under-decide is_zero from a definite False to "
                      "undetermined, failing the assumption tests that expect the "
                      "definite nonzero conclusion. Faithful but non-resolving.",
        "rationale": "REJECT from the discriminating anchor-zero clause: with an "
                     "anchor sub-sum zero, a pure imaginary present and no "
                     "imaginary-or-zero, the spec pins the verdict to `some false` "
                     "(definite nonzero); the rival returns `none`. Binder spread: "
                     "terms include an imaginary term, realSumZero = some true.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realNonzero, Summand.realZero, Summand.imaginary] (some true)\n"
            "    (implementation_zeroStatus [Summand.realNonzero, Summand.realZero, Summand.imaginary] (some true)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- added for clause coverage: the anchor-nonzero clause ----
    # No nagini counterpart attacks this clause directly; added so the
    # realSumZero=some false leaf of the partition is defended.
    {
        "id": "weak-anchor-nonzero-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # When the real-anchor fact is definitely nonzero, fall through to
        # undetermined instead of returning definite nonzero.
        "module": _swap(_BASE, _I_SOMEFALSE, "  | some false => pure ()"),
        "refinement": "a faithful real patch that dropped the definite-nonzero "
                      "conclusion when the real anchor sub-sum is itself nonzero "
                      "would weaken is_zero to undetermined for a sum with a "
                      "provably-nonzero real part, failing the assumption tests "
                      "expecting the definite False. Non-resolving.",
        "rationale": "REJECT from the anchor-nonzero clause: active region with "
                     "realSumZero = some false pins the verdict to `some false`; "
                     "the rival returns `none`. Binder spread: this is the ONLY "
                     "rival moving realSumZero to `some false`, so that leaf is "
                     "demonstrated live.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realNonzero, Summand.realZero] (some false)\n"
            "    (implementation_zeroStatus [Summand.realNonzero, Summand.realZero] (some false)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- added for clause coverage: the unclassified short-circuit ----
    # The load-bearing outer guard (`terms.any isUnclassified -> none`); no
    # nagini case isolates it on this carrier.
    {
        "id": "weak-unclassified-not-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        # Treat an undecidable real term as a definitely-nonzero anchor instead of
        # forcing the undetermined short-circuit.
        "module": _swap(_BASE, _I_REALUNK, "    | .realUnknown => nz := nz + 1"),
        "refinement": "a faithful real patch that treated a real term of "
                      "undetermined zero-ness as a definitely-nonzero anchor would "
                      "let it participate in the anchor dispatch and produce a "
                      "definite verdict, whereas the presence of any undecidable "
                      "real term must force undetermined — a soundness break. "
                      "Non-resolving.",
        "rationale": "REJECT from the outer unclassified guard: any undecidable "
                     "term present pins the verdict to `none`; the rival mis-counts "
                     "it and yields a definite verdict. Binder spread: terms "
                     "include a realUnknown term, realSumZero = some false — the "
                     "only rival exercising realUnknown.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realUnknown, Summand.realZero] (some false)\n"
            "    (implementation_zeroStatus [Summand.realUnknown, Summand.realZero] (some false)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- added for clause coverage: the all-zero clause ----
    # The `z == n -> some true` clause; no nagini case isolates it.
    {
        "id": "weak-allzero-underdecide",
        "kind": "uniqueness",
        "expect": "reject",
        # When every term is a real-zero, return undetermined instead of the
        # definite zero verdict.
        "module": _swap(_BASE, _I_ZN, "  if z == terms.length then\n    return none"),
        "refinement": "a faithful real patch that answered undetermined for a sum "
                      "of only real-zero terms would refuse the guaranteed zero "
                      "verdict, weakening is_zero from True to undetermined and "
                      "failing the assumption tests asserting such a sum is zero. "
                      "Non-resolving.",
        "rationale": "REJECT from the all-zero clause: with every term a real-zero "
                     "the spec pins the verdict to `some true`; the rival returns "
                     "`none`. Binder spread: terms = two real-zero, realSumZero = "
                     "none.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realZero, Summand.realZero] none\n"
            "    (implementation_zeroStatus [Summand.realZero, Summand.realZero] none) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # =====================================================================
    # AUDIT ADDITIONS — clauses the port left with no rival at all
    # =====================================================================

    # ---- the OTHER half of the undetermined disjunct ----
    # `weak-drop-no-anchor` deletes the `nz == 0` half (the fix's half). The
    # `nz == terms.length` half — every term a definitely-nonzero anchor, so the
    # anchor sub-sum IS the whole sum and settles nothing about it — was
    # undefended: an impl keeping only `nz == 0` passed no case.
    {
        "id": "weak-drop-all-anchor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_NZ0, "  if nz == 0 then\n    return none"),
        "refinement": "a faithful real patch that kept only the no-anchor half of the "
                      "undetermined guard would let a sum made up ENTIRELY of "
                      "definitely-nonzero real terms fall into the anchor dispatch, "
                      "where the anchor sub-sum is the whole sum and so decides "
                      "nothing new: it reports the sum definitely zero on the "
                      "strength of its own zero-ness assumption, fabricating a "
                      "definite verdict from a vacuous premise. Faithful but "
                      "non-resolving — it does not restore the undetermined answer "
                      "the reported complex sum needs.",
        "rationale": "REJECT from the second half of the undetermined disjunct: with "
                     "every term a definitely-nonzero anchor the spec pins the verdict "
                     "to `none`; the rival returns a definite verdict. Binder spread: "
                     "terms = two realNonzero (the all-anchor profile, reached by no "
                     "other rival), realSumZero = some true.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realNonzero, Summand.realNonzero] (some true)\n"
            "    (implementation_zeroStatus [Summand.realNonzero, Summand.realNonzero] (some true)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- the second constructor of the unclassified guard ----
    # `weak-unclassified-not-short-circuit` moves `realUnknown` only; the
    # `indeterminate` constructor of `isUnclassified` was undefended.
    {
        "id": "weak-indeterminate-not-short-circuit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_INDET, "    | .indeterminate => imOrZ := true"),
        "refinement": "a faithful real patch that folded a wholly unclassifiable term "
                      "into the imaginary-or-zero class instead of forcing the "
                      "undetermined short-circuit would let a term about which nothing "
                      "is known participate in the anchor dispatch and produce a "
                      "definite verdict — a soundness break: the presence of any term "
                      "that fits none of the categories must force undetermined. "
                      "Non-resolving.",
        "rationale": "REJECT from the outer unclassified guard, second constructor: any "
                     "unclassifiable term present pins the verdict to `none`; the rival "
                     "mis-files it as imaginary-or-zero and yields a definite verdict. "
                     "Binder spread: terms include an indeterminate term — the only "
                     "rival exercising that constructor — realSumZero = some false.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.indeterminate, Summand.realNonzero, Summand.realZero] (some false)\n"
            "    (implementation_zeroStatus [Summand.indeterminate, Summand.realNonzero, Summand.realZero] (some false)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # ---- the both-imaginary-classes leaf of the anchor-zero dispatch ----
    # `weak-ignore-imag-or-zero-true` and `weak-imag-underdecide-none` each move
    # one imaginary flag; the profile carrying BOTH at once (which must stay
    # undetermined) was reached by no witness.
    {
        "id": "weak-both-imag-classes-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_IMNOTIOZ,
                        "      if im then\n        return some false"),
        "refinement": "a faithful real patch that concluded definitely-nonzero from a "
                      "pure-imaginary term while IGNORING a co-present "
                      "imaginary-or-zero term would overlook that the two imaginary "
                      "contributions can cancel: the imaginary content is then not "
                      "pinned away from zero, so the true verdict is undetermined and "
                      "the patch claims a possibly-zero expression is nonzero — a "
                      "soundness break in the opposite direction from the ignore-"
                      "imaginary-or-zero rival. Faithful but non-resolving.",
        "rationale": "REJECT from the anchor-zero imaginary-content clause at its "
                     "BOTH-classes leaf: with an anchor sub-sum zero and a pure "
                     "imaginary AND an imaginary-or-zero term present the spec pins "
                     "the verdict to `none`; the rival returns `some false`. Binder "
                     "spread: the only rival whose terms carry both imaginary "
                     "constructors at once (length-four profile), realSumZero = "
                     "some true.",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realNonzero, Summand.realZero, Summand.imaginary, Summand.imagOrZero] (some true)\n"
            "    (implementation_zeroStatus [Summand.realNonzero, Summand.realZero, Summand.imaginary, Summand.imagOrZero] (some true)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },

    # =====================================================================
    # SECOND-AUDIT ADDITION — the one leaf of the partition with no rival
    # =====================================================================

    # ---- the CANCELLATION leaf of the anchor-zero dispatch ----
    # Enumerating the nine top-level leaves of the partition against all ten
    # shipped rivals over every category profile of length <= 4 and all three
    # anchor-fact values showed exactly one leaf that NO rival differs from the
    # frozen verdict anywhere inside, and that no shipped witness pins:
    # anchor sub-sum ZERO with NO imaginary content of either kind, whose verdict
    # is the definite ZERO. The two imaginary rivals both move a flag and so only
    # ever reach the leaves where a flag is set; the anchor-count rivals never
    # enter the dispatch at this profile. So the spec's positive `some true`
    # conclusion on the cancellation profile was asserted by the docstring's
    # clause list and demonstrated by nothing. This rival under-decides exactly
    # there and nowhere else.
    {
        "id": "weak-cancel-leaf-underdecide",
        "kind": "uniqueness",
        "expect": "reject",
        # In the anchor-zero branch, refuse the definite-zero conclusion when the
        # real anchor cancels and there is no imaginary content at all.
        "module": _swap(_BASE, _I_IOZ, "      if !imOrZ && !im then\n        return none"),
        "refinement": "a faithful real patch that declined to conclude zero when the "
                      "real anchor sub-sum vanishes and the sum carries no imaginary "
                      "content of either kind would under-decide the most basic "
                      "cancellation there is — a purely real sum whose nonzero parts "
                      "provably cancel — weakening is_zero from a definite True to "
                      "undetermined and failing the assumption tests that expect the "
                      "definite zero. It also does not restore the undetermined answer "
                      "the reported complex sum needs, since that input carries "
                      "imaginary content and never reaches this leaf. Faithful but "
                      "non-resolving.",
        "rationale": "REJECT from the anchor-zero CANCELLATION leaf: with an anchor "
                     "sub-sum zero and neither imaginary class present the spec pins "
                     "the verdict to `some true`; the rival returns `none`. This is "
                     "the only rival reaching that leaf — the two imaginary rivals "
                     "each set a flag and so cannot. Binder spread: terms = one "
                     "nonzero anchor + one real-zero, realSumZero = some true (a "
                     "point no other rival's witness uses).",
        "witness": (
            "example : ¬ problem_spec_zeroStatus [Summand.realNonzero, Summand.realZero] (some true)\n"
            "    (implementation_zeroStatus [Summand.realNonzero, Summand.realZero] (some true)) := by\n"
            "  unfold problem_spec_zeroStatus\n"
            "  decide"
        ),
    },
]

# No AXIOM lane here: the bundle declares no `opaque` callee and consumes no
# `axiom` (the recursive real-anchor zero-test is supplied as the input
# `realSumZero`, not axiomatized). The nagini AXIOM_TESTS (deep-model
# soundness/containment) belong to G-AX; dropped.
AXIOM_TESTS = []
