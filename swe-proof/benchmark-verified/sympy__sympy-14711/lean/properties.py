"""properties.py — G-PBT falsification battery for sympy__sympy-14711 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant built by region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region — and, for the positives that
legitimately re-prove, inside ``-- proof-start`` / ``-- proof-end`` — differs
from the frozen file, so ``markers.same_spec`` holds by construction and the
single ``theorem correct_vectorAdd`` STATEMENT stays byte-identical.
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``). That sibling models the operation over a heap
carrier: a left operand held at a fractional access permission, an operand
object carrying two mutable discriminator fields, and an opaque normalising
constructor applied to the concatenation of the two carriers. Nine of its cases
are expressed against that machinery. This Lean bundle models the SAME single
purely-functional core over a pure carrier: a component list ``selfArgs : List
Int`` plus an operand classified by shape (``AddOperand``), with the observable
result as ``Except Unit (List Int)``. The ADVERSARIAL ARGUMENT of each sibling
case carries over where the carrier keeps the distinction it attacked; where the
carrier collapses it, the case is dropped and recorded in ``assessment``.

DEFENDED SURFACE (one modeled behavior; three independent top-level clauses).
``problem_spec_vectorAdd selfArgs other result`` is a total case split on the
operand's shape, pinning an EQUALITY on each arm:

  * (C-vec)  ``.vector otherArgs`` -> ``result = Except.ok (selfArgs ++
    otherArgs)`` — the operand's components contribute, appended after the
    receiver's own, in that order;
  * (C-zero) ``.scalarZero`` -> ``result = Except.ok selfArgs`` — the additive
    identity leaves the receiver's component list EXACTLY unchanged, and in
    particular SUCCEEDS rather than being rejected;
  * (C-err)  ``.nonVector`` -> ``result = Except.error ()`` — anything else is
    rejected.

The BEHAVIOURAL DISCRIMINATOR (what the fix is about) is C-zero: the additive
identity must be accepted, and accepted as a no-op. The pre-fix behavior sent
the identity down the rejecting path; the ``weak-identity-rejected`` rival below
IS that behavior, and it is the case that maps one-to-one onto the sibling's
``prepatch-no-shortcircuit``.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``selfArgs`` (the
receiver's component list) and ``other`` (the operand). Both are load-bearing on
every arm and both are varied across the reject witnesses: ``selfArgs`` ranges
over one- and two-element lists with distinct contents, and ``other`` ranges over
all THREE constructors, with two distinct ``.vector`` payloads (one of length 1,
one of length 2). The five reject witnesses probe five DISTINCT input pairs
(``pts=5``); see the point-spread block at the bottom.

ADVERSARIAL READ of the sibling's case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Two sibling cases are rejections by
    the fractional-permission system: one writes the read-only left operand's
    component list in place, one overwrites the operand's discriminator field.
    Neither exists here. Lean is referentially transparent: ``selfArgs`` is an
    immutable value, ``other`` is an immutable inductive value, there is no
    aliasing, no mutable field, and no permission to be insufficient. No
    substitute probe is fabricated (porting map: vacuous here). The frame
    OBLIGATION those cases defended — that the unchanged part of the input is
    pinned — is discharged structurally instead, by C-zero's ``result =
    Except.ok selfArgs`` naming the input list itself; the
    ``weak-identity-renormalised`` rival attacks exactly that pinning.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE, not a vacuous class. The
    sibling carries no ``diverge-*`` case, and the class was originally recorded
    here as vacuous on the ground that a non-terminating implementation "cannot
    be written". That is only half true and the correction matters, so both
    halves were MEASURED:

      - A plain self-recursive ``def`` with no decreasing measure is indeed
        rejected, but for a TERMINATION reason, not a spec reason: the build
        fails with ``fail to show termination for implementation_vectorAdd ...
        failed to infer structural recursion``. That rejection attributes
        nothing to ``problem_spec_vectorAdd``, so it is not a shippable reject
        case (a witness for it would be refuting the elaborator, not the spec).

      - A ``partial def`` DOES elaborate, so the diverging implementation is
        expressible on this carrier after all. It is not shippable either, but
        for the opposite reason: ``partial def`` makes the constant opaque to
        reduction, so no witness can refute it. Measured — the conditioned
        witness ``example (h : implementation_vectorAdd [1] .scalarZero ≠
        Except.ok [1]) : ¬ problem_spec_vectorAdd [1] .scalarZero ...``
        elaborates against the ``partial`` rival (exit 0) AND against the frozen
        solution (exit 0), because ``h`` is satisfiable-looking on both sides
        once the constant is opaque. Failing on gold is the half that makes a
        witness a discriminator, so this witness is not one, and no witness
        stated over an opaque constant can be.

    Disposition: KNOWN HOLE. A ``partial`` rival cannot be refuted on this
    carrier, so the class is not shipped; recording it as "vacuous" would have
    claimed the battery is complete here when in fact the spec is what is
    incomplete. (Distinct from, though adjacent to, the velvet
    ``partial``-semantics hole of ``the corpus-wide termination-semantics finding``: this bundle's
    frozen solution sets no ``loom.semantics.termination`` option at all — it is
    a plain total Lean ``def`` — so the hole is reached only by a rival that
    opts INTO ``partial``, which the frozen artifact does not.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The sibling's three ``drop-other`` cases
    exist because its postcondition applies an OPAQUE normalising function to the
    concatenation of both carriers, so "echo the function at a smaller argument"
    is a live evasion there. This carrier has no opaque function: each arm pins a
    concrete equality on the input lists themselves, so there is nothing to echo
    and producing the right list IS doing the work. The VALUE-level content of
    those cases does port, as the two C-vec rivals below (drop the operand's
    contribution; return the empty list) — but they are refuted by a concrete
    computed disagreement, not by opacity.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the battery lives. Five
    rivals, each correct on part of the domain and diverging on one arm.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script ends in ``rfl`` on three arms and
a targeted ``simp only`` on a fourth, all tuned to the frozen syntactic form — so
a rejection alone attributes NOTHING to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate directly at one
CONCRETE input pair and reduces both sides. Each witness binds NOTHING in its
head (both inputs are ground literals: a ``List Int`` literal and an
``AddOperand`` constructor), so there are no hypotheses whose joint
satisfiability could be in question, and no ``opaque`` term to condition on.
Each was checked with two real ``lake env lean`` builds and SEEN to discriminate:
it elaborates against its rival (exit 0) and fails on the frozen solution
(exit 1, ``unsolved goals ⊢ False`` — the frozen implementation satisfies the
predicate at that point, so the negation is unprovable).

REFINEMENT, and a correction to the sibling's inventory. Each reject case's
``refinement`` argues that its faithful real counterpart would NOT resolve the
recorded FAIL_TO_PASS. Those arguments were not taken on trust: every rival's
faithful counterpart was EXECUTED against the recorded FAIL_TO_PASS and
PASS_TO_PASS at ``base_commit`` with the test patch applied, and all five shipped
rivals were confirmed to fail. Two sibling cases were DROPPED because that same
execution showed their faithful counterparts RESOLVE — the recorded tests do not
observe the behavior they attack. See ``assessment``; shipping them would have
been a false ``refinement``.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the operand classification and the resulting component list are
modeled deeply and structurally), so the sibling's three ``AXIOM_TESTS`` — two
soundness probes and a caller-domain containment probe for its two axiomatized
callees — have no referent. They are dropped; the axiom lane is G-AX's job and
this bundle's G-AX is a recorded skip.

INDEPENDENT AUDIT (post-port). The battery was re-attacked from scratch with real
builds. Two defects were found and fixed, and the surrounding probes are recorded
here so the next reader does not have to re-measure them.

  * FIXED — a positive that tested nothing. The former ``pos-pure-if-else``
    reshaped the monadic skeleton into a pure ``if``/``else``, but that variant is
    definitionally EQUAL to the frozen implementation: ``∀ s o,
    implementation_vectorAdd s o = <variant> s o`` closes by ``rfl``, and the
    frozen tactic body closes the variant verbatim. It verified honestly while
    probing nothing. Replaced by ``pos-fold-append``, which is measurably NOT
    definitionally equal and which the frozen tactic body does NOT close.

  * FIXED — a false vacuity claim. The divergence class was recorded as VACUOUS;
    a ``partial def`` rival is in fact expressible and elaborates. Re-recorded as
    a KNOWN HOLE with the measurement that no witness discriminates over it.

  * SPEC-TOO-WEAK probes (attack D), four NEW wrong implementations the battery
    does not contain. All four were REJECTED by the frozen spec, so no spec hole
    was found on this carrier:
      - operand's components prepended instead of appended (``otherArgs ++
        selfArgs``) — rejected; witness at ([1], .vector [2]) discriminates.
      - an invalid operand yielding the empty list instead of a type error —
        rejected; witness at ([1], .nonVector) discriminates.
      - an operand carrying no components rejected as a type error, i.e. an
        attack on the ``.vector []``/identity OVERLAP that no shipped witness
        reaches — rejected; witness at ([1], .vector []) discriminates. This is
        the least-probed point in the battery and it is defended.
      - the combined list de-duplicated (``.eraseDups``) — rejected. Note its
        witness needs a ``decide`` step after ``simp``: at ([1], .vector [1]) the
        residual goal is ``¬[1, 1].eraseDups = [1, 1]``, which ``simp`` alone
        leaves open. Recorded because it is the one place on this carrier where
        the standard witness scaffold is not enough.

  * SPEC-TOO-STRONG probes (attack E), three NEW correct reshapes beyond the two
    shipped positives — an ``Option``-funnelled classification, a guard written
    as a decidable equality disjunction, and the fold (now shipped). All three
    VERIFY, so no soundness hole was found: the spec admits faithful reshapes of
    the branching, of the guard's spelling, and of the construction.

  * The admissibility positive's ``have``s were confirmed load-bearing rather
    than decorative: the same ground ``have`` on the identity arm FAILS against
    the pre-fix implementation (``Tactic `rfl` failed``), so it is discharging the
    modeled behavior at the discriminating input and not restating a triviality.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14711"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---- region anchors (each verified unique inside Solution.lean at load) ----
# The whole implementation body: the guard that recognises the additive
# identity, then the dispatch on the operand's shape. Lies entirely inside
# `-- impl-start` / `-- impl-end`.
_I_BODY = """  Id.run do
    if isAdditiveZero other then
      return Except.ok selfArgs
    match other with
    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)
    | _                 => return Except.error ()"""

# The identity-branch guard alone (two lines), for the rival that removes it.
_I_GUARD = """    if isAdditiveZero other then
      return Except.ok selfArgs
"""

# The identity branch's returned value, for the rivals that change WHAT the
# identity branch yields while leaving the dispatch alone.
_I_ZERO_RESULT = "      return Except.ok selfArgs"

# The operand-contributes arm, for the rivals that change the combined list.
_I_VEC_ARM = "    | .vector otherArgs => return Except.ok (selfArgs ++ otherArgs)"

# The frozen proof's whole tactic body, for the positives that must re-prove.
_P_BODY = """  intro selfArgs other
  unfold problem_spec_vectorAdd implementation_vectorAdd
  cases other with
  | vector otherArgs =>
    cases otherArgs with
    | nil =>
      simp only [isAdditiveZero, Id.run, if_true, List.append_nil, pure]
    | cons a as => rfl
  | scalarZero => rfl
  | nonVector => rfl"""

# The frozen proof's intro line, so the admissibility positive can prepend
# ground `have`s without touching the theorem STATEMENT or the spec view.
_P_INTRO = "  intro selfArgs other\n"


# ---------------------------------------------------------------------------
# witness scaffold. State the spec predicate directly at a ground input pair,
# reduce the monadic implementation, and let `simp` close the negation. Both
# inputs are literals, so the head binds nothing and there is no hypothesis
# whose consistency could be questioned.
# ---------------------------------------------------------------------------
def _w(self_args, other):
    return (
        f"example : ¬ problem_spec_vectorAdd {self_args} {other}\n"
        f"    (implementation_vectorAdd {self_args} {other}) := by\n"
        "  unfold problem_spec_vectorAdd implementation_vectorAdd\n"
        "  simp [Id.run, isAdditiveZero, Id.instMonad]\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_vectorAdd` statement byte-identical and re-proves inside
    # the proof region only. Both were checked with a real build.
    # =====================================================================
    {
        "id": "pos-total-dispatch",
        "kind": "soundness",
        "expect": "verify",
        # RESHAPE: drop the leading identity guard and instead dispatch on all
        # three operand shapes in ONE total match, handling the identity in its
        # own arm. Same result on every input — the guard's extra reach (an
        # operand carrying no components) lands on the arm that appends an empty
        # list, which yields the same list — but a different control-flow shape:
        # one match, no `if`, no early return before the match. The proof
        # collapses to three `rfl`s because no arm needs the empty-list case
        # split the frozen form's guard forces.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             "  Id.run do\n"
             "    match other with\n"
             "    | .scalarZero       => return Except.ok selfArgs\n"
             "    | .vector otherArgs => return Except.ok "
             "(selfArgs ++ otherArgs)\n"
             "    | .nonVector        => return Except.error ()"),
            (_P_BODY,
             "  intro selfArgs other\n"
             "  unfold problem_spec_vectorAdd implementation_vectorAdd\n"
             "  cases other with\n"
             "  | vector otherArgs => rfl\n"
             "  | scalarZero => rfl\n"
             "  | nonVector => rfl"),
        ),
        "rationale": "correct reshape: one total three-way dispatch on the "
                     "operand's shape instead of a leading identity guard "
                     "followed by a two-way match. It computes the same result "
                     "on every input of every arm — on an operand carrying no "
                     "components the frozen guard's identity answer and this "
                     "form's append answer are the same list — so C-vec, C-zero "
                     "and C-err all still hold; if this were rejected the spec "
                     "would be SPEC-TOO-STRONG, pinning the frozen CONTROL FLOW "
                     "rather than the modeled behavior. Re-proved honestly in "
                     "the proof region (three `rfl`s; the frozen form's "
                     "empty-payload `simp only` is no longer needed because no "
                     "arm overlaps). Statement byte-identical, no new "
                     "axiom/lemma/helper. Ports the sibling's pos-two-loops "
                     "positive, whose reshape was of a construction LOOP this "
                     "carrier does not have; the analogous "
                     "structurally-different-but-correct move here is the "
                     "dispatch shape. Verified: real build, exit 0.",
    },
    {
        "id": "pos-fold-append",
        "kind": "soundness",
        "expect": "verify",
        # RESHAPE: build the combined list by CONSUMING the operand's components
        # one at a time — a left fold that appends each singleton onto the
        # receiver — instead of a single `++`. This is the closest analogue on
        # this carrier of the sibling's pos-two-loops reshape (which reshapes an
        # index-loop construction of the combined carrier), and it is a REAL
        # reshape rather than a re-spelling: `List.foldl (fun acc x => acc ++
        # [x]) selfArgs otherArgs` is NOT definitionally equal to `selfArgs ++
        # otherArgs` (measured: `rfl` between the two implementations fails,
        # "not definitionally equal"), so C-vec has to be RE-ESTABLISHED by an
        # induction on the operand's component list rather than fall out of
        # reduction. The frozen tactic body does NOT close this variant
        # (measured: `unsolved goals ⊢ Except.ok (List.foldl ...) = Except.ok
        # selfArgs` on the empty arm and `rfl` failed on the cons arm), which is
        # what makes it a genuine soundness probe: if the spec rejected it, the
        # spec would be pinning HOW the combined list is built rather than what
        # it is.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             "  match other with\n"
             "  | .vector otherArgs => Except.ok "
             "(otherArgs.foldl (fun acc x => acc ++ [x]) selfArgs)\n"
             "  | .scalarZero       => Except.ok selfArgs\n"
             "  | .nonVector        => Except.error ()"),
            (_P_BODY,
             "  intro selfArgs other\n"
             "  unfold problem_spec_vectorAdd implementation_vectorAdd\n"
             "  cases other with\n"
             "  | vector otherArgs =>\n"
             "    simp only [Except.ok.injEq]\n"
             "    induction otherArgs generalizing selfArgs with\n"
             "    | nil => simp\n"
             "    | cons a as ih => simp [ih, List.append_assoc]\n"
             "  | scalarZero => rfl\n"
             "  | nonVector => rfl"),
        ),
        "rationale": "correct reshape: the combined component list is built by "
                     "folding the operand's components onto the receiver one at "
                     "a time instead of by a single append. Same result on every "
                     "input of every arm, so C-vec, C-zero and C-err all still "
                     "hold — if this were rejected the spec would be "
                     "SPEC-TOO-STRONG, pinning the CONSTRUCTION of the combined "
                     "list rather than its value. Unlike a monadic-skeleton "
                     "re-spelling, this reshape is NOT definitionally equal to "
                     "the frozen implementation (checked: `rfl` between the two "
                     "fails) and the frozen tactic body does NOT close it "
                     "(checked: unsolved goals on the empty arm, `rfl` failed on "
                     "the cons arm), so the proof genuinely re-establishes the "
                     "clause by induction on the operand's component list "
                     "rather than by reduction. Re-proved inside the proof "
                     "region only; statement byte-identical, no new "
                     "axiom/lemma/helper. Second positive at a different "
                     "structural axis from pos-total-dispatch: that one varies "
                     "the BRANCHING, this one varies how the combined VALUE is "
                     "constructed. Ports the sibling's pos-two-loops reshape "
                     "(an incremental construction of the combined carrier) "
                     "faithfully. Verified: real build, exit 0.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE, non-vacuously, at
    # normal inputs on all three arms. The frozen theorem carries no hypothesis
    # binder (it is universally quantified over both inputs with no
    # precondition), so the sibling's precondition-admission case has no
    # precondition to admit; the honest analogue is to discharge the modeled
    # behavior at one ground input on EACH arm as `have`s, then close the frozen
    # obligation verbatim. Nothing is assumed: no new declaration, statement
    # byte-identical, the ground instances are `have`s prepended inside the
    # existing tactic body. Verified: real build, exit 0.
    # =====================================================================
    {
        "id": "admiss-ground-arms",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _identity : problem_spec_vectorAdd [1] "
            "AddOperand.scalarZero\n"
            "      (implementation_vectorAdd [1] AddOperand.scalarZero) := by\n"
            "    rfl\n"
            "  have _combined : problem_spec_vectorAdd [1] "
            "(AddOperand.vector [2])\n"
            "      (implementation_vectorAdd [1] (AddOperand.vector [2])) := by\n"
            "    rfl\n"
            "  have _rejected : problem_spec_vectorAdd [1] "
            "AddOperand.nonVector\n"
            "      (implementation_vectorAdd [1] AddOperand.nonVector) := by\n"
            "    rfl\n"
            + _P_INTRO),
        "rationale": "the modeled behavior is discharged by evaluation at one "
                     "ground input on EACH of the three arms — the additive "
                     "identity against a one-component receiver (the shape the "
                     "newly-observed behavior turns on), a genuine operand with "
                     "its own component, and an invalid operand — then the "
                     "frozen obligation is closed verbatim. Verifies, so the "
                     "obligation is satisfiable and non-vacuous at normal "
                     "inputs; if it did not, the spec would be unsatisfiable at "
                     "exactly the inputs the modeled behavior is about (the "
                     "analogue of PRECOND-TOO-STRONG, which is what the "
                     "sibling's admiss-gold case tested via its Requires). "
                     "Nothing is assumed: no new declaration, statement "
                     "byte-identical, ground instances are `have`s in the "
                     "existing tactic body. Verified: real build, exit 0.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) a `refinement`
    # argument, CONFIRMED BY EXECUTION of the faithful counterpart against the
    # recorded FAIL_TO_PASS + PASS_TO_PASS at base_commit with the test patch
    # applied, and (b) a witness SEEN to discriminate with two real builds.
    # =====================================================================

    # ---- the discriminating behavior itself: the identity is rejected ----
    {
        "id": "weak-identity-rejected",
        "kind": "uniqueness",
        "expect": "reject",
        # Remove the identity-recognising guard, so the additive identity falls
        # through the dispatch to the rejecting arm. This is the pre-fix
        # behavior and the direct counterpart of the sibling's
        # prepatch-no-shortcircuit case.
        "module": _swap(_BASE, _I_GUARD, ""),
        "refinement": "this is the pre-fix behavior: with no branch recognising "
                      "the additive identity, an identity operand reaches the "
                      "validating step and is rejected as a type error instead "
                      "of leaving the receiver unchanged. EXECUTED: the faithful "
                      "counterpart raises on the very assertion the test patch "
                      "adds (the additive identity added to a basis component "
                      "must equal that component), so the FAIL_TO_PASS test "
                      "errors out and does NOT resolve. Confirmed against the "
                      "recorded tests at base_commit — this is the documented "
                      "G-DIFF discriminator and the reason the bundle exists.",
        "rationale": "REJECT from C-zero: the spec pins `result = Except.ok "
                     "selfArgs` for an identity operand, but with the guard "
                     "removed the identity operand is matched by the catch-all "
                     "arm and the rival yields `Except.error ()`. Refuted at "
                     "(selfArgs = [1], other = .scalarZero) — the smallest input "
                     "on the discriminating arm, and the modeled counterpart of "
                     "the assertion the test patch adds.",
        "witness": _w("[1]", "AddOperand.scalarZero"),
    },

    # ---- the identity branch succeeds but does not preserve the receiver ----
    {
        "id": "weak-identity-renormalised",
        "kind": "uniqueness",
        "expect": "reject",
        # Subtler than dropping the guard: the identity IS recognised and the
        # call SUCCEEDS, but it yields the empty component list instead of the
        # receiver's own. Attacks the no-op half of C-zero rather than the
        # accepted half, and carries the frame obligation the sibling's
        # permission-mutation cases defended: the unchanged input must be pinned.
        "module": _swap(_BASE, _I_ZERO_RESULT,
                        "      return Except.ok ([] : List Int)"),
        "refinement": "recognising the additive identity but returning an empty "
                      "component list is 'accepted' without being a no-op. "
                      "EXECUTED: the faithful counterpart returns the zero "
                      "vector for every identity addition, so the assertion the "
                      "test patch adds (identity plus a basis component equals "
                      "that component) is False rather than raising, the "
                      "FAIL_TO_PASS test fails, and a PASS_TO_PASS test that "
                      "sums derivative terms through the identity fails too. "
                      "Confirmed against the recorded tests at base_commit: does "
                      "NOT resolve.",
        "rationale": "REJECT from C-zero: the spec pins `result = Except.ok "
                     "selfArgs` — the receiver's own list, unchanged — and the "
                     "rival yields `Except.ok []`, which differs for every "
                     "non-empty receiver. This is the clause that carries the "
                     "frame discipline on this carrier (the unchanged input is "
                     "named explicitly), so it is the honest counterpart of the "
                     "sibling's read-only-operand cases and of its "
                     "scalar-zero-renormalise case. Refuted at (selfArgs = "
                     "[3, 4], other = .scalarZero): a DIFFERENT point from "
                     "weak-identity-rejected — same arm, but a two-element "
                     "receiver with different contents, so the two witnesses do "
                     "not collapse onto one input and the receiver binder is "
                     "genuinely varied on this arm.",
        "witness": _w("[3, 4]", "AddOperand.scalarZero"),
    },

    # ---- the operand's contribution is dropped ----
    {
        "id": "weak-operand-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # A genuine operand is accepted, but its components are discarded: the
        # receiver's own list comes back. Ports the VALUE content of the
        # sibling's drop-other family onto a carrier where the disagreement is
        # computed rather than blocked by opacity.
        "module": _swap(_BASE, _I_VEC_ARM,
                        "    | .vector _         => return Except.ok selfArgs"),
        "refinement": "accepts a genuine operand and then discards its "
                      "contribution, returning the receiver unchanged. EXECUTED: "
                      "the faithful counterpart makes every addition of two "
                      "genuine operands return the left one, so the FAIL_TO_PASS "
                      "test's assertions about a sum's components (each "
                      "component of the sum must be the sum of the two "
                      "operands' components) are False, and two PASS_TO_PASS "
                      "tests fail as well once derivative terms accumulate "
                      "through addition. Confirmed against the recorded tests at "
                      "base_commit: does NOT resolve.",
        "rationale": "REJECT from C-vec: the spec pins `result = Except.ok "
                     "(selfArgs ++ otherArgs)` but the rival yields `Except.ok "
                     "selfArgs`, which differs whenever the operand carries any "
                     "component. Refuted at (selfArgs = [5], other = .vector "
                     "[6, 7]) — a two-component operand, so the disagreement is "
                     "not a length-one coincidence.",
        "witness": _w("[5]", "(AddOperand.vector [6, 7])"),
    },

    # ---- both contributions are dropped ----
    {
        "id": "weak-combination-emptied",
        "kind": "uniqueness",
        "expect": "reject",
        # The degenerate C-vec attack: accept a genuine operand and return the
        # empty component list, independent of BOTH inputs. Ports the sibling's
        # most degenerate drop-other case.
        "module": _swap(
            _BASE, _I_VEC_ARM,
            "    | .vector _         => return Except.ok ([] : List Int)"),
        "refinement": "accepts a genuine operand and returns an empty component "
                      "list regardless of either input. EXECUTED: the faithful "
                      "counterpart makes every addition of two genuine operands "
                      "produce the zero vector, so the FAIL_TO_PASS test's "
                      "component assertions about a sum are False and all three "
                      "recorded tests fail (one of them by indexing into the "
                      "now-empty component list). Confirmed against the recorded "
                      "tests at base_commit: does NOT resolve.",
        "rationale": "REJECT from C-vec: the spec pins `result = Except.ok "
                     "(selfArgs ++ otherArgs)` but the rival yields `Except.ok "
                     "[]`, which differs whenever either input carries a "
                     "component. Distinct from weak-operand-dropped, which "
                     "keeps the receiver and so agrees with the spec on an "
                     "empty operand: this one is wrong on strictly more of the "
                     "domain, so it gets its OWN witness rather than sharing. "
                     "Refuted at (selfArgs = [8, 9], other = .vector [10]) — "
                     "receiver and operand lengths swapped relative to "
                     "weak-operand-dropped, so the two C-vec witnesses vary both "
                     "binders against each other.",
        "witness": _w("[8, 9]", "(AddOperand.vector [10])"),
    },

    # ---- the classification is inverted: invalid operands are accepted ----
    {
        "id": "weak-invalid-accepted",
        "kind": "uniqueness",
        "expect": "reject",
        # The classification is inverted between the two non-appending shapes:
        # the additive identity is sent to the rejecting path, and an invalid
        # operand is silently accepted as a no-op. Ports the argument of the
        # sibling's swallow-neither / swallow-not-a-vector cases while keeping a
        # refinement that HOLDS on this instance's recorded tests (see
        # assessment: the plain swallow does not).
        "module": _swap(
            _BASE, _I_BODY,
            "  Id.run do\n"
            "    match other with\n"
            "    | .vector otherArgs => return Except.ok "
            "(selfArgs ++ otherArgs)\n"
            "    | .scalarZero       => return Except.error ()\n"
            "    | .nonVector        => return Except.ok selfArgs"),
        "refinement": "inverts the classification of the two non-appending "
                      "operand shapes: an invalid operand is silently accepted "
                      "as a no-op, and the additive identity is rejected. "
                      "EXECUTED: the faithful counterpart raises on the "
                      "assertion the test patch adds (the additive identity must "
                      "be accepted and leave the receiver unchanged), so the "
                      "FAIL_TO_PASS test errors out. Confirmed against the "
                      "recorded tests at base_commit: does NOT resolve. The "
                      "silent acceptance half is additionally a behavioural "
                      "regression the library's callers rely on — an invalid "
                      "addend would be absorbed instead of reported, so a "
                      "downstream product of the mis-typed sum would be computed "
                      "on the wrong operand rather than refused.",
        "rationale": "REJECT from C-err: the spec pins `result = Except.error ()` "
                     "for an invalid operand and the rival yields `Except.ok "
                     "selfArgs`. This is the ONLY rival attacking C-err, and the "
                     "witness is stated on that arm, so the rejection is "
                     "attributed to C-err specifically; the F2P failure of its "
                     "faithful counterpart comes from the identity half of the "
                     "same inversion, which is stated plainly in `refinement` "
                     "rather than claimed for the C-err half. Refuted at "
                     "(selfArgs = [2], other = .nonVector) — the third operand "
                     "constructor, which no other witness reaches.",
        "witness": _w("[2]", "AddOperand.nonVector"),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 7 uniqueness rivals) plus 3 AXIOM_TESTS. This
# bundle models the SAME single purely-functional core, but over a pure carrier
# with no heap, no permissions and no opaque normalising callee, so several
# sibling cases have no referent. Every sibling case is recorded below.
#
#   sibling case                 -> here
#   -----------------------------------------------------------------------
#   admiss-gold                  -> admiss-ground-arms       RE-EXPRESSED
#   pos-two-loops                -> pos-fold-append          RE-EXPRESSED
#   (none)                       -> pos-total-dispatch       ADDED (2nd axis)
#   prepatch-no-shortcircuit     -> weak-identity-rejected   PORTED
#   scalar-zero-renormalise      -> weak-identity-renormalised  RE-EXPRESSED
#   drop-other-return-self       -> weak-operand-dropped     RE-EXPRESSED
#   drop-other-vec-empty         -> weak-combination-emptied RE-EXPRESSED
#   drop-other-vec-self          -> (none)                   DROPPED (collapses)
#   swallow-neither-sharp        -> weak-invalid-accepted     RE-EXPRESSED
#   swallow-not-a-vector         -> (none)                   DROPPED (resolves)
#   frame-write-self-terms       -> (none)                   VACUOUS (no heap)
#   frame-write-is-vector        -> (none)                   VACUOUS (no heap)
#   AXIOM_TESTS (3)              -> (none)                   DROPPED (G-AX)
#
# RE-EXPRESSED (admiss-ground-arms): the sibling's admissibility witness is the
#   frozen implementation itself, testing that its fractional-permission
#   Requires is not too strong to admit an F2P-shaped input. The frozen
#   obligation here has NO precondition at all (both inputs universally
#   quantified, no hypothesis binder), so there is no precondition to admit and
#   an identity case would test nothing beyond G-VERIFY. The honest analogue is
#   to show the modeled behavior is SATISFIABLE and non-vacuous at a ground input
#   on each of the three arms, then close the frozen obligation verbatim.
# RE-EXPRESSED (pos-fold-append): the sibling's positive reshapes an index-loop
#   construction of the combined carrier into two sequential loops — i.e. it
#   varies HOW the combined carrier is built. The faithful analogue here is the
#   fold reshape: build the combined list by consuming the operand's components
#   one at a time instead of by a single `++`. Confirmed a real reshape and not a
#   re-spelling: the two implementations are NOT definitionally equal (`rfl`
#   between them fails) and the frozen tactic body does not close it, so the
#   clause is re-established by induction. An earlier port used a pure
#   `if`/`else` re-spelling of the same guard-then-dispatch here; that variant
#   was definitionally EQUAL to the frozen implementation (measured: `∀ s o,
#   implementation_vectorAdd s o = <variant> s o` closes by `rfl`, and the frozen
#   tactic body closes the variant verbatim), so it verified without probing
#   anything and was replaced.
# ADDED (pos-total-dispatch): a second positive at a different structural axis —
#   one total three-way match instead of guard-then-two-way, which varies the
#   BRANCHING rather than the construction. Not definitionally equal to the
#   frozen implementation either (measured: `rfl` between the two fails), so it
#   is an independent probe and not a duplicate of pos-fold-append.
# RE-EXPRESSED (the three drop-other rivals -> two here): the sibling needs three
#   because its postcondition applies an OPAQUE normalising function, so `return
#   self`, `Vec(self.terms)` and `Vec([])` are three distinct arguments to that
#   function and each has to be refuted separately. Here the arm pins a concrete
#   list equality, so `Vec(self.terms)` and `return self` are the SAME function on
#   this carrier — both yield exactly `selfArgs` — and shipping both would be one
#   rival twice. Two survive: drop the operand's contribution
#   (weak-operand-dropped) and drop both (weak-combination-emptied), and they get
#   separate witnesses at swapped input lengths because the second is wrong on
#   strictly more of the domain than the first.
# DROPPED (swallow-not-a-vector) — NOT a carrier collapse, a FALSE REFINEMENT.
#   The sibling's cheapest swallow accepts any non-identity operand and returns
#   the receiver, never rejecting an invalid one. It ports cleanly to this
#   carrier as `.nonVector => Except.ok selfArgs` with the other two arms left
#   gold, and it IS rejected by C-err, and a discriminating witness at
#   (selfArgs = [2], other = .nonVector) was built and SEEN to discriminate
#   (rival exit 0, gold exit 1). It is dropped anyway, because its `refinement`
#   would be false: the faithful counterpart was EXECUTED against the recorded
#   FAIL_TO_PASS and both PASS_TO_PASS tests at base_commit with the test patch
#   applied, and all three PASS. The recorded tests never add an invalid operand,
#   so they do not observe the swallow at all. Shipping it would have asserted a
#   verify-does-not-resolve break that this instance's tests cannot exhibit.
#   weak-invalid-accepted attacks the SAME clause with the same witness arm but
#   pairs the swallow with an inverted identity branch, which the recorded
#   FAIL_TO_PASS does catch — so C-err stays attacked with a refinement that
#   holds. Recorded here because the C-err clause is real (the modeled behavior
#   does reject invalid operands) but is NOT F2P-discriminating on its own; that
#   is a property of this instance's test set, not a gap in the battery.
# DROPPED (a reversed-append rival) — same reason, no sibling counterpart. An
#   obvious C-vec rival is `otherArgs ++ selfArgs` (operand's components first).
#   It is rejected by C-vec and a witness discriminates, but its faithful
#   counterpart PASSES all three recorded tests (the downstream constructor is
#   order-insensitive for the component families the tests use), so its
#   refinement would be false. Not shipped. The two shipped C-vec rivals both
#   DROP content rather than reorder it, and both were confirmed to fail the
#   recorded tests.
# VACUOUS (frame-write-self-terms, frame-write-is-vector): the sibling rejects
#   these by the fractional-permission system — an in-place append to a
#   half-permission list, and a full write to a half-permission discriminator
#   field. Lean is referentially transparent: `selfArgs` and `other` are
#   immutable values, there is no mutable field, no aliasing and no permission,
#   so neither rival can be written at all. No substitute probe is fabricated.
#   The obligation those cases defended is not lost: C-zero pins the result to
#   the input list by name, and weak-identity-renormalised attacks that pinning.
# KNOWN HOLE (divergence): the sibling carries no diverge-*/nonterm-*/weak-diverge
#   case, and the class was originally recorded here as VACUOUS on the ground that
#   a non-terminating implementation "cannot be written". Corrected: it CAN be
#   written, as a `partial def`, which elaborates fine and is in variant scope. It
#   is still not shippable, but for a different reason than vacuity — `partial
#   def` makes the constant opaque to reduction, so no witness discriminates.
#   Measured: the conditioned witness elaborates against the `partial` rival (exit
#   0) and ALSO against the frozen solution (exit 0), and failing on gold is the
#   half that makes a witness a discriminator. A plain self-recursive `def` (no
#   `partial`) is rejected instead by the termination checker (`fail to show
#   termination ... failed to infer structural recursion`), which attributes
#   nothing to the spec. So: known hole in the spec, not a complete battery. See
#   the DIVERGENCE bullet in the module docstring for the full measurement. The
#   frozen solution sets no `loom.semantics.termination` option at all, so this is
#   adjacent to but distinct from the velvet `partial`-semantics hole of
#   the corpus-wide termination-semantics finding.
#
# POINT SPREAD. The five reject witnesses probe five DISTINCT input pairs
# (pts=5):
#   (selfArgs, other) =
#     ([1],    .scalarZero)      weak-identity-rejected       C-zero
#     ([3, 4], .scalarZero)      weak-identity-renormalised   C-zero
#     ([5],    .vector [6, 7])   weak-operand-dropped         C-vec
#     ([8, 9], .vector [10])     weak-combination-emptied     C-vec
#     ([2],    .nonVector)       weak-invalid-accepted        C-err
#   `other` covers all THREE constructors, with two distinct `.vector` payloads
#   of different lengths (1 and 2). `selfArgs` takes five pairwise-distinct
#   values across two lengths, and within EACH arm it is varied (the two C-zero
#   witnesses differ in it; the two C-vec witnesses swap receiver and operand
#   lengths), so neither binder is pinned on any clause and every top-level
#   clause is attacked.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job, and this bundle declares no
# `opaque` callee and consumes no `axiom` — the operand classification and the
# combined component list are modeled deeply — so the sibling's three probes (two
# axiom-soundness, one caller-domain containment, all for callees this bundle
# folds into the structural model) have no referent. This bundle's recorded G-AX
# is a skip, and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
