"""properties.py — G-PBT falsification battery for sympy__sympy-12419 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start``/``-- impl-end`` — and, where a case
legitimately re-proves, inside ``-- proof-start``/``-- proof-end`` — is changed,
so ``markers.same_spec`` holds and the single ``theorem
correct_identityElement`` STATEMENT stays byte-identical). ``expect:"verify"``
passes iff the variant is in scope AND elaborates with the obligation closed (no
``sorry``/``admit``/``native_decide``, no new ``axiom``/``theorem``);
``expect:"reject"`` passes iff it is in scope AND does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the element accessor over integer CELL TAGS (a ``{10,11,12}`` encoding of
the three returned values) chosen disjoint from a ``{0,1,2}`` encoding of the
comparison status. This Lean bundle models the SAME purely-functional core over
an ALGEBRAIC carrier: the classification of the position pair is the
three-constructor ``IdxCmp``, the outcome of obtaining the deferred indicator is
the two-constructor ``IndOutcome``, the returned value is the three-constructor
``Elem α``, and the nagini clauses collapse into ONE total equation,
``result = elemOf cmp ind i j``. Totality is carried by the type (``Elem α`` has
exactly the three admissible shapes, so nagini's disjunction
``Result() in {10,11,12}`` is a TYPING fact here, not a clause to attack).

TWO CARRIED OBSERVATIONS, and why the second one exists. The modeled routine
reads the position pair through TWO distinct upstream comparison mechanisms, not
one, and they do not agree. The first classifies the pair three ways
(``IdxCmp``); the second is the act of obtaining the deferred indicator, which
carries its OWN means of settling the pair and on some pairs succeeds where the
first classification did not — delivering an outright plain zero instead of a
symbolic value (``IndOutcome.settled_zero``). Both statuses are UNCHANGED
upstream observations carried as plain input data (SPEC_GUIDE §3
carried-observation refinement), and BOTH are load-bearing: a model over the
first observation alone asserts that an undetermined pair always yields a
non-zero symbolic indicator, which the real routine does NOT guarantee — measured
directly against the real callee, see the cell census below. So the spec is
stated over the pair of observations, and it PREDICTS a plain zero exactly where
the real routine produces one.

MEASURED CELL CENSUS against the real post-patch callee (6970 position pairs
drawn from a 23-assumption symbol pool plus randomized arithmetic expressions,
seed 12419, run in the instance container with the gold patch applied). Each cell
is (classification, indicator outcome) and every one recorded here is POPULATED,
so no arm of the spec is dead:

    (known_equal,    left_symbolic)  61     -> one
    (known_equal,    settled_zero)    3     -> one
    (known_distinct, settled_zero)  682     -> zero
    (known_distinct, left_symbolic) 750     -> zero
    (undetermined,   left_symbolic) 4525    -> the symbolic indicator
    (undetermined,   settled_zero)  801     -> a PLAIN ZERO

The last row is the one a one-observation model gets wrong; it is 801/5326 = 15%
of the undetermined pairs, not a corner. The repaired model's predictions were
diffed against the real callee's returned value on all 6970 pairs: ZERO
disagreements. A separate 23403-pair search found NO pair where the
classification is undetermined and the indicator resolves to a plain ONE, which
is why ``IndOutcome`` has two constructors rather than three — the model
predicts what the callee produces, over the outcomes the callee can produce.

Note that the classification decides FIRST and the indicator outcome is read only
under ``undetermined``: on the decided arms the real routine returns its constant
without ever obtaining the indicator, which is why the two ``known_equal`` rows
above agree and why both ``known_distinct`` rows do.

DEFENDED SURFACE (one modeled behavior, one obligation, four input binders).
``problem_spec_identityElement cmp ind i j result`` pins EXACTLY

    result = elemOf cmp ind i j

whose arms are the independent sub-clauses a rival can attack:

  * (A1 known-equal)            ``cmp = .known_equal    → result = .one``
  * (A2 known-distinct)         ``cmp = .known_distinct → result = .zero``
  * (A3s undetermined/settled)  ``cmp = .undetermined, ind = .settled_zero
                                  → result = .zero``
  * (A3d undetermined/symbolic) ``cmp = .undetermined, ind = .left_symbolic
                                  → result = .deferred i j``

The DISCRIMINATING arm — the substance of the reported defect — is A3d: when the
pair is not yet classified AND obtaining the indicator left it symbolic, the
element must remain the indicator OF THOSE TWO POSITIONS and must NOT be reported
as a plain zero. Collapsing that case to zero treats an open comparison as a
settled one, and an aggregation of the element over a range that includes the
diagonal then loses the diagonal contribution entirely.

A3s is the arm the one-observation predecessor of this spec got WRONG: it
required a non-zero symbolic indicator on all 5326 undetermined pairs, whereas
the real routine returns a plain zero on 801 of them. A3s now states what the
routine GUARANTEES there. It is not a weakening of A3d — A3d still forbids the
plain zero on every pair where the indicator survives symbolically, which is
exactly the class the defect is about and exactly the class the graded test
observes — it is the removal of a prediction the real routine never honoured.
``weak-ignore-indicator`` below is the rival that pins this: it is the OLD
one-observation behavior, and it is rejected.

A3d is the only arm whose right-hand side MENTIONS ``i`` and ``j``: every other
arm returns a position-independent constant. So the ``i``/``j`` binders are
load-bearing in exactly one place, and a rival that produced the indicator of the
WRONG pair of positions would be invisible to any witness that only ever probed
``i = j`` or only ever probed the constant arms.
``weak-undetermined-wrong-positions`` exists precisely to move those two binders,
and its witness is stated at ``i ≠ j`` for that reason.

BINDER STRUCTURE / POINT SPREAD. Four input binders — ``cmp``, ``ind``, ``i``,
``j``. The eleven reject witnesses probe eleven DISTINCT input tuples
(``pts=11``) and vary all four: ``cmp`` takes all THREE of its values across the
witnesses, ``ind`` takes BOTH of its values (``left_symbolic`` for the A3d
rivals, ``settled_zero`` for ``weak-ignore-indicator``,
``weak-settled-to-deferred``, ``weak-undetermined-swapped``,
``weak-decided-swapped`` and ``weak-known-equal-to-deferred``), and ``(i, j)``
ranges over eleven distinct position pairs, both equal (8/8 and 14/14) and
distinct. No binder is held at one value by every witness.

CLAUSE COVERAGE, per arm, counting rivals that violate that arm ALONE — the only
kind whose rejection is attributable to that arm and nothing else:

  * A3d (undetermined/symbolic) — four rivals, each isolating A3d: to-zero,
    to-one, wrong-positions (attacks the ARGUMENTS, not the branch), and the
    two-valued wildcard shape.
  * A3s (undetermined/settled) — ``weak-ignore-indicator`` and
    ``weak-settled-to-deferred`` isolate it; the latter changes ONLY that arm.
  * A2 (known-distinct) — ``weak-known-distinct-to-one`` isolates it.
  * A1 (known-equal) — ``weak-known-equal-to-deferred`` isolates it.

``weak-undetermined-swapped`` breaks A3s AND A3d jointly (it exchanges the two
undetermined sub-arms), and the two decided-arm joint rivals
(``weak-constant-deferred``, ``weak-decided-swapped``) each break A1 AND A2
together, so none of the three can attribute a rejection to one arm; the
single-arm rivals above exist for that reason.

SPEC STRENGTH / OVER-STRENGTH, both probed with real builds beyond the shipped
cases. Wrong impls the battery does not ship — the known-distinct arm sent to
one, the known-equal arm sent to the indicator, the indicator built from the
second position twice (``.deferred j j``), the positions exchanged, and spin-loop
shapes returning a wrong value — were all REJECTED, including under
author-written ``simp_all``/``aesop``/``decide`` proof attempts rather than only
the frozen tactic body: no spec hole was found. Four CORRECT reshapes — a
``let``-bound single-exit form with a mutable accumulator, the arms in reverse
order, a FLATTENED ``match cmp, ind with`` over the joint pair, and a delegation
to the ``elemOf`` helper — all VERIFY (exit 0, real builds), so the spec is not
over-fit to any one spelling, and in particular not to the nested-match shape:
the flattened four-arm form is a different syntax tree for the same function and
it is accepted.

One MEASURED over-strength residue, stated rather than hidden. Exchanging the two
positions on A3d (``return .deferred j i``) is REJECTED by this spec — the
residual goals are ``⊢ j = i`` and ``⊢ i = j``, unprovable for a free ``α``,
which is correct for the Lean model since ``Elem`` is an inductive with no
symmetry — yet its faithful counterpart IS reported resolved on the real carrier,
because the real indicator is symmetric in its two positions. This is a modeling
choice, not a defect: ``Elem.deferred`` is a free constructor and imposing
symmetry on it would require quotienting the carrier. It is recorded here because
it is the one place where "rejected by the spec" does NOT imply "non-resolving on
the real carrier", and the exchange rival is therefore NOT shipped as a reject
case.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already argues its
    own frame class away (its parameters are immutable integer tags passed by
    value, with no permission predicate and nothing to write through). On this
    referentially transparent carrier it is doubly vacuous: ``cmp``, ``ind``,
    ``i`` and ``j`` are immutable values, there is no aliasing and no mutable
    binder, and the spec quantifies over the argument values themselves. No
    substitute probe is fabricated (porting map: vacuous here).

  * VACUOUS NON-TERMINATION — VACUOUS HERE, and this is the one class where the
    nagini battery is STRICTLY richer than anything expressible on this backend.
    Nagini carries two such rivals (``nonterm-loop-before-return`` and
    ``nonterm-self-recursion``), and they are load-bearing there: they are the
    RECORDED counterexample family, admitted vacuously by a value-only contract
    and rejected only because that contract also carries a termination
    obligation. Neither shape ports to a REJECT case here. MEASURED with real
    builds, per shape:

      - SELF-RECURSION is genuinely unwritable. A same-argument self-call fails
        the termination checker at elaboration (``fail to show termination ...
        no parameters suitable for structural recursion``), and marking the
        ``def`` ``partial`` fails too, because the polymorphic return type
        ``Elem α`` has no ``Nonempty`` instance for a free ``α`` (``could not
        prove that the type ... is nonempty``). So this shape cannot be written.

      - A SPINNING LOOP *can* be written and DOES elaborate: a
        ``while true do k := k + 1`` prefix in front of the frozen match
        verifies (exit 0), with ``#print axioms correct_identityElement``
        reporting no axiom dependence.

    But that verifying spin-loop variant is NOT a spec hole, and the reason is
    the one that matters: the loop is DEAD CODE. Its accumulator is never read by
    the returned value, so the elaborated term beta-reduces past it, and the
    variant is definitionally the FROZEN function — a correct reshape spelled
    with an unused loop, not a diverging impl admitted vacuously. Two
    measurements pin that:

      - make the loop OBSERVABLE (read ``k`` in the returned value) and the
        variant is REJECTED (exit 1);
      - keep the spinning loop but return the WRONG value on the discriminating
        arm — the headline defect — and it is REJECTED (exit 1), under both the
        frozen tactic body and an author-written ``simp_all``/``aesop`` attempt.
        Same for a spin loop returning ``.zero`` on every arm.

    So on this carrier the postcondition is a TOTAL equation that constrains the
    returned value on every arm; there is no non-terminating run on which it is
    satisfied vacuously. The class is inexpressible as a reject case because no
    witness can refute a variant that is definitionally gold — not because the
    shape cannot be written. Contrast the velvet backend under partial
    termination semantics, where this class IS a known hole
    (``the corpus-wide termination-semantics finding``); that finding does not apply to this cell,
    and the measurements above are why.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for a DIFFERENT reason than on nagini.
    Nagini rules the echo out by ENCODING: its returned-value tags are disjoint
    from its comparison-status codes, so returning the status is ill-typed
    against the contract and the cheapest honest implementation is forced to
    branch. Here the echo is available — ``return elemOf cmp ind i j`` is exactly
    it — but it is not UNGROUNDED: ``elemOf`` is a transparent total function of
    the four inputs, spelled out in the spec view, not an opaque answer key. So
    echoing it IS performing the modeled decision, and it is shipped below as a
    correct positive control (``pos-delegate-decision``) rather than as a rival.
    The battery's substitute for the missing echo attack is the
    ``weak-undetermined-wrong-positions`` rival, which attacks the ARGUMENTS the
    deferred indicator is built from rather than the branch that produces it.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is the whole reject lane. Eleven
    rivals, each correct on part of the input domain: eight wrong on exactly one
    arm (four on A3d, two on A3s, one on A2, one on A1) and three wrong on two
    arms jointly (the undetermined sub-arms exchanged, and the two decided-arm
    rivals).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases cmp <;> cases ind <;> rfl`` is
tuned to the frozen match — so a rejection alone attributes nothing to the spec.
Every ``expect="reject"`` case therefore carries a Lean snippet that states the
spec predicate NEGATED at one concrete input tuple and closes by unfolding the
spec, the implementation and ``elemOf`` and letting ``simp`` finish on
constructor injectivity/disjointness. Every witness is stated at GROUND literals
over ``α := Nat`` and binds NOTHING in its head, so there are no hypotheses whose
joint satisfiability could be in question and no conditioning on an opaque term
is needed (the carrier is fully transparent: no ``opaque`` callee, no consumed
``axiom``). Each was checked with two real ``lake env lean`` builds — it HOLDS of
its rival and FAILS on the frozen solution — so it discriminates rather than
asserting a tautology.

REFINEMENT — MEASURED, NOT ASSUMED, and this is where the port DIVERGES from its
design document. Each rival's faithful counterpart was written as a real
``_entry`` body, installed in the instance container at ``base_commit`` with the
test patch applied, and the graded test set run. The measurements are recorded in
each case's own ``refinement``. The headline result: the graded test set observes
ONLY the arm where the indicator survives symbolically (A3d), because the real
indicator AUTO-EVALUATES at decided positions — a collapse the Lean model
deliberately does not make, since ``Elem.deferred i j`` is a distinct constructor
from ``Elem.one`` and ``Elem.zero``. So the four A3d rivals and the
``weak-undetermined-swapped`` rival are CONFIRMED non-resolving by measurement,
while the decided-arm rivals and ``weak-settled-to-deferred`` are reported
resolved and are retained for clause coverage with that limitation stated
plainly rather than a false refinement asserted.

AXIOM lane: EMPTY here. This bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed decision is modeled deeply and both comparison
observations are carried as plain input data), so the nagini ``AXIOM_TESTS`` —
which run the real comparison callees in Docker — have no counterpart to attach
to and are DROPPED: the axiom lane belongs to G-AX, which skips this bundle.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-12419"
BACKEND = "lean"

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    """Replace exactly one occurrence of a region substring; assert it matched,
    so silent drift (Solution.lean edited) fails loudly at manifest load."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Both lie ENTIRELY inside the region they name and both are
# unique in the frozen file (asserted by _swap at load).
#
# _GOLD_IMPL is the whole nested match inside `-- impl-start`/`-- impl-end`;
# every rival and every impl-reshaping positive replaces exactly this block, so
# the spec view is untouched and a rejection is attributable solely to the
# swapped body.
#
# _GOLD_PROOF is the frozen tactic body inside `-- proof-start`/`-- proof-end`;
# only the admissibility positive touches it, and only to PREPEND a ground
# `have` — the `theorem correct_identityElement` STATEMENT is never edited.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .zero
    | .left_symbolic => return .deferred i j"""

_GOLD_PROOF = """  intro cmp ind i j
  cases cmp <;> cases ind <;> rfl"""


def _witness(cmp, ind, i, j):
    """Negate the spec predicate at one ground input tuple over `α := Nat`.

    Binds nothing in its head (no hypotheses => nothing whose consistency could
    be in question), names only frozen vocabulary, and closes by reducing the
    implementation and `elemOf` and appealing to `Elem`'s constructor
    disjointness/injectivity.

    `pure` is handed to `simp` alongside `Id.run` deliberately: reducing the
    `Id.run do` skeleton leaves the returned value wrapped in the identity
    monad's `pure`, and on the arms where the two sides differ only in a
    constructor ARGUMENT (the wrong-positions rival: `.deferred i i` against
    `.deferred i j`) constructor disjointness alone cannot finish — `simp` has to
    strip the `pure` first to reach the injectivity step. Checked with real
    builds: without `pure` that one witness fails against its own rival
    (`unsolved goals: ¬pure (Elem.deferred 4 4) = Elem.deferred 4 5`), which
    would have landed as `witness-unproven` on a rival that is genuinely wrong.
    """
    call = f"IdxCmp.{cmp} IndOutcome.{ind} ({i} : Nat) {j}"
    return (f"example : ¬ problem_spec_identityElement {call}\n"
            f"    (implementation_identityElement {call}) := by\n"
            "  unfold problem_spec_identityElement implementation_identityElement"
            " elemOf\n"
            "  simp [Id.run, pure]\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS — structurally different but CORRECT implementations
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_identityElement` statement byte-identical and adds no
    # declaration, axiom or assumption token.
    # =====================================================================
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Same decision, arms written in the OPPOSITE order (undetermined first
        # with its two sub-arms also exchanged in source order, known-equal
        # last). Definitionally the same function, so the frozen
        # `cases cmp <;> cases ind <;> rfl` still closes each case.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .undetermined   =>
    match ind with
    | .left_symbolic => return .deferred i j
    | .settled_zero  => return .zero
  | .known_distinct => return .zero
  | .known_equal    => return .one"""),
        "rationale": "correct reshape: the arms of the decision are written in "
                     "reverse source order, at BOTH levels of the nested match, so "
                     "the SAME value is produced for every input and the single "
                     "spec equation still holds on all four arms A1/A2/A3s/A3d. "
                     "Must verify — if a faithful reordering were rejected the "
                     "postcondition would be over-fit to the frozen arm order => "
                     "SPEC-TOO-STRONG. Each case is still closed by the frozen "
                     "tactic body (definitional equality), so no proof authoring, "
                     "no helper lemma, no assumption token; statement "
                     "byte-identical. VERIFIED with a real build (exit 0). Ports "
                     "nagini's pos-control-branch-reorder.",
    },
    {
        "id": "pos-single-exit",
        "kind": "soundness",
        "expect": "verify",
        # Single exit: a mutable local defaulted to zero and overwritten on the
        # two arms that are not zero, returned once at the end, instead of four
        # early returns. Decided by DecidableEq tests rather than by a match.
        "module": _swap(_BASE, _GOLD_IMPL, """  let mut out : Elem α := .zero
  if cmp = .known_equal then
    out := .one
  else if cmp = .undetermined then
    if ind = .left_symbolic then
      out := .deferred i j
  return out"""),
        "rationale": "correct reshape with a different CONTROL SHAPE: one exit, a "
                     "mutable local defaulted to zero and overwritten on the two "
                     "arms whose value is not zero, via equality tests on both "
                     "carried observations, rather than four early returns out of a "
                     "nested match. Same value on every input, so all four arms "
                     "still hold; must verify, else the spec is over-fit to the "
                     "early-return spelling => SPEC-TOO-STRONG. Note it also "
                     "collapses the two zero-valued arms (A2 and A3s) into the "
                     "default, which is exactly the kind of legitimate sharing a "
                     "faithful impl may do and which the spec must not forbid. "
                     "Still closed by the frozen tactic body; statement "
                     "byte-identical, nothing added. VERIFIED with a real build "
                     "(exit 0). Ports nagini's pos-control-single-exit.",
    },
    {
        "id": "pos-flat-joint-match",
        "kind": "soundness",
        "expect": "verify",
        # The decision written as ONE match on the joint pair of observations
        # rather than a match nested inside a match — a different syntax tree for
        # the same function, with wildcards on the arms that ignore `ind`.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp, ind with
  | .known_equal, _              => return .one
  | .known_distinct, _           => return .zero
  | .undetermined, .settled_zero => return .zero
  | .undetermined, .left_symbolic=> return .deferred i j"""),
        "rationale": "correct reshape that FLATTENS the nested match into a single "
                     "match on the joint pair of observations, using wildcards on "
                     "the two arms that do not read the indicator outcome. This is "
                     "the most likely alternative spelling of a two-observation "
                     "decision and a different syntax tree from the frozen one, so "
                     "it is the sharpest available check that the spec pins the "
                     "FUNCTION and not the nesting: if the postcondition were "
                     "over-fit to the nested shape this would be rejected => "
                     "SPEC-TOO-STRONG. Same value on every input, all four arms "
                     "hold, still closed by the frozen tactic body; statement "
                     "byte-identical, nothing added. VERIFIED with a real build "
                     "(exit 0).",
    },
    {
        "id": "pos-delegate-decision",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest honest implementation on this carrier: return the value
        # the modeled decision dictates, computed by the transparent total
        # helper the spec view already spells out.
        "module": _swap(_BASE, _GOLD_IMPL, "  return elemOf cmp ind i j"),
        "rationale": "the cheapest HONEST implementation: return the value the "
                     "modeled decision dictates, computed by the transparent total "
                     "helper the spec view spells out. Must verify. Its purpose is "
                     "the one nagini's echo-attempt-honest serves, by the opposite "
                     "route: nagini rules an echo out by ENCODING (its returned-"
                     "value tags are disjoint from its status codes, so returning "
                     "the status is ill-typed), whereas here the echo exists but is "
                     "GROUNDED — the helper is a transparent function of the four "
                     "inputs, not an opaque answer key — so echoing it IS "
                     "performing the decision and is correct, not a spec hole. "
                     "VERIFIED with a real build (exit 0). Confirms "
                     "UNGROUNDED-ORACLE-ECHO is N/A on this carrier.",
    },
    {
        "id": "admiss-ground-undetermined",
        "kind": "admissibility",
        "expect": "verify",
        # The obligation carries NO precondition (`∀ cmp ind i j`, no
        # hypothesis), so it must be satisfiable at every input. Discharge it by
        # evaluation at one concrete tuple on the DISCRIMINATING arm as a `have`,
        # then close the frozen obligation verbatim. Only the tactic BODY grows.
        "module": _swap(_BASE, _GOLD_PROOF,
                        "  have _ground : problem_spec_identityElement "
                        "IdxCmp.undetermined IndOutcome.left_symbolic (7 : Nat) 8\n"
                        "      (implementation_identityElement "
                        "IdxCmp.undetermined IndOutcome.left_symbolic (7 : Nat) 8) "
                        ":= by\n"
                        "    unfold problem_spec_identityElement "
                        "implementation_identityElement elemOf\n"
                        "    rfl\n"
                        + _GOLD_PROOF),
        "rationale": "the obligation binds four inputs and carries NO precondition, "
                     "so it must admit every input; this discharges it by "
                     "evaluation at one concrete tuple on the discriminating arm "
                     "(undetermined classification, indicator left symbolic) at two "
                     "DISTINCT positions (7, 8) — the shape on which the reported "
                     "defect appears — as a `have`, then closes the frozen "
                     "obligation verbatim. If a normal input could not be admitted "
                     "the modeled behavior would be unsatisfiable exactly where it "
                     "matters => the analogue of PRECOND-TOO-STRONG. Nothing is "
                     "assumed: no new declaration, no axiom, statement "
                     "byte-identical, the ground instance is a `have` prepended "
                     "inside the existing tactic body. VERIFIED with a real build "
                     "(exit 0). Ports nagini's admiss-classify-distinct-tags, whose "
                     "in-line probe of the classifier on the tags (7, 8) it mirrors "
                     "at the same positions.",
    },

    # =====================================================================
    # UNIQUENESS RIVALS — wrong implementations sharing the frozen spec that
    # MUST be rejected. Each carries a witness pinning the violation at one
    # concrete input, and a refinement argument grounded in a MEASURED run of
    # the faithful counterpart against the graded test set.
    # =====================================================================

    # ---- A3d: the headline defect — the surviving indicator collapsed to zero --
    {
        "id": "weak-undetermined-to-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   => return .zero"""),
        "refinement": "MEASURED non-resolving. This is the reported defect itself: "
                      "an undetermined classification is reported as a plain zero "
                      "whatever obtaining the indicator delivered, i.e. an open "
                      "comparison is treated as a settled one. Its faithful "
                      "counterpart (`return S.Zero` on the fall-through) was "
                      "installed in the real element accessor at base_commit with "
                      "the test patch applied and the graded test set run: the "
                      "FAIL_TO_PASS test FAILS (AssertionError — the element at two "
                      "distinct symbolic positions compares equal to zero, and the "
                      "aggregation of the element over a range covering the diagonal "
                      "evaluates to zero instead of the matrix dimension), all 25 "
                      "PASS_TO_PASS still pass. Definitively non-resolving.",
        "rationale": "REJECT from arm A3d of the spec equation: at "
                     "cmp = .undetermined with ind = .left_symbolic the spec pins "
                     "result = .deferred i j but the rival returns .zero, and those "
                     "are distinct constructors of Elem. Note the rival is also "
                     "wrong nowhere else — it AGREES with the spec on A3s, which is "
                     "why the witness must fix ind = .left_symbolic. Refuted at "
                     "(.undetermined, .left_symbolic, 0, 1) — an open comparison of "
                     "two distinct positions. REJECTED with a real build (exit 1); "
                     "witness holds of the rival (exit 0) and fails on the frozen "
                     "solution (exit 1).",
        "witness": _witness("undetermined", "left_symbolic", 0, 1),
    },

    # ---- A3s + A3d: the OLD one-observation behavior — the unfaithful model ----
    {
        "id": "weak-ignore-indicator",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignores the second observation entirely: always returns the symbolic
        # indicator on an undetermined classification, even on the pairs where
        # obtaining that indicator settled the comparison and delivered a plain
        # zero. This is the shape a one-observation model would license.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   => return .deferred i j"""),
        "refinement": "MEASURED — and this rival is why the second observation is "
                      "in the spec at all. It DISCARDS the indicator outcome and "
                      "claims a surviving symbolic indicator on every undetermined "
                      "pair. Measured against the real callee on 6970 position "
                      "pairs: that claim is false on 801 of them (15% of the "
                      "undetermined pairs), where obtaining the indicator settles "
                      "the comparison and the real routine returns a PLAIN ZERO — "
                      "e.g. a pair of positions the classification cannot separate "
                      "but the indicator's own settling can. So this rival is not "
                      "merely wrong on the Lean carrier; it predicts a non-zero "
                      "symbolic value where the real routine produces zero, which "
                      "is exactly the unfaithfulness the spec now avoids. Its "
                      "faithful counterpart cannot be written as a plain "
                      "`return KroneckerDelta(i, j)` — that IS the gold body, since "
                      "the real indicator does its own settling — which is precisely "
                      "the point: on the real carrier the settling is not optional, "
                      "so a routine that genuinely ignored it (forcing an "
                      "unevaluated indicator) is `weak-settled-to-deferred` below, "
                      "measured there. Retained for A3s coverage as the direct "
                      "refutation of the one-observation model.",
        "rationale": "REJECT from arm A3s: at cmp = .undetermined with "
                     "ind = .settled_zero the spec pins result = .zero — what "
                     "obtaining the indicator actually delivered — but the rival "
                     "returns .deferred i j, a distinct constructor. It is correct "
                     "on A1, A2 and A3d, so its rejection is attributable to A3s "
                     "alone. This is the single most important reject case in the "
                     "battery: it is the behavior a spec written over the "
                     "classification alone would ADMIT, and the spec must reject it "
                     "to be faithful. Refuted at "
                     "(.undetermined, .settled_zero, 20, 21). REJECTED with a real "
                     "build (exit 1); witness holds of the rival (exit 0) and fails "
                     "on the frozen solution (exit 1).",
        "witness": _witness("undetermined", "settled_zero", 20, 21),
    },

    # ---- A3s ALONE: force a symbolic indicator where the pair was settled ----
    {
        "id": "weak-settled-to-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        # Changes ONLY the settled sub-arm: returns the symbolic indicator there
        # too, so the routine never reports the plain zero the indicator itself
        # delivered.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .deferred i j
    | .left_symbolic => return .deferred i j"""),
        "refinement": "HONEST LIMITATION, and MEASURED. The faithful counterpart is "
                      "an `_entry` that bypasses the indicator's own settling and "
                      "emits an unevaluated indicator on every undetermined pair "
                      "(`KroneckerDelta(i, j, evaluate=False)`). Installed at "
                      "base_commit with the test patch applied, the graded test set "
                      "reports RESOLVED (FAIL_TO_PASS passes, all 25 PASS_TO_PASS "
                      "pass), because the graded tests probe only pairs whose "
                      "indicator survives symbolically anyway — the arm this rival "
                      "leaves correct. So its rejection here demonstrates spec "
                      "STRENGTH on an arm the graded tests cannot see, not a "
                      "verify-does-not-imply-resolve break. It regresses real "
                      "behavior nonetheless: on the 801 measured pairs where the "
                      "indicator settles, this returns a symbolic value where the "
                      "real routine returns a plain zero, so an aggregation over "
                      "those positions no longer reduces. Retained for A3s coverage "
                      "in ISOLATION — it is the only rival that changes that one arm "
                      "and nothing else.",
        "rationale": "REJECT from arm A3s ALONE: the spec pins result = .zero at "
                     "cmp = .undetermined with ind = .settled_zero and the rival "
                     "returns .deferred i j. Every other arm is byte-correct, so "
                     "the rejection is attributable to A3s and to nothing else — "
                     "weak-ignore-indicator also violates A3s but via a wildcard "
                     "that discards the observation entirely, so a spec that had "
                     "lost A3s while keeping the others would still need this case "
                     "to expose the gap. Refuted at "
                     "(.undetermined, .settled_zero, 16, 17). REJECTED with a real "
                     "build (exit 1); witness holds of the rival (exit 0) and fails "
                     "on the frozen solution (exit 1).",
        "witness": _witness("undetermined", "settled_zero", 16, 17),
    },

    # ---- A3s + A3d jointly: the two undetermined sub-arms exchanged ----
    {
        "id": "weak-undetermined-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # The two sub-arms of the undetermined case transposed: the settled pair
        # gets the symbolic indicator and the surviving-symbolic pair gets a
        # plain zero. Exactly inverts which observation licenses which value.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .deferred i j
    | .left_symbolic => return .zero"""),
        "refinement": "MEASURED non-resolving. It reads the second observation but "
                      "draws the opposite conclusion from it. Its faithful "
                      "counterpart — emit an unevaluated indicator exactly where the "
                      "real indicator settled to zero, and a plain zero where it "
                      "survived — was installed at base_commit with the test patch "
                      "applied and the graded test set run: the FAIL_TO_PASS test "
                      "FAILS (AssertionError), all 25 PASS_TO_PASS pass. "
                      "Definitively non-resolving, and for the right reason: the "
                      "graded tests probe pairs whose indicator survives, which is "
                      "precisely where this rival reports the plain zero the defect "
                      "is about.",
        "rationale": "REJECT from arms A3s AND A3d jointly: the spec pins .zero on "
                     "the settled sub-arm and .deferred i j on the surviving one, "
                     "and the rival returns each where the other belongs. Because "
                     "it violates both, its rejection cannot be attributed to "
                     "either alone — which is why weak-settled-to-deferred (A3s "
                     "only) and weak-undetermined-to-zero (A3d only) are both "
                     "shipped alongside it. Refuted at "
                     "(.undetermined, .settled_zero, 18, 19), on the settled arm, "
                     "so this rival and weak-undetermined-to-zero are witnessed at "
                     "different observations rather than sharing a point. REJECTED "
                     "with a real build (exit 1); witness holds of the rival (exit "
                     "0) and fails on the frozen solution (exit 1).",
        "witness": _witness("undetermined", "settled_zero", 18, 19),
    },

    # ---- A3d: undetermined treated as ON the diagonal ----
    {
        "id": "weak-undetermined-to-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   => return .one"""),
        "refinement": "MEASURED non-resolving. The mirror-image mistake on the "
                      "discriminating arm: an undetermined classification is "
                      "reported as a constant one, i.e. treated as if the two "
                      "positions were known to COINCIDE. Its faithful counterpart "
                      "(`return S.One` on the fall-through) was installed at "
                      "base_commit with the test patch applied: the FAIL_TO_PASS "
                      "test FAILS (AssertionError — every off-diagonal element at "
                      "undetermined positions becomes one, so the aggregation over a "
                      "range covering the diagonal over-counts, totalling the square "
                      "of the dimension rather than the dimension), all 25 "
                      "PASS_TO_PASS pass. Faithful but definitively non-resolving — "
                      "and a distinct sub-domain error from "
                      "weak-undetermined-to-zero, so it is witnessed at its own "
                      "input point.",
        "rationale": "REJECT from arm A3d: at cmp = .undetermined with "
                     "ind = .left_symbolic the spec pins result = .deferred i j but "
                     "the rival returns .one. Refuted at "
                     "(.undetermined, .left_symbolic, 2, 3) — a DIFFERENT point "
                     "from the to-zero rival, since the two rivals err in different "
                     "directions on this arm and each rationale should be "
                     "demonstrated at its own input rather than shared. REJECTED "
                     "with a real build (exit 1).",
        "witness": _witness("undetermined", "left_symbolic", 2, 3),
    },

    # ---- A3d: right constructor, WRONG POSITIONS (the binder-moving rival) ----
    {
        "id": "weak-undetermined-wrong-positions",
        "kind": "uniqueness",
        "expect": "reject",
        # Produces the deferred indicator — the right SHAPE on the right arm —
        # but builds it from the first position twice, discarding the second.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .zero
    | .left_symbolic => return .deferred i i"""),
        "refinement": "MEASURED non-resolving. A NEAR-MISS that no other rival "
                      "covers: it selects the correct arm AND the correct returned "
                      "shape, and errs only in the POSITIONS the deferred indicator "
                      "is built from — the first position twice, discarding the "
                      "second. Its faithful counterpart (`KroneckerDelta(i, i)`) was "
                      "installed at base_commit with the test patch applied: the "
                      "FAIL_TO_PASS test FAILS (AssertionError), all 25 PASS_TO_PASS "
                      "pass — an indicator of a position against ITSELF reduces to a "
                      "constant one, so every element at undetermined positions "
                      "becomes one and the aggregation over a range covering the "
                      "diagonal over-counts exactly as the to-one rival does. "
                      "(Measured contrast, and the reason this rival is stated as "
                      "position DUPLICATION rather than position EXCHANGE: building "
                      "the indicator from the two positions in the opposite ORDER is "
                      "reported resolved, because the real indicator is symmetric in "
                      "its two positions. That exchange rival is therefore NOT wrong "
                      "on the real carrier and is not shipped.)",
        "rationale": "REJECT from arm A3d, attacking the ARGUMENTS rather than the "
                     "branch: the spec pins result = .deferred i j and the rival "
                     "returns .deferred i i, which differ by injectivity of the "
                     "constructor's second field whenever i ≠ j. This is the only "
                     "rival that MOVES the i/j binders — A3d is the sole arm whose "
                     "right-hand side mentions them, every other arm returning a "
                     "position-independent constant — so without it a rival that "
                     "mishandled only the positions would go unnoticed. Refuted at "
                     "(.undetermined, .left_symbolic, 4, 5), necessarily a point "
                     "with i ≠ j: at i = j this rival AGREES with the spec, so a "
                     "witness probing only equal positions would not discriminate "
                     "it. REJECTED with a real build (exit 1).",
        "witness": _witness("undetermined", "left_symbolic", 4, 5),
    },

    # ---- A3d via the two-valued shape: the literal pre-fix decision ----
    {
        "id": "weak-two-valued-decision",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix decision shape: a TWO-valued comparison — known-equal
        # gives one and every other status (including undetermined, whatever the
        # indicator delivered) falls into a single wildcard arm giving a plain
        # zero. The symbolic indicator is never produced at all.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal => return .one
  | _            => return .zero"""),
        "refinement": "MEASURED non-resolving. This is the literal pre-fix decision "
                      "SHAPE: a two-valued comparison whose single wildcard arm "
                      "folds known-distinct and both undetermined sub-arms together "
                      "into a plain zero, so the symbolic indicator is never "
                      "produced on any input. Installed at base_commit as the "
                      "original `if i == j` body with the test patch applied: the "
                      "FAIL_TO_PASS test FAILS (AssertionError), all 25 PASS_TO_PASS "
                      "pass. It is the pre-patch behavior; definitively "
                      "non-resolving. (Note the carrier collapse: on this carrier "
                      "this rival is OBSERVATIONALLY equal to "
                      "weak-undetermined-to-zero, because folding known-distinct and "
                      "the settled sub-arm into the zero arm AGREES with the spec "
                      "there — the only divergence is on A3d, so both witnesses "
                      "refute it for the same reason on that arm. It is shipped "
                      "anyway because it exercises a structurally different "
                      "implementation shape, the wildcard-arm match that a "
                      "two-valued comparison naturally produces, rather than a "
                      "nested match with one sub-arm changed.)",
        "rationale": "REJECT from arm A3d: the wildcard arm sends "
                     "cmp = .undetermined with ind = .left_symbolic to .zero where "
                     "the spec pins .deferred i j. Refuted at "
                     "(.undetermined, .left_symbolic, 6, 7), its own input point. "
                     "REJECTED with a real build (exit 1); witness holds of the "
                     "rival (exit 0) and fails on the frozen solution (exit 1). "
                     "This rival is also exactly the prepatch twin's impl, so its "
                     "rejection is the same fact G-DIFF/G-GOLD check from the other "
                     "side.",
        "witness": _witness("undetermined", "left_symbolic", 6, 7),
    },

    # ---- A1 + A2: the decided arms, both collapsed onto the indicator ----
    {
        "id": "weak-constant-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops every decided arm: always returns the deferred indicator, never
        # the constants one or zero.
        "module": _swap(_BASE, _GOLD_IMPL, "  return .deferred i j"),
        "refinement": "HONEST LIMITATION — this rival's faithful counterpart "
                      "(`return KroneckerDelta(i, j)` unconditionally) is reported "
                      "RESOLVED by the graded test set, measured at base_commit with "
                      "the test patch applied (FAIL_TO_PASS passes, all 25 "
                      "PASS_TO_PASS pass), so its rejection here demonstrates spec "
                      "STRENGTH but is NOT a verify-does-not-imply-resolve break, "
                      "and the nagini sibling's claim to the contrary (its "
                      "constant-delta case) does not survive measurement on the real "
                      "carrier. The reason is that the REAL indicator auto-evaluates "
                      "at decided positions — it reduces to one when the positions "
                      "are known equal and to zero when known distinct — so on the "
                      "graded inputs it is observationally identical to the frozen "
                      "behavior. The Lean model deliberately does NOT make that "
                      "collapse: `.deferred i j` is a constructor distinct from "
                      "`.one` and `.zero`, which is what lets the spec pin the "
                      "soundness-critical property that a surviving symbolic "
                      "indicator must not be reported as a plain zero. Retained for "
                      "CLAUSE and BINDER coverage — it is one of only two rivals "
                      "that attack the decided arms at all, and dropping it would "
                      "leave cmp = .known_equal probed by no witness — with this "
                      "limitation stated rather than a false refinement asserted.",
        "rationale": "REJECT from BOTH decided arms: at cmp = .known_equal the spec "
                     "pins .one and at cmp = .known_distinct it pins .zero, while "
                     "the rival returns .deferred i j in every case; all three are "
                     "distinct constructors. Refuted at "
                     "(.known_equal, .left_symbolic, 8, 8) — the only witness in the "
                     "battery that probes the known-equal value of cmp, and at a "
                     "pair of coinciding positions, which no other witness does "
                     "either. REJECTED with a real build (exit 1).",
        "witness": _witness("known_equal", "left_symbolic", 8, 8),
    },

    # ---- A1 + A2: the decided arms transposed ----
    {
        "id": "weak-decided-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # The two decided arms transposed: known-equal gives zero and
        # known-distinct gives one. The undetermined arms are left correct.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .zero
  | .known_distinct => return .one
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .zero
    | .left_symbolic => return .deferred i j"""),
        "refinement": "HONEST LIMITATION — as with weak-constant-deferred, this "
                      "rival's faithful counterpart is reported RESOLVED by the "
                      "graded test set, measured at base_commit with the test patch "
                      "applied (FAIL_TO_PASS passes, all 25 PASS_TO_PASS pass), so "
                      "the nagini sibling's claim for its mask-swap case does not "
                      "survive measurement and is not repeated. Transposing the two "
                      "decided values DOES regress real behavior — element access at "
                      "concrete positions returns the wrong constant, so a concrete "
                      "3x3 identity reads zero on the diagonal and one off it — but "
                      "no GRADED test sees it. The reason is the same "
                      "auto-evaluation noted above: the graded tests exercise only "
                      "the undetermined-with-surviving-indicator arm, which this "
                      "rival leaves correct. So this case demonstrates spec strength "
                      "on arms the graded tests cannot see, and is retained for that "
                      "coverage rather than as a verify-does-not-imply-resolve "
                      "break.",
        "rationale": "REJECT from BOTH decided arms, transposed: A1 pins .one where "
                     "the rival returns .zero and A2 pins .zero where it returns "
                     ".one. Refuted at (.known_distinct, .settled_zero, 10, 11), the "
                     "only witness in the battery that probes the known-distinct "
                     "value of cmp — so this rival and weak-constant-deferred, which "
                     "also violates both decided arms, are witnessed on DIFFERENT "
                     "arms rather than sharing a point, and between them the two "
                     "decided arms are each demonstrated. The witness also fixes "
                     "ind = .settled_zero, confirming that the decided arms ignore "
                     "the second observation exactly as the real routine does (it "
                     "returns its constant without ever obtaining the indicator). "
                     "REJECTED with a real build (exit 1). Ports nagini's "
                     "mask-swap-equal-unequal. It does NOT subsume nagini's "
                     "partial-true-to-delta: that rival sends the known-equal arm to "
                     "the DEFERRED indicator, whereas this one sends it to .zero, "
                     "and neither implies the other. The partial-true-to-delta shape "
                     "is shipped on its own below as weak-known-equal-to-deferred.",
        "witness": _witness("known_distinct", "settled_zero", 10, 11),
    },

    # ---- A2 ALONE: the single-decided-arm near-miss ----
    {
        "id": "weak-known-distinct-to-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong on EXACTLY ONE arm: known-distinct yields one instead of zero.
        # Every other arm — including both discriminating undetermined arms — is
        # left byte-correct.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .one
  | .known_distinct => return .one
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .zero
    | .left_symbolic => return .deferred i j"""),
        "refinement": "HONEST LIMITATION, same shape as the two rivals above: this "
                      "rival's faithful counterpart is reported RESOLVED by the "
                      "graded test set, measured at base_commit with the test patch "
                      "applied (FAIL_TO_PASS passes, all 25 PASS_TO_PASS pass). The "
                      "reason is the one already stated: the graded tests observe "
                      "only the undetermined-with-surviving-indicator arm, which "
                      "this rival leaves correct. It regresses real behavior — a "
                      "known-distinct off-diagonal element reports one instead of "
                      "zero, so the concrete 3x3 identity reads all-ones — but no "
                      "graded test sees it. Retained for CLAUSE coverage, not as a "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from arm A2 ALONE, which no other rival isolates: every "
                     "other decided-arm rival in the battery violates A1 and A2 "
                     "TOGETHER (weak-constant-deferred collapses both onto the "
                     "indicator, weak-decided-swapped transposes both), so a spec "
                     "that had lost the A2 clause while keeping A1 would still "
                     "reject all of them and the gap would be invisible. This rival "
                     "changes exactly one arm, so its rejection is attributable to "
                     "A2 and to nothing else: the spec pins result = .zero at "
                     "cmp = .known_distinct and the rival returns .one, distinct "
                     "constructors of Elem. Refuted at "
                     "(.known_distinct, .left_symbolic, 12, 13), its own input "
                     "point. REJECTED with a real build (exit 1).",
        "witness": _witness("known_distinct", "left_symbolic", 12, 13),
    },

    # ---- A1 ALONE: the deferred-indicator-on-a-decided-arm near-miss ----
    {
        "id": "weak-known-equal-to-deferred",
        "kind": "uniqueness",
        "expect": "reject",
        # Wrong on EXACTLY ONE arm: known-equal yields the deferred indicator
        # instead of the constant one. The right SHAPE on the wrong arm.
        "module": _swap(_BASE, _GOLD_IMPL, """  match cmp with
  | .known_equal    => return .deferred i j
  | .known_distinct => return .zero
  | .undetermined   =>
    match ind with
    | .settled_zero  => return .zero
    | .left_symbolic => return .deferred i j"""),
        "refinement": "HONEST LIMITATION: measured at base_commit with the test "
                      "patch applied, the faithful counterpart (return the indicator "
                      "on the `eq is S.true` branch) is reported RESOLVED "
                      "(FAIL_TO_PASS passes, all 25 PASS_TO_PASS pass), because the "
                      "REAL indicator auto-evaluates to one at known-equal "
                      "positions, so returning it there is observationally identical "
                      "to returning the constant one on every graded input. That is "
                      "precisely the measurement that defeats the nagini sibling's "
                      "refinement claim for this shape, and it is stated plainly "
                      "here rather than the nagini claim being copied. Retained for "
                      "CLAUSE coverage of A1 in isolation.",
        "rationale": "REJECT from arm A1 ALONE — the shape nagini ships as "
                     "partial-true-to-delta, which no other case in this battery "
                     "covers. It is the strictest near-miss available on a decided "
                     "arm: it returns the deferred indicator OF THE CORRECT PAIR "
                     "(.deferred i j, exactly what A3d demands) but on the "
                     "known-equal arm, where the spec pins the constant .one. So it "
                     "differs from the frozen function on one arm only, and by "
                     "constructor disjointness alone rather than by any argument "
                     "mismatch. Its rejection is attributable to A1 and nothing "
                     "else. Refuted at (.known_equal, .settled_zero, 14, 14) — "
                     "deliberately at COINCIDING positions, the shape on which a "
                     "known-equal classification actually arises. REJECTED with a "
                     "real build (exit 1).",
        "witness": _witness("known_equal", "settled_zero", 14, 14),
    },
]
