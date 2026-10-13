"""properties.py — G-PBT falsification battery for psf__requests-1921 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution, or against a declared ``witness_reference``).

DEFENDED SURFACE. One contracted method combining two per-key value collections
over a shared key universe:

  effectiveCollection (session request : List Int) return (out : List Int)
    ensures out = combinedSeq session request
    ensures ∀ x ∈ out, x ≠ noneVal

Both inputs are FREE, read-only ``List Int`` values (neither is a ``mut``
binder) and there is no ``require`` clause, so the admitted domain is total.
Two distinguished integers carry the modeled meaning: ``absent`` (= 0) means the
key is not carried by a collection / is dropped from the result, and ``noneVal``
(= -1) means the explicit unset value a caller may store under a key; any other
integer is an ordinary value. The per-key behaviour ``combinedSeq`` realises is:
the per-request value wins where the per-request collection carries the key
(``rv ≠ absent``), else the standing per-session value; then a key whose
effective value equals the unset value is dropped (becomes ``absent``),
regardless of WHICH side contributed that unset value. Positions beyond the
shorter input are not in the shared key universe and are dropped.

The obligation bundles a FULL output equality with the headline drop guarantee:
  (1) the whole result is exactly ``combinedSeq session request`` — every
      aligned position is pinned to the per-key ``combined`` value, and the
      result's LENGTH is pinned to the shared key universe; and
  (2) no position of the result holds the unset value ``noneVal`` — the headline
      guarantee an impl that inspects only the per-request side (leaving a
      per-session-supplied unset value in place) violates.
``combined`` / ``effective`` / ``combinedSeq`` are fully-unfolded functions of
the two inputs (mapping.md §1); there is NO opaque callee.

ADVERSARIAL READ of the nagini classes:
  * FRAME-MUTATION — VACUOUS on this backend. The class exists on nagini because
    an input carries a fractional heap permission an impl can overwrite (both
    inputs there are read-only at a half permission). Lean and Velvet are
    referentially transparent: every parameter is an immutable value, there is
    no heap and no aliasing, and neither input is a ``mut`` binder (``session`` /
    ``request`` are consumed by value; only the local ``result`` is mutated) —
    there is no read-only input to mutate and no substitute probe to build.
    Reported vacuous, not fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully unfolded
    function of the two inputs; there is no opaque answer key to echo. Instead we
    carry an honest cheapest-reshape POSITIVE CONTROL (``pos-oracle-direct``).
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
  * PARTIAL-DOMAIN / VALUE — APPLIES: near-miss impls right on part of the domain
    but diverging on a sub-domain (a per-request-keyed drop; a session-side-only
    drop; a first-position carve-out; a too-aggressive drop that also removes a
    real per-request override; a wrong key universe on unequal-length inputs).
    Each is refuted at a concrete point, and the points vary BOTH input binders
    AND their lengths so no binder is pinned across the battery.

WITNESS MECHANICS — and the ``witness_reference`` this cell requires. The spec
here is a ``method`` CONTRACT, so a witness reaches it through Velvet's own
tester machinery: ``effectiveCollectionTester session request = false`` says the
extracted program's result violates the method's postcondition at that concrete
input, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict.

MEASURED on this bundle: the FROZEN impl keeps a ``while`` loop, and under
``loom.semantics.choice "demonic"`` that loop's fixpoint elaborates through
``Classical.choice``, which the kernel cannot unfold. So ``decide`` against the
frozen tester is stuck for EVERY claim regardless of truth — the frozen side's
exit code carries no information, and a witness refuted "against gold" here
would attest to a refutation that was never performed (the gate reports this as
``witness-undecided``; an earlier revision of this battery recorded exactly that
on all four of its rivals). The repair is the documented one: every reject case
names a shared ``witness_reference`` — ``_LOOPFREE``, a loop-free impl that
returns the per-key combined sequence directly. It shares the frozen spec and
VERIFIES (so it cannot violate its own postcondition), and it REDUCES, so it can
serve as the second half's subject. Each rival is likewise written as a loop-free
reshape of its wrong per-key rule so its own tester reduces.

The reference was checked to be a real two-sided oracle before shipping, not
merely to fail: at ``session=[-1], request=[0]`` it PROVES the tester is ``true``
(gold's answer) and REFUTES ``= false``, so its verdicts track truth rather than
being uniformly negative. ``_LOOPFREE`` is additionally shipped as its own
``expect="verify"`` case (``pos-loopfree-direct``), so the battery itself records
that loop-freeness is not what any rival is being rejected for.

AXIOM lane: EMPTY (the ``axioms`` region declares no ``axiom``; the behaviour is
modeled deeply from the two inputs, so no callee is owed a contract). The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "psf__requests-1921"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each `old` below occurs EXACTLY ONCE in Solution.lean;
# `_IMPL` and `_BODY` lie strictly inside `-- impl-start` / `-- impl-end`, and
# `_PROOF` is the `prove_correct` tactic body — both elided from the consumer
# spec view, so every variant is same_spec by construction. Uniqueness is
# asserted at load by _swap.
# ---------------------------------------------------------------------------

# The whole gold impl body (used by reject rivals that reshape to a loop-free
# expression whose extracted program `decide`-reduces).
_IMPL = """    let mut result : List Int := []
    let mut i := min session.length request.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ min session.length request.length
      invariant result = combinedSeq (session.drop i) (request.drop i)
      done_with i = 0
      decreasing i
    do
      let sv := session[i - 1]!
      let rv := request[i - 1]!
      -- Precedence: the per-request value wins where the per-request collection
      -- carries the key, else the per-session value.
      let ev : Int := if rv ≠ absent then rv else sv
      -- Drop the key (absent) when its effective value is the unset value,
      -- regardless of which side contributed it; otherwise carry it through.
      let val : Int := if ev = noneVal then absent else ev
      result := val :: result
      i := i - 1
    return result"""

# The per-iteration per-key rule (precedence + drop), reshaped by the loop-
# preserving soundness positives so the frozen proof still closes.
_BODY = """      let sv := session[i - 1]!
      let rv := request[i - 1]!
      -- Precedence: the per-request value wins where the per-request collection
      -- carries the key, else the per-session value.
      let ev : Int := if rv ≠ absent then rv else sv
      -- Drop the key (absent) when its effective value is the unset value,
      -- regardless of which side contributed it; otherwise carry it through.
      let val : Int := if ev = noneVal then absent else ev"""

# The `mut result := []` head line; a stable insertion point (occurs once,
# inside the impl region) for an in-region admissibility assert.
_RESULT_HEAD = "    let mut result : List Int := []\n"

# The frozen proof body (tactic-only region; reshaped by variants whose impl
# leaves a different goal).
_PROOF = """prove_correct effectiveCollection by
  loom_solve
  rw [combinedSeq_drop_step session request i (by omega) (by omega) (by omega)]
  simp only [combined, effective, invariant_2]"""


# ---------------------------------------------------------------------------
# The shared witness_reference: a CORRECT, loop-free impl of the frozen spec.
#
# Why this file needs one at all: the frozen impl's `while` loop elaborates
# through `Classical.choice` under demonic choice, so `decide` against the frozen
# tester is stuck for every claim and the frozen side cannot be the subject of a
# refutation (see WITNESS MECHANICS). This impl returns the per-key combined
# sequence directly, so its extracted program kernel-reduces; the whole
# postcondition then falls out by `loom_solve` with no fold step to peel, hence
# the shortened tactic body. Verified: shares the frozen spec, and VERIFIES.
# ---------------------------------------------------------------------------
_LOOPFREE = _swap(
    _swap(_BASE, _IMPL,
          "    -- Loop-free: return the per-key combined sequence over the shared\n"
          "    -- key universe directly, with no accumulation.\n"
          "    return combinedSeq session request"),
    _PROOF,
    "prove_correct effectiveCollection by\n  loom_solve")


def _rival(expr):
    """Gold with its whole impl replaced by a loop-free `List.zipWith` whose
    per-key lambda is `expr`. Loop-free so the extracted program reduces and the
    witness `decide` closes."""
    return _swap(
        _BASE, _IMPL,
        "    -- Loop-free reshape of the per-key rule (observationally the same\n"
        "    -- shape as the gold loop, so the same postcondition is owed).\n"
        "    return List.zipWith (fun sv rv => " + expr + ") session request")


def _tester_witness(session, request):
    """A velvet refutation witness: reach the method's postcondition via the
    derived tester and assert it is `false` at one concrete input. Binds nothing
    (literal inputs only), so there are no hypotheses that could be inconsistent."""
    m = "effectiveCollection"
    return (f"extract_program_for {m}\n"
            f"prove_precondition_decidable_for {m}\n"
            f"prove_postcondition_decidable_for {m}\n"
            f"derive_tester_for {m}\n\n"
            f"example : {m}Tester ({session} : List Int) "
            f"({request} : List Int) = false := by\n"
            f"  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — grounded-oracle direct. `combined` /
    # `effective` are grounded functions of the two inputs, not an opaque
    # answer key, so there is no wrong echo to build. The honest cheapest impl
    # computes them DIRECTLY instead of re-deriving the branches inline; it must
    # verify, else the spec would reject its own grounded per-key functions
    # (SPEC-TOO-STRONG). The loop and every proof obligation are unchanged, so
    # the frozen proof discharges verbatim.
    # =====================================================================
    {
        "id": "pos-oracle-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _BODY,
            "      let sv := session[i - 1]!\n"
            "      let rv := request[i - 1]!\n"
            "      -- Compute the per-key effective value and the combined value via\n"
            "      -- the grounded per-key functions directly, rather than\n"
            "      -- re-deriving the two branches inline.\n"
            "      let ev : Int := effective sv rv\n"
            "      let val : Int := combined sv rv"),
        "rationale": (
            "the per-key functions `effective`/`combined` are grounded (functions "
            "of the two inputs, not an opaque oracle), so the honest cheapest impl "
            "invokes them directly and computes the identical per-key value on "
            "every input; the loop shape and every proof obligation are unchanged, "
            "so the full equality (clause 1) and the drop guarantee (clause 2) "
            "still discharge under the frozen proof. If it fails => SPEC-TOO-STRONG "
            "on its own grounded oracle."),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — structurally different but CORRECT: both
    # branch conditions negated and reordered (take the per-session value UNLESS
    # the per-request side carries the key; carry the effective value through
    # UNLESS it is the unset value). Observationally identical to the gold per-key
    # rule on every input; the loop and both invariants are unchanged, so the same
    # single fold goal remains and `grind` finishes it after the frozen unfold.
    # Must verify; else the spec rejects a faithful reordering (SPEC-TOO-STRONG).
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _BODY,
                "      let sv := session[i - 1]!\n"
                "      let rv := request[i - 1]!\n"
                "      -- Reordered / negated form of the same per-key rule: take the\n"
                "      -- per-session value unless the per-request side carries the\n"
                "      -- key, then carry the effective value through unless it is the\n"
                "      -- unset value.\n"
                "      let ev : Int := if rv = absent then sv else rv\n"
                "      let val : Int := if ev ≠ noneVal then ev else absent"),
            _PROOF,
            _PROOF + "\n  grind"),
        "rationale": (
            "a structurally-different CORRECT impl (both branch conditions negated "
            "and reordered) computes the identical per-key value on every input; "
            "the loop and both invariants are byte-identical so the single fold "
            "goal is unchanged, and `grind` closes the negated branch form after "
            "the frozen unfold. Verifies => the full equality (clause 1) and drop "
            "guarantee (clause 2) hold for the reshaped branches; if it failed the "
            "spec would be SPEC-TOO-STRONG on branch orientation."),
    },

    # =====================================================================
    # POSITIVE CONTROL (soundness) — the loop-free impl that every reject case
    # names as its `witness_reference`, shipped as a case in its own right. It
    # drops the accumulator loop entirely and returns the per-key combined
    # sequence directly: a genuinely different SHAPE (no invariant, no fold step
    # to peel, so the frozen `rw` would have no goal and the tactic body shortens
    # to `loom_solve`). Two jobs: (a) it must verify, else the spec rejects the
    # most direct correct impl of its own post-image (SPEC-TOO-STRONG); and (b)
    # shipping it here records in the battery that loop-freeness is NOT what any
    # rival is rejected for — the rivals are loop-free too, and this one verifies.
    # =====================================================================
    {
        "id": "pos-loopfree-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _LOOPFREE,
        "rationale": (
            "the most direct correct impl of the post-image: return the per-key "
            "combined sequence over the shared key universe with no accumulation. "
            "A different loop SHAPE (no loop at all, hence no invariant and no fold "
            "step), so the whole postcondition falls out of `loom_solve` directly. "
            "Must verify, else the spec is SPEC-TOO-STRONG against its own "
            "post-image. Also the battery's `witness_reference`: shipping it as a "
            "case is what records that the reject rivals are refuted for their "
            "wrong per-key rule, not for being loop-free (this one is loop-free and "
            "VERIFIES)."),
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the usual "a normal input
    # satisfies the precondition" probe is vacuous. Re-aimed at the residual
    # admissibility risk: that the post-image is DEGENERATE / unsatisfiable at the
    # interesting corner. An in-region assert pins the combined collection at an
    # F2P-shaped input (a per-session unset value at key 0 with no per-request
    # entry, a real per-session value at key 1) to the sequence that DROPS key 0
    # to absent and CARRIES key 1 — demonstrating the spec is satisfiable AND
    # non-degenerate there. The impl is otherwise verbatim; the assert adds one
    # `decide`-able goal the proof discharges first, and a false claim at the same
    # point would leave an unsolved `False` goal (verified during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-drop-and-carry",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _RESULT_HEAD,
                "    -- Admissibility / non-degeneracy probe (F2P-shaped input): a\n"
                "    -- per-session unset value at key 0 with no per-request entry, and\n"
                "    -- a real per-session value at key 1, combine to DROP key 0 to\n"
                "    -- absent and CARRY key 1 — so the post-image is satisfiable and\n"
                "    -- non-trivial at the corner the change turns on.\n"
                "    assert (with_name_prefix `admiss\n"
                "      (combinedSeq [noneVal, 5] [absent, absent] = [absent, 5]))\n"
                + _RESULT_HEAD),
            _PROOF,
            "prove_correct effectiveCollection by\n"
            "  loom_solve\n"
            "  · decide\n"
            "  · rw [combinedSeq_drop_step session request i (by omega) (by omega) (by omega)]\n"
            "    simp only [combined, effective, invariant_2]"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at an F2P-shaped "
            "input: a per-session unset value at key 0 (no per-request entry) and a "
            "real per-session value at key 1 combine to `[absent, 5]` — key 0 "
            "dropped, key 1 carried. The in-region assert must discharge (else the "
            "obligation is unsatisfiable / PRECOND-TOO-STRONG at the interesting "
            "corner); the impl is otherwise verbatim so the equality and drop "
            "guarantee still discharge."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real patch
    # would NOT resolve. All five name the shared `_LOOPFREE` witness_reference,
    # because the frozen looping impl cannot decide anything (see WITNESS
    # MECHANICS). Witnesses vary BOTH input binders and their LENGTHS:
    #   session over [-1] / [5,-1] / [0] / [-1,-1] / [5]
    #   request over [0]  / [5,5]   / [-1] / [0,0]   / []
    # =====================================================================
    {
        "id": "weak-per-request-keyed-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug: the drop inspects the PER-REQUEST side (rv) instead of
        # the EFFECTIVE value. Correct on every key EXCEPT one carried only by the
        # per-session collection and set there to the unset value.
        "module": _rival(
            "let ev := if rv ≠ absent then rv else sv; if rv = noneVal then absent else ev"),
        "refinement": (
            "this is the pre-fix behaviour: the drop keys off the per-request side, "
            "so a key carried only by the standing collection and set there to the "
            "unset value survives holding that unset value. Its faithful real patch "
            "is the UNPATCHED combine, which leaves the unset value in the combined "
            "result and emits it — the F2P test that observes such a standing-side "
            "unset key must not appear in the prepared output then FAILS, so it "
            "would NOT resolve."),
        "rationale": (
            "REJECT from the full equality (clause 1) and the drop guarantee "
            "(clause 2): at a key with rv = absent and sv = noneVal the effective "
            "value is noneVal so `combined` = absent, but the rival keys the drop "
            "off rv (≠ noneVal) and keeps noneVal. Refuted at session=[-1], "
            "request=[0]: the correct answer drops to [0], the rival yields [-1] "
            "which holds the unset value."),
        "witness": _tester_witness("[-1]", "[0]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-over-drop-real-override",
        "kind": "uniqueness",
        "expect": "reject",
        # Too-aggressive drop: also drops whenever the per-session value is the
        # unset value, even when the per-request side overrides it with a real
        # value (so the effective value is real and must be carried).
        "module": _rival(
            "let ev := if rv ≠ absent then rv else sv; "
            "if ev = noneVal ∨ sv = noneVal then absent else ev"),
        "refinement": (
            "a faithful real patch that dropped a key whenever the STANDING value "
            "was the unset value — even when the per-request side overrides it with "
            "a real value — would strip a legitimately-set per-request entry. The "
            "PASS_TO_PASS request-construction suite would lose an entry it must "
            "carry, so it would NOT resolve."),
        "rationale": (
            "REJECT from the full equality (clause 1): at a key with sv = noneVal "
            "and a real rv the per-request value wins so `combined` = rv, but the "
            "rival drops it to absent. Refuted at session=[5,-1], request=[5,5]: at "
            "key 1 the correct answer carries 5, the rival drops it — a two-element "
            "point distinct from the other rivals'."),
        "witness": _tester_witness("[5, -1]", "[5, 5]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-session-side-only-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # A distinct near-miss: drop only when the STANDING (session) value is the
        # unset value, ignoring an effective value that is unset because the
        # per-request side supplied it. Mirrors the per-request-keyed bug on the
        # opposite side.
        "module": _rival(
            "let ev := if rv ≠ absent then rv else sv; if sv = noneVal then absent else ev"),
        "refinement": (
            "a real patch that dropped a key only when the STANDING value was the "
            "unset value would leave in place an effective unset value contributed "
            "by the per-request side; the F2P observable (no combined position "
            "holds the unset value) can land on that key, so it would NOT resolve."),
        "rationale": (
            "REJECT from the drop guarantee (clause 2) and the equality (clause 1): "
            "at a key with sv = absent and rv = noneVal the per-request value wins "
            "so the effective value is noneVal and `combined` = absent, but the "
            "rival (sv ≠ noneVal) keeps noneVal. Refuted at session=[0], "
            "request=[-1]: the correct answer drops to [0], the rival yields [-1]."),
        "witness": _tester_witness("[0]", "[-1]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-first-position-carve-out",
        "kind": "uniqueness",
        "expect": "reject",
        # A carve-out a "most positions" fuzzer would miss: correct at every
        # position k > 0 but at k == 0 it carries the effective value through with
        # NO unset-drop. The universal over all positions catches it.
        "module": _swap(
            _BASE, _IMPL,
            "    -- Loop-free reshape with a first-position carve-out: the unset-drop\n"
            "    -- is skipped at position 0 and applied only at later positions.\n"
            "    return (List.zipWith (fun sv rv => if rv ≠ absent then rv else sv) "
            "session request).mapIdx\n"
            "      (fun k ev => if k > 0 ∧ ev = noneVal then absent else ev)"),
        "refinement": (
            "a real patch that skipped the unset-drop for the first key would still "
            "emit an unset value at that position; the F2P observable can fall on "
            "the first key, so the test FAILS — it would NOT resolve."),
        "rationale": (
            "REJECT from the full equality (clause 1) and the drop guarantee "
            "(clause 2): the universal over all positions pins EVERY position, so a "
            "position-0-only carve-out an under-quantified fuzzer would miss is "
            "caught. Refuted at session=[-1,-1], request=[0,0]: at key 0 the correct "
            "answer drops to absent but the rival keeps noneVal — a distinct "
            "two-element point."),
        "witness": _tester_witness("[-1, -1]", "[0, 0]"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "weak-wrong-key-universe",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the LENGTH half of clause 1, which no per-key rival reaches:
        # every other witness holds the two inputs at EQUAL length, so a rival that
        # got the shared key universe wrong would slip past them all. This rival
        # takes the universe to be the per-session side, defaulting a missing
        # per-request entry to absent, instead of the SHARED universe (the shorter
        # side). Identical to gold whenever the lengths agree.
        "module": _swap(
            _BASE, _IMPL,
            "    -- Loop-free reshape taking the key universe to be the per-session\n"
            "    -- side, with a missing per-request entry defaulted to absent.\n"
            "    return session.mapIdx (fun k sv =>\n"
            "      let rv := (request[k]?).getD absent\n"
            "      let ev : Int := if rv ≠ absent then rv else sv\n"
            "      if ev = noneVal then absent else ev)"),
        "refinement": (
            "a real patch that took the key universe from the standing collection "
            "alone would carry entries the per-request side never shared, emitting a "
            "standing entry the caller's own collection had already narrowed away. "
            "The PASS_TO_PASS request-construction suite compares the prepared "
            "output's entries exactly, so an extra carried entry FAILS it — it would "
            "NOT resolve."),
        "rationale": (
            "REJECT from the LENGTH half of the full equality (clause 1): "
            "`combinedSeq` is defined over the SHARED key universe and returns [] "
            "once either side runs out, so the result length is the shorter input's. "
            "Refuted at session=[5], request=[]: the correct answer is [] but the "
            "rival returns [5]. This is the only witness with UNEQUAL input lengths "
            "— every per-key rival above is refuted at equal lengths, where this "
            "rival agrees with the correct answer everywhere, so the length clause "
            "would otherwise go unattacked."),
        "witness": _tester_witness("[5]", "[]"),
        "witness_reference": _LOOPFREE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 cases (1 soundness
# positive, 1 admissibility, 3 uniqueness/partial-domain rivals, 1 frame-mutation
# rival, 1 oracle "positive control") over the single modeled function
# effective_collection(session, request, n). This bundle models the same one
# behaviour as `effectiveCollection session request` (the length binder `n` is
# folded into `min session.length request.length` — the shared key universe — so
# there is no separate `n` binder to attack, but the universe it determines IS
# attacked, by weak-wrong-key-universe).
#
#   nagini case                              -> here
#   ---------------------------------------------------------------------
#   oracle-direct-positive                   -> pos-oracle-direct           PORTED
#   pos-control-branch-reorder-fused         -> pos-branch-reorder          PORTED
#   admissibility-f2p-shaped-self-call       -> admiss-f2p-drop-and-carry   RE-AIMED
#   partial-domain-prepatch-rv-keyed-drop    -> weak-per-request-keyed-drop PORTED
#   over-drop-real-request-override          -> weak-over-drop-real-override PORTED
#   partial-domain-first-element-no-drop     -> weak-first-position-carve-out PORTED
#   (new, opposite-side mirror of prepatch)  -> weak-session-side-only-drop ADDED
#   (new, attacks the length/universe clause)-> weak-wrong-key-universe     ADDED
#   (new, the shared witness_reference)      -> pos-loopfree-direct         ADDED
#   frame-mutation-write-session             -> (none)                      VACUOUS
#   (nagini carries no divergence case)      -> (none)                      SPEC-CLOSED
#
# 5 ported, 1 re-aimed, 3 added, 1 vacuous.
#
# RE-AIMED (admissibility): the nagini case builds an F2P-shaped input and self-
#   calls to prove the precondition is establishable. Here there is no `require`
#   clause, so that reading is vacuous (nothing could exclude the input). The
#   case is re-aimed at proving the post-image is satisfiable and NON-degenerate
#   at the F2P corner (a standing unset value at key 0 with no per-request entry,
#   a real value at key 1 -> drop key 0, carry key 1). The in-region assert is a
#   live `decide`-able goal the proof discharges; a false claim at the same point
#   leaves an unsolved goal (verified during authoring).
# ADDED (weak-session-side-only-drop): the opposite-side mirror of the
#   per-request-keyed drop. It probes the sub-domain where the effective unset
#   value is contributed by the PER-REQUEST side (sv = absent, rv = noneVal),
#   which the prepatch rival (rv-keyed) happens to handle correctly — so it is a
#   genuinely distinct wrong rule with its own separating witness, not a
#   near-miss of an existing rival.
# ADDED (weak-wrong-key-universe): closes the binder-coverage gap the per-key
#   rivals leave. All four of those are refuted at EQUAL input lengths, so the
#   length half of clause 1 — `combinedSeq` stopping at the shorter side — was
#   attacked by nothing, and a rival that took the universe from one side alone
#   would have verified against the whole battery. Refuted at unequal lengths
#   (session=[5], request=[]), the one point where it differs from gold.
# ADDED (pos-loopfree-direct): the shared `witness_reference`, shipped as an
#   expect="verify" case so the battery records that loop-freeness is not the
#   property any rival is rejected for.
# FRAME-MUTATION: VACUOUS here. The nagini rival WRITES a read-only input held at
#   a fractional permission. This backend is referentially transparent, has no
#   heap and no aliasing, and this bundle declares NO `mut` binder among the
#   parameters (`session`/`request` are consumed by value; only the local
#   `result` is mutated) — there is no read-only input to overwrite and no
#   substitute probe to build. No case fabricated.
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
# BINDER / POINT COVERAGE. The five reject witnesses probe five distinct inputs:
#   (session=[-1],    request=[0])      weak-per-request-keyed-drop
#   (session=[5,-1],  request=[5,5])    weak-over-drop-real-override
#   (session=[0],     request=[-1])     weak-session-side-only-drop
#   (session=[-1,-1], request=[0,0])    weak-first-position-carve-out
#   (session=[5],     request=[])       weak-wrong-key-universe
#   so `session` is varied over [-1] / [5,-1] / [0] / [-1,-1] / [5] and `request`
#   over [0] / [5,5] / [-1] / [0,0] / []. Neither input binder is pinned across
#   the battery; the points span length-1, length-2 and UNEQUAL-length inputs;
#   and each of the three per-key roles (a standing unset value, a per-request
#   unset value, a real per-request override of an unset standing value) is the
#   discriminator of some witness. Both top-level clauses are attacked: the full
#   equality (clause 1) by every rival — its per-key half by four of them and its
#   LENGTH half by weak-wrong-key-universe — and the drop guarantee (clause 2)
#   specifically by the per-request-keyed drop, the session-side-only drop and
#   the first-position carve-out.
#
# WITNESS DISCRIMINATION (measured, per case, before shipping). The frozen
#   looping impl cannot decide anything under demonic choice, so every reject case
#   names the shared loop-free `_LOOPFREE` reference and each witness was built
#   BOTH ways by hand: it elaborates against its rival (exit 0) and is REFUTED
#   against `_LOOPFREE` with `decide proved that the proposition ... is false`
#   — a real verdict, not the `did not reduce to isTrue or isFalse` stuck
#   reduction that an earlier revision of this battery recorded against gold on
#   all four of its rivals. `_LOOPFREE` itself was checked to decide in BOTH
#   directions at (session=[-1], request=[0]) — proving the tester `true` and
#   refuting `false` — so it is a two-sided oracle rather than an impl that
#   merely fails everything. No witness binds a hypothesis (all inputs are
#   literals), so the consistency probe is not applicable.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom (the behaviour is modeled deeply from the two inputs), so there is
# nothing there to probe.
AXIOM_TESTS = []
