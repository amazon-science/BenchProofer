"""properties.py — G-PBT falsification battery for sympy__sympy-14976 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_mpfRational`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide``, no new
``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff (in scope AND it
does NOT verify AND the case's refutation ``witness`` holds of the rival while
FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the same single purely-functional core over a ``PSeq[int]`` code-point
carrier and pins the result against a GROUNDED pure deep model (nagini's
``rendered(p, q)``, itself spelled out from ``ctor()`` and the two operand
sequences). This Lean bundle models the SAME core — the textual rendering of a
rational number for the arbitrary-precision floating-point evaluation backend —
over ``Int → Int → List Char``, with the SAME grounding: the postcondition is a
single equation relating ``result`` to a concatenation built from the two integer
inputs, so there is no opaque answer key an implementation could echo. Every
nagini value-level rival carries over as an attack on that equation; the nagini
frame/permission-mutation class is VACUOUS here (see ``assessment``); there is no
divergence case in the sibling and none is SHIPPABLE here, for the measured
reason recorded under ``assessment`` (not because a diverging body cannot be
written — one can, as a ``partial def``; it is the WITNESS that cannot be made to
discriminate).

DEFENDED SURFACE (one modeled behavior, one obligation, one top-level clause).
``problem_spec_mpfRational p q result`` pins EXACTLY one equation:

    result = mpfName ++ "(" ++ intText p ++ ")/" ++ mpfName ++ "(" ++ intText q ++ ")"

Read as a conjunction of independent structural commitments, all of which live in
that single clause and each of which some rival below violates:

  * (S1) the numerator operand is WRAPPED — the backend constructor name and an
    opening paren precede ``intText p``, and a closing paren follows it;
  * (S2) the denominator operand is INDEPENDENTLY wrapped the same way — the
    constructor name is applied a SECOND time, to ``intText q``;
  * (S3) the two wrapped operands are joined by the division sign, in that
    ORDER: the numerator's text first, the denominator's second;
  * (S4) the wrapper is exactly ``mpfName``, both times;
  * (S5) the operands are the FUNCTIONS ``intText p`` and ``intText q`` of the
    respective binders — not each other, not a constant.

The BEHAVIOURAL DISCRIMINATOR: each operand must carry its own full-precision
integer text inside its own constructor application, so that neither operand — and
not the quotient as a whole — is ever formed at reduced precision. Emitting the
bare textual quotient of the two integers is the pre-fix behavior; the
``bare-division`` rival below IS that behavior, and ``wrap-once`` is the
one-constructor-around-the-whole-quotient near miss, which still forms the
quotient at reduced precision before the constructor ever sees it.

BINDER STRUCTURE. The spec predicate has THREE binders: ``p`` (numerator),
``q`` (denominator), ``result``. Both INPUT binders are load-bearing and both are
varied across the reject witnesses — see the point-spread block at the bottom:
twelve witnesses at twelve DISTINCT ``(p, q)`` points (``pts=12``), with
``p ∈ {-3, 0, 1, 2, 3, 4, 5, 7, 8, 11, 232}`` and
``q ∈ {2, 3, 4, 5, 6, 7, 9, 10, 13}``. Two rivals exist specifically to keep
each binder honest: ``dup-numerator`` ignores ``q`` entirely and ``dup-denominator``
ignores ``p`` entirely, so a rival mishandling only one input cannot slip
through, and ``hardcode-f2p`` ignores BOTH (it returns the literal text the hidden
observation expects), so the battery demonstrates that the spec is not
satisfiable by echoing a constant.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The sibling's two mandatory
    frame-mutation rivals write into an input held at partial permission. This
    carrier has no heap, no aliasing, no permission and no mutable input binder:
    ``p`` and ``q`` are immutable ``Int`` values passed by value. There is nothing
    to overwrite and no substitute probe is fabricated (porting map: vacuous
    here).

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE (not vacuous), and the sibling
    carries no such case. The earlier revision of this note claimed a diverging
    implementation "cannot be written at all" because the frozen callee is a
    total Lean ``def``. That is WRONG, and measured wrong: the impl region may be
    respelled ``partial def implementation_mpfRational ... := implementation_mpfRational p q``,
    which is inside ``impl-start``/``impl-end``, passes ``variant_scope``
    (``same_spec`` holds, the obligation statement is byte-identical, no new
    axiom/theorem, and ``partial`` is not an assumption token) and elaborates —
    only the frozen ``rfl`` fails, exit 1. A plain self-recursive ``def`` is
    genuinely unwritable (``fail to show termination``, so the FILE does not
    compile and the case would be a tooling artifact rather than a rival), but the
    ``partial`` spelling sidesteps that.

    So the class is expressible; what it lacks is a DISCRIMINATING witness, and
    that is a property of the spec, not of the carrier. ``partial def`` makes the
    constant opaque to the kernel — it is compiled via a well-founded escape and
    carries no equation lemma — so every witness route measured fails on the
    rival side, which is the half that must SUCCEED: ``unfold`` reports "failed to
    unfold ``implementation_mpfRational``"; ``decide`` after unfolding only the
    spec reports "``decide`` failed for proposition"; ``simp`` with the impl and
    both spec helpers, and a ``List.length`` projection route, both leave
    "unsolved goals". Conditioning does not rescue it either: a witness
    hypothesising ``implementation_mpfRational 1 2 = []`` elaborates against the
    rival (exit 0) but ALSO against the frozen solution (exit 0), because the
    hypothesis is unsatisfiable-but-irrefutable on both sides — the gate records
    that as ``witness-vacuous``, and the consistency probe cannot clear it
    (``simp_all made no progress``, exit 1, on gold AND on the rival). A witness
    that holds of gold attests to nothing.

    Recorded as a KNOWN HOLE per the divergence-lane rule: this bundle's frozen
    obligation is a bare ``∀ p q, problem_spec ...`` with no termination
    obligation attached to the impl, so a ``partial`` rival is not refuted by the
    spec — it is merely not provable by any tactic, which is exactly the
    "rejected for a tooling reason, not a spec reason" outcome the witness
    requirement exists to exclude. Shipping it would record a hollow ``rejected``.
    Nothing is claimed as vacuous here.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, exactly as the sibling records. The
    postcondition is GROUNDED: ``result`` is pinned to a concatenation of literal
    pieces and the two ``intText`` applications, so producing it IS doing the
    work; there is no opaque answer key to echo. In its place the sibling ships an
    honest cheapest-implementation positive control, and so does this battery
    (``pos-inline-func``). The ``hardcode-f2p`` rival is the mechanical proof that
    the grounding bites: the cheapest possible cheat — return the exact text the
    hidden observation checks — is refuted at any other input point.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole battery lives.
    Every rival is correct on part of the domain (or on the single input the
    hidden observation probes) and diverges where one of S1–S5 bites.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is a bare ``rfl``, tuned to the
frozen concatenation's syntactic form — so a rejection alone attributes nothing to
the spec. Every ``expect="reject"`` case therefore carries a Lean snippet that
states the spec predicate NEGATED at one concrete ``(p, q)`` and closes by
``decide`` after unfolding both the spec and the implementation. Eleven of the
twelve witnesses bind NOTHING in their head (both inputs are non-negative integer
literals, and the whole carrier is a decidable ``List Char`` equality at those
points), so there are no hypotheses whose joint satisfiability could be in
question; the twelfth conditions on one true equation and is checked for
satisfiability by the gate's own consistency probe. Each
witness was checked with two real ``lake env lean`` builds: it HOLDS of its rival
and FAILS on the frozen solution, so it discriminates rather than asserting a
tautology.

  Note on the witness input domain. The eleven EVALUATING witnesses use
  non-negative literals, because ``intText`` is ``toString`` on ``Int`` and its
  negative branch
  does not reduce in the kernel: measured, ``decide``, ``decide +kernel``,
  ``rfl``, ``simp``, ``simp [Int.toString, Int.repr]`` and ``norm_num`` all fail
  to establish even ``intText (-3) = "-3".toList``, while the same claim at ``3``
  closes by ``decide``. That is a property of the numeral's kernel reduction, not
  of the spec.

  It does NOT mean the sign of an operand is untestable, and it is not recorded as
  a gap. ``drop-sign`` is a rival that is correct on every non-negative input and
  wrong on every negative one, and its witness reaches the negative point by
  CONDITIONING instead of evaluating — stating the one fact the kernel will not
  compute (the decimal text of a negative integer is a minus sign followed by the
  text of its magnitude) as a hypothesis that is true of ``intText``, hence
  satisfiable, and deriving the disequality from it. See ``_witness_signed``.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
renders text differing from what the hidden observation of this behavior demands
for the smallest rational, so the faithful patch would NOT resolve — and, for the
rivals that keep the text well-formed, that the rendered expression additionally
evaluates the rational at reduced precision or to the wrong value, which is the
defect the issue reports.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the rendering is modeled deeply; the constructor name and the integer
decimal text are A-references validated out of band by G-AX). The sibling's
``AXIOM_TESTS`` is empty too, and this gate ignores that lane regardless — see
``assessment``.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-14976"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each is unique in Solution.lean (asserted by _swap at import)
# and lies ENTIRELY inside the region it names, so every variant is in scope by
# construction.
# ---------------------------------------------------------------------------

# The whole body of `implementation_mpfRational`, i.e. everything after the
# signature line and strictly inside `-- impl-start` / `-- impl-end`.
_I_BODY = (
    '  let func := mpfName\n'
    '  func ++ "(".toList ++ intText p ++ ")/".toList ++\n'
    '  func ++ "(".toList ++ intText q ++ ")".toList')

# The frozen tactic body, strictly inside `-- proof-start` / `-- proof-end`.
# Swapping this NEVER touches the `theorem correct_mpfRational` statement line,
# which stays byte-identical in every variant.
_P_BODY = "  intro p q\n  rfl"


def _impl(body):
    """The full solution source with only the implementation body replaced."""
    return _swap(_BASE, _I_BODY, body)


def _witness(p, q):
    """Negate the spec predicate at the concrete input point (p, q).

    Both the spec and the implementation are unfolded, leaving a ground
    `List Char` disequality that `decide` settles. Binds nothing, so there are no
    hypotheses to be inconsistent.
    """
    return (
        f"example : ¬ problem_spec_mpfRational {p} {q}\n"
        f"    (implementation_mpfRational {p} {q}) := by\n"
        "  unfold problem_spec_mpfRational implementation_mpfRational\n"
        "  decide\n")


def _witness_signed(neg, pos, q):
    """Negate the spec predicate at a NEGATIVE numerator, by conditioning.

    `intText` is `toString` on `Int`, and the negative branch does not reduce in
    the kernel: measured, `decide`, `decide +kernel`, `rfl`, `simp`,
    `simp [Int.toString, Int.repr]` and `norm_num` all fail to establish even
    `intText (-3) = "-3".toList`, while the same claim at `3` closes by `decide`.
    So a negative point cannot be settled by EVALUATION the way `_witness` does.

    It can still be refuted, by stating the one fact evaluation cannot reach as a
    HYPOTHESIS — that the decimal text of a negative integer is a minus sign
    followed by the text of its magnitude — and deriving the disequality from it.
    The hypothesis is TRUE of `intText`, so it assumes nothing false; the gate's
    consistency probe confirms it is satisfiable (no tactic derives `False` from
    it, since the negative branch is exactly what will not reduce).

    This keeps the SIGN of the numerator an attacked part of the domain rather
    than a recorded gap.

    FORGERY-CHECKED (the one witness here whose gold-side failure is not a plain
    evaluation: gold reports "`decide` proved that the proposition False is
    false", because `rw [hneg]; simp [mpfName]` closes the equation for gold and
    collapses the negated goal to `False`). A collapsed goal has to be shown to
    track the CLAIM rather than to be a fixed artifact of the script, so the
    flipped-claim experiment was run: asserting the OPPOSITE (the same head and
    hypothesis, `¬` dropped, proved by `unfold ...; rw [hneg]`) elaborates against
    the FROZEN solution (exit 0) and FAILS against this rival (exit 1, "unsolved
    goals"). That is the exact inverse of the witness's own pair (rival exit 0,
    gold exit 1), so gold's exit code carries information about what is claimed:
    gold satisfies the spec at (-3, 5) and the rival does not. The error is a
    semantic refutation, not a syntactic accident.
    """
    return (
        f"example (hneg : intText (-{neg}) = '-' :: intText {pos}) :\n"
        f"    ¬ problem_spec_mpfRational (-{neg}) {q}\n"
        f"      (implementation_mpfRational (-{neg}) {q}) := by\n"
        "  unfold problem_spec_mpfRational implementation_mpfRational\n"
        "  rw [hneg]\n"
        "  simp [mpfName]\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_mpfRational` statement byte-identical and adds no
    # declaration. All three confirmed with real builds.
    # =====================================================================
    {
        "id": "pos-inline-func",
        "kind": "soundness",
        "expect": "verify",
        # Drop the named local for the constructor name and mention it directly
        # at both operand positions. Definitionally the frozen body, so the
        # frozen `rfl` still closes with no proof authoring at all — this is the
        # cheapest correct implementation of the modeled behavior, and it is the
        # honest stand-in for the sibling's ungrounded-oracle slot (there is no
        # oracle to echo; see the module docstring).
        "module": _impl(
            '  mpfName ++ "(".toList ++ intText p ++ ")/".toList ++\n'
            '  mpfName ++ "(".toList ++ intText q ++ ")".toList'),
        "rationale": "CORRECT reshape that inlines the shared local naming the "
                     "constructor, mentioning it directly at both operand "
                     "positions. Produces the same text on every (p, q), so the "
                     "single postcondition equation still holds — else "
                     "SPEC-TOO-STRONG. Definitionally the frozen body, so the "
                     "frozen tactic body closes it unchanged; statement "
                     "byte-identical, no new axiom/lemma. Ports the sibling's "
                     "pos-cheapest / pos-single-expr positives, which likewise "
                     "assemble the sequence as one expression instead of a chain "
                     "of accumulating writes.",
    },
    {
        "id": "pos-den-local",
        "kind": "soundness",
        "expect": "verify",
        # Build the DENOMINATOR side into its own local first, then prefix the
        # numerator side. Different build order and data shape, same text. The
        # frozen `rfl` no longer applies to this `let`-shape, so the proof body
        # is re-proved by unfolding both sides — still inside the proof region,
        # statement byte-identical, nothing assumed.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             '  let den := mpfName ++ "(".toList ++ intText q ++ ")".toList\n'
             '  mpfName ++ "(".toList ++ intText p ++ ")/".toList ++ den'),
            (_P_BODY,
             "  intro p q\n"
             "  simp [problem_spec_mpfRational, implementation_mpfRational]"),
        ),
        "rationale": "CORRECT reshape that assembles the DENOMINATOR-side "
                     "fragment into a local first and then prefixes the "
                     "numerator-side fragment: reversed build order, different "
                     "data shape, identical resulting text, so the postcondition "
                     "equation must still hold — else SPEC-TOO-STRONG. Re-proved "
                     "in the proof region by unfolding both sides (no new "
                     "axiom/lemma, no assumption token, statement "
                     "byte-identical). Ports the sibling's pos-reorder-build, "
                     "which likewise stages the two operand sides into separate "
                     "locals before joining them.",
    },
    {
        "id": "pos-string-level",
        "kind": "soundness",
        "expect": "verify",
        # Assemble the whole rendering at the STRING level and convert once at
        # the end, instead of concatenating character lists. Genuinely different
        # carrier for the intermediate value; same final text. Re-proved by
        # unfolding the two spec-side helpers as well.
        "module": _swaps(
            _BASE,
            (_I_BODY,
             '  ("mpmath.mpf(" ++ toString p ++ ")/mpmath.mpf(" ++ toString q\n'
             '    ++ ")").toList'),
            (_P_BODY,
             "  intro p q\n"
             "  simp [problem_spec_mpfRational, implementation_mpfRational,\n"
             "    mpfName, intText]"),
        ),
        "rationale": "CORRECT implementation over a DIFFERENT intermediate "
                     "carrier: the rendering is assembled as a single string and "
                     "converted to the character-list result once at the end, "
                     "rather than concatenating character lists throughout. Same "
                     "text for every (p, q), so it must verify — else "
                     "SPEC-TOO-STRONG (the spec would be pinning an incidental "
                     "concatenation shape rather than the rendered text). "
                     "Re-proved by unfolding the spec's two named pieces; "
                     "statement byte-identical, no new axiom/lemma. This is the "
                     "structural-difference positive the sibling gets from its "
                     "single-expression build; on this carrier the sharper "
                     "distinction available is the intermediate representation.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal input of the shape the hidden observation of this behavior uses.
    # The frozen theorem carries NO precondition hypothesis (the spec is stated
    # for all integer p, q), so the sibling's precondition-admission self-call
    # re-expresses as: discharge the spec predicate BY EVALUATION at that
    # concrete point as a `have`, then close the frozen obligation verbatim.
    # Nothing is assumed: no new declaration, statement byte-identical, the
    # ground instance is a `have` prepended to the existing tactic body.
    # (Confirmed: real build.)
    # =====================================================================
    {
        "id": "admiss-smallest-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_BODY,
            "  have _ground : problem_spec_mpfRational 1 2\n"
            "      (implementation_mpfRational 1 2) := by\n"
            "    unfold problem_spec_mpfRational implementation_mpfRational\n"
            "    decide\n"
            + _P_BODY),
        "rationale": "the obligation is discharged BY EVALUATION at the smallest "
                     "non-trivial input (numerator 1, denominator 2 — the "
                     "smallest rational the modeled behavior can be observed "
                     "on), as a `have`, and then the frozen obligation is closed "
                     "verbatim. Verifies, so the modeled behavior is satisfiable "
                     "at exactly a normal input rather than only vacuously or "
                     "only in the abstract — the analogue of the sibling's "
                     "PRECOND-TOO-STRONG probe, whose self-call establishes the "
                     "input carriers and asserts the load-bearing clause for "
                     "that same point. Nothing is assumed: no new declaration, "
                     "statement byte-identical, ground instance sits inside the "
                     "existing tactic body. Ports admiss-f2p-shaped.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve, and (b) a witness pinning the
    # violation at one concrete input, confirmed by two real builds to hold of
    # the rival and fail on the frozen solution.
    # =====================================================================

    # ---- S2: denominator operand left unwrapped (closest near miss) ----------
    {
        "id": "drop-den-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '  let func := mpfName\n'
            '  func ++ "(".toList ++ intText p ++ ")/".toList ++ intText q'),
        "refinement": "a faithful patch applying the backend constructor to the "
                      "numerator only renders the smallest rational as the "
                      "constructor applied to 1, divided by a bare 2. The hidden "
                      "observation of this behavior demands the constructor "
                      "around BOTH operands, so it does not resolve — and "
                      "behaviourally the emitted expression still performs a "
                      "reduced-precision division on the unwrapped side, which is "
                      "precisely the loss of precision the issue reports.",
        "rationale": "REJECT from S2: the spec pins a SECOND application of "
                     "`mpfName` (with parens) around `intText q`, but the rival "
                     "emits `intText q` bare after the division sign, so the "
                     "equation fails for every q. Refuted at (1, 2), the smallest "
                     "rational and the point the closest-near-miss argument is "
                     "about.",
        "witness": _witness(1, 2),
    },

    # ---- S1: numerator operand left unwrapped (the mirror near miss) --------
    {
        "id": "drop-num-wrap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '  let func := mpfName\n'
            '  intText p ++ "/".toList ++ func ++ "(".toList ++ intText q\n'
            '    ++ ")".toList'),
        "refinement": "the mirror of the previous rival: a faithful patch "
                      "wrapping only the denominator renders a bare numerator "
                      "divided by the constructor applied to the denominator. The "
                      "hidden observation demands both wrapped, so it does not "
                      "resolve.",
        "rationale": "REJECT from S1: the spec pins `mpfName ++ \"(\"` BEFORE "
                     "`intText p` and a closing paren after it, but the rival "
                     "emits the numerator text bare. Refuted at (0, 5) — a "
                     "distinct point that additionally exercises a zero "
                     "numerator, where the unwrapped operand is a single "
                     "character.",
        "witness": _witness(0, 5),
    },

    # ---- S1+S2: neither operand wrapped — the pre-fix behavior ---------------
    {
        "id": "bare-division",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl('  intText p ++ "/".toList ++ intText q'),
        "refinement": "this IS the pre-fix behavior: the rendering falls back to "
                      "the generic textual quotient of the two integers, with no "
                      "backend constructor anywhere. The companion prepatch "
                      "artifact reproduces it and G-DIFF confirms the spec senses "
                      "it. The emitted expression evaluates the rational as an "
                      "ordinary reduced-precision division — the exact defect the "
                      "issue reports — so it does not resolve.",
        "rationale": "REJECT from S1 AND S2 together: neither operand is wrapped, "
                     "so the result is `intText p ++ \"/\" ++ intText q` and the "
                     "equation fails for all inputs. Refuted at (232, 3), the "
                     "multi-digit rational named in the issue, so the witness "
                     "probes the reported input rather than only the minimal one.",
        "witness": _witness(232, 3),
    },

    # ---- S3: operand ORDER transposed ---------------------------------------
    {
        "id": "swap-operands",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '  let func := mpfName\n'
            '  func ++ "(".toList ++ intText q ++ ")/".toList ++\n'
            '  func ++ "(".toList ++ intText p ++ ")".toList'),
        "refinement": "a faithful patch that wraps both operands but transposes "
                      "them renders the RECIPROCAL of the intended rational. The "
                      "hidden observation pins the operand order, and the emitted "
                      "expression evaluates to a numerically different value, so "
                      "it does not resolve.",
        "rationale": "REJECT from S3 (ordering): the spec pins `intText p` inside "
                     "the FIRST constructor application and `intText q` inside the "
                     "second; the rival transposes them, so the equation fails "
                     "whenever p ≠ q. Refuted at (7, 4), a point with p > q where "
                     "the transposition is observable and both operands are "
                     "single-digit but distinct.",
        "witness": _witness(7, 4),
    },

    # ---- S4: wrong wrapper text --------------------------------------------
    {
        "id": "wrong-ctor-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '  let func := "mpmath.mp".toList\n'
            '  func ++ "(".toList ++ intText p ++ ")/".toList ++\n'
            '  func ++ "(".toList ++ intText q ++ ")".toList'),
        "refinement": "a faithful patch naming a truncated wrapper renders a "
                      "structurally correct quotient of two wrapped operands whose "
                      "wrapper text is wrong. The hidden observation pins the "
                      "wrapper text exactly, so it does not resolve — and the "
                      "emitted expression would fail to evaluate at all, since the "
                      "truncated name is not bound in the evaluation backend.",
        "rationale": "REJECT from S4: the spec pins the wrapper to `mpfName` at "
                     "both operand positions; the rival uses a truncated name "
                     "(final character missing), so the equation fails for all "
                     "inputs. Value-level near miss with the whole structure "
                     "intact. Refuted at (2, 9), a distinct single-digit point.",
        "witness": _witness(2, 9),
    },

    # ---- S3: the division sign itself missing -------------------------------
    {
        "id": "no-slash",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            '  let func := mpfName\n'
            '  func ++ "(".toList ++ intText p ++ ")".toList ++\n'
            '  func ++ "(".toList ++ intText q ++ ")".toList'),
        "refinement": "a faithful patch omitting the division sign renders the two "
                      "wrapped operands juxtaposed, which is not a quotient at all "
                      "and is not even syntactically valid in the generated "
                      "evaluation code. The hidden observation pins the sign, so it "
                      "does not resolve.",
        "rationale": "REJECT from S3 (the joining operator): the spec interleaves "
                     "the division sign between the closing paren of the first "
                     "operand and the wrapper of the second; the rival closes the "
                     "first operand and immediately opens the second. Structural "
                     "near miss — both operands ARE correctly wrapped. Refuted at "
                     "(3, 10), which also exercises a two-digit denominator "
                     "against a one-digit numerator.",
        "witness": _witness(3, 10),
    },

    # ---- S1-S5 all at once: cheapest possible cheat -------------------------
    {
        "id": "empty-output",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl("  ([] : List Char)"),
        "refinement": "rendering nothing at all emits an empty expression for "
                      "every rational, which is trivially not the text the hidden "
                      "observation demands and would leave the generated "
                      "evaluation code malformed. Supporting cheapest cheat; does "
                      "not resolve.",
        "rationale": "REJECT: the result is empty while the spec's right-hand side "
                     "is a non-empty concatenation for every input (it always "
                     "contains at least the wrapper and the parens), so the "
                     "equation fails everywhere. Refuted at (5, 6), a distinct "
                     "point; the floor case that pins the spec as non-trivial.",
        "witness": _witness(5, 6),
    },

    # ---- S5: the `q` binder is IGNORED -------------------------------------
    {
        "id": "dup-numerator",
        "kind": "uniqueness",
        "expect": "reject",
        # BINDER-COVERAGE rival (see assessment): correct shape, correct wrapper,
        # correct order — but the SECOND operand re-reads the numerator, so `q`
        # never reaches the output. Refutes any suggestion that the spec's
        # dependence on `q` is untested.
        "module": _impl(
            '  let func := mpfName\n'
            '  func ++ "(".toList ++ intText p ++ ")/".toList ++\n'
            '  func ++ "(".toList ++ intText p ++ ")".toList'),
        "refinement": "a faithful patch substituting the numerator into both "
                      "operand positions renders a quotient of a value with "
                      "itself, i.e. the constant one, for every rational. The "
                      "hidden observation pins the denominator's text, and the "
                      "emitted expression evaluates to the wrong number, so it "
                      "does not resolve.",
        "rationale": "REJECT from S5 on the `q` binder: the spec pins the second "
                     "operand to `intText q`, but the rival emits `intText p` "
                     "there, so `q` is absent from the result. This rival exists "
                     "to VARY the `q` binder — without it a rival mishandling only "
                     "the denominator input would be untested. Refuted at (8, 13), "
                     "where p ≠ q and the two texts even differ in length.",
        "witness": _witness(8, 13),
    },

    # ---- S5: the `p` binder is IGNORED -------------------------------------
    {
        "id": "dup-denominator",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror binder-coverage rival: `p` never reaches the output.
        "module": _impl(
            '  let func := mpfName\n'
            '  func ++ "(".toList ++ intText q ++ ")/".toList ++\n'
            '  func ++ "(".toList ++ intText q ++ ")".toList'),
        "refinement": "the mirror: a faithful patch substituting the denominator "
                      "into both operand positions also renders the constant one, "
                      "losing the numerator entirely. The hidden observation pins "
                      "the numerator's text, so it does not resolve.",
        "rationale": "REJECT from S5 on the `p` binder: the spec pins the first "
                     "operand to `intText p`, but the rival emits `intText q` "
                     "there, so `p` is absent from the result. This rival exists to "
                     "VARY the `p` binder. Refuted at (11, 4), where the numerator "
                     "is the two-digit one — a point no other witness uses.",
        "witness": _witness(11, 4),
    },

    # ---- S5: BOTH binders ignored — echo the observed literal ---------------
    {
        "id": "hardcode-f2p",
        "kind": "uniqueness",
        "expect": "reject",
        # GROUNDING rival (see assessment): return the exact text the hidden
        # observation of this behavior checks, ignoring both inputs. This is the
        # mechanical demonstration that the postcondition is grounded in the
        # inputs rather than pinned to a constant answer key — the class the
        # sibling could only argue for in prose.
        "module": _impl(
            '  let _ := (p, q)\n'
            '  "mpmath.mpf(1)/mpmath.mpf(2)".toList'),
        "refinement": "a faithful patch returning a fixed rendering for every "
                      "rational happens to match the smallest-rational "
                      "observation while rendering every other rational as that "
                      "same wrong text. It would therefore make the emitted "
                      "evaluation code numerically wrong for all but one input, "
                      "and the broader numeric-solver observations of this "
                      "behavior (which exercise a different rational entirely) "
                      "fail, so it does not resolve.",
        "rationale": "REJECT from S5 on BOTH binders: the result is a constant, "
                     "while the spec pins it to a concatenation containing "
                     "`intText p` and `intText q`. Refuted at (3, 7) — a point "
                     "where the constant is wrong; note the witness would NOT be "
                     "available at the one input the constant was chosen to match, "
                     "which is exactly the point of the case. Demonstrates the "
                     "postcondition is GROUNDED (no constant echo satisfies it) "
                     "rather than an answer-key oracle.",
        "witness": _witness(3, 7),
    },

    # ---- S1+S2: ONE wrapper around the whole quotient -----------------------
    {
        "id": "wrap-once",
        "kind": "uniqueness",
        "expect": "reject",
        # The sharpest behavioural near miss: the text IS well-formed and DOES
        # mention the backend constructor, but it wraps the quotient rather than
        # each operand, so the division still happens before the constructor sees
        # it.
        "module": _impl(
            '  let func := mpfName\n'
            '  func ++ "(".toList ++ intText p ++ "/".toList ++ intText q\n'
            '    ++ ")".toList'),
        "refinement": "the sharpest near miss: a faithful patch applying the "
                      "backend constructor ONCE, around the whole quotient, "
                      "renders well-formed code that does mention the "
                      "high-precision constructor — but the quotient of the two "
                      "integers is formed FIRST, at the host language's reduced "
                      "precision, and only then handed to the constructor, so the "
                      "precision is already lost. The hidden observation pins two "
                      "separate constructor applications, so it does not resolve, "
                      "and the numeric-solver observation still returns a "
                      "reduced-precision result — the reported defect survives the "
                      "patch.",
        "rationale": "REJECT from S1 and S2 jointly: the spec pins the wrapper "
                     "applied TWICE, once per operand, with the division sign "
                     "OUTSIDE both applications; the rival applies it once with "
                     "the division sign inside. Every character of the wrapper is "
                     "present and the operands are in the right order — only the "
                     "nesting differs. Refuted at (4, 9), a point used by no other "
                     "witness.",
        "witness": _witness(4, 9),
    },

    # ---- S5: the operand's SIGN is dropped ----------------------------------
    {
        "id": "drop-sign",
        "kind": "uniqueness",
        "expect": "reject",
        # SIGN-LANE rival. Correct wrapper, correct order, correct nesting, and
        # correct on every NON-NEGATIVE input — but each operand is rendered from
        # its MAGNITUDE, so a negative numerator loses its minus sign. This is the
        # one part of the input domain no other rival here attacks: the eleven
        # `_witness` points are all non-negative, so before this case a rival
        # wrong only on negative operands went untested.
        "module": _impl(
            '  let mag (n : Int) : List Char := (toString n.natAbs).toList\n'
            '  mpfName ++ "(".toList ++ mag p ++ ")/".toList ++\n'
            '  mpfName ++ "(".toList ++ mag q ++ ")".toList'),
        "refinement": "a faithful patch that renders each operand from its "
                      "magnitude emits a structurally perfect quotient of two "
                      "wrapped operands whose SIGN is gone, so a negative "
                      "rational is rendered as its absolute value. The emitted "
                      "expression then evaluates to a number of the wrong sign — "
                      "a strictly worse defect than the reduced precision the "
                      "issue reports — so it does not resolve.",
        "rationale": "REJECT from S5 on the numerator's VALUE: the spec pins the "
                     "first operand to `intText p`, the signed decimal text, but "
                     "the rival emits the text of `p.natAbs`, which agrees with "
                     "`intText` exactly on the non-negative integers and differs "
                     "on every negative one. Refuted at (-3, 5). This case exists "
                     "because the sign of an operand is otherwise an unattacked "
                     "part of the domain: every other witness here sits at a "
                     "non-negative point, so a rival correct only up to sign would "
                     "have passed unnoticed. Its witness must CONDITION rather "
                     "than evaluate — see `_witness_signed` for the measured "
                     "reason the negative branch of the decimal conversion does "
                     "not reduce in the kernel.",
        "witness": _witness_signed(3, 3, 5),
    },
]

# ---------------------------------------------------------------------------
# Sibling -> lean accounting. The nagini battery has 13 SPEC cases (3 soundness
# positives, 1 admissibility, 2 mandatory frame-mutation rivals, 7 value-level
# uniqueness rivals) plus an EMPTY axiom lane. This bundle models the SAME single
# purely-functional core, so every value-level case has a counterpart; the two
# frame cases are vacuous on this carrier. Four rivals are ADDED to close binder
# and grounding coverage the sibling did not need. Every sibling case is recorded.
#
#   sibling case         -> here                    disposition
#   -----------------------------------------------------------------------
#   pos-single-expr      -> pos-inline-func         RE-EXPRESSED
#   pos-cheapest         -> pos-inline-func         MERGED (see below)
#   pos-reorder-build    -> pos-den-local           PORTED (re-proved)
#   (none)               -> pos-string-level        ADDED (carrier-level reshape)
#   admiss-f2p-shaped    -> admiss-smallest-input   RE-EXPRESSED
#   frame-append-p       -> (none)                  VACUOUS (no mutable input)
#   frame-setitem-q      -> (none)                  VACUOUS (no mutable input)
#   drop-den-wrap        -> drop-den-wrap           PORTED
#   drop-num-wrap        -> drop-num-wrap           PORTED
#   bare-division        -> bare-division           PORTED
#   swap-operands        -> swap-operands           PORTED
#   wrong-ctor-token     -> wrong-ctor-token        PORTED
#   no-slash             -> no-slash                PORTED
#   empty-output         -> empty-output            PORTED
#   (none)               -> dup-numerator           ADDED (varies the q binder)
#   (none)               -> dup-denominator         ADDED (varies the p binder)
#   (none)               -> hardcode-f2p            ADDED (grounding, both binders)
#   (none)               -> wrap-once               ADDED (behavioural near miss)
#   (none)               -> drop-sign               ADDED (sign lane, conditioned)
#   AXIOM_TESTS (0)      -> (none)                  DROPPED (G-AX's lane)
#
# MERGED (pos-cheapest into pos-inline-func): the sibling ships pos-cheapest as a
#   SECOND copy of pos-single-expr's module, standing in for the
#   ungrounded-oracle slot with the argument that the deep model is grounded in
#   the arguments so there is no wrong echo to build. Shipping the identical
#   module twice would cost a redundant build here and record nothing new, so the
#   argument is carried in pos-inline-func's rationale AND, better, made
#   MECHANICAL by the added `hardcode-f2p` rival: the cheapest constant echo is
#   exhibited as a rival and refuted with a witness, which is strictly stronger
#   evidence for the same claim than a duplicated positive.
# ADDED (pos-string-level): the sibling's structural variety comes from
#   associativity and write order over one carrier. This backend admits a sharper
#   difference — assembling the rendering in a different intermediate
#   representation entirely and converting once — which tests that the spec pins
#   the rendered TEXT and not an incidental concatenation shape.
# ADDED (dup-numerator, dup-denominator, hardcode-f2p): the seven sibling rivals
#   all keep both operands as honest functions of their own binder, attacking
#   only the wrapping/order/wrapper-text. So none of them varies an input binder
#   in the sense this backend's coverage tool means: a rival that mishandled ONLY
#   the numerator input, or only the denominator, or that ignored both, would
#   have gone unnoticed. These three close exactly that gap and are not
#   fabricated for an unmodeled behavior — they attack S5, a load-bearing part of
#   the same single postcondition equation.
# ADDED (wrap-once): the behaviourally sharpest rival available, and the one
#   whose faithful patch is most likely to look like a fix while leaving the
#   reported defect in place (the quotient is still formed at reduced precision
#   before the constructor is applied). The sibling's rival set jumps from
#   "one operand unwrapped" straight to "neither wrapped" and never probes the
#   nesting.
# VACUOUS (frame-append-p, frame-setitem-q): the sibling's two MANDATORY
#   frame-mutation rivals write into an input carrier held at partial permission
#   and must be rejected by the permission system. This carrier is referentially
#   transparent: the inputs are immutable `Int` values, there is no heap, no
#   aliasing, no permission and no mutable binder, so a mutating rival cannot be
#   written at all. No substitute probe is fabricated.
# KNOWN HOLE (divergence): the sibling carries NO divergence case. This lane was
#   previously recorded here as VACUOUS on the ground that "a non-terminating
#   implementation cannot be written" — corrected, because it can: a
#   `partial def implementation_mpfRational ... := implementation_mpfRational p q`
#   body is in-region, clears `variant_scope`, and elaborates (only the frozen
#   `rfl` fails). What blocks the case is the WITNESS half, not expressibility:
#   `partial` leaves the constant kernel-opaque with no equation lemma, so every
#   route measured (`unfold`; `decide` after unfolding the spec alone; `simp` with
#   the impl and both spec helpers; a `List.length` projection) fails on the RIVAL
#   side, the half that must succeed. A conditioned witness elaborates on the
#   rival but ALSO on gold (both exit 0) and so is `witness-vacuous`, with the
#   consistency probe unable to clear it on either side. Since the frozen
#   obligation attaches no termination requirement to the impl, such a rival is
#   rejected for a TOOLING reason rather than by the spec, so shipping it would
#   record a hollow `rejected`. Recorded as a hole in the spec's reach — the
#   battery is NOT complete in this direction. See the `assessment` block.
# DROPPED (AXIOM_TESTS): the axiom lane is G-AX's job and this gate ignores it.
#   The sibling's lane is empty anyway; this bundle likewise declares no `opaque`
#   callee and consumes no `axiom` — the wrapper name and the integer decimal text
#   are deep-model A-references, validated against the real callees out of band.
#
# ADDED (drop-sign): the sign of an operand was the one part of the input domain
#   nothing here attacked — every other witness sits at a non-negative point, so a
#   rival agreeing with the spec exactly on the non-negatives would have passed.
#   It is landed with a CONDITIONED witness because the negative branch of the
#   decimal conversion does not reduce in the kernel (measured; see the module
#   docstring). The earlier revision of this battery recorded that irreducibility
#   as a reason no negative-domain rival was needed, which was wrong on both
#   counts: such a rival exists and its witness builds.
#
# POINT SPREAD. The twelve reject witnesses probe TWELVE DISTINCT input points
# (pts=12), so no rival is refuted at another's input and every rationale's
# sub-domain claim is demonstrated at its own point:
#   (p, q) = (1, 2)     drop-den-wrap      S2   smallest rational
#            (0, 5)     drop-num-wrap      S1   zero numerator
#            (232, 3)   bare-division      S1+S2 the reported rational
#            (7, 4)     swap-operands      S3   p > q
#            (2, 9)     wrong-ctor-token   S4
#            (3, 10)    no-slash           S3   two-digit denominator
#            (5, 6)     empty-output       all
#            (8, 13)    dup-numerator      S5   q ignored
#            (11, 4)    dup-denominator    S5   p ignored (two-digit numerator)
#            (3, 7)     hardcode-f2p       S5   both ignored
#            (4, 9)     wrap-once          S1+S2 nesting
#            (-3, 5)    drop-sign          S5   NEGATIVE numerator (conditioned)
#   Across them p takes 11 distinct values (a negative, 0, one-digit, two-digit
#   and three-digit) and q takes 9, so NEITHER input binder is pinned at a single
#   value by the battery, and three rivals exist precisely to make each binder's
#   contribution individually observable.
#
# WITNESS DOMAIN. The eleven evaluating witnesses use non-negative literals; the
# twelfth (`drop-sign`) reaches a NEGATIVE numerator by CONDITIONING on the one
# fact the kernel will not compute. See the module docstring for the measured
# reason the negative branch of the integer-to-text conversion does not reduce
# under `decide`/`decide +kernel`/`rfl`/`simp`/`norm_num` in this workspace, and
# for why that is a reduction limit rather than a limit on what can be attacked.
AXIOM_TESTS = []
