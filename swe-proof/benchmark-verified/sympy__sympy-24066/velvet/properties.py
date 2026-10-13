"""properties.py — G-PBT falsification battery for sympy__sympy-24066 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes. Each SPEC case is a
full ``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region, or the
``prove_correct`` tactic body, is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and the ``prove_correct normalizeDimensions``
obligation survives with a byte-identical statement). ``expect="verify"`` passes
iff (in scope AND verifies); ``expect="reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: it must elaborate
against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  normalizeDimensions (dims : List Dimension) return (out : List Dimension)
    ensures out = normSeq dims                          (E: exact canon shape)

  ``normSeq`` is a front-recursive spec fold applying the per-element rule
  ``normDim d = if isDimensionless d then dimOne else d`` to each element, order
  preserved. The single load-bearing clause E pins the whole canonicalization:
  every element that carries no physical dimension must be reported as the
  single canonical dimensionless value, and every other element kept verbatim
  and in position. The whole content of the fix lives on the
  dimensionless-but-non-canonical sub-domain — an element ``d`` with
  ``isDimensionless d = true`` yet ``d ≠ dimOne`` — where the desired result
  reports ``dimOne`` and the pre-change behaviour reported ``d``.

CARRIER NOTE — why every witness CONDITIONS on the carrier.

  ``Dimension`` is an opaque type axiom with no constructors; ``isDimensionless``
  and ``dimOne`` are opaque axioms. There is no literal ``Dimension`` value to
  feed ``decide``, and ``extract_program_for`` / ``derive_tester_for`` cannot
  compile a program whose postcondition depends on the noncomputable ``normSeq``.
  So each reject ``witness`` refutes the method's Hoare triple DIRECTLY at a
  concrete-LENGTH input whose element is described by HYPOTHESIS
  (``example (d : Dimension) (hdl : isDimensionless d = <b>) (hne : d ≠ dimOne)
  : ¬ triple True (normalizeDimensions [...]) (fun out => out = normSeq [...])``),
  reduced through ``triple_pure`` for the straight-line rivals, checked in a file
  whose ``prove_correct`` block has been stripped so no tactic script interferes.

  WHICH SUBJECT THE REFUTATION IS CHECKED AGAINST. Every reject case names a
  ``witness_reference``: the loop-free grounded-oracle impl, which the gate
  independently re-checks shares this spec and VERIFIES. This is load-bearing, not
  decoration. The FROZEN impl is a ``while`` loop, and a ``triple`` over a loop
  elaborates to an unreduced ``forIn Lean.Loop.mk ...`` term that ``triple_pure``
  cannot rewrite, so a witness built against the frozen impl never reaches a
  verdict — its exit code reports a tactic mismatch on an un-normalised loop term,
  which is the same code a claim of the OPPOSITE polarity earns. Against the
  reference the postcondition genuinely reduces (``simp`` discharges it, leaving
  ``False``), so the build's outcome tracks what the witness CLAIMS. Verified by
  replacing each refutation step with a deliberate ``exact (0 : Nat)`` and reading
  the goal Lean printed: ``¬d = dimOne`` on the rival, ``False`` on the reference,
  an unreduced ``forIn`` term on the frozen impl.

  AUDIT (2026-08-16) — THE FORGERY PAIR, re-derived independently for all five
  reject cases. Reading a gold-side error and calling it "semantic" is not
  evidence; the evidence is that the exit code CHANGES when the claim changes. For
  each case, three files differing only in what they CLAIM were built against the
  ``witness_reference``:

    file                                   exit  first error
    the shipped witness (¬ triple ...)      1    introN failed ... ⊢ False
    the same with the ``¬`` DROPPED         1    No goals to be solved
    the flipped claim, refutation steps     1    No goals to be solved
      truncated so a PROOF would exit 0

  ``⊢ False`` versus ``No goals to be solved`` is the whole distinction: against
  the reference, ``simp`` DISCHARGES the postcondition at that input, so the
  refutation's residual goal is ``False`` (unprovable, exit 1) while the flipped
  claim has already been closed before its own tactic runs (no goals left, exit
  1). Two different errors for two different claims, so the reference's exit code
  carries information about the claim. Confirmed from the other direction: a bare
  positive claim (``triple ... `` with no refutation steps) exits 0 against the
  reference and 1 against every rival, with the rival's residue naming the rival's
  own output — e.g. ``⊢ [d] = normSeq [d]`` for S-prepatch, ``⊢ d :: List.map
  normDim [e] = normSeq [d, e]`` for S-head. And the type-revealing probe
  (``exact (h : Nat)`` in place of the final step) prints the hypothesis's real
  type: a CONCRETE equation on each rival (``d = dimOne``, ``dimOne = d`` for the
  inverted rule, ``b = dimOne`` for the interior rival) and ``False`` on the
  reference. That pair is a genuine refutation, not a tactic mismatch.

  Why the reference and not the frozen impl: measured, the frozen impl's own
  gold-side error is an ``Application type mismatch`` on an unreduced ``forIn
  Lean.Loop.mk ...`` term — the ``_STUCK_UNIFICATION`` shape — and the ``¬``-dropped
  forgery against the frozen impl prints ``h has type True``, i.e. the claim was
  never evaluated there. That is exactly the hollow case the ``witness_reference``
  exists to avoid, and naming it is what makes these five rejections attest to the
  spec. Every reject case's consistency probe was also re-run: all five exit 1 on
  ``⊢ False``, so no witness proves its refutation from a contradiction.

  AUDIT (2026-08-16, SECOND independent pass — re-derived from scratch by an
  auditor who did not write the above, and CONFIRMING it with its own builds).
  All 94 files rebuilt through ``scripts/lean_verify.sh``. Per reject case, the
  four subjects that decide whether the rejection attests to the spec:

    build                                            exit  first error / goal
    shipped witness vs the RIVAL                      0    (elaborates)
    shipped witness vs the ``witness_reference``      1    introN failed
    shipped witness vs the FROZEN impl                1    Application type
                                                           mismatch, on an
                                                           unreduced ``forIn
                                                           Lean.Loop.mk`` term
    consistency probe vs the reference                1    unsolved goals

  The FORGERY PAIR, per case, all five identical in shape:

    flipped claim (``¬`` dropped) vs the reference    1    No goals to be solved
    flipped claim, refutation tail truncated          1    No goals to be solved
    bare POSITIVE claim vs the reference              0    (elaborates)
    bare POSITIVE claim vs the RIVAL                  1    unsolved goals

  The last two lines are the strongest single piece of evidence in this battery
  and they are what settles the ``introN`` signature class. A claim that the impl
  is CORRECT at the witness point exits 0 on the reference and 1 on the rival —
  the exact inverse of the shipped witness — so the exit code tracks the CLAIM and
  not the file's syntactic shape. The rival-side residues name the discriminating
  element concretely: ``⊢ d = dimOne`` (S-prepatch, S-head, S-last),
  ``⊢ dimOne = d`` (S-inverted, the predicate's ``false`` mirror) and
  ``⊢ b = dimOne`` (S-interior).

  Independently re-confirmed by a goal-revealing probe (the final refutation step
  replaced by ``exact (0 : Nat)``, which makes Lean print the goal actually
  reached) — three subjects, all five cases:

    subject     goal reached
    rival       ``¬d = dimOne`` / ``¬dimOne = d`` / ``¬b = dimOne``  <- the claim
    reference   ``False``            <- ``simp`` DISCHARGED the postcondition
    frozen      ``¬{True}MProdWithNames.snd <$> ...``  <- nothing was decided

  ``False`` on the reference is what makes the ``introN`` failure a real
  refutation rather than a tactic mismatch: the postcondition was PROVED there, so
  the refutation's residue is the unprovable ``False`` and ``intro`` has no binder
  left to introduce. The frozen impl's goal is an unreduced monadic loop term,
  which is exactly the ``_STUCK_UNIFICATION`` shape the gate screens for — so
  naming a ``witness_reference`` is load-bearing here and not decoration, and the
  cell would be hollow without it.

  The two hypotheses pin the exact sub-domain the fix bites: ``isDimensionless d
  = true`` with ``d ≠ dimOne`` (or the ``false`` mirror for the inverted rival).
  They are JOINTLY SATISFIABLE — this is precisely the load-bearing witness
  mapping.md §3.2 exhibits on real ``Dimension`` values (e.g. the dimension of
  ``second/(ohm*farad)`` is dimensionless yet not the canonical value). One
  hypothesis per opaque term; no two hypotheses constrain the same term, so the
  gate's inconsistency probe cannot derive ``False`` from them.

ADVERSARIAL READ of the weakness classes (others justified-N/A in `assessment`):
  * FRAME-MUTATION — VACUOUS. The nagini sibling ships two MANDATORY
    frame-mutation rivals (write-in-place and no-op write) against a read-only
    input held at a fractional heap permission. This backend is referentially
    transparent: ``dims`` is an immutable value, no ``mut`` binder on the input,
    no heap, no aliasing. No read-only input to overwrite, no permission system
    to trip. Not fabricated (per the porting map, dropped rather than replaced).
  * PARTIAL-DOMAIN — the STRONG class here, ported in full. The fix differs from
    the pre-change behaviour only on the dimensionless-but-non-canonical
    sub-domain. FIVE rivals attack E there: the pre-change verbatim pass-through
    (S-prepatch), the inverted rule (S-inverted), the head-only / tail-only
    positional divergences (S-head-verbatim / S-last-verbatim), and — added by
    the 2026-08-16 audit — the INTERIOR divergence (S-interior-verbatim). The
    fifth closes a real positional gap: head-only and tail-only both refute at
    length ≤ 2, where the two ends between them cover every slot, so a rival
    correct at BOTH ends and wrong strictly in between was unattacked. It is
    observationally identical to gold at lengths 0-2 and wrong from length 3 up.
  * UNGROUNDED-ORACLE ECHO — N/A as a WRONG echo. E is grounded in ``normSeq``
    (a fold over the actual input ``dims``), fully unfolded, bottoming out in the
    opaque-but-total ``isDimensionless``. There is no answer-key a wrong impl
    could echo. Instead, standing in for the sibling's cheapest-honest-impl slot,
    a positive control MATERIALISES the grounded fold (``return normSeq dims``):
    it MUST verify, because the grounded oracle is the correct answer.
  * CONTROL-FLOW / SECOND-CHANNEL — N/A. The operation has a single value output
    (the canonicalized list); no raise surface is modeled (the callee's partial
    domain is an axiom-lane obligation), no second observable channel.
  * ADMISSIBILITY — PORTED (``S-adm-f2p-singleton``). An earlier revision of this
    manifest recorded the lane N/A on the ground that the method carries no
    ``require`` clause. That reasoning is wrong, and the audit replaced it: on a
    TOTAL carrier the analogue of a too-strong precondition is the OBLIGATION
    being unsatisfiable at an F2P-shaped input. The ported case discharges the
    obligation at that concrete input as a ``have`` before closing E verbatim,
    which tests the direction directly. The sibling's fractional-permission
    framing is indeed absent here; the DIRECTION it tested is not.
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

WITNESS PLACEMENT / coverage. The method has ONE input binder, ``dims``. The
five reject witnesses probe it at FIVE distinct input points: a singleton
``[d]`` with a dimensionless-non-canonical head (S-prepatch), a singleton
``[d]`` with a NON-dimensionless head (S-inverted, the ``false`` mirror of the
predicate), a two-element ``[d, e]`` whose HEAD is dimensionless-non-canonical
(S-head-verbatim), a two-element ``[e, d]`` whose TAIL is
dimensionless-non-canonical (S-last-verbatim), and a three-element ``[a, b, z]``
whose INTERIOR element is dimensionless-non-canonical (S-interior-verbatim). So
E is attacked at both predicate verdicts and at the head, the tail AND an
interior slot, across lengths 1, 2 and 3. The variation is meaningful rather than
two spellings of one point: every witness point changes E's verdict for at least
one rival that the others leave standing.

  AUDIT (2026-08-16, independent re-derivation) — the count and the
  non-redundancy claim previously stated here were BOTH wrong, and the fix is to
  state what the cross-product actually measures. Two corrections:

  (a) ``pts``. The header claimed ``pts=5`` and the accounting block below
      claimed ``pts=4``; ``scripts/pbt_coverage.py`` reports ``pts=4-4``. The
      reporter dedups on the witness's LIST LITERAL after aligning binder names,
      and S-prepatch and S-inverted both instantiate ``dims := [d]`` — they
      differ in the HYPOTHESIS on the predicate (``= true`` vs ``= false``), not
      in the input term, so they collapse to one point for the reporter. Four
      literal points (``[d]``, ``[d, e]``, ``[e, d]``, ``[a, b, z]``) across five
      hypothesis-distinguished sub-domains. ``pts=4`` is the machine-checked
      number and both prose sites now say so.

  (b) Non-redundancy. The claim "each rival AGREES with the frozen impl at every
      other case's witness point" is FALSE, measured by building all 20
      off-diagonal (witness × rival) pairs. Exit 0 means that witness also
      refutes that rival:

        witness \\ rival    prepatch  inverted  head  last  interior
        S-prepatch  [d]       --         0       0     1       1
        S-inverted  [d]       1         --       1     1       1
        S-head   [d,e]        1          1      --     1       1
        S-last   [e,d]        1          1       1    --       1
        S-interior[a,b,z]     1          1       1     1      --

      So S-prepatch's witness ALSO refutes the inverted and head rivals (the
      pass-through rival is wrong at every dimensionless-non-canonical slot, and
      ``[d]``'s single element is the head). Confirmed semantically as well as by
      tactic: on ``[d]`` with the element dimensionless-non-canonical, gold says
      ``[dimOne]`` while prepatch, inverted, head AND last all say ``[d]``.

      What survives, and is the property that actually matters, is that no
      witness is DROPPABLE. Each of the five is the unique refuter of at least
      one rival: S-inverted is the only witness refuting the inverted rival at
      the predicate's ``false`` verdict, S-last the only one refuting the
      tail-only rival, S-interior the only one refuting the interior rival, and
      S-prepatch/S-head each refute their own rival. Dropping any one leaves a
      rival unrefuted, which is the non-redundancy the battery needs; overlap in
      the other direction is coverage, not waste.

AUDIT (2026-08-16) — WHAT THE THREE POSITIVES EACH BUY. The two ported positives
reshape only the DATA FLOW (an inlined binding inside the frozen backward loop;
`return normSeq dims` with no loop). Neither varies the TRAVERSAL DIRECTION, so a
spec too strong on the walk order would have passed. ``S-pos-forward-loop`` closes
that: it walks ``dims`` forward with ``++`` accumulation under a ``take``-shaped
invariant and the measure ``dims.length - i``, reusing neither the frozen loop
skeleton nor the frozen ``drop``-step lemma. The nagini sibling declines this
control on the ground that the required ``f (a ++ b) = f a ++ f b`` lemma is not
auto-discharged; on this carrier it is provable by induction and can be proven as
a ``have`` inside the tactic body, so no top-level lemma is declared and the
variant scope stays clean.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-24066"
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
# -- impl-end). Replaced wholesale by the structure-attacking rivals and the
# grounded-oracle positive, which abandon the loop entirely.
_IMPL = (
    "    let mut result : List Dimension := []\n"
    "    let mut i := dims.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ dims.length\n"
    "      invariant result = normSeq (dims.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let d := dims[i - 1]!\n"
    "      result := normDim d :: result\n"
    "      i := i - 1\n"
    "    return result\n"
)

# The two loop-body lines that bind `d` then prepend its canonicalization. The
# positive control inlines `d` into the prepend — a data-flow reshape that keeps
# the accumulated `result` definitionally identical, so the frozen tactic script
# still closes.
_INNER = (
    "      let d := dims[i - 1]!\n"
    "      result := normDim d :: result\n"
)

# The frozen `prove_correct` block. The grounded-oracle positive abandons the
# loop, so its (much shorter) proof needs the loop-step rewrite dropped — only
# the tactic body changes; the `prove_correct normalizeDimensions` header (hence
# the obligation statement) is byte-identical.
_PROOF = (
    "prove_correct normalizeDimensions by\n"
    "  loom_solve\n"
    "  rw [normSeq_drop_step dims i (by omega) (by omega)]\n"
    "  simp_all\n"
)

# The loop-free grounded-oracle impl, shared by the S-pos-grounded-oracle
# positive and by every reject case's `witness_reference`. AUDIT (2026-08-13):
# the frozen impl is a `while` loop, and a `triple` over a loop elaborates to an
# unreduced `forIn Lean.Loop.mk ...` term that `triple_pure` cannot touch. So a
# witness stated through `triple_pure` never reaches a VERDICT on the frozen
# impl — measured by replacing each witness's refutation step with a deliberate
# `exact (0 : Nat)`, which makes Lean print the goal actually reached:
#
#   subject   goal Lean printed for the S-prepatch witness
#   rival     ¬d = dimOne                         <- the concrete claim
#   frozen    ¬{True}...forIn Lean.Loop.mk...     <- nothing was decided
#   this impl False                               <- `simp` PROVED the equation
#
# Naming this impl explicitly makes each rejection attest against a subject that
# REDUCES (`False` is the residue of the postcondition being discharged), instead
# of depending on the gate's stuck-screen fallback firing.
_ORACLE_MODULE = _swap(
    _swap(_BASE, _IMPL, "    return normSeq dims\n"),
    _PROOF,
    "prove_correct normalizeDimensions by\n"
    "  loom_solve\n")


# ---- witness helper. The spec is a `method` contract whose postcondition is
# ---- noncomputable over an opaque carrier, so a witness reaches it NOT through
# ---- the tester machinery (which cannot extract a noncomputable program) but by
# ---- refuting the method's Hoare triple directly at a concrete-length input
# ---- whose element is described by hypothesis. Checked in a file whose
# ---- `prove_correct` block has been stripped.
def _witness(binders, list_lit, refute_body):
    return (
        f"example {binders} :\n"
        f"    ¬ (triple (l := Prop) True (normalizeDimensions {list_lit})\n"
        f"        (fun out => out = normSeq {list_lit})) := by\n"
        f"  unfold normalizeDimensions\n"
        f"{refute_body}"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 0 (soundness) — AUDIT (2026-08-16). The two ported
    # positives reshape only the DATA FLOW: one inlines a binding inside the
    # frozen backward loop, the other abandons the loop for `return normSeq
    # dims`. Neither exercises a different LOOP DIRECTION, so a spec that were
    # too strong on the traversal order (only a backward, front-recursive-
    # matching walk provable) would still have passed. The nagini sibling
    # explicitly flags this as the risk and DECLINES it — directive 3 there says
    # a forward-append control would need an `f(a ++ b) = f a ++ f b` lemma
    # "the verifier cannot auto-discharge", so both sibling positives keep the
    # gold backward loop. That reason does not survive on this carrier: the
    # lemma is provable here (`normSeq (xs ++ ys) = normSeq xs ++ normSeq ys` by
    # induction on `xs`), and it can be proven as a `have` INSIDE the tactic
    # body, so no new top-level lemma is declared and `variant_scope` stays
    # clean. This case walks the input FORWARD, accumulating with `++` under a
    # `take`-shaped invariant and the measure `dims.length - i`, and closes with
    # the take-step lemma the frozen `drop`-step lemma is the mirror of. MUST
    # verify, else E is SPEC-TOO-STRONG on the traversal direction.
    # =====================================================================
    {
        "id": "S-pos-forward-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL,
                "    let mut result : List Dimension := []\n"
                "    let mut i := 0\n"
                "    while i < dims.length\n"
                "      invariant i ≤ dims.length\n"
                "      invariant result = normSeq (dims.take i)\n"
                "      done_with i = dims.length\n"
                "      decreasing dims.length - i\n"
                "    do\n"
                "      result := result ++ [normDim dims[i]!]\n"
                "      i := i + 1\n"
                "    return result\n"),
            _PROOF,
            "prove_correct normalizeDimensions by\n"
            "  loom_solve\n"
            "  have happ : ∀ (xs ys : List Dimension),\n"
            "      normSeq (xs ++ ys) = normSeq xs ++ normSeq ys := by\n"
            "    intro xs ys\n"
            "    induction xs with\n"
            "    | nil => simp [normSeq]\n"
            "    | cons a bs ih => simp [normSeq, ih]\n"
            "  have hstep : normSeq (dims.take (i + 1))\n"
            "      = normSeq (dims.take i) ++ [normDim dims[i]!] := by\n"
            "    have hk : i < dims.length := by omega\n"
            "    have h : dims.take (i + 1) = dims.take i ++ [dims[i]!] := by\n"
            "      rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hk,\n"
            "          Option.getD_some]\n"
            "      exact List.take_succ_eq_append_getElem hk\n"
            "    rw [h, happ]\n"
            "    simp [normSeq]\n"
            "  subst invariant_2\n"
            "  rw [hstep]\n"),
        "rationale": "SPEC-TOO-STRONG probe on the TRAVERSAL DIRECTION, the one "
                     "axis the other two positives leave untested (both keep the "
                     "frozen backward walk or drop the loop entirely). This impl "
                     "walks `dims` FORWARD from index 0, accumulating with `++` "
                     "under a `take`-shaped invariant and the measure "
                     "`dims.length - i`, so neither the frozen loop skeleton nor "
                     "the frozen `drop`-step lemma is reusable — the proof "
                     "re-derives the mirror `take`-step fact from a `have`-proven "
                     "append law. It verifies, so E (`out = normSeq dims`) is a "
                     "claim about the OUTPUT VALUE and not about how the impl "
                     "walks the input: the front-recursive shape of `normSeq` is "
                     "not smuggled into the obligation as a required traversal "
                     "order. Failing here would be SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. The intermediate
    # `let d := dims[i-1]!` binding is inlined into the prepend: the
    # accumulated `result` is DEFINITIONALLY identical, so `loom_solve` leaves
    # the same single loop-body goal and the frozen tactic script (`rw
    # [normSeq_drop_step …]; simp_all`) discharges it unchanged. No new lemma
    # is introduced and the obligation statement is byte-identical.
    # =====================================================================
    {
        "id": "S-pos-inline-binding",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _INNER,
            "      result := normDim dims[i - 1]! :: result\n"),
        "rationale": "Inlining the per-element binding into the prepend leaves "
                     "the accumulated `result` definitionally identical, so E "
                     "(`out = normSeq dims`) holds and the frozen proof closes "
                     "without change. A correct reshape that failed to verify "
                     "would mean the spec is SPEC-TOO-STRONG on the impl's "
                     "data-flow shape. Defends E along the loop-based skeleton.",
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness, cheapest honest impl) — MATERIALISE the
    # grounded fold. `normSeq` is a pure function of the input (fully unfolded,
    # bottoming out in the opaque-but-total `isDimensionless`), so the cheapest
    # correct impl returns `normSeq dims` directly. This is the on-carrier
    # analogue of the sibling's grounded-oracle positive: NOT an ungrounded
    # echo, because `normSeq dims` IS the correct answer. Abandons the loop
    # entirely, so its proof is a bare `loom_solve` (only the tactic body
    # changes; the obligation statement is byte-identical). MUST verify, else
    # the spec rejects its own grounded model => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "S-pos-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _ORACLE_MODULE,
        "rationale": "Returning `normSeq dims` directly is the cheapest honest "
                     "impl: the postcondition oracle is GROUNDED (a pure fold "
                     "over the actual input, not an opaque answer-key), so "
                     "materialising it is the correct computation, not a cheat. "
                     "A structurally-different (loop-free) correct impl that "
                     "MUST verify; failing would be SPEC-TOO-STRONG. Defends E "
                     "with a value-level impl distinct from the loop skeleton.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG probe). AUDIT (2026-08-13): the port
    # recorded this lane N/A because the method carries no `require`. That is the
    # reason the porting guide explicitly rejects — on a TOTAL carrier the
    # analogue of a too-strong precondition is the OBLIGATION being unsatisfiable
    # at exactly an F2P-shaped input, which this case tests directly. It
    # discharges the obligation at that concrete input FIRST, as a `have`
    # (`isDimensionless x = true → normSeq [x] = [dimOne]` — the singleton
    # dimensionless-but-non-canonical shape the reported scenario has), and only
    # then closes the frozen obligation verbatim. The impl region is untouched, so
    # this is the frozen impl plus a discharged precondition-shaped lemma: if the
    # spec were unsatisfiable at that input the `have` could not close, and the
    # case would fail while every uniqueness rival still passed.
    # =====================================================================
    {
        "id": "S-adm-f2p-singleton",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF,
            "prove_correct normalizeDimensions by\n"
            "  have hadm : ∀ (x : Dimension), isDimensionless x = true →\n"
            "      normSeq [x] = [dimOne] := by\n"
            "    intro x hx\n"
            "    simp [normSeq, normDim, hx]\n"
            "  loom_solve\n"
            "  rw [normSeq_drop_step dims i (by omega) (by omega)]\n"
            "  simp_all\n"),
        "rationale": "PRECOND-TOO-STRONG probe on a total carrier: the obligation "
                     "must be SATISFIABLE at the F2P-shaped input — a single "
                     "operand that is dimensionless yet not the canonical value. "
                     "The proof discharges exactly that instance as a `have` "
                     "(`normSeq [x] = [dimOne]` under `isDimensionless x = true`) "
                     "before closing E verbatim, so a spec that excluded this "
                     "ordinary single-operand input would fail HERE while the "
                     "uniqueness rivals still rejected. Verifies, so the clause is "
                     "satisfiable at the input the change is about — not "
                     "degenerate, and not too strong.",
    },

    # =====================================================================
    # UNIQUENESS rivals — wrong impls sharing the frozen spec that MUST be
    # rejected, each with a machine-checked refutation witness at a concrete
    # input and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "S-prepatch-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-CHANGE BEHAVIOUR. Every element reported verbatim, no
        # canonicalization. Correct on genuinely-dimensionful and
        # already-canonical elements, WRONG on a dimensionless-but-non-canonical
        # one (reports the element instead of the canonical value).
        "module": _swap(_BASE, _IMPL, "    return dims\n"),
        "refinement": "This is the pre-change branch: it emits every operand "
                      "dimension verbatim. A faithful real patch reverting the "
                      "canonicalization leaves a dimensionless-but-non-canonical "
                      "operand reporting its own dimension; the downstream "
                      "structural-equality check on the combined expression then "
                      "sees a mismatched dimension and raises, so the F2P "
                      "scenario (a sum over an applied function of a "
                      "dimensionless argument) still errors. It would NOT "
                      "resolve, so a verifying rival is a true "
                      "verify-does-not-imply-resolve break.",
        "rationale": "REJECT from E (`out = normSeq dims`): on a singleton whose "
                     "element is dimensionless (`isDimensionless d = true`) yet "
                     "not canonical (`d ≠ dimOne`), `normSeq [d]` reports "
                     "`dimOne` while the rival reports `d`. Verifying would be "
                     "SPEC-TOO-WEAK on the load-bearing clause. Refuted at "
                     "`[d]` with `d` in that exact sub-domain.",
        "witness": _witness(
            "(d : Dimension) (hdl : isDimensionless d = true) (hne : d ≠ dimOne)",
            "[d]",
            "  simp only [triple_pure, le_Prop_eq, true_implies]\n"
            "  simp [normSeq, normDim, hdl]\n"
            "  intro h\n"
            "  exact hne h\n"),
        "witness_reference": _ORACLE_MODULE,
    },
    {
        "id": "S-inverted-rule",
        "kind": "uniqueness",
        "expect": "reject",
        # INVERTED per-element rule: canonicalize the NON-dimensionless
        # elements (report the canonical value for them) and keep the
        # dimensionless ones verbatim -- the exact opposite of the desired rule.
        # Wrong on BOTH regimes wherever they differ from the desired verdict.
        "module": _swap(
            _BASE, _IMPL,
            "    return dims.map (fun x => if isDimensionless x then x else dimOne)\n"),
        "refinement": "Applying the canonicalization to the NON-dimensionless "
                      "elements and leaving the dimensionless ones verbatim is "
                      "the opposite rule. Its faithful real patch would (a) "
                      "leave the F2P dimensionless argument non-canonical so the "
                      "reported scenario still raises, AND (b) collapse every "
                      "genuinely-dimensionful operand to the canonical "
                      "dimensionless value, corrupting ordinary dimensional "
                      "arithmetic that the pass-to-pass suite exercises. It "
                      "would NOT resolve.",
        "rationale": "REJECT from E on the NON-dimensionless regime: for a "
                     "singleton whose element is NOT dimensionless "
                     "(`isDimensionless d = false`) and `d ≠ dimOne`, "
                     "`normSeq [d]` reports `d` while the rival reports "
                     "`dimOne`. Uses the `false` verdict of the predicate — the "
                     "mirror sub-domain S-prepatch does not touch. Refuted at "
                     "`[d]` with `d` non-dimensionless.",
        "witness": _witness(
            "(d : Dimension) (hdl : isDimensionless d = false) (hne : d ≠ dimOne)",
            "[d]",
            "  simp only [triple_pure, le_Prop_eq, true_implies]\n"
            "  simp [normSeq, normDim, hdl, List.map]\n"
            "  intro h\n"
            "  exact hne h.symm\n"),
        "witness_reference": _ORACLE_MODULE,
    },
    {
        "id": "S-head-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # HEAD-ONLY divergence: canonicalize every element EXCEPT the head,
        # reported verbatim. Correct on a singleton whose head is not that
        # regime; wrong when the HEAD is dimensionless-but-non-canonical.
        "module": _swap(
            _BASE, _IMPL,
            "    match dims with\n"
            "    | [] => return []\n"
            "    | d :: ds => return d :: ds.map normDim\n"),
        "refinement": "Canonicalizing every operand except the leading one has "
                      "no gold counterpart (the desired rule canonicalizes "
                      "every operand). A faithful real patch that skipped the "
                      "first operand would leak a non-canonical dimensionless "
                      "dimension out of the head slot; the downstream "
                      "structural-equality comparison then rejects it, so an "
                      "F2P-shaped sum over such an expression fails. It would "
                      "NOT resolve. A test whose first operand is never that "
                      "regime would miss it.",
        "rationale": "REJECT from E on the HEAD element: for `[d, e]` with the "
                     "head `d` dimensionless (`isDimensionless d = true`) and "
                     "`d ≠ dimOne`, `normSeq [d, e]` reports `dimOne` at "
                     "position 0 while the rival reports `d`. Positional "
                     "boundary the bulk clause leaves implicit; probes `dims` "
                     "at length 2. Refuted at `[d, e]`.",
        "witness": _witness(
            "(d e : Dimension) (hdl : isDimensionless d = true) (hne : d ≠ dimOne)",
            "[d, e]",
            "  simp only [triple_pure, le_Prop_eq, true_implies]\n"
            "  simp [normSeq, normDim, hdl, List.map]\n"
            "  intro h\n"
            "  exact hne h\n"),
        "witness_reference": _ORACLE_MODULE,
    },
    {
        "id": "S-last-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # TAIL-ONLY divergence: canonicalize every element EXCEPT the last,
        # reported verbatim -- disjoint from S-head-verbatim. Wrong when the
        # LAST element is dimensionless-but-non-canonical (the single-argument
        # F2P case is exactly this: length 1 -> head and tail coincide).
        "module": _swap(
            _BASE, _IMPL,
            "    match dims.reverse with\n"
            "    | [] => return []\n"
            "    | d :: ds => return (d :: ds.map normDim).reverse\n"),
        "refinement": "Canonicalizing every operand except the trailing one has "
                      "no gold counterpart. On an applied function whose LAST "
                      "operand is dimensionless-but-non-canonical (the "
                      "single-operand F2P scenario is exactly this — length 1, "
                      "so head and tail coincide), the faithful real patch leaks "
                      "the non-canonical dimension and the reported sum still "
                      "raises. It would NOT resolve.",
        "rationale": "REJECT from E on the TAIL element: for `[e, d]` with the "
                     "last element `d` dimensionless (`isDimensionless d = "
                     "true`) and `d ≠ dimOne`, `normSeq [e, d]` reports `dimOne` "
                     "at position 1 while the rival reports `d`. Disjoint from "
                     "S-head-verbatim (attacks the opposite end) and covers the "
                     "actual F2P witness shape. Refuted at `[e, d]`.",
        # AUDIT (2026-08-13) — the ported witness led with a STANDALONE
        # `simp only [List.reverse_cons, ...]` step. Against the rival that step
        # fires (the rival's body is built from `.reverse`), but against any
        # subject whose impl contains no `reverse` it has nothing to rewrite and
        # dies with `simp` made no progress — BEFORE the claim is ever looked at.
        # Measured: the same first error line, byte-identical, for this witness
        # and for a FORGERY that drops the `¬` (i.e. asserts the subject is
        # CORRECT at `[e, d]`). That exit code carried no information about the
        # claim. Folding the `reverse` lemmas into the same `simp only` as
        # `triple_pure` removes the standalone step, so the tactic now reaches the
        # postcondition on every subject and the claim decides the outcome.
        "witness": _witness(
            "(d e : Dimension) (hdl : isDimensionless d = true) (hne : d ≠ dimOne)",
            "[e, d]",
            "  simp only [List.reverse_cons, List.reverse_nil, List.nil_append,\n"
            "             List.cons_append, List.append_nil, List.map_cons,\n"
            "             List.map_nil, triple_pure, le_Prop_eq, true_implies]\n"
            "  simp [normSeq, normDim, hdl]\n"
            "  intro h\n"
            "  exact hne h\n"),
        "witness_reference": _ORACLE_MODULE,
    },
    {
        "id": "S-interior-verbatim",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT (2026-08-16) — INTERIOR divergence, the positional gap the four
        # ported rivals leave. S-head attacks position 0, S-last attacks the
        # final position, and both refute at length ≤ 2 where head and tail
        # between them cover EVERY slot. So a rival correct at the two ends and
        # wrong strictly in between was unattacked, and the corresponding
        # near-miss — a real change that canonicalizes the boundary operands and
        # skips the middle ones — would have been admitted by this battery. This
        # rival canonicalizes the FIRST and LAST elements and passes every
        # interior element through verbatim: observationally identical to gold at
        # lengths 0, 1 and 2, and wrong from length 3 up. Refuted at `[a, b, z]`
        # with the INTERIOR element `b` dimensionless-but-non-canonical, the
        # first witness point in this battery at length 3.
        "module": _swap(
            _BASE, _IMPL,
            "    match dims with\n"
            "    | [] => return []\n"
            "    | [a] => return [normDim a]\n"
            "    | a :: rest =>\n"
            "      return normDim a :: (rest.dropLast ++ [normDim (rest.getLast!)])\n"),
        "refinement": "Canonicalizing only the leading and trailing operand "
                      "dimensions and passing the middle ones through verbatim "
                      "has no counterpart in the desired rule, which canonicalizes "
                      "EVERY operand. A faithful real change of this shape leaks a "
                      "non-canonical dimensionless dimension out of any middle "
                      "operand slot; the downstream structural-equality comparison "
                      "on the combined expression then sees a mismatched dimension "
                      "and raises, so an applied function with three or more "
                      "operands whose middle one is dimensionless still errors. It "
                      "would NOT resolve. Note it is INDISTINGUISHABLE from the "
                      "desired behaviour on any input of length ≤ 2, which is what "
                      "makes it the near-miss the other four rivals cannot reach.",
        "rationale": "REJECT from E (`out = normSeq dims`) on an INTERIOR element: "
                     "for `[a, b, z]` with the middle element `b` dimensionless "
                     "(`isDimensionless b = true`) yet not canonical "
                     "(`b ≠ dimOne`), `normSeq [a, b, z]` reports `dimOne` at "
                     "position 1 while the rival reports `b`. Disjoint from both "
                     "S-head-verbatim (position 0) and S-last-verbatim (final "
                     "position): this rival AGREES with gold at both ends, so "
                     "neither of those witness points refutes it, and it is the "
                     "only case that probes `dims` at length 3. Verifying would be "
                     "SPEC-TOO-WEAK on the positional universality of the "
                     "per-element rule.",
        "witness": _witness(
            "(a b z : Dimension) (hdl : isDimensionless b = true) (hne : b ≠ dimOne)",
            "[a, b, z]",
            "  simp only [triple_pure, le_Prop_eq, true_implies]\n"
            "  simp [normSeq, normDim, hdl]\n"
            "  intro h\n"
            "  exact hne h\n"),
        "witness_reference": _ORACLE_MODULE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 2 frame-mutation rivals, 4 partial-domain rivals)
# plus 2 AXIOM_TESTS probes. This bundle models only the purely-functional core
# — a single method `normalizeDimensions` whose per-element predicate/constant
# (`isDimensionless`/`dimOne`) are OPAQUE axioms — so the discriminable surface
# is the value of the canonicalized list under the grounded `normSeq` fold, with
# every witness conditioned on the opaque predicate. Every sibling case is
# accounted for below.
#
#   sibling case                        -> here
#   -------------------------------------------------------------------------
#   pos-control-inverted-branch-local   -> S-pos-inline-binding   PORTED (reshape
#                                                                  kept proof-
#                                                                  closing here)
#   (declined by the sibling,            -> S-pos-forward-loop     ADDED by audit
#    directive 3: "needs an                                        2026-08-16 —
#    f(a+b)==f(a)+f(b) lemma the                                   the lemma IS
#    verifier cannot auto-discharge")                              provable here
#   pos-control-grounded-oracle         -> S-pos-grounded-oracle  PORTED
#                                                                  (materialise
#                                                                  `normSeq dims`)
#   admiss-f2p-singleton                -> S-adm-f2p-singleton    PORTED (audit:
#                                                                  obligation
#                                                                  satisfiable at
#                                                                  the F2P input)
#   frame-mutation-write-inplace        -> (none)                 VACUOUS
#   frame-mutation-noop-write           -> (none)                 VACUOUS
#   uniq-prepatch-no-canonicalise       -> S-prepatch-verbatim    PORTED
#   uniq-inverted-canonicalise          -> S-inverted-rule        PORTED
#   uniq-first-element-verbatim         -> S-head-verbatim        PORTED
#   uniq-last-element-verbatim          -> S-last-verbatim        PORTED
#   (no sibling case — the sibling's    -> S-interior-verbatim    ADDED by audit
#    head/tail rivals refute at len<=2                            2026-08-16 —
#    where the ends cover every slot)                             positional gap
#   ax-sound-is_dimensionless           -> (none)                 G-AX's job
#   ax-cover-resolvable                 -> (none)                 G-AX's job
#
# 7 ported + 2 ADDED by the 2026-08-16 audit, 2 dropped as VACUOUS carrier classes
# (frame-mutation), 2 dropped as axiom-lane. No case was dropped because its proof
# or witness was hard; every drop is a carrier limit stated with reason.
#
# VACUOUS (frame-mutation-write-inplace, frame-mutation-noop-write): the sibling
#   writes to a read-only container held at a fractional heap permission and must
#   reject for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `dims` is an immutable value, no `mut` input binder, no heap, no
#   aliasing, no permission system. There is no read-only input to overwrite and
#   no store to reject. No substitute fabricated (per the porting map).
# PORTED (admiss-f2p-singleton -> S-adm-f2p-singleton): the sibling's SHAPE (a
#   fractional-permission Requires at a self-call site) has no counterpart here,
#   but its DIRECTION does and is now tested. See the ADMISSIBILITY bullet above:
#   "no `require` clause" is not a sufficient reason to drop the lane, because on
#   a total carrier PRECOND-TOO-STRONG shows up as the obligation being
#   unsatisfiable at an F2P-shaped input rather than as a rejected call.
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
#   AUDIT (2026-08-16) — RE-MEASURED, and the "no witness ELABORATES" half of the
#   argument above needed correcting. It is true only for the NO-MEASURE framing:
#   there the module fails at the ``method`` itself (``Decreasing annotations are
#   required in total correctness semantics``), so the appended
#   ``example : True := trivial`` never runs and the build exits 1 —
#   ``witness-unproven``, as claimed. But the CONSTANT-MEASURE framing behaves
#   differently and the manifest did not distinguish them: the rival is refused on
#   the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin < spin``) while
#   the ``prove_correct`` block, which is the only thing carrying that obligation,
#   is STRIPPED from the witness file — so ``example : True := trivial`` appended
#   to it builds and exits 0. A trivial witness elaborating is not a refutation,
#   though, and that is why the class still ships nothing. Four tactic angles were
#   tried against a PURE-divergence rival (one whose returned value would be
#   correct if the loop ever finished, so ONLY termination can reject it) and none
#   reaches a verdict: the goal Lean prints is an unreduced
#   ``¬wp ((fun a => normSeq [d]) <$> forIn Lean.Loop.mk 1 ...)``, i.e. the
#   witness file has no obligation left that mentions termination at all. So the
#   DISPOSITION is unchanged and correct — nothing shippable in this class — but
#   the reason is sharper: the rejection is genuine and lives in the termination
#   obligation, and the witness contract cannot see that obligation because
#   ``witness_file`` removes the very block that carries it. Not a spec hole (the
#   rival IS rejected, measured twice) and not a battery gap (no witness of any
#   shape can attest to it on this carrier).
# AXIOM_TESTS (ax-sound-is_dimensionless, ax-cover-resolvable): dropped. The
#   axiom lane is G-AX's job; `isDimensionless`/`dimOne` and the `normSeq`
#   A-reference are validated there (axiom_check.py). This gate ignores
#   AXIOM_TESTS.
#
# BINDER / CLAUSE COVERAGE. The single clause E (`out = normSeq dims`) is the
#   whole spec; it is defended by all THREE positives (the frozen backward loop
#   with an inlined binding, a FORWARD-traversing loop, and the loop-free
#   grounded-oracle materialisation), probed for satisfiability at the F2P input by
#   S-adm-f2p-singleton, and attacked by all FIVE rivals. The single input binder
#   `dims` is varied across FOUR distinct witness LITERALS — `[d]`, `[d, e]`
#   (head bad), `[e, d]` (tail bad), `[a, b, z]` (interior bad) — carrying FIVE
#   hypothesis-distinguished sub-domains, since `[d]` is used twice with opposite
#   verdicts of the opaque predicate (`isDimensionless d = true` for S-prepatch,
#   `= false` for S-inverted). So both verdicts of `isDimensionless` and the head,
#   tail AND an interior slot are exercised, across lengths 1, 2 and 3.
#   pts=4 — `scripts/pbt_coverage.py` dedups on the list literal after aligning
#   binder names, so the two `[d]` witnesses collapse to one point for the
#   reporter even though they attack disjoint sub-domains. AUDIT (2026-08-16):
#   this block previously said "all four rivals" and omitted the forward-loop
#   positive and the interior witness point, i.e. it described the battery as it
#   stood BEFORE the two cases the 2026-08-16 audit added. Corrected to the
#   shipped set; the WITNESS PLACEMENT section above carries the measured
#   witness-by-rival cross-product.
#
# SPEC-TOO-WEAK / SPEC-TOO-STRONG probes run by the audit and NOT shipped (they
#   add no discrimination the shipped rivals do not already provide, but they are
#   the evidence that E is neither weak nor strong). Re-run independently
#   2026-08-16 with real builds; exit codes as recorded:
#     wrong, all REJECTED  — `return []`; `dims.map (fun _ => dimOne)`;
#                            `(normSeq dims).reverse`; canonicalize-all-but-the-
#                            second-element; and `if dims.length ≤ 1 then normSeq
#                            dims else dims` (correct on the F2P singleton shape,
#                            wrong from length 2 up — the "passes the reported
#                            scenario, breaks everything else" shape). Each exits
#                            1 with an `unsolved goals` residue in the
#                            `«ensures_1: out = normSeq dims»` case, i.e. rejected
#                            BY the clause and not by a tactic mismatch. The
#                            length-gated one is the sharpest: its residue is
#                            `(isDimensionless head = true → head = dimOne) ∧ ...`,
#                            exactly the per-element obligation it dodges.
#     correct, all VERIFY  — `dims.map normDim`; `dims.foldr (fun x acc =>
#                            normDim x :: acc) []`; `normSeq (normSeq dims)`
#                            (double canonicalization, exercising `normDim`'s
#                            idempotence), each closed by `induction dims <;>
#                            simp_all [normSeq, normDim]`; and the forward loop
#                            now SHIPPED as `S-pos-forward-loop`. So E admits
#                            loop-free, map-shaped, foldr-shaped, idempotent and
#                            forward-traversing faithful impls: no
#                            SPEC-TOO-STRONG on impl shape or on walk direction.
#     admissibility control — the `have` in `S-adm-f2p-singleton` is load-bearing,
#                            not decoration: flipping its claim from
#                            `normSeq [x] = [dimOne]` to `normSeq [x] = [x]`
#                            (everything else byte-identical) makes the case FAIL,
#                            exit 1 on `⊢ dimOne = x`. So that positive's outcome
#                            tracks what the `have` asserts about the obligation
#                            at the F2P-shaped input.
#
# AUDIT (2026-08-16, second independent pass) — a further SEVEN wrong impls and
#   SEVEN correct reshapes, none overlapping the probes above, built against the
#   frozen spec. Exit codes observed, not predicted:
#     wrong, all REJECTED (exit 1, each with its residue inside the
#       `«ensures_1: out = normSeq dims»` case, so rejected BY the clause):
#         `(normSeq dims).reverse`            residue `normSeq bs ++ [normDim a]
#                                             = normDim a :: normSeq bs`  (order)
#         `normSeq (dims ++ dims)`            (length by duplication)
#         `if dims.length ≤ 2 then normSeq dims else dims` — the sharpest of the
#             set: it agrees with gold on EVERY shipped witness point except
#             S-interior's length-3 one, so it is the near-miss that would have
#             survived this battery before S-interior was added. Residue
#             `1 < bs.length → (isDimensionless a = true → a = dimOne) ∧ ...`,
#             exactly the per-element obligation the length gate dodges. This is
#             the machine-checked evidence that S-interior is load-bearing.
#         canonicalize only EVEN indices (`dims.zipIdx.map ...`)
#         `normSeq dims.tail`                 (drops the head)
#         `dimOne :: normSeq ds`              (forces the head unconditionally)
#         `if dims.all isDimensionless then normSeq dims else dims`
#                                             (all-or-nothing gating)
#     correct, all VERIFY (exit 0) — `dims.map normDim`; `dims.foldr`;
#         `(dims.reverse.map normDim).reverse`; `normSeq (normSeq dims)`;
#         `dims.filterMap (fun d => some (normDim d))`; and a forward loop
#         accumulating onto a REVERSED accumulator then reversing at the end
#         (invariant `acc = (normSeq (dims.take i)).reverse`). Each closes from a
#         `have hmap : ∀ xs, normSeq xs = xs.map normDim` proven by induction
#         inside the tactic body, so no top-level lemma is added and
#         `variant_scope` stays clean. NOTE the reverse-map-reverse and
#         idempotence reshapes each needed two or three proof attempts before
#         closing — the first failures were `rewrite` pattern misses and a "No
#         goals to be solved" over-proof, i.e. MY tactic scripts, not the spec.
#         Recorded because "I could not close it" is not evidence of
#         SPEC-TOO-STRONG and must not be reported as such.
#     divergence, RE-MEASURED against `loom.semantics.termination "total"`:
#         a no-measure loop is refused at the `method` (`Decreasing annotations
#         are required in total correctness semantics`), so an appended
#         `example : True := trivial` never runs (exit 1). A CONSTANT-measure
#         pure-divergence rival — one whose returned value would be correct if
#         the loop ever finished, so ONLY termination can reject it — is refused
#         on `case «decreasing_1: spin» ... ⊢ 1 < spin` (exit 1), while the same
#         module with `example : True := trivial` appended EXITS 0, because
#         `witness_file` strips the `prove_correct` block that carries the
#         termination obligation. A refutation witness against it reaches goal
#         `False` (type-revealing `exact (0 : Nat)` probe), i.e. the
#         postcondition HOLDS at that input for this rival. So the class is
#         genuinely rejected by the semantics and genuinely unwitnessable here;
#         the disposition above is confirmed, not merely restated.
AXIOM_TESTS = []
