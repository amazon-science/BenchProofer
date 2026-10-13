"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-13124 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, and —
where a case legitimately re-proves — the ``prove_correct`` tactic body, are
changed; both are elided from the consumer spec view, so ``markers.same_spec``
holds and the ``prove_correct perClassShuffles`` obligation survives with a
byte-identical statement). ``expect="verify"`` passes iff (in scope AND
verifies); ``expect="reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: it elaborates against the rival and FAILS
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  perClassShuffles (counts : List Nat) (nSplits : Nat) (s : Int)
      return (out : List (List Nat))
    ensures out = (threadAll nSplits s counts).1

  ``threadAll`` is a left-fold that threads ONE shared source through the classes
  in order: element ``k`` is the permutation the source (selected by ``s``)
  yields for class ``k``'s block AFTER the source has already been consumed by
  every earlier class (the accumulated residue = the earlier block sizes). Each
  block is ``blockSize nSplits count = max count nSplits`` positions. So the
  single ``ensures`` binds three things jointly on the WHOLE domain:
    * the OUTER structure — one permutation per class, in class order (length);
    * the block size handed to the source per class (``max count nSplits``);
    * the RESIDUE handed to the source per class — the source advances across
      classes and is never restarted, so element ``k`` depends on classes
      ``0..k-1`` and distinct configuration values ``s`` give distinct per-class
      shuffles.
  The failing scenario asserts that two distinct configuration values produce
  DIFFERENT sorted per-fold test sets, which holds only if the per-class draws
  genuinely advance (the residue is load-bearing), not if every class is drawn
  from the source in its initial state.

CARRIER NOTE — why this port refutes through the Hoare triple, not a tester.

  The source is an OPAQUE axiom (``shuffleAfter : Int → List Nat → Nat →
  List Nat``), so ``threadAll`` is ``noncomputable``. Two consequences drive
  every design choice below:

   1. The ``extract_program_for`` / ``derive_tester_for`` + ``decide`` witness
      route is UNAVAILABLE: extraction cannot compile a program whose
      postcondition depends on a noncomputable term. So each reject ``witness``
      refutes the method's Hoare triple DIRECTLY at a concrete input —
      ``¬ triple True (perClassShuffles …) (fun out => out = (threadAll …).1)`` —
      reduced through ``triple_pure`` for the straight-line (pure-``return``)
      rivals, checked in a file whose ``prove_correct`` block has been stripped
      so no tactic script interferes.

      WITNESS SUBJECT — why every reject case names a ``witness_reference``.
      ``triple_pure`` peels the triple only for a straight-line ``return``. The
      FROZEN impl is a ``while`` loop, so against gold the triple stays an
      un-normalised ``forIn Lean.Loop.mk …`` term and the hypothesis ``hEq`` is
      never reduced at all: gold's build then fails because the tactic could not
      GET to the claim, not because the claim is false there. Measured, with the
      two experiments the audit protocol requires:
        * FORGERY (flip the claim): the same witness with the ``¬`` DROPPED —
          i.e. asserting the impl is CORRECT at that input, which for gold is
          TRUE — also fails against gold, with the same un-reduced loop term
          (exit 1). Gold's exit code therefore carried NO information about the
          claim.
        * A WRONG impl that KEEPS THE LOOP (residue dropped inside the loop
          body) fails with an error body byte-identical to gold's but for the
          one sub-term that differs, so the shape does not track wrongness.
        * REVEAL (``exact (hEq : Nat)``) prints ``hEq``'s real type: against
          gold, the whole ``forIn Lean.Loop.mk`` triple (nothing reduced);
          against the loop-free verifying reference, ``True`` — ``simp`` PROVED
          the equation there, which is the genuine refutation.
      So each reject case is refuted against a ``witness_reference`` instead: the
      loop-free ``return (threadAll nSplits s counts).1`` impl, which shares the
      frozen spec and VERIFIES (the gate re-checks both before using it). An impl
      the verifier accepts cannot violate its own spec, so a genuine witness must
      still fail there — and against it the witnesses reduce, so the exit code
      tracks the claim: the witness fails (``h : … ⊢ False``, exit 1) while the
      flipped claim SUCCEEDS (exit 0). That pair is the discrimination.
   2. What is DISCRIMINABLE is narrowed by the opacity. We do not need to know
      what ``shuffleAfter`` COMPUTES to refute a rival that hands it the WRONG
      RESIDUE or the WRONG BLOCK SIZE: it is enough to ASSUME the two source
      results differ (the residue/block-size rivals below each carry one such
      hypothesis, whose satisfiability the gate independently checks). What is
      refutable WITHOUT any assumption is the OUTER structure (the list length —
      one permutation per class).

ADVERSARIAL READ of the weakness classes (others justified-N/A in `assessment`):
  * WRONG RESIDUE / value — APPLIES, conditioned on the carrier. The nagini
    headline rivals draw every class from the SAME initial state (residue
    dropped = the prepatch bug), anchor the stream one draw advanced, or advance
    two draws per class. Each ports as a rival threading the WRONG residue into
    ``shuffleAfter``, refuted at a concrete input under one hypothesis that two
    source results (differing only in residue) differ.
  * WRONG BLOCK SIZE / nSplits — APPLIES against the transparent ``blockSize``
    structure. A rival that permutes a block of ``count`` positions instead of
    ``max count nSplits`` refutes the clause where ``count < nSplits`` under one
    hypothesis that two source results (differing only in block size) differ;
    this is the case that makes ``nSplits`` load-bearing.
  * PARTIAL-DOMAIN / structure — APPLIES against the OUTER shape. A rival that
    produces one fewer permutation than there are classes (drops the last class)
    refutes the clause via list LENGTH with NO hypothesis.
  * UNGROUNDED-ORACLE ECHO — N/A as a wrong echo. The clause is grounded in
    ``threadAll`` (a fold over the actual inputs ``counts``/``nSplits``/``s``),
    not an opaque answer-key: satisfying it requires threading each class through
    the source with the correct residue and block size, which the positive
    controls do (one reshapes the loop, one materializes the fold directly).
  * ADMISSIBILITY — APPLIES, and shipped as ``S-admiss-f2p-point``. The method
    carries no ``require`` clause, but "no precondition" is NOT a reason to drop
    the lane: the analogue on a total carrier is the obligation being
    UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
    discharges the obligation AT that concrete input — as an in-region ``assert``,
    before closing the frozen obligation verbatim — tests directly. The F2P
    scenario's shape is two equal-sized classes with the split count equal to the
    class size, so the case asserts the obligation's own value at that point
    (``counts = [5,5]``, ``nSplits = 5``, ``s = 0``) and then proves the frozen
    ``ensures`` unchanged. LIVENESS CONFIRMED: falsifying the asserted value to
    the residue-free one makes the build FAIL with ``unsolved goals … ⊢
    shuffleAfter 0 [5] 5 = shuffleAfter 0 [] 5``, so this case's exit 0 is
    contingent on the claim it makes and not on the assert being elided.
  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling has no frame rival
    for this instance (both inputs are ints passed by value; there is no
    read-only reference and no ``list_pred`` input). This backend is likewise
    referentially transparent: every parameter is an immutable value, no ``mut``
    input binder, no heap, no aliasing. No expressible instance; no substitute
    fabricated.

WITNESS PLACEMENT / coverage. The three binders ``counts``/``nSplits``/``s`` are
varied across FIVE distinct input points (pts=5): the reject witnesses range
``counts`` over ``[3,4]``/``[5]``/``[2,3]``/``[2]``, ``nSplits`` over
``2``/``3``/``5``, and ``s`` over ``0``/``1``/``7``. Rivals share no witness:
each fails for a distinct reason at a distinct point (residue dropped; residue
anchored one block advanced; residue advanced two blocks per class; block size
missing the ``nSplits`` floor; missing last class via length). The value rivals
each condition on ONE hypothesis (two source results differ), whose
satisfiability the gate confirms by failing to derive ``False`` from it; never
two hypotheses about the same term.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-13124"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique in Solution.lean; both facts asserted at load by _swap) ------

# The whole loop-based impl body (text strictly between -- impl-start and
# -- impl-end). Replaced wholesale by the structure/value-attacking rivals and
# by the direct-materialize positive control, which abandon the loop.
_IMPL = (
    "    let mut result : List (List Nat) := []\n"
    "    let mut prev : List Nat := []\n"
    "    let mut i := 0\n"
    "    while i < counts.length\n"
    "      invariant i ≤ counts.length\n"
    "      invariant (result, prev) = (counts.take i).foldl (threadStep nSplits s) ([], [])\n"
    "      done_with i = counts.length\n"
    "      decreasing counts.length - i\n"
    "    do\n"
    "      let count := counts[i]!\n"
    "      let sz := blockSize nSplits count\n"
    "      result := result ++ [shuffleAfter s prev sz]\n"
    "      prev := prev ++ [sz]\n"
    "      i := i + 1\n"
    "    return result\n"
)

# The three loop-body lines that bind `count`, compute `sz`, and append. The
# inline positive control folds `count` into the `sz` computation — a data-flow
# reshape that keeps the accumulated result definitionally identical, so the
# frozen tactic script still closes.
_INNER = (
    "      let count := counts[i]!\n"
    "      let sz := blockSize nSplits count\n"
)

# The frozen proof body (tactic script only; elided from the spec view). The
# rivals and the direct-materialize positive control reshape the impl into a
# single expression, so there is no loop invariant to peel: they retune the
# proof to a bare `loom_solve`. For the rivals that then FAILS (the point,
# attributed by the witness, not by a stale tactic script tuned to a loop that
# no longer exists); for the direct-materialize positive it CLOSES.
_PROOF = (
    "prove_correct perClassShuffles by\n"
    "  loom_solve\n"
    "  · have hi : i < counts.length := by omega\n"
    "    have hr := congrArg Prod.fst invariant_2\n"
    "    have hp := congrArg Prod.snd invariant_2\n"
    "    simp only at hr hp\n"
    "    rw [hr, hp, threadAll_take_step nSplits s counts i hi, threadStep, blockSize]\n"
    "  · have hr := congrArg Prod.fst invariant_2\n"
    "    simp only at hr\n"
    "    have hlen : i = counts.length := done_1\n"
    "    subst hlen\n"
    "    rw [List.take_length] at hr\n"
    "    simp_all [threadAll]\n"
)
_PROOF_FLAT = "prove_correct perClassShuffles by\n  loom_solve\n"

assert _BASE.count(_IMPL) == 1, "impl anchor drift — re-sync _IMPL"
assert _BASE.count(_INNER) == 1, "inner anchor drift — re-sync _INNER"
assert _BASE.count(_PROOF) == 1, "proof anchor drift — re-sync _PROOF"


def _expr_rival(return_body):
    """A full Solution.lean whose impl is a single straight-line expression and
    whose proof is the flat `loom_solve` (which fails for a wrong rival — the
    rejection is then attributed by the witness). Edits ONLY the impl and proof
    regions, so `same_spec` holds and the obligation statement is unchanged."""
    return _swap(_swap(_BASE, _IMPL, return_body), _PROOF, _PROOF_FLAT)


# ---- witness helper. The postcondition is noncomputable, so a witness refutes
# ---- the method's Hoare triple directly at a concrete input, checked in a file
# ---- whose `prove_correct` block has been stripped. `head` optionally declares
# ---- the example's binder (a hypothesis that two source results differ, for the
# ---- value rivals); `refute` is the tactic body after the triple is peeled.
def _witness(head, counts_lit, nsplits_lit, s_lit, refute):
    return (
        f"example {head}:\n"
        f"    ¬ (triple (l := Prop) True\n"
        f"    (perClassShuffles {counts_lit} {nsplits_lit} {s_lit})\n"
        f"    (fun out => out = (threadAll {nsplits_lit} {s_lit} {counts_lit}).1)) := by\n"
        f"  unfold perClassShuffles\n"
        f"  simp only [triple_pure, le_Prop_eq, true_implies]\n"
        f"{refute}"
    )


# The value-rival refutation body: reduce the goal to the hypothesis `h` that the
# two source results differ, by unfolding the fold and the source application.
#
# The unfolding `simp only` is guarded by `try`, and that is load-bearing rather
# than defensive. It runs against TWO subjects: the rival (where it fires and
# leaves the rival's concrete list equated to the spec's) and the
# `witness_reference` (where `simp` has ALREADY closed the equation, so `hEq` is
# `True` and the unfolding step has nothing left to do). Un-guarded, that second
# build died on `` `simp` made no progress `` — a TACTIC error rather than a
# refutation, which is exactly the uninformative exit code this repair exists to
# remove. With the guard, the reference-side failure is the semantic one
# (`h : ¬… ⊢ False`: the hypothesis cannot be contradicted because the reference
# genuinely satisfies the spec there) and the flipped claim SUCCEEDS on that same
# subject — so the exit code tracks the claim.
_VALUE_REFUTE = (
    "  intro hEq\n"
    "  apply h\n"
    "  try simp only [threadAll, threadStep, blockSize, List.foldl] at hEq\n"
    "  simp_all\n"
)

# The loop-free correct impl every reject case refutes its witness against. It
# IS the spec's own fold materialized, it shares the frozen spec, and it VERIFIES
# (it is also shipped as the `S-pos-materialize-fold` positive control, and the
# gate independently re-checks both facts before using it as a subject). Needed
# because `triple_pure` cannot peel the frozen impl's `while` loop, so against
# gold no witness — true, false, or flipped — is ever reduced; see the CARRIER
# NOTE's WITNESS SUBJECT paragraph for the builds that establish this.
_WITNESS_REF = _expr_rival("    return (threadAll nSplits s counts).1\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the spec is SPEC-TOO-STRONG. Neither introduces a
    # helper lemma, an axiom, or an assumption token; both keep the
    # `prove_correct perClassShuffles` obligation byte-identical.
    # =====================================================================
    {
        "id": "S-pos-inline-blocksize",
        "kind": "soundness",
        "expect": "verify",
        # Fold the per-class binding into the block-size computation: the
        # accumulated `result`/`prev` are DEFINITIONALLY identical, so
        # `loom_solve` leaves the same single loop-body goal and the frozen
        # tactic script (`rw [threadAll_take_step …]; …`) discharges it unchanged.
        # (Verified during authoring: verifies, exit 0. Frozen proof retained.)
        "module": _swap(
            _BASE, _INNER,
            "      let sz := blockSize nSplits counts[i]!\n"),
        "rationale": "Inlining the per-class count into the block-size computation "
                     "leaves the accumulated `result`/`prev` definitionally "
                     "identical, so `out = (threadAll nSplits s counts).1` still "
                     "holds on the whole domain and the frozen proof closes without "
                     "change. A correct reshape that failed to verify would mean the "
                     "spec is SPEC-TOO-STRONG on the impl's data-flow shape.",
    },
    {
        "id": "S-pos-materialize-fold",
        "kind": "soundness",
        "expect": "verify",
        # A structurally DIFFERENT control flow: no loop at all — return the
        # threaded fold directly. Still correct (it IS the spec's own fold), and
        # the strongest honest cheapest impl: materializing the grounded fold is
        # the real work. Proof retuned to the flat `loom_solve`, which closes for
        # the definitional-equality shape. (Verified during authoring: exit 0.)
        "module": _expr_rival("    return (threadAll nSplits s counts).1\n"),
        "rationale": "Returning the threaded fold directly (no loop) is the honest "
                     "cheapest correct impl — it materializes the grounded fold, "
                     "which is the real work — so it must verify on the whole "
                     "domain; the flat `loom_solve` closes the definitional "
                     "equality. A correct impl of a structurally different shape "
                     "that failed would mean SPEC-TOO-STRONG.",
    },
    {
        "id": "S-pos-commuted-max",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY THE AUDIT (attack E). The two existing positives are both
        # DEFINITIONALLY equal to the frozen impl's accumulation — one inlines a
        # `let`, one returns the fold itself — so neither exercises a reshape the
        # spec has to be proven THROUGH. This one commutes the block-size
        # arguments (`max nSplits c` for `blockSize nSplits c = max c nSplits`),
        # which is NOT definitional: `simp`/`rfl` do not close it and the flat
        # `loom_solve` alone FAILS (`unsolved goals … max nSplits c … = … max c
        # nSplits …`, measured). It needs `Nat.max_comm` to be discharged, so it
        # is a faithful correct impl the spec accepts only via a real proof step.
        # If the spec rejected it, `nSplits`/`count` argument order would be
        # over-constrained (SPEC-TOO-STRONG).
        "module": _expr_rival(
            "    return (counts.foldl (fun acc c => "
            "(acc.1 ++ [shuffleAfter s acc.2 (max nSplits c)], "
            "acc.2 ++ [max nSplits c])) ([], [])).1\n").replace(
                _PROOF_FLAT,
                "prove_correct perClassShuffles by\n"
                "  loom_solve\n"
                "  unfold threadAll threadStep blockSize\n"
                "  simp only [Nat.max_comm]\n"),
        "rationale": "Computing each block as `max nSplits c` rather than `blockSize "
                     "nSplits c = max c nSplits` is the SAME block size on every "
                     "input (`max` is commutative), so this is a faithful correct "
                     "impl and must verify. Unlike the other two positives it is not "
                     "definitionally equal to the frozen accumulation: the flat "
                     "`loom_solve` does NOT close it (measured: `unsolved goals … max "
                     "nSplits c … = … max c nSplits …`) and the proof needs "
                     "`Nat.max_comm`. So the spec accepts it only through a real "
                     "proof step, which is what makes it a load-bearing "
                     "SPEC-TOO-STRONG probe rather than a restatement of the frozen "
                     "impl; a faithful reshape the spec REJECTED would mean the "
                     "argument order of the block-size computation is "
                     "over-constrained.",
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete
    # input and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing scenario.
    # =====================================================================

    # ---- WRONG RESIDUE (the prepatch bug): draw EVERY class from the source in
    # ---- its INITIAL state (residue `[]`), never from the source as advanced by
    # ---- earlier classes. Refuted under the hypothesis that the two source
    # ---- results (empty vs one-block residue) differ, at a two-class input.
    {
        "id": "S-reset-residue",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _expr_rival(
            "    return counts.map (fun c => shuffleAfter s [] (blockSize nSplits c))\n"),
        "refinement": "Drawing every class from the source in its initial state "
                      "(residue dropped) is exactly the pre-existing data-flow: a "
                      "source re-obtained from the raw configuration value inside "
                      "each class, so every class is permuted identically from the "
                      "initial state. The failing scenario asserts that two distinct "
                      "configuration values give DIFFERENT sorted per-fold test "
                      "sets; with identical per-class draws the sorted multiset is "
                      "configuration-invariant, so the assertion still FAILS. It "
                      "would NOT resolve — this is the leg's prepatch.",
        "rationale": "REJECT from `out = (threadAll nSplits s counts).1`: the spec "
                     "threads the accumulating residue into class 1 "
                     "(`shuffleAfter s [blockSize …] …`) while the rival hands it "
                     "the empty residue (`shuffleAfter s [] …`). Verifying would "
                     "leave the residue unpinned (SPEC-TOO-WEAK on the threading). "
                     "Refuted at a two-class `[3,4]` input under the hypothesis that "
                     "the two source results (empty vs one-block residue) differ.",
        "witness": _witness(
            "(h : shuffleAfter 0 [] 4 ≠ shuffleAfter 0 [3] 4) ",
            "[3, 4]", "2", "0", _VALUE_REFUTE),
        "witness_reference": _WITNESS_REF,
    },

    # ---- WRONG RESIDUE (anchor advanced): the source starts from a NON-EMPTY
    # ---- residue, so class 0 is permuted from an already-advanced source rather
    # ---- than the source's initial state. Refuted under the hypothesis that the
    # ---- two class-0 source results (empty vs one-block residue) differ.
    {
        "id": "S-start-advanced",
        "kind": "uniqueness",
        "expect": "reject",
        # ANCHOR BLOCK SIZE = 2, not 1, and that is a correctness fix rather
        # than a cosmetic one. A block of ONE position has only one arrangement,
        # so a real source is not consumed by permuting it: measured against the
        # real callee, residue `[1]` and residue `[]` yield the IDENTICAL next
        # permutation, which makes the `[1]`-anchored impl behaviourally EQUAL to
        # gold on the carrier's own intended reading and the witness's hypothesis
        # (`shuffleAfter 0 [] 5 ≠ shuffleAfter 0 [1] 5`) FALSE of the callee the
        # axiom denotes. The gate could not see it — `shuffleAfter` is opaque, so
        # no tactic derives `False` from the hypothesis and the consistency probe
        # passes — but the case would have attested to rejecting a rival that is
        # not wrong. Residue `[2]` is a block that genuinely consumes the source
        # (`shuffleAfter 0 [] 5 ≠ shuffleAfter 0 [2] 5` holds of the real callee),
        # so the re-anchored rival is observably wrong and the hypothesis is true.
        "module": _expr_rival(
            "    return (counts.foldl (threadStep nSplits s) ([], [2])).1\n"),
        "refinement": "Starting the shared source from a non-empty residue draws an "
                      "extra throw-away permutation before the first class, so every "
                      "class's permutation is shifted by one block relative to the "
                      "gold. The real patched behaviour would then produce a "
                      "different (though still configuration-dependent) per-fold "
                      "assignment than the gold on the failing scenario's input; the "
                      "exact sorted test sets the scenario (and the deterministic "
                      "fold layout the existing coverage/index checks assume) change "
                      "— the faithful real patch does NOT resolve. The throw-away "
                      "block is TWO positions, not one: a one-position block has a "
                      "single arrangement and so consumes nothing from a real source, "
                      "which would make the shifted impl agree with gold rather than "
                      "differ from it.",
        "rationale": "REJECT from `out = (threadAll nSplits s counts).1`: at index 0 "
                     "the spec permutes from the empty residue (`shuffleAfter s [] "
                     "…`) while the rival permutes from `[2]`. Verifying would leave "
                     "the source's anchor unpinned (SPEC-TOO-WEAK). Refuted at a "
                     "one-class `[5]` input, `nSplits=3`, under the hypothesis that "
                     "the two class-0 source results differ — a hypothesis that is "
                     "TRUE of the real callee for a two-position anchor block (and "
                     "would be FALSE for a one-position one, which is why the anchor "
                     "is `[2]`).",
        "witness": _witness(
            "(h : shuffleAfter 0 [] 5 ≠ shuffleAfter 0 [2] 5) ",
            "[5]", "3", "0", _VALUE_REFUTE),
        "witness_reference": _WITNESS_REF,
    },

    # ---- WRONG RESIDUE (granularity): the residue advances by TWO blocks per
    # ---- class instead of one (an extra spurious draw per class). Correct at
    # ---- class 0; wrong from class 1. Refuted under the hypothesis that the two
    # ---- class-1 source results (one- vs two-block residue) differ.
    {
        "id": "S-double-advance",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _expr_rival(
            "    return (counts.foldl (fun acc c => "
            "(acc.1 ++ [shuffleAfter s acc.2 (blockSize nSplits c)], "
            "acc.2 ++ [blockSize nSplits c, blockSize nSplits c])) ([], [])).1\n"),
        "refinement": "Advancing the shared source by TWO blocks between classes "
                      "(an extra spurious draw per class) makes class 1's "
                      "permutation the source state after two blocks, not one. The "
                      "real patched behaviour's per-fold test sets then differ from "
                      "the gold's at every class beyond the first; the gold's exact "
                      "sorted per-fold assignment (which the failing scenario pins, "
                      "and which the existing split/coverage checks depend on) "
                      "changes — the faithful real patch does NOT resolve.",
        "rationale": "REJECT from `out = (threadAll nSplits s counts).1`: at index 1 "
                     "the spec threads a one-block residue while the rival threads a "
                     "two-block residue. Verifying would leave the advance "
                     "granularity unpinned (SPEC-TOO-WEAK). Correct only at class 0. "
                     "Refuted at a two-class `[3,4]` input, `s=1` (a distinct point "
                     "from S-reset-residue), under the hypothesis that the two "
                     "class-1 source results differ.",
        "witness": _witness(
            "(h : shuffleAfter 1 [3] 4 ≠ shuffleAfter 1 [3, 3] 4) ",
            "[3, 4]", "2", "1", _VALUE_REFUTE),
        "witness_reference": _WITNESS_REF,
    },

    # ---- WRONG BLOCK SIZE (nSplits floor dropped): permute a block of `count`
    # ---- positions instead of `max count nSplits`. Invisible where
    # ---- count >= nSplits; wrong where count < nSplits. Attacks the transparent
    # ---- `blockSize` clause and makes `nSplits` load-bearing. Refuted under the
    # ---- hypothesis that the two source results (block sizes 5 vs 2) differ.
    {
        "id": "S-ignore-nsplits",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _expr_rival(
            "    return (counts.foldl (fun acc c => "
            "(acc.1 ++ [shuffleAfter s acc.2 c], acc.2 ++ [c])) ([], [])).1\n"),
        "refinement": "Permuting a block of `count` positions instead of "
                      "`max count nSplits` gives a block too small whenever a class "
                      "has fewer members than there are splits — the block must "
                      "never be smaller than the number of requested splits. The "
                      "real patched behaviour would then permute the wrong number of "
                      "positions for a small class, producing a per-fold assignment "
                      "that diverges from the gold and mis-sizes folds. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "REJECT from `out = (threadAll nSplits s counts).1`: the spec "
                     "permutes a block of `blockSize nSplits count = max count "
                     "nSplits` positions while the rival uses `count`. Verifying "
                     "would leave the `nSplits` floor unpinned (SPEC-TOO-WEAK), so "
                     "this is the case that makes `nSplits` load-bearing. Refuted at "
                     "a one-class `[2]` input, `nSplits=5` (where count < nSplits), "
                     "under the hypothesis that the two source results (block sizes "
                     "5 vs 2) differ.",
        "witness": _witness(
            "(h : shuffleAfter 0 [] 5 ≠ shuffleAfter 0 [] 2) ",
            "[2]", "5", "0", _VALUE_REFUTE),
        "witness_reference": _WITNESS_REF,
    },

    # ---- STRUCTURAL (drop last class): produce one fewer permutation than there
    # ---- are classes. Correct on every emitted element; wrong on the LENGTH.
    # ---- Refuted via the list length with NO hypothesis, at a two-class input.
    {
        "id": "S-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _expr_rival("    return (threadAll nSplits s counts).1.dropLast\n"),
        "refinement": "Producing one fewer permutation than there are classes (an "
                      "off-by-one that drops the last class) leaves the last class "
                      "with no shuffle, so the stratified split fails to assign that "
                      "class's samples to folds. The real patched behaviour would "
                      "then diverge from the gold on fold coverage and shape — the "
                      "failing scenario and the existing coverage checks would not "
                      "match. The faithful real patch does NOT resolve.",
        "rationale": "REJECT from `out = (threadAll nSplits s counts).1`: for a "
                     "two-class input `threadAll` has length 2 while the rival "
                     "returns length 1. Verifying would leave the outer structure "
                     "(one permutation per class) unpinned (SPEC-TOO-WEAK). Refuted "
                     "with NO hypothesis at a two-class `[2,3]` input, `s=7`, via "
                     "the list length.",
        "witness": _witness(
            "", "[2, 3]", "2", "7",
            "  intro hEq\n"
            "  have hlen := congrArg List.length hEq\n"
            "  simp only [threadAll, threadStep, blockSize, List.foldl] at hlen\n"
            "  simp at hlen\n"),
        # Same subject fix as the value cases, and here the un-informativeness was
        # already visible in the recorded signature: against gold this witness
        # failed with `Application type mismatch: … hEq has type {True}do let r ←
        # forIn Lean.Loop.mk …` — `congrArg List.length` applied to an un-peeled
        # TRIPLE, i.e. the tactic never reached a list equation to take the length
        # of. Against the loop-free reference the REVEAL probe prints `hEq : True`
        # (`simp` proved the equation for that impl) and the same step fails as
        # `hEq has type True but is expected to have type ?m = ?m`, leaving
        # `hEq : True ⊢ False` — the reference genuinely satisfies the length
        # clause, which is the refutation this case claims.
        "witness_reference": _WITNESS_REF,
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation is SATISFIABLE at an F2P-shaped input.
    # The method has no `require`, so the nagini "a normal input satisfies the
    # precondition" probe has no literal counterpart; the analogue on this total
    # carrier is that the obligation must not be UNSATISFIABLE (or degenerate) at
    # exactly the input shape the failing scenario uses. This case discharges the
    # obligation's own value AT that point by evaluation, as an in-region
    # `assert`, and then closes the frozen obligation verbatim.
    # =====================================================================
    {
        "id": "S-admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        # The failing scenario's shape: two equal-sized classes, split count
        # equal to the class size, an integer configuration value. At that point
        # the obligation's value is forced to be the two-element list whose
        # SECOND element is drawn from the source ALREADY ADVANCED by the first
        # class's block — so the assert simultaneously witnesses that the
        # obligation is satisfiable there AND that its value at that point is the
        # residue-threading one. The impl is otherwise gold, so `ensures` closes
        # with the frozen script (the added bullet discharges the assert).
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "    assert (with_name_prefix `assert ((threadAll 5 0 [5, 5]).1 =\n"
                "      [shuffleAfter 0 [] 5, shuffleAfter 0 [5] 5]))\n" + _IMPL),
            _PROOF,
            "prove_correct perClassShuffles by\n"
            "  loom_solve\n"
            "  · simp [threadAll, threadStep, blockSize]\n"
            "  · have hi : i < counts.length := by omega\n"
            "    have hr := congrArg Prod.fst invariant_2\n"
            "    have hp := congrArg Prod.snd invariant_2\n"
            "    simp only at hr hp\n"
            "    rw [hr, hp, threadAll_take_step nSplits s counts i hi, threadStep, blockSize]\n"
            "  · have hr := congrArg Prod.fst invariant_2\n"
            "    simp only at hr\n"
            "    have hlen : i = counts.length := done_1\n"
            "    subst hlen\n"
            "    rw [List.take_length] at hr\n"
            "    simp_all [threadAll]\n"),
        "rationale": "the obligation `out = (threadAll nSplits s counts).1` must be "
                     "SATISFIABLE at an F2P-shaped input — two equal-sized classes "
                     "(`counts = [5,5]`) with the split count equal to the class size "
                     "(`nSplits = 5`) and an integer configuration value (`s = 0`) — "
                     "and its value there must be the residue-threading one. The "
                     "in-region assert discharges exactly that by evaluation "
                     "(`(threadAll 5 0 [5,5]).1 = [shuffleAfter 0 [] 5, shuffleAfter 0 "
                     "[5] 5]`: the second class drawn from the source ALREADY advanced "
                     "by the first class's block), before the frozen obligation closes "
                     "verbatim. LIVENESS CONFIRMED by the audit: weakening the "
                     "asserted value to the residue-free `[shuffleAfter 0 [] 5, "
                     "shuffleAfter 0 [] 5]` makes the build FAIL with `unsolved goals "
                     "… ⊢ shuffleAfter 0 [5] 5 = shuffleAfter 0 [] 5`, so this case's "
                     "exit 0 is contingent on the claim it makes and not on the assert "
                     "being elided. If it could not verify ⇒ PRECOND-TOO-STRONG (the "
                     "obligation would be unsatisfiable at the very input shape the "
                     "failing scenario exercises).",
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals) plus 1 AXIOM_TESTS entry. This
# bundle models the purely-functional core — a single method `perClassShuffles`
# whose random source is an OPAQUE axiom `shuffleAfter` — with a single `ensures`
# clause and three input binders `counts`/`nSplits`/`s`. Every sibling case is
# accounted for below. The carrier differs from nagini's (nagini abstracts the
# whole draw stream as `seed_state`/`advance`/`state_stream` over a single
# ordinal state; this bundle models the source-residue threading AND the
# transparent `blockSize` explicitly over per-class counts), which is what drives
# the re-siting and the one addition.
#
#   sibling case                     -> here
#   -------------------------------------------------------------------------
#   pos-control-rename-locals        -> S-pos-inline-blocksize    PORTED (reshape)
#   pos-control-zero-early-return    -> S-pos-materialize-fold     RE-EXPRESSED
#   admiss-self-call                 -> S-admiss-f2p-point         RE-EXPRESSED
#                                                                  (audit repair)
#   (no sibling: a reshape the spec   -> S-pos-commuted-max         ADDED by audit
#    accepts only via a proof step)                                 (attack E)
#   weak-constant-state-prepatch     -> S-reset-residue            PORTED
#   weak-double-advance              -> S-double-advance           PORTED
#   weak-start-advanced              -> S-start-advanced           PORTED
#   weak-drop-last-class             -> S-drop-last                PORTED
#   (no sibling: this carrier's      -> S-ignore-nsplits           ADDED (blockSize
#    explicit blockSize / nSplits)                                  / nSplits cover)
#   ax-ref-advancing-source          -> (none)                     DROPPED (G-AX lane)
#
# 5 ported, 2 re-expressed, 2 added, 1 dropped (the axiom lane). No case was
# dropped because its proof was hard, and after the audit no lane is dropped at
# all: the admissibility lane is re-expressed rather than declared N/A.
#
# RE-EXPRESSED (S-pos-materialize-fold): the sibling's second positive is a
#   different control flow (explicit n==0 early return, then the gold loop).
#   Velvet bans early return inside a loop, so rather than transliterate that
#   shape this port ships an even more structurally different correct impl — no
#   loop at all, returning the threaded fold directly. It is the honest cheapest
#   impl that materializes the grounded spec fold (also standing in for the
#   non-existent ungrounded-oracle echo, exactly as the sibling's zero-return
#   case did). Verified to close with the flat `loom_solve`.
# RE-EXPRESSED (admiss-self-call -> S-admiss-f2p-point): the port originally
#   recorded this lane N/A because the method carries no `require`. That reason is
#   WRONG and the audit replaced it: "the frozen obligation has no precondition"
#   does not make the admissibility lane vacuous, because the analogue on a total
#   carrier is the obligation being UNSATISFIABLE (or degenerate) at exactly an
#   F2P-shaped input. A positive that discharges the obligation AT that concrete
#   input — by evaluation, as an in-region `assert`, before closing the frozen
#   obligation verbatim — tests that directly, and the sibling's self-call probe
#   re-expresses cleanly into it. Nor is the risk covered by the other positives:
#   they prove the obligation on the WHOLE domain symbolically, which says nothing
#   about the obligation's VALUE at the failing scenario's point, and that value
#   is what the assert pins (the second class drawn from the ALREADY-ADVANCED
#   source). Liveness of the assert is machine-confirmed — see the case's own
#   rationale for the error the falsified variant produces.
# ADDED (S-ignore-nsplits): nagini abstracts the draw as a single opaque state
#   advance and never models the block SIZE, so it has no rival for the
#   `max count nSplits` floor. This bundle models `blockSize` explicitly and
#   transparently, so the block size handed to the source per class is part of
#   the defended surface; a rival that drops the `nSplits` floor attacks it and
#   is what makes the `nSplits` binder load-bearing.
# DROPPED (ax-ref-advancing-source): the sibling's AXIOM_TESTS entry probes the
#   `seed_state`/`advance`/`state_stream` A-reference deep model against the real
#   numpy source. Here the source is the opaque axiom `shuffleAfter`, validated
#   by axiom_check.py (G-AX); the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless.
#
# FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling explicitly documents
#   this class as N/A for this instance (both parameters are ints passed by
#   value; no read-only reference, no `list_pred` input, nothing writable to
#   vacuously satisfy a postcondition). This backend is likewise referentially
#   transparent: every parameter is an immutable value, no `mut` input binder, no
#   heap, no aliasing. No expressible instance; no substitute fabricated.
#
# BINDER / CLAUSE COVERAGE. The single clause `out = (threadAll nSplits s
#   counts).1` is attacked by all five rivals: the RESIDUE threading
#   (S-reset-residue = residue dropped, S-start-advanced = anchor advanced,
#   S-double-advance = advance granularity), the BLOCK SIZE (S-ignore-nsplits =
#   nSplits floor dropped), and the OUTER structure (S-drop-last, via list
#   length, NO hypothesis). The three binders are varied across FIVE distinct
#   input points (pts=5): `counts` over `[3,4]`/`[5]`/`[2,3]`/`[2]`, `nSplits`
#   over `2`/`3`/`5`, `s` over `0`/`1`/`7`. Each value rival conditions on ONE
#   hypothesis (two source results differ), never two about the same term. No two
#   rivals share a witness. The clause is defended by three positive controls and
#   by the admissibility case.
#
#   HYPOTHESIS TRUTH, not just satisfiability. The gate's consistency probe only
#   shows a hypothesis cannot be refuted, which for an OPAQUE source is automatic
#   and therefore weak evidence — it would pass a hypothesis that is FALSE of the
#   callee the axiom denotes, leaving a rival that is not observably wrong. So
#   each conditioning hypothesis was additionally checked against the REAL
#   sequential source (the callee `shuffleAfter` abstracts, per mapping.md §3.1),
#   and all four hold of it:
#     shuffleAfter 0 []    4 ≠ shuffleAfter 0 [3]    4   (residue dropped)
#     shuffleAfter 0 []    5 ≠ shuffleAfter 0 [2]    5   (anchor advanced)
#     shuffleAfter 1 [3]   4 ≠ shuffleAfter 1 [3, 3] 4   (advance granularity)
#     shuffleAfter 0 []    5 ≠ shuffleAfter 0 []     2   (block-size floor)
#   The audit repaired one that did NOT: the anchor case originally conditioned on
#   `shuffleAfter 0 [] 5 ≠ shuffleAfter 0 [1] 5`, and a ONE-position block has a
#   single arrangement, so a real source is not consumed by permuting it and the
#   two draws are EQUAL. That made the `[1]`-anchored rival behaviourally
#   indistinguishable from gold — a vacuous reject case that the gate could not
#   detect, since no tactic derives `False` from an opaque disequation. The anchor
#   is now `[2]`, a block that genuinely consumes the source.
#
# AXIOM_TESTS: empty. The opaque `shuffleAfter` is validated by G-AX
#   (axiom_check.py); this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
