"""properties.py — G-PBT falsification battery for sympy__sympy-13615 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct complementFinite`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the witness SUBJECT. On this bundle the subject is NOT the frozen
solution: its ``while`` loop leaves an un-normalised ``forIn Lean.Loop.mk`` term
that stalls every such claim regardless of truth, so each reject case supplies a
``witness_reference`` — a loop-free impl of the same spec that the gate verifies
first and that provably DECIDES these claims. See "WITNESS SUBJECT" below for
the builds that establish this.

================================  DEFENDED SURFACE  ==========================

ONE contracted method over a read-only finite collection and an opaque
three-valued membership oracle:

  complementFinite (elems : List Int) return (out : Partition)
    ensures out.definite = definiteOut elems      -- (P1) the definite members
    ensures out.symbolic = symbolicUnknown elems  -- (P2) the retained-symbolic

The method models the relative complement of a finite collection against an
ambient set, decided element-by-element by a deterministic three-valued oracle
(modeled ``opaque`` as ``contains : Int → Trit``, carrying NO value contract —
only determinism). Each element is classified once into one of three classes:

  * decided-negative (``Trit.outside``) — a DEFINITE member of the result;
  * undetermined (``Trit.unknown``)     — RETAINED SEPARATELY for symbolic
    handling, NOT asserted to be a member;
  * decided-positive (``Trit.inside``)  — EXCLUDED from the result entirely
    (appears in NEITHER field).

``definiteOut`` and ``symbolicUnknown`` are front-recursive folds selecting
exactly the ``outside`` (resp. ``unknown``) elements of ``elems``, in order. The
two ``ensures`` pin the two output fields as the two membership-keyed selections
of the SAME input:

  * (P1) the definite field is exactly the order-preserving ``outside`` sublist;
  * (P2) the symbolic field is exactly the order-preserving ``unknown`` sublist
    — the LOAD-BEARING part of the change: the undetermined elements must be
    carried in a SEPARATE field, never folded into the definite bucket and never
    dropped.

The three folds are GROUNDED in the input (fully-unfolded selections over
``elems`` composed with the opaque leaf ``contains``, applied element-by-
element), NOT an opaque answer-key equated to ``out`` — there is no wrong echo to
build, so the ungrounded-oracle probe is replaced by an honest positive control.

ONE input binder: ``elems : List Int`` (the ``pre-conditions`` region is empty,
so the domain is total). The per-element ``contains`` verdict selects each
element's class.

THE DISCRIMINATING BEHAVIOUR (the public issue): removing a finite collection
that MIXES decided-negative elements with undetermined ones. The pre-change code
folds every non-decided-positive element into ONE definite bucket and produces
no symbolic field, silently asserting the undetermined elements are non-members;
the fix routes them into the separate symbolic field. Any rival that folds an
undetermined element into the definite field, or drops it from the symbolic
field, reproduces the exact pre-change bug and would NOT resolve the F2P.

================================  THE CARRIER  ===============================

``contains`` is OPAQUE: it never reduces at a concrete element, so a
``decide``-on-a-literal tester STALLS on every ``contains n`` — for a rival AND
for gold — and discriminates nothing. Both routes the porting map prescribes are
used here:

  * STRUCTURAL clauses are transparent WITHOUT knowing ``contains``: which field
    an element lands in, and the shape/length of each field, are fixed by the
    fold once the per-element branch is taken. A rival that mis-routes or drops
    an element diverges from the fold at a point the witness can name.
  * VALUE / ROUTING clauses need CONDITIONING ON THE CARRIER: a rival is refuted
    at a concrete ``elems`` under a SINGLE weak hypothesis about the one opaque
    verdict at play (e.g. ``contains 5 = Trit.unknown``). One hypothesis about
    ONE opaque term is self-satisfiable (``contains`` is opaque — no ``False``
    follows from a single equation about it), so the refuting input genuinely
    exists; the witness holds of the rival (whose output differs from the folds
    at that input) and fails on gold (whose output IS the folds).

Every reject witness reaches the impl through Velvet's extractor
(``extract_program_for complementFinite`` gives ``complementFiniteExec elems``,
which reduces to ``DivM.res result``) and states ``complementFiniteExec xs ≠
DivM.res (⟨definiteOut xs, symbolicUnknown xs⟩ : Partition)`` at a concrete
``xs``. Each rival is a loop-free closed form the extractor DOES reduce.

The frozen impl's ``while`` loop also leaves the goal open — but that is NOT
evidence of anything, and an earlier revision of this file wrongly claimed it
was. Measured with real builds: a FORGERY asserting the exact OPPOSITE claim
(``=`` in place of ``≠``, i.e. that the frozen impl IS correct at that point)
fails against the frozen impl with the byte-identical ``unsolved goals`` error
over the same unreduced ``forIn Lean.Loop.mk`` term, at EVERY refutation
point (all seven, the five ported ones and the two the audit added). Gold's exit
code carries no information here, so every witness is refuted against the
``witness_reference`` instead (see WITNESS SUBJECT below).

Every witness build in this battery was re-run out-of-band with
``scripts/lean_verify.sh``: each ELABORATES against its rival (exit 0), FAILS
against the loop-free reference (exit 1) while the opposite-claim forgery
SUCCEEDS against that same reference (exit 0) — so the reference genuinely
decides rather than stalling — and each single-hypothesis consistency probe
leaves ``False`` unsolved (exit 1: the hypotheses are jointly satisfiable). So
each rejection is a genuine spec refutation, not mechanical tactic breakage nor
a forgery from a contradiction.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case in the
footer):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO
    MANDATORY frame-mutation rivals (append to / index-assign into the read-only
    input ``other`` held at ``Acc(list_pred(other), 1/2)``) — its #1 weakness
    class, because the input is a fractional heap permission an impl can
    illegally WRITE. Lean and Velvet are referentially transparent: ``elems`` is
    an immutable value, this bundle declares NO ``mut`` binder, there is no heap
    and no aliasing — so there is no read-only input to overwrite and no
    substitute probe to build. Not fabricated (per the porting map: this class is
    vacuous on Lean/Velvet).
  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE CARRIER, and NOT a spec hole.
    This bundle runs under ``loom.semantics.termination "total"``, so the
    verifier discharges a termination obligation and a diverging rival is
    genuinely REJECTED rather than verifying vacuously. Measured with real
    builds (four rivals): a ``while True do pure ()`` prefix spliced ahead of
    the frozen body, a bare ``while True`` loop replacing it, the frozen loop
    with its ``decreasing i`` annotation deleted, and the frozen loop with
    ``decreasing 1`` supplied but ``i`` never decremented — ALL exit 1. The
    first three report ``error: Decreasing annotations are required in total
    correctness semantics``; the fourth cannot even elaborate its measure. So
    the spec is complete on the termination axis here and there is no
    verify-does-not-imply-resolve break to record.
    The class is nonetheless NOT shippable as a reject case, for a TOOLING
    reason rather than a spec one: the termination error is an ELABORATION
    failure of the module itself, so it also fires inside the witness file (the
    gate appends the witness to that same source), leaving
    ``complementFiniteExec`` bound to ``sorry`` and every witness ``unsolved
    goals`` regardless of claim. Measured: witness against the diverging rival
    exit 1, with ``sorry ()`` visible in the printed goal term. A reject case
    needs a witness that ELABORATES against its rival, and no rival that trips
    the termination check can supply one. Recorded as VACUOUS-BY-REJECTION (the
    spec already rejects it — nothing is left unpinned), not as a known hole.
    NOTE the docstring of an earlier revision of this file described this bundle
    as ``"partial"`` and recorded the class as a KNOWN SPEC HOLE, citing an internal
    findings doc. Both are withdrawn: the frozen ``Solution.lean`` carries ``"total"``
    plus a ``decreasing i`` measure on the loop, its only correctness ``open`` is
    ``TotalCorrectness``, and the two cannot disagree because the ``set_option``
    elaborator itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Nor is the refusal only the
    annotation linter: a loop CARRYING a measure that does not decrease
    (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``, body
    ``q := q``) is REJECTED on the measure's own goal - ``case «decreasing_1: q»``,
    residual ``⊢ q < q``. (The nagini
    sibling carries no ``diverge-*`` case either, so nothing was dropped in the
    port.)
  * UNGROUNDED-ORACLE ECHO — N/A, as the nagini note itself frames it. Both
    ``ensures`` pin the output fields to ``definiteOut``/``symbolicUnknown`` —
    grounded folds over the method's own input composed with the opaque leaf
    ``contains``, not an opaque expected-result the impl could echo. The only
    satisfier is the honest per-element classification; the positive controls do
    it faithfully.
  * PARTIAL-DOMAIN / VALUE / ROUTING — the heart of this port: each reject rival
    is correct on part of the input domain (typically inputs with no undetermined
    element) and wrong on a sub-domain, refuted at a concrete input that pins one
    routing decision (definite vs symbolic vs excluded, or the loop boundary).

AXIOM lane: DROPPED. The ``axioms`` region declares ``contains`` (opaque, no
value contract) and the two folds are ``def``s validated == the real callee by
axiom_check.py (G-AX). That is G-AX's job; this gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-13615"
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
# -- impl-end) and is unique in Solution.lean; both facts are asserted at load
# by _swap. Editing only these keeps markers.same_spec True and the
# `prove_correct complementFinite` statement byte-identical (the spec view
# elides the impl region and the proof body).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method (the accumulating backward loop plus
# the return). Reject rivals replace it with a closed form; the positive
# controls instead edit only the loop body (below), keeping the loop shape so
# the frozen invariants and the frozen `prove_correct` script still close it.
_IMPL_BODY = (
    "    let mut def_ : List Int := []\n"
    "    let mut sym : List Int := []\n"
    "    let mut i := elems.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ elems.length\n"
    "      invariant def_ = definiteOut (elems.drop i)\n"
    "      invariant sym = symbolicUnknown (elems.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let el := elems[i - 1]!\n"
    "      def_ := (if contains el = Trit.outside then [el] else []) ++ def_\n"
    "      sym := (if contains el = Trit.unknown then [el] else []) ++ sym\n"
    "      i := i - 1\n"
    "    return { definite := def_, symbolic := sym }"
)
assert _BASE.count(_IMPL_BODY) == 1, "complementFinite impl region drifted from expected text"

# The two accumulator assignments (the routing core of the loop body). The
# branch-reorder positive control swaps their ORDER; the frozen invariants pin
# each accumulator independently, so the two disjoint prepends commute and the
# frozen proof still closes.
_ACCUM = (
    "      let el := elems[i - 1]!\n"
    "      def_ := (if contains el = Trit.outside then [el] else []) ++ def_\n"
    "      sym := (if contains el = Trit.unknown then [el] else []) ++ sym\n"
)
assert _BASE.count(_ACCUM) == 1, "loop-body accumulators drifted from expected text"


# The frozen `prove_correct` script. Its two bullets discharge the loop-body
# goals `loom_solve` leaves for the BACKWARD walk; a loop-free impl leaves no
# such goals, so a closed-form variant must also drop the bullets or Lean reports
# `No goals to be solved`. Variant scope permits retuning the tactic BODY (the
# `prove_correct complementFinite` statement itself stays byte-identical), which
# is what makes the verifying loop-free reference below available at all.
_PROOF = (
    "prove_correct complementFinite by\n"
    "  loom_solve\n"
    "  · rw [definiteOut_drop_step elems i (by omega) (by omega)]; simp_all\n"
    "  · rw [symbolicUnknown_drop_step elems i (by omega) (by omega)]; simp_all"
)
assert _BASE.count(_PROOF) == 1, "prove_correct script drifted from expected text"


def _closed(defn: str, symb: str) -> str:
    """Solution.lean whose impl body is a single loop-free
    `return { definite := <defn>, symbolic := <symb> }`.

    The frozen proof's two loop-body bullets are dropped with it: with no loop
    there are no per-step goals, so keeping them errors with `No goals to be
    solved` — a failure that has nothing to do with the spec. Only the tactic
    body changes; the obligation statement stays byte-identical (checked by
    `variant_problems`).
    """
    return _swap(_swap(_BASE, _IMPL_BODY,
                       f"    return {{ definite := {defn}, symbolic := {symb} }}"),
                 _PROOF, "prove_correct complementFinite by\n  loom_solve")


# ---------------------------------------------------------------------------
# WITNESS SUBJECT. The frozen impl CANNOT serve as the second subject of the
# discrimination check on this bundle, and this is measured, not argued.
#
# `complementFinite` carries a `while` loop under `loom.semantics.choice
# "demonic"`. Through the extractor the loop stays an un-normalised
# `forIn Lean.Loop.mk ...` term that `simp` cannot push through, so a witness
# stated as `complementFiniteExec xs ≠ DivM.res ⟨...⟩` leaves `unsolved goals`
# against the frozen impl for EVERY claim, true or false. Verified with real
# builds at all seven refutation points below: the witness fails against the
# frozen impl (exit 1) AND a FORGERY asserting the exact OPPOSITE — that the
# frozen impl IS correct there (`=` in place of `≠`) — fails with the
# byte-identical `unsolved goals` error over the same unreduced `forIn
# Lean.Loop.mk` term (exit 1). A `1 + 1 = 2` witness builds fine against the
# same file (exit 0), so the bundle is not simply broken; it is this claim's
# reduction that is unavailable. Gold's exit code therefore carries NO
# information, and a rejection checked against it attests to a tactic mismatch
# rather than to the spec.
#
# So each reject case names `witness_reference`: the loop-free closed form
# below. The gate checks it shares the frozen spec and VERIFIES before refuting
# any witness against it, and an impl the verifier accepts cannot violate its
# own spec — so a genuine witness must still fail there. Measured: it verifies
# (exit 0), every witness FAILS against it (exit 1), and the opposite-claim
# forgery SUCCEEDS against it (exit 0). That last build is the one the frozen
# impl could not provide: it shows the reference actually DECIDES these claims
# instead of stalling, which is what makes the exit codes mean something.
_REFERENCE = _closed("definiteOut elems", "symbolicUnknown elems")


# ---- witness preamble + builder. The spec is a `method` CONTRACT over a
# ---- partly-opaque carrier, so a witness reaches the impl through Velvet's
# ---- extractor: `complementFiniteExec xs` is `NonDetT.run (complementFinite
# ---- xs)`, which reduces to `DivM.res result`; `≠ DivM.res ⟨definiteOut xs,
# ---- symbolicUnknown xs⟩` says the impl's output contradicts the postcondition
# ---- at that concrete input. Checked in a file whose `prove_correct` block is
# ---- stripped, so no tactic script can mask the verdict. `contains` never
# ---- reduces, so each witness conditions on it via a SINGLE satisfiable
# ---- equation about the one verdict at play.
_EXTRACT = "extract_program_for complementFinite\n\n"


def _w(hyp: str, xs: str) -> str:
    return (
        _EXTRACT +
        f"example (h : {hyp}) :\n"
        f"    complementFiniteExec {xs} ≠ DivM.res\n"
        f"      (⟨definiteOut {xs}, symbolicUnknown {xs}⟩ : Partition) := by\n"
        "  unfold complementFiniteExec complementFinite\n"
        "  simp [NonDetT.run, pure, definiteOut, symbolicUnknown, h]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Both keep the backward-walk +
    # front-prepend loop shape (so the front-recursive folds unfold one step per
    # iteration, matching the invariants) and the frozen `prove_correct` script
    # closes the byte-identical obligation with no retune (confirmed with real
    # builds).
    # =====================================================================

    # POS 1 — branch/assignment REORDER. Write the two accumulator updates in the
    # OPPOSITE order (symbolic first, then definite). The two prepends touch
    # DISJOINT accumulators and each is pinned by its own invariant, so their
    # order is irrelevant; the partition is identical on every input. Ports the
    # nagini `pos-control-branch-reorder` argument (UNDECIDED tested first).
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ACCUM,
            "      let el := elems[i - 1]!\n"
            "      sym := (if contains el = Trit.unknown then [el] else []) ++ sym\n"
            "      def_ := (if contains el = Trit.outside then [el] else []) ++ def_\n"),
        "rationale": "PASS SOURCE = (P1) ∧ (P2). Writing the two accumulator "
                     "updates in the opposite order (symbolic then definite) "
                     "touches disjoint accumulators, each pinned by its own "
                     "invariant, so the two prepends commute and the partition is "
                     "identical on every input — both `out.definite = definiteOut "
                     "elems` and `out.symbolic = symbolicUnknown elems` still "
                     "discharge under the frozen invariants and the frozen proof "
                     "script (no retune). Same backward walk + front-prepend, so "
                     "the folds unfold one step per iteration. A faithful reshape "
                     "MUST verify, else the spec is over-fit to the assignment "
                     "ORDER (SPEC-TOO-STRONG). Ports the sibling's "
                     "branch-reorder positive control.",
    },

    # POS 2 — local-variable reshape. Hoist the index into a local `j = i-1` and
    # read the element through it. Same backward direction, same front-recursive
    # unfold, same invariants/asserts; only the token shape of the index read
    # differs. Ports the nagini `pos-control-equality-ladder` intent (the spec is
    # not pinned to the gold's exact token shape).
    {
        "id": "pos-control-localvar-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _ACCUM,
            "      let j := i - 1\n"
            "      let el := elems[j]!\n"
            "      def_ := (if contains el = Trit.outside then [el] else []) ++ def_\n"
            "      sym := (if contains el = Trit.unknown then [el] else []) ++ sym\n"),
        "rationale": "PASS SOURCE = (P1) ∧ (P2). Hoisting the index into a local "
                     "`j = i-1` and reading the element through it is "
                     "observationally identical to gold on every input (`j` "
                     "denotes the same index), so both field clauses discharge "
                     "under the frozen invariants and the frozen proof script "
                     "with no retune. Confirms the spec is not pinned to gold's "
                     "exact index-read token shape. A faithful reshape MUST "
                     "verify, else SPEC-TOO-STRONG.",
    },

    # POS 3 — DIRECTION reshape (added by audit, attack E). The two positives
    # above vary only the TOKEN shape of the loop body: both keep gold's backward
    # walk, gold's front-prepend, gold's invariants and gold's proof script, so
    # neither one would notice a spec over-fit to the walk direction. This one
    # walks FORWARD (`i` from 0 up), accumulates by APPEND at the back, states the
    # invariants over `elems.take i` instead of `elems.drop i`, and closes the
    # obligation with its own inline `take`-based fold-step `have`s (the frozen
    # `drop`-oriented step lemmas do not apply). Structurally the maximal distance
    # from gold that is still faithful: same partition on every input, reached by
    # the opposite traversal. Verified with a real build (exit 0).
    {
        "id": "pos-control-forward-walk",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    let mut def_ : List Int := []\n"
                  "    let mut sym : List Int := []\n"
                  "    let mut i := 0\n"
                  "    while i < elems.length\n"
                  "      invariant 0 ≤ i ∧ i ≤ elems.length\n"
                  "      invariant def_ = definiteOut (elems.take i)\n"
                  "      invariant sym = symbolicUnknown (elems.take i)\n"
                  "      done_with i = elems.length\n"
                  "      decreasing elems.length - i\n"
                  "    do\n"
                  "      let el := elems[i]!\n"
                  "      def_ := def_ ++ (if contains el = Trit.outside then [el] else [])\n"
                  "      sym := sym ++ (if contains el = Trit.unknown then [el] else [])\n"
                  "      i := i + 1\n"
                  "    return { definite := def_, symbolic := sym }"),
            _PROOF,
            "prove_correct complementFinite by\n"
            "  have takeStepD : ∀ (xs : List Int) (k : Nat), k < xs.length →\n"
            "      definiteOut (xs.take (k + 1))\n"
            "        = definiteOut (xs.take k) ++ (if contains xs[k]! = Trit.outside then [xs[k]!] else []) := by\n"
            "    intro xs k hk\n"
            "    induction xs generalizing k with\n"
            "    | nil => simp at hk\n"
            "    | cons a t ih =>\n"
            "      cases k with\n"
            "      | zero => simp [definiteOut]\n"
            "      | succ m =>\n"
            "        have hm : m < t.length := by simpa using hk\n"
            "        simp only [List.take_succ_cons, definiteOut_cons, ih m hm,\n"
            "          List.getElem!_cons_succ, List.append_assoc]\n"
            "  have takeStepS : ∀ (xs : List Int) (k : Nat), k < xs.length →\n"
            "      symbolicUnknown (xs.take (k + 1))\n"
            "        = symbolicUnknown (xs.take k) ++ (if contains xs[k]! = Trit.unknown then [xs[k]!] else []) := by\n"
            "    intro xs k hk\n"
            "    induction xs generalizing k with\n"
            "    | nil => simp at hk\n"
            "    | cons a t ih =>\n"
            "      cases k with\n"
            "      | zero => simp [symbolicUnknown]\n"
            "      | succ m =>\n"
            "        have hm : m < t.length := by simpa using hk\n"
            "        simp only [List.take_succ_cons, symbolicUnknown_cons, ih m hm,\n"
            "          List.getElem!_cons_succ, List.append_assoc]\n"
            "  loom_solve"),
        "rationale": "PASS SOURCE = (P1) ∧ (P2). A forward walk that appends at "
                     "the back produces the SAME order-preserving selections as "
                     "gold's backward walk that prepends at the front — the "
                     "partition is identical on every input — so both "
                     "`out.definite = definiteOut elems` and `out.symbolic = "
                     "symbolicUnknown elems` must still discharge. Unlike the two "
                     "positives above (which keep gold's direction, accumulation "
                     "side, invariants and proof), this one changes ALL of them: "
                     "the invariants are stated over `elems.take i`, and the "
                     "fold-step facts are re-proved inline by induction because "
                     "the frozen `drop`-oriented lemmas do not apply. If the spec "
                     "rejected it, the spec would be over-fit to gold's TRAVERSAL "
                     "DIRECTION rather than to the partition it computes "
                     "(SPEC-TOO-STRONG) — the one over-fit the token-level "
                     "positives cannot detect. Added by the audit (attack E); "
                     "verified with a real build.",
    },

    # =====================================================================
    # ADMISSIBILITY (added by audit) — PRECOND-TOO-STRONG, the third direction
    # this gate exists to test and the lane an earlier revision of this file
    # omitted as "vacuous (no precond)". That reason was wrong. The frozen
    # `pre-conditions` region is indeed empty, but on a TOTAL carrier the
    # analogue is not "is there a `require` to satisfy" — it is whether the
    # obligation is SATISFIABLE at exactly an F2P-shaped input, which an empty
    # precondition does not establish. A spec whose two `ensures` were jointly
    # unsatisfiable at a mixed input (or whose post-image collapsed there) would
    # pass every case above: the five rivals only need the spec to REJECT them,
    # and the three positives all reproduce the frozen partition, so a
    # degenerate post-image is invisible to all eight.
    #
    # This case discharges the obligation at the concrete F2P-shaped input BY
    # EVALUATION, as an in-region `have`-style `assert`, BEFORE the frozen
    # obligation closes verbatim. The input is the discriminating one: a
    # collection MIXING all three verdict classes — one decided-positive element
    # (excluded from both fields), TWO undetermined ones (the load-bearing
    # separate-field class), and one decided-negative one — so the assert pins a
    # genuinely three-way, non-degenerate split rather than a single class.
    #
    # `contains` is opaque, so the four verdicts are supplied as HYPOTHESES and
    # the claim is stated as an implication; that is what makes an opaque carrier
    # attackable at all. Measured, and all four builds are the substance of this
    # case:
    #   * the TRUE claim verifies (exit 0);
    #   * falsifying the symbolic field alone (adding the decided-positive
    #     element 2 to it) fails exit 1 on the `admiss_1` goal ITSELF;
    #   * falsifying the definite field alone (adding 2 to it) fails exit 1 on
    #     the same goal;
    #   so the assert is LIVE — it is not being closed incidentally by
    #   `loom_solve`, and a false claim is caught at the assert rather than
    #   somewhere downstream.
    #   * and the four hypotheses are jointly SATISFIABLE: the gate's own
    #     consistency-probe shape (`example <those binders> : False`) leaves the
    #     goal open (exit 1, `simp_all made no progress`), so the input the
    #     assert claims admissibility at genuinely exists. Without that build the
    #     case could have been discharged from a contradiction, which would
    #     attest to nothing.
    #
    # The proof is retuned only in its BODY (permitted; the `prove_correct
    # complementFinite` statement stays byte-identical) and only to make the
    # bullet structure order-robust: the extra `assert` goal changes how many
    # goals `loom_solve` leaves, so the frozen positional bullets no longer line
    # up. `first | ... | ... | ...` tries the admiss discharge and the two frozen
    # fold-step tactics against whichever goal is in front of it, which keeps the
    # two frozen fold-step arguments verbatim rather than weakening them.
    # =====================================================================
    {
        "id": "admiss-f2p-mixed-verdicts",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_BODY,
                  "    assert (with_name_prefix `admiss\n"
                  "      (contains 2 = Trit.inside → contains 11 = Trit.unknown →\n"
                  "       contains 12 = Trit.unknown → contains 20 = Trit.outside →\n"
                  "       (definiteOut [11, 12, 2, 20] = [20]\n"
                  "        ∧ symbolicUnknown [11, 12, 2, 20] = [11, 12])))\n"
                  + _IMPL_BODY),
            _PROOF,
            "prove_correct complementFinite by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | (intro h2 h11 h12 h20; simp [definiteOut, symbolicUnknown, h2, h11, h12, h20])\n"
            "    | (rw [definiteOut_drop_step elems i (by omega) (by omega)]; simp_all)\n"
            "    | (rw [symbolicUnknown_drop_step elems i (by omega) (by omega)]; simp_all)"),
        "rationale": "PRECOND-TOO-STRONG probe. The obligation must be "
                     "SATISFIABLE at an F2P-shaped input, and on this total "
                     "carrier that is the live admissibility question even though "
                     "the `pre-conditions` region is empty — an empty precondition "
                     "does not establish that the post-image is non-degenerate "
                     "where the change matters. The in-region assert discharges "
                     "both clauses BY EVALUATION at a collection mixing ALL THREE "
                     "verdict classes: `[11, 12, 2, 20]` with 2 decided-positive, "
                     "11 and 12 undetermined, 20 decided-negative. It pins "
                     "`definiteOut = [20]` (the decided-positive element is "
                     "excluded from the definite field, and the two undetermined "
                     "ones are NOT folded into it) and `symbolicUnknown = [11, "
                     "12]` (both undetermined elements are carried, in order, in "
                     "the SEPARATE field — the load-bearing clause), so the "
                     "three-way split is genuinely non-degenerate here and neither "
                     "field is a constant or an empty collapse. The frozen "
                     "obligation then closes verbatim after it. If this were "
                     "rejected, the spec would be unsatisfiable at exactly the "
                     "input shape the change is about (PRECOND-TOO-STRONG). "
                     "`contains` is opaque so the four verdicts are hypotheses; "
                     "measured, they are jointly satisfiable (a `False` probe over "
                     "those binders leaves the goal open) and the assert is LIVE "
                     "(falsifying either field alone fails ON the assert goal). "
                     "Added by the audit: the lane was previously omitted as "
                     "'vacuous (no precond)', which is not the analogue on a total "
                     "carrier.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input (conditioned on the single opaque
    # verdict at play) and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test. The five rivals attack the
    # two field clauses across distinct routing decisions and distinct inputs.
    # =====================================================================

    # ---- THE BUG (prepatch / G-DIFF): fold every non-excluded element into the
    # ---- ONE definite field and leave the symbolic field empty. Attacks BOTH
    # ---- (P1) and (P2) the moment an undetermined element appears. ----
    {
        "id": "weak-prepatch-fold-undecided-into-definite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "elems.filter (fun e => contains e != Trit.inside)", "[]"),
        "refinement": "this IS the pre-change behaviour: every element that is "
                      "not decided-positive is folded into ONE concrete "
                      "collection and no separate symbolic part is produced, "
                      "silently asserting the undetermined elements are "
                      "non-members. On the discriminating removal (a finite "
                      "collection mixing undetermined elements with a "
                      "decided-negative one) it returns the undetermined elements "
                      "as definite members instead of a separate symbolic result, "
                      "so the reported equality fails. It is the exact bug the "
                      "change fixes (the G-DIFF discriminator) — the faithful "
                      "real patch (= prechange) does NOT resolve.",
        "rationale": "REJECT from (P1) `out.definite = definiteOut elems` (the "
                     "definite field then also contains the undetermined "
                     "elements `definiteOut` excludes) AND (P2) `out.symbolic = "
                     "symbolicUnknown elems` (the symbolic field is empty but "
                     "`symbolicUnknown` is not). Refuted at a single undetermined "
                     "element `[7]` under `contains 7 = Trit.unknown`: the rival "
                     "keeps 7 in the definite field with an empty symbolic field, "
                     "the spec demands the reverse. If it verified, the "
                     "undetermined→symbolic fix would be unpinned (SPEC-TOO-WEAK "
                     "/ the prepatch family).",
        "witness": _w("contains 7 = Trit.unknown", "[7]"),
        "witness_reference": _REFERENCE,
    },

    # ---- (P2) only: definite field correct, symbolic field always empty
    # ---- (drop the undetermined elements). Correct where there is no
    # ---- undetermined element; wrong the moment one appears. ----
    {
        "id": "weak-symbolic-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("definiteOut elems", "[]"),
        "refinement": "this gets the definite field right but produces an EMPTY "
                      "symbolic field — equivalent to dropping the undetermined "
                      "elements entirely (no separate symbolic result emitted). "
                      "On the discriminating removal the undetermined elements "
                      "vanish from the result, so the reported equality fails. "
                      "The faithful real patch does NOT resolve.",
        "rationale": "REJECT from (P2) `out.symbolic = symbolicUnknown elems` "
                     "whenever an undetermined element exists: the symbolic field "
                     "is empty but `symbolicUnknown` is not. (P1) still holds "
                     "(the definite field IS `definiteOut elems`), so the "
                     "rejection is attributable SOLELY to the missing symbolic "
                     "elements. Refuted at `[5]` under `contains 5 = "
                     "Trit.unknown`.",
        "witness": _w("contains 5 = Trit.unknown", "[5]"),
        "witness_reference": _REFERENCE,
    },

    # ---- (P1) only: symbolic field correct, but the undetermined elements ALSO
    # ---- leak into the definite field (a double-count a length-only proxy would
    # ---- miss). ----
    {
        "id": "weak-undecided-leaks-into-definite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "definiteOut elems ++ symbolicUnknown elems", "symbolicUnknown elems"),
        "refinement": "this carries the undetermined elements in the symbolic "
                      "field (correct) but ALSO puts them in the concrete "
                      "definite field — asserting they ARE known non-members "
                      "while the symbolic field says their membership is "
                      "unresolved, a contradiction the fixed result never "
                      "produces. On the discriminating removal it returns the "
                      "undetermined elements in BOTH parts, so the reported "
                      "equality fails. The faithful real patch does NOT resolve.",
        "rationale": "REJECT from (P1) `out.definite = definiteOut elems` "
                     "whenever an undetermined element exists: the definite field "
                     "over-counts by the undetermined elements `definiteOut` "
                     "excludes. (P2) holds (the symbolic field IS `symbolicUnknown "
                     "elems`), so the rejection is attributable SOLELY to the "
                     "definite over-count — a double-count an order-/length-only "
                     "proxy would miss. Refuted at `[6]` under `contains 6 = "
                     "Trit.unknown`.",
        "witness": _w("contains 6 = Trit.unknown", "[6]"),
        "witness_reference": _REFERENCE,
    },

    # ---- BOTH (P1) and (P2): route the two fields into the WRONG selections
    # ---- (definite gets the undetermined sublist, symbolic gets the
    # ---- decided-negative sublist). Wrong the moment either an outside or an
    # ---- unknown element appears. ----
    {
        "id": "weak-fields-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed("symbolicUnknown elems", "definiteOut elems"),
        "refinement": "this swaps the two fields: the decided-negative elements "
                      "land in the symbolic part and the undetermined elements in "
                      "the definite part — asserting the undetermined elements are "
                      "known non-members and leaving the known-out elements "
                      "unresolved. On the discriminating removal the result is "
                      "structurally wrong (the definite field holds the "
                      "undetermined elements), so the equality fails. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "REJECT from (P1) (the definite field gets the undetermined "
                     "elements, not the decided-negative ones) AND (P2) (the "
                     "symbolic field gets the decided-negative elements, not the "
                     "undetermined ones) whenever any decided-negative OR "
                     "undetermined element exists. Refuted at a decided-negative "
                     "element `[4]` under `contains 4 = Trit.outside`: the rival "
                     "puts 4 in the symbolic field, the spec demands the definite "
                     "field. This moves the attacked verdict off `unknown` "
                     "(exercised by the other rivals) onto `outside`.",
        "witness": _w("contains 4 = Trit.outside", "[4]"),
        "witness_reference": _REFERENCE,
    },

    # ---- OFF-BY-ONE boundary: skip the FIRST input element (drop 1). Correct
    # ---- where the first element is decided-positive (dropped anyway); wrong
    # ---- when it is decided-negative (missing from definite) or undetermined
    # ---- (missing from symbolic). Needs a >=2-element input to distinguish from
    # ---- the single-element rivals. ----
    {
        "id": "weak-skip-first-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "definiteOut (elems.drop 1)", "symbolicUnknown (elems.drop 1)"),
        "refinement": "this never classifies the first element of the "
                      "collection, dropping it from BOTH parts regardless of its "
                      "verdict — a decided-negative first element vanishes from "
                      "the definite result, an undetermined first element from the "
                      "symbolic result. On any removal whose first element "
                      "survives or is undetermined, the fixed result drops an "
                      "element it must keep, so the reported equality fails. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "REJECT from (P1)/(P2) on the first input element whenever it "
                     "is decided-negative (missing from `definiteOut`) or "
                     "undetermined (missing from `symbolicUnknown`) — an "
                     "off-by-one a value proxy that ignores index 0 would miss. "
                     "Refuted at a TWO-element input `[8, 9]` under `contains 8 = "
                     "Trit.outside`: the rival drops the leading decided-negative "
                     "element 8 from the definite field, the spec keeps it. Moves "
                     "the `elems` binder to length 2 (distinct from every "
                     "single-element rival above).",
        "witness": _w("contains 8 = Trit.outside", "[8, 9]"),
        "witness_reference": _REFERENCE,
    },

    # ---- OFF-BY-ONE, the OTHER boundary (added by audit, attack D): skip the
    # ---- LAST input element. The five rivals above probe index 0 (skip-first)
    # ---- but nothing probes the far end of the walk, and the frozen impl's
    # ---- loop STARTS at `i = elems.length` — so the last element is exactly the
    # ---- one the first iteration reads, and an off-by-one in the loop bound
    # ---- (`i > 1`-style, or `elems.length - 1` as the start) lands here rather
    # ---- than at index 0. Verified with a real build: rejected (exit 1). ----
    {
        "id": "weak-skip-last-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "definiteOut (elems.take (elems.length - 1))",
            "symbolicUnknown (elems.take (elems.length - 1))"),
        "refinement": "this never classifies the LAST element of the collection, "
                      "dropping it from BOTH parts regardless of its verdict — a "
                      "decided-negative final element vanishes from the definite "
                      "result, an undetermined final element from the symbolic "
                      "result. On any removal whose last element is decided-negative "
                      "or undetermined, the fixed result drops an element it must "
                      "keep, so the reported equality fails. The faithful real patch "
                      "does NOT resolve — it would silently shorten every "
                      "non-trivial removal by one element, so even removals with no "
                      "undetermined element (the sub-domain every other rival here "
                      "gets right) come out wrong.",
        "rationale": "REJECT from (P1)/(P2) on the LAST input element whenever it is "
                     "decided-negative (missing from `definiteOut`) or undetermined "
                     "(missing from `symbolicUnknown`). Attacks the boundary "
                     "OPPOSITE to weak-skip-first-element: the frozen walk starts at "
                     "`i = elems.length`, so the last element is the first one read "
                     "and an off-by-one in the loop's STARTING bound shows up here, "
                     "not at index 0. Refuted at a TWO-element input `[13, 14]` "
                     "under `contains 14 = Trit.outside`: the rival drops the "
                     "trailing decided-negative element 14 from the definite field, "
                     "the spec keeps it. A SIXTH distinct refutation point, and the "
                     "only one whose input's *tail* is the discriminating position. "
                     "Added by the audit (attack D).",
        "witness": _w("contains 14 = Trit.outside", "[13, 14]"),
        "witness_reference": _REFERENCE,
    },

    # ---- (P2) OVER-count, the mirror of weak-undecided-leaks-into-definite
    # ---- (added by audit, attack D). That rival over-fills the DEFINITE field
    # ---- with the undetermined elements; nothing over-filled the SYMBOLIC field,
    # ---- so a spec that pinned (P1) tightly but only pinned (P2) up to
    # ---- containment would have passed every case above. Verified with a real
    # ---- build: rejected (exit 1). ----
    {
        "id": "weak-definite-leaks-into-symbolic",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _closed(
            "definiteOut elems", "symbolicUnknown elems ++ definiteOut elems"),
        "refinement": "this gets the definite field right but ALSO copies the "
                      "decided-negative elements into the symbolic field — so an "
                      "element whose membership the oracle DECIDED is additionally "
                      "reported as unresolved, and it is emitted twice across the "
                      "two parts. The fixed result never does this: the three "
                      "classes are disjoint and each element appears in at most one "
                      "field. On the discriminating removal the symbolic part is "
                      "polluted with elements that need no symbolic handling at all, "
                      "so the reported equality fails. The faithful real patch does "
                      "NOT resolve.",
        "rationale": "REJECT from (P2) `out.symbolic = symbolicUnknown elems` "
                     "whenever a decided-negative element exists: the symbolic field "
                     "over-counts by exactly the elements `symbolicUnknown` "
                     "excludes. (P1) still holds (the definite field IS `definiteOut "
                     "elems`), so the rejection is attributable SOLELY to the "
                     "symbolic over-count. This is the MIRROR of "
                     "weak-undecided-leaks-into-definite (which over-fills the "
                     "definite field): together they pin both fields against "
                     "over-counting in both directions, where before only (P1) was "
                     "attacked that way — a spec pinning (P2) merely up to "
                     "containment would have passed the whole battery. Refuted at "
                     "`[15]` under `contains 15 = Trit.outside`, a SEVENTH distinct "
                     "refutation point. Added by the audit (attack D).",
        "witness": _w("contains 15 = Trit.outside", "[15]"),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation, 5 uniqueness rivals) plus a
# 1-case AXIOM lane. It models the SAME purely-functional core — a three-way
# partition of a finite collection by a three-valued membership verdict into
# (survivors, pending) — so the value/routing rivals port near 1:1; the frame
# cases are genuinely vacuous on this carrier and the divergence class is
# REJECTED by the carrier (vacuous-by-rejection, NOT a spec hole — see below).
#
#   sibling case (nagini)                          -> here                                   disposition
#   ---------------------------------------------------------------------------------------------------------
#   pos-control-branch-reorder                     -> pos-control-branch-reorder             PORTED
#   pos-control-equality-ladder                    -> pos-control-localvar-reshape           RE-EXPRESSED
#   (no sibling case)                              -> pos-control-forward-walk               ADDED BY AUDIT (attack E)
#   admiss-self-call-singleton                     -> admiss-f2p-mixed-verdicts              RE-AIMED BY AUDIT (attack F)
#   frame-mutate-other-append                      -> (none)                                 VACUOUS (no heap)
#   frame-mutate-other-index-assign                -> (none)                                 VACUOUS (no heap)
#   weak-prepatch-fold-undecided-into-survivors    -> weak-prepatch-fold-undecided-into-definite  PORTED
#   weak-pending-always-empty                      -> weak-symbolic-always-empty             PORTED
#   weak-undecided-leaks-into-survivors            -> weak-undecided-leaks-into-definite     PORTED
#   weak-buckets-swapped                           -> weak-fields-swapped                    PORTED
#   weak-skip-first-element                        -> weak-skip-first-element                PORTED
#   (no sibling case)                              -> weak-skip-last-element                 ADDED BY AUDIT (attack D)
#   (no sibling case)                              -> weak-definite-leaks-into-symbolic      ADDED BY AUDIT (attack D)
#   AXIOM_TESTS (x1)                               -> (none)                                 DROPPED (G-AX)
#
# PORTED (branch-reorder): the sibling reorders the two membership branches
#   (UNDECIDED tested first) and splits them into two ifs; the argument is "the
#   verdicts are disjoint, so the routing order is irrelevant". On this carrier the
#   two routing decisions are two separate accumulator assignments, so the SAME
#   idea is expressed by swapping their order (symbolic then definite). Each
#   accumulator is pinned by its own invariant, so the frozen proof closes with no
#   retune.
# RE-EXPRESSED (equality-ladder -> localvar-reshape): the sibling's second
#   positive uses an explicit three-rung equality ladder with a DEFINITELY_IN
#   no-op rung to show the spec is not pinned to gold's if/elif token shape. On
#   this carrier the excluded (`inside`) class is already an implicit no-op (it is
#   simply not selected by either `if`), so an explicit rung has nothing to
#   dispatch. The SAME "not pinned to the exact token shape" intent is preserved by
#   reshaping the index read (hoist `j = i-1`), an observationally identical impl
#   whose frozen proof closes unchanged.
# PORTED (5 uniqueness rivals): the prepatch fold, pending-always-empty,
#   undecided-leak, buckets-swap and skip-first rivals port DIRECTLY onto the two
#   field clauses. Their refinement arguments carry over verbatim (fold-into-one /
#   drop-symbolic / double-count / swap / off-by-one). Each is refuted at a
#   concrete input by a witness that conditions on the SINGLE opaque verdict at
#   play; each elaborates against the rival and fails against the loop-free
#   `witness_reference` (NOT against gold — gold cannot decide these claims; see
#   WITNESS SUBJECT in the module docstring and the AUDIT note below).
# ADDED BY AUDIT (pos-control-forward-walk): attack E built a correct impl that
#   reverses the traversal direction (forward walk + back-append + `take`-based
#   invariants + inline re-proved fold steps) and it VERIFIES (exit 0). The two
#   ported positives both keep gold's direction, accumulation side, invariants and
#   proof script, so neither could have detected a spec over-fit to the traversal
#   direction. Shipped as a third positive because that over-fit was the largest
#   untested SPEC-TOO-STRONG risk on this bundle.
#
# AUDIT FINDING (witness subject — the reason this battery was repaired).
#   As first ported, all five reject cases refuted their witness against the
#   FROZEN solution and the gate recorded SOUND. That SOUND was hollow. The
#   frozen impl's `while` loop leaves an un-normalised `forIn Lean.Loop.mk` term
#   that `simp` cannot push through, so the goal stays open for EVERY claim about
#   `complementFiniteExec` regardless of truth. Measured: at all five refutation
#   points a FORGERY asserting the exact OPPOSITE (that the frozen impl IS
#   correct there) fails with the byte-identical `unsolved goals` error, while a
#   `1 + 1 = 2` witness against the same file builds fine (exit 0). So gold's
#   exit code carried no information and all five rejections attested to a tactic
#   mismatch rather than to the spec.
#   NOTE this arrival is NOT matched by the gate's four `_stuck` screens: it
#   presents as plain `unsolved goals` over the unreduced loop term, not as
#   `did not reduce to isTrue/isFalse`, `Dependent elimination failed`, a missing
#   `Decidable` instance, or an `Application type mismatch`. `_stuck()` therefore
#   returns False and the gate credited the cases. Reported for the screen list.
#   REPAIR: each reject case now names a `witness_reference` — the loop-free
#   closed form `_REFERENCE`. The gate checks it shares the frozen spec and
#   VERIFIES before using it. Measured: it verifies (exit 0), every witness FAILS
#   against it (exit 1), and the opposite-claim forgery SUCCEEDS against it
#   (exit 0), which is the build proving the reference actually DECIDES these
#   claims instead of stalling. The five rivals themselves were never in doubt —
#   each is observably wrong at its refutation point — only the evidence was.
# RE-AIMED BY AUDIT (admissibility): as first ported this lane was omitted with
#   the reason "VACUOUS (no precond)" — the `pre-conditions` region is empty, so
#   there is no `require` clause to admit. That reason is WRONG on a total
#   carrier, and the audit replaced the omission with a live case. What the
#   sibling's admissibility case actually buys is not "the precondition is
#   satisfiable" but "the POST-IMAGE is reachable at an F2P-shaped input" — i.e.
#   the contract, taken together, is not accidentally unsatisfiable there. On a
#   `"total"` carrier that is expressible WITHOUT any `require`: an in-region
#   `assert (with_name_prefix `admiss (...))` makes the verifier discharge a NEW
#   goal at a concrete input, inside the same obligation, with the frozen `method`
#   and `ensures` untouched. `admiss-f2p-mixed-verdicts` does exactly that at the
#   discriminating input shape — a removal MIXING both decided classes with two
#   undetermined elements — and asserts the exact two-field split the spec
#   demands there. Three supporting builds: the true claim verifies (exit 0); TWO
#   independent falsifications of the asserted split FAIL on the `admiss_1` goal
#   itself (exit 1 each — so the assert is LIVE, not closed for free by
#   `loom_solve`); and the hypothesis conjunction's consistency probe leaves
#   `False` unsolved (exit 1 — the four oracle verdicts are jointly satisfiable,
#   so the case is not admitting from a contradiction).
# VACUOUS (two frame-mutation rivals): the sibling carries these MANDATORY (its #1
#   weakness class) because `other` is held at `Acc(list_pred(other),1/2)` an impl
#   can illegally append to / index-assign into. This backend is referentially
#   transparent and declares no `mut` binder — `elems` is an immutable value with
#   no heap footprint — so there is no read-only input to overwrite and no
#   permission system to trip. No substitute is fabricated (per the porting map).
# VACUOUS-BY-REJECTION (divergence): NOT shipped, and NOT a spec hole. An earlier
#   revision of this footer recorded it as a KNOWN SPEC HOLE on the grounds that
#   the bundle runs under `loom.semantics.termination "partial"`, where (per an
#   internal findings doc it cited) a non-terminating impl satisfies both `ensures`
#   vacuously. The frozen `Solution.lean` carries `"total"` plus a `decreasing i`
#   measure on the loop, and its only correctness `open` is TotalCorrectness, so that
#   reasoning does not apply here; both the premise and the citation are withdrawn.
#   The refusal is not just the annotation linter either: a loop CARRYING a measure
#   that does not decrease (`while q > 0 ... decreasing q`, body `q := q`) is rejected
#   on the measure's own goal -- `case «decreasing_1: q»`, residual `q < q`.
#   Re-derived with real builds against the frozen spec (four
#   diverging rivals: a `while True do pure ()` prefix spliced ahead of the frozen
#   body, a bare `while True` replacing it, the frozen loop with `decreasing i`
#   deleted, and the frozen loop with a measure supplied but `i` never
#   decremented) — ALL exit 1, the first three with `error: Decreasing annotations
#   are required in total correctness semantics`. So the spec IS complete on the
#   termination axis and there is no verify-does-not-imply-resolve break.
#   Not shippable as a reject case for a TOOLING reason, not a spec one: the
#   termination error is an ELABORATION failure of the module, so it fires inside
#   the witness file too (the gate appends the witness to that same source),
#   leaving `complementFiniteExec` bound to `sorry` — visible as `sorry ()` in the
#   printed goal — so every witness reports `unsolved goals` regardless of claim.
#   Four distinct witness shapes (`≠ DivM.res`, `= DivM.div`, `decide +kernel`,
#   `native_decide`) across three distinct diverging rivals: all exit 1. A reject
#   needs a witness that ELABORATES against its rival and none exists. The nagini
#   sibling carries no diverge-* case either, so nothing was dropped in the port.
# DROPPED (AXIOM_TESTS x1): the axiom lane is G-AX's job (axiom_check.py validates
#   the opaque `contains` trichotomy and the `definiteOut`/`symbolicUnknown`
#   reference folds against the real callee); this gate ignores AXIOM_TESTS
#   regardless.
#
# COVERAGE. The sole obligation (`prove_correct complementFinite`) is DEFENDED
# (pos-control-branch-reorder + pos-control-localvar-reshape +
# pos-control-forward-walk), PROBED FOR REACHABILITY (admiss-f2p-mixed-verdicts)
# and ATTACKED (all seven reject rivals). BOTH independent postcondition clauses
# are attacked, and each is attacked in BOTH directions:
#   (P1) `out.definite = definiteOut elems` — UNDER-count by
#     weak-prepatch-fold / weak-skip-first / weak-skip-last, OVER-count by
#     weak-undecided-leaks-into-definite, WRONG SELECTION by weak-fields-swapped;
#   (P2) `out.symbolic = symbolicUnknown elems` — UNDER-count by
#     weak-symbolic-always-empty / weak-prepatch-fold / weak-skip-first /
#     weak-skip-last, OVER-count by weak-definite-leaks-into-symbolic, WRONG
#     SELECTION by weak-fields-swapped.
# That two-directional pinning is what the audit added: as ported, only (P1) was
# attacked from the over-count side, so a spec that pinned (P2) merely up to
# containment would have passed the whole battery (weak-definite-leaks-into-
# symbolic closes it); and only the index-0 boundary was attacked, though the
# frozen loop STARTS at `i = elems.length`, so the far end was the untested
# boundary (weak-skip-last-element closes it).
# The single input binder `elems` is genuinely varied across the reject witnesses:
# `[7]`, `[5]`, `[6]`, `[4]`, `[15]` (single elements), `[8,9]` and `[13,14]`
# (length 2, exercising each loop boundary from its own end), plus the length-4
# mixed-verdict input `[11,12,2,20]` in the admissibility case — the only input in
# the battery where all THREE verdict classes are live at once. The attacked
# `contains` verdict moves across `unknown` (prepatch, symbolic-empty, leak) and
# `outside` (fields-swapped, skip-first, skip-last, definite-leak) — so no rival
# that mishandled only the `outside` class or only length-1 inputs could hide.
# SEVEN DISTINCT reject input points (pts=7): `[7]`, `[5]`, `[6]`, `[4]`, `[8,9]`,
# `[13,14]`, `[15]`. No two rivals share a refutation point; the near-miss rivals
# (leak vs symbolic-empty vs prepatch; definite-leak vs leak; skip-first vs
# skip-last) sit at distinct inputs and attack distinct clauses or distinct
# directions, so each demonstrates the sub-domain its rationale claims. Each
# witness's single hypothesis is jointly satisfiable (a consistency probe deriving
# `False` from it leaves the goal open — confirmed with a real build, exit 1,
# against the same subject the refutation was checked on). No frame/permission
# rival is fabricated (vacuous on this carrier); the divergence class is
# vacuous-by-rejection under `"total"` (measured), not shipped.
#
# AUDIT PROBES (attack D — NEW wrong impls, aimed at what the shipped rivals leave
# unattacked). The ported rivals all attack the `outside`/`unknown` routing; the
# `inside` (excluded) class, the ORDER and MULTIPLICITY of each field, the far
# loop boundary and the (P2) over-count direction were unprobed. SEVEN new rivals
# were written and built against the frozen spec:
#   * definite field also carries the `inside`-verdict elements   -> REJECTED
#   * symbolic field also carries the `inside`-verdict elements   -> REJECTED
#   * definite field REVERSED (right elements, wrong order)       -> REJECTED
#   * symbolic field DUPLICATED (right elements, doubled)         -> REJECTED
#   * definite field selects every NON-`inside` element           -> REJECTED
#   * LAST element never classified (far boundary)                -> REJECTED  [shipped]
#   * symbolic field over-counted with the definite elements      -> REJECTED  [shipped]
# All seven fail to verify (exit 1), so the two `ensures` pin the exclusion of the
# `inside` class, field order, field multiplicity, both loop boundaries and both
# over-count directions — not merely field membership. No SPEC-TOO-WEAK hole
# found. The last two were additionally given discriminating witnesses (each
# ELABORATES against its rival at exit 0, FAILS against the loop-free reference at
# exit 1 with a SEMANTIC `unsolved goals / h : contains N = Trit.outside / ⊢ False`
# residue, with the opposite-claim forgery SUCCEEDING against that reference at
# exit 0 and the consistency probe leaving `False` open at exit 1) and shipped as
# reject cases, because the clause DIRECTIONS they pin were the two the battery
# could not otherwise demonstrate.
#
# AUDIT PROBES (attack E — NEW correct reshapes, aimed at SPEC-TOO-STRONG). Two
# further verifying impls of the same spec were written beyond the three shipped
# positives: a `List.filter`-based closed form and a `foldr`-based one, each
# proved equal to the frozen folds inline by induction. BOTH verify (exit 0), so
# the two `ensures` are not over-fit to the fold's recursion shape, its traversal
# direction, or its accumulator style. No SPEC-TOO-STRONG hole found; not shipped,
# since pos-control-forward-walk already covers the reshape lane and these add no
# distinct risk.
#
# AXIOM_TESTS: empty. The axiom lane is G-AX's job; this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
