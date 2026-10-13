"""properties.py — G-PBT falsification battery for astropy__astropy-14182 (lean).

NOT a Lean file: a record of adversarial cases the G-PBT gate executes. Each
case is a FULL ``Solution.lean`` variant produced by region surgery, so only
text inside an ``-- impl-start`` / ``-- impl-end`` region — or, where a case
legitimately re-proves, inside a ``-- proof-start`` / ``-- proof-end`` region —
differs from the frozen file. ``markers.same_spec`` therefore holds by
construction, every ``theorem correct_<name>`` STATEMENT stays byte-identical,
and a rejection is attributable to the postcondition rather than to a tampered
spec. No case introduces an ``axiom``, a helper ``theorem``/``lemma``, a
``sorry``/``admit``, or ``native_decide``.

DEFENDED SURFACE
----------------
This bundle models TWO obligations, one per independently-observable position in
the fixed-width layout that depends on how many header rows there are.

(1) ``problem_spec_rstWrap (numHeaderRows : Nat) (lines : List String)
     (result : List String)``

        result = [lines.getD numHeaderRows ""] ++ lines
                 ++ [lines.getD numHeaderRows ""]

    One equality, but it carries three independent obligations at once, and each
    is attacked separately below:

      a. WHICH line is copied to bracket the output — the line at position
         ``numHeaderRows``, i.e. a value GROUNDED in the input sequence and in
         the count binder. Not a constant, and not a synthesisable sentinel.
      b. THAT it is copied at BOTH ends — the leading and the trailing copy are
         separate conjuncts of the single list equality.
      c. THAT the middle is ``lines`` VERBATIM — every other element is the
         input element in its original order and position.

    Input binders: ``numHeaderRows`` and ``lines``. The obligation is unguarded
    (no precondition hypothesis), so the behavior is total: ``getD`` supplies the
    out-of-range read, and the desired behavior is pinned at every count.

(2) ``problem_spec_rstDataStart (numHeaderRows : Nat) (result : Nat)``

        result = 2 + numHeaderRows

    The position is a CONSTANT AFFINE function of the count, pinned at every
    count rather than at the historical single-header-row value. Sole input
    binder: ``numHeaderRows``. Also unguarded.

For the historical single-header-row case the two positions reduce to ``1`` and
``3``; the whole content of the change is that they must track the count instead,
so every rival below is refuted at a count OTHER than 1 unless it is wrong at
count 1 too (the two off-by-one / structural rivals are).

ADVERSARIAL READ OF THE CLASSES ON THIS CARRIER
-----------------------------------------------
  * PARTIAL-DOMAIN (the actual differential) — APPLIES, and is the core of the
    battery. ``weak-wrap-const-position`` and ``weak-offset-const`` each pin only
    the single-header-row sub-domain, agreeing with the frozen spec exactly at
    count 1 and diverging at every other count. Ports the nagini
    ``frame-const-1`` / ``offset-const-3`` pair.

  * UNGROUNDED-ORACLE ECHO — APPLIES. ``weak-wrap-ungrounded-sep`` brackets the
    output with a synthesised constant string instead of reading the input
    sequence at the counted position. Because clause (a) is grounded in
    ``lines`` and ``numHeaderRows`` rather than in an answer key, no constant can
    discharge it, so the rival must reject at any input whose counted line is not
    that constant. Ports the nagini ``wrong-const-echo`` argument; the grounded
    positive control that pairs with it (nagini ``honest-cheapest``) is
    ``pos-wrap-inline-read``, the cheapest faithful shape, which still has to
    perform the input read.

  * STRUCTURAL / FRAMING — APPLIES, and has no nagini counterpart because
    nagini's sequence equality was discharged as one opaque ``PSeq`` term.
    ``weak-wrap-single-bracket`` copies the counted line only at the leading end,
    attacking clause (b); ``weak-wrap-clobber-passthrough`` overwrites one
    pass-through element with the bracketing line, attacking clause (c). Both are
    added on this carrier's terms rather than ported.

  * OFF-BY-ONE NEAR-MISS — APPLIES. ``weak-offset-near-miss`` lands one position
    short of the pinned affine value: wrong at EVERY count, including count 1
    where the constant-pin rival agrees with the spec. Ports the nagini
    ``offset-off-by-one`` supporting case, and is refuted at a count where the
    other offset rival is indistinguishable from gold, so the two do not share a
    witness.

  * UNGUARDED-DOMAIN / DEFAULT READ — APPLIES, no nagini counterpart. The
    sibling's precondition required the block to be longer than the count, so the
    over-the-end domain was excluded by hypothesis and had no case. Here the
    obligation is unguarded, which makes ``getD``'s default part of the specified
    behavior: ``weak-wrap-oor-sentinel`` reads the counted position faithfully
    while in range and substitutes its own sentinel past the end. It is the only
    case refuted at an out-of-range point, and it is what turns the header's
    totality claim from an assertion into a demonstration.

  * UNIVERSALITY SPIKE — APPLIES, no nagini counterpart. Every other rival here
    is wrong on a whole half-line of counts, so a spec that pinned the position
    only at a few sampled counts would still catch them. ``weak-offset-spike``
    agrees with the frozen spec at every count but one, which separates "pinned
    at every count" from "pinned where the battery happened to look".

  * FRAME / PERMISSION MUTATION — VACUOUS, deliberately NOT ported. The nagini
    sibling's two mandatory probes (``frame-mutate-block``,
    ``frame-mutate-headers``) write through an input held at a read-only half
    permission and must fail for INSUFFICIENT PERMISSION. This carrier is
    referentially transparent: inputs carry no permission, there is no aliasing,
    and no store-through-an-argument is expressible, so neither rival has an
    instance and neither has a discriminating witness. Demonstrated rather than
    asserted: the closest expressible analogue — rebind the sequence locally,
    ``List.set`` the counted position, then read the bracketing line back out of
    the mutated copy — was built and it VERIFIES, because writing a position the
    value already occupies is provably the identity (``List.set_getElem_self`` in
    range, ``List.set_eq_of_length_le`` past the end). A probe that cannot fail is
    not a falsification case, so there is nothing here to reject and no
    substitute is fabricated. (``weak-wrap-clobber-passthrough`` is NOT that
    substitute: it is refuted by the postcondition's pass-through clause, which
    is a value obligation the frozen spec states outright, not by a permission
    system.)

  * DIVERGENCE / NON-TERMINATION — nothing to port: the nagini sibling carries no
    ``diverge-*`` / ``nonterm-*`` / ``weak-diverge`` case. On this backend the
    class is in any event vacuous, because ``implementation_rstWrap`` and
    ``implementation_rstDataStart`` are total Lean ``def``s and a diverging
    implementation cannot be written at all. This is the one disposition where
    "vacuous" is the honest word rather than a hidden spec hole.

  * CONTROL-FLOW-EFFECT / VALUE-DOUBLE-MASK — N/A, for the reason the nagini
    sibling gives and which survives the port: both modeled behaviors are pure
    value computations with no raise/return path, and the postconditions pin the
    ENTIRE returned sequence and the whole scalar rather than an index-via-value
    proxy that could drop disagreeing positions.

BINDER COVERAGE
---------------
``numHeaderRows`` — varied across the reject witnesses at 3, 1, 2, 4, 3 (obligation
1) and 3, 1, 7 (obligation 2). It is load-bearing in several distinct ways rather
than at one arity: ``weak-wrap-const-position`` and ``weak-offset-const`` are
refuted only at counts ``≠ 1`` (they are exactly correct at 1);
``weak-offset-near-miss`` is refuted AT count 1, where the constant rival agrees
with gold, so the affine pin is demonstrated at the historical value too;
``weak-wrap-clobber-passthrough`` is refuted at count 4 precisely because at
count 0 the clobber would coincide with the identity, so that rival's
wrongness is a function of the count and not of the sequence alone; and
``weak-offset-spike`` is refuted at count 7, where BOTH other offset rivals are
indistinguishable from gold, so no two offset cases share a refutation point.

``lines`` — varied in length (3, 4, 5, 6, 2) and in content across the
obligation-1 witnesses, and varied against the count in BOTH directions: four
witnesses put the counted position in range, while ``weak-wrap-oor-sentinel``
puts it past the end (count 3, two elements), so the length is not merely
decorative but decides which half of the total read is under test. The binder is
made load-bearing by ``weak-wrap-ungrounded-sep``, whose refutation depends on
nothing but the counted element of ``lines`` differing from a synthesised
constant, and by ``weak-wrap-clobber-passthrough``, whose refutation depends on
an element of ``lines`` OTHER than the counted one. A rival that read the right
position but corrupted the pass-through, or that ignored ``lines`` entirely, is
caught.

WITNESSES
---------
On a tactic-proof backend "did not verify" is the DEFAULT outcome of reshaping an
implementation: the frozen scripts are ``rfl`` after an ``unfold``, so ANY
reshape — correct or wrong — breaks them, and a rejection on its own attributes
nothing to the spec. Every ``expect="reject"`` case therefore carries a Lean
snippet proving the rival CONTRADICTS the frozen spec predicate at one concrete
input. All inputs are literal (small ``Nat``s and short string lists), so each
witness closes by ``decide`` with no hypothesis binder — nothing is conditioned
on, so there are no assumptions that could be jointly unsatisfiable. Each was
checked by hand, before submission, to ELABORATE against its own rival and to
FAIL against the frozen solution, so it discriminates rather than asserting a
tautology.

AXIOM LANE
----------
EMPTY. This bundle's ``axioms`` region declares nothing (both modeled quantities
are pure functions of the inputs; the rendered sequence enters as a direct input
observation rather than being recomputed), and the nagini sibling's
``AXIOM_TESTS`` is likewise empty. The axiom lane belongs to G-AX regardless;
this gate ignores it.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-14182"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is the FULL body of one impl region or the FULL tactic
# body of one proof region, so every replacement lands entirely inside the
# region it means to edit. Uniqueness is asserted at import time, so the
# manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------
_IMPL_WRAP = (
    "  let idx := numHeaderRows\n"
    "  let sep := lines.getD idx \"\"\n"
    "  let mut out := [sep] ++ lines ++ [sep]\n"
    "  return out\n"
)
_IMPL_OFFSET = (
    "  return 2 + numHeaderRows\n"
)
_PROOF_WRAP = (
    "  intro numHeaderRows lines\n"
    "  unfold problem_spec_rstWrap implementation_rstWrap\n"
    "  rfl\n"
)
_PROOF_OFFSET = (
    "  intro numHeaderRows\n"
    "  unfold problem_spec_rstDataStart implementation_rstDataStart\n"
    "  rfl\n"
)

for _a in (_IMPL_WRAP, _IMPL_OFFSET, _PROOF_WRAP, _PROOF_OFFSET):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drift / not unique: {_a!r}")


def _wrap_impl(body, base=None):
    return _swap(base if base is not None else _BASE, _IMPL_WRAP, body)


def _offset_impl(body, base=None):
    return _swap(base if base is not None else _BASE, _IMPL_OFFSET, body)


# ===========================================================================
# Re-authored proof bodies. The `theorem correct_<name>` STATEMENT is untouched
# in every one of these; only the tactic script between `-- proof-start` and
# `-- proof-end` changes, which is what a case that legitimately re-proves a
# reshaped implementation must do. No `have` below is a new top-level
# declaration, and none of them assumes anything: each is discharged by
# evaluation or by Mathlib's linear-arithmetic decision procedure.
# ===========================================================================

# The frozen `rfl` closes the inlined wrap reshape unchanged (the two reads
# reduce to the same term), so `pos-wrap-inline-read` needs no re-proof.

# `pos-wrap-build-by-cons` prepends the bracketing line with `::` after the
# trailing copy is already appended. Definitionally the same list, but the
# monadic `let mut` rebind leaves a `pure` the frozen bare `rfl` does not see
# through, so the script names it.
_PROOF_WRAP_CONS = (
    "  intro numHeaderRows lines\n"
    "  unfold problem_spec_rstWrap implementation_rstWrap\n"
    "  simp [Id.run, pure]\n"
)

# `pos-offset-successor` reaches the position by two successive increments of the
# count rather than by adding the literal offset to it. Equal as integers but not
# syntactically, so the goal is stated and handed to `omega`.
_PROOF_OFFSET_SUCC = (
    "  intro numHeaderRows\n"
    "  unfold problem_spec_rstDataStart implementation_rstDataStart\n"
    "  show numHeaderRows + 1 + 1 = 2 + numHeaderRows\n"
    "  omega\n"
)

# ADMISSIBILITY. The frozen obligations carry no precondition hypothesis, so the
# nagini precondition-admission probes have no binder to attack; the honest
# analogue on this carrier discharges each spec predicate at the ground inputs
# the behavior is actually exercised on — the historical single-header-row shape
# and the multi-header-row shape the F2P round-trip uses — by EVALUATION, and
# then closes the frozen obligation verbatim. If a ground instance could not be
# discharged, the obligation would be unsatisfiable at an input it must admit,
# which is this carrier's form of PRECOND-TOO-STRONG / a vacuous obligation.
# The ground instances name the expected output as a LITERAL list rather than as
# `implementation_rstWrap <input>`. Writing the second argument as an application
# of the implementation would make each `have` an instance of `correct_rstWrap`
# itself — restating the obligation the case is supposed to probe independently,
# and discharged by the very evaluation the frozen `rfl` already performs. Spelled
# out, the `have` is a claim about the SPEC alone (`implementation_rstWrap` does
# not appear in it), so it fails if the postcondition admits the wrong bracketed
# sequence at that count, which is the admissibility question.
_PROOF_WRAP_ADMISS = (
    "  have _ground_single : problem_spec_rstWrap 1 [\"h0\", \"==\", \"d0\"]\n"
    "      [\"==\", \"h0\", \"==\", \"d0\", \"==\"] := by\n"
    "    unfold problem_spec_rstWrap\n"
    "    decide\n"
    "  have _ground_three : problem_spec_rstWrap 3 [\"h0\", \"h1\", \"h2\", \"==\", \"d0\"]\n"
    "      [\"==\", \"h0\", \"h1\", \"h2\", \"==\", \"d0\", \"==\"] := by\n"
    "    unfold problem_spec_rstWrap\n"
    "    decide\n"
    + _PROOF_WRAP
)
_PROOF_OFFSET_ADMISS = (
    "  have _ground_single : problem_spec_rstDataStart 1 3 := by\n"
    "    unfold problem_spec_rstDataStart\n"
    "    decide\n"
    "  have _ground_three : problem_spec_rstDataStart 3 5 := by\n"
    "    unfold problem_spec_rstDataStart\n"
    "    decide\n"
    # Deliberately NO `problem_spec_rstDataStart 3 (implementation_rstDataStart 3)`
    # instance here: that is `correct_rstDataStart` specialised to one count, so it
    # restates the frozen obligation instead of probing the spec independently. The
    # two literal pins above are claims about the postcondition alone.
    + _PROOF_OFFSET
)


# ===========================================================================
# SPEC CASES
# ===========================================================================
SPEC_TESTS = [

    # =====================================================================
    # SOUNDNESS POSITIVES — structurally different but CORRECT implementations
    # that MUST verify. If a faithful reshape cannot satisfy the frozen
    # obligation, the spec is SPEC-TOO-STRONG. Each keeps its theorem statement
    # byte-identical and re-proves only where the reshape moves the goal out of
    # the frozen script's reach.
    # =====================================================================

    # Ports the nagini grounded-oracle positive control (`honest-cheapest`) and
    # its direct-index positive (`pos-frame-direct-n`), which collapse into one
    # shape here: dropping the intermediate bindings leaves the cheapest possible
    # faithful implementation, and it STILL has to read the input sequence at the
    # counted position. There is no shortcut for a grounded obligation.
    {
        "id": "pos-wrap-inline-read",
        "kind": "soundness",
        "expect": "verify",
        "module": _wrap_impl(
            "  return [lines.getD numHeaderRows \"\"] ++ lines"
            " ++ [lines.getD numHeaderRows \"\"]\n"),
        "rationale": "the cheapest faithful shape: no intermediate position or "
                     "bracketing-line binding, the counted read performed inline "
                     "at both ends, and no mutable accumulator. Same value at "
                     "every input, so the sole clause of "
                     "`problem_spec_rstWrap` still holds and the frozen script "
                     "closes it unchanged. Must verify, else SPEC-TOO-STRONG. "
                     "Doubles as the grounded-oracle control: because the "
                     "bracketing line is pinned to `lines.getD numHeaderRows \"\"` "
                     "— a function of both input binders, fully unfolded — even "
                     "the cheapest implementation must perform the input read, "
                     "which is what leaves no room for the echo cheat that "
                     "`weak-wrap-ungrounded-sep` attempts.",
    },

    # A reshape that builds the result in a different ORDER: the trailing copy is
    # appended first and the leading copy is then prepended by `::`, rather than
    # both being concatenated in one expression. Attacks the risk that the spec
    # accidentally pins a construction shape rather than a value.
    {
        "id": "pos-wrap-build-by-cons",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _wrap_impl(
                "  let sep := lines.getD numHeaderRows \"\"\n"
                "  let mut out := lines ++ [sep]\n"
                "  out := sep :: out\n"
                "  return out\n"),
            _PROOF_WRAP, _PROOF_WRAP_CONS),
        "rationale": "builds the same list in a different ORDER — trailing copy "
                     "appended first, leading copy prepended by `::` through a "
                     "rebound accumulator — so the value is identical while the "
                     "construction shape is not. Confirms the spec pins a VALUE "
                     "and not a syntactic build, i.e. that the reject cases below "
                     "reject for being wrong rather than for being reshaped. "
                     "Re-proved because the accumulator rebind leaves a monadic "
                     "`pure` the frozen bare `rfl` does not see through; closed by "
                     "`simp [Id.run, pure]`, no new declaration and nothing "
                     "assumed. Must verify, else SPEC-TOO-STRONG.",
    },

    # Ports the nagini `pos-offset-reassoc`: the same position reached by a
    # different-but-equal arithmetic expression.
    {
        "id": "pos-offset-successor",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _offset_impl(
                "  let mut k := numHeaderRows\n"
                "  k := k + 1\n"
                "  k := k + 1\n"
                "  return k\n"),
            _PROOF_OFFSET, _PROOF_OFFSET_SUCC),
        "rationale": "reaches the pinned position by two successive increments of "
                     "the count instead of adding the offset to it: the same "
                     "natural number at every count, so "
                     "`result = 2 + numHeaderRows` still holds. Equal but not "
                     "syntactically so, hence the goal is stated and closed by "
                     "`omega` (a Mathlib decision procedure, no new declaration, "
                     "nothing assumed). Must verify, else the spec pins an "
                     "arithmetic FORM rather than the position — SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligations are SATISFIABLE (non-vacuous) at the
    # inputs the behavior is actually exercised on. Ports the nagini
    # `admiss-frame-n3` / `admiss-offset-n3` pair, re-expressed: with no
    # precondition hypothesis to establish, the analogue is that each spec
    # predicate can be DISCHARGED BY EVALUATION at the historical
    # single-header-row shape and at the multi-header-row shape.
    # =====================================================================
    {
        "id": "admiss-ground-shapes",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _PROOF_WRAP, _PROOF_WRAP_ADMISS),
            _PROOF_OFFSET, _PROOF_OFFSET_ADMISS),
        "rationale": "both postconditions are discharged by evaluation at ground "
                     "inputs — the historical single-header-row shape (count 1, "
                     "where the two positions take their historical values) and "
                     "the multi-header-row shape the F2P round-trip exercises "
                     "(count 3) — and then the frozen obligations are closed "
                     "verbatim. Every ground fact names its EXPECTED RESULT as a "
                     "literal (the bracketed sequence spelled out; the positions 3 "
                     "and 5) rather than as an application of "
                     "`implementation_*`, so no `have` here is an instance of the "
                     "`correct_*` theorem this case sits inside: each is a claim "
                     "about the spec predicate alone, and it fails if the "
                     "postcondition admits the wrong sequence or position at that "
                     "count. Verifies, else the modeled behavior is unsatisfiable "
                     "at an input it must admit, or the postconditions are vacuous "
                     "at the very counts the change turns on. Nothing is assumed: "
                     "every ground fact is a `have` inside a tactic body, both "
                     "theorem statements are byte-identical, and no declaration is "
                     "added.",
    },

    # =====================================================================
    # UNIQUENESS RIVALS — wrong implementations sharing the frozen spec, which
    # MUST be rejected. Each carries the refinement argument that its faithful
    # real patch would NOT resolve the F2P (so a verifying rival would be a true
    # verify-does-not-imply-resolve break, not an artifact) and a refutation
    # witness pinning the violation at one concrete input.
    # =====================================================================

    # THE DIFFERENTIAL on obligation 1. Ports the nagini `frame-const-1`: pins
    # the bracketing line to the historical constant position instead of tracking
    # the count.
    {
        "id": "weak-wrap-const-position",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrap_impl(
            "  let idx := 1\n"
            "  let sep := lines.getD idx \"\"\n"
            "  let mut out := [sep] ++ lines ++ [sep]\n"
            "  return out\n"),
        "refinement": "this is the historical behavior: the bracketing line is "
                      "taken from the fixed position 1, which is the correct "
                      "position only when there is exactly one header row. The "
                      "F2P renders a table with three header rows, where position "
                      "1 holds a header row of text rather than the column-rule "
                      "line, so the emitted table is bracketed with a header row "
                      "and the round-trip comparison against the expected output "
                      "lines fails. A faithful patch keeping the constant position "
                      "would NOT resolve — and it is precisely the state of the "
                      "code before the change, which is why the F2P fails there.",
        "rationale": "REJECT from clause (a) of `problem_spec_rstWrap`: the "
                      "bracketing element is pinned to "
                      "`lines.getD numHeaderRows \"\"`, so at any count other than "
                      "1 the constant position selects a different element and the "
                      "list equality fails at both bracket ends. Refuted at count "
                      "3 (the multi-header-row shape), where the counted line and "
                      "the line at position 1 are distinct — the exact sub-domain "
                      "the change is about. Verifying here would be SPEC-TOO-WEAK "
                      "in the most consequential way available: the spec would "
                      "admit the historical behavior.",
        "witness": (
            "example : ¬ problem_spec_rstWrap 3 [\"h0\", \"h1\", \"h2\", \"==\", \"d0\"]\n"
            "    (implementation_rstWrap 3 [\"h0\", \"h1\", \"h2\", \"==\", \"d0\"]) := by\n"
            "  unfold problem_spec_rstWrap implementation_rstWrap\n"
            "  decide\n"),
    },

    # UNGROUNDED-ORACLE ECHO. Ports the nagini `wrong-const-echo`.
    {
        "id": "weak-wrap-ungrounded-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrap_impl(
            "  let sep := \"\"\n"
            "  let mut out := [sep] ++ lines ++ [sep]\n"
            "  return out\n"),
        "refinement": "bracketing the output with a synthesised constant ignores "
                      "the rendered sequence entirely: the emitted table would be "
                      "framed with a line that is not the column-rule line, so it "
                      "is neither the expected output nor even re-readable in the "
                      "format. Every F2P and P2P round-trip comparison against "
                      "expected output lines fails, so a faithful patch emitting a "
                      "literal in place of the read line would NOT resolve.",
        "rationale": "REJECT from clause (a), on the GROUNDING half rather than "
                      "the position half. The bracketing value is pinned to a "
                      "function of both input binders, not to an opaque answer key, "
                      "so no constant can discharge it: the equality fails at any "
                      "input whose counted line differs from the constant. Refuted "
                      "at count 1 — the historical count, where "
                      "`weak-wrap-const-position` agrees with the frozen spec "
                      "exactly — so this rival gets its own input point and its "
                      "wrongness is demonstrated on `lines` alone rather than on "
                      "the count. If it verified, an implementation could satisfy "
                      "the spec without reading its input: SPEC-TOO-WEAK.",
        "witness": (
            "example : ¬ problem_spec_rstWrap 1 [\"h0\", \"==\", \"d0\"]\n"
            "    (implementation_rstWrap 1 [\"h0\", \"==\", \"d0\"]) := by\n"
            "  unfold problem_spec_rstWrap implementation_rstWrap\n"
            "  decide\n"),
    },

    # STRUCTURAL: only one of the two bracket copies. No nagini counterpart — the
    # sibling discharged its sequence equality as one opaque term, so the two
    # ends were never attacked separately.
    {
        "id": "weak-wrap-single-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrap_impl(
            "  let idx := numHeaderRows\n"
            "  let sep := lines.getD idx \"\"\n"
            "  let mut out := [sep] ++ lines\n"
            "  return out\n"),
        "refinement": "reading the counted position correctly but bracketing only "
                      "the top leaves the emitted table without its closing rule "
                      "line. The format requires the table to be closed, so the "
                      "output has one line too few and does not equal the expected "
                      "output in the F2P round-trip (nor is it re-readable). A "
                      "faithful patch that emitted only the leading copy would NOT "
                      "resolve, at ANY header-row count including the historical "
                      "one.",
        "rationale": "REJECT from clause (b): the leading and trailing copies are "
                      "independent conjuncts of the single list equality, so an "
                      "implementation that satisfies one and drops the other must "
                      "still fail — the two lists differ in LENGTH at every input. "
                      "Refuted at count 2, a third distinct count, on a sequence "
                      "whose counted read this rival performs CORRECTLY: the "
                      "rejection is attributable to the framing structure alone and "
                      "not to a mis-selected position, which is what makes it a "
                      "genuinely different rival from the two above rather than a "
                      "witness-sharing near-duplicate.",
        "witness": (
            "example : ¬ problem_spec_rstWrap 2 [\"h0\", \"h1\", \"==\", \"d0\"]\n"
            "    (implementation_rstWrap 2 [\"h0\", \"h1\", \"==\", \"d0\"]) := by\n"
            "  unfold problem_spec_rstWrap implementation_rstWrap\n"
            "  decide\n"),
    },

    # STRUCTURAL: the pass-through is not verbatim. Also no nagini counterpart.
    # NOTE this is NOT a stand-in for the omitted permission-mutation rivals: it
    # is refuted by a value clause the frozen spec states outright, and nothing
    # here writes through an input.
    {
        "id": "weak-wrap-clobber-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrap_impl(
            "  let idx := numHeaderRows\n"
            "  let sep := lines.getD idx \"\"\n"
            "  let mut out := [sep] ++ lines.set 0 sep ++ [sep]\n"
            "  return out\n"),
        "refinement": "brackets the output correctly but replaces the first "
                      "rendered line with a copy of the column-rule line, so one "
                      "header row is lost from the emitted table. The F2P compares "
                      "the emitted lines against an expected table in which every "
                      "header row is present, and the reader would recover the "
                      "wrong column names, so a faithful patch that overwrote a "
                      "rendered line while bracketing would NOT resolve.",
        "rationale": "REJECT from clause (c): the middle of the result is pinned to "
                      "`lines` VERBATIM, element for element in order, so replacing "
                      "any element breaks the equality even when both bracket "
                      "copies are the correct counted line. Refuted at count 4, a "
                      "fourth distinct count, and deliberately not at count 0 — "
                      "where overwriting position 0 with the counted line is the "
                      "IDENTITY and this rival coincides with gold. So the witness "
                      "point is chosen where the rival is actually wrong, and the "
                      "case demonstrates a dependence on an element of `lines` "
                      "OTHER than the counted one, which no other rival probes.",
        "witness": (
            "example : ¬ problem_spec_rstWrap 4 [\"h0\", \"h1\", \"h2\", \"h3\", \"==\", \"d0\"]\n"
            "    (implementation_rstWrap 4 [\"h0\", \"h1\", \"h2\", \"h3\", \"==\", \"d0\"]) := by\n"
            "  unfold problem_spec_rstWrap implementation_rstWrap\n"
            "  decide\n"),
    },

    # THE DIFFERENTIAL on obligation 2. Ports the nagini `offset-const-3`.
    {
        "id": "weak-offset-const",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _offset_impl(
            "  return 3\n"),
        "refinement": "this is the historical behavior: the first data position is "
                      "fixed at the value that is correct only for a single header "
                      "row. The F2P parses a table with three header rows, whose "
                      "first data line sits two positions further down, so the "
                      "reader slices from inside the header block and recovers the "
                      "wrong rows, units and dtypes; its assertions fail. A "
                      "faithful patch keeping the constant would NOT resolve — it "
                      "is the pre-change state of the code.",
        "rationale": "REJECT from the sole clause of `problem_spec_rstDataStart`: "
                      "the position is pinned as `2 + numHeaderRows`, an affine "
                      "function of the count, so a constant satisfies it at exactly "
                      "one count and fails at every other. Refuted at count 3, the "
                      "multi-header-row shape the change is about. Verifying here "
                      "would mean the spec admits the historical behavior on the "
                      "parsing side: SPEC-TOO-WEAK.",
        "witness": (
            "example : ¬ problem_spec_rstDataStart 3 (implementation_rstDataStart 3) := by\n"
            "  unfold problem_spec_rstDataStart implementation_rstDataStart\n"
            "  decide\n"),
    },

    # OUT-OF-RANGE DOMAIN on obligation 1. No nagini counterpart: the sibling's
    # precondition required `len(block) > n`, so the over-the-end domain was
    # excluded by hypothesis there and simply does not exist as a case. Here the
    # obligation is UNGUARDED, so `getD`'s default is part of the specified
    # behavior and is its own attackable sub-domain — one that every rival above
    # leaves untouched, since all four are refuted at in-range points.
    {
        "id": "weak-wrap-oor-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrap_impl(
            "  let sep := if numHeaderRows < lines.length"
            " then lines.getD numHeaderRows \"\" else \"=\"\n"
            "  let mut out := [sep] ++ lines ++ [sep]\n"
            "  return out\n"),
        "refinement": "reads the counted position correctly whenever it is in "
                      "range and otherwise substitutes a synthesised rule-like "
                      "line. A faithful patch shaped this way would silently "
                      "invent a bracketing line for any count the rendered "
                      "sequence does not reach instead of propagating the "
                      "renderer's own total-read behavior, so the emitted table "
                      "would not equal the expected output on that domain and it "
                      "would NOT resolve there.",
        "rationale": "REJECT from clause (a) on the DEFAULT half of the read. "
                      "Because the obligation carries no precondition bounding "
                      "the count by the sequence length, `lines.getD "
                      "numHeaderRows \"\"` pins the over-the-end result too, and "
                      "the spec is violated by any impl that substitutes its own "
                      "sentinel there. Refuted at count 3 against a two-element "
                      "sequence — a point NO other rival reaches, since the four "
                      "above are all refuted in range. This is the sub-domain the "
                      "unguarded totality claim in the header rests on: without "
                      "this case that claim is asserted and never demonstrated.",
        "witness": (
            "example : ¬ problem_spec_rstWrap 3 [\"h0\", \"d0\"]\n"
            "    (implementation_rstWrap 3 [\"h0\", \"d0\"]) := by\n"
            "  unfold problem_spec_rstWrap implementation_rstWrap\n"
            "  decide\n"),
    },

    # NEAR-MISS on obligation 2. Ports the nagini `offset-off-by-one`. Tracks the
    # count — so it defeats a spec that only checked count-dependence — but lands
    # one position short at EVERY count, including the historical one.
    {
        "id": "weak-offset-near-miss",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _offset_impl(
            "  return 1 + numHeaderRows\n"),
        "refinement": "one position short of the first data line, the parser "
                      "begins reading at the closing rule line of the header "
                      "block rather than at the first data row. The base reader "
                      "then mis-parses the table body, so the F2P assertions on "
                      "the recovered rows fail; a faithful patch off by one would "
                      "NOT resolve, and unlike the constant rival it would fail "
                      "the existing single-header-row round-trips as well.",
        "rationale": "REJECT from the same clause, but on the OFFSET rather than "
                      "the count-dependence: `1 + numHeaderRows` does track the "
                      "count, so it would survive a spec that merely required "
                      "count-sensitivity, and it is nonetheless wrong at every "
                      "count. Refuted at count 1 — the historical count, where "
                      "`weak-offset-const` is exactly correct and therefore "
                      "indistinguishable from gold — so this rival needs and gets "
                      "its own input point rather than sharing the other's. "
                      "Together the two witnesses pin the affine position at a "
                      "count where the constant is right and at one where it is "
                      "wrong.",
        "witness": (
            "example : ¬ problem_spec_rstDataStart 1 (implementation_rstDataStart 1) := by\n"
            "  unfold problem_spec_rstDataStart implementation_rstDataStart\n"
            "  decide\n"),
    },

    # SINGLE-COUNT SPIKE on obligation 2. No nagini counterpart. Both offset
    # rivals above are wrong on a whole half-line of counts, so either would be
    # caught by a spec that merely pinned the position at two or three sampled
    # counts. This one agrees with the frozen spec at EVERY count but one, which
    # is the weakest possible perturbation of the affine pin and the case that
    # distinguishes "pinned at every count" from "pinned where the battery looked".
    {
        "id": "weak-offset-spike",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _offset_impl(
            "  if numHeaderRows == 7 then return 99 else return 2 + numHeaderRows\n"),
        "refinement": "a faithful patch shaped this way computes the first data "
                      "position correctly for every header-row count the existing "
                      "tests exercise and mislocates it for one specific count, so "
                      "a table with that many header rows is sliced from the wrong "
                      "line and its rows, units and types are recovered wrongly. "
                      "It would pass the F2P and the P2P round-trips while being "
                      "wrong on the domain the change generalises to, so it would "
                      "NOT resolve the issue as stated: the whole point is that the "
                      "position tracks the count at EVERY count.",
        "rationale": "REJECT from the sole clause of `problem_spec_rstDataStart`, "
                      "on UNIVERSALITY rather than on the constant or the offset. "
                      "The obligation is quantified over all counts, so agreeing "
                      "with `2 + numHeaderRows` everywhere except one point still "
                      "violates it. Refuted at count 7 — a fifth distinct count, "
                      "and one no other case in the battery names — which is why "
                      "this rival cannot share a witness with either offset rival "
                      "above: both of those are exactly correct at 7. Verifying "
                      "here would mean the spec pins the position only at the "
                      "counts someone thought to sample: SPEC-TOO-WEAK.",
        "witness": (
            "example : ¬ problem_spec_rstDataStart 7 (implementation_rstDataStart 7) := by\n"
            "  unfold problem_spec_rstDataStart implementation_rstDataStart\n"
            "  decide\n"),
    },
]

# ===========================================================================
# AXIOM CASES — none. The bundle declares no callee contract (its `axioms`
# region is empty: both modeled quantities are pure functions of the inputs),
# and the nagini sibling's AXIOM_TESTS is empty for the same reason. The axiom
# lane is G-AX's obligation regardless of this bundle; this gate ignores it.
# ===========================================================================
AXIOM_TESTS = []
